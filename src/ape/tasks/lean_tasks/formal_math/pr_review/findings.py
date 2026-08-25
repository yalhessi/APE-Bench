"""Shared PR review finding taxonomy and compatibility helpers."""

from __future__ import annotations

import re
from typing import Any, Iterable, Literal, Sequence

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

AI_GENERATED_PR_LABEL = "llm_generated"
AI_GENERATED_PR_GITHUB_LABEL = "llm-generated"


def normalize_review_key(value: str) -> str:
    """Normalize review-related keys such as categories or topic identifiers."""
    normalized = str(value or "").strip().lower()
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)
    return normalized


def normalize_review_category(category: str) -> str:
    """Normalize finding categories for deterministic scoring."""
    return normalize_review_key(category)


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


class ReviewDiffLocation(BaseModel):
    """Location in the diff that supports a review finding."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(..., description="Repo-root relative file path in the diff")
    line_start: int = Field(..., ge=1, description="1-based starting line number on the chosen diff side")
    line_end: int = Field(..., ge=1, description="1-based ending line number on the chosen diff side")
    diff_side: Literal["old", "new"] = Field(..., description="Which side of the diff the line span refers to")

    @model_validator(mode="after")
    def _normalize_fields(self) -> "ReviewDiffLocation":
        self.file_path = str(self.file_path or "").strip()
        if self.line_end < self.line_start:
            raise ValueError("line_end must be greater than or equal to line_start")
        return self


class ReviewDeclarationReference(BaseModel):
    """Declaration reference used as structured evidence for a review finding."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Declaration name referenced by the finding")
    file_path: str | None = Field(default=None, description="Optional repo-root relative file path")
    line_start: int | None = Field(default=None, ge=1, description="Optional 1-based starting line number")
    line_end: int | None = Field(default=None, ge=1, description="Optional 1-based ending line number")

    @model_validator(mode="after")
    def _normalize_fields(self) -> "ReviewDeclarationReference":
        self.name = str(self.name or "").strip()
        self.file_path = str(self.file_path or "").strip() or None
        if self.line_end is not None and self.line_start is None:
            raise ValueError("line_start must be provided when line_end is provided")
        if self.line_start is not None and self.line_end is not None and self.line_end < self.line_start:
            raise ValueError("line_end must be greater than or equal to line_start")
        return self


class ReviewGuideCitation(BaseModel):
    """Guide citation used as structured evidence for a review finding."""

    model_config = ConfigDict(extra="forbid")

    topic: str = Field(..., description="Normalized guide topic key supporting the finding")
    relative_path: str = Field(..., description="Relative path within the managed review skill bundle")

    @model_validator(mode="after")
    def _normalize_fields(self) -> "ReviewGuideCitation":
        self.topic = normalize_review_key(self.topic)
        self.relative_path = str(self.relative_path or "").strip()
        return self


class ReviewFindingEvidence(BaseModel):
    """Structured evidence bundle attached to one review finding."""

    model_config = ConfigDict(extra="forbid")

    diff_locations: list[ReviewDiffLocation] = Field(
        default_factory=list,
        description="Diff locations that directly support the finding",
    )
    referenced_files: list[str] = Field(
        default_factory=list,
        description="Additional repo-root relative files inspected for the finding",
    )
    referenced_declarations: list[ReviewDeclarationReference] = Field(
        default_factory=list,
        description="Declarations inspected to support the finding",
    )
    guide_citations: list[ReviewGuideCitation] = Field(
        default_factory=list,
        description="Managed-guide citations used to support policy or style judgments",
    )

    @model_validator(mode="after")
    def _normalize_fields(self) -> "ReviewFindingEvidence":
        self.referenced_files = dedupe_preserve_order(self.referenced_files)
        return self


class ReviewFinding(BaseModel):
    """Structured review finding used by PR review tasks and datasets."""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(..., description="Canonical review finding category")
    summary: str = Field(default="", description="Short human-readable summary of the finding")
    evidence: ReviewFindingEvidence = Field(..., description="Structured evidence supporting the finding")

    @model_validator(mode="before")
    @classmethod
    def _coerce_input(cls, data: Any) -> Any:
        if isinstance(data, ReviewFinding):
            return data.model_dump(mode="json")
        if isinstance(data, str):
            return {"category": data, "summary": "", "evidence": {}}
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


def categories_to_review_findings(categories: Sequence[str]) -> list[ReviewFinding]:
    """Build minimal findings from category names."""
    findings: list[ReviewFinding] = []
    for category in categories:
        normalized_category = normalize_review_category(category)
        if not normalized_category:
            continue
        findings.append(
            ReviewFinding(
                category=normalized_category,
                evidence=ReviewFindingEvidence(),
            )
        )
    return findings


def review_findings_to_json(findings: Sequence[ReviewFinding | dict[str, Any] | str]) -> list[dict[str, Any]]:
    """Serialize findings into stable JSON-compatible dicts."""
    return [finding.model_dump(mode="json") for finding in coerce_review_findings(list(findings))]
