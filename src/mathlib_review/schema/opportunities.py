"""The systematic-opportunity pipeline: methods, operators, norms and adjudication.

The largest block by count and the most self-contained -- only the v4 opportunity tooling
constructs or reads these.
"""

from typing import Dict, List, Literal, Optional, get_args
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import StrictModel
from .identity import ArtifactRef, ComponentKind, LifecycleFacet, SubjectKind


"""Versioned schemas for the PR Review v4 benchmark foundation."""


class ManualAgendaProbeTask(StrictModel):
    """One frozen specialist pass cloned from a stable candidate work unit."""

    schema_version: Literal["manual-agenda-probe-task1"] = "manual-agenda-probe-task1"
    probe_work_unit_id: str
    source_work_unit_id: str
    pass_id: Literal["statement_api", "proof", "relational"]
    investigation_kinds: List[str]
    source_sha256: str


OpportunityMethod = Literal[
    "naming_contrast",
    "canonical_api_search",
    "proof_compression",
    "intra_pr_composition",
    "repository_pattern",
    "family_consistency",
]


class MethodApplicability(StrictModel):
    subject_kinds: List[SubjectKind]
    lifecycles: List[LifecycleFacet]
    any_changed_components: List[ComponentKind]
    visibilities: List[Literal["public", "private", "local", "unknown"]] = Field(
        default_factory=lambda: ["public", "private", "local", "unknown"]
    )


class InvestigationMethod(StrictModel):
    """Versioned executable method definition, not prompt-only checklist prose."""

    schema_version: Literal["investigation-method1"] = "investigation-method1"
    method_id: str
    applies_when: MethodApplicability
    required_inputs: List[str]
    operators: List[str] = Field(min_length=1)
    max_opportunities: int = Field(ge=1)
    technical_checks: List[str] = Field(default_factory=list)
    norm_sources: List[str] = Field(default_factory=list)
    selection_policy: str
    source_sha256: str


class OpportunityTreatmentManifest(StrictModel):
    """Immutable production-safe treatment metadata over a frozen benchmark release."""

    schema_version: Literal["systematic-opportunity-treatment1"] = (
        "systematic-opportunity-treatment1"
    )
    treatment_id: str
    parent_dataset_manifest: ArtifactRef
    method_registry: ArtifactRef
    derived_artifacts: List[ArtifactRef]
    generator_versions: Dict[str, str]
    source_sha256: str


class InvestigationTask(StrictModel):
    """One scheduled method over a bounded set of review-time modifications."""

    schema_version: Literal["investigation-task1"] = "investigation-task1"
    investigation_id: str
    method_id: str
    work_unit_id: str
    episode_id: str
    pr_number: int
    modification_ids: List[str] = Field(min_length=1)
    primary_change_id: str
    related_change_ids: List[str] = Field(default_factory=list)
    expected_operators: List[str] = Field(min_length=1)
    method_registry_sha256: str
    source_sha256: str


class OperatorRun(StrictModel):
    """Auditable execution result for one deterministic or model-backed operator."""

    schema_version: Literal["operator-run1"] = "operator-run1"
    operator_run_id: str
    investigation_id: str
    operator: str
    status: Literal["completed", "failed", "unavailable"]
    query_sha256: Optional[str] = None
    artifact_ids: List[str] = Field(default_factory=list)
    result_count: int = Field(default=0, ge=0)
    failure_reason: Optional[str] = None
    source_sha256: str

    @model_validator(mode="after")
    def validate_failure_reason(self):
        if self.status in {"failed", "unavailable"} and not self.failure_reason:
            raise ValueError("failed or unavailable operator runs require a failure reason")
        if self.status == "completed" and self.failure_reason:
            raise ValueError("completed operator runs cannot carry a failure reason")
        return self


class ImplementationCapability(StrictModel):
    """One executable implementation of a broad method, scoped to explicit target shapes."""

    schema_version: Literal["implementation-capability1"] = "implementation-capability1"
    implementation_id: str
    method_id: str
    operator_version: str
    capability_predicate: str
    required_inputs: List[str]
    terminal_outputs: List[str] = Field(min_length=1)
    max_opportunities: int = Field(ge=1)
    source_sha256: str


