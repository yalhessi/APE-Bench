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
SPENDS = frozenset({"score", "run", "judge", "bench", "replay", "pipeline", "match", "session",
                    "study prepare", "study run", "study score"})


def _producer(args) -> int:
    """`producer bench` and `producer context`. Neither calls a model; `context` writes a new file
    and never touches `--base`."""

    from src.mathlib_review.io import jsonl_rows
    from src.mathlib_review.paths import assert_repo_root

    assert_repo_root()
    if args.producer_command == "bench":
        from src.mathlib_review.analysis.producer_bench import bench

        out = bench(args.producer, args.set)
        if args.out is not None:
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / "facts.jsonl").write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in out["fact_rows"]),
                encoding="utf-8")
            summary = {k: v for k, v in out.items() if k != "fact_rows"}
            (args.out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
        print(json.dumps({k: v for k, v in out.items() if k not in ("fact_rows", "located")}, indent=2))
        return 0
    from src.mathlib_review.analysis.probes import load_probe_set
    from src.mathlib_review.producers import change_graphs, context_jsonl, context_rows

    spec = load_probe_set(args.set)
    if args.out.exists():
        raise SystemExit(f"{args.out} exists; a context_file is written once, under a new name")
    graphs = change_graphs(spec.release, spec.pr_numbers)
    rows = context_rows([graphs[pr] for pr in spec.pr_numbers if pr in graphs], args.producers,
                        jsonl_rows(args.base) if args.base else None)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(context_jsonl(rows), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "prs": len(rows),
                      "sections_added": sum(len(r["sections"]) for r in rows)
                      - (sum(len(r["sections"]) for r in jsonl_rows(args.base)) if args.base else 0)},
                     indent=2))
    return 0


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


def _add_stage_input(parser: argparse.ArgumentParser) -> None:
    """The first stage's run, for a chained per-PR design (`DESIGNS[...].reads_stage`).

    The judge's `--of` and this are the same idea: which finished run a stage reads is part of
    the invocation, never of the config. The runner refuses a chained design without it and a
    stage run whose ledgers do not cover the PR set.
    """

    parser.add_argument(
        "--of", dest="of_run", default=None,
        help="for a chained design: the run whose per-PR ledgers this stage reads")


