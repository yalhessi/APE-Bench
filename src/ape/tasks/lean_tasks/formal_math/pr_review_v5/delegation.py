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
TIER_MULTIPLIERS = {"cheap": 0.5, "standard": 1.0, "deep": 2.0}


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
    cost: float = 0.0
    token_usage: Optional[Dict[str, float]] = None
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    verification_artifacts: List[Dict[str, Any]] = field(default_factory=list)
    result_sha256: Optional[str] = None
    #: sha256 of the user prompt as delivered, including any brief. Differs from the sealed
    #: `rendered_prompt_sha256` exactly when a brief was attached.
    delivered_prompt_sha256: Optional[str] = None
    error: Optional[str] = None

    def summary(self) -> Dict[str, Any]:
        """The compact view the lead sees. Deliberately not the full candidate text.

        The lead routes; it does not re-adjudicate. Returning every candidate body would
        spend the lead's context re-reading work the finalization chain will read anyway,
        and would invite it to arbitrate in place of the gates.
        """

        return {
            "invocation_id": self.invocation_id,
            "arm_id": self.arm_id,
            "work_unit_id": self.work_unit_id,
            "status": self.status,
            "candidates": len(self.candidates),
            "verified_edits": len(self.verification_artifacts),
            "cost": round(self.cost, 4),
            "claims": [
                {
                    "ordinal": index,
                    "concern_family": item.get("concern_family"),
                    "issue_kind": item.get("issue_kind"),
                    "severity": item.get("severity"),
                    "primary_subject": item.get("primary_subject"),
                    "claim": str(item.get("claim") or "")[:240],
                }
                for index, item in enumerate(self.candidates)
            ],
            "error": self.error,
        }


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _tier_config(parent_task, tier: str, standard_cap: float, wave: int):
    """A scaffold config for one tier's nested orchestrator."""

    config = parent_task.config.model_copy(deep=True)
    config.execution.sample_max_cost = round(standard_cap * TIER_MULTIPLIERS[tier], 6)
    # In-process: the lead may already be inside a worker process.
    config.execution.num_processes = 0
    # One attempt per job. Best-of-n across arms is a different experiment, and running it
    # by accident would make a routing comparison a sampling comparison.
    config.execution.sample_count = 1
    # The ENUM member, not the string. `ExecutionConfig` does not set `validate_assignment`,
    # so assigning `"disabled"` post-construction stores a raw `str` that bypasses coercion.
    # `EarlyStopMode` is a `str, Enum`, so every `==` comparison still passes and the defect
    # is invisible — until `orchestrator.py` calls `.early_stop_mode.value` and raises
    # `'str' object has no attribute 'value'`, which is what killed every delegate call on
    # the second smoke run.
    config.execution.early_stop_mode = EarlyStopMode.DISABLED
    subtasks = Path(parent_task.attempt_path) / "subtasks" / f"wave{wave}" / tier
    subtasks.mkdir(parents=True, exist_ok=True)
    config.runs_base_dir = subtasks
    return config


async def _sample_facts(orchestrator, results) -> Dict[str, Dict[str, Any]]:
    """Per-task status and cost, read from the samples the orchestrator persisted.

    Taken from the sample records rather than from the returned results, because a job that
    failed or paused has no result to read and those are exactly the rows the trace needs.
    """

    from ape.orchestration.persistence import TaskStorage

    facts: Dict[str, Dict[str, Any]] = {}
    for result in results.task_results:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        global_index = raw.get("global_index")
        task_id = raw.get("task_id")
        if not global_index or not task_id:
            continue
        storage = TaskStorage(orchestrator.tasks_dir / str(global_index), str(global_index))
        samples = await storage.load_all_samples()
        cost = 0.0
        status = None
        for _index, sample in sorted(samples.items()):
            cost += float(sample.get_accumulated_cost() or 0.0)
            attempt = sample.current_attempt
            if attempt is not None and attempt.status is not None:
                status = str(getattr(attempt.status, "value", attempt.status))
        facts[task_id] = {"cost": cost, "status": status}
    return facts


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


async def run_tier(parent_task, tier: str, jobs: Sequence[JobSpec], *,
                   standard_cap: float, wave: int, logger) -> List[JobOutcome]:
    """Run one budget tier's jobs in a single nested orchestrator."""

    from ape.orchestration.orchestrator import TaskOrchestrator
    from ape.tasks.base import create_task_from_data

    config = _tier_config(parent_task, tier, standard_cap, wave)
    cap = config.execution.sample_max_cost
    payloads = {
        job.invocation_id: compose_prompt(job.payload, job.brief_text) for job in jobs
    }
    tasks = [
        create_task_from_data(dict(payloads[job.invocation_id]), config,
                              task_config_overrides=getattr(
                                  parent_task.config, "task_config_overrides", None))
        for job in jobs
    ]
    orchestrator_id = f"{parent_task.data.pr_number}_w{wave}_{tier}"
    logger.info("delegating %d job(s) at tier %s (cap=%s): %s",
                len(jobs), tier, cap, ", ".join(job.arm_id for job in jobs))

    started = time.monotonic()
    orchestrator = TaskOrchestrator(config=config, orchestrator_id=orchestrator_id, logger=logger)
    results = await orchestrator.run(tasks)
    elapsed = time.monotonic() - started

    facts = await _sample_facts(orchestrator, results)
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
            budget_tier=tier,
            budget_cap=cap,
            status=_normalize_status(fact.get("status"), succeeded),
            # Wall time is per tier, not per job: the tier's jobs run concurrently inside one
            # orchestrator, so attributing the whole span to each would multiply it.
            wall_seconds=round(elapsed, 3),
            cost=float(fact.get("cost") or 0.0),
            token_usage=(
                results.total_token_usage.model_dump(mode="json")
                if hasattr(results.total_token_usage, "model_dump") else None
            ),
            candidates=candidates,
            verification_artifacts=artifacts,
            result_sha256=_digest(candidates) if candidates else None,
            delivered_prompt_sha256=hashlib.sha256(
                (payloads[job.invocation_id].get("rendered_user_prompt") or "").encode()
            ).hexdigest(),
            error=(None if succeeded else str(raw.get("error") or "no terminal submission")),
        ))
    return outcomes


async def run_jobs(parent_task, jobs: Sequence[JobSpec], *,
                   standard_cap: float, wave: int, logger) -> List[JobOutcome]:
    """Group jobs into budget tiers and run every tier concurrently."""

    if not jobs:
        return []
    by_tier: Dict[str, List[JobSpec]] = {}
    for job in jobs:
        tier = job.budget_tier if job.budget_tier in TIER_MULTIPLIERS else "standard"
        by_tier.setdefault(tier, []).append(job)

    batches = await asyncio.gather(*(
        run_tier(parent_task, tier, tier_jobs,
                 standard_cap=standard_cap, wave=wave, logger=logger)
        for tier, tier_jobs in sorted(by_tier.items())
    ))
    return [outcome for batch in batches for outcome in batch]
