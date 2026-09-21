"""One way to run nested work, for every task family.

`TaskOrchestrator(` was constructed directly in four files with three conventions.
`judgment/task.py` and `review_gate.py` share one -- flat `subtasks/`, both bubbling
`nested_token_usage`. `pr_review_v5/delegation.py` invented a third and did not bubble usage,
and the accounting failures that voided two September runs were what that cost.

The primitive imposes only what nesting itself requires and leaves the rest to the caller.
That distinction is load-bearing: `judgment` deliberately runs a *different* model at
`sample_count=num_judges` for its majority vote, so a primitive that forced the parent's config
on its children could not serve it -- and a primitive only one family can use is not one.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ape.orchestration.config import EarlyStopMode
from ape.orchestration.models import (
    EXECUTION_LIMITS_KEY, TaskExecutionSpec, task_execution_limits,
)
from ape.orchestration.subtasks import DEFAULT_NESTED_CONCURRENCY, nested_config


def _config():
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    return ApeAgentConfig()


# --- per-task limits ---------------------------------------------------------------------


def test_a_task_may_carry_a_tighter_limit_than_its_orchestrator():
    """`Attempt.cost_limit` was always per-attempt and `runtime.run_task` always took
    `cost_limit` per call; both were simply filled from the orchestrator config. Reading an
    override off the task is what retired budget tiers."""

    execution = SimpleNamespace(max_turns=40, sample_max_cost=0.30)
    tighter = task_execution_limits(
        {EXECUTION_LIMITS_KEY: {"billed_cost_limit": 0.10, "max_turns": 5}}, execution)
    assert tighter.billed_cost_limit == 0.10
    assert tighter.max_turns == 5


def test_a_task_without_an_override_gets_the_orchestrator_value():
    execution = SimpleNamespace(max_turns=40, sample_max_cost=0.30)
    limits = task_execution_limits({}, execution)
    assert (limits.max_turns, limits.billed_cost_limit) == (40, 0.30)


@pytest.mark.parametrize("bad", [
    {EXECUTION_LIMITS_KEY: {"billed_cost_limit": "lots"}},
    {EXECUTION_LIMITS_KEY: {"max_turns": None}},
    {EXECUTION_LIMITS_KEY: "not-a-dict"},
])
def test_a_malformed_override_falls_back_rather_than_failing_the_run(bad):
    """The orchestrator-wide value is always a safe answer, so a bad override must not be able
    to fail a run that would otherwise have succeeded."""

    execution = SimpleNamespace(max_turns=40, sample_max_cost=0.30)
    limits = task_execution_limits(bad, execution)
    assert limits.billed_cost_limit == 0.30
    assert limits.max_turns == 40


@pytest.mark.parametrize("task_limits, expected", [
    ({EXECUTION_LIMITS_KEY: {"max_turns": 5}}, 5),
    ({}, 40),
])
def test_a_per_task_turn_limit_reaches_the_conversation(monkeypatch, task_limits, expected):
    """The worker put `max_turns` on the Attempt, and the conversation enforces
    `config.execution.max_turns`, which nothing overrode -- so the limit was recorded and never
    bound. Asserted on the config the task runner actually receives."""

    import asyncio

    import ape.scaffolds.runner as runner

    seen = {}

    async def fake_run_task(self, **kwargs):
        seen["max_turns"] = self.config.execution.max_turns
        return None, None

    monkeypatch.setattr(runner, "TaskRunner", type("R", (runner.TaskRunner,), {
        "run_task": fake_run_task}))
    monkeypatch.setattr("ape.tasks.base.create_task_from_data",
                        lambda data, config, task_config_overrides=None: None)
    config = _config()
    config.execution.max_turns = 40
    asyncio.run(runner.main_from_params({
        "task_data": {"task_type": "t", **task_limits},
        "config": config.model_dump(mode="json"),
        "scaffold_type": "ape_agent",
    }))
    assert seen["max_turns"] == expected


def test_reserved_run_level_keys_survive_into_the_job(monkeypatch):
    """`BaseTaskData` ignores keys it does not declare, so a task's dump loses every
    run-level directive. This silently dropped every `execution_limits` a lead attached to its
    arms -- they ran under the nested orchestrator's sample_max_cost instead -- and turned a
    session replay into an ordinary run from the prompt."""

    from ape.scaffolds.ape_agent.replay import SESSION_REPLAY_KEY
    from ape.tasks.base import create_task_from_data
    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmData

    payload = {
        **ReviewArmData(
            task_id="t", invocation_id="wu:a#naming", arm_id="naming", work_unit_id="wu:a",
            episode_id="ep:1", pr_number=1, diff="d", changed_files=["A.lean"],
            change_ids=["change:a"], entity_ids_by_change={}, primary_subjects_by_change={},
            rendered_system_prompt="s", rendered_user_prompt="u",
            rendered_prompt_sha256="a" * 64,
            target_workspace={"name": "target", "commit_hash": "c" * 40,
                              "repo_url": "https://e.invalid/m.git",
                              "default_target": "Mathlib"}).model_dump(mode="json"),
        EXECUTION_LIMITS_KEY: {"max_turns": 5, "billed_cost_limit": 0.1},
        SESSION_REPLAY_KEY: {"prefix_path": "p.jsonl", "prefix_sha256": "0" * 64,
                             "recorded_tool_sha256": {}},
    }
    task = create_task_from_data(payload, _config())
    job = task.job_data()
    assert job[EXECUTION_LIMITS_KEY] == {"max_turns": 5, "billed_cost_limit": 0.1}
    assert job[SESSION_REPLAY_KEY]["prefix_path"] == "p.jsonl"
    # Still the validated model otherwise, including the identity the orchestrator keys on.
    assert job["global_index"] == task.data.global_index
    assert task_execution_limits(job, SimpleNamespace(max_turns=40, sample_max_cost=0.3)
                                 ).max_turns == 5


def test_the_orchestrator_hands_the_worker_job_data():
    """The seam where the keys were lost: a re-dump of the model instead of the payload."""

    import inspect

    from ape.orchestration.orchestrator import TaskOrchestrator

    source = inspect.getsource(TaskOrchestrator)
    assert '"task_data": task.job_data()' in source
    assert 'task.data.model_dump(mode="json")' not in source


def test_a_spec_attaches_its_limits_to_the_payload():
    spec = TaskExecutionSpec(
        spec_id="s1", task_type="t", task_data={"task_id": "x"}, billed_cost_limit=0.5)
    payload = spec.with_limits()
    assert payload["task_id"] == "x"
    assert payload[EXECUTION_LIMITS_KEY] == {"billed_cost_limit": 0.5}


def test_a_spec_with_no_limits_leaves_the_payload_alone():
    """Almost every task has no override, and the payload it produces must be unchanged."""

    spec = TaskExecutionSpec(spec_id="s1", task_type="t", task_data={"task_id": "x"})
    assert spec.with_limits() == {"task_id": "x"}


# --- what nesting imposes, and what it does not -------------------------------------------


def test_nesting_imposes_in_process_execution(tmp_path):
    """The parent is already inside a worker; a process pool inside a pool is not a
    configuration choice."""

    assert nested_config(tmp_path, _config(), group="g").execution.num_processes == 0


def test_nesting_puts_children_under_the_parent_attempt(tmp_path):
    config = nested_config(tmp_path, _config(), group="wave1")
    assert config.runs_base_dir == tmp_path / "subtasks" / "wave1"
    assert config.runs_base_dir.is_dir()


def test_nesting_does_not_impose_the_parents_sample_count(tmp_path):
    """`judgment` runs `sample_count=num_judges` for a majority vote. A primitive that forced
    the parent's value on its children could not serve it."""

    config = nested_config(tmp_path, _config(), group="g", sample_count=3)
    assert config.execution.sample_count == 3


