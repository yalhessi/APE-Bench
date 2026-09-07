"""One way to run nested work, for every task family.

`TaskOrchestrator(` is constructed directly in four files. `judgment/task.py` and
`reviewed_proof_engineering/review_gate.py` share one convention -- a flat `subtasks/`
directory, and both bubble `nested_token_usage`. `pr_review_v5/delegation.py` invented a third:
`subtasks/wave<N>/<tier>/`, its own outcome type, its own cost aggregation, and it did *not*
bubble usage. The accounting failures that voided two September runs were what that divergence
cost -- paused work booked at $0.00, tier totals stamped onto every child, a run scored as
complete over coverage it did not have.

This module is the shared implementation. A parent describes its children as
`TaskExecutionSpec`s and gets `TaskOutcome`s back; directory layout, isolation, per-task
limits, bounded concurrency and usage aggregation live here once.

**Isolation is a property of path derivation, and it stays that way.** Each child runs under
`<parent attempt>/subtasks/<group>/`, and within that the orchestrator's own
`tasks/<index>/samples/<n>/attempts/<id>_<timestamp>` gives every attempt its own directory --
which is what makes `_ensure_patched_target_workspace` safe to run concurrently, since it
unlinks and rebuilds the workspace it is handed.

**Nested execution never spawns processes.** The parent is already inside a worker, so
`num_processes` is 0 and concurrency is bounded async. Nothing bounded it before: four leads,
four arms each, three tiers gathered concurrently was up to 48 simultaneous Lean compiles from
one process.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .config import EarlyStopMode
from .models import TaskExecutionSpec, TaskOutcome

#: How many children may run at once inside one parent. Deliberately small: each carries its
#: own multi-gigabyte Lean workspace overlay, and the failure mode of getting this wrong is
#: memory pressure on a shared machine rather than a clean error.
DEFAULT_NESTED_CONCURRENCY = 4


def nested_config(attempt_path, config, *, group: str,
                  concurrency: Optional[int] = None, **overrides):
    """A scaffold config for one group of children.

    Sets two things and leaves everything else to the caller:

    * `runs_base_dir` under the parent's attempt. This is the one genuine invariant -- it is
      what keeps every child's workspace its own, and `_ensure_patched_target_workspace`
      unlinks and rebuilds whatever path it is handed, so two children sharing one would race.
    * `num_processes = 0` **by default**, because a parent that is itself inside a worker
      cannot safely spawn a process pool. It is a default rather than a rule: `judgment` and
      `review_gate` set their own and pass it through, and forcing them to 0 would be a silent
      concurrency change dressed up as sharing a directory convention.

    Everything else -- the model, the sample count, the turn limit, early-stop behaviour --
    belongs to the caller. `judgment` deliberately runs a *different* model at
    `sample_count=num_judges` for its majority vote, so a primitive that forced the parent's
    config on its children could not serve it, and a primitive only one family can use is not
    a primitive.

    Takes the attempt path and a config rather than a parent task, because the two callers
    that are not `BaseTask` subclasses -- `judgment` and `review_gate` -- have a path and a
    config they built themselves and no task object to offer.
    """

    config = config.model_copy(deep=True)
    config.execution.num_processes = 0
    if concurrency is not None:
        config.execution.max_concurrency = max(1, int(concurrency))
    for key, value in overrides.items():
        setattr(config.execution, key, value)

    subtasks = Path(attempt_path) / "subtasks" / group
    subtasks.mkdir(parents=True, exist_ok=True)
    config.runs_base_dir = subtasks
    return config


async def run_subtasks(
    parent_task,
    specs: Sequence[TaskExecutionSpec],
    *,
    group: str,
    logger=None,
    base=None,
    concurrency: int = DEFAULT_NESTED_CONCURRENCY,
    execution_overrides: Optional[Dict[str, Any]] = None,
    index_path: Optional[Any] = None,
):
    """Run one group of children and return `(outcomes_by_spec_id, results)`.

    `results` is the raw `OrchestratorResults`, because a caller that wants the children's
    returned payloads needs them and this must not become a second projection of the same
    thing.
    """

    from ape.tasks.base import create_task_from_data

    from .orchestrator import TaskOrchestrator

    if not specs:
        return {}, None

    config = nested_config(
        parent_task.attempt_path, base if base is not None else parent_task.config,
        group=group, concurrency=concurrency, **(execution_overrides or {}))
    tasks, spec_by_task_id = [], {}
    for spec in specs:
        payload = spec.with_limits()
        tasks.append(create_task_from_data(payload, config))
        spec_by_task_id[payload.get("task_id")] = spec.spec_id

    orchestrator = TaskOrchestrator(config=config, logger=logger)
    orchestrator.orchestrator_id = group
    results = await orchestrator.run(tasks)

    # Semantic id -> physical path, recorded where the paths are made. Optional because most
    # families do not read their own runs back; the ones that do stop parsing directory names.
    from . import execution_index

    await execution_index.record(
        index_path or getattr(getattr(parent_task, "data", None), "execution_index_path", None),
        orchestrator, results, semantic_ids=spec_by_task_id, group=group,
        parent=getattr(getattr(parent_task, "data", None), "task_id", None),
    )

    outcomes = await collect_outcomes(orchestrator, results, spec_by_task_id, config)
    return outcomes, results


async def collect_outcomes(
    orchestrator, results, spec_by_task_id: Dict[str, str], config,
) -> Dict[str, TaskOutcome]:
    """One `TaskOutcome` per child, read from what the orchestrator persisted.

    Read from the persisted samples rather than the returned results: a child that failed or
    paused has no result to read, and those are exactly the rows an honest ledger needs. This
    is the same reasoning `_sample_facts` encodes, moved somewhere every task family gets it.
    """

    from .persistence import TaskStorage

    outcomes: Dict[str, TaskOutcome] = {}
    for result in getattr(results, "task_results", []) or []:
        raw = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
        global_index = raw.get("global_index")
        task_id = raw.get("task_id")
        spec_id = spec_by_task_id.get(task_id)
        if not (global_index and spec_id):
            continue
        task_dir = orchestrator.tasks_dir / str(global_index)
        storage = TaskStorage(task_dir, str(global_index))
        samples = await storage.load_all_samples()
        outcomes[spec_id] = TaskOutcome.from_samples(
            task_id=task_id, task_type=raw.get("task_type", ""), global_index=global_index,
            samples=samples,
            max_retries=config.execution.task_max_retries,
            max_turns=config.execution.max_turns,
            sample_max_cost=config.execution.sample_max_cost,
            has_result=bool(raw.get("success")),
        )
    return outcomes


def nested_usage(outcomes: Dict[str, TaskOutcome]):
    """What the children cost, in the shape `BaseTaskResult.nested_token_usage` expects.

    Costs only. Per-child token counts were the enclosing tier's totals stamped on every row,
    so summing them was meaningless; cost is per child and reconciles against the ledger.
    """

    from ape.llm_clients.models import TokenUsage

    return TokenUsage(
        total_cost=round(sum(item.nominal_cost for item in outcomes.values()), 6),
        cached_total_cost=round(sum(item.billed_cost for item in outcomes.values()), 6),
    )
