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

from src.mathlib_review.agenda.focused_specs import (
    DECLARATION_KINDS,
    FocusedAgentSpec,
    prompt_hashes,
    default_specs,
)
from src.mathlib_review.io import canonical_json_bytes, sealed_model, sha256_bytes

from src.mathlib_review.agenda.registry import (
    ARM_DEFINITIONS, UNIVERSAL_CONTEXT_TOOLS, checkable_arms, context_grants,
    MODULE_DOC_KINDS as _MODULE_DOC_KINDS, PLACEMENT_KINDS as _PLACEMENT_KINDS,
)
from src.mathlib_review.schema.review import CONTEXT_TOOLS, ReviewArm

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


#: Declared in `arm_registry` with the arms that use them; re-exported because callers here
#: and in the tests import them from this module.
MODULE_DOC_KINDS = _MODULE_DOC_KINDS
PLACEMENT_KINDS = _PLACEMENT_KINDS


def _new_spec(definition) -> FocusedAgentSpec:
    """One registry entry as a `FocusedAgentSpec`. Nothing is decided here."""

    hashes = prompt_hashes()
    if definition.arm_id not in hashes:
        # Adding an arm takes two edits and this is the second one. It used to surface as a
        # bare `KeyError: 'import_hygiene'` from a dict lookup two frames down, which says
        # nothing about what to do -- and forgetting a step then being told nothing useful is
        # the specific complaint this consolidation started from.
        raise KeyError(
            f"arm {definition.arm_id!r} is declared in `arm_registry.ARM_DEFINITIONS` but has "
            "no prompt. Add a `(TOOLS, SYSTEM, USER)` entry for it to `FOCUSED_PROMPTS` in "
            "src/ape/tasks/lean_tasks/formal_math/pr_shared/focused_prompts.py. An arm is a "
            "declaration plus the one question it asks: the registry holds the first and the "
            f"prompt file holds the second. Known: {sorted(hashes)}"
        )
    return FocusedAgentSpec(
        spec_id=definition.arm_id,
        spec_version=V5_SPEC_VERSION,
        task_type=ARM_TASK_TYPE,
        concern_family=definition.concern_family,
        issue_kind=definition.issue_kind,
        lifecycles=_BOTH_LIFECYCLES,
        component=definition.component,
        subject_kinds=DECLARATION_KINDS | definition.extra_subject_kinds,
        prompt_sha256=hashes[definition.arm_id][0],
        tools_sha256=hashes[definition.arm_id][1],
        rationale=definition.rationale,
    )


def v5_specs() -> List[FocusedAgentSpec]:
    """The specialist set v5 schedules, built from `arm_registry`.

    This function used to re-declare all ten arms -- id, concern family, issue kind, subject
    kinds and a rationale -- next to a registry that already declared all ten. Adding an arm
    meant editing both, and the two rationales drifted apart in every one of the ten. Now the
    registry is the declaration and this is its projection into v4's `FocusedAgentSpec`.

    The additions to v4's four are not speculative. On the medium smoke set the gold that no
    v4 arm could own was: three `encard_` prefix renames, a docstring typo, a
    section-formatting request, and a build break — naming, docs/style, and correctness
    respectively. `api_reuse` covers the smaller sibling of duplication that kept surfacing as
    "use the existing lemma here" inside an otherwise fine declaration.
    """

    inherited = {spec.spec_id: spec for spec in default_specs()}
    specs = []
    for definition in ARM_DEFINITIONS:
        if definition.inherited_from_v4:
            # v4's spec, widened. Its prompt and eligibility rule come from `default_specs()`;
            # the registry supplies the rationale so it is stated in one place like the rest.
            base = inherited[definition.arm_id]
            specs.append(replace(
                base, lifecycles=_BOTH_LIFECYCLES, spec_version=V5_SPEC_VERSION,
                rationale=definition.rationale))
            continue
        specs.append(_new_spec(definition))
    return specs


#: Derived from `arm_registry`, which is the one place an arm is declared.
#:
#: These four facts -- checkable, patch-set, retrieval grant, allowed concerns -- used to be
#: four dictionaries keyed by arm id, two here and two in `src/ape/tasks/.../arm.py`, on
#: opposite sides of the package boundary with nothing checking they agreed. An arm could be
#: in one and missing from another: `migration_consistency` sat in `PATCH_SET_ARMS` while
#: never being registered as an arm at all, and this file's grant was per-arm for months while
#: `schema.py` still documented it as uniform.
#:
#: The measurement behind the grant, kept here because this is where it was made: given four
#: retrieval tools the arms reach for the cheapest identifier lookup rather than the one that
#: answers their question. `family_design` spent 50 of its 63 discretionary retrieval calls on
#: `declaration_search` -- which returns nothing but `X is declared in file Y` -- against 13 on
#: `content_search`, the only tool that could have found the mechanism its own prompt told it
#: to look for, and produced zero candidates from eleven invocations. So the rule is output
#: shape, not concern: `declaration_search` for arms asking about a *named* thing,
#: `precedent_search`/`zulip_search` for arms asking a convention question the code corpus
#: answers wrongly (`coe_` outnumbers the requested form 4,707 to 50).
CHECKABLE_ARMS = checkable_arms()

_UNIVERSAL_CONTEXT_TOOLS = UNIVERSAL_CONTEXT_TOOLS

def _grant_for(arm_id: str) -> List[str]:
    """This arm's context grant, in `CONTEXT_TOOLS` order so the hash is stable.

    Reads the registry on each call rather than a `_CONTEXT_GRANTS = context_grants()` taken
    at import. The snapshot was correct -- the registry is static in a running process -- and
    it was still a copy of a table this module exists to stop copying: a derived view that
    stops tracking its source the moment the source changes is the same defect as the four
    hand-maintained dictionaries the registry replaced, one import earlier.
    """

    granted = set(context_grants().get(arm_id, ())) | set(_UNIVERSAL_CONTEXT_TOOLS)
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
    the reasoning is in `arm_registry.context_grants`; the generalist is deliberately
    exempt so it stays comparable with the runs before this one.
    """

    grant = [item for item in arm.context_tools if item in CONTEXT_TOOLS]
    if available is None:
        return grant
    offered = set(available)
    return [item for item in grant if item in offered]