def test_a_caller_may_supply_a_different_base_config(tmp_path):
    """`judgment` builds its own config with a different model entirely."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    other = ApeAgentConfig()
    other.execution.max_turns = 7
    config = nested_config(tmp_path, other, group="g")
    assert config.execution.max_turns == 7
    assert config.execution.num_processes == 0     # still imposed


def test_concurrency_is_bounded(tmp_path):
    """Nothing bounded it while tiers were gathered concurrently: four leads, four arms each,
    three tiers was up to 48 simultaneous Lean compiles from one process."""

    config = nested_config(tmp_path, _config(), group="g", concurrency=2)
    assert config.execution.max_concurrency == 2
    assert DEFAULT_NESTED_CONCURRENCY >= 1


def test_an_enum_field_set_by_a_caller_keeps_its_type(tmp_path):
    """`ExecutionConfig` sets no `validate_assignment`, so a raw string passes every `==`
    while `orchestrator.py`'s `.early_stop_mode.value` raises on it -- which is how every
    delegate call failed on the second smoke run."""

    config = nested_config(tmp_path, _config(), group="g",
                           early_stop_mode=EarlyStopMode.DISABLED)
    assert isinstance(config.execution.early_stop_mode, EarlyStopMode)
    assert config.execution.early_stop_mode.value == "disabled"


def test_base_task_exposes_the_primitive():
    from ape.tasks.base import BaseTask

    assert callable(getattr(BaseTask, "spawn_subtasks", None))


# --- all three call sites share one convention --------------------------------------------


def test_every_nested_call_site_uses_the_shared_convention():
    """The acceptance test for this being a primitive rather than a fourth convention.

    `TaskOrchestrator(` was constructed directly in four files. Three of them nest work, and
    they had three different ideas of where children go, how to read what came back, and what
    to call a job that paused. They now call `run_subtasks` and construct no orchestrator at
    all -- which is the stronger statement, because sharing the directory helper while keeping
    a private reader is exactly the state that lost a paused child in two of them.
    """

    from pathlib import Path

    sources = {
        "delegation": "src/ape/tasks/lean_tasks/formal_math/review/delegation.py",
        "judgment": "src/ape/tasks/lean_tasks/formal_math/judgment/task.py",
        "review_gate": (
            "src/ape/tasks/lean_tasks/formal_math/reviewed_proof_engineering/review_gate.py"),
    }
    for name, path in sources.items():
        text = Path(path).read_text(encoding="utf-8")
        assert "run_subtasks" in text or "nested_config" in text, (
            f"{name} does not use the shared convention")
        # And none of them still hand-rolls the directory.
        assert 'parent_attempt_path / "subtasks"' not in text, name

    # Fully migrated: no private orchestrator, no private reader of what the children did.
    # `judgment` and `review_gate` follow; they share the directory helper today.
    delegation = Path(sources["delegation"]).read_text(encoding="utf-8")
    assert "run_subtasks" in delegation
    assert "TaskOrchestrator(" not in delegation, (
        "delegation constructs its own orchestrator again; the primitive exists so the layout, "
        "the reader and the ledger vocabulary are not written a second time")


def test_the_directory_is_the_one_genuine_invariant(tmp_path):
    """A caller may override the model, the sample count, the turn limit, even
    `num_processes`. It may not put its children somewhere else: two children sharing a
    workspace race in `_ensure_patched_target_workspace`, which unlinks and rebuilds whatever
    path it is handed."""

    config = nested_config(tmp_path, _config(), group="g", num_processes=4)
    assert config.execution.num_processes == 4          # caller's choice honoured
    assert config.runs_base_dir == tmp_path / "subtasks" / "g"   # not negotiable


# --- what comes back: one typed ChildRun per spec ------------------------------------------


import asyncio
import json
from datetime import datetime

from ape.orchestration.models import (
    Attempt, ChildRun, ExecutionStatus, Sample, TaskExecutionStatus,
)
from ape.orchestration.persistence import TaskStorage
from ape.tasks.base import (
    BaseTask, BaseTaskConfig, BaseTaskData, BaseTaskResult, register_task,
)


class _ProbeData(BaseTaskData):
    task_type: str = "subtask_probe"
    payload: str = ""


class _ProbeResult(BaseTaskResult):
    answer: str = ""


class _ProbeConfig(BaseTaskConfig):
    pass


class _ProbeTask(BaseTask):
    task_type = "subtask_probe"
    data_class = _ProbeData
    task_config_class = _ProbeConfig
    task_result_class = _ProbeResult


register_task("subtask_probe", _ProbeTask)


def _spec(spec_id: str, payload: str, **kwargs):
    return TaskExecutionSpec(
        spec_id=spec_id, task_type="subtask_probe",
        task_data={"task_type": "subtask_probe", "task_id": spec_id, "payload": payload},
        **kwargs)


async def _write_success(task_dir, index, answer="filed"):
    """What a finished task leaves: an aggregated result and a successful sample."""

    storage = TaskStorage(task_dir, index)
    result = _ProbeResult(task_id="t", task_type="subtask_probe", global_index=index,
                          success=True, score=1.0, answer=answer)
    await storage.save_task_result(result)
    await storage.save_sample(Sample(
        sample_id="s", task_global_index=index, sample_index=0,
        status=ExecutionStatus.SUCCESS, created_at=datetime.now(), updated_at=datetime.now(),
        attempts=[Attempt(attempt_id=0, path=task_dir / "a", status=ExecutionStatus.SUCCESS,
                          created_at=datetime.now(), max_turns=10, cost_limit=None,
                          cost=0.2, cached_cost=0.1,
                          result=result.model_dump(mode="json"))]))


async def _write_paused(task_dir, index):
    """What a task that stopped on its budget leaves: a sample, and NO task_result.json.

    This is the row the old readers could not see: the orchestrator aggregates only finished
    tasks, so a paused child is absent from `results.task_results` entirely.
    """

    storage = TaskStorage(task_dir, index)
    await storage.save_sample(Sample(
        sample_id="s", task_global_index=index, sample_index=0,
        status=ExecutionStatus.PAUSED_COST_LIMIT, created_at=datetime.now(),
        updated_at=datetime.now(),
        attempts=[Attempt(attempt_id=0, path=task_dir / "a",
                          status=ExecutionStatus.PAUSED_COST_LIMIT,
                          created_at=datetime.now(), max_turns=10, cost_limit=0.3,
                          cost=0.6, cached_cost=0.3, result=None)]))


def _run(monkeypatch, tmp_path, specs, writers, **kwargs):
    """Drive `run_subtasks` with the orchestrator's execution stubbed but its layout real."""

    from ape.orchestration import orchestrator as orchestrator_module

    seen = {}

    async def fake_run(self, tasks):
        seen["tasks_dir"] = self.tasks_dir
        seen["workspace_path"] = self.workspace_path
        seen["max_concurrency"] = self.config.execution.max_concurrency
        seen["num_processes"] = self.config.execution.num_processes
        for task in tasks:
            index = task.data.global_index
            await writers[task.data.task_id](self.tasks_dir / index, index)
        return SimpleNamespace(task_results=[], total_token_usage=None)

    monkeypatch.setattr(orchestrator_module.TaskOrchestrator, "run", fake_run)
    from ape.orchestration.subtasks import run_subtasks

    runs, _results = asyncio.run(run_subtasks(
        specs, attempt_path=tmp_path, config=_config(), group="wave1", **kwargs))
    return runs, seen


