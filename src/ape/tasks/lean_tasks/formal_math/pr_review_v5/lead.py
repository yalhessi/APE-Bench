"""The delegating reviewer: one lead per PR round, routing specialists over its work units.

This is the piece the generation exists for. v2 fanned every checker over every PR and
unioned the results; v4 fixed the arm set per condition offline. Neither ever decided, while
looking at a specific PR, that *this* proof is worth a deep golf pass and *that* one is not.

The lead's authority is deliberately narrow and the narrowness is the experiment. It routes,
and routing is authoritative. It also records an assessment of what came back — which claims
duplicate which, whether a golf and an idiom claim on one proof are really one finding, what
severity it would assign — and none of that is applied. Publication belongs to the
verification and evidence chain downstream.

Two reasons for that split, and both are about being able to read the result afterwards. If
the lead both routed and arbitrated, a change in recall could not be attributed to either.
And an LLM that can override a verification gate turns a proof-carrying pipeline back into a
persuasion contest, which is the property this project spent three generations acquiring.

The lead never renders a prompt. Every specialist job it can run was rendered and hashed
before the run started, so a job the lead adds on impulse is still a job the sealed plan
vouches for — and `fanout`, `rules` and `lead` all send byte-identical text for the same
(arm, work unit) pair, which is what makes comparing them mean anything.
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from ape.tasks.base import EvaluationResult, register_task
from ape.tasks.lean_tasks.formal_math.pr_review_v2.base import (
    BasePRReviewConfig,
    BasePRReviewData,
    BasePRReviewResult,
    BasePRReviewTask,
)

from .delegation import TIER_MULTIPLIERS, JobSpec, run_jobs
from .prompts import LEAD_SYSTEM, LEAD_USER

LEAD_TASK_TYPE = "lean_pr_review_v5_lead"


class InvestigationBrief(BaseModel):
    """What the lead wants a specialist to find out, and what it already knows.

    The lead's routing rationale used to be recorded and thrown away: `DelegationRequest.reason`
    landed in the ledger while the child was built from the sealed payload unchanged, so the
    subagent saw only its generic arm prompt. That cost real findings. In one measured case
    the lead delegated a `generality` job whose reason named a *naming* concern, the child
    never saw it, reported a style issue instead, and had it rejected at the arm gate — while
    its own precedent search had already returned the exact rename convention the maintainer
    wanted.

    Everything here is framed as a **question**, never a conclusion. An arm that is told what
    to find will find it, and the whole warrant of this pipeline is that a specialist
    established its claim independently and a compiler agreed. A brief that says "report that
    X duplicates Y" converts the lead into an unverified author with extra steps; a brief that
    says "determine whether X duplicates Y, and here is why I suspect it" does not.
    """

    model_config = ConfigDict(extra="forbid")

    #: The question, in the lead's own words. Concrete enough to be answered yes or no.
    question: str
    #: Why the lead thinks it is worth asking — what it saw in the diff or in the floor's
    #: findings. Grounds the question without asserting its answer.
    because: str = ""
    #: Declarations to look at first. Not a restriction: the arm's scope is still its
    #: scheduled sites, and this only says where the lead would start.
    look_at: List[str] = Field(default_factory=list)
    #: What has already been established, so the arm spends its budget on the open part
    #: rather than repeating a search the lead or the floor already ran.
    already_checked: str = ""
    #: When to return nothing. Stated explicitly because an arm handed a hypothesis feels
    #: obliged to confirm it, and the cheapest way to prevent that is to say so.
    abstain_if: str = ""

    def render(self, arm_id: str) -> str:
        lines = [
            "\n\n---\n## Brief from the reviewer who assigned you this check\n",
            "This is a **hypothesis, not a finding**. It is one reviewer's suspicion, formed "
            "from the diff and an earlier broad pass — it has not been verified and may be "
            "wrong. Investigate it yourself and report only what you establish. If it does "
            "not hold up, say nothing; a refuted hypothesis is a correct outcome here.\n",
            f"**Question:** {self.question}",
        ]
        if self.because:
            lines.append(f"**Why I am asking:** {self.because}")
        if self.look_at:
            lines.append("**Start with:** " + ", ".join(f"`{item}`" for item in self.look_at))
        if self.already_checked:
            lines.append(f"**Already established (do not re-derive):** {self.already_checked}")
        if self.abstain_if:
            lines.append(f"**Return nothing if:** {self.abstain_if}")
        lines.append(
            f"\nThis does not widen your scope. You are still the {arm_id} check and may "
            "report only your own concern; if the answer turns out to belong to a different "
            "concern, drop it rather than restating it as yours."
        )
        return "\n\n".join(lines)


class DelegationRequest(BaseModel):
    """One job the lead wants run.

    A typed model rather than a free-form dict, because `Dict[str, Any]` generates
    `{"type": "object", "additionalProperties": true}` — an object with no declared
    properties. Providers running strict tool schemas reject that, so the tool is advertised
    and then fails on every call, which is exactly what happened on the first smoke run: all
    four leads reported "delegate tool failed (schema error)" and pruned everything. v4's
    `submit_candidates` already takes a typed model for this reason.
    """

    model_config = ConfigDict(extra="forbid")

    #: Cite a job from `read_agenda`...
    proposal_id: Optional[str] = None
    #: ...or name an (arm, work unit) pair yourself to add one the rule did not select.
    arm_id: Optional[str] = None
    work_unit_id: Optional[str] = None
    budget_tier: Literal["cheap", "standard", "deep"] = "standard"
    reason: str = ""
    #: What you want this specialist to find out. Omitting it sends the arm its generic
    #: prompt and nothing else, which is what every run before this one did.
    brief: Optional[InvestigationBrief] = None


class PrunedProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str
    reason: str = ""


class CandidateAssessmentInput(BaseModel):
    """The lead's read on one returned claim. Recorded; never applied."""

    model_config = ConfigDict(extra="forbid")

    invocation_id: str
    candidate_ordinal: int
    verdict: Literal["keep", "drop", "duplicate_of", "needs_sibling"]
    duplicate_of: Optional[str] = None
    concern_disambiguation: Optional[str] = None
    severity: Optional[Literal["blocking", "advisory"]] = None
    reason: str = ""