class MethodExpressionContract(StrictModel):
    """Frozen target-independent mapping from a method to issue/transformation classes."""

    schema_version: Literal["method-expression-contract1"] = "method-expression-contract1"
    method_id: str
    issue_classes: List[str] = Field(min_length=1)
    transformation_classes: List[str] = Field(min_length=1)
    source_sha256: str


class CapabilityAssessment(StrictModel):
    """Deterministic capability verdict for one (investigation, implementation) pair."""

    schema_version: Literal["capability-assessment1"] = "capability-assessment1"
    assessment_id: str
    implementation_id: str
    investigation_id: str
    method_id: str
    episode_id: str
    pr_number: int
    primary_change_id: str
    status: Literal[
        "supported", "unsupported_shape", "missing_input", "not_applicable", "failed"
    ]
    reason_code: str
    required_input_status: Dict[str, Literal["available", "unavailable"]] = Field(
        default_factory=dict
    )
    evidence_artifact_ids: List[str] = Field(default_factory=list)
    source_sha256: str

    @model_validator(mode="after")
    def require_reason(self):
        if not self.reason_code:
            raise ValueError("capability assessments require an explicit reason code")
        return self


class RepositoryDeclaration(StrictModel):
    """One declaration in a temporally frozen, target-relevant repository neighborhood."""

    schema_version: Literal["repository-declaration1"] = "repository-declaration1"
    declaration_id: str
    index_version: str
    snapshot_sha: str
    path: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    declaration_kind: str
    name: str
    fullname: str
    namespace: Optional[str] = None
    signature: str
    type_shape_tokens: List[str]
    direct_dependencies: List[str]
    source_sha256: str


class CanonicalRetrievalHit(StrictModel):
    """Auditable ranking result from canonical API discovery."""

    schema_version: Literal["canonical-retrieval-hit1"] = "canonical-retrieval-hit1"
    retrieval_hit_id: str
    investigation_id: str
    primary_change_id: str
    declaration_id: str
    rank: int = Field(ge=1)
    score: float = Field(ge=0)
    matched_tokens: List[str]
    already_used: bool
    query_sha256: str
    source_sha256: str


class SemanticSubjectInference(StrictModel):
    """Deterministic subject and declaration-role inference for one changed declaration."""

    schema_version: Literal["semantic-subject-inference1"] = "semantic-subject-inference1"
    inference_id: str
    investigation_id: str
    primary_change_id: str
    declaration_name: str
    subject: str
    subject_role: Literal["direct_lhs", "role_conditioned", "incidental", "unknown"]
    conclusion: str
    subject_expression: Optional[str] = None
    confidence: Literal["high", "medium", "low"]
    classifier_version: str
    source_sha256: str


class NamingPopulationMember(StrictModel):
    """One declaration counted in a snapshot-scoped semantic-subject naming population."""

    schema_version: Literal["naming-population-member1"] = "naming-population-member1"
    member_id: str
    population_version: str
    snapshot_sha: str
    path: str
    line_start: int = Field(ge=1)
    declaration_kind: str
    fullname: str
    leaf_name: str
    namespace: Optional[str] = None
    subject: str
    subject_role: Literal["direct_lhs"] = "direct_lhs"
    subject_expression: str
    conclusion: str
    naming_form: Literal[
        "subject_prefix", "subject_elsewhere", "conflicting_prefix", "role_specific_other"
    ]
    source_sha256: str


class NameCollisionResult(StrictModel):
    """Exact review-snapshot and current-PR collision check for a proposed declaration name."""

    schema_version: Literal["name-collision-result1"] = "name-collision-result1"
    collision_id: str
    investigation_id: str
    primary_change_id: str
    current_fullname: str
    proposed_fullname: Optional[str] = None
    repository_matches: List[str] = Field(default_factory=list)
    pr_matches: List[str] = Field(default_factory=list)
    collision: bool
    snapshot_sha: str
    source_sha256: str


class CompositionSource(StrictModel):
    """One repository or current-PR declaration used by a wrapper composition plan."""

    schema_version: Literal["composition-source1"] = "composition-source1"
    composition_source_id: str
    investigation_id: str
    role: Literal[
        "repository_wrapper",
        "cardinality_bridge",
        "cover_witness",
        "subset_witness",
        "parallel_sibling",
    ]
    source_kind: Literal["repository_declaration", "changed_declaration"]
    source_id: str
    declaration_name: str
    signature: str
    source_ref: str
    snapshot_sha: str
    source_sha256: str


