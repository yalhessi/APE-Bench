"""The warrant a holistic finding earns, and what it is worth at the merge.

`generalist_findings` projected every holistic candidate at `model_assertion`, whatever its
evidence said, because it never passed an `evidence_tier` and
`merge.finding_from_candidate` defaults to the floor. `conditions._EVIDENCE_BY_METHOD`
already mapped `naming_norm.v1 -> repository_measurement`, but only `deterministic_findings`
— the v4 arm — ever read it.

That is not a labelling problem. `merge_findings` resolves two findings at one anchor by
`evidence_rank`, and **only when the ranks differ**: equal ranks are an unresolved conflict
and both sides are demoted. With every holistic finding at the floor, a claim `naming_norm`
had supported with a counted population could not outrank the unsupported claim sitting on
the same declaration, so both were lost.

Measured on the three held-out A reps by replaying the recorded findings through the merge:
conflicts 37/35/34 -> 35/33/32 and published 25/28/27 -> 27/30/29, the gain being `naming`
in every rep — the family that published **zero** in all three.

These tests pin the mechanism, not the numbers: the numbers live in
`docs/research/lead-orientation-audit.md` and move with the runs.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.evidence.verifiers import VERIFIERS, WARRANT_BY_ISSUE_KIND
from src.mathlib_review.review.merge import merge_findings
from src.mathlib_review.schema import EVIDENCE_TIERS, FindingSource, ReviewFinding


def _finding(finding_id: str, tier: str, action: str) -> ReviewFinding:
    """A real `ReviewFinding`, not a stand-in.

    A `SimpleNamespace` shaped like one is free to be wrong — it accepts a field the model
    does not have and keeps passing when the model gains one. The model refuses both.
    """

    return ReviewFinding(
        finding_id=finding_id,
        pr_number=33145,
        episode_id="episode:test",
        arm="generalist",
        admission="published",
        admission_reason="evidence packet supports the claim",
        change_ids=["change:abc"],
        primary_change_id="change:abc",
        concern_family="naming",
        issue_kind="naming_convention_violation",
        severity="advisory",
        claim=f"claim {finding_id}",
        requested_change=action,
        evidence_tier=tier,
        action_key=action,
        sources=[FindingSource(arm="generalist", candidate_id=f"candidate:{finding_id}")],
        source_sha256="0" * 64,
    )


def test_equal_tiers_at_one_anchor_lose_both():
    """The failure the tier attachment exists to stop, pinned so it cannot come back."""

    findings = [
        _finding("finding:aaa", "model_assertion", "rename to upperBounds_image"),
        _finding("finding:bbb", "model_assertion", "add a docstring"),
    ]
    merged, conflicts, _report = merge_findings(findings, pr_finding_limit=None)

    assert len(conflicts) == 1, "same anchor, same family, equal warrant is a conflict"
    assert all(item.admission == "diagnostic" for item in merged), (
        "equal ranks demote every side — this is why a supported naming claim was lost"
    )


def test_a_stronger_warrant_resolves_the_anchor():
    """One side measured against the repository outranks one that was only asserted."""

    findings = [
        _finding("finding:aaa", "repository_measurement", "rename to upperBounds_image"),
        _finding("finding:bbb", "model_assertion", "add a docstring"),
    ]
    merged, conflicts, _report = merge_findings(findings, pr_finding_limit=None)

    assert not conflicts, "differing ranks resolve rather than conflict"
    by_id = {item.finding_id: item for item in merged}
    assert by_id["finding:aaa"].admission == "published"
    assert by_id["finding:bbb"].admission == "diagnostic"


def test_every_declared_warrant_is_a_real_tier():
    """A typo here would be silent: the tier is read, not validated, at projection."""

    for issue_kind, tier in WARRANT_BY_ISSUE_KIND.items():
        assert issue_kind in VERIFIERS, f"{issue_kind} has no verifier to earn a warrant"
        assert tier in EVIDENCE_TIERS, f"{tier} is not an evidence tier"


@pytest.mark.parametrize("issue_kind", ["documentation_gap", "scope_placement",
                                        "proof_simplification"])
def test_the_unearned_kinds_stay_at_the_floor(issue_kind):
    """Conservatism is the contract, and each omission has its own reason.

    `documentation_gap` reads the target's own text, not the repository, and a blanket
    missing-docstring rule was falsified at 8% of theorems / 67% of defs. `scope_placement`
    abstains unconditionally today. `proof_simplification`'s warrant is the compile, which is
    tiered from the `lean_compile` artifact — tiering it here as well would let a
    statement-gate pass stand in for a compiler.

    Promoting any of them is a decision with a measurement behind it, not a one-line edit.
    """

    assert issue_kind in VERIFIERS
    assert issue_kind not in WARRANT_BY_ISSUE_KIND