def test_a_paused_child_is_reported_rather_than_lost(monkeypatch, tmp_path):
    """The defect this contract exists to close. `results.task_results` holds only tasks the
    orchestrator aggregated, and a task with a resumable sample writes `task_outcome.json` and
    returns before aggregation -- so both readers this replaces dropped it, and a wave's ledger
    silently omitted the job that spent its whole budget."""

    runs, _ = _run(monkeypatch, tmp_path,
                   [_spec("filed", "a"), _spec("starved", "b")],
                   {"filed": _write_success, "starved": _write_paused})

    assert sorted(runs) == ["filed", "starved"]
    assert runs["starved"].outcome.execution_status is TaskExecutionStatus.PAUSED
    assert runs["starved"].succeeded is False and runs["starved"].result is None
    # And its spend is on the row, which is the reason the row has to exist at all.
    assert runs["starved"].outcome.billed_cost == pytest.approx(0.3)


def test_a_successful_child_comes_back_as_its_own_result_class(monkeypatch, tmp_path):
    """Not a dict the caller re-validates. `JobOutcome` re-dumped the result and read fields off
    the dump, which is why a field the arm recorded and the result class did not declare was
    invisible for a whole run."""

    runs, _ = _run(monkeypatch, tmp_path, [_spec("filed", "a")], {"filed": _write_success})
    child = runs["filed"]
    assert isinstance(child.result, _ProbeResult) and child.result.answer == "filed"
    assert child.succeeded is True
    assert child.outcome.execution_status is TaskExecutionStatus.COMPLETED


