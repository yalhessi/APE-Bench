"""Run one arm against its bench, with no lead and no judge.

    # look at the fixture, spend nothing
    ./ape/bin/python -m src.mathlib_review.analysis.bench_cli \
        --config configs/bases/v5_generation.yaml --arm duplication

    # actually run it
    ./ape/bin/python -m src.mathlib_review.analysis.bench_cli \
        --config configs/bases/v5_generation.yaml --arm duplication --execute

Without `--execute` this prints the fixture and what would run, and makes no model call and no
write. That default is the point: a bench is the cheap way to learn about an arm, and looking
at one should cost nothing.

**Why this exists.** An arm could only be measured by running the whole pipeline and
attributing findings backwards, so learning anything about one arm cost a paid run over every
arm. That is why no arm has ever been investigated on its own, and why a replacement for
`proof_golf` -- a tactic search, a premise selector -- has had no way to prove itself against
the incumbent.

**The payloads are the agenda's own.** Arm task data is built by `build_agenda` and looked up
by `work_unit#arm`, not reassembled here. Rebuilding the per-target maps the submission
contract checks against is how edit confinement quietly stops confining anything, and a bench
that ran an arm on a differently-built payload would not be measuring the arm that runs in
production.

**Gold never enters the run.** The arm receives the same gold-free payload the agenda seals.
The expected obligations are joined afterwards, by the scorer, on the evaluation side.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from src.datasets.pr_review_v4.benches import (
    ArmBench, build_all, coverage_report, gold_anchor_index, score_bench,
)
from src.datasets.pr_review_v4.io import load_jsonl
from src.datasets.pr_review_v4.schema import JudgmentNode

from src.mathlib_review.agenda.registry import ARM_DEFINITIONS


def roster() -> Dict[str, List[str]]:
    """`arm_id -> the concern families it may declare`, from the arm registry."""

    return {item.arm_id: sorted(item.expected_concerns) for item in ARM_DEFINITIONS}


def _payloads_for(bench: ArmBench, dataset, release) -> Dict[str, Dict[str, Any]]:
    """The agenda's own arm payload for each case in the fixture, keyed by work unit."""

    from src.mathlib_review.agenda.agenda import build_agenda

    pr_numbers = sorted({case.pr_number for case in bench.cases})
    _agenda, pool = build_agenda(
        run_name=f"bench-{bench.arm_id}", routing_mode="fanout",
        release=dataset.release, modification_inventory=dataset.modification_inventory,
        pr_numbers=pr_numbers,
        # The floor is a coverage device for a whole review; a bench runs one arm.
        generalist_floor=False,
        use_exposure_index=dataset.use_exposure_index,
        **release,
    )
    # A pool entry *is* the arm's task data -- `_arm_payload` returns the v4 payload with the
    # arm fields added. The nested `task_data` key exists only in the written
    # `arm_pool.jsonl`, which is a different shape.
    wanted = {case.work_unit_id for case in bench.cases}
    return {
        payload["work_unit_id"]: payload
        for payload in pool.values()
        if payload.get("arm_id") == bench.arm_id and payload.get("work_unit_id") in wanted
    }


async def _run_arm(payloads: Dict[str, Dict[str, Any]], scaffold, run_name: str, logger):
    """Run one arm over its cases in a single top-level orchestrator.

    Top-level, not nested: there is no lead here, so none of the wave/tier machinery applies
    and the arm is measured on its own budget.
    """

    from ape.orchestration import TaskOrchestrator
    from ape.tasks.base import create_task_from_data

    tasks, by_task_id = [], {}
    for work_unit_id, data in sorted(payloads.items()):
        task = create_task_from_data(data, scaffold)
        tasks.append(task)
        by_task_id[data["task_id"]] = work_unit_id

    scaffold.execution.run_name = run_name
    results = await TaskOrchestrator(config=scaffold, logger=logger).run(tasks)

    anchors: Dict[str, List[str]] = defaultdict(list)
    errors: Dict[str, str] = {}
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        work_unit_id = by_task_id.get(raw.get("task_id"))
        if not work_unit_id:
            continue
        if raw.get("error"):
            errors[work_unit_id] = str(raw["error"])
        for candidate in raw.get("candidates") or []:
            primary = candidate.get("primary_change_id")
            if primary:
                anchors[work_unit_id].append(primary)
    return dict(anchors), errors, results


