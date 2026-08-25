"""Versioned schemas for the PR Review v4 benchmark foundation."""

from typing import Dict, List, Literal, Optional, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator


MANIFEST_SCHEMA_VERSION = "pr4-manifest-1"
EVENT_SCHEMA_VERSION = "event1"
EPISODE_SCHEMA_VERSION = "episode1"
CHANGE_GRAPH_SCHEMA_VERSION = "cg1"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ArtifactRef(StrictModel):
    path: str
    sha256: str
    role: Optional[str] = None
    schema_version: Optional[str] = None
    records: Optional[int] = None


class DatasetManifest(StrictModel):
    schema_version: Literal["pr4-manifest-1"] = MANIFEST_SCHEMA_VERSION
    dataset_id: str
    release: str
    source_kind: Literal["raw_event_ledger", "legacy_migration"]
    split: Literal["development", "validation", "test"]
    sources: List[ArtifactRef]
    source_artifacts: List[ArtifactRef] = Field(default_factory=list)
    input_artifacts: List[ArtifactRef]
    gold_artifacts: List[ArtifactRef] = Field(default_factory=list)
    derived_artifacts: List[ArtifactRef] = Field(default_factory=list)
    pr_numbers: List[int]
    corpus_cutoff_policy: str
    generator_git_commit: Optional[str] = None
    generator_tree_state: Literal["clean", "dirty", "unknown"] = "unknown"
    generator_versions: Dict[str, str]
    created_at: str


DescriptionProvenance = Literal[
    "review_time_verified",
    "source_current_value_unverified",
    "legacy_unverified",
    "legacy_post_edit_risk_omitted",
    "absent",
]


class VisibleText(StrictModel):
    text: Optional[str] = None
    provenance: DescriptionProvenance
    omission_reason: Optional[str] = None


class ReviewEpisodeInput(StrictModel):
    """The physically isolated, reviewer-visible half of one review episode."""

    schema_version: Literal["episode1"] = EPISODE_SCHEMA_VERSION
    episode_id: str
    repo: str
    pr_number: int
    round_index: int = Field(ge=1)
    title: VisibleText
    description: VisibleText
    base_sha: str
    reviewed_head_sha: str
    diff: str
    changed_files: List[str]
    patch_sha256: str
    source_projection_sha256: str


class ReviewEpisodeBoundary(StrictModel):
    """Hidden event-derived boundary and feedback window for one episode."""

    schema_version: Literal["episode-boundary1"] = "episode-boundary1"
    episode_id: str
    repo: str
    pr_number: int
    round_index: int = Field(ge=1)
    review_started_at: str
    feedback_window_end: Optional[str] = None
    reviewed_head_sha: str
    reviewed_head_resolution: Literal["review_commit_id", "pushed_before_review"]
    triggering_event_ids: List[str]
    feedback_event_ids: List[str]
    next_head_sha: Optional[str] = None
    source_bundle_sha256: str
    compare_sha256: str


class FunnelDecision(StrictModel):
    schema_version: Literal["funnel1"] = "funnel1"
    repo: str
    pr_number: int
    included: bool
    stage: str
    reason: str


class ReviewRoundSegment(StrictModel):
    """A reviewer-event group separated from adjacent groups by an author push."""

    schema_version: Literal["round-segment1"] = "round-segment1"
    segment_id: str
    episode_id: Optional[str] = None
    repo: str
    pr_number: int
    round_index: int = Field(ge=1)
    review_started_at: str
    feedback_window_end: Optional[str] = None
    reviewed_head_sha: str
    reviewed_head_resolution: Literal["review_commit_id", "pushed_before_review"]
    triggering_event_ids: List[str]
    feedback_event_ids: List[str]
    next_head_sha: Optional[str] = None
    hydration_status: Literal["hydrated", "missing_compare"]
    exclusion_reason: Optional[str] = None


class LineSpan(StrictModel):
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)


class ChangedRange(StrictModel):
    """One contiguous run of added/deleted lines in the review-time diff."""

    schema_version: Literal["changed-range1"] = "changed-range1"
    range_id: str
    path: str
    old_path: Optional[str] = None
    hunk_index: int = Field(ge=0)
    range_index: int = Field(ge=0)
    change_kind: Literal["addition", "deletion", "replacement"]
    old_span: Optional[LineSpan] = None
    reviewed_span: Optional[LineSpan] = None
    diff_fragment: str
    source_sha256: str


class SemanticEntity(StrictModel):
    """A complete parser-derived entity from one side of a changed file."""

    schema_version: Literal["semantic-entity1"] = "semantic-entity1"
    entity_id: str
    side: Literal["base", "reviewed"]
    path: str
    kind: str
    name: Optional[str] = None
    fullname: Optional[str] = None
    span: LineSpan
    code: str
    source_sha256: str
    parser_version: str


ChangeTargetKind = Literal[
    "declaration",
    "command",
    "import",
    "module_doc",
    "namespace",
    "section",
    "whitespace",
    "non_lean",
    "unparsed",
]


class ChangeTarget(StrictModel):
    """A reviewable target covering one or more immutable changed ranges."""

    schema_version: Literal["change-target1"] = "change-target1"
    change_id: str
    episode_id: str
    pr_number: int
    kind: ChangeTargetKind
    path: str
    declaration_name: Optional[str] = None
    declaration_kind: Optional[str] = None
    base_entity_ids: List[str] = Field(default_factory=list)
    reviewed_entity_ids: List[str] = Field(default_factory=list)
    changed_range_ids: List[str]
    diff_fragments: List[str]
    base_code: Optional[str] = None
    reviewed_code: Optional[str] = None
    context_refs: List[str] = Field(default_factory=list)
    parse_status: Literal["semantic", "structural", "unparsed"]
    source_sha256: str


