"""Build physically isolated review-episode inputs.

The legacy adapter is a bootstrap and parity path only. It reads an explicit allowlist from v2 and
never receives `gold` or `validation` objects through its internal projection.
"""

import shlex
from typing import Any, Dict, List

from .io import canonical_json_bytes, sha256_bytes
from .schema import ReviewEpisodeInput, VisibleText


LEGACY_EPISODE_ADAPTER_VERSION = "legacy_adapter_v1"


def _strip_git_prefix(path: str) -> str:
    path = path.strip()
    return path[2:] if path.startswith(("a/", "b/")) else path


def _is_dev_null(path: str) -> bool:
    return _strip_git_prefix(path) in {"/dev/null", "dev/null"}


def changed_files_from_diff(diff: str) -> List[str]:
    """Return paths in diff order, including files deleted by the PR."""
    paths: List[str] = []
    seen = set()
    for line in (diff or "").splitlines():
        if not line.startswith("diff --git "):
            continue
        try:
            fields = shlex.split(line)
        except ValueError as exc:
            raise ValueError(f"invalid diff header: {line!r}") from exc
        if len(fields) < 4:
            raise ValueError(f"invalid diff header: {line!r}")
        old_path, new_path = fields[-2], fields[-1]
        selected = old_path if _is_dev_null(new_path) else new_path
        selected = _strip_git_prefix(selected)
        if selected and not _is_dev_null(selected) and selected not in seen:
            paths.append(selected)
            seen.add(selected)
    return paths


def _visible_text(text: Any, *, post_edit_risk: bool = False) -> VisibleText:
    value = str(text or "").strip()
    if post_edit_risk:
        return VisibleText(
            text=None,
            provenance="legacy_post_edit_risk_omitted",
            omission_reason="legacy source cannot prove the description predates review",
        )
    if not value:
        return VisibleText(text="", provenance="absent")
    return VisibleText(text=value, provenance="legacy_unverified")


def project_legacy_record(record: Dict[str, Any], *, round_index: int = 1) -> ReviewEpisodeInput:
    """Project a v2 record through an allowlist into `episode1`.

    This function intentionally never examines `gold`, `validation`, or `slices`. The resulting byte
    representation is therefore invariant to poisoning or removing those fields.
    """
    input_block = record.get("input") or {}
    repo = str(record.get("repo") or "").strip()
    pr_number = int(record["pr_number"])
    base_sha = str(input_block.get("base_sha") or "").strip()
    head_sha = str(input_block.get("head_sha") or "").strip()
    diff = str(input_block.get("diff") or "")
    if not (repo and base_sha and head_sha and diff.strip()):
        raise ValueError(f"PR {pr_number}: legacy record lacks repo/base/head/review-time diff")

    projection = {
        "repo": repo,
        "pr_number": pr_number,
        "round_index": round_index,
        "title": input_block.get("title") or "",
        "description": input_block.get("description") or "",
        "description_maybe_post_edited": bool(
            input_block.get("description_maybe_post_edited", False)
        ),
        "base_sha": base_sha,
        "head_sha": head_sha,
        "diff": diff,
    }
    source_hash = sha256_bytes(canonical_json_bytes(projection))
    episode_id = f"{repo}:{pr_number}:round{round_index}:{head_sha}"
    return ReviewEpisodeInput(
        episode_id=episode_id,
        repo=repo,
        pr_number=pr_number,
        round_index=round_index,
        title=_visible_text(input_block.get("title")),
        description=_visible_text(
            input_block.get("description"),
            post_edit_risk=bool(input_block.get("description_maybe_post_edited", False)),
        ),
        base_sha=base_sha,
        reviewed_head_sha=head_sha,
        diff=diff,
        changed_files=changed_files_from_diff(diff),
        patch_sha256=sha256_bytes(diff.encode("utf-8")),
        source_projection_sha256=source_hash,
    )