def _add_execute(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--execute", action="store_true",
        help="actually call the model. Without it this does the full preflight and stops.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pr-review", description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    study = sub.add_parser("study", help="paired convention review studies, configured in configs/studies")
    stages = study.add_subparsers(dest="study_action", required=True)
    for action, summary in (
        ("plan", "inspect the reviewer inputs and tool grants using local fixtures"),
        ("prepare", "freeze the shared excerpts, learn conventions and select them for each PR"),
        ("run", "prepare missing selections and generate a paired sample of reviews"),
        ("score", "read a saved sample against its reference feedback"),
    ):
        stage = stages.add_parser(action, help=summary)
        stage.add_argument("study", help="study name in configs/studies or path to a study YAML")
        if f"study {action}" in SPENDS:
            _add_execute(stage)
        if action in ("run", "score"):
            stage.add_argument("--sample", type=int, default=1)
        if action == "prepare":
            stage.add_argument("--retry", action="append", default=[], metavar="STAGE=N")
        if action == "score":
            stage.add_argument("--reading", help="name a new comparison of the same submissions")
            stage.add_argument("--question-form", action="store_true", help="apply the alternative question rubric")

    plan = sub.add_parser("plan", help="render and price a run; call no model")
    _add_run_name(plan)
    _add_stage_input(plan)
    _add_set(plan)

    run = sub.add_parser("run", help="a generation run")
    _add_run_name(run)
    _add_stage_input(run)
    _add_set(run)
    again = run.add_mutually_exclusive_group()
    again.add_argument("--redo", action="store_true",
                       help="discard this run_name's results and state, then run it again")
    again.add_argument("--resume", action="store_true",
                       help="continue this run_name after an interruption, or reopen it if it "
                            "closed partial: sessions that failed on errors are requeued and "
                            "successes kept; refused once a complete run has written its outputs")
    run.add_argument("--cost-model", default=None,
                     help="how to read provider token accounting when pricing calls")
    _add_execute(run)

    from src.mathlib_review.analysis.submissions import SCORERS
    reviewer_names = sorted(p.stem for p in Path("configs/designs/reviewers").glob("*.yaml"))
    for stage in (plan, run):
        source = stage.add_mutually_exclusive_group(required=True)
        source.add_argument("--config", type=Path)
        source.add_argument("--reviewer", choices=reviewer_names, help="a versioned whole-PR reviewer")
        stage.add_argument("--case", metavar="PR@HEAD", help="pinned release revision for --reviewer")
        stage.add_argument("--score", choices=SCORERS, help="score this named review after submission")
    score = sub.add_parser("score", help="score saved submissions without generating reviews")
    score.add_argument("--of", dest="runs", nargs="+", required=True, metavar="RUN")
    score.add_argument("--using", choices=SCORERS, required=True)
    _add_execute(score)

    probe = sub.add_parser("probe", help="the reviewer-model probe on a set (analysis/probes.py)")
    probe_sub = probe.add_subparsers(dest="probe_command", required=True)
    log = probe_sub.add_parser("log-call", help="(the packet wrapper's) record one tool call")
    for name in ("log", "stamp", "tool", "arguments", "out", "status"):
        log.add_argument(name)
    step = {
        "packets": "write reviewer packets (brief, PR, diff, pass-0 model, ptool)",
        "prompts": "print each packet's reviewer prompt",
        "feedback": "extract round-1 feedback; --write refuses while a session is unfinished",
        "readers": "reader folders (batch, rubric) and their prompts",
        "asks": "the agreed asks from two readers' labels",
        "seal": "(historical; new matchings draw it with match-plan --sessions) a fresh blinding of "
                "the named sessions",
        "match-inputs": "(historical; new matchings: match-plan, then cli match or match-import) blind "
                        "matcher inputs and matcher folders under a seal",
        "unblind": "(historical; new matchings: report match) reach per session and condition from the "
                   "matchers' outputs; refuses files that miss cells",
        "audit": "check a transcript stayed in its folder",
        "restore-bases": "restore the PRs' built base snapshots, before a reviewed build",
        "import": "write a session's findings as a scoreable run (anchoring + finalize), for the judge",
        "match-plan": "seal a raw-ask matching: the exact blind inputs, the seal, the batches, the "
                      "measurement identity (analysis/matching.py); calls no model",
        "match-import": "store externally produced matches.json files as a plan's verdicts, "
                        "refused unless they cover every expected cell",
        "session-plan": "seal model sessions over packet folders: every file, the brief, the "
                        "declared outputs (analysis/sessions.py); calls no model",
        "session-import": "store hand-launched sessions' declared outputs beside a session plan",
        "context-derive": "write a solo context_file whose per-PR sections are stored session "
                          "outputs, with its lineage (analysis/sessions.derive_context)",
    }
    parsers = {name: probe_sub.add_parser(name, help=text) for name, text in step.items()}
    for name, sp in parsers.items():
        if name not in ("audit", "session-plan", "session-import", "context-derive"):
            sp.add_argument("--set", required=True, type=Path, help="configs/probe_sets/<name>.yaml")
    for name in ("packets", "prompts", "feedback"):
        parsers[name].add_argument("--sessions", nargs="+", default=["X1", "X2"])
    for name in ("packets", "prompts", "restore-bases"):
        parsers[name].add_argument("--prs", nargs="+", type=int)
    parsers["packets"].add_argument("--scratch", required=True, type=Path,
                                    help="where each session's tool workdir and raw outputs go")
    parsers["packets"].add_argument("--swap-from", metavar="RUN",
                                    help="swap packets: each PR's delivered messages from this solo run, "
                                         "for one session (write_swap_packets)")
    parsers["packets"].add_argument("--conventions", type=Path, metavar="BRIEFS",
                                    help='end each brief with its PR\'s conventions section: a JSON '
                                         '{"prs": {pr: [entry ids]}}, with --codebook (needs --prs)')
    parsers["packets"].add_argument("--codebook", type=Path, help="the census codebook --conventions names entries of")
    parsers["packets"].add_argument("--candidates", type=Path, metavar="BRIEFS",
                                    help='end each brief with its PR\'s pinpointed candidates instead: a JSON '
                                         '{"prs": {pr: [items]}} (probes.load_candidates; needs --prs)')
    parsers["packets"].add_argument("--conventions-from", type=Path,
                                   help="end each brief with the conventions section of its PR's row in a "
                                        "solo context file, byte for byte (probes.context_sections)")
    parsers["packets"].add_argument("--candidates-lead", default="verify",
                                    choices=["verify", "disposition", "ledger"],
                                    help="the candidates section's lead (probes.CANDIDATES_LEADS); "
                                         "verify is stage G's")
    parsers["feedback"].add_argument("--write", action="store_true")
    for name in ("readers", "match-inputs"):
        parsers[name].add_argument("--out", required=True, type=Path)
    parsers["asks"].add_argument("--labels", nargs=2, required=True, type=Path)
    parsers["seal"].add_argument("--sessions", nargs="+", required=True)
    parsers["seal"].add_argument("--prs", nargs="+", type=int,
                                 help="default: the set's PRs that have asks")
    parsers["seal"].add_argument("--out", required=True, type=Path)
    for name in ("match-inputs", "unblind"):
        parsers[name].add_argument("--seal", required=True, type=Path)
    parsers["match-inputs"].add_argument("--sources", required=True, type=Path,
                                         help='JSON {session: {"kind": "claude|solo|lead", "run": ...}}')
    parsers["match-inputs"].add_argument("--question-form", action="store_true",
                                         help="the rubric that judges a question to the author like any "
                                              "finding (probes.MATCHER_RUBRIC_QUESTIONS)")
    parsers["match-inputs"].add_argument("--harness-blind", action="store_true",
                                         help="cut Claude sessions to the solo budget, locate their targets "
                                              "as path:line, and redact the conventions cues (probes.match_inputs)")
    parsers["unblind"].add_argument("--matches", required=True, type=Path,
                                    help="a directory with matches.1.json, matches.2.json, session_stats.json")
    parsers["unblind"].add_argument("--scope", nargs="+", help="families to restrict to")
    parsers["unblind"].add_argument("--allow-incomplete", action="store_true",
                                    help="read matchers' files that miss cells, marked forensic")
    parsers["import"].add_argument("--session", required=True)
    parsers["import"].add_argument("--run-name", required=True,
                                   help="the run directory to write under results/pr_review_v5/runs/")
    parsers["audit"].add_argument("--folder", required=True, type=Path)
    parsers["audit"].add_argument("--transcript", required=True, type=Path)
    mp = parsers["match-plan"]
    mp.add_argument("--name", required=True, help="the plan's id; also its measurement's name")
    mp.add_argument("--out", required=True, type=Path,
                    help="the measurement directory, in the repository: the plan, the verdicts "
                         "and the report live here")
    seal_from = mp.add_mutually_exclusive_group(required=True)
    seal_from.add_argument("--seal", type=Path, help="an existing blinding file")
    seal_from.add_argument("--sessions", nargs="+", help="draw a fresh blinding of these sessions, "
                                                          "written to <out>/seal.json")
    mp.add_argument("--prs", nargs="+", type=int, help="with --sessions: default the set's PRs with asks")
    mp.add_argument("--sources", required=True, type=Path,
                    help='JSON {session: {"kind": "claude|solo|lead|findings_file", "run": ..., '
                         '"path": ...}}')
    mp.add_argument("--ask-packets", type=Path,
                    help="the asks as the study built them, {pr: [ask, ...]}, in place of the set's "
                         "feedback and agreed asks")
    mp.add_argument("--version", default="2-task", choices=["2-task", "1-session"],
                    help="2-task: the matching will run as tasks; 1-session: bind an existing "
                         "hand-launched matching so its matches.json can be imported")
    mp.add_argument("--question-form", action="store_true",
                    help="the rules that judge a question to the author like any finding")
    mp.add_argument("--harness-blind", action="store_true")
    mp.add_argument("--replicates", type=int, default=2, help="independent blind matchers")
    mp.add_argument("--batch-size", type=int, help="PRs a matcher session judges; default all")
    mi = parsers["match-import"]
    mi.add_argument("--plan", required=True, type=Path)
    mi.add_argument("--matches", nargs="+", required=True, type=Path,
                    help="one matches.json per replicate, in replicate order")
    mi.add_argument("--name", required=True, help="names this import in the verdict store")
    mi.add_argument("--executor", nargs="*", default=[], metavar="KEY=VALUE",
                    help="what is known of how they were produced, e.g. model=claude-opus-5-5")
    mi.add_argument("--allow-incomplete", action="store_true",
                    help="store an import that misses cells; its report is then forensic")

    sp_plan = parsers["session-plan"]
    sp_plan.add_argument("--packets", required=True, type=Path,
                         help="a directory holding one folder per session")
    sp_plan.add_argument("--packet-ids", nargs="+", help="only these folders")
    sp_plan.add_argument("--brief", required=True, type=Path,
                         help="the session prompt; {dir} stands for the folder")
    sp_plan.add_argument("--output", action="append", required=True, metavar="NAME[:KIND]",
                         help="a file each session must leave, kind json|jsonl|text. Repeatable")
    sp_plan.add_argument("--name", required=True)
    sp_plan.add_argument("--out", required=True, type=Path)
    sp_plan.add_argument("--replicates", type=int, default=1)
    sp_plan.add_argument("--include", nargs="+", metavar="FILE",
                         help="plan folders sessions already ran in: exactly these files were "
                              "their inputs (outputs and audits beside them are not); a name "
                              "with * ? or [ is a glob, e.g. 'base/**/*.lean'")
    sp_plan.add_argument("--input-from", action="append", default=[],
                         metavar="FILE=PLAN_DIR@PRODUCER[:OUTPUT]",
                         help="this input is an upstream session's stored output (taken from it, "
                              "or with --include checked against it); recorded in lineage.json. "
                              "Repeat a FILE with --include to bind it to whichever of several "
                              "producers holds its bytes")
    sp_plan.add_argument("--upstream-packet", action="append", default=[], metavar="PACKET=UPSTREAM",
                         help="the upstream packet a packet's bound inputs come from, when the ids differ")
    sp_plan.add_argument("--allow-unmatched", action="store_true",
                         help="with --include: plan inputs no upstream observation holds, listed "
                              "with the reason in lineage.json")
    sp_derive = parsers["context-derive"]
    sp_derive.add_argument("--spec", required=True, type=Path,
                           help='JSON {"base", "prs", "sections": [{"title", "lead", "plan_dir", '
                                '"producer", "output", "replicate"?, "by_pr"?}]}')
    sp_derive.add_argument("--out", required=True, type=Path, help="the context file to write")
    sp_import = parsers["session-import"]
    sp_import.add_argument("--plan", required=True, type=Path)
    sp_import.add_argument("--folder", action="append", required=True, metavar="PACKET=FOLDER")
    sp_import.add_argument("--name", required=True)
    sp_import.add_argument("--executor", nargs="*", default=[], metavar="KEY=VALUE")

    session = sub.add_parser("session", help="run a sealed session plan's packets as tasks")
    session.add_argument("--plan", required=True, type=Path)
    session.add_argument("--config", required=True, type=Path,
                         help="the sessions' route, e.g. configs/session/packet_session_opus55_claude_sub.yaml")
    _add_run_name(session)
    _add_set(session)
    _add_execute(session)

    match = sub.add_parser("match", help="run a sealed raw-ask matching's blind matchers as tasks")
    match.add_argument("--plan", required=True, type=Path, help="the measurement directory")
    match.add_argument("--config", required=True, type=Path,
                       help="the matcher's route, e.g. configs/match/ask_match_opus55_claude_sub.yaml")
    _add_run_name(match)
    _add_set(match)
    _add_execute(match)

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
        metavar=("all|arm|invocation_ids|gold-site-abstentions|missed-obligations|"
                 "control-abstentions"),
        help="which recorded sessions to re-decide. The gold-derived selectors read the "
             "judge's verdicts or the release, and are sealed into the plan as such: the "
             "prefix replayed is still the recording, so gold reaches no prompt, but the "
             "selection is in-sample. `control-abstentions` is the guard population -- silent "
             "specialists on PRs the release records no obligation for -- and a condition "
             "measured without it cannot say whether it bought reach or noise.")
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
    adjudicate.add_argument("--silences", type=Path, default=None,
                            help="a JSONL file of hand-made SilenceLabel rows -- why arms said "
                                 "nothing at gold sites -- added to the silence store. Its own "
                                 "store and its own key; `report silences` reads it back")

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
    match_report = report_sub.add_parser(
        "match", help="a matching's numbers, with its measurement identity and coverage")
    match_report.add_argument("--plan", required=True, type=Path)
    match_report.add_argument("--asks", type=Path, help="the set's asks.json, for --scope families")
    match_report.add_argument("--scope", nargs="+", help="families to restrict to")
    match_report.add_argument("--producer", help="read one execution or import of the plan "
                                                 "(task-<run> or import-<name>); required when "
                                                 "the store holds several")
    match_report.add_argument("--producers", nargs="+",
                              help="read several side by side, each judged on its own coverage")
    match_report.add_argument("--replicates", nargs="+",
                              help="read only these observations, e.g. task-r1:1 task-r1:2")
    sessions_report = report_sub.add_parser(
        "sessions", help="a session plan's coverage: per producer, the observations held, missing "
                         "and unreadable")
    sessions_report.add_argument("--plan", required=True, type=Path)
    sessions_report.add_argument("--producer", help="one execution or import (task-<run>, import-<name>)")
    trace = report_sub.add_parser(
        "trace", help="one number followed back to its bytes: a matching cell (--plan --pr --ask "
                      "--session) or a judged obligation (--of --obligation)")
    trace.add_argument("--plan", type=Path, help="a matching's measurement directory")
    trace.add_argument("--pr", type=int)
    trace.add_argument("--ask")
    trace.add_argument("--session")
    trace.add_argument("--producer", help="one execution or import of the matching; default all")
    trace.add_argument("--of", dest="of_run", help="a judged generation run")
    trace.add_argument("--obligation")
    trace.add_argument("--node", default="judge", help="which judgement of the run")
    compare = report_sub.add_parser(
        "compare", help="why two or more results differ: their measurement identities, their runs' "
                        "sealed plans, and what the difference can support")
    compare.add_argument("sources", nargs="+", metavar="LABEL=SOURCE",
                         help="a matching's measurement directory (optionally @<producer>) or a "
                              "judged run's name")
    compare.add_argument("--contrast", nargs="+", default=[],
                         help="what is meant to differ (identity or run-plan fields, e.g. "
                              "model_name evaluation_settings.design); the rest is listed as "
                              "undeclared")
    inputs = report_sub.add_parser(
        "inputs", help="what a run's reviewers were given: the sealed input files, the route, and "
                       "each attempt's stored first messages and tools")
    inputs.add_argument("--run", required=True)
    inputs.add_argument("--pr", type=int)
    inputs.add_argument("--full", action="store_true", help="print the messages whole")
    tools = report_sub.add_parser(
        "tools", help="what every tool call came back with: answered, negative, refused, "
                      "error or env, per tool, from the session transcripts in .ape/runs")
    tools.add_argument("--run", required=True)
    stages = report_sub.add_parser(
        "stages", help="what has happened to this run, and whether its artifacts agree")
    stages.add_argument("--run", required=True)
    token_census = report_sub.add_parser(
        "token-census",
        help="processed tokens per role, and the tokens-per-billed-dollar rate the token "
             "caps were calibrated against; re-run it when the model changes")
    token_census.add_argument("--run", action="append", required=True, dest="runs",
                              help="repeatable; several runs widen the distribution")
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
    silences = report_sub.add_parser(
        "silences",
        help="every gold-site silence beside the ask it is silent about, and its label")
    silences.add_argument("--run", required=True)
    silences.add_argument("--replay", default=None,
                          help="a replay run, to say which silences reproduce and what the "
                               "replayed arms gave as their reason")
    silences.add_argument("--no-audit", dest="audit", action="store_false",
                          help="skip the judge's verdicts; the coarse bucket is then "
                               "LOCATED_UNJUDGED and nothing else changes")
    silences.add_argument("--labels", type=Path, default=None,
                          help="a silence-label store to read instead of the default")

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

    union = report_sub.add_parser(
        "union",
        help="the union of several passes' findings, written as a derived run the judge scores "
             "like any other: identical asks collapse, agreement is a label, nothing is "
             "suppressed. Calls no model.")
    union.add_argument("--runs", required=True, metavar="RUN[,RUN...]",
                       help="the passes, comma-separated: two or more finished runs")
    union.add_argument("--as", dest="derived", required=True,
                       help="the derived run's name; results/pr_review_v5/runs/<name>")
    union.add_argument("--control-pr", type=int, action="append", default=[],
                       dest="control_pr_numbers",
                       help="repeatable; a PR where maintainers asked for nothing, whose "
                            "findings are counted per pass and in the union")
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

    tool = sub.add_parser(
        "tool", help="call one of the arms' own tools outside a run, for probes; calls no model")
    tool.add_argument("name", help="a tool name, `list`, or `describe` (each tool as an arm sees it)")
    tool.add_argument("--episodes", type=Path, required=True,
                      help="an episodes.jsonl holding the PR (a release's input/ or a probe's)")
    tool.add_argument("--pr", type=int, required=True)
    tool.add_argument("--workdir", type=Path, required=True,
                      help="where the reviewed overlay and the context trace are kept")
    tool.add_argument("--run-config", type=Path, required=True,
                      help="the run config whose scaffold (Lean timeouts, axioms) the tools use")
    tool.add_argument("--arguments", default="", help="the tool's arguments, as a JSON object")

    producer = sub.add_parser(
        "producer", help="facts about a PR computed before review (src/mathlib_review/producers); "
                         "calls no model")
    producer_sub = producer.add_subparsers(dest="producer_command", required=True)
    producer_bench = producer_sub.add_parser(
        "bench", help="measure a producer alone on a probe set: facts per PR, control emission, "
                      "asks located (analysis/producer_bench.py)")
    producer_bench.add_argument("--producer", required=True)
    producer_bench.add_argument("--set", type=Path, required=True, help="a configs/probe_sets/*.yaml")
    producer_bench.add_argument("--out", type=Path, default=None,
                                help="a directory for summary.json and facts.jsonl")
    producer_context = producer_sub.add_parser(
        "context", help="write a solo `context_file`: each PR's base sections, then each producer's")
    producer_context.add_argument("--producer", action="append", required=True, dest="producers")
    producer_context.add_argument("--set", type=Path, required=True, help="a configs/probe_sets/*.yaml")
    producer_context.add_argument("--base", type=Path, default=None,
                                  help="an existing context_file whose sections come first (read, never rewritten)")
    producer_context.add_argument("--out", type=Path, required=True)

    return parser


