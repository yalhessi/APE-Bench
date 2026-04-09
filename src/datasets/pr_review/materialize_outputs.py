"""Materialize aggregate and slice-specific PR review benchmark outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from ape.tasks.lean_tasks.formal_math.pr_review.findings import normalize_review_category

from .create_skill_variants import create_skill_variants


PRIMARY_CASES: tuple[str, ...] = ("easy", "major_feedback", "abandoned")
OVERLAY_CASES: tuple[str, ...] = ("ai_authored",)


def _write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def _slice_output_path(aggregate_output: Path, slice_name: str) -> Path:
    return aggregate_output.with_name(f"{aggregate_output.stem}__{slice_name}{aggregate_output.suffix}")


def materialize_hybrid_outputs(
    records: list[Dict[str, Any]],
    aggregate_output: Path,
    *,
    skill_bundle: str,
    write_aggregate: bool = True,
    create_variants: bool = True,
) -> dict[str, Path]:
    outputs: dict[str, Path] = {"aggregate": aggregate_output}
    if write_aggregate:
        _write_jsonl(aggregate_output, records)

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

    for slice_name, slice_rows in slice_records.items():
        slice_output = _slice_output_path(aggregate_output, slice_name)
        _write_jsonl(slice_output, slice_rows)
        outputs[slice_name] = slice_output

    if create_variants:
        baseline_output, skill_output = create_skill_variants(
            aggregate_output,
            skill_bundle=skill_bundle,
        )
        outputs["aggregate_baseline"] = baseline_output
        outputs["aggregate_with_skills"] = skill_output

        for slice_name in (*PRIMARY_CASES, *OVERLAY_CASES):
            baseline_output, skill_output = create_skill_variants(
                outputs[slice_name],
                skill_bundle=skill_bundle,
            )
            outputs[f"{slice_name}_baseline"] = baseline_output
            outputs[f"{slice_name}_with_skills"] = skill_output

    return outputs
