"""
Create paired baseline/skill variants for Mathlib PR review JSONL files.

Usage examples:
  python src/datasets/pr_review/create_skill_variants.py \
    --input inputs/proof_pr_review/mathlib_pr_review_10tasks.jsonl
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


def _build_variant_record(
    record: dict[str, Any],
    *,
    variant: str,
    skill_bundle: str,
    task_type: str | None = None,
) -> dict[str, Any]:
    updated = copy.deepcopy(record)
    base_task_id = str(updated.get("task_id", "task"))
    metadata = dict(updated.get("metadata") or {})
    metadata["paired_variant"] = variant
    metadata["paired_base_task_id"] = base_task_id
    metadata["skill_bundle"] = skill_bundle
    updated["metadata"] = metadata
    updated["task_id"] = f"{base_task_id}__{variant}"
    if task_type is not None:
        updated["task_type"] = task_type
    return updated


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def create_skill_variants(
    input_path: Path,
    *,
    baseline_output: Path | None = None,
    skill_output: Path | None = None,
    skill_bundle: str = "mathlib-pr-review",
    baseline_task_type: str | None = "lean_pr_review",
    skill_task_type: str | None = "skilled_pr_review",
) -> tuple[Path, Path]:
    records = _read_jsonl(input_path)

    if baseline_output is None:
        baseline_output = input_path.with_name(f"{input_path.stem}_baseline{input_path.suffix}")
    if skill_output is None:
        skill_output = input_path.with_name(f"{input_path.stem}_with_skills{input_path.suffix}")

    baseline_records = [
        _build_variant_record(
            record,
            variant="baseline",
            skill_bundle=skill_bundle,
            task_type=baseline_task_type,
        )
        for record in records
    ]
    skill_records = [
        _build_variant_record(
            record,
            variant="with_skills",
            skill_bundle=skill_bundle,
            task_type=skill_task_type,
        )
        for record in records
    ]

    _write_jsonl(baseline_output, baseline_records)
    _write_jsonl(skill_output, skill_records)
    return baseline_output, skill_output


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create paired baseline/skill variants for PR review JSONL inputs.",
    )
    parser.add_argument("--input", type=Path, required=True, help="Source PR review JSONL file")
    parser.add_argument("--baseline-output", type=Path, default=None, help="Optional output path for baseline variant")
    parser.add_argument("--skill-output", type=Path, default=None, help="Optional output path for skill variant")
    parser.add_argument(
        "--skill-bundle",
        type=str,
        default="mathlib-pr-review",
        help="Label stored in metadata.skill_bundle",
    )
    parser.add_argument(
        "--baseline-task-type",
        type=str,
        default="lean_pr_review",
        help="Task type to write into the baseline records",
    )
    parser.add_argument(
        "--skill-task-type",
        type=str,
        default="skilled_pr_review",
        help="Task type to write into the skill-targeted records",
    )
    return parser


def main() -> None:
    parser = create_argument_parser()
    args = parser.parse_args()
    baseline_output, skill_output = create_skill_variants(
        args.input,
        baseline_output=args.baseline_output,
        skill_output=args.skill_output,
        skill_bundle=args.skill_bundle,
        baseline_task_type=args.baseline_task_type,
        skill_task_type=args.skill_task_type,
    )
    print(baseline_output)
    print(skill_output)


if __name__ == "__main__":
    main()
