"""Baseline PR review task variant."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field, model_validator

from ape.tasks.base import BaseTaskConfig

from ..core import HeadWorkspaceFastPathMode, ReviewPRCoreTask
from ..findings import REVIEW_FINDING_CATEGORIES, normalize_review_categories
from ..models import ReviewPRData, ReviewPRResult


class ReviewPRConfig(BaseTaskConfig):
    """Configuration for Lean PR review tasks."""

    decision_weight: float = 0.65
    blocking_issue_weight: float = 0.25
    advisory_issue_weight: float = 0.10
    severe_false_approve_max_score: float = 0.20

    strict_category_validation: bool = False
    allowed_finding_categories: List[str] = Field(default_factory=lambda: list(REVIEW_FINDING_CATEGORIES))
    diff_preview_char_limit: int = 12000
    managed_skill_name: Optional[str] = None
    force_skill_use: bool = False
    enable_head_cache_fast_path: Optional[bool] = None
    head_workspace_fast_path_mode: HeadWorkspaceFastPathMode = "cache_probe"

    enabled_tools: Optional[List[str]] = [
        "bash_execute",
        "file_read",
        # "lean_retrieve",
        # "get_lean_goal",
        "code_hover",
        "code_goto",
    ]

    @model_validator(mode="after")
    def _normalize_category_config(self) -> "ReviewPRConfig":
        self.allowed_finding_categories = normalize_review_categories(
            list(self.allowed_finding_categories or [])
        )
        if not self.allowed_finding_categories:
            self.allowed_finding_categories = list(REVIEW_FINDING_CATEGORIES)
        return self


class ReviewPRTask(ReviewPRCoreTask):
    """Lean PR review task implementation."""

    task_type = "lean_pr_review"
    data_class = ReviewPRData
    task_config_class = ReviewPRConfig
    task_result_class = ReviewPRResult
