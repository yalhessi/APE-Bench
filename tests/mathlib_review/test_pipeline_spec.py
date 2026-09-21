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
    import logging

    from src.mathlib_review.review import cli

    monkeypatch.setattr("src.mathlib_review.paths.RUNS", tmp_path / "runs")
    code = cli.main(["pipeline", "--config", "configs/pipelines/heldout12_judged.yaml",
                     "--run-name", "pipeline_probe"])
    assert code == 0
    assert not (tmp_path / "runs").exists()
    printed = capsys.readouterr()
    assert "NOTHING RAN" in printed.err
    plan = json.loads(printed.err[printed.err.index("{"):])
    assert set(plan["stages"]) == {"run", "judge", "judge_relation"}
