"""
Workspace (agentic) mode for v2 review — configured like any other ape task.

The config YAML is a STANDARD scaffold config (the same shape as
configs/ape_bench_proof_engineering_pilot.yaml): top-level `llm_config`,
`execution`, `task_config`, `scaffold_type`, optional `tools_config` /
`runtime_config` — plus a `dataset:` section selecting which PRs to review.
So the model and all generation params are controlled exactly as for
proof_engineering, and CLI dot-overrides work too:

    python -m src.datasets.pr_review_v2.runner_workspace \
        --config configs/pr_review_workspace_v2.yaml \
        llm_config.model_name=gpt_5.2 execution.sample_max_cost=1.0 dataset.limit=2

Reuses the execution infrastructure: tasks are built with create_task_from_data
and run through the standard TaskOrchestrator (which owns the tasks/<task_id>/
run-dir layout, persistence, resume and concurrency — no reimplementation here).
`task_config` is split out and passed as task_config_overrides exactly like the
standard CLI does. Results are adapted into the same PredictionRecord the
diff_only runner emits (mode="workspace"), so D2/D3 score both identically.

Note: lean_retrieve is OFF by default — it needs a per-commit retrieval index
(build via `python -m ape.toolkits.retrieve.lean.build`); without it the tool
silently returns empty results.
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from ape.orchestration import TaskOrchestrator
from ape.tasks.base import create_task_from_data
from ape.utils import deep_merge, load_yaml, parse_cli_args
from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

from .predictions import PredictionRecord
from .runner import load_records, summarize
from .schema import PRReviewV2Record
from .task_adapter import build_task_data, result_to_prediction


class WorkspaceDatasetConfig(BaseModel):
    """The `dataset:` section — which PRs to review and where to write predictions.
    Field names match the diff_only runner so load_records is reused as-is."""

    records: Path = Field(description="v2 extract JSONL (gold records)")
    task_type: str = Field(
        default="lean_pr_review_v2",
        description="Which review task to run (single-task runner): lean_pr_review_v2 (holistic) | "
        "lean_pr_review_golf | lean_pr_review_dup | lean_pr_review_gen.",
    )
    checkers: List[str] = Field(
        default_factory=list,
        description="The composed/decomposed review's checker set (used by review.py only). "
        "Empty defaults to the standard set in review.DECOMPOSED_CHECKERS.",
    )
    pr_numbers: List[int] = Field(default_factory=list)
    limit: int = Field(default=0, description="0 = all")
    h0_review_commit_only: bool = False
    output_dir: Path = PROJECT_ROOT / "inputs" / "pr_review_v2" / "predictions"
    output_file: Optional[Path] = None
    resume: bool = True
    dry_run: bool = False
    run_name: Optional[str] = Field(
        default=None,
        description="Descriptive .ape/runs/ dir name; auto-built from model+PRs+tool-rung if unset",
    )


def _tool_rung_tag(enabled_tools: Optional[List[str]]) -> str:
    tools = set(enabled_tools or [])
    if not tools:
        return "default"
    if tools == {"file_read"}:
        return "readonly"
    # Compositional so each capability rung gets a distinct run dir (no accidental
    # resume of a different rung): e.g. grep_verify, verify_retrieve, grep_verify_retrieve.
    parts = []
    if "content_search" in tools:
        parts.append("grep")
    if "lean_verify" in tools:
        parts.append("verify")
    if "lean_retrieve" in tools:
        parts.append("retrieve")
    return "_".join(parts) if parts else "tools"


def _prompt_tag(prompt_version: Optional[str]) -> str:
    """Compact tag for the prompt framing: acceptability_v2 -> acc_v2, mergeready_v1 -> mer_v1."""
    pv = prompt_version or "acceptability_v2"
    if "_v" in pv:
        name, num = pv.rsplit("_v", 1)
        return f"{name[:3]}_v{num}"
    return pv[:6]


def _build_run_name(dataset: "WorkspaceDatasetConfig", model_name: str,
                    enabled_tools: Optional[List[str]], prompt_version: Optional[str], n_prs: int) -> str:
    """Descriptive .ape/runs/ name, matching the existing convention
    (e.g. ape_bench_pe_gpt52_first20_no_retrieve). Encodes every ablation axis that
    distinguishes a run — which review task (holistic v2 / dup / gen checker), model,
    PR count, tool rung, prompt framing — so a config change gets a FRESH dir and never
    silently resumes a different setup. (Note: niche task_config knobs like finding_budget
    are not in the name; set dataset.run_name explicitly if you vary those.)"""
    if dataset.run_name:
        return dataset.run_name
    # task tag: lean_pr_review_v2 -> v2, lean_pr_review_dup -> dup, _gen -> gen
    task_tag = dataset.task_type.replace("lean_pr_review_", "") or "v2"
    model_tag = model_name.replace("_", "").replace(".", "").replace("-", "")  # gpt_5.4 -> gpt54
    return (f"pr_review_{task_tag}_{model_tag}_{n_prs}prs_"
            f"{_tool_rung_tag(enabled_tools)}_{_prompt_tag(prompt_version)}")


def load_workspace_run(
    config_path: Optional[Path], cli_overrides: Optional[Dict[str, Any]]
) -> Tuple[WorkspaceDatasetConfig, Any, Dict[str, Any]]:
    """Split a standard scaffold-config YAML into (dataset, scaffold_config, task_config_overrides)."""
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    raw: Dict[str, Any] = load_yaml(config_path) if config_path else {}
    if cli_overrides:
        raw = deep_merge(raw, cli_overrides)

    dataset = WorkspaceDatasetConfig.model_validate(raw.pop("dataset", {}))
    # task_config is popped and passed as overrides (the standard create_task_from_data path).
    task_config_overrides = raw.pop("task_config", {}) or {}
    raw.setdefault("scaffold_type", "ape_agent")
    scaffold_config = ApeAgentConfig.model_validate(raw)
    # The orchestrator/runtime rebuilds each task from its data + config, taking the
    # task_config from config.task_config_overrides — so the toolset/budget must live there.
    scaffold_config.task_config_overrides = task_config_overrides
    return dataset, scaffold_config, task_config_overrides


def _resolve_output(dataset: WorkspaceDatasetConfig, model_name: str) -> Path:
    if dataset.output_file:
        return dataset.output_file
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return dataset.output_dir / f"preds_{model_name}_workspace_{stamp}.jsonl"


def _pr_number_from_result(result: Any) -> Optional[int]:
    data = result if isinstance(result, dict) else result.model_dump(mode="json")
    if data.get("pr_number"):
        return int(data["pr_number"])
    task_id = str(data.get("task_id") or "")  # "pr_review_v2_33440"
    try:
        return int(task_id.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return None


def _result_to_prediction(result: Any, model_name: str) -> PredictionRecord:
    pr = _pr_number_from_result(result)
    data = result if isinstance(result, dict) else result.model_dump(mode="json")
    if not data.get("success", False):
        return PredictionRecord(
            pr_number=pr or 0, model=model_name, mode="workspace",
            parse_ok=False, parse_error=str(data.get("error") or "unsuccessful")[:2000],
        )
    prediction = result_to_prediction(result, model=model_name, mode="workspace", pr_number=pr)
    usage = data.get("token_usage") or {}
    prediction.cost_usd = usage.get("total_cost") or 0.0
    prediction.input_tokens = usage.get("input_tokens") or 0
    prediction.output_tokens = usage.get("output_tokens") or 0
    return prediction


async def run(
    dataset: WorkspaceDatasetConfig, scaffold_config, task_config_overrides: Dict[str, Any], logger
) -> Optional[Path]:

    model_name = scaffold_config.llm_config.model_name or "model"
    records = load_records(dataset)  # duck-typed: reads records/pr_numbers/limit/h0_review_commit_only
    logger.info("Workspace mode: %d records, task=%s, scaffold=%s, model=%s, tools=%s",
                len(records), dataset.task_type, scaffold_config.scaffold_type, model_name,
                task_config_overrides.get("enabled_tools", "<task default>"))

    if dataset.dry_run:
        for record in records:
            d = build_task_data(record, task_type=dataset.task_type)
            logger.info("PR #%d: task=%s base=%s head=%s changed=%d diff_chars=%d",
                        record.pr_number, d.task_type, d.target_workspace.commit_hash[:8],
                        (d.snapshot_head_sha or "")[:8], len(d.changed_files), len(d.diff))
        return None

    # Build one task per PR and run them through the standard Orchestrator — it owns
    # the tasks/<task_id>/ run-dir layout, persistence, resume, and concurrency, so we
    # don't reimplement any of that. The descriptive, stable run name lets re-runs resume.
    tasks = [
        create_task_from_data(
            build_task_data(r, task_type=dataset.task_type).model_dump(mode="json"),
            scaffold_config, task_config_overrides=task_config_overrides)
        for r in records
    ]
    run_name = _build_run_name(
        dataset, model_name, task_config_overrides.get("enabled_tools"),
        task_config_overrides.get("prompt_version"), len(records),
    )
    orchestrator = TaskOrchestrator(
        config=scaffold_config,
        orchestrator_id=run_name,
        logger=logger,
    )
    results = await orchestrator.run(tasks)

    predictions = [_result_to_prediction(tr, model_name) for tr in results.task_results]
    predictions.sort(key=lambda p: p.pr_number)

    output_file = _resolve_output(dataset, model_name)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w") as fh:
        for prediction in predictions:
            fh.write(json.dumps(prediction.model_dump(mode="json"), ensure_ascii=False) + "\n")

    rows = [p.model_dump(mode="json") for p in predictions]
    summary = summarize(rows)
    output_file.with_name(output_file.stem + "_summary.json").write_text(json.dumps(summary, indent=2))
    logger.info("Workspace summary: %s", summary)
    logger.info("Run dir (standard tasks/ layout): %s", orchestrator.workspace_path)
    logger.info("Predictions: %s", output_file)
    return output_file


def main(config_path: Optional[Path] = None, cli_overrides: Optional[Dict[str, Any]] = None, logger=None):
    logger = logger or create_logger()
    dataset, scaffold_config, task_config_overrides = load_workspace_run(config_path, cli_overrides)
    return asyncio.run(run(dataset, scaffold_config, task_config_overrides, logger))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic (workspace) v2 review — standard scaffold config")
    parser.add_argument("--config", type=Path, default=None)
    args, remaining = parser.parse_known_args()
    result = main(config_path=args.config, cli_overrides=parse_cli_args(remaining))
    if result:
        print(result)
