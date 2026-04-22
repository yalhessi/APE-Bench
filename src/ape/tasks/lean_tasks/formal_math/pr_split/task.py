"""Standalone Lean PR split task."""

from __future__ import annotations

import inspect
import json
import re
import traceback
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Dict, List, Optional, Set, TYPE_CHECKING

from pydantic import Field

from ape.tasks.base import BaseTaskConfig, BaseTaskResult, EvaluationResult, register_task
from ape.tasks.lean_tasks.base import BaseLeanTask

from ..pr_review.findings import (
    REVIEW_FINDING_CATEGORIES,
    ReviewFinding,
    coerce_review_findings,
    normalize_review_categories,
    normalize_review_category,
)
from ..pr_shared.change_units import PRChangeUnit, build_chunk_diff, parse_pr_change_units
from .models import (
    PRSplitChunk,
    PRSplitData,
    PRSplitResult,
    PRSplitSubmission,
    SkilledPRSplitData,
)
from .scoring import evaluate_split_submission

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


DEFAULT_SKILLED_SPLIT_BOOTSTRAP_PATHS: tuple[str, ...] = (
    "references/splitting-guidelines.md",
    "references/dependency-ordering.md",
    "references/pr-metadata.md",
)


class PRSplitConfig(BaseTaskConfig):
    """Configuration for standalone PR split tasks."""

    diff_preview_char_limit: int = 12000
    enabled_tools: Optional[List[str]] = [
        "bash_execute",
        "file_read",
        "code_hover",
        "code_goto",
        "code_references",
    ]


