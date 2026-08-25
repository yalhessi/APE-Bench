"""The one command that runs a v5 review, in any of its three routing modes.

    ./ape/bin/python -m src.datasets.pr_review_v5.runner --config configs/pr_review_v5.yaml

Two things this deliberately does differently from the pipeline it descends from.

**One run identity.** `run_name` derives the orchestrator scratch dir, the results dir, the
sealed plan, the arm pool and the context trace. v4 spells a run's identity three times —
`dataset.run_name`, the parent of `dataset.output_file`, and the release name repeated in up
to eight downstream `--path` flags — with nothing enforcing that they agree, so a run can be
assembled from artifacts that were never part of it.

**`--dry-run` is a flag, not a default.** v4's checked-in configs set `dry_run: true`, which
makes every real run a command-line override, and of the two override spellings the docs
carry only one actually parses. Here the safe thing is explicit and the default is the thing
you meant.

The three modes share one execution and finalization path, and one pre-rendered prompt pool,
so a difference between them is a difference in routing and nothing else.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ape.orchestration import TaskOrchestrator
from ape.tasks.base import create_task_from_data
from ape.utils import parse_cli_args
from ape.llm_clients.config import COST_MODELS
from ape.utils.config_loader import deep_merge, load_yaml
from ape.utils.logging import create_logger

from src.datasets.pr_review_v4.io import (
    canonical_json_bytes,
    git_state,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from src.datasets.pr_review_v4.runs import unbuilt_base_commits
from src.datasets.pr_review_v4.schema import (
    ChangeGraph,
    ModificationRecord,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)

from .agenda import agenda_report, build_agenda, initial_jobs
from .arms import GENERALIST_ARM_ID
from .cutoffs import cutoffs_by_episode
from .finalize import finalize
from .paths import PRECEDENT_INDEX, assert_repo_root, run_dir
from .schema import ROUTING_MODES, V5RunManifest, V5RunPlan
from .trace import reconcile

LEAD_TASK_TYPE = "lean_pr_review_v5_lead"


class V5DatasetConfig(BaseModel):
    #: `fanout` (every arm everywhere) | `rules` (the deterministic rule's selection) |
    #: `lead` (the mandatory floor plus whatever the lead keeps or adds).
    routing_mode: str = "lead"
    release: Path
    #: The modification inventory is a treatment artifact, not part of a release, and it is
    #: what specialist eligibility is enumerated from.
    modification_inventory: Path
    #: The frozen deterministic execution release, so the non-model arm is identical in all
    #: three modes. Optional: without it the comparison is model-arms-only, which is a
    #: narrower claim but still a clean one.
    execution_release: Optional[Path] = None
    exclude_methods: List[str] = Field(default_factory=list)
    pr_numbers: List[int] = Field(default_factory=list)
    work_unit_limit: int = 0
    run_name: str = "pr_review_v5"
    dry_run: bool = False
    require_prebuilt_workspaces: bool = True
    pr_finding_limit: int = 20
    #: Cost policy. Both are required for a real run; a lead with no cap can spend the whole
    #: run on one work unit.
    standard_budget_cap: float = 0.25
    lead_cost_cap: float = 2.0
    per_pr_cost_cap: float = 8.0
    max_delegations: int = 60


def load_run(config_path: Path, overrides: Optional[Dict[str, Any]] = None):
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    raw = load_yaml(config_path)
    if overrides:
        raw = deep_merge(raw, overrides)
    dataset = V5DatasetConfig.model_validate(raw.pop("dataset"))
    task_overrides = raw.pop("task_config", {}) or {}
    raw.setdefault("scaffold_type", "ape_agent")
    scaffold = ApeAgentConfig.model_validate(raw)
    scaffold.task_config_overrides = task_overrides
    return dataset, scaffold, task_overrides


def _load_release(dataset: V5DatasetConfig):
    release = dataset.release
    return {
        "units": load_jsonl(release / "derived/work_units.jsonl", ReviewWorkUnit),
        "episodes": load_jsonl(release / "input/episodes.jsonl", ReviewEpisodeInput),
        "graphs": load_jsonl(release / "derived/change_graphs.jsonl", ChangeGraph),
        "release_prompts": load_jsonl(release / "derived/rendered_prompts.jsonl", RenderedPrompt),
        "modifications": load_jsonl(dataset.modification_inventory, ModificationRecord),
    }


def _context_index_identity() -> Dict[str, str]:
    """Hashes of the corpora a context read ranks over.

    Recorded in the plan because a retrieval result is only interpretable relative to the
    index that produced it: rebuild the index and the same query returns something else,
    with nothing in the run saying so.
    """

    identity: Dict[str, str] = {}
    manifest = PRECEDENT_INDEX / "manifest.json"
    if manifest.is_file():
        payload = json.loads(manifest.read_text())
        identity["precedent_corpus"] = payload.get("corpus_sha256", "")
        identity["precedent_model"] = payload.get("model_name", "")
    from src.datasets.zulip.config import ZulipConfig

    zulip = Path(ZulipConfig().sqlite_path)
    if zulip.is_file():
        zulip_manifest = Path("inputs/zulip/manifest.json")
        if zulip_manifest.is_file():
            identity["zulip_corpus"] = sha256_file(zulip_manifest)
    return identity


def _write_pool(path: Path, pool: Dict[str, Dict[str, Any]], cutoff_by_episode: Dict[str, str],
                trace_path: Path) -> None:
    """Write the runnable arm payloads, with the gate instant baked into each one.

    The cutoff arrives as data rather than being resolved inside the worker, so a worker
    process can neither choose its own instant nor silently proceed without one.
    """

    rows = []
    for invocation_id, payload in sorted(pool.items()):
        data = dict(payload)
        data["retrieval_cutoff"] = cutoff_by_episode.get(data.get("episode_id"))
        data["trace_path"] = str(trace_path)
        rows.append({
            "invocation_id": invocation_id,
            "arm_id": data["arm_id"],
            "work_unit_id": data["work_unit_id"],
            "spec_id": data.get("spec_id"),
            "rendered_prompt_sha256": data.get("rendered_prompt_sha256"),
            "task_data": data,
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")


def _lead_task_data(agenda, episodes, dataset, pool_path: Path, trace_path: Path,
                    cutoff_by_episode: Dict[str, str]) -> List[Dict[str, Any]]:
    """One lead per episode. A review round is the unit a maintainer actually reviews."""

    episode_by_id = {item.episode_id: item for item in episodes}
    by_episode: Dict[str, List[Any]] = {}
    for proposal in agenda.proposals:
        by_episode.setdefault(proposal.episode_id, []).append(proposal)

    data = []
    for episode_id, proposals in sorted(by_episode.items()):
        episode = episode_by_id[episode_id]
        data.append({
            "task_type": LEAD_TASK_TYPE,
            "task_id": f"pr5lead_{episode_id.replace(':', '_')}",
            "episode_id": episode_id,
            "pr_number": episode.pr_number,
            "pr_title": episode.title.text or "",
            "pr_description": episode.description.text or "",
            "diff": episode.diff,
            "changed_files": list(episode.changed_files),
            "snapshot_head_sha": episode.reviewed_head_sha,
            "snapshot_base_sha": episode.base_sha,
            "proposals": [item.model_dump(mode="json") for item in proposals],
            "arm_pool_path": str(pool_path),
            "routing_mode": agenda.routing_mode,
            "retrieval_cutoff": cutoff_by_episode.get(episode_id),
            "trace_path": str(trace_path),
            "target_workspace": {
                "name": "target",
                "commit_hash": episode.base_sha,
                "repo_url": "https://github.com/leanprover-community/mathlib4.git",
                "default_target": "Mathlib",
            },
        })
    return data


def _direct_arm_task_data(agenda, pool: Dict[str, Dict[str, Any]],
                          cutoff_by_episode: Dict[str, str],
                          trace_path: Path) -> List[Dict[str, Any]]:
    """`fanout` and `rules`: run the arms straight, with no lead in the loop.

    Same payloads and the same pre-rendered prompts the lead would have dispatched, so these
    are controls for the routing decision and not for the prompt.
    """

    data = []
    for proposal in initial_jobs(agenda):
        payload = dict(pool[proposal.invocation_id])
        payload["retrieval_cutoff"] = cutoff_by_episode.get(payload.get("episode_id"))
        payload["trace_path"] = str(trace_path)
        data.append(payload)
    return data


def _responses_from_results(results, mode: str) -> List[Dict[str, Any]]:
    """Normalize both execution shapes into one list of arm responses."""

    responses: List[Dict[str, Any]] = []
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        if mode == "lead":
            responses.extend(raw.get("arm_responses") or [])
        else:
            # A task that never reached a terminal submission carries no identity, so there
            # is nothing to attribute its (empty) output to. The failure itself is already
            # in the ledger via the delegation record, which is where a coverage failure
            # belongs; synthesizing a null-keyed response here made it look like an orphan
            # response instead and blocked reconciliation.
            if not raw.get("invocation_id"):
                continue
            responses.append({
                "invocation_id": raw.get("invocation_id"),
                "arm_id": raw.get("arm_id"),
                "work_unit_id": raw.get("work_unit_id"),
                "spec_id": raw.get("spec_id"),
                "pr_number": raw.get("pr_number"),
                "status": "success" if raw.get("success") else "failed",
                "candidates": raw.get("candidates") or [],
                "verification_artifacts": raw.get("verification_artifacts") or [],
                "rendered_prompt_sha256": raw.get("rendered_prompt_sha256"),
            })
    return responses


def _delegations_from_results(results, mode: str, agenda,
                              floor_records: Optional[List[Dict[str, Any]]] = None,
                              ) -> List[Dict[str, Any]]:
    """Delegation records: the lead's own plus the floor's, or synthesized for the
    model-free modes, where every job is decided by rule."""

    floor_records = list(floor_records or [])

    if mode == "lead":
        records = []
        for result in results.task_results:
            raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
            records.extend(raw.get("delegations") or [])
        return records + floor_records
    ran = {item.invocation_id for item in initial_jobs(agenda)}
    return [
        {
            "schema_version": "v5-delegation1",
            "invocation_id": item.invocation_id,
            "proposal_id": item.proposal_id,
            "arm_id": item.arm_id,
            "work_unit_id": item.work_unit_id,
            "pr_number": item.pr_number,
            "disposition": (
                "mandatory" if item.mandatory
                else "proposed" if item.invocation_id in ran else "pruned"
            ),
            "reason": ("" if item.invocation_id in ran else f"not selected in {mode} mode"),
            "budget_tier": "standard" if item.invocation_id in ran else None,
            "context_calls": [],
        }
        for item in agenda.proposals
    ]


def _build_plan(dataset: V5DatasetConfig, scaffold, agenda) -> V5RunPlan:
    """Seal the pre-registration. Constructed identically in dry and real runs.

    The dry run builds it and throws it away rather than skipping it: sealing is the only
    step a real run performs that a dry run otherwise would not, so skipping it made the dry
    run unable to catch exactly the errors it exists to catch cheaply.
    """

    model_name = scaffold.llm_config.model_name
    if not model_name:
        raise ValueError(
            "llm_config.model_name is not set. The sealed plan records which model produced "
            "a run, and a run that cannot name its model cannot be compared with another — "
            "so this is refused rather than stamped as null."
        )
    commit, tree_state = git_state()
    plan = V5RunPlan(
        run_id=f"v5run:{dataset.run_name}",
        run_name=dataset.run_name,
        routing_mode=dataset.routing_mode,
        agenda_sha256=sha256_bytes(canonical_json_bytes(agenda.model_dump(mode="json"))),
        release=str(dataset.release),
        prompt_sha256_by_invocation={
            item.invocation_id: item.prompt_sha256 for item in agenda.proposals
        },
        arm_sha256_by_id={arm.arm_id: arm.source_sha256 for arm in agenda.arms},
        context_index_sha256=_context_index_identity(),
        model_name=model_name,
        scaffold_config_sha256=sha256_bytes(
            canonical_json_bytes(scaffold.model_dump(mode="json"))),
        lead_cost_cap=dataset.lead_cost_cap,
        standard_budget_cap=dataset.standard_budget_cap,
        per_pr_cost_cap=dataset.per_pr_cost_cap,
        git_commit=commit, git_tree_state=tree_state,
        source_sha256="",
    )
    return plan.model_copy(update={"source_sha256": sha256_bytes(canonical_json_bytes(
        plan.model_dump(mode="json", exclude={"source_sha256"})))})


#: Artifacts whose presence means a previous execution already produced results here.
#: The sealed plan and agenda are deliberately not in this list: they are reproducible from
#: the same inputs, so re-writing them byte-identically is a `write_once` no-op.
_TERMINAL_OUTPUTS = (
    "run_manifest.json", "delegations.jsonl", "arm_responses.jsonl", "findings.jsonl",
    "issues.jsonl", "finalization_report.json",
)


def _scratch_dirs(run_name: str) -> List[Path]:
    from ape.orchestration.config import ExecutionConfig  # noqa: F401

    base = Path(".ape/runs")
    return [base / run_name, base / f"{run_name}_floor"]


def guard_run_name(dataset: V5DatasetConfig, logger) -> None:
    """Refuse to reuse a run name that already produced results, BEFORE spending anything.

    Two separate things go wrong when a name is reused after a code change, and neither
    announces itself:

    * `run_name` is the orchestrator's **resume key**. Every attempt that already succeeded
      is returned from cache, so the code you just changed never executes — the run looks
      like it re-ran and reports the old behaviour.
    * The derived outputs *do* get rebuilt, and `write_once` then refuses them for differing
      — but only at the very end, after the floor has been paid for again.

    So the check happens here, before the first orchestrator starts. This is the same
    discipline v4 records in its own configs ("bumped to FRESH names — prompt+tool changed,
    must not resume"); making it an error rather than a convention is the difference between
    remembering it and being told.
    """

    directory = run_dir(dataset.run_name)
    existing = [name for name in _TERMINAL_OUTPUTS if (directory / name).is_file()]
    scratch = [item for item in _scratch_dirs(dataset.run_name) if item.is_dir()]
    if not existing and not scratch:
        return
    raise RuntimeError(
        f"run_name {dataset.run_name!r} has already been executed"
        + (f" (outputs: {', '.join(existing)})" if existing else "")
        + (f" (orchestrator state: {', '.join(str(item) for item in scratch)})" if scratch else "")
        + ".\n\n"
        "`run_name` is the orchestrator's resume key, so re-running it would return every "
        "previously successful attempt from cache — any code you changed since would not "
        "execute, and the run would report the old behaviour as if it were new.\n\n"
        "Either:\n"
        f"  - bump the name (dataset.run_name={dataset.run_name}_rep2), keeping the old run, or\n"
        "  - pass --redo to discard this run's results and orchestrator state and execute "
        "it again from scratch."
    )


def redo_run(dataset: V5DatasetConfig, logger) -> None:
    """Discard a run's results AND its orchestrator state, so a redo really re-executes.

    Clearing only the results directory would leave the resume key intact, which is the
    failure this exists to prevent: the outputs would be rebuilt from cached attempts and
    look like a fresh run.
    """

    import shutil

    directory = run_dir(dataset.run_name)
    for target in [directory, *_scratch_dirs(dataset.run_name)]:
        if target.is_dir():
            shutil.rmtree(target)
            logger.info("redo: removed %s", target)


async def _require_prebuilt(dataset: V5DatasetConfig, data: List[Dict[str, Any]]) -> None:
    if not dataset.require_prebuilt_workspaces:
        return
    missing = await unbuilt_base_commits(
        item["target_workspace"]["commit_hash"] for item in data
    )
    if missing:
        raise RuntimeError(
            f"{len(missing)} base workspace(s) are not prebuilt: {missing}. Run "
            "`./ape/bin/python -m src.datasets.pr_review_v4.prebuild --config "
            "<a v4 config for this release>`, then the printed lean build command."
        )


def _context_calls_by_invocation(trace_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Group the append-only context trace. Shared by the floor and the lead."""

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    if not trace_path.is_file():
        return grouped
    for line in trace_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        grouped.setdefault(row.get("invocation_id", "?"), []).append(row)
    return grouped


async def run(dataset: V5DatasetConfig, scaffold, task_overrides, logger):
    assert_repo_root()
    if dataset.routing_mode not in ROUTING_MODES:
        raise ValueError(
            f"unknown routing_mode {dataset.routing_mode!r}; expected one of {ROUTING_MODES}")

    release = _load_release(dataset)
    units = release["units"]
    if dataset.pr_numbers:
        wanted = set(dataset.pr_numbers)
        units = [unit for unit in units if unit.pr_number in wanted]
    if dataset.work_unit_limit:
        units = units[:dataset.work_unit_limit]
    if not units:
        raise ValueError("no work units selected; check dataset.pr_numbers")
    selected_prs = sorted({unit.pr_number for unit in units})
    episodes = [item for item in release["episodes"] if item.pr_number in set(selected_prs)]

    agenda, pool = build_agenda(
        run_name=dataset.run_name, routing_mode=dataset.routing_mode,
        release=dataset.release, modification_inventory=dataset.modification_inventory,
        units=units, episodes=episodes, graphs=release["graphs"],
        release_prompts=release["release_prompts"], modifications=release["modifications"],
        pr_numbers=selected_prs,
    )
    report = agenda_report(agenda)

    if dataset.dry_run:
        logger.info("DRY RUN — nothing is written and no model is called")
        logger.info("%s", json.dumps(report, indent=2))
        floor = report["mandatory_floor_cost"]
        cap = dataset.per_pr_cost_cap * len(selected_prs)
        logger.info(
            "mandatory generalist floor $%.2f vs run cap $%.2f — %s",
            floor, cap, "fits" if floor <= cap else "DOES NOT FIT (raise per_pr_cost_cap)")
        # Resolving cutoffs during a dry run is the cheapest place to discover that a gated
        # read would have been impossible.
        cutoffs_by_episode(episodes)
        logger.info("retrieval cutoffs resolve for all %d episode(s)", len(episodes))
        plan = _build_plan(dataset, scaffold, agenda)
        logger.info("run plan seals (agenda %s, %d prompt hashes) — not written",
                    plan.agenda_sha256[:12], len(plan.prompt_sha256_by_invocation))
        return None

    guard_run_name(dataset, logger)
    out = run_dir(dataset.run_name)
    out.mkdir(parents=True, exist_ok=True)
    cutoff_by_episode = cutoffs_by_episode(episodes)
    pool_path = out / "arm_pool.jsonl"
    trace_path = out / "context_trace.jsonl"
    _write_pool(pool_path, pool, cutoff_by_episode, trace_path)
    write_once(out / "agenda.json", pretty_json_bytes(agenda.model_dump(mode="json")))
    write_once(out / "agenda_report.json", pretty_json_bytes(report))

    plan = _build_plan(dataset, scaffold, agenda)
    write_once(out / "run_plan.json", pretty_json_bytes(plan.model_dump(mode="json")))

    if dataset.routing_mode == "lead":
        # No separate floor pass. The coverage floor is injected as the lead's first wave, so
        # there is one agent per PR delegating all of its own work — the shape the generation
        # is named for. The guarantee survives the move: `delegate` prepends the mandatory
        # jobs whatever the lead asked for, and `submit_routing` refuses to close until they
        # have run, so the floor is still not the lead's to skip.
        data = _lead_task_data(agenda, episodes, dataset, pool_path, trace_path,
                               cutoff_by_episode)
        scaffold.task_config_overrides = {
            **(task_overrides or {}),
            "standard_budget_cap": dataset.standard_budget_cap,
            "max_delegations": dataset.max_delegations,
            "per_pr_cost_cap": dataset.per_pr_cost_cap,
        }
        scaffold.execution.sample_max_cost = dataset.lead_cost_cap
    else:
        data = _direct_arm_task_data(agenda, pool, cutoff_by_episode, trace_path)
        scaffold.execution.sample_max_cost = dataset.standard_budget_cap

    await _require_prebuilt(dataset, data)

    logger.info("routing_mode=%s tasks=%d prs=%s", dataset.routing_mode, len(data), selected_prs)
    tasks = [create_task_from_data(item, scaffold,
                                   task_config_overrides=scaffold.task_config_overrides)
             for item in data]
    orchestrator = TaskOrchestrator(config=scaffold, orchestrator_id=dataset.run_name,
                                    logger=logger)
    results = await orchestrator.run(tasks)

    responses = _responses_from_results(results, dataset.routing_mode)
    delegations = _delegations_from_results(results, dataset.routing_mode, agenda)
    write_once(out / "arm_responses.jsonl", jsonl_bytes(responses))
    write_once(out / "delegations.jsonl", jsonl_bytes(delegations))

    summary = finalize(
        out, units=units, responses=responses, routing_mode=dataset.routing_mode,
        execution_release=dataset.execution_release,
        exclude_methods=dataset.exclude_methods, pr_numbers=selected_prs,
        pr_finding_limit=dataset.pr_finding_limit, logger=logger,
    )

    manifest = reconcile(
        agenda=agenda, delegations=delegations, responses=responses,
        plan=plan, results=results, issues_total=summary["issues_total"],
    )
    write_once(out / "run_manifest.json", pretty_json_bytes(manifest.model_dump(mode="json")))
    logger.info("run dir: %s", out)
    logger.info("completion_status=%s issues=%d cost=$%.2f",
                manifest.completion_status, manifest.issues_total, manifest.total_cost)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true",
                        help="Render and cost the agenda; write nothing, call no model.")
    parser.add_argument("--cost-model", choices=COST_MODELS, default=None,
                        help="How to read provider token accounting when pricing calls. "
                             "Default is the LLMConfig default (prompt_inclusive); pass "
                             "prompt_exclusive to reproduce pre-2026-08 figures.")
    parser.add_argument("--redo", action="store_true",
                        help="Discard this run_name's results and orchestrator state, then "
                             "execute it again. Without this, reusing a name is refused.")
    args, rest = parser.parse_known_args()
    dataset, scaffold, task_overrides = load_run(args.config, parse_cli_args(rest))
    if args.dry_run:
        dataset.dry_run = True
    if args.cost_model:
        scaffold.llm_config.cost_model = args.cost_model
    logger = create_logger()
    logger.info("cost model: %s", scaffold.llm_config.cost_model)
    if args.redo and not dataset.dry_run:
        redo_run(dataset, logger)
    result = asyncio.run(run(dataset, scaffold, task_overrides, logger))
    if result:
        print(result)


if __name__ == "__main__":
    main()
