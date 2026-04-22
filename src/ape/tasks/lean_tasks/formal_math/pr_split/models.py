"""Typed models for standalone Lean PR split tasks."""

from __future__ import annotations

import re
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ape.tasks.base import BaseTaskResult

from ..pr_shared.models import PRBaseTaskData, PRBenchmarkContext, PRSnapshot
from ..pr_review.findings import ReviewFinding, coerce_review_findings


_SAFE_CHUNK_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = str(item or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


class ChunkReview(BaseModel):
    """Standalone review payload for one proposed sub-PR."""

    model_config = ConfigDict(extra="forbid")

    merge_ready: bool = Field(..., description="Whether this hypothetical sub-PR is ready to merge")
    needs_human_review: bool = Field(
        default=False,
        description="Whether the chunk should be handed off to a human reviewer",
    )
    decision_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional calibrated confidence in the chunk-level judgment",
    )
    blocking_findings: List[ReviewFinding] = Field(default_factory=list, description="Blocking findings for the chunk")
    advisory_findings: List[ReviewFinding] = Field(default_factory=list, description="Advisory findings for the chunk")
    feedback: str = Field(default="", description="Standalone reviewer feedback for the chunk")

    @model_validator(mode="after")
    def _normalize_fields(self) -> "ChunkReview":
        self.blocking_findings = coerce_review_findings(self.blocking_findings)
        self.advisory_findings = coerce_review_findings(self.advisory_findings)
        self.feedback = str(self.feedback or "").strip()
        return self


class PRSplitChunk(BaseModel):
    """One coherent proposed sub-PR."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(..., description="Stable chunk identifier unique within the submission")
    title: str = Field(..., description="Proposed PR title for the chunk")
    summary: str = Field(..., description="Short explanation of the chunk boundary and intent")
    selected_unit_ids: List[str] = Field(default_factory=list, description="Canonical diff-unit IDs assigned here")
    depends_on: List[str] = Field(default_factory=list, description="Chunk IDs that must land first")
    review: ChunkReview = Field(..., description="Standalone review for the hypothetical sub-PR")

    @model_validator(mode="after")
    def _normalize_fields(self) -> "PRSplitChunk":
        self.chunk_id = str(self.chunk_id or "").strip()
        self.title = str(self.title or "").strip()
        self.summary = str(self.summary or "").strip()
        self.selected_unit_ids = _dedupe_preserve_order(list(self.selected_unit_ids or []))
        self.depends_on = _dedupe_preserve_order(list(self.depends_on or []))
        if self.chunk_id and not _SAFE_CHUNK_ID_RE.match(self.chunk_id):
            raise ValueError("chunk_id may only contain letters, numbers, '.', '_' or '-'")
        return self


class PRSplitSubmission(BaseModel):
    """Normalized `submit_result` payload for PR splitting."""

    model_config = ConfigDict(extra="forbid")

    should_split: bool = Field(..., description="Whether the PR should be decomposed into smaller sub-PRs")
    rationale: str = Field(..., description="High-level rationale for splitting or not splitting")
    chunks: List[PRSplitChunk] = Field(default_factory=list, description="Proposed sub-PRs in dependency-aware order")

    @model_validator(mode="after")
    def _normalize_fields(self) -> "PRSplitSubmission":
        self.rationale = str(self.rationale or "").strip()
        self.chunks = list(self.chunks or [])
        return self


class PRSplitData(PRBaseTaskData):
    """Data model for Lean PR split tasks."""

    task_type: Literal["lean_pr_split"] = Field(
        default="lean_pr_split",
        description="Task type identifier",
    )
    snapshot: PRSnapshot = Field(..., description="Splittable PR snapshot")
    benchmark_context: Optional[PRBenchmarkContext] = Field(
        default=None,
        description="Optional benchmark-only metadata",
    )


class SkilledPRSplitData(PRSplitData):
    """Data model for skill-targeted Lean PR split tasks."""

    task_type: Literal["skilled_pr_split"] = Field(
        default="skilled_pr_split",
        description="Task type identifier",
    )


class PRSplitResult(BaseTaskResult):
    """Result model for standalone PR split tasks."""

    model_config = ConfigDict()

    should_split: bool = Field(..., description="Whether the PR should be decomposed")
    rationale: str = Field(..., description="High-level explanation for the decision")
    chunks: List[PRSplitChunk] = Field(default_factory=list, description="Predicted decomposition plan")
    split_data: Dict[str, object] = Field(default_factory=dict, description="Detailed split evaluation data")
    workspace_artifacts: Dict[str, str] = Field(
        default_factory=dict,
        description="Scratch-local artifact paths written for the submitted split and chunk diffs",
    )
