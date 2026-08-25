"""
Gold record schema for the first-round review task.

Implements §5 of docs/research/review-task-spec.md: one JSONL row per PR, holding
the input contract (d, δ₀, workspace pins), the gold object G (verdict, comments
with linkage, change-sets, outcome), and the validation timeline.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = "pr_review_v2/0.1"

Verdict = Literal["APPROVED", "CHANGES_REQUESTED", "COMMENT_ONLY"]
CommentKind = Literal["inline", "review_body", "issue_comment"]
LinkConfidence = Literal["resolved_thread", "line_overlap", "none"]
H0Resolution = Literal["review_commit_id", "pushed_before_t1"]


class SliceFlags(BaseModel):
    """Population tags used for slicing; never used to filter the headline funnel."""

    merged: bool
    author_is_maintainer: bool = False
    ai_authored: bool = False
    multi_reviewer: bool = False
    automated_sweep: bool = False


class Anchor(BaseModel):
    path: str
    line: Optional[int] = None
    original_line: Optional[int] = None
    side: Optional[str] = None


class GoldComment(BaseModel):
    id: str
    author: str
    kind: CommentKind
    submitted_at: str
    body: str
    anchor: Optional[Anchor] = None
    thread_id: Optional[str] = None
    thread_resolved: Optional[bool] = None
    linked_hunks: List[str] = Field(default_factory=list, description="Hunk ids in gold.delta_near")
    link_confidence: LinkConfidence = "none"
    # Filled by the Step-3 rubric pass (docs/research/stratum-rubric.md).
    # V1-V4 = verifiability strata; P = process/meta, Q = pure question — both
    # non-findings, excluded from stratum statistics but kept for completeness.
    stratum: Optional[Literal["V1", "V2", "V3", "V4", "P", "Q"]] = None
    severity: Optional[Literal["blocking", "advisory"]] = None


class DeltaHunk(BaseModel):
    """One hunk of the patch-level change-set Δ (spec §3.6).

    `op` records which side of the patch comparison the hunk came from:
    `added_in_revision` = present in the later patch only (new/changed content),
    `removed_in_revision` = present in the review-time patch only (content the
    revision dropped or rewrote).
    """

    hunk_id: str
    path: str
    op: Literal["added_in_revision", "removed_in_revision"]
    new_start: Optional[int] = None
    new_lines: Optional[int] = None
    old_start: Optional[int] = None
    old_lines: Optional[int] = None
    patch: str


class Outcome(BaseModel):
    merged: bool
    merged_at: Optional[str] = None
    closed_at: Optional[str] = None
    rounds: Optional[int] = None
    merge_signal: Optional[str] = None


class InputBlock(BaseModel):
    title: str
    description: str
    description_maybe_post_edited: bool = False
    base_sha: str
    head_sha: str = Field(description="h₀, the head the first reviewer saw")
    h0_resolution: H0Resolution
    diff: Optional[str] = Field(default=None, description="δ₀ unified diff; hydrated from compare API")


class GoldBlock(BaseModel):
    verdict: Verdict
    comments: List[GoldComment]
    delta_near: Optional[List[DeltaHunk]] = None
    delta_total: Optional[List[DeltaHunk]] = None
    outcome: Outcome


class ValidationBlock(BaseModel):
    label_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    process_signals: List[Dict[str, Any]] = Field(default_factory=list)
    force_push_before_t1: bool = False
    roster_association_disagreements: int = 0
    h1_sha: Optional[str] = None
    final_head_sha: Optional[str] = None
    t1: Optional[str] = None
    t_push: Optional[str] = None
    hydration_error: Optional[str] = None


class PRReviewV2Record(BaseModel):
    schema_version: str = SCHEMA_VERSION
    repo: str
    pr_number: int
    slices: SliceFlags
    input: InputBlock
    gold: GoldBlock
    validation: ValidationBlock


class SkipReason(BaseModel):
    """A PR dropped by the eligibility funnel (spec §3.8); counted in the funnel report."""

    pr_number: int
    stage: str
    reason: str
