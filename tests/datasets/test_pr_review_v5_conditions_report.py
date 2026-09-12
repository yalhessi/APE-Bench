"""`report conditions`: the comparison the design question is read on.

The first production caller of `analysis.reports.compare_conditions`, which implemented the
mean / union / stable protocol in Phase 9 and was called only by its tests since. It reports
sets and not just rates because Phase 9's finding was two arms tied on mean recall while
recovering nearly disjoint obligations -- and at one repetition the sets are the only honest
output, since a rate delta at these denominators is inside the judge's disagreement with
itself.

The real fixture is `pr5-smoke4-rep9`, whose `denominator_correction.json` records the hit
counts by hand: location 14, issue 6, resolution 3, over 17. The synthetic fixtures exercise
the two refusals that make the comparison meaningful: one judge, one denominator.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis import report as report_module

REAL_AUDIT = Path("results/pr_review_v5/audits/pr5-smoke4-rep9/semantic_report.json")
RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.mark.skipif(not REAL_AUDIT.is_file(), reason="needs the rep9 audit on disk")
def test_the_funnel_reproduces_the_audits_own_hand_recorded_counts():
    out = report_module.conditions({"A": "pr5_smoke4_rep9"})

    assert out["denominator"] == 17
    assert out["funnel"]["A"]["location"]["hit"] == 14
    assert out["funnel"]["A"]["issue"]["hit"] == 6
    assert out["funnel"]["A"]["resolution"]["hit"] == 3
    assert out["one_flip_pp"] == 5.9
    assert out["repetitions"] == {"A": 1}


@pytest.mark.skipif(not REAL_AUDIT.is_file() or not RELEASE.is_dir(),
                    reason="needs the rep9 audit and the release on disk")
def test_attention_and_redundancy_are_facts_about_one_run():
    """Neither needs a repetition: the concern distribution of what a run raised, against the
    maintainers', and how many times it wrote up one change target."""

    out = report_module.conditions({"A": "pr5_smoke4_rep9"}, RELEASE)

    attention = out["attention"]
    assert attention["maintainers"]["n"] == 17
    assert 0.0 <= attention["A"]["distance_from_maintainers"] <= 1.0
    # `documentation` (arm spelling) must have been bridged to `docs` (gold spelling), or the
    # docs family reads as disjoint attention when it is the same family.
    assert "documentation" not in attention["A"]["share"]

    redundancy = out["redundancy"]["A"]
    assert redundancy["findings"] == 54
    assert redundancy["findings_per_target"] > 1.0


# --- the two refusals ----------------------------------------------------------------------


def _audit(tmp_path, name, *, identity, obligations, hits):
    """A minimal scored semantic_report.json under a fake audit root."""

    out = tmp_path / "audits" / name
    out.mkdir(parents=True)
    rows = [{"obligation_id": ob,
             "location_hit": ob in hits["location"],
             "issue_status": "hit" if ob in hits["issue"] else "miss",
             "resolution_status": "hit" if ob in hits["resolution"] else "miss"}
            for ob in obligations]
    (out / "semantic_report.json").write_text(json.dumps({
        "scored": True, "judge_identity": identity, "per_obligation": rows,
        "silent_pr_emission": {"candidates": 0, "candidates_per_control_pr": 0.0,
                               "control_pr_numbers": []},
    }))
    return out


def _point_audits_at(monkeypatch, tmp_path):
    def fake_derive(run_name):
        return {"out_dir": tmp_path / "audits" / run_name}
    import src.mathlib_review.judge.runner as judge_runner
    monkeypatch.setattr(judge_runner, "derive_from_run", fake_derive)


def test_conditions_judged_by_different_instruments_are_refused(tmp_path, monkeypatch):
    """`judge_identity` hashes rubric, model, sampling and decode budgets; R0 found two judge
    arms disagreeing on 4 of 18 pairs from decode budgets alone."""

    obs = ["ob:1", "ob:2", "ob:3"]
    _audit(tmp_path, "a", identity="judge-x", obligations=obs,
           hits={"location": obs, "issue": ["ob:1"], "resolution": []})
    _audit(tmp_path, "b", identity="judge-y", obligations=obs,
           hits={"location": obs, "issue": ["ob:2"], "resolution": []})
    _point_audits_at(monkeypatch, tmp_path)

    with pytest.raises(SystemExit, match="different instruments"):
        report_module.conditions({"A": "a", "B": "b"})


def test_conditions_scored_over_different_denominators_are_refused(tmp_path, monkeypatch):
    """The judge scopes obligations to the PRs a run reviewed, so a mismatch means the runs
    did not review the same PRs -- and a recall from one is not a recall from the other."""

    _audit(tmp_path, "a", identity="j", obligations=["ob:1", "ob:2"],
           hits={"location": [], "issue": [], "resolution": []})
    _audit(tmp_path, "b", identity="j", obligations=["ob:1", "ob:2", "ob:3"],
           hits={"location": [], "issue": [], "resolution": []})
    _point_audits_at(monkeypatch, tmp_path)

    with pytest.raises(SystemExit, match="different denominator"):
        report_module.conditions({"A": "a", "B": "b"})


def test_union_and_exclusive_sets_are_the_output_not_just_the_rates(tmp_path, monkeypatch):
    """Phase 9: two arms tied on mean recall while recovering nearly disjoint obligations. A
    report that printed only the two rates would have called them equivalent."""

    obs = ["ob:1", "ob:2", "ob:3", "ob:4"]
    _audit(tmp_path, "a", identity="j", obligations=obs,
           hits={"location": obs, "issue": ["ob:1", "ob:2"], "resolution": []})
    _audit(tmp_path, "b", identity="j", obligations=obs,
           hits={"location": obs, "issue": ["ob:3", "ob:4"], "resolution": []})
    _point_audits_at(monkeypatch, tmp_path)

    out = report_module.conditions({"A": "a", "B": "b"})
    issue = out["by_level"]["issue"]

    assert out["funnel"]["A"]["issue"]["recall"] == out["funnel"]["B"]["issue"]["recall"] == 0.5
    assert issue["exclusive_ids"] == {"A": ["ob:1", "ob:2"], "B": ["ob:3", "ob:4"]}
    assert issue["combined_union_recall"] == 1.0
