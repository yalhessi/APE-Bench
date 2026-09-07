"""Build complete review-time change graphs from isolated v4 episode inputs."""

from __future__ import annotations

import argparse
import json
import re
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, pretty_json_bytes, sha256_bytes, write_once
from src.mathlib_review.schema import (
    ChangeFileCoverage,
    ChangeGraph,
    ChangeTarget,
    ChangedRange,
    LineSpan,
    ReviewEpisodeInput,
    SemanticEntity,
)


CHANGE_GRAPH_BUILDER_VERSION = "cg1_builder_v2"
LEAN_PARSER_VERSION = "ape_lean_major_decl_v1"
_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_DIFF_RE = re.compile(r"^diff --git a/(.*?) b/(.*)$")


@dataclass
class DiffHunk:
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    header: str
    lines: List[str] = field(default_factory=list)


@dataclass
class DiffFile:
    old_path: Optional[str]
    path: str
    status: str
    hunks: List[DiffHunk] = field(default_factory=list)
    missing_patch_reason: Optional[str] = None


def _hash_id(prefix: str, value: object) -> str:
    return f"{prefix}:{sha256_bytes(canonical_json_bytes(value))}"


def parse_unified_diff(diff: str) -> List[DiffFile]:
    """Parse the stable unified-diff subset emitted by the v4 compare assembler."""
    parsed: List[DiffFile] = []
    current: Optional[Dict] = None
    hunk: Optional[DiffHunk] = None

    def finish() -> None:
        nonlocal current, hunk
        if current is None:
            return
        raw_old = current.get("old_header")
        raw_new = current.get("new_header")
        old_path = None if raw_old == "/dev/null" else (raw_old or current["git_old"])
        new_path = None if raw_new == "/dev/null" else (raw_new or current["git_new"])
        path = new_path or old_path
        if path is None:
            raise ValueError("diff file has neither an old nor a reviewed path")
        if old_path is None:
            status = "added"
        elif new_path is None:
            status = "removed"
        elif old_path != new_path:
            status = "renamed"
        else:
            status = "modified"
        parsed.append(
            DiffFile(
                old_path=old_path,
                path=path,
                status=status,
                hunks=current["hunks"],
                missing_patch_reason=current.get("missing_patch_reason"),
            )
        )
        current = None
        hunk = None

    for line in diff.splitlines():
        match = _DIFF_RE.match(line)
        if match:
            finish()
            current = {"git_old": match.group(1), "git_new": match.group(2), "hunks": []}
            continue
        if current is None:
            if line.strip():
                raise ValueError(f"content outside a diff file: {line[:80]}")
            continue
        if hunk is None and line.startswith("--- "):
            label = line[4:].strip()
            current["old_header"] = label[2:] if label.startswith("a/") else label
            continue
        if hunk is None and line.startswith("+++ "):
            label = line[4:].strip()
            current["new_header"] = label[2:] if label.startswith("b/") else label
            continue
        hunk_match = _HUNK_RE.match(line)
        if hunk_match:
            hunk = DiffHunk(
                old_start=int(hunk_match.group(1)),
                old_lines=int(hunk_match.group(2) or 1),
                new_start=int(hunk_match.group(3)),
                new_lines=int(hunk_match.group(4) or 1),
                header=line,
            )
            current["hunks"].append(hunk)
            continue
        if line.startswith("(no textual patch available"):
            current["missing_patch_reason"] = line
            continue
        if hunk is not None:
            hunk.lines.append(line)
    finish()
    return parsed


