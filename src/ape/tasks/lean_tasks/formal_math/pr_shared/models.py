"""Shared models for PR-shaped Lean tasks."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ape.tasks.lean_tasks.base import BaseLeanTaskData


class PRHeadMetadata(BaseModel):
    """PR-head checkout hints for fork-aware workspace resolution."""

    sha: str = Field(..., description="Head commit SHA for the PR branch")
    repo_full_name: str = Field(..., description="GitHub owner/name of the PR head repository")
    clone_url: str = Field(..., description="Git clone URL for the PR head repository")
    ref: str = Field(..., description="Git ref/branch name for the PR head repository")
    is_fork: bool = Field(default=False, description="Whether the PR head repository is a fork")
    default_target: Optional[str] = Field(default=None, description="Default target directory for the PR head repo")
    toolchain: Optional[str] = Field(default=None, description="Lean toolchain for the PR head repo")


class PRConversation(BaseModel):
    """Optional author/reviewer conversation context attached to a PR snapshot."""

    model_config = ConfigDict(extra="forbid")

    author_input: List[Dict[str, Any]] = Field(default_factory=list, description="PR author comments for the snapshot")
    reviewer_feedback: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Reviewer comments for the snapshot",
    )


class PRSnapshot(BaseModel):
    """Neutral PR snapshot envelope shared by review and split tasks."""

    model_config = ConfigDict(extra="forbid")

    pr_number: Optional[int] = Field(default=None, description="Pull request number")
    pr_url: Optional[str] = Field(default=None, description="Pull request URL")
    pr_title: str = Field(..., description="Pull request title")
    pr_author: Optional[str] = Field(default=None, description="Pull request author")
    pr_description: str = Field(default="", description="Pull request description/body")
    pr_dependencies: List[str] = Field(default_factory=list, description="Declared PR dependencies, if any")
    pr_diff: str = Field(..., description="Unified diff patch of the PR snapshot")
    changed_files: List[str] = Field(default_factory=list, description="Changed file paths")
    snapshot_type: Optional[str] = Field(default=None, description="Snapshot type for this record")
    snapshot_at: Optional[str] = Field(default=None, description="Snapshot cutoff timestamp (UTC ISO-8601)")
    snapshot_base_sha: Optional[str] = Field(default=None, description="Base commit used for snapshot context")
    snapshot_head_sha: Optional[str] = Field(default=None, description="Head commit used for snapshot diff context")
    review_state: Optional[str] = Field(default=None, description="Maintainer review state at snapshot time")
    review_focus: Optional[str] = Field(
        default=None,
        description="Optional focus hints for what maintainers care about for this PR",
    )
    pr_head: Optional[PRHeadMetadata] = Field(
        default=None,
        description="PR head checkout hints for fork-aware workspace setup",
    )
    conversation: PRConversation = Field(
        default_factory=PRConversation,
        description="Optional author/reviewer conversation context for this snapshot",
    )


class PRBenchmarkContext(BaseModel):
    """Benchmark-only metadata shared across PR-shaped tasks."""

    model_config = ConfigDict(extra="forbid")

    primary_case: Optional[str] = Field(default=None, description="Primary benchmark case for this PR snapshot")
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
    split_candidate: Optional[bool] = Field(
        default=None,
        description="Hidden flag indicating whether this PR looks like a good split-task candidate",
    )
    maintainer_requested_split: Optional[bool] = Field(
        default=None,
        description="Hidden flag indicating whether maintainer feedback explicitly asked for splitting",
    )


class PRBaseTaskData(BaseLeanTaskData):
    """Shared base model for Lean tasks that operate on PR snapshots."""

    snapshot: PRSnapshot = Field(..., description="Pull-request snapshot envelope")

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
    def pr_head(self) -> Optional[PRHeadMetadata]:
        return self.snapshot.pr_head

    @property
    def conversation(self) -> PRConversation:
        return self.snapshot.conversation
