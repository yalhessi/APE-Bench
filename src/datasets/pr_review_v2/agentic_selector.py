"""
Agentic selector runner — the tool-grounded counterpart to the diff-only LLM selector.

For each PR in a candidate pool, runs the `lean_pr_review_selector` task: a per-PR triage
agent that materializes the reviewed workspace (merge base + δ₀, read-only), investigates
each pooled candidate finding with tools (read / search / verify), and assigns each a
maintainer-worthiness score 0-100. Scores are mapped back to the candidates and run through
the SAME metrics as selector.py (AUC overall + per hit-stratum + the gold-recall/precision
frontier), so the agentic and diff-only selectors are directly comparable — the decisive
number being `auc_by_hit_stratum.V2`.

Reuses the standard scaffold config + TaskOrchestrator (tasks/<task_id>/ layout, resume,
concurrency), exactly like runner_workspace / review. No new scoring infra.

    python -m src.datasets.pr_review_v2.agentic_selector \
        --config configs/pr_review_selector_v2.yaml pool=grand_union
"""

import argparse
import asyncio
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.orchestration import TaskOrchestrator
from ape.tasks.base import create_task_from_data
from ape.utils import parse_cli_args
from ape.utils.logging import create_logger

from .evaluate_d2 import _pred_span
from .runner_workspace import load_workspace_run
from .schema import PRReviewV2Record
from .selector import (
    GOLD, POOLS, PRED_DIR, build_candidates, compute_result, load_gold, print_summary,
)
from .task_adapter import build_task_data

SELECTOR_TASK = "lean_pr_review_selector"


def _candidate_payload(finding: Dict[str, Any], index: int) -> Dict[str, Any]:
    path, start, end = _pred_span(finding)
    return {
        "index": index,
        "path": path,
        "line_start": start,
        "line_end": end or start,
        "severity": finding.get("severity"),
        "claim": finding.get("claim"),
        "suggested_fix": finding.get("suggested_fix"),
    }


def build_pr_tasks(pool_name, scaffold_config, task_config_overrides, logger):
    """Build one selector task per PR-with-candidates. Returns
    (candidates, gold_to_cands, pr_cand_order, tasks)."""
    gold_raw = load_gold()
    candidates, gold_to_cands, uncached = build_candidates(gold_raw, POOLS[pool_name])
    records = {r.pr_number: r for r in
               (PRReviewV2Record.model_validate(json.loads(l))
                for l in GOLD.read_text().splitlines() if l.strip())}

    by_pr: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for c in candidates:
        by_pr[c["pr"]].append(c)

    pr_cand_order: Dict[int, List[Dict[str, Any]]] = {}
    tasks = []
    for pr, cands in sorted(by_pr.items()):
        record = records.get(pr)
        if record is None:
            logger.warning("PR %d has candidates but no gold record; skipping", pr)
            continue
        d = build_task_data(record, task_type=SELECTOR_TASK).model_dump(mode="json")
        d["candidate_findings"] = [_candidate_payload(c["finding"], i) for i, c in enumerate(cands)]
        pr_cand_order[pr] = cands
        tasks.append(create_task_from_data(
            d, scaffold_config, task_config_overrides=task_config_overrides))
    logger.info("Agentic selector pool=%s: %d candidates over %d PRs, %d on-target, %d uncached labels",
                pool_name, len(candidates), len(pr_cand_order),
                sum(1 for c in candidates if c["on_target"]), uncached)
    return candidates, gold_to_cands, pr_cand_order, tasks


def _assign_scores(results, pr_cand_order, logger) -> int:
    """Map task results' per-index scores back onto candidates. Returns #PRs scored."""
    scored_prs = 0
    for tr in results.task_results:
        data = tr if isinstance(tr, dict) else tr.model_dump(mode="json")
        task_id = str(data.get("task_id") or "")
        try:
            pr = int(task_id.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            continue
        cands = pr_cand_order.get(pr)
        if cands is None:
            continue
        if not data.get("success"):
            logger.warning("PR %d selector task failed: %s", pr, str(data.get("error"))[:160])
            continue
        by_index = {int(s["index"]): float(s["score"])
                    for s in (data.get("scores") or []) if "index" in s}
        for i, c in enumerate(cands):
            c["score"] = by_index.get(i, 0.0)
        scored_prs += 1
    # any candidate whose PR failed / wasn't scored defaults to 0.0
    for cands in pr_cand_order.values():
        for c in cands:
            c.setdefault("score", 0.0)
    return scored_prs


async def run(pool_name, scaffold_config, task_config_overrides, dry_run, logger) -> Optional[Path]:
    model = scaffold_config.llm_config.model_name or "model"
    candidates, gold_to_cands, pr_cand_order, tasks = build_pr_tasks(
        pool_name, scaffold_config, task_config_overrides, logger)

    if dry_run:
        logger.info("[dry-run] %d selector tasks built (pool=%s, model=%s)", len(tasks), pool_name, model)
        return None

    model_tag = model.replace("_", "").replace(".", "").replace("-", "")
    run_name = f"pr_review_selector_{pool_name}_{model_tag}"
    orchestrator = TaskOrchestrator(config=scaffold_config, orchestrator_id=run_name, logger=logger)
    results = await orchestrator.run(tasks)
    n_prs = _assign_scores(results, pr_cand_order, logger)

    result = compute_result(candidates, gold_to_cands, pool_name=pool_name, model=model,
                            mode="agentic", prompt_version="v1", n_scored=n_prs)
    out = PRED_DIR / f"selector_{pool_name}_{model}_agentic.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    logger.info("Run dir (standard tasks/ layout): %s", orchestrator.workspace_path)
    print_summary(result, out)
    return out


def main(config_path: Optional[Path] = None, cli_overrides: Optional[Dict[str, Any]] = None, logger=None):
    logger = logger or create_logger()
    cli_overrides = dict(cli_overrides or {})
    pool_name = cli_overrides.pop("pool", "grand_union")  # pop so scaffold config validation ignores it
    if pool_name not in POOLS:
        raise SystemExit(f"unknown pool {pool_name!r}; choose from {sorted(POOLS)}")
    dataset, scaffold_config, task_config_overrides = load_workspace_run(config_path, cli_overrides)
    return asyncio.run(run(pool_name, scaffold_config, task_config_overrides, dataset.dry_run, logger))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic (tool-grounded) selector over a candidate pool")
    parser.add_argument("--config", type=Path, default=None)
    args, remaining = parser.parse_known_args()
    result = main(config_path=args.config, cli_overrides=parse_cli_args(remaining))
    if result:
        print(result)
