"""Slice C of the task/data refactor: failures, resumes, repetitions, interrupted output, fallbacks
and continuation stay identifiable, and an unsupported continuation fails explicitly.

The interruption cases were measured before they were fixed (2026-10-22): a task whose sample
succeeded but whose process died before aggregation, and a task whose result was written but whose
log row was not, both reached `OrchestratorResults.task_results` as nothing on resume -- so a resumed
review lost that PR's findings without a word. Every test here runs the real orchestrator over real
tasks; only the model is absent.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime

import pytest

from ape.orchestration.models import Attempt, ExecutionStatus, Sample
from ape.orchestration.orchestrator import TaskOrchestrator
from ape.orchestration.persistence import TaskStorage
from ape.orchestration.products import sample_products
from ape.orchestration.worker import AGGREGATION_CLAIM
from ape.scaffolds.ape_agent.config import ApeAgentConfig
from ape.tasks.base import create_task_from_data

PAYLOAD = {"task_type": "lean_judgment", "task_id": "j", "target_code": "a", "original_code": "b",
           "task_description": "d", "reference_implementation": "r", "gold_diff": "g",
           "filename": "f.lean", "target_workspace": {"name": "ws"}}


def _setup(tmp_path, task_id="j"):
    config = ApeAgentConfig(runs_base_dir=tmp_path)
    config.execution.task_max_retries = 0
    task = create_task_from_data({**PAYLOAD, "task_id": task_id}, config)
    orchestrator = TaskOrchestrator(config=config, orchestrator_id="o")
    gi = task.data.global_index
    return config, task, orchestrator, TaskStorage(orchestrator.tasks_dir / gi, gi)


def _result(task, **extra):
    return task.task_result_class(task_id=task.data.task_id, task_type=task.task_type,
                                  global_index=task.data.global_index, success=True, score=1.0,
                                  judgment_conclusion="positive", judgment_data={}, **extra)


def _attempt(storage, n, status, result=None):
    now = datetime.now()
    return Attempt(attempt_id=n, path=storage.task_dir / f"a{n}", status=status, created_at=now,
                   max_turns=5, cost_limit=None,
                   result=result.model_dump(mode="json") if result is not None else None)


def _save(storage, index, attempts, status):
    now = datetime.now()
    asyncio.run(storage.save_sample(Sample(
        sample_id=f"s{index}", task_global_index=storage.task_dir.name, sample_index=index,
        status=status, created_at=now, updated_at=now, attempts=attempts)))


# --- interrupted output ------------------------------------------------------------------------


def test_samples_that_ended_unaggregated_are_published_on_resume(tmp_path):
    _config, task, orchestrator, storage = _setup(tmp_path)
    _save(storage, 0, [_attempt(storage, 1, ExecutionStatus.SUCCESS, _result(task))],
          ExecutionStatus.SUCCESS)
    results = asyncio.run(orchestrator.run([task]))
    assert len(results.task_results) == 1
    assert (storage.task_dir / "task_result.json").is_file()
    assert (storage.task_dir / "task_outcome.json").is_file()
    assert results.recovered_results == [task.data.global_index]


def test_a_result_the_log_lost_is_read_from_its_file_and_the_log_healed(tmp_path):
    _config, task, orchestrator, storage = _setup(tmp_path)
    _save(storage, 0, [_attempt(storage, 1, ExecutionStatus.SUCCESS, _result(task))],
          ExecutionStatus.SUCCESS)
    asyncio.run(storage.save_task_result(_result(task)))
    results = asyncio.run(orchestrator.run([task]))
    assert len(results.task_results) == 1 and results.completed_tasks == 1
    assert task.data.global_index in results.recovered_results
    rows = [json.loads(l) for l in orchestrator.aggregated_results_file.read_text().splitlines()
            if l.strip()]
    assert [r["global_index"] for r in rows] == [task.data.global_index]


def test_a_stale_claim_from_a_killed_publisher_is_finished(tmp_path):
    _config, task, orchestrator, storage = _setup(tmp_path)
    _save(storage, 0, [_attempt(storage, 1, ExecutionStatus.SUCCESS, _result(task))],
          ExecutionStatus.SUCCESS)
    (storage.task_dir / AGGREGATION_CLAIM).write_text("")
    results = asyncio.run(orchestrator.run([task]))
    assert len(results.task_results) == 1
    assert not (storage.task_dir / AGGREGATION_CLAIM).exists()


def test_a_live_claim_stops_a_second_publisher(tmp_path):
    """Two workers finishing a task's samples together: only the claimant publishes."""
    import threading

    from ape.orchestration.worker import SampleWorker

    config, task, orchestrator, storage = _setup(tmp_path)
    _save(storage, 0, [_attempt(storage, 1, ExecutionStatus.SUCCESS, _result(task))],
          ExecutionStatus.SUCCESS)
    (storage.task_dir / AGGREGATION_CLAIM).write_text("")        # another worker holds it
    worker = SampleWorker(config=config, scaffold_type="ape_agent",
                          orchestrator_dir=orchestrator.workspace_path, worker_id=1,
                          early_stop_events={}, aggregation_lock=threading.Lock(),
                          execution_mode_name="t", orchestrator_start_time=datetime.now())
    job = {"task_global_index": task.data.global_index, "task_type": task.task_type}
    asyncio.run(worker._try_aggregate(job, storage, task.job_data(), task.task_type))
    assert not (storage.task_dir / "task_result.json").exists()


