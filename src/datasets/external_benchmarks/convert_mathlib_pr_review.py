#!/usr/bin/env python3
"""
Convert APE judgment records into PR review tasks.

This creates `lean_pr_review` tasks with structured ground truth labels so models can
be evaluated on merge-readiness review quality.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.tasks.lean_tasks.formal_math.pr_review.findings import (
    categories_to_review_findings,
    normalize_review_category,
    review_findings_to_json,
)

try:
    from ..taxonomy.lean_task_taxonomy import annotate_record_metadata
except Exception:  # pragma: no cover - direct script execution fallback
    try:
        import sys
        sys.path.append(str(Path(__file__).resolve().parents[2]))
        sys.path.append(str(Path(__file__).resolve().parents[1]))
        from taxonomy.lean_task_taxonomy import annotate_record_metadata
    except Exception:
        def annotate_record_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
            """Fallback taxonomy annotator when APE dependencies are unavailable."""
            metadata = record.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}
            evaluation = record.get("evaluation") or {}
            ground_truth = evaluation.get("ground_truth") or {}
            blocking_items = ground_truth.get("blocking_findings") or []
            advisory_items = ground_truth.get("advisory_findings") or []
            metadata["taxonomy"] = {
                "task_type": "lean_pr_review",
                "dataset": metadata.get("dataset"),
                "task_family": "pr_review",
                "edit_regime": "pr_review",
                "primary_archetype": "merge_readiness_judgment",
                "has_ground_truth": bool(ground_truth),
                "merge_ready_ground_truth": ground_truth.get("merge_ready"),
                "blocking_issue_count": len(blocking_items),
                "advisory_issue_count": len(advisory_items),
            }
            record["metadata"] = metadata
            return record


BLOCKING_CATEGORY_BY_DIMENSION = {
    "semantic_correctness": "correctness",
    "requirement_alignment": "requirements_scope",
    "scope_control": "requirements_scope",
}

ADVISORY_CATEGORY_BY_DIMENSION = {
    "semantic_correctness": "robustness_performance",
    "requirement_alignment": "documentation_metadata",
    "scope_control": "readability_maintainability",
}


def dedupe_categories(categories: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for category in categories:
        normalized = normalize_review_category(category)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def derive_finding_categories(record: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Map human annotation ratings into blocking/advisory finding categories."""
    human = (record.get("metadata") or {}).get("human_evaluation") or {}

    blocking: List[str] = []
    advisory: List[str] = []
    for dimension in ("semantic_correctness", "requirement_alignment", "scope_control"):
        rating = (human.get(dimension) or "").strip().lower()
        if rating == "unacceptable":
            blocking.append(BLOCKING_CATEGORY_BY_DIMENSION[dimension])
        elif rating == "good":
            advisory.append(ADVISORY_CATEGORY_BY_DIMENSION[dimension])

    return dedupe_categories(blocking), dedupe_categories(advisory)


def build_pr_title(record: Dict[str, Any]) -> str:
    filename = record.get("filename") or "Unknown.lean"
    task_description = (record.get("task_description") or "").strip()
    first_line = task_description.splitlines()[0] if task_description else "Mathlib PR update"
    first_line = re.sub(r"\s+", " ", first_line).strip()
    return f"{Path(filename).name}: {first_line[:120]}"


def convert_record(record: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Convert one `lean_judgment` record to one `lean_pr_review` record."""
    if record.get("task_type") != "lean_judgment":
        raise ValueError(f"Expected task_type=lean_judgment, got {record.get('task_type')!r}")

    target_workspace = record.get("target_workspace")
    if not isinstance(target_workspace, dict) or not target_workspace.get("commit_hash"):
        raise ValueError("Missing target_workspace.commit_hash in source record")

    blocking_categories, advisory_categories = derive_finding_categories(record)
    merge_ready = bool(record.get("judgement_ground_truth"))

    filename = record.get("filename")
    changed_files = [filename] if filename else []

    source_metadata = record.get("metadata") or {}
    original_task_id = source_metadata.get("original_task_id") or record.get("task_id") or f"source_{index}"

    pr_review_record = {
        "task_type": "lean_pr_review",
        "task_id": f"pr_review_{index:04d}_{re.sub(r'[^a-zA-Z0-9_]+', '_', str(original_task_id))}",
        "snapshot": {
            "pr_number": None,
            "pr_url": None,
            "pr_title": build_pr_title(record),
            "pr_author": None,
            "pr_description": record.get("task_description") or "",
            "pr_dependencies": [],
            "pr_diff": record.get("gold_diff") or "",
            "changed_files": changed_files,
            "snapshot_type": "converted_judgment",
            "snapshot_at": None,
            "snapshot_base_sha": target_workspace.get("commit_hash"),
            "snapshot_head_sha": None,
            "review_state": None,
            "review_focus": (
                "Assess merge readiness under Mathlib standards. "
                "Prioritize semantic correctness, requirement alignment, and scope control."
            ),
            "pr_head": None,
            "conversation": {
                "author_input": [],
                "reviewer_feedback": [],
            },
        },
        "evaluation": {
            "ground_truth": {
                "merge_ready": merge_ready,
                "needs_human_review": False,
                "decision_confidence": None,
                "blocking_findings": review_findings_to_json(categories_to_review_findings(blocking_categories)),
                "advisory_findings": review_findings_to_json(categories_to_review_findings(advisory_categories)),
                "rationale": (source_metadata.get("human_evaluation") or {}).get("comment"),
            },
            "label_source": "converted_from_judgment_annotation",
        },
        "benchmark_context": None,
        "target_workspace": target_workspace,
        "metadata": {
            "dataset": "ape_pr_review",
            "source": "converted_from_ape_judge_benchmark",
            "source_task_id": record.get("task_id"),
            "original_task_id": original_task_id,
            "annotation_date": source_metadata.get("annotation_date"),
            "human_evaluation": source_metadata.get("human_evaluation"),
            "llm_judge_baseline": source_metadata.get("llm_judge_baseline"),
        },
    }

    annotate_record_metadata(pr_review_record)
    return pr_review_record


def convert_file(input_file: Path, output_file: Path, max_records: Optional[int] = None) -> int:
    """Convert a JSONL file to PR review format."""
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    converted = 0

    with input_file.open("r", encoding="utf-8") as infile, output_file.open("w", encoding="utf-8") as outfile:
        for idx, line in enumerate(infile):
            line = line.strip()
            if not line:
                continue
            if max_records is not None and converted >= max_records:
                break

            record = json.loads(line)
            pr_review_record = convert_record(record, index=converted)
            outfile.write(json.dumps(pr_review_record, ensure_ascii=False) + "\n")
            converted += 1

    return converted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert APE judgment benchmark to PR review benchmark format.")
    parser.add_argument(
        "--input_file",
        type=Path,
        default=Path("inputs/ape_judge_benchmark/ape_judge_benchmark.jsonl"),
        help="Input JSONL path (default: inputs/ape_judge_benchmark/ape_judge_benchmark.jsonl)",
    )
    parser.add_argument(
        "--output_file",
        type=Path,
        default=Path("inputs/proof_pr_review/proof_pr_review_benchmark.jsonl"),
        help="Output JSONL path (default: inputs/proof_pr_review/proof_pr_review_benchmark.jsonl)",
    )
    parser.add_argument("--max_records", type=int, default=None, help="Optional max records to convert")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    converted = convert_file(args.input_file, args.output_file, args.max_records)
    print(f"Converted {converted} records to {args.output_file}")


if __name__ == "__main__":
    main()
