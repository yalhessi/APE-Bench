"""A task setting takes effect on every path that builds the task, or the task is refused.

`create_task_from_data` is how planning, direct construction, the worker and nested execution all
reach a task. Until 2026-10-22 it rebuilt the config from the overrides alone, filtered to the
config class's fields: a concrete `config.task_config` was never read, a misspelled key became the
default, and a parent's settings were broadcast into children of another type and kept wherever a
name matched. Both nested judges have run under their class default since they were written
(`docs/todo/framework-defects-2026-09.md` §1).

Each test asserts at the far end: on the task the worker rebuilds from the serialized
orchestrator config, not only on the parent-side object, because that is the side that dropped
settings twice before (`.claude/rules/mathlib-review.md`, "a directive that travels in task data
must be asserted at the far end").
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from ape.scaffolds.ape_agent.config import ApeAgentConfig
from ape.tasks.base import TaskConfigError, create_task_from_data, resolve_task_config
from ape.tasks.lean_tasks.formal_math.judgment.task import (
    LeanJudgmentConfig, LeanJudgmentData, LeanJudgmentTask,
)
from ape.tasks.lean_tasks.formal_math.review import (
    ReviewArmConfig, ReviewLeadConfig, SoloReviewTask,
)

NON_DEFAULT_MODE = ("generated_only" if LeanJudgmentConfig().judge_mode != "generated_only"
                    else "with_ground_truth")


def _judge_payload():
    return LeanJudgmentData(
        task_id="j", target_code="a", original_code="b", task_description="d",
        reference_implementation="r", gold_diff="g", filename="f.lean",
        target_workspace={"name": "ws"}, metadata={}).model_dump(mode="json")


def _worker_rebuild(orchestrator_config, task):
    """What `scaffolds.runner.main_from_params` does with the job the orchestrator hands it."""

    rebuilt_config = type(orchestrator_config).model_validate(
        orchestrator_config.model_dump(mode="json"))
    return create_task_from_data(task.job_data(), rebuilt_config,
                                 task_config_overrides=rebuilt_config.task_config_overrides)


# --- precedence and refusal -----------------------------------------------------------------


def test_a_concrete_config_of_the_tasks_own_class_takes_effect():
    config = ApeAgentConfig(task_config=LeanJudgmentConfig(judge_mode=NON_DEFAULT_MODE))
    task = create_task_from_data(_judge_payload(), config)
    assert task.config.task_config.judge_mode == NON_DEFAULT_MODE


def test_a_concrete_config_survives_the_worker_boundary():
    """The field is annotated `BaseTaskConfig` and pydantic dumps by annotation, so the subclass
    fields vanished on the way to the worker with no warning."""

    config = ApeAgentConfig(task_config=LeanJudgmentConfig(judge_mode=NON_DEFAULT_MODE))
    rebuilt = ApeAgentConfig.model_validate(config.model_dump(mode="json"))
    assert isinstance(rebuilt.task_config, LeanJudgmentConfig)
    assert rebuilt.task_config.judge_mode == NON_DEFAULT_MODE
    # Only what was set crosses, so an unset field stays a default rather than a frozen value.
    assert rebuilt.task_config.model_fields_set == {"judge_mode"}


def test_an_untagged_task_config_dump_still_validates_as_before():
    """An orchestrator config written before 2026-10-22 has no class tag."""

    rebuilt = ApeAgentConfig.model_validate(
        {"task_config": {"enabled_tools": ["file_read"], "disabled_tools": None}})
    assert rebuilt.task_config.enabled_tools == ["file_read"]


def test_precedence_is_defaults_then_config_then_record_then_invocation():
    config = ApeAgentConfig(task_config=ReviewArmConfig(finding_budget=4, prompt_version="v1"))
    resolved = resolve_task_config(
        type("T", (), {"task_config_class": ReviewArmConfig, "task_type": "t"}), config,
        record_overrides={"finding_budget": 5, "enabled_tools": ["file_read"]},
        invocation_overrides={"finding_budget": 6})
    assert resolved.finding_budget == 6               # invocation beats the record
    assert resolved.enabled_tools == ["file_read"]     # record beats the concrete config
    assert resolved.prompt_version == "v1"             # concrete config beats the default


@pytest.mark.parametrize("where", ["invocation", "record", "config"])
def test_a_setting_that_would_have_no_effect_is_refused(where):
    payload = _judge_payload()
    config = ApeAgentConfig()
    invocation = None
    if where == "invocation":
        invocation = {"judge_mod": NON_DEFAULT_MODE}
    elif where == "record":
        payload["task_config_overrides"] = {"judge_mod": NON_DEFAULT_MODE}
    else:
        config = ApeAgentConfig(task_config=ReviewLeadConfig())
    with pytest.raises(TaskConfigError) as raised:
        create_task_from_data(payload, config, task_config_overrides=invocation)
    message = str(raised.value)
    assert "lean_judgment" in message
    assert ("judge_mod" in message) if where != "config" else ("ReviewLeadConfig" in message)


# --- nested execution: nothing inherited, everything explicit, both sides agree ------------


def _drive_run_subtasks(monkeypatch, tmp_path, specs, *, config, **kwargs):
    from ape.orchestration import orchestrator as orchestrator_module
    from ape.orchestration.subtasks import run_subtasks

    seen = {}

    async def fake_run(self, tasks):
        seen["config"] = self.config
        seen["tasks"] = list(tasks)
        return SimpleNamespace(task_results=[], total_token_usage=None, workspace_path=None)

    monkeypatch.setattr(orchestrator_module.TaskOrchestrator, "run", fake_run)
    asyncio.run(run_subtasks(specs, attempt_path=tmp_path, config=config, group="g", **kwargs))
    return seen


def test_a_lead_runs_settings_do_not_reach_its_arms(monkeypatch, tmp_path):
    """The 17 lead configs on disk put five lead-only budget keys and the run's tool list in the
    run-level overrides, and the arms were dispatched with the lead's config. Every one of those
    tool lists equals the arms' own default, so not inheriting it changes nothing on disk."""

    from ape.orchestration.models import TaskExecutionSpec
    from ape.tasks.lean_tasks.formal_math.review.base import DEFAULT_REVIEW_TOOLS

    lead_overrides = {"enabled_tools": ["file_read"], "standard_budget_cap": 0.3,
                      "max_delegations": 9}
    parent = ApeAgentConfig(task_config=ReviewLeadConfig(**lead_overrides),
                            task_config_overrides=lead_overrides)
    spec = TaskExecutionSpec(spec_id="arm", task_type=LeanJudgmentTask.task_type,
                             task_data=_judge_payload())
    seen = _drive_run_subtasks(monkeypatch, tmp_path, [spec], config=parent)
    child = seen["config"]
    assert child.task_config is None and child.task_config_overrides is None
    for task in (seen["tasks"][0], _worker_rebuild(child, seen["tasks"][0])):
        assert task.config.task_config.enabled_tools == LeanJudgmentConfig().enabled_tools
    assert ReviewArmConfig().enabled_tools == DEFAULT_REVIEW_TOOLS
    # And a lead run says so, where a user of `--set task_config.X` will read it.
    import inspect

    from src.mathlib_review.review import runner

    assert "configures the lead only" in inspect.getsource(runner.run)


