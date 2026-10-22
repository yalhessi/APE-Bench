"""`sample_products`: a legal product, or a row that says why not -- never a stand-in.

Design §5: execution status, a file on disk and a legal product are different facts. The persisted
record makes two of them easy to conflate: `TaskStorage` validates an attempt's result as the task's
own class and falls back to a bare `BaseTaskResult`, and old runs carry a synthetic failure result.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from ape.orchestration.models import Attempt, ExecutionStatus, Sample
from ape.orchestration.persistence import TaskStorage
from ape.orchestration.products import sample_products, succeeded
from ape.tasks.base import BaseTask, BaseTaskConfig, BaseTaskData, BaseTaskResult, register_task


class _Data(BaseTaskData):
    task_type: str = "products_probe"
    payload: str = ""


class _Result(BaseTaskResult):
    answer: str
    keep: bool = True


class _Config(BaseTaskConfig):
    pass


class _Task(BaseTask):
    task_type = "products_probe"
    data_class = _Data
    task_config_class = _Config
    task_result_class = _Result

    @classmethod
    def product_of(cls, result):
        return {"answer": result.answer} if result.success and result.keep else None


register_task("products_probe", _Task)


def _task(name):
    """A real task (`.claude/rules`: a hand-built stand-in cannot disagree with the class)."""
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.base import create_task_from_data

    return create_task_from_data({"task_type": "products_probe", "task_id": f"t_{name}",
                                  "payload": name}, ApeAgentConfig())


def _save(tmp_path, name, index, status, result):
    gi = _task(name).data.global_index
    if result is not None:
        result = {**result, "global_index": gi}
    now = datetime.now()
    asyncio.run(TaskStorage(tmp_path / gi, gi).save_sample(Sample(
        sample_id=f"{gi}_{index}", task_global_index=gi, sample_index=index, status=status,
        created_at=now, updated_at=now,
        attempts=[Attempt(attempt_id=1, path=tmp_path / gi / f"a{index}", status=status,
                          created_at=now, max_turns=5, cost_limit=None, result=result)])))


def _rows(tmp_path, tasks, n=None):
    return asyncio.run(sample_products(tmp_path, tasks, n))


def test_a_legal_submission_is_projected(tmp_path):
    _save(tmp_path, "g", 0, ExecutionStatus.SUCCESS,
          {"task_id": "t", "task_type": "products_probe", "global_index": "g", "success": True,
           "score": 1.0, "answer": "42"})
    (row,) = _rows(tmp_path, [_task("g")])
    assert row.product == {"answer": "42"} and row.error is None


def test_a_result_that_is_not_the_tasks_own_class_is_not_a_product(tmp_path):
    """Missing the required `answer`, it validates only as the bare fallback."""
    _save(tmp_path, "g", 0, ExecutionStatus.SUCCESS,
          {"task_id": "t", "task_type": "products_probe", "global_index": "g", "success": True,
           "score": 1.0})
    (row,) = _rows(tmp_path, [_task("g")])
    assert row.product is None and "not a legal _Result" in row.error


def test_a_failed_sample_and_a_declined_projection_have_no_product(tmp_path):
    _save(tmp_path, "f", 0, ExecutionStatus.FAILED_MODEL, None)
    _save(tmp_path, "d", 0, ExecutionStatus.SUCCESS,
          {"task_id": "t", "task_type": "products_probe", "global_index": "d", "success": True,
           "score": 1.0, "answer": "x", "keep": False})
    failed, declined = _rows(tmp_path, [_task("f"), _task("d")])
    assert failed.product is None and "no successful attempt" in failed.error
    assert declined.product is None and "product_of returned None" in declined.error
    assert succeeded([failed, declined]) == []


def test_a_requested_sample_that_never_ran_is_reported_not_omitted(tmp_path):
    _save(tmp_path, "g", 0, ExecutionStatus.SUCCESS,
          {"task_id": "t", "task_type": "products_probe", "global_index": "g", "success": True,
           "score": 1.0, "answer": "42"})
    rows = _rows(tmp_path, [_task("g")], n=2)
    assert [(r.sample_index, r.status) for r in rows] == [(0, "success"), (1, "unscheduled")]


def test_an_empty_product_is_a_product():
    assert _Task.product_of(_Result(task_id="t", task_type="products_probe", global_index="g",
                                    success=True, score=1.0, answer="")) == {"answer": ""}
