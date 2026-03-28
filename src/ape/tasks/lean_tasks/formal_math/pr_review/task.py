"""
Lean PR review task.

Evaluates whether an agent can provide Mathlib-quality pull request review feedback,
including merge readiness and issue identification.
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING, Literal, Set, Tuple
import asyncio
import hashlib
import inspect
import json
import os
import re
import shutil
import traceback
from pathlib import Path
from pydantic import Field, BaseModel, ConfigDict

from ape.tasks.base import BaseTaskConfig, register_task, BaseTaskResult, EvaluationResult
from ape.tasks.lean_tasks.base import BaseLeanTask, BaseLeanTaskData
from ape.tasks.models import WorkspaceInfo
from ape.toolkits.execute.lean.utils.process_ops import run_command

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


DEFAULT_REVIEW_ISSUE_TAGS = [
    "semantic_incorrectness",
    "requirement_mismatch",
    "scope_control_violation",
    "proof_fragility",
    "insufficient_documentation",
    "insufficient_tests",
    "library_integration_issue",
    "deprecated_api_usage",
    "performance_regression",
    "style_or_readability",
]

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

DEFAULT_SKILLED_REVIEW_REQUIRED_TOPICS: tuple[str, ...] = (
    "review_norms",
    "naming",
    "documentation",
    "style",
)

DEFAULT_SKILLED_REVIEW_BOOTSTRAP_PATHS: tuple[str, ...] = (
    "references/pr-review-guide-reviewer.md",
    "references/naming-conventions-reviewer.md",
    "references/documentation-style-reviewer.md",
    "references/style-guidelines-reviewer.md",
)


class ReviewPRConfig(BaseTaskConfig):
    """Configuration for Lean PR review tasks."""

    decision_weight: float = 0.65
    blocking_issue_weight: float = 0.25
    advisory_issue_weight: float = 0.10
    severe_false_approve_max_score: float = 0.20

    strict_tag_validation: bool = False
    allowed_issue_tags: List[str] = Field(default_factory=lambda: list(DEFAULT_REVIEW_ISSUE_TAGS))
    diff_preview_char_limit: int = 12000

    enabled_tools: Optional[List[str]] = [
        "bash_execute",
        "file_read",
        "lean_retrieve",
        "get_lean_goal",
        "code_hover",
        "code_goto",
        "code_references",
    ]


class PRReviewGroundTruth(BaseModel):
    """Ground-truth labels for PR review evaluation."""

    merge_ready: bool = Field(..., description="Whether maintainers judged this PR as merge-ready")
    blocking_issue_tags: List[str] = Field(default_factory=list, description="Blocking issue tags")
    advisory_issue_tags: List[str] = Field(default_factory=list, description="Non-blocking issue tags")
    rationale: Optional[str] = Field(default=None, description="Optional rationale from expert reviewers")


class ReviewPRData(BaseLeanTaskData):
    """Data model for Lean PR review tasks."""

    task_type: Literal["lean_pr_review"] = Field(
        default="lean_pr_review",
        description="Task type identifier",
    )

    pr_number: Optional[int] = Field(default=None, description="Pull request number")
    pr_url: Optional[str] = Field(default=None, description="Pull request URL")
    pr_title: str = Field(..., description="Pull request title")
    pr_author: Optional[str] = Field(default=None, description="Pull request author")
    pr_description: str = Field(default="", description="Pull request description/body")
    pr_dependencies: List[str] = Field(default_factory=list, description="Declared PR dependencies, if any")
    pr_diff: str = Field(..., description="Unified diff patch of the PR")
    changed_files: List[str] = Field(default_factory=list, description="Changed file paths")
    snapshot_type: Optional[str] = Field(default=None, description="Snapshot type for this review record")
    snapshot_at: Optional[str] = Field(default=None, description="Snapshot cutoff timestamp (UTC ISO-8601)")
    snapshot_base_sha: Optional[str] = Field(default=None, description="Base commit used for snapshot context")
    snapshot_head_sha: Optional[str] = Field(default=None, description="Head commit used for snapshot diff context")
    review_state: Optional[str] = Field(default=None, description="Maintainer review state at snapshot time")
    review_focus: Optional[str] = Field(
        default=None,
        description="Optional focus hints for what maintainers care about for this PR",
    )

    ground_truth: Optional[PRReviewGroundTruth] = Field(
        default=None,
        description="Optional ground truth labels for automatic evaluation",
    )


class SkilledReviewPRData(ReviewPRData):
    """Data model for skill-targeted Lean PR review tasks."""

    task_type: Literal["skilled_pr_review"] = Field(
        default="skilled_pr_review",
        description="Task type identifier",
    )


class ReviewPRResult(BaseTaskResult):
    """Result model for Lean PR review tasks."""

    model_config = ConfigDict()

    merge_ready: bool = Field(..., description="Predicted merge readiness")
    blocking_issue_tags: List[str] = Field(default_factory=list, description="Predicted blocking issue tags")
    advisory_issue_tags: List[str] = Field(default_factory=list, description="Predicted advisory issue tags")
    guide_evidence_topics: List[str] = Field(
        default_factory=list,
        description="Guide-topic evidence declared with the submission",
    )
    feedback: str = Field(..., description="Submitted review feedback")
    review_data: Dict[str, Any] = Field(default_factory=dict, description="Detailed review/evaluation data")


class ReviewPRTask(BaseLeanTask):
    """Lean PR review task implementation."""

    task_type = "lean_pr_review"
    data_class = ReviewPRData
    task_config_class = ReviewPRConfig
    task_result_class = ReviewPRResult
    patch_marker_filename = ".ape_pr_review_patch.json"

    def _get_required_skill_name(self) -> str:
        """Return the preferred managed skill name for this task, if configured."""
        task_config = getattr(self.config, "task_config", None)
        required_skill_name = getattr(task_config, "required_skill_name", None)
        if isinstance(required_skill_name, str) and required_skill_name.strip():
            return required_skill_name.strip()
        return "mathlib-pr-review"

    def _get_relevant_managed_skills(self) -> tuple[Any, ...]:
        """Return managed skills that look relevant to Mathlib PR review."""
        from ape.scaffolds.skills import get_task_managed_skills

        managed_skills = get_task_managed_skills(self)
        if not managed_skills or not managed_skills.skills:
            return ()

        required_skill_name = self._get_required_skill_name().lower()
        required_skill_slug = required_skill_name.replace(" ", "-")
        return tuple(
            skill
            for skill in managed_skills.skills
            if skill.name.strip().lower() == required_skill_name
            or skill.skill_id.startswith(f"{required_skill_slug}-")
            or "mathlib" in skill.name.lower()
            or "mathlib" in skill.description.lower()
            or ("pull request" in skill.description.lower() and "review" in skill.description.lower())
        )

    def _build_managed_skill_guidance(self) -> str:
        """Return task-specific prompt guidance about managed skills."""
        return ""

    def _build_submit_tool_description(self) -> str:
        """Return the task-specific description for `submit_result`."""
        return (
            "Submit your final PR review decision.\n\n"
            "Provide:\n"
            "- merge_ready: whether the PR is ready to merge\n"
            "- blocking_issue_tags: blocking issues preventing merge\n"
            "- advisory_issue_tags: non-blocking suggestions\n"
            "- guide_evidence_topics: guide topics consulted to support policy/style judgments\n"
            "- feedback: concise, evidence-based reviewer feedback\n\n"
            "You must call this tool to finish the task."
        )

    def _get_skill_tool_usage(self) -> dict[str, int]:
        """Return tracked managed-skill tool usage counts for this task."""
        usage = getattr(self, "_managed_skill_tool_usage", None)
        if not isinstance(usage, dict):
            return {"list_skills": 0, "read_skill": 0}
        return {
            "list_skills": int(usage.get("list_skills", 0) or 0),
            "read_skill": int(usage.get("read_skill", 0) or 0),
        }

    def _get_skill_read_records(self) -> tuple[tuple[str, str], ...]:
        """Return ordered `(skill_id, relative_path)` pairs read via `read_skill`."""
        usage = getattr(self, "_managed_skill_tool_usage", None)
        if not isinstance(usage, dict):
            return ()

        records = usage.get("read_skill_records", [])
        if not isinstance(records, list):
            return ()

        normalized_records: list[tuple[str, str]] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            skill_id = str(record.get("skill_id") or "").strip()
            relative_path = str(record.get("relative_path") or "SKILL.md").strip() or "SKILL.md"
            if not skill_id:
                continue
            normalized_records.append((skill_id, relative_path))
        return tuple(normalized_records)

    def _get_skill_read_relative_paths(self) -> tuple[str, ...]:
        """Return ordered unique relative paths read from managed skills."""
        ordered_paths: list[str] = []
        seen: set[str] = set()
        for _skill_id, relative_path in self._get_skill_read_records():
            if relative_path in seen:
                continue
            seen.add(relative_path)
            ordered_paths.append(relative_path)
        return tuple(ordered_paths)

    @staticmethod
    def _normalize_guide_topic(topic: str) -> str:
        normalized = topic.strip().lower()
        normalized = re.sub(r"[\s\-]+", "_", normalized)
        normalized = re.sub(r"[^a-z0-9_]", "", normalized)
        return normalized

    def _normalize_guide_topics(self, topics: Optional[List[str]]) -> List[str]:
        if not topics:
            return []
        normalized: List[str] = []
        seen: Set[str] = set()
        for topic in topics:
            n = self._normalize_guide_topic(topic)
            if not n or n in seen:
                continue
            seen.add(n)
            normalized.append(n)
        return normalized

    def _get_required_guide_evidence_topics(self) -> tuple[str, ...]:
        """Return guide topics that every skilled review submission must declare."""
        task_config = getattr(self.config, "task_config", None)
        configured_topics = getattr(task_config, "required_guide_evidence_topics", None)
        if not configured_topics:
            return ()

        return tuple(self._normalize_guide_topics(list(configured_topics)))

    def _get_required_guide_bootstrap_paths(self) -> tuple[str, ...]:
        """Return guide reference files that must be read before final submission."""
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
        blocking_issue_tags: Optional[List[str]] = None,
        advisory_issue_tags: Optional[List[str]] = None,
        feedback: str = "",
    ) -> Set[str]:
        """Infer guide topics that the submission appears to rely on."""
        inferred: Set[str] = set()
        normalized_tags = set(self._normalize_tag_list((blocking_issue_tags or []) + (advisory_issue_tags or [])))
        feedback_lower = (feedback or "").lower()

        if "insufficient_documentation" in normalized_tags:
            inferred.add("documentation")
        if normalized_tags & {"library_integration_issue", "deprecated_api_usage", "performance_regression"}:
            inferred.add("style")

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

    def _validate_submission_prerequisites(
        self,
        *,
        merge_ready: bool,
        blocking_issue_tags: List[str],
        advisory_issue_tags: List[str],
        feedback: str,
        guide_evidence_topics: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Return an error message when submit_result should be rejected."""
        return None

    @classmethod
    def _patch_fingerprint(cls, data: ReviewPRData) -> str:
        digest = hashlib.sha256()
        digest.update((data.target_workspace.commit_hash or "").encode("utf-8"))
        digest.update(b"\0")
        digest.update((data.pr_diff or "").encode("utf-8"))
        return digest.hexdigest()

    @classmethod
    async def _clone_workspace_with_hardlinks(
        cls,
        source_path: Path,
        output_path: Path,
    ) -> None:
        await asyncio.to_thread(
            shutil.copytree,
            source_path,
            output_path,
            symlinks=True,
            copy_function=os.link,
        )

    @classmethod
    async def _break_link_for_changed_files(
        cls,
        workspace_path: Path,
        changed_files: List[str],
    ) -> None:
        for rel_path in changed_files:
            candidate = workspace_path / rel_path
            await cls._ensure_patch_path_writable(workspace_path, candidate)
            await asyncio.to_thread(candidate.parent.mkdir, parents=True, exist_ok=True)
            if not candidate.exists():
                continue
            if candidate.is_dir():
                continue

            temp_path = candidate.parent / f".{candidate.name}.pr_review_copy"
            await asyncio.to_thread(shutil.copy2, candidate, temp_path, follow_symlinks=True)
            await asyncio.to_thread(os.replace, temp_path, candidate)

    @classmethod
    async def _ensure_patch_path_writable(
        cls,
        workspace_path: Path,
        candidate: Path,
    ) -> None:
        current = candidate.parent
        while True:
            if current.exists():
                await asyncio.to_thread(cls._make_path_user_writable, current)
            if current == workspace_path:
                break
            if current.parent == current:
                break
            current = current.parent

        if candidate.exists():
            await asyncio.to_thread(cls._make_path_user_writable, candidate)

    @staticmethod
    def _make_path_user_writable(path: Path) -> None:
        mode = path.stat().st_mode
        if path.is_dir():
            os.chmod(path, mode | 0o700)
        else:
            os.chmod(path, mode | 0o600)

    @classmethod
    async def _read_patch_marker(cls, marker_path: Path) -> Optional[str]:
        if not marker_path.exists():
            return None
        try:
            marker_data = await asyncio.to_thread(json.loads, marker_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return marker_data.get("patch_fingerprint")

    @classmethod
    async def _write_patch_marker(
        cls,
        marker_path: Path,
        *,
        patch_fingerprint: str,
        data: ReviewPRData,
    ) -> None:
        marker_payload = {
            "patch_fingerprint": patch_fingerprint,
            "task_id": data.task_id,
            "pr_number": data.pr_number,
            "snapshot_base_sha": data.snapshot_base_sha,
            "snapshot_head_sha": data.snapshot_head_sha,
        }
        await asyncio.to_thread(
            marker_path.write_text,
            json.dumps(marker_payload, indent=2, ensure_ascii=False),
            "utf-8",
        )

    @classmethod
    async def _apply_pr_diff(
        cls,
        workspace_path: Path,
        pr_diff: str,
        logger: Optional["logging.LoggerAdapter"] = None,
    ) -> None:
        if not pr_diff.strip():
            return

        # `git apply` can silently no-op when the attempt workspace lives under the
        # outer APE git repo (for example `.ape/runs/...`). `patch` applies hunks
        # relative to `cwd`, which makes it reliable for these materialized review
        # workspaces.
        check_stdout, check_stderr, check_code = await run_command(
            ["patch", "--dry-run", "-p1", "--batch"],
            cwd=workspace_path,
            input_text=pr_diff,
            logger=logger,
        )
        if check_code != 0:
            raise RuntimeError(
                "PR diff failed `patch --dry-run` in review workspace:\n"
                f"stdout:\n{check_stdout}\n\nstderr:\n{check_stderr}"
            )

        apply_stdout, apply_stderr, apply_code = await run_command(
            ["patch", "-p1", "--batch"],
            cwd=workspace_path,
            input_text=pr_diff,
            logger=logger,
        )
        if apply_code != 0:
            raise RuntimeError(
                "PR diff failed `patch` in review workspace:\n"
                f"stdout:\n{apply_stdout}\n\nstderr:\n{apply_stderr}"
            )

    @classmethod
    async def _ensure_patched_target_workspace(
        cls,
        data: ReviewPRData,
        target_workspace: WorkspaceInfo,
        logger: Optional["logging.LoggerAdapter"] = None,
        progress_callback=None,
    ) -> WorkspaceInfo:
        target_path = target_workspace.path
        if target_path is None:
            raise RuntimeError("Target workspace path is missing for PR review task")

        patch_fingerprint = cls._patch_fingerprint(data)
        marker_path = target_path / cls.patch_marker_filename
        existing_fingerprint = await cls._read_patch_marker(marker_path)
        if existing_fingerprint == patch_fingerprint:
            if logger:
                logger.info("Using existing patched PR review workspace: %s", target_path)
            await cls._emit_progress(
                progress_callback,
                f"Reusing existing patched PR review workspace for commit {data.target_workspace.commit_hash[:8]}...",
            )
            return target_workspace

        if target_path.is_symlink():
            base_workspace_path = target_path.resolve()
            target_path.unlink()
            if logger:
                logger.info(
                    "Materializing patched PR review workspace from base snapshot: %s -> %s",
                    base_workspace_path,
                    target_path,
                )
            await cls._emit_progress(
                progress_callback,
                "Creating a writable PR review workspace from the cached Lean snapshot...",
            )
            await cls._clone_workspace_with_hardlinks(base_workspace_path, target_path)
        elif existing_fingerprint and existing_fingerprint != patch_fingerprint:
            raise RuntimeError(
                "PR review workspace already contains a different applied patch. "
                f"workspace={target_path}"
            )

        await asyncio.to_thread(cls._make_path_user_writable, target_path)
        await cls._emit_progress(
            progress_callback,
            "Preparing changed files so the PR patch can be applied cleanly...",
        )
        await cls._break_link_for_changed_files(target_path, data.changed_files)
        await cls._emit_progress(
            progress_callback,
            "Applying the PR diff to the review workspace...",
        )
        await cls._apply_pr_diff(target_path, data.pr_diff, logger=logger)
        await cls._write_patch_marker(
            marker_path,
            patch_fingerprint=patch_fingerprint,
            data=data,
        )

        return target_workspace.model_copy(
            update={
                "path": target_path,
                "read_only_path_patterns": target_workspace.read_only_path_patterns or ["**/*"],
            }
        )

    @classmethod
    async def setup_attempt(
        cls,
        data: "ReviewPRData",
        config: "BaseScaffoldConfig",
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
        logger: Optional["logging.LoggerAdapter"] = None,
        progress_callback=None,
    ) -> tuple[Path, WorkspaceInfo, Optional[WorkspaceInfo], Optional[List[WorkspaceInfo]]]:
        attempt_path, scratch_workspace, target_workspace, reference_workspaces = await super().setup_attempt(
            data=data,
            config=config,
            orchestrator_id=orchestrator_id,
            attempt_path=attempt_path,
            logger=logger,
            progress_callback=progress_callback,
        )

        if target_workspace:
            try:
                target_workspace = await cls._ensure_patched_target_workspace(
                    data=data,
                    target_workspace=target_workspace,
                    logger=logger,
                    progress_callback=progress_callback,
                )
            except Exception:
                if logger:
                    logger.error(
                        "Failed to prepare patched PR review workspace: %s",
                        traceback.format_exc(),
                    )
                raise

        return attempt_path, scratch_workspace, target_workspace, reference_workspaces

    def __init__(self, data: ReviewPRData, config: "BaseScaffoldConfig"):
        super().__init__(data, config)
        self.scratch_pr_diff_path: Optional[Path] = None
        self.scratch_pr_context_path: Optional[Path] = None

    @staticmethod
    def _normalize_issue_tag(tag: str) -> str:
        normalized = tag.strip().lower()
        normalized = re.sub(r"[\s\-]+", "_", normalized)
        normalized = re.sub(r"[^a-z0-9_]", "", normalized)
        return normalized

    def _normalize_tag_list(self, tags: Optional[List[str]]) -> List[str]:
        if not tags:
            return []
        normalized: List[str] = []
        seen: Set[str] = set()
        for tag in tags:
            n = self._normalize_issue_tag(tag)
            if not n or n in seen:
                continue
            seen.add(n)
            normalized.append(n)
        return normalized

    @staticmethod
    def _set_metrics(predicted: Set[str], gold: Set[str]) -> Tuple[float, float, float]:
        if not predicted and not gold:
            return 1.0, 1.0, 1.0
        if not predicted:
            return 0.0, 0.0, 0.0

        intersection_size = len(predicted & gold)
        precision = intersection_size / len(predicted) if predicted else 0.0
        recall = 1.0 if not gold else intersection_size / len(gold)
        if precision + recall == 0.0:
            f1 = 0.0
        else:
            f1 = (2.0 * precision * recall) / (precision + recall)
        return precision, recall, f1

    def _build_diff_preview(self, limit: int) -> str:
        if limit <= 0:
            return "# Diff preview disabled by configuration."
        diff_text = self.data.pr_diff or ""
        if len(diff_text) <= limit:
            return diff_text if diff_text.strip() else "# Empty diff"
        truncated = diff_text[:limit].rstrip()
        return (
            f"{truncated}\n\n"
            f"... [truncated preview: showing first {limit} characters; inspect `scratch/pr.diff` for full diff]"
        )

    async def setup(
        self,
        termination_callback,
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
    ) -> "logging.LoggerAdapter":
        """Set up review task workspace artifacts."""
        logger = await super().setup(termination_callback, orchestrator_id, attempt_path)
        if not self.scratch_workspace:
            raise RuntimeError("Scratch workspace not initialized for PR review task")

        self.scratch_pr_diff_path = self.scratch_workspace.path / "pr.diff"
        self.scratch_pr_context_path = self.scratch_workspace.path / "pr_context.md"

        context_lines = [
            f"# PR Review Context",
            f"",
            f"- PR number: {self.data.pr_number if self.data.pr_number is not None else 'N/A'}",
            f"- PR URL: {self.data.pr_url or 'N/A'}",
            f"- Title: {self.data.pr_title}",
            f"- Author: {self.data.pr_author or 'unknown'}",
            f"- Snapshot type: {self.data.snapshot_type or 'unknown'}",
            f"- Snapshot cutoff: {self.data.snapshot_at or 'N/A'}",
            f"- Snapshot base SHA: {self.data.snapshot_base_sha or 'N/A'}",
            f"- Snapshot head SHA: {self.data.snapshot_head_sha or 'N/A'}",
            f"- Review state at snapshot: {self.data.review_state or 'N/A'}",
            f"- Target workspace contents: PR patch already applied at this snapshot",
            f"",
            "## PR dependencies",
        ]
        if self.data.pr_dependencies:
            context_lines.extend([f"- {dependency}" for dependency in self.data.pr_dependencies])
        else:
            context_lines.append("- (none provided)")

        context_lines.extend([
            "",
            "## Changed files",
        ])
        if self.data.changed_files:
            context_lines.extend([f"- {path}" for path in self.data.changed_files])
        else:
            context_lines.append("- (not provided)")

        import aiofiles

        await self.emit_progress("Writing PR review context files into the scratch workspace...")
        async with aiofiles.open(self.scratch_pr_diff_path, "w", encoding="utf-8") as f:
            await f.write(self.data.pr_diff or "")
        async with aiofiles.open(self.scratch_pr_context_path, "w", encoding="utf-8") as f:
            await f.write("\n".join(context_lines))

        self.scratch_workspace.read_only_path_patterns = [
            str(self.scratch_pr_diff_path.resolve()),
            str(self.scratch_pr_context_path.resolve()),
        ]
        return logger

    @staticmethod
    async def _emit_progress(progress_callback, message: str) -> None:
        """Emit a user-facing setup progress update when configured."""
        if not progress_callback:
            return

        result = progress_callback(message)
        if inspect.isawaitable(result):
            await result

    async def create_user_prompt(self) -> str:
        """Create user prompt for PR review."""
        from .prompt import LEAN_PR_REVIEW_USER_PROMPT

        task_config: ReviewPRConfig = self.config.task_config

        pr_display = f"#{self.data.pr_number}" if self.data.pr_number is not None else "N/A"
        if self.data.pr_url:
            pr_display = f"{pr_display} ({self.data.pr_url})"

        changed_files_list = (
            "\n".join(f"- `{file_path}`" for file_path in self.data.changed_files)
            if self.data.changed_files
            else "- (no file list provided)"
        )
        review_focus = self.data.review_focus or "No extra focus hints provided."
        issue_tags = "\n".join(
            f"- `{self._normalize_issue_tag(tag)}`" for tag in task_config.allowed_issue_tags
        )
        pr_dependencies = (
            "\n".join(f"- `{dependency}`" for dependency in self.data.pr_dependencies)
            if self.data.pr_dependencies
            else "- (none provided)"
        )
        snapshot_lines = [
            f"- Snapshot type: {self.data.snapshot_type or 'unknown'}",
            f"- Snapshot cutoff: {self.data.snapshot_at or 'N/A'}",
            f"- Snapshot base SHA: {self.data.snapshot_base_sha or 'N/A'}",
            f"- Snapshot head SHA: {self.data.snapshot_head_sha or 'N/A'}",
            f"- Maintainer review state: {self.data.review_state or 'N/A'}",
        ]
        snapshot_context = "\n".join(snapshot_lines)

        submit_tool_name = f"{self.config.mcp_server_name}submit_result"

        return LEAN_PR_REVIEW_USER_PROMPT.format(
            submit_tool_name=submit_tool_name,
            managed_skill_guidance=self._build_managed_skill_guidance(),
            pr_display=pr_display,
            pr_title=self.data.pr_title,
            pr_author=self.data.pr_author or "unknown",
            changed_files_count=len(self.data.changed_files),
            changed_files_list=changed_files_list,
            pr_dependencies=pr_dependencies,
            snapshot_context=snapshot_context,
            review_focus=review_focus,
            pr_description=self.data.pr_description or "(empty PR description)",
            pr_diff_preview=self._build_diff_preview(task_config.diff_preview_char_limit),
            issue_tags=issue_tags,
        )

    async def register_task_tools(self, mcp) -> None:
        """Register task-specific submission tool."""
        from typing import Annotated
        from pydantic import Field

        @mcp.tool(
            description=self._build_submit_tool_description()
        )
        async def submit_result(
            merge_ready: Annotated[bool, Field(description="True if PR is ready to merge, else False")],
            blocking_issue_tags: Annotated[List[str], Field(
                description="Blocking issue tags. Use canonical tags from prompt."
            )],
            advisory_issue_tags: Annotated[Optional[List[str]], Field(
                description="Advisory issue tags (non-blocking).",
                default=None,
            )] = None,
            guide_evidence_topics: Annotated[Optional[List[str]], Field(
                description=(
                    "Guide-topic evidence used in the review. "
                    "Use keys such as `review_norms`, `naming`, `documentation`, `style`, "
                    "`pr_metadata`, `git_workflow`, and `branches_ci`."
                ),
                default=None,
            )] = None,
            feedback: Annotated[str, Field(
                description="Final reviewer feedback with key evidence.",
            )] = "",
        ) -> Dict[str, Any]:
            """Submit PR review for evaluation and termination."""
            self.logger.info("Tool submit_result: execution started")
            try:
                blocked_reason = self._validate_submission_prerequisites(
                    merge_ready=merge_ready,
                    blocking_issue_tags=blocking_issue_tags,
                    advisory_issue_tags=advisory_issue_tags or [],
                    feedback=feedback,
                    guide_evidence_topics=guide_evidence_topics or [],
                )
                if blocked_reason:
                    self.logger.info("Tool submit_result: rejected by task prerequisites")
                    return {
                        "evaluation_result": EvaluationResult(
                            success=False,
                            score=0.0,
                            message=blocked_reason,
                        ),
                        "message": blocked_reason,
                    }

                evaluation_result, review_data, custom_metrics = self._evaluate_review(
                    merge_ready=merge_ready,
                    blocking_issue_tags=blocking_issue_tags,
                    advisory_issue_tags=advisory_issue_tags or [],
                    guide_evidence_topics=guide_evidence_topics or [],
                    feedback=feedback,
                )

                if self.should_terminate(evaluation_result) and self.termination_callback:
                    task_result = self.create_result(
                        success=True,
                        score=evaluation_result.score,
                        merge_ready=merge_ready,
                        blocking_issue_tags=review_data.get("predicted", {}).get("blocking_issue_tags", []),
                        advisory_issue_tags=review_data.get("predicted", {}).get("advisory_issue_tags", []),
                        guide_evidence_topics=review_data.get("predicted", {}).get("guide_evidence_topics", []),
                        feedback=feedback,
                        review_data=review_data,
                        custom_metrics=custom_metrics,
                    )
                    await self.termination_callback(task_result)

                self.logger.info(
                    "Tool submit_result: execution completed (score=%.3f, success=%s)",
                    evaluation_result.score,
                    evaluation_result.success,
                )
                return {
                    "evaluation_result": evaluation_result,
                    "review_data": review_data,
                    "message": "PR review submitted and evaluated",
                }
            except Exception:
                self.logger.error("PR review evaluation failed: %s", traceback.format_exc())
                return {
                    "evaluation_result": EvaluationResult(
                        success=False,
                        score=0.0,
                        message=traceback.format_exc(),
                    ),
                    "message": "Evaluation failed or not ready",
                }

    def _evaluate_review(
        self,
        merge_ready: bool,
        blocking_issue_tags: List[str],
        advisory_issue_tags: List[str],
        guide_evidence_topics: List[str],
        feedback: str,
    ) -> Tuple[EvaluationResult, Dict[str, Any], Optional[Dict[str, float]]]:
        task_config: ReviewPRConfig = self.config.task_config

        normalized_blocking = self._normalize_tag_list(blocking_issue_tags)
        normalized_advisory = self._normalize_tag_list(advisory_issue_tags)
        normalized_guide_topics = self._normalize_guide_topics(guide_evidence_topics)
        allowed_tags = {self._normalize_issue_tag(tag) for tag in task_config.allowed_issue_tags}

        unknown_tags = sorted(
            set(normalized_blocking + normalized_advisory) - allowed_tags
        )
        if unknown_tags and task_config.strict_tag_validation:
            return (
                EvaluationResult(
                    success=False,
                    score=0.0,
                    message=(
                        "Unknown issue tags under strict_tag_validation: "
                        + ", ".join(f"`{tag}`" for tag in unknown_tags)
                    ),
                ),
                {},
                None,
            )

        predicted = {
            "merge_ready": merge_ready,
            "blocking_issue_tags": normalized_blocking,
            "advisory_issue_tags": normalized_advisory,
            "guide_evidence_topics": normalized_guide_topics,
            "read_skill_relative_paths": list(self._get_skill_read_relative_paths()),
            "unknown_tags": unknown_tags,
            "feedback_length": len(feedback or ""),
        }

        ground_truth = self.data.ground_truth
        if not ground_truth:
            review_data = {
                "predicted": predicted,
                "ground_truth": None,
                "metrics": None,
                "notes": "No ground truth provided; score defaults to 1.0 on valid submission.",
            }
            return (
                EvaluationResult(
                    success=True,
                    score=1.0,
                    message="Review submitted (no ground truth available for scoring).",
                    metrics=review_data,
                ),
                review_data,
                None,
            )

        gold_blocking = set(self._normalize_tag_list(ground_truth.blocking_issue_tags))
        gold_advisory = set(self._normalize_tag_list(ground_truth.advisory_issue_tags))

        blocking_precision, blocking_recall, blocking_f1 = self._set_metrics(
            set(normalized_blocking),
            gold_blocking,
        )
        advisory_precision, advisory_recall, advisory_f1 = self._set_metrics(
            set(normalized_advisory),
            gold_advisory,
        )

        decision_accuracy = 1.0 if merge_ready == ground_truth.merge_ready else 0.0
        weighted_score = (
            task_config.decision_weight * decision_accuracy
            + task_config.blocking_issue_weight * blocking_f1
            + task_config.advisory_issue_weight * advisory_f1
        )

        false_approve = bool(not ground_truth.merge_ready and merge_ready)
        if false_approve:
            weighted_score = min(weighted_score, task_config.severe_false_approve_max_score)
        weighted_score = max(0.0, min(1.0, weighted_score))

        tp = 1.0 if merge_ready and ground_truth.merge_ready else 0.0
        tn = 1.0 if (not merge_ready) and (not ground_truth.merge_ready) else 0.0
        fp = 1.0 if merge_ready and (not ground_truth.merge_ready) else 0.0
        fn = 1.0 if (not merge_ready) and ground_truth.merge_ready else 0.0

        custom_metrics = {
            "decision_accuracy": decision_accuracy,
            "blocking_issue_precision": blocking_precision,
            "blocking_issue_recall": blocking_recall,
            "blocking_issue_f1": blocking_f1,
            "advisory_issue_precision": advisory_precision,
            "advisory_issue_recall": advisory_recall,
            "advisory_issue_f1": advisory_f1,
            "review_quality_score": weighted_score,
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
        }

        review_metrics = {
            "decision_accuracy": decision_accuracy,
            "blocking_issue": {
                "precision": blocking_precision,
                "recall": blocking_recall,
                "f1": blocking_f1,
            },
            "advisory_issue": {
                "precision": advisory_precision,
                "recall": advisory_recall,
                "f1": advisory_f1,
            },
            "false_approve": false_approve,
            "weights": {
                "decision_weight": task_config.decision_weight,
                "blocking_issue_weight": task_config.blocking_issue_weight,
                "advisory_issue_weight": task_config.advisory_issue_weight,
            },
            "review_quality_score": weighted_score,
        }

        review_data = {
            "predicted": predicted,
            "ground_truth": {
                "merge_ready": ground_truth.merge_ready,
                "blocking_issue_tags": sorted(gold_blocking),
                "advisory_issue_tags": sorted(gold_advisory),
                "rationale": ground_truth.rationale,
            },
            "metrics": review_metrics,
        }

        summary = (
            f"Decision match={bool(decision_accuracy)}; "
            f"blocking F1={blocking_f1:.3f}; advisory F1={advisory_f1:.3f}; "
            f"score={weighted_score:.3f}"
        )
        if false_approve:
            summary += " (false-approve penalty applied)"

        return (
            EvaluationResult(
                success=True,
                score=weighted_score,
                message=summary,
                metrics=review_data,
            ),
            review_data,
            custom_metrics,
        )

    def create_result(
        self,
        success: bool,
        score: float,
        merge_ready: bool,
        blocking_issue_tags: List[str],
        advisory_issue_tags: List[str],
        guide_evidence_topics: List[str],
        feedback: str,
        review_data: Dict[str, Any],
        **kwargs,
    ) -> ReviewPRResult:
        return ReviewPRResult(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=success,
            score=score,
            merge_ready=merge_ready,
            blocking_issue_tags=blocking_issue_tags,
            advisory_issue_tags=advisory_issue_tags,
            guide_evidence_topics=guide_evidence_topics,
            feedback=feedback,
            review_data=review_data,
            **kwargs,
        )

    def should_terminate(self, evaluation_result: EvaluationResult = None) -> bool:
        """Terminate once a valid review is submitted."""
        return bool(evaluation_result and evaluation_result.success)


class SkilledReviewPRConfig(ReviewPRConfig):
    """Configuration for skill-targeted Lean PR review tasks."""

    required_skill_name: str = "mathlib-pr-review"
    require_read_skill_before_submit: bool = True
    required_guide_evidence_topics: List[str] = Field(
        default_factory=lambda: list(DEFAULT_SKILLED_REVIEW_REQUIRED_TOPICS)
    )
    required_guide_bootstrap_paths: List[str] = Field(
        default_factory=lambda: list(DEFAULT_SKILLED_REVIEW_BOOTSTRAP_PATHS)
    )


class SkilledReviewPRTask(ReviewPRTask):
    """Skill-targeted Lean PR review task implementation."""

    task_type = "skilled_pr_review"
    data_class = SkilledReviewPRData
    task_config_class = SkilledReviewPRConfig
    task_result_class = ReviewPRResult

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
            "Provide:\n"
            "- merge_ready: whether the PR is ready to merge\n"
            "- blocking_issue_tags: blocking issues preventing merge\n"
            "- advisory_issue_tags: non-blocking suggestions\n"
            "- guide_evidence_topics: guide topics consulted to support policy/style judgments\n"
            "- feedback: concise, evidence-based reviewer feedback grounded in the guides you read\n\n"
            "If the guide bootstrap is incomplete, continue reviewing instead of calling this tool."
        )

    def _build_managed_skill_guidance(self) -> str:
        required_skill_name = self._get_required_skill_name()
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
                f"This task variant is designed to use the managed `{required_skill_name}` skill.\n"
                "If no relevant managed skill is available, the run configuration is invalid.\n"
                "</managed_skill_guidance>\n"
            )

        skill_list = "\n".join(
            f"- `{skill.name}` (`{skill.skill_id}`): {skill.description}"
            for skill in relevant_skills
        )
        return (
            "<managed_skill_guidance>\n"
            "This is the skill-targeted PR review task variant.\n"
            "Complete this workflow in order. Do not form a final judgment or call `submit_result` "
            "until the guide bootstrap is complete.\n"
            "Guide bootstrap for every `skilled_pr_review` run:\n"
            f"{bootstrap_lines}\n"
            "After the bootstrap, inspect the PR code and use the guides as the only source for quality "
            "judgments such as merge-readiness posture, naming, documentation quality, and style policy. "
            "Code inspection tells you what the PR does; the guides tell you how to judge it.\n"
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
        blocking_issue_tags: List[str],
        advisory_issue_tags: List[str],
        feedback: str,
        guide_evidence_topics: Optional[List[str]] = None,
    ) -> Optional[str]:
        task_config: SkilledReviewPRConfig = self.config.task_config
        required_skill_name = self._get_required_skill_name()
        relevant_skills = self._get_relevant_managed_skills()
        if not relevant_skills:
            return (
                f"This `skilled_pr_review` run requires the managed `{required_skill_name}` skill, "
                "but no relevant skill was materialized. Re-run with skills enabled and the "
                "Mathlib review skill available in `skills.extra_roots`."
            )

        usage = self._get_skill_tool_usage()
        if task_config.require_read_skill_before_submit and usage["read_skill"] < 1:
            return (
                "This `skilled_pr_review` variant requires consulting the managed Mathlib review "
                f"skill before submission. Call `list_skills`, then `read_skill` on `{required_skill_name}` "
                "review skill, and continue the review."
            )

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
                "`submit_result` is final-only for `skilled_pr_review`. "
                "Finish the guide bootstrap first by reading these required files with `read_skill`: "
                + ", ".join(f"`{path}`" for path in missing_bootstrap_paths)
                + ". Then inspect the PR and submit once at the end."
            )

        missing_required_topics = sorted(required_topics - set(declared_topics))
        if missing_required_topics:
            return (
                "This `skilled_pr_review` variant requires explicit guide-topic evidence in "
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
            blocking_issue_tags=blocking_issue_tags,
            advisory_issue_tags=advisory_issue_tags,
            feedback=feedback,
        )
        undeclared_inferred_topics = sorted(inferred_topics - set(declared_topics))
        if undeclared_inferred_topics:
            first_topic = undeclared_inferred_topics[0]
            topic_description = GUIDE_TOPIC_DESCRIPTIONS.get(first_topic, first_topic.replace("_", " "))
            required_paths = ", ".join(f"`{path}`" for path in GUIDE_TOPIC_FILE_MAP[first_topic])
            return (
                "Your submission appears to rely on guide-backed evidence for "
                f"{topic_description}, but `guide_evidence_topics` does not include `{first_topic}`. "
                f"Read one of {required_paths} and add `{first_topic}` to `guide_evidence_topics`."
            )

        style_issue_tags = {
            self._normalize_issue_tag(tag)
            for tag in (blocking_issue_tags or []) + (advisory_issue_tags or [])
        }
        if "style_or_readability" in style_issue_tags and not (
            {"naming", "documentation", "style", "pr_metadata"} & set(declared_topics)
        ):
            return (
                "If you submit a `style_or_readability` issue, declare which guide topic supports it "
                "in `guide_evidence_topics` (for example `naming`, `documentation`, `style`, or "
                "`pr_metadata`) and read the matching reference file first."
            )

        return None


register_task("lean_pr_review", ReviewPRTask)
register_task("skilled_pr_review", SkilledReviewPRTask)
