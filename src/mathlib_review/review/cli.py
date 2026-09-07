"""One entrypoint for the review pipeline.

Every stage had its own module, its own argument parser and its own idea of what is safe by
default, so running an experiment meant remembering five invocations and which flags each one
needs -- and the flags encode lessons that are easy to forget between runs:

* `runner --dry-run` costs nothing; `runner` with no flag spends. The safe form is the one you
  have to remember to type, so the unsafe one is the default.
* `judge --of <run>` derives the three paths that must agree. Without it they are three
  free-form strings, and in the tree right now they disagree: a config bumped to rep2 while
  its judge still reads rep1.
* `report contamination` has to run **before** spending, and nothing sequences it.

So they are one command with one rule: **nothing that spends money runs without `--execute`.**
Every spending subcommand without it does the full preflight -- renders the agenda, prices it,
checks the budget, reports what would run -- and stops. That is the same work a `--dry-run`
did, made the default rather than a flag, so forgetting a flag costs nothing instead of
spending a budget.

    python -m src.mathlib_review.review.cli plan   --config configs/x.yaml
    python -m src.mathlib_review.review.cli run    --config configs/x.yaml --execute
    python -m src.mathlib_review.review.cli judge  --of <run_name> --config configs/j.yaml --execute
    python -m src.mathlib_review.review.cli bench  --config configs/x.yaml --arm proof_golf --execute
    python -m src.mathlib_review.review.cli report routing --run <run_name>

`plan` is `run` without `--execute`, spelled positively, because that is what it is for.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

#: Subcommands that call a model. Listed once so the gate cannot be added to a new command by
#: remembering to; a command absent from here is asserted to be read-only by the tests.
SPENDS = frozenset({"run", "judge", "bench"})


def _add_execute(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--execute", action="store_true",
        help="actually call the model. Without it this does the full preflight and stops.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pr-review", description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="render and price a run; call no model")
    plan.add_argument("--config", type=Path, required=True)

    run = sub.add_parser("run", help="a generation run")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--redo", action="store_true",
                     help="discard this run_name's results and state, then run it again")
    run.add_argument("--cost-model", default=None,
                     help="how to read provider token accounting when pricing calls")
    _add_execute(run)

    judge = sub.add_parser("judge", help="score a generation run against gold")
    judge.add_argument("--config", type=Path, required=True)
    judge.add_argument("--of", dest="of_run", default=None,
                       help="the generation run to score. Derives candidates, out_dir and "
                            "run_name from it, so the three cannot disagree.")
    _add_execute(judge)

    bench = sub.add_parser("bench", help="run one arm against its own bench, with no lead")
    bench.add_argument("--config", type=Path, required=True)
    bench.add_argument("--arm", action="append", required=True)
    bench.add_argument("--pr", type=int, action="append", dest="pr_numbers")
    bench.add_argument("--negatives-per-pr", type=int, default=3)
    bench.add_argument("--out", type=Path, default=None)
    _add_execute(bench)

    report = sub.add_parser("report", help="read a finished run")
    report_sub = report.add_subparsers(dest="report_command", required=True)
    routing = report_sub.add_parser("routing", help="what the lead did")
    routing.add_argument("--run", required=True)
    score = report_sub.add_parser("score", help="issue and resolution match against gold")
    score.add_argument("--audit", type=Path, required=True)
    score.add_argument("--run")
    contamination = report_sub.add_parser(
        "contamination", help="do any arm instructions quote gold? run before spending")
    contamination.add_argument("--release", type=Path, required=True)
    overlay = report_sub.add_parser("overlay", help="the per-PR review as browsable HTML")
    overlay.add_argument("--run", required=True)
    overlay.add_argument("--audit", type=Path)
    overlay.add_argument("--out", type=Path)
    retrieval = report_sub.add_parser(
        "retrieval", help="which retrieval tool the arms reached for, and what came back")
    retrieval.add_argument("--run", required=True)
    scope = report_sub.add_parser(
        "scope", help="recall split by whether the ask is local or requires a design decision")
    scope.add_argument("--audit", type=Path, required=True,
                       help="the judge output directory, holding semantic_report.json")
    scope.add_argument("--release", type=Path, required=True)
    scope.add_argument("--pr", type=int, action="append", dest="pr_numbers")

    trajectory = sub.add_parser("trajectory", help="extract one run's transcripts")
    trajectory.add_argument("--run", required=True)
    trajectory.add_argument("--ape-root", type=Path, default=None)
    trajectory.add_argument("--tool-result-cap", type=int, default=None)

    return parser


def _plan(config: Path, overrides, logger) -> int:
    """Render, price and check the budget. Writes nothing and calls nothing."""

    from src.mathlib_review.review.runner import load_run, run

    dataset, scaffold, task_overrides = load_run(config, overrides)
    dataset.dry_run = True
    asyncio.run(run(dataset, scaffold, task_overrides, logger))
    return 0


def _run(args, overrides, logger) -> int:
    from src.mathlib_review.review.runner import load_run, redo_run, run

    if not args.execute:
        logger.info("no --execute: preflight only, nothing will be spent")
        return _plan(args.config, overrides, logger)

    dataset, scaffold, task_overrides = load_run(args.config, overrides)
    if args.cost_model:
        scaffold.llm_config.cost_model = args.cost_model
    logger.info("cost model: %s", scaffold.llm_config.cost_model)
    if args.redo:
        redo_run(dataset, logger)
    result = asyncio.run(run(dataset, scaffold, task_overrides, logger))
    if result:
        print(result)
    return 0


def _judge(args, overrides, logger) -> int:
    from src.datasets.pr_review_v4.judge_runner import (
        assert_paths_agree, derive_from_run, load_run, run,
    )

    if args.of_run:
        derived = {k: str(v) for k, v in derive_from_run(args.of_run).items()}
        # An explicit override still wins -- rescoring into a second audit directory is a real
        # thing to want -- and `assert_paths_agree` then checks the result is coherent.
        overrides["dataset"] = {**derived, **(overrides.get("dataset") or {})}
    elif not (overrides.get("dataset") or {}).get("candidates"):
        # The v5 judge configs carry no paths on purpose: `candidates`, `out_dir` and
        # `run_name` are one run identity, and writing it three times is what let a judge
        # score rep1's findings under rep2's name. Say that, rather than letting pydantic
        # report two missing fields with no hint that a flag supplies both.
        raise SystemExit(
            f"{args.config} names no run to score, by design. Pass --of <run_name> to derive "
            "candidates, out_dir and run_name from the generation run, so the three cannot "
            "disagree:\n"
            "  python -m src.mathlib_review.review.cli judge "
            f"--config {args.config} --of <run_name> --execute")
    dataset, scaffold, task_overrides = load_run(args.config, overrides)
    if args.of_run:
        assert_paths_agree(dataset, args.of_run)

    if not args.execute:
        print(json.dumps({
            "would_judge": str(dataset.candidates),
            "into": str(dataset.out_dir),
            "of_run": args.of_run,
            "note": "no --execute: paths resolved and checked, no model called",
        }, indent=2))
        return 0

    out = asyncio.run(run(dataset, scaffold, task_overrides, logger))
    if out:
        print(out)
    return 0


def _bench(args, logger) -> int:
    from src.mathlib_review.analysis.bench_cli import run_benches

    return run_benches(
        config=args.config, arms=args.arm, pr_numbers=args.pr_numbers,
        negatives_per_pr=args.negatives_per_pr, out=args.out,
        execute=args.execute, logger=logger)


def _report(args) -> int:
    from src.mathlib_review.analysis.report import contamination, overlay, routing, score

    if args.report_command == "contamination":
        found = contamination(args.release)
        print(json.dumps(found, indent=2))
        return 0 if found["clean"] else 1
    if args.report_command == "routing":
        print(json.dumps(routing(args.run), indent=2))
    elif args.report_command == "score":
        print(json.dumps(score(args.audit, args.run), indent=2))
    elif args.report_command == "retrieval":
        from src.mathlib_review.analysis.report import retrieval

        print(json.dumps(retrieval(args.run), indent=2))
    elif args.report_command == "scope":
        # The competence question the recall number cannot answer on its own: is the reviewer
        # good, or is the set unusually local? `obligation_scope` has answered it since it was
        # written and nothing could call it.
        from src.mathlib_review.analysis.obligation_scope import scope_report

        print(json.dumps(scope_report(
            Path(args.audit) / "semantic_report.json",
            Path(args.release) / "gold/judgments.jsonl",
            args.pr_numbers), indent=2))
    else:
        print(json.dumps(overlay(args.run, args.audit, args.out), indent=2))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    from ape.utils.config_loader import parse_cli_args
    from ape.utils.logging import create_logger

    parser = build_parser()
    args, rest = parser.parse_known_args(argv)
    overrides = parse_cli_args(rest)
    logger = create_logger()

    if args.command == "plan":
        return _plan(args.config, overrides, logger)
    if args.command == "run":
        return _run(args, overrides, logger)
    if args.command == "judge":
        return _judge(args, overrides, logger)
    if args.command == "bench":
        return _bench(args, logger)
    if args.command == "report":
        return _report(args)
    if args.command == "trajectory":
        from src.mathlib_review.analysis.trajectory import (
            DEFAULT_APE_ROOT, DEFAULT_TOOL_RESULT_CAP, assert_repo_root, write_trajectory,
        )

        assert_repo_root()
        print(json.dumps(write_trajectory(
            args.run,
            args.ape_root if args.ape_root is not None else DEFAULT_APE_ROOT,
            args.tool_result_cap if args.tool_result_cap is not None
            else DEFAULT_TOOL_RESULT_CAP,
        ), indent=2))
        return 0
    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
