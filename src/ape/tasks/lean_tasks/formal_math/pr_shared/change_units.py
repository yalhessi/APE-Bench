"""Canonical PR diff units for standalone split planning."""

from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from typing import Iterable, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field


_DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")
_HUNK_HEADER_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_lines>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_lines>\d+))? @@(?P<label>.*)$"
)
_OLD_PATH_RE = re.compile(r"^--- (?P<path>.+)$")
_NEW_PATH_RE = re.compile(r"^\+\+\+ (?P<path>.+)$")
_RENAME_FROM_RE = re.compile(r"^rename from (?P<path>.+)$")
_RENAME_TO_RE = re.compile(r"^rename to (?P<path>.+)$")
_NO_NEWLINE_MARKER = "\\ No newline at end of file"


class PRChangeUnit(BaseModel):
    """One canonical unit that can be assigned to a split chunk."""

    model_config = ConfigDict(extra="forbid")

    unit_id: str = Field(..., description="Stable unit identifier within the PR snapshot")
    file_index: int = Field(..., ge=0, description="0-based order of the file block in the diff")
    unit_index: int = Field(..., ge=0, description="0-based order of the unit within the file block")
    file_path: str = Field(..., description="Repo-root relative file path for this unit")
    old_path: Optional[str] = Field(default=None, description="Repo-root relative old path, when available")
    new_path: Optional[str] = Field(default=None, description="Repo-root relative new path, when available")
    operation: str = Field(..., description="Coarse file operation: add, delete, rename, or modify")
    unit_kind: str = Field(..., description="Canonical unit kind: hunk or file_operation")
    hunk_header: Optional[str] = Field(default=None, description="Raw unified-diff hunk header when applicable")
    old_start: Optional[int] = Field(default=None, ge=0, description="Old-side hunk start line")
    old_lines: Optional[int] = Field(default=None, ge=0, description="Old-side hunk line span")
    new_start: Optional[int] = Field(default=None, ge=0, description="New-side hunk start line")
    new_lines: Optional[int] = Field(default=None, ge=0, description="New-side hunk line span")
    text: str = Field(..., description="Raw diff text for the unit")
    file_header_text: str = Field(..., description="Raw file-header text shared by units in this file block")
    preview: str = Field(..., description="Short human-readable preview of the unit")


def _normalize_diff_path(path: Optional[str]) -> Optional[str]:
    normalized = str(path or "").strip()
    if not normalized or normalized == "/dev/null":
        return None
    if normalized.startswith("a/") or normalized.startswith("b/"):
        return normalized[2:]
    return normalized


def _split_file_blocks(diff_text: str) -> list[list[str]]:
    if not diff_text:
        return []

    file_blocks: list[list[str]] = []
    current_block: list[str] = []
    for line in diff_text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            if current_block:
                file_blocks.append(current_block)
            current_block = [line]
            continue
        if current_block:
            current_block.append(line)
    if current_block:
        file_blocks.append(current_block)
    return file_blocks


def _default_old_lines(raw_value: Optional[str]) -> int:
    return int(raw_value) if raw_value is not None else 1


def _default_new_lines(raw_value: Optional[str]) -> int:
    return int(raw_value) if raw_value is not None else 1


def _preview_from_text(
    *,
    file_path: str,
    operation: str,
    unit_kind: str,
    old_path: Optional[str],
    new_path: Optional[str],
    text: str,
) -> str:
    if unit_kind == "file_operation":
        if operation == "rename" and old_path and new_path:
            return f"Rename `{old_path}` -> `{new_path}`"
        if operation == "add":
            return f"Add `{file_path}`"
        if operation == "delete":
            return f"Delete `{file_path}`"
        return f"{operation.title()} `{file_path}`"

    preview_source = ""
    for raw_line in text.splitlines():
        if raw_line.startswith(("+++", "---", "@@")) or raw_line == _NO_NEWLINE_MARKER:
            continue
        if raw_line.startswith(("+", "-", " ")):
            preview_source = raw_line[1:].strip()
            if preview_source:
                break
    if not preview_source:
        preview_source = file_path
    preview_source = re.sub(r"\s+", " ", preview_source)
    if len(preview_source) > 120:
        preview_source = preview_source[:117].rstrip() + "..."
    return preview_source or file_path


def _make_unit_id(
    *,
    file_index: int,
    unit_index: int,
    file_path: str,
    operation: str,
    unit_kind: str,
    hunk_header: Optional[str],
    text: str,
) -> str:
    digest_input = "\u241f".join(
        [
            file_path,
            operation,
            unit_kind,
            hunk_header or "",
            text,
            str(file_index),
            str(unit_index),
        ]
    )
    digest = hashlib.sha1(digest_input.encode("utf-8")).hexdigest()[:10]
    return f"u{file_index + 1:03d}_{unit_index + 1:03d}_{digest}"


def _build_file_header_text(lines: Sequence[str]) -> str:
    return "".join(lines)


