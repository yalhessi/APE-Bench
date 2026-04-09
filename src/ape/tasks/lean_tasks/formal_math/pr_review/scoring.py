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


def evaluate_review_submission(
    *,
    submission: PRReviewSubmission,
    evaluation: Optional[PRReviewEvaluationSpec],
    task_config: Any,
    read_skill_relative_paths: Optional[Sequence[str]] = None,
) -> Tuple[EvaluationResult, Dict[str, Any], Optional[Dict[str, float]]]:
    """Score a normalized PR-review submission against optional ground truth."""

    normalized_blocking = coerce_review_findings(submission.blocking_findings or [])
    normalized_advisory = coerce_review_findings(submission.advisory_findings or [])
    blocking_categories = extract_review_categories(normalized_blocking)
    advisory_categories = extract_review_categories(normalized_advisory)
    normalized_guide_topics = list(submission.guide_evidence_topics or [])
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
        "blocking_findings": review_findings_to_json(normalized_blocking),
        "advisory_findings": review_findings_to_json(normalized_advisory),
        "blocking_categories": blocking_categories,
        "advisory_categories": advisory_categories,
        "guide_evidence_topics": normalized_guide_topics,
        "read_skill_relative_paths": list(read_skill_relative_paths or []),
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

    custom_metrics = {
        "decision_accuracy": decision_accuracy,
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
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }

    review_metrics = {
        "decision_accuracy": decision_accuracy,
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
        "review_quality_score": weighted_score,
    }

    review_data = {
        "predicted": predicted,
        "ground_truth": {
            "merge_ready": ground_truth.merge_ready,
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
