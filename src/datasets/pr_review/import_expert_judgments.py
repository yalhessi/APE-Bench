"""
Import expert-labeled PR review snapshots into task JSONL.

Usage examples:
  python -m src.datasets.pr_review.import_expert_judgments \
    --input examples/proof_pr_review/expert_judgments_template.jsonl \
    --output inputs/proof_pr_review/codex_pr_review_calibration.jsonl

  python -m src.datasets.pr_review.import_expert_judgments \
    --input annotations.json \
    --output inputs/proof_pr_review/codex_pr_review_eval.jsonl \
    --task-id-prefix codex-pr-review-eval \
    --create-skill-variants \
    --skill-bundle codex-pr-review
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ape.tasks.lean_tasks.formal_math.pr_review.findings import (
    ReviewFinding,
    normalize_review_category,
)
from ape.utils.config_loader import deep_merge
from ape.utils.logging import create_logger

from .collector import PRReviewDataCollector
from .config import PRReviewDatasetConfig
from .create_skill_variants import create_skill_variants
from .materialize_outputs import PRIMARY_CASES, OVERLAY_CASES, materialize_hybrid_outputs

DEFAULT_TASK_ID_PREFIX = "codex-pr-review"
DEFAULT_METADATA_SOURCE = "expert_judgment_import"


def _parse_github_pr_url(pr_url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into owner, repo, and PR number."""
    normalized_url = str(pr_url or "").strip()
    if not normalized_url:
        raise ValueError("pr_url must be non-empty")

    parsed = urlparse(normalized_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("pr_url must start with http:// or https://")
    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise ValueError("pr_url must point to github.com")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 4 or parts[2] != "pull":
        raise ValueError("pr_url must have the form https://github.com/<owner>/<repo>/pull/<number>")

    repo_owner, repo_name, _, pr_number_text = parts[:4]
    try:
        pr_number = int(pr_number_text)
    except ValueError as exc:
        raise ValueError("pr_url must end with a numeric pull request number") from exc

    return repo_owner, repo_name, pr_number


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            normalized = str(item or "").strip()
            if normalized:
                out.append(normalized)
        return out
    raise TypeError(f"Expected a string or list of strings, got {type(value).__name__}")


def _sanitize_task_id_prefix(prefix: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(prefix or "").strip()).strip("-")
    return normalized or DEFAULT_TASK_ID_PREFIX


def _default_task_id(prefix: str, pr_number: int, snapshot_head_sha: str) -> str:
    safe_prefix = _sanitize_task_id_prefix(prefix)
    short_sha = str(snapshot_head_sha or "").strip()[:12]
    return f"{safe_prefix}_{pr_number}_{short_sha}"


class ExpertGroundTruth(BaseModel):
    """Expert-provided review labels."""

    model_config = ConfigDict(extra="forbid")

    merge_ready: bool
    needs_human_review: bool = False
    decision_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    blocking_findings: list[ReviewFinding] = Field(default_factory=list)
    advisory_findings: list[ReviewFinding] = Field(default_factory=list)
    rationale: Optional[str] = None

class ExpertJudgmentAnnotation(BaseModel):
    """Annotation input for one expert-labeled PR snapshot."""

    model_config = ConfigDict(extra="forbid")

    pr_url: Optional[str] = None
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    pr_number: Optional[int] = None
    snapshot_head_sha: Optional[str] = None

    merge_ready: Optional[bool] = None
    needs_human_review: bool = False
    decision_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    blocking_findings: list[ReviewFinding] = Field(default_factory=list)
    advisory_findings: list[ReviewFinding] = Field(default_factory=list)
    rationale: Optional[str] = None
    ground_truth: Optional[ExpertGroundTruth] = None

    task_id: Optional[str] = None
    task_type: Optional[str] = None
    review_focus: Optional[str] = None
    split: Optional[str] = None
    primary_case: Optional[str] = None
    case_flags: list[str] = Field(default_factory=list)
    authoring_mode: Optional[str] = None

    annotators: list[str] = Field(default_factory=list)
    adjudicated: Optional[bool] = None
    label_source: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _lift_aliases_and_ground_truth(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        if not normalized.get("snapshot_head_sha"):
            for alias in ("commit", "head_sha", "snapshot_commit"):
                candidate = str(normalized.get(alias) or "").strip()
                if candidate:
                    normalized["snapshot_head_sha"] = candidate
                    break
        for alias in ("commit", "head_sha", "snapshot_commit"):
            normalized.pop(alias, None)

        ground_truth = normalized.get("ground_truth")
        if isinstance(ground_truth, dict):
            for field_name in (
                "merge_ready",
                "needs_human_review",
                "decision_confidence",
                "blocking_findings",
                "advisory_findings",
                "rationale",
            ):
                if normalized.get(field_name) is None and ground_truth.get(field_name) is not None:
                    normalized[field_name] = ground_truth.get(field_name)

        normalized["annotators"] = _normalize_string_list(normalized.get("annotators"))
        normalized["case_flags"] = [normalize_review_category(item) for item in _normalize_string_list(normalized.get("case_flags"))]
        if normalized.get("primary_case") is not None:
            normalized["primary_case"] = normalize_review_category(normalized.get("primary_case"))
        if normalized.get("authoring_mode") is not None:
            normalized["authoring_mode"] = normalize_review_category(normalized.get("authoring_mode"))
        if not normalized.get("label_source"):
            normalized["label_source"] = "expert_adjudicated" if normalized.get("adjudicated") else "expert_annotation"
        return normalized

    @model_validator(mode="after")
    def _validate_and_fill_repo_info(self) -> "ExpertJudgmentAnnotation":
        if self.pr_url:
            repo_owner, repo_name, pr_number = _parse_github_pr_url(self.pr_url)
            if self.repo_owner and self.repo_owner != repo_owner:
                raise ValueError("repo_owner does not match pr_url")
            if self.repo_name and self.repo_name != repo_name:
                raise ValueError("repo_name does not match pr_url")
            if self.pr_number is not None and self.pr_number != pr_number:
                raise ValueError("pr_number does not match pr_url")
            self.repo_owner = repo_owner
            self.repo_name = repo_name
            self.pr_number = pr_number

        missing = [
            name
            for name, value in (
                ("repo_owner", self.repo_owner),
                ("repo_name", self.repo_name),
                ("pr_number", self.pr_number),
                ("snapshot_head_sha", self.snapshot_head_sha),
            )
            if value in {None, ""}
        ]
        if missing:
            raise ValueError("Missing required annotation fields: " + ", ".join(missing))

        if self.ground_truth is None:
            if self.merge_ready is None:
                raise ValueError("Missing required annotation field: merge_ready")
            self.ground_truth = ExpertGroundTruth(
                merge_ready=self.merge_ready,
                needs_human_review=self.needs_human_review,
                decision_confidence=self.decision_confidence,
                blocking_findings=self.blocking_findings,
                advisory_findings=self.advisory_findings,
                rationale=self.rationale,
            )

        if self.adjudicated and len({annotator for annotator in self.annotators if annotator}) < 2:
            raise ValueError("Adjudicated expert annotations require at least two annotators")
        return self


def _load_annotations(path: Path) -> list[ExpertJudgmentAnnotation]:
    if not path.exists():
        raise FileNotFoundError(f"Annotation file not found: {path}")

    suffix = path.suffix.lower()
    raw_records: list[dict[str, Any]] = []
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            raw_records = payload
        elif isinstance(payload, dict) and isinstance(payload.get("records"), list):
            raw_records = payload["records"]
        else:
            raise ValueError("JSON annotation file must contain a list or a {\"records\": [...]} object")
    else:
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} of {path}: {exc}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"Expected an object on line {line_number} of {path}")
            raw_records.append(payload)

    return [ExpertJudgmentAnnotation.model_validate(record) for record in raw_records]


