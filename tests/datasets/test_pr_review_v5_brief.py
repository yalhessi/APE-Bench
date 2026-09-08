"""The delegation brief: what the lead knows, reaching the specialist that needs it.

Before this, `DelegationRequest.reason` was recorded in the ledger and the child was built
from the sealed payload unchanged — so the subagent saw only its generic arm prompt. The cost
was measurable. In one case the lead delegated a `generality` job whose reason named a
*naming* concern; the child never saw it, reported a style issue instead, had it rejected at
the arm gate, and submitted nothing — while its own precedent search had already returned the
exact rename convention the maintainer wanted.

The brief is framed as a question throughout, and these tests pin that framing as hard as
they pin the plumbing. An arm told what to find will find it, and the entire warrant of this
pipeline is that a specialist established its claim independently and a compiler agreed.
"""

from __future__ import annotations

import asyncio
import hashlib
import json

import pytest

from ape.tasks.lean_tasks.formal_math.review.delegation import (
    JobSpec,
    compose_prompt,
)
from ape.tasks.lean_tasks.formal_math.review.lead import InvestigationBrief


def _brief(**overrides):
    payload = dict(
        question="Does `Foo.bar` restate the existing `Baz.qux`?",
        because="The floor flagged this declaration and the diff adds it wholesale.",
        look_at=["Foo.bar"],
        already_checked="`Baz.qux` exists at this commit and has the same statement shape.",
        abstain_if="the two differ in their hypotheses",
    )
    payload.update(overrides)
    return InvestigationBrief(**payload)


# --------------------------------------------------------------------------------------
# framing
# --------------------------------------------------------------------------------------

def test_the_brief_presents_itself_as_a_hypothesis():
    """The single most important property. A brief that reads as a verdict turns the lead
    into an unverified author with extra steps."""

    text = _brief().render("duplication")
    lowered = text.lower()
    assert "hypothesis, not a finding" in lowered
    assert "has not been verified" in lowered
    assert "may be wrong" in lowered


def test_it_gives_explicit_permission_to_find_nothing():
    """An arm handed a suspicion feels obliged to confirm it; saying otherwise is cheap."""

    text = _brief().render("duplication").lower()
    assert "refuted hypothesis is a correct outcome" in text
    assert "return nothing if" in text


def test_it_does_not_widen_the_arm_s_concern():
    """The brief is context, not a licence. An arm that follows a brief outside its concern
    has its findings rejected at submission, which is the same silent loss in a new costume."""

    text = _brief().render("duplication")
    assert "does not widen your scope" in text
    assert "duplication check" in text
    assert "drop it rather than restating it as yours" in text


def test_the_arm_is_named_in_its_own_brief():
    assert "naming check" in _brief().render("naming")
    assert "proof_golf check" in _brief().render("proof_golf")


# --------------------------------------------------------------------------------------
# content
# --------------------------------------------------------------------------------------

def test_every_field_reaches_the_rendered_text():
    text = _brief().render("duplication")
    assert "Does `Foo.bar` restate the existing `Baz.qux`?" in text
    assert "The floor flagged this declaration" in text
    assert "`Foo.bar`" in text
    assert "do not re-derive" in text.lower()
    assert "the two differ in their hypotheses" in text


def test_a_bare_question_still_renders():
    """Only `question` is required; a lead with nothing else to add must still be able to
    ask something rather than being pushed into inventing supporting detail."""

    text = InvestigationBrief(question="Is this proof shorter with `grind`?").render("proof_golf")
    assert "Is this proof shorter with `grind`?" in text
    assert "hypothesis, not a finding" in text.lower()


def test_a_question_is_required():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        InvestigationBrief(because="something looked off")


def test_unknown_fields_are_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        InvestigationBrief(question="q", verdict="it duplicates")


# --------------------------------------------------------------------------------------
# delivery
# --------------------------------------------------------------------------------------

def test_the_brief_is_appended_to_the_sealed_prompt_not_substituted():
    """The arm's own instructions are what the plan vouched for; the brief is additive."""

    payload = {"rendered_user_prompt": "ARM INSTRUCTIONS", "arm_id": "duplication"}
    composed = compose_prompt(payload, _brief().render("duplication"))
    assert composed["rendered_user_prompt"].startswith("ARM INSTRUCTIONS")
    assert "hypothesis, not a finding" in composed["rendered_user_prompt"].lower()
    # the original is not mutated
    assert payload["rendered_user_prompt"] == "ARM INSTRUCTIONS"


def test_no_brief_leaves_the_payload_untouched():
    """A job without a brief must be byte-identical to what earlier runs dispatched, so the
    brief is a clean ablation rather than a confound."""

    payload = {"rendered_user_prompt": "ARM INSTRUCTIONS", "arm_id": "duplication"}
    assert compose_prompt(payload, "") is payload


def test_the_delivered_prompt_hash_differs_when_a_brief_is_attached():
    """The sealed plan vouches for the template; `delivered_prompt_sha256` records what was
    actually read. They must be distinguishable or the pre-registration quietly stops
    describing the run."""

    base = {"rendered_user_prompt": "ARM INSTRUCTIONS", "arm_id": "duplication"}
    sealed = hashlib.sha256(base["rendered_user_prompt"].encode()).hexdigest()
    composed = compose_prompt(base, _brief().render("duplication"))
    delivered = hashlib.sha256(composed["rendered_user_prompt"].encode()).hexdigest()
    assert delivered != sealed


def test_a_job_spec_carries_both_the_text_and_the_record():
    """The rendered text is what the model reads; the structured form is what the ledger
    keeps, so an analysis can ask what was briefed without re-parsing prose."""

    brief = _brief()
    spec = JobSpec("wu:1#duplication", "duplication", "wu:1", 1, {},
                   brief_text=brief.render("duplication"), brief=brief.model_dump())
    assert spec.brief["question"] == brief.question
    assert "hypothesis" in spec.brief_text.lower()


def test_the_lead_prompt_asks_for_questions_not_answers():
    from ape.tasks.lean_tasks.formal_math.review.prompts import LEAD_SYSTEM

    assert "question, not an answer" in LEAD_SYSTEM
    assert "A brief that turns out to be wrong is a good brief" in LEAD_SYSTEM
    assert "Every delegation carries a brief" in LEAD_SYSTEM