class WrapperCompositionPlan(StrictModel):
    """Auditable multi-source plan for replacing reconstructed implementation reasoning."""

    schema_version: Literal["wrapper-composition-plan1"] = "wrapper-composition-plan1"
    plan_id: str
    investigation_id: str
    primary_change_id: str
    target_goal: str
    status: Literal["composed", "no_composition"]
    composition_source_ids: List[str]
    related_change_ids: List[str] = Field(default_factory=list)
    repository_declaration_ids: List[str] = Field(default_factory=list)
    replacement_declaration: Optional[str] = None
    old_dependencies: List[str] = Field(default_factory=list)
    new_dependencies: List[str] = Field(default_factory=list)
    removed_dependencies: List[str] = Field(default_factory=list)
    source_sha256: str


class HistoricalTransformationTrigger(StrictModel):
    """Review-time code situation that prompted a historical maintainer request."""

    schema_version: Literal["historical-transformation-trigger1"] = (
        "historical-transformation-trigger1"
    )
    trigger_id: str
    source_intervention_id: str
    repo: str
    source_pr_number: int
    source_episode_id: Optional[str] = None
    source_snapshot_sha: Optional[str] = None
    method_family: Literal["proof_compression", "structural_rewrite", "other"]
    concern: str
    context_path: Optional[str] = None
    context_declaration: Optional[str] = None
    context_code: Optional[str] = None
    context_sha256: Optional[str] = None
    trigger_features: List[str] = Field(default_factory=list)
    reviewer: Optional[str] = None
    occurred_at: Optional[str] = None
    source_sha256: str


class HistoricalTransformationRequest(StrictModel):
    """Maintainer ask kept separate from its trigger and eventual outcome."""

    schema_version: Literal["historical-transformation-request1"] = (
        "historical-transformation-request1"
    )
    request_id: str
    trigger_id: str
    canonical_ask: str
    source_comment_ids: List[str] = Field(default_factory=list)
    source_comment_bodies: List[str] = Field(default_factory=list)
    request_features: List[str] = Field(default_factory=list)
    source_sha256: str


class HistoricalTransformationResolution(StrictModel):
    """Observed disposition and adopted form of one historical request."""

    schema_version: Literal["historical-transformation-resolution1"] = (
        "historical-transformation-resolution1"
    )
    resolution_id: str
    request_id: str
    outcome: Literal["adopted", "partially_adopted", "contested", "dropped", "unknown"]
    outcome_confidence: Literal["high", "medium", "low"]
    resolution_evidence: str
    exact_replacement: Optional[str] = None
    transformation_features: List[str] = Field(default_factory=list)
    exceptions: List[str] = Field(default_factory=list)
    source_sha256: str


class HistoricalTransformationRecord(StrictModel):
    """Join record for independently hashed trigger, request, and resolution objects."""

    schema_version: Literal["historical-transformation-record1"] = (
        "historical-transformation-record1"
    )
    record_id: str
    trigger_id: str
    request_id: str
    resolution_id: str
    source_intervention_id: str
    source_pr_number: int
    method_family: Literal["proof_compression", "structural_rewrite", "other"]
    source_sha256: str


class HistoricalTransformationQuery(StrictModel):
    """Gold-free, method-specific query over one technically valid target opportunity."""

    schema_version: Literal["historical-transformation-query1"] = (
        "historical-transformation-query1"
    )
    query_id: str
    target_episode_id: str
    target_pr_number: int
    primary_change_id: str
    declaration_name: str
    cutoff_at: str
    method_family: Literal["proof_compression", "structural_rewrite"]
    target_features: List[str] = Field(default_factory=list)
    target_code_sha256: str
    source_sha256: str


class HistoricalTransformationHit(StrictModel):
    """One temporally eligible trigger-ranked precedent or anti-precedent."""

    schema_version: Literal["historical-transformation-hit1"] = (
        "historical-transformation-hit1"
    )
    hit_id: str
    query_id: str
    record_id: str
    rank: int = Field(ge=1)
    trigger_score: float = Field(ge=0)
    matched_features: List[str] = Field(default_factory=list)
    outcome: Literal["adopted", "partially_adopted", "contested", "dropped", "unknown"]
    source_pr_number: int
    occurred_at: str
    source_sha256: str


