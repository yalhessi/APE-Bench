"""A ladder rung must be a switchable treatment, not an edit to the baseline.

Rung 0 established that both proof arms reach every site of PR33098's `grind` family, locate
5 of 5, compile 44 candidate edits between them, and propose `simpa` 51 times and `grind` zero
times. Rung 3a tests whether that is a procedure failure: it requires the arm to carry out the
search its prompt already describes, over the tactic families its prompt already names.

For the rung to mean anything, the baseline it is compared against must be unmoved — so the
treatment is an appended, named supplement rather than a rewrite, and the name travels into the
run's identity.
"""

from __future__ import annotations

import pytest

from ape.tasks.lean_tasks.formal_math.review.focused_prompts import (
    PROCEDURE_SUPPLEMENTS, procedure_supplement,
)
from src.mathlib_review.agenda.focused_specs import default_specs
from src.mathlib_review.agenda.render_focused import (
    FOCUSED_RENDERER_VERSION, focused_system_prompt,
)

SPECS = {spec.spec_id: spec for spec in default_specs()}


def test_an_unknown_variant_raises_rather_than_running_the_baseline():
    """A typo'd variant name that returned nothing would run the baseline under the
    treatment's name and be reported as a rung result."""

    with pytest.raises(ValueError) as excinfo:
        procedure_supplement("rung3z", "proof_idiom")
    assert "unknown procedure variant" in str(excinfo.value)


def test_baseline_leaves_every_prompt_exactly_as_written():
    for arm_id in PROCEDURE_SUPPLEMENTS["rung3a"]:
        assert procedure_supplement("baseline", arm_id) == ""


def test_rung3a_treats_only_the_proof_arms():
    treated = {arm for arm in SPECS
               if focused_system_prompt(SPECS[arm], "rung3a")
               != focused_system_prompt(SPECS[arm], "baseline")}
    assert treated == {"proof_idiom", "proof_golf"}


def test_rung3a_adds_procedure_and_not_a_tactic_recommendation():
    """The supplement must not re-weight the tactic list, or it becomes rung 3b wearing 3a's
    name: a rung that smuggles in evidence cannot attribute its own result.
    """

    for arm_id in ("proof_idiom", "proof_golf"):
        baseline = focused_system_prompt(SPECS[arm_id], "baseline")
        treated = focused_system_prompt(SPECS[arm_id], "rung3a")
        assert len(treated) > len(baseline)
        # No tactic named in the supplement at all -- the families are referenced, never
        # re-listed, so the supplement cannot privilege one of them.
        #
        # Checked on the backticked form, which is how every prompt in this file names a
        # tactic. A bare-substring check fails on English: "decide what to propose" is not a
        # reference to the `decide` tactic, and the looser test reported it as one.
        supplement = procedure_supplement("rung3a", arm_id)
        for tactic in ("grind", "simpa", "simp only", "simp_all", "omega", "gcongr", "grw",
                       "decide", "by_cases", "by_cases!", "fun_prop", "aesop", "OrderDual"):
            assert f"`{tactic}" not in supplement, f"`{tactic}` named in the 3a supplement"
        # And the two that have no innocent English reading are absent outright.
        for tactic in ("grind", "simpa", "gcongr"):
            assert tactic not in supplement, f"{tactic} named in the 3a supplement"
        # And the baseline's own mentions are untouched.
        assert treated.count("grind") == baseline.count("grind")
        # It does require the goal inspection neither arm has ever performed.
        assert "get_lean_goal" in supplement
        assert "lean_verify_edit" in supplement
        # No PR-specific term, and nothing gold-derived.
        for leak in ("33098", "minimalCover", "maximalSeparatedSet", "encard_", "684"):
            assert leak not in supplement, f"{leak} leaked into the 3a supplement"


def test_the_variant_name_reaches_the_renderer_version():
    """A prompt hash says two runs differed; the name says how, without reading the prompt.

    `baseline` must stay spelled as the bare version, or every artifact rendered before
    variants existed would read as a different renderer.
    """

    from src.mathlib_review.agenda.render_focused import renderer_version_for

    assert renderer_version_for("baseline") == FOCUSED_RENDERER_VERSION
    assert renderer_version_for() == FOCUSED_RENDERER_VERSION
    assert renderer_version_for("rung3a") == f"{FOCUSED_RENDERER_VERSION}+rung3a"