def _parse_file_block(
    *,
    file_index: int,
    lines: Sequence[str],
    changed_files: Sequence[str],
) -> list[PRChangeUnit]:
    if not lines:
        return []

    header_lines: list[str] = []
    old_path: Optional[str] = None
    new_path: Optional[str] = None
    rename_from: Optional[str] = None
    rename_to: Optional[str] = None
    operation = "modify"
    hunks: list[list[str]] = []
    current_hunk: list[str] = []
    in_hunk = False

    for raw_line in lines:
        stripped = raw_line.rstrip("\n")

        if raw_line.startswith("@@ "):
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = [raw_line]
            in_hunk = True
            continue

        if in_hunk:
            current_hunk.append(raw_line)
            continue

        header_lines.append(raw_line)
        if stripped.startswith("new file mode "):
            operation = "add"
        elif stripped.startswith("deleted file mode "):
            operation = "delete"
        elif stripped.startswith("rename from "):
            operation = "rename"
            match = _RENAME_FROM_RE.match(stripped)
            if match:
                rename_from = _normalize_diff_path(match.group("path"))
        elif stripped.startswith("rename to "):
            operation = "rename"
            match = _RENAME_TO_RE.match(stripped)
            if match:
                rename_to = _normalize_diff_path(match.group("path"))

        old_match = _OLD_PATH_RE.match(stripped)
        if old_match:
            old_path = _normalize_diff_path(old_match.group("path"))

        new_match = _NEW_PATH_RE.match(stripped)
        if new_match:
            new_path = _normalize_diff_path(new_match.group("path"))

        diff_match = _DIFF_HEADER_RE.match(stripped)
        if diff_match:
            old_path = old_path or _normalize_diff_path(diff_match.group(1))
            new_path = new_path or _normalize_diff_path(diff_match.group(2))

    if current_hunk:
        hunks.append(current_hunk)

    old_path = rename_from or old_path
    new_path = rename_to or new_path
    file_path = new_path or old_path or (changed_files[file_index] if file_index < len(changed_files) else f"file_{file_index}")
    file_header_text = _build_file_header_text(header_lines)

    units: list[PRChangeUnit] = []
    if not hunks:
        unit_text = "".join(lines)
        preview = _preview_from_text(
            file_path=file_path,
            operation=operation,
            unit_kind="file_operation",
            old_path=old_path,
            new_path=new_path,
            text=unit_text,
        )
        units.append(
            PRChangeUnit(
                unit_id=_make_unit_id(
                    file_index=file_index,
                    unit_index=0,
                    file_path=file_path,
                    operation=operation,
                    unit_kind="file_operation",
                    hunk_header=None,
                    text=unit_text,
                ),
                file_index=file_index,
                unit_index=0,
                file_path=file_path,
                old_path=old_path,
                new_path=new_path,
                operation=operation,
                unit_kind="file_operation",
                hunk_header=None,
                old_start=None,
                old_lines=None,
                new_start=None,
                new_lines=None,
                text=unit_text,
                file_header_text=file_header_text,
                preview=preview,
            )
        )
        return units

    for unit_index, hunk_lines in enumerate(hunks):
        hunk_text = "".join(hunk_lines)
        hunk_header = hunk_lines[0].rstrip("\n")
        match = _HUNK_HEADER_RE.match(hunk_header)
        old_start = int(match.group("old_start")) if match else None
        old_lines = _default_old_lines(match.group("old_lines")) if match else None
        new_start = int(match.group("new_start")) if match else None
        new_lines = _default_new_lines(match.group("new_lines")) if match else None
        preview = _preview_from_text(
            file_path=file_path,
            operation=operation,
            unit_kind="hunk",
            old_path=old_path,
            new_path=new_path,
            text=hunk_text,
        )
        units.append(
            PRChangeUnit(
                unit_id=_make_unit_id(
                    file_index=file_index,
                    unit_index=unit_index,
                    file_path=file_path,
                    operation=operation,
                    unit_kind="hunk",
                    hunk_header=hunk_header,
                    text=hunk_text,
                ),
                file_index=file_index,
                unit_index=unit_index,
                file_path=file_path,
                old_path=old_path,
                new_path=new_path,
                operation=operation,
                unit_kind="hunk",
                hunk_header=hunk_header,
                old_start=old_start,
                old_lines=old_lines,
                new_start=new_start,
                new_lines=new_lines,
                text=hunk_text,
                file_header_text=file_header_text,
                preview=preview,
            )
        )
    return units


def parse_pr_change_units(pr_diff: str, changed_files: Sequence[str]) -> list[PRChangeUnit]:
    """Parse a PR diff into canonical file-scoped change units."""

    file_blocks = _split_file_blocks(pr_diff or "")
    units: list[PRChangeUnit] = []
    for file_index, file_lines in enumerate(file_blocks):
        units.extend(
            _parse_file_block(
                file_index=file_index,
                lines=file_lines,
                changed_files=changed_files,
            )
        )
    return units


def build_chunk_diff(units: Sequence[PRChangeUnit]) -> str:
    """Render a readable diff preview for one proposed split chunk."""

    ordered_units = sorted(units, key=lambda unit: (unit.file_index, unit.unit_index))
    if not ordered_units:
        return "# Empty chunk diff\n"

    grouped_units: "OrderedDict[int, list[PRChangeUnit]]" = OrderedDict()
    for unit in ordered_units:
        grouped_units.setdefault(unit.file_index, []).append(unit)

    sections: list[str] = []
    for file_units in grouped_units.values():
        first_unit = file_units[0]
        if any(unit.unit_kind == "file_operation" for unit in file_units):
            for unit in file_units:
                text = unit.text.rstrip("\n")
                if text:
                    sections.append(text)
            continue

        header = first_unit.file_header_text.rstrip("\n")
        if header:
            sections.append(header)
        for unit in file_units:
            text = unit.text.rstrip("\n")
            if text:
                sections.append(text)

    rendered = "\n".join(section for section in sections if section)
    return f"{rendered.rstrip()}\n" if rendered.strip() else "# Empty chunk diff\n"
