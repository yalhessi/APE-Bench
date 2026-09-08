"""Spawn specialist subagents from inside a running task, and report what each one cost.

The primitive already existed and was used twice, both hardcoded to one subtask type:
`lean_semantic_evaluation` and `lean_review_gate` each build a subtask, point
`runs_base_dir` at `<parent_attempt>/subtasks/`, run a nested `TaskOrchestrator`, and return
`nested_token_usage`. This generalizes that shape so a *model* can drive it.

Three things here are not obvious and are load-bearing.

**Budgets are grouped, not per-job.** `sample_max_cost` lives on `ExecutionConfig`, which is
orchestrator-wide — there is no per-task cost cap. A tier is therefore not a knob on a job,
it is the set a job is placed into: one nested orchestrator per tier, launched concurrently,
each with its own cap.

**Nested execution runs in-process.** `num_processes=0` selects the orchestrator's
main-process async mode. The lead is itself very likely running inside a `SampleWorker`
process, and spawning a multiprocessing pool from there is the obvious way to deadlock the
run.

**Every subtask keeps its own workspace overlay.** `_ensure_patched_target_workspace` unlinks
the snapshot symlink, builds a lazy overlay in its place, and writes a patch marker that
raises if a different patch is applied. Handing several concurrent subagents one path — each
compiling into it via `lean_verify_edit` — corrupts the thing they are all reading. The
overlay is lazy over the cached base snapshot, so isolation costs a symlink and a patch, not
a rebuild; passing a materialized path between tasks would save little and break much.

A paused job is reported as paused and is never silently retried at a higher tier. Budget
exhaustion is a measurement about routing — the whole reason the trace exists — and quietly
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
    result_sha256: Optional[str] = None
    #: sha256 of the user prompt as delivered, including any brief. Differs from the sealed
    #: `rendered_prompt_sha256` exactly when a brief was attached.
    delivered_prompt_sha256: Optional[str] = None
    error: Optional[str] = None

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


def _wave_config(parent_task, wave: int):
    """A scaffold config for one wave's nested orchestrator.

    One orchestrator per wave, not one per budget tier. Tiers existed as *groupings* only
    because `sample_max_cost` is orchestrator-wide, so varying a job's budget meant running it
    in its own orchestrator. Per-task limits (`ExecutionLimits`, read by the worker before it
    builds the Attempt) removed that constraint, and with it three defects: unbounded
    concurrency across tiers dispatched by `asyncio.gather`, an exception in one tier
    discarding another tier's completed outcomes *and* their spend, and a directory depth that
    the trajectory reader had to hardcode.

    `TIER_MULTIPLIERS` survives as the vocabulary the lead uses to ask for a budget. Only the
    grouping is gone.
    """

    from ape.orchestration.subtasks import DEFAULT_NESTED_CONCURRENCY, nested_config

    return nested_config(
        parent_task.attempt_path, parent_task.config, group=f"wave{wave}",
        concurrency=DEFAULT_NESTED_CONCURRENCY,
        # One attempt per job. Best-of-n across arms is a different experiment, and running it
        # by accident would make a routing comparison a sampling comparison.
        sample_count=1,
        # The ENUM member, not the string: `ExecutionConfig` does not set
        # `validate_assignment`, so assigning `"disabled"` stores a raw `str` that bypasses
        # coercion. `EarlyStopMode` is a `str, Enum` so every `==` still passes and the defect
        # is invisible until `orchestrator.py` calls `.early_stop_mode.value` and raises --
        # which killed every delegate call on the second smoke run.
        early_stop_mode=EarlyStopMode.DISABLED,
    )


async def _sample_facts(orchestrator, results) -> Dict[str, Dict[str, Any]]:
    """Per-task status, cost, usage and duration, from what the orchestrator persisted.

    Read from the per-task records rather than the returned results, because a job that failed
    or paused has no result to read and those are exactly the rows the trace needs.

    `task_outcome.json` is preferred when present: it is written for every scheduled task,
    including the paused ones that produce no `task_result.json`, and it carries billed cost,
    nominal cost, the job's own token usage, its own wall time, and a reason. Falling back to
    the sample records keeps this working for runs made before that file existed.
    """

    from ape.orchestration.persistence import TaskStorage

    facts: Dict[str, Dict[str, Any]] = {}
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        global_index = raw.get("global_index")
        task_id = raw.get("task_id")
        if not global_index or not task_id:
            continue
        task_dir = orchestrator.tasks_dir / str(global_index)

        outcome_path = task_dir / "task_outcome.json"
        if outcome_path.is_file():
            try:
                outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                outcome = None
            if outcome:
                facts[task_id] = {
                    "cost": float(outcome.get("billed_cost") or 0.0),
                    "nominal_cost": float(outcome.get("nominal_cost") or 0.0),
                    "status": _outcome_status(outcome),
                    "reason": outcome.get("reason"),
                    "wall_seconds": float(outcome.get("wall_seconds") or 0.0),
                    "token_usage": _outcome_usage(outcome),
                }
                continue

        storage = TaskStorage(task_dir, str(global_index))
        samples = await storage.load_all_samples()
        billed = nominal = wall = 0.0
        status = None
        for _index, sample in sorted(samples.items()):
            billed += float(sample.get_accumulated_cached_cost() or 0.0)
            nominal += float(sample.get_accumulated_cost() or 0.0)
            for attempt in sample.attempts:
                if attempt.started_at and attempt.completed_at:
                    wall += (attempt.completed_at - attempt.started_at).total_seconds()
            attempt = sample.current_attempt
            if attempt is not None and attempt.status is not None:
                status = str(getattr(attempt.status, "value", attempt.status))
        facts[task_id] = {
            "cost": billed, "nominal_cost": nominal, "status": status,
            "reason": None, "wall_seconds": wall, "token_usage": None,
        }
    return facts


def _outcome_status(outcome: Dict[str, Any]) -> Optional[str]:
    """The sample-level status the ledger's vocabulary is built on.

    `TaskOutcome.execution_status` is coarser than the ledger needs — it says `paused` without
    saying paused on what — so the finest sample status is used when there is one.
    """

    for sample in reversed(outcome.get("samples") or []):
        if sample.get("status"):
            return str(sample["status"])
    return str(outcome.get("execution_status") or "") or None


def _outcome_usage(outcome: Dict[str, Any]) -> Dict[str, float]:
    """This job's own cost figures, in the shape the ledger records."""

    return {
        "billed_cost": float(outcome.get("billed_cost") or 0.0),
        "nominal_cost": float(outcome.get("nominal_cost") or 0.0),
        "turns": int(outcome.get("turns") or 0),
    }


