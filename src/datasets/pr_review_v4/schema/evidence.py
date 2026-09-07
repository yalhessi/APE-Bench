"""Warrants: what was checked, what it showed, and which tier of evidence that is."""

from typing import Dict, List, Literal, Optional, get_args
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import StrictModel


class OpportunityEvidenceArtifact(StrictModel):
    """Review-time source or check result supporting a production opportunity."""

    schema_version: Literal["opportunity-evidence-artifact1"] = (
        "opportunity-evidence-artifact1"
    )
    artifact_id: str
    investigation_id: str
    episode_id: str
    pr_number: int
    kind: Literal[
        "reviewed_code",
        "repository_declaration",
        "retrieval_trace",
        "applicability_check",
        "negative_control",
        "semantic_subject",
        "naming_population",
        "name_collision",
        "pr_relation",
        "composition_plan",
        "dependency_reduction",
        # Added with the deterministic lint and repository-policy checkers. Extending this
        # literal is backward compatible: every previously written artifact keeps a valid
        # `kind`, so frozen evidence still loads and re-hashes identically.
        "lint_report",
        "policy_report",
    ]
    source_ref: str
    content: str
    snapshot_sha: str
    source_sha256: str


class AdjudicationVerificationArtifact(StrictModel):
    """Run-level mechanical evidence created while adjudicating one opportunity."""

    schema_version: Literal["adjudication-verification-artifact1"] = (
        "adjudication-verification-artifact1"
    )
    artifact_id: str
    opportunity_id: str
    kind: Literal["lean_compile"]
    success: bool
    source_evidence_artifact_ids: List[str] = Field(min_length=1)
    edit_sha256: str
    content: str
    snapshot_sha: str
    source_sha256: str


class ResidualCandidateVerificationArtifact(StrictModel):
    """Mechanical evidence produced by the residual candidate submission gate."""

    schema_version: Literal["residual-candidate-verification1"] = (
        "residual-candidate-verification1"
    )
    artifact_id: str
    work_unit_id: str
    candidate_ordinal: int = Field(ge=0)
    stage: Literal["baseline", "proposed_edit"]
    kind: Literal["lean_compile"] = "lean_compile"
    success: bool
    path: str
    edit_sha256: Optional[str] = None
    content: str
    snapshot_sha: str
    source_sha256: str


class EvidenceArtifact(StrictModel):
    schema_version: Literal["evidence-artifact1"] = "evidence-artifact1"
    artifact_id: str
    candidate_id: str
    collector: str
    kind: Literal[
        "target_context", "search_result", "compile_result", "policy_text", "policy_result",
        "precedent",
        #: An issue-kind verifier's finding: the operator that can check this kind of claim
        #: either confirmed or refuted it. An abstention produces no artifact — "we did not
        #: check" and "we checked and found nothing" must not look alike.
        "verification",
    ]
    polarity: Literal["support", "counterevidence", "neutral"]
    content: str
    source_ref: str
    occurred_at: Optional[str] = None
    source_sha256: str


class EvidenceAssertion(StrictModel):
    schema_version: Literal["evidence-assertion1"] = "evidence-assertion1"
    assertion_id: str
    candidate_id: str
    artifact_ids: List[str]
    assertion_scope: Literal["claim", "proposed_edit", "context"] = "claim"
    polarity: Literal["supports", "contradicts", "inconclusive"]
    claim: str
    producer: Literal["collector", "human"]
    source_sha256: str


class EvidencePacket(StrictModel):
    schema_version: Literal["evidence-packet1"] = "evidence-packet1"
    packet_id: str
    candidate_id: str
    artifact_ids: List[str]
    assertion_ids: List[str]
    requested_collectors: List[str]
    completed_collectors: List[str]
    terminal_failures: Dict[str, str] = Field(default_factory=dict)
    status: Literal["supported", "contradicted", "inconclusive", "incomplete"]
    source_sha256: str


class SelectedFinding(StrictModel):
    schema_version: Literal["finding1"] = "finding1"
    finding_id: str
    candidate_id: str
    packet_id: str
    pr_number: int
    change_ids: List[str]
    concern_label: str
    severity: Literal["blocking", "advisory"]
    claim: str
    suggested_fix: Optional[str] = None
    evidence_assertion_ids: List[str]
    rank_key: str
    source_sha256: str


#: Evidence strength as a fixed ordinal, never a count.
#:
#: The existing support score is `10.0 or 5.0 + len(evidence_artifact_ids)/100` — it treats
#: "more artifacts" as "stronger", and its two call sites disagree about the base. Counting
#: artifacts rewards a checker that cites its inputs twice; ranking tiers rewards a checker
#: that actually verified something.
EVIDENCE_TIERS = ("model_assertion", "lexical_rule", "repository_measurement", "verified_compile")


EvidenceTier = Literal[
    "model_assertion", "lexical_rule", "repository_measurement", "verified_compile"
]


def evidence_rank(tier: str) -> int:
    return EVIDENCE_TIERS.index(tier)