class ChangeFileCoverage(StrictModel):
    """Accounting for one file named by the episode diff."""

    schema_version: Literal["change-file-coverage1"] = "change-file-coverage1"
    path: str
    old_path: Optional[str] = None
    file_status: Literal["added", "modified", "removed", "renamed", "unknown"]
    patch_status: Literal["textual", "missing_textual_patch"]
    source_status: Literal[
        "full",
        "full_blob_cache",
        "missing_base_snapshot",
        "missing_base_file",
        "parse_failed",
        "not_lean",
        "not_applicable",
    ]
    base_source_sha256: Optional[str] = None
    reviewed_source_sha256: Optional[str] = None
    changed_range_ids: List[str] = Field(default_factory=list)
    change_target_ids: List[str] = Field(default_factory=list)
    exclusion_reason: Optional[str] = None


class ChangeGraph(StrictModel):
    """Complete review-time change surface for one hydrated review episode."""

    schema_version: Literal["cg1"] = CHANGE_GRAPH_SCHEMA_VERSION
    graph_id: str
    episode_id: str
    repo: str
    pr_number: int
    round_index: int = Field(ge=1)
    base_sha: Optional[str] = None
    reviewed_head_sha: Optional[str] = None
    patch_sha256: str
    parser_version: str
    changed_ranges: List[ChangedRange]
    entities: List[SemanticEntity]
    targets: List[ChangeTarget]
    file_coverage: List[ChangeFileCoverage]
    source_sha256: str


class ScopeResolution(StrictModel):
    """One auditable route from a legacy scope cue to stable cg1 targets."""

    schema_version: Literal["scope-resolution1"] = "scope-resolution1"
    resolution_id: str
    source_kind: Literal["source_comment", "i5_revision_hunk", "identifier", "policy"]
    source_ref: str
    path: Optional[str] = None
    line_start: Optional[int] = Field(default=None, ge=1)
    line_end: Optional[int] = Field(default=None, ge=1)
    side: Optional[Literal["LEFT", "RIGHT"]] = None
    method: Literal[
        "review_line_entity",
        "review_line_range",
        "review_line_nearest",
        "identifier_exact",
        "axiom_declaration_kind",
        "revision_span_overlap",
        "metadata_policy",
        "unresolved",
    ]
    confidence: Literal["exact", "overlap", "inferred", "unresolved"]
    change_ids: List[str] = Field(default_factory=list)
    entity_ids: List[str] = Field(default_factory=list)
    contributes_to_scope: bool = True
    note: Optional[str] = None


class InterventionScopeMigration(StrictModel):
    """Gold-only migration proposal from one i5 intervention to cg1 scope."""

    schema_version: Literal["i5-cg1-map1"] = "i5-cg1-map1"
    migration_id: str
    intervention_id: str
    pr_number: int
    episode_id: str
    graph_id: str
    status: Literal["resolved", "partial", "unresolved", "metadata", "not_judgeable"]
    resolved_change_ids: List[str] = Field(default_factory=list)
    resolved_entity_ids: List[str] = Field(default_factory=list)
    source_event_ids: List[str] = Field(default_factory=list)
    resolutions: List[ScopeResolution]
    exception_codes: List[str] = Field(default_factory=list)
    intervention_sha256: str
    source_sha256: str


class JudgmentAction(StrictModel):
    kind: str
    object: str


class JudgmentScopeRelation(StrictModel):
    change_id: str
    relation: Literal["applies_to", "related", "metadata_target"]


class JudgmentContextRelation(StrictModel):
    event_id: str
    antecedent_event_id: str
    relation: Literal["extends_scope", "coexpresses_judgment"]
    confidence: Literal["mechanical", "inherited_i5_grouping"]


class JudgmentObligation(StrictModel):
    schema_version: Literal["obligation1"] = "obligation1"
    obligation_id: str
    claim: str
    resolution_criteria: Optional[str] = None
    required: bool = True
    status: Literal["proposed_atomic", "needs_decomposition", "not_evaluable"]
    change_ids: List[str] = Field(default_factory=list)
    source_event_ids: List[str] = Field(default_factory=list)
    source_sha256: str


class JudgmentAnnotation(StrictModel):
    producer: str
    source_schema: str
    status: Literal[
        "migration_proposal", "curator_confirmed", "human_confirmed", "rejected"
    ]
    atomicity_status: Literal[
        "presumed_atomic",
        "reviewed_decomposed",
        "needs_decomposition",
        "not_judgeable",
        "metadata",
        "unresolved_scope",
    ]
    atomicity_signals: List[str] = Field(default_factory=list)


class JudgmentNode(StrictModel):
    schema_version: Literal["jg1"] = "jg1"
    judgment_id: str
    source_intervention_id: str
    repo: str
    pr_number: int
    episode_id: str
    action: JudgmentAction
    speech_act: Literal["request", "suggestion", "question", "decision_target", "process"]
    blocking_force: Literal["blocking", "advisory"]
    concern_labels: List[str]
    scope_relations: List[JudgmentScopeRelation]
    obligations: List[JudgmentObligation]
    source_event_ids: List[str]
    context_relations: List[JudgmentContextRelation]
    outcome_observation_ids: List[str]
    annotation: JudgmentAnnotation
    source_sha256: str