_STATUS_MAP = {
    "SUCCESS": "success",
    "PAUSED_COST_LIMIT": "paused_cost",
    "PAUSED_MAX_TURNS": "paused_turns",
}


def _normalize_status(raw_status: Optional[str], succeeded: bool) -> str:
    if succeeded:
        return "success"
    if not raw_status:
        return "failed"
    key = raw_status.rsplit(".", 1)[-1].upper()
    return _STATUS_MAP.get(key, "failed")


async def run_wave(parent_task, jobs: Sequence[JobSpec], *,
                   standard_cap: float, wave: int, logger) -> List[JobOutcome]:
    """Run one wave's jobs in a single nested orchestrator, each with its own budget."""

    from ape.orchestration import execution_index
    from ape.orchestration.models import EXECUTION_LIMITS_KEY
    from ape.orchestration.orchestrator import TaskOrchestrator
    from ape.tasks.base import create_task_from_data

    config = _wave_config(parent_task, wave)
    caps = {
        job.invocation_id: round(standard_cap * TIER_MULTIPLIERS.get(job.budget_tier, 1.0), 6)
        for job in jobs
    }
    payloads = {}
    for job in jobs:
        payload = dict(compose_prompt(job.payload, job.brief_text))
        # The job's own ceiling travels with it, so one orchestrator can run a `cheap` job
        # beside a `deep` one without either being charged the other's budget.
        payload[EXECUTION_LIMITS_KEY] = {"billed_cost_limit": caps[job.invocation_id]}
        payloads[job.invocation_id] = payload
    tasks = [
        create_task_from_data(dict(payloads[job.invocation_id]), config,
                              task_config_overrides=getattr(
                                  parent_task.config, "task_config_overrides", None))
        for job in jobs
    ]
    orchestrator_id = f"{parent_task.data.pr_number}_w{wave}"
    logger.info("delegating %d job(s) in wave %d: %s",
                len(jobs), wave,
                ", ".join(f"{job.arm_id}@${caps[job.invocation_id]:.2f}" for job in jobs))

    started = time.monotonic()
    orchestrator = TaskOrchestrator(config=config, orchestrator_id=orchestrator_id, logger=logger)
    results = await orchestrator.run(tasks)
    elapsed = time.monotonic() - started

    # Where each invocation actually ran, written down rather than left to be inferred from
    # the directory name later. See `ape/orchestration/execution_index.py`.
    await execution_index.record(
        getattr(parent_task.data, "execution_index_path", None),
        orchestrator, results,
        semantic_ids={payloads[job.invocation_id].get("task_id"): job.invocation_id
                      for job in jobs},
        group=f"wave{wave}",
        parent=getattr(parent_task.data, "episode_id", None),
    )

    # Everything from here to the `return` derives from work that has already been paid for.
    # A failure in any of it used to lose the whole wave: `delegate` catches, discards the
    # outcomes and releases the reservations, so the arms ran, cost money, and left nothing.
    # That is what happened on `pr5_smoke4_rep8` -- $3.13 billed spent, $0.27 reported.
    #
    # So cost attribution is allowed to fail without taking the results with it. A wave with
    # no facts reports zero cost, which is wrong and visible; a wave that raises reports
    # nothing at all, which is wrong and silent.
    try:
        facts = await _sample_facts(orchestrator, results)
    except Exception:  # noqa: BLE001 - see above
        logger.error("wave %d: cost attribution failed; the wave's results are kept and its "
                     "costs will read as zero", wave, exc_info=True)
        facts = {}

    by_task_id = {}
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        by_task_id[raw.get("task_id")] = raw

    outcomes = []
    for job in jobs:
        task_id = job.payload.get("task_id")
        raw = by_task_id.get(task_id) or {}
        fact = facts.get(task_id) or {}
        succeeded = bool(raw.get("success"))
        candidates = list(raw.get("candidates") or [])
        artifacts = list(raw.get("verification_artifacts") or [])
        outcomes.append(JobOutcome(
            invocation_id=job.invocation_id,
            arm_id=job.arm_id,
            work_unit_id=job.work_unit_id,
            pr_number=job.pr_number,
            budget_tier=job.budget_tier,
            budget_cap=caps[job.invocation_id],
            status=_normalize_status(fact.get("status"), succeeded),
            # This job's own span when the outcome recorded one. Falls back to the tier's
            # elapsed only when it did not, and that case is now the exception rather than
            # every row.
            wall_seconds=round(float(fact.get("wall_seconds") or elapsed), 3),
            cost=float(fact.get("cost") or 0.0),
            nominal_cost=float(fact.get("nominal_cost") or 0.0),
            token_usage=fact.get("token_usage"),
            candidates=candidates,
            verification_artifacts=artifacts,
            result_sha256=_digest(candidates) if candidates else None,
            delivered_prompt_sha256=hashlib.sha256(
                (payloads[job.invocation_id].get("rendered_user_prompt") or "").encode()
            ).hexdigest(),
            # Say why. "no terminal submission" was recorded for a job that had actually
            # exhausted its budget, which is the difference between an arm that declined to
            # speak and one that was cut off — and the two were read as the same thing.
            error=(None if succeeded else str(
                raw.get("error")
                or fact.get("reason")
                or (f"{fact['status']} (no terminal submission)"
                    if fact.get("status") else "no terminal submission")
            )),
        ))
    return outcomes


async def run_jobs(parent_task, jobs: Sequence[JobSpec], *,
                   standard_cap: float, wave: int, logger) -> List[JobOutcome]:
    """Group jobs into budget tiers and run every tier concurrently."""

    if not jobs:
        return []
    return await run_wave(parent_task, jobs,
                          standard_cap=standard_cap, wave=wave, logger=logger)
