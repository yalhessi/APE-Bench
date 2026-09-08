"""Semantic judgment of one candidate review request against one gold obligation.

This is the registered-task form of `src/mathlib_review/judge/semantic_judge.py`. The
script version calls the LLM client directly and keeps a hand-rolled JSON file cache; as
a task it inherits the framework's machinery instead:

- `global_index` is the content hash of the record, and the judged pair *is* the record,
  so **resume becomes the cache** — a re-run skips pairs whose `task_result.json` exists,
  with no bespoke cache directory.
- `sample_count > 1` gives repeated verdicts on the same pair for free, which is how the
  known 2-of-3 flip on byte-identical artifacts gets measured and voted away.
- Cost and turn limits are enforced where the framework enforces them.

It reads gold, so it is run from its own top-level orchestrator (`judge_runner.py`) and
never nested inside a reviewer task — the reviewer's run tree must stay gold-free.

The rubric, prompt rendering and verdict shape all come from
`src/mathlib_review/judge/protocol.py`, so there is one judge rather than two that
are asserted to be equal.
"""

import json
from typing import Annotated, Any, Dict, Optional

from pydantic import Field

from ape.tasks.base import (
    BaseTask,
    BaseTaskConfig,
    BaseTaskData,
    BaseTaskResult,
    EvaluationResult,
    register_task,
)

from src.mathlib_review.judge.protocol import (
    JUDGE_PROMPT,
    JUDGE_VERSION,
    ContextProfile,
    Verdict,
    render_prompt,
)


class LeanPRReviewV4JudgmentConfig(BaseTaskConfig):
    """The judge needs no tools; it reads the pair out of its own prompt."""

    enabled_tools: Optional[list] = Field(default_factory=list)


class LeanPRReviewV4JudgmentData(BaseTaskData):
    """One (candidate, obligation) pair to adjudicate.

    The fields below are exactly the inputs the script's `_pair_key` hashes, so this
    record's `global_index` and the script's cache key identify the same unit of work.
    """

    task_type: str = "lean_pr_review_v4_semantic_judgment"
    candidate_id: str
    obligation_id: str
    candidate_source_sha256: str
    obligation_source_sha256: str
    judge_version: str = JUDGE_VERSION
    # Rendered prompt inputs.
    gold_concerns: str
    gold_claim: str
    resolution_criteria: str
    primary_subject: str
    candidate_family: str
    candidate_claim: str
    requested_change: str
    suggested_fix: str
    # v8 context. Defaults keep v7.1 records valid and, because `global_index` hashes the
    # record, a v8 record is automatically a distinct unit of work from its v7.1 twin —
    # so the two rubrics can never resume into each other's results.
    target_code: str = ""
    gold_action: str = "(unspecified)"
    proposed_edit: str = "(none)"
    # v9 optional context. Each is an independent ablation; whether a block is present is
    # declared in `context_profile` and hashed into the judge's identity, so an ablation can
    # never resume into a differently-contextualised verdict.
    candidate_code: str = ""
    maintainer_comment: str = ""
    sibling_claims: list = Field(default_factory=list)
    context_profile: str = "base"
    # Carried for downstream joining; not part of the judged content.
    pr_number: int = 0
    overlap_change_ids: list = Field(default_factory=list)
    candidate_change_ids: list = Field(default_factory=list)
    pairing_tier: str = "anchor"


class LeanPRReviewV4JudgmentResult(BaseTaskResult):
    candidate_id: Optional[str] = None
    obligation_id: Optional[str] = None
    issue_match: bool = False
    resolution_match: bool = False
    abstain: bool = False
    reason: str = ""
    judge_version: str = JUDGE_VERSION


