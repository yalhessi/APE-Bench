"""Review-time unified diffs from immutable cached compare responses."""

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from .io import sha256_file


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


def review_diff(cache_dir: Path, reviewed_head_sha: str) -> Tuple[str, str, str, Path]:
    compare, path = load_review_compare(cache_dir, reviewed_head_sha)
    merge_base = str(compare.get("merge_base_sha") or "").strip()
    if not merge_base:
        raise ValueError(f"cached compare has no merge base: {path}")
    return assemble_unified_diff(compare), merge_base, sha256_file(path), path