def _plan(config: Path, overrides, logger, *, resume: bool = False,
          of_run: Optional[str] = None) -> int:
    """Render, price and check the budget. Writes nothing and calls nothing.

    `resume` is `run --resume` without `--execute`: the dry run then says what the resume
    would do (continue, or reopen a partial run and requeue which sessions) rather than that
    the name is spent.
    """

    from src.mathlib_review.review.runner import load_run, run

    dataset, scaffold, task_overrides = load_run(config, overrides)
    dataset.dry_run = True
    dataset.stage_input_run = of_run
    asyncio.run(run(dataset, scaffold, task_overrides, logger, resume=resume))
    return 0


def _run(args, overrides, logger) -> int:
    from src.mathlib_review.review.runner import load_run, redo_run, run

    if not args.execute:
        _say_nothing_ran("run", {"config": str(args.config),
                                 "run name": getattr(args, "run_name", None) or "(from config)"})
        return _plan(args.config, overrides, logger, resume=args.resume,
                     of_run=getattr(args, "of_run", None))

    dataset, scaffold, task_overrides = load_run(args.config, overrides)
    dataset.stage_input_run = getattr(args, "of_run", None)
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
    result = asyncio.run(run(dataset, scaffold, task_overrides, logger, resume=args.resume))
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
    elif args.report_command == "match":
        from src.mathlib_review.analysis.matching import report_matching

        families = json.loads(args.asks.read_text()).get("families") if args.asks else None
        producers = [args.producer] if args.producer else args.producers
        try:
            print(json.dumps(report_matching(args.plan, families=families,
                                             scope=set(args.scope) if args.scope else None,
                                             replicates=args.replicates, producers=producers),
                             indent=1))
        except ValueError as error:
            raise SystemExit(str(error))
    elif args.report_command == "sessions":
        from src.mathlib_review.analysis.sessions import session_coverage

        try:
            coverage = session_coverage(args.plan, args.producer)
        except ValueError as error:
            raise SystemExit(str(error))
        print(json.dumps(coverage, indent=1))
        return 0 if all(p["complete"] for p in coverage["producers"].values()) else 1
    elif args.report_command == "trace":
        from src.mathlib_review.analysis.trace import trace_judgment, trace_matching

        if args.plan and not args.of_run and None not in (args.pr, args.ask, args.session):
            print(json.dumps(trace_matching(args.plan, args.pr, args.ask, args.session,
                                            producer=args.producer), indent=1))
        elif args.of_run and args.obligation and not args.plan:
            print(json.dumps(trace_judgment(args.of_run, args.obligation, args.node), indent=1))
        else:
            raise SystemExit("trace a matching cell with --plan --pr --ask --session, or a judged "
                             "obligation with --of --obligation")
    elif args.report_command == "compare":
        from src.mathlib_review.analysis.trace import compare_measurements

        sources = {}
        for item in args.sources:
            label, sep, source = item.partition("=")
            sources[label if sep else item] = source if sep else item
        try:
            print(json.dumps(compare_measurements(sources, args.contrast), indent=1, default=str))
        except ValueError as error:
            raise SystemExit(str(error))
    elif args.report_command == "inputs":
        from src.mathlib_review.analysis.trace import run_inputs

        print(json.dumps(run_inputs(args.run, pr=args.pr, full=args.full), indent=1))
    elif args.report_command == "tools":
        from src.mathlib_review.analysis.tool_outcomes import tool_outcomes

        print(json.dumps(tool_outcomes(args.run), indent=2))
    elif args.report_command == "stages":
        from src.mathlib_review.analysis.report import stages as stages_report

        print(json.dumps(stages_report(args.run), indent=2))
    elif args.report_command == "token-census":
        from src.mathlib_review.analysis.corrections import token_census

        print(json.dumps(token_census(args.runs), indent=2))
    elif args.report_command == "silences":
        from src.mathlib_review.analysis.report import silences as silences_report

        print(json.dumps(silences_report(args.run, replay=args.replay, audit=args.audit,
                                         labels=args.labels), indent=2))
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
    elif args.report_command == "union":
        # Writes a derived run rather than reading one, and is still `report`: it calls no
        # model, and the judge then reads what it wrote like any other run.
        from src.mathlib_review.review.merge import write_union_run

        names = [name for name in args.runs.split(",") if name]
        print(json.dumps(write_union_run(
            names, args.derived, control_pr_numbers=args.control_pr_numbers), indent=2))
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