class OutcomeObservation(StrictModel):
    schema_version: Literal["outcome-observation1"] = "outcome-observation1"
    observation_id: str
    source_intervention_id: str
    judgment_id: str
    outcome: Literal["adopted", "partially_adopted", "contested", "dropped", "unknown"]
    evidence: str
    producer: str
    source_sha256: str


class InterventionView(StrictModel):
    schema_version: Literal["view1"] = "view1"
    view_id: str
    source_intervention_id: str
    judgment_ids: List[str]
    obligation_ids: List[str]
    aggregation_policy: Literal["all_required"]
    evaluation_eligibility: Literal[
        "included",
        "pending_decomposition",
        "excluded_not_judgeable",
        "metadata",
        "unresolved_scope",
    ]
    source_sha256: str


class DecomposedObligationSpec(StrictModel):
    obligation_key: str
    claim: str
    resolution_criteria: str
    change_ids: List[str]
    source_event_ids: List[str]
    required: bool = True


class JudgmentDecompositionDecision(StrictModel):
    schema_version: Literal["judgment-decomposition1"] = "judgment-decomposition1"
    decision_id: str
    source_intervention_id: str
    decision: Literal["accept_atomic", "split", "not_evaluable"]
    obligations: List[DecomposedObligationSpec]
    rationale: str
    curator: str
    source_sha256: str


EventType = Literal[
    "pull_request",
    "commit",
    "review",
    "review_comment",
    "issue_comment",
    "timeline",
    "review_thread",
    "metadata_edit",
    "file",
    "check",
]


class SourceEvent(StrictModel):
    """Content-addressed index entry for an immutable raw GitHub/Git source object."""

    schema_version: Literal["event1"] = EVENT_SCHEMA_VERSION
    event_id: str
    repo: str
    pr_number: int
    event_type: EventType
    occurred_at: Optional[str] = None
    actor: Optional[str] = None
    source_object: ArtifactRef
    source_key: str
    payload_sha256: str


class PromptPrecedent(StrictModel):
    """One temporally eligible maintainer ask retrieved for a stable review target."""

    schema_version: Literal["prompt-precedent1"] = "prompt-precedent1"
    precedent_id: str
    corpus_version: str
    work_unit_id: str
    primary_change_id: str
    target_episode_id: str
    target_pr_number: int
    cutoff_at: str
    source_event_id: str
    source_pr_number: int
    source_event_type: Literal["review_comment"] = "review_comment"
    actor: str
    occurred_at: str
    context_path: str
    context: str
    context_sha256: str
    body: str
    body_sha256: str
    query_sha256: str
    matched_terms: List[str]
    lexical_score: float = Field(ge=0)
    rank: int = Field(ge=1)
    source_sha256: str


class RetrievalCutoff(StrictModel):
    """Minimal chronology projection permitted in generation-time retrieval."""

    schema_version: Literal["retrieval-cutoff1"] = "retrieval-cutoff1"
    cutoff_id: str
    episode_id: str
    repo: str
    pr_number: int
    review_started_at: str
    source_segment_id: str
    source_sha256: str


# Experimental artifacts are deliberately separate from immutable benchmark gold.
# They address stable change IDs, so generation never needs to open a gold file.
class ReviewWorkUnit(StrictModel):
    schema_version: Literal["work-unit1"] = "work-unit1"
    work_unit_id: str
    episode_id: str
    graph_id: str
    repo: str
    pr_number: int
    round_index: int = Field(ge=1)
    change_ids: List[str]
    target_sha256s: Dict[str, str]
    entity_ids_by_change: Dict[str, List[str]] = Field(default_factory=dict)
    primary_subjects_by_change: Dict[str, str] = Field(default_factory=dict)
    #: File path per change target, populated from renderer `candidate-prompt/12`. Needed to
    #: confine a proposed edit to the target it claims to be about: the edit check only
    #: verified the path was one of the PR's *changed files* — PR-wide — so an agent
    #: scheduled on file A could submit an edit to file B and pass every check.
    #: Empty on `/11` and earlier releases, which is why it defaults rather than being
    #: required.
    paths_by_change: Dict[str, str] = Field(default_factory=dict)
    renderer_version: str
    source_sha256: str


class RenderedPrompt(StrictModel):
    schema_version: Literal["rendered-prompt1"] = "rendered-prompt1"
    work_unit_id: str
    #: Set only by the focused arm, which runs four specs against one work unit and so needs
    #: an identity finer than the unit. Optional because every holistic prompt — including
    #: every frozen one — is one invocation of one unit, where the unit id already is the
    #: invocation id.
    invocation_id: Optional[str] = None
    spec_id: Optional[str] = None
    renderer_version: str
    system_prompt: str
    user_prompt: str
    system_sha256: str
    user_sha256: str
    prompt_sha256: str
    rendered_chars: int = Field(ge=0)
    estimated_tokens: int = Field(ge=0)
    included_change_ids: List[str]
    omitted_change_ids: List[str] = Field(default_factory=list)
    submission_verification_policy: Literal[
        "none", "verify_checkable_edits"
    ] = "none"


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


SubjectKind = Literal[
    "theorem",
    "definition",
    "instance",
    "structure_or_class",
    "inductive",
    "abbreviation",
    "command",
    "import",
    "module_doc",
    "namespace_or_section",
    "non_lean",
    "unknown",
]
LifecycleFacet = Literal[
    "added", "removed", "modified", "renamed", "moved", "unchanged_context", "unknown"
]
ComponentKind = Literal[
    "name",
    "binders",
    "statement_or_type",
    "attributes",
    "proof",
    "value_or_body",
    "documentation",
    "namespace",
    "imports",
    "layout",
    "unknown",
]


