"""
Duplication checker (`lean_pr_review_dup`).

A focused review task whose ONLY job is the V2-duplication hunt: find every
declaration this PR adds that restates or specializes material Mathlib already
has. A holistic agent won't run this exhaustive search; a dedicated checker
whose success criterion IS the search will. Each finding must carry the existing
declaration as `evidence` (proof-carrying). Tool defaults are search-heavy.
"""

from typing import List, Tuple

from ape.tasks.base import register_task

from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewConfig, VerifiedPRReviewTask

# The prompt text now lives in `review.focused_prompts` so the v4 focused arm can
# reuse it without a code edge into this frozen generation. Re-exported here under the
# original names: they are this module's public surface and the config default below.
from ape.tasks.lean_tasks.formal_math.review.focused_prompts import DUP_TOOLS, DUP_SYSTEM, DUP_USER  # noqa: F401


class LeanPRReviewDupConfig(BasePRReviewConfig):
    """Duplication-checker config: search-heavy tool defaults."""

    enabled_tools: List[str] = list(DUP_TOOLS)


class LeanPRReviewDupTask(VerifiedPRReviewTask):
    """Focused V2 duplication checker (decomposed review implementation)."""

    task_type = "lean_pr_review_dup"
    task_config_class = LeanPRReviewDupConfig

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return DUP_SYSTEM, DUP_USER


register_task("lean_pr_review_dup", LeanPRReviewDupTask)
