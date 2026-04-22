"""Structural scoring helpers for PR split tasks."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

from ape.tasks.base import EvaluationResult

from .models import PRSplitSubmission


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator


def _is_dependency_acyclic(chunk_map: Dict[str, list[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> bool:
        if node in visited:
            return True
        if node in visiting:
            return False
        visiting.add(node)
        for neighbor in chunk_map.get(node, []):
            if not dfs(neighbor):
                return False
        visiting.remove(node)
        visited.add(node)
        return True

    return all(dfs(node) for node in chunk_map)


def evaluate_split_submission(
    *,
    submission: PRSplitSubmission,
    all_unit_ids: Iterable[str],
) -> Tuple[EvaluationResult, Dict[str, object], Dict[str, float]]:
    """Score a structurally valid split submission."""

    all_units = list(all_unit_ids)
    all_unit_set = set(all_units)
    selected_units = [unit_id for chunk in submission.chunks for unit_id in chunk.selected_unit_ids]
    selected_unit_set = set(selected_units)
    overlap_count = max(0, len(selected_units) - len(selected_unit_set))
    chunk_dependency_map = {chunk.chunk_id: list(chunk.depends_on) for chunk in submission.chunks}
    dependency_acyclic = _is_dependency_acyclic(chunk_dependency_map)

    custom_metrics = {
        "split_declared": 1.0 if submission.should_split else 0.0,
        "chunk_count": float(len(submission.chunks)),
        "coverage_rate": _safe_rate(len(selected_unit_set & all_unit_set), len(all_unit_set)),
        "overlap_rate": _safe_rate(overlap_count, len(selected_units)) if selected_units else 0.0,
        "dependency_acyclic": 1.0 if dependency_acyclic else 0.0,
        "chunk_review_valid_rate": 1.0,
    }

    split_data: Dict[str, object] = {
        "predicted": submission.model_dump(mode="json"),
        "ground_truth": None,
        "metrics": custom_metrics,
        "notes": "Structural-only scoring for v1 standalone PR split tasks.",
    }
    return (
        EvaluationResult(
            success=True,
            score=1.0,
            message="PR split plan submitted and structurally validated.",
            metrics=split_data,
        ),
        split_data,
        custom_metrics,
    )
