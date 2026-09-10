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

from src.mathlib_review.analysis.benches import (
    ArmBench, build_all, coverage_report, gold_anchor_index, score_bench,
)
from src.mathlib_review.io import load_jsonl
from src.mathlib_review.schema import JudgmentNode

from src.mathlib_review.agenda.registry import ARM_DEFINITIONS


def roster() -> Dict[str, List[str]]:
    """`arm_id -> the concern families it may declare`, from the arm registry."""

    return {item.arm_id: sorted(item.expected_concerns) for item in ARM_DEFINITIONS}


def _payloads_for(bench: ArmBench, dataset, release,
                  procedure_variant: str = "baseline") -> Dict[str, Dict[str, Any]]:
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
        procedure_variant=procedure_variant,
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

    # `orchestrator_id`, not `scaffold.execution.run_name`: `ExecutionConfig` has no such
    # field and pydantic refuses the assignment, so `--execute` raised before reaching a model
    # every time it was tried. The whole execute path had never run. The v5 runner names its
    # orchestrator the same way (`runner.py`), which is also what puts the scratch tree at
    # `runs_base_dir / <run_name>` where the trajectory extractor looks for it.
    results = await TaskOrchestrator(
        config=scaffold, orchestrator_id=run_name, logger=logger).run(tasks)

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


#: Billed cost a bench may reach before it is refused, in dollars. Measured on
#: `pr5_smoke4_rep9`: specialists billed a median $0.039 and a max $0.117, so a 16-case bench
#: has a realistic ceiling near $2 and this is roughly 4x it.
DEFAULT_BENCH_COST_CAP = 8.00


def bench_run_name(arm_id: str, procedure_variant: str, attempt: int) -> str:
    """The orchestrator id for one bench attempt.

    It has to carry the variant AND the attempt, because the name is the orchestrator's
    *resume key*. `bench_{arm}` alone meant that a second attempt found every task already
    complete and returned it from cache: five runs of this bench produced two distinct results
    and four no-ops, with costs identical to the microdollar and four of them paid for
    nothing. Only the prompt change saved the variants from collapsing into each other too --
    a different prompt is a different task id.
    """

    return f"bench_{arm_id}_{procedure_variant}_a{attempt}"


def assert_scratch_is_unused(run_name: str, scaffold, *, resume: bool, logger) -> None:
    """Refuse a bench whose orchestrator state already exists, before spending anything.

    The same discipline as `review.runner.guard_run_name`, which documents the hazard this
    path was missing: every attempt that already succeeded is returned from cache, so the
    change under test never executes and the run reports the old behaviour as if it were new.
    """

    from src.mathlib_review.review.runner import _scratch_dirs

    existing = [item for item in _scratch_dirs(run_name, scaffold) if item.is_dir()]
    if not existing:
        return
    if resume:
        logger.warning(
            "resuming %s from %s -- completed cases will NOT be re-run and this is not an "
            "independent attempt", run_name, ", ".join(str(item) for item in existing))
        return
    raise SystemExit(
        f"orchestrator state for {run_name!r} already exists "
        f"({', '.join(str(item) for item in existing)}). That name is a resume key: rerunning "
        "it returns the completed cases from cache, so the result would be a copy of the "
        "earlier attempt rather than a new sample. Use --attempt N for an independent "
        "attempt, or --resume to continue this one deliberately."
    )


def estimate_cost(benches, *, per_case: float) -> float:
    """Worst-case billed spend, as `cases x the per-task ceiling`.

    A ceiling, not a forecast: it assumes every case exhausts its budget, which no run has
    done. It exists so the refusal below happens before the first model call rather than
    after the last one.
    """

    return sum(len(bench.cases) for bench in benches.values()) * per_case


