"""Thin skill-enabled PR review task variant."""

from __future__ import annotations

from ..base.task import ReviewPRConfig, ReviewPRTask
from ..models import ReviewPRResult, SkilledReviewPRData


class SkilledReviewPRConfig(ReviewPRConfig):
    """Configuration for thin skill-enabled Lean PR review tasks."""

    managed_skill_name: str = "mathlib-pr-review"
    force_skill_use: bool = True


class SkilledReviewPRTask(ReviewPRTask):
    """Thin skill-enabled Lean PR review task implementation."""

    task_type = "skilled_pr_review"
    data_class = SkilledReviewPRData
    task_config_class = SkilledReviewPRConfig
    task_result_class = ReviewPRResult
