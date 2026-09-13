"""A rename proposal offers more than one name, because two generators are each right alone.

`propose_rename` built one name: the conventional prefix plus the *old name's remainder*. That
is right exactly when the old name already described the statement and only its head was wrong,
and wrong when the remainder was the thing being corrected. Both happen in one release:

    PR 33337  coe_starProjection_eq_isComplProjection
              -> toLinearMap_starProjection_eq_isComplProjection    prefix swap is right
    PR 33145  Dense.continuous_upperBounds
              -> Dense.upperBounds_image                            prefix swap gives
                                                                    upperBounds_upperBounds

The second name is readable from the conclusion -- `upperBounds (f '' S) = …`, where `''` is
`Set.image` -- which is what the arm's own prompt says a Mathlib name is: "the head symbol and
the shape of the statement, in the order they appear". Measured over the release's rename asks
this operator fires on, prefix-swap is right on one and statement-derived on the other; both
offered puts the maintainer's name in the list for both.

Candidates change only *what* a firing says, never *whether* it fires, so none of this can cost
control-PR silence -- unlike widening the population test, which can.
"""

from __future__ import annotations

from src.mathlib_review.evidence.operators.naming_norm import (
    SubjectInference, SubjectPopulation, propose_rename, rename_candidates, scan_population,
    statement_head,
)
from collections import Counter


def test_the_prefix_swap_is_still_offered_first():
    """Today's behaviour, unchanged: it is right whenever the remainder already fits."""

    assert rename_candidates(
        "Submodule.coe_starProjection_eq_isComplProjection", "toLinearMap",
        "K.starProjection.toLinearMap", {},
    )[0] == "Submodule.toLinearMap_starProjection_eq_isComplProjection"


def test_the_statement_derived_name_recovers_the_miss():
    """The conclusion says `image`; the old name never did."""

    assert rename_candidates(
        "Dense.continuous_upperBounds", "upperBounds",
        "upperBounds (f '' S)", {"''": "image"},
    ) == ["Dense.upperBounds_upperBounds", "Dense.upperBounds_image"]


def test_a_notation_is_read_as_the_declaration_it_denotes():
    assert statement_head("f '' S", {"''": "image"}) == "image"
    assert statement_head("f '' S", {"''": "Set.image"}) == "image", "last component only"


def test_single_character_operators_are_never_used():
    """`+` appears in half of Mathlib; matching it would name everything after `HAdd`."""

    assert statement_head("a + b", {"+": "HAdd.hAdd"}) == "a"


def test_an_ascription_reads_the_expression_not_the_type():
    assert rename_candidates(
        "Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl", "toLinearMap",
        "(K.orthogonalProjection : E →ₗ[𝕜] K)", {},
    )[0] == "Submodule.toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl"


def test_agreeing_generators_produce_one_candidate_not_two():
    """PR 33098's shape: the old remainder already *is* what the statement is about."""

    assert rename_candidates(
        "Metric.card_maximalSeparatedSet", "encard",
        "(maximalSeparatedSet ε A).encard", {},
    ) == ["Metric.encard_maximalSeparatedSet"]


def test_the_proposal_carries_alternatives_without_moving_what_was_sealed():
    """`proposed_fullname` and `observed_pattern()` are what the opportunities executor reads
    and what the frozen naming-smoke releases recorded; `alternatives` is additive."""

    population = SubjectPopulation("upperBounds", Counter({"upperBounds": 27}), 27)
    subject = SubjectInference("upperBounds", "application_head", "upperBounds (f '' S)", "high")
    proposal = propose_rename(
        "Dense.continuous_upperBounds", subject, population, {"''": "image"})

    assert proposal.proposed_fullname == "Dense.upperBounds_upperBounds"
    assert proposal.alternatives == ("Dense.upperBounds_image",)
    assert "27/27" in proposal.observed_pattern()


def test_without_a_notation_map_the_proposal_is_exactly_what_it_was():
    population = SubjectPopulation("upperBounds", Counter({"upperBounds": 27}), 27)
    subject = SubjectInference("upperBounds", "application_head", "upperBounds (f '' S)", "high")
    proposal = propose_rename("Dense.continuous_upperBounds", subject, population)
    assert proposal.proposed_fullname == "Dense.upperBounds_upperBounds"
    assert "Dense.upperBounds_f" in proposal.alternatives or proposal.alternatives == ()


def test_the_scan_collects_the_snapshots_own_notation(tmp_path):
    root = tmp_path / "Mathlib"
    root.mkdir(parents=True)
    (root / "Defs.lean").write_text(
        'infixl:80 " \'\' " => Set.image\n'
        "theorem encard_thing (s : Set α) : (f s).encard = 0 := by simp\n")
    scan = scan_population(tmp_path, "sha")
    assert scan.notation.get("''") == "image"