class ModificationComponent(StrictModel):
    """One content-addressed component delta within a semantic change target."""

    schema_version: Literal["modification-component1"] = "modification-component1"
    component: ComponentKind
    status: Literal["added", "removed", "modified", "unchanged", "unknown"]
    base_sha256: Optional[str] = None
    reviewed_sha256: Optional[str] = None
    classifier: str


class ModificationRecord(StrictModel):
    """Deterministic inventory record used only to route investigation methods."""

    schema_version: Literal["modification1"] = "modification1"
    modification_id: str
    episode_id: str
    pr_number: int
    primary_change_id: str
    context_change_ids: List[str] = Field(default_factory=list)
    subject_kind: SubjectKind
    lifecycle: LifecycleFacet
    visibility: Literal["public", "private", "local", "unknown"] = "unknown"
    component_deltas: List[ModificationComponent]
    relation_flags: List[str] = Field(default_factory=list)
    classification_status: Literal["complete", "partial", "unknown"]
    unknown_reasons: List[str] = Field(default_factory=list)
    source_sha256: str

    @model_validator(mode="after")
    def require_unknown_reasons(self):
        if self.classification_status != "complete" and not self.unknown_reasons:
            raise ValueError("partial or unknown modification classification requires a reason")
        return self


class PRRelation(StrictModel):
    """Review-time relation hypothesis used for bounded scope expansion and synthesis."""

    schema_version: Literal["pr-relation1"] = "pr-relation1"
    relation_id: str
    episode_id: str
    pr_number: int
    relation_kind: Literal[
        "declaration_dependency",
        "changed_siblings",
        "name_family",
        "direct_use_of_changed_declaration",
        "repeated_implementation_shape",
        "possible_wrapper_or_replacement",
    ]
    source_change_id: str
    related_change_ids: List[str]
    evidence_artifact_ids: List[str] = Field(default_factory=list)
    confidence: Literal["exact", "high", "hypothesis"]
    producer: Literal["deterministic", "model"]
    source_sha256: str


class RelationEvidence(StrictModel):
    """Deterministic parser/code observation supporting one PR relation edge."""

    schema_version: Literal["relation-evidence1"] = "relation-evidence1"
    evidence_id: str
    episode_id: str
    pr_number: int
    relation_kind: Literal[
        "declaration_dependency",
        "changed_siblings",
        "name_family",
        "direct_use_of_changed_declaration",
    ]
    source_change_id: str
    related_change_id: str
    match_kind: Literal[
        "signature_identifier", "body_identifier", "adjacent_parser_entity", "shared_name_token"
    ]
    source_ref: str
    content: str
    source_sha256: str


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


ConcernFamily = Literal[
    "correctness",
    "proof-golf",
    "duplication",
    "naming",
    "generalization",
    "documentation",
    "style",
    "scope",
    "other",
]


#: What kind of issue a finding claims — the same vocabulary the deterministic arm and the
#: C0–C2 census already speak, so the two arms sit on one axis.
#:
#: `concern_family` is too coarse to verify: "naming" is not a check, so no evidence
#: collector could ever support a naming claim and every one of them stayed `inconclusive`.
#: An issue kind names something checkable, and each kind routes to the operator that can
#: check it — `naming_convention_violation` to the snapshot population scan,
#: `style_norm_violation` to the text-style linter, `duplicate_implementation` to canonical
#: retrieval. The operators already exist; what was missing was the routing key.
IssueKind = Literal[
    "broken_build",
    "correctness_policy",
    "documentation_gap",
    "duplicate_implementation",
    "generalization_available",
    "missed_canonical_api",
    "naming_convention_violation",
    "policy_violation",
    "proof_simplification",
    "scope_placement",
    "style_norm_violation",
]



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


class SynthesisAnchor(StrictModel):
    change_id: str
    source_candidate_ids: List[str] = Field(min_length=1)
    source_opportunity_ids: List[str] = Field(min_length=1)
    relation_ids: List[str] = Field(default_factory=list)


class SynthesizedFinding(StrictModel):
    """One publishable PR-level finding with complete many-to-one source lineage."""

    schema_version: Literal["synthesized-finding1"] = "synthesized-finding1"
    finding_id: str
    pr_number: int
    source_candidate_ids: List[str] = Field(min_length=1)
    source_opportunity_ids: List[str] = Field(min_length=1)
    investigation_ids: List[str] = Field(default_factory=list)
    change_ids: List[str] = Field(min_length=1)
    context_change_ids: List[str] = Field(default_factory=list)
    anchors: List[SynthesisAnchor] = Field(min_length=1)
    method_ids: List[str] = Field(min_length=1)
    action_key: str
    concern_family: ConcernFamily
    severity: Literal["blocking", "advisory"]
    claim: str
    requested_change: str
    evidence_artifact_ids: List[str] = Field(min_length=1)
    rank_key: str
    source_sha256: str

    @model_validator(mode="after")
    def anchors_must_equal_issue_changes(self):
        if {item.change_id for item in self.anchors} != set(self.change_ids):
            raise ValueError("synthesis anchors must account for every issue change ID exactly")
        if set(self.change_ids).intersection(self.context_change_ids):
            raise ValueError("issue and context-only change IDs must be disjoint")
        return self


