"""The focused review task: one spec, one work unit, the sites its rule selected.

Deliberately a subclass of the candidate task rather than a sibling. Everything that makes a
v4 candidate anchorable — `change_ids ⊆ unit`, `primary_subject` equality, the entity check,
the statement gate, edit confinement, the compile-backed verification gate — lives in
`submit_candidates`, and a second implementation of that contract would be a second thing to
keep correct. What a focused invocation changes is its *prompt* and its *identity*, not what
a valid submission is.

Identity is the substantive addition. Four specs run against one work unit, so `work_unit_id`
no longer identifies a run: `invocation_id` (`wu:…#proof_golf`) does. It is carried on the
result so that ingestion can key on it, tell four terminal responses apart from four
duplicates of one, and attribute each candidate to the spec that produced it — from the
invocation, never from the model's own report of which agent it is.
"""

from typing import Optional, Tuple

from ape.tasks.base import register_task

from .candidates import (
    LeanPRReviewV4CandidateConfig,
    LeanPRReviewV4CandidateData,
    LeanPRReviewV4CandidateResult,
    LeanPRReviewV4CandidateTask,
)


class LeanPRReviewV4FocusedConfig(LeanPRReviewV4CandidateConfig):
    """Verify-heavy defaults: a focused claim is settled by compiling the replacement."""

    finding_budget: int = 20
    enabled_tools: list = [
        "file_read",
        "content_search",
        "lean_verify",
        "get_lean_goal",
        "code_hover",
        "code_goto",
    ]


class LeanPRReviewV4FocusedData(LeanPRReviewV4CandidateData):
    task_type: str = "lean_pr_review_v4_focused"
    #: `wu:…#spec_id`. The unit alone cannot identify this run.
    invocation_id: str
    spec_id: str


class LeanPRReviewV4FocusedResult(LeanPRReviewV4CandidateResult):
    invocation_id: Optional[str] = None
    spec_id: Optional[str] = None


class LeanPRReviewV4FocusedTask(LeanPRReviewV4CandidateTask):
    task_type = "lean_pr_review_v4_focused"
    data_class = LeanPRReviewV4FocusedData
    task_config_class = LeanPRReviewV4FocusedConfig
    task_result_class = LeanPRReviewV4FocusedResult

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return self.data.rendered_system_prompt, self.data.rendered_user_prompt

    def create_result(self, **kwargs):
        """Stamp the invocation onto every result the inherited submission path builds.

        Done here rather than in the handler so the contract in `submit_candidates` stays
        one implementation: the focused arm adds identity to the result, and changes nothing
        about what a valid candidate is.
        """

        kwargs.setdefault("invocation_id", self.data.invocation_id)
        kwargs.setdefault("spec_id", self.data.spec_id)
        return super().create_result(**kwargs)


register_task("lean_pr_review_v4_focused", LeanPRReviewV4FocusedTask)
