"""Every sample's product, read one way: the legal submission a task's own class validates, or why not.

Readers of finished work kept re-deriving this, each a little differently: the matcher's verdicts, a
lead's children, the probe readers. And the persisted record allows two silent errors. A task whose
samples all failed used to carry a synthetic `task_result.json` (no longer written, but on disk in
old runs), and `TaskStorage` validates an attempt's result as the task's own class and falls back to
a bare `BaseTaskResult` when that fails -- so "a file is there", "the task completed" and "a legal
submission came back" were easy to conflate, and a default or empty product could stand in for a
failure.

`sample_products` returns one row per sample slot of every scheduled task. A row's `product` is set
only when the sample's successful attempt holds a result of the task's own `task_result_class` and
the class's `product_of` projects it; otherwise the row says what happened instead (`status`,
`error`). An empty product is a product; a missing one is never empty.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Sequence

from pydantic import BaseModel, ConfigDict

from .models import ExecutionStatus


class SampleProduct(BaseModel):
    """One sample slot of one scheduled task, and the product its successful attempt submitted."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_global_index: str
    task_id: str
    task_type: str
    sample_index: int
    status: str
    attempts: int
    attempt_path: Optional[str] = None
    #: The validated projection of a legal submission (`BaseTask.product_of`), or None.
    product: Optional[Any] = None
    #: Why there is no product, when there is none.
    error: Optional[str] = None
    #: False when an attempt's usage never came back (`Attempt.usage_known`).
    usage_known: bool = True


async def sample_products(tasks_dir: Path, tasks: Sequence[Any],
                          sample_count: Optional[int] = None) -> List[SampleProduct]:
    """One row per sample slot of each scheduled task, read through `TaskStorage`.

    `sample_count` names the slots that were requested; a slot with no record is reported as
    `unscheduled` rather than left out, so "never ran" stays distinguishable from "ran and failed".
    """

    from .persistence import TaskStorage

    rows: List[SampleProduct] = []
    for task in tasks:
        index = task.data.global_index
        storage = TaskStorage(Path(tasks_dir) / index, index)
        samples = await storage.load_all_samples(task.task_type)
        slots = sorted(set(samples) | set(range(sample_count or 0)))
        for slot in slots:
            sample = samples.get(slot)
            if sample is None:
                rows.append(SampleProduct(task_global_index=index, task_id=task.data.task_id,
                                          task_type=task.task_type, sample_index=slot,
                                          status="unscheduled", attempts=0,
                                          error="no record of this sample"))
                continue
            attempt = sample.successful_attempt
            product, error = None, None
            if attempt is None:
                error = f"no successful attempt ({sample.status.value})"
            elif not isinstance(attempt.result, task.task_result_class):
                error = (f"the successful attempt's result is not a legal "
                         f"{task.task_result_class.__name__}")
            else:
                product = type(task).product_of(attempt.result)
                if product is None:
                    error = "the result is not a product (product_of returned None)"
            rows.append(SampleProduct(
                task_global_index=index, task_id=task.data.task_id, task_type=task.task_type,
                sample_index=slot, status=sample.status.value, attempts=len(sample.attempts),
                attempt_path=str(attempt.path) if attempt else None, product=product,
                error=error, usage_known=all(getattr(a, "usage_known", True)
                                             for a in sample.attempts)))
    return rows


def succeeded(rows: Sequence[SampleProduct]) -> List[SampleProduct]:
    return [row for row in rows if row.product is not None]


__all__ = ["SampleProduct", "sample_products", "succeeded", "ExecutionStatus"]
