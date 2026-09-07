"""Maintainer ground truth: judgments, the obligations decomposed from them, and the views
that scope them.

Gold-bearing. Generation must not import this module -- the reviewer's run tree stays
gold-free, which is why the judge gets its own orchestrator run.
"""

from typing import Dict, List, Literal, Optional, get_args
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import StrictModel


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


class PilotCase(StrictModel):
    schema_version: Literal["pilot-case1"] = "pilot-case1"
    pr_number: int
    episode_ids: List[str]
    case_kind: Literal["intervention", "control"]
    target_facets: List[str]
    rationale: str
    control_semantics: Optional[str] = None
    source_sha256: str
