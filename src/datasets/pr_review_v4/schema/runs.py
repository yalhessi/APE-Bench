"""Pre-registration and receipts: what a run promised to do, and what it did."""

from typing import Dict, List, Literal, Optional, get_args
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import StrictModel
from .identity import ArtifactRef


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
