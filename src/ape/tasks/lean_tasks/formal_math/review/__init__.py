"""Every task the Mathlib review system schedules.

Was three packages -- `pr_review_v4`, `pr_review_v5` and the review half of `pr_shared` --
which is what made "which generation is this task" a question anyone had to ask. The pipeline
they served is one package (`src/mathlib_review/`), and so are they.

`base.py` is what every review task inherits: the workspace, the tool grant, `lean_verify_edit`
and the edit-confinement rules around it, the submission plumbing, the statement gate. It lived
inside `pr_review_v2` until a v5-only observation about `lean_verify_edit` changed the tool
contract for every v2 checker.

**Task type strings keep their `v5` spelling on purpose.** `lean_pr_review_v5_arm` and
`lean_pr_review_v5_lead` are inside `FocusedAgentSpec.identity()`, so renaming them would move
every spec hash and the sealed agenda with them -- paying a real identity change for a cosmetic
one. A class name is internal; a task type is a recorded identity.
"""

from .base import (
    BasePRReviewConfig,
    BasePRReviewData,
    BasePRReviewResult,
    BasePRReviewTask,
    DEFAULT_REVIEW_TOOLS,
    VerifiedPRReviewTask,
)
from .candidates import (
    LeanPRReviewV4CandidateConfig, LeanPRReviewV4CandidateData,
    LeanPRReviewV4CandidateResult, LeanPRReviewV4CandidateTask,
)
from .focused import (
    LeanPRReviewV4FocusedConfig, LeanPRReviewV4FocusedData,
    LeanPRReviewV4FocusedResult, LeanPRReviewV4FocusedTask,
)
from .file_scoped import (
    LeanPRReviewV4FileConfig, LeanPRReviewV4FileData,
    LeanPRReviewV4FileResult, LeanPRReviewV4FileTask,
)
from .judgment import (
    LeanPRReviewV4JudgmentConfig, LeanPRReviewV4JudgmentData,
    LeanPRReviewV4JudgmentResult, LeanPRReviewV4JudgmentTask,
)
from .arm import ARM_TASK_TYPE, ReviewArmConfig, ReviewArmData, ReviewArmTask
from .lead import LEAD_TASK_TYPE, ReviewLeadConfig, ReviewLeadData, ReviewLeadTask

__all__ = [
    "BasePRReviewConfig", "BasePRReviewData", "BasePRReviewResult", "BasePRReviewTask",
    "DEFAULT_REVIEW_TOOLS", "VerifiedPRReviewTask",
    "LeanPRReviewV4CandidateConfig", "LeanPRReviewV4CandidateData",
    "LeanPRReviewV4CandidateResult", "LeanPRReviewV4CandidateTask",
    "LeanPRReviewV4FocusedConfig", "LeanPRReviewV4FocusedData",
    "LeanPRReviewV4FocusedResult", "LeanPRReviewV4FocusedTask",
    "LeanPRReviewV4FileConfig", "LeanPRReviewV4FileData",
    "LeanPRReviewV4FileResult", "LeanPRReviewV4FileTask",
    "LeanPRReviewV4JudgmentConfig", "LeanPRReviewV4JudgmentData",
    "LeanPRReviewV4JudgmentResult", "LeanPRReviewV4JudgmentTask",
    "ARM_TASK_TYPE", "ReviewArmConfig", "ReviewArmData", "ReviewArmTask",
    "LEAD_TASK_TYPE", "ReviewLeadConfig", "ReviewLeadData", "ReviewLeadTask",
]
