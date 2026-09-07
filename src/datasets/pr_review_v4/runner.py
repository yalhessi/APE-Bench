"""Run production-identical v4 candidate work units through the APE orchestrator."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict, BaseModel, Field

from ape.orchestration import TaskOrchestrator
from ape.tasks.base import create_task_from_data
from ape.utils import deep_merge, load_yaml, parse_cli_args
from ape.utils.logging import create_logger

from .io import canonical_json_bytes, load_jsonl, sha256_bytes
from .runs import (
    candidate_response_rows,
    failed_work_unit_ids,
    reviewed_workspace_map,
    unbuilt_base_commits,
    write_candidate_responses,
)
from .schema import (
    ChangeGraph,
    InvestigationTask,
    OpportunityEvidenceArtifact,
    OracleOpportunity,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewOpportunity,
    ReviewWorkUnit,
)
from .run_contract import create_run_plan
from .task_adapter import (
    build_candidate_task_data,
    build_file_task_data,
    build_focused_task_data,
    build_opportunity_task_data,
    build_review_opportunity_task_data,
)
from src.mathlib_review.run_config import load_run as _load_run


#: Which reviewer this run drives. Each arm schedules and renders its own invocations from
#: the same gold-free change graph; they differ in scope, not in what they are allowed to see.
#:
#: * `generalist`  — one invocation per work unit. The control.
#: * `focused`     — one per (spec, work unit) the spec's rule selects. Four specialists.
#: * `file`        — one per changed file. The component, restricted to cross-target claims.
ARM_CHOICES = ("generalist", "focused", "file")


class V4DatasetConfig(BaseModel):
    # `extra="forbid"`, because the half of the config that spends money was the unvalidated
    # half. A misspelled key was silently ignored and the field fell back to its default:
    # `per_pr_cost_capp: 1.50` left the cap at 8.0, authorising five times the intended
    # budget, while `ExecutionConfig` rejected the same typo one block away in the same file.
    model_config = ConfigDict(extra="forbid")

    arm: str = "generalist"
    #: Focused scheduling reads the modification inventory, which is a treatment artifact
    #: rather than part of the release. Required only for `arm: focused`.
    modification_inventory: Optional[Path] = None
    release: Path
    pr_numbers: List[int] = Field(default_factory=list)
    work_unit_ids: List[str] = Field(default_factory=list)
    work_unit_limit: int = 0
    output_file: Path
    run_name: str = "pr_review_v4_candidates"
    dry_run: bool = False
    require_prebuilt_workspaces: bool = True
    retry_failed_from: Optional[Path] = None


def load_run(config_path: Path, overrides: Optional[Dict[str, Any]] = None):
    """Load a v4 generation run. The convention itself is in `mathlib_review.run_config`, which existed
    three times byte-identical except for the model validated against."""

    return _load_run(config_path, V4DatasetConfig, overrides)


def _generalist_task_data(units, episode_by_id, prompt_by_id, opportunities_by_unit,
                          production_by_unit, production_evidence):
    """The per-site control, and the two adjudication tasks that share its shape."""

    return [
        build_opportunity_task_data(
            unit, episode_by_id[unit.episode_id], prompt_by_id[unit.work_unit_id],
            opportunities_by_unit[unit.work_unit_id],
        )
        if unit.work_unit_id in opportunities_by_unit
        else build_review_opportunity_task_data(
            unit, episode_by_id[unit.episode_id], prompt_by_id[unit.work_unit_id],
            production_by_unit[unit.work_unit_id], production_evidence,
        )
        if unit.work_unit_id in production_by_unit
        else build_candidate_task_data(
            unit, episode_by_id[unit.episode_id], prompt_by_id[unit.work_unit_id]
        )
        for unit in units
    ]


def _focused_task_data(dataset, release, units, episodes, graphs, logger):
    """Schedule and render the four focused specs, then adapt them to tasks."""

    from .focused_specs import default_specs, schedule_focused
    from .render_focused import render_focused_all
    from .schema import ModificationRecord

    if dataset.modification_inventory is None:
        raise ValueError("arm 'focused' requires dataset.modification_inventory")
    modifications = load_jsonl(dataset.modification_inventory, ModificationRecord)
    specs = default_specs()
    invocations = schedule_focused(
        specs, modifications, units, dataset.pr_numbers or None
    )
    prompts = render_focused_all(specs, invocations, units, episodes, graphs)
    unit_by_id = {item.work_unit_id: item for item in units}
    episode_by_id = {item.episode_id: item for item in episodes}
    logger.info("focused arm: %d invocations over %d work units",
                len(invocations), len({item.work_unit_id for item in invocations}))
    return [
        build_focused_task_data(
            unit_by_id[prompt.work_unit_id],
            episode_by_id[unit_by_id[prompt.work_unit_id].episode_id],
            prompt,
        )
        for prompt in prompts
    ], prompts


def _file_task_data(dataset, release, units, episodes, graphs, logger):
    """Schedule and render one invocation per changed file."""

    from .render_file_scoped import render_file_all, schedule_files

    invocations = schedule_files(graphs, units, dataset.pr_numbers or None)
    prompts = render_file_all(invocations, episodes, graphs)
    unit_by_id = {item.work_unit_id: item for item in units}
    episode_by_id = {item.episode_id: item for item in episodes}
    graph_by_episode = {item.episode_id: item for item in graphs}
    invocation_by_id = {item.invocation_id: item for item in invocations}
    logger.info("file arm: %d invocations over %d files",
                len(invocations), len({item.path for item in invocations}))
    data = []
    for prompt in prompts:
        unit = unit_by_id[prompt.work_unit_id]
        invocation = invocation_by_id[prompt.invocation_id]
        data.append(build_file_task_data(
            unit, episode_by_id[unit.episode_id], prompt, invocation.path,
            graph_by_episode[unit.episode_id],
        ))
    return data, prompts


async def run(dataset: V4DatasetConfig, scaffold, task_overrides, logger):
    if dataset.arm not in ARM_CHOICES:
        raise ValueError(f"unknown arm {dataset.arm!r}; expected one of {ARM_CHOICES}")
    release = dataset.release
    units = load_jsonl(release / "derived/work_units.jsonl", ReviewWorkUnit)
    episodes = load_jsonl(release / "input/episodes.jsonl", ReviewEpisodeInput)
    prompts = load_jsonl(release / "derived/rendered_prompts.jsonl", RenderedPrompt)
    opportunity_path = release / "derived/oracle_opportunities.jsonl"
    opportunities = load_jsonl(opportunity_path, OracleOpportunity) if opportunity_path.is_file() else []
    production_path = release / "derived/opportunities.jsonl"
    production_opportunities = (
        load_jsonl(production_path, ReviewOpportunity) if production_path.is_file() else []
    )
    investigation_path = release / "derived/investigation_tasks.jsonl"
    investigations = (
        load_jsonl(investigation_path, InvestigationTask) if investigation_path.is_file() else []
    )
    production_evidence_path = release / "derived/opportunity_evidence.jsonl"
    production_evidence = (
        load_jsonl(production_evidence_path, OpportunityEvidenceArtifact)
        if production_evidence_path.is_file()
        else []
    )
    if opportunities and production_opportunities:
        raise ValueError("release cannot mix oracle and production opportunities")
    if dataset.pr_numbers:
        wanted = set(dataset.pr_numbers)
        units = [unit for unit in units if unit.pr_number in wanted]
    if dataset.work_unit_ids:
        wanted_units = set(dataset.work_unit_ids)
        units = [unit for unit in units if unit.work_unit_id in wanted_units]
        missing_units = wanted_units - {unit.work_unit_id for unit in units}
        if missing_units:
            raise ValueError(f"unknown requested work_unit_ids={sorted(missing_units)}")
    if dataset.retry_failed_from:
        failed = failed_work_unit_ids(dataset.retry_failed_from)
        units = [unit for unit in units if unit.work_unit_id in failed]
        logger.info("Retry selection: %d failed work units from %s", len(units),
                    dataset.retry_failed_from)
    if dataset.work_unit_limit:
        units = units[:dataset.work_unit_limit]
    selected_unit_ids = {item.work_unit_id for item in units}
    selected_investigations = [
        item for item in investigations if item.work_unit_id in selected_unit_ids
    ]
    episode_by_id = {item.episode_id: item for item in episodes}
    prompt_by_id = {item.work_unit_id: item for item in prompts}
    opportunities_by_unit = {}
    for opportunity in opportunities:
        opportunities_by_unit.setdefault(opportunity.work_unit_id, []).append(opportunity)
    investigation_by_id = {item.investigation_id: item for item in investigations}
    production_by_unit = {}
    for opportunity in production_opportunities:
        investigation = investigation_by_id.get(opportunity.investigation_id)
        if investigation is None:
            raise ValueError(
                f"production opportunity has no investigation: {opportunity.opportunity_id}"
            )
        production_by_unit.setdefault(investigation.work_unit_id, []).append(opportunity)
    graphs = load_jsonl(release / "derived/change_graphs.jsonl", ChangeGraph)
    arm_prompts = prompts
    if dataset.arm == "focused":
        data, arm_prompts = _focused_task_data(
            dataset, release, units, episodes, graphs, logger
        )
    elif dataset.arm == "file":
        data, arm_prompts = _file_task_data(
            dataset, release, units, episodes, graphs, logger
        )
    else:
        data = _generalist_task_data(
            units, episode_by_id, prompt_by_id, opportunities_by_unit,
            production_by_unit, production_evidence,
        )
    if dataset.dry_run:
        for item in data:
            logger.info("%s PR #%d changes=%d prompt=%s",
                        getattr(item, "invocation_id", None) or item.work_unit_id,
                        item.pr_number, len(item.change_ids),
                        item.rendered_prompt_sha256[:12])
        logger.info("arm=%s invocations=%d", dataset.arm, len(data))
        return None
    # Seal the pre-registration before any model call, but only for a real run: a dry
    # run must leave no artifact behind, and a plan sealed from one would block the
    # eventual run under `write_once` if any input changed in between.
    create_run_plan(
        release=release,
        out=dataset.output_file.parent / "run_plan.json",
        run_id=dataset.run_name,
        model_name=scaffold.llm_config.model_name,
        units=units,
        # The arm's own prompts, not the release's: a focused or file run sends prompts the
        # release never rendered, and a plan carrying the release's would vouch for text
        # nobody was shown.
        prompts=arm_prompts,
        investigations=selected_investigations,
        method_registry_path=(release / "methods.jsonl") if investigations else None,
        orchestrator_id=dataset.run_name,
        scaffold_config_sha256=sha256_bytes(
            canonical_json_bytes(scaffold.model_dump(mode="json"))
        ),
    )
    if dataset.require_prebuilt_workspaces:
        missing = await unbuilt_base_commits(
            item.target_workspace.commit_hash for item in data
        )
        if missing:
            raise RuntimeError(
                f"{len(missing)} base workspace(s) are not prebuilt: {missing}. Run "
                "`./ape/bin/python -m src.datasets.pr_review_v4.prebuild --config "
                "configs/pr_review_v4_pilot.yaml`, then execute the printed build command."
            )
    tasks = [create_task_from_data(item.model_dump(mode="json"), scaffold,
                                   task_config_overrides=task_overrides) for item in data]
    orchestrator = TaskOrchestrator(config=scaffold, orchestrator_id=dataset.run_name, logger=logger)
    results = await orchestrator.run(tasks)
    data_by_task_id = {item.task_id: item for item in data}
    rows = candidate_response_rows(data_by_task_id, results.task_results)
    workspace_map = await reviewed_workspace_map(
        orchestrator.tasks_dir, data_by_task_id, results.task_results
    )
    write_candidate_responses(dataset.output_file, rows)
    workspace_map_path = dataset.output_file.with_name(dataset.output_file.stem + "_workspace_map.json")
    workspace_map_path.write_text(json.dumps(workspace_map, sort_keys=True, indent=2) + "\n")
    logger.info("Wrote %d terminal work-unit responses to %s", len(rows), dataset.output_file)
    logger.info("Wrote %d reviewed workspace roots to %s", len(workspace_map), workspace_map_path)
    return dataset.output_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args, rest = parser.parse_known_args()
    dataset, scaffold, task_overrides = load_run(args.config, parse_cli_args(rest))
    result = asyncio.run(run(dataset, scaffold, task_overrides, create_logger()))
    if result:
        print(result)


if __name__ == "__main__":
    main()
