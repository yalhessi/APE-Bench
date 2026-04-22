"""Materialize aggregate and slice-specific PR review and PR split outputs."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable

from ape.tasks.lean_tasks.formal_math.pr_review.findings import normalize_review_category

from .create_skill_variants import create_skill_variants


PRIMARY_CASES: tuple[str, ...] = ("easy", "major_feedback", "abandoned")
OVERLAY_CASES: tuple[str, ...] = ("ai_authored",)
SPLIT_OVERLAY_CASES: tuple[str, ...] = ("split_candidate", "maintainer_requested_split")


def _write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def _slice_output_path(aggregate_output: Path, slice_name: str) -> Path:
    return aggregate_output.with_name(f"{aggregate_output.stem}__{slice_name}{aggregate_output.suffix}")


def _build_slice_records(
    records: list[Dict[str, Any]],
    *,
    extra_slice_predicates: Dict[str, Callable[[Dict[str, Any]], bool]] | None = None,
) -> dict[str, list[Dict[str, Any]]]:
    slice_records: dict[str, list[Dict[str, Any]]] = {}
    for primary_case in PRIMARY_CASES:
        slice_records[primary_case] = [
            record
            for record in records
            if normalize_review_category((record.get("benchmark_context") or {}).get("primary_case")) == primary_case
        ]
    slice_records["ai_authored"] = [
        record
        for record in records
        if normalize_review_category((record.get("benchmark_context") or {}).get("authoring_mode")) == "ai_authored"
    ]
    for slice_name, predicate in (extra_slice_predicates or {}).items():
        slice_records[slice_name] = [record for record in records if predicate(record)]
    return slice_records


def _materialize_task_outputs(
    records: list[Dict[str, Any]],
    aggregate_output: Path,
    *,
    skill_bundle: str,
    baseline_task_type: str,
    skill_task_type: str,
    write_aggregate: bool = True,
    create_variants: bool = True,
    extra_slice_predicates: Dict[str, Callable[[Dict[str, Any]], bool]] | None = None,
) -> dict[str, Path]:
    outputs: dict[str, Path] = {"aggregate": aggregate_output}
    if write_aggregate:
        _write_jsonl(aggregate_output, records)

    slice_records = _build_slice_records(records, extra_slice_predicates=extra_slice_predicates)
    for slice_name, slice_rows in slice_records.items():
        slice_output = _slice_output_path(aggregate_output, slice_name)
        _write_jsonl(slice_output, slice_rows)
        outputs[slice_name] = slice_output

    if create_variants:
        baseline_output, skill_output = create_skill_variants(
            aggregate_output,
            skill_bundle=skill_bundle,
            baseline_task_type=baseline_task_type,
            skill_task_type=skill_task_type,
        )
        outputs["aggregate_baseline"] = baseline_output
        outputs["aggregate_with_skills"] = skill_output

        for slice_name in slice_records:
            baseline_output, skill_output = create_skill_variants(
                outputs[slice_name],
                skill_bundle=skill_bundle,
                baseline_task_type=baseline_task_type,
                skill_task_type=skill_task_type,
            )
            outputs[f"{slice_name}_baseline"] = baseline_output
            outputs[f"{slice_name}_with_skills"] = skill_output

    return outputs


def materialize_hybrid_outputs(
    records: list[Dict[str, Any]],
    aggregate_output: Path,
    *,
    skill_bundle: str,
    write_aggregate: bool = True,
    create_variants: bool = True,
) -> dict[str, Path]:
    return _materialize_task_outputs(
        records,
        aggregate_output,
        skill_bundle=skill_bundle,
        baseline_task_type="lean_pr_review",
        skill_task_type="skilled_pr_review",
        write_aggregate=write_aggregate,
        create_variants=create_variants,
    )


def build_split_task_records(
    review_records: list[Dict[str, Any]],
    *,
    task_type: str = "lean_pr_split",
) -> list[Dict[str, Any]]:
    """Convert PR review snapshot records into standalone PR split task records."""

    split_records: list[Dict[str, Any]] = []
    for record in review_records:
        updated = copy.deepcopy(record)
        source_task_id = str(updated.get("task_id") or "pr_task")
        source_task_type = str(updated.get("task_type") or "lean_pr_review")
        metadata = dict(updated.get("metadata") or {})
        metadata["source_task_type"] = source_task_type
        metadata["source_task_id"] = source_task_id
        updated["metadata"] = metadata
        updated["task_type"] = task_type
        updated["evaluation"] = None
        updated.pop("global_index", None)
        if source_task_id.startswith("mathlib_pr_review_"):
            updated["task_id"] = "mathlib_pr_split_" + source_task_id[len("mathlib_pr_review_"):]
        else:
            updated["task_id"] = f"{source_task_id}__pr_split"
        split_records.append(updated)
    return split_records


def materialize_split_outputs(
    records: list[Dict[str, Any]],
    aggregate_output: Path,
    *,
    skill_bundle: str,
    write_aggregate: bool = True,
    create_variants: bool = True,
) -> dict[str, Path]:
    return _materialize_task_outputs(
        records,
        aggregate_output,
        skill_bundle=skill_bundle,
        baseline_task_type="lean_pr_split",
        skill_task_type="skilled_pr_split",
        write_aggregate=write_aggregate,
        create_variants=create_variants,
        extra_slice_predicates={
            "split_candidate": lambda record: bool((record.get("benchmark_context") or {}).get("split_candidate")),
            "maintainer_requested_split": lambda record: bool(
                (record.get("benchmark_context") or {}).get("maintainer_requested_split")
            ),
        },
    )
