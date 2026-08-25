"""Compatibility shim for PR split task variants."""

from __future__ import annotations

from ape.tasks.base import register_task

from .base.task import PRSplitConfig, PRSplitTask
from .models import (
    PRSplitChunk,
    PRSplitData,
    PRSplitResult,
    PRSplitSubmission,
    SkilledPolicyPRSplitData,
    SkilledPRSplitData,
)
from .skilled.task import SkilledPRSplitConfig, SkilledPRSplitTask
from .skilled_policy.task import SkilledPolicyPRSplitConfig, SkilledPolicyPRSplitTask

register_task("lean_pr_split", PRSplitTask)
register_task("skilled_pr_split", SkilledPRSplitTask)
register_task("skilled_policy_pr_split", SkilledPolicyPRSplitTask)

__all__ = [
    "PRSplitChunk",
    "PRSplitConfig",
    "PRSplitData",
    "PRSplitResult",
    "PRSplitSubmission",
    "PRSplitTask",
    "SkilledPRSplitConfig",
    "SkilledPolicyPRSplitConfig",
    "SkilledPRSplitData",
    "SkilledPolicyPRSplitData",
    "SkilledPRSplitTask",
    "SkilledPolicyPRSplitTask",
]