def run_benches(*, config, arms, pr_numbers=None, negatives_per_pr=3, out=None,
                execute=False, logger=None) -> int:
    """Build the benches, report coverage, and run them only when told to.

    Split out of `main` so the unified entrypoint calls the same code path with the same
    `--execute` gate rather than reimplementing it -- a second implementation of "does this
    spend money" is the kind of divergence this consolidation exists to remove.
    """

    from ape.utils.logging import create_logger

    from src.mathlib_review.review.runner import load_release, load_run

    logger = logger or create_logger("bench")
    dataset, scaffold, _overrides = load_run(config)
    release = load_release(dataset)

    benches = build_all(dataset.release, roster(), pr_numbers=pr_numbers,
                        negatives_per_pr=negatives_per_pr)
    wanted = set(arms)
    unknown = wanted - set(benches)
    if unknown:
        raise SystemExit(f"unknown arm(s): {sorted(unknown)}; known: {sorted(benches)}")
    benches = {k: v for k, v in benches.items() if k in wanted}

    print(json.dumps(coverage_report(benches), indent=2))

    if not execute:
        total = sum(len(b.cases) for b in benches.values())
        print(f"\n-- no --execute: {total} case(s) across {len(benches)} arm(s) would run. "
              "Nothing was called and nothing was written.")
        return 0

    judgments = load_jsonl(dataset.release / "gold/judgments.jsonl", JudgmentNode)
    scores = {}
    for arm_id, bench in sorted(benches.items()):
        payloads = _payloads_for(bench, dataset, release)
        missing = {case.work_unit_id for case in bench.cases} - set(payloads)
        if missing:
            # An arm is not eligible everywhere, so a case with no rendered payload is a
            # statement about eligibility rather than an error. Say which, and score the rest.
            logger.info("%s: %d of %d case(s) have no rendered payload (arm not eligible "
                        "there); scoring the remaining %d",
                        arm_id, len(missing), len(bench.cases), len(payloads))
        anchors, errors, results = asyncio.run(
            _run_arm(payloads, scaffold, f"bench_{arm_id}", logger))
        score = score_bench(
            bench, anchors,
            gold_anchors_by_unit=gold_anchor_index(bench, judgments),
            errors_by_unit=errors,
        )
        score["cases_not_eligible"] = sorted(missing)
        score["cost"] = round(float(getattr(results, "total_cost", 0.0) or 0.0), 6)
        scores[arm_id] = score
        print(json.dumps(score, indent=2))

    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(scores, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {out}")
    return 0


def main() -> None:
    """Kept so the module stays runnable on its own; the shared path is `run_benches`."""

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", type=Path, required=True,
                        help="a v5 generation config; supplies the release and the model")
    parser.add_argument("--arm", action="append", required=True,
                        help="arm to bench; repeatable")
    parser.add_argument("--pr", type=int, action="append", dest="pr_numbers")
    parser.add_argument("--negatives-per-pr", type=int, default=3)
    parser.add_argument("--out", type=Path, default=None,
                        help="write the score here (only with --execute)")
    parser.add_argument("--execute", action="store_true",
                        help="actually run the arm. Without it this is read-only.")
    args = parser.parse_args()
    raise SystemExit(run_benches(
        config=args.config, arms=args.arm, pr_numbers=args.pr_numbers,
        negatives_per_pr=args.negatives_per_pr, out=args.out, execute=args.execute))


if __name__ == "__main__":
    main()
