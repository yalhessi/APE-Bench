"""Pure scoring helpers for PR review tasks."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Set, Tuple

from ape.tasks.base import EvaluationResult

from .findings import (
    REVIEW_FINDING_CATEGORIES,
    coerce_review_findings,
    extract_review_categories,
    normalize_review_categories,
    normalize_review_category,
    review_findings_to_json,
)
from .models import PRReviewEvaluationSpec, PRReviewSubmission


def _set_metrics(predicted: Set[str], gold: Set[str]) -> Tuple[float, float, float]:
    if not predicted and not gold:
        return 1.0, 1.0, 1.0
    if not predicted:
        return 0.0, 0.0, 0.0

    intersection_size = len(predicted & gold)
    precision = intersection_size / len(predicted) if predicted else 0.0
    recall = 1.0 if not gold else intersection_size / len(gold)
    if precision + recall == 0.0:
        f1 = 0.0
    else:
        f1 = (2.0 * precision * recall) / (precision + recall)
    return precision, recall, f1


def _finding_has_code_anchor(finding) -> bool:
    evidence = finding.evidence
    return bool(evidence.diff_locations or evidence.referenced_files or evidence.referenced_declarations)


def _finding_has_path_anchor(finding) -> bool:
    evidence = finding.evidence
    return bool(
        evidence.diff_locations
        or evidence.referenced_files
        or any(declaration.file_path for declaration in evidence.referenced_declarations)
    )


def _finding_has_guide_citation(finding) -> bool:
    return bool(finding.evidence.guide_citations)


def _finding_repo_paths(finding) -> Set[str]:
    repo_paths: set[str] = set()
    repo_paths.update(
        location.file_path
        for location in finding.evidence.diff_locations
        if location.file_path
    )
    repo_paths.update(
        file_path
        for file_path in finding.evidence.referenced_files
        if file_path
    )
    repo_paths.update(
        declaration.file_path
        for declaration in finding.evidence.referenced_declarations
        if declaration.file_path
    )
    return repo_paths


def _finding_trace_coverage_rate(findings, inspected_repo_paths: Set[str]) -> float:
    if not findings:
        return 1.0

    covered_count = 0
    for finding in findings:
        if _finding_repo_paths(finding) & inspected_repo_paths:
            covered_count += 1
    return covered_count / len(findings)


def _location_file_paths(findings) -> Set[str]:
    location_paths: set[str] = set()
    for finding in findings:
        location_paths.update(
            location.file_path
            for location in finding.evidence.diff_locations
            if location.file_path
        )
    return location_paths


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator


def evaluate_review_submission(
    *,
    submission: PRReviewSubmission,
    evaluation: Optional[PRReviewEvaluationSpec],
    task_config: Any,
    read_skill_relative_paths: Optional[Sequence[str]] = None,
    tool_trace_payload: Optional[Dict[str, Any]] = None,
) -> Tuple[EvaluationResult, Dict[str, Any], Optional[Dict[str, float]]]:
    """Score a normalized PR-review submission against optional ground truth."""

    normalized_blocking = coerce_review_findings(submission.blocking_findings or [])
    normalized_advisory = coerce_review_findings(submission.advisory_findings or [])
    normalized_findings = normalized_blocking + normalized_advisory
    blocking_categories = extract_review_categories(normalized_blocking)
    advisory_categories = extract_review_categories(normalized_advisory)
    normalized_guide_topics = list(submission.guide_evidence_topics or [])
    tool_trace_payload = tool_trace_payload or {}
    tool_trace_summary = dict(tool_trace_payload.get("summary") or {})
    tool_trace_records = list(tool_trace_payload.get("records") or [])
    allowed_categories = set(
        normalize_review_categories(
            list(getattr(task_config, "allowed_finding_categories", None) or REVIEW_FINDING_CATEGORIES)
        )
    )

    unknown_categories = sorted(set(blocking_categories + advisory_categories) - allowed_categories)
    if unknown_categories and bool(getattr(task_config, "strict_category_validation", False)):
        return (
            EvaluationResult(
                success=False,
                score=0.0,
                message=(
                    "Unknown finding categories under strict_category_validation: "
                    + ", ".join(f"`{normalize_review_category(category)}`" for category in unknown_categories)
                ),
            ),
            {},
            None,
        )

    predicted = {
        "merge_ready": submission.merge_ready,
        "needs_human_review": submission.needs_human_review,
        "decision_confidence": submission.decision_confidence,
        "blocking_findings": review_findings_to_json(normalized_blocking),
        "advisory_findings": review_findings_to_json(normalized_advisory),
        "blocking_categories": blocking_categories,
        "advisory_categories": advisory_categories,
        "guide_evidence_topics": normalized_guide_topics,
        "read_skill_relative_paths": list(read_skill_relative_paths or []),
        "tool_trace_summary": tool_trace_summary,
        "tool_trace_records": tool_trace_records,
        "unknown_categories": unknown_categories,
        "feedback_length": len(submission.feedback or ""),
    }

    if evaluation is None:
        review_data = {
            "predicted": predicted,
            "ground_truth": None,
            "metrics": None,
            "notes": "No evaluation attachment provided; score defaults to 1.0 on valid submission.",
        }
        return (
            EvaluationResult(
                success=True,
                score=1.0,
                message="Review submitted (no evaluation attachment provided for scoring).",
                metrics=review_data,
            ),
            review_data,
            None,
        )

    ground_truth = evaluation.ground_truth
    gold_blocking_findings = coerce_review_findings(ground_truth.blocking_findings)
    gold_advisory_findings = coerce_review_findings(ground_truth.advisory_findings)
    gold_findings = gold_blocking_findings + gold_advisory_findings
    gold_blocking = set(extract_review_categories(gold_blocking_findings))
    gold_advisory = set(extract_review_categories(gold_advisory_findings))

    blocking_precision, blocking_recall, blocking_f1 = _set_metrics(
        set(blocking_categories),
        gold_blocking,
    )
    advisory_precision, advisory_recall, advisory_f1 = _set_metrics(
        set(advisory_categories),
        gold_advisory,
    )

    decision_accuracy = 1.0 if submission.merge_ready == ground_truth.merge_ready else 0.0
    handoff_accuracy = 1.0 if submission.needs_human_review == ground_truth.needs_human_review else 0.0
    weighted_score = (
        float(getattr(task_config, "decision_weight", 0.65)) * decision_accuracy
        + float(getattr(task_config, "blocking_issue_weight", 0.25)) * blocking_f1
        + float(getattr(task_config, "advisory_issue_weight", 0.10)) * advisory_f1
    )

    false_approve = bool(not ground_truth.merge_ready and submission.merge_ready)
    if false_approve:
        weighted_score = min(weighted_score, float(getattr(task_config, "severe_false_approve_max_score", 0.20)))
    weighted_score = max(0.0, min(1.0, weighted_score))

    tp = 1.0 if submission.merge_ready and ground_truth.merge_ready else 0.0
    tn = 1.0 if (not submission.merge_ready) and (not ground_truth.merge_ready) else 0.0
    fp = 1.0 if submission.merge_ready and (not ground_truth.merge_ready) else 0.0
    fn = 1.0 if (not submission.merge_ready) and ground_truth.merge_ready else 0.0

    inspected_repo_paths = set(tool_trace_summary.get("inspected_repo_paths") or [])
    evidence_code_anchor_rate = _safe_rate(
        sum(1 for finding in normalized_findings if _finding_has_code_anchor(finding)),
        len(normalized_findings),
    )
    evidence_path_anchor_rate = _safe_rate(
        sum(1 for finding in normalized_findings if _finding_has_path_anchor(finding)),
        len(normalized_findings),
    )
    guide_citation_rate = _safe_rate(
        sum(1 for finding in normalized_findings if _finding_has_guide_citation(finding)),
        len(normalized_findings),
    )
    evidence_trace_coverage_rate = _finding_trace_coverage_rate(normalized_findings, inspected_repo_paths)

    location_file_precision, location_file_recall, location_file_f1 = _set_metrics(
        _location_file_paths(normalized_findings),
        _location_file_paths(gold_findings),
    )

    decision_confidence_provided = 1.0 if submission.decision_confidence is not None else 0.0
    decision_brier_score = None
    decision_calibration_error = None
    if submission.decision_confidence is not None:
        decision_brier_score = float((submission.decision_confidence - decision_accuracy) ** 2)
        decision_calibration_error = float(abs(submission.decision_confidence - decision_accuracy))

    selective_coverage = 0.0 if submission.needs_human_review else 1.0
    selective_decision_risk = 0.0 if submission.needs_human_review else (1.0 - decision_accuracy)

    custom_metrics = {
        "decision_accuracy": decision_accuracy,
        "handoff_accuracy": handoff_accuracy,
        "blocking_precision": blocking_precision,
        "blocking_recall": blocking_recall,
        "blocking_category_f1": blocking_f1,
        "advisory_precision": advisory_precision,
        "advisory_recall": advisory_recall,
        "advisory_category_f1": advisory_f1,
        "blocking_issue_precision": blocking_precision,
        "blocking_issue_recall": blocking_recall,
        "blocking_issue_f1": blocking_f1,
        "advisory_issue_precision": advisory_precision,
        "advisory_issue_recall": advisory_recall,
        "advisory_issue_f1": advisory_f1,
        "review_quality_score": weighted_score,
        "evidence_code_anchor_rate": evidence_code_anchor_rate,
        "evidence_path_anchor_rate": evidence_path_anchor_rate,
        "guide_citation_rate": guide_citation_rate,
        "evidence_trace_coverage_rate": evidence_trace_coverage_rate,
        "location_file_precision": location_file_precision,
        "location_file_recall": location_file_recall,
        "location_file_f1": location_file_f1,
        "decision_confidence_provided": decision_confidence_provided,
        "selective_coverage": selective_coverage,
        "selective_decision_risk": selective_decision_risk,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }
    if decision_brier_score is not None:
        custom_metrics["decision_brier_score"] = decision_brier_score
    if decision_calibration_error is not None:
        custom_metrics["decision_calibration_error"] = decision_calibration_error

    review_metrics = {
        "decision_accuracy": decision_accuracy,
        "handoff": {
            "predicted": submission.needs_human_review,
            "ground_truth": ground_truth.needs_human_review,
            "accuracy": handoff_accuracy,
        },
        "blocking_category": {
            "precision": blocking_precision,
            "recall": blocking_recall,
            "f1": blocking_f1,
        },
        "advisory_category": {
            "precision": advisory_precision,
            "recall": advisory_recall,
            "f1": advisory_f1,
        },
        "false_approve": false_approve,
        "weights": {
            "decision_weight": float(getattr(task_config, "decision_weight", 0.65)),
            "blocking_issue_weight": float(getattr(task_config, "blocking_issue_weight", 0.25)),
            "advisory_issue_weight": float(getattr(task_config, "advisory_issue_weight", 0.10)),
        },
        "location_file": {
            "precision": location_file_precision,
            "recall": location_file_recall,
            "f1": location_file_f1,
        },
        "evidence": {
            "code_anchor_rate": evidence_code_anchor_rate,
            "path_anchor_rate": evidence_path_anchor_rate,
            "guide_citation_rate": guide_citation_rate,
            "trace_coverage_rate": evidence_trace_coverage_rate,
        },
        "calibration": {
            "decision_confidence": submission.decision_confidence,
            "provided": bool(submission.decision_confidence is not None),
            "brier_score": decision_brier_score,
            "absolute_error": decision_calibration_error,
        },
        "selective_behavior": {
            "coverage": selective_coverage,
            "decision_risk": selective_decision_risk,
        },
        "review_quality_score": weighted_score,
    }

    review_data = {
        "predicted": predicted,
        "ground_truth": {
            "merge_ready": ground_truth.merge_ready,
            "needs_human_review": ground_truth.needs_human_review,
            "decision_confidence": ground_truth.decision_confidence,
            "blocking_findings": review_findings_to_json(gold_blocking_findings),
            "advisory_findings": review_findings_to_json(gold_advisory_findings),
            "blocking_categories": sorted(gold_blocking),
            "advisory_categories": sorted(gold_advisory),
            "rationale": ground_truth.rationale,
            "label_source": evaluation.label_source,
        },
        "metrics": review_metrics,
    }

    summary = (
        f"Decision match={bool(decision_accuracy)}; "
        f"blocking F1={blocking_f1:.3f}; advisory F1={advisory_f1:.3f}; "
        f"score={weighted_score:.3f}"
    )
    if false_approve:
        summary += " (false-approve penalty applied)"

    return (
        EvaluationResult(
            success=True,
            score=weighted_score,
            message=summary,
            metrics=review_data,
        ),
        review_data,
        custom_metrics,
    )