class SynthesisDecision(StrictModel):
    schema_version: Literal["synthesis-decision1"] = "synthesis-decision1"
    synthesis_id: str
    pr_number: int
    action: Literal[
        "retain", "group", "suppress_duplicate", "suppress_dominated", "defer_conflict",
        "suppress_volume"
    ]
    opportunity_ids: List[str] = Field(min_length=1)
    candidate_ids: List[str] = Field(default_factory=list)
    finding_id: Optional[str] = None
    evidence_artifact_ids: List[str] = Field(default_factory=list)
    rationale: str
    source_sha256: str

    @model_validator(mode="after")
    def validate_finding_reference(self):
        if self.action in {"retain", "group", "suppress_duplicate"} and self.finding_id is None:
            raise ValueError(f"{self.action} decisions require a synthesized finding ID")
        if self.action in {"suppress_dominated", "defer_conflict", "suppress_volume"} and self.finding_id is not None:
            raise ValueError(f"{self.action} decisions cannot reference a published finding")
        return self


class SynthesisMatchProjection(StrictModel):
    """Gold-side projection used to measure whether synthesis retained an atomic match."""

    schema_version: Literal["synthesis-match-projection1"] = "synthesis-match-projection1"
    projection_id: str
    finding_id: str
    obligation_id: str
    source_candidate_ids: List[str] = Field(min_length=1)
    issue_match: bool
    resolution_match: bool
    source_match_ids: List[str] = Field(min_length=1)
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


class EvidenceRequest(StrictModel):
    collector: Literal[
        "local_context", "repository_search", "lean_compile", "policy", "precedent"
    ]
    query: str
    purpose: Literal["support", "counterevidence", "both"] = "both"


class ProposedEdit(StrictModel):
    path: str
    declaration_name: Optional[str] = None
    new_declaration: Optional[str] = None
    line_start: Optional[int] = Field(default=None, ge=1)
    line_end: Optional[int] = Field(default=None, ge=1)
    replacement: Optional[str] = None


class CandidateClaim(StrictModel):
    schema_version: Literal["c1"] = "c1"
    candidate_id: str
    producer: Literal["model", "deterministic"] = "model"
    investigation_id: Optional[str] = None
    opportunity_ids: List[str] = Field(default_factory=list)
    work_unit_id: str
    #: Position within its own submission. Already inside the identity payload that mints
    #: `candidate_id`, but never recorded — so a candidate could not be joined to the
    #: verification artifact that compiled it, which is keyed on
    #: `(work_unit_id, candidate_ordinal)`. Optional so frozen candidate files still load;
    #: adding it does not move any existing `candidate_id`.
    ordinal: Optional[int] = None
    episode_id: str
    pr_number: int
    change_ids: List[str]
    entity_ids: List[str] = Field(default_factory=list)
    primary_change_id: Optional[str] = None
    primary_entity_id: Optional[str] = None
    primary_subject: Optional[str] = None
    requested_change: Optional[str] = None
    concern_family: ConcernFamily = "other"
    #: Optional on the model, required at ingestion from renderer `candidate-prompt/12`
    #: onward. It has to stay optional here or the frozen 0.9.x candidate files — written
    #: before the field existed — would no longer load, and those carry Phase 9's lineage.
    issue_kind: Optional[IssueKind] = None
    #: Which focused agent produced this, when one did. `issue_kind` is not enough to tell
    #: them apart: proof golf and proof idiom both declare `proof_simplification`, and they
    #: make *different* claims — golf says the proof gets shorter, idiom says it gets more
    #: canonical and explicitly may not. A verifier keyed on the issue kind alone would hand
    #: idiom's laxer warrant to golf candidates and repeal golf's own rule.
    spec_id: Optional[str] = None
    concern_label: str
    severity: Literal["blocking", "advisory"]
    claim: str
    suggested_fix: Optional[str] = None
    proposed_edit: Optional[ProposedEdit] = None
    evidence_requests: List[EvidenceRequest]
    model_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    source_sha256: str

    @model_validator(mode="before")
    @classmethod
    def infer_legacy_concern_family(cls, data):
        if isinstance(data, dict) and "concern_family" not in data:
            label = data.get("concern_label")
            families = set(ConcernFamily.__args__)
            data = {**data, "concern_family": label if label in families else "other"}
        return data


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


class FindingSource(StrictModel):
    """Where one contribution to a finding came from.

    Replaces `CandidateOpportunityLink` for the arm-neutral path. Opportunity lineage is
    *optional*: a holistic finding has none, and the old link required one, which is why
    `synthesis.link_candidates` raised on every holistic candidate and made a unified merge
    impossible.
    """

    schema_version: Literal["finding-source1"] = "finding-source1"
    #: `holistic` is the retired spelling of `generalist`, kept loadable because 264 frozen
    #: findings carry it. New writes use `generalist`: the arm was never holistic — 162 of
    #: 225 medium work units hold a single change target, and its prompt never contained the
    #: PR diff. It is a generalist reviewer of the same sites, with the same seven tools as
    #: the focused arm, differing only in breadth of checklist.
    arm: Literal["deterministic", "holistic", "generalist", "file_generalist",
                 "focused_agent"]
    candidate_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    method_id: Optional[str] = None
    #: Which focused spec produced this, when the arm is `focused_agent`. Golf and idiom
    #: make different claims under one issue kind, so the finding must record which.
    spec_id: Optional[str] = None
    evidence_artifact_ids: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _deterministic_sources_carry_lineage(self):
        if self.arm == "deterministic" and not (self.opportunity_id and self.evidence_artifact_ids):
            raise ValueError(
                "a deterministic source must name its opportunity and evidence; that "
                "lineage is what makes the arm auditable"
            )
        if self.arm in ("holistic", "generalist", "file_generalist") and not self.candidate_id:
            raise ValueError(f"a {self.arm} source must name its candidate")
        if self.arm == "focused_agent":
            # A focused finding's whole warrant is "an agent constructed this replacement and
            # the compiler accepted it". Without the candidate it cannot be traced to the
            # invocation that made it, and without the verification artifact the compile is
            # an unevidenced assertion — which is precisely the `model_assertion` tier the
            # arm exists to beat. Neither is optional here, unlike for a holistic source.
            if not self.candidate_id:
                raise ValueError("a focused source must name its candidate")
            if not self.spec_id:
                raise ValueError("a focused source must name the spec that produced it")
            if not self.evidence_artifact_ids:
                raise ValueError(
                    "a focused source must name its verification artifacts; the arm's "
                    "warrant is a compile, and an unevidenced compile is an assertion"
                )
        return self


