"""Strict records for the delegating reviewer: what may run, what ran, and why.

Three ideas carry the whole generation:

* An **arm** is a specialist the lead may call. It is a row plus a prompt — the property
  v2 and v4 both have and the one thing that must not be lost, because a registry you can
  only extend by writing code stops being extended.
* A **proposal** is one (arm, work unit) pair the deterministic scheduler enumerated. Every
  proposal ends its life with a **disposition**, and reconciliation refuses to close a run
  until every one of them does.
* A **delegation record** is what actually happened to a job. It is the object the routing
  ablation is measured on, so it holds cost and outcome even for jobs that failed or paused
  — those are exactly the cases a run summary would otherwise silently drop.

`source_sha256` on every record follows v4's `sealed_model` convention (hash the constructed
model minus its own hash field, caller supplies the ID). It is deliberately *not*
`sealed_from_payload`: the two produce different digests for the same logical record, and
mixing them inside one package is how a frozen hash quietly moves.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from src.datasets.pr_review_v4.schema import StrictModel

#: What a lead is allowed to do with the agenda it is handed.
#:
#: * `fanout` — every arm on every work unit. The upper bound on coverage and on cost.
#: * `rules`  — only the pairs the deterministic scheduler marked eligible. No model call
#:              decides anything; this is the control that separates "routing helped" from
#:              "the lead's own inspection helped".
#: * `lead`   — the mandatory floor, plus whichever specialists the lead keeps or adds.
ROUTING_MODES = ("fanout", "rules", "lead")

#: Budget tiers, as multiples of the configured `standard` cap. Named rather than numeric
#: because `sample_max_cost` is an *orchestrator*-level setting, so a tier is not a per-job
#: knob — it is the set a job is grouped into. See `delegation.py`.
BUDGET_TIERS = ("cheap", "standard", "deep")
TIER_MULTIPLIERS = {"cheap": 0.5, "standard": 1.0, "deep": 2.0}

#: How a job came to run, or why it did not. `pruned` is a terminal disposition like any
#: other: a proposal the lead dropped is a measurement, not an absence.
DISPOSITIONS = ("mandatory", "proposed", "agent_added", "pruned")

#: Context capabilities an arm may be granted.
#:
#: The grant is **per arm**, and the policy lives in `arms._CONTEXT_GRANTS` — this tuple is
#: only the vocabulary. It used to say that granting every arm all four was deliberate and
#: that a per-arm subset would answer an unmeasured question by assumption; smoke4 measured
#: it, `arms.py` was changed, and this comment was left behind asserting the opposite of what
#: the code does. Policy and its rationale belong together, which is why the reasoning is
#: there and not here.
CONTEXT_TOOLS = ("zulip_search", "precedent_search", "declaration_search", "lean_verify_edit")


class ReviewArm(StrictModel):
    """One specialist the lead may delegate to."""

    schema_version: Literal["v5-arm1"] = "v5-arm1"
    arm_id: str
    task_type: str
    kind: Literal["generalist", "specialist"]
    concern_family: str
    issue_kind: Optional[str] = None
    #: A mandatory arm runs on every work unit in every mode and cannot be pruned. The
    #: generalist is mandatory because R1 measured coverage, not selection, as the dominant
    #: wall for a single run — a lead free to prune everything could fall below the
    #: coverage floor and win on cost for the wrong reason.
    mandatory: bool = False
    #: The v4 `FocusedAgentSpec` this arm delegates its eligibility rule to, when it has
    #: one. `None` means the arm runs on every work unit.
    spec_id: Optional[str] = None
    prompt_sha256: str
    tools_sha256: str
    context_tools: List[str] = Field(default_factory=lambda: list(CONTEXT_TOOLS))
    cost_hint: float
    rationale: str
    source_sha256: str


class AgendaProposal(StrictModel):
    """One (arm, work unit) pair, and whether the deterministic rule selected it.

    Every renderable pair is enumerated, not just the eligible ones, so that `fanout`,
    `rules` and `lead` all draw from *the same pre-rendered pool*. If each mode rendered its
    own prompts, a difference between modes could be a difference in prompt text rather
    than in routing, and the comparison would not mean what it claims.
    """

    schema_version: Literal["v5-proposal1"] = "v5-proposal1"
    proposal_id: str
    #: `wu:…#arm_id`. Identity has to be finer than the work unit: several arms run against
    #: one unit, and attribution is taken from the invocation, never from the model's own
    #: report of which agent it is.
    invocation_id: str
    arm_id: str
    work_unit_id: str
    episode_id: str
    pr_number: int
    site_change_ids: List[str]
    #: True when the arm's rule selected this pair from the modification inventory.
    eligible: bool
    mandatory: bool
    #: What the coverage contract says about this pair.
    #:
    #: `required` work is not the lead's to skip: it is derived from a trigger the PR itself
    #: supplies — a stated intent, a component grain, a measured importance — rather than
    #: from a quota. Measured on heldout11 rep2, the lead ran 30 of 459 specialist proposals
    #: (7%) while using half its cost cap and a quarter of its job quota, and `proof_golf`,
    #: `api_reuse` and `generality` ran *zero* times across 11 PRs — including on PR 33285,
    #: whose title says golf and whose gold is two golf asks.
    #:
    #: `recommended` and `optional` remain entirely the lead's call. The contract sets a
    #: floor under coverage; it does not take over routing.
    routing_priority: Literal["required", "recommended", "optional"] = "optional"
    #: Why this priority, in the PR's own terms. Read by the lead, and the thing to audit
    #: when required work looks wrong: a reason that does not survive reading is a bad rule.
    routing_reason: str = ""
    #: The `ReviewComponent` this pair reviews, when one is more specific than the work unit.
    component_id: Optional[str] = None
    component_grain: Optional[str] = None
    prompt_sha256: str
    cost_hint: float
    rationale: str
    source_sha256: str


class ReviewAgenda(StrictModel):
    """The full enumerated pool for one run, sealed before the first model call."""

    schema_version: Literal["v5-agenda1"] = "v5-agenda1"
    agenda_id: str
    run_name: str
    routing_mode: Literal["fanout", "rules", "lead"]
    release: str
    modification_inventory: Optional[str] = None
    arms: List[ReviewArm]
    proposals: List[AgendaProposal]
    scheduler_version: str
    renderer_version: str
    source_sha256: str


class DelegationJob(StrictModel):
    """A job the lead asked for. Proposed jobs cite an id; added jobs give full scope."""

    schema_version: Literal["v5-job1"] = "v5-job1"
    #: Set when the lead selected a pair the scheduler enumerated. `None` only for a pair
    #: the lead constructed itself, which must then name its own scope.
    proposal_id: Optional[str] = None
    arm_id: str
    work_unit_id: str
    budget_tier: Literal["cheap", "standard", "deep"] = "standard"
    reason: str = ""


class ContextCall(StrictModel):
    """One retrieval an arm made, recorded so an unsuccessful job is still auditable.

    Persisted append-only during the attempt rather than returned with the result: a job
    that fails or exhausts its budget returns nothing, and those are precisely the jobs
    whose retrieval behaviour explains the outcome.
    """

    schema_version: Literal["v5-context-call1"] = "v5-context-call1"
    invocation_id: str
    tool: Literal["zulip_search", "precedent_search", "declaration_search", "lean_verify_edit"]
    query: str
    #: What the gate was set to. A Zulip read is only correct relative to its cutoff, so a
    #: trace without the cutoff cannot be checked after the fact.
    as_of: Optional[str] = None
    exclude_pr: Optional[int] = None
    #: Identifies the corpus the ranking ran over, so a result set stays interpretable when
    #: the index is rebuilt.
    corpus_sha256: Optional[str] = None
    result_ids: List[str] = Field(default_factory=list)
    result_count: int = 0
    truncated: bool = False


class CandidateAssessment(StrictModel):
    """The lead's judgment about one returned candidate — recorded, never applied.

    v1 gives the lead authority over *routing* only. Its arbitration is captured because
    that is the evidence for whether arbitration is worth building next, but publication
    stays with the deterministic finalization chain: an LLM must not be able to talk a
    finding past a verification gate, and letting routing and arbitration move together
    would make any recall change unattributable to either.
    """

    schema_version: Literal["v5-assessment1"] = "v5-assessment1"
    invocation_id: str
    candidate_ordinal: int
    verdict: Literal["keep", "drop", "duplicate_of", "needs_sibling"]
    #: Set when `verdict == "duplicate_of"`, naming the candidate this one restates.
    duplicate_of: Optional[str] = None
    concern_disambiguation: Optional[str] = None
    severity: Optional[Literal["blocking", "advisory"]] = None
    reason: str = ""


class DelegationRecord(StrictModel):
    """What became of one job. The unit the routing ablation is measured on."""

    schema_version: Literal["v5-delegation1"] = "v5-delegation1"
    invocation_id: str
    proposal_id: Optional[str] = None
    arm_id: str
    work_unit_id: str
    pr_number: int
    disposition: Literal["mandatory", "proposed", "agent_added", "pruned"]
    #: The lead's stated reason for keeping, adding or dropping this job. Free text, and
    #: the only place the lead's routing rationale is captured at all.
    reason: str = ""
    budget_tier: Optional[Literal["cheap", "standard", "deep"]] = None
    budget_cap: Optional[float] = None
    #: `None` for a pruned job, which never executed.
    status: Optional[Literal["success", "failed", "paused_cost", "paused_turns"]] = None
    wall_seconds: Optional[float] = None
    cost: Optional[float] = None
    token_usage: Optional[Dict[str, float]] = None
    candidate_count: Optional[int] = None
    verification_artifact_count: Optional[int] = None
    result_sha256: Optional[str] = None
    context_calls: List[ContextCall] = Field(default_factory=list)
    source_sha256: str


class V5RunPlan(StrictModel):
    """Pre-registration, sealed before the first model call.

    v4's `run_contract.seal_run` asserts that every expected work unit has exactly one
    successful terminal response. A lead that prunes cannot satisfy that, and weakening the
    assertion for everyone would remove a guarantee v4 depends on. So v5 seals a different
    object — the enumerated agenda — and reconciles against *dispositions* instead of
    against exhaustive coverage. The guarantee is the same shape: nothing ran that was not
    planned, and nothing planned was silently skipped.

    Prompt *hashes* only. `contracts.assert_gold_free` substring-sweeps the serialized plan
    and the focused prompts are full of phrases like "would a maintainer say"; shipping the
    text would trip a leak check on prose that is not a leak.
    """

    schema_version: Literal["v5-run-plan1"] = "v5-run-plan1"
    run_id: str
    run_name: str
    routing_mode: Literal["fanout", "rules", "lead"]
    agenda_sha256: str
    release: str
    release_manifest_sha256: Optional[str] = None
    #: `invocation_id -> prompt sha256`, one entry per enumerated pair. Keyed on the
    #: invocation rather than the work unit because four arms on one unit would collide on
    #: a unit-keyed map, which is the bug v4's focused arm had to name explicitly.
    prompt_sha256_by_invocation: Dict[str, str]
    arm_sha256_by_id: Dict[str, str]
    context_index_sha256: Dict[str, str] = Field(default_factory=dict)
    model_name: str
    scaffold_config_sha256: str
    lead_cost_cap: float
    standard_budget_cap: float
    per_pr_cost_cap: float
    deterministic_release_sha256: Optional[str] = None
    #: How the lead composed its children, and what its assessments were allowed to do.
    #:
    #: Sealed because coordination is about to become a variable and a result attributed to a
    #: mechanism the run does not record is not attributable at all. Every value here was a
    #: constant in `lead.py` or `delegation.py` until it was written down: two waves, a pair
    #: may run at most once, the parent sees a truncated summary, a child sees nothing of its
    #: siblings, the lead may drop and fold but not rewrite.
    coordination: Dict[str, Any] = Field(default_factory=dict)
    git_commit: Optional[str] = None
    #: `io.git_state()`'s second element verbatim. Tri-state, not a bool: `unknown` (git
    #: unavailable) is a real provenance answer and is not the same claim as `clean`.
    git_tree_state: Optional[Literal["clean", "dirty", "unknown"]] = None
    source_sha256: str


class V5RunManifest(StrictModel):
    """Post-run reconciliation. Written only when every proposal is accounted for."""

    schema_version: Literal["v5-run-manifest1"] = "v5-run-manifest1"
    run_id: str
    run_name: str
    run_plan_sha256: str
    routing_mode: Literal["fanout", "rules", "lead"]
    proposals_total: int
    delegated: int
    pruned: int
    agent_added: int
    mandatory: int
    succeeded: int
    failed: int
    paused: int
    total_cost: float
    #: Where `total_cost` came from: `lead` (the leads' own conversations, or the single
    #: orchestrator in the model-free modes), `nested` (everything under a lead attempt —
    #: floor and specialists), `extra` (caller-supplied remainder). Recorded because the
    #: three come from orchestrators that cannot see each other, and a total with no
    #: breakdown is exactly how the floor's $14.52 went missing for a whole run.
    cost_breakdown: Dict[str, float] = Field(default_factory=dict)
    wall_seconds: float
    candidates_total: int
    issues_total: int
    context_calls_total: int
    #: `partial` sits between the other two: nothing errored, but the run did not cover what
    #: it promised to. Finalization and judging treat it as non-success, because a recall
    #: number from a partial run is measured against a denominator it never looked at.
    completion_status: Literal["complete", "partial", "failed"]
    #: Mandatory jobs that did not succeed, one row each. Empty on a complete run.
    coverage_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    source_sha256: str
