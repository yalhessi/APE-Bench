"""The raw-ask matcher as a registered Task: one batch of PRs, judged blind, verdict typed.

Until 2026-10-22 every matching ran as hand-launched Claude Code sessions over folders written to a
scratch directory outside the repository, driven by shell scripts under a probe directory, and only
the `matches.json` they wrote was kept. As a Task it inherits the framework instead: the orchestrator
runs it, resumes it and records its outcome, `sample_count` independent samples of the same inputs
are the independent blind matchers (two, by the probes' practice), and the inputs are the task's own
data, so the bytes a matcher judged are hashed into its identity and kept with its run.

The instrument -- the rubric, the projection, the validation -- is `src/mathlib_review/judge/
ask_matching.py`, version `2-task`; this module only runs it. Gold-bearing: never nested inside a
reviewer task.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import Field

from ape.tasks.base import (
    BaseTask,
    BaseTaskConfig,
    BaseTaskData,
    BaseTaskResult,
    EvaluationResult,
    register_task,
)

from src.mathlib_review.io import sha256_bytes
from src.mathlib_review.judge.ask_matching import (
    V2_TASK,
    AskVerdict,
    flat_rows,
    render_matcher_prompt,
    verdict_problems,
)
from src.mathlib_review.schema import BlindPacket

ASK_MATCHING_TASK_TYPE = "lean_pr_review_ask_matching"


class AskMatchingConfig(BaseTaskConfig):
    """The matcher needs no tools: everything it judges is in its first message."""

    enabled_tools: Optional[list] = Field(default_factory=list)


class AskMatchingData(BaseTaskData):
    """One batch of a sealed matching plan: its PRs' asks and each label's blind findings."""

    task_type: str = ASK_MATCHING_TASK_TYPE
    plan_id: str
    batch_id: str
    instrument_version: str = V2_TASK
    question_policy: Literal["request_only", "questions"] = "request_only"
    packets: List[BlindPacket]


class AskMatchingResult(BaseTaskResult):
    plan_id: Optional[str] = None
    batch_id: Optional[str] = None
    instrument_version: str = V2_TASK
    #: SHA-256 of the first message, so a verdict names the exact text it answered.
    prompt_sha256: Optional[str] = None
    #: The historical `matches.json` row shape (`"R1": value, "R1_finding": index, "note"`).
    asks: List[Dict[str, Any]] = Field(default_factory=list)
    unmatched: Dict[str, Dict[str, int]] = Field(default_factory=dict)


class AskMatchingTask(BaseTask):
    """Judge one batch; the typed verdict is the result."""

    task_type = ASK_MATCHING_TASK_TYPE
    data_class = AskMatchingData
    task_config_class = AskMatchingConfig
    task_result_class = AskMatchingResult
    submit_tool = "submit_matches"

    def _prompt(self) -> str:
        if self.data.instrument_version != V2_TASK:
            raise ValueError(
                f"ask-match {self.data.instrument_version!r} cannot run as a task; only {V2_TASK} "
                "does. 1-session results are imported (`cli match import`), never re-run.")
        return render_matcher_prompt(self.data.packets, self.data.question_policy)

    async def create_user_prompt(self) -> str:
        return self._prompt()

    async def register_task_tools(self, mcp) -> None:
        @mcp.tool(
            description=(
                "Submit every verdict for this batch. Refused, with the reasons, if any ask or "
                "reviewer is missing or a finding index does not exist; the session ends when a "
                "submission is accepted."
            )
        )
        async def submit_matches(
            asks: Annotated[List[AskVerdict], Field(
                description="One entry per ask: pr, ask_id, a verdict per reviewer label, a note."
            )],
            unmatched: Annotated[Dict[str, Dict[str, int]], Field(
                description="Per PR (as a string), per reviewer label, the count of that "
                            "reviewer's findings that reach no ask."
            )],
        ) -> Dict[str, Any]:
            rows = flat_rows([a if isinstance(a, AskVerdict) else AskVerdict.model_validate(a)
                              for a in asks])
            problems = verdict_problems(self.data.packets, rows, unmatched)
            if problems:
                return {"success": False, "accepted": False,
                        "error": "Submission refused; correct these and submit again.",
                        "problems": problems[:40], "problem_count": len(problems)}
            evaluation = EvaluationResult(
                success=True,
                # A verdict is a measurement: 1.0 means a complete verdict was recorded.
                score=1.0,
                message=f"{len(rows)} asks judged",
            )
            if self.termination_callback:
                await self.termination_callback(self.create_result(
                    success=True, score=1.0,
                    plan_id=self.data.plan_id, batch_id=self.data.batch_id,
                    instrument_version=self.data.instrument_version,
                    prompt_sha256=sha256_bytes(self._prompt().encode("utf-8")),
                    asks=rows, unmatched=unmatched,
                ))
            return {"evaluation_result": evaluation, "accepted": True,
                    "message": "Verdicts recorded"}

    @classmethod
    def is_best_result(cls, result) -> bool:
        """Every complete verdict counts; no replicate is better than another."""

        return bool(getattr(result, "success", False))

    @classmethod
    def aggregate_results(cls, results):
        """No aggregation: each sample is one blind matcher, read separately.

        The orchestrator needs one `task_result.json` per task, and this is the first replicate
        with the count beside it. It is a marker, not the measurement: the verdict store reads
        every sample's own result (`analysis/matching.collect_task_verdicts`), because two blind
        matchers are reported matcher by matcher with their agreement, never merged.
        """

        results = [item for item in results if getattr(item, "success", False)]
        if not results:
            return None
        return results[0].model_copy(update={
            "custom_metrics": {**(results[0].custom_metrics or {}),
                               "replicates_succeeded": float(len(results))}})


register_task(ASK_MATCHING_TASK_TYPE, AskMatchingTask)