class ReviewFinding(StrictModel):
    """One thing the system says about the PR, from either arm, in one shape.

    This is what gets judged. Scoring candidates *before* the merge and projecting verdicts
    back through them credits a finding for wording it no longer has — the merge keeps only
    the representative's text.
    """

    schema_version: Literal["review-finding1"] = "review-finding1"
    finding_id: str
    pr_number: int
    episode_id: str
    arm: Literal["deterministic", "holistic", "generalist", "file_generalist",
                 "focused_agent", "merged"]
    #: `published` is what the system would show a maintainer; `diagnostic` is retained and
    #: judged but never counted as system output. Keeping both is what lets the detection
    #: ceiling and the publishable result be reported without conflating them.
    admission: Literal["published", "diagnostic"]
    admission_reason: str
    change_ids: List[str]
    primary_change_id: str
    concern_family: str
    issue_kind: Optional[IssueKind] = None
    primary_subject: Optional[str] = None
    severity: Literal["blocking", "advisory"]
    claim: str
    requested_change: str
    #: Resolution judging compares transformations, so the edit has to survive the merge.
    proposed_edit: Optional[ProposedEdit] = None
    evidence_tier: EvidenceTier
    action_key: str
    sources: List[FindingSource]
    source_sha256: str


#: Every arm a finding can carry, read off the model rather than restated.
#:
#: Reports that enumerate arms must derive them from here. A hand-written list does not fail
#: when an arm is added — it reports nothing for it, so a whole arm's output silently reads
#: as zero, which is indistinguishable from that arm having found nothing.
ARMS = get_args(ReviewFinding.model_fields["arm"].annotation)

#: The arms that actually produce findings; `merged` is what the merge makes of them.
PRODUCING_ARMS = tuple(arm for arm in ARMS if arm != "merged")

#: The file-scoped generalist. Separate from `generalist` rather than a mode of it, because
#: the two are deliberately run as different things and must be counted apart: the per-site
#: generalist is the *control* — same sites and tools as the specialists, covering the concern
#: families no specialist exists for — while this one is a *component* whose distinguishing
#: input is the whole file's changes at once.
FILE_GENERALIST_ARM = "file_generalist"

#: The `spec_id` a file-scoped candidate carries. It is a spec in the plumbing sense — it
#: identifies which scheduled reviewer produced the candidate — but it is not a focused
#: agent, and reading "has a spec_id" as "is focused" would file this arm's output under the
#: arm it is meant to be compared with.
FILE_COHERENCE_SPEC = "file_coherence"

#: The arm a model candidate without a focused spec belongs to. Named once so writers cannot
#: reintroduce the retired spelling by habit.
GENERALIST_ARM = "generalist"
RETIRED_ARM_SPELLINGS = {"holistic": GENERALIST_ARM}


class ReviewIssue(StrictModel):
    """One thing the system says to a maintainer, after site-level results are digested.

    A finding is anchored to one change target; a maintainer's ask often is not. Measured on
    medium, 8 of 43 gold obligations name more than one change target, and one names 19 —
    *"remove the newly introduced axioms ... so the file adds no new axioms"*. The
    deterministic arm emitted 19 separate findings there, one per axiom, so the system was
    structurally mismatched with the unit it is evaluated against: 19 published items scored
    against a single maintainer ask, occupying 19 of that PR's 20 publication slots.

    An issue is the unit that gets published and paired with gold. `change_ids` is the union
    over its member findings, which makes it directly comparable to `obligation.change_ids`.
    """

    schema_version: Literal["review-issue1"] = "review-issue1"
    issue_id: str
    pr_number: int
    episode_id: str
    concern_family: ConcernFamily
    issue_kind: Optional[IssueKind] = None
    #: Union over member findings, comparable to `obligation.change_ids`.
    change_ids: List[str]
    primary_change_id: str
    #: Every subject the members named, so a pattern issue can list what it covers.
    primary_subjects: List[str] = Field(default_factory=list)
    severity: Literal["blocking", "advisory"]
    claim: str
    requested_change: str
    proposed_edit: Optional[ProposedEdit] = None
    evidence_tier: EvidenceTier
    admission: Literal["published", "diagnostic"]
    admission_reason: str
    #: The findings this issue speaks for, and the arms they came from.
    finding_ids: List[str]
    arms: List[str]
    #: `per_site` — one finding, published as itself. `per_pattern` — several findings that
    #: the producing method declares are instances of one violation.
    aggregation: Literal["per_site", "per_pattern"]
    site_count: int = Field(ge=1)
    source_sha256: str


class ConflictRecord(StrictModel):
    """Two findings on the same anchor asking for incompatible transformations.

    Emitted instead of picking a winner when neither side has strictly stronger evidence.
    A merge that silently resolves a genuine disagreement reports more confidence than the
    system has.
    """

    schema_version: Literal["conflict-record1"] = "conflict-record1"
    conflict_id: str
    pr_number: int
    primary_change_id: str
    concern_family: str
    finding_ids: List[str]
    action_keys: List[str]
    evidence_tiers: List[str]
    rationale: str
    source_sha256: str


