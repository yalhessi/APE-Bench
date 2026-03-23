"""
Tasks Module.

Provides core task types for theorem proving, proof engineering, judgment,
and Isabelle conjecturing.

Architecture:
- BaseTask: Universal base class for all tasks (in base.py)
- BaseLeanTask: Base class for Lean-specific tasks (in lean_tasks/base.py)
- BaseIsabelleTask: Base class for Isabelle-specific tasks (in isabelle_tasks/base.py)
- lean_tasks/: All Lean task implementations
  - formal_math/: Formal mathematical reasoning tasks
    - theorem_proving/: Theorem proving tasks
    - proof_engineering/: Proof engineering tasks
    - judgment/: Code judgment tasks
  - utils.py: Utility functions for Lean tasks
- isabelle_tasks/: Isabelle task implementations
  - formal_math/: Formal mathematical reasoning tasks
    - conjecturing/: Conjecturing tasks
"""

from .base import BaseTask, register_task, create_task_from_data
from .models import (
    WorkspaceSource,
    GitWorkspaceSource,
    LocalWorkspaceSource,
    WorkspaceInfo,
    LeanWorkspaceInfo,
    IsabelleWorkspaceInfo,
)
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
)
from .isabelle_tasks import (
    BaseIsabelleTask,
    BaseIsabelleTaskData,
    IsabelleConjecturingTask,
    IsabelleConjecturingData,
    IsabelleConjecturingConfig,
    IsabelleConjecturingResult,
)

__all__ = [
    'BaseTask',
    'register_task',
    'create_task_from_data',
    'WorkspaceSource',
    'GitWorkspaceSource',
    'LocalWorkspaceSource',
    'WorkspaceInfo',
    'LeanWorkspaceInfo',
    'IsabelleWorkspaceInfo',
    'BaseLeanTask',
    'BaseLeanTaskData',
    'BaseIsabelleTask',
    'BaseIsabelleTaskData',
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
    'IsabelleConjecturingTask',
    'IsabelleConjecturingData',
    'IsabelleConjecturingConfig',
    'IsabelleConjecturingResult',
]