def test_the_spec_travels_with_the_answer(monkeypatch, tmp_path):
    """`required` and `budget_scope` are read beside the outcome -- the coverage-gap rule and
    the discretionary-spend rule both need them, and joining them back on by id is what they
    did before."""

    runs, _ = _run(monkeypatch, tmp_path,
                   [_spec("floor", "a", required=True, budget_scope="floor")],
                   {"floor": _write_success})
    assert runs["floor"].spec.required is True
    assert runs["floor"].spec.budget_scope == "floor"


def test_a_required_child_without_a_result_is_said_out_loud(monkeypatch, tmp_path):
    messages = []
    logger = SimpleNamespace(warning=lambda *args, **kwargs: messages.append(args[0] % args[1:]),
                             info=lambda *a, **k: None, error=lambda *a, **k: None)
    _run(monkeypatch, tmp_path, [_spec("floor", "a", required=True)],
         {"floor": _write_paused}, logger=logger)
    assert any("coverage gap" in item for item in messages), messages


def test_the_batch_directory_is_the_id_the_caller_gave(monkeypatch, tmp_path):
    """`orchestrator_id` was assigned AFTER construction, which is too late: the orchestrator
    fixes `workspace_path = runs_base_dir / orchestrator_id` in `__init__`, so children landed
    in a timestamped directory and a resumed parent could not find the work it had paid for."""

    _runs, seen = _run(monkeypatch, tmp_path, [_spec("filed", "a")], {"filed": _write_success},
                       orchestrator_id="33098_w1")
    assert seen["workspace_path"] == tmp_path / "subtasks" / "wave1" / "33098_w1"