class CandidateRejection(StrictModel):
    """One candidate that failed validation, kept as a record rather than aborting the batch.

    Ingestion used to `raise` on the first malformed candidate, discarding every other
    candidate in the run and leaving no artifact — so drop rates were unmeasurable. A
    rejected *candidate* is distinct from a failed *response*: the latter means the model
    produced nothing usable and is a coverage failure, the former is one bad item among
    good ones.
    """

    schema_version: Literal["candidate-rejection1"] = "candidate-rejection1"
    work_unit_id: str
    pr_number: int
    ordinal: int
    reason_code: str
    detail: str
    raw_sha256: str
    source_sha256: str


#: How a candidate and an obligation came to be compared at all.
#:
#: `anchor` is the original rule: they share a `change_id`. It left 16 of 22 obligations
#: (73%) unjudged in the shipped v8 runs, because a semantically perfect finding anchored one
#: declaration away is an automatic, invisible miss. The wider tiers make those comparisons
#: possible; they are reported separately because widening can only raise recall.
PairingTier = Literal["anchor", "relation", "file"]


class GenerationPlanV2(StrictModel):
    """The generation contract for one ensemble condition. **Contains nothing gold-derived.**

    The reviewer's plan must stay gold-free or the leak-free boundary the whole benchmark
    rests on is broken. Judge configuration, gold hashes, ambiguity rulings and the context
    sidecar therefore live in `EvaluationProtocol`, not here — a first draft put them all in
    one plan, which would have made the reviewer's own contract depend on gold.

    This is the *parent*: one per condition, with a `GenerationRunReceipt` per repetition.
    Repetitions are separate deployed systems, never one pooled ensemble.
    """

    schema_version: Literal["pr4-generation-plan-2"] = "pr4-generation-plan-2"
    plan_id: str
    condition: str
    release_path: str
    release_manifest_sha256: str
    expected_work_unit_ids: List[str]
    expected_pr_numbers: List[int]
    prompt_sha256_by_work_unit: Dict[str, str]
    renderer_version: str
    #: The deterministic arm is computed once and shared across repetitions; binding it here
    #: is what stops a later repetition from silently pairing with a different checker run.
    execution_release_path: Optional[str] = None
    execution_release_sha256: Optional[str] = None
    #: The focused arm's inputs, bound for the same reason the deterministic arm's are: a
    #: `merged_ensemble_v2` repetition must pair with one known focused run, not whichever
    #: candidates file happened to be on disk. Both are recorded because a focused finding is
    #: only admissible with its verification artifact, so the artifacts are as much a part of
    #: the arm's identity as the candidates.
    focused_candidates_path: Optional[str] = None
    focused_candidates_sha256: Optional[str] = None
    focused_verification_path: Optional[str] = None
    focused_verification_sha256: Optional[str] = None
    #: The spec set the focused arm ran, by `spec_id@spec_version`. A spec whose prompt text
    #: changes gets a new version, so this pins *which* four agents produced the run.
    focused_spec_versions: List[str] = Field(default_factory=list)
    adjudication_policy_version: Optional[str] = None
    merge_version: str
    admission_policy: str
    pr_finding_limit: int
    #: Requested inference configuration. The provider-reported model revision is only
    #: observable after the fact and belongs in the receipt, not here.
    model_name: str
    max_tokens: Optional[int] = None
    thinking_budget_tokens: Optional[int] = None
    temperature: Optional[float] = None
    repetitions: int
    scaffold_config_sha256: str
    created_at: str
    source_sha256: str


class GenerationRunReceipt(StrictModel):
    """What one repetition actually did, bound to its parent plan."""

    schema_version: Literal["pr4-generation-receipt-1"] = "pr4-generation-receipt-1"
    receipt_id: str
    plan_id: str
    plan_sha256: str
    repetition: int
    orchestrator_id: str
    #: Observed after execution, unlike the requested configuration in the plan.
    observed_model: Optional[str] = None
    observed_model_revision: Optional[str] = None
    candidates_path: str
    candidates_sha256: str
    findings_path: Optional[str] = None
    findings_sha256: Optional[str] = None
    rejected_candidates: int = 0
    failed_work_unit_ids: List[str] = Field(default_factory=list)
    completed_at: str
    source_sha256: str


class EvaluationProtocol(StrictModel):
    """The evaluation contract, sealed **before** any judging.

    Policy and metric definitions are fixed here so the analysis cannot be chosen after
    seeing verdicts. Gold-bearing by design — which is exactly why it is a separate artifact
    from the generation plan.
    """

    schema_version: Literal["pr4-evaluation-protocol-1"] = "pr4-evaluation-protocol-1"
    protocol_id: str
    gold_release_path: str
    gold_judgments_sha256: str
    gold_views_sha256: str
    judge_version: str
    judge_model: str
    judge_identity: str
    sample_count: int
    aggregation_policy: str
    pairing_tiers: List[str]
    headline_tier: str
    null_pairs_per_obligation: int
    ambiguity_registry_sha256: str
    context_registry_sha256: Optional[str] = None
    context_profile: str
    #: Named before any verdict exists, so the headline cannot be selected post hoc.
    metric_definitions: List[str]
    control_pr_numbers: List[int]
    created_at: str
    source_sha256: str


