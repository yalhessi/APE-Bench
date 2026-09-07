"""The registry of specialists the lead may call, and the eligibility rule behind each.

Two properties this file exists to preserve.

**Adding an arm stays a row plus a prompt.** That is true of v2's checkers (a tool list, a
prompt pair, `register_task`) and of v4's focused specs, and it is the reason the arm set
could grow at all. A registry that can only be extended by writing a new task class stops
being extended.

**Eligibility is delegated, not reimplemented.** The specialists reuse v4's
`FocusedAgentSpec.applies_to` verbatim rather than restating its rule. That rule encodes a
measured scoping decision — golf and idiom run on `modified` proofs only, because a brand
new proof is not a simplification *of* anything and scheduling both lifecycles would put
all four specs on all 131 added theorems at medium — and a second copy of it would drift
from the version the v2 recall baseline was measured under.

The generalist is not a `FocusedAgentSpec` and does not pretend to be one. It runs on every
work unit, which is not a rule any spec predicate can express, and it is `mandatory`: the
lead may prune specialists but can never drop below the coverage floor.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from dataclasses import replace

from src.datasets.pr_review_v4.focused_specs import (
    DECLARATION_KINDS,
    FocusedAgentSpec,
    _prompt_hashes,
    default_specs,
)
from src.datasets.pr_review_v4.io import canonical_json_bytes, sealed_model, sha256_bytes

from .schema import CONTEXT_TOOLS, ReviewArm

ARM_REGISTRY_VERSION = "v5-arm-registry/2"

#: Every arm — generalist and specialist alike — is the same registered task type. Only its
#: prompt, its tools and its context grant differ. Keeping one task class keeps the
#: submission contract single-implementation, which is the lesson v4 already encodes: its
#: focused arm subclasses the candidate task rather than forking it, because a second
#: implementation of `change_ids ⊆ unit`, subject equality, the entity check, the statement
#: gate and edit confinement is a second thing to keep correct.
ARM_TASK_TYPE = "lean_pr_review_v5_arm"

GENERALIST_ARM_ID = "generalist"

#: Measured billed cost per invocation, from the rep5 smoke run re-priced under the
#: `prompt_inclusive` cost model: floor jobs ran a median $0.046 and specialists $0.039.
#: The previous anchor of $0.079 came from the medium runbook, which was computed under the
#: old model that double-charged cached tokens — so it was roughly 1.7x the real figure and
#: made every dry-run projection pessimistic by the same factor.
COST_HINT_PER_WORK_UNIT = 0.05



#: Lifecycles a v5 specialist may be scheduled on.
#:
#: v4 restricts proof_golf and proof_idiom to `modified` proofs, on the reasoning that a
#: brand-new proof "is not a simplification *of* anything". That reasoning holds for a
#: diff-comparison framing and is wrong for this corpus. Measured on the medium smoke set:
#: **all 22 gold change targets in PRs 33066/33098 have lifecycle `added`**, and PR 33098's
#: gold is dominated by proof-simplification asks — "replace the case-split proof with
#: `grind [minimalCover]`", "simplify with the requested grind-based treatment". Under v4's
#: rule both proof arms were marked ineligible at *every one* of those sites.
#:
#: Maintainers routinely ask for a better proof of a newly added lemma. The arm has to be
#: allowed to look.
_BOTH_LIFECYCLES = frozenset({"added", "modified"})

V5_SPEC_VERSION = "focused/1-v5"


def _relaxed(spec: FocusedAgentSpec) -> FocusedAgentSpec:
    """A v4 spec with its lifecycle filter widened, and a version that says so.

    `source_sha256` derives from `identity()`, so the new version and lifecycles change the
    spec's identity automatically — a v5 run can never be confused with a v4 one that shared
    a spec_id.
    """

    return replace(spec, lifecycles=_BOTH_LIFECYCLES, spec_version=V5_SPEC_VERSION)


#: Changed things that are not declarations. The modification inventory for the medium
#: release holds 49 `module_doc`, 46 `namespace_or_section`, 91 `command` and 17 `import`
#: records — and until now *no arm accepted any of them*, because every spec took
#: `DECLARATION_KINDS`. Two gold obligations are unreachable purely because of that: PR
#: 33305 asks to wrap an over-long line in a module doc, and PR 33362 asks to move
#: declarations inside `namespace Complex`. Both are ordinary review comments about things
#: no arm was allowed to look at.
MODULE_DOC_KINDS = frozenset({"module_doc"})
PLACEMENT_KINDS = frozenset({"namespace_or_section", "command", "import"})


def _new_spec(spec_id: str, concern_family: str, issue_kind: str, rationale: str,
              *, component: Optional[str] = None,
              extra_subject_kinds: frozenset = frozenset(),
              lifecycles: frozenset = _BOTH_LIFECYCLES) -> FocusedAgentSpec:
    hashes = _prompt_hashes()
    return FocusedAgentSpec(
        spec_id=spec_id,
        spec_version=V5_SPEC_VERSION,
        task_type=ARM_TASK_TYPE,
        concern_family=concern_family,
        issue_kind=issue_kind,
        lifecycles=lifecycles,
        component=component,
        subject_kinds=DECLARATION_KINDS | extra_subject_kinds,
        prompt_sha256=hashes[spec_id][0],
        tools_sha256=hashes[spec_id][1],
        rationale=rationale,
    )


def v5_specs() -> List[FocusedAgentSpec]:
    """The specialist set v5 schedules: v4's four, widened, plus the four classes it lacks.

    The additions are not speculative. On the medium smoke set the gold that no v4 arm could
    own was: three `encard_` prefix renames, a docstring typo, a section-formatting request,
    and a build break — naming, docs/style, and correctness respectively. `api_reuse` covers
    the smaller sibling of duplication that kept surfacing as "use the existing lemma here"
    inside an otherwise fine declaration.
    """

    widened = [_relaxed(spec) for spec in default_specs()]
    return widened + [
        _new_spec(
            "naming", "naming", "naming_convention_violation",
            "Is this declaration named the way its own family is named? Settled by reading "
            "the siblings and past rename requests, not by taste.",
        ),
        # Split from a single docs+style arm because the rendered submission contract
        # names ONE concern_family, so a style finding from a documentation-declared arm
        # would be filed as documentation — and the judge gates on concern kind, so the
        # mislabelling would lose the match it was trying to make.
        _new_spec(
            "docs", "documentation", "documentation_gap",
            # Rewritten against what maintainers actually asked for. Measured on heldout11:
            # every one of 16 documentation candidates was a *contradiction* claim — "the
            # docstring says X, the code says Y" — while the three documentation obligations
            # in gold asked to finish an unfinished sentence, correct a typo, and add an
            # "Implementation details" discussion explaining a non-obvious proof approach.
            # Accuracy is one of three things a docstring can fail at, and it was the only
            # one being checked. Three of the 16 landed on control PRs, where maintainers
            # asked for nothing at all.
            "Is the documentation COMPLETE, CORRECT and CONFORMANT — in that order?\n"
            "  * complete: a sentence that stops mid-thought, a hypothesis or a `TODO` left "
            "unexplained, a module whose non-obvious approach has no `Implementation "
            "details` note. This is the most requested and the least often noticed.\n"
            "  * correct: a typo, or a statement the code contradicts.\n"
            "  * conformant: over-long lines and malformed markup, which the repository's "
            "own linter can settle.\n"
            "A docstring that is merely terse is not a finding. Neither is a cross-reference "
            "you have not opened and confirmed is wrong.",
            extra_subject_kinds=MODULE_DOC_KINDS,
        ),
        _new_spec(
            "style", "style", "style_norm_violation",
            "Is this formatted and placed the way the surrounding file does it? Only a "
            "deviation from a convention the file is otherwise consistent about — including "
            "where a declaration sits: a lemma that belongs inside a `namespace` block and "
            "was left outside it is a placement defect, not a matter of taste.",
            extra_subject_kinds=MODULE_DOC_KINDS | PLACEMENT_KINDS,
        ),
        _new_spec(
            "api_reuse", "duplication", "missed_canonical_api",
            "Does the code re-derive something the library already provides, or spell an "
            "existing API the long way? Smaller and commoner than whole-declaration "
            "duplication, and checkable by compiling the replacement.",
        ),
        _new_spec(
            # The arm that owns a group. Five of the nineteen audited obligations cannot be
            # resolved by a reviewer confined to one declaration with one edit — rename a
            # pair, add a lemma and prove it from its dual, attribute a family and delete the
            # siblings it generates — and no existing arm's concern covers "these are wrong
            # together". It is the only arm besides `migration_consistency` allowed to submit
            # a coordinated patch, because it is the only one whose scope is a set.
            "family_design", "generalization", "generalization_available",
            "Are these declarations right AS A GROUP — a dual proved from scratch instead of "
            "from its counterpart, a missing counterpart, a generated form written by hand, "
            "a repeated argument that should be one lemma?",
        ),
        _new_spec(
            "correctness", "correctness", "correctness_policy",
            "Is anything actually broken — the build, a statement that does not say what it "
            "claims, a looping simp lemma, an unaccepted axiom? Starts by compiling the "
            "reviewed file, which no other arm does.",
        ),
    ]


#: Which concern families are settled by compiling something. A specialist outside this set
#: cannot carry a compile artifact, so it must be admitted through the evidence chain rather
#: than the verification gate — otherwise its findings are dropped for lacking a warrant its
#: concern can never produce.
CHECKABLE_ARMS = frozenset({"proof_golf", "proof_idiom", "duplication", "generality",
                            "api_reuse", "correctness"})

#: `lean_verify_edit` is granted to every arm without exception. It is registered by the
#: shared review base for *all* review tasks, and the smoke4 run measured 87 of its 100
#: calls carrying a real edit — it is the one tool that turns a suggestion into a checked
#: one, and no arm should be reviewing without it.
_UNIVERSAL_CONTEXT_TOOLS = ("lean_verify_edit",)

#: The retrieval grant, per arm, matched to the shape of the answer that arm needs.
#:
#: This was uniform until smoke4 measured what the arms do with four retrieval tools: they
#: reach for the cheapest identifier lookup rather than the one that answers their question.
#: `family_design` spent **50 of its 63** discretionary retrieval calls on
#: `declaration_search` — which returns nothing but `X is declared in file Y` — against 13
#: on `content_search`, the only tool that could have found the mechanism its own prompt
#: told it to look for. It produced zero candidates from eleven invocations.
#:
#: So the rule is output shape, not concern:
#:
#: * `declaration_search` answers "does this name exist, and where" — it belongs to the arms
#:   whose question is about a *named* thing: is there already a lemma for this, where does
#:   this sibling live, what is the canonical form called.
#: * `precedent_search` and `zulip_search` answer "what do maintainers say" — they belong to
#:   the arms whose question is a convention, which is not decidable from the code corpus.
#:   This is measured too: the code corpus argues *against* the maintainer in both naming
#:   cases (`coe_` 4,707 against `toLinearMap_` 50), while the review corpus states them.
#: * every arm keeps `content_search` (a file-system tool, never gated here) and
#:   `lean_verify_edit`.
#:
#: An arm absent from this table gets the universal grant only. That is deliberate for
#: `family_design`: denying it the identifier lookup it wasted its budget on is the whole
#: intervention, and `content_search` remains available to it.
_CONTEXT_GRANTS: Dict[str, tuple] = {
    # "is there already a declaration that does this?" — a name question.
    "proof_golf": ("declaration_search",),
    "proof_idiom": ("declaration_search",),
    "duplication": ("declaration_search",),
    "api_reuse": ("declaration_search",),
    "generality": ("declaration_search",),
    "correctness": ("declaration_search",),
    # Naming is both: what the siblings are called, and what maintainers call them.
    "naming": ("declaration_search", "precedent_search", "zulip_search"),
    # Pure convention arms. Neither question is settled by the library's own frequencies.
    "docs": ("precedent_search", "zulip_search"),
    "style": ("precedent_search", "zulip_search"),
    # `family_design` asks whether a *group* is shaped right. No identifier lookup answers
    # that, and the measurement above is what removed it.
    "family_design": ("precedent_search", "zulip_search"),
}


def _grant_for(arm_id: str) -> List[str]:
    """This arm's context grant, in `CONTEXT_TOOLS` order so the hash is stable."""

    granted = set(_CONTEXT_GRANTS.get(arm_id, ())) | set(_UNIVERSAL_CONTEXT_TOOLS)
    return [name for name in CONTEXT_TOOLS if name in granted]


