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
    python -m src.mathlib_review.review.cli replay --config configs/r.yaml --of <run> --run-name <n>
    python -m src.mathlib_review.review.cli report routing --run <run_name>

`plan` is `run` without `--execute`, spelled positively, because that is what it is for.

Config overrides go through repeated `--set key=value`. Trailing bare `key=value` tokens
used to work, and the difference is what happens to something that is *not* an override: a
mistyped subcommand or a stray path was indistinguishable from a config key, and the
override parser could only tell them apart by looking for an `=`. Behind a flag, argparse
rejects the leftover and the error names the token.
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
SPENDS = frozenset({"run", "judge", "bench", "replay", "pipeline"})


def _say_nothing_ran(command: str, facts: dict) -> None:
    """Report a preflight so it cannot be read as a completed run.

    On stderr, banner first, and never as a bare JSON object -- `judge` without `--execute`
    printed one, it looked exactly like a result, and it was taken for one.
    """

    width = max(len(f"  {k}: {v}") for k, v in facts.items()) if facts else 40
    line = "=" * max(width, 58)
    print(line, file=sys.stderr)
    print(f"NOTHING RAN. `{command}` is read-only without --execute.", file=sys.stderr)
    print(line, file=sys.stderr)
    for key, value in facts.items():
        print(f"  {key}: {value}", file=sys.stderr)
    print(f"\nAdd --execute to actually run it.", file=sys.stderr)


def _add_run_name(parser: argparse.ArgumentParser) -> None:
    """Which run this is, supplied at the invocation rather than checked into the config.

    A config used to name the run it produced, so every paid repetition needed its own file
    and the file went stale the moment the run was spent -- four still named an already-spent
    run. A config describes a PR set and a policy; `rep2` is not part of either. The judge
    already worked this way (`--of <run_name>`), and this is the generation side of the same
    thing.
    """

    parser.add_argument(
        "--run-name", default=None,
        help="names this run: its results directory, its orchestrator cache key, and the "
             "identity the judge scores it under. Required unless the config sets one.")


