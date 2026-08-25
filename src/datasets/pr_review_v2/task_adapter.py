"""
Adapter between the v2 gold records (dataset layer) and the lean_pr_review_v2
task (execution layer).

This is the seam: it builds task input from a gold record (so the existing
scaffolds can drive an agentic, tool-using review of the reviewed PR state) and
converts the task's result back into the same `PredictionRecord` the diff_only
runner emits — so D1/D2/D3 score workspace-mode and diff_only on identical
footing. The dataset layer never imports task internals beyond the data/result
classes; the task never scores.
"""

from typing import Any, Dict, List, Optional

from ape.tasks.lean_tasks import LeanPRReviewV2Data
from ape.tasks.models import WorkspaceInfo

from .predictions import PredictedAnchor, PredictedFinding, PredictionRecord
from .schema import PRReviewV2Record

DEFAULT_MATHLIB_URL = "https://github.com/leanprover-community/mathlib4.git"


def _changed_files(record: PRReviewV2Record) -> List[str]:
    """Changed paths for the patch overlay — parsed from δ₀ itself (`+++ b/<path>`),
    which is authoritative, with comment/Δ anchors as a fallback."""
    paths = set()
    for line in (record.input.diff or "").splitlines():
        if line.startswith("+++ b/"):
            p = line[len("+++ b/"):].strip()
            if p and p != "/dev/null":
                paths.add(p)
    if not paths:
        for comment in record.gold.comments:
            if comment.anchor and comment.anchor.path:
                paths.add(comment.anchor.path)
        for hunk in (record.gold.delta_near or []) + (record.gold.delta_total or []):
            paths.add(hunk.path)
    return sorted(paths)


def build_task_data(
    record: PRReviewV2Record,
    *,
    task_type: str = "lean_pr_review_v2",
    repo_url: str = DEFAULT_MATHLIB_URL,
    default_target: str = "Mathlib",
    toolchain: Optional[str] = None,
) -> LeanPRReviewV2Data:
    """Gold record → review task data.

    `task_type` selects which review task runs (holistic lean_pr_review_v2, or a
    checker lean_pr_review_dup / lean_pr_review_gen) — all share this data shape.
    The reviewed state is materialized as the MERGE BASE (base_sha, a real master
    commit that is reliably cached/buildable) with δ₀ applied — not by resolving
    the fork head — mirroring the legacy task. head_sha is kept for reference.
    """
    return LeanPRReviewV2Data(
        task_type=task_type,
        task_id=f"{task_type}_{record.pr_number}",
        pr_number=record.pr_number,
        pr_title=record.input.title,
        pr_description=record.input.description,
        diff=record.input.diff or "",
        changed_files=_changed_files(record),
        snapshot_head_sha=record.input.head_sha,
        snapshot_base_sha=record.input.base_sha,
        target_workspace=WorkspaceInfo(
            name="target",
            commit_hash=record.input.base_sha,
            repo_url=repo_url,
            default_target=default_target,
            toolchain=toolchain,
        ),
    )


def result_to_prediction(
    result: Dict[str, Any] | Any,
    *,
    model: str,
    mode: str = "workspace",
    pr_number: Optional[int] = None,
) -> PredictionRecord:
    """LeanPRReviewV2Result (or its dict dump) → PredictionRecord for D1/D2/D3.

    Accepts either the pydantic result or a plain dict so callers can pass a
    deserialized task result without importing task classes. A failed/aborted run
    returns a generic BaseTaskResult lacking pr_number/findings, so all review
    fields are read defensively and `pr_number` falls back to the caller's value.
    """
    data = result if isinstance(result, dict) else result.model_dump(mode="json")
    resolved_pr = data.get("pr_number", pr_number)
    if resolved_pr is None:
        raise ValueError("result_to_prediction: pr_number missing from result and no fallback given")
    findings: List[PredictedFinding] = []
    for raw in data.get("findings") or []:
        anchor_raw = raw.get("anchor")
        anchor = None
        if anchor_raw and anchor_raw.get("path"):
            anchor = PredictedAnchor(
                path=anchor_raw["path"],
                line_start=anchor_raw.get("line_start"),
                line_end=anchor_raw.get("line_end"),
            )
        findings.append(PredictedFinding(
            anchor=anchor,
            severity=raw.get("severity", "advisory"),
            claim=raw.get("claim", ""),
            suggested_fix=raw.get("suggested_fix"),
            evidence=raw.get("evidence"),
            verified=raw.get("verified"),
            confidence=raw.get("confidence"),
        ))
    return PredictionRecord(
        pr_number=resolved_pr,
        model=model,
        mode=mode,  # type: ignore[arg-type]
        merge_ready_as_is=data.get("merge_ready_as_is"),
        confidence=data.get("confidence"),
        findings=findings,
        # The agent's free-text summary (e.g. the instantiate checker's per-item SKIP reasons) —
        # previously dropped here, which forced skip-reason analysis into run-dir spelunking.
        review_message=str(data.get("review_message") or ""),
        parse_ok=True,
    )