def test_a_childs_explicit_settings_reach_both_sides(monkeypatch, tmp_path):
    from ape.orchestration.models import TaskExecutionSpec

    spec = TaskExecutionSpec(spec_id="j", task_type=LeanJudgmentTask.task_type,
                             task_data=_judge_payload())
    seen = _drive_run_subtasks(monkeypatch, tmp_path, [spec], config=ApeAgentConfig(),
                               task_config_overrides={"judge_mode": NON_DEFAULT_MODE})
    parent_side = seen["tasks"][0]
    worker_side = _worker_rebuild(seen["config"], parent_side)
    assert parent_side.config.task_config.judge_mode == NON_DEFAULT_MODE
    assert worker_side.config.task_config.judge_mode == NON_DEFAULT_MODE


def test_the_nested_judge_runs_in_the_mode_it_was_built_with(monkeypatch, tmp_path):
    """The real entry point, with a parent whose own settings would have been broadcast."""

    from ape.tasks.base import SemanticValidationConfig
    from ape.tasks.lean_tasks.formal_math.judgment.task import lean_semantic_evaluation
    from ape.tasks.models import WorkspaceInfo

    parent = ApeAgentConfig(task_config=ReviewLeadConfig(max_delegations=3),
                            task_config_overrides={"max_delegations": 3})
    from ape.orchestration import orchestrator as orchestrator_module

    seen = {}

    async def fake_run(self, tasks):
        seen["config"], seen["tasks"] = self.config, list(tasks)
        return SimpleNamespace(task_results=[], total_token_usage=None, workspace_path=None)

    monkeypatch.setattr(orchestrator_module.TaskOrchestrator, "run", fake_run)
    out = asyncio.run(lean_semantic_evaluation(
        final_code="theorem x : True := trivial", original_code="theorem x : True := by trivial",
        task_description="d", semantic_config=SemanticValidationConfig(judge_mode=NON_DEFAULT_MODE),
        base_config=parent, target_workspace=WorkspaceInfo(name="ws"),
        parent_attempt_path=tmp_path))
    assert "tasks" in seen, out
    worker_side = _worker_rebuild(seen["config"], seen["tasks"][0])
    assert seen["tasks"][0].config.task_config.judge_mode == NON_DEFAULT_MODE
    assert worker_side.config.task_config.judge_mode == NON_DEFAULT_MODE


