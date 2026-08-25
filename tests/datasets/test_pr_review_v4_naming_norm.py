"""Gates for the subject-general naming checker.

The frozen `naming_contrast` operator reaches one subject (`Set.encard`), which is why
C2 was 5/40 with nothing outside the development PR. These tests pin the generalization
against the *real* conclusions from the medium benchmark — including the coercion
ascription that a naive head rule misreads as a bound variable — and pin the guards that
keep the rule from firing where the corpus has no opinion.
"""

from collections import Counter

import pytest

from src.datasets.pr_review_v4.operators.naming_norm import (
    MIN_SUPPORT,
    SubjectPopulation,
    conclusion_subject,
    leaf_prefix,
    propose_rename,
)

# Conclusions taken verbatim from the medium release's change graphs.
REAL_CONCLUSIONS = {
    "(maximalSeparatedSet ε A).encard = packingNumber ε A": ("encard", "projection"),
    "upperBounds (f '' S) = upperBounds (range f)": ("upperBounds", "application_head"),
    "lowerBounds (f '' S) = lowerBounds (range f)": ("lowerBounds", "application_head"),
    "K.starProjection.toLinearMap = K.isCompl_orthogonal.projection": (
        "toLinearMap", "projection",
    ),
    # PR 33337's second rename: the subject sits inside a coercion ascription. The naive
    # head rule extracted the bound variable `K`, which is why the B1 probe first
    # over-counted this obligation as reachable.
    "(K.orthogonalProjection : E →ₗ[𝕜] K) = K.linearProjOfIsCompl _ h": (
        "→ₗ", "coercion_ascription",
    ),
}


@pytest.mark.parametrize("conclusion,expected", REAL_CONCLUSIONS.items())
def test_subject_extraction_on_real_medium_conclusions(conclusion, expected):
    token, kind = expected
    subject = conclusion_subject(conclusion)
    assert (subject.token, subject.kind) == (token, kind)
    assert subject.confidence == "high"


def test_quantified_and_role_conditioned_conclusions_carry_no_subject():
    """Unchanged from the frozen operator: these cannot name a declaration."""

    for conclusion in (
        "∃ C, C ⊆ A ∧ C.encard = packingNumber ε A",
        "∀ x ∈ A, x.encard = 0",
        "",
    ):
        assert conclusion_subject(conclusion).token is None


def test_leaf_prefix_splits_on_the_first_underscore():
    assert leaf_prefix("card_maximalSeparatedSet") == "card"
    assert leaf_prefix("encard") == "encard"
    assert leaf_prefix("coe_starProjection_eq_isComplProjection") == "coe"


def _population(counts, token="encard"):
    return SubjectPopulation(token, Counter(counts), sum(counts.values()))


def test_rename_is_proposed_when_the_corpus_disagrees_with_the_name():
    """The motivating case, now derived rather than hardcoded."""

    population = _population({"encard": 87, "other": 4})
    subject = conclusion_subject("(maximalSeparatedSet ε A).encard = packingNumber ε A")
    proposal = propose_rename("Metric.card_maximalSeparatedSet", subject, population)

    assert proposal is not None
    assert proposal.proposed_fullname == "Metric.encard_maximalSeparatedSet"
    assert proposal.subject_token == "encard"
    # The warrant the evidence-parity gate requires must be present and quantitative.
    pattern = proposal.observed_pattern()
    assert "87/91" in pattern and "no `card_` examples" in pattern


def test_no_proposal_when_the_name_already_follows_the_convention():
    population = _population({"encard": 87, "other": 4})
    subject = conclusion_subject("(maximalSeparatedSet ε A).encard = packingNumber ε A")
    assert propose_rename("Metric.encard_maximalSeparatedSet", subject, population) is None


def test_no_proposal_when_the_corpus_has_no_strong_convention():
    """Control safety: a subject the corpus is undecided about must not be policed."""

    weak = _population({"encard": 5, "card": 4, "size": 3})       # below MIN_SUPPORT
    split = _population({"encard": 30, "card": 25})               # below the ratio
    subject = conclusion_subject("(maximalSeparatedSet ε A).encard = packingNumber ε A")
    assert propose_rename("Metric.card_maximalSeparatedSet", subject, weak) is None
    assert propose_rename("Metric.card_maximalSeparatedSet", subject, split) is None


def test_no_proposal_when_the_current_prefix_is_itself_well_attested():
    """A tolerated alternative convention is not a violation.

    This guard is the main reason control PRs stay silent under generalization: without
    it, any minority-but-accepted spelling would be reported as a naming defect.
    """

    tolerated = _population({"encard": 80, "card": 20})  # card is 20% — well above MAX_CONFLICT_RATIO
    subject = conclusion_subject("(maximalSeparatedSet ε A).encard = packingNumber ε A")
    assert propose_rename("Metric.card_maximalSeparatedSet", subject, tolerated) is None


def test_no_proposal_without_a_resolved_subject_or_population():
    population = _population({"encard": MIN_SUPPORT + 1})
    unresolved = conclusion_subject("∃ C, C.encard = n")
    assert propose_rename("Metric.card_x", unresolved, population) is None
    resolved = conclusion_subject("(s).encard = n")
    assert propose_rename("Metric.card_x", resolved, None) is None


def test_generalization_reaches_the_subjects_the_frozen_operator_could_not():
    """PR 33145 `upperBounds` and PR 33337 `toLinearMap` — the B1-priced obligations."""

    upper = propose_rename(
        "Dense.continuous_upperBounds",
        conclusion_subject("upperBounds (f '' S) = upperBounds (range f)"),
        _population({"upperBounds": 40, "other": 2}, token="upperBounds"),
    )
    assert upper is not None
    assert upper.conventional_prefix == "upperBounds"
    assert upper.current_prefix == "continuous"
    assert upper.proposed_fullname == "Dense.upperBounds_upperBounds"

    linear = propose_rename(
        "Submodule.coe_starProjection_eq_isComplProjection",
        conclusion_subject("K.starProjection.toLinearMap = K.projection"),
        _population({"toLinearMap": 35, "other": 1}, token="toLinearMap"),
    )
    assert linear is not None
    assert linear.proposed_fullname.startswith("Submodule.toLinearMap_")