def _merge_annotation_into_record(
    base_record: Dict[str, Any],
    annotation: ExpertJudgmentAnnotation,
    *,
    input_index: int,
    default_task_type: str,
    task_id_prefix: str,
) -> Dict[str, Any]:
    record = copy.deepcopy(base_record)

    builder_task_id = str(record.get("task_id") or "")
    builder_evaluation = copy.deepcopy(record.get("evaluation"))
    builder_ground_truth = copy.deepcopy((builder_evaluation or {}).get("ground_truth"))
    builder_label_source = copy.deepcopy((builder_evaluation or {}).get("label_source"))
    snapshot = record.get("snapshot") or {}
    if not isinstance(snapshot, dict):
        snapshot = {}
        record["snapshot"] = snapshot
    snapshot_head_sha = str(snapshot.get("snapshot_head_sha") or annotation.snapshot_head_sha or "")
    pr_number = int(snapshot.get("pr_number") or annotation.pr_number or 0)

    record["task_id"] = annotation.task_id or _default_task_id(task_id_prefix, pr_number, snapshot_head_sha)
    record["task_type"] = annotation.task_type or default_task_type
    if annotation.review_focus:
        snapshot["review_focus"] = annotation.review_focus

    existing_benchmark_context = record.get("benchmark_context") or {}
    if not isinstance(existing_benchmark_context, dict):
        existing_benchmark_context = {}

    merged_case_flags = _normalize_string_list(existing_benchmark_context.get("case_flags"))
    if annotation.case_flags:
        merged_case_flags = _normalize_string_list(merged_case_flags + annotation.case_flags)

    record["benchmark_context"] = {
        "primary_case": annotation.primary_case or existing_benchmark_context.get("primary_case"),
        "case_flags": merged_case_flags,
        "authoring_mode": annotation.authoring_mode or existing_benchmark_context.get("authoring_mode"),
        "final_pr_outcome": existing_benchmark_context.get("final_pr_outcome"),
        "maintainer_round_count": existing_benchmark_context.get("maintainer_round_count"),
        "maintainer_feedback_count": existing_benchmark_context.get("maintainer_feedback_count"),
        "changes_requested_count": existing_benchmark_context.get("changes_requested_count"),
        "selected_snapshot_kind": existing_benchmark_context.get("selected_snapshot_kind"),
        "source_labels": existing_benchmark_context.get("source_labels"),
        "round_index": existing_benchmark_context.get("round_index"),
        "round_window": existing_benchmark_context.get("round_window"),
    }
    record["evaluation"] = {
        "ground_truth": annotation.ground_truth.model_dump(mode="json"),
        "label_source": annotation.label_source,
    }

    metadata = copy.deepcopy(record.get("metadata") or {})
    metadata_updates: Dict[str, Any] = {
        "source": DEFAULT_METADATA_SOURCE,
        "expert_judgment": {
            "annotators": annotation.annotators,
            "adjudicated": annotation.adjudicated,
            "label_source": annotation.label_source,
            "notes": annotation.notes,
            "primary_case": annotation.primary_case,
            "case_flags": annotation.case_flags,
            "authoring_mode": annotation.authoring_mode,
        },
        "import_context": {
            "input_index": input_index,
            "builder_task_id": builder_task_id or None,
            "builder_ground_truth": builder_ground_truth,
            "builder_label_source": builder_label_source,
            "requested_snapshot_head_sha": annotation.snapshot_head_sha,
            "requested_pr_url": annotation.pr_url,
        },
    }
    if annotation.split:
        metadata_updates["split"] = annotation.split

    metadata = deep_merge(metadata, metadata_updates)
    metadata = deep_merge(metadata, annotation.metadata)
    record["metadata"] = metadata
    return record


