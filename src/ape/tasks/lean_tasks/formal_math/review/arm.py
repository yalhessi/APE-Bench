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
from ape.tasks.lean_tasks.formal_math.review.candidates import (
    LeanPRReviewV4CandidateConfig,
    LeanPRReviewV4CandidateData,
    LeanPRReviewV4CandidateResult,
    LeanPRReviewV4CandidateTask,
)

from src.mathlib_review.agenda.registry import (
    expected_concerns, patch_set_arms,
)

from .context_tools import register_context_tools

ARM_TASK_TYPE = "lean_pr_review_v5_arm"

#: The concern family each specialist is expected to speak in. The generalist is absent: it
#: has no concern filter, which is what makes it the control.
#:
#: **Not enforced.** It was, and the justification was that the alternative is a silent
#: deletion: a `generality` arm reporting a `style` claim passes submission (style is not a
#: checkable family, so no verification artifact is required), and `focused_findings` then
#: dropped it at finalization for having no artifact — without a word. On the rep2 smoke run
#: that was all four specialist candidates.
#:
#: The drop is no longer silent: finalization retains every one as a `diagnostic` finding in
#: `findings.jsonl`, so a correct claim that lacked a warrant can be told apart from a wrong
#: one. What remained was the cost — 11 of the 19 gold obligations labelled `style` are grind
#: simplifications and `encard_` renames, so an arm that found one and labelled it honestly
#: was refused for guessing the evaluator's vocabulary wrong. An off-concern submission is now
#: recorded on the candidate as a `concern_tags` entry instead of being refused.
#:
#: golf and idiom share `proof-golf` on purpose: they inspect the same proofs and make
#: different claims about them, and they are kept apart by `spec_id`, not by family.
#: Derived from `arm_registry`, which is where an arm is declared. This and
#: `PATCH_SET_ARMS` used to be dictionaries here while `CHECKABLE_ARMS` and the retrieval
#: grant were dictionaries in `src/mathlib_review/agenda/arms.py` — four tables keyed by
#: arm id, on opposite sides of the package boundary, with nothing checking they agreed.
EXPECTED_CONCERN_BY_ARM = {
    arm_id: set(concerns) for arm_id, concerns in expected_concerns().items()
}

#: Tag written onto a candidate whose declared concern is outside its arm's expected set.
#: Prefixed so a reader can tell a routing observation from a concern the arm asserted.
OFF_CONCERN_TAG = "off-concern"


class ReviewArmConfig(LeanPRReviewV4CandidateConfig):
    """Verify-heavy defaults; a focused claim is settled by compiling the replacement."""

    finding_budget: int = 20


class ReviewArmData(LeanPRReviewV4CandidateData):
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


class ReviewArmResult(LeanPRReviewV4CandidateResult):
    invocation_id: Optional[str] = None
    arm_id: Optional[str] = None
    spec_id: Optional[str] = None


class ReviewArmTask(LeanPRReviewV4CandidateTask):
    task_type = ARM_TASK_TYPE
    data_class = ReviewArmData
    task_config_class = ReviewArmConfig
    task_result_class = ReviewArmResult

    def create_result(self, success: bool, score: float, **kwargs) -> ReviewArmResult:
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
    PATCH_SET_ARMS = patch_set_arms()

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

    def _annotate_candidate(self, candidate: Dict[str, Any]) -> None:
        """Record which arm produced this and whether it stayed inside its own concern.

        This replaces a rejection. The rejection's argument was that refusing is kinder than
        the alternative, because the alternative was not that the claim survives — it was
        that the claim is dropped at finalization with no explanation. That is no longer the
        alternative: an unwarranted claim is retained as a `diagnostic` finding the judge can
        score, so a correct claim that lacked a warrant is distinguishable from a wrong one.

        What is left of the rejection is its cost. 11 of the 19 gold obligations labelled
        `style` are grind simplifications and `encard_` renames; an arm that finds one and
        labels it honestly was refused for guessing the evaluator's vocabulary wrong. The arm
        prompt still tells it what its one job is — that is where routing discipline belongs.
        Here we record what it did, and let the measurement say whether it wandered.
        """

        tags = [tag for tag in (candidate.get("concern_tags") or []) if isinstance(tag, str)]
        family = candidate.get("concern_family")
        if isinstance(family, str) and family not in tags:
            tags.append(family)
        expected = EXPECTED_CONCERN_BY_ARM.get(self.data.arm_id)
        if expected and family not in expected:
            tags.append(f"{OFF_CONCERN_TAG}:{self.data.arm_id}")
            if self.logger is not None:
                self.logger.warning(
                    "arm %s declared concern_family=%r, outside its expected set %s; "
                    "recorded, not refused",
                    self.data.arm_id, family, sorted(expected),
                )
        candidate["concern_tags"] = tags

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


register_task(ARM_TASK_TYPE, ReviewArmTask)
