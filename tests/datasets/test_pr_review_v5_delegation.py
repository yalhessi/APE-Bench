"""Spawning subagents, and closing the books afterwards.

Two clusters. The first is about *how* jobs run: budgets are orchestrator-wide, so a tier is
a grouping and not a per-job knob, and nested execution must stay in-process or a lead
running inside a worker deadlocks the run. The second is about the ledger: v5 replaces v4's
"every expected work unit produced exactly one response" — which a pruning lead cannot
satisfy — with a disposition rule that gives the same guarantee without demanding exhaustive
coverage.

The ledger tests matter more than they look. A run whose books do not balance is not a
crashed run; it is a run that quietly measured a different system than the one it claims.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from ape.orchestration.config import EarlyStopMode
from ape.tasks.lean_tasks.formal_math.pr_review_v5.delegation import (
    TIER_MULTIPLIERS,
    JobSpec,
    _normalize_status,
    _tier_config,
    run_jobs,
)
from src.datasets.pr_review_v4.io import sha256_bytes, canonical_json_bytes
from src.datasets.pr_review_v5.schema import ReviewAgenda, V5RunPlan
from src.datasets.pr_review_v5.trace import ReconciliationError, reconcile, routing_report


# --------------------------------------------------------------------------------------
# tiers
# --------------------------------------------------------------------------------------

def _parent(tmp_path, cap=0.25):
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    return SimpleNamespace(
        config=ApeAgentConfig(),
        attempt_path=tmp_path,
        data=SimpleNamespace(pr_number=33098),
        logger=SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None),
    )


def test_each_tier_gets_its_own_cap(tmp_path):
    """`sample_max_cost` is orchestrator-wide — there is no per-task cap — so the only way
    to give two jobs different budgets is to run them in different orchestrators."""

    parent = _parent(tmp_path)
    caps = {
        tier: _tier_config(parent, tier, 0.25, wave=1).execution.sample_max_cost
        for tier in TIER_MULTIPLIERS
    }
    assert caps == {"cheap": 0.125, "standard": 0.25, "deep": 0.5}


def test_nested_execution_stays_in_process(tmp_path):
    """The lead is very likely already inside a `SampleWorker`; spawning a multiprocessing
    pool from there is the obvious way to deadlock the run."""

    config = _tier_config(_parent(tmp_path), "standard", 0.25, wave=1)
    assert config.execution.num_processes == 0


def test_one_attempt_per_job(tmp_path):
    """Best-of-n across arms is a different experiment; running it by accident would turn a
    routing comparison into a sampling comparison."""

    config = _tier_config(_parent(tmp_path), "standard", 0.25, wave=1)
    assert config.execution.sample_count == 1
    # The TYPE, not just the value. `EarlyStopMode` is a `str, Enum`, so a raw string passes
    # every `==` check while `orchestrator.py`'s `.early_stop_mode.value` raises on it — and
    # `ExecutionConfig` sets no `validate_assignment`, so a post-construction assignment of
    # `"disabled"` is never coerced. That is precisely how every delegate call failed with
    # `'str' object has no attribute 'value'` while this test passed.
    assert isinstance(config.execution.early_stop_mode, EarlyStopMode)
    assert config.execution.early_stop_mode is EarlyStopMode.DISABLED
    # And the thing the raw string actually broke.
    assert config.execution.early_stop_mode.value == "disabled"


def test_every_tier_config_field_survives_assignment(tmp_path):
    """`ExecutionConfig` does not validate on assignment, so anything `_tier_config` sets
    post-construction keeps whatever type it was handed. Enum-typed fields are the ones that
    fail late and silently."""

    for tier in TIER_MULTIPLIERS:
        config = _tier_config(_parent(tmp_path), tier, 0.25, wave=1)
        assert isinstance(config.execution.num_processes, int)
        assert isinstance(config.execution.sample_count, int)
        assert isinstance(config.execution.sample_max_cost, float)
        assert isinstance(config.execution.early_stop_mode, EarlyStopMode)


def test_subtasks_are_nested_under_the_parent_attempt(tmp_path):
    config = _tier_config(_parent(tmp_path), "deep", 0.25, wave=2)
    assert config.runs_base_dir == tmp_path / "subtasks" / "wave2" / "deep"
    assert config.runs_base_dir.is_dir()


def test_waves_do_not_collide(tmp_path):
    parent = _parent(tmp_path)
    first = _tier_config(parent, "standard", 0.25, wave=1).runs_base_dir
    second = _tier_config(parent, "standard", 0.25, wave=2).runs_base_dir
    assert first != second


def test_jobs_are_grouped_into_one_orchestrator_per_tier(tmp_path, monkeypatch):
    seen = []

    async def fake_run_tier(parent, tier, jobs, **kwargs):
        seen.append((tier, [job.invocation_id for job in jobs]))
        return []

    import ape.tasks.lean_tasks.formal_math.pr_review_v5.delegation as module

    monkeypatch.setattr(module, "run_tier", fake_run_tier)
    jobs = [
        JobSpec("a#x", "x", "a", 1, {}, budget_tier="cheap"),
        JobSpec("b#y", "y", "b", 1, {}, budget_tier="deep"),
        JobSpec("c#z", "z", "c", 1, {}, budget_tier="cheap"),
    ]
    asyncio.run(run_jobs(_parent(tmp_path), jobs, standard_cap=0.25, wave=1,
                         logger=SimpleNamespace(info=lambda *a, **k: None)))
    grouped = dict(seen)
    assert set(grouped) == {"cheap", "deep"}
    assert sorted(grouped["cheap"]) == ["a#x", "c#z"]
    assert grouped["deep"] == ["b#y"]


def test_an_unknown_tier_falls_back_to_standard(tmp_path, monkeypatch):
    seen = []

    async def fake_run_tier(parent, tier, jobs, **kwargs):
        seen.append(tier)
        return []

    import ape.tasks.lean_tasks.formal_math.pr_review_v5.delegation as module

    monkeypatch.setattr(module, "run_tier", fake_run_tier)
    asyncio.run(run_jobs(_parent(tmp_path),
                         [JobSpec("a#x", "x", "a", 1, {}, budget_tier="lavish")],
                         standard_cap=0.25, wave=1,
                         logger=SimpleNamespace(info=lambda *a, **k: None)))
    assert seen == ["standard"]


def test_a_paused_job_is_reported_as_paused_not_failed():
    """Budget exhaustion is a fact about routing — the thing being measured — so it must be
    distinguishable from a job that broke."""

    assert _normalize_status("ExecutionStatus.PAUSED_COST_LIMIT", False) == "paused_cost"
    assert _normalize_status("PAUSED_MAX_TURNS", False) == "paused_turns"
    assert _normalize_status("FAILED_ERROR", False) == "failed"
    assert _normalize_status(None, True) == "success"


# --------------------------------------------------------------------------------------
# the ledger
# --------------------------------------------------------------------------------------

def _agenda(proposal_ids):
    from src.datasets.pr_review_v4.io import sealed_model
    from src.datasets.pr_review_v5.schema import AgendaProposal, ReviewArm

    proposals = [
        sealed_model(
            AgendaProposal, proposal_id=pid, invocation_id=pid,
            arm_id=pid.split("#")[1], work_unit_id=pid.split("#")[0],
            episode_id="ep:1", pr_number=1, site_change_ids=["change:a"],
            eligible=True, mandatory=pid.endswith("#generalist"),
            prompt_sha256="a" * 64, cost_hint=0.079, rationale="r",
        )
        for pid in proposal_ids
    ]
    return sealed_model(
        ReviewAgenda, agenda_id="agenda:t", run_name="t", routing_mode="lead",
        release="rel", arms=[], proposals=proposals,
        scheduler_version="s", renderer_version="r",
    )


def _plan():
    plan = V5RunPlan(
        run_id="v5run:t", run_name="t", routing_mode="lead", agenda_sha256="a" * 64,
        release="rel", prompt_sha256_by_invocation={}, arm_sha256_by_id={},
        model_name="m", scaffold_config_sha256="b" * 64,
        lead_cost_cap=1.0, standard_budget_cap=0.25, per_pr_cost_cap=4.0,
        source_sha256="",
    )
    return plan.model_copy(update={"source_sha256": sha256_bytes(canonical_json_bytes(
        plan.model_dump(mode="json", exclude={"source_sha256"})))})


def _record(invocation_id, disposition, **overrides):
    row = {
        "schema_version": "v5-delegation1", "invocation_id": invocation_id,
        "proposal_id": invocation_id, "arm_id": invocation_id.split("#")[1],
        "work_unit_id": invocation_id.split("#")[0], "pr_number": 1,
        "disposition": disposition, "reason": "", "status": (
            None if disposition == "pruned" else "success"),
        "cost": None if disposition == "pruned" else 0.05, "context_calls": [],
    }
    row.update(overrides)
    return row


RESULTS = SimpleNamespace(total_cost=0.4, wall_clock_time=12.0)


def test_a_balanced_ledger_closes():
    agenda = _agenda(["wu:1#generalist", "wu:1#proof_golf", "wu:1#duplication"])
    delegations = [
        _record("wu:1#generalist", "mandatory"),
        _record("wu:1#proof_golf", "proposed"),
        _record("wu:1#duplication", "pruned"),
    ]
    manifest = reconcile(
        agenda=agenda, delegations=delegations, responses=[], plan=_plan(),
        results=RESULTS, issues_total=3,
    )
    assert manifest.completion_status == "complete"
    assert (manifest.proposals_total, manifest.delegated, manifest.pruned) == (3, 2, 1)
    assert manifest.mandatory == 1


def test_an_unaccounted_proposal_refuses_to_close():
    """The rule that replaces v4's exhaustive-coverage assertion. A proposal that is neither
    run nor explained is a silent gap in what the system looked at."""

    agenda = _agenda(["wu:1#generalist", "wu:1#proof_golf"])
    with pytest.raises(ReconciliationError, match="no disposition"):
        reconcile(agenda=agenda, delegations=[_record("wu:1#generalist", "mandatory")],
                  responses=[], plan=_plan(), results=RESULTS, issues_total=0)


def test_a_job_outside_the_sealed_agenda_refuses_to_close():
    """A pair the agenda never enumerated has a prompt the plan did not vouch for, which is
    the pre-registration failing open."""

    agenda = _agenda(["wu:1#generalist"])
    delegations = [
        _record("wu:1#generalist", "mandatory"),
        _record("wu:9#proof_golf", "agent_added"),
    ]
    with pytest.raises(ReconciliationError, match="never enumerated"):
        reconcile(agenda=agenda, delegations=delegations, responses=[], plan=_plan(),
                  results=RESULTS, issues_total=0)


def test_a_duplicate_job_refuses_to_close():
    agenda = _agenda(["wu:1#generalist"])
    delegations = [
        _record("wu:1#generalist", "mandatory"),
        _record("wu:1#generalist", "proposed"),
    ]
    with pytest.raises(ReconciliationError, match="twice"):
        reconcile(agenda=agenda, delegations=delegations, responses=[], plan=_plan(),
                  results=RESULTS, issues_total=0)


def test_an_orphan_response_refuses_to_close():
    agenda = _agenda(["wu:1#generalist"])
    with pytest.raises(ReconciliationError, match="no recorded job"):
        reconcile(agenda=agenda, delegations=[_record("wu:1#generalist", "mandatory")],
                  responses=[{"invocation_id": "wu:1#ghost", "candidates": []}],
                  plan=_plan(), results=RESULTS, issues_total=0)


def test_failed_and_paused_jobs_are_counted_not_dropped():
    """A summary that reports only successes makes budget exhaustion invisible."""

    agenda = _agenda(["wu:1#generalist", "wu:1#proof_golf", "wu:1#duplication"])
    delegations = [
        _record("wu:1#generalist", "mandatory"),
        _record("wu:1#proof_golf", "proposed", status="paused_cost"),
        _record("wu:1#duplication", "proposed", status="failed"),
    ]
    manifest = reconcile(agenda=agenda, delegations=delegations, responses=[],
                         plan=_plan(), results=RESULTS, issues_total=0)
    assert (manifest.succeeded, manifest.paused, manifest.failed) == (1, 1, 1)
    assert manifest.completion_status == "failed"


def test_spend_is_the_orchestrator_plus_everything_nested_under_it():
    """`results.total_cost` sees only the leads' own conversations. Floor and specialist jobs
    run in nested orchestrators it cannot observe, so their spend has to come off the ledger —
    omitting it is how the held-out run reported $6.54 against a true $19.17."""

    agenda = _agenda(["wu:1#generalist"])
    manifest = reconcile(agenda=agenda, delegations=[_record("wu:1#generalist", "mandatory")],
                         responses=[], plan=_plan(), results=RESULTS, issues_total=0)
    assert manifest.total_cost == pytest.approx(0.4 + 0.05)
    assert manifest.cost_breakdown == {"lead": 0.4, "nested": 0.05, "extra": 0.0}


def test_a_job_that_ran_without_a_recorded_cost_refuses_to_close():
    """Unattributed spend: the money left the account and the ledger cannot say for what."""

    agenda = _agenda(["wu:1#generalist"])
    record = _record("wu:1#generalist", "mandatory")
    record["cost"] = None
    with pytest.raises(ReconciliationError, match="no cost"):
        reconcile(agenda=agenda, delegations=[record], responses=[], plan=_plan(),
                  results=RESULTS, issues_total=0)


def test_the_routing_report_names_both_degenerate_cases():
    """If the lead pruned nothing, or ran nothing, the mechanism did not engage — and a
    recall number would be measuring the arms rather than the delegation."""

    fanned = [_record("wu:1#generalist", "mandatory"), _record("wu:1#proof_golf", "proposed")]
    assert routing_report(fanned)["degenerate_fanout"] is True
    mixed = fanned + [_record("wu:1#duplication", "pruned")]
    report = routing_report(mixed)
    assert report["degenerate_fanout"] is False
    assert report["jobs_delegated"] == 2 and report["jobs_pruned"] == 1
    assert routing_report([_record("wu:1#a", "pruned")])["degenerate_silent"] is True
