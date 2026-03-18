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
  - program_synthesis/: Executable synthesis and translation tasks
    - code_generation/: Python-to-Lean translation tasks
    - spec_generation/: Prompt-only HumanEval-to-Lean formalization tasks
  - utils.py: Utility functions for Lean tasks
"""

from .base import BaseTask, register_task, create_task_from_data
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
    LeanCodeGenerationTask,
    LeanCodeGenerationData,
    LeanCodeGenerationConfig,
    LeanCodeGenerationResult,
    LeanSpecGenerationTask,
    LeanSpecGenerationData,
    LeanSpecGenerationConfig,
    LeanSpecGenerationResult,
)

__all__ = [
    'BaseTask',
    'register_task',
    'create_task_from_data',
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
    'LeanCodeGenerationTask',
    'LeanCodeGenerationData',
    'LeanCodeGenerationConfig',
    'LeanCodeGenerationResult',
    'LeanSpecGenerationTask',
    'LeanSpecGenerationData',
    'LeanSpecGenerationConfig',
    'LeanSpecGenerationResult',
]