def changed_ranges(episode: ReviewEpisodeInput, files: Sequence[DiffFile]) -> List[ChangedRange]:
    ranges: List[ChangedRange] = []
    range_index = 0
    for diff_file in files:
        for hunk_index, hunk in enumerate(diff_file.hunks):
            old_cursor = hunk.old_start
            new_cursor = hunk.new_start
            run_lines: List[str] = []
            old_positions: List[int] = []
            new_positions: List[int] = []

            def flush() -> None:
                nonlocal range_index, run_lines, old_positions, new_positions
                if not run_lines:
                    return
                kind = (
                    "replacement"
                    if old_positions and new_positions
                    else "deletion"
                    if old_positions
                    else "addition"
                )
                fragment = "\n".join([hunk.header, *run_lines]) + "\n"
                identity = {
                    "episode_id": episode.episode_id,
                    "path": diff_file.path,
                    "old_path": diff_file.old_path,
                    "hunk_index": hunk_index,
                    "range_index": range_index,
                    "old_positions": old_positions,
                    "new_positions": new_positions,
                    "fragment": fragment,
                }
                ranges.append(
                    ChangedRange(
                        range_id=_hash_id("range", identity),
                        path=diff_file.path,
                        old_path=diff_file.old_path,
                        hunk_index=hunk_index,
                        range_index=range_index,
                        change_kind=kind,
                        old_span=(
                            LineSpan(line_start=min(old_positions), line_end=max(old_positions))
                            if old_positions
                            else None
                        ),
                        reviewed_span=(
                            LineSpan(line_start=min(new_positions), line_end=max(new_positions))
                            if new_positions
                            else None
                        ),
                        diff_fragment=fragment,
                        source_sha256=sha256_bytes(canonical_json_bytes(identity)),
                    )
                )
                range_index += 1
                run_lines = []
                old_positions = []
                new_positions = []

            for line in hunk.lines:
                marker = line[:1]
                if marker == " ":
                    flush()
                    old_cursor += 1
                    new_cursor += 1
                elif marker == "-":
                    run_lines.append(line)
                    old_positions.append(old_cursor)
                    old_cursor += 1
                elif marker == "+":
                    run_lines.append(line)
                    new_positions.append(new_cursor)
                    new_cursor += 1
                elif marker == "\\" and run_lines:
                    run_lines.append(line)
                elif line:
                    raise ValueError(f"unexpected hunk line marker in {diff_file.path}: {line[:80]}")
            flush()
    return ranges


def apply_file_patch(base_text: str, diff_file: DiffFile) -> str:
    """Apply one parsed file patch in memory, validating every context/deletion line."""
    source = base_text.splitlines()
    output: List[str] = []
    source_index = 0
    final_newline = base_text.endswith("\n") or diff_file.status == "added"
    for hunk in diff_file.hunks:
        hunk_index = max(0, hunk.old_start - 1)
        if hunk_index < source_index:
            raise ValueError(f"overlapping hunks in {diff_file.path}")
        output.extend(source[source_index:hunk_index])
        source_index = hunk_index
        previous_marker = ""
        for line in hunk.lines:
            marker, content = line[:1], line[1:]
            if marker in {" ", "-"}:
                if source_index >= len(source) or source[source_index] != content:
                    actual = source[source_index] if source_index < len(source) else "<EOF>"
                    raise ValueError(
                        f"patch mismatch in {diff_file.path}:{source_index + 1}: "
                        f"expected {content!r}, found {actual!r}"
                    )
                if marker == " ":
                    output.append(content)
                source_index += 1
            elif marker == "+":
                output.append(content)
            elif marker == "\\":
                if previous_marker == "+":
                    final_newline = False
            elif line:
                raise ValueError(f"unexpected patch line in {diff_file.path}: {line[:80]}")
            previous_marker = marker
    output.extend(source[source_index:])
    rendered = "\n".join(output)
    return rendered + ("\n" if final_newline else "")


def _line_span(source: str, start: int, end: int) -> LineSpan:
    line_start = source.count("\n", 0, start) + 1
    last = max(start, end - 1)
    line_end = source.count("\n", 0, last) + 1
    return LineSpan(line_start=line_start, line_end=line_end)


def _parse_major_declarations(source: str) -> List[Any]:
    from ape.toolkits.code.lean.lean_parser import parse_major_declarations

    return parse_major_declarations(source)