def import_expert_judgments(
    input_path: Path,
    output_path: Path,
    *,
    default_task_type: str = "lean_pr_review",
    task_id_prefix: str = DEFAULT_TASK_ID_PREFIX,
    github_token: Optional[str] = None,
    timeout_seconds: float = 30.0,
    request_interval_seconds: float = 0.0,
    default_review_focus: Optional[str] = None,
    materialize_slice_outputs: bool = True,
    create_skill_variants_output: bool = False,
    skill_bundle: str = "codex-pr-review",
    baseline_output: Optional[Path] = None,
    skill_output: Optional[Path] = None,
    logger=None,
    collector_class=PRReviewDataCollector,
) -> list[Dict[str, Any]]:
    logger = logger or create_logger()
    annotations = _load_annotations(input_path)
    logger.info("Loaded %d expert annotation(s) from %s", len(annotations), input_path)

    collectors: dict[tuple[str, str], PRReviewDataCollector] = {}
    records: list[Dict[str, Any]] = []

    try:
        for input_index, annotation in enumerate(annotations, start=1):
            repo_key = (str(annotation.repo_owner), str(annotation.repo_name))
            collector = collectors.get(repo_key)
            if collector is None:
                collector = collector_class(
                    config=PRReviewDatasetConfig(
                        repo_owner=annotation.repo_owner,
                        repo_name=annotation.repo_name,
                        github_token=github_token,
                        timeout_seconds=timeout_seconds,
                        request_interval_seconds=request_interval_seconds,
                        review_focus=default_review_focus or PRReviewDatasetConfig().review_focus,
                    ),
                    logger=logger,
                )
                collectors[repo_key] = collector

            base_record = collector.build_live_pr_review_task_data(
                pr_number=int(annotation.pr_number),
                snapshot_head_sha=str(annotation.snapshot_head_sha),
                pr_url=annotation.pr_url,
            )
            final_record = _merge_annotation_into_record(
                base_record,
                annotation,
                input_index=input_index,
                default_task_type=default_task_type,
                task_id_prefix=task_id_prefix,
            )
            records.append(final_record)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False))
                handle.write("\n")

        if materialize_slice_outputs:
            materialize_hybrid_outputs(
                records,
                output_path,
                skill_bundle=skill_bundle,
                write_aggregate=False,
                create_variants=create_skill_variants_output and baseline_output is None and skill_output is None,
            )

        logger.info("Wrote %d record(s) to %s", len(records), output_path)

        if create_skill_variants_output and (baseline_output is not None or skill_output is not None):
            baseline_path, skill_path = create_skill_variants(
                output_path,
                baseline_output=baseline_output,
                skill_output=skill_output,
                skill_bundle=skill_bundle,
            )
            logger.info("Wrote baseline variant to %s", baseline_path)
            logger.info("Wrote skill variant to %s", skill_path)
            if materialize_slice_outputs:
                for slice_name in (*PRIMARY_CASES, *OVERLAY_CASES):
                    slice_path = output_path.with_name(f"{output_path.stem}__{slice_name}{output_path.suffix}")
                    create_skill_variants(
                        slice_path,
                        skill_bundle=skill_bundle,
                    )

        return records
    finally:
        for collector in collectors.values():
            collector.close()


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import expert-labeled PR review snapshots into task JSONL.",
    )
    parser.add_argument("--input", type=Path, required=True, help="Input annotation file (.json or .jsonl)")
    parser.add_argument("--output", type=Path, required=True, help="Output task JSONL file")
    parser.add_argument(
        "--default-task-type",
        type=str,
        default="lean_pr_review",
        help="Task type to write when an annotation does not override it",
    )
    parser.add_argument(
        "--task-id-prefix",
        type=str,
        default=DEFAULT_TASK_ID_PREFIX,
        help="Prefix for generated task_id values",
    )
    parser.add_argument("--github-token", type=str, default=None, help="Optional GitHub token override")
    parser.add_argument("--timeout-seconds", type=float, default=30.0, help="HTTP timeout for GitHub requests")
    parser.add_argument(
        "--request-interval-seconds",
        type=float,
        default=0.0,
        help="Optional sleep interval between GitHub API requests",
    )
    parser.add_argument(
        "--default-review-focus",
        type=str,
        default=None,
        help="Optional review_focus value used unless the annotation overrides it",
    )
    parser.add_argument(
        "--create-skill-variants",
        action="store_true",
        help="Also emit paired baseline/skill variants from the imported JSONL",
    )
    parser.add_argument(
        "--skill-bundle",
        type=str,
        default="codex-pr-review",
        help="Label written into metadata.skill_bundle when creating variants",
    )
    parser.add_argument(
        "--baseline-output",
        type=Path,
        default=None,
        help="Optional path for the baseline variant when --create-skill-variants is set",
    )
    parser.add_argument(
        "--skill-output",
        type=Path,
        default=None,
        help="Optional path for the skill variant when --create-skill-variants is set",
    )
    return parser


def main() -> Path:
    logger = create_logger()
    parser = create_argument_parser()
    args = parser.parse_args()

    import_expert_judgments(
        args.input,
        args.output,
        default_task_type=args.default_task_type,
        task_id_prefix=args.task_id_prefix,
        github_token=args.github_token,
        timeout_seconds=args.timeout_seconds,
        request_interval_seconds=args.request_interval_seconds,
        default_review_focus=args.default_review_focus,
        create_skill_variants_output=args.create_skill_variants,
        skill_bundle=args.skill_bundle,
        baseline_output=args.baseline_output,
        skill_output=args.skill_output,
        logger=logger,
    )
    return args.output


if __name__ == "__main__":
    output_path = main()
    print(output_path)
