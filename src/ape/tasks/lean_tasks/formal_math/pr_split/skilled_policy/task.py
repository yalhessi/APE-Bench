"""Policy-heavy skill-targeted PR split task variant."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from ..models import PRSplitSubmission, SkilledPolicyPRSplitData
from ..skilled.task import SkilledPRSplitConfig, SkilledPRSplitTask


DEFAULT_SKILLED_POLICY_SPLIT_BOOTSTRAP_PATHS: tuple[str, ...] = (
    "references/splitting-guidelines.md",
    "references/dependency-ordering.md",
    "references/pr-metadata.md",
)


class SkilledPolicyPRSplitConfig(SkilledPRSplitConfig):
    """Configuration for policy-heavy skill-targeted standalone PR split tasks."""

    required_bootstrap_paths: List[str] = Field(
        default_factory=lambda: list(DEFAULT_SKILLED_POLICY_SPLIT_BOOTSTRAP_PATHS)
    )


class SkilledPolicyPRSplitTask(SkilledPRSplitTask):
    """Policy-heavy skill-targeted standalone PR split task implementation."""

    task_type = "skilled_policy_pr_split"
    data_class = SkilledPolicyPRSplitData
    task_config_class = SkilledPolicyPRSplitConfig

    def _build_managed_skill_guidance(self) -> str:
        managed_skill_name = self._get_managed_skill_name() or "mathlib-pr-split"
        relevant_skills = self._get_relevant_managed_skills()
        bootstrap_paths = list(getattr(self.config.task_config, "required_bootstrap_paths", None) or [])
        bootstrap_lines = "\n".join(
            f"{index}. `read_skill(..., relative_path=\"{path}\")`"
            for index, path in enumerate(bootstrap_paths, start=1)
        )
        if not relevant_skills:
            return (
                "<managed_skill_guidance>\n"
                f"This task variant is designed to use the managed `{managed_skill_name}` skill.\n"
                "If no relevant managed skill is available, the run configuration is invalid.\n"
                "</managed_skill_guidance>\n"
            )

        skill_list = "\n".join(
            f"- `{skill.name}` (`{skill.skill_id}`): {skill.description}"
            for skill in relevant_skills
        )
        return (
            "<managed_skill_guidance>\n"
            "This is the policy-heavy skill-targeted PR split task variant.\n"
            "Before finalizing a split plan, read the required bootstrap files via `read_skill`:\n"
            f"{bootstrap_lines}\n"
            "Use those references to reason about coherence, dependency ordering, and PR metadata hygiene.\n"
            "Treat `submit_result` as final-only. Do not use it to discover which bootstrap files are missing.\n"
            "Relevant skill(s):\n"
            f"{skill_list}\n"
            "</managed_skill_guidance>\n"
        )

    def _validate_submission_prerequisites(
        self,
        submission: PRSplitSubmission,
    ) -> Optional[str]:
        blocked_reason = super()._validate_submission_prerequisites(submission)
        if blocked_reason:
            return blocked_reason

        required_bootstrap_paths = list(self.config.task_config.required_bootstrap_paths or [])
        read_paths = set(self._get_skill_read_relative_paths())
        read_paths.discard("SKILL.md")
        missing_bootstrap_paths = [path for path in required_bootstrap_paths if path not in read_paths]
        if missing_bootstrap_paths:
            return (
                "`submit_result` is final-only for `skilled_policy_pr_split`. Finish the skill bootstrap first by "
                "reading these required files with `read_skill`: "
                + ", ".join(f"`{path}`" for path in missing_bootstrap_paths)
                + "."
            )
        return None