def test_two_different_results_for_one_task_are_named_not_silently_chosen(tmp_path):
    _config, task, orchestrator, storage = _setup(tmp_path)
    _save(storage, 0, [_attempt(storage, 1, ExecutionStatus.SUCCESS, _result(task))],
          ExecutionStatus.SUCCESS)
    on_file = _result(task, error=None)
    asyncio.run(storage.save_task_result(on_file))
    (storage.task_dir / "task_outcome.json").write_text("{}")
    first = _result(task).model_dump(mode="json")
    other = {**first, "judgment_conclusion": "negative"}
    orchestrator.aggregated_results_file.parent.mkdir(parents=True, exist_ok=True)
    orchestrator.aggregated_results_file.write_text(json.dumps(other) + "\n" + json.dumps(first) + "\n")
    results = asyncio.run(orchestrator.run([task]))
    assert results.conflicting_results == [task.data.global_index]
    assert results.task_results[0].judgment_conclusion == on_file.judgment_conclusion


@pytest.mark.parametrize("stale_claim", [False, True])
def test_a_previous_outcome_does_not_block_a_resumed_samples_publication(tmp_path, stale_claim):
    """Implementation review 2026-10-22, finding 4. A sample paused at a five-turn ceiling was
    reconciled into an outcome (failed, nothing resumable) and no result. The ceiling was raised,
    a resumed worker succeeded and was killed after saving its sample. The old outcome must not
    stand in for the present."""

    config, task, orchestrator, storage = _setup(tmp_path)
    config.execution.max_turns = 5
    paused = _attempt(storage, 1, ExecutionStatus.PAUSED_MAX_TURNS)
    paused.turns = 5
    _save(storage, 0, [paused], ExecutionStatus.PAUSED_MAX_TURNS)
    first = asyncio.run(orchestrator.run([task]))
    assert first.task_results == [] and (storage.task_dir / "task_outcome.json").is_file()
    assert not (storage.task_dir / "task_result.json").exists()

    config.execution.max_turns = 10
    _save(storage, 0, [paused, _attempt(storage, 2, ExecutionStatus.SUCCESS, _result(task))],
          ExecutionStatus.SUCCESS)
    if stale_claim:
        (storage.task_dir / AGGREGATION_CLAIM).write_text("")
    resumed = TaskOrchestrator(config=config, orchestrator_id="o")
    results = asyncio.run(resumed.run([task]))
    assert len(results.task_results) == 1 and results.completed_tasks == 1
    assert results.failed_tasks == 0 and results.recovered_results == [task.data.global_index]
    outcome = json.loads((storage.task_dir / "task_outcome.json").read_text())
    assert outcome["has_result"] is True and outcome["execution_status"] == "completed"
    assert not (storage.task_dir / AGGREGATION_CLAIM).exists()


