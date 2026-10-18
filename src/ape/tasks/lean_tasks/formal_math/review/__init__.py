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
from .solo import (
    SOLO_RENDERER_VERSION, SOLO_TASK_TYPE, SoloReviewConfig, SoloReviewData,
    SoloReviewResult, SoloReviewTask,
)
from .structured import STRUCTURED_TASK_TYPE, StructuredReviewTask
from .structured_critic import CRITIC_TASK_TYPE, StructuredCriticTask
from .filing_contract import FILING_TASK_TYPE, FilingContractTask

#: The per-PR review designs, by the name a config gives `dataset.design`.
#:
#: A design is a task that reads the whole PR and ends in the solo submission contract --
#: findings with a path, a line, a claim, a fix and a severity -- so everything after the
#: submission (anchoring, finalization, the judge, the probe harness) is design-agnostic
#: (`docs/plans/2026-10-02-review-designs.md` §2). The runner's `routing_mode: solo` path
#: builds one task per episode from this table: the task type, the task-id prefix and the
#: design's own payload (`design_payload`) come from the class, so adding a design is one
#: module, one line here and one config, not a branch in the runner. `solo` is the frozen
#: baseline and is never edited again; every other design is read against it.
DESIGNS = {
    "solo": SoloReviewTask,
    "structured": StructuredReviewTask,
    "structured_critic": StructuredCriticTask,
    "filing_contract": FilingContractTask,
}

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
    "SOLO_RENDERER_VERSION", "SOLO_TASK_TYPE", "SoloReviewConfig", "SoloReviewData",
    "SoloReviewResult", "SoloReviewTask",
    "DESIGNS", "STRUCTURED_TASK_TYPE", "StructuredReviewTask",
    "CRITIC_TASK_TYPE", "StructuredCriticTask",
    "FILING_TASK_TYPE", "FilingContractTask",
]
