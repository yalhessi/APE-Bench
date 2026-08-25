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

ARM_REGISTRY_VERSION = "v5-arm-registry/1"

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


def _new_spec(spec_id: str, concern_family: str, issue_kind: str, rationale: str,
              *, component: Optional[str] = None,
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
        subject_kinds=DECLARATION_KINDS,
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
            "Is the docstring accurate? Typos and contradicted statements are small, exact, "
            "and the easiest thing for a reader scanning for something substantive to miss.",
        ),
        _new_spec(
            "style", "style", "style_norm_violation",
            "Is this formatted the way the surrounding file formats things? Only a deviation "
            "from a convention the file is otherwise consistent about.",
        ),
        _new_spec(
            "api_reuse", "duplication", "missed_canonical_api",
            "Does the code re-derive something the library already provides, or spell an "
            "existing API the long way? Smaller and commoner than whole-declaration "
            "duplication, and checkable by compiling the replacement.",
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


def _generalist_arm(renderer_version: str) -> ReviewArm:
    """The per-site control: same sites and tools as the specialists, no concern filter.

    Its prompt is the release's own rendered production prompt, so the arm-level hash
    identifies the *renderer* rather than a template string — there is no generalist
    template to hash, the renderer is the template.
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
        context_tools=list(CONTEXT_TOOLS),
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

    Every arm defaults to all four. Which evidence source a given concern needs is an open
    question the precedent design says to settle by benchmark; answering it here by handing
    the duplication arm retrieval and denying it to golf would bake in an assumption that
    has never been measured. The field exists so the question stays askable.
    """

    grant = [item for item in arm.context_tools if item in CONTEXT_TOOLS]
    if available is None:
        return grant
    offered = set(available)
    return [item for item in grant if item in offered]