def _entity(
    side: str,
    path: str,
    source: str,
    decl: Any,
    *,
    start_override: Optional[int] = None,
) -> SemanticEntity:
    start = decl.span[0] if start_override is None else start_override
    code = source[start : decl.span[1]]
    identity = {
        "parser_version": LEAN_PARSER_VERSION,
        "side": side,
        "path": path,
        "kind": decl.kind,
        "name": decl.name,
        "fullname": decl.fullname,
        "code": code,
    }
    return SemanticEntity(
        entity_id=_hash_id("lean-decl", identity),
        side=side,
        path=path,
        kind=decl.kind,
        name=decl.name,
        fullname=decl.fullname,
        span=_line_span(source, start, decl.span[1]),
        code=code,
        source_sha256=sha256_bytes(code.encode("utf-8")),
        parser_version=LEAN_PARSER_VERSION,
    )


def _region_entity(
    side: str, path: str, source: str, *, kind: str, start: int, end: int
) -> SemanticEntity:
    code = source[start:end]
    identity = {
        "parser_version": LEAN_PARSER_VERSION,
        "side": side,
        "path": path,
        "kind": kind,
        "code": code,
    }
    return SemanticEntity(
        entity_id=_hash_id("lean-region", identity),
        side=side,
        path=path,
        kind=kind,
        span=_line_span(source, start, end),
        code=code,
        source_sha256=sha256_bytes(code.encode("utf-8")),
        parser_version=LEAN_PARSER_VERSION,
    )


def _source_entities(side: str, path: str, source: str) -> List[SemanticEntity]:
    """Parse major declarations plus the remaining complete top-level command regions."""
    from ape.toolkits.code.lean.lean_parser import _build_top_level_index

    index = _build_top_level_index(source)
    declarations = []
    for declaration in _parse_major_declarations(source):
        prior_index = bisect_right(index.cmd_positions, declaration.span[0]) - 1
        command_start = (
            index.cmd_positions[prior_index]
            if prior_index >= 0
            else declaration.span[0]
        )
        if index.find_next_cmd_after(command_start) <= declaration.span[0]:
            command_start = declaration.span[0]
        declarations.append(
            _entity(
                side,
                path,
                source,
                declaration,
                start_override=command_start,
            )
        )
    declaration_spans = [(item.span.line_start, item.span.line_end) for item in declarations]
    regions: List[SemanticEntity] = []
    for position, end in zip(index.cmd_positions, [*index.cmd_positions[1:], len(source)]):
        span = _line_span(source, position, end)
        if any(
            span.line_start <= decl_end and decl_start <= span.line_end
            for decl_start, decl_end in declaration_spans
        ):
            continue
        code = source[position:end]
        stripped = code.lstrip()
        kind = "module_doc" if stripped.startswith("/-!") else "command"
        regions.append(
            _region_entity(side, path, source, kind=kind, start=position, end=end)
        )
    return sorted([*declarations, *regions], key=lambda item: (item.span.line_start, item.entity_id))


def _target_kind_for_entity(entity: SemanticEntity) -> str:
    if entity.kind in {"module_doc", "namespace", "section", "import"}:
        return entity.kind
    if entity.kind == "command":
        stripped = entity.code.lstrip()
        if re.match(r"^(?:namespace|open|export)\b", stripped):
            return "namespace"
        if re.match(r"^(?:section|end|variable|variables|include|omit|attribute)\b", stripped):
            return "section"
        return "command"
    return "declaration"


def _overlaps(left: Optional[LineSpan], right: LineSpan) -> bool:
    return bool(
        left
        and left.line_start <= right.line_end
        and right.line_start <= left.line_end
    )


def _changed_text(item: ChangedRange) -> List[str]:
    return [line[1:] for line in item.diff_fragment.splitlines()[1:] if line[:1] in {"+", "-"}]