# --- the review path is unchanged ----------------------------------------------------------


def test_a_review_run_config_still_reaches_its_solo_task(tmp_path):
    """The YAML loader turns `task_config:` into invocation overrides; that path already worked
    and must keep working, and a typo in it is now refused rather than defaulted."""

    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig

    task_class = SoloReviewTask
    resolved = resolve_task_config(task_class, ApeAgentConfig(),
                                   invocation_overrides={"finding_budget": 3})
    assert resolved.finding_budget == 3
    assert SoloReviewConfig().finding_budget != 3
    with pytest.raises(TaskConfigError, match="finding_budegt"):
        resolve_task_config(task_class, ApeAgentConfig(),
                            invocation_overrides={"finding_budegt": 3})


def test_the_pilots_review_gate_neither_sees_gold_nor_holds_write_tools(monkeypatch, tmp_path):
    """`docs/todo/thesis-pilot-integrity.md`, defects 1 and 2: the pilot config says
    `judge_mode: generated_only`, the gate's config class inherits `with_ground_truth`, and in
    `ape_bench_reviewed_pe_gpt52_first5_fixed3` all 11 reviewer sessions had
    `<maintainer_reference_diff>` in their prompt; and the reviewer was built from the generator's
    config, so it was offered `file_write`, `file_edit` and `file_multi_edit`. Built here exactly
    as `LeanReviewedProofEngineeringTask` builds it, with the pilot's own task config."""

    from pathlib import Path

    from ape.orchestration import orchestrator as orchestrator_module
    from ape.tasks.lean_tasks.formal_math.reviewed_proof_engineering.review_gate import (
        LeanReviewGateConfig, lean_review_gate,
    )
    from ape.tasks.lean_tasks.formal_math.reviewed_proof_engineering.task import (
        LeanReviewedProofEngineeringConfig,
    )
    from ape.tasks.models import WorkspaceInfo
    from ape.utils.config_loader import load_yaml

    pilot = load_yaml(Path("configs/ape_bench_reviewed_proof_engineering_pilot.yaml"))
    generator_settings = pilot["task_config"]
    assert generator_settings["review_gate"]["judge_mode"] == "generated_only"
    assert "file_write" in generator_settings["enabled_tools"]
    generator = ApeAgentConfig(
        task_config=LeanReviewedProofEngineeringConfig.model_validate(generator_settings),
        task_config_overrides=generator_settings)
    gate = LeanReviewedProofEngineeringConfig.model_validate(generator_settings).review_gate

    seen = {}

    async def fake_run(self, tasks):
        seen["config"], seen["tasks"] = self.config, list(tasks)
        return SimpleNamespace(task_results=[], total_token_usage=None, workspace_path=None)

    monkeypatch.setattr(orchestrator_module.TaskOrchestrator, "run", fake_run)
    asyncio.run(lean_review_gate(
        final_code="theorem x : True := trivial", original_code="theorem x : True := by trivial",
        task_description="d", review_config=LeanReviewGateConfig(judge_mode=gate.judge_mode),
        base_config=generator, target_workspace=WorkspaceInfo(name="ws"), gold_diff="- a\n+ b",
        parent_attempt_path=tmp_path))
    assert "tasks" in seen
    file_editing = {"file_write", "file_edit", "file_multi_edit"}
    for reviewer in (seen["tasks"][0], _worker_rebuild(seen["config"], seen["tasks"][0])):
        assert reviewer.config.task_config.judge_mode == "generated_only"
        # The reviewer holds its own class's grant, not the generator's.
        assert reviewer.config.task_config.enabled_tools == LeanReviewGateConfig().enabled_tools
        assert not file_editing & set(reviewer.config.task_config.enabled_tools or [])
