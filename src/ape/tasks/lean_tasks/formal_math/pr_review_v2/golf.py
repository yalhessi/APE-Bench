"""
Golf checker (`lean_pr_review_golf`).

A focused review task whose ONLY job is the V2-golf hunt: for each proof the PR
adds or changes, can it be made shorter or more idiomatic? This is the single
DOMINANT V2 sub-family in the gold (proof simplification — ~half of all V2
maintainer findings), and the cleanest executable proposition of all: a shorter
proof either compiles or it does not. The checker is expected to CONSTRUCT the
shorter proof and verify it with lean_verify, putting the verified proof in
`evidence`. Tool defaults are verify-heavy.
"""

from typing import List, Tuple

from ape.tasks.base import register_task

from .base import BasePRReviewConfig, VerifiedPRReviewTask

# The prompt text now lives in `pr_shared.focused_prompts` so the v4 focused arm can
# reuse it without a code edge into this frozen generation. Re-exported here under the
# original names: they are this module's public surface and the config default below.
from ..pr_shared.focused_prompts import GOLF_TOOLS, GOLF_SYSTEM, GOLF_USER  # noqa: F401


class LeanPRReviewGolfConfig(BasePRReviewConfig):
    """Golf-checker config: verify-heavy tool defaults."""

    enabled_tools: List[str] = list(GOLF_TOOLS)


class LeanPRReviewGolfTask(VerifiedPRReviewTask):
    """Focused V2 golf checker — the dominant V2 sub-family (decomposed review)."""

    task_type = "lean_pr_review_golf"
    task_config_class = LeanPRReviewGolfConfig

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return GOLF_SYSTEM, GOLF_USER


register_task("lean_pr_review_golf", LeanPRReviewGolfTask)