class HistoricalTransformationStoreManifest(StrictModel):
    """Immutable lineage for a separately versioned historical transformation store."""

    schema_version: Literal["historical-transformation-store-manifest1"] = (
        "historical-transformation-store-manifest1"
    )
    store_id: str
    corpus_version: str
    retrieval_version: str
    sources: List[ArtifactRef]
    artifacts: List[ArtifactRef]
    created_at: str
    source_sha256: str


class OpportunityTransformation(StrictModel):
    kind: str
    symbols: List[str] = Field(default_factory=list)
    description: str


class ReviewOpportunity(StrictModel):
    """Automatically discovered pre-candidate hypothesis for production review."""

    schema_version: Literal["review-opportunity1"] = "review-opportunity1"
    opportunity_id: str
    investigation_id: str
    method_id: str
    episode_id: str
    pr_number: int
    primary_change_id: str
    related_change_ids: List[str] = Field(default_factory=list)
    observed_pattern: str
    proposed_transformation: Optional[OpportunityTransformation] = None
    source_artifact_ids: List[str] = Field(min_length=1)
    discovery_rank: int = Field(ge=1)
    discovery_score: Optional[float] = Field(default=None, ge=0, le=1)
    source_provenance: Literal["automatic"] = "automatic"
    source_sha256: str


class InvestigationRecord(StrictModel):
    """Terminal accounting record whose completion must be backed by operator artifacts."""

    schema_version: Literal["investigation-record1"] = "investigation-record1"
    investigation_id: str
    execution_status: Literal["completed", "failed"]
    disposition: Literal[
        "opportunities", "checked_no_opportunity", "inconclusive", "needs_followup", "not_applicable"
    ]
    operator_run_ids: List[str] = Field(default_factory=list)
    artifact_ids: List[str] = Field(default_factory=list)
    opportunity_ids: List[str] = Field(default_factory=list)
    followup_ids: List[str] = Field(default_factory=list)
    basis: str
    producer: Literal["deterministic", "model", "mixed"]
    source_sha256: str

    @model_validator(mode="after")
    def validate_terminal_evidence(self):
        if self.disposition == "opportunities" and not self.opportunity_ids:
            raise ValueError("opportunities disposition requires at least one opportunity ID")
        if self.disposition != "opportunities" and self.opportunity_ids:
            raise ValueError("only opportunities disposition may reference opportunity IDs")
        if self.disposition != "not_applicable" and not self.operator_run_ids:
            raise ValueError("terminal investigation disposition requires an operator run")
        if self.disposition == "needs_followup" and not self.followup_ids:
            raise ValueError("needs_followup disposition requires a follow-up ID")
        return self


class TechnicalAssessment(StrictModel):
    schema_version: Literal["technical-assessment1"] = "technical-assessment1"
    assessment_id: str
    opportunity_id: str
    status: Literal["valid", "invalid", "uncertain"]
    evidence_artifact_ids: List[str]
    proposed_edit_compiled: Optional[bool] = None
    rationale: str
    producer: Literal["policy", "model", "human"]
    source_sha256: str


class NormScope(StrictModel):
    namespace: Optional[str] = None
    subject: Optional[str] = None
    snapshot_sha: str


class NormRecord(StrictModel):
    schema_version: Literal["norm-record1"] = "norm-record1"
    norm_id: str
    norm_kind: Literal[
        "naming_pattern", "canonical_api", "adopted_transformation", "local_family", "policy"
    ]
    trigger_predicate: str
    recommended_action: str
    scope: NormScope
    support_count: Optional[int] = Field(default=None, ge=0)
    counterexample_count: Optional[int] = Field(default=None, ge=0)
    counterexample_refs: List[str] = Field(default_factory=list)
    effective_before: str
    source_artifact_ids: List[str] = Field(min_length=1)
    strength: Literal["canonical", "strong_convention", "recurring_preference", "weak_prior"]
    source_sha256: str


class NormAssessment(StrictModel):
    """Opportunity-specific application of zero or more frozen norm records."""

    schema_version: Literal["norm-assessment1"] = "norm-assessment1"
    assessment_id: str
    opportunity_id: str
    status: Literal["applicable", "contradicted", "weak_prior", "unknown"]
    norm_ids: List[str] = Field(default_factory=list)
    evidence_artifact_ids: List[str]
    rationale: str
    producer: Literal["policy", "model", "human"]
    source_sha256: str

    @model_validator(mode="after")
    def require_norm_for_applicable_status(self):
        if self.status == "applicable" and not self.norm_ids:
            raise ValueError("applicable norm assessments require at least one norm ID")
        return self


