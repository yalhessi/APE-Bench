"""
Generality checker (`lean_pr_review_gen`).

A focused review task whose ONLY job is the V2-generality hunt: for each new
declaration, decide whether it should be stated more generally, and — crucially —
VERIFY the stronger statement by compiling it. "Should be more general" is
unfalsifiable taste in ordinary code review; in Lean it is an executable claim,
so the checker is expected to construct and compile the generalization and put it
in `evidence`. Tool defaults are verify-heavy.
"""

from typing import List, Tuple

from ape.tasks.base import register_task

from ape.tasks.lean_tasks.formal_math.review_task import BasePRReviewConfig, VerifiedPRReviewTask

# The prompt text now lives in `pr_shared.focused_prompts` so the v4 focused arm can
# reuse it without a code edge into this frozen generation. Re-exported here under the
# original names: they are this module's public surface and the config default below.
from ..pr_shared.focused_prompts import GEN_TOOLS, GEN_SYSTEM, GEN_USER  # noqa: F401


class LeanPRReviewGenConfig(BasePRReviewConfig):
    """Generality-checker config: verify-heavy tool defaults."""

    enabled_tools: List[str] = list(GEN_TOOLS)


class LeanPRReviewGenTask(VerifiedPRReviewTask):
    """Focused V2 generality checker (decomposed review implementation)."""

    task_type = "lean_pr_review_gen"
    task_config_class = LeanPRReviewGenConfig

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return GEN_SYSTEM, GEN_USER


register_task("lean_pr_review_gen", LeanPRReviewGenTask)