def _structural_kind(path: str, item: ChangedRange) -> str:
    lines = _changed_text(item)
    nonempty = [line.strip() for line in lines if line.strip()]
    if not path.endswith(".lean"):
        return "non_lean"
    if not nonempty:
        return "whitespace"
    if all(re.match(r"^(?:public\s+)?import\b", line) for line in nonempty):
        return "import"
    if all(
        re.match(
            r"^(?:module|prelude|deprecated_module\b|(?:public\s+)?(?:meta\s+)?import\b)",
            line,
        )
        for line in nonempty
    ):
        return "command"
    if any("/-!" in line or "-/" in line for line in nonempty):
        return "module_doc"
    if all(re.match(r"^(?:namespace|open|export)\b", line) for line in nonempty):
        return "namespace"
    if all(re.match(r"^(?:section|end|variable|include|omit|attribute)\b", line) for line in nonempty):
        return "section"
    return "unparsed"


def _target(
    episode: ReviewEpisodeInput,
    *,
    path: str,
    kind: str,
    ranges: Sequence[ChangedRange],
    base_entities: Sequence[SemanticEntity] = (),
    reviewed_entities: Sequence[SemanticEntity] = (),
    context_refs: Sequence[str] = (),
) -> ChangeTarget:
    base_ids = sorted({item.entity_id for item in base_entities})
    reviewed_ids = sorted({item.entity_id for item in reviewed_entities})
    range_ids = sorted({item.range_id for item in ranges})
    fragments = [item.diff_fragment for item in sorted(ranges, key=lambda item: item.range_index)]
    semantic = bool(base_ids or reviewed_ids)
    declaration = (list(reviewed_entities) or list(base_entities) or [None])[0]
    identity = {
        "episode_id": episode.episode_id,
        "kind": kind,
        "path": path,
        "base_entity_ids": base_ids,
        "reviewed_entity_ids": reviewed_ids,
        "range_ids": range_ids,
    }
    source = {
        **identity,
        "fragments": fragments,
        "base_code": [item.code for item in base_entities],
        "reviewed_code": [item.code for item in reviewed_entities],
    }
    return ChangeTarget(
        change_id=_hash_id("change", identity),
        episode_id=episode.episode_id,
        pr_number=episode.pr_number,
        kind=kind,
        path=path,
        declaration_name=(declaration.fullname or declaration.name) if declaration else None,
        declaration_kind=declaration.kind if declaration else None,
        base_entity_ids=base_ids,
        reviewed_entity_ids=reviewed_ids,
        changed_range_ids=range_ids,
        diff_fragments=fragments,
        base_code="\n\n".join(item.code for item in base_entities) or None,
        reviewed_code="\n\n".join(item.code for item in reviewed_entities) or None,
        context_refs=list(dict.fromkeys(context_refs)),
        parse_status="semantic" if semantic else "structural" if kind != "unparsed" else "unparsed",
        source_sha256=sha256_bytes(canonical_json_bytes(source)),
    )


