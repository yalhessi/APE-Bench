"""Lean-specific tasks module.

All Lean task implementations are organized into:
- formal_math/: Formal mathematical reasoning
  - theorem_proving/
  - proof_engineering/
  - judgment/
- program_synthesis/: Executable Lean synthesis and translation
  - code_generation/
  - spec_generation/
- utils.py: Utility functions for Lean tasks
- base.py: BaseLeanTask and BaseLeanTaskData base classes
"""

from .base import BaseLeanTask, BaseLeanTaskData
from .formal_math.theorem_proving import (
    LeanTheoremProvingTask,
    LeanTheoremProvingData,
    LeanTheoremProvingConfig,
    LeanTheoremProvingResult,
)
from .formal_math.proof_engineering import (
    LeanProofEngineeringTask,
    LeanProofEngineeringData,
    LeanProofEngineeringConfig,
    LeanProofEngineeringResult,
)
from .formal_math.judgment import (
    LeanJudgmentTask,
    LeanJudgmentData,
    LeanJudgmentConfig,
    LeanJudgmentResult,
)
from .program_synthesis.code_generation import (
    LeanCodeGenerationTask,
    LeanCodeGenerationData,
    LeanCodeGenerationConfig,
    LeanCodeGenerationResult,
)
from .program_synthesis.spec_generation import (
    LeanSpecGenerationTask,
    LeanSpecGenerationData,
    LeanSpecGenerationConfig,
    LeanSpecGenerationResult,
)

__all__ = [
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
