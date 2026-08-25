"""Reviewed proof-engineering task.

Subclasses :class:`LeanProofEngineeringTask` and interposes a maintainer-reviewer gate
between syntax validation and semantic validation. A submission must be judged merge-ready
by the reviewer before semantic judgment runs; otherwise the reviewer's blocking feedback is
returned to the agent (non-terminal, score 0.0) so it can revise and resubmit.
"""

from __future__ import annotations

import traceback
from typing import List, Literal, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from ape.tasks.base import EvaluationResult, register_task
from ape.tasks.lean_tasks.formal_math.proof_engineering.task import (
    LeanProofEngineeringConfig,
    LeanProofEngineeringData,
    LeanProofEngineeringResult,
    LeanProofEngineeringTask,
)

from .prompt import REVIEWED_PE_GENERATOR_NOTE
from .review_gate import LeanReviewGateConfig, lean_review_gate

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig


class ReviewGateConfig(BaseModel):
    """Configuration for the maintainer-reviewer gate within reviewed proof engineering."""

    enabled: bool = True
    num_reviewers: int = 1  # reviewer samples; majority vote on merge readiness
    model: str = "gpt_5_mini"
    scaffold_type: str = "ape_agent"
    runtime_type: str = "local"
    max_turns: int = 100
    num_processes: int = 0
    max_concurrency: int = 3
    # "with_ground_truth" shows the reviewer the gold/maintainer diff as a calibration
    # reference; "generated_only" hides it.
    judge_mode: str = "generated_only"
    # If the reviewer subsystem errors out, proceed to semantic validation rather than
    # trapping the agent in a loop on infrastructure failures.
    fail_open: bool = True


class LeanReviewedProofEngineeringConfig(LeanProofEngineeringConfig):
    """Proof-engineering config plus a maintainer-reviewer gate."""

    review_gate: ReviewGateConfig = ReviewGateConfig()


class LeanReviewedProofEngineeringData(LeanProofEngineeringData):
    """Data model for reviewed proof-engineering tasks (same shape as proof engineering)."""

    task_type: Literal["lean_reviewed_proof_engineering"] = Field(
        default="lean_reviewed_proof_engineering",
        description="Task type identifier",
    )


class LeanReviewedProofEngineeringTask(LeanProofEngineeringTask):
    """Proof engineering with a merge-readiness reviewer gate before semantic judgment."""

    task_type = "lean_reviewed_proof_engineering"
    data_class = LeanReviewedProofEngineeringData
    task_config_class = LeanReviewedProofEngineeringConfig
    task_result_class = LeanProofEngineeringResult

    async def create_user_prompt(self) -> str:
        """Extend the proof-engineering prompt with the maintainer-review-gate notice."""
        base_prompt = await super().create_user_prompt()
        submit_tool_name = f"{self.config.mcp_server_name}submit_result"
        return base_prompt + REVIEWED_PE_GENERATOR_NOTE.format(submit_tool_name=submit_tool_name)

    async def _evaluate_proof_engineering(self, final_code: str) -> EvaluationResult:
        """Syntax -> reviewer gate -> semantic. The reviewer gate must pass first."""
        try:
            syntax_failure = await self._run_syntax_validation(final_code)
            if syntax_failure is not None:
                return syntax_failure

            cfg: LeanReviewedProofEngineeringConfig = self.config.task_config
            if cfg.review_gate.enabled:
                gate_block = await self._run_review_gate(final_code)
                if gate_block is not None:
                    return gate_block

            return await self._run_semantic_validation(final_code)

        except Exception:
            if self.logger:
                self.logger.error(
                    f"Reviewed proof engineering execution failed: {traceback.format_exc()}"
                )
            return EvaluationResult(success=False, score=0.0, message=traceback.format_exc())

    async def _run_review_gate(self, final_code: str) -> Optional[EvaluationResult]:
        """Run the maintainer-reviewer gate.

        Returns ``None`` when the reviewer judges the change merge-ready (proceed to
        semantic validation). Returns a non-terminal failing ``EvaluationResult``
        (success=True, score=0.0) carrying the reviewer's blocking feedback when the
        reviewer blocks, so the agent can revise and resubmit.
        """
        cfg: LeanReviewedProofEngineeringConfig = self.config.task_config
        gate_cfg = cfg.review_gate

        review_config = LeanReviewGateConfig(
            model=gate_cfg.model,
            scaffold_type=gate_cfg.scaffold_type,
            runtime_type=gate_cfg.runtime_type,
            max_turns=gate_cfg.max_turns,
            num_processes=gate_cfg.num_processes,
            max_concurrency=gate_cfg.max_concurrency,
            judge_mode=gate_cfg.judge_mode,
        )

        gate_result = await lean_review_gate(
            final_code=final_code,
            original_code=self.data.original_code,
            task_description=self.data.task_description,
            review_config=review_config,
            base_config=self.config,
            num_reviewers=gate_cfg.num_reviewers,
            reference_implementation=self.data.reference_implementation,
            filename=self.data.filename,
            target_workspace=self.data.target_workspace,
            gold_diff=self.data.gold_diff,
            logger=self.logger,
            parent_attempt_path=self.attempt_path,
        )

        if not gate_result.get("success"):
            # Reviewer subsystem error (or no-change). Optionally proceed to semantic.
            if gate_cfg.fail_open:
                self.logger.warning(
                    f"Review gate did not produce a decision ({gate_result.get('message')}); "
                    "failing open to semantic validation."
                )
                return None
            return EvaluationResult(
                success=False,
                score=0.0,
                message=f"Review gate system failed: {gate_result.get('message')}",
                nested_token_usage=gate_result.get("nested_token_usage"),
            )

        if gate_result.get("merge_ready"):
            self.logger.info("Review gate passed; proceeding to semantic validation.")
            return None

        # Blocked: return the reviewer's feedback for the agent to act on (non-terminal).
        message = self._format_gate_feedback(
            gate_result.get("blocking_issues") or [],
            gate_result.get("advisory_issues") or [],
            gate_result.get("summary") or "",
        )
        return EvaluationResult(
            success=True,
            score=0.0,
            message=message,
            metrics=None,
            nested_token_usage=gate_result.get("nested_token_usage"),
        )

    @staticmethod
    def _format_gate_feedback(
        blocking_issues: List[str],
        advisory_issues: List[str],
        summary: str,
    ) -> str:
        """Render reviewer feedback as a revision prompt for the generating agent."""
        parts = [
            "Maintainer review: NOT merge-ready. The change compiles but does not yet meet "
            "Mathlib merge standards. Address the blocking issues below and resubmit."
        ]
        if summary:
            parts.append(f"\nReviewer summary:\n{summary}")
        if blocking_issues:
            parts.append(
                "\nBlocking issues (must fix before merge):\n"
                + "\n".join(f"- {issue}" for issue in blocking_issues)
            )
        else:
            parts.append("\nBlocking issues: (reviewer blocked without enumerating specifics)")
        if advisory_issues:
            parts.append(
                "\nAdvisory (non-blocking) suggestions:\n"
                + "\n".join(f"- {issue}" for issue in advisory_issues)
            )
        return "\n".join(parts)


register_task("lean_reviewed_proof_engineering", LeanReviewedProofEngineeringTask)