def build_change_graph(
    episode: ReviewEpisodeInput,
    *,
    workspace_root: Path,
    blob_cache_root: Optional[Path] = None,
) -> ChangeGraph:
    files = parse_unified_diff(episode.diff)
    ranges = changed_ranges(episode, files)
    ranges_by_path: Dict[str, List[ChangedRange]] = defaultdict(list)
    for item in ranges:
        ranges_by_path[item.path].append(item)

    all_entities: Dict[str, SemanticEntity] = {}
    targets: List[ChangeTarget] = []
    coverage: List[ChangeFileCoverage] = []
    source_inputs: List[Dict] = []
    base_workspace = workspace_root / episode.base_sha

    for diff_file in files:
        file_ranges = ranges_by_path[diff_file.path]
        patch_status = "textual" if diff_file.hunks else "missing_textual_patch"
        source_status = "not_lean" if not diff_file.path.endswith(".lean") else "full"
        exclusion_reason = diff_file.missing_patch_reason
        base_text: Optional[str] = None
        reviewed_text: Optional[str] = None
        base_path = diff_file.old_path or diff_file.path

        if diff_file.path.endswith(".lean") and patch_status == "textual":
            if diff_file.status == "added":
                base_text = ""
            else:
                candidate = base_workspace / base_path
                if candidate.is_file():
                    base_text = candidate.read_text(encoding="utf-8")
                elif blob_cache_root and (blob_cache_root / episode.base_sha / base_path).is_file():
                    base_text = (blob_cache_root / episode.base_sha / base_path).read_text(
                        encoding="utf-8"
                    )
                    source_status = "full_blob_cache"
                else:
                    source_status = (
                        "missing_base_snapshot"
                        if not base_workspace.is_dir()
                        else "missing_base_file"
                    )
                    exclusion_reason = f"base file unavailable: {episode.base_sha}:{base_path}"
            if base_text is not None and diff_file.status != "removed":
                try:
                    reviewed_text = apply_file_patch(base_text, diff_file)
                except ValueError as exc:
                    source_status = "missing_base_file"
                    exclusion_reason = str(exc)
                    base_text = None
            elif diff_file.status == "removed":
                reviewed_text = ""
        elif patch_status == "missing_textual_patch":
            source_status = "not_applicable"

        try:
            base_entities = (
                _source_entities("base", base_path, base_text)
                if base_text
                else []
            )
            reviewed_entities = (
                [
                    item
                    for item in _source_entities("reviewed", diff_file.path, reviewed_text)
                ]
                if reviewed_text
                else []
            )
        except Exception as exc:  # Parser failures are coverage states, not dropped ranges.
            source_status = "parse_failed"
            exclusion_reason = f"Lean declaration parser failed: {type(exc).__name__}: {exc}"
            base_entities = []
            reviewed_entities = []
        source_inputs.append(
            {
                "path": diff_file.path,
                "base_sha256": (
                    sha256_bytes(base_text.encode("utf-8"))
                    if base_text is not None
                    else None
                ),
                "reviewed_sha256": (
                    sha256_bytes(reviewed_text.encode("utf-8"))
                    if reviewed_text is not None
                    else None
                ),
                "source_status": source_status,
            }
        )
        entity_order = {item.entity_id: index for index, item in enumerate(reviewed_entities)}
        target_groups: Dict[Tuple, Dict] = {}

        for changed in file_ranges:
            old_hits = [item for item in base_entities if _overlaps(changed.old_span, item.span)]
            new_hits = [
                item for item in reviewed_entities if _overlaps(changed.reviewed_span, item.span)
            ]
            if new_hits or old_hits:
                attached_old_ids = set()
                for entity in new_hits:
                    target_kind = _target_kind_for_entity(entity)
                    matches = [
                        item
                        for item in old_hits
                        if (item.fullname or item.name) == (entity.fullname or entity.name)
                    ]
                    if not matches and len(new_hits) == 1 and len(old_hits) == 1:
                        matches = old_hits
                    attached_old_ids.update(item.entity_id for item in matches)
                    key = (target_kind, entity.entity_id)
                    group = target_groups.setdefault(
                        key,
                        {"ranges": [], "base": [], "reviewed": [entity], "context": []},
                    )
                    group["base"].extend(matches)
                    index = entity_order[entity.entity_id]
                    for neighbor in reviewed_entities[max(0, index - 1) : index + 2]:
                        if neighbor.entity_id != entity.entity_id:
                            group["context"].append(neighbor.entity_id)
                            all_entities[neighbor.entity_id] = neighbor
                    group["ranges"].append(changed)
                    all_entities[entity.entity_id] = entity
                    for item in matches:
                        all_entities[item.entity_id] = item
                for entity in old_hits:
                    if entity.entity_id in attached_old_ids:
                        continue
                    key = (_target_kind_for_entity(entity), entity.entity_id)
                    group = target_groups.setdefault(
                        key,
                        {"ranges": [], "base": [entity], "reviewed": [], "context": []},
                    )
                    group["ranges"].append(changed)
                    all_entities[entity.entity_id] = entity
            else:
                kind = _structural_kind(diff_file.path, changed)
                key = (kind, diff_file.path)
                group = target_groups.setdefault(
                    key, {"ranges": [], "base": [], "reviewed": [], "context": []}
                )
                group["ranges"].append(changed)

        file_targets = []
        for (kind, _key), group in target_groups.items():
            item = _target(
                episode,
                path=diff_file.path,
                kind=kind,
                ranges=group["ranges"],
                base_entities=list({x.entity_id: x for x in group["base"]}.values()),
                reviewed_entities=list(
                    {x.entity_id: x for x in group["reviewed"]}.values()
                ),
                context_refs=group["context"],
            )
            targets.append(item)
            file_targets.append(item)

        coverage.append(
            ChangeFileCoverage(
                path=diff_file.path,
                old_path=diff_file.old_path,
                file_status=diff_file.status,
                patch_status=patch_status,
                source_status=source_status,
                base_source_sha256=(
                    sha256_bytes(base_text.encode("utf-8"))
                    if base_text is not None
                    else None
                ),
                reviewed_source_sha256=(
                    sha256_bytes(reviewed_text.encode("utf-8"))
                    if reviewed_text is not None
                    else None
                ),
                changed_range_ids=[item.range_id for item in file_ranges],
                change_target_ids=[item.change_id for item in file_targets],
                exclusion_reason=exclusion_reason,
            )
        )

    source_identity = {
        "episode_id": episode.episode_id,
        "patch_sha256": episode.patch_sha256,
        "parser_version": LEAN_PARSER_VERSION,
        "files": source_inputs,
    }
    graph_content = {
        "source": source_identity,
        "ranges": [item.model_dump(mode="json") for item in ranges],
        "entities": [item.model_dump(mode="json") for item in all_entities.values()],
        "targets": [item.model_dump(mode="json") for item in targets],
        "coverage": [item.model_dump(mode="json") for item in coverage],
    }
    graph = ChangeGraph(
        graph_id=_hash_id("graph", graph_content),
        episode_id=episode.episode_id,
        repo=episode.repo,
        pr_number=episode.pr_number,
        round_index=episode.round_index,
        base_sha=episode.base_sha,
        reviewed_head_sha=episode.reviewed_head_sha,
        patch_sha256=episode.patch_sha256,
        parser_version=CHANGE_GRAPH_BUILDER_VERSION,
        changed_ranges=ranges,
        entities=sorted(all_entities.values(), key=lambda item: item.entity_id),
        targets=sorted(targets, key=lambda item: item.change_id),
        file_coverage=sorted(coverage, key=lambda item: item.path),
        source_sha256=sha256_bytes(canonical_json_bytes(source_identity)),
    )
    validate_change_graph(graph, episode)
    return graph


