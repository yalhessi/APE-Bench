"""One way to run nested work, for every task family.

`TaskOrchestrator(` was constructed directly in four files with three conventions.
`judgment/task.py` and `reviewed_proof_engineering/review_gate.py` shared one -- a flat
`subtasks/` directory, both bubbling `nested_token_usage`. `review/delegation.py` invented a
third: its own outcome reader, its own status vocabulary, its own cost aggregation, and it did
*not* bubble usage. The accounting failures that voided two September runs were what that
divergence cost -- paused work booked at $0.00, tier totals stamped onto every child, a run
scored as complete over coverage it did not have.

This module is the shared implementation. A parent describes its children as
`TaskExecutionSpec`s and gets a `ChildRun` back per spec; directory layout, isolation, per-task
limits, bounded concurrency, the execution index and usage aggregation live here once.

**Isolation is a property of path derivation, and it stays that way.** Each child runs under
`<parent attempt>/subtasks/<group>/<orchestrator id>/`, and within that the orchestrator's own
`tasks/<index>/samples/<n>/attempts/<id>_<timestamp>` gives every attempt its own directory --
which is what makes `_ensure_patched_target_workspace` safe to run concurrently, since it
unlinks and rebuilds the workspace it is handed.

**Nested execution never spawns processes.** The parent is already inside a worker, so
`num_processes` defaults to 0 and concurrency is bounded async. Nothing bounded it before: four
leads, four arms each, three tiers gathered concurrently was up to 48 simultaneous Lean
compiles from one process.

**Children are read back from what was scheduled, never from what was aggregated.** A task with
a resumable sample writes `task_outcome.json` and returns before aggregation, so it is absent
from `results.task_results`. Both readers this module replaces iterated that list, and so could
not see a paused child at all -- the one row a budget ledger most needs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .models import ChildRun, TaskExecutionSpec, TaskExecutionStatus, TaskOutcome

#: How many children may run at once inside one parent. Deliberately small: each carries its
#: own multi-gigabyte Lean workspace overlay, and the failure mode of getting this wrong is
#: memory pressure on a shared machine rather than a clean error.
DEFAULT_NESTED_CONCURRENCY = 4


def nested_config(attempt_path, config, *, group: str,
                  concurrency: Optional[int] = None, **overrides):
    """A scaffold config for one group of children.

    Sets one thing and leaves the rest to the caller:

    * `runs_base_dir` under the parent's attempt. This is the genuine invariant -- it is what
      keeps every child's workspace its own, and `_ensure_patched_target_workspace` unlinks and
      rebuilds whatever path it is handed, so two children sharing one would race.
    * `num_processes = 0` **by default**, because a parent that is itself inside a worker
      cannot safely spawn a process pool. It is a default rather than a rule: `judgment` and
      `review_gate` pass their own through, and forcing them to 0 would be a silent concurrency
      change dressed up as sharing a directory convention.

    Everything else -- the model, the sample count, the turn limit, early-stop behaviour --
    belongs to the caller. `judgment` deliberately runs a *different* model at
    `sample_count=num_judges` for its majority vote, so a primitive that forced the parent's
    config on its children could not serve it, and a primitive only one family can use is not a
    primitive.

    Takes the attempt path and a config rather than a parent task, because the two callers that
    are not `BaseTask` subclasses -- `judgment` and `review_gate` -- have a path and a config
    they built themselves and no task object to offer.
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


def _top_level_config(config, *, concurrency: Optional[int] = None, **overrides):
    """The same overrides without nesting, for a caller that has no parent attempt.

    `judgment` and `review_gate` both branch on whether they were given one: a review gate
    invoked outside a task attempt has nowhere to nest, and putting its children in the default
    runs root is the behaviour it has always had.
    """

    config = config.model_copy(deep=True)
    if concurrency is not None:
        config.execution.max_concurrency = max(1, int(concurrency))
    for key, value in overrides.items():
        setattr(config.execution, key, value)
    return config


