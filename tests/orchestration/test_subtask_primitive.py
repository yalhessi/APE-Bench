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
    they had three different ideas of where children go. They now share one.
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
        assert "nested_config" in text, f"{name} does not use the shared convention"
        # And none of them still hand-rolls the directory.
        assert 'parent_attempt_path / "subtasks"' not in text, name


def test_the_directory_is_the_one_genuine_invariant(tmp_path):
    """A caller may override the model, the sample count, the turn limit, even
    `num_processes`. It may not put its children somewhere else: two children sharing a
    workspace race in `_ensure_patched_target_workspace`, which unlinks and rebuilds whatever
    path it is handed."""

    config = nested_config(tmp_path, _config(), group="g", num_processes=4)
    assert config.execution.num_processes == 4          # caller's choice honoured
    assert config.runs_base_dir == tmp_path / "subtasks" / "g"   # not negotiable
