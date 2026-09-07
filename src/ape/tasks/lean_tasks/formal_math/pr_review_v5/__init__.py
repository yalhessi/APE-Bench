"""The delegating reviewer (v5): one lead per PR round, specialists as subagents.

Two registered task types:
  - `lean_pr_review_v5_lead` (lead.py) — routes work to specialists and records what it did.
  - `lean_pr_review_v5_arm`  (arm.py)  — one specialist invocation, inheriting v4's
    candidate contract whole.

Scheduling, sealing and finalization live in `src/mathlib_review`; this package is
only the execution half.
"""

from .arm import (
    ARM_TASK_TYPE,
    LeanPRReviewV5ArmConfig,
    LeanPRReviewV5ArmData,
    LeanPRReviewV5ArmResult,
    LeanPRReviewV5ArmTask,
)
from .lead import (
    LEAD_TASK_TYPE,
    LeanPRReviewV5LeadConfig,
    LeanPRReviewV5LeadData,
    LeanPRReviewV5LeadResult,
    LeanPRReviewV5LeadTask,
)

__all__ = [
    "ARM_TASK_TYPE",
    "LEAD_TASK_TYPE",
    "LeanPRReviewV5ArmConfig",
    "LeanPRReviewV5ArmData",
    "LeanPRReviewV5ArmResult",
    "LeanPRReviewV5ArmTask",
    "LeanPRReviewV5LeadConfig",
    "LeanPRReviewV5LeadData",
    "LeanPRReviewV5LeadResult",
    "LeanPRReviewV5LeadTask",
]
