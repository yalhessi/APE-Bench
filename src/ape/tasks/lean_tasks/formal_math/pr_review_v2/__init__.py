"""First-round PR review tasks (v2): thin, read-only, externally scored.

Two review implementations share `BasePRReviewTask`, which lives in
`src/mathlib_review/review_task.py` -- three generations inherit it, so it is not v2's.
This package no longer re-exports it: importing it from here made `ape.tasks` eagerly pull v2
in order to reach a class v2 does not own, which is a cycle as well as a lie about ownership.
  - holistic acceptability pass  -> task.py (lean_pr_review_v2)
  - fully-decomposed checkers     -> golf.py        (lean_pr_review_golf, dominant V2),
                                     duplication.py (lean_pr_review_dup),
                                     generality.py  (lean_pr_review_gen)

Distinct from the legacy formal_math/pr_review task — no review_quality_score,
no multi-round snapshots. Scoring lives in src/datasets/pr_review_v2 (D1/D2/D3).
"""

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
