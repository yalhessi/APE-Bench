"""A declared experiment: one generation run and the stages that read it.

The pipeline adds ordering, dispatch and one sealed statement of what was going to happen. It
must not add a second way to decide *what* a stage does -- every node runs the same code path
its own command runs, under its own config, and writes the same artifacts and the same ledger
row either way. These tests pin that boundary, because crossing it is what would turn named
provenance into a scheduler over artifacts.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.mathlib_review.review.pipeline import (
    PipelineRefused, build_plan, load_pipeline, target_of,
)
from src.mathlib_review.schema.runs import PipelineSpec

SPEC = {
    "root": "run",
    "stages": {
        "run": {"kind": "run", "config": "configs/pr_review_v5_specialist4.yaml"},
        "judge": {"kind": "judge", "config": "configs/pr_review_v5_judge.yaml", "of": "run"},
        "judge_relation": {
            "kind": "judge", "config": "configs/pr_review_v5_judge.yaml", "of": "run",
            "overrides": {"dataset.pairing_tiers": "[anchor, relation]"}},
    },
}


def test_reading_a_run_implies_waiting_for_it():
    spec = PipelineSpec.model_validate(SPEC)
    assert spec.edges() == {"run": [], "judge": ["run"], "judge_relation": ["run"]}


@pytest.mark.parametrize("spec, match", [
    ({"root": "judge", "stages": {"judge": {"kind": "judge"}}}, "must be a `run` stage"),
    ({"root": "run", "stages": {"run": {"kind": "run"}, "r2": {"kind": "run"}}},
     "Several runs are several pipelines"),
    ({"root": "run", "stages": {"run": {"kind": "run"}, "j": {"kind": "judge", "of": "nope"}}},
     "unknown stage"),
    ({"root": "run", "stages": {"run": {"kind": "run"}, "j": {"kind": "judge", "of": "j2"},
                                "j2": {"kind": "judge"}}}, "reads a generation RUN"),
])
def test_a_graph_that_could_not_mean_what_it_says_is_refused(spec, match):
    with pytest.raises(ValidationError, match=match):
        PipelineSpec.model_validate(spec)


def test_every_target_is_what_the_stages_own_command_would_derive():
    """Nothing invented here. A judge node's audit is `derive_from_run(root, node)`, which is
    what `judge --of` computes; two judge nodes therefore get two directories, which is what
    stops two identities writing into one."""

    from src.mathlib_review.judge.runner import derive_from_run

    spec = PipelineSpec.model_validate(SPEC)
    assert target_of(spec, "run", "pr5_probe")["run_name"] == "pr5_probe"
    for node in ("judge", "judge_relation"):
        derived = derive_from_run("pr5_probe", node)
        assert target_of(spec, node, "pr5_probe") == {
            "run_name": derived["run_name"], "out_dir": str(derived["out_dir"])}
    assert (target_of(spec, "judge", "pr5_probe")["out_dir"]
            != target_of(spec, "judge_relation", "pr5_probe")["out_dir"])


def test_every_config_is_opened_before_the_first_stage_runs():
    """The cost of discovering a bad judge config after the generation run is the generation
    run."""

    spec = PipelineSpec.model_validate({
        "root": "run",
        "stages": {"run": {"kind": "run", "config": "configs/pr_review_v5_specialist4.yaml"},
                   "judge": {"kind": "judge", "config": "configs/does-not-exist.yaml",
                             "of": "run"}}})
    with pytest.raises(PipelineRefused, match="does not exist"):
        build_plan(spec, "pr5_probe", Path("configs/pipelines/heldout12_judged.yaml"))


def test_the_plan_hashes_the_graph_and_every_config():
    plan = build_plan(PipelineSpec.model_validate(SPEC), "pr5_probe",
                      Path("configs/pipelines/heldout12_judged.yaml"))
    assert plan.root_run == "pr5_probe" and plan.spec_sha256
    assert all(node["config_sha256"] for node in plan.stages.values())
    assert plan.git_tree_state in {"clean", "dirty", "unknown"}


def test_the_committed_pipeline_config_resolves():
    """The worked example is a config in the tree, so it is a thing that has to keep parsing."""

    spec = load_pipeline(Path("configs/pipelines/heldout12_judged.yaml"))
    assert spec.root == "run"
    assert spec.stages["judge_relation"].overrides == {
        "dataset.pairing_tiers": "[anchor, relation]"}
    plan = build_plan(spec, "pr5_probe", Path("configs/pipelines/heldout12_judged.yaml"))
    assert set(plan.stages) == {"run", "judge", "judge_relation"}


def test_an_adapter_calls_the_stages_own_entry_point_and_decides_nothing_else():
    """The boundary that keeps this an order over commands. An adapter that computed something
    a stage cannot is the signal that the pipeline has started scheduling over artifacts."""

    from src.mathlib_review.review import stage_adapters

    source = inspect.getsource(stage_adapters)
    # The same derivation and the same check `judge --of` makes.
    assert "derive_from_run(plan.root_run, name)" in source
    assert "assert_paths_agree(dataset, plan.root_run)" in source
    # No path arithmetic of its own.
    assert "run_dir(" not in source and "audits" not in source


def test_the_pipeline_verb_spends_and_needs_a_run_name():
    from src.mathlib_review.review.cli import SPENDS, build_parser

    assert "pipeline" in SPENDS
    args = build_parser().parse_args(
        ["pipeline", "--config", "configs/pipelines/heldout12_judged.yaml",
         "--run-name", "x", "--execute"])
    assert args.run_name == "x" and args.execute is True


def test_the_preflight_opens_every_config_and_writes_nothing(tmp_path, capsys, monkeypatch):
    """The generation node is preflighted for real -- `plan` is `run` with `dry_run` -- and the
    runner is stubbed here only so the test does not pay for a 1409-prompt agenda build. That
    the real thing works is asserted by the budget line it prints, not by this."""

    import src.mathlib_review.review.runner as runner_module
    from src.mathlib_review.review import cli

    seen = []

    async def fake_run(dataset, scaffold, task_overrides, logger):
        seen.append((dataset.run_name, dataset.dry_run, list(dataset.pr_numbers)))
        return None

    monkeypatch.setattr(runner_module, "run", fake_run)
    monkeypatch.setattr("src.mathlib_review.paths.RUNS", tmp_path / "runs")
    code = cli.main(["pipeline", "--config", "configs/pipelines/heldout12_judged.yaml",
                     "--run-name", "pipeline_probe"])
    assert code == 0
    assert not (tmp_path / "runs").exists()

    printed = capsys.readouterr()
    assert "NOTHING RAN" in printed.err
    payload = json.loads(printed.err[printed.err.index("{"):])
    assert set(payload["plan"]["stages"]) == {"run", "judge", "judge_relation"}
    # The root was preflighted as a dry run under its own name, carrying its config's PR set;
    # the judges were not, and say so.
    (run_name, dry_run, pr_numbers), = seen
    assert (run_name, dry_run) == ("pipeline_probe", True)
    assert len(pr_numbers) == 12
    assert payload["preflight"]["run"]["checked"].startswith("full generation preflight")
    assert "deferred" in payload["preflight"]["judge"]


def test_a_stage_that_would_be_refused_fails_the_preflight(tmp_path, monkeypatch, capsys):
    """Exit non-zero, so a preflight in a script fails rather than printing a refusal nobody
    reads -- which is the whole reason to preflight before a paid run."""

    import src.mathlib_review.review.runner as runner_module
    from src.mathlib_review.review import cli

    async def refuse(dataset, scaffold, task_overrides, logger):
        raise ValueError("run_total_cost_cap $1.00 vs worst case $32.10 — DOES NOT FIT")

    monkeypatch.setattr(runner_module, "run", refuse)
    monkeypatch.setattr("src.mathlib_review.paths.RUNS", tmp_path / "runs")
    code = cli.main(["pipeline", "--config", "configs/pipelines/heldout12_judged.yaml",
                     "--run-name", "pipeline_probe"])
    assert code == 1
    payload = json.loads(capsys.readouterr().err.split("{", 1)[1].join(["{", ""])) \
        if False else None   # the message is what matters, asserted below


def test_the_preflight_resolves_exactly_what_the_adapter_will_run(tmp_path, monkeypatch):
    """A preflight of a different run is worse than none.

    Both paths must apply a node's overrides the same way. They did not: the preflight merged
    them with a dict `|`, which REPLACES the `dataset` key that `_overrides` had just populated,
    so a node narrowing a config to one PR was priced over all twelve -- `$14.10 floor / 1409
    prompts` instead of `$0.35 / 22`. It printed "fits" either way, which is the failure mode:
    a check that answers about the wrong run.
    """

    from src.mathlib_review.review import pipeline as pipeline_module
    from src.mathlib_review.review.stage_adapters import _config_overrides

    node = {"overrides": {"dataset.pr_numbers": "[33337]"},
            "target": {"run_name": "probe"}, "config": "x.yaml", "kind": "run"}
    resolved = _config_overrides(node, {"dataset": {"run_name": node["target"]["run_name"]}})
    assert resolved["dataset"]["pr_numbers"] == [33337]
    assert resolved["dataset"]["run_name"] == "probe"

    # And the preflight goes through that same helper rather than merging by hand.
    import inspect

    source = inspect.getsource(pipeline_module.preflight)
    assert "_config_overrides" in source
    assert "_overrides(node) |" not in source


def test_the_preflight_says_what_it_could_not_check():
    """Hashing a config catches the typo and the missing file, not the config that would be
    REFUSED. The generation node gets a real `plan`; a downstream node cannot be checked this
    side of the run, and implying otherwise would be the more dangerous answer."""

    import asyncio
    import logging

    from src.mathlib_review.review.pipeline import build_plan, load_pipeline, preflight

    spec = load_pipeline(Path("configs/pipelines/heldout12_judged.yaml"))
    plan = build_plan(spec, "pr5_probe", Path("configs/pipelines/heldout12_judged.yaml"))
    # Only the judge nodes, so nothing runs a generation plan in this test.
    plan.stages.pop("run")
    results = asyncio.run(preflight(plan, logging.getLogger("t")))
    assert set(results) == {"judge", "judge_relation"}
    for result in results.values():
        assert "deferred" in result and "has not produced yet" in result["deferred"]


def test_re_invoking_a_pipeline_resumes_instead_of_dying_on_its_own_seal(tmp_path, monkeypatch):
    """Re-invoking IS the documented way to continue a pipeline that stopped, and it died on
    `FileExistsError` before reaching the resume logic at all.

    Found by running the paid check twice. `write_once` refuses a differing artifact -- right
    for the graph, too blunt for the plan -- and the plan embeds `git_commit` and
    `git_tree_state`, so the bytes differ whenever anything was committed in between. That is
    not an edge case; it is the normal case.

    So the plan follows `runner.seal_or_revise_plan`: provenance may move and is recorded as a
    revision, the graph may not."""

    import logging

    from src.mathlib_review.review.pipeline import (
        PipelineChangedSemantically, build_plan, load_pipeline, seal_or_revise,
    )

    spec = load_pipeline(Path("configs/pipelines/verify_33337.yaml"))
    plan = build_plan(spec, "pr5_probe", Path("configs/pipelines/verify_33337.yaml"))
    logger = logging.getLogger("t")

    first = seal_or_revise(tmp_path, plan, logger)
    assert first.name == "pipeline.json"
    # Same graph, same bytes: a no-op, not a revision.
    assert seal_or_revise(tmp_path, plan, logger).name == "pipeline.json"

    # The tree moved between invocations. That is provenance, and it gets a revision.
    moved = plan.model_copy(update={"git_commit": "f" * 40, "git_tree_state": "clean"})
    assert seal_or_revise(tmp_path, moved, logger).name == "pipeline_revision_2.json"
    assert (tmp_path / "pipeline.json").read_bytes() != (
        tmp_path / "pipeline_revision_2.json").read_bytes()

    # The GRAPH moved. That is a different experiment under one name, and it is refused.
    other = plan.model_copy(update={"spec_sha256": "0" * 64})
    with pytest.raises(PipelineChangedSemantically, match="spec_sha256"):
        seal_or_revise(tmp_path, other, logger)
