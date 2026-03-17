"""
PR Review benchmark configuration.
"""

from pathlib import Path
from typing import Optional, Literal, List
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from ape.utils.project import PROJECT_ROOT


class PRReviewDatasetConfig(BaseModel):
    """Configuration for Mathlib PR review benchmark extraction."""

    repo_owner: str = Field(default="leanprover-community", description="GitHub repository owner")
    repo_name: str = Field(default="mathlib4", description="GitHub repository name")

    dataset_dir: Path = Field(
        default=PROJECT_ROOT / "inputs" / "proof_pr_review",
        description="Output directory for generated benchmark JSONL",
    )
    output_file: Optional[Path] = Field(
        default=None,
        description="Optional explicit output file path",
    )

    date_field: Literal["created", "updated", "closed", "merged"] = Field(
        default="closed",
        description="PR date field used for filtering",
    )
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD), inclusive")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD), inclusive")

    include_merged: bool = Field(default=True, description="Include merged PRs")
    include_closed_unmerged: bool = Field(default=True, description="Include closed-but-unmerged PRs")
    exclude_draft: bool = Field(default=True, description="Exclude draft PRs")

    decision_review_states: List[str] = Field(
        default_factory=lambda: ["APPROVED", "CHANGES_REQUESTED", "COMMENTED"],
        description="Maintainer review states extracted as review rounds",
    )
    include_comment_only_rounds: bool = Field(
        default=True,
        description="If no selected review-state events exist, synthesize rounds from maintainer comments",
    )
    max_review_events_per_pr: int = Field(
        default=0,
        description="Maximum temporal decision points per PR (0 means no limit)",
    )

    max_search_pages: int = Field(default=10, description="Max GitHub search pages (100 results/page)")
    max_prs: int = Field(default=200, description="Max PRs to keep from search candidates")
    pr_order: Literal["newest", "oldest"] = Field(
        default="newest",
        description="Candidate PR extraction order (oldest-first or newest-first)",
    )

    min_changed_files: int = Field(default=1, description="Minimum number of changed files")
    max_changed_files: int = Field(default=30, description="Maximum number of changed files")
    min_diff_lines: int = Field(default=10, description="Minimum additions+deletions")
    max_diff_lines: int = Field(default=800, description="Maximum additions+deletions")

    require_lean_files: bool = Field(default=True, description="Require at least one changed .lean file")
    require_maintainer_feedback: bool = Field(
        default=True,
        description="Require maintainer reviews/comments to build ground truth",
    )

    maintainers_file: Optional[Path] = Field(
        default=None,
        description="Optional newline-separated GitHub usernames treated as maintainers",
    )
    github_token: Optional[str] = Field(
        default=None,
        description="GitHub token (falls back to GITHUB_TOKEN env var if omitted)",
    )
    timeout_seconds: float = Field(default=30.0, description="HTTP timeout")
    request_interval_seconds: float = Field(default=0.0, description="Sleep between API requests")

    rationale_char_limit: int = Field(default=4000, description="Max chars for stored rationale")

    review_focus: str = Field(
        default=(
            "Assess merge readiness under Mathlib standards. "
            "Prioritize semantic correctness, requirement alignment, and scope control."
        ),
        description="Review focus text inserted into task records",
    )

    @property
    def repo_url(self) -> str:
        return f"https://github.com/{self.repo_owner}/{self.repo_name}.git"

    @model_validator(mode="after")
    def validate_constraints(self):
        if not self.include_merged and not self.include_closed_unmerged:
            raise ValueError("At least one of include_merged/include_closed_unmerged must be True")

        if self.start_date:
            datetime.strptime(self.start_date, "%Y-%m-%d")
        if self.end_date:
            datetime.strptime(self.end_date, "%Y-%m-%d")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be <= end_date")

        if self.max_prs <= 0:
            raise ValueError("max_prs must be positive")
        if self.max_search_pages <= 0:
            raise ValueError("max_search_pages must be positive")
        if self.max_review_events_per_pr < 0:
            raise ValueError("max_review_events_per_pr must be >= 0")

        if self.min_diff_lines < 0 or self.max_diff_lines < 0:
            raise ValueError("diff line bounds must be non-negative")
        if self.min_diff_lines > self.max_diff_lines:
            raise ValueError("min_diff_lines must be <= max_diff_lines")

        if self.min_changed_files < 0 or self.max_changed_files < 0:
            raise ValueError("changed file bounds must be non-negative")
        if self.min_changed_files > self.max_changed_files:
            raise ValueError("min_changed_files must be <= max_changed_files")

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if self.request_interval_seconds < 0:
            raise ValueError("request_interval_seconds must be >= 0")

        if self.rationale_char_limit <= 0:
            raise ValueError("rationale_char_limit must be > 0")

        allowed_review_states = {"APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"}
        normalized_states: List[str] = []
        seen = set()
        for state in self.decision_review_states:
            normalized = str(state or "").strip().upper()
            if not normalized or normalized in seen:
                continue
            if normalized not in allowed_review_states:
                raise ValueError(
                    f"Unsupported decision_review_state '{state}'. "
                    f"Allowed: {sorted(allowed_review_states)}"
                )
            normalized_states.append(normalized)
            seen.add(normalized)
        if not normalized_states:
            raise ValueError("decision_review_states must be non-empty")
        self.decision_review_states = normalized_states

        return self
