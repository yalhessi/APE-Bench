"""Issue-kind verifiers: the routing key that makes the publication gate reachable.

Measured on the 4-PR smoke before this existed: **0 of 33** candidates obtained a
claim-scoped `supports`, so the holistic arm published nothing and the merged ensemble was
exactly the checker arm. Twelve of those (documentation 6, naming 4, scope 2) could not have
been supported by any collector that existed, whatever they said — `concern_family` names a
topic, and a topic is not a check.
"""

from __future__ import annotations

import pytest

from src.datasets.pr_review_v4.verifiers import VERIFIERS, verify
from src.datasets.pr_review_v4.schema import CandidateClaim, ChangeTarget


def _candidate(family="style", kind=None, claim="c", requested="r"):
    return CandidateClaim(
        candidate_id="candidate:1", work_unit_id="w", episode_id="e1", pr_number=1,
        change_ids=["change:1"], primary_change_id="change:1", concern_family=family,
        issue_kind=kind, concern_label=family, severity="advisory", claim=claim,
        requested_change=requested, evidence_requests=[], source_sha256="h",
    )


def _target(code):
    return ChangeTarget(
        change_id="change:1", episode_id="e1", pr_number=1, kind="declaration",
        path="Mathlib/Test.lean", declaration_name="Foo.bar", declaration_kind="theorem",
        changed_range_ids=[], diff_fragments=[], reviewed_code=code,
        parse_status="semantic", source_sha256="t",
    )


def test_a_candidate_without_an_issue_kind_abstains():
    """No routing key, no check — and that must not read as a pass."""

    result = verify(_candidate(kind=None), _target("theorem foo : True := trivial"))
    assert result.verdict == "abstain"


def test_linter_silence_does_not_refute_a_style_claim():
    """The linters can support a style claim; they are not entitled to refute one.

    This asserted `contradicts`, and a `contradicts` sets the packet to `contradicted`, which
    `select_findings` skips — so linter silence suppressed the claim. The medium gold says
    that is backwards: `style` is its largest concern family at 10 of 33 maintainer
    judgments, while `lint_norm` produced a single opportunity on all of medium. An
    instrument that finds ~10% of the family cannot veto the other ~90%.
    """

    result = verify(
        _candidate("style", "style_norm_violation"),
        _target("theorem foo : True := trivial\n"),
    )
    assert result.verdict == "abstain"
    assert result.verifier == "lint_policy"
    assert not result.decided, "an abstention must not drive the packet to `contradicted`"


def test_a_style_claim_the_linters_confirm_is_supported():
    result = verify(
        _candidate("style", "style_norm_violation"), _target("x" * 101),
    )
    assert result.verdict == "supports"
    assert "ERR_LIN" in result.detail


def test_naming_abstains_without_the_population_scan_rather_than_guessing():
    """The scan is snapshot-keyed and expensive; absent it, the honest answer is unknown."""

    result = verify(
        _candidate("naming", "naming_convention_violation"),
        _target("theorem Foo.bar : True := trivial"),
    )
    assert result.verdict == "abstain"
    assert "population scan" in result.detail


def test_documentation_refutes_only_the_decidable_case():
    """A missing-docstring *rule* was measured and rejected — 8% of Mathlib lemmas carry
    one, so demanding them would fire on 92% of new lemmas. Only presence is checkable."""

    present = verify(
        _candidate("documentation", "documentation_gap",
                   claim="missing docstring on this lemma"),
        _target("/-- Doc. -/\ntheorem foo : True := trivial"),
    )
    assert present.verdict == "contradicts"

    absent = verify(
        _candidate("documentation", "documentation_gap",
                   claim="missing docstring on this lemma"),
        _target("theorem foo : True := trivial"),
    )
    assert absent.verdict == "supports"

    quality = verify(
        _candidate("documentation", "documentation_gap",
                   claim="the docstring is unclear about the hypothesis"),
        _target("/-- Doc. -/\ntheorem foo : True := trivial"),
    )
    assert quality.verdict == "abstain", "docstring quality is editorial, not decidable"


