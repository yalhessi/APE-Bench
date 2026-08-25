"""`verified_compile` must mean "the same theorem, proved better" — not "a theorem compiles".

The submission path splices a whole replacement declaration *including its signature*
(`pr_review_v2/base.py:299`) and nothing compared the old signature to the new one. An agent
that adds a hypothesis, specialises a type, or weakens the conclusion produced a file that
compiled and earned the top evidence tier for a theorem nobody asked about.

golf/idiom and generality need opposite guarantees, and one comparison serves both.
"""

from __future__ import annotations

import pytest

from src.datasets.pr_review_v4.statement_gate import (
    compare_statements,
    declaration_source,
    gate_error,
    masked_signature,
)

ORIGINAL = "theorem foo (a b : Nat) : a + b = b + a := by omega"
PROOF_ONLY = "theorem foo (a b : Nat) : a + b = b + a := by simp [Nat.add_comm]"
EXTRA_HYPOTHESIS = "theorem foo (a b : Nat) (h : a = 0) : a + b = b + a := by omega"
GENERALIZED = (
    "theorem foo {α} [AddCommMonoid α] (a b : α) : a + b = b + a := by exact add_comm a b"
)


def test_a_proof_only_rewrite_is_unchanged():
    assert compare_statements(ORIGINAL, PROOF_ONLY).verdict == "unchanged"


@pytest.mark.parametrize("replacement", [EXTRA_HYPOTHESIS, GENERALIZED])
def test_a_signature_edit_is_detected(replacement):
    assert compare_statements(ORIGINAL, replacement).verdict == "changed"


def test_golf_may_not_move_the_statement():
    """The failure this gate exists for: it compiles, so it used to pass."""

    error = gate_error("proof_simplification", compare_statements(ORIGINAL, EXTRA_HYPOTHESIS))
    assert error and "must not change the statement" in error
    assert gate_error("proof_simplification", compare_statements(ORIGINAL, PROOF_ONLY)) is None


def test_generality_must_move_the_statement():
    """`generality.py` tells the agent to drop proof-only findings; nothing enforced it."""

    error = gate_error("generalization_available", compare_statements(ORIGINAL, PROOF_ONLY))
    assert error and "must change the statement" in error
    assert gate_error(
        "generalization_available", compare_statements(ORIGINAL, GENERALIZED)
    ) is None


def test_a_rename_alone_is_not_a_statement_change():
    """Signatures are compared with the declaration's own name masked."""

    renamed = "theorem foo_comm (a b : Nat) : a + b = b + a := by omega"
    assert compare_statements(ORIGINAL, renamed).verdict == "unchanged"


def test_an_uncomparable_edit_is_rejected_not_waved_through():
    """A line-span edit that is not one declaration cannot be checked, so it is refused."""

    comparison = compare_statements(ORIGINAL, "  simp [Nat.add_comm]")
    assert comparison.verdict == "undecidable"
    error = gate_error("proof_simplification", comparison)
    assert error and "declaration_name + new_declaration" in error


def test_other_issue_kinds_are_not_gated():
    """The check only makes sense where the claim is about the statement/proof split."""

    assert gate_error("naming_convention_violation",
                      compare_statements(ORIGINAL, EXTRA_HYPOTHESIS)) is None
    assert gate_error(None, compare_statements(ORIGINAL, EXTRA_HYPOTHESIS)) is None


def test_declaration_source_declines_when_ambiguous():
    """Comparing against the wrong declaration is worse than declining to compare."""

    twice = f"{ORIGINAL}\n\ntheorem Other.foo (a : Nat) : a = a := rfl\n"
    assert declaration_source(twice, "foo") is None
    assert declaration_source(ORIGINAL, "foo") is not None


def test_masked_signature_is_none_for_unparseable_input():
    assert masked_signature("") is None
    assert masked_signature("not lean at all") is None
