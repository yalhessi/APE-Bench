"""
PR review benchmark dataset package.
"""

from .config import PRReviewDatasetConfig
from .collector import PRReviewDataCollector

__all__ = [
    "PRReviewDatasetConfig",
    "PRReviewDataCollector",
]
