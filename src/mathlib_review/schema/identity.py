"""What a review is *about*: the dataset, its episodes, the change graph, the work units
cut from it, and the prompts rendered for them.

Derived from the PR itself and gold-free by construction.
"""

from typing import Dict, List, Literal, Optional, get_args
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import CHANGE_GRAPH_SCHEMA_VERSION, EPISODE_SCHEMA_VERSION, EVENT_SCHEMA_VERSION, MANIFEST_SCHEMA_VERSION, StrictModel


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
