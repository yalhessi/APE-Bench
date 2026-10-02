"""`run --resume` on a run that closed partial: requeue what failed on errors, keep the rest.

Before this, `--resume` was refused once a run had written its outputs, and a partial run's only
way back was `--redo`. On 2026-10-01 that meant re-running H-claude rep 2's 13 good sessions,
about 21M subscription tokens, to replace two that a spent usage limit had killed.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from types import SimpleNamespace

import pytest

from ape.orchestration.models import Attempt, ExecutionStatus, Sample
from ape.orchestration.persistence import TaskStorage
from src.mathlib_review.review import runner
from src.mathlib_review.run_state import RunState, ledger, state_of

LOG = logging.getLogger(__name__)
RUN = "probe_dev_x_rep2"


def _sample(task_dir, statuses):
    now = datetime.now()
    asyncio.run(TaskStorage(task_dir, task_dir.name).save_sample(Sample(
        sample_id=f"{task_dir.name}_0", sample_index=0, task_global_index=task_dir.name,
        attempts=[Attempt(attempt_id=i + 1, path=task_dir / f"a{i}", status=status,
                          created_at=now, max_turns=160, cost_limit=None)
                  for i, status in enumerate(statuses)],
        created_at=now, updated_at=now)))
    (task_dir / "task_result.json").write_text(json.dumps(
        {"success": statuses[-1] is ExecutionStatus.SUCCESS}))


@pytest.fixture
def partial(tmp_path, monkeypatch):
    """A solo run closed partial: one session lost to the limit, one success."""

    results = tmp_path / "results"
    monkeypatch.setattr(runner, "run_dir", lambda name: results / name)
    out = results / RUN
    out.mkdir(parents=True)
    (out / "run_manifest.json").write_text(json.dumps({"completion_status": "partial"}))
    for name in ("run_plan.json", "run_plan_revision_2.json", "agenda.json", "findings.jsonl",
                 "issues.jsonl", "anchoring.jsonl", "context_trace.jsonl",
                 "execution_index.jsonl"):
        (out / name).write_text("{}\n")
    (out / "evidence").mkdir()
    (out / "evidence" / "packets.jsonl").write_text("{}\n")
    (out / "stages.jsonl").write_text(json.dumps({"stage": "run"}) + "\n")

    base = tmp_path / ".ape" / "runs"
    _sample(base / RUN / "tasks" / "spent", [ExecutionStatus.FAILED_ERROR] * 4)
    _sample(base / RUN / "tasks" / "done", [ExecutionStatus.SUCCESS])
    scaffold = SimpleNamespace(runs_base_dir=base, execution=SimpleNamespace(task_max_retries=3))
    dataset = SimpleNamespace(run_name=RUN, routing_mode="solo")
    return SimpleNamespace(out=out, base=base, scaffold=scaffold, dataset=dataset)


def test_the_guard_lets_a_partial_run_resume_and_still_refuses_a_complete_one(partial):
    runner.guard_run_name(partial.dataset, LOG, partial.scaffold, resume=True)
    (partial.out / "run_manifest.json").write_text(json.dumps({"completion_status": "complete"}))
    with pytest.raises(RuntimeError, match="finished"):
        runner.guard_run_name(partial.dataset, LOG, partial.scaffold, resume=True)


def test_a_reopen_requeues_the_failed_session_and_keeps_the_success(partial):
    rows = asyncio.run(runner.reopen_partial_run(partial.dataset, partial.scaffold, LOG))
    assert [(row["task"], row["attempts"], row["orchestrator"]) for row in rows] == [
        ("spent", 4, RUN)]

    tasks = partial.base / RUN / "tasks"
    assert not (tasks / "spent" / "task_result.json").exists()
    assert (tasks / "done" / "task_result.json").exists()

    # Closed outputs cleared; the plan, the agenda and the append-only logs kept.
    kept = sorted(p.name for p in partial.out.iterdir())
    assert kept == ["agenda.json", "context_trace.jsonl", "execution_index.jsonl",
                    "run_plan.json", "run_plan_revision_2.json", "stages.jsonl"]
    assert state_of(partial.out) is RunState.RUNNING

    reopen = ledger(partial.out)[-1]
    assert reopen["stage"] == "reopen" and reopen["transition"] == "partial -> running"
    assert [row["task"] for row in reopen["identity"]["requeued"]] == ["spent"]
    assert "findings.jsonl" in reopen["identity"]["cleared"]
    assert "evidence" in reopen["identity"]["cleared"]


def test_a_dry_reopen_writes_nothing(partial):
    rows = asyncio.run(runner.reopen_partial_run(partial.dataset, partial.scaffold, LOG,
                                                 dry_run=True))
    assert [row["task"] for row in rows] == ["spent"]
    assert (partial.out / "findings.jsonl").exists()
    assert state_of(partial.out) is RunState.PARTIAL
    assert len(ledger(partial.out)) == 1


def test_a_partial_with_nothing_failed_on_errors_is_its_result(partial):
    """A model failure or a coverage gap is what the run measured; there is no outage to undo."""

    _sample(partial.base / RUN / "tasks" / "spent", [ExecutionStatus.FAILED_MODEL])
    with pytest.raises(RuntimeError, match="nothing to requeue"):
        asyncio.run(runner.reopen_partial_run(partial.dataset, partial.scaffold, LOG))
    assert (partial.out / "findings.jsonl").exists()


def test_a_lead_run_is_refused(partial):
    partial.dataset.routing_mode = "lead"
    with pytest.raises(RuntimeError, match="nested orchestrators"):
        asyncio.run(runner.reopen_partial_run(partial.dataset, partial.scaffold, LOG))


def test_a_run_that_is_not_partial_is_left_alone(partial):
    (partial.out / "run_manifest.json").write_text(json.dumps({"completion_status": "complete"}))
    assert asyncio.run(runner.reopen_partial_run(partial.dataset, partial.scaffold, LOG)) == []
    assert (partial.out / "findings.jsonl").exists()


def test_both_run_paths_reopen_on_resume():
    import inspect

    source = inspect.getsource(runner.run)
    assert "await reopen_partial_run(dataset, scaffold, logger, dry_run=True)" in source
    assert "await reopen_partial_run(dataset, scaffold, logger)" in source


def test_a_dry_resume_says_what_the_resume_would_do():
    """`run --resume` without `--execute` went to the plan path without the flag, so it warned
    that the real run would refuse the spent name -- of a run the resume accepts."""

    import inspect

    from src.mathlib_review.review import cli

    assert "_plan(args.config, overrides, logger, resume=args.resume," in inspect.getsource(cli._run)
    assert "resume=resume" in inspect.getsource(cli._plan)