def validate_change_graph(graph: ChangeGraph, episode: ReviewEpisodeInput) -> None:
    if graph.episode_id != episode.episode_id or graph.patch_sha256 != episode.patch_sha256:
        raise ValueError(f"{episode.episode_id}: graph source episode mismatch")
    range_ids = {item.range_id for item in graph.changed_ranges}
    if len(range_ids) != len(graph.changed_ranges):
        raise ValueError(f"{episode.episode_id}: duplicate changed range ID")
    target_ids = {item.change_id for item in graph.targets}
    if len(target_ids) != len(graph.targets):
        raise ValueError(f"{episode.episode_id}: duplicate change target ID")
    entity_ids = {item.entity_id for item in graph.entities}
    if len(entity_ids) != len(graph.entities):
        raise ValueError(f"{episode.episode_id}: duplicate semantic entity ID")
    covered_ranges = {
        range_id for item in graph.targets for range_id in item.changed_range_ids
    }
    if covered_ranges != range_ids:
        raise ValueError(f"{episode.episode_id}: target coverage does not equal changed ranges")
    file_ranges = {
        range_id for item in graph.file_coverage for range_id in item.changed_range_ids
    }
    if file_ranges != range_ids:
        raise ValueError(f"{episode.episode_id}: file coverage does not equal changed ranges")
    file_targets = {
        target_id for item in graph.file_coverage for target_id in item.change_target_ids
    }
    if file_targets != target_ids:
        raise ValueError(f"{episode.episode_id}: file coverage does not equal change targets")
    for target in graph.targets:
        if not set(target.base_entity_ids + target.reviewed_entity_ids).issubset(entity_ids):
            raise ValueError(f"{target.change_id}: references unknown semantic entity")
        if not set(target.context_refs).issubset(entity_ids):
            raise ValueError(f"{target.change_id}: references unknown context entity")
    for entity in graph.entities:
        if sha256_bytes(entity.code.encode("utf-8")) != entity.source_sha256:
            raise ValueError(f"{entity.entity_id}: semantic entity source hash mismatch")
    graph_paths = {item.path for item in graph.file_coverage}
    if graph_paths != set(episode.changed_files):
        raise ValueError(
            f"{episode.episode_id}: graph files differ from episode changed files: "
            f"{sorted(graph_paths ^ set(episode.changed_files))}"
        )
    for item in graph.file_coverage:
        if item.patch_status == "missing_textual_patch" and not item.exclusion_reason:
            raise ValueError(f"{episode.episode_id}:{item.path}: missing patch has no exclusion")
        if (
            graph.parser_version == CHANGE_GRAPH_BUILDER_VERSION
            and item.source_status in {"full", "full_blob_cache"}
        ):
            if item.base_source_sha256 is None or item.reviewed_source_sha256 is None:
                raise ValueError(f"{episode.episode_id}:{item.path}: full source hashes missing")


