"""Baseline PR split task variant."""

from __future__ import annotations

from typing import List, Optional

from ape.tasks.base import BaseTaskConfig

from ..core import PRSplitCoreTask
from ..models import PRSplitData, PRSplitResult


class PRSplitConfig(BaseTaskConfig):
    """Configuration for standalone PR split tasks."""

    diff_preview_char_limit: int = 12000
    managed_skill_name: Optional[str] = None
    force_skill_use: bool = False
    enabled_tools: Optional[List[str]] = [
        "bash_execute",
        "file_read",
        "code_hover",
        "code_goto",
        "code_references",
    ]


class PRSplitTask(PRSplitCoreTask):
    """Standalone PR split task implementation."""

    task_type = "lean_pr_split"
    data_class = PRSplitData
    task_config_class = PRSplitConfig
    task_result_class = PRSplitResult