class WorthinessDecision(StrictModel):
    schema_version: Literal["worthiness-decision1"] = "worthiness-decision1"
    decision_id: str
    opportunity_id: str
    technical_assessment_id: str
    norm_assessment_id: Optional[str] = None
    norm_ids: List[str] = Field(default_factory=list)
    review_worthiness: Literal["request", "advisory_option", "no_request", "defer"]
    request_force: Optional[Literal["blocking", "advisory"]] = None
    evidence_artifact_ids: List[str]
    rationale: str
    producer: Literal["policy", "model", "human"]
    source_sha256: str

    @model_validator(mode="after")
    def validate_request_force(self):
        if self.review_worthiness == "request" and self.request_force is None:
            raise ValueError("request decisions require blocking or advisory force")
        if self.review_worthiness != "request" and self.request_force is not None:
            raise ValueError("only request decisions may carry request force")
        return self


class CitedAdjudicationClaim(StrictModel):
    """One factual adjudication premise with explicit artifact lineage."""

    schema_version: Literal["cited-adjudication-claim1"] = "cited-adjudication-claim1"
    claim_id: str
    opportunity_id: str
    text: str
    evidence_artifact_ids: List[str] = Field(min_length=1)
    source_sha256: str


class AdjudicationBundle(StrictModel):
    """Linked three-axis result; factual premises live only in cited claims."""

    schema_version: Literal["adjudication-bundle1"] = "adjudication-bundle1"
    bundle_id: str
    opportunity_id: str
    policy_id: str
    technical_assessment_id: str
    norm_assessment_id: str
    worthiness_decision_id: str
    cited_claim_ids: List[str] = Field(min_length=1)
    route: Literal["deterministic", "redundant_adjudication"]
    redundancy_request_id: Optional[str] = None
    source_sha256: str

    @model_validator(mode="after")
    def validate_redundancy_route(self):
        if self.route == "redundant_adjudication" and not self.redundancy_request_id:
            raise ValueError("redundant adjudication route requires a request ID")
        if self.route == "deterministic" and self.redundancy_request_id is not None:
            raise ValueError("deterministic route cannot carry a redundancy request ID")
        return self


class RedundancyRequest(StrictModel):
    """A bounded request for a second judgment, emitted only for ambiguity."""

    schema_version: Literal["redundancy-request1"] = "redundancy-request1"
    request_id: str
    opportunity_id: str
    reason: Literal["low_confidence", "conflicting_evidence"]
    disputed_axes: List[Literal["technical", "norm", "worthiness"]] = Field(min_length=1)
    evidence_artifact_ids: List[str] = Field(min_length=1)
    required_votes: Literal[2] = 2
    source_sha256: str


class FixedPipelineOpportunityLedger(StrictModel):
    """Frozen Phase 9 route for one automatically discovered production opportunity."""

    schema_version: Literal["fixed-pipeline-opportunity1"] = "fixed-pipeline-opportunity1"
    opportunity_id: str
    investigation_id: str
    method_id: str
    pr_number: int
    primary_change_id: str
    source_status: Literal["opportunity", "checked_no_opportunity", "failed"]
    transformation_status: Literal["constructed", "none"]
    initial_worthiness: Literal["request", "advisory_option", "no_request", "defer"]
    adjudication_route: Literal["deterministic", "model"]
    source_artifact_ids: List[str] = Field(min_length=1)
    source_sha256: str


class AdjudicationVote(StrictModel):
    schema_version: Literal["adjudication-vote1"] = "adjudication-vote1"
    vote_id: str
    request_id: str
    opportunity_id: str
    assessor_id: str
    technical_status: Literal["valid", "invalid", "uncertain"]
    norm_status: Literal["applicable", "contradicted", "weak_prior", "unknown"]
    review_worthiness: Literal["request", "advisory_option", "no_request", "defer"]
    evidence_artifact_ids: List[str] = Field(min_length=1)
    producer: Literal["model", "human"]
    source_sha256: str


