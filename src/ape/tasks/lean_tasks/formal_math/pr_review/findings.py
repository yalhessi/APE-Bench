"""Shared PR review finding taxonomy and compatibility helpers."""

from __future__ import annotations

import re
from typing import Any, Iterable, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator


REVIEW_FINDING_CATEGORIES: tuple[str, ...] = (
    "correctness",
    "requirements_scope",
    "integration_compatibility",
    "robustness_performance",
    "tests_ci",
    "documentation_metadata",
    "readability_maintainability",
)

LEGACY_ISSUE_TAG_TO_FINDING_CATEGORY: dict[str, str] = {
    "semantic_incorrectness": "correctness",
    "requirement_mismatch": "requirements_scope",
    "scope_control_violation": "requirements_scope",
    "library_integration_issue": "integration_compatibility",
    "deprecated_api_usage": "integration_compatibility",
    "proof_fragility": "robustness_performance",
    "performance_regression": "robustness_performance",
    "insufficient_tests": "tests_ci",
    "insufficient_documentation": "documentation_metadata",
    "style_or_readability": "readability_maintainability",
}

AI_GENERATED_PR_LABEL = "llm_generated"
AI_GENERATED_PR_GITHUB_LABEL = "llm-generated"


def normalize_issue_tag(tag: str) -> str:
    """Normalize legacy issue tags for deterministic compatibility handling."""
    normalized = str(tag or "").strip().lower()
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)
    return normalized


def normalize_review_category(category: str) -> str:
    """Normalize finding categories for deterministic scoring."""
    normalized = str(category or "").strip().lower()
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)
    return normalized


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        normalized = str(item or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


class ReviewFinding(BaseModel):
    """Structured review finding used by PR review tasks and datasets."""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(..., description="Canonical review finding category")
    summary: str = Field(default="", description="Short human-readable summary of the finding")

    @model_validator(mode="before")
    @classmethod
    def _coerce_input(cls, data: Any) -> Any:
        if isinstance(data, ReviewFinding):
            return data.model_dump(mode="json")
        if isinstance(data, str):
            return {"category": data, "summary": ""}
        return data

    @model_validator(mode="after")
    def _normalize_fields(self) -> "ReviewFinding":
        self.category = normalize_review_category(self.category)
        self.summary = str(self.summary or "").strip()
        return self


def coerce_review_findings(value: Any) -> list[ReviewFinding]:
    """Parse findings from strings, dicts, or already-validated models."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"Expected a list of review findings, got {type(value).__name__}")

    findings: list[ReviewFinding] = []
    for item in value:
        finding = ReviewFinding.model_validate(item)
        if finding.category:
            findings.append(finding)
    return findings


def normalize_review_categories(categories: Sequence[str]) -> list[str]:
    """Normalize and deduplicate category names while preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for category in categories:
        normalized = normalize_review_category(category)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def extract_review_categories(findings: Sequence[ReviewFinding | dict[str, Any] | str]) -> list[str]:
    """Extract unique normalized categories from structured findings."""
    return normalize_review_categories(
        [finding.category for finding in coerce_review_findings(list(findings))]
    )


def legacy_issue_tags_to_review_findings(tags: Sequence[str]) -> list[ReviewFinding]:
    """Map legacy issue tags into the new review finding categories."""
    findings: list[ReviewFinding] = []
    for tag in tags:
        legacy_tag = normalize_issue_tag(tag)
        category = LEGACY_ISSUE_TAG_TO_FINDING_CATEGORY.get(legacy_tag)
        if not category:
            continue
        findings.append(ReviewFinding(category=category))
    return findings


def review_findings_to_json(findings: Sequence[ReviewFinding | dict[str, Any] | str]) -> list[dict[str, str]]:
    """Serialize findings into stable JSON-compatible dicts."""
    return [finding.model_dump(mode="json") for finding in coerce_review_findings(list(findings))]