def build_graph_artifact(
    *,
    release_dir: Path,
    workspace_root: Path,
    blob_cache_root: Optional[Path],
    out: Path,
    report_out: Path,
) -> Dict[str, object]:
    episodes = [
        ReviewEpisodeInput.model_validate_json(line)
        for line in (release_dir / "input" / "episodes.jsonl").read_text().splitlines()
        if line.strip()
    ]
    graphs = [
        build_change_graph(
            episode,
            workspace_root=workspace_root,
            blob_cache_root=blob_cache_root,
        )
        for episode in episodes
    ]
    status_counts: Dict[str, int] = defaultdict(int)
    kind_counts: Dict[str, int] = defaultdict(int)
    range_states: Dict[str, set] = defaultdict(set)
    for graph in graphs:
        for item in graph.file_coverage:
            status_counts[item.source_status] += 1
        for item in graph.targets:
            kind_counts[item.kind] += 1
            for range_id in item.changed_range_ids:
                range_states[range_id].add(item.parse_status)
    range_mapping = {"semantic": 0, "structural_only": 0, "unparsed_only": 0}
    for states in range_states.values():
        if "semantic" in states:
            range_mapping["semantic"] += 1
        elif "structural" in states:
            range_mapping["structural_only"] += 1
        else:
            range_mapping["unparsed_only"] += 1
    report = {
        "schema_version": "cg-audit1",
        "release": str(release_dir),
        "builder_version": CHANGE_GRAPH_BUILDER_VERSION,
        "episodes": len(graphs),
        "changed_ranges": sum(len(item.changed_ranges) for item in graphs),
        "semantic_entities": sum(len(item.entities) for item in graphs),
        "change_targets": sum(len(item.targets) for item in graphs),
        "file_coverage": sum(len(item.file_coverage) for item in graphs),
        "source_status": dict(sorted(status_counts.items())),
        "target_kind": dict(sorted(kind_counts.items())),
        "range_mapping": range_mapping,
        "graphs_with_unparsed_targets": sum(
            any(target.parse_status == "unparsed" for target in graph.targets)
            for graph in graphs
        ),
        "graphs_sha256": sha256_bytes(jsonl_bytes(graphs)),
    }
    write_once(out, jsonl_bytes(graphs))
    write_once(report_out, pretty_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PR Review v4 change graphs")
    parser.add_argument("release", type=Path)
    parser.add_argument(
        "--workspaces",
        type=Path,
        default=Path("data/code_execute/repos/mathlib4/workspaces"),
    )
    parser.add_argument(
        "--blob-cache",
        type=Path,
        default=Path("data/pr_review_v4/cache/base_files"),
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = build_graph_artifact(
        release_dir=args.release,
        workspace_root=args.workspaces,
        blob_cache_root=args.blob_cache,
        out=args.out,
        report_out=args.report,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