class AdjudicationConsensus(StrictModel):
    schema_version: Literal["adjudication-consensus1"] = "adjudication-consensus1"
    consensus_id: str
    request_id: str
    opportunity_id: str
    vote_ids: List[str] = Field(min_length=2)
    status: Literal["agreement", "disagreement"]
    final_worthiness: Literal["request", "advisory_option", "no_request", "defer"]
    source_sha256: str

    @model_validator(mode="after")
    def disagreement_must_defer(self):
        if self.status == "disagreement" and self.final_worthiness != "defer":
            raise ValueError("adjudication disagreement must defer")
        return self


class CandidateOpportunityLink(StrictModel):
    """Auditable bridge from a generated candidate back to one discovered opportunity."""

    schema_version: Literal["candidate-opportunity-link1"] = "candidate-opportunity-link1"
    link_id: str
    candidate_id: str
    opportunity_id: str
    investigation_id: Optional[str] = None
    pr_number: int
    method_id: str
    primary_change_id: str
    context_change_ids: List[str] = Field(default_factory=list)
    relation_ids: List[str] = Field(default_factory=list)
    action_kind: str
    action_symbols: List[str] = Field(default_factory=list)
    evidence_artifact_ids: List[str] = Field(min_length=1)
    source_sha256: str


class ResidualReviewPass(StrictModel):
    """Terminal accounting for the novelty pass after structured synthesis."""

    schema_version: Literal["residual-review-pass1"] = "residual-review-pass1"
    residual_id: str
    episode_id: str
    pr_number: int
    status: Literal["scheduled", "completed", "failed", "not_needed"]
    covered_method_ids: List[str]
    structured_finding_ids: List[str]
    covered_change_ids: List[str]
    uncovered_change_ids: List[str]
    candidate_ids: List[str] = Field(default_factory=list)
    terminal_reason: Optional[str] = None
    source_sha256: str

    @model_validator(mode="after")
    def terminal_status_requires_reason(self):
        if self.status in {"completed", "failed", "not_needed"} and not self.terminal_reason:
            raise ValueError("terminal residual-review status requires a reason")
        if self.status == "scheduled" and self.terminal_reason is not None:
            raise ValueError("scheduled residual review cannot carry a terminal reason")
        if set(self.covered_change_ids).intersection(self.uncovered_change_ids):
            raise ValueError("covered and uncovered residual-review changes must be disjoint")
        return self


class OracleOpportunityEvidence(StrictModel):
    """One immutable review-time observation supplied to opportunity adjudication."""

    schema_version: Literal["oracle-opportunity-evidence1"] = "oracle-opportunity-evidence1"
    evidence_id: str
    kind: Literal[
        "reviewed_code",
        "repository_declaration",
        "repository_pattern",
        "intra_pr_relation",
        "counterexample",
        "mechanical_check",
        "quantitative_pattern",
    ]
    source_ref: str
    content: str
    snapshot_sha: str
    source_sha256: str


class OracleOpportunity(StrictModel):
    """A diagnostic pre-discovered contrast that may or may not warrant a request."""

    schema_version: Literal["oracle-opportunity1"] = "oracle-opportunity1"
    opportunity_id: str
    work_unit_id: str
    source_work_unit_ids: List[str]
    episode_id: str
    pr_number: int
    primary_change_id: str
    related_change_ids: List[str] = Field(default_factory=list)
    method: OpportunityMethod
    information_class: Literal[
        "repository_convention",
        "canonical_api",
        "mechanical_simplification",
        "intra_pr_composition",
        "maintainer_preference",
    ]
    selection_provenance: Literal["oracle_gold_targeted", "matched_control"]
    current_observation: str
    proposed_alternative: Optional[str] = None
    question: str
    evidence: List[OracleOpportunityEvidence]
    source_sha256: str


class OpportunityAdjudication(StrictModel):
    """One model disposition over a frozen oracle opportunity."""

    schema_version: Literal["opportunity-adjudication1"] = "opportunity-adjudication1"
    adjudication_id: str
    opportunity_id: str
    work_unit_id: str
    disposition: Literal["request", "no_request", "inconclusive"]
    validity: Literal["valid", "invalid", "uncertain"]
    norm_strength: Literal[
        "required", "canonical", "conventional", "common", "preference", "unsupported", "uncertain"
    ]
    review_worthiness: Literal["blocking", "advisory", "not_worth_mentioning", "uncertain"]
    evidence_ids: List[str]
    rationale: str
    candidate_id: Optional[str] = None
    producer: Literal["model"] = "model"
    source_sha256: str