class LeanPRReviewV4JudgmentTask(BaseTask):
    """Adjudicate one candidate/obligation pair; the verdict is the task result."""

    task_type = "lean_pr_review_v4_semantic_judgment"
    data_class = LeanPRReviewV4JudgmentData
    task_config_class = LeanPRReviewV4JudgmentConfig
    task_result_class = LeanPRReviewV4JudgmentResult

    async def create_user_prompt(self) -> str:
        data = self.data
        if data.judge_version != JUDGE_VERSION:
            raise ValueError(
                f"unknown judge rubric version: {data.judge_version}. Only "
                f"{JUDGE_VERSION} is active; retired rubrics are in "
                "src/mathlib_review/legacy_pipeline/judge_v71.py and are not re-rendered."
            )
        return render_prompt(
            gold_code=data.target_code,
            gold_concerns=data.gold_concerns,
            gold_action=data.gold_action,
            gold_claim=data.gold_claim,
            resolution_criteria=data.resolution_criteria,
            primary_subject=data.primary_subject,
            candidate_family=data.candidate_family,
            candidate_claim=data.candidate_claim,
            requested_change=data.requested_change,
            suggested_fix=data.suggested_fix,
            proposed_edit=data.proposed_edit,
            candidate_code=data.candidate_code,
            maintainer_comment=data.maintainer_comment,
            sibling_claims=tuple(data.sibling_claims),
        )

    async def register_task_tools(self, mcp) -> None:
        @mcp.tool(
            description=(
                "Submit the verdict for this candidate/obligation pair. "
                "Call exactly once; this terminates the judgment."
            )
        )
        async def submit_result(
            issue_match: Annotated[bool, Field(
                description="True only when the candidate names the same specific problem "
                            "the maintainer says must change."
            )],
            resolution_match: Annotated[bool, Field(
                description="True only when issue_match is true AND the candidate's concrete "
                            "transformation achieves the maintainer's requested end state."
            )],
            abstain: Annotated[bool, Field(
                description="True only when this pair falls on a boundary the rubric does not "
                            "settle. Not for merely difficult calls."
            )],
            reason: Annotated[str, Field(description="One sentence.")],
        ) -> Dict[str, Any]:
            # Typed parameters, not a JSON string the model has to serialise correctly.
            # Under the string protocol an unparseable reply was scored as a negative
            # verdict, silently converting judge failures into misses — and `bool("false")`
            # is `True`, so a stringified boolean inverted the verdict.
            resolution_match = bool(resolution_match) and bool(issue_match)
            evaluation_result = EvaluationResult(
                success=True,
                # A verdict is a measurement, not a pass/fail: score 1.0 means "a verdict
                # was recorded", so a `false` judgment is not mistaken for a failed task.
                score=1.0,
                message=(
                    f"issue_match={issue_match} resolution_match={resolution_match} "
                    f"abstain={abstain}"
                ),
                metrics={
                    "issue_match": float(bool(issue_match)),
                    "resolution_match": float(resolution_match),
                    "abstain": float(bool(abstain)),
                },
            )
            if self.termination_callback:
                await self.termination_callback(self.create_result(
                    success=True,
                    score=1.0,
                    candidate_id=self.data.candidate_id,
                    obligation_id=self.data.obligation_id,
                    issue_match=bool(issue_match),
                    resolution_match=resolution_match,
                    abstain=bool(abstain),
                    reason=reason,
                    judge_version=self.data.judge_version,
                ))
            return {"evaluation_result": evaluation_result, "message": "Verdict recorded"}

    @classmethod
    def is_best_result(cls, result) -> bool:
        """Every recorded verdict counts; there is no 'better' verdict to prefer."""

        return bool(getattr(result, "success", False))

    @classmethod
    def aggregate_results(cls, results):
        """Majority vote across samples, which is the point of running more than one.

        Three corrections over the first implementation, each of which was hiding something:

        1. **Resolution votes are counted only among samples that issue-matched.** Counting
           them across all samples mixes in samples that said `issue=False`, whose
           `resolution_match` is `False` by the clamp rather than by judgement — so the
           resolution majority was being decided partly by votes that never considered the
           question.
        2. **`unanimous` was issue-only**, which is why resolution-level self-disagreement
           went unnoticed: under v8 the issue splits went 4/18 -> 0/18 while the resolution
           splits went 2/18 -> 4/18. Both levels are now reported.
        3. **Failed samples no longer shrink the denominator.** With `sample_count=3` and one
           failure, a 1-1 split used to resolve on n=2 and be reported `unanimous`. Too few
           successes is a coverage gap (`None`), not a verdict.
        """

        requested = len(results)
        results = [item for item in results if getattr(item, "success", False)]
        if not results or requested and len(results) * 3 < requested * 2:
            return None
        base = results[0]
        issue_votes = sum(bool(getattr(item, "issue_match", False)) for item in results)
        abstain_votes = sum(bool(getattr(item, "abstain", False)) for item in results)
        majority_issue = issue_votes * 2 > len(results)
        majority_abstain = abstain_votes * 2 > len(results)

        issue_matching = [item for item in results if bool(getattr(item, "issue_match", False))]
        resolution_votes = sum(
            bool(getattr(item, "resolution_match", False)) for item in issue_matching
        )
        majority_resolution = (
            majority_issue
            and bool(issue_matching)
            and resolution_votes * 2 > len(issue_matching)
        )
        return base.model_copy(update={
            "issue_match": majority_issue,
            "resolution_match": majority_resolution,
            "abstain": majority_abstain,
            "custom_metrics": {
                **(getattr(base, "custom_metrics", None) or {}),
                "issue_votes": issue_votes,
                "resolution_votes": resolution_votes,
                "resolution_denominator": len(issue_matching),
                "abstain_votes": abstain_votes,
                "samples_requested": requested,
                "samples_succeeded": len(results),
                "issue_unanimous": issue_votes in (0, len(results)),
                "resolution_unanimous": (
                    resolution_votes in (0, len(issue_matching)) if issue_matching else True
                ),
            },
        })


register_task("lean_pr_review_v4_semantic_judgment", LeanPRReviewV4JudgmentTask)
