"""Compatibility shim for PR review task variants."""

from __future__ import annotations

from ape.tasks.base import register_task

from .base.task import ReviewPRConfig, ReviewPRTask
from .findings import (
    ReviewDeclarationReference,
    ReviewDiffLocation,
    ReviewFinding,
    ReviewFindingEvidence,
    ReviewGuideCitation,
)
from .models import (
    PRReviewBenchmarkContext,
    PRReviewConversation,
    PRReviewGroundTruth,
    PRReviewHeadMetadata,
    PRReviewSnapshot,
    PRReviewSubmission,
    ReviewPRData,
    ReviewPRResult,
    SkilledPolicyReviewPRData,
    SkilledReviewPRData,
)
from .skilled.task import SkilledReviewPRConfig, SkilledReviewPRTask
from .skilled_policy.task import SkilledPolicyReviewPRConfig, SkilledPolicyReviewPRTask

register_task("lean_pr_review", ReviewPRTask)
register_task("skilled_pr_review", SkilledReviewPRTask)
register_task("skilled_policy_pr_review", SkilledPolicyReviewPRTask)

__all__ = [
    "ReviewDiffLocation",
    "ReviewDeclarationReference",
    "ReviewGuideCitation",
    "ReviewFindingEvidence",
    "ReviewFinding",
    "PRReviewBenchmarkContext",
    "PRReviewConversation",
    "PRReviewGroundTruth",
    "PRReviewHeadMetadata",
    "PRReviewSnapshot",
    "PRReviewSubmission",
    "ReviewPRConfig",
    "SkilledReviewPRConfig",
    "SkilledPolicyReviewPRConfig",
    "ReviewPRData",
    "SkilledReviewPRData",
    "SkilledPolicyReviewPRData",
    "ReviewPRResult",
    "ReviewPRTask",
    "SkilledReviewPRTask",
    "SkilledPolicyReviewPRTask",
]