def test_two_specs_with_the_same_payload_are_refused(monkeypatch, tmp_path):
    """`global_index` is a content hash and resume skips a task whose result exists, so two
    identical payloads are one task and the second spec would be handed the first's result with
    nothing saying so."""

    from ape.orchestration.subtasks import run_subtasks

    with pytest.raises(ValueError) as error:
        asyncio.run(run_subtasks(
            [_spec("first", "same"), _spec("second", "same")],
            attempt_path=tmp_path, config=_config(), group="wave1"))
    assert "identical task data" in str(error.value)
    assert "'first'" in str(error.value) and "'second'" in str(error.value)


def test_an_unreadable_child_does_not_lose_the_wave(monkeypatch, tmp_path):
    """Everything after the orchestrator returns derives from work already paid for. A failure
    there used to discard the whole wave -- `pr5_smoke4_rep8` spent $3.13 billed and reported
    $0.27 -- so a child that cannot be read is a failed row, not an exception."""

    async def explode(task_dir, index):
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "samples").mkdir()
        (task_dir / "samples" / "sample_0.json").write_text("{ not json")

    runs, _ = _run(monkeypatch, tmp_path, [_spec("broken", "a"), _spec("fine", "b")],
                   {"broken": explode, "fine": _write_success})
    assert sorted(runs) == ["broken", "fine"]
    assert runs["fine"].succeeded is True
    assert runs["broken"].succeeded is False


def test_concurrency_none_leaves_the_callers_value_alone(monkeypatch, tmp_path):
    """`judgment` sets its own `max_concurrency` and passes its config through. A default that
    overwrote it would be a silent change to how many judges run at once."""

    config = _config()
    config.execution.max_concurrency = 7

    from ape.orchestration import orchestrator as orchestrator_module
    from ape.orchestration.subtasks import run_subtasks

    seen = {}

    async def fake_run(self, tasks):
        seen["max_concurrency"] = self.config.execution.max_concurrency
        return SimpleNamespace(task_results=[], total_token_usage=None)

    monkeypatch.setattr(orchestrator_module.TaskOrchestrator, "run", fake_run)
    asyncio.run(run_subtasks([_spec("one", "a")], attempt_path=tmp_path, config=config,
                             group="wave1"))
    assert seen["max_concurrency"] == 7


def test_without_an_attempt_path_the_children_are_not_nested(monkeypatch, tmp_path):
    """`judgment` and `review_gate` both branch on having a parent attempt: invoked outside one
    there is nowhere to nest, and their children have always gone to the default runs root."""

    config = _config()
    config.runs_base_dir = tmp_path / "top"
    config.execution.num_processes = 2

    from ape.orchestration import orchestrator as orchestrator_module
    from ape.orchestration.subtasks import run_subtasks

    seen = {}

    async def fake_run(self, tasks):
        seen["base"] = self.config.runs_base_dir
        seen["num_processes"] = self.config.execution.num_processes
        return SimpleNamespace(task_results=[], total_token_usage=None)

    monkeypatch.setattr(orchestrator_module.TaskOrchestrator, "run", fake_run)
    asyncio.run(run_subtasks([_spec("one", "a")], attempt_path=None, config=config,
                             group="subtasks"))
    assert seen["base"] == tmp_path / "top"
    assert seen["num_processes"] == 2       # not forced to 0 when there is no parent worker


def test_nested_usage_sums_the_children(monkeypatch, tmp_path):
    runs, _ = _run(monkeypatch, tmp_path, [_spec("a", "a"), _spec("b", "b")],
                   {"a": _write_success, "b": _write_success})
    from ape.orchestration.subtasks import nested_usage

    usage = nested_usage(runs)
    assert usage.cached_total_cost == pytest.approx(0.2)   # billed, both children
    assert usage.total_cost == pytest.approx(0.4)          # nominal


def test_every_scheduled_child_is_indexed_including_the_paused_one(monkeypatch, tmp_path):
    """The index is how a later stage finds a session. Built from the results alone it held
    only aggregated tasks, so a paused child had no row and `cli replay` had to locate task
    directories another way -- it says so in its own comment, having lost two sessions to it."""

    from ape.orchestration.execution_index import by_semantic_id

    index = tmp_path / "execution_index.jsonl"
    runs, _ = _run(monkeypatch, tmp_path, [_spec("filed", "a"), _spec("starved", "b")],
                   {"filed": _write_success, "starved": _write_paused}, index_path=index)
    rows = by_semantic_id(index)
    assert sorted(rows) == ["filed", "starved"]
    assert rows["starved"]["global_index"] == runs["starved"].global_index
