"""Typed models for Lean PR review tasks."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ape.tasks.base import BaseTaskResult
from ape.tasks.lean_tasks.base import BaseLeanTaskData

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


class PRReviewHeadMetadata(BaseModel):
    """PR-head checkout hints for fork-aware workspace resolution."""

    sha: str = Field(..., description="Head commit SHA for the PR branch")
    repo_full_name: str = Field(..., description="GitHub owner/name of the PR head repository")
    clone_url: str = Field(..., description="Git clone URL for the PR head repository")
    ref: str = Field(..., description="Git ref/branch name for the PR head repository")
    is_fork: bool = Field(default=False, description="Whether the PR head repository is a fork")
    default_target: Optional[str] = Field(default=None, description="Default target directory for the PR head repo")
    toolchain: Optional[str] = Field(default=None, description="Lean toolchain for the PR head repo")


class PRReviewConversation(BaseModel):
    """Optional review-round conversation context attached to a snapshot."""

    author_input: List[Dict[str, Any]] = Field(default_factory=list, description="PR author comments for the snapshot")
    reviewer_feedback: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Reviewer comments for the snapshot",
    )


class PRReviewSnapshot(BaseModel):
    """Reviewable PR snapshot shared by live and benchmark entrypoints."""

    pr_number: Optional[int] = Field(default=None, description="Pull request number")
    pr_url: Optional[str] = Field(default=None, description="Pull request URL")
    pr_title: str = Field(..., description="Pull request title")
    pr_author: Optional[str] = Field(default=None, description="Pull request author")
    pr_description: str = Field(default="", description="Pull request description/body")
    pr_dependencies: List[str] = Field(default_factory=list, description="Declared PR dependencies, if any")
    pr_diff: str = Field(..., description="Unified diff patch of the PR snapshot")
    changed_files: List[str] = Field(default_factory=list, description="Changed file paths")
    snapshot_type: Optional[str] = Field(default=None, description="Snapshot type for this review record")
    snapshot_at: Optional[str] = Field(default=None, description="Snapshot cutoff timestamp (UTC ISO-8601)")
    snapshot_base_sha: Optional[str] = Field(default=None, description="Base commit used for snapshot context")
    snapshot_head_sha: Optional[str] = Field(default=None, description="Head commit used for snapshot diff context")
    review_state: Optional[str] = Field(default=None, description="Maintainer review state at snapshot time")
    review_focus: Optional[str] = Field(
        default=None,
        description="Optional focus hints for what maintainers care about for this PR",
    )
    pr_head: Optional[PRReviewHeadMetadata] = Field(
        default=None,
        description="PR head checkout hints for fork-aware workspace setup",
    )
    conversation: PRReviewConversation = Field(
        default_factory=PRReviewConversation,
        description="Optional author/reviewer conversation context for this snapshot",
    )


class PRReviewEvaluationSpec(BaseModel):
    """Optional evaluation attachment for benchmark-style runs."""

    ground_truth: PRReviewGroundTruth = Field(..., description="Ground-truth labels used for scoring")
    label_source: Optional[str] = Field(default=None, description="Source of the attached labels")


class PRReviewBenchmarkContext(BaseModel):
    """Benchmark-specific metadata that should not leak into the prompt."""

    primary_case: Optional[Literal["easy", "major_feedback", "abandoned"]] = Field(
        default=None,
        description="Primary benchmark case for this review snapshot",
    )
    case_flags: List[str] = Field(default_factory=list, description="Additional benchmark-slice flags")
    authoring_mode: Optional[str] = Field(default=None, description="PR authoring mode classification")
    final_pr_outcome: Optional[str] = Field(default=None, description="Final PR outcome classification")
    maintainer_round_count: Optional[int] = Field(default=None, description="Number of substantive maintainer rounds")
    maintainer_feedback_count: Optional[int] = Field(default=None, description="Count of maintainer feedback items")
    changes_requested_count: Optional[int] = Field(default=None, description="Count of CHANGES_REQUESTED reviews")
    selected_snapshot_kind: Optional[str] = Field(default=None, description="Why this snapshot was selected")
    source_labels: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Source label payload preserved for calibration analysis",
    )
    round_index: Optional[int] = Field(default=None, description="Selected review-round index within the PR")
    round_window: Optional[Dict[str, Optional[str]]] = Field(
        default=None,
        description="Timestamp window describing the selected review round",
    )


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


class ReviewPRData(BaseLeanTaskData):
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
    def pr_number(self) -> Optional[int]:
        return self.snapshot.pr_number

    @property
    def pr_url(self) -> Optional[str]:
        return self.snapshot.pr_url

    @property
    def pr_title(self) -> str:
        return self.snapshot.pr_title

    @property
    def pr_author(self) -> Optional[str]:
        return self.snapshot.pr_author

    @property
    def pr_description(self) -> str:
        return self.snapshot.pr_description

    @property
    def pr_dependencies(self) -> List[str]:
        return self.snapshot.pr_dependencies

    @property
    def pr_diff(self) -> str:
        return self.snapshot.pr_diff

    @property
    def changed_files(self) -> List[str]:
        return self.snapshot.changed_files

    @property
    def snapshot_type(self) -> Optional[str]:
        return self.snapshot.snapshot_type

    @property
    def snapshot_at(self) -> Optional[str]:
        return self.snapshot.snapshot_at

    @property
    def snapshot_base_sha(self) -> Optional[str]:
        return self.snapshot.snapshot_base_sha

    @property
    def snapshot_head_sha(self) -> Optional[str]:
        return self.snapshot.snapshot_head_sha

    @property
    def review_state(self) -> Optional[str]:
        return self.snapshot.review_state

    @property
    def review_focus(self) -> Optional[str]:
        return self.snapshot.review_focus

    @property
    def pr_head(self) -> Optional[PRReviewHeadMetadata]:
        return self.snapshot.pr_head

    @property
    def conversation(self) -> PRReviewConversation:
        return self.snapshot.conversation

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