async def run_subtasks(
    specs: Sequence[TaskExecutionSpec],
    *,
    attempt_path,
    config,
    group: str,
    logger=None,
    concurrency: Optional[int] = None,
    execution_overrides: Optional[Dict[str, Any]] = None,
    orchestrator_id: Optional[str] = None,
    index_path: Optional[Any] = None,
    parent_id: Optional[str] = None,
) -> Tuple[Dict[str, ChildRun], Any]:
    """Run one group of children and return `({spec_id: ChildRun}, results)`.

    `results` is the raw `OrchestratorResults`, because a caller that wants the orchestrator's
    own aggregate -- `total_token_usage`, which `judgment` and `review_gate` bubble as
    `nested_token_usage` -- needs it, and this must not become a second projection of the same
    thing.

    `attempt_path=None` means the children are not nested under an attempt: the config is used
    as given, including its `num_processes`. That is the branch `judgment` and `review_gate`
    already had for a call outside a task attempt.

    `orchestrator_id` names the child batch's directory and is passed to the constructor, which
    is the only place it takes effect. It used to be *assigned* after construction, so the
    directory kept the default timestamped name and a resumed parent could not find the
    children it had already paid for.

    `concurrency=None` leaves `max_concurrency` alone. A caller that has set it deliberately --
    `judgment` runs its judges at its own -- must not have it overwritten by a default.
    """

    from ape.tasks.base import create_task_from_data

    from .orchestrator import TaskOrchestrator

    if not specs:
        return {}, None

    overrides = dict(execution_overrides or {})
    if attempt_path is None:
        config = _top_level_config(config, concurrency=concurrency, **overrides)
    else:
        config = nested_config(attempt_path, config, group=group,
                               concurrency=concurrency, **overrides)

    tasks, spec_by_task_id, spec_by_index = [], {}, {}
    for spec in specs:
        payload = spec.with_limits()
        # The same overrides the worker applies when it rebuilds the task on the far side
        # (`scaffolds/runner.py::main_from_params`). Passing them here keeps the parent-side
        # object and the worker-side one the same task.
        task = create_task_from_data(
            payload, config, task_config_overrides=getattr(config, "task_config_overrides", None))
        index = task.data.global_index
        if index in spec_by_index:
            # Identical payloads are one task to the orchestrator, and its resume skips a task
            # whose result exists -- so the second spec would be handed the first's result and
            # nothing would say so. This is the failure the whole contract exists to refuse.
            raise ValueError(
                f"specs {spec_by_index[index]!r} and {spec.spec_id!r} have identical task data, "
                f"so they are one task ({index[:12]}) to the orchestrator and only one would "
                f"run. Give them something that differs, or dispatch one of them."
            )
        spec_by_index[index] = spec.spec_id
        spec_by_task_id[payload.get("task_id")] = spec.spec_id
        tasks.append(task)

    orchestrator = TaskOrchestrator(config=config, orchestrator_id=orchestrator_id, logger=logger)
    results = await orchestrator.run(tasks)

    # Semantic id -> physical path, recorded where the paths are made. Optional because most
    # families do not read their own runs back; the ones that do stop parsing directory names.
    from . import execution_index

    await execution_index.record(
        index_path, orchestrator, results, semantic_ids=spec_by_task_id, group=group,
        parent=parent_id,
        # What was scheduled, not what came back: a paused child is absent from the results and
        # would otherwise have no row, which is how a replay lost two whole sessions.
        tasks=tasks,
    )

    runs = await collect_child_runs(orchestrator, tasks, specs, config, logger=logger)
    for spec_id, child in sorted(runs.items()):
        if child.spec.required and not child.succeeded:
            (logger.warning if logger else print)(
                "required child %s did not produce a result (%s): it is a coverage gap, not a "
                "silence", spec_id, child.outcome.reason or child.outcome.execution_status.value)
    return runs, results


async def collect_child_runs(
    orchestrator, tasks: Sequence[Any], specs: Sequence[TaskExecutionSpec], config, logger=None,
) -> Dict[str, ChildRun]:
    """One `ChildRun` per spec, from what the orchestrator persisted.

    Iterates the tasks that were SCHEDULED, not the results that came back. A child that failed
    or paused has no result to read, and those are exactly the rows an honest ledger needs --
    the orchestrator aggregates only finished tasks, so reading `results.task_results` drops a
    paused child entirely.

    Reading a child must never be able to fail the wave that already paid for it: a child whose
    records cannot be read is reported as failed with the reason, and the rest are returned.
    """

    from .persistence import TaskStorage

    runs: Dict[str, ChildRun] = {}
    for spec, task in zip(specs, tasks):
        index = task.data.global_index
        task_dir = orchestrator.tasks_dir / str(index)
        try:
            storage = TaskStorage(task_dir, str(index))
            samples = await storage.load_all_samples(task.task_type)
            raw_result = await storage.load_task_result()
            has_result = bool(raw_result and raw_result.get("success"))
            result = None
            if has_result:
                try:
                    result = task.task_result_class.model_validate(raw_result)
                except Exception:  # noqa: BLE001 - a result that no longer validates is still
                    # evidence that something came back; the caller sees `succeeded` False and
                    # a reason rather than a crash.
                    has_result = False
                    if logger is not None:
                        logger.warning("child %s: task_result.json does not validate as %s",
                                       spec.spec_id, task.task_result_class.__name__)
            outcome = TaskOutcome.from_samples(
                task_id=task.data.task_id, task_type=task.task_type, global_index=index,
                samples=samples,
                max_retries=config.execution.task_max_retries,
                max_turns=config.execution.max_turns,
                sample_max_cost=config.execution.sample_max_cost,
                has_result=has_result,
            )
        except Exception as error:  # noqa: BLE001 - see the docstring
            if logger is not None:
                logger.warning("child %s: could not read its records (%s)", spec.spec_id, error,
                               exc_info=True)
            outcome = TaskOutcome(
                task_id=task.data.task_id, task_type=task.task_type, global_index=index,
                execution_status=TaskExecutionStatus.FAILED, has_result=False,
                reason=f"records unreadable: {error}")
            result = None
        runs[spec.spec_id] = ChildRun(
            spec=spec, global_index=index, task_dir=str(task_dir), outcome=outcome, result=result)
    return runs


def nested_usage(runs: Dict[str, ChildRun]):
    """What the children cost, in the shape `BaseTaskResult.nested_token_usage` expects.

    Costs only. Per-child token counts were the enclosing tier's totals stamped on every row,
    so summing them was meaningless; cost is per child and reconciles against the ledger.
    """

    from ape.llm_clients.models import TokenUsage

    return TokenUsage(
        total_cost=round(sum(item.outcome.nominal_cost for item in runs.values()), 6),
        cached_total_cost=round(sum(item.outcome.billed_cost for item in runs.values()), 6),
    )
