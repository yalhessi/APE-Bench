"""
Lean PR review task.

Evaluates whether an agent can provide Mathlib-quality pull request review feedback,
including merge readiness and issue identification.
"""

from typing import Annotated, Dict, Any, Optional, List, TYPE_CHECKING, Literal, Set, Tuple, cast
import asyncio
import hashlib
import inspect
import json
import os
import re
import shutil
import traceback
from pathlib import Path, PurePosixPath
from pydantic import Field

from ape.tasks.base import BaseTaskResult, EvaluationResult
from ape.tasks.lean_tasks.base import BaseLeanTask
from ape.tasks.models import WorkspaceInfo
from ape.toolkits.execute.lean.utils.process_ops import run_command
from .findings import (
    ReviewDeclarationReference,
    ReviewDiffLocation,
    ReviewFinding,
    ReviewFindingEvidence,
    ReviewGuideCitation,
    coerce_review_findings,
    extract_review_categories,
    normalize_review_category,
)
from .models import (
    PRReviewSubmission,
    ReviewPRData,
    ReviewPRResult,
)
from .scoring import evaluate_review_submission

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


HeadWorkspaceFastPathMode = Literal["off", "reuse_only", "cache_probe", "full_build"]


class ReviewPRCoreTask(BaseLeanTask):
    """Lean PR review task implementation."""

    patch_marker_filename = ".ape_pr_review_patch.json"
    review_submission_schema_filename = "review_submission_schema.json"
    review_submission_example_filename = "review_submission_example.json"
    submitted_review_filename = "submitted_review.json"
    review_grading_filename = "review_grading.json"

    @classmethod
    def _review_submission_schema_relpath(cls) -> str:
        return f"scratch/{cls.review_submission_schema_filename}"

    @classmethod
    def _review_submission_example_relpath(cls) -> str:
        return f"scratch/{cls.review_submission_example_filename}"

    @classmethod
    def _submitted_review_relpath(cls) -> str:
        return f"scratch/{cls.submitted_review_filename}"

    @classmethod
    def _review_grading_relpath(cls) -> str:
        return f"scratch/{cls.review_grading_filename}"

    def _build_managed_skill_guidance(self) -> str:
        """Return generic prompt guidance about managed skills."""
        managed_skill_name = self._get_managed_skill_name()
        if not managed_skill_name:
            return ""

        relevant_skills = self._get_relevant_managed_skills()
        if not relevant_skills:
            return (
                "<managed_skill_guidance>\n"
                f"This task variant enables the managed `{managed_skill_name}` skill.\n"
                "No matching managed skill was materialized for this run, so the configuration is invalid.\n"
                "</managed_skill_guidance>\n"
            )

        skill_list = "\n".join(
            f"- `{skill.name}` (`{skill.skill_id}`): {skill.description}"
            for skill in relevant_skills
        )
        guidance_lines = [
            "<managed_skill_guidance>",
            f"This task variant enables the managed `{managed_skill_name}` skill.",
            "Use `list_skills` to inspect the available managed skills and `read_skill` to consult the relevant one during the review.",
        ]
        if self._force_skill_use():
            guidance_lines.append(
                "You must call `read_skill` on that managed skill before submitting your final review."
            )
        guidance_lines.extend(
            [
                "Relevant skill(s):",
                skill_list,
                "</managed_skill_guidance>",
            ]
        )
        return "\n".join(guidance_lines) + "\n"

    def _build_submission_contract_guidance(self) -> str:
        schema_path = self._review_submission_schema_relpath()
        example_path = self._review_submission_example_relpath()
        submitted_review_path = self._submitted_review_relpath()
        review_grading_path = self._review_grading_relpath()
        return (
            f"Mirror the exact field names and nesting from `{schema_path}`.\n"
            f"A filled example lives at `{example_path}`.\n"
            "Each finding must include at least one code-local evidence anchor via "
            "`diff_locations`, `referenced_files`, or `referenced_declarations`; guide citations alone are not enough.\n"
            "Use repo-root paths in `diff_locations.file_path`; never use `scratch/pr.diff` there.\n"
            "Every `diff_locations.file_path` must point to a changed file from this PR.\n"
            "`diff_side` must be `old` or `new`.\n"
            "`referenced_declarations` entries must be objects with `name`, not raw strings.\n"
            "`guide_citations` entries must use `topic` and `relative_path`.\n"
            "Do not invent alternate keys like `path`, `file`, `declaration`, `title`, `quote`, or `comment`.\n"
            f"After a successful `submit_result`, the task writes your final review to `{submitted_review_path}`.\n"
            f"It also writes grading details to `{review_grading_path}`; if ground truth is attached, "
            "that file explains how the review was graded.\n"
        )

    def _build_submit_tool_description(self) -> str:
        """Return the task-specific description for `submit_result`."""
        return (
            "Submit your final PR review decision.\n\n"
            f"{self._build_submission_contract_guidance()}\n"
            "Provide:\n"
            "- merge_ready: whether the PR is ready to merge\n"
            "- needs_human_review: whether the PR should be escalated or handed off for human review\n"
            "- decision_confidence: optional calibrated confidence in the overall decision (0.0-1.0)\n"
            "- blocking_findings: blocking findings preventing merge\n"
            "- advisory_findings: non-blocking findings; use `[]` if you do not have a concrete advisory issue worth raising\n"
            "- evidence on every finding: diff_locations, referenced_files, referenced_declarations, and guide_citations\n"
            "- guide_evidence_topics: guide topics consulted to support policy/style judgments\n"
            "- feedback: concise, evidence-based reviewer feedback; a clean PR can legitimately have no extra suggestions\n\n"
            "You must call this tool to finish the task."
        )

    def _get_skill_read_relative_paths(self) -> tuple[str, ...]:
        """Return relevant managed-skill relative paths used for scoring context."""
        relevant_skill_ids = {skill.skill_id for skill in self._get_relevant_managed_skills()}
        if self._get_managed_skill_name() and not relevant_skill_ids:
            return ()

        ordered_paths: list[str] = []
        seen: set[str] = set()
        for skill_id, relative_path in self._get_skill_read_records():
            if relevant_skill_ids and skill_id not in relevant_skill_ids:
                continue
            if relative_path in seen:
                continue
            seen.add(relative_path)
            ordered_paths.append(relative_path)
        return tuple(ordered_paths)

    @staticmethod
    def _normalize_managed_skill_slug(skill_name: str) -> str:
        normalized = str(skill_name or "").strip().lower()
        normalized = re.sub(r"[\s_]+", "-", normalized)
        normalized = re.sub(r"-{2,}", "-", normalized)
        return normalized.strip("-")

    def _get_managed_skill_name(self) -> Optional[str]:
        task_config = getattr(self.config, "task_config", None)
        raw_value = getattr(task_config, "managed_skill_name", None)
        if not isinstance(raw_value, str):
            return None
        normalized = raw_value.strip()
        return normalized or None

    def _force_skill_use(self) -> bool:
        task_config = getattr(self.config, "task_config", None)
        return bool(getattr(task_config, "force_skill_use", False))

    def _get_relevant_managed_skills(self) -> tuple[Any, ...]:
        managed_skill_name = self._get_managed_skill_name()
        if not managed_skill_name:
            return ()

        from ape.scaffolds.skills import get_task_managed_skills

        managed_skills = get_task_managed_skills(self)
        if not managed_skills or not managed_skills.skills:
            return ()

        managed_skill_name_lower = managed_skill_name.lower()
        managed_skill_slug = self._normalize_managed_skill_slug(managed_skill_name)

        def is_match(skill: Any) -> bool:
            skill_name = str(getattr(skill, "name", "") or "").strip()
            skill_id = str(getattr(skill, "skill_id", "") or "").strip()
            if not skill_name or not skill_id:
                return False
            return (
                skill_name.lower() == managed_skill_name_lower
                or self._normalize_managed_skill_slug(skill_name) == managed_skill_slug
                or skill_id == managed_skill_slug
                or skill_id.startswith(f"{managed_skill_slug}-")
            )

        return tuple(skill for skill in managed_skills.skills if is_match(skill))

    def _get_skill_tool_usage(self) -> dict[str, int]:
        usage = getattr(self, "_managed_skill_tool_usage", None)
        if not isinstance(usage, dict):
            return {"list_skills": 0, "read_skill": 0}
        return {
            "list_skills": int(usage.get("list_skills", 0) or 0),
            "read_skill": int(usage.get("read_skill", 0) or 0),
        }

    def _get_skill_read_records(self) -> tuple[tuple[str, str], ...]:
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

    def _validate_managed_skill_prerequisites(self) -> Optional[str]:
        managed_skill_name = self._get_managed_skill_name()
        if not managed_skill_name:
            return None

        relevant_skills = self._get_relevant_managed_skills()
        if not relevant_skills:
            return (
                f"This `{self.task_type}` run requires the managed `{managed_skill_name}` skill, "
                "but no relevant skill was materialized. Re-run with skills enabled."
            )

        if not self._force_skill_use():
            return None

        relevant_skill_ids = {skill.skill_id for skill in relevant_skills}
        if any(skill_id in relevant_skill_ids for skill_id, _relative_path in self._get_skill_read_records()):
            return None

        return (
            f"This `{self.task_type}` variant requires consulting the managed `{managed_skill_name}` skill "
            "before submission. Call `list_skills`, then `read_skill` on "
            f"`{managed_skill_name}`, and continue the review."
        )

    @classmethod
    def _normalize_tool_trace_value(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            normalized = re.sub(r"\s+", " ", value).strip()
            if len(normalized) > 200:
                return f"{normalized[:197]}..."
            return normalized
        if isinstance(value, list):
            normalized_items: list[Any] = []
            for item in value[:8]:
                normalized_item = cls._normalize_tool_trace_value(item)
                if isinstance(normalized_item, (str, int, float, bool)):
                    normalized_items.append(normalized_item)
            return normalized_items
        return None

    def _record_tool_usage_trace(self, *, tool_name: str, **details: Any) -> None:
        usage = getattr(self, "_review_tool_usage_trace", None)
        if not isinstance(usage, dict):
            usage = {"counts": {}, "records": []}

        counts = usage.get("counts")
        if not isinstance(counts, dict):
            counts = {}
        counts[tool_name] = int(counts.get(tool_name, 0) or 0) + 1
        usage["counts"] = counts

        normalized_record = {"tool_name": tool_name}
        for key, value in details.items():
            normalized_value = self._normalize_tool_trace_value(value)
            if normalized_value is not None:
                normalized_record[key] = normalized_value

        records = usage.get("records")
        if not isinstance(records, list):
            records = []
        records.append(normalized_record)
        usage["records"] = records[-200:]

        setattr(self, "_review_tool_usage_trace", usage)

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

        if parts[0] == "scratch":
            return None
        if parts[0] == "target":
            if len(parts) <= 1:
                return None
            return "/".join(parts[1:])
        if parts[0] == "reference":
            if len(parts) <= 2:
                return None
            return "/".join(parts[2:])

        if any(part in ("", ".", "..") for part in parts):
            return None
        return normalized

    @classmethod
    def _invalid_repo_relative_path_reason(cls, path: str) -> Optional[str]:
        normalized = str(path or "").strip()
        if not normalized:
            return "path is empty"
        if normalized == "scratch/pr.diff":
            return "use the changed repo file path, not `scratch/pr.diff`"
        pure_path = PurePosixPath(normalized.replace("\\", "/"))
        if pure_path.is_absolute():
            return "path must be repo-root relative, not absolute"
        if pure_path.parts and pure_path.parts[0] in {"scratch", "target", "reference"}:
            return "path must be repo-root relative without a workspace prefix"
        if any(part in ("", ".", "..") for part in pure_path.parts):
            return "path contains unsafe segments"
        return None

    @classmethod
    def _finding_repo_evidence_paths(cls, finding: ReviewFinding) -> tuple[str, ...]:
        paths: list[str] = []
        seen: set[str] = set()

        def add_path(raw_path: Optional[str]) -> None:
            normalized_path = cls._normalize_repo_relative_path(raw_path or "")
            if not normalized_path or normalized_path in seen:
                return
            seen.add(normalized_path)
            paths.append(normalized_path)

        for diff_location in finding.evidence.diff_locations:
            add_path(diff_location.file_path)
        for file_path in finding.evidence.referenced_files:
            add_path(file_path)
        for declaration in finding.evidence.referenced_declarations:
            add_path(declaration.file_path)
        return tuple(paths)

    def _get_review_tool_trace_payload(self) -> Dict[str, Any]:
        usage = getattr(self, "_review_tool_usage_trace", None)
        if not isinstance(usage, dict):
            usage = {}

        raw_counts = usage.get("counts")
        counts = {
            str(tool_name): int(count or 0)
            for tool_name, count in (raw_counts.items() if isinstance(raw_counts, dict) else [])
        }

        raw_records = usage.get("records")
        records = list(raw_records) if isinstance(raw_records, list) else []

        inspected_workspace_paths: list[str] = []
        inspected_repo_paths: list[str] = []
        seen_workspace_paths: set[str] = set()
        seen_repo_paths: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                continue
            for field_name in ("file_path", "path", "directory_path"):
                raw_path = record.get(field_name)
                if not isinstance(raw_path, str):
                    continue
                normalized_workspace_path = raw_path.strip()
                if normalized_workspace_path and normalized_workspace_path not in seen_workspace_paths:
                    seen_workspace_paths.add(normalized_workspace_path)
                    inspected_workspace_paths.append(normalized_workspace_path)
                normalized_repo_path = self._normalize_repo_relative_path(normalized_workspace_path)
                if normalized_repo_path and normalized_repo_path not in seen_repo_paths:
                    seen_repo_paths.add(normalized_repo_path)
                    inspected_repo_paths.append(normalized_repo_path)

        tool_trace_summary = {
            "tool_call_counts": counts,
            "tool_call_total": sum(counts.values()),
            "records_captured": len(records),
            "inspected_workspace_paths": inspected_workspace_paths,
            "inspected_repo_paths": inspected_repo_paths,
            "used_file_inspection": any(
                counts.get(tool_name, 0) > 0 for tool_name in ("file_read", "content_search", "file_search")
            ),
            "used_code_navigation": any(
                counts.get(tool_name, 0) > 0 for tool_name in ("code_hover", "code_goto", "code_references")
            ),
            "used_bash_execute": counts.get("bash_execute", 0) > 0,
            "used_skill_tools": any(
                counts.get(tool_name, 0) > 0 for tool_name in ("list_skills", "read_skill")
            ),
            "read_scratch_diff": "scratch/pr.diff" in inspected_workspace_paths,
        }
        return {
            "summary": tool_trace_summary,
            "records": records,
        }

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
        """Return an error message when submit_result should be rejected."""
        blocked_reason = self._validate_managed_skill_prerequisites()
        if blocked_reason:
            return blocked_reason

        changed_files = list(self.data.changed_files or [])
        changed_file_set = set(changed_files)

        for finding_kind, findings in (
            ("Blocking", blocking_findings or []),
            ("Advisory", advisory_findings or []),
        ):
            for index, finding in enumerate(findings, start=1):
                finding_label = f"{finding_kind} finding {index} (`{finding.category}`)"
                if not finding.summary:
                    return f"{finding_label} must include a short summary."

                evidence = finding.evidence
                has_code_anchor = bool(
                    evidence.diff_locations
                    or evidence.referenced_files
                    or evidence.referenced_declarations
                )
                if not has_code_anchor:
                    return (
                        f"{finding_label} must include at least one code-local evidence anchor via "
                        "`diff_locations`, `referenced_files`, or `referenced_declarations`. "
                        "Guide citations alone are not enough."
                    )

                for diff_location in evidence.diff_locations:
                    invalid_reason = self._invalid_repo_relative_path_reason(diff_location.file_path)
                    if invalid_reason:
                        return (
                            f"{finding_label} has invalid `diff_locations.file_path` "
                            f"`{diff_location.file_path}`: {invalid_reason}."
                        )
                    if changed_file_set and diff_location.file_path not in changed_file_set:
                        changed_file_examples = ", ".join(f"`{path}`" for path in changed_files[:5])
                        return (
                            f"{finding_label} must use changed files for `diff_locations.file_path`. "
                            f"Got `{diff_location.file_path}`; changed files include {changed_file_examples}."
                        )

                for referenced_file in evidence.referenced_files:
                    invalid_reason = self._invalid_repo_relative_path_reason(referenced_file)
                    if invalid_reason:
                        return (
                            f"{finding_label} has invalid `referenced_files` entry "
                            f"`{referenced_file}`: {invalid_reason}."
                        )

                for declaration in evidence.referenced_declarations:
                    if declaration.file_path is None:
                        continue
                    invalid_reason = self._invalid_repo_relative_path_reason(declaration.file_path)
                    if invalid_reason:
                        return (
                            f"{finding_label} has invalid `referenced_declarations.file_path` "
                            f"`{declaration.file_path}`: {invalid_reason}."
                        )

        return None

    @classmethod
    def _patch_fingerprint(cls, data: ReviewPRData) -> str:
        digest = hashlib.sha256()
        digest.update((data.target_workspace.commit_hash or "").encode("utf-8"))
        digest.update(b"\0")
        digest.update((data.pr_diff or "").encode("utf-8"))
        return digest.hexdigest()

    @classmethod
    def _safe_overlay_path_parts(cls, rel_path: str) -> Tuple[str, ...]:
        normalized = rel_path.strip()
        if not normalized:
            return ()

        pure_path = PurePosixPath(normalized)
        if pure_path.is_absolute():
            raise RuntimeError(f"Refusing to materialize absolute patch path: {rel_path}")

        parts = pure_path.parts
        if any(part in ("", ".", "..") for part in parts):
            raise RuntimeError(f"Refusing to materialize unsafe patch path: {rel_path}")

        return tuple(parts)

    @staticmethod
    def _path_lexists(path: Path) -> bool:
        return os.path.lexists(path)

    @classmethod
    def _next_overlay_temp_path(cls, parent: Path, stem: str) -> Path:
        temp_path = parent / f".{stem}.pr_review_overlay"
        counter = 0
        while cls._path_lexists(temp_path):
            counter += 1
            temp_path = parent / f".{stem}.pr_review_overlay.{counter}"
        return temp_path

    @classmethod
    def _symlink_overlay_children(cls, base_root: Path, overlay_root: Path) -> None:
        for child in base_root.iterdir():
            (overlay_root / child.name).symlink_to(child)

    @classmethod
    def _collect_patch_touched_paths(cls, pr_diff: str, changed_files: List[str]) -> List[str]:
        touched_paths: List[str] = []
        seen: Set[str] = set()

        def add_path(candidate: str) -> None:
            normalized = candidate.strip()
            if not normalized or normalized == "/dev/null" or normalized in seen:
                return
            seen.add(normalized)
            touched_paths.append(normalized)

        for rel_path in changed_files:
            add_path(rel_path)

        for line in pr_diff.splitlines():
            if line.startswith("diff --git "):
                match = re.match(r"^diff --git a/(.+) b/(.+)$", line)
                if match:
                    add_path(match.group(1))
                    add_path(match.group(2))
                continue

            if line.startswith("--- ") or line.startswith("+++ "):
                header_path = line[4:].strip()
                if header_path.startswith(("a/", "b/")):
                    header_path = header_path[2:]
                add_path(header_path)

        return touched_paths

    @classmethod
    def _collect_patch_file_operations(cls, pr_diff: str) -> Tuple[List[str], List[Tuple[str, str]]]:
        deleted_paths: List[str] = []
        renamed_paths: List[Tuple[str, str]] = []
        seen_deleted: Set[str] = set()
        seen_renamed: Set[Tuple[str, str]] = set()

        current_old_path: Optional[str] = None
        rename_from: Optional[str] = None
        rename_to: Optional[str] = None
        deleted = False

        def finalize_current_file() -> None:
            if deleted and current_old_path and current_old_path != "/dev/null" and current_old_path not in seen_deleted:
                seen_deleted.add(current_old_path)
                deleted_paths.append(current_old_path)

            if rename_from and rename_to and rename_from != rename_to:
                rename_pair = (rename_from, rename_to)
                if rename_pair not in seen_renamed:
                    seen_renamed.add(rename_pair)
                    renamed_paths.append(rename_pair)

        for line in pr_diff.splitlines():
            if line.startswith("diff --git "):
                finalize_current_file()
                current_old_path = None
                rename_from = None
                rename_to = None
                deleted = False

                match = re.match(r"^diff --git a/(.+) b/(.+)$", line)
                if match:
                    current_old_path = match.group(1)
                continue

            if line.startswith("deleted file mode "):
                deleted = True
                continue

            if line.startswith("rename from "):
                rename_from = line[len("rename from ") :].strip()
                continue

            if line.startswith("rename to "):
                rename_to = line[len("rename to ") :].strip()
                continue

            if line.startswith("--- "):
                header_path = line[4:].strip()
                if header_path.startswith("a/"):
                    current_old_path = header_path[2:]
                elif header_path != "/dev/null":
                    current_old_path = header_path
                continue

            if line.startswith("+++ "):
                header_path = line[4:].strip()
                if header_path.startswith("b/") or header_path == "/dev/null":
                    continue

        finalize_current_file()
        return deleted_paths, renamed_paths

    @classmethod
    def _create_snapshot_overlay(cls, base_root: Path, overlay_root: Path) -> None:
        overlay_root.mkdir(parents=True, exist_ok=False)
        cls._make_path_user_writable(overlay_root)
        cls._symlink_overlay_children(base_root, overlay_root)

    @classmethod
    def _expand_overlay_directory(cls, base_dir: Path, overlay_dir: Path) -> None:
        if not base_dir.exists() or not base_dir.is_dir():
            raise RuntimeError(f"Cannot expand non-directory base path for overlay: {base_dir}")

        temp_dir = cls._next_overlay_temp_path(overlay_dir.parent, overlay_dir.name)
        temp_dir.mkdir()
        cls._make_path_user_writable(temp_dir)
        cls._symlink_overlay_children(base_dir, temp_dir)

        overlay_dir.unlink()
        os.replace(temp_dir, overlay_dir)
        cls._make_path_user_writable(overlay_dir)

    @classmethod
    def _materialize_overlay_path(
        cls,
        base_root: Path,
        overlay_root: Path,
        rel_path: str,
    ) -> None:
        parts = cls._safe_overlay_path_parts(rel_path)
        if not parts:
            return

        current_base = base_root
        current_overlay = overlay_root

        for part in parts[:-1]:
            next_base = current_base / part
            next_overlay = current_overlay / part

            if next_overlay.is_symlink():
                cls._expand_overlay_directory(next_base, next_overlay)
            elif cls._path_lexists(next_overlay):
                if not next_overlay.is_dir():
                    raise RuntimeError(
                        "PR patch path requires a directory, but overlay contains a non-directory: "
                        f"{next_overlay}"
                    )
                cls._make_path_user_writable(next_overlay)
            else:
                next_overlay.mkdir()
                cls._make_path_user_writable(next_overlay)

            current_base = next_base
            current_overlay = next_overlay

        leaf_name = parts[-1]
        leaf_base = current_base / leaf_name
        leaf_overlay = current_overlay / leaf_name

        cls._make_path_user_writable(current_overlay)

        if leaf_overlay.is_symlink():
            if leaf_base.is_dir():
                cls._expand_overlay_directory(leaf_base, leaf_overlay)
                return

            temp_path = cls._next_overlay_temp_path(leaf_overlay.parent, leaf_overlay.name)
            shutil.copy2(leaf_base, temp_path, follow_symlinks=True)
            leaf_overlay.unlink()
            os.replace(temp_path, leaf_overlay)
            cls._make_path_user_writable(leaf_overlay)
            return

        if cls._path_lexists(leaf_overlay):
            cls._make_path_user_writable(leaf_overlay)

    @classmethod
    def _apply_patch_file_operations(
        cls,
        workspace_path: Path,
        deleted_paths: List[str],
        renamed_paths: List[Tuple[str, str]],
    ) -> None:
        for rel_path in deleted_paths:
            parts = cls._safe_overlay_path_parts(rel_path)
            if not parts:
                continue

            delete_path = workspace_path.joinpath(*parts)
            if not cls._path_lexists(delete_path):
                continue

            cls._make_path_user_writable(delete_path.parent)
            if delete_path.is_dir() and not delete_path.is_symlink():
                shutil.rmtree(delete_path)
                continue

            cls._make_path_user_writable(delete_path)
            delete_path.unlink()

        for old_rel_path, new_rel_path in renamed_paths:
            old_parts = cls._safe_overlay_path_parts(old_rel_path)
            new_parts = cls._safe_overlay_path_parts(new_rel_path)
            if not old_parts or not new_parts:
                continue

            old_path = workspace_path.joinpath(*old_parts)
            new_path = workspace_path.joinpath(*new_parts)
            if not cls._path_lexists(old_path):
                continue

            new_path.parent.mkdir(parents=True, exist_ok=True)
            cls._make_path_user_writable(new_path.parent)

            if cls._path_lexists(new_path):
                if new_path.is_dir() and not new_path.is_symlink():
                    shutil.rmtree(new_path)
                else:
                    new_path.unlink()

            os.replace(old_path, new_path)
            cls._make_path_user_writable(new_path)

    @staticmethod
    def _make_path_user_writable(path: Path) -> None:
        if path.is_symlink():
            return
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
    def _head_workspace_fast_path_mode(cls, config: "BaseScaffoldConfig") -> HeadWorkspaceFastPathMode:
        task_config = getattr(config, "task_config", None)
        raw_mode = getattr(task_config, "head_workspace_fast_path_mode", None)
        if isinstance(raw_mode, str):
            normalized_mode = raw_mode.strip().lower()
            if normalized_mode in {"off", "reuse_only", "cache_probe", "full_build"}:
                return cast(HeadWorkspaceFastPathMode, normalized_mode)

        legacy_enabled = getattr(task_config, "enable_head_cache_fast_path", None)
        if legacy_enabled is not None:
            return "cache_probe" if bool(legacy_enabled) else "off"

        return "cache_probe"

    @classmethod
    def _get_pr_head_metadata(cls, data: ReviewPRData) -> Optional[Dict[str, Any]]:
        pr_head = data.pr_head
        if pr_head is None:
            return None
        return pr_head.model_dump(mode="json")

    @classmethod
    def _build_head_workspace_spec(cls, data: ReviewPRData) -> Optional[WorkspaceInfo]:
        head_commit_hash = str(data.snapshot_head_sha or "").strip()
        if not head_commit_hash:
            return None

        head_metadata = cls._get_pr_head_metadata(data) or {}
        default_target = head_metadata.get("default_target") or data.target_workspace.default_target
        toolchain = head_metadata.get("toolchain") or data.target_workspace.toolchain

        return data.target_workspace.model_copy(
            update={
                "commit_hash": head_commit_hash,
                "default_target": default_target,
                "toolchain": toolchain,
            }
        )

    @staticmethod
    def _lean_file_path_to_module_name(file_path: str) -> Optional[str]:
        if not file_path.endswith(".lean"):
            return None

        module_path = PurePosixPath(file_path)
        if not module_path.parts:
            return None

        return ".".join(module_path.with_suffix("").parts)

    @classmethod
    def _head_workspace_verify_targets(cls, data: ReviewPRData, default_target: str) -> List[str]:
        seen: set[str] = set()
        verify_targets: List[str] = []
        for rel_path in data.changed_files:
            module_name = cls._lean_file_path_to_module_name(rel_path)
            if not module_name or module_name in seen:
                continue
            seen.add(module_name)
            verify_targets.append(module_name)

        if verify_targets:
            return verify_targets

        fallback_target = str(default_target or "Mathlib").strip() or "Mathlib"
        return [fallback_target]

    @classmethod
    def _format_head_fast_path_reason(cls, reason: object) -> str:
        text = str(reason).strip()
        if not text and isinstance(reason, BaseException):
            text = reason.__class__.__name__
        text = re.sub(r"\s+", " ", text)
        if len(text) > 220:
            text = f"{text[:217].rstrip()}..."
        return text or "unknown reason"

    @classmethod
    async def _emit_head_fast_path_fallback(
        cls,
        data: ReviewPRData,
        reason: object,
        *,
        logger: Optional["logging.LoggerAdapter"] = None,
        progress_callback=None,
    ) -> None:
        formatted_reason = cls._format_head_fast_path_reason(reason)
        if logger:
            logger.info(
                "PR-head workspace fast path fell back to base patching for %s: %s",
                data.task_id,
                formatted_reason,
            )
        await cls._emit_progress(
            progress_callback,
            f"PR-head fast path fell back to base snapshot patching: {formatted_reason}",
        )

    @classmethod
    async def _link_resolved_workspace(
        cls,
        workspace_spec: WorkspaceInfo,
        actual_workspace_path: Path,
        link_path: Path,
        logger: Optional["logging.LoggerAdapter"] = None,
    ) -> WorkspaceInfo:
        if link_path.exists() and link_path.is_dir() and not link_path.is_symlink():
            if logger:
                logger.info(
                    "Workspace %s already exists as directory at %s, using existing",
                    workspace_spec.name,
                    link_path,
                )
            read_only_patterns = workspace_spec.read_only_path_patterns or ["**/*"]
            return workspace_spec.model_copy(
                update={
                    "path": link_path,
                    "read_only_path_patterns": read_only_patterns,
                }
            )

        if link_path.is_symlink():
            link_path.unlink()
        elif link_path.exists():
            link_path.unlink()

        link_path.symlink_to(actual_workspace_path, target_is_directory=True)
        read_only_patterns = workspace_spec.read_only_path_patterns or ["**/*"]
        return workspace_spec.model_copy(
            update={
                "path": link_path,
                "read_only_path_patterns": read_only_patterns,
            }
        )

    @classmethod
    async def _maybe_resolve_cached_workspace(
        cls,
        workspace_spec: WorkspaceInfo,
        *,
        logger: Optional["logging.LoggerAdapter"] = None,
        progress_callback=None,
    ) -> Optional[Path]:
        if not workspace_spec.commit_hash:
            return None

        try:
            from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
            from ape.toolkits.execute.lean.core.restore_manager import RestoreManager

            verify_config = LeanVerifyToolConfig()
            repo_name, resolved_url = verify_config.resolve_repo(workspace_spec.repo_url)
            restore_manager = RestoreManager(
                verify_config,
                logger,
                resolved_url,
                progress_callback=progress_callback,
            )

            if await restore_manager._requires_build_first(workspace_spec.commit_hash):
                if logger:
                    logger.info(
                        "No local compiled workspace is available yet for %s@%s",
                        repo_name,
                        workspace_spec.commit_hash,
                    )
                return None

            if logger:
                logger.info(
                    "Attempting to reuse compiled workspace for %s@%s",
                    repo_name,
                    workspace_spec.commit_hash,
                )
            return await restore_manager.get_workspace(workspace_spec.commit_hash)

        except Exception as exc:
            if logger:
                logger.info(
                    "Unable to reuse compiled workspace for %s@%s: %s",
                    workspace_spec.name,
                    workspace_spec.commit_hash,
                    exc,
                )
            return None

    @classmethod
    async def _maybe_setup_head_target_workspace(
        cls,
        data: ReviewPRData,
        config: "BaseScaffoldConfig",
        target_link_path: Path,
        *,
        logger: Optional["logging.LoggerAdapter"] = None,
        progress_callback=None,
    ) -> Optional[WorkspaceInfo]:
        fast_path_mode = cls._head_workspace_fast_path_mode(config)
        if fast_path_mode == "off":
            return None

        head_workspace_spec = cls._build_head_workspace_spec(data)
        if head_workspace_spec is None or not head_workspace_spec.commit_hash:
            return None

        await cls._emit_progress(
            progress_callback,
            f"Trying a PR-head workspace fast path for {head_workspace_spec.name}@{head_workspace_spec.commit_hash[:8]}...",
        )

        cached_workspace_path = await cls._maybe_resolve_cached_workspace(
            head_workspace_spec,
            logger=logger,
            progress_callback=progress_callback,
        )
        if cached_workspace_path is not None:
            if logger:
                logger.info(
                    "Using existing compiled PR-head workspace for %s@%s",
                    head_workspace_spec.name,
                    head_workspace_spec.commit_hash,
                )
            await cls._emit_progress(
                progress_callback,
                f"Using a compiled PR-head workspace for commit {head_workspace_spec.commit_hash[:8]}...",
            )
            return await cls._link_resolved_workspace(
                head_workspace_spec,
                cached_workspace_path,
                target_link_path,
                logger=logger,
            )

        if fast_path_mode == "reuse_only":
            await cls._emit_head_fast_path_fallback(
                data,
                "local reuse is enabled, but no compiled PR-head workspace is available yet",
                logger=logger,
                progress_callback=progress_callback,
            )
            return None

        head_metadata = cls._get_pr_head_metadata(data)
        if not head_metadata:
            await cls._emit_head_fast_path_fallback(
                data,
                "PR-head metadata is unavailable",
                logger=logger,
                progress_callback=progress_callback,
            )
            return None

        fetch_repo_url = str(head_metadata.get("clone_url") or "").strip()
        fetch_ref = str(head_metadata.get("ref") or "").strip()
        if not fetch_repo_url or not fetch_ref:
            await cls._emit_head_fast_path_fallback(
                data,
                "PR-head clone_url/ref metadata is incomplete",
                logger=logger,
                progress_callback=progress_callback,
            )
            return None

        try:
            from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
            from ape.toolkits.execute.lean.core.build_manager import BuildManager

            verify_targets = cls._head_workspace_verify_targets(data, head_workspace_spec.default_target)
            verify_config = LeanVerifyToolConfig()
            build_manager = BuildManager(
                verify_config,
                logger,
                head_workspace_spec.repo_url,
            )
            cache_repo_full_name = str(head_metadata.get("repo_full_name") or "").strip() or None
            if fast_path_mode == "full_build":
                await cls._emit_progress(
                    progress_callback,
                    "Attempting a full PR-head workspace build from cache metadata...",
                )
                await build_manager.build_workspace_from_ref(
                    head_workspace_spec.commit_hash,
                    fetch_repo_url=fetch_repo_url,
                    fetch_ref=fetch_ref,
                    cache_repo_full_name=cache_repo_full_name,
                )
            else:
                await cls._emit_progress(
                    progress_callback,
                    "Attempting a bounded cache-only PR-head workspace probe...",
                )
                await build_manager.prepare_workspace_from_ref_with_cache_probe(
                    head_workspace_spec.commit_hash,
                    fetch_repo_url=fetch_repo_url,
                    fetch_ref=fetch_ref,
                    cache_repo_full_name=cache_repo_full_name,
                    verify_targets=verify_targets,
                    progress_callback=progress_callback,
                )
            resolved_head_workspace_path = await cls._resolve_lean_workspace(
                commit_hash=head_workspace_spec.commit_hash,
                repo_url=head_workspace_spec.repo_url,
                config=config,
                logger=logger,
                progress_callback=progress_callback,
            )
            await cls._emit_progress(
                progress_callback,
                f"Prepared a compiled PR-head workspace for commit {head_workspace_spec.commit_hash[:8]}...",
            )
            return await cls._link_resolved_workspace(
                head_workspace_spec,
                resolved_head_workspace_path,
                target_link_path,
                logger=logger,
            )
        except Exception as exc:
            await cls._emit_head_fast_path_fallback(
                data,
                exc,
                logger=logger,
                progress_callback=progress_callback,
            )
            return None

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

        deleted_paths, renamed_paths = cls._collect_patch_file_operations(pr_diff)
        if deleted_paths or renamed_paths:
            await asyncio.to_thread(
                cls._apply_patch_file_operations,
                workspace_path,
                deleted_paths,
                renamed_paths,
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
        base_workspace_path: Optional[Path] = None
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
                    "Creating lazy overlay PR review workspace from base snapshot: %s -> %s",
                    base_workspace_path,
                    target_path,
                )
            await cls._emit_progress(
                progress_callback,
                "Creating a lazy overlay PR review workspace from the cached Lean snapshot...",
            )
            await asyncio.to_thread(
                cls._create_snapshot_overlay,
                base_workspace_path,
                target_path,
            )
        elif existing_fingerprint and existing_fingerprint != patch_fingerprint:
            raise RuntimeError(
                "PR review workspace already contains a different applied patch. "
                f"workspace={target_path}"
            )

        await asyncio.to_thread(cls._make_path_user_writable, target_path)
        touched_paths = cls._collect_patch_touched_paths(data.pr_diff, data.changed_files)
        await cls._emit_progress(
            progress_callback,
            "Materializing only the changed paths so the PR patch can be applied cleanly...",
        )
        if touched_paths:
            if base_workspace_path is None:
                raise RuntimeError(
                    "Unable to determine the immutable base snapshot for the PR review overlay. "
                    f"workspace={target_path}"
                )
            for rel_path in touched_paths:
                await asyncio.to_thread(
                    cls._materialize_overlay_path,
                    base_workspace_path,
                    target_path,
                    rel_path,
                )
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
        attempt_path, scratch_workspace, _, _ = await super(BaseLeanTask, cls).setup_attempt(
            data=data,
            config=config,
            orchestrator_id=orchestrator_id,
            attempt_path=attempt_path,
            logger=logger,
            progress_callback=progress_callback,
        )

        workspaces_dir = attempt_path / config.workspaces_dir_name
        target_workspace: Optional[WorkspaceInfo] = None

        if data.target_workspace:
            try:
                target_workspace = await cls._maybe_setup_head_target_workspace(
                    data=data,
                    config=config,
                    target_link_path=workspaces_dir / "target",
                    logger=logger,
                    progress_callback=progress_callback,
                )
            except Exception:
                if logger:
                    logger.error(
                        "Failed during PR-head workspace fast path: %s",
                        traceback.format_exc(),
                    )
                target_workspace = None

            if target_workspace is None:
                await cls._emit_progress(
                    progress_callback,
                    f"Resolving target Lean workspace {data.target_workspace.name}@{data.target_workspace.commit_hash[:8]}...",
                )
                target_workspace = await cls._setup_workspace_symlink(
                    workspace_spec=data.target_workspace,
                    link_path=workspaces_dir / "target",
                    config=config,
                    logger=logger,
                    progress_callback=progress_callback,
                )

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

        reference_workspaces = None
        if data.reference_workspaces:
            reference_workspaces = []
            ref_base_dir = workspaces_dir / "reference"
            ref_base_dir.mkdir(parents=True, exist_ok=True)

            for ref_ws in data.reference_workspaces:
                await cls._emit_progress(
                    progress_callback,
                    f"Resolving reference Lean workspace {ref_ws.name}@{ref_ws.commit_hash[:8]}...",
                )
                linked_ref = await cls._setup_workspace_symlink(
                    workspace_spec=ref_ws,
                    link_path=ref_base_dir / ref_ws.name,
                    config=config,
                    logger=logger,
                    progress_callback=progress_callback,
                )
                reference_workspaces.append(linked_ref)

        return attempt_path, scratch_workspace, target_workspace, reference_workspaces

    def __init__(self, data: ReviewPRData, config: "BaseScaffoldConfig"):
        super().__init__(data, config)
        self.scratch_pr_diff_path: Optional[Path] = None
        self.scratch_pr_context_path: Optional[Path] = None
        self.scratch_review_submission_schema_path: Optional[Path] = None
        self.scratch_review_submission_example_path: Optional[Path] = None
        self.scratch_submitted_review_path: Optional[Path] = None
        self.scratch_review_grading_path: Optional[Path] = None
        self._review_tool_usage_trace: Dict[str, Any] = {"counts": {}, "records": []}

    @staticmethod
    def _normalize_finding_category(category: str) -> str:
        return normalize_review_category(category)

    def _normalize_findings(self, findings: Optional[List[ReviewFinding]]) -> List[ReviewFinding]:
        return coerce_review_findings(findings or [])

    def _extract_finding_categories(self, findings: Optional[List[ReviewFinding]]) -> List[str]:
        return extract_review_categories(findings or [])

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

    @staticmethod
    def _example_declaration_name(file_path: str) -> str:
        normalized_path = str(file_path or "").strip()
        if normalized_path.endswith(".lean"):
            module_name = ".".join(PurePosixPath(normalized_path).with_suffix("").parts)
            if module_name:
                return f"{module_name}.example"
        return "Example.declaration"

    def _build_submission_schema_payload(self) -> dict[str, Any]:
        template = PRReviewSubmission(
            merge_ready=False,
            needs_human_review=False,
            decision_confidence=None,
            blocking_findings=[],
            advisory_findings=[],
            guide_evidence_topics=[],
            feedback="Replace this placeholder with concise, evidence-based reviewer feedback.",
        )
        return template.model_dump(mode="json")

    def _build_submission_example_payload(self) -> dict[str, Any]:
        changed_files = list(self.data.snapshot.changed_files or [])
        example_file_path = next(
            (str(path).strip() for path in changed_files if str(path).strip()),
            "Mathlib/Example.lean",
        )
        example_declaration_name = self._example_declaration_name(example_file_path)

        example = PRReviewSubmission(
            merge_ready=False,
            needs_human_review=False,
            decision_confidence=0.78,
            blocking_findings=[
                ReviewFinding(
                    category="integration_compatibility",
                    summary=(
                        "This change introduces a new dependency pattern that should be checked "
                        "against Mathlib library-integration expectations before merging."
                    ),
                    evidence=ReviewFindingEvidence(
                        diff_locations=[
                            ReviewDiffLocation(
                                file_path=example_file_path,
                                line_start=1,
                                line_end=8,
                                diff_side="new",
                            )
                        ],
                        referenced_files=[example_file_path],
                        referenced_declarations=[
                            ReviewDeclarationReference(
                                name=example_declaration_name,
                                file_path=example_file_path,
                                line_start=1,
                                line_end=12,
                            )
                        ],
                        guide_citations=[
                            ReviewGuideCitation(
                                topic="style",
                                relative_path="references/style-guidelines-reviewer.md",
                            )
                        ],
                    ),
                )
            ],
            advisory_findings=[
                ReviewFinding(
                    category="documentation_metadata",
                    summary="The PR description should explain the motivation and tradeoffs more clearly.",
                    evidence=ReviewFindingEvidence(
                        diff_locations=[],
                        referenced_files=[],
                        referenced_declarations=[],
                        guide_citations=[
                            ReviewGuideCitation(
                                topic="pr_metadata",
                                relative_path="references/commit-conventions-reviewer.md",
                            )
                        ],
                    ),
                )
            ],
            guide_evidence_topics=["style", "pr_metadata"],
            feedback=(
                "Not merge ready yet. The change needs a clearer library-integration justification, "
                "and the PR metadata should explain the intent more explicitly."
            ),
        )
        return example.model_dump(mode="json")

    def _initialize_workspace_artifact_paths(self) -> None:
        if not self.scratch_workspace or not self.scratch_workspace.path:
            return

        self.scratch_submitted_review_path = self.scratch_workspace.path / self.submitted_review_filename
        self.scratch_review_grading_path = self.scratch_workspace.path / self.review_grading_filename

    def _workspace_artifact_relpaths(self) -> Dict[str, str]:
        return {
            "submitted_review": self._submitted_review_relpath(),
            "review_grading": self._review_grading_relpath(),
        }

    def _build_grading_rubric_payload(self) -> dict[str, Any]:
        task_config = self.config.task_config
        return {
            "primary_metric": "review_quality_score",
            "components": [
                {
                    "metric": "decision_accuracy",
                    "weight": float(getattr(task_config, "decision_weight", 0.65)),
                    "description": "1.0 when `merge_ready` matches ground truth; otherwise 0.0.",
                },
                {
                    "metric": "blocking_issue_f1",
                    "weight": float(getattr(task_config, "blocking_issue_weight", 0.25)),
                    "description": "F1 over predicted vs ground-truth blocking finding categories.",
                },
                {
                    "metric": "advisory_issue_f1",
                    "weight": float(getattr(task_config, "advisory_issue_weight", 0.10)),
                    "description": "F1 over predicted vs ground-truth advisory finding categories.",
                },
            ],
            "weights": {
                "decision_accuracy": float(getattr(task_config, "decision_weight", 0.65)),
                "blocking_issue_f1": float(getattr(task_config, "blocking_issue_weight", 0.25)),
                "advisory_issue_f1": float(getattr(task_config, "advisory_issue_weight", 0.10)),
            },
            "false_approve_penalty": {
                "max_score": float(getattr(task_config, "severe_false_approve_max_score", 0.20)),
                "description": (
                    "If the review approves a PR that ground truth rejects, cap the final score at this value."
                ),
            },
            "supplementary_metrics": [
                "handoff_accuracy",
                "location_file_precision",
                "location_file_recall",
                "location_file_f1",
                "evidence_code_anchor_rate",
                "evidence_path_anchor_rate",
                "guide_citation_rate",
                "evidence_trace_coverage_rate",
                "decision_confidence_provided",
                "decision_brier_score",
                "decision_calibration_error",
                "selective_coverage",
                "selective_decision_risk",
            ],
        }

    def _build_review_grading_payload(
        self,
        *,
        evaluation_result: EvaluationResult,
        review_data: Dict[str, Any],
        custom_metrics: Optional[Dict[str, float]],
    ) -> dict[str, Any]:
        return {
            "ground_truth_available": self.data.evaluation is not None,
            "label_source": self.data.label_source,
            "rubric": self._build_grading_rubric_payload(),
            "grading": {
                "status": "graded" if self.data.evaluation is not None else "unscored",
                "score": evaluation_result.score,
                "summary": evaluation_result.message,
                "custom_metrics": custom_metrics,
                "review_data": review_data,
            },
        }

    @staticmethod
    async def _write_json_artifact(path: Path, payload: Dict[str, Any]) -> None:
        import aiofiles

        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(payload, indent=2, ensure_ascii=False))
            await f.write("\n")

    async def _write_workspace_artifacts(
        self,
        *,
        submission: PRReviewSubmission,
        evaluation_result: EvaluationResult,
        review_data: Dict[str, Any],
        custom_metrics: Optional[Dict[str, float]],
    ) -> Dict[str, str]:
        self._initialize_workspace_artifact_paths()
        if not self.scratch_submitted_review_path or not self.scratch_review_grading_path:
            return {}

        await self._write_json_artifact(
            self.scratch_submitted_review_path,
            submission.model_dump(mode="json"),
        )
        await self._write_json_artifact(
            self.scratch_review_grading_path,
            self._build_review_grading_payload(
                evaluation_result=evaluation_result,
                review_data=review_data,
                custom_metrics=custom_metrics,
            ),
        )
        return self._workspace_artifact_relpaths()

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

        snapshot = self.data.snapshot
        self.scratch_pr_diff_path = self.scratch_workspace.path / "pr.diff"
        self.scratch_pr_context_path = self.scratch_workspace.path / "pr_context.md"
        self.scratch_review_submission_schema_path = (
            self.scratch_workspace.path / self.review_submission_schema_filename
        )
        self.scratch_review_submission_example_path = (
            self.scratch_workspace.path / self.review_submission_example_filename
        )
        self._initialize_workspace_artifact_paths()

        context_lines = [
            f"# PR Review Context",
            f"",
            f"- PR number: {snapshot.pr_number if snapshot.pr_number is not None else 'N/A'}",
            f"- PR URL: {snapshot.pr_url or 'N/A'}",
            f"- Title: {snapshot.pr_title}",
            f"- Author: {snapshot.pr_author or 'unknown'}",
            f"- Snapshot type: {snapshot.snapshot_type or 'unknown'}",
            f"- Snapshot cutoff: {snapshot.snapshot_at or 'N/A'}",
            f"- Snapshot base SHA: {snapshot.snapshot_base_sha or 'N/A'}",
            f"- Snapshot head SHA: {snapshot.snapshot_head_sha or 'N/A'}",
            f"- Review state at snapshot: {snapshot.review_state or 'N/A'}",
            f"- Target workspace contents: PR patch already applied at this snapshot",
            f"",
            "## PR dependencies",
        ]
        if snapshot.pr_dependencies:
            context_lines.extend([f"- {dependency}" for dependency in snapshot.pr_dependencies])
        else:
            context_lines.append("- (none provided)")

        context_lines.extend([
            "",
            "## Changed files",
        ])
        if snapshot.changed_files:
            context_lines.extend([f"- {path}" for path in snapshot.changed_files])
        else:
            context_lines.append("- (not provided)")

        import aiofiles

        await self.emit_progress("Writing PR review context files into the scratch workspace...")
        async with aiofiles.open(self.scratch_pr_diff_path, "w", encoding="utf-8") as f:
            await f.write(snapshot.pr_diff or "")
        async with aiofiles.open(self.scratch_pr_context_path, "w", encoding="utf-8") as f:
            await f.write("\n".join(context_lines))
        async with aiofiles.open(self.scratch_review_submission_schema_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(self._build_submission_schema_payload(), indent=2, ensure_ascii=False))
            await f.write("\n")
        async with aiofiles.open(self.scratch_review_submission_example_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(self._build_submission_example_payload(), indent=2, ensure_ascii=False))
            await f.write("\n")

        self.scratch_workspace.read_only_path_patterns = [
            str(self.scratch_pr_diff_path.resolve()),
            str(self.scratch_pr_context_path.resolve()),
            str(self.scratch_review_submission_schema_path.resolve()),
            str(self.scratch_review_submission_example_path.resolve()),
        ]
        if self.scratch_submitted_review_path:
            self.scratch_workspace.read_only_path_patterns.append(
                str(self.scratch_submitted_review_path.resolve())
            )
        if self.scratch_review_grading_path:
            self.scratch_workspace.read_only_path_patterns.append(
                str(self.scratch_review_grading_path.resolve())
            )
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

        task_config = self.config.task_config
        snapshot = self.data.snapshot

        pr_display = f"#{snapshot.pr_number}" if snapshot.pr_number is not None else "N/A"
        if snapshot.pr_url:
            pr_display = f"{pr_display} ({snapshot.pr_url})"

        changed_files_list = (
            "\n".join(f"- `{file_path}`" for file_path in snapshot.changed_files)
            if snapshot.changed_files
            else "- (no file list provided)"
        )
        review_focus = snapshot.review_focus or "No extra focus hints provided."
        finding_categories = "\n".join(
            f"- `{self._normalize_finding_category(category)}`" for category in task_config.allowed_finding_categories
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
        snapshot_context = "\n".join(snapshot_lines)

        submit_tool_name = f"{self.config.mcp_server_name}submit_result"

        return LEAN_PR_REVIEW_USER_PROMPT.format(
            submit_tool_name=submit_tool_name,
            managed_skill_guidance=self._build_managed_skill_guidance(),
            submission_schema_path=self._review_submission_schema_relpath(),
            submission_example_path=self._review_submission_example_relpath(),
            submitted_review_path=self._submitted_review_relpath(),
            review_grading_path=self._review_grading_relpath(),
            pr_display=pr_display,
            pr_title=snapshot.pr_title,
            pr_author=snapshot.pr_author or "unknown",
            changed_files_count=len(snapshot.changed_files),
            changed_files_list=changed_files_list,
            pr_dependencies=pr_dependencies,
            snapshot_context=snapshot_context,
            review_focus=review_focus,
            pr_description=snapshot.pr_description or "(empty PR description)",
            pr_diff_preview=self._build_diff_preview(task_config.diff_preview_char_limit),
            finding_categories=finding_categories,
        )

    async def register_task_tools(self, mcp) -> None:
        """Register task-specific submission tool."""
        from pydantic import Field

        @mcp.tool(
            description=self._build_submit_tool_description()
        )
        async def submit_result(
            merge_ready: Annotated[bool, Field(description="True if PR is ready to merge, else False")],
            blocking_findings: Annotated[List[ReviewFinding], Field(
                description=(
                    "Blocking findings. Use canonical categories from the prompt and include structured evidence "
                    "on each finding."
                )
            )],
            advisory_findings: Annotated[Optional[List[ReviewFinding]], Field(
                description="Advisory findings (non-blocking), each with structured evidence.",
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
            needs_human_review: Annotated[bool, Field(
                description="True if the review should be escalated or handed off to a human maintainer.",
            )] = False,
            decision_confidence: Annotated[Optional[float], Field(
                description="Optional calibrated confidence in the overall merge-readiness decision.",
                ge=0.0,
                le=1.0,
                default=None,
            )] = None,
            feedback: Annotated[str, Field(
                description="Final reviewer feedback with key evidence.",
            )] = "",
        ) -> Dict[str, Any]:
            """Submit PR review for evaluation and termination."""
            self.logger.info("Tool submit_result: execution started")
            try:
                submission = PRReviewSubmission(
                    merge_ready=merge_ready,
                    needs_human_review=needs_human_review,
                    decision_confidence=decision_confidence,
                    blocking_findings=self._normalize_findings(blocking_findings),
                    advisory_findings=self._normalize_findings(advisory_findings or []),
                    guide_evidence_topics=self._normalize_guide_topics(guide_evidence_topics or []),
                    feedback=feedback,
                )
                blocked_reason = self._validate_submission_prerequisites(
                    merge_ready=submission.merge_ready,
                    needs_human_review=submission.needs_human_review,
                    decision_confidence=submission.decision_confidence,
                    blocking_findings=submission.blocking_findings,
                    advisory_findings=submission.advisory_findings,
                    feedback=submission.feedback,
                    guide_evidence_topics=submission.guide_evidence_topics,
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

                evaluation_result, review_data, custom_metrics = self._evaluate_review(submission)
                workspace_artifacts: Dict[str, str] = {}
                try:
                    workspace_artifacts = await self._write_workspace_artifacts(
                        submission=submission,
                        evaluation_result=evaluation_result,
                        review_data=review_data,
                        custom_metrics=custom_metrics,
                    )
                except Exception:
                    self.logger.error(
                        "Failed to write PR review workspace artifacts: %s",
                        traceback.format_exc(),
                    )

                if self.should_terminate(evaluation_result) and self.termination_callback:
                    task_result = self.create_result(
                        success=True,
                        score=evaluation_result.score,
                        merge_ready=submission.merge_ready,
                        needs_human_review=submission.needs_human_review,
                        decision_confidence=submission.decision_confidence,
                        blocking_findings=submission.blocking_findings,
                        advisory_findings=submission.advisory_findings,
                        guide_evidence_topics=submission.guide_evidence_topics,
                        feedback=submission.feedback,
                        review_data=review_data,
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
                    "review_data": review_data,
                    "workspace_artifacts": workspace_artifacts,
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
        submission: PRReviewSubmission,
    ) -> Tuple[EvaluationResult, Dict[str, Any], Optional[Dict[str, float]]]:
        return evaluate_review_submission(
            submission=submission,
            evaluation=self.data.evaluation,
            task_config=self.config.task_config,
            read_skill_relative_paths=self._get_skill_read_relative_paths(),
            tool_trace_payload=self._get_review_tool_trace_payload(),
        )

    def create_result(
        self,
        success: bool,
        score: float,
        merge_ready: bool,
        needs_human_review: bool,
        decision_confidence: Optional[float],
        blocking_findings: List[ReviewFinding],
        advisory_findings: List[ReviewFinding],
        guide_evidence_topics: List[str],
        feedback: str,
        review_data: Dict[str, Any],
        workspace_artifacts: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> ReviewPRResult:
        return ReviewPRResult(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=success,
            score=score,
            merge_ready=merge_ready,
            needs_human_review=needs_human_review,
            decision_confidence=decision_confidence,
            blocking_findings=blocking_findings,
            advisory_findings=advisory_findings,
            guide_evidence_topics=guide_evidence_topics,
            feedback=feedback,
            review_data=review_data,
            workspace_artifacts=workspace_artifacts or {},
            **kwargs,
        )

    def should_terminate(self, evaluation_result: EvaluationResult = None) -> bool:
        """Terminate once a valid review is submitted."""
        return bool(evaluation_result and evaluation_result.success)

    @classmethod
    def is_best_result(cls, result: BaseTaskResult) -> bool:
        """Treat decision correctness as the optimal outcome when it is available."""
        if not result.success:
            return False

        decision_accuracy = None
        if isinstance(result.custom_metrics, dict):
            raw_decision_accuracy = result.custom_metrics.get("decision_accuracy")
            if isinstance(raw_decision_accuracy, (int, float)):
                decision_accuracy = float(raw_decision_accuracy)

        if decision_accuracy is not None:
            return decision_accuracy == 1.0

        return super().is_best_result(result)
