"""
Runner for the workspace-grounded distillation task (lean_pr_review_distill).

Runs the distillation task over a set of PRs (a candidate pool's PRs, or an explicit list)
through the standard TaskOrchestrator, and writes the resulting `PRDistillation` artifacts
to a JSONL — the shared resource the selector probe (and later the review agent / checkers)
consume via distillation.load_distillations.

    python -m src.datasets.pr_review_v2.distill_runner \
        --config configs/pr_review_distill_v2.yaml pool=grand_union

`pool` (CLI) picks the PR set from selector.POOLS (the PRs that have candidate findings);
dataset.records supplies the PR inputs for materialization.
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.orchestration import TaskOrchestrator
from ape.tasks.base import create_task_from_data
from ape.utils import parse_cli_args
from ape.utils.logging import create_logger

from .distillation import PRDistillation, DeclDistillation
from .runner_workspace import load_workspace_run
from .schema import PRReviewV2Record
from .selector import GOLD, POOLS, PRED_DIR, build_candidates, load_gold
from .task_adapter import build_task_data

DISTILL_TASK = "lean_pr_review_distill"


def _result_to_artifact(result: Any, pr_fallback: Optional[int]) -> PRDistillation:
    data = result if isinstance(result, dict) else result.model_dump(mode="json")
    pr = data.get("pr_number") or pr_fallback
    if pr is None:
        tid = str(data.get("task_id") or "")
        try:
            pr = int(tid.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            pr = 0
    if not data.get("success", False):
        return PRDistillation(pr_number=pr, parse_ok=False,
                              pr_summary=str(data.get("error") or "unsuccessful")[:300])
    decls = [DeclDistillation.model_validate(d) for d in (data.get("declarations") or [])
             if isinstance(d, dict)]
    return PRDistillation(pr_number=pr, pr_summary=str(data.get("pr_summary") or ""),
                          declarations=decls)


async def run(pool_name, scaffold_config, task_config_overrides, dry_run, logger) -> Optional[Path]:
    model = scaffold_config.llm_config.model_name or "model"
    gold_raw = load_gold()
    cands, _, _ = build_candidates(gold_raw, POOLS[pool_name])
    prs = sorted({c["pr"] for c in cands})
    records = {r.pr_number: r for r in
               (PRReviewV2Record.model_validate(json.loads(l))
                for l in GOLD.read_text().splitlines() if l.strip())}

    tasks, pr_order = [], []
    for pr in prs:
        record = records.get(pr)
        if record is None:
            logger.warning("PR %d in pool but no gold record; skipping", pr)
            continue
        d = build_task_data(record, task_type=DISTILL_TASK).model_dump(mode="json")
        tasks.append(create_task_from_data(d, scaffold_config, task_config_overrides=task_config_overrides))
        pr_order.append(pr)
    logger.info("Distillation runner pool=%s: %d PRs, model=%s", pool_name, len(tasks), model)

    if dry_run:
        logger.info("[dry-run] %d distillation tasks built", len(tasks))
        return None

    model_tag = model.replace("_", "").replace(".", "").replace("-", "")
    run_name = f"pr_review_distill_{pool_name}_{model_tag}"
    orchestrator = TaskOrchestrator(config=scaffold_config, orchestrator_id=run_name, logger=logger)
    results = await orchestrator.run(tasks)

    artifacts = [_result_to_artifact(tr, None) for tr in results.task_results]
    artifacts.sort(key=lambda a: a.pr_number)

    out = PRED_DIR / f"distillations_{pool_name}_{model}.jsonl"
    with out.open("w") as fh:
        for art in artifacts:
            fh.write(art.model_dump_json() + "\n")
    ok = sum(a.parse_ok for a in artifacts)
    n_decls = sum(len(a.declarations) for a in artifacts)
    logger.info("Distillations: %d PRs (%d parse_ok), %d decls -> %s", len(artifacts), ok, n_decls, out)
    logger.info("Run dir: %s", orchestrator.workspace_path)
    print(f"wrote {out}  ({len(artifacts)} PRs, {n_decls} decls)")
    return out


def main(config_path: Optional[Path] = None, cli_overrides: Optional[Dict[str, Any]] = None, logger=None):
    logger = logger or create_logger()
    cli_overrides = dict(cli_overrides or {})
    pool_name = cli_overrides.pop("pool", "grand_union")
    if pool_name not in POOLS:
        raise SystemExit(f"unknown pool {pool_name!r}; choose from {sorted(POOLS)}")
    dataset, scaffold_config, task_config_overrides = load_workspace_run(config_path, cli_overrides)
    return asyncio.run(run(pool_name, scaffold_config, task_config_overrides, dataset.dry_run, logger))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Workspace-grounded PR distillation runner")
    parser.add_argument("--config", type=Path, default=None)
    args, remaining = parser.parse_known_args()
    result = main(config_path=args.config, cli_overrides=parse_cli_args(remaining))
    if result:
        print(result)