def _add_set(parser: argparse.ArgumentParser) -> None:
    """Config overrides, one `--set key=value` each.

    Trailing bare `key=value` tokens worked and are no longer accepted. The difference is what
    happens to something that is *not* an override: as a positional leftover, a mistyped
    subcommand or a stray path was indistinguishable from a config key, and `parse_cli_args`
    could only tell them apart by looking for an `=`. Behind a flag, argparse rejects the
    leftover itself and the error names the token.
    """

    parser.add_argument(
        "--set", action="append", default=[], metavar="KEY=VALUE", dest="overrides",
        help="override a config key, e.g. --set dataset.pr_numbers='[33117]'. Repeatable.")


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
    _add_run_name(plan)
    _add_set(plan)

    run = sub.add_parser("run", help="a generation run")
    run.add_argument("--config", type=Path, required=True)
    _add_run_name(run)
    _add_set(run)
    run.add_argument("--redo", action="store_true",
                     help="discard this run_name's results and state, then run it again")
    run.add_argument("--cost-model", default=None,
                     help="how to read provider token accounting when pricing calls")
    _add_execute(run)

    judge = sub.add_parser("judge", help="score a generation run against gold")
    judge.add_argument("--config", type=Path, required=True)
    _add_set(judge)
    judge.add_argument("--of", dest="of_run", default=None,
                       help="the generation run to score. Derives candidates, out_dir and "
                            "run_name from it, so the three cannot disagree.")
    _add_execute(judge)

    bench = sub.add_parser("bench", help="run one arm against its own bench, with no lead")
    bench.add_argument("--config", type=Path, required=True)
    _add_set(bench)
    bench.add_argument("--arm", action="append", required=True)
    bench.add_argument("--pr", type=int, action="append", dest="pr_numbers")
    bench.add_argument("--negatives-per-pr", type=int, default=3)
    bench.add_argument("--out", type=Path, default=None)
    _add_execute(bench)

    replay = sub.add_parser(
        "replay", help="re-decide recorded arm sessions from just before they submitted")
    replay.add_argument("--config", type=Path, required=True)
    replay.add_argument("--of", dest="of_run", default=None,
                        help="the generation run whose arm sessions are replayed")
    replay.add_argument(
        "--select", default=None,
        metavar="all|arm|invocation_ids|gold-site-abstentions|missed-obligations",
        help="which recorded sessions to re-decide. The two gold-derived selectors read the "
             "judge's verdicts and are sealed into the plan as such: the prefix replayed is "
             "still the recording, so gold reaches no prompt, but the selection is in-sample.")
    replay.add_argument(
        "--cut", default=None, metavar="turn=N|node=I|tool=NAME[:first|:last|:N]",
        help="where the model takes over, replacing the config's cut. `--set dataset.cut=` "
             "would merge with it instead, leaving two spellings, which is refused.")
    _add_run_name(replay)
    _add_set(replay)
    _add_execute(replay)

    pipeline = sub.add_parser(
        "pipeline", help="a declared experiment: one run and the stages that read it")
    pipeline.add_argument("--config", type=Path, required=True)
    _add_run_name(pipeline)
    _add_set(pipeline)
    _add_execute(pipeline)

    adjudicate = sub.add_parser(
        "adjudicate",
        help="label the findings gold cannot judge, and report how many still are not")
    adjudicate.add_argument("--of", dest="of_run", required=True,
                            help="the judged generation run whose off-gold findings to read")
    adjudicate.add_argument("--labels", type=Path, default=None,
                            help="a JSONL file of human labels to add to the store first")

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
    stages = report_sub.add_parser(
        "stages", help="what has happened to this run, and whether its artifacts agree")
    stages.add_argument("--run", required=True)
    buckets = report_sub.add_parser(
        "buckets",
        help="why each gold obligation ended where it did, and what became of every finding")
    buckets.add_argument("--run", action="append", required=True, dest="runs",
                         help="repeatable; several runs add `reps_with_key` per finding")
    buckets.add_argument("--audit", action="store_true",
                         help="read the judge's verdicts too, which is what splits the located "
                              "obligations into COVERED and LOCATED_MISS")
    buckets.add_argument("--replay", default=None,
                         help="a replay run, to annotate each silence with whether it was "
                              "stable under re-sampling")
    scope = report_sub.add_parser(
        "scope", help="recall split by whether the ask is local or requires a design decision")
    scope.add_argument("--audit", type=Path, required=True,
                       help="the judge output directory, holding semantic_report.json")
    scope.add_argument("--release", type=Path, required=True)
    scope.add_argument("--pr", type=int, action="append", dest="pr_numbers")
    conditions = report_sub.add_parser(
        "conditions",
        help="two or more judged runs on one denominator: funnel, union, exclusive sets")
    conditions.add_argument(
        "--condition", action="append", required=True, dest="conditions",
        metavar="LABEL=RUN_NAME[,RUN_NAME...]",
        help="repeatable; audits are derived from the run name the way `judge --of` does")
    conditions.add_argument(
        "--release", type=Path,
        help="adds attention-vs-maintainers and redundancy, which read gold concern labels")

    replay_report = report_sub.add_parser(
        "replay", help="a replay against the decisions it replayed, or against another replay")
    replay_report.add_argument("--run", required=True)
    replay_report.add_argument(
        "--against", default=None,
        help="a baseline replay (normally the null) to pair with, session by session")

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
        _say_nothing_ran("run", {"config": str(args.config),
                                 "run name": getattr(args, "run_name", None) or "(from config)"})
        return _plan(args.config, overrides, logger)

    dataset, scaffold, task_overrides = load_run(args.config, overrides)
    if dataset.dry_run:
        # Same rule as the judge. Generation works today only because its base happens not to
        # set `dry_run`; relying on that is how the judge's `--execute` came to mean nothing.
        logger.info("--execute overrides `dataset.dry_run: true` from the config")
        dataset.dry_run = False
    if args.cost_model:
        scaffold.llm_config.cost_model = args.cost_model
    logger.info("cost model: %s", scaffold.llm_config.cost_model)
    if args.redo:
        redo_run(dataset, logger, scaffold)
    result = asyncio.run(run(dataset, scaffold, task_overrides, logger))
    if result:
        print(result)
    return 0


