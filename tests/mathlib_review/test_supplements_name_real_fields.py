"""A supplement may only tell the arm to write into a field the submission actually has.

All four ladder supplements ended with "state in `rationale` ...", and `CandidateSubmission`
has no `rationale` field. So every "say what you attempted" instruction in the ladder was inert,
and rung 3c's finding -- that the arm produced a compiling `grind [minimalCover]` and submitted
`simpa` -- came with no stated reason partly because there was nowhere to state one.

This guard is the general fix. The instance was cheap to correct; an instruction pointing at a
field that does not exist is invisible until someone reads a transcript looking for the answer
it was supposed to produce.
"""

from __future__ import annotations

import re

from ape.tasks.lean_tasks.formal_math.review.candidates import (
    CandidateSubmission, RejectedAlternative,
)
from ape.tasks.lean_tasks.formal_math.review.focused_prompts import (
    PROCEDURE_SUPPLEMENTS, procedure_supplement,
)

#: Fields an arm can actually write to, across the submission and its nested models.
WRITABLE = (set(CandidateSubmission.model_fields)
            | set(RejectedAlternative.model_fields))

#: Backticked words in a supplement that are not submission fields: tools, tactics, Lean syntax.
#: Listed rather than inferred, so a new one is a deliberate addition.
NOT_FIELDS = {
    "proof_profile", "get_lean_goal", "lean_verify_edit", "content_search",
    "declaration_search", "grind", "grind [<lemma>]", "simpa", "have",
}


def test_no_supplement_directs_the_arm_to_a_field_that_does_not_exist():
    for variant in PROCEDURE_SUPPLEMENTS:
        supplement = procedure_supplement(variant, "proof_idiom")
        if not supplement:
            continue
        # Only the phrasings that direct output somewhere: "in `x`", "state in `x`",
        # "goes in `x`". A backticked tool name elsewhere in the prose is not a claim
        # about the schema.
        directed = re.findall(r"(?:in|into) `([a-z_]+)`", supplement)
        for name in directed:
            if name in NOT_FIELDS:
                continue
            assert name in WRITABLE, (
                f"{variant} tells the arm to write into `{name}`, which is not a field of "
                f"CandidateSubmission or RejectedAlternative. Writable: {sorted(WRITABLE)}")


def test_the_supplements_still_direct_output_somewhere():
    """Guarding against a fix that removes the instruction instead of correcting it."""

    for variant in ("rung3a", "rung3b", "rung3c", "rung3d"):
        supplement = procedure_supplement(variant, "proof_idiom")
        assert re.search(r"(?:in|into) `[a-z_]+`", supplement), variant


def test_every_rung_routes_a_discarded_compiling_edit_to_the_field_that_records_one():
    """The one thing the artifacts could not express. Each rung that has the arm attempt
    several alternatives must send the losers somewhere durable."""

    for variant in ("rung3a", "rung3b", "rung3c", "rung3d"):
        assert "rejected_alternatives" in procedure_supplement(variant, "proof_idiom"), variant


def test_a_rejection_cannot_be_recorded_without_a_reason():
    import pydantic
    import pytest

    RejectedAlternative(replacement="by grind [foo]", compiled=True, why_not="chose simpa")
    with pytest.raises(pydantic.ValidationError):
        RejectedAlternative(replacement="by grind [foo]", compiled=True)
