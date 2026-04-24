"""Thin skill-enabled PR split task variant."""

from __future__ import annotations

from ..base.task import PRSplitConfig, PRSplitTask
from ..models import PRSplitResult, SkilledPRSplitData


class SkilledPRSplitConfig(PRSplitConfig):
    """Configuration for thin skill-enabled standalone PR split tasks."""

    managed_skill_name: str = "mathlib-pr-split"
    force_skill_use: bool = True


class SkilledPRSplitTask(PRSplitTask):
    """Thin skill-enabled standalone PR split task implementation."""

    task_type = "skilled_pr_split"
    data_class = SkilledPRSplitData
    task_config_class = SkilledPRSplitConfig
    task_result_class = PRSplitResult
