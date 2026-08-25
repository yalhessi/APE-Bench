"""
Guidelines-supplied holistic review (`lean_pr_review_guidelines`).

Identical to the holistic acceptability agent (lean_pr_review_v2) in every respect
— same materialization, tools, submit contract, and evaluator — EXCEPT that the
Mathlib community guidelines (distilled checklist + naming/style/documentation/review
summaries) are appended to its system prompt. The supplied guidelines are therefore
the ONLY variable between the two agents, so the experiment measures exactly whether
having the community's stated norms in context moves the agent's flag/no-flag
threshold toward the maintainer's (the convention/judgment gap from the baseline).
"""

from ape.tasks.base import register_task

from .guidelines import guidelines_block
from .task import LeanPRReviewV2Task

__all__ = ["LeanPRReviewGuidelinesTask"]


class LeanPRReviewGuidelinesTask(LeanPRReviewV2Task):
    """Holistic acceptability review with the Mathlib guidelines supplied in-context."""

    task_type = "lean_pr_review_guidelines"

    async def create_system_prompt(self) -> str:
        base = await super().create_system_prompt()  # acceptability_v2 (or selected version)
        return f"{base}\n\n{guidelines_block()}"


register_task("lean_pr_review_guidelines", LeanPRReviewGuidelinesTask)