def _generalist_arm(renderer_version: str) -> ReviewArm:
    """The per-site control: same sites and tools as the specialists, no concern filter.

    Its prompt is the release's own rendered production prompt, so the arm-level hash
    identifies the *renderer* rather than a template string — there is no generalist
    template to hash, the renderer is the template.

    It keeps all four context tools when the specialists no longer do. That is the point of
    a control: it is the arm every prior run was measured against, and narrowing it would
    make the specialist grant and the generalist's own reach move at the same time, so
    neither could be read off the result.
    """

    return sealed_model(
        ReviewArm,
        arm_id=GENERALIST_ARM_ID,
        task_type=ARM_TASK_TYPE,
        kind="generalist",
        concern_family="other",
        issue_kind=None,
        mandatory=True,
        spec_id=None,
        prompt_sha256=sha256_bytes(canonical_json_bytes({"renderer": renderer_version})),
        tools_sha256=sha256_bytes(canonical_json_bytes(sorted(CONTEXT_TOOLS))),
        context_tools=list(CONTEXT_TOOLS),
        cost_hint=COST_HINT_PER_WORK_UNIT,
        rationale=(
            "One invocation per work unit with no concern filter. The coverage floor: it "
            "runs in every routing mode and cannot be pruned."
        ),
    )


def _specialist_arm(spec: FocusedAgentSpec) -> ReviewArm:
    return sealed_model(
        ReviewArm,
        arm_id=spec.spec_id,
        task_type=ARM_TASK_TYPE,
        kind="specialist",
        concern_family=spec.concern_family,
        issue_kind=spec.issue_kind,
        mandatory=False,
        spec_id=spec.spec_id,
        prompt_sha256=spec.prompt_sha256,
        tools_sha256=spec.tools_sha256,
        context_tools=_grant_for(spec.spec_id),
        cost_hint=COST_HINT_PER_WORK_UNIT,
        rationale=spec.rationale,
    )


