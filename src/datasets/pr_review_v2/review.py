"""
Composed (fully-decomposed) review — the second review implementation.

Runs the decomposed checker set (golf / duplication / generality — each a focused,
kernel-verified-at-submission task) over the PRs and aggregates their findings into
one review per PR. This is the structural counterpart to the single holistic
acceptability pass (runner_workspace + lean_pr_review_v2): both share the
materialization, the PredictionRecord contract, and the D1/D2/D3 evaluators, so the
two implementations are directly comparable.

All PR×checker tasks run in ONE TaskOrchestrator (standard tasks/<task_id>/ layout);
results are grouped by PR and merged (findings union, deduped, each tagged with its
source checker). The checkers are verifiable tasks, so a composed finding that
carries verified=True is kernel-checked by construction.

Config is the same standard scaffold-config YAML as runner_workspace, plus
`dataset.checkers` (defaults to DECOMPOSED_CHECKERS). No CLI yet — batch entry only:

    python -m src.datasets.pr_review_v2.review --config configs/pr_review_composed_v2.yaml
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ape.orchestration import TaskOrchestrator
from ape.tasks.base import create_task_from_data
from ape.utils import parse_cli_args
from ape.utils.logging import create_logger

from .predictions import PredictionRecord
from .runner import load_records, summarize
from .runner_workspace import _result_to_prediction, load_workspace_run
from .task_adapter import build_task_data

# The decomposed review's checker set (extensible — add a checker = add its task_type).
DECOMPOSED_CHECKERS = [
    "lean_pr_review_golf",  # dominant V2 sub-family
    "lean_pr_review_dup",
    "lean_pr_review_gen",
]


def _checker_tag(task_type: str) -> str:
    return task_type.replace("lean_pr_review_", "")


def _split_task_id(task_id: str) -> Tuple[Optional[str], Optional[int]]:
    """'lean_pr_review_golf_33440' -> ('lean_pr_review_golf', 33440)."""
    try:
        checker, pr = task_id.rsplit("_", 1)
        return checker, int(pr)
    except (ValueError, AttributeError):
        return None, None


def aggregate_pr(
    pr_number: int, checker_preds: List[Tuple[str, PredictionRecord]], model_name: str
) -> PredictionRecord:
    """Merge one PR's per-checker predictions into a composed review. Findings are
    deduped by (path, line, claim-prefix); each carries its source checker(s). The
    composed PR is merge-ready iff no checker surfaced anything."""
    parsed = [(tag, rec) for tag, rec in checker_preds if rec.parse_ok]
    if not parsed:
        errs = "; ".join(f"{tag}:{rec.parse_error}" for tag, rec in checker_preds)
        return PredictionRecord(pr_number=pr_number, model=model_name, mode="workspace",
                                parse_ok=False, parse_error=f"all checkers failed: {errs}"[:2000])

    seen: Dict[Tuple, Any] = {}
    confidences: List[float] = []
    cost = inp = out = 0
    for tag, rec in parsed:
        if rec.confidence is not None:
            confidences.append(rec.confidence)
        cost += rec.cost_usd or 0.0
        inp += rec.input_tokens or 0
        out += rec.output_tokens or 0
        for f in rec.findings:
            a = f.anchor
            key = ((a.path if a else None), (a.line_start if a else None), f.claim.strip()[:80].lower())
            if key in seen:
                existing = seen[key]
                tags = {t for t in (existing.source or "").split("+") if t} | {tag}
                existing.source = "+".join(sorted(tags))
            else:
                seen[key] = f.model_copy(update={"source": tag})

    findings = list(seen.values())
    composed = PredictionRecord(
        pr_number=pr_number, model=model_name, mode="workspace",
        merge_ready_as_is=(len(findings) == 0),
        confidence=(min(confidences) if confidences else None),
        findings=findings, parse_ok=True,
    )
    composed.cost_usd, composed.input_tokens, composed.output_tokens = cost, inp, out
    return composed


def _resolve_output(dataset, model_name: str) -> Path:
    if dataset.output_file:
        return dataset.output_file
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return dataset.output_dir / f"preds_{model_name}_composed_{stamp}.jsonl"


async def run(dataset, scaffold_config, task_config_overrides: Dict[str, Any], logger) -> Optional[Path]:
    model_name = scaffold_config.llm_config.model_name or "model"
    checkers = dataset.checkers or list(DECOMPOSED_CHECKERS)
    records = load_records(dataset)
    logger.info("Composed review: %d PRs × %d checkers (%s), model=%s",
                len(records), len(checkers), ",".join(_checker_tag(c) for c in checkers), model_name)

    if dataset.dry_run:
        for record in records:
            d = build_task_data(record, task_type=checkers[0])
            logger.info("PR #%d: base=%s changed=%d (× %d checkers)",
                        record.pr_number, d.target_workspace.commit_hash[:8], len(d.changed_files), len(checkers))
        return None

    # One task per (PR, checker); each checker rebuilds its own task_config (native
    # tools) from its task_class via create_task_from_data + the shared overrides.
    tasks = []
    for record in records:
        for checker in checkers:
            data = build_task_data(record, task_type=checker)
            tasks.append(create_task_from_data(
                data.model_dump(mode="json"), scaffold_config, task_config_overrides=task_config_overrides))

    model_tag = model_name.replace("_", "").replace(".", "").replace("-", "")
    run_name = dataset.run_name or f"pr_review_composed_{model_tag}_{len(records)}prs"
    orchestrator = TaskOrchestrator(config=scaffold_config, orchestrator_id=run_name, logger=logger)
    results = await orchestrator.run(tasks)

    # Group results by PR, tag each with its checker, aggregate.
    by_pr: Dict[int, List[Tuple[str, PredictionRecord]]] = {}
    for tr in results.task_results:
        data = tr if isinstance(tr, dict) else tr.model_dump(mode="json")
        checker, pr = _split_task_id(str(data.get("task_id") or ""))
        if pr is None:
            continue
        by_pr.setdefault(pr, []).append((_checker_tag(checker or ""), _result_to_prediction(tr, model_name)))

    composed = [aggregate_pr(pr, preds, model_name) for pr, preds in sorted(by_pr.items())]

    output_file = _resolve_output(dataset, model_name)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w") as fh:
        for rec in composed:
            fh.write(json.dumps(rec.model_dump(mode="json"), ensure_ascii=False) + "\n")

    rows = [r.model_dump(mode="json") for r in composed]
    summary = summarize(rows)
    summary["checkers"] = [_checker_tag(c) for c in checkers]
    summary["findings_by_source"] = _source_tally(composed)
    output_file.with_name(output_file.stem + "_summary.json").write_text(json.dumps(summary, indent=2))
    logger.info("Composed summary: %s", summary)
    logger.info("Run dir: %s", orchestrator.workspace_path)
    logger.info("Composed predictions: %s", output_file)
    return output_file


def _source_tally(composed: List[PredictionRecord]) -> Dict[str, int]:
    tally: Dict[str, int] = {}
    for rec in composed:
        for f in rec.findings:
            for tag in (f.source or "?").split("+"):
                tally[tag] = tally.get(tag, 0) + 1
    return tally


def main(config_path: Optional[Path] = None, cli_overrides: Optional[Dict[str, Any]] = None, logger=None):
    logger = logger or create_logger()
    dataset, scaffold_config, task_config_overrides = load_workspace_run(config_path, cli_overrides)
    return asyncio.run(run(dataset, scaffold_config, task_config_overrides, logger))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Composed (decomposed) v2 review — runs the checker set + aggregates")
    parser.add_argument("--config", type=Path, default=None)
    args, remaining = parser.parse_known_args()
    result = main(config_path=args.config, cli_overrides=parse_cli_args(remaining))
    if result:
        print(result)
