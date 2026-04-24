"""Typed models for Lean PR review tasks."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from ape.tasks.base import BaseTaskResult

from ..pr_shared.models import (
    PRBaseTaskData,
    PRBenchmarkContext as PRReviewBenchmarkContext,
    PRConversation as PRReviewConversation,
    PRHeadMetadata as PRReviewHeadMetadata,
    PRSnapshot as PRReviewSnapshot,
)
from .findings import ReviewFinding


class PRReviewGroundTruth(BaseModel):
    """Ground-truth labels for PR review evaluation."""

    model_config = ConfigDict(extra="forbid")

    merge_ready: bool = Field(..., description="Whether maintainers judged this PR as merge-ready")
    needs_human_review: bool = Field(
        default=False,
        description="Whether maintainers would want a human handoff before merge",
    )
    decision_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence attached to the merge-readiness judgment",
    )
    blocking_findings: List[ReviewFinding] = Field(default_factory=list, description="Blocking review findings")
    advisory_findings: List[ReviewFinding] = Field(default_factory=list, description="Non-blocking review findings")
    rationale: Optional[str] = Field(default=None, description="Optional rationale from expert reviewers")


class PRReviewEvaluationSpec(BaseModel):
    """Optional evaluation attachment for benchmark-style runs."""

    ground_truth: PRReviewGroundTruth = Field(..., description="Ground-truth labels used for scoring")
    label_source: Optional[str] = Field(default=None, description="Source of the attached labels")


class PRReviewSubmission(BaseModel):
    """Normalized `submit_result` payload for review scoring."""

    model_config = ConfigDict(extra="forbid")

    merge_ready: bool = Field(..., description="Whether the PR is predicted to be merge-ready")
    needs_human_review: bool = Field(
        default=False,
        description="Whether the reviewer recommends escalation or human handoff",
    )
    decision_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Calibrated confidence in the overall merge-readiness decision",
    )
    blocking_findings: List[ReviewFinding] = Field(default_factory=list, description="Predicted blocking findings")
    advisory_findings: List[ReviewFinding] = Field(default_factory=list, description="Predicted advisory findings")
    guide_evidence_topics: List[str] = Field(
        default_factory=list,
        description="Guide-topic evidence declared with the submission",
    )
    feedback: str = Field(default="", description="Submitted reviewer feedback")


class ReviewPRData(PRBaseTaskData):
    """Data model for Lean PR review tasks."""

    task_type: Literal["lean_pr_review"] = Field(
        default="lean_pr_review",
        description="Task type identifier",
    )
    snapshot: PRReviewSnapshot = Field(..., description="Reviewable PR snapshot")
    evaluation: Optional[PRReviewEvaluationSpec] = Field(
        default=None,
        description="Optional scoring attachment for benchmark runs",
    )
    benchmark_context: Optional[PRReviewBenchmarkContext] = Field(
        default=None,
        description="Optional benchmark-only metadata",
    )

    @property
    def ground_truth(self) -> Optional[PRReviewGroundTruth]:
        return self.evaluation.ground_truth if self.evaluation else None

    @property
    def label_source(self) -> Optional[str]:
        return self.evaluation.label_source if self.evaluation else None

    @property
    def primary_case(self) -> Optional[str]:
        return self.benchmark_context.primary_case if self.benchmark_context else None

    @property
    def case_flags(self) -> List[str]:
        return self.benchmark_context.case_flags if self.benchmark_context else []

    @property
    def authoring_mode(self) -> Optional[str]:
        return self.benchmark_context.authoring_mode if self.benchmark_context else None

    @property
    def final_pr_outcome(self) -> Optional[str]:
        return self.benchmark_context.final_pr_outcome if self.benchmark_context else None

    @property
    def maintainer_round_count(self) -> Optional[int]:
        return self.benchmark_context.maintainer_round_count if self.benchmark_context else None

    @property
    def maintainer_feedback_count(self) -> Optional[int]:
        return self.benchmark_context.maintainer_feedback_count if self.benchmark_context else None

    @property
    def changes_requested_count(self) -> Optional[int]:
        return self.benchmark_context.changes_requested_count if self.benchmark_context else None

    @property
    def selected_snapshot_kind(self) -> Optional[str]:
        return self.benchmark_context.selected_snapshot_kind if self.benchmark_context else None

    @property
    def source_labels(self) -> Optional[Dict[str, Any]]:
        return self.benchmark_context.source_labels if self.benchmark_context else None


class SkilledReviewPRData(ReviewPRData):
    """Data model for skill-targeted Lean PR review tasks."""

    task_type: Literal["skilled_pr_review"] = Field(
        default="skilled_pr_review",
        description="Task type identifier",
    )


class SkilledPolicyReviewPRData(ReviewPRData):
    """Data model for policy-heavy skill-targeted Lean PR review tasks."""

    task_type: Literal["skilled_policy_pr_review"] = Field(
        default="skilled_policy_pr_review",
        description="Task type identifier",
    )


class ReviewPRResult(BaseTaskResult):
    """Result model for Lean PR review tasks."""

    model_config = ConfigDict()

    merge_ready: bool = Field(..., description="Predicted merge readiness")
    needs_human_review: bool = Field(
        default=False,
        description="Whether the reviewer requested escalation or human handoff",
    )
    decision_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Calibrated confidence in the overall merge-readiness decision",
    )
    blocking_findings: List[ReviewFinding] = Field(default_factory=list, description="Predicted blocking findings")
    advisory_findings: List[ReviewFinding] = Field(default_factory=list, description="Predicted advisory findings")
    guide_evidence_topics: List[str] = Field(
        default_factory=list,
        description="Guide-topic evidence declared with the submission",
    )
    feedback: str = Field(..., description="Submitted review feedback")
    review_data: Dict[str, Any] = Field(default_factory=dict, description="Detailed review/evaluation data")
    workspace_artifacts: Dict[str, str] = Field(
        default_factory=dict,
        description="Scratch-local artifact paths written for the submitted review and grading output",
    )


# Backward-compatible alias for modules that have not been updated yet.
PRReviewData = ReviewPRData