#: What the lead may use on its own behalf. Read-only and cheap: it is deciding where to
#: spend, not doing the review. It gets `lean_verify_edit` from the shared base because
#: "does this even compile today" is often the fastest way to tell whether a site is worth a
#: specialist at all.
LEAD_TOOLS = ["file_read", "content_search", "lean_verify_edit"]

#: How many proposals one `read_agenda` page shows. A PR with 40 work units has ~160
#: specialist jobs, and dumping them all costs more context than reading the diff.
AGENDA_PAGE = 40


class LeanPRReviewV5LeadConfig(BasePRReviewConfig):
    enabled_tools: List[str] = list(LEAD_TOOLS)
    #: The per-job `standard` cap. `cheap` and `deep` are multiples of it. Required for a
    #: real run: a lead with no cost policy can spend the whole run on one work unit.
    standard_budget_cap: float = 0.25
    #: A ceiling on specialist jobs across all waves, independent of cost. Cost caps bound
    #: each job; this bounds the fan-out, which is the thing a confused lead inflates.
    #: Per lead, not per run.
    max_delegations: int = 60
    #: Total spend one lead may cause, including everything it delegates. The per-job cap
    #: bounds a single subagent and `max_delegations` bounds their number, but neither bounds
    #: the product — and the lead's own `sample_max_cost` does not see nested spend at all,
    #: because subagents run in their own orchestrator. Without this a 17-work-unit PR could
    #: quietly authorise 60 jobs nobody budgeted for.
    per_pr_cost_cap: float = 2.0


class LeanPRReviewV5LeadData(BasePRReviewData):
    task_type: str = LEAD_TASK_TYPE
    episode_id: str
    #: Proposal metadata only — no prompt text. The text lives in the pool file, which is
    #: not part of the sealed agenda for exactly that reason.
    proposals: List[Dict[str, Any]] = Field(default_factory=list)
    #: Repo-relative JSONL of runnable arm payloads, keyed by `invocation_id`.
    arm_pool_path: str
    routing_mode: str = "lead"
    retrieval_cutoff: Optional[str] = None
    trace_path: Optional[str] = None
    #: `work_unit_id -> {status, claims[]}` from the mandatory generalist pass, which
    #: runs before the lead. Empty when the floor produced nothing.
    floor_summary: Dict[str, Any] = Field(default_factory=dict)


