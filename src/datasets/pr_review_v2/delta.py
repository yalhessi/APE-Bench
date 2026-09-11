"""
Stage D: hydrate δ₀ and the patch-level change-sets Δ₁ / Δ* (spec §3.6), and
link gold comments to Δ hunks (§3.7).

Everything is computed from cached three-dot compare-API calls — a three-dot
compare diffs against the merge base, so the patches P₀/P₁/P* are exactly the
PR's effective change at each head, with upstream churn excluded by
construction. Δ is then the per-file hunk difference between two patches,
where hunk identity is the normalized +/- content (robust to line drift from
unrelated upstream movement, validated in the Step-2 audit).
"""

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .config import PRReviewV2Config
from .fetch import fetch_compare
from .github import GitHubClient
from .schema import DeltaHunk, GoldComment, PRReviewV2Record

_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class ParsedHunk:
    def __init__(self, path: str, old_start: int, old_lines: int, new_start: int, new_lines: int,
                 lines: List[str]):
        self.path = path
        self.old_start = old_start
        self.old_lines = old_lines
        self.new_start = new_start
        self.new_lines = new_lines
        self.lines = lines  # full hunk body including context lines

    @property
    def content_key(self) -> str:
        """Identity of the change itself: only +/- lines, positions ignored."""
        changed = "\n".join(l for l in self.lines if l[:1] in "+-")
        return hashlib.md5(changed.encode("utf-8")).hexdigest()

    @property
    def hunk_id(self) -> str:
        return f"{self.path}@{self.content_key[:10]}"

    @property
    def patch_text(self) -> str:
        header = f"@@ -{self.old_start},{self.old_lines} +{self.new_start},{self.new_lines} @@"
        return "\n".join([header, *self.lines])


def parse_patch_hunks(path: str, patch: Optional[str]) -> List[ParsedHunk]:
    if not patch:
        return []
    hunks: List[ParsedHunk] = []
    current: Optional[ParsedHunk] = None
    for line in patch.splitlines():
        match = _HUNK_HEADER_RE.match(line)
        if match:
            current = ParsedHunk(
                path,
                int(match.group(1)), int(match.group(2) or 1),
                int(match.group(3)), int(match.group(4) or 1),
                [],
            )
            hunks.append(current)
        elif current is not None:
            current.lines.append(line)
    return hunks


def _patch_index(compare: Dict[str, Any]) -> Dict[str, List[ParsedHunk]]:
    index: Dict[str, List[ParsedHunk]] = {}
    for entry in compare.get("files") or []:
        path = entry.get("filename")
        if path:
            index[path] = parse_patch_hunks(path, entry.get("patch"))
    return index


# `assemble_unified_diff` lived here and in `mathlib_review/diffs.py` as two copies. They agree on
# all 223 cached compares; the shared one also skips a file entry with no filename, where this copy
# emitted `diff --git a/None b/None`. Re-exported so `delta` reads as it did.
from src.mathlib_review.diffs import assemble_unified_diff  # noqa: E402,F401


def diff_patches(p_before: Dict[str, List[ParsedHunk]], p_after: Dict[str, List[ParsedHunk]]) -> List[DeltaHunk]:
    """Hunk-level difference between two patches, aligned per file (spec §3.6)."""
    delta: List[DeltaHunk] = []
    for path in sorted(set(p_before) | set(p_after)):
        before = {h.content_key: h for h in p_before.get(path, [])}
        after = {h.content_key: h for h in p_after.get(path, [])}
        for key, hunk in after.items():
            if key not in before:
                delta.append(_to_delta(hunk, "added_in_revision"))
        for key, hunk in before.items():
            if key not in after:
                delta.append(_to_delta(hunk, "removed_in_revision"))
    return delta


def _to_delta(hunk: ParsedHunk, op: str) -> DeltaHunk:
    return DeltaHunk(
        hunk_id=hunk.hunk_id,
        path=hunk.path,
        op=op,  # type: ignore[arg-type]
        old_start=hunk.old_start,
        old_lines=hunk.old_lines,
        new_start=hunk.new_start,
        new_lines=hunk.new_lines,
        patch=hunk.patch_text,
    )


# ---------------------------------------------------------------------------
# comment → hunk linkage (spec §3.7)
# ---------------------------------------------------------------------------

def link_comments_to_hunks(
    comments: List[GoldComment],
    delta_near: List[DeltaHunk],
    *,
    line_slack: int,
) -> None:
    """Mutates `comments` in place with linked_hunks + link_confidence.

    Caveat (documented in the spec): comment anchors are line numbers in the
    h₀-era diff while Δ hunk positions are relative to each patch's own merge
    base; the slack absorbs small drift and the Step-2 audit judges the rest.
    """
    by_path: Dict[str, List[DeltaHunk]] = {}
    for hunk in delta_near:
        by_path.setdefault(hunk.path, []).append(hunk)

    for comment in comments:
        if comment.anchor is None or not comment.anchor.path:
            continue
        line = comment.anchor.line or comment.anchor.original_line
        if line is None:
            continue
        matches = [
            hunk for hunk in by_path.get(comment.anchor.path, [])
            if _overlaps(hunk, line, line_slack)
        ]
        if matches:
            comment.linked_hunks = [h.hunk_id for h in matches]
            comment.link_confidence = (
                "resolved_thread" if comment.thread_resolved else "line_overlap"
            )


def _overlaps(hunk: DeltaHunk, line: int, slack: int) -> bool:
    for start, length in ((hunk.new_start, hunk.new_lines), (hunk.old_start, hunk.old_lines)):
        if start is None:
            continue
        if start - slack <= line <= start + (length or 0) + slack:
            return True
    return False


# ---------------------------------------------------------------------------
# record hydration
# ---------------------------------------------------------------------------

def hydrate_record(
    record: PRReviewV2Record,
    client: GitHubClient,
    config: PRReviewV2Config,
    *,
    base_ref: str = "master",
) -> PRReviewV2Record:
    """Fill input.diff (δ₀), input.base_sha (true merge base), Δ₁, Δ*, linkage."""
    h0 = record.input.head_sha
    h1 = record.validation.h1_sha
    final_head = record.validation.final_head_sha
    refresh = config.refetch_compares

    try:
        c0 = fetch_compare(client, config, base_ref, h0, refresh=refresh)
        record.input.diff = assemble_unified_diff(c0)
        if c0.get("merge_base_sha"):
            record.input.base_sha = c0["merge_base_sha"]
        p0 = _patch_index(c0)

        if h1 and h1 != h0:
            c1 = fetch_compare(client, config, base_ref, h1, refresh=refresh)
            record.gold.delta_near = diff_patches(p0, _patch_index(c1))
        else:
            record.gold.delta_near = []

        if final_head and final_head != h0:
            if final_head == h1:
                record.gold.delta_total = list(record.gold.delta_near or [])
            else:
                ct = fetch_compare(client, config, base_ref, final_head, refresh=refresh)
                record.gold.delta_total = diff_patches(p0, _patch_index(ct))
        else:
            record.gold.delta_total = []

        link_comments_to_hunks(
            record.gold.comments,
            record.gold.delta_near or [],
            line_slack=config.linkage_line_slack,
        )
    except httpx.HTTPStatusError as exc:
        record.validation.hydration_error = f"compare_failed: {exc.response.status_code}"
    return record
