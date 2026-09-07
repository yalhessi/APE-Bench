"""
Holistic first-round PR review task (the acceptability pass).

One of two review implementations (the other is the fully-decomposed checker set
— see duplication.py / generality.py). All share BasePRReviewTask (base.py):
materialization, the submit_findings contract, and the externally-scored result.
This task is the single holistic agent; it selects its framing from the
PROMPT_VERSIONS registry (acceptability_v2 default | mergeready_v1).

See docs/research/review-task-spec.md.
"""

from typing import Tuple

from ape.tasks.base import register_task

from ape.tasks.lean_tasks.formal_math.review_task import (
    DEFAULT_REVIEW_TOOLS,
    BasePRReviewConfig,
    BasePRReviewData,
    BasePRReviewResult,
    BasePRReviewTask,
)
from .prompt import get_prompts

# Back-compat aliases (imported by lean_tasks/__init__, the dataset adapter, tests).
LeanPRReviewV2Config = BasePRReviewConfig
LeanPRReviewV2Data = BasePRReviewData
LeanPRReviewV2Result = BasePRReviewResult

__all__ = [
    "DEFAULT_REVIEW_TOOLS",
    "LeanPRReviewV2Config",
    "LeanPRReviewV2Data",
    "LeanPRReviewV2Result",
    "LeanPRReviewV2Task",
]


class LeanPRReviewV2Task(BasePRReviewTask):
    """Holistic acceptability review: a single agent over the whole PR."""

    task_type = "lean_pr_review_v2"

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return get_prompts(version)


register_task("lean_pr_review_v2", LeanPRReviewV2Task)
