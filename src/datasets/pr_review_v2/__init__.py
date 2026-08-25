"""
v2 collector for the first-round Mathlib PR review task.

Implements docs/research/review-task-spec.md. Replaces src/datasets/pr_review
for all new work; the legacy package remains for the old multi-round task.
"""

from .config import PRReviewV2Config
from .schema import PRReviewV2Record, SkipReason, SCHEMA_VERSION

__all__ = ["PRReviewV2Config", "PRReviewV2Record", "SkipReason", "SCHEMA_VERSION"]
