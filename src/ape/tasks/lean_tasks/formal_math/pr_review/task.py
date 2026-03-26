"""
Lean PR review task.

Evaluates whether an agent can provide Mathlib-quality pull request review feedback,
including merge readiness and issue identification.
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING, Literal, Set, Tuple
import asyncio
import hashlib
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


class ReviewPRResult(BaseTaskResult):
    """Result model for Lean PR review tasks."""

    model_config = ConfigDict()

    merge_ready: bool = Field(..., description="Predicted merge readiness")
    blocking_issue_tags: List[str] = Field(default_factory=list, description="Predicted blocking issue tags")
    advisory_issue_tags: List[str] = Field(default_factory=list, description="Predicted advisory issue tags")
    feedback: str = Field(..., description="Submitted review feedback")
    review_data: Dict[str, Any] = Field(default_factory=dict, description="Detailed review/evaluation data")


class ReviewPRTask(BaseLeanTask):
    """Lean PR review task implementation."""

    task_type = "lean_pr_review"
    data_class = ReviewPRData
    task_config_class = ReviewPRConfig
    task_result_class = ReviewPRResult
    patch_marker_filename = ".ape_pr_review_patch.json"

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
            await cls._clone_workspace_with_hardlinks(base_workspace_path, target_path)
        elif existing_fingerprint and existing_fingerprint != patch_fingerprint:
            raise RuntimeError(
                "PR review workspace already contains a different applied patch. "
                f"workspace={target_path}"
            )

        await asyncio.to_thread(cls._make_path_user_writable, target_path)
        await cls._break_link_for_changed_files(target_path, data.changed_files)
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
    ) -> tuple[Path, WorkspaceInfo, Optional[WorkspaceInfo], Optional[List[WorkspaceInfo]]]:
        attempt_path, scratch_workspace, target_workspace, reference_workspaces = await super().setup_attempt(
            data=data,
            config=config,
            orchestrator_id=orchestrator_id,
            attempt_path=attempt_path,
            logger=logger,
        )

        if target_workspace:
            try:
                target_workspace = await cls._ensure_patched_target_workspace(
                    data=data,
                    target_workspace=target_workspace,
                    logger=logger,
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

        async with aiofiles.open(self.scratch_pr_diff_path, "w", encoding="utf-8") as f:
            await f.write(self.data.pr_diff or "")
        async with aiofiles.open(self.scratch_pr_context_path, "w", encoding="utf-8") as f:
            await f.write("\n".join(context_lines))

        self.scratch_workspace.read_only_path_patterns = [
            str(self.scratch_pr_diff_path.resolve()),
            str(self.scratch_pr_context_path.resolve()),
        ]
        return logger

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
            description=(
                "Submit your final PR review decision.\n\n"
                "Provide:\n"
                "- merge_ready: whether the PR is ready to merge\n"
                "- blocking_issue_tags: blocking issues preventing merge\n"
                "- advisory_issue_tags: non-blocking suggestions\n"
                "- feedback: concise, evidence-based reviewer feedback\n\n"
                "You must call this tool to finish the task."
            )
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
            feedback: Annotated[str, Field(
                description="Final reviewer feedback with key evidence.",
            )] = "",
        ) -> Dict[str, Any]:
            """Submit PR review for evaluation and termination."""
            self.logger.info("Tool submit_result: execution started")
            try:
                evaluation_result, review_data, custom_metrics = self._evaluate_review(
                    merge_ready=merge_ready,
                    blocking_issue_tags=blocking_issue_tags,
                    advisory_issue_tags=advisory_issue_tags or [],
                    feedback=feedback,
                )

                if self.should_terminate(evaluation_result) and self.termination_callback:
                    task_result = self.create_result(
                        success=True,
                        score=evaluation_result.score,
                        merge_ready=merge_ready,
                        blocking_issue_tags=review_data.get("predicted", {}).get("blocking_issue_tags", []),
                        advisory_issue_tags=review_data.get("predicted", {}).get("advisory_issue_tags", []),
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
        feedback: str,
    ) -> Tuple[EvaluationResult, Dict[str, Any], Optional[Dict[str, float]]]:
        task_config: ReviewPRConfig = self.config.task_config

        normalized_blocking = self._normalize_tag_list(blocking_issue_tags)
        normalized_advisory = self._normalize_tag_list(advisory_issue_tags)
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
            feedback=feedback,
            review_data=review_data,
            **kwargs,
        )

    def should_terminate(self, evaluation_result: EvaluationResult = None) -> bool:
        """Terminate once a valid review is submitted."""
        return bool(evaluation_result and evaluation_result.success)


register_task("lean_pr_review", ReviewPRTask)
