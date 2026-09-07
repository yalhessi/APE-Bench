"""Maintainer-reviewer gate: an agentic reviewer sub-task and an orchestration helper.

The reviewer is modeled closely on :class:`LeanJudgmentTask` (same agentic, read-only
inspection setup and majority-vote aggregation) but plays a Mathlib *maintainer* judging
*merge readiness* rather than semantic correctness. Its binary decision (merge-ready or not)
is encoded in the reused ``judgment_conclusion`` field ("positive" == merge-ready) so that
all existing sub-task orchestration and majority voting apply unchanged.

``lean_review_gate`` mirrors ``lean_semantic_evaluation``: it spins up N reviewer samples via
a ``TaskOrchestrator`` and returns the aggregated merge-readiness decision plus the union of
blocking issues, for use as a gate inside the reviewed proof-engineering task.
"""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, TYPE_CHECKING

from pydantic import Field, Field as PydField

TypingList = List

from ape.tasks.base import EvaluationResult, register_task
from ape.tasks.models import WorkspaceInfo
from ape.tasks.lean_tasks.formal_math.judgment.task import (
    LeanJudgmentConfig,
    LeanJudgmentData,
    LeanJudgmentResult,
    LeanJudgmentTask,
)
from ape.utils.logging import create_logger

from .prompt import REVIEW_GATE_USER_PROMPT

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class LeanReviewGateConfig(LeanJudgmentConfig):
    """Configuration for the maintainer-reviewer gate sub-task.

    Inherits the read-only inspection tool set and ``judge_mode`` from the
    judgment config. The remaining fields control how the reviewer subtask is
    orchestrated from reviewed proof engineering.

    ``judge_mode == "with_ground_truth"`` shows the reviewer the expert/gold
    diff as a reference point (without requiring the agent to match it).
    """

    model: str = "gpt_5_mini"
    scaffold_type: str = "ape_agent"
    runtime_type: str = "local"
    max_turns: int = 100
    num_processes: int = 0
    max_concurrency: int = 3


class LeanReviewGateData(LeanJudgmentData):
    """Data model for the reviewer gate sub-task (same shape as judgment data)."""

    task_type: Literal["lean_review_gate"] = Field(
        default="lean_review_gate",
        description="Task type identifier",
    )