def run_benches(*, config, arms, pr_numbers=None, negatives_per_pr=3, out=None,
                selector="audited", cost_cap=DEFAULT_BENCH_COST_CAP,
                procedure_variant="baseline", attempt=1, resume=False,
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

    # `audited` by default: the gold-label rule gives `family_design` one positive case in
    # the whole release and `proof_idiom` three, and floods `style` with twelve that belong to
    # other arms. A bench meant to test a conclusion has to be selected from the audited
    # request groups. `--selector gold_label` reproduces the old fixture for comparison.
    benches = build_all(dataset.release, roster(), pr_numbers=pr_numbers,
                        negatives_per_pr=negatives_per_pr, selector=selector)
    wanted = set(arms)
    unknown = wanted - set(benches)
    if unknown:
        raise SystemExit(f"unknown arm(s): {sorted(unknown)}; known: {sorted(benches)}")
    benches = {k: v for k, v in benches.items() if k in wanted}

    print(json.dumps(coverage_report(benches), indent=2))

    # The per-task ceiling the arms will actually run under, from the config rather than a
    # number restated here — a second copy of a budget is how a cap stops matching the thing
    # it caps.
    per_case = float(getattr(dataset, "standard_budget_cap", 0.30) or 0.30)
    projected = estimate_cost(benches, per_case=per_case)

    if not execute:
        total = sum(len(b.cases) for b in benches.values())
        print(f"\n-- no --execute: {total} case(s) across {len(benches)} arm(s) would run, "
              f"at most ${projected:.2f} billed (${per_case:.2f} per case). "
              "Nothing was called and nothing was written.")
        return 0

    # Refused before the first model call, not reported after the last one. This project has
    # already lost a paid run to a spend gate that printed a number instead of stopping.
    if cost_cap is not None and projected > cost_cap:
        raise SystemExit(
            f"this bench could bill up to ${projected:.2f} "
            f"({sum(len(b.cases) for b in benches.values())} cases x ${per_case:.2f}), over "
            f"the ${cost_cap:.2f} cap. Narrow it with --pr/--arm, or raise --cost-cap "
            "deliberately."
        )

    judgments = load_jsonl(dataset.release / "gold/judgments.jsonl", JudgmentNode)
    scores = {}
    for arm_id, bench in sorted(benches.items()):
        payloads = _payloads_for(bench, dataset, release, procedure_variant)
        missing = {case.work_unit_id for case in bench.cases} - set(payloads)
        if missing:
            # An arm is not eligible everywhere, so a case with no rendered payload is a
            # statement about eligibility rather than an error. Say which, and score the rest.
            logger.info("%s: %d of %d case(s) have no rendered payload (arm not eligible "
                        "there); scoring the remaining %d",
                        arm_id, len(missing), len(bench.cases), len(payloads))
        run_name = bench_run_name(arm_id, procedure_variant, attempt)
        assert_scratch_is_unused(run_name, scaffold, resume=resume, logger=logger)
        anchors, errors, results = asyncio.run(
            _run_arm(payloads, scaffold, run_name, logger))
        score = score_bench(
            bench, anchors,
            gold_anchors_by_unit=gold_anchor_index(bench, judgments),
            errors_by_unit=errors,
        )
        score["cases_not_eligible"] = sorted(missing)
        score["cost"] = round(float(getattr(results, "total_cost", 0.0) or 0.0), 6)
        # Which rung this is. Recorded on the score so a result file can never be read as
        # the wrong treatment; the prompt hash in the payload says the same thing, less
        # legibly.
        score["procedure_variant"] = procedure_variant
        # A variant carrying gold-derived material measures what the arm *can* do, not what it
        # would do unaided. Stamped here so a score file can never be quoted as performance.
        from ape.tasks.lean_tasks.formal_math.review.focused_prompts import is_oracle_variant

        score["oracle_variant"] = is_oracle_variant(procedure_variant)
        if score["oracle_variant"]:
            score["note_oracle"] = (
                "GOLD-DERIVED ORACLE. This variant's supplement names a tactic taken from the "
                "maintainer's own comment on a PR in the burned development set. The result is "
                "a capability measurement and must not be reported as review performance."
            )
        score["attempt"] = attempt
        score["run_name"] = run_name
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
    parser.add_argument("--selector", choices=("audited", "gold_label"), default="audited",
                        help="how positives are chosen; see build_all")
    parser.add_argument("--cost-cap", type=float, default=DEFAULT_BENCH_COST_CAP,
                        help="refuse before running if the worst case exceeds this")
    parser.add_argument("--procedure-variant", default="baseline",
                        help="named procedure supplement for the treated arms; "
                             "`baseline` is the prompts as written")
    parser.add_argument("--attempt", type=int, default=1,
                        help="which independent attempt this is; part of the resume key, so "
                             "repeats MUST increment it or they return the first from cache")
    parser.add_argument("--resume", action="store_true",
                        help="continue an existing attempt instead of refusing it. Completed "
                             "cases are not re-run, so the result is not a new sample.")
    parser.add_argument("--out", type=Path, default=None,
                        help="write the score here (only with --execute)")
    parser.add_argument("--execute", action="store_true",
                        help="actually run the arm. Without it this is read-only.")
    args = parser.parse_args()
    raise SystemExit(run_benches(
        config=args.config, arms=args.arm, pr_numbers=args.pr_numbers,
        negatives_per_pr=args.negatives_per_pr, out=args.out, execute=args.execute,
        selector=args.selector, cost_cap=args.cost_cap,
        procedure_variant=args.procedure_variant, attempt=args.attempt,
        resume=args.resume))


if __name__ == "__main__":
    main()
