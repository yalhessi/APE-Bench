"""Spawn specialist subagents from inside a running task, and report what each one cost.

This is the review family's use of the framework primitive (`ape.orchestration.subtasks`),
not a second copy of it. It used to be a third convention: its own nested orchestrator, its own
reader of what the children did, its own status vocabulary, its own cost aggregation -- and the
accounting failures that voided two September runs were what that divergence cost. What is
left here is what is genuinely the review family's: how a lead's job becomes a runnable spec,
and how a finished child becomes a row in the delegation ledger.

Three things are still not obvious and are still load-bearing.

**A budget is per job, not per group.** Tiers existed as *groupings* only because
`sample_max_cost` is orchestrator-wide, so varying a job's budget meant running it in its own
orchestrator. `ExecutionLimits` travels on the payload and the worker reads it before building
the attempt, so one wave runs a `cheap` job beside a `deep` one. `TIER_MULTIPLIERS` survives as
the vocabulary the lead asks in.

**Nested execution runs in-process.** The lead is itself inside a `SampleWorker`, and spawning
a multiprocessing pool from there is the obvious way to deadlock the run. The primitive's
default of `num_processes=0` is what that is.

**Every subtask keeps its own workspace overlay.** `_ensure_patched_target_workspace` unlinks
the snapshot symlink, builds a lazy overlay in its place, and writes a patch marker that raises
if a different patch is applied. Handing several concurrent subagents one path -- each
compiling into it via `lean_verify_edit` -- corrupts the thing they are all reading. Isolation
is the primitive's directory derivation, and it is why that derivation is not negotiable.

A paused job is reported as paused and is never silently retried at a higher tier. Budget
exhaustion is a measurement about routing -- the whole reason the trace exists -- and quietly
buying more of it would erase the signal.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ape.orchestration.config import EarlyStopMode
from ape.orchestration.models import ChildRun, ExecutionStatus, TaskExecutionSpec
from ape.orchestration.subtasks import DEFAULT_NESTED_CONCURRENCY, run_subtasks

#: Multipliers on the configured `standard` cap. Named tiers rather than free-form numbers
#: so the lead cannot invent a budget, and so a run's cost policy is one number in config.
#:
#: Imported, not restated. This was a verbatim duplicate of the definition in
#: `src.mathlib_review.schema.review` with neither side importing the other — the task layer
#: read this copy and the dataset layer read that one, so the two could drift apart and a run
#: would price its jobs differently from the plan that budgeted them.
from src.mathlib_review.schema.review import TIER_MULTIPLIERS  # noqa: E402


@dataclass
class JobSpec:
    """One delegation the lead asked for, resolved to a runnable payload."""

    invocation_id: str
    arm_id: str
    work_unit_id: str
    pr_number: int
    payload: Dict[str, Any]
    budget_tier: str = "standard"
    proposal_id: Optional[str] = None
    disposition: str = "proposed"
    reason: str = ""
    #: Rendered brief text, already composed by the lead. Empty when none was given.
    brief_text: str = ""
    #: Serialized brief, for the ledger.
    brief: Optional[Dict[str, Any]] = None

    @property
    def required(self) -> bool:
        """The coverage floor. A required job that does not succeed is a coverage gap, and a
        coverage gap closes the run `partial` rather than complete."""

        return self.disposition == "mandatory"

    @property
    def budget_scope(self) -> str:
        """Which budget this job's spend is charged to.

        The floor is exempt from the per-PR discretionary cap by design: charging coverage to
        the routing allowance once left PR 33149 with a $10.05 floor against a $1.50 cap and
        therefore zero specialists.
        """

        return "floor" if self.required else "discretionary"

    def execution_spec(self, standard_cap: float) -> TaskExecutionSpec:
        """This job as the framework describes a child: identity, payload, and its own ceiling.

        The payload is the sealed arm prompt with the lead's brief composed onto it, which is
        what the model actually reads -- and what `global_index` therefore hashes, so two
        dispatches of one pair with different briefs are different tasks rather than a resume.
        """

        return TaskExecutionSpec(
            spec_id=self.invocation_id,
            task_type=self.payload.get("task_type", ""),
            task_data=compose_prompt(self.payload, self.brief_text),
            billed_cost_limit=round(
                standard_cap * TIER_MULTIPLIERS.get(self.budget_tier, 1.0), 6),
            required=self.required,
            budget_scope=self.budget_scope,
        )


#: Appended to the arm's sealed user prompt at dispatch. The sealed plan vouches for the
#: *template*; the delivered text is template + brief, and both halves are recorded — the
#: brief on the delegation record, and the composed hash as `delivered_prompt_sha256` — so
#: what the model actually read stays reconstructible.
def compose_prompt(payload: Dict[str, Any], brief_text: str) -> Dict[str, Any]:
    if not brief_text:
        return payload
    composed = dict(payload)
    composed["rendered_user_prompt"] = payload.get("rendered_user_prompt", "") + brief_text
    return composed


@dataclass
class JobOutcome:
    """What became of one job, including when nothing came back."""

    invocation_id: str
    arm_id: str
    work_unit_id: str
    pr_number: int
    budget_tier: str
    budget_cap: Optional[float] = None
    status: str = "failed"
    wall_seconds: float = 0.0
    #: Billed — what was actually paid, and what every cap is enforced against.
    cost: float = 0.0
    #: The no-cache counterfactual, for reporting only. Never sum this and call it spend.
    nominal_cost: float = 0.0
    #: This job's own usage. It used to be the enclosing tier's total stamped onto every job
    #: in it — 59 jobs carrying 9 distinct values on smoke4 — which made per-arm token
    #: attribution impossible and, summed, reported $1,141 against a real $21.
    token_usage: Optional[Dict[str, float]] = None
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    verification_artifacts: List[Dict[str, Any]] = field(default_factory=list)
    #: `{"reason": ..., "detail": ...}` when the arm submitted nothing. Carried here because
    #: this dataclass is a closed list between the child result and the response row: a field
    #: the tool records and this does not declare is dropped silently, with the suite green.
    abstention: Optional[Dict[str, str]] = None
    result_sha256: Optional[str] = None
    #: sha256 of the user prompt as delivered, including any brief. Differs from the sealed
    #: `rendered_prompt_sha256` exactly when a brief was attached.
    delivered_prompt_sha256: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_run(cls, job: JobSpec, child: ChildRun, *, elapsed: float,
                 delivered_prompt_sha256: str) -> "JobOutcome":
        """One finished child as the ledger's row.

        Everything here comes off the typed `ChildRun`: the result is the arm's own
        `ReviewArmResult`, not a re-dumped dict read by key, and the outcome is built from what
        the orchestrator persisted for the task that was scheduled -- so a job that paused on
        its cap has a row with its spend on it instead of being absent.
        """

        result = child.result
        candidates = list(getattr(result, "candidates", None) or [])
        artifacts = list(getattr(result, "verification_artifacts", None) or [])
        return cls(
            invocation_id=job.invocation_id,
            arm_id=job.arm_id,
            work_unit_id=job.work_unit_id,
            pr_number=job.pr_number,
            budget_tier=job.budget_tier,
            budget_cap=child.spec.billed_cost_limit,
            status=ledger_status(child),
            # This job's own span. The wave's elapsed time is the fallback only, and that case
            # is now the exception rather than every row.
            wall_seconds=round(float(child.outcome.wall_seconds or elapsed), 3),
            cost=float(child.outcome.billed_cost or 0.0),
            nominal_cost=float(child.outcome.nominal_cost or 0.0),
            token_usage={
                "billed_cost": float(child.outcome.billed_cost or 0.0),
                "nominal_cost": float(child.outcome.nominal_cost or 0.0),
                "turns": int(child.outcome.turns or 0),
            },
            candidates=candidates,
            verification_artifacts=artifacts,
            abstention=getattr(result, "abstention", None),
            result_sha256=_digest(candidates) if candidates else None,
            delivered_prompt_sha256=delivered_prompt_sha256,
            # Say why. "no terminal submission" was recorded for a job that had actually
            # exhausted its budget, which is the difference between an arm that declined to
            # speak and one that was cut off -- and the two were read as the same thing.
            error=(None if child.succeeded else str(
                child.error
                or child.outcome.reason
                or f"{child.outcome.execution_status.value} (no terminal submission)"
            )),
        )

    def summary(self) -> Dict[str, Any]:
        """The compact view the lead sees: counts, cost, and each claim truncated.

        The first version of this returned no claim text at all, on the reasoning that the
        lead routes and does not re-adjudicate. That stopped being the design when synthesis
        became subtractive -- the lead now decides which claims are the same observation, and
        it cannot do that from a count. So claims are included, and the boundary is truncation
        rather than omission: 800 characters of claim and 400 of requested change, enough to
        judge duplication and not enough to re-review.

        What is still withheld is the rest of the candidate -- evidence requests, proposed
        edits, verification artifacts. Those belong to the gates the lead cannot reach.
        """

        return {
            "invocation_id": self.invocation_id,
            "arm_id": self.arm_id,
            "work_unit_id": self.work_unit_id,
            "status": self.status,
            "candidates": len(self.candidates),
            "verified_edits": len(self.verification_artifacts),
            "cost": round(self.cost, 4),
            # Why it produced nothing, when it produced nothing. Without this the lead cannot
            # tell an arm that looked and declined from one that was cut off mid-review, and
            # those call for opposite responses: accept the abstention, or re-run with more
            # budget. Omitted on success so the common row stays compact.
            **({"reason": self.error} if self.error else {}),
            "claims": [
                {
                    "ordinal": index,
                    "concern_family": item.get("concern_family"),
                    "issue_kind": item.get("issue_kind"),
                    "severity": item.get("severity"),
                    "primary_subject": item.get("primary_subject"),
                    # 240 characters was enough to see *that* a claim exists and too little
                    # to tell whether two of them are the same observation. Judging that is
                    # now a decision the lead actually makes, so it has to be able to read
                    # far enough to make it.
                    "claim": str(item.get("claim") or "")[:800],
                    # What the claim asks for, which is what the merge keys a conflict on:
                    # two claims at one target asking for different transformations are
                    # suppressed together. Duplication is a property of this field.
                    "requested_change": str(item.get("requested_change") or "")[:400],
                }
                for index, item in enumerate(self.candidates)
            ],
            "error": self.error,
        }


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


#: The wave's execution policy. Two values, and both are deliberate.
#:
#: One attempt per job: best-of-n across arms is a different experiment, and running it by
#: accident would make a routing comparison a sampling comparison. Early stop disabled as the
#: ENUM member, not the string -- `ExecutionConfig` does not set `validate_assignment`, so
#: assigning `"disabled"` stores a raw `str` that passes every `==` until `orchestrator.py`
#: calls `.early_stop_mode.value` and raises, which killed every delegate call on the second
#: smoke run.
WAVE_EXECUTION = {"sample_count": 1, "early_stop_mode": EarlyStopMode.DISABLED}

#: Sample statuses, in the vocabulary the delegation ledger has always used. A status outside
#: this map is `failed`: the ledger's job is to separate "declined" from "cut off", and an
#: unrecognised state is neither.
_LEDGER_STATUS = {
    ExecutionStatus.SUCCESS: "success",
    ExecutionStatus.PAUSED_COST_LIMIT: "paused_cost",
    ExecutionStatus.PAUSED_MAX_TURNS: "paused_turns",
}


def ledger_status(child: ChildRun) -> str:
    """How this job ended, in the ledger's four words.

    Read off the typed sample status rather than off a string that had been round-tripped
    through JSON and back -- the old reader took `str(status).rsplit(".")[-1].upper()` and
    looked it up in a dict of spellings, which is a second vocabulary nothing checked against
    the first.

    The finest sample status wins, not `TaskOutcome.execution_status`: the outcome says
    `paused` without saying paused on *what*, and "exhausted its budget" and "ran out of turns"
    call for opposite responses.
    """

    if child.succeeded:
        return "success"
    for sample in reversed(child.outcome.samples or []):
        if sample.status is not None:
            return _LEDGER_STATUS.get(sample.status, "failed")
    return "failed"


async def run_wave(parent_task, jobs: Sequence[JobSpec], *,
                   standard_cap: float, wave: int, logger) -> List[JobOutcome]:
    """Run one wave's jobs as the lead's children, each with its own budget.

    One orchestrator per wave, not one per budget tier. Tiers were groupings only because
    `sample_max_cost` is orchestrator-wide; per-task limits removed that constraint and with it
    three defects -- unbounded concurrency across tiers dispatched by `asyncio.gather`, an
    exception in one tier discarding another tier's completed outcomes *and* their spend, and a
    directory depth the trajectory reader had to hardcode.

    Everything after `run_subtasks` returns derives from work that has already been paid for, so
    none of it may raise: a failure there used to lose the whole wave, because `delegate`
    catches, discards the outcomes and releases the reservations -- the arms ran, cost money and
    left nothing (`pr5_smoke4_rep8`: $3.13 billed, $0.27 reported). The primitive keeps that
    guarantee per child; this keeps it for the projection.
    """

    specs = [job.execution_spec(standard_cap) for job in jobs]
    logger.info("delegating %d job(s) in wave %d: %s",
                len(jobs), wave,
                ", ".join(f"{job.arm_id}@${spec.billed_cost_limit:.2f}"
                          for job, spec in zip(jobs, specs)))

    started = time.monotonic()
    runs, _results = await run_subtasks(
        specs,
        attempt_path=parent_task.attempt_path,
        config=parent_task.config,
        group=f"wave{wave}",
        logger=logger,
        concurrency=DEFAULT_NESTED_CONCURRENCY,
        execution_overrides=WAVE_EXECUTION,
        # Deterministic, and it has to be: the orchestrator fixes its directory from this in
        # `__init__`, and a resumed lead must find the wave it already paid for.
        orchestrator_id=f"{parent_task.data.pr_number}_w{wave}",
        index_path=getattr(parent_task.data, "execution_index_path", None),
        parent_id=getattr(parent_task.data, "episode_id", None),
    )
    elapsed = time.monotonic() - started

    outcomes = []
    for job, spec in zip(jobs, specs):
        child = runs.get(job.invocation_id)
        if child is None:
            # Cannot happen -- the primitive returns one run per spec -- but a missing row here
            # would be a silently shorter ledger, which is the shape of defect this whole
            # contract exists to refuse.
            logger.error("wave %d: no child run came back for %s", wave, job.invocation_id)
            continue
        outcomes.append(JobOutcome.from_run(
            job, child, elapsed=elapsed,
            delivered_prompt_sha256=hashlib.sha256(
                (spec.task_data.get("rendered_user_prompt") or "").encode()).hexdigest()))
    return outcomes


async def run_jobs(parent_task, jobs: Sequence[JobSpec], *,
                   standard_cap: float, wave: int, logger) -> List[JobOutcome]:
    """Group jobs into budget tiers and run every tier concurrently."""

    if not jobs:
        return []
    return await run_wave(parent_task, jobs,
                          standard_cap=standard_cap, wave=wave, logger=logger)