class LeanReviewGateTask(LeanJudgmentTask):
    """Agentic Mathlib-maintainer reviewer that decides merge readiness.

    Reuses ``LeanJudgmentTask`` setup/result/aggregation; only the prompt and the
    submission tool differ. The merge-readiness decision is stored as
    ``judgment_conclusion`` ("positive" => merge-ready) and the structured findings live in
    ``judgment_data``.
    """

    task_type = "lean_review_gate"
    data_class = LeanReviewGateData
    task_config_class = LeanReviewGateConfig

    async def create_user_prompt(self) -> str:
        """Create the maintainer-reviewer prompt for the proposed change."""
        import asyncio
        from ape.toolkits.code.lean.provider import LeanCodeToolsProvider

        review_config: LeanReviewGateConfig = self.config.task_config
        has_ground_truth = (review_config.judge_mode == "with_ground_truth")
        is_new_file = not self.data.original_code or not self.data.original_code.strip()
        target_filename = self.scratch_target_path.name if self.scratch_target_path else (
            str(self.data.filename) if self.data.filename else "target.lean"
        )

        if is_new_file:
            agent_solution = self.data.target_code
            original_content = "# Empty file (new file creation)"
        else:
            agent_solution = self._compute_diff(
                self.data.original_code,
                self.data.target_code,
                str(self.data.filename) if self.data.filename else "file.lean",
            )
            line_spans = None
            if review_config.format_display_mode == "line_spans":
                line_spans = self._convert_diff_to_line_spans(agent_solution)
            original_content = await asyncio.to_thread(
                LeanCodeToolsProvider.display_content,
                content=self.data.original_code,
                display_mode=review_config.format_display_mode,
                body_handling=review_config.format_body_handling,
                line_spans=line_spans,
                context_lines=review_config.format_context_lines,
            )

        diff_stats_section = ""
        if not is_new_file:
            agent_stats = self._compute_diff_stats(agent_solution)
            if has_ground_truth and self.data.gold_diff:
                expert_stats = self._compute_diff_stats(self.data.gold_diff)
                diff_stats_section = (
                    f"\n<diff_statistics>\nProposed change: +{agent_stats['additions']} "
                    f"-{agent_stats['deletions']} lines\nMaintainer reference: "
                    f"+{expert_stats['additions']} -{expert_stats['deletions']} lines\n\n"
                    "Note: large discrepancies in change magnitude may indicate scope issues.\n"
                    "</diff_statistics>\n"
                )
            else:
                diff_stats_section = (
                    f"\n<diff_statistics>\nProposed change: +{agent_stats['additions']} "
                    f"-{agent_stats['deletions']} lines\n</diff_statistics>\n"
                )

        if has_ground_truth and self.data.gold_diff:
            expert_section = (
                "\n<maintainer_reference_diff>\n"
                "A reference solution by Mathlib maintainers is shown for calibration only. "
                "Different but equally acceptable approaches should not be penalized.\n"
                f"{self.data.gold_diff}\n</maintainer_reference_diff>\n"
            )
        else:
            expert_section = ""

        submit_tool_name = f"{self.config.mcp_server_name}submit_result"

        return REVIEW_GATE_USER_PROMPT.format(
            task_description=self.data.task_description,
            target_filename=target_filename,
            original_content=original_content,
            agent_solution=agent_solution,
            diff_stats_section=diff_stats_section,
            expert_section=expert_section,
            submit_tool_name=submit_tool_name,
        )

    async def register_task_tools(self, mcp) -> None:
        """Register the reviewer's merge-readiness submission tool."""
        from typing import Annotated, List as TypingList
        from pydantic import Field as PydField

        @mcp.tool(
            description=(
                "Submit your final merge-readiness review.\n\n"
                "- merge_ready (bool): true only if a Mathlib maintainer would merge this as-is.\n"
                "- blocking_issues (list[str]): specific, actionable issues that MUST be fixed "
                "before merge (empty when merge_ready is true).\n"
                "- advisory_issues (list[str]): optional non-blocking suggestions.\n"
                "- summary (str): short overall assessment.\n\n"
                "**You MUST use this tool to submit your review. A text-only response is INVALID.**"
            )
        )
        async def submit_result(
            merge_ready: Annotated[bool, PydField(
                description="Whether the change is merge-ready under Mathlib standards"
            )],
            blocking_issues: Annotated[Optional[TypingList[str]], PydField(
                description="Blocking issues that must be fixed before merge",
            )] = None,
            advisory_issues: Annotated[Optional[TypingList[str]], PydField(
                description="Optional non-blocking suggestions",
            )] = None,
            summary: Annotated[str, PydField(
                description="Short overall assessment",
            )] = "",
        ) -> Dict[str, Any]:
            """Submit the maintainer review and (on success) end the reviewer conversation."""
            self.logger.info("Tool submit_result (review gate): execution started")
            try:
                blocking = list(blocking_issues or [])
                advisory = list(advisory_issues or [])
                # A reviewer cannot both approve and list blocking issues.
                merge_ready_final = bool(merge_ready) and not blocking
                judgment_conclusion = "positive" if merge_ready_final else "negative"

                judgment_data = {
                    "merge_ready": merge_ready_final,
                    "blocking_issues": blocking,
                    "advisory_issues": advisory,
                    "summary": summary,
                    "reviewer_declared_merge_ready": bool(merge_ready),
                }

                evaluation_result = EvaluationResult(
                    success=True,
                    score=1.0,
                    message="Merge-readiness review submitted successfully",
                )
                should_terminate = self.should_terminate(evaluation_result)

                if should_terminate and self.termination_callback:
                    try:
                        task_result = self.create_result(
                            success=True,
                            score=1.0,
                            judgment_conclusion=judgment_conclusion,
                            judgment_data=judgment_data,
                        )
                        await self.termination_callback(task_result)
                    except Exception:
                        self.logger.warning(
                            f"Failed to trigger termination: {traceback.format_exc()}"
                        )

                self.logger.info(
                    f"Tool submit_result (review gate): completed "
                    f"(merge_ready={merge_ready_final}, blocking={len(blocking)})"
                )
                return {
                    "success": True,
                    "message": "Review submitted and recorded successfully",
                    "merge_ready": merge_ready_final,
                    "blocking_issues": blocking,
                    "advisory_issues": advisory,
                    "summary": summary,
                }
            except Exception:
                self.logger.error(
                    f"Unexpected error in review-gate submit_result: {traceback.format_exc()}"
                )
                return {
                    "success": False,
                    "error": f"Unexpected system error occurred:\n{traceback.format_exc()}",
                    "message": "Evaluation failed or not ready",
                }


