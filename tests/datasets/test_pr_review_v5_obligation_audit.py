"""Score the agent against what a maintainer asked for, not what a migration inferred.

18 of the 20 anchored obligations on the heldout set are `migration_proposal` — an automated
pass turned a review comment into a structured ask, unconfirmed by any curator. One of them
demonstrably overstates its source, and the release's own artifacts say so:

* the obligation asks to add an "Implementation details" discussion;
* the comment it came from is a bare GitHub suggestion block replacing one line of prose;
* its outcome is recorded `dropped` on evidence describing that very suggestion being adopted.

The audit does not decide anything. It joins each obligation to its comment and its outcome
so a person can read the pair, and flags rows worth reading. Exclusions are then named
explicitly, with reasons, and never by editing the release.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis.obligation_audit import audit, audit_report
from src.mathlib_review.analysis.obligation_exclusions import (
    EXCLUSIONS, apply, exclusion_report,
)

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
HELDOUT = [33117, 33145, 33285, 33294, 33305, 33321, 33337, 33362, 33421]


@pytest.fixture(scope="module")
def rows():
    if not (RELEASE / "gold/judgments.jsonl").is_file():
        pytest.skip("release not available in this checkout")
    return audit(RELEASE, HELDOUT)


def test_every_obligation_joins_to_a_maintainer_comment(rows):
    """The join is on `source_key` into the raw GitHub bundle, so it is position in the real
    thread rather than any id the migration invented. An unmatched row cannot be audited at
    all, which is itself a finding."""

    assert rows
    assert audit_report(rows)["without_a_matched_comment"] == 0


def test_the_overstated_obligation_is_flagged(rows):
    flagged = {r.pr_number for r in rows if r.flagged}
    assert 33321 in flagged


def test_flagging_is_a_prompt_to_read_not_a_verdict(rows):
    """PR 33145's suggestion blocks literally contain the lemma names *and* the dual proof,
    so its obligation is faithful even though the heuristic flags the word "refactor". A
    flag that decided the question would have thrown away a real obligation."""

    faithful = [r for r in rows if r.pr_number == 33145 and r.flagged]
    assert faithful, "expected the heuristic to over-flag here"
    assert any("Dense.ciSup" in c for r in faithful for c in r.comments)


def test_a_bare_suggestion_bounds_the_ask(rows):
    excluded = {e.obligation_id for e in EXCLUSIONS}
    row = next(r for r in rows if r.obligation_id in excluded)
    assert row.suggestion_only
    assert "implementation details" in row.expansion_markers
    assert len(row.comments) == 1


def test_the_excluded_row_contradicts_its_own_outcome(rows):
    """Recorded `dropped`, on evidence describing the maintainer's suggestion being adopted."""

    excluded = {e.obligation_id for e in EXCLUSIONS}
    row = next(r for r in rows if r.obligation_id in excluded)
    assert row.outcome == "dropped"
    assert "ultimate existence" in row.outcome_evidence


def test_exclusions_are_few_and_carry_their_evidence():
    """The guard against fitting the benchmark to the system: every exclusion states why,
    in terms a reader can check against the release."""

    assert len(EXCLUSIONS) <= 2, "exclusions should stay exceptional"
    for item in EXCLUSIONS:
        assert len(item.reason) > 200
        assert "suggestion" in item.reason or "evidence" in item.reason


def test_apply_removes_only_the_named_rows():
    kept = apply(["obligation:keepme", EXCLUSIONS[0].obligation_id, "obligation:alsokeep"])
    assert kept == ["obligation:keepme", "obligation:alsokeep"]


def test_the_report_names_what_it_removed():
    report = exclusion_report()
    assert report["excluded"] == len(EXCLUSIONS)
    assert 33321 in report["by_pr"]