def default_arms(renderer_version: str) -> List[ReviewArm]:
    """The mandatory generalist plus the four focused specialists, in stable id order."""

    specialists = [_specialist_arm(spec) for spec in v5_specs()]
    return [_generalist_arm(renderer_version)] + sorted(
        specialists, key=lambda item: item.arm_id
    )


def specs_by_arm_id() -> Dict[str, FocusedAgentSpec]:
    """Arm id -> the v4 spec whose `applies_to` decides where that arm is eligible.

    The generalist is absent by construction: it has no spec, and a caller that reaches for
    one is asking the wrong question — `arm.mandatory` is what says where it runs.
    """

    return {spec.spec_id: spec for spec in v5_specs()}


def arm_by_id(arms: List[ReviewArm]) -> Dict[str, ReviewArm]:
    return {arm.arm_id: arm for arm in arms}


def mandatory_arm_ids(arms: List[ReviewArm]) -> List[str]:
    return [arm.arm_id for arm in arms if arm.mandatory]


def registry_identity(arms: List[ReviewArm]) -> Dict[str, str]:
    """`arm_id -> source_sha256`, for the sealed run plan.

    A run is only comparable to another run if the arms meant the same thing in both, and
    an arm's identity is its prompt, its tools and its eligibility together — not its name.
    """

    return {arm.arm_id: arm.source_sha256 for arm in arms}


def resolve_context_tools(arm: ReviewArm, available: Optional[List[str]] = None) -> List[str]:
    """Which context tools this arm actually gets, intersected with what the run offers.

    This used to hand every arm all four, on the stated grounds that which evidence source a
    concern needs was unmeasured and that answering it by assumption would bake in a guess.
    smoke4 measured it. Given the choice of four, the arms converge on the cheapest
    identifier lookup regardless of what they are being asked: 106 `declaration_search`
    calls run-wide, 50 of them from `family_design`, whose question no identifier lookup can
    answer and which returned nothing from eleven invocations. The grant is now per arm and
    the reasoning is in `_CONTEXT_GRANTS`; the generalist is deliberately exempt so it stays
    comparable with the runs before this one.
    """

    grant = [item for item in arm.context_tools if item in CONTEXT_TOOLS]
    if available is None:
        return grant
    offered = set(available)
    return [item for item in grant if item in offered]
