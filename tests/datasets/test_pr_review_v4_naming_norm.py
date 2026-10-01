"""Gates for the subject-general naming checker.

The frozen `naming_contrast` operator reaches one subject (`Set.encard`), which is why
C2 was 5/40 with nothing outside the development PR. These tests pin the generalization
against the *real* conclusions from the medium benchmark — including the coercion
ascription that a naive head rule misreads as a bound variable — and pin the guards that
keep the rule from firing where the corpus has no opinion.
"""

from collections import Counter

import pytest

from src.mathlib_review.evidence.operators.naming_norm import (
    MIN_SUPPORT,
    MIN_SUPPORT_RATIO,
    SubjectPopulation,
    conclusion_subject,
    leaf_prefix,
    norm_verdict,
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


def test_an_empty_naming_verdict_says_which_of_three_things_happened():
    """One sentence used to stand for three causes, and it asserted the third.

    `subject.token is None`, `subject.confidence != "high"` and `population is None` all
    returned "The corpus has no counted opinion about this declaration's subject ... Submit
    nothing on naming". The first two are this tool failing to parse a subject out of the
    conclusion; only the third is a fact about the repository. So a tool failure was reported
    to the arm as the repository having no convention, with an instruction to be silent
    attached -- and 477 of 632 calls across the three held-out reps came back empty with
    nothing to say which had happened.

    The distinction matters for what the arm does next: an unmeasured subject is a reason to
    fall back on its own judgement, and a counted corpus with no population is a reason to
    drop the question.
    """

    import inspect

    from ape.tasks.lean_tasks.formal_math.review import context_tools
    from src.mathlib_review.schema.review import ContextCall

    source = inspect.getsource(context_tools)
    assert 'cause = "subject_unresolved" if unresolved else "no_population"' in source

    # The unresolved branch must not tell the arm the corpus was consulted, and must not
    # instruct silence -- that instruction is what the measured behaviour followed.
    unresolved_text = source.split('if unresolved:', 1)[1].split('return {', 1)[1].split('}', 1)[0]
    assert "could not work out what this declaration is ABOUT" in unresolved_text
    assert "limit of" in unresolved_text
    assert "Submit nothing" not in unresolved_text

    # The corpus branch says the corpus was counted, and scopes the silence to what was counted:
    # "Submit nothing on naming" claimed the whole name for a census of leading prefixes
    # (2026-09-24), the same over-claim the counted branch made at both held-out naming misses.
    corpus_text = source.split('"no_population"', 1)[1]
    assert "holds no counted population" in corpus_text
    assert "Submit nothing about the prefix" in corpus_text
    no_population_text = corpus_text.split("return {", 1)[1].split("}", 1)[0]
    assert "Submit nothing on naming" not in no_population_text

    # And the trace carries the cause, declared on the row model rather than smuggled into a
    # dict -- a trace row that does not validate is how a vocabulary goes unchecked.
    annotation = ContextCall.model_fields["empty_because"].annotation
    assert "subject_unresolved" in str(annotation) and "no_population" in str(annotation)
    row = ContextCall(invocation_id="wu:a#naming", tool="naming_norm", query="Foo.bar",
                      gate="base_snapshot", empty_because="subject_unresolved")
    assert row.empty_because == "subject_unresolved"
    # Rows written before the split still load.
    assert ContextCall(invocation_id="wu:a#naming", tool="naming_norm", query="Foo.bar",
                       gate="base_snapshot").empty_because is None


def test_the_tool_description_scopes_the_silence_to_the_cause_that_warrants_it():
    """The results text was split and the description was not, so they contradicted.

    97.3% of the 477 recorded empty calls are `subject_unresolved` -- the tool never asked the
    corpus -- and the description told the arm that `insufficient_evidence` means the corpus
    has no opinion and it should submit nothing. An arm reading the description rather than the
    result would draw the conclusion the split exists to prevent, on almost every empty call.
    """

    import inspect

    from ape.tasks.lean_tasks.formal_math.review import context_tools

    source = inspect.getsource(context_tools)
    assert "no opinion here and you should submit nothing" not in source
    assert "`no_population`" in source and "`subject_unresolved`" in source
    assert "UNMEASURED rather than settled" in source


def test_a_counted_verdict_claims_no_more_than_the_prefix_it_measured():
    """At both held-out naming misses the arm's stated reason for silence was the tool's sentence
    "The corpus does not back a rename here. Submit nothing on naming." -- after counting only the
    leading token (`round_eq'`, whose ask was a suffix change; a coercion lemma whose `coe_` lead was
    48 of 124). The counted branch now reports which of three things it found and says outright
    that the rest of the name is unmeasured, and the description scopes every verdict the same way."""

    import inspect

    from ape.tasks.lean_tasks.formal_math.review import context_tools

    source = inspect.getsource(context_tools)
    assert 'lines.append("The corpus does not back a rename here' not in source
    assert "counts only each name's LEADING token" in source
    assert "a plurality (" in source and "is the convention for this subject" in source
    assert "the name's LEADING prefix only: the tool does not measure a suffix" in source


# Populations as the tool returned them on the 2026-09-30 gpt runs (`counts`, `members`).
DIST = {"dist": 397, "mul": 10, "prod": 5, "aposteriori": 1, "apriori": 1, "embeddingOfSubset": 1,
        "eq": 1, "finite": 1, "other": 7}
OF_ALG_EQUIV = {"ofAlgEquiv": 4}


def test_a_name_that_follows_its_convention_is_an_answer_not_missing_evidence():
    """`dist_` 397 of 424 came back `insufficient_evidence` beside a sentence saying `dist_` is the
    convention, so the verdict told the reviewer the census settled nothing while the text said it
    settled everything. Replayed over the 43 counted empty verdicts of six gpt runs, 15 were this."""

    assert norm_verdict(_population(DIST, "dist"), "dist") == ("conforms", None)
    # The same population still asks for the rename when the name does not follow it.
    assert norm_verdict(_population(DIST, "dist"), "mul")[0] in ("established", "emerging")


def test_every_counted_empty_verdict_says_which_of_two_things_it_found():
    """`ofAlgEquiv_` 4 of 4 was reported as "only a plurality (4 of 4, under the 80% bar)": the
    census had too few to count, not a divided corpus. An `insufficient_evidence` now carries
    `population_too_small` or `no_dominant_prefix`, and an answer carries no reason."""

    assert norm_verdict(_population(OF_ALG_EQUIV, "ofAlgEquiv"), "ofAlgEquiv") == (
        "insufficient_evidence", "population_too_small")
    # The coercion lemma whose `coe_` lead was 48 of 124: a plurality, under the bar.
    coercion = {"coe": 48, "toLinearMap": 40, "apply": 36}
    assert norm_verdict(_population(coercion, "toLinearMap"), "coe") == (
        "insufficient_evidence", "no_dominant_prefix")

    # Exhaustively over small two-spelling populations: the reason is set exactly when the verdict
    # is empty, and the two reasons are the whole vocabulary (a strong population always answers).
    seen = set()
    for lead in range(1, 2 * MIN_SUPPORT + 1):
        for other in range(0, lead + 1):
            for current in ("a", "b", "c"):
                counts = {"a": lead, "b": other} if other else {"a": lead}
                verdict, because = norm_verdict(_population(counts), current)
                assert (verdict == "insufficient_evidence") == (because is not None)
                seen.add(because)
                if because == "population_too_small":
                    assert lead < MIN_SUPPORT
                if because == "no_dominant_prefix":
                    assert lead >= MIN_SUPPORT and lead / (lead + other) < MIN_SUPPORT_RATIO
    assert seen == {None, "population_too_small", "no_dominant_prefix"}


def test_the_registered_description_names_every_verdict_and_reason():
    """The description quotes the thresholds, and they were imported inside the call, after the
    decorator had already run: registration raised `NameError` before any test built it. Build it."""

    from typing import get_args

    from ape.tasks.lean_tasks.formal_math.review import context_tools
    from src.mathlib_review.schema.review import ContextCall

    captured = {}

    class CapturingMCP:
        def tool(self, **kwargs):
            def decorate(fn):
                captured[fn.__name__] = kwargs
                return fn
            return decorate

    context_tools._register_naming_norm(None, CapturingMCP())
    description = captured["naming_norm"]["description"]
    reasons = [r for r in get_args(get_args(ContextCall.model_fields["empty_because"].annotation)[0])]
    for word in ["established", "emerging", "conforms", "insufficient_evidence", *reasons]:
        assert f"`{word}`" in description, word
    assert f"fewer than {MIN_SUPPORT} declarations" in description
    assert f"{MIN_SUPPORT_RATIO:.0%} bar" in description