class LeanPRReviewV5LeadResult(BasePRReviewResult):
    model_config = ConfigDict()

    episode_id: str = ""
    routing_mode: str = "lead"
    #: One row per job that ran, plus one per proposal that did not.
    delegations: List[Dict[str, Any]] = Field(default_factory=list)
    #: Recorded, never applied. See the module docstring.
    candidate_assessments: List[Dict[str, Any]] = Field(default_factory=list)
    #: Every specialist candidate returned, for the finalization chain to ingest.
    arm_responses: List[Dict[str, Any]] = Field(default_factory=list)
    waves: int = 0


class LeanPRReviewV5LeadTask(BasePRReviewTask):
    task_type = LEAD_TASK_TYPE
    data_class = LeanPRReviewV5LeadData
    task_config_class = LeanPRReviewV5LeadConfig
    task_result_class = LeanPRReviewV5LeadResult

    def _task_config(self) -> LeanPRReviewV5LeadConfig:
        """The cost policy, with declared defaults when none was supplied.

        `create_task_from_data` always builds one, but a task constructed directly — a test,
        a harness introspecting the toolset — has none, and reading through `None` turns a
        missing config into an `AttributeError` deep inside a tool call rather than a clear
        default at the edge.
        """

        return self.config.task_config or self.task_config_class()

    @staticmethod
    def _specialist_count(state: Dict[str, Any]) -> int:
        """Jobs the lead actually chose. The floor is not spent from its allowance.

        Counting the 22 mandatory generalist jobs against `max_delegations` would mean a
        budget of 30 left the lead eight specialists on a 22-unit PR, which is not a routing
        decision so much as a formality.
        """

        return sum(
            1 for _invocation_id, (_outcome, spec) in state["outcomes"].items()
            if spec.disposition != "mandatory"
        )

    # --- state across waves --------------------------------------------------------
    def _state(self) -> Dict[str, Any]:
        if not hasattr(self, "_delegation_state"):
            self._delegation_state = {
                "wave": 0, "outcomes": {}, "requested": set(), "spend": 0.0,
                # Spend the lead actually chose to incur. Tracked apart from `spend` because
                # the coverage floor is not a routing decision: charging it to the routing
                # budget means the cap binds hardest on the largest PRs, which are exactly
                # the ones where routing matters. PR 33149 had 108 work units, a $10.05
                # floor against a $1.50 cap, and therefore zero specialists.
                "delegated_spend": 0.0,
                # The coverage floor runs *through* the lead, as its first wave, but is not
                # the lead's to skip. Tracking it here is what lets `delegate` inject it and
                # `submit_routing` refuse to close without it.
                "floor_done": False,
            }
        return self._delegation_state

    # --- prompt --------------------------------------------------------------------
    def _get_prompts(self, version: str):
        return LEAD_SYSTEM, LEAD_USER

    async def create_system_prompt(self) -> str:
        return LEAD_SYSTEM

    async def create_user_prompt(self) -> str:
        specialists = [p for p in self.data.proposals if not p.get("mandatory")]
        eligible = [p for p in specialists if p.get("eligible")]
        changed = "\n".join(f"  - `{p}`" for p in self.data.changed_files) or "  (none listed)"
        return LEAD_USER.format(
            pr_number=self.data.pr_number,
            title=self.data.pr_title,
            description=self.data.pr_description.strip() or "(no description provided)",
            changed_files=changed,
            work_units=len({p.get("work_unit_id") for p in self.data.proposals}),
            specialist_count=len(specialists),
            eligible_count=len(eligible),
            standard_cap=f"{self._task_config().standard_budget_cap:.2f}",
            max_delegations=self._task_config().max_delegations,
            tool_prefix=self.config.mcp_server_name,
            floor_block=self._floor_block(),
            diff=self.data.diff,
        )

    def _floor_block(self) -> str:
        """Render the floor's findings, or say plainly that it found nothing.

        Silence is information for routing — a work unit the generalist had nothing to say
        about is a candidate for a specialist, not a reason to skip it."""

        summary = self.data.floor_summary or {}
        if not summary:
            return "_(the generalist pass returned no findings)_"
        lines = []
        for unit_id, row in sorted(summary.items()):
            claims = row.get("claims") or []
            if not claims:
                lines.append(f"- `{unit_id}` — generalist found nothing")
                continue
            lines.append(f"- `{unit_id}` — {len(claims)} finding(s):")
            for claim in claims[:6]:
                lines.append(
                    f"    - [{claim.get('concern_family')}] "
                    f"`{claim.get('primary_subject')}`: {claim.get('claim')}"
                )
        return "\n".join(lines)

    # --- pool ----------------------------------------------------------------------
    def _pool(self) -> Dict[str, Dict[str, Any]]:
        """Runnable arm payloads, loaded once per attempt."""

        if getattr(self, "_pool_cache", None) is None:
            path = Path(self.data.arm_pool_path)
            if not path.is_file():
                raise RuntimeError(
                    f"arm pool not found at {path}; the runner writes it before the lead "
                    "starts, so this means the run directory was moved or the lead is being "
                    "replayed against a different run."
                )
            pool = {}
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        row = json.loads(line)
                        pool[row["invocation_id"]] = row
            self._pool_cache = pool
        return self._pool_cache

    def _proposal_by_id(self) -> Dict[str, Dict[str, Any]]:
        return {p["proposal_id"]: p for p in self.data.proposals}

    # --- tools ---------------------------------------------------------------------
    async def register_task_tools(self, mcp) -> None:
        self._register_lean_verify_edit(mcp)

        @mcp.tool(
            description=(
                "List the specialist jobs available for this PR: which arm, which work "
                "unit, which declarations it would look at, whether the deterministic rule "
                "marked it eligible, and why that arm exists. Paged."
            )
        )
        async def read_agenda(
            page: Annotated[int, Field(description="0-based page index")] = 0,
            eligible_only: Annotated[bool, Field(
                description="Show only jobs the rule selected")] = False,
        ) -> Dict[str, Any]:
            rows = [p for p in self.data.proposals if not p.get("mandatory")]
            if eligible_only:
                rows = [p for p in rows if p.get("eligible")]
            start = max(0, int(page)) * AGENDA_PAGE
            window = rows[start:start + AGENDA_PAGE]
            return {
                "total": len(rows),
                "page": page,
                "pages": max(1, (len(rows) + AGENDA_PAGE - 1) // AGENDA_PAGE),
                "mandatory_generalist_jobs": sum(
                    1 for p in self.data.proposals if p.get("mandatory")),
                "jobs": [
                    {
                        "proposal_id": p["proposal_id"],
                        "arm_id": p["arm_id"],
                        "work_unit_id": p["work_unit_id"],
                        "eligible": p["eligible"],
                        "targets": p["site_change_ids"],
                        "rationale": p["rationale"],
                    }
                    for p in window
                ],
            }

        @mcp.tool(
            description=(
                "Run a batch of specialist jobs. Every job in one call runs concurrently, "
                "so batch them. Give either `proposal_id` (a job from read_agenda) or both "
                "`arm_id` and `work_unit_id` (to add one the rule did not select). "
                "ALWAYS include a `brief`: the question you want answered, why you are "
                "asking, and what you already know. Without one the specialist gets only its "
                "generic prompt and has to rediscover from scratch what you already saw. "
                "`budget_tier` is cheap, standard or deep. You may call this more than once "
                "— a cheap first wave, then depth where it mattered. The mandatory generalist "
                "pass has already run and is not requested here. Returns each job's claims "
                "in summary; the full text goes downstream."
            )
        )
        async def delegate(
            jobs: Annotated[List[DelegationRequest], Field(
                description="Jobs to run. Give a reason for each — it is recorded.")] = [],
        ) -> Dict[str, Any]:
            state = self._state()
            pool = self._pool()
            proposals = self._proposal_by_id()
            budget = self._task_config().max_delegations
            specs: List[JobSpec] = []
            rejected: List[Dict[str, str]] = []

            for request in jobs or []:
                raw = (request.model_dump() if hasattr(request, "model_dump")
                       else dict(request))
                proposal_id = raw.get("proposal_id")
                arm_id = raw.get("arm_id")
                work_unit_id = raw.get("work_unit_id")
                if proposal_id and proposal_id in proposals:
                    proposal = proposals[proposal_id]
                    invocation_id = proposal["invocation_id"]
                    disposition = "proposed"
                elif arm_id and work_unit_id:
                    invocation_id = f"{work_unit_id}#{arm_id}"
                    proposal = proposals.get(invocation_id)
                    disposition = "agent_added"
                else:
                    rejected.append({"job": str(raw)[:120], "reason": (
                        "give either a proposal_id from read_agenda, or both arm_id and "
                        "work_unit_id")})
                    continue

                if invocation_id not in pool:
                    rejected.append({"job": invocation_id, "reason": (
                        "no prompt was rendered for this (arm, work unit) pair — the arm has "
                        "no target it could speak about in that unit")})
                    continue
                # One run per pair. A duplicate is a mistake, not a retry: a second run of an
                # identical job produces a second set of candidates the merge would then have
                # to tell apart from a genuine repeat finding.
                if invocation_id in state["requested"]:
                    rejected.append({"job": invocation_id, "reason": "already delegated"})
                    continue
                if self._specialist_count(state) + len(specs) >= budget:
                    rejected.append({"job": invocation_id, "reason": (
                        f"delegation budget exhausted ({budget} jobs)")})
                    continue
                if state["delegated_spend"] >= self._task_config().per_pr_cost_cap:
                    rejected.append({"job": invocation_id, "reason": (
                        f"per-PR cost cap reached (${state['delegated_spend']:.2f} of "
                        f"${self._task_config().per_pr_cost_cap:.2f} spent on delegated work)")})
                    continue

                tier = str(raw.get("budget_tier") or "standard")
                if tier not in TIER_MULTIPLIERS:
                    tier = "standard"
                payload = pool[invocation_id]
                brief = raw.get("brief")
                brief_model = (
                    InvestigationBrief.model_validate(brief)
                    if isinstance(brief, dict) and brief.get("question") else None
                )
                specs.append(JobSpec(
                    invocation_id=invocation_id,
                    arm_id=payload["arm_id"],
                    work_unit_id=payload["work_unit_id"],
                    pr_number=self.data.pr_number,
                    payload=payload["task_data"],
                    budget_tier=tier,
                    proposal_id=(proposal or {}).get("proposal_id"),
                    disposition=disposition,
                    reason=str(raw.get("reason") or ""),
                    brief_text=(brief_model.render(payload["arm_id"]) if brief_model else ""),
                    brief=(brief_model.model_dump() if brief_model else None),
                ))

            # The mandatory generalist pass is prepended to the first wave, whatever the
            # lead asked for. It runs through the lead so that there is one agent per PR
            # delegating all of its own work — but it is injected rather than requested, so
            # "the lead cannot drop below the coverage floor" stays true by construction.
            #
            # An empty `jobs` list on the first wave is therefore meaningful, not an error:
            # it is how a lead runs the broad sweep and looks at the results before choosing
            # where to go deep.
            floor_specs: List[JobSpec] = []
            if not state["floor_done"]:
                for proposal in self.data.proposals:
                    if not proposal.get("mandatory"):
                        continue
                    invocation_id = proposal["invocation_id"]
                    if invocation_id not in pool or invocation_id in state["requested"]:
                        continue
                    payload = pool[invocation_id]
                    floor_specs.append(JobSpec(
                        invocation_id=invocation_id,
                        arm_id=payload["arm_id"],
                        work_unit_id=payload["work_unit_id"],
                        pr_number=self.data.pr_number,
                        payload=payload["task_data"],
                        budget_tier="standard",
                        proposal_id=proposal["proposal_id"],
                        disposition="mandatory",
                        reason="coverage floor — runs in every routing mode",
                    ))
                specs = floor_specs + specs

            if not specs:
                return {"success": False, "ran": 0, "rejected": rejected,
                        "message": "nothing to run"}

            state["wave"] += 1
            for spec in specs:
                state["requested"].add(spec.invocation_id)
            if floor_specs:
                state["floor_done"] = True
            try:
                outcomes = await run_jobs(
                    self, specs,
                    standard_cap=self._task_config().standard_budget_cap,
                    wave=state["wave"], logger=self.logger,
                )
            except Exception as exc:  # noqa: BLE001
                # `self.logger` is bound during setup; a task exercised without it must still
                # report the failure through its return value rather than dying on the log.
                if self.logger is not None:
                    self.logger.error("delegation wave %d failed: %s",
                                      state["wave"], traceback.format_exc())
                for spec in specs:
                    state["requested"].discard(spec.invocation_id)
                return {"success": False, "ran": 0, "rejected": rejected,
                        "error": f"delegation failed: {exc}"}

            spec_by_id = {spec.invocation_id: spec for spec in specs}
            for outcome in outcomes:
                spec = spec_by_id[outcome.invocation_id]
                state["outcomes"][outcome.invocation_id] = (outcome, spec)
                state["spend"] += outcome.cost
                if spec.disposition != "mandatory":
                    state["delegated_spend"] += outcome.cost

            return {
                "success": True,
                "wave": state["wave"],
                "ran": len(outcomes),
                "rejected": rejected,
                "spend_so_far": round(state["spend"], 4),
                "delegated_spend": round(state["delegated_spend"], 4),
                "spend_remaining": round(
                    max(0.0, self._task_config().per_pr_cost_cap
                        - state["delegated_spend"]), 4),
                "delegations_used": self._specialist_count(state),
                "delegations_remaining": max(0, budget - self._specialist_count(state)),
                "floor_jobs_run": len(floor_specs),
                "results": [outcome.summary() for outcome in outcomes],
            }

        @mcp.tool(
            description=(
                "Finish. Anything you did not delegate is recorded as pruned "
                "automatically — you do NOT need to list them all. Use `pruned` only where "
                "you want the reason recorded, and `message` for the policy behind the rest. "
                "Optionally assess the claims that came back; your assessments are recorded "
                "for analysis but do NOT change what gets published. Call this exactly once."
            )
        )
        async def submit_routing(
            pruned: Annotated[List[PrunedProposal], Field(
                description=(
                    "Optional. Jobs you want to record a specific reason for. Everything "
                    "you did not delegate is pruned automatically regardless."
                )
            )] = [],
            candidate_assessments: Annotated[List[CandidateAssessmentInput], Field(
                description=(
                    "Your read on each returned claim. Recorded for analysis; it does not "
                    "change what gets published."
                )
            )] = [],
            message: Annotated[str, Field(description="Short summary of your routing.", default="")] = "",
        ) -> Dict[str, Any]:
            if not self._state()["floor_done"]:
                return {"evaluation_result": EvaluationResult(
                    success=False, score=0.0,
                    message=(
                        "The mandatory generalist pass has not run yet, so no work unit has "
                        "been reviewed at all. Call `delegate` first — passing an empty "
                        "`jobs` list runs just that broad sweep — then read what it found "
                        "and decide which specialists are worth adding.")),
                    "message": "Coverage floor has not run"}

            pruned_rows = [
                (item.model_dump() if hasattr(item, "model_dump") else dict(item))
                for item in (pruned or [])
            ]
            assessment_rows = [
                (item.model_dump() if hasattr(item, "model_dump") else dict(item))
                for item in (candidate_assessments or [])
            ]
            try:
                records, responses = self._reconcile(pruned_rows)
            except Exception:  # noqa: BLE001
                self.logger.error("reconciliation failed: %s", traceback.format_exc())
                return {"evaluation_result": EvaluationResult(
                    success=False, score=0.0, message=traceback.format_exc()),
                    "message": "Submit failed"}

            state = self._state()
            result = self.create_result(
                success=True, score=1.0, pr_number=self.data.pr_number,
                episode_id=self.data.episode_id,
                routing_mode=self.data.routing_mode,
                delegations=records,
                candidate_assessments=[
                    dict(item, schema_version="v5-assessment1") for item in assessment_rows
                ],
                arm_responses=responses,
                waves=state["wave"],
                merge_ready_as_is=None,
                findings=[], review_message=message or "",
            )
            if self.termination_callback:
                try:
                    await self.termination_callback(result)
                except Exception as exc:  # noqa: BLE001
                    self.logger.warning("Failed to trigger termination: %s", exc)
            return {"evaluation_result": EvaluationResult(
                success=True, score=1.0,
                message=(
                    f"Routing recorded: {len(records)} job(s) across {state['wave']} wave(s), "
                    f"{sum(len(r['candidates']) for r in responses)} candidate(s).")),
                "message": "Routing submitted"}

    # --- reconciliation ------------------------------------------------------------
    def _reconcile(self, pruned: List[Dict[str, str]]):
        """Turn state into delegation records, auto-pruning whatever was not delegated.

        This is v5's replacement for v4's "every expected work unit has exactly one
        successful response", which a lead that prunes cannot satisfy. The ledger guarantee
        is the same — every proposal ends with a disposition — but the *bookkeeping* is the
        runner's job, not the model's.

        It used to be the model's, and that killed a lead. With 184 proposals the largest
        agenda has ~46 jobs for one lead, and refusing its submission until it had serialized
        a prune record for every one of them cost it four rejected `submit_routing` calls and
        its entire budget; it hit `paused_cost_limit` having reviewed nothing. A reason is
        worth recording where the lead has one, and worth nothing at all when the alternative
        is transcribing a list the runner already holds.
        """

        state = self._state()
        proposals = self._proposal_by_id()
        pruned_by_id = {
            str(item.get("proposal_id")): str(item.get("reason") or "")
            for item in pruned if isinstance(item, dict) and item.get("proposal_id")
        }

        records: List[Dict[str, Any]] = []
        responses: List[Dict[str, Any]] = []
        context_calls = self._context_calls()

        for invocation_id, (outcome, spec) in sorted(state["outcomes"].items()):
            records.append({
                "schema_version": "v5-delegation1",
                "invocation_id": invocation_id,
                "proposal_id": spec.proposal_id,
                "arm_id": outcome.arm_id,
                "work_unit_id": outcome.work_unit_id,
                "pr_number": outcome.pr_number,
                "disposition": spec.disposition,
                "reason": spec.reason,
                "budget_tier": outcome.budget_tier,
                "budget_cap": outcome.budget_cap,
                "status": outcome.status,
                "wall_seconds": outcome.wall_seconds,
                "cost": outcome.cost,
                "token_usage": outcome.token_usage,
                "candidate_count": len(outcome.candidates),
                "verification_artifact_count": len(outcome.verification_artifacts),
                "result_sha256": outcome.result_sha256,
                # Both halves of what the model actually read: the brief itself, and the hash
                # of the composed prompt. The sealed plan vouches for the template alone.
                "brief": spec.brief,
                "delivered_prompt_sha256": outcome.delivered_prompt_sha256,
                "context_calls": context_calls.get(invocation_id, []),
            })
            responses.append({
                "invocation_id": invocation_id,
                "arm_id": outcome.arm_id,
                "work_unit_id": outcome.work_unit_id,
                "spec_id": spec.payload.get("spec_id"),
                "pr_number": outcome.pr_number,
                "status": outcome.status,
                "candidates": outcome.candidates,
                "verification_artifacts": outcome.verification_artifacts,
                "rendered_prompt_sha256": spec.payload.get("rendered_prompt_sha256"),
            })

        for proposal_id, proposal in sorted(proposals.items()):
            if proposal["invocation_id"] in state["outcomes"]:
                continue
            if proposal.get("mandatory"):
                # Only reachable if the floor could not be dispatched at all; recording it as
                # pruned would file a coverage failure as a decision.
                self.logger and self.logger.warning(
                    "mandatory job %s never ran", proposal["invocation_id"])
            records.append({
                "schema_version": "v5-delegation1",
                "invocation_id": proposal["invocation_id"],
                "proposal_id": proposal_id,
                "arm_id": proposal["arm_id"],
                "work_unit_id": proposal["work_unit_id"],
                "pr_number": proposal["pr_number"],
                "disposition": "pruned",
                # The lead's own words when it gave them; otherwise a marker that says it
                # made a choice rather than that the choice went unrecorded.
                "reason": pruned_by_id.get(proposal_id, "not selected by the lead"),
                "reason_given": proposal_id in pruned_by_id,
                "budget_tier": None, "budget_cap": None, "status": None,
                "wall_seconds": None, "cost": None, "token_usage": None,
                "candidate_count": None, "verification_artifact_count": None,
                "result_sha256": None, "context_calls": [],
            })
        return records, responses

    def _context_calls(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group the append-only context trace by invocation."""

        path = self.data.trace_path
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        if not path or not Path(path).is_file():
            return grouped
        try:
            with Path(path).open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    grouped.setdefault(row.get("invocation_id", "?"), []).append(row)
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("could not read context trace %s: %s", path, exc)
        return grouped

    def should_terminate(self, evaluation_result: EvaluationResult = None) -> bool:
        return True

    @classmethod
    def is_best_result(cls, result) -> bool:
        return bool(result.success)


register_task(LEAD_TASK_TYPE, LeanPRReviewV5LeadTask)