def _session(args, overrides, logger) -> int:
    """Run a sealed session plan's packets as `packet_session` tasks."""

    from src.mathlib_review.analysis.matching import MatchDatasetConfig
    from src.mathlib_review.analysis.sessions import load_session_plan, run_sessions
    from src.mathlib_review.run_config import load_run

    plan = load_session_plan(args.plan)
    plan_dir = args.plan if args.plan.is_dir() else args.plan.parent
    dataset, scaffold, _task_overrides = load_run(args.config, MatchDatasetConfig, overrides)
    run_name = args.run_name or dataset.run_name
    if not run_name:
        raise SystemExit("name the run: --run-name <name>")
    if not args.execute:
        _say_nothing_ran("session", {
            "plan": f"{plan.plan_id} (brief {plan.brief_sha256[:12]})",
            "would run": f"{len(plan.packets)} session(s) x {plan.replicates} replicate(s)",
            "outputs": ", ".join(o["name"] for o in plan.outputs),
            "route": _route_line(scaffold),
            "into": f".ape/runs/{run_name}, outputs to {plan_dir}/outputs/",
        })
        return 0
    from src.mathlib_review.review.preflight import assert_credentials

    assert_credentials(scaffold)
    import asyncio

    from src.mathlib_review.analysis.matching import task_producer
    from src.mathlib_review.analysis.sessions import session_coverage

    asyncio.run(run_sessions(plan, plan_dir, scaffold, run_name, logger))
    coverage = session_coverage(plan_dir, task_producer(run_name))
    held = coverage["producers"][task_producer(run_name)]
    print(json.dumps({"plan_id": plan.plan_id, "producer": task_producer(run_name), **held}, indent=1))
    return 0 if held["complete"] else 1


