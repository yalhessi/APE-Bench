"""Every scheduled task leaves an execution record, and caps are enforced on billed cost.

Both properties come from one incident. A `family_design` arm on PR 33117 ran for 184 seconds
and was billed real money, then reached the delegation ledger as `status=failed, cost=0.0`.
That row satisfied a mandatory-coverage check, which set `units_without_specialist` to empty,
which is the field used to green-light a specialist-only run — and the arm was written up as
having abstained.

Two independent defects produced it:

* the conversation paused on **nominal** cost while `Sample.can_execute` decided resumability
  on **billed** cost, so a job that had exhausted its cap looked resumable;
* `_try_aggregate` returned early for a resumable task without writing anything at all, so the
  spend had nowhere to be recorded.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ape.orchestration.models import (
    Attempt, ExecutionStatus, Sample, TaskExecutionStatus, TaskOutcome,
)


def _attempt(attempt_id, status, *, nominal, billed, turns=3):
    start = datetime(2026, 9, 7, 12, 0, 0)
    return Attempt(
        attempt_id=attempt_id,
        path=f"/tmp/attempt_{attempt_id}",
        status=status,
        created_at=start,
        started_at=start,
        completed_at=start + timedelta(seconds=30),
        cost=nominal,
        cached_cost=billed,
        turns=turns,
        max_turns=40,
        cost_limit=0.30,
    )


def _sample(attempts, index=0):
    return Sample(
        sample_id=f"s{index}",
        task_global_index="gi",
        sample_index=index,
        attempts=attempts,
        created_at=datetime(2026, 9, 7, 12, 0, 0),
        updated_at=datetime(2026, 9, 7, 12, 1, 0),
    )


def test_a_cost_paused_sample_is_not_resumable_once_billed_reaches_the_cap():
    """The exact 33117 numbers: nominal $0.3017, billed $0.1218, cap $0.30.

    Under the old rule this returned True — the sample looked resumable, so it was never
    aggregated and its spend was never booked. The conversation now pauses on billed too, so a
    sample only reaches this state having actually been billed the cap.
    """

    exhausted = _sample([_attempt(1, ExecutionStatus.PAUSED_COST_LIMIT,
                                 nominal=0.75, billed=0.30)])
    assert exhausted.can_execute(max_retries=3, max_turns=40, sample_max_cost=0.30) is False


def test_billed_cost_accumulates_across_attempts():
    """Charging only the last attempt let a sample pause and resume indefinitely, each attempt
    staying under the cap on its own."""

    sample = _sample([
        _attempt(1, ExecutionStatus.PAUSED_COST_LIMIT, nominal=0.40, billed=0.18),
        _attempt(2, ExecutionStatus.PAUSED_COST_LIMIT, nominal=0.40, billed=0.17),
    ])
    assert sample.get_accumulated_cached_cost() == pytest.approx(0.35)
    assert sample.can_execute(max_retries=3, max_turns=40, sample_max_cost=0.30) is False


def test_a_paused_task_records_its_spend_rather_than_reading_as_a_free_failure():
    """The property the ledger needed: paused is not failed, and it is not $0.00."""

    samples = {0: _sample([_attempt(1, ExecutionStatus.PAUSED_COST_LIMIT,
                                    nominal=0.3017, billed=0.1218)])}
    outcome = TaskOutcome.from_samples(
        task_id="t", task_type="arm", global_index="gi", samples=samples,
        max_retries=3, max_turns=40, sample_max_cost=0.30, has_result=False)

    assert outcome.execution_status is TaskExecutionStatus.PAUSED
    assert outcome.has_result is False
    assert outcome.billed_cost == pytest.approx(0.1218)
    assert outcome.nominal_cost == pytest.approx(0.3017)
    assert outcome.reason


def test_execution_status_is_independent_of_the_domain_verdict():
    """A judgment task that correctly returns a negative verdict completed successfully.

    `BaseTaskResult.success` is the domain answer; `execution_status` is whether the task ran.
    Conflating them is what makes a valid negative judgment look like an infrastructure
    failure.
    """

    samples = {0: _sample([_attempt(1, ExecutionStatus.SUCCESS, nominal=0.10, billed=0.04)])}
    outcome = TaskOutcome.from_samples(
        task_id="t", task_type="judge", global_index="gi", samples=samples,
        max_retries=3, max_turns=40, sample_max_cost=1.0, has_result=True)

    assert outcome.execution_status is TaskExecutionStatus.COMPLETED
    assert outcome.has_result is True


def test_the_sample_level_survives_because_the_judge_votes():
    """task -> samples -> attempts, not task -> attempts: the judge runs sample_count 3, and
    collapsing the sample level would lose the majority-vote structure it depends on."""

    samples = {
        i: _sample([_attempt(1, ExecutionStatus.SUCCESS, nominal=0.10, billed=0.04)], index=i)
        for i in range(3)
    }
    outcome = TaskOutcome.from_samples(
        task_id="t", task_type="judge", global_index="gi", samples=samples,
        max_retries=3, max_turns=40, sample_max_cost=1.0, has_result=True)

    assert [s.sample_index for s in outcome.samples] == [0, 1, 2]
    assert outcome.billed_cost == pytest.approx(0.12)


def test_a_failed_task_is_distinguishable_from_a_paused_one():
    samples = {0: _sample([_attempt(1, ExecutionStatus.FAILED_MODEL, nominal=0.05, billed=0.02)])}
    outcome = TaskOutcome.from_samples(
        task_id="t", task_type="arm", global_index="gi", samples=samples,
        max_retries=0, max_turns=40, sample_max_cost=0.30, has_result=False)

    assert outcome.execution_status is TaskExecutionStatus.FAILED
    assert outcome.billed_cost == pytest.approx(0.02)


# --- a task whose samples all failed: no fake result, the failure in the outcome --------------
#
# `docs/todo/framework-defects-2026-09.md` §4. The worker wrote a bare
# `BaseTaskResult(success=False, error="All samples failed: [...]")` as `task_result.json` and
# then an outcome with `has_result=True`, so the task read `completed` having concluded nothing.
# Asserted on a real `SampleWorker` and real `TaskStorage`, not on a stand-in.


def _failed_attempt(error="Exception: provider said no"):
    attempt = _attempt(1, ExecutionStatus.FAILED_ERROR, nominal=0.05, billed=0.02)
    attempt.error_message = error
    return attempt


def _worker(tmp_path):
    import threading

    from ape.orchestration.worker import SampleWorker
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    config = ApeAgentConfig()
    config.execution.task_max_retries = 0
    return SampleWorker(
        config=config, scaffold_type="ape_agent", orchestrator_dir=tmp_path, worker_id=0,
        early_stop_events={}, aggregation_lock=threading.Lock(), execution_mode_name="test",
        orchestrator_start_time=datetime(2026, 10, 22))


def _store_failed_task(tmp_path, gi="gi"):
    import asyncio

    from ape.orchestration.persistence import TaskStorage

    task_dir = tmp_path / "tasks" / gi
    storage = TaskStorage(task_dir, gi)
    sample = _sample([_failed_attempt()])
    sample.task_global_index = gi
    asyncio.run(storage.save_sample(sample))
    return storage


def test_an_all_failed_task_writes_no_result_and_a_failed_outcome(tmp_path):
    import asyncio
    import json

    worker = _worker(tmp_path)
    storage = _store_failed_task(tmp_path)
    job = {"task_global_index": "gi", "task_type": "lean_judgment"}
    asyncio.run(worker._try_aggregate(job, storage, {"task_id": "t"}, "lean_judgment"))

    assert not (storage.task_dir / "task_result.json").exists()
    outcome = TaskOutcome.model_validate(
        json.loads((storage.task_dir / "task_outcome.json").read_text()))
    assert outcome.execution_status is TaskExecutionStatus.FAILED
    assert outcome.has_result is False
    assert outcome.billed_cost == pytest.approx(0.02)
    # The attempt's error reaches the outcome (it was read from a field `Attempt` lacks).
    assert outcome.samples[0].attempts[0].error == "Exception: provider said no"
    progress = asyncio.run(worker.progress_manager.read())
    assert progress.completed_task_indices == ["gi"] and progress.successful_tasks == 0


def test_a_failed_child_says_why_from_its_outcome(tmp_path):
    import asyncio

    from ape.orchestration.models import TaskExecutionSpec
    from ape.orchestration.subtasks import collect_child_runs
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.base import create_task_from_data
    from types import SimpleNamespace

    payload = {"task_type": "lean_judgment", "task_id": "j", "target_code": "a",
               "original_code": "b", "task_description": "d", "reference_implementation": "r",
               "gold_diff": "g", "filename": "f.lean", "target_workspace": {"name": "ws"}}
    config = ApeAgentConfig()
    config.execution.task_max_retries = 0
    task = create_task_from_data(payload, config)
    _store_failed_task(tmp_path, task.data.global_index)
    spec = TaskExecutionSpec(spec_id="judge", task_type="lean_judgment", task_data=payload)
    runs = asyncio.run(collect_child_runs(
        SimpleNamespace(tasks_dir=tmp_path / "tasks"), [task], [spec], config))
    child = runs["judge"]
    assert not child.succeeded
    assert child.outcome.execution_status is TaskExecutionStatus.FAILED
    assert "provider said no" in child.error


def test_the_batch_counts_failed_and_paused_tasks_and_their_spend(tmp_path):
    import asyncio

    from ape.orchestration.orchestrator import TaskOrchestrator
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from types import SimpleNamespace

    config = ApeAgentConfig(runs_base_dir=tmp_path)
    orchestrator = TaskOrchestrator(config=config, orchestrator_id="o")
    for gi, status, has_result in (("f", TaskExecutionStatus.FAILED, False),
                                   ("p", TaskExecutionStatus.PAUSED, False),
                                   ("c", TaskExecutionStatus.COMPLETED, True)):
        path = orchestrator.tasks_dir / gi / "task_outcome.json"
        path.parent.mkdir(parents=True)
        path.write_text(TaskOutcome(task_id=gi, task_type="x", global_index=gi,
                                    execution_status=status, has_result=has_result,
                                    billed_cost=0.5, nominal_cost=1.0, tokens=100,
                                    ).model_dump_json())
    tasks = [SimpleNamespace(data=SimpleNamespace(global_index=gi)) for gi in "fpcm"]
    counts = asyncio.run(orchestrator._scheduled_outcomes(tasks))
    assert (counts["failed_tasks"], counts["paused_tasks"],
            counts["tasks_without_outcome"]) == (1, 1, 1)
    assert counts["outcome_usage"].self_billed == pytest.approx(1.5)
    assert counts["outcome_usage"].self_tokens == 300


def test_an_attempt_that_raises_keeps_its_error_and_says_its_usage_is_unknown(
        monkeypatch, tmp_path):
    """The worker wrote the traceback, then overwrote it with None two steps later, and booked
    the attempt at $0 whatever it had spent. Driven through the real `execute_sample`, with only
    the scaffold call replaced by one that raises."""

    import asyncio
    import json

    from ape.orchestration.models import Sample as SampleModel

    worker = _worker(tmp_path)

    async def raising(**_kwargs):
        raise RuntimeError("provider went away mid-conversation")

    monkeypatch.setattr(worker, "_execute_with_early_stop_monitoring", raising)
    job = {"task_global_index": "gi", "task_type": "lean_judgment", "sample_index": 0,
           "early_stop_mode": "disabled",
           "task_data": {"task_type": "lean_judgment", "task_id": "t", "global_index": "gi"}}
    asyncio.run(worker.execute_sample(job))

    sample = SampleModel.model_validate(json.loads(
        (tmp_path / "tasks" / "gi" / "samples" / "0" / "sample.json").read_text()))
    attempt = sample.attempts[-1]
    assert attempt.status is ExecutionStatus.FAILED_ERROR
    assert "provider went away mid-conversation" in attempt.error_message
    assert attempt.usage_known is False
    outcome = TaskOutcome.model_validate(json.loads(
        (tmp_path / "tasks" / "gi" / "task_outcome.json").read_text()))
    assert outcome.usage_known is False
    assert "provider went away" in outcome.samples[0].attempts[0].error