def test_scope_placement_abstains_loudly_rather_than_inventing_a_check():
    """Placement needs file-level adjacency; hunk-level change targets do not record it —
    on one measured file fourteen targets share a single line."""

    result = verify(
        _candidate("scope", "scope_placement"), _target("theorem foo : True := trivial"),
    )
    assert result.verdict == "abstain"
    assert "adjacency" in result.detail


def test_an_unrouted_issue_kind_abstains_rather_than_passing():
    """A kind with no verifier is "we cannot check this", never "it is fine"."""

    result = verify(
        _candidate("correctness", "correctness_policy"),
        _target("theorem foo : True := trivial"),
    )
    assert result.verdict == "abstain"
    assert "correctness_policy" not in VERIFIERS


# --- proof simplification: golf and idiom are not the same claim --------------------

def _proof_candidate(spec, replacement, original_family="proof-golf"):
    from src.datasets.pr_review_v4.schema import ProposedEdit

    candidate = _candidate(original_family, "proof_simplification",
                           claim="this proof can be improved",
                           requested="rewrite it")
    return candidate.model_copy(update={
        "spec_id": spec,
        "proposed_edit": ProposedEdit(
            path="Mathlib/Test.lean", declaration_name="Foo.bar",
            new_declaration=replacement,
        ),
    })


ORIGINAL_PROOF = "theorem Foo.bar (a b : Nat) : a + b = b + a := by\n  induction a <;> simp\n"
SHORTER = "theorem Foo.bar (a b : Nat) : a + b = b + a := by omega"
LONGER_BUT_CANONICAL = (
    "theorem Foo.bar (a b : Nat) : a + b = b + a := by\n  exact Nat.add_comm a b\n"
    "  -- canonical lemma rather than induction\n"
)
CHANGED_STATEMENT = "theorem Foo.bar (a b : Nat) (h : a = 0) : a + b = b + a := by omega"


def test_golf_must_be_shorter_and_idiom_need_not_be():
    """The two specs make different claims and must be held to different warrants.

    Keying the verifier on `issue_kind` would give idiom's laxer rule to golf, and since
    `select.py` publishes on ANY claim-scoped support, that silently repeals golf's own
    shorter-and-compiles rule.
    """

    golf_short = verify(_proof_candidate("proof_golf", SHORTER), _target(ORIGINAL_PROOF))
    assert golf_short.verdict == "supports"

    golf_long = verify(_proof_candidate("proof_golf", LONGER_BUT_CANONICAL),
                       _target(ORIGINAL_PROOF))
    assert golf_long.verdict == "contradicts"
    assert "must be shorter" in golf_long.detail

    idiom_long = verify(_proof_candidate("proof_idiom", LONGER_BUT_CANONICAL),
                        _target(ORIGINAL_PROOF))
    assert idiom_long.verdict == "supports", (
        "idiom explicitly claims the proof may already be short; requiring brevity would "
        "reject every finding it exists to make"
    )


def test_neither_spec_may_change_the_statement():
    for spec in ("proof_golf", "proof_idiom"):
        result = verify(_proof_candidate(spec, CHANGED_STATEMENT), _target(ORIGINAL_PROOF))
        assert result.verdict == "contradicts"
        assert "changes the statement" in result.detail


def test_a_claim_from_no_known_spec_abstains():
    """A holistic candidate declaring `proof_simplification` has no spec warrant, so the
    verifier declines rather than applying one of the focused rules to it."""

    result = verify(_proof_candidate(None, SHORTER), _target(ORIGINAL_PROOF))
    assert result.verdict == "abstain"


def test_a_proof_claim_without_an_edit_abstains():
    candidate = _candidate("proof-golf", "proof_simplification").model_copy(
        update={"spec_id": "proof_golf"}
    )
    assert verify(candidate, _target(ORIGINAL_PROOF)).verdict == "abstain"
