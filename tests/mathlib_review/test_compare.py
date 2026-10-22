"""`report compare`: why two results differ, and what the difference can support.

The user could not tell how two reports compared (2026-10-22). This pins the three verdicts --
one scale, side by side only, never pooled -- and that every difference nobody declared as the
contrast is listed, including the one a scaffold digest hides (which task setting moved).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review import paths
from src.mathlib_review.analysis.trace import compare_measurements
from src.mathlib_review.judge import runner


def _judged(tmp_path, run, *, gold_text="{}\n", hits=2, model="m", context=None):
    """A judged run as the judge leaves it: an audit with its measurement, a sealed plan, an
    agenda that names its own run, and the orchestrator's record of its task settings."""

    release = tmp_path / f"release_{gold_text.strip()[:4] or 'x'}"
    (release / "gold").mkdir(parents=True, exist_ok=True)
    (release / "gold" / "judgments.jsonl").write_text(gold_text)
    out = runner.derive_from_run(run)["out_dir"]
    out.mkdir(parents=True)
    pairs = out / "semantic_pairs.jsonl"
    pairs.write_text('{"pr_number": 7}\n')
    dataset = runner.JudgeDatasetConfig(release=release, candidates=tmp_path / "f.jsonl",
                                        out_dir=out, input_kind="finding", run_name=run)
    rows = [{"obligation_id": f"o{i}", "issue_status": "hit" if i < hits else "miss",
             "resolution_status": "miss", "location_hit": True} for i in range(4)]
    measurement = runner.judge_measurement(dataset, identity="judge", sample_count=3,
                                           report={"per_obligation": rows},
                                           sealed_pairs_path=pairs, pr_scope=[7])
    (out / "semantic_report.json").write_text(json.dumps(
        {"per_obligation": rows, "judge_identity": "judge", "measurement": measurement}))
    run_dir = tmp_path / "runs" / run
    run_dir.mkdir(parents=True)
    (run_dir / "run_plan.json").write_text(json.dumps(
        {"model_name": model, "routing_mode": "solo", "evaluation_settings": {"design": None}}))
    (run_dir / "agenda.json").write_text(json.dumps(
        {"agenda_id": f"agenda:{run}", "run_name": run, "source_sha256": run, "units": [1, 2]}))
    ape = tmp_path / "ape" / run
    ape.mkdir(parents=True)
    (ape / "config.json").write_text(json.dumps(
        {"config": {"task_config_overrides": {"context_file": context or "same.jsonl"}}}))


@pytest.fixture
def roots(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "AUDITS", tmp_path / "audits")
    monkeypatch.setattr(paths, "run_dir", lambda name: tmp_path / "runs" / name)
    return tmp_path


def test_two_runs_measured_alike_are_on_one_scale(roots):
    _judged(roots, "a_rep1")
    _judged(roots, "b_rep1", hits=3)
    out = compare_measurements({"A": "a_rep1", "B": "b_rep1"}, ape_root=roots / "ape")
    assert out["verdict"].startswith("one scale")
    assert out["measurements"]["A"]["numbers"] == {"denominator": 4, "issue_hits": 2,
                                                   "resolution_hits": 0}
    assert "subjects" in out["identity_differences"]
    # The agendas differ only in naming their own run: not a difference.
    assert out["run_differences"] == {} and out["undeclared_differences"] == []


def test_a_different_reference_set_is_side_by_side_never_subtracted(roots):
    _judged(roots, "a_rep1")
    _judged(roots, "b_rep1", gold_text='{"other": 1}\n')
    out = compare_measurements({"A": "a_rep1", "B": "b_rep1"}, ape_root=roots / "ape")
    assert out["verdict"].startswith("one instrument over different references")
    assert "reference_sha256" in out["identity_differences"]
    assert "reference_sha256" in out["undeclared_differences"]


def test_an_undeclared_run_difference_is_named_and_a_declared_one_is_not(roots):
    _judged(roots, "a_rep1", model="m1", context="base.jsonl")
    _judged(roots, "b_rep1", model="m2", context="treated.jsonl")
    out = compare_measurements({"A": "a_rep1", "B": "b_rep1"}, contrast=["task_config.context_file"],
                               ape_root=roots / "ape")
    assert out["run_differences"]["task_config.context_file"] == {
        "a_rep1": "base.jsonl", "b_rep1": "treated.jsonl"}
    assert out["undeclared_differences"] == ["model_name"]


def test_a_matching_and_a_judged_run_are_never_pooled(roots, tmp_path):
    from tests.mathlib_review.test_matching import _v2_plan

    _judged(roots, "a_rep1")
    plan_root = tmp_path / "planned"
    plan_root.mkdir()
    _v2_plan(plan_root)
    from src.mathlib_review.analysis import matching as MA
    from src.mathlib_review.judge.ask_matching import flat_rows, AskVerdict, ReviewerVerdict

    plan = MA.load_plan(plan_root / "m")
    rows = flat_rows([AskVerdict(pr=p.pr, ask_id=p.asks[0].ask_id, verdicts=[
        ReviewerVerdict(reviewer=label, value="no") for label in p.reviewers])
        for p in plan.packets])
    matches = plan_root / "matches.json"
    matches.write_text(json.dumps({"asks": rows, "unmatched": {
        str(p.pr): {label: len(found) for label, found in p.reviewers.items()} for p in plan.packets}}))
    MA.import_matches(plan, plan_root / "m", {"1": matches}, name="x")
    out = compare_measurements({"M": str(plan_root / "m"), "J": "a_rep1"}, ape_root=roots / "ape")
    assert out["verdict"].startswith("different instruments")
