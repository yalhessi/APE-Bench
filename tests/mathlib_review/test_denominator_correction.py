"""An archived audit's recall, recomputed over the PRs its run actually reviewed.

The correction is exact rather than estimated: an obligation belonging to a PR the run never
reviewed cannot be hit by it, so the archived hit counts are already right and only the divisor
was wrong. The audits themselves are never rewritten -- same argument as `corrections.py`.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.mathlib_review.analysis.denominators import (
    DENOMINATOR_CORRECTION_VERSION, correct, correct_archive, resolve_run_for_audit,
    sidecar_payload,
)

PR_OF = {"o1": 33098, "o2": 33098, "o3": 33066, "o4": 33117, "o5": 33145}


def _report(**rows):
    # Real reports print `counts.obligations` as the length of `per_obligation`; the whole
    # defect is that this number was taken over the wrong population, not that it disagreed
    # with its own rows.
    return {
        "counts": {"obligations": len(rows)},
        "per_obligation": [
            {"obligation_id": key, "issue_status": value[0],
             "resolution_status": value[1], "location_hit": value[2]}
            for key, value in rows.items()
        ],
    }


def test_obligations_from_unreviewed_prs_leave_the_denominator():
    report = _report(o1=("hit", "hit", True), o2=("miss", "miss", True),
                     o3=("miss", "miss", False), o4=("miss", "miss", False),
                     o5=("miss", "miss", False))
    result = correct(report, audit="a", run_name="r", pr_scope=[33066, 33098],
                     pr_of_obligation=PR_OF)
    assert result.printed_obligations == 5
    assert result.scoped_obligations == 3
    # The hit was on a reviewed PR, so it survives; the divisor is what changed.
    assert result.issue_hits == 1
    assert result.rates()["issue_recall"] == round(1 / 3, 4)


def test_an_unknown_scope_carries_the_printed_denominator_through():
    report = _report(o1=("hit", "miss", True), o4=("miss", "miss", False))
    result = correct(report, audit="a", run_name=None, pr_scope=None,
                     pr_of_obligation=PR_OF)
    assert result.scoped_obligations == 2


def test_the_sidecar_keeps_both_numbers_and_the_source_hash():
    report = _report(o1=("hit", "hit", True), o4=("miss", "miss", False))
    payload = sidecar_payload(
        correct(report, audit="a", run_name="r", pr_scope=[33098],
                pr_of_obligation=PR_OF),
        report_sha256="abc",
    )
    assert payload["schema_version"] == DENOMINATOR_CORRECTION_VERSION
    assert payload["source_report_sha256"] == "abc"
    assert payload["printed"]["obligations"] == 2
    assert payload["corrected"]["obligations"] == 1
    assert payload["corrected"]["pr_scope"] == [33098]


def test_archive_audits_match_the_rule_or_the_hand_written_name():
    """`derive_from_run` is the rule; the older audit directories predate it."""

    runs = ["pr_review_v5_lead_smoke4_rep7", "pr_review_v5_lead_heldout11_rep2"]
    assert resolve_run_for_audit("lead-smoke4-rep7", runs) == "pr_review_v5_lead_smoke4_rep7"
    assert resolve_run_for_audit("heldout11-rep2", runs) == "pr_review_v5_lead_heldout11_rep2"
    assert resolve_run_for_audit("nothing-like-this", runs) is None


def test_the_real_archive_reproduces_the_corrected_smoke4_table():
    """The numbers every comparison in `docs/plans/2026-09-08-*` rests on.

    Skips rather than fails where the archive is absent, so the suite still runs in a checkout
    without `results/`.
    """

    import pytest

    if not Path("results/pr_review_v5/audits").is_dir():
        pytest.skip("no archived audits in this checkout")
    by_audit = {row["audit"]: row for row in correct_archive(write=False)}
    expected = {
        "lead-smoke4-rep6": (17, 0.3529),
        "lead-smoke4-rep7": (17, 0.4118),
        "pr5-smoke4-rep9": (17, 0.3529),
        "heldout11-rep2": (20, 0.0),
    }
    for audit, (obligations, issue_recall) in expected.items():
        if audit not in by_audit:
            pytest.skip(f"{audit} not present")
        row = by_audit[audit]["corrected"]
        assert row["obligations"] == obligations, audit
        assert row["issue_recall"] == issue_recall, audit