def _route_line(scaffold) -> str:
    """The executor a run binding will record, as one line, so a dry run shows what binds."""

    from src.mathlib_review.analysis.matching import executor_of

    executor = executor_of(scaffold)
    line = f"{executor['scaffold']} {executor['model']} at effort {executor['effort']}"
    return line + (f", CLI {executor['cli_version']}" if executor["cli_version"] != "unknown" else "")


def _match(args, overrides, logger) -> int:
    """Run a sealed matching's batches as `lean_pr_review_ask_matching` tasks."""

    from src.mathlib_review.analysis.matching import (
        MatchDatasetConfig, load_plan, plan_dir_of, run_matching, task_payloads,
    )
    from src.mathlib_review.run_config import load_run

    plan = load_plan(args.plan)
    payloads = task_payloads(plan)
    dataset, scaffold, _task_overrides = load_run(args.config, MatchDatasetConfig, overrides)
    run_name = args.run_name or dataset.run_name
    if not run_name:
        raise SystemExit("name the run: --run-name <name> (its orchestrator directory and the "
                         "verdict store's file are named by it)")
    if not args.execute:
        _say_nothing_ran("match", {
            "plan": f"{plan.plan_id} ({plan.identity.instrument}/{plan.identity.instrument_version})",
            "would run": f"{len(payloads)} batch task(s) x {plan.identity.replicates} replicate(s)",
            "cells per replicate": plan.expected_cells,
            "route": _route_line(scaffold),
            "into": f".ape/runs/{run_name}, verdicts to {plan_dir_of(args.plan)}/verdicts/",
        })
        return 0
    from src.mathlib_review.review.preflight import assert_credentials

    assert_credentials(scaffold)
    import asyncio

    rows = asyncio.run(run_matching(plan, plan_dir_of(args.plan), scaffold, run_name, logger))
    print(json.dumps({"plan_id": plan.plan_id, "verdicts": len(rows),
                      "expected": len(payloads) * plan.identity.replicates}, indent=1))
    return 0 if len(rows) == len(payloads) * plan.identity.replicates else 1


