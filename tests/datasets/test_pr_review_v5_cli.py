"""One entrypoint, and one rule: nothing that spends money runs without `--execute`.

Five stages, five parsers, five ideas of what is safe by default. Running an experiment meant
remembering which flag each one needs, and the flags encode lessons that are easy to forget
between runs:

* `runner --dry-run` costs nothing and `runner` alone spends, so the safe form is the one you
  have to remember to type;
* `judge --of <run>` derives the three paths that must agree, and without it they are three
  free-form strings that in this tree *do* disagree -- a config bumped to rep2 while its judge
  still reads rep1;
* `report contamination` has to run before spending and nothing sequences it.

The user's words for this: "we have to make many calls repeatedly, often messing up command
line args by forgetting certain lessons we learned from prior experience."
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.review import cli

CONFIG = Path("configs/pr_review_v5_specialist4.yaml")


def test_every_spending_subcommand_has_an_execute_gate():
    """Structural, so a new subcommand cannot be added without one. `SPENDS` is the list;
    this checks the list is honoured rather than merely written down."""

    parser = cli.build_parser()
    subparsers = [action for action in parser._actions
                  if isinstance(action, __import__("argparse")._SubParsersAction)][0]
    for name in cli.SPENDS:
        assert name in subparsers.choices, f"{name} is listed as spending but has no parser"
        options = {s for action in subparsers.choices[name]._actions
                   for s in action.option_strings}
        assert "--execute" in options, f"{name} spends money and has no --execute gate"


def test_read_only_subcommands_have_no_execute_flag():
    """A gate on a command that cannot spend teaches the flag is decorative, which is how it
    stops being read as a warning."""

    parser = cli.build_parser()
    subparsers = [action for action in parser._actions
                  if isinstance(action, __import__("argparse")._SubParsersAction)][0]
    for name, sub in subparsers.choices.items():
        if name in cli.SPENDS:
            continue
        options = {s for action in sub._actions for s in action.option_strings}
        assert "--execute" not in options, f"{name} does not spend but offers --execute"


def test_plan_is_run_without_execute_spelled_positively():
    parser = cli.build_parser()
    args = parser.parse_args(["plan", "--config", str(CONFIG)])
    assert args.command == "plan"
    assert not hasattr(args, "execute")


def test_run_defaults_to_not_executing():
    args = cli.build_parser().parse_args(["run", "--config", str(CONFIG)])
    assert args.execute is False


# --- the gate actually holds ---------------------------------------------------------------


def test_run_without_execute_calls_no_model(monkeypatch):
    """And does the whole preflight, so forgetting the flag costs a render, not a budget."""

    seen = {}

    def _fake_run(dataset, scaffold, task_overrides, logger):
        seen["dry_run"] = dataset.dry_run
        return None

    import src.mathlib_review.review.runner as runner

    async def _async(*a, **k):
        return _fake_run(*a, **k)

    monkeypatch.setattr(runner, "run", _async)
    assert cli.main(["run", "--config", str(CONFIG)]) == 0
    assert seen["dry_run"] is True, "the preflight must run, and must run as a dry run"


def test_run_with_execute_does_not_force_dry_run(monkeypatch):
    seen = {}

    import src.mathlib_review.review.runner as runner

    async def _async(dataset, scaffold, task_overrides, logger):
        seen["dry_run"] = dataset.dry_run
        return None

    monkeypatch.setattr(runner, "run", _async)
    assert cli.main(["run", "--config", str(CONFIG), "--execute"]) == 0
    assert seen["dry_run"] is False


def test_judge_without_execute_resolves_paths_and_stops(monkeypatch, capsys):
    """The resolution is the valuable half: it is where a judge pointed at the wrong run is
    caught, and it costs nothing."""

    import src.mathlib_review.judge.runner as judge_runner

    called = {"ran": False}

    async def _never(*a, **k):
        called["ran"] = True

    monkeypatch.setattr(judge_runner, "run", _never)
    code = cli.main(["judge", "--config", "configs/pr_review_v5_specialist4_judge.yaml",
                     "--of", "pr_review_v5_specialist4_rep1"])
    assert code == 0
    assert called["ran"] is False
    # Reported on stderr as a banner rather than as a result-shaped object, so it cannot be
    # read as a finished judge run. It was, once.
    err = capsys.readouterr().err
    assert "NOTHING RAN" in err
    assert "pr_review_v5_specialist4_rep1/findings.jsonl" in err
    assert "audits/specialist4-rep1" in err


def test_judge_of_a_run_that_disagrees_with_the_config_is_refused(monkeypatch):
    """The live mistake, caught before `--execute` is even considered."""

    with pytest.raises(ValueError) as excinfo:
        cli.main(["judge", "--config", "configs/pr_review_v5_specialist4_judge.yaml",
                  "--of", "pr_review_v5_specialist4_rep1",
                  "--set", "dataset.candidates=results/pr_review_v5/runs/"
                  "pr_review_v5_lead_heldout11_rep2/findings.jsonl"])
    assert "attribute one run's findings to another" in str(excinfo.value)


def test_bench_shares_one_implementation_of_the_gate():
    """`bench_cli.main` and `cli bench` must not each decide what `--execute` means."""

    import inspect

    from src.mathlib_review.analysis import bench_cli

    assert "run_benches" in inspect.getsource(bench_cli.main)
    assert "run_benches" in inspect.getsource(cli._bench)


def test_the_help_text_names_the_rule():
    """Someone reading `--help` after a break should not have to remember it."""

    assert "--execute" in cli.__doc__
    assert "nothing that spends money" in cli.__doc__.lower()


# --- the config backlog --------------------------------------------------------------------
#
# 64 tracked configs, 7 v5 ones naming an already-spent run, 2 using `extends:`. Each config
# restated ~15 keys identical to every other, so a change to the shared policy meant editing
# nine files and the ones you forgot silently kept the old value.


def _v5_configs(suffix=""):
    return sorted(Path("configs").glob(f"pr_review_v5*{suffix}.yaml"))


def test_every_v5_config_extends_a_base():
    """The measure of whether this stayed fixed. A config that restates the shared policy is
    a config that will drift from it."""

    for path in _v5_configs():
        text = path.read_text(encoding="utf-8")
        assert "extends:" in text, f"{path} restates the base instead of extending it"


def test_no_v5_config_is_longer_than_its_own_deltas_plus_its_reasoning():
    """A soft ceiling, and the point of the exercise: 84 lines became 25. What is left in a
    config should be what that run varies, plus why."""

    import yaml

    for path in _v5_configs():
        body = yaml.safe_load(path.read_text(encoding="utf-8"))
        body.pop("extends", None)
        leaves = sum(len(v) if isinstance(v, dict) else 1 for v in body.values())
        assert leaves <= 8, f"{path} sets {leaves} keys; is it varying all of them?"


def test_no_v5_judge_config_names_a_run():
    """`candidates`, `out_dir` and `run_name` are one identity written three times. They
    disagreed: medium_heldout was bumped to rep2 while its judge still read rep1."""

    for path in _v5_configs("_judge"):
        text = path.read_text(encoding="utf-8")
        for field in ("candidates:", "out_dir:", "run_name:"):
            assert f"  {field}" not in text, (
                f"{path} writes {field} — `judge --of <run_name>` derives it")


def test_judging_without_of_says_what_to_do():
    """Not two missing pydantic fields with no hint that one flag supplies both."""

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["judge", "--config", "configs/pr_review_v5_specialist4_judge.yaml"])
    message = str(excinfo.value)
    assert "--of" in message and "cannot disagree" in message


def test_nothing_asks_for_a_tool_that_cannot_register():
    """`code_references` has no registration -- the provider block is commented out, and it
    was removed from `SUPPORTED_TOOLS` with a measurement behind it (0 attempts across a full
    11-PR run). 24 configs and a dozen per-task tool lists went on naming it: "a capability
    granted to nothing, readable as coverage that is not there".

    The provider itself is exempt: it carries the commented-out block and the measurement
    that justifies keeping the record.
    """

    for path in sorted(Path("configs").glob("*.yaml")):
        assert "code_references" not in path.read_text(encoding="utf-8"), path

    for path in sorted(Path("src").rglob("*.py")):
        if "toolkits/code/" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            if "code_references" not in line:
                continue
            assert line.lstrip().startswith("#"), f"{path}:{number} asks for it: {line!r}"


def test_no_prompt_offers_the_model_a_tool_it_does_not_have():
    """The half that did real harm. The `api_reuse` arm's prompt named `code_references` in
    the sentence telling it how to search before making a claim, and the shared capability
    line advertised "navigate declarations (hover/goto/references)" to every task in every
    generation."""

    from ape.tasks.lean_tasks.formal_math.review import base
    from ape.tasks.lean_tasks.formal_math.review import focused_prompts

    for module in (focused_prompts, base):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "hover/goto/references" not in source, module.__name__
        for line in source.splitlines():
            if "`code_references`" in line:
                assert line.lstrip().startswith("#"), f"{module.__name__}: {line!r}"


def test_the_generation_base_carries_the_measurements_behind_its_caps():
    """They lived in smoke4's copy of the values. Deleting the copy would have deleted the
    only record of why 0.30 and 1.00 are those numbers."""

    text = Path("configs/bases/v5_generation.yaml").read_text(encoding="utf-8")
    assert "median $0.039" in text
    assert "median $0.094" in text


def test_the_scope_report_is_reachable():
    """`obligation_scope` classifies each gold ask as answerable by editing a site (`local`)
    or as requiring a decision about what should exist (`design`). It was written to test a
    specific claim -- that this reviewer is competent at local asks and structurally unable to
    reach design ones -- and nothing could call it, so the claim stayed untested.

    It was also the only module in the three review packages that no entrypoint and no test
    reached.
    """

    parser = cli.build_parser()
    args = parser.parse_args(["report", "scope", "--audit", "a", "--release", "r"])
    assert args.report_command == "scope"


def test_the_scope_report_is_read_only():
    """It reads a finished audit. Nothing it does can spend."""

    assert "report" not in cli.SPENDS


def test_the_retrieval_report_is_reachable_and_read_only():
    """The question a recall number cannot answer: which of its three retrieval tools an arm
    actually reached for, and what came back. 83% of 2,024 calls across thirteen runs went to
    `declaration_search`, which returns nothing but "X is declared in file Y"."""

    args = cli.build_parser().parse_args(["report", "retrieval", "--run", "r"])
    assert args.report_command == "retrieval"
    assert "report" not in cli.SPENDS


def test_the_retrieval_report_separates_the_tools_and_the_arms():
    """Per tool because the empty rate means a different thing for each; per arm because the
    grant is per arm, and that is how you see whether an arm uses what it was given."""

    from src.mathlib_review.analysis.report import retrieval

    found = retrieval("pr_review_v5_specialist4_rep1")
    assert found["calls"] > 0
    assert set(found["by_tool"]) <= {
        "declaration_search", "precedent_search", "zulip_search", "lean_verify_edit", "?"}
    assert all("empty_rate" in stats for stats in found["by_tool"].values())
    assert found["by_arm"], "per-arm rows are the point of the grant being per arm"


def test_the_retrieval_report_counts_calls_that_declared_no_gate():
    """Runs made before gates were recorded have none, and a modern run should have one on
    every row -- a row without one is a tool added without saying how it is bounded."""

    from src.mathlib_review.analysis.report import retrieval

    found = retrieval("pr_review_v5_specialist4_rep1")
    assert "calls_without_a_recorded_gate" in found


# --- overrides go through a flag ------------------------------------------------------------


def test_overrides_are_a_repeatable_flag():
    args = cli.build_parser().parse_args(
        ["plan", "--config", str(CONFIG),
         "--set", "dataset.pr_numbers=[33117]", "--set", "dataset.lead_cost_cap=2.0"])
    assert args.overrides == ["dataset.pr_numbers=[33117]", "dataset.lead_cost_cap=2.0"]


def test_a_stray_token_is_an_error_that_names_it():
    """It used to be handed to the override parser, which could only tell a mistyped
    subcommand from a config key by looking for an `=`. `parse_cli_args` raising on a token
    without one was the guard; a flag makes argparse reject the token itself and say which."""

    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["plan", "--config", str(CONFIG), "oops"])


def test_every_config_taking_command_accepts_overrides():
    """A command that reads a config but cannot be overridden sends you back to editing the
    config, which is the thing `extends:` exists to stop."""

    import argparse

    parser = cli.build_parser()
    sub = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)][0]
    for name, command in sub.choices.items():
        options = {s for action in command._actions for s in action.option_strings}
        if "--config" in options:
            assert "--set" in options, f"{name} takes a config but not --set"


# --- the run name is an invocation argument --------------------------------------------------
#
# Configs used to name the run they produced, so every paid repetition needed its own file and
# the file went stale the moment the run was spent. Four still named an already-spent run.


def test_no_generation_config_names_a_run():
    """A config describes a PR set and a policy. `rep2` is part of neither."""

    for path in _v5_configs():
        if "judge" in path.name:
            continue
        assert "  run_name:" not in path.read_text(encoding="utf-8"), path


def test_plan_and_run_take_a_run_name():
    for command in ("plan", "run"):
        args = cli.build_parser().parse_args(
            [command, "--config", str(CONFIG), "--run-name", "some_run"])
        assert args.run_name == "some_run"


def test_an_unnamed_run_is_refused_before_anything_is_rendered():
    """The sentinel matters more than the flag. A real default means a config that forgets to
    name its run lands on top of whatever ran under the default last."""

    from src.mathlib_review.review.runner import V5DatasetConfig, assert_run_is_named

    unnamed = V5DatasetConfig(
        release=Path("inputs/pr_review_v4/releases/dev-medium-0.3.0"),
        modification_inventory=Path("x"))
    assert unnamed.run_name == "UNNAMED"
    with pytest.raises(ValueError) as excinfo:
        assert_run_is_named(unnamed)
    message = str(excinfo.value)
    assert "--run-name" in message
    assert "cache key" in message


def test_a_named_run_passes():
    from src.mathlib_review.review.runner import V5DatasetConfig, assert_run_is_named

    named = V5DatasetConfig(
        release=Path("inputs/pr_review_v4/releases/dev-medium-0.3.0"),
        modification_inventory=Path("x"), run_name="pr_review_v5_specialist4_rep2")
    assert assert_run_is_named(named) is None


def test_a_preflight_cannot_be_mistaken_for_a_completed_run(capsys):
    """`judge` without `--execute` printed a success-shaped JSON object, it read like a
    result, and it was taken for one -- the only signal that nothing had happened was the
    absence of an audit directory.

    Banner on stderr, and never a bare JSON object: a preflight has to be unmistakable rather
    than merely accurate.
    """

    cli.main(["judge", "--config", "configs/pr_review_v5_specialist4_judge.yaml",
              "--of", "pr_review_v5_specialist4_rep1"])
    captured = capsys.readouterr()
    assert "NOTHING RAN" in captured.err
    assert "--execute" in captured.err
    # Not parseable as a result.
    assert not captured.out.strip().startswith("{")


def test_run_says_it_the_same_way(capsys, monkeypatch):
    import src.mathlib_review.review.runner as runner

    async def _noop(dataset, scaffold, task_overrides, logger):
        return None

    monkeypatch.setattr(runner, "run", _noop)
    cli.main(["run", "--config", str(CONFIG), "--run-name", "probe"])
    assert "NOTHING RAN" in capsys.readouterr().err
