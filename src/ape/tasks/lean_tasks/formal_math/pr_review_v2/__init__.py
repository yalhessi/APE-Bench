"""First-round PR review tasks (v2): thin, read-only, externally scored.

Two review implementations share BasePRReviewTask (base.py):
  - holistic acceptability pass  -> task.py (lean_pr_review_v2)
  - fully-decomposed checkers     -> golf.py        (lean_pr_review_golf, dominant V2),
                                     duplication.py (lean_pr_review_dup),
                                     generality.py  (lean_pr_review_gen)

Distinct from the legacy formal_math/pr_review task — no review_quality_score,
no multi-round snapshots. Scoring lives in src/datasets/pr_review_v2 (D1/D2/D3).
"""

from .base import (
    DEFAULT_REVIEW_TOOLS,
    BasePRReviewConfig,
    BasePRReviewData,
    BasePRReviewResult,
    BasePRReviewTask,
    VerifiedPRReviewTask,
)
from .task import (
    LeanPRReviewV2Config,
    LeanPRReviewV2Data,
    LeanPRReviewV2Result,
    LeanPRReviewV2Task,
)
from .guidelines_task import LeanPRReviewGuidelinesTask
from .duplication import LeanPRReviewDupConfig, LeanPRReviewDupTask
from .generality import LeanPRReviewGenConfig, LeanPRReviewGenTask
from .golf import LeanPRReviewGolfConfig, LeanPRReviewGolfTask
from .idiom import LeanPRReviewIdiomConfig, LeanPRReviewIdiomTask
from .instantiate import LeanPRReviewInstantiateConfig, LeanPRReviewInstantiateTask
from .selector_task import (
    LeanPRReviewSelectorTask,
    PRReviewSelectorData,
    PRReviewSelectorResult,
)
from .distill_task import LeanPRReviewDistillTask, PRDistillResult

__all__ = [
    "DEFAULT_REVIEW_TOOLS",
    "BasePRReviewConfig",
    "BasePRReviewData",
    "BasePRReviewResult",
    "BasePRReviewTask",
    "VerifiedPRReviewTask",
    "LeanPRReviewV2Config",
    "LeanPRReviewV2Data",
    "LeanPRReviewV2Result",
    "LeanPRReviewV2Task",
    "LeanPRReviewGuidelinesTask",
    "LeanPRReviewDupConfig",
    "LeanPRReviewDupTask",
    "LeanPRReviewGenConfig",
    "LeanPRReviewGenTask",
    "LeanPRReviewGolfConfig",
    "LeanPRReviewGolfTask",
    "LeanPRReviewIdiomConfig",
    "LeanPRReviewIdiomTask",
    "LeanPRReviewInstantiateConfig",
    "LeanPRReviewInstantiateTask",
    "LeanPRReviewSelectorTask",
    "PRReviewSelectorData",
    "PRReviewSelectorResult",
    "LeanPRReviewDistillTask",
    "PRDistillResult",
]
