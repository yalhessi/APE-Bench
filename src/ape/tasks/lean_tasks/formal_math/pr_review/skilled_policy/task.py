"""Policy-heavy skill-targeted PR review task variant."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from ..findings import ReviewFinding
from ..models import SkilledPolicyReviewPRData
from ..skilled.task import SkilledReviewPRConfig, SkilledReviewPRTask


GUIDE_TOPIC_FILE_MAP: dict[str, tuple[str, ...]] = {
    "review_norms": (
        "references/pr-review-guide-reviewer.md",
        "references/pr-review-guide-official.md",
    ),
    "naming": (
        "references/naming-conventions-reviewer.md",
        "references/naming-conventions-official.md",
    ),
    "documentation": (
        "references/documentation-style-reviewer.md",
        "references/documentation-style-official.md",
    ),
    "style": (
        "references/style-guidelines-reviewer.md",
        "references/style-guidelines-official.md",
    ),
    "pr_metadata": (
        "references/commit-conventions-reviewer.md",
        "references/commit-conventions-official.md",
    ),
    "git_workflow": (
        "references/git-guide-reviewer.md",
        "references/git-guide-official.md",
    ),
    "branches_ci": (
        "references/tags-and-branches-reviewer.md",
        "references/tags-and-branches-official.md",
    ),
}

GUIDE_TOPIC_DESCRIPTIONS: dict[str, str] = {
    "review_norms": "merge readiness, blocking vs advisory, and general PR review posture",
    "naming": "declaration naming, theorem statement shape, dot notation, and namespace choices",
    "documentation": "docstrings, module headers, comments, citations, and proof explanations",
    "style": "imports, API design, attributes, deprecations, formatting, and library integration style",
    "pr_metadata": "PR title, PR description, and history-facing metadata conventions",
    "git_workflow": "fork/remote/rebase workflow and contributor git process",
    "branches_ci": "toolchains, CI branches, bors, and nightly-testing branch conventions",
}

DEFAULT_SKILLED_POLICY_REVIEW_REQUIRED_TOPICS: tuple[str, ...] = (
    "review_norms",
    "naming",
    "documentation",
    "style",
)

DEFAULT_SKILLED_POLICY_REVIEW_BOOTSTRAP_PATHS: tuple[str, ...] = (
    "references/pr-review-guide-reviewer.md",
    "references/naming-conventions-reviewer.md",
    "references/documentation-style-reviewer.md",
    "references/style-guidelines-reviewer.md",
    "references/checklist.md",
    "references/tag-mapping.md",
)


class SkilledPolicyReviewPRConfig(SkilledReviewPRConfig):
    """Configuration for policy-heavy skill-targeted Lean PR review tasks."""

    required_guide_evidence_topics: List[str] = Field(
        default_factory=lambda: list(DEFAULT_SKILLED_POLICY_REVIEW_REQUIRED_TOPICS)
    )
    required_guide_bootstrap_paths: List[str] = Field(
        default_factory=lambda: list(DEFAULT_SKILLED_POLICY_REVIEW_BOOTSTRAP_PATHS)
    )


class SkilledPolicyReviewPRTask(SkilledReviewPRTask):
    """Policy-heavy skill-targeted Lean PR review task implementation."""

    task_type = "skilled_policy_pr_review"
    data_class = SkilledPolicyReviewPRData
    task_config_class = SkilledPolicyReviewPRConfig

    def _get_required_guide_evidence_topics(self) -> tuple[str, ...]:
        task_config = getattr(self.config, "task_config", None)
        configured_topics = getattr(task_config, "required_guide_evidence_topics", None)
        if not configured_topics:
            return ()
        return tuple(self._normalize_guide_topics(list(configured_topics)))

    def _get_required_guide_bootstrap_paths(self) -> tuple[str, ...]:
        task_config = getattr(self.config, "task_config", None)
        configured_paths = getattr(task_config, "required_guide_bootstrap_paths", None)
        if not configured_paths:
            return ()

        normalized_paths: list[str] = []
        seen: set[str] = set()
        for path in configured_paths:
            normalized_path = str(path or "").strip()
            if not normalized_path or normalized_path in seen:
                continue
            seen.add(normalized_path)
            normalized_paths.append(normalized_path)
        return tuple(normalized_paths)

    def _infer_guide_topics_from_submission(
        self,
        *,
        blocking_findings: Optional[List[ReviewFinding]] = None,
        advisory_findings: Optional[List[ReviewFinding]] = None,
        feedback: str = "",
    ) -> set[str]:
        inferred: set[str] = set()
        normalized_categories = set(
            self._extract_finding_categories((blocking_findings or []) + (advisory_findings or []))
        )
        feedback_lower = (feedback or "").lower()

        if normalized_categories & {"correctness", "requirements_scope", "robustness_performance"}:
            inferred.add("review_norms")

        if "documentation_metadata" in normalized_categories:
            if any(
                needle in feedback_lower
                for needle in ("pr title", "pr description", "commit message", "metadata", "history-facing")
            ):
                inferred.add("pr_metadata")
            else:
                inferred.add("documentation")

        if "readability_maintainability" in normalized_categories:
            if any(
                needle in feedback_lower
                for needle in (
                    "naming",
                    "rename",
                    "renaming",
                    "theorem name",
                    "declaration name",
                    "namespace",
                    "dot notation",
                    "camelcase",
                    "snake_case",
                )
            ):
                inferred.add("naming")
            else:
                inferred.add("style")

        if normalized_categories & {"integration_compatibility", "tests_ci"}:
            inferred.add("style")
        if "tests_ci" in normalized_categories and any(
            needle in feedback_lower
            for needle in (
                "bors",
                "toolchain",
                "ci",
                "nightly-with-mathlib",
                "nightly-testing",
                "lean-pr-testing",
                "ci branch",
            )
        ):
            inferred.add("branches_ci")

        if any(
            needle in feedback_lower
            for needle in (
                "docstring",
                "docstrings",
                "documentation",
                "module header",
                "proof sketch",
                "citation",
                "citations",
                "comment this proof",
                "comment explaining",
            )
        ):
            inferred.add("documentation")

        if any(
            needle in feedback_lower
            for needle in (
                "naming",
                "rename",
                "renaming",
                "theorem name",
                "declaration name",
                "namespace",
                "dot notation",
                "camelcase",
                "snake_case",
            )
        ):
            inferred.add("naming")

        if any(
            needle in feedback_lower
            for needle in (
                "style",
                "readability",
                "import",
                "api",
                "attribute",
                "attributes",
                "deprecated",
                "deprecation",
                "nonrec",
                "@[simp]",
                "@[ext]",
                "formatter",
                "tactic",
                "library integration",
                "regression test",
                "coverage",
                "test",
            )
        ):
            inferred.add("style")

        if any(
            needle in feedback_lower
            for needle in (
                "pr title",
                "pr description",
                "title and description",
                "permanent git history",
                "commit message",
                "metadata",
            )
        ):
            inferred.add("pr_metadata")

        if any(
            needle in feedback_lower
            for needle in (
                "upstream remote",
                "fork workflow",
                "git checkout",
                "git fetch",
                "rebase onto",
                "local remote",
            )
        ):
            inferred.add("git_workflow")

        if any(
            needle in feedback_lower
            for needle in (
                "bors",
                "toolchain",
                "nightly-with-mathlib",
                "nightly-testing",
                "lean-pr-testing",
                "ci branch",
            )
        ):
            inferred.add("branches_ci")

        return inferred

    def _build_submit_tool_description(self) -> str:
        bootstrap_paths = self._get_required_guide_bootstrap_paths()
        required_topics = self._get_required_guide_evidence_topics()
        bootstrap_lines = "\n".join(f"  - `{path}`" for path in bootstrap_paths)
        required_topic_text = ", ".join(f"`{topic}`" for topic in required_topics)
        return (
            "Submit your final PR review decision.\n\n"
            "FINAL-ONLY TOOL: do not call this tool to discover missing prerequisites.\n"
            "Call it once, at the end, after you have:\n"
            "1. Read the required guide bootstrap files via `read_skill`\n"
            f"{bootstrap_lines}\n"
            "2. Inspected the PR and surrounding code.\n"
            f"3. Prepared `guide_evidence_topics` covering at least {required_topic_text}.\n\n"
            f"{self._build_submission_contract_guidance()}\n"
            "Provide:\n"
            "- merge_ready: whether the PR is ready to merge\n"
            "- needs_human_review: whether the PR should be escalated or handed off for human review\n"
            "- decision_confidence: optional calibrated confidence in the overall decision (0.0-1.0)\n"
            "- blocking_findings: blocking findings preventing merge\n"
            "- advisory_findings: non-blocking findings; use `[]` if you do not have a concrete advisory issue worth raising\n"
            "- evidence on every finding: diff_locations, referenced_files, referenced_declarations, and guide_citations\n"
            "- guide_evidence_topics: guide topics consulted to support policy/style judgments\n"
            "- feedback: concise, evidence-based reviewer feedback grounded in the guides you read; a clean PR can be merge-ready with no extra suggestions\n\n"
            "If the guide bootstrap is incomplete, continue reviewing instead of calling this tool."
        )

    def _build_managed_skill_guidance(self) -> str:
        managed_skill_name = self._get_managed_skill_name() or "mathlib-pr-review"
        relevant_skills = self._get_relevant_managed_skills()
        bootstrap_paths = self._get_required_guide_bootstrap_paths()
        required_topics = self._get_required_guide_evidence_topics()
        required_topic_lines = "\n".join(f"- `{topic}`" for topic in required_topics)
        topic_lines = "\n".join(
            f"- `{topic}`: read one of {', '.join(f'`{path}`' for path in GUIDE_TOPIC_FILE_MAP[topic])}"
            for topic in GUIDE_TOPIC_FILE_MAP
        )
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
            "This is the policy-heavy skill-targeted PR review task variant.\n"
            "Complete this workflow in order. Do not form a final judgment or call `submit_result` "
            "until the guide bootstrap is complete.\n"
            "Guide bootstrap for every `skilled_policy_pr_review` run:\n"
            f"{bootstrap_lines}\n"
            "After the bootstrap, inspect the PR code and use the guides as the only source for quality "
            "judgments such as merge-readiness posture, naming, documentation quality, and style policy. "
            "Code inspection tells you what the PR does; the guides tell you how to judge it.\n"
            "A clean PR may legitimately have zero blocking findings and zero advisory findings. "
            "Do not invent speculative polish comments just to avoid an empty `advisory_findings` list; "
            "prefer no finding over a weak preference or hypothetical cleanup idea.\n"
            "Use `references/checklist.md` and `references/tag-mapping.md` to calibrate whether a point "
            "is truly blocking, merely advisory, or not worth surfacing at all.\n"
            "In `submit_result`, include `guide_evidence_topics` listing the guide topics that support "
            "your review. The submission will be rejected if the bootstrap files were not read, if a "
            "declared topic has no matching guide read, or if the feedback makes guide-backed claims "
            "without the corresponding topic evidence.\n"
            "Treat `submit_result` as a final-only tool. Do not use it to probe for missing guide files.\n"
            "Required guide evidence topics for every run:\n"
            f"{required_topic_lines}\n"
            "Guide topics:\n"
            f"{topic_lines}\n"
            "Relevant skill(s):\n"
            f"{skill_list}\n"
            "</managed_skill_guidance>\n"
        )

    def _validate_submission_prerequisites(
        self,
        *,
        merge_ready: bool,
        blocking_findings: List[ReviewFinding],
        advisory_findings: List[ReviewFinding],
        feedback: str,
        needs_human_review: bool = False,
        decision_confidence: Optional[float] = None,
        guide_evidence_topics: Optional[List[str]] = None,
    ) -> Optional[str]:
        blocked_reason = super()._validate_submission_prerequisites(
            merge_ready=merge_ready,
            needs_human_review=needs_human_review,
            decision_confidence=decision_confidence,
            blocking_findings=blocking_findings,
            advisory_findings=advisory_findings,
            feedback=feedback,
            guide_evidence_topics=guide_evidence_topics,
        )
        if blocked_reason:
            return blocked_reason

        declared_topics = self._normalize_guide_topics(guide_evidence_topics or [])
        required_topics = set(self._get_required_guide_evidence_topics())
        required_bootstrap_paths = self._get_required_guide_bootstrap_paths()
        read_paths = set(self._get_skill_read_relative_paths())
        read_paths.discard("SKILL.md")

        missing_bootstrap_paths = [
            path
            for path in required_bootstrap_paths
            if path not in read_paths
        ]
        if missing_bootstrap_paths:
            return (
                "`submit_result` is final-only for `skilled_policy_pr_review`. "
                "Finish the guide bootstrap first by reading these required files with `read_skill`: "
                + ", ".join(f"`{path}`" for path in missing_bootstrap_paths)
                + ". Then inspect the PR and submit once at the end."
            )

        missing_required_topics = sorted(required_topics - set(declared_topics))
        if missing_required_topics:
            return (
                "This `skilled_policy_pr_review` variant requires explicit guide-topic evidence in "
                "`guide_evidence_topics`. Missing required topics: "
                + ", ".join(f"`{topic}`" for topic in missing_required_topics)
                + ". Read the corresponding guide file(s) and include those topic keys in the submission."
            )

        unsupported_topics = [
            topic
            for topic in declared_topics
            if topic not in GUIDE_TOPIC_FILE_MAP
        ]
        if unsupported_topics:
            supported_topics = ", ".join(f"`{topic}`" for topic in GUIDE_TOPIC_FILE_MAP)
            return (
                "Unknown guide evidence topic(s): "
                + ", ".join(f"`{topic}`" for topic in unsupported_topics)
                + f". Supported topics are: {supported_topics}."
            )

        missing_topic_reads = [
            topic
            for topic in declared_topics
            if not any(path in read_paths for path in GUIDE_TOPIC_FILE_MAP[topic])
        ]
        if missing_topic_reads:
            first_missing = missing_topic_reads[0]
            required_paths = ", ".join(f"`{path}`" for path in GUIDE_TOPIC_FILE_MAP[first_missing])
            return (
                "Guide-backed evidence must come from the matching reference file. "
                f"You declared `{first_missing}` in `guide_evidence_topics`, but did not read any of: "
                f"{required_paths}."
            )

        inferred_topics = self._infer_guide_topics_from_submission(
            blocking_findings=blocking_findings,
            advisory_findings=advisory_findings,
            feedback=feedback,
        )
        missing_inferred_topics = sorted(inferred_topics - set(declared_topics))
        if missing_inferred_topics:
            first_missing = missing_inferred_topics[0]
            required_paths = ", ".join(f"`{path}`" for path in GUIDE_TOPIC_FILE_MAP[first_missing])
            topic_description = GUIDE_TOPIC_DESCRIPTIONS.get(
                first_missing,
                first_missing.replace("_", " "),
            )
            return (
                "The review feedback makes guide-backed claims about "
                f"{topic_description}, so include `{first_missing}` in `guide_evidence_topics` "
                f"and read one of: {required_paths}."
            )

        return None
