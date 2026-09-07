"""One task class for every specialist. Prompt, tools and context grant are the only variables.

Deliberately a subclass of v4's candidate task rather than a sibling, for the reason v4's
own focused arm gives: everything that makes a candidate *anchorable* — `change_ids ⊆ unit`,
`primary_subject` equality, the entity check, the statement gate, edit confinement, and the
compile-backed verification gate — lives in `submit_candidates`, and a second implementation
of that contract would be a second thing to keep correct. Edit confinement in particular is
not optional at work-unit grain: without it an arm scheduled on one target can submit an
edit to another file, declare a `primary_change_id` back in its own, and pass every check
while the compiler cheerfully verifies the wrong file.

What v5 adds is identity and context, not a new contract:

* `invocation_id` (`wu:…#arm_id`) is the run identity. The work unit does not identify a run
  when five arms share it, and attribution is taken from the invocation rather than from the
  model's own report of which agent it is.
* `context_tools` is the grant, and `retrieval_cutoff` is the instant every gated read is
  taken at. Both arrive as data so that a worker process can neither widen its own grant nor
  choose its own cutoff.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from ape.tasks.base import register_task
from ape.tasks.lean_tasks.formal_math.pr_review_v4.candidates import (
    LeanPRReviewV4CandidateConfig,
    LeanPRReviewV4CandidateData,
    LeanPRReviewV4CandidateResult,
    LeanPRReviewV4CandidateTask,
)

from .context_tools import register_context_tools

ARM_TASK_TYPE = "lean_pr_review_v5_arm"

#: The concern family each specialist is allowed to speak in. The generalist is absent: it
#: has no concern filter, which is what makes it the control.
#:
#: This is enforced because the alternative is a silent deletion. A `generality` arm that
#: reports a `style` claim passes submission (style is not a checkable family, so no
#: verification artifact is required), and `focused_findings` then drops it at finalization
#: for having no artifact — without a word. On the rep2 smoke run that was all four
#: specialist candidates: the generality arm wandered into style and naming, and every one
#: of them vanished between submission and the report.
#:
#: golf and idiom share `proof-golf` on purpose: they inspect the same proofs and make
#: different claims about them, and they are kept apart by `spec_id`, not by family.
ALLOWED_CONCERN_BY_ARM = {
    "proof_golf": {"proof-golf"},
    "proof_idiom": {"proof-golf"},
    "duplication": {"duplication"},
    "generality": {"generalization"},
    "naming": {"naming"},
    "docs": {"documentation"},
    "style": {"style"},
    "api_reuse": {"duplication"},
    # `correctness` also owns `scope`: a declaration whose imports cannot support where it
    # sits is a build problem wearing a placement problem's clothes, and no other arm compiles.
    "correctness": {"correctness", "scope"},
    # `family_design` is the one arm whose scope is a *set*, and the defect a set exhibits
    # takes two shapes that no single concern covers: a missing counterpart or a hardcoded
    # shared parameter is `generalization`, while a generated form written out by hand is
    # `duplication`. Forcing one would leave the arm unable to state half the findings it
    # exists for — PR 33117's thirteen hand-written `fun_*` lemmas are duplication-shaped,
    # PR 33145's absent dual is generalization-shaped, and both are group properties.
    "family_design": {"generalization", "duplication"},
}


class LeanPRReviewV5ArmConfig(LeanPRReviewV4CandidateConfig):
    """Verify-heavy defaults; a focused claim is settled by compiling the replacement."""

    finding_budget: int = 20


class LeanPRReviewV5ArmData(LeanPRReviewV4CandidateData):
    task_type: str = ARM_TASK_TYPE
    #: `wu:…#arm_id`. Finer than the work unit, because several arms share one.
    invocation_id: str
    arm_id: str
    #: The v4 `FocusedAgentSpec` behind this arm, when it has one. `None` for the generalist,
    #: whose scope is the whole unit rather than a rule's selection.
    spec_id: Optional[str] = None
    context_tools: List[str] = Field(default_factory=list)
    #: The instant every gated context read is taken at — the committer timestamp of the
    #: reviewed commit. Optional on the model so task data written before context tools
    #: existed still loads, but a gated tool refuses to run without it rather than silently
    #: reading ungated.
    retrieval_cutoff: Optional[str] = None
    #: Append-only JSONL the arm records its context calls to. Written during the attempt so
    #: that a job which fails or exhausts its budget still leaves a trace — those are the
    #: jobs whose retrieval behaviour explains the outcome.
    trace_path: Optional[str] = None


class LeanPRReviewV5ArmResult(LeanPRReviewV4CandidateResult):
    invocation_id: Optional[str] = None
    arm_id: Optional[str] = None
    spec_id: Optional[str] = None


class LeanPRReviewV5ArmTask(LeanPRReviewV4CandidateTask):
    task_type = ARM_TASK_TYPE
    data_class = LeanPRReviewV5ArmData
    task_config_class = LeanPRReviewV5ArmConfig
    task_result_class = LeanPRReviewV5ArmResult

    def create_result(self, success: bool, score: float, **kwargs) -> LeanPRReviewV5ArmResult:
        """Stamp the invocation's identity onto every result.

        Taken from `self.data`, never from anything the model supplied: the whole point of
        an invocation id is that it says which agent ran, and a self-reported label would
        let a mislabelled response be attributed to the arm it is measured against.
        """

        kwargs.setdefault("invocation_id", self.data.invocation_id)
        kwargs.setdefault("arm_id", self.data.arm_id)
        kwargs.setdefault("spec_id", self.data.spec_id)
        return super().create_result(success=success, score=score, **kwargs)

    #: Arms allowed to submit a coordinated patch. Narrow on purpose: the capability exists
    #: for fixes one edit cannot express — rename a pair, add a lemma and prove it from its
    #: dual, attribute a family and delete the siblings it generates — and an arm reviewing
    #: one site has no use for it. Granting it broadly would turn a bounded capability into
    #: a licence to rewrite whatever the arm happened to be shown.
    #
    # Only arms that actually exist. `migration_consistency` was listed here before it had a
    # spec or a prompt, which is the same defect as `code_references` sitting in
    # `SUPPORTED_TOOLS` with its registration commented out: a capability granted to nothing,
    # readable as coverage that is not there. `test_every_patch_set_arm_is_a_registered_spec`
    # keeps it honest — add the arm first, then add it here.
    PATCH_SET_ARMS = frozenset({"family_design"})

    @property
    def patch_set_paths(self) -> tuple:
        """Files a coordinated patch may touch: this invocation's own targets, and no more.

        Confinement comes from the task data rather than from anything the model supplies,
        so a patch cannot widen its own scope by naming a file it would like to edit. An arm
        not on `PATCH_SET_ARMS` gets an empty tuple, which `_patch_set_error` reads as
        "coordinated patches are not accepted here".
        """

        if self.data.arm_id not in self.PATCH_SET_ARMS:
            return ()
        paths = {self.data.paths_by_change.get(cid) for cid in self.data.change_ids}
        return tuple(sorted(p for p in paths if p))

    def _extra_candidate_error(self, candidate: Dict[str, Any]) -> Optional[str]:
        """Keep a specialist inside its own concern.

        This is the hook v4 documents for exactly this purpose — "an arm whose *scope*
        differs adds its rule here rather than reimplementing the rest and drifting from
        it" — so the rest of the contract stays single-implementation.

        Rejecting is kinder than it sounds: the alternative is not that the claim survives,
        it is that the claim is dropped later with no explanation. Telling the arm now lets
        it either restate the finding in its own terms or drop it deliberately.
        """

        allowed = ALLOWED_CONCERN_BY_ARM.get(self.data.arm_id)
        if not allowed:
            return None
        family = candidate.get("concern_family")
        if family in allowed:
            return None
        expected = " or ".join(sorted(allowed))
        return (
            f"this is the {self.data.arm_id} check, which reports {expected} findings only; "
            f"you declared concern_family={family!r}. A finding outside this arm's concern "
            "cannot be published from here — the per-site generalist already covers the "
            "other families. Either restate it as a genuine "
            f"{expected} finding, or drop it."
        )

    async def register_task_tools(self, mcp) -> None:
        # The v4 contract first — `submit_candidates` plus `lean_verify_edit` — then only
        # the context tools this arm was granted.
        await super().register_task_tools(mcp)
        registered = register_context_tools(self, mcp)
        # `self.logger` is only bound during `setup()`, and tools are registerable before
        # then (a harness may introspect the toolset without running the task).
        if self.logger is not None:
            self.logger.info(
                "arm %s (%s): context tools %s",
                self.data.arm_id, self.data.invocation_id, registered or "none",
            )

    def _tool_summary(self) -> str:
        base = super()._tool_summary()
        granted = list(self.data.context_tools or [])
        extra = []
        if "zulip_search" in granted:
            extra.append("search prior Mathlib Zulip discussion (zulip_search)")
        if "precedent_search" in granted:
            extra.append("find past maintainer comments on similar code (precedent_search)")
        if "declaration_search" in granted:
            extra.append("find where a declaration is defined (declaration_search)")
        return ", ".join([base] + extra) if extra else base


register_task(ARM_TASK_TYPE, LeanPRReviewV5ArmTask)