def _probe(args, logger) -> int:
    from src.mathlib_review.analysis import probes

    if args.probe_command == "log-call":
        # Called by a packet's `ptool` after every tool call; its stdout is the reviewer's
        # terminal, so it prints nothing.
        probes.log_call(Path(args.log), args.stamp, args.tool, args.arguments, Path(args.out),
                        int(args.status))
        return 0
    if args.probe_command == "audit":
        report = probes.audit_transcript(args.folder, args.transcript)
        print(json.dumps(report, indent=1))
        return 1 if report["flagged"] else 0
    if args.probe_command == "session-plan":
        from src.mathlib_review.analysis.sessions import plan_sessions

        outputs = []
        for item in args.output:
            out_name, _sep, kind = item.partition(":")
            outputs.append({"name": out_name, "kind": kind or "text"})
        inputs_from = {}
        for item in args.input_from:
            file_name, _sep, source = item.partition("=")
            plan_dir, _at, rest = source.partition("@")
            producer, _colon, output = rest.partition(":")
            if not (file_name and plan_dir and producer):
                raise SystemExit(f"--input-from {item!r}: FILE=PLAN_DIR@PRODUCER[:OUTPUT]")
            inputs_from.setdefault(file_name, []).append(
                {"plan_dir": plan_dir, "producer": producer, **({"output": output} if output else {})})
        plan = plan_sessions(args.packets, name=args.name, brief=args.brief.read_text(),
                             outputs=outputs, out_dir=args.out, replicates=args.replicates,
                             packet_ids=args.packet_ids, include=args.include,
                             inputs_from=inputs_from or None,
                             upstream_packets=dict(i.split("=", 1) for i in args.upstream_packet),
                             allow_unmatched=args.allow_unmatched)
        print(json.dumps({"plan": str(args.out), "plan_id": plan.plan_id,
                          "packets": len(plan.packets), "replicates": plan.replicates,
                          "brief_sha256": plan.brief_sha256}, indent=1))
        return 0
    if args.probe_command == "context-derive":
        from src.mathlib_review.analysis.sessions import context_lineage_path, derive_context

        spec = json.loads(args.spec.read_text())
        lineage = derive_context(base=Path(spec["base"]), sections=spec["sections"],
                                 prs=spec["prs"], out=args.out)
        print(json.dumps({"context_file": str(args.out),
                          "lineage": str(context_lineage_path(args.out)),
                          "context_sha256": lineage.context_sha256,
                          "prs": sorted(int(p) for p in lineage.rows),
                          "sections": [s["title"] for s in lineage.sections]}, indent=1))
        return 0
    if args.probe_command == "session-import":
        from src.mathlib_review.analysis.sessions import import_session_outputs, load_session_plan

        plan = load_session_plan(args.plan)
        folders = dict(item.split("=", 1) for item in args.folder)
        rows = import_session_outputs(plan, args.plan if args.plan.is_dir() else args.plan.parent,
                                      {k: Path(v) for k, v in folders.items()}, args.name,
                                      executor=dict(i.split("=", 1) for i in args.executor))
        print(json.dumps({"imported": len(rows), "plan_id": plan.plan_id}, indent=1))
        return 0
    spec = probes.load_probe_set(args.set)
    if args.probe_command == "packets" and args.swap_from:
        if len(args.sessions) != 1:
            raise SystemExit("--swap-from writes one session's packets; name it with --sessions")
        written = probes.write_swap_packets(spec, args.sessions[0], args.scratch.resolve(),
                                            args.swap_from, prs=args.prs)
        print(json.dumps([str(d) for d in written], indent=1))
    elif args.probe_command == "packets":
        if bool(args.conventions) != bool(args.codebook):
            raise SystemExit("--conventions and --codebook go together")
        written = probes.write_packets(
            spec, args.sessions, args.scratch.resolve(), prs=args.prs,
            conventions=probes.load_conventions(args.conventions, args.codebook) if args.conventions else None,
            candidates=probes.load_candidates(args.candidates) if args.candidates else None,
            candidates_lead=args.candidates_lead,
            sections=probes.context_sections(args.conventions_from) if args.conventions_from else None)
        print(json.dumps([str(d) for d in written], indent=1))
    elif args.probe_command == "prompts":
        for pr in args.prs or spec.pr_numbers:
            for session in args.sessions:
                print(json.dumps({"pr": pr, "session": session,
                                  "prompt": probes.session_prompt(spec.session_dir(pr, session))}))
    elif args.probe_command == "feedback":
        feedback = probes.extract_feedback(spec)
        if args.write:
            waiting = probes.unfinished_sessions(spec, args.sessions)
            if waiting:
                raise SystemExit(f"feedback is extracted only after every session has finished; "
                                 f"{len(waiting)} have not: {waiting[:6]}")
            probes.write_json(spec.feedback_file, feedback)
        print(json.dumps({"rows": len(feedback["rows"]), "no_feedback": feedback["no_feedback"],
                          "written": bool(args.write)}))
    elif args.probe_command == "readers":
        batch = probes.reader_batch(json.loads(spec.feedback_file.read_text()), spec.pr_numbers)
        args.out.mkdir(parents=True, exist_ok=True)
        batch_file = args.out / "batch.jsonl"
        batch_file.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in batch))
        for d in probes.judge_folders(args.out, 2, [batch_file], probes.READER_RUBRIC):
            print(json.dumps({"folder": str(d.resolve()),
                              "prompt": probes.READER_PROMPT.format(dir=d.resolve())}))
    elif args.probe_command == "asks":
        feedback = json.loads(spec.feedback_file.read_text())
        a, b = (probes.load_labels(p) for p in args.labels)
        asks = probes.agreed_asks(feedback, a, b, spec.pr_numbers)
        probes.write_json(spec.asks_file, {**asks, "source": f"{args.labels[0]} and {args.labels[1]} agreeing"})
        print(json.dumps({"asks": sum(map(len, asks["asks"].values())), "controls": asks["controls"]}))
    elif args.probe_command == "seal":
        if args.out.exists():
            raise SystemExit(f"{args.out} exists; a seal is written once")
        asks = json.loads(spec.asks_file.read_text())["asks"]
        prs = args.prs or [int(pr) for pr, ids in asks.items() if ids]
        probes.write_json(args.out, probes.seal_labels(prs, args.sessions))
        print(json.dumps({"sealed": str(args.out), "prs": len(prs), "sessions": args.sessions}))
    elif args.probe_command == "match-inputs":
        sources = {k: probes.Source.model_validate(v) for k, v in json.loads(args.sources.read_text()).items()}
        inputs = args.out / "inputs"
        stats = probes.match_inputs(spec, json.loads(spec.feedback_file.read_text()),
                                    json.loads(spec.asks_file.read_text()),
                                    json.loads(args.seal.read_text()), sources, inputs,
                                    harness_blind=args.harness_blind)
        files = sorted(p for p in inputs.iterdir() if p.name != "session_stats.json")
        seal = json.loads(args.seal.read_text())
        reviewers = {len(labels) for labels in seal.values()}
        if len(reviewers) != 1:
            raise SystemExit(f"every sealed PR needs the same number of reviewers, got {sorted(reviewers)}")
        rubric = probes.matcher_rubric(reviewers.pop(), len(seal), probes.MATCHER_RUBRIC_QUESTIONS
                                       if args.question_form else probes.MATCHER_RUBRIC)
        for d in probes.judge_folders(args.out, 2, files, probes.MATCHER_RUBRIC, rubric_text=rubric):
            print(json.dumps({"folder": str(d.resolve()),
                              "prompt": probes.MATCHER_PROMPT.format(dir=d.resolve())}))
        print(json.dumps({"prs": len(stats), "inputs": str(inputs)}))
    elif args.probe_command == "match-plan":
        from src.mathlib_review.analysis.matching import SEAL_FILE, plan_matching

        if args.seal:
            seal_path = args.seal
        else:
            asks = json.loads(spec.asks_file.read_text())["asks"]
            prs = args.prs or [int(pr) for pr, ids in asks.items() if ids]
            seal_path = args.out / SEAL_FILE
            if seal_path.exists():
                raise SystemExit(f"{seal_path} exists; a seal is drawn once")
            probes.write_json(seal_path, probes.seal_labels(prs, args.sessions))
        sources = {k: probes.Source.model_validate(v)
                   for k, v in json.loads(args.sources.read_text()).items()}
        plan = plan_matching(
            spec, name=args.name, seal=json.loads(seal_path.read_text()), seal_path=seal_path,
            sources=sources, out_dir=args.out, version=args.version,
            question_policy="questions" if args.question_form else "request_only",
            replicates=args.replicates, batch_size=args.batch_size,
            harness_blind=args.harness_blind,
            ask_packets=json.loads(args.ask_packets.read_text()) if args.ask_packets else None,
            ask_packets_path=args.ask_packets)
        print(json.dumps({"plan": str(args.out), "plan_id": plan.plan_id,
                          "identity_sha256": plan.identity_sha256, "prs": len(plan.packets),
                          "batches": len(plan.batches), "expected_cells": plan.expected_cells,
                          "replicates": plan.identity.replicates}, indent=1))
    elif args.probe_command == "match-import":
        from src.mathlib_review.analysis.matching import import_matches, load_plan, plan_dir_of

        plan = load_plan(args.plan)
        executor = dict(item.split("=", 1) for item in args.executor)
        rows = import_matches(plan, plan_dir_of(args.plan),
                              {str(n): path for n, path in enumerate(args.matches, start=1)},
                              args.name, executor=executor, allow_incomplete=args.allow_incomplete)
        print(json.dumps({"imported": len(rows), "plan_id": plan.plan_id}, indent=1))
    elif args.probe_command == "import":
        from src.mathlib_review.paths import run_dir
        print(json.dumps(probes.import_probe_session(spec, args.session, run_dir(args.run_name)), indent=1))
    elif args.probe_command == "restore-bases":
        status = probes.restore_bases(spec, args.prs)
        print(json.dumps(status, indent=1))
        return 0 if all(v == "restored" for v in status.values()) else 1
    elif args.probe_command == "unblind":
        from src.mathlib_review.judge.ask_matching import missing_cells

        matches = {m: json.loads((args.matches / f"matches.{m}.json").read_text()) for m in ("1", "2")}
        stats = json.loads((args.matches / "session_stats.json").read_text())
        asks, seal = json.loads(spec.asks_file.read_text()), json.loads(args.seal.read_text())
        scope = set(args.scope) if args.scope else None
        missing = missing_cells(asks, seal, matches, scope)
        if missing and not args.allow_incomplete:
            raise SystemExit("the matchers' files miss cells, which unblind would read as not "
                             "reached: " + "; ".join(f"matcher {m}: {len(v)} ({', '.join(v[:3])})"
                                                     for m, v in missing.items())
                             + ". New matchings: `probe match-plan`, `cli match` or `probe "
                               "match-import`, `report match`. --allow-incomplete reads it "
                               "anyway, marked forensic.")
        out = probes.unblind(asks, seal, matches, stats, scope=scope)
        if missing:
            out = {"forensic": True, "missing_cells": missing, **out}
        print(json.dumps(out, indent=1))
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

    if args.command == "score" or getattr(args, "reviewer", None):
        try:
            if args.command == "score":
                from src.mathlib_review.analysis.submissions import review_directory, score_reviews
                return score_reviews([review_directory(name) for name in args.runs], args.using, execute=args.execute)
            from src.mathlib_review.review.reviewers import run_reviewer
            from src.mathlib_review.review.runner import NoSubmittedReview
            try:
                return run_reviewer(args, logger)
            except NoSubmittedReview as error:
                print(f"NO SUBMITTED REVIEW: {error}", file=sys.stderr)
                return 1
        except (ValueError, FileNotFoundError, FileExistsError) as error:
            parser.error(str(error))
    if args.command in ("plan", "run") and (args.case or args.score):
        parser.error("--case and --score require --reviewer")
    if args.command == "study":
        from src.mathlib_review.review.study import run_study
        try:
            return run_study(args, logger)
        except (ValueError, FileNotFoundError, FileExistsError, BlockingIOError) as error:
            parser.error(str(error))
    if args.command == "plan":
        return _plan(args.config, overrides, logger, of_run=args.of_run)
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
        if args.silences:
            from src.mathlib_review.judge.adjudicate import ingest_silences

            print(json.dumps(ingest_silences(args.silences)))
        print(adjudicate_run(args.of_run, labels=args.labels, logger=logger))
        return 0
    if args.command == "report":
        return _report(args)
    if args.command == "probe":
        return _probe(args, logger)
    if args.command == "match":
        return _match(args, overrides, logger)
    if args.command == "session":
        return _session(args, overrides, logger)
    if args.command == "tool":
        from src.mathlib_review.review.toolbox import main as tool_main

        return tool_main(args)
    if args.command == "producer":
        return _producer(args)
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
