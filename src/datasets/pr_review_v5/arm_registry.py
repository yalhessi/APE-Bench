"""One declaration per arm, in one place.

Adding a specialist used to mean editing thirteen source files across six packages, and four
of those edits were dictionaries keyed by arm id that had to agree with each other by hand:

    arms.CHECKABLE_ARMS        can a compile settle this arm's claims
    arms._CONTEXT_GRANTS       which retrieval tools it gets
    arm.ALLOWED_CONCERN_BY_ARM which concerns it may declare on a submission
    arm.PATCH_SET_ARMS         may it submit a coordinated multi-file patch

Two lived in `src/datasets/pr_review_v5`, two in `src/ape/tasks/.../pr_review_v5`, on opposite
sides of the package boundary, with nothing checking that an arm appeared in the right subset
of them. That is not hypothetical: `migration_consistency` was listed in `PATCH_SET_ARMS`
while never being registered as an arm at all, and the per-arm tool grant was documented in
`schema.py` as being uniform for months after `arms.py` had made it per-arm.

This module is the single source; the four structures above are now derived views of it. The
prompts, the eligibility rule and the verifier table are still elsewhere — moving those is the
arm split proper, and this is the registry it will hang off.

**Not policy about what an arm is good at.** Nothing here says which concerns matter or which
arm to prefer; those are routing and evaluation questions and live in `routing.py` and
`evaluation/` respectively. This is the arm's *contract*: what it may claim, what it may use,
and what can warrant it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Tuple

#: Granted to every arm without exception. It is registered by the shared review base for all
#: review tasks, and it is the one tool that turns a suggestion into a checked one — 87 of its
#: 100 calls on smoke4 carried a real edit.
UNIVERSAL_CONTEXT_TOOLS: Tuple[str, ...] = ("lean_verify_edit",)


@dataclass(frozen=True)
class ArmDefinition:
    """The contract for one reviewer arm."""

    arm_id: str
    #: The concern family the arm's findings are filed under.
    concern_family: str
    #: The kind of check that would settle its claim, for the verifier table.
    issue_kind: str
    #: What the arm exists to ask. Shown to no model; this is for the reader.
    rationale: str

    #: Concerns this arm may declare on a submission.
    #:
    #: Enforced today because the alternative is a silent deletion: an arm that reports a
    #: concern outside its family passes submission, then finalization drops it for lacking a
    #: verification artifact its declared concern can never produce — without a word. On the
    #: rep2 smoke run that was all four specialist candidates.
    #:
    #: Worth revisiting, and deliberately not revisited here: 11 of the 19 gold obligations
    #: labelled `style` are grind simplifications and renames, so an arm that correctly finds
    #: one and declares it honestly is rejected for guessing the evaluator's label wrong.
    #: Removing the gate requires finalization to report every drop first.
    allowed_concerns: FrozenSet[str]

    #: Retrieval tools beyond the universal grant, matched to the shape of answer this arm
    #: needs. See `_CONTEXT_GRANTS` in `arms.py` for the measurement that made this per-arm.
    context_tools: Tuple[str, ...] = ()

    #: Can a compile settle this arm's claims? A checkable arm is admitted through the
    #: verification gate; everything else must go through the evidence chain, which has so far
    #: admitted nothing (see `pr_review_v4/reachability.py`).
    checkable: bool = False

    #: May this arm submit a coordinated multi-file patch? Only an arm whose *scope* is a set
    #: of declarations has anything to coordinate.
    patch_set: bool = False

    #: v4 `FocusedAgentSpec` knobs, kept here so the whole contract reads in one place.
    component: Optional[str] = None
    extra_subject_kinds: FrozenSet[str] = frozenset()

    #: True when the arm is one of v4's four, widened by v5 rather than newly declared. The
    #: prompt and eligibility rule then come from v4's `default_specs()`.
    inherited_from_v4: bool = False

    def granted_tools(self) -> List[str]:
        return sorted(set(self.context_tools) | set(UNIVERSAL_CONTEXT_TOOLS))


def _arm(arm_id: str, concern: str, issue_kind: str, rationale: str, **kwargs) -> ArmDefinition:
    return ArmDefinition(
        arm_id=arm_id, concern_family=concern, issue_kind=issue_kind,
        rationale=rationale,
        allowed_concerns=frozenset(kwargs.pop("allowed_concerns", (concern,))),
        **kwargs,
    )


#: Every arm v5 can schedule. The generalist is deliberately absent: it has no concern filter,
#: which is what makes it the control, and it is not a `FocusedAgentSpec`.
ARM_DEFINITIONS: Tuple[ArmDefinition, ...] = (
    # --- v4's four, widened by v5 -------------------------------------------------------
    _arm("proof_golf", "proof-golf", "proof_simplification",
         "Can this proof be replaced by a canonical lemma, tactic or structure?",
         context_tools=("declaration_search",), checkable=True, component="proof",
         inherited_from_v4=True),
    _arm("proof_idiom", "proof-golf", "proof_simplification",
         "Is this proof written the way Mathlib writes this kind of proof?",
         context_tools=("declaration_search",), checkable=True, component="proof",
         inherited_from_v4=True),
    _arm("duplication", "duplication", "duplicate_implementation",
         "Does something in the library already do this?",
         context_tools=("declaration_search",), checkable=True, inherited_from_v4=True),
    _arm("generality", "generalization", "generalization_available",
         "Is this stated at the level maintainers would reuse?",
         context_tools=("declaration_search",), checkable=True, inherited_from_v4=True),

    # --- the classes v4 had no arm for -------------------------------------------------
    _arm("naming", "naming", "naming_convention_violation",
         "Is this named the way its own family is named? Settled by reading the siblings and "
         "past rename requests, not by taste.",
         # Both: what the siblings are called, and what maintainers call them. The code corpus
         # argues against the maintainer on both naming asks this release scores.
         context_tools=("declaration_search", "precedent_search", "zulip_search")),
    _arm("docs", "documentation", "documentation_gap",
         "Is the documentation complete, correct and conformant?",
         context_tools=("precedent_search", "zulip_search")),
    _arm("style", "style", "style_norm_violation",
         "Does this follow Mathlib's stated formatting and structural norms?",
         context_tools=("precedent_search", "zulip_search")),
    _arm("api_reuse", "duplication", "missed_canonical_api",
         "Is there a canonical API this should have gone through?",
         context_tools=("declaration_search",), checkable=True),
    _arm("correctness", "correctness", "correctness_policy",
         "Is there a present semantic, elaboration, build or policy error?",
         # `scope` too: a declaration whose imports cannot support where it sits is a build
         # problem wearing a placement problem's clothes, and no other arm compiles.
         allowed_concerns=("correctness", "scope"),
         context_tools=("declaration_search",), checkable=True),
    _arm("family_design", "generalization", "generalization_available",
         "Are these declarations right AS A GROUP — a missing dual, a hand-written generated "
         "form, a hardcoded shared parameter?",
         # It owns both shapes a group's defect takes, which is why it may declare either.
         allowed_concerns=("generalization", "duplication"),
         # No `declaration_search`: it spent 50 of 63 retrieval calls on a name lookup that
         # cannot answer a question about a group's shape, and returned nothing from eleven
         # invocations.
         context_tools=("precedent_search", "zulip_search"),
         patch_set=True),
)

BY_ID: Dict[str, ArmDefinition] = {item.arm_id: item for item in ARM_DEFINITIONS}


def arm_ids() -> Tuple[str, ...]:
    return tuple(sorted(BY_ID))


def checkable_arms() -> FrozenSet[str]:
    """Arms whose claims a compile can settle."""

    return frozenset(item.arm_id for item in ARM_DEFINITIONS if item.checkable)


def patch_set_arms() -> FrozenSet[str]:
    """Arms that may submit a coordinated multi-file patch."""

    return frozenset(item.arm_id for item in ARM_DEFINITIONS if item.patch_set)


def context_grants() -> Dict[str, Tuple[str, ...]]:
    """`arm_id -> the retrieval tools it is granted`, beyond the universal set."""

    return {item.arm_id: item.context_tools for item in ARM_DEFINITIONS}


def allowed_concerns() -> Dict[str, FrozenSet[str]]:
    """`arm_id -> the concerns it may declare on a submission`."""

    return {item.arm_id: item.allowed_concerns for item in ARM_DEFINITIONS}