def _judge(args, overrides, logger) -> int:
    from src.mathlib_review.judge.runner import (
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
        # A success-shaped JSON object was the whole of this, and it read like a result: it
        # was mistaken for a finished judge run, and the absence of an audit directory was
        # the only way to tell. A preflight has to be unmistakable, not merely accurate.
        _say_nothing_ran("judge", {
            "would judge": str(dataset.candidates),
            "into": str(dataset.out_dir),
            "of run": args.of_run or "(from config)",
        })
        return 0

    # `--execute` is the ONE thing that decides whether a command spends. The judge base
    # config carries `dry_run: true`, and it silently outvoted the flag: `judge --execute`
    # built its pairs, called nothing, wrote nothing, and exited 0. Two mechanisms for one
    # decision, which is the defect this branch exists to remove -- so the flag wins, loudly.
    if dataset.dry_run:
        logger.info("--execute overrides `dataset.dry_run: true` from the config")
        dataset.dry_run = False

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


def _replay(args, overrides, logger) -> int:
    """Preflight without `--execute`: select, cut, condition, price, check -- and write nothing."""

    from ape.scaffolds.ape_agent.replay import parse_cut
    from src.mathlib_review.review.replay import load_replay, run_replay

    if args.of_run:
        overrides.setdefault("dataset", {})["of_run"] = args.of_run
    if args.select:
        overrides.setdefault("dataset", {})["selector"] = args.select
    dataset, execution = load_replay(
        args.config, overrides, parse_cut(args.cut) if args.cut else None)
    if not args.execute:
        _say_nothing_ran("replay", {"config": str(args.config), "of run": dataset.of_run,
                                    "run name": dataset.run_name,
                                    "condition": dataset.condition.name,
                                    "cut": dataset.cut.name})
    result = asyncio.run(run_replay(dataset, execution, logger, execute=args.execute))
    if not args.execute:
        print(json.dumps({"sessions": len(result.prefix_sha256_by_invocation),
                          "skipped": len(result.skipped), "sample_count": result.sample_count,
                          "estimate": result.estimate}, indent=2), file=sys.stderr)
    elif result:
        print(result)
    return 0


def _pipeline(args, overrides, logger) -> int:
    """Resolve the whole graph, and with `--execute`, run it.

    Without it: every node's config is opened and hashed and the plan is printed, and nothing
    is written. That rule matters more for a pipeline than for a single verb -- the cost of
    discovering a bad judge config after the generation run is the generation run.
    """

    from src.mathlib_review.review.pipeline import load_pipeline, run as run_pipeline_spec

    if not args.run_name:
        raise SystemExit(
            "--run-name is required: it names the generation run at the root of the pipeline, "
            "and every other stage's run name and audit directory derive from it.")
    # `--set` here targets the GRAPH -- `max_parallel_stages`, or one node's own overrides --
    # not a dataset. The run name is the root's, and it is passed as such rather than merged
    # into a config that has no `dataset` key and would refuse one.
    spec = load_pipeline(args.config, {key: value for key, value in overrides.items()
                                       if key != "dataset"})
    if not args.execute:
        _say_nothing_ran("pipeline", {"config": str(args.config), "root run": args.run_name,
                                      "stages": ", ".join(sorted(spec.stages))})
    summary = asyncio.run(run_pipeline_spec(
        spec, args.run_name, args.config, logger, execute=args.execute))
    if not args.execute:
        print(json.dumps({"plan": summary["plan"], "preflight": summary.get("preflight")},
                         indent=2), file=sys.stderr)
        # Non-zero when a stage would be refused, so a preflight in a script fails rather than
        # printing a refusal nobody reads.
        refused = [name for name, result in (summary.get("preflight") or {}).items()
                   if "refused" in result]
        return 1 if refused else 0
    print(json.dumps(summary, indent=2))
    # Non-zero when any stage did not produce its output, so a pipeline in a script fails the
    # way a command does. The stages that did finish keep their artifacts and their rows.
    return 1 if summary.get("unfinished") else 0


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
    elif args.report_command == "replay":
        from src.mathlib_review.review.replay import compare_replays, load_outcomes, replay_report

        treatment = load_outcomes(args.run)
        print(json.dumps(compare_replays(load_outcomes(args.against), treatment)
                         if args.against else replay_report(treatment), indent=2))
    elif args.report_command == "retrieval":
        from src.mathlib_review.analysis.report import retrieval

        print(json.dumps(retrieval(args.run), indent=2))
    elif args.report_command == "stages":
        from src.mathlib_review.analysis.report import stages as stages_report

        print(json.dumps(stages_report(args.run), indent=2))
    elif args.report_command == "buckets":
        from src.mathlib_review.analysis.report import buckets as buckets_report

        print(json.dumps(
            buckets_report(args.runs, audit=args.audit, replay=args.replay), indent=2))
    elif args.report_command == "conditions":
        from src.mathlib_review.analysis.report import conditions as conditions_report

        pairs: dict = {}
        for item in args.conditions:
            if "=" not in item:
                raise SystemExit(f"--condition wants LABEL=RUN_NAME[,RUN_NAME...], got {item!r}")
            label, names = item.split("=", 1)
            # Several runs under one label are repetitions of one condition. Repeating the
            # flag with the same label does the same thing, so either spelling aggregates.
            pairs.setdefault(label, []).extend(n for n in names.split(",") if n)
        print(json.dumps(conditions_report(pairs, args.release), indent=2))
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
    # `parse_args`, not `parse_known_args`: an unrecognised token is now an error naming the
    # token, rather than something silently handed to the override parser.
    args = parser.parse_args(argv)
    overrides = parse_cli_args(list(getattr(args, "overrides", []) or []))
    if getattr(args, "run_name", None):
        overrides.setdefault("dataset", {})["run_name"] = args.run_name
    logger = create_logger()

    if args.command == "plan":
        return _plan(args.config, overrides, logger)
    if args.command == "run":
        return _run(args, overrides, logger)
    if args.command == "judge":
        return _judge(args, overrides, logger)
    if args.command == "bench":
        return _bench(args, logger)
    if args.command == "replay":
        return _replay(args, overrides, logger)
    if args.command == "pipeline":
        return _pipeline(args, overrides, logger)
    if args.command == "adjudicate":
        from src.mathlib_review.judge.adjudicate import adjudicate_run

        # Not in `SPENDS`: no model runs. A label is in the store or it is not, and the report
        # says how much of the run is still unadjudicated rather than filling the gap.
        print(adjudicate_run(args.of_run, labels=args.labels, logger=logger))
        return 0
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