async def lean_review_gate(
    final_code: str,
    original_code: Optional[str],
    task_description: str,
    review_config: LeanReviewGateConfig,
    base_config: "BaseScaffoldConfig",
    *,
    num_reviewers: int = 1,
    reference_implementation: Optional[str] = None,
    filename: Optional[str] = None,
    target_workspace: Optional[WorkspaceInfo] = None,
    gold_diff: Optional[str] = None,
    logger: Optional["logging.LoggerAdapter"] = None,
    parent_attempt_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run the maintainer-reviewer gate over a submission and aggregate the decision.

    Returns a dict with ``merge_ready`` (aggregated, majority vote), the union of
    ``blocking_issues`` from reviewers that blocked, and orchestration metadata. Mirrors
    ``lean_semantic_evaluation`` so it can be invoked the same way as the semantic judge.
    """
    if logger is None:
        logger = create_logger()

    if target_workspace is None:
        raise ValueError("target_workspace specification is required for the review gate")

    if original_code is not None and original_code.strip() and final_code.strip() == original_code.strip():
        # No change to review; treat as a non-decision so callers can skip the gate.
        return {
            "success": False,
            "message": "No modifications detected - nothing for the reviewer to assess",
            "merge_ready": False,
            "blocking_issues": [],
            "advisory_issues": [],
            "summary": "",
            "nested_token_usage": None,
        }

    try:
        from ape.orchestration.config import ExecutionConfig
        from ape.scaffolds.factory import create_scaffold_config_for_type
        from ape.orchestration.orchestrator import TaskOrchestrator
        from ape.llm_clients.config import LLMConfig
        from ape.runtime.factory import create_runtime_config_for_type

        review_data = LeanReviewGateData(
            task_id="merge_readiness_reviewer",
            target_code=final_code,
            original_code=original_code,
            task_description=task_description,
            reference_implementation=reference_implementation,
            gold_diff=gold_diff,
            filename=filename,
            target_workspace=target_workspace,
            metadata={},
        )

        reviewer_task_config = LeanReviewGateConfig(judge_mode=review_config.judge_mode)
        reviewer_runtime_config = create_runtime_config_for_type(review_config.runtime_type)

        reviewer_config = create_scaffold_config_for_type(
            scaffold_type=review_config.scaffold_type,
            base_config=base_config,
            execution=ExecutionConfig(
                num_processes=review_config.num_processes,
                max_concurrency=review_config.max_concurrency,
                max_turns=review_config.max_turns,
                sample_count=num_reviewers,
            ),
            task_config=reviewer_task_config,
            llm_config=LLMConfig(model_name=review_config.model),
            runtime_config=reviewer_runtime_config,
        )

        if parent_attempt_path:
            # One convention for nested work, shared with every other task family: the
            # subtask directory under the parent's attempt, which is what keeps each child's
            # workspace its own. Three call sites had three conventions, and the divergent one
            # cost a class of accounting failures.
            #
            # The config stays this caller's. It deliberately runs a different model at its own
            # sample count, and `num_processes` is passed through unchanged rather than forced
            # to 0 -- that default is v5's, where the lead is known to be inside a worker, and
            # silently changing this caller's concurrency is not part of sharing a directory
            # convention.
            from ape.orchestration.subtasks import nested_config

            reviewer_config = nested_config(
                parent_attempt_path, reviewer_config, group="subtasks",
                num_processes=reviewer_config.execution.num_processes,
            )

        reviewer_task = LeanReviewGateTask(review_data, reviewer_config)

        logger.info(f"Running maintainer-reviewer gate with {num_reviewers} reviewer(s)...")
        reviewer_results = await TaskOrchestrator(config=reviewer_config, logger=logger).run([reviewer_task])

        if not reviewer_results.task_results:
            return {
                "success": False,
                "message": "No reviewer results received, please retry",
                "merge_ready": False,
                "blocking_issues": [],
                "advisory_issues": [],
                "summary": "",
                "nested_token_usage": reviewer_results.total_token_usage,
            }

        aggregated = reviewer_results.task_results[0]
        if not isinstance(aggregated, LeanJudgmentResult):
            logger.error(f"Reviewer task failed: {getattr(aggregated, 'error', None) or 'unknown'}")
            return {
                "success": False,
                "message": f"Reviewer task failed: {getattr(aggregated, 'error', None) or 'no details'}",
                "merge_ready": False,
                "blocking_issues": [],
                "advisory_issues": [],
                "summary": "",
                "nested_token_usage": reviewer_results.total_token_usage,
            }

        merge_ready = aggregated.judgment_conclusion == "positive"

        # Union blocking issues from individual reviewers that blocked; collect advisory.
        blocking_issues: List[str] = []
        advisory_issues: List[str] = []
        summaries: List[str] = []
        per_reviewer = aggregated.judgment_data.get("judge_results", [])
        sources = per_reviewer if per_reviewer else [aggregated]
        for r in sources:
            data = getattr(r, "judgment_data", None) or {}
            if not getattr(r, "success", True):
                continue
            for issue in data.get("blocking_issues", []) or []:
                if issue and issue not in blocking_issues:
                    blocking_issues.append(issue)
            for issue in data.get("advisory_issues", []) or []:
                if issue and issue not in advisory_issues:
                    advisory_issues.append(issue)
            if data.get("summary"):
                summaries.append(data["summary"])

        logger.info(f"🏁 Review gate decision: {'MERGE-READY' if merge_ready else 'BLOCKED'} "
                    f"({len(blocking_issues)} blocking issue(s))")

        return {
            "success": True,
            "message": f"Review gate completed with {num_reviewers} reviewer(s)",
            "merge_ready": merge_ready,
            "blocking_issues": blocking_issues,
            "advisory_issues": advisory_issues,
            "summary": summaries[0] if summaries else "",
            "review_data": aggregated.judgment_data,
            "nested_token_usage": reviewer_results.total_token_usage,
        }

    except Exception:
        logger.error(f"Review gate failed: {traceback.format_exc()}")
        return {
            "success": False,
            "message": f"Review gate failed, please retry: {traceback.format_exc()}",
            "merge_ready": False,
            "blocking_issues": [],
            "advisory_issues": [],
            "summary": "",
            "nested_token_usage": None,
        }


register_task("lean_review_gate", LeanReviewGateTask)
