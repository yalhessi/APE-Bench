"""Requeueing the samples a partial run lost to its environment, and nothing else.

H-claude rep 2 (2026-10-01) closed `partial`: 13 of 15 sessions succeeded, and two failed when
the subscription's usage limit was spent mid-session, then spent their three retries on the
same error in under a minute. The orchestrator called them Failed, and the only way back was
`--redo`, re-running the 13 good sessions too. A requeue puts back exactly the failed-on-errors
samples, keeps everything they spent, and leaves successes and model failures where they are.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime

from ape.orchestration.models import Attempt, ExecutionStatus, Sample
from ape.orchestration.persistence import TaskStorage, requeue_failed_samples

MAX_RETRIES = 3


def _sample(task_dir, statuses, tokens=1000):
    now = datetime.now()
    sample = Sample(
        sample_id=f"{task_dir.name}_0", sample_index=0, task_global_index=task_dir.name,
        attempts=[Attempt(attempt_id=i + 1, path=task_dir / "samples/0/attempts" / f"a{i + 1}",
                          status=status, created_at=now, max_turns=160, cost_limit=None,
                          tokens=tokens if i == 0 else 0)
                  for i, status in enumerate(statuses)],
        created_at=now, updated_at=now)
    asyncio.run(TaskStorage(task_dir, task_dir.name).save_sample(sample))
    return sample


def _aggregate(task_dir, success):
    (task_dir / "task_result.json").write_text(json.dumps({"success": success}))
    (task_dir / "task_outcome.json").write_text(json.dumps({"has_result": True}))


def _layout(tmp_path):
    tasks = tmp_path / "tasks"
    spent = tasks / "spent"         # the limit: one long attempt, then three instant failures
    _sample(spent, [ExecutionStatus.FAILED_ERROR] * 4, tokens=2_489_144)
    _aggregate(spent, success=False)
    done = tasks / "done"
    _sample(done, [ExecutionStatus.SUCCESS])
    _aggregate(done, success=True)
    model = tasks / "model"         # the model's own failure is a result, not an outage
    _sample(model, [ExecutionStatus.FAILED_MODEL])
    _aggregate(model, success=False)
    retrying = tasks / "retrying"   # retries left: an ordinary resume already runs it
    _sample(retrying, [ExecutionStatus.FAILED_ERROR])
    return tasks


def _load(task_dir):
    return asyncio.run(TaskStorage(task_dir, task_dir.name).load_sample(0))


def test_only_the_samples_failed_on_errors_are_requeued(tmp_path):
    tasks = _layout(tmp_path)
    rows = asyncio.run(requeue_failed_samples(tasks, MAX_RETRIES, "five_hour limit spent"))
    assert [(row["task"], row["attempts"], row["errors"]) for row in rows] == [("spent", 4, 4)]

    spent = _load(tasks / "spent")
    assert [r.after_attempt for r in spent.requeues] == [4]
    assert spent.requeues[0].reason == "five_hour limit spent"
    assert spent.can_execute(MAX_RETRIES, 160, None, None)
    assert spent.get_error_count() == 0
    # Kept, with what they spent: the record is not rewritten to look like a first attempt.
    assert len(spent.attempts) == 4 and spent.get_accumulated_tokens() == 2_489_144
    # Its aggregate is gone, so the orchestrator schedules it again.
    assert not (tasks / "spent" / "task_result.json").exists()
    assert not (tasks / "spent" / "task_outcome.json").exists()

    for name in ("done", "model"):
        assert (tasks / name / "task_result.json").exists(), name
        assert not _load(tasks / name).requeues, name
    assert not _load(tasks / "retrying").requeues


def test_a_requeued_sample_gets_its_full_retry_budget_and_no_more(tmp_path):
    tasks = _layout(tmp_path)
    asyncio.run(requeue_failed_samples(tasks, MAX_RETRIES, "limit"))
    spent = _load(tasks / "spent")
    now = datetime.now()
    for i in range(MAX_RETRIES + 1):
        assert spent.can_execute(MAX_RETRIES, 160, None, None)
        spent.attempts.append(Attempt(attempt_id=5 + i, path=tmp_path / f"r{i}",
                                      status=ExecutionStatus.FAILED_ERROR, created_at=now,
                                      max_turns=160, cost_limit=None))
    assert not spent.can_execute(MAX_RETRIES, 160, None, None)
    assert spent.is_failed_on_errors(MAX_RETRIES)


def test_a_dry_run_changes_nothing(tmp_path):
    tasks = _layout(tmp_path)
    rows = asyncio.run(requeue_failed_samples(tasks, MAX_RETRIES, "limit", dry_run=True))
    assert [row["task"] for row in rows] == ["spent"]
    assert not _load(tasks / "spent").requeues
    assert (tasks / "spent" / "task_result.json").exists()


def test_a_sample_record_from_before_requeues_still_loads(tmp_path):
    task = tmp_path / "tasks" / "old"
    sample = _sample(task, [ExecutionStatus.SUCCESS])
    data = json.loads((task / "samples/0/sample.json").read_text())
    data.pop("requeues")
    (task / "samples/0/sample.json").write_text(json.dumps(data))
    assert _load(task).requeues == [] and _load(task).attempts[0].status == sample.status
