"""The file-scoped generalist task: one invocation per changed file.

Subclasses the candidate task so the submission contract is the same code — `change_ids ⊆
unit`, subject equality, entity checks, edit confinement. What differs is scope, and scope is
enforced through the one hook the base class exposes rather than by reimplementing the rest.

The scope rule is the arm's whole justification. Cross-site *unification* belongs to the
digest phase, which solves it once for every arm; if this arm also emitted per-site findings
it would duplicate the specialists' output, flood the merge, and leave the cross-arm problem
exactly where it was. So a claim here must need the file view: several targets, or a
`scope_placement` claim, which is inherently about a declaration's position among its
neighbours.
"""

from typing import Any, Dict, List, Optional, Tuple

from ape.tasks.base import register_task

from .candidates import (
    LeanPRReviewV4CandidateConfig,
    LeanPRReviewV4CandidateData,
    LeanPRReviewV4CandidateResult,
    LeanPRReviewV4CandidateTask,
)


class LeanPRReviewV4FileConfig(LeanPRReviewV4CandidateConfig):
    finding_budget: int = 20
    enabled_tools: list = [
        "file_read", "content_search", "lean_verify", "get_lean_goal",
        "code_hover", "code_goto", "code_references",
    ]


class LeanPRReviewV4FileData(LeanPRReviewV4CandidateData):
    task_type: str = "lean_pr_review_v4_file"
    invocation_id: str
    reviewed_path: str


class LeanPRReviewV4FileResult(LeanPRReviewV4CandidateResult):
    invocation_id: Optional[str] = None
    reviewed_path: Optional[str] = None


class LeanPRReviewV4FileTask(LeanPRReviewV4CandidateTask):
    task_type = "lean_pr_review_v4_file"
    data_class = LeanPRReviewV4FileData
    task_config_class = LeanPRReviewV4FileConfig
    task_result_class = LeanPRReviewV4FileResult

    def _get_prompts(self, version: str) -> Tuple[str, str]:
        return self.data.rendered_system_prompt, self.data.rendered_user_prompt

    def _extra_candidate_error(self, candidate: Dict[str, Any]) -> Optional[str]:
        from src.datasets.pr_review_v4.render_file_scoped import file_claim_error

        return file_claim_error(
            candidate.get("change_ids") or [], candidate.get("issue_kind")
        )

    def create_result(self, **kwargs):
        kwargs.setdefault("invocation_id", self.data.invocation_id)
        kwargs.setdefault("reviewed_path", self.data.reviewed_path)
        return super().create_result(**kwargs)


register_task("lean_pr_review_v4_file", LeanPRReviewV4FileTask)
