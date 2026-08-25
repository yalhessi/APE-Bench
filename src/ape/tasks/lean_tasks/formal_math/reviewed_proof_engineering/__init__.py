"""Reviewed proof engineering task.

Mirrors the standard Lean proof-engineering task but interposes a Mathlib
maintainer-style *reviewer gate* between syntax (compilation) verification and
semantic (LLM-judge) verification. A submission must pass the reviewer — i.e. be
judged merge-ready — before semantic judgment is run.

This is the substrate for the "reviewer-in-the-loop" experiment: when the reviewer
blocks, its feedback is returned to the generating agent (as a non-terminal,
score=0.0 result) so the agent can revise and resubmit, forming a
generate -> review -> revise loop that terminates only once the reviewer passes and
semantic judgment is positive.
"""

from .review_gate import (
    LeanReviewGateConfig,
    LeanReviewGateData,
    LeanReviewGateTask,
    lean_review_gate,
)
from .task import (
    LeanReviewedProofEngineeringConfig,
    LeanReviewedProofEngineeringData,
    LeanReviewedProofEngineeringTask,
    ReviewGateConfig,
)

__all__ = [
    "LeanReviewGateConfig",
    "LeanReviewGateData",
    "LeanReviewGateTask",
    "lean_review_gate",
    "LeanReviewedProofEngineeringConfig",
    "LeanReviewedProofEngineeringData",
    "LeanReviewedProofEngineeringTask",
    "ReviewGateConfig",
]
