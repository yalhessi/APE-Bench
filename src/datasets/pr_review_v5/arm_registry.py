"""One declaration per arm, in one place.

Adding a specialist used to mean editing thirteen source files across six packages, and four
of those edits were dictionaries keyed by arm id that had to agree with each other by hand:

    arms.CHECKABLE_ARMS        can a compile settle this arm's claims
    arms._CONTEXT_GRANTS       which retrieval tools it gets
    arm.ALLOWED_CONCERN_BY_ARM which concerns it may declare on a submission (now
                               arm.EXPECTED_CONCERN_BY_ARM, and no longer a gate)
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
    #: What the arm exists to ask, in the arm's own words.
    #:
    #: Written twice until now: once here as a one-line summary "for the reader", and once in
    #: `arms.v5_specs()` as the fuller text that reaches the agenda -- and through it a lead
    #: reading the flat proposal list. All ten disagreed, as two hand-maintained paraphrases
    #: of one question will, and `docs` had a measurement in one of them and not the other.
    #: The fuller text won and lives here; `v5_specs` reads it.
    rationale: str

    #: Concerns this arm is expected to report. Provenance and routing vocabulary — read by
    #: the per-arm benches to decide which gold obligations this arm is answerable for, and
    #: recorded on a submission that falls outside it. **Not** an admission rule.
    #:
    #: It was one until the drop it guarded stopped being silent. The argument for enforcing
    #: it was that an arm reporting an unexpected concern passes submission and is then
    #: dropped at finalization for lacking a verification artifact its declared concern can
    #: never produce, without a word — on the rep2 smoke run, all four specialist candidates.
    #: Refusing up front at least told the arm.
    #:
    #: The cost was findings: 11 of the 19 gold obligations labelled `style` are grind
    #: simplifications and `encard_` renames, so an arm that correctly finds one and declares
    #: it honestly was refused for guessing the evaluator's label wrong. With every drop now
    #: retained as a `diagnostic` finding the judge can score, refusing buys nothing and still
    #: costs that.
    expected_concerns: FrozenSet[str]

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
    #: Changed things that are not declarations, which this arm may also speak about.
    #:
    #: The modification inventory for the medium release holds 49 `module_doc`, 46
    #: `namespace_or_section`, 91 `command` and 17 `import` records, and for a long time *no
    #: arm accepted any of them* because every spec took `DECLARATION_KINDS` alone. Two gold
    #: obligations were unreachable purely because of that: PR 33305 asks to wrap an over-long
    #: line in a module doc, and PR 33362 asks to move declarations inside `namespace Complex`.
    #: Both are ordinary review comments about things no arm was allowed to look at.
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
        expected_concerns=frozenset(kwargs.pop("expected_concerns", (concern,))),
        **kwargs,
    )


#: Changed things that are not declarations. Named here rather than in `arms.py` so an arm's
#: whole contract, including what it is allowed to look at, reads in one place.
MODULE_DOC_KINDS = frozenset({"module_doc"})
PLACEMENT_KINDS = frozenset({"namespace_or_section", "command", "import"})


#: Every arm v5 can schedule. The generalist is deliberately absent: it has no concern filter,
#: which is what makes it the control, and it is not a `FocusedAgentSpec`.
ARM_DEFINITIONS: Tuple[ArmDefinition, ...] = (
    # --- v4's four, widened by v5 -------------------------------------------------------
    _arm("proof_golf", "proof-golf", "proof_simplification",
         "Can a proof this PR changed be written shorter? Verified by recompiling.",
         context_tools=("declaration_search",), checkable=True, component="proof",
         inherited_from_v4=True),
    _arm("proof_idiom", "proof-golf", "proof_simplification",
         "Is a changed proof written the canonical way — `grw`/`gcongr`, `simp`, "
         "`omega`/`grind`, `fun_prop`, the canonical lemma? Explicitly not about length, which "
         "is why it needs its own warrant.",
         context_tools=("declaration_search",), checkable=True, component="proof",
         inherited_from_v4=True),
    _arm("duplication", "duplication", "duplicate_implementation",
         "Does a new declaration restate something Mathlib already has? Verified by closing "
         "the new declaration with the existing one.",
         context_tools=("declaration_search",), checkable=True, inherited_from_v4=True),
    _arm("generality", "generalization", "generalization_available",
         "Is a new declaration stated less generally than it should be? The statement must "
         "move, which is the gate that separates it from a golf finding.",
         context_tools=("declaration_search",), checkable=True, inherited_from_v4=True),

    # --- the classes v4 had no arm for -------------------------------------------------
    _arm("naming", "naming", "naming_convention_violation",
         "Is this declaration named the way its own family is named? Settled by reading the "
         "siblings and past rename requests, not by taste.",
         # Both: what the siblings are called, and what maintainers call them. The code corpus
         # argues against the maintainer on both naming asks this release scores.
         context_tools=("declaration_search", "precedent_search", "zulip_search")),
    _arm("docs", "documentation", "documentation_gap",
         "Is the documentation COMPLETE, CORRECT and CONFORMANT — in that "
         "order?\n  * complete: a sentence that stops mid-thought, a hypothesis or a `TODO` "
         "left unexplained, a module whose non-obvious approach has no `Implementation "
         "details` note. This is the most requested and the least often "
         "noticed.\n  * correct: a typo, or a statement the code "
         "contradicts.\n  * conformant: over-long lines and malformed markup, which the "
         "repository's own linter can "
         "settle.\nA docstring that is merely terse is not a finding. Neither is a "
         "cross-reference you have not opened and confirmed is wrong.",
         context_tools=("precedent_search", "zulip_search"),
         extra_subject_kinds=MODULE_DOC_KINDS),
    _arm("style", "style", "style_norm_violation",
         "Is this formatted and placed the way the surrounding file does it? Only a deviation "
         "from a convention the file is otherwise consistent about — including where a "
         "declaration sits: a lemma that belongs inside a `namespace` block and was left "
         "outside it is a placement defect, not a matter of taste.",
         context_tools=("precedent_search", "zulip_search"),
         extra_subject_kinds=MODULE_DOC_KINDS | PLACEMENT_KINDS),
    _arm("api_reuse", "duplication", "missed_canonical_api",
         "Does the code re-derive something the library already provides, or spell an existing "
         "API the long way? Smaller and commoner than whole-declaration duplication, and "
         "checkable by compiling the replacement.",
         context_tools=("declaration_search",), checkable=True),
    _arm("correctness", "correctness", "correctness_policy",
         "Is anything actually broken — the build, a statement that does not say what it "
         "claims, a looping simp lemma, an unaccepted axiom? Starts by compiling the reviewed "
         "file, which no other arm does.",
         # `scope` too: a declaration whose imports cannot support where it sits is a build
         # problem wearing a placement problem's clothes, and no other arm compiles.
         expected_concerns=("correctness", "scope"),
         context_tools=("declaration_search",), checkable=True),
    _arm("family_design", "generalization", "generalization_available",
         "Are these declarations right AS A GROUP — a dual proved from scratch instead of from "
         "its counterpart, a missing counterpart, a generated form written by hand, a repeated "
         "argument that should be one lemma?",
         # It owns both shapes a group's defect takes, which is why it may declare either.
         expected_concerns=("generalization", "duplication"),
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


def expected_concerns() -> Dict[str, FrozenSet[str]]:
    """`arm_id -> the concerns it is expected to report`.

    Was `allowed_concerns`, and the rename is the change: nothing refuses a submission on
    this any more. It says what an arm is for, which is what the benches need and what makes
    an off-concern claim worth recording.
    """

    return {item.arm_id: item.expected_concerns for item in ARM_DEFINITIONS}