class PRSplitTask(BaseLeanTask):
    """Standalone PR split task implementation."""

    task_type = "lean_pr_split"
    data_class = PRSplitData
    task_config_class = PRSplitConfig
    task_result_class = PRSplitResult
    split_submission_schema_filename = "split_submission_schema.json"
    split_submission_example_filename = "split_submission_example.json"
    pr_change_units_filename = "pr_change_units.json"
    submitted_split_filename = "submitted_split.json"
    split_grading_filename = "split_grading.json"
    split_dirname = "splits"

    @classmethod
    def _split_submission_schema_relpath(cls) -> str:
        return f"scratch/{cls.split_submission_schema_filename}"

    @classmethod
    def _split_submission_example_relpath(cls) -> str:
        return f"scratch/{cls.split_submission_example_filename}"

    @classmethod
    def _pr_change_units_relpath(cls) -> str:
        return f"scratch/{cls.pr_change_units_filename}"

    @classmethod
    def _submitted_split_relpath(cls) -> str:
        return f"scratch/{cls.submitted_split_filename}"

    @classmethod
    def _split_grading_relpath(cls) -> str:
        return f"scratch/{cls.split_grading_filename}"

    @classmethod
    def _split_dir_relpath(cls) -> str:
        return f"scratch/{cls.split_dirname}"

    def __init__(self, data: PRSplitData, config: "BaseScaffoldConfig"):
        super().__init__(data, config)
        self.scratch_pr_diff_path: Optional[Path] = None
        self.scratch_pr_context_path: Optional[Path] = None
        self.scratch_pr_change_units_path: Optional[Path] = None
        self.scratch_split_submission_schema_path: Optional[Path] = None
        self.scratch_split_submission_example_path: Optional[Path] = None
        self.scratch_submitted_split_path: Optional[Path] = None
        self.scratch_split_grading_path: Optional[Path] = None
        self.scratch_splits_dir: Optional[Path] = None
        self.change_units: list[PRChangeUnit] = []

    def _get_required_skill_name(self) -> str:
        task_config = getattr(self.config, "task_config", None)
        required_skill_name = getattr(task_config, "required_skill_name", None)
        if isinstance(required_skill_name, str) and required_skill_name.strip():
            return required_skill_name.strip()
        return "mathlib-pr-split"

    def _get_relevant_managed_skills(self) -> tuple[Any, ...]:
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
            or ("pull request" in skill.description.lower() and "split" in skill.description.lower())
        )

    def _get_skill_tool_usage(self) -> dict[str, int]:
        usage = getattr(self, "_managed_skill_tool_usage", None)
        if not isinstance(usage, dict):
            return {"list_skills": 0, "read_skill": 0}
        return {
            "list_skills": int(usage.get("list_skills", 0) or 0),
            "read_skill": int(usage.get("read_skill", 0) or 0),
        }

    def _get_skill_read_relative_paths(self) -> tuple[str, ...]:
        usage = getattr(self, "_managed_skill_tool_usage", None)
        if not isinstance(usage, dict):
            return ()
        records = usage.get("read_skill_records", [])
        ordered_paths: list[str] = []
        seen: set[str] = set()
        if not isinstance(records, list):
            return ()
        for record in records:
            if not isinstance(record, dict):
                continue
            relative_path = str(record.get("relative_path") or "SKILL.md").strip() or "SKILL.md"
            if relative_path in seen:
                continue
            seen.add(relative_path)
            ordered_paths.append(relative_path)
        return tuple(ordered_paths)

    def _build_managed_skill_guidance(self) -> str:
        return ""

    @staticmethod
    def _normalize_repo_relative_path(path: str) -> Optional[str]:
        normalized = str(path or "").strip().replace("\\", "/")
        if not normalized:
            return None
        pure_path = PurePosixPath(normalized)
        if pure_path.is_absolute():
            return None
        parts = pure_path.parts
        if not parts:
            return None
        if parts[0] in {"scratch", "target", "reference"}:
            return None
        if any(part in ("", ".", "..") for part in parts):
            return None
        return normalized

    @classmethod
    def _invalid_repo_relative_path_reason(cls, path: str) -> Optional[str]:
        normalized = str(path or "").strip()
        if not normalized:
            return "path is empty"
        if normalized == "scratch/pr.diff":
            return "use the repo-root file path, not `scratch/pr.diff`"
        pure_path = PurePosixPath(normalized.replace("\\", "/"))
        if pure_path.is_absolute():
            return "path must be repo-root relative, not absolute"
        if pure_path.parts and pure_path.parts[0] in {"scratch", "target", "reference"}:
            return "path must be repo-root relative without a workspace prefix"
        if any(part in ("", ".", "..") for part in pure_path.parts):
            return "path contains unsafe segments"
        return None

    @staticmethod
    def _normalize_finding_category(category: str) -> str:
        return normalize_review_category(category)

    def _normalize_findings(self, findings: Optional[List[ReviewFinding]]) -> List[ReviewFinding]:
        return coerce_review_findings(findings or [])

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

    def _build_change_unit_summary(self, limit: int = 8) -> str:
        if not self.change_units:
            return "- (no change units detected)"
        lines: list[str] = []
        for unit in self.change_units[:limit]:
            span_suffix = ""
            if unit.hunk_header:
                span_suffix = f" `{unit.hunk_header}`"
            lines.append(
                f"- `{unit.unit_id}`: `{unit.file_path}` [{unit.unit_kind}/{unit.operation}]{span_suffix} — {unit.preview}"
            )
        if len(self.change_units) > limit:
            lines.append(f"- ... and {len(self.change_units) - limit} more units in `scratch/pr_change_units.json`")
        return "\n".join(lines)

    def _build_split_submission_schema_payload(self) -> dict[str, object]:
        template = PRSplitSubmission(
            should_split=False,
            rationale="Replace this placeholder with a clear split or no-split rationale.",
            chunks=[],
        )
        return template.model_dump(mode="json")

    def _build_split_submission_example_payload(self) -> dict[str, object]:
        if len(self.change_units) < 2:
            return PRSplitSubmission(
                should_split=False,
                rationale="This PR is already coherent and small enough to review as one unit.",
                chunks=[],
            ).model_dump(mode="json")

        first_unit = self.change_units[0]
        remaining_units = self.change_units[1:]
        second_chunk_units = [unit.unit_id for unit in remaining_units]
        if not second_chunk_units:
            second_chunk_units = [first_unit.unit_id]

        example = PRSplitSubmission(
            should_split=True,
            rationale=(
                "Split out the prerequisite mechanical refactor first, then review the feature work on top "
                "of that smaller foundation."
            ),
            chunks=[
                PRSplitChunk(
                    chunk_id="prep_refactor",
                    title="refactor: isolate prerequisite cleanup",
                    summary="Small mechanical changes that unblock the main feature without mixing semantics.",
                    selected_unit_ids=[first_unit.unit_id],
                    depends_on=[],
                    review={
                        "merge_ready": True,
                        "needs_human_review": False,
                        "decision_confidence": 0.82,
                        "blocking_findings": [],
                        "advisory_findings": [],
                        "feedback": "This prerequisite cleanup looks mergeable as an isolated preparatory PR.",
                    },
                ),
                PRSplitChunk(
                    chunk_id="main_feature",
                    title="feat: land the main change on top of the preparatory cleanup",
                    summary="Feature-facing changes that become easier to review once the prerequisite cleanup lands.",
                    selected_unit_ids=second_chunk_units,
                    depends_on=["prep_refactor"],
                    review={
                        "merge_ready": False,
                        "needs_human_review": True,
                        "decision_confidence": 0.63,
                        "blocking_findings": [
                            {
                                "category": "integration_compatibility",
                                "summary": "Check that the public API boundary is still the intended one after splitting.",
                                "evidence": {
                                    "diff_locations": [
                                        {
                                            "file_path": remaining_units[0].file_path,
                                            "line_start": max(remaining_units[0].new_start or 1, 1),
                                            "line_end": max(
                                                remaining_units[0].new_start or 1,
                                                1,
                                            ),
                                            "diff_side": "new",
                                        }
                                    ],
                                    "referenced_files": [remaining_units[0].file_path],
                                    "referenced_declarations": [],
                                    "guide_citations": [],
                                },
                            }
                        ],
                        "advisory_findings": [],
                        "feedback": "The main feature chunk is reviewable, but it still needs a closer integration check.",
                    },
                ),
            ],
        )
        return example.model_dump(mode="json")

    def _initialize_workspace_artifact_paths(self) -> None:
        if not self.scratch_workspace or not self.scratch_workspace.path:
            return
        self.scratch_submitted_split_path = self.scratch_workspace.path / self.submitted_split_filename
        self.scratch_split_grading_path = self.scratch_workspace.path / self.split_grading_filename
        self.scratch_splits_dir = self.scratch_workspace.path / self.split_dirname

    def _workspace_artifact_relpaths(self) -> Dict[str, str]:
        return {
            "submitted_split": self._submitted_split_relpath(),
            "split_grading": self._split_grading_relpath(),
            "split_dir": self._split_dir_relpath(),
        }

    @staticmethod
    async def _write_json_artifact(path: Path, payload: Dict[str, object]) -> None:
        import aiofiles

        async with aiofiles.open(path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(payload, indent=2, ensure_ascii=False))
            await handle.write("\n")

    async def setup(
        self,
        termination_callback,
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
    ) -> "logging.LoggerAdapter":
        logger = await super().setup(termination_callback, orchestrator_id, attempt_path)
        if not self.scratch_workspace:
            raise RuntimeError("Scratch workspace not initialized for PR split task")

        snapshot = self.data.snapshot
        self.change_units = parse_pr_change_units(snapshot.pr_diff or "", snapshot.changed_files or [])
        self.scratch_pr_diff_path = self.scratch_workspace.path / "pr.diff"
        self.scratch_pr_context_path = self.scratch_workspace.path / "pr_context.md"
        self.scratch_pr_change_units_path = self.scratch_workspace.path / self.pr_change_units_filename
        self.scratch_split_submission_schema_path = self.scratch_workspace.path / self.split_submission_schema_filename
        self.scratch_split_submission_example_path = self.scratch_workspace.path / self.split_submission_example_filename
        self._initialize_workspace_artifact_paths()

        context_lines = [
            "# PR Split Context",
            "",
            f"- PR number: {snapshot.pr_number if snapshot.pr_number is not None else 'N/A'}",
            f"- PR URL: {snapshot.pr_url or 'N/A'}",
            f"- Title: {snapshot.pr_title}",
            f"- Author: {snapshot.pr_author or 'unknown'}",
            f"- Snapshot type: {snapshot.snapshot_type or 'unknown'}",
            f"- Snapshot cutoff: {snapshot.snapshot_at or 'N/A'}",
            f"- Snapshot base SHA: {snapshot.snapshot_base_sha or 'N/A'}",
            f"- Snapshot head SHA: {snapshot.snapshot_head_sha or 'N/A'}",
            f"- Review state at snapshot: {snapshot.review_state or 'N/A'}",
            "- Target workspace contents: base snapshot only; inspect PR changes via scratch artifacts.",
            "",
            "## PR dependencies",
        ]
        if snapshot.pr_dependencies:
            context_lines.extend([f"- {dependency}" for dependency in snapshot.pr_dependencies])
        else:
            context_lines.append("- (none provided)")

        context_lines.extend(["", "## Changed files"])
        if snapshot.changed_files:
            context_lines.extend([f"- {path}" for path in snapshot.changed_files])
        else:
            context_lines.append("- (not provided)")

        import aiofiles

        await self.emit_progress("Writing PR split context files into the scratch workspace...")
        async with aiofiles.open(self.scratch_pr_diff_path, "w", encoding="utf-8") as handle:
            await handle.write(snapshot.pr_diff or "")
        async with aiofiles.open(self.scratch_pr_context_path, "w", encoding="utf-8") as handle:
            await handle.write("\n".join(context_lines))
        async with aiofiles.open(self.scratch_pr_change_units_path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps([unit.model_dump(mode="json") for unit in self.change_units], indent=2, ensure_ascii=False))
            await handle.write("\n")
        async with aiofiles.open(self.scratch_split_submission_schema_path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(self._build_split_submission_schema_payload(), indent=2, ensure_ascii=False))
            await handle.write("\n")
        async with aiofiles.open(self.scratch_split_submission_example_path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(self._build_split_submission_example_payload(), indent=2, ensure_ascii=False))
            await handle.write("\n")
        if self.scratch_splits_dir:
            self.scratch_splits_dir.mkdir(parents=True, exist_ok=True)

        read_only_paths = [
            str(self.scratch_pr_diff_path.resolve()),
            str(self.scratch_pr_context_path.resolve()),
            str(self.scratch_pr_change_units_path.resolve()),
            str(self.scratch_split_submission_schema_path.resolve()),
            str(self.scratch_split_submission_example_path.resolve()),
        ]
        if self.scratch_submitted_split_path:
            read_only_paths.append(str(self.scratch_submitted_split_path.resolve()))
        if self.scratch_split_grading_path:
            read_only_paths.append(str(self.scratch_split_grading_path.resolve()))
        if self.scratch_splits_dir:
            read_only_paths.append(str(self.scratch_splits_dir.resolve()))
        self.scratch_workspace.read_only_path_patterns = read_only_paths
        return logger

    @staticmethod
    async def _emit_progress(progress_callback, message: str) -> None:
        if not progress_callback:
            return
        result = progress_callback(message)
        if inspect.isawaitable(result):
            await result

    def _build_prompt(self, *, managed_skill_guidance: str) -> str:
        from .prompt import LEAN_PR_SPLIT_USER_PROMPT

        task_config: PRSplitConfig = self.config.task_config
        snapshot = self.data.snapshot

        pr_display = f"#{snapshot.pr_number}" if snapshot.pr_number is not None else "N/A"
        if snapshot.pr_url:
            pr_display = f"{pr_display} ({snapshot.pr_url})"

        changed_files_list = (
            "\n".join(f"- `{file_path}`" for file_path in snapshot.changed_files)
            if snapshot.changed_files
            else "- (no file list provided)"
        )
        pr_dependencies = (
            "\n".join(f"- `{dependency}`" for dependency in snapshot.pr_dependencies)
            if snapshot.pr_dependencies
            else "- (none provided)"
        )
        snapshot_lines = [
            f"- Snapshot type: {snapshot.snapshot_type or 'unknown'}",
            f"- Snapshot cutoff: {snapshot.snapshot_at or 'N/A'}",
            f"- Snapshot base SHA: {snapshot.snapshot_base_sha or 'N/A'}",
            f"- Snapshot head SHA: {snapshot.snapshot_head_sha or 'N/A'}",
            f"- Maintainer review state: {snapshot.review_state or 'N/A'}",
        ]
        finding_categories = "\n".join(
            f"- `{self._normalize_finding_category(category)}`" for category in REVIEW_FINDING_CATEGORIES
        )
        submit_tool_name = f"{self.config.mcp_server_name}submit_result"
        return LEAN_PR_SPLIT_USER_PROMPT.format(
            submit_tool_name=submit_tool_name,
            managed_skill_guidance=managed_skill_guidance,
            pr_display=pr_display,
            pr_title=snapshot.pr_title,
            pr_author=snapshot.pr_author or "unknown",
            pr_dependencies=pr_dependencies,
            changed_files_count=len(snapshot.changed_files),
            changed_files_list=changed_files_list,
            snapshot_context="\n".join(snapshot_lines),
            change_unit_summary=self._build_change_unit_summary(),
            pr_description=snapshot.pr_description or "(empty PR description)",
            pr_diff_preview=self._build_diff_preview(task_config.diff_preview_char_limit),
            finding_categories=finding_categories,
        )

    async def create_user_prompt(self) -> str:
        return self._build_prompt(managed_skill_guidance=self._build_managed_skill_guidance())

    @staticmethod
    def _finding_has_code_anchor(finding: ReviewFinding) -> bool:
        evidence = finding.evidence
        return bool(evidence.diff_locations or evidence.referenced_files or evidence.referenced_declarations)

    @classmethod
    def _finding_touched_chunk_diff(cls, finding: ReviewFinding, chunk_file_paths: Set[str]) -> bool:
        for diff_location in finding.evidence.diff_locations:
            if diff_location.file_path in chunk_file_paths:
                return True
        return False

    @staticmethod
    def _dependency_cycle(chunk_map: Dict[str, PRSplitChunk]) -> Optional[List[str]]:
        visiting: list[str] = []
        visited: set[str] = set()

        def dfs(node: str) -> Optional[List[str]]:
            if node in visited:
                return None
            if node in visiting:
                cycle_start = visiting.index(node)
                return visiting[cycle_start:] + [node]
            visiting.append(node)
            for dep in chunk_map[node].depends_on:
                cycle = dfs(dep)
                if cycle:
                    return cycle
            visiting.pop()
            visited.add(node)
            return None

        for chunk_id in chunk_map:
            cycle = dfs(chunk_id)
            if cycle:
                return cycle
        return None

    def _validate_chunk_review(
        self,
        *,
        chunk: PRSplitChunk,
        chunk_file_paths: Set[str],
    ) -> Optional[str]:
        if not chunk.review.feedback:
            return f"Chunk `{chunk.chunk_id}` must include non-empty `review.feedback`."

        for finding_kind, findings in (
            ("Blocking", chunk.review.blocking_findings),
            ("Advisory", chunk.review.advisory_findings),
        ):
            for index, finding in enumerate(findings, start=1):
                finding_label = f"{finding_kind} finding {index} in chunk `{chunk.chunk_id}` (`{finding.category}`)"
                if not finding.summary:
                    return f"{finding_label} must include a short summary."
                if not self._finding_has_code_anchor(finding):
                    return (
                        f"{finding_label} must include at least one code-local evidence anchor via "
                        "`diff_locations`, `referenced_files`, or `referenced_declarations`."
                    )
                for diff_location in finding.evidence.diff_locations:
                    invalid_reason = self._invalid_repo_relative_path_reason(diff_location.file_path)
                    if invalid_reason:
                        return (
                            f"{finding_label} has invalid `diff_locations.file_path` "
                            f"`{diff_location.file_path}`: {invalid_reason}."
                        )
                    if diff_location.file_path not in chunk_file_paths:
                        chunk_examples = ", ".join(f"`{path}`" for path in sorted(chunk_file_paths)[:5]) or "(none)"
                        return (
                            f"{finding_label} must use files touched by chunk `{chunk.chunk_id}` for "
                            f"`diff_locations.file_path`. Got `{diff_location.file_path}`; chunk files include {chunk_examples}."
                        )
                for referenced_file in finding.evidence.referenced_files:
                    invalid_reason = self._invalid_repo_relative_path_reason(referenced_file)
                    if invalid_reason:
                        return (
                            f"{finding_label} has invalid `referenced_files` entry `{referenced_file}`: "
                            f"{invalid_reason}."
                        )
                for declaration in finding.evidence.referenced_declarations:
                    if declaration.file_path is None:
                        continue
                    invalid_reason = self._invalid_repo_relative_path_reason(declaration.file_path)
                    if invalid_reason:
                        return (
                            f"{finding_label} has invalid `referenced_declarations.file_path` "
                            f"`{declaration.file_path}`: {invalid_reason}."
                        )
        return None

    def _validate_submission_prerequisites(
        self,
        submission: PRSplitSubmission,
    ) -> Optional[str]:
        all_unit_ids = [unit.unit_id for unit in self.change_units]
        all_unit_set = set(all_unit_ids)

        if not submission.rationale:
            return "`rationale` must be non-empty."
        if not submission.should_split:
            if submission.chunks:
                return "`should_split=false` requires `chunks=[]`."
            return None

        if len(self.change_units) < 2:
            return "This PR does not expose enough canonical change units to produce a meaningful split."
        if not (2 <= len(submission.chunks) <= 6):
            return "`should_split=true` requires between 2 and 6 chunks."

        chunk_map: dict[str, PRSplitChunk] = {}
        unit_assignment_counts: dict[str, int] = {}
        for chunk in submission.chunks:
            if not chunk.chunk_id:
                return "Each chunk must include a non-empty `chunk_id`."
            if chunk.chunk_id in chunk_map:
                return f"Duplicate chunk_id `{chunk.chunk_id}`."
            if not chunk.title:
                return f"Chunk `{chunk.chunk_id}` must include a non-empty `title`."
            if not chunk.summary:
                return f"Chunk `{chunk.chunk_id}` must include a non-empty `summary`."
            if not chunk.selected_unit_ids:
                return f"Chunk `{chunk.chunk_id}` must include at least one `selected_unit_id`."
            chunk_map[chunk.chunk_id] = chunk
            for unit_id in chunk.selected_unit_ids:
                if unit_id not in all_unit_set:
                    return (
                        f"Chunk `{chunk.chunk_id}` references unknown unit_id `{unit_id}`. "
                        f"Use IDs from `{self._pr_change_units_relpath()}` only."
                    )
                unit_assignment_counts[unit_id] = unit_assignment_counts.get(unit_id, 0) + 1

        for chunk in submission.chunks:
            for dependency in chunk.depends_on:
                if dependency not in chunk_map:
                    return f"Chunk `{chunk.chunk_id}` depends on unknown chunk_id `{dependency}`."
                if dependency == chunk.chunk_id:
                    return f"Chunk `{chunk.chunk_id}` cannot depend on itself."

        cycle = self._dependency_cycle(chunk_map)
        if cycle:
            cycle_text = " -> ".join(cycle)
            return f"`depends_on` must be acyclic. Detected cycle: {cycle_text}."

        overlapping_units = sorted(unit_id for unit_id, count in unit_assignment_counts.items() if count > 1)
        if overlapping_units:
            overlap_preview = ", ".join(f"`{unit_id}`" for unit_id in overlapping_units[:5])
            return f"Each diff unit must be assigned exactly once. Overlapping units include {overlap_preview}."

        missing_units = [unit_id for unit_id in all_unit_ids if unit_assignment_counts.get(unit_id, 0) != 1]
        if missing_units:
            missing_preview = ", ".join(f"`{unit_id}`" for unit_id in missing_units[:5])
            return f"Every diff unit must be covered exactly once. Missing units include {missing_preview}."

        unit_map = {unit.unit_id: unit for unit in self.change_units}
        for chunk in submission.chunks:
            chunk_file_paths = {
                unit_map[unit_id].file_path
                for unit_id in chunk.selected_unit_ids
                if unit_id in unit_map
            }
            review_error = self._validate_chunk_review(chunk=chunk, chunk_file_paths=chunk_file_paths)
            if review_error:
                return review_error
        return None

    def _build_split_grading_payload(
        self,
        *,
        evaluation_result: EvaluationResult,
        split_data: Dict[str, object],
        custom_metrics: Optional[Dict[str, float]],
    ) -> Dict[str, object]:
        return {
            "ground_truth_available": False,
            "rubric": {
                "primary_metric": "structural_validity",
                "components": [
                    "coverage_rate",
                    "overlap_rate",
                    "dependency_acyclic",
                    "chunk_review_valid_rate",
                ],
            },
            "grading": {
                "status": "structural_only",
                "score": evaluation_result.score,
                "summary": evaluation_result.message,
                "custom_metrics": custom_metrics,
                "split_data": split_data,
            },
        }

    async def _write_workspace_artifacts(
        self,
        *,
        submission: PRSplitSubmission,
        evaluation_result: EvaluationResult,
        split_data: Dict[str, object],
        custom_metrics: Optional[Dict[str, float]],
    ) -> Dict[str, str]:
        self._initialize_workspace_artifact_paths()
        if not self.scratch_submitted_split_path or not self.scratch_split_grading_path or not self.scratch_splits_dir:
            return {}
        self.scratch_splits_dir.mkdir(parents=True, exist_ok=True)
        await self._write_json_artifact(
            self.scratch_submitted_split_path,
            submission.model_dump(mode="json"),
        )
        await self._write_json_artifact(
            self.scratch_split_grading_path,
            self._build_split_grading_payload(
                evaluation_result=evaluation_result,
                split_data=split_data,
                custom_metrics=custom_metrics,
            ),
        )

        unit_map = {unit.unit_id: unit for unit in self.change_units}
        for chunk in submission.chunks:
            selected_units = [unit_map[unit_id] for unit_id in chunk.selected_unit_ids if unit_id in unit_map]
            chunk_diff_path = self.scratch_splits_dir / f"{chunk.chunk_id}.diff"
            chunk_diff_text = build_chunk_diff(selected_units)
            chunk_diff_path.write_text(chunk_diff_text, encoding="utf-8")
        return self._workspace_artifact_relpaths()

    async def register_task_tools(self, mcp) -> None:
        from pydantic import Field

        @mcp.tool(
            description=(
                "Submit your final PR split decision.\n\n"
                f"Mirror the exact field names and nesting from `{self._split_submission_schema_relpath()}`.\n"
                f"A filled example lives at `{self._split_submission_example_relpath()}`.\n"
                "If `should_split` is `false`, provide a non-empty rationale and `chunks=[]`.\n"
                "If `should_split` is `true`, provide 2-6 chunks that cover every diff unit exactly once.\n"
                f"Use only unit IDs from `{self._pr_change_units_relpath()}`.\n"
                "Every chunk must include a standalone review with structured evidence-backed findings.\n"
                f"After a successful `submit_result`, the task writes the final split plan to `{self._submitted_split_relpath()}`.\n"
                f"It also writes structural grading details to `{self._split_grading_relpath()}` and chunk diffs to `{self._split_dir_relpath()}`.\n"
            )
        )
        async def submit_result(
            should_split: Annotated[bool, Field(description="Whether the PR should be split into smaller sub-PRs")],
            rationale: Annotated[str, Field(description="High-level rationale for the split or no-split decision")],
            chunks: Annotated[List[PRSplitChunk], Field(
                description="Proposed sub-PRs with chunk IDs, selected unit IDs, dependencies, and standalone reviews."
            )],
        ) -> Dict[str, Any]:
            self.logger.info("Tool submit_result: execution started")
            try:
                submission = PRSplitSubmission(
                    should_split=should_split,
                    rationale=rationale,
                    chunks=chunks,
                )
                blocked_reason = self._validate_submission_prerequisites(submission)
                if blocked_reason:
                    self.logger.info("Tool submit_result: rejected by task prerequisites")
                    return {
                        "evaluation_result": EvaluationResult(success=False, score=0.0, message=blocked_reason),
                        "message": blocked_reason,
                    }

                evaluation_result, split_data, custom_metrics = evaluate_split_submission(
                    submission=submission,
                    all_unit_ids=[unit.unit_id for unit in self.change_units],
                )
                workspace_artifacts: Dict[str, str] = {}
                try:
                    workspace_artifacts = await self._write_workspace_artifacts(
                        submission=submission,
                        evaluation_result=evaluation_result,
                        split_data=split_data,
                        custom_metrics=custom_metrics,
                    )
                except Exception:
                    self.logger.error("Failed to write PR split workspace artifacts: %s", traceback.format_exc())

                if self.should_terminate(evaluation_result) and self.termination_callback:
                    task_result = self.create_result(
                        success=True,
                        score=evaluation_result.score,
                        should_split=submission.should_split,
                        rationale=submission.rationale,
                        chunks=submission.chunks,
                        split_data=split_data,
                        workspace_artifacts=workspace_artifacts,
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
                    "split_data": split_data,
                    "workspace_artifacts": workspace_artifacts,
                    "message": "PR split plan submitted and validated",
                }
            except Exception:
                self.logger.error("PR split evaluation failed: %s", traceback.format_exc())
                return {
                    "evaluation_result": EvaluationResult(
                        success=False,
                        score=0.0,
                        message=traceback.format_exc(),
                    ),
                    "message": "Evaluation failed or not ready",
                }

    def create_result(
        self,
        success: bool,
        score: float,
        should_split: bool,
        rationale: str,
        chunks: List[PRSplitChunk],
        split_data: Dict[str, object],
        workspace_artifacts: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> PRSplitResult:
        return PRSplitResult(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=success,
            score=score,
            should_split=should_split,
            rationale=rationale,
            chunks=chunks,
            split_data=split_data,
            workspace_artifacts=workspace_artifacts or {},
            **kwargs,
        )

    def should_terminate(self, evaluation_result: EvaluationResult = None) -> bool:
        return bool(evaluation_result and evaluation_result.success)


class SkilledPRSplitConfig(PRSplitConfig):
    """Configuration for skill-targeted standalone PR split tasks."""

    required_skill_name: str = "mathlib-pr-split"
    require_read_skill_before_submit: bool = True
    required_bootstrap_paths: List[str] = Field(
        default_factory=lambda: list(DEFAULT_SKILLED_SPLIT_BOOTSTRAP_PATHS)
    )


class SkilledPRSplitTask(PRSplitTask):
    """Skill-targeted standalone PR split task implementation."""

    task_type = "skilled_pr_split"
    data_class = SkilledPRSplitData
    task_config_class = SkilledPRSplitConfig
    task_result_class = PRSplitResult

    def _build_managed_skill_guidance(self) -> str:
        required_skill_name = self._get_required_skill_name()
        relevant_skills = self._get_relevant_managed_skills()
        bootstrap_paths = list(getattr(self.config.task_config, "required_bootstrap_paths", None) or [])
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
            "This is the skill-targeted PR split task variant.\n"
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
        task_config: SkilledPRSplitConfig = self.config.task_config
        required_skill_name = self._get_required_skill_name()
        relevant_skills = self._get_relevant_managed_skills()
        if not relevant_skills:
            return (
                f"This `skilled_pr_split` run requires the managed `{required_skill_name}` skill, "
                "but no relevant skill was materialized. Re-run with skills enabled."
            )

        usage = self._get_skill_tool_usage()
        if task_config.require_read_skill_before_submit and usage["read_skill"] < 1:
            return (
                "This `skilled_pr_split` variant requires consulting the managed Mathlib split "
                f"skill before submission. Call `list_skills`, then `read_skill` on `{required_skill_name}`, "
                "and continue the split analysis."
            )

        required_bootstrap_paths = list(task_config.required_bootstrap_paths or [])
        read_paths = set(self._get_skill_read_relative_paths())
        read_paths.discard("SKILL.md")
        missing_bootstrap_paths = [path for path in required_bootstrap_paths if path not in read_paths]
        if missing_bootstrap_paths:
            return (
                "`submit_result` is final-only for `skilled_pr_split`. Finish the skill bootstrap first by "
                "reading these required files with `read_skill`: "
                + ", ".join(f"`{path}`" for path in missing_bootstrap_paths)
                + "."
            )
        return super()._validate_submission_prerequisites(submission)


register_task("lean_pr_split", PRSplitTask)
register_task("skilled_pr_split", SkilledPRSplitTask)
