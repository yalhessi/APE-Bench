"""Recovering a finished run's real spend, without touching its ledger.

The September runs book their paused jobs at $0.00, because a sample that paused on budget was
judged resumable, never aggregated, and reached the ledger as a bare failure. Their raw
artifacts are deliberately left alone -- rewriting them destroys the evidence the defect
existed -- so the recovery lands beside them as a derived artifact.

Cross-checked against figures verified by hand: heldout11 rep2 hid $0.6829 billed and $1.8908
nominal against a reported $10.1519; specialist4 hid $0.1218 / $0.3017, which is the exact
family_design job on PR 33117.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis.corrections import CORRECTION_VERSION, recover


def _scratch(tmp_path, attempts, *, run_name="r1"):
    sample_dir = (tmp_path / run_name / "tasks" / "gi" / "samples" / "0")
    sample_dir.mkdir(parents=True)
    (sample_dir / "sample.json").write_text(
        json.dumps({"status": None, "attempts": attempts}), encoding="utf-8")
    return tmp_path


def test_a_paused_attempt_is_recovered_with_both_cost_figures(tmp_path):
    root = _scratch(tmp_path, [
        {"status": "paused_cost_limit", "cost": 0.301742,
         "cached_cost": 0.121822, "turns": 9},
    ])
    correction = recover("r1", scratch_root=root)

    assert len(correction.recovered) == 1
    assert correction.hidden_billed == pytest.approx(0.121822)
    assert correction.hidden_nominal == pytest.approx(0.301742)


def test_a_successful_attempt_is_not_a_correction(tmp_path):
    """Only work that spent money without producing a terminal result was mis-booked."""

    root = _scratch(tmp_path, [
        {"status": "success", "cost": 0.20, "cached_cost": 0.08},
    ])
    assert recover("r1", scratch_root=root).recovered == []


def test_a_turn_pause_counts_too(tmp_path):
    """`paused_max_turns` reaches the ledger the same way `paused_cost_limit` does."""

    root = _scratch(tmp_path, [
        {"status": "paused_max_turns", "cost": 0.5, "cached_cost": 0.2},
    ])
    assert len(recover("r1", scratch_root=root).recovered) == 1


def test_billed_falls_back_to_nominal_when_no_cached_figure(tmp_path):
    root = _scratch(tmp_path, [{"status": "paused_cost_limit", "cost": 0.25}])
    correction = recover("r1", scratch_root=root)
    assert correction.hidden_billed == pytest.approx(0.25)


def test_the_sidecar_carries_its_derivation_and_says_the_run_is_forensic(tmp_path):
    root = _scratch(tmp_path, [
        {"status": "paused_cost_limit", "cost": 0.30, "cached_cost": 0.12},
    ])
    payload = recover("r1", scratch_root=root).as_dict()

    assert payload["correction_version"] == CORRECTION_VERSION
    assert payload["source_sha256"]
    assert "forensic" in payload["verdict"]
    # Nominal and billed are reported separately and neither is called "spend" alone.
    assert payload["recovered"]["hidden_billed_cost"] == pytest.approx(0.12)
    assert payload["recovered"]["hidden_nominal_cost"] == pytest.approx(0.30)


def test_a_run_with_no_scratch_tree_reports_nothing_rather_than_guessing(tmp_path):
    assert recover("absent", scratch_root=tmp_path).recovered == []


@pytest.mark.parametrize("run_name,billed,nominal", [
    ("pr_review_v5_lead_heldout11_rep2", 0.6829245, 1.8907805),
    ("pr_review_v5_specialist4_rep1", 0.121822, 0.301742),
])
def test_the_checked_in_sidecars_match_the_hand_verified_figures(run_name, billed, nominal):
    """The sidecars are tracked, so this pins them without depending on the ignored .ape tree."""

    path = Path("results/pr_review_v5/runs") / run_name / "correction_sidecar.json"
    if not path.is_file():
        pytest.skip(f"{run_name} sidecar not present")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["recovered"]["hidden_billed_cost"] == pytest.approx(billed)
    assert payload["recovered"]["hidden_nominal_cost"] == pytest.approx(nominal)
    assert "forensic" in payload["verdict"]
