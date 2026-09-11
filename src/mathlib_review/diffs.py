"""Review-time unified diffs from immutable cached compare responses.

Where a compare comes from is a *source*: the flat v2 cache directory (`DirectoryCompares`), or the
PR store (`PullRequestStore.compares(n)`). The funnel asks a source for `review_diff(head)` and never
learns which; that is what lets the store replace the frozen cache without the funnel changing.
"""

import json
from pathlib import Path
from typing import Any, Dict, Protocol, Tuple

from src.mathlib_review.io import sha256_file


def assemble_unified_diff(compare: Dict[str, Any]) -> str:
    parts = []
    for entry in compare.get("files") or []:
        path = entry.get("filename")
        if not path:
            continue
        status = entry.get("status")
        old_path = entry.get("previous_filename") or path
        old_label = "/dev/null" if status == "added" else f"a/{old_path}"
        new_label = "/dev/null" if status == "removed" else f"b/{path}"
        parts.extend(
            [
                f"diff --git a/{old_path} b/{path}",
                f"--- {old_label}",
                f"+++ {new_label}",
            ]
        )
        patch = entry.get("patch")
        if patch:
            parts.append(str(patch))
        else:
            parts.append(f"(no textual patch available for {path}, status={status})")
    return "\n".join(parts) + ("\n" if parts else "")


def load_review_compare(cache_dir: Path, reviewed_head_sha: str) -> Tuple[Dict[str, Any], Path]:
    matches = sorted(cache_dir.glob(f"*...{reviewed_head_sha}.json"))
    if len(matches) != 1:
        raise ValueError(
            f"expected one cached compare for {reviewed_head_sha}, found {len(matches)}"
        )
    path = matches[0]
    return json.loads(path.read_text()), path


def diff_from_compare(compare: Dict[str, Any], compare_sha256: str, *, where: Any) -> Tuple[str, str, str]:
    """`(unified diff, merge base, compare sha)` from one compare payload."""

    merge_base = str(compare.get("merge_base_sha") or "").strip()
    if not merge_base:
        raise ValueError(f"cached compare has no merge base: {where}")
    return assemble_unified_diff(compare), merge_base, compare_sha256


def review_diff(cache_dir: Path, reviewed_head_sha: str) -> Tuple[str, str, str, Path]:
    compare, path = load_review_compare(cache_dir, reviewed_head_sha)
    diff, merge_base, sha = diff_from_compare(compare, sha256_file(path), where=path)
    return diff, merge_base, sha, path


class CompareSource(Protocol):
    def review_diff(self, reviewed_head_sha: str) -> Tuple[str, str, str]:
        """`(diff, merge base, compare sha256)`; raises ValueError when there is no compare."""


class DirectoryCompares:
    """Compares from a flat cache directory, found by head sha -- the v2 cache's layout."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)

    def review_diff(self, reviewed_head_sha: str) -> Tuple[str, str, str]:
        diff, merge_base, sha, _path = review_diff(self.cache_dir, reviewed_head_sha)
        return diff, merge_base, sha