def test_a_result_beside_an_older_outcome_refreshes_the_outcome(tmp_path):
    _config, task, orchestrator, storage = _setup(tmp_path)
    _save(storage, 0, [_attempt(storage, 1, ExecutionStatus.SUCCESS, _result(task))],
          ExecutionStatus.SUCCESS)
    asyncio.run(storage.save_task_result(_result(task)))
    (storage.task_dir / "task_outcome.json").write_text(json.dumps(
        {"task_id": "j", "task_type": task.task_type, "global_index": task.data.global_index,
         "execution_status": "paused", "has_result": False}))
    results = asyncio.run(orchestrator.run([task]))
    outcome = json.loads((storage.task_dir / "task_outcome.json").read_text())
    assert outcome["has_result"] is True and outcome["execution_status"] == "completed"
    assert task.data.global_index in results.recovered_results


# --- resume, repetition, failure -----------------------------------------------------------------


def test_a_resumed_sample_is_one_observation_with_two_attempts(tmp_path):
    _config, task, _orchestrator, storage = _setup(tmp_path)
    _save(storage, 0, [_attempt(storage, 1, ExecutionStatus.PAUSED_TOKEN_LIMIT),
                       _attempt(storage, 2, ExecutionStatus.SUCCESS, _result(task))],
          ExecutionStatus.SUCCESS)
    rows = asyncio.run(sample_products(storage.task_dir.parent, [task], 1))
    assert [(r.sample_index, r.attempts, r.product is not None) for r in rows] == [(0, 2, True)]


def test_identical_independent_samples_stay_two_observations(tmp_path):
    _config, task, _orchestrator, storage = _setup(tmp_path)
    for index in (0, 1):
        _save(storage, index, [_attempt(storage, 1, ExecutionStatus.SUCCESS, _result(task))],
              ExecutionStatus.SUCCESS)
    rows = asyncio.run(sample_products(storage.task_dir.parent, [task], 2))
    assert [r.sample_index for r in rows if r.product is not None] == [0, 1]
    assert rows[0].product.model_dump() == rows[1].product.model_dump()


def test_a_failed_sample_is_a_failure_not_an_empty_product(tmp_path):
    _config, task, _orchestrator, storage = _setup(tmp_path)
    _save(storage, 0, [_attempt(storage, 1, ExecutionStatus.FAILED_MODEL)],
          ExecutionStatus.FAILED_MODEL)
    (row,) = asyncio.run(sample_products(storage.task_dir.parent, [task], 1))
    assert row.product is None and row.status == "failed_model"


# --- explicit fallback, waiting, continuation ----------------------------------------------------


def test_a_reviewer_whose_context_lacks_its_pr_refuses_rather_than_reviewing_without_it(tmp_path):
    """An acquisition that produced nothing for a PR leaves that PR out of the context file; the
    reviewer must not quietly review it unassisted (design §8: a fallback is explicit)."""
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig, solo_context_block

    context = tmp_path / "context.jsonl"
    context.write_text(json.dumps({"pr_number": 1, "sections": [{"title": "t", "text": "x"}]}) + "\n")
    with pytest.raises(KeyError, match="holds no row for PR 2"):
        solo_context_block(SoloReviewConfig(context_file=context), 2)


def test_a_matching_with_no_verdicts_yet_is_waiting_not_scored(tmp_path):
    from src.mathlib_review.analysis import matching as MA
    from tests.mathlib_review.test_matching import _v2_plan

    _v2_plan(tmp_path)
    with pytest.raises(ValueError, match="no verdicts yet"):
        MA.report_matching(tmp_path / "m", write=False)


def test_a_run_name_continues_its_own_plan_and_refuses_another(tmp_path):
    from src.mathlib_review.analysis.matching import bind_run_to_plan

    bind_run_to_plan(tmp_path, "r", "matching", "p1", "a" * 64)
    bind_run_to_plan(tmp_path, "r", "matching", "p1", "a" * 64)          # a resume
    with pytest.raises(ValueError, match="new run name"):
        bind_run_to_plan(tmp_path, "r", "matching", "p2", "b" * 64)
