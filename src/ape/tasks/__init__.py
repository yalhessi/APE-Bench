"""
Tasks Module.

Provides core task types for theorem proving, proof engineering, and judgment.

Architecture:
- BaseTask: Universal base class for all tasks (in base.py)
- BaseLeanTask: Base class for Lean-specific tasks (in lean_tasks/base.py)
- lean_tasks/: All Lean task implementations
  - formal_math/: Formal mathematical reasoning tasks
    - theorem_proving/: Theorem proving tasks
    - proof_engineering/: Proof engineering tasks
    - judgment/: Code judgment tasks
    - pr_review/: Pull request review tasks
  - utils.py: Utility functions for Lean tasks
"""

from .base import BaseTask, register_task, create_task_from_data, list_task_types
from .lean_tasks import (
    BaseLeanTask,
    BaseLeanTaskData,
    LeanTheoremProvingTask,
    LeanTheoremProvingData,
    LeanTheoremProvingConfig,
    LeanTheoremProvingResult,
    LeanProofEngineeringTask,
    LeanProofEngineeringData,
    LeanProofEngineeringConfig,
    LeanProofEngineeringResult,
    LeanJudgmentTask,
    LeanJudgmentData,
    LeanJudgmentConfig,
    LeanJudgmentResult,
    ReviewPRTask,
    ReviewPRData,
    ReviewPRConfig,
    ReviewPRResult,
    PRReviewGroundTruth,
)

__all__ = [
    'BaseTask',
    'register_task',
    'create_task_from_data',
    'list_task_types',
    'BaseLeanTask',
    'BaseLeanTaskData',
    'LeanTheoremProvingTask',
    'LeanTheoremProvingData',
    'LeanTheoremProvingConfig',
    'LeanTheoremProvingResult',
    'LeanProofEngineeringTask',
    'LeanProofEngineeringData',
    'LeanProofEngineeringConfig',
    'LeanProofEngineeringResult',
    'LeanJudgmentTask',
    'LeanJudgmentData',
    'LeanJudgmentConfig',
    'LeanJudgmentResult',
    'ReviewPRTask',
    'ReviewPRData',
    'ReviewPRConfig',
    'ReviewPRResult',
    'PRReviewGroundTruth',
]