class PairManifest(StrictModel):
    """Binds the findings actually produced to the pairs that will be judged.

    Sits between the two contracts: generation has happened, judging has not. Without it
    there is no artifact asserting that the judged set corresponds to the generated set.
    """

    schema_version: Literal["pr4-pair-manifest-1"] = "pr4-pair-manifest-1"
    manifest_id: str
    protocol_id: str
    protocol_sha256: str
    generation_receipt_ids: List[str]
    findings_sha256: str
    finding_ids: List[str]
    pair_ids: List[str]
    observed_pairs: int
    null_pairs: int
    created_at: str
    source_sha256: str


class EvaluationReceipt(StrictModel):
    """Terminal artifact: the verdicts, the report, and what actually served them."""

    schema_version: Literal["pr4-evaluation-receipt-1"] = "pr4-evaluation-receipt-1"
    receipt_id: str
    manifest_id: str
    manifest_sha256: str
    matches_sha256: str
    report_sha256: str
    #: Observed, not requested: a provider can serve a different revision than the one asked
    #: for, and that is knowable only afterwards.
    observed_judge_model: Optional[str] = None
    observed_judge_model_revision: Optional[str] = None
    verdicts_returned: int
    coverage_complete: bool
    scored: bool
    completed_at: str
    source_sha256: str


class SemanticPair(StrictModel):
    """One planned comparison, sealed before the judge is asked anything.

    Planning pairs as artifacts is what makes the verdict set checkable: the returned
    verdicts must reconcile exactly against these, so a pair that silently produced no
    verdict is a coverage failure rather than an invisible miss.
    """

    schema_version: Literal["semantic-pair1"] = "semantic-pair1"
    pair_id: str
    obligation_id: str
    obligation_source_sha256: str
    candidate_id: str
    candidate_source_sha256: str
    pr_number: int
    pairing_tier: PairingTier
    #: Why this tier applies — the shared change IDs, the relation ID, or the shared path.
    #: "Has a valid relation" is not a coherent requirement at the `file` tier.
    tier_justification: str
    gold_change_ids: List[str]
    candidate_change_ids: List[str]
    gold_code_sha256: str
    #: Absent at the `anchor` tier, where both sides point at the same code.
    candidate_code_sha256: Optional[str] = None
    prompt_sha256: str
    judge_identity: str
    #: `null` pairs calibrate how often the judge matches things that merely sit near each
    #: other. They are judged alongside the observed pairs and excluded from every recall.
    role: Literal["observed", "null"] = "observed"
    source_sha256: str


class SemanticMatch(StrictModel):
    schema_version: Literal["semantic-match1"] = "semantic-match1"
    match_id: str
    candidate_id: str
    obligation_id: str
    issue_match: bool
    resolution_match: bool
    reason: str
    judge_model: str
    judge_version: str
    candidate_source_sha256: str
    obligation_source_sha256: str
    #: Carried so a widened verdict can never be counted as an anchored one. Defaults keep
    #: verdicts written before tiered pairing loadable.
    pairing_tier: PairingTier = "anchor"
    role: Literal["observed", "null"] = "observed"
    abstain: bool = False
    pair_id: Optional[str] = None
    source_sha256: str


class RunPlan(StrictModel):
    """LEGACY pre-registration contract. Frozen plans load only through this schema.

    Superseded by the split contracts below. It is kept unchanged, with its permissive
    optionals, because eleven sealed plans were written against it; new plans must use
    `GenerationPlanV2` / `EvaluationProtocol`, whose fields are required. Making the new
    fields optional "for compatibility" would silently accept an incomplete new plan, which
    defeats the point of sealing one.
    """

    schema_version: Literal["pr4-run-plan-1"] = "pr4-run-plan-1"
    run_id: str
    #: The orchestrator run this plan governs. Today it always equals `run_id`, but that
    #: was an undeclared convention: nothing tied a sealed pre-registration to the run
    #: directory that executed it. Optional so plans frozen before this field still load.
    orchestrator_id: Optional[str] = None
    #: Hash of the scaffold config the run was planned with, so a sealed run can prove it
    #: executed under the configuration its pre-registration declared.
    scaffold_config_sha256: Optional[str] = None
    dataset_manifest_path: str
    dataset_manifest_sha256: str
    expected_work_unit_ids: List[str]
    expected_pr_numbers: List[int]
    expected_investigation_ids: List[str] = Field(default_factory=list)
    method_registry_sha256: Optional[str] = None
    prompt_sha256_by_work_unit: Dict[str, str]
    renderer_versions: List[str]
    model_name: str
    created_at: str
    source_sha256: str


class RunManifest(StrictModel):
    """Sealed terminal run with complete artifact and lineage accounting."""

    schema_version: Literal["pr4-run-1"] = "pr4-run-1"
    run_id: str
    run_plan_path: str
    run_plan_sha256: str
    dataset_manifest_path: str
    dataset_manifest_sha256: str
    expected_work_unit_ids: List[str]
    successful_work_unit_ids: List[str]
    failed_work_unit_ids: List[str]
    investigations: int = Field(default=0, ge=0)
    operator_runs: int = Field(default=0, ge=0)
    opportunities: int = Field(default=0, ge=0)
    candidates: int = Field(ge=0)
    evidence_packets: int = Field(ge=0)
    findings: int = Field(ge=0)
    artifacts: List[ArtifactRef]
    completion_status: Literal["complete", "failed", "incomplete"]
    created_at: str
    source_sha256: str


class PilotCase(StrictModel):
    schema_version: Literal["pilot-case1"] = "pilot-case1"
    pr_number: int
    episode_ids: List[str]
    case_kind: Literal["intervention", "control"]
    target_facets: List[str]
    rationale: str
    control_semantics: Optional[str] = None
    source_sha256: str
