"""Decision-turn replay of a review arm: the arm task itself, cut before it submits.

Built from real classes -- the arm task, its `submit_candidates` schema as the scaffold lists
it, sessions assembled with `ConversationSession` -- because a wrong replay is wrong silently:
it still produces a submission, and the submission would be read as a condition's effect.
The generic mechanics are pinned in `tests/ape/test_session_replay.py`.
"""

from __future__ import annotations

import asyncio

import pytest

from ape.llm_clients.config import LLMConfig
from ape.llm_clients.models import ContentBlock, ConversationSession
from ape.scaffolds.ape_agent.config import ApeAgentConfig
from ape.scaffolds.ape_agent.conversation import ApeAgentConversationManager
from ape.scaffolds.ape_agent.replay import (
    SESSION_REPLAY_KEY, ReplayCondition, ReplayRefused, SessionReplay, cut_before_tool_call,
    load_prefix,
    recorded_tools, replay_task_data,
)
from ape.tasks.base import create_task_from_data
from ape.tasks.lean_tasks.formal_math.review.arm import (
    ARM_TASK_TYPE, ReviewArmData, ReviewArmTask,
)
from src.mathlib_review.review.replay import (
    SUBMIT_TOOL, accepted_summary, decision_record,
)

ARM_FIELDS = dict(
    task_id="t", invocation_id="wu:a#naming", arm_id="naming", spec_id="naming",
    work_unit_id="wu:a", episode_id="ep:1", pr_number=1, diff="d", changed_files=["A.lean"],
    change_ids=["change:a"], entity_ids_by_change={"change:a": []},
    primary_subjects_by_change={"change:a": "Foo.bar"}, paths_by_change={"change:a": "A.lean"},
    rendered_system_prompt="NAMING CONTRACT. Abstain when unsure.",
    rendered_user_prompt="Review Foo.bar.", rendered_prompt_sha256="a" * 64,
    target_workspace={"name": "target", "commit_hash": "c" * 40,
                      "repo_url": "https://e.invalid/m.git", "default_target": "Mathlib"},
)
CONFIG = ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2"))


def _registered_tools(task):
    """What the scaffold sends: registered on fastmcp, listed by the conversation manager."""

    from fastmcp import Client, FastMCP

    async def listed():
        mcp = FastMCP("probe")
        await task.register_task_tools(mcp)
        async with Client(mcp) as client:
            return await ApeAgentConversationManager(ApeAgentConfig())._get_available_tools(
                client)

    return asyncio.run(listed())


@pytest.fixture(scope="module")
def payload():
    return ReviewArmData(**ARM_FIELDS).model_dump(mode="json")


@pytest.fixture(scope="module")
def tools(payload):
    return _registered_tools(create_task_from_data(payload, CONFIG))


def _call(session, call_id, name, arguments, result):
    session.add_assistant_message([ContentBlock.tool_use_block(call_id, name, arguments)],
                                  cwd="/w")
    session.add_tool_result(call_id, result, cwd="/w", tool_name=name)


def _session(tools):
    """Investigate, submit a mute abstention (refused), resubmit it labelled -- the shape of
    26 of 321 arm sessions on the v2 held-out rep."""

    session = ConversationSession()
    session.add_system_message([ContentBlock.text_block(ARM_FIELDS["rendered_system_prompt"])],
                               cwd="/w")
    session.add_tool_definitions(tools, cwd="/w")
    session.add_user_message([ContentBlock.text_block("Review Foo.bar.")], cwd="/w")
    _call(session, "c1", "lean_verify_edit", {"path": "A.lean"}, {"success": True})
    _call(session, "c2", SUBMIT_TOOL, {"candidates": []},
          {"evaluation_result": {"success": False, "message": "Only the label is missing."}})
    _call(session, "c3", SUBMIT_TOOL,
          {"abstention_reason": "already_correct", "candidates": [],
           "abstention_detail": "Foo.bar matches the prefix."},
          {"evaluation_result": {"success": True, "message": "Recorded 0 candidates"}})
    return [node.model_dump(mode="json") for node in session.nodes]


def test_the_decision_starts_before_the_first_submission(tools):
    nodes = _session(tools)
    prefix, index = cut_before_tool_call(nodes, SUBMIT_TOOL)
    assert index == 5 and prefix[-1]["type"] == "user"
    record = decision_record(nodes, index)
    assert (record["turns"], record["submissions"]) == (2, 2)
    assert record["refusals"] == ["Only the label is missing."]
    assert record["first"]["filed"] is False and record["first"]["abstention_reason"] is None


def test_a_replay_is_the_arm_task_not_a_new_task_type(tools, payload, tmp_path):
    """Its results are ordinary arm results, so finalize and the judge read them unchanged."""

    prefix, _ = cut_before_tool_call(_session(tools), SUBMIT_TOOL)
    replayed, content = replay_task_data(payload, prefix, ReplayCondition(name="null"),
                                         tmp_path / "p.jsonl", {"run": "r"})
    task = create_task_from_data(replayed, CONFIG)
    assert type(task) is ReviewArmTask and task.data.task_type == ARM_TASK_TYPE
    assert task.data.task_id == payload["task_id"]
    # `session_replay` is not a task field: the runtime attaches it.
    assert not hasattr(task.data, SESSION_REPLAY_KEY)


def test_reason_before_verdict_on_the_real_candidate_schema(tools, payload, tmp_path):
    """fastmcp inlines `$defs`, so one candidate's schema is at `properties/candidates/items`."""

    prefix, _ = cut_before_tool_call(_session(tools), SUBMIT_TOOL)
    condition = ReplayCondition(name="claim_first", tool_schema_edits=[
        {"tool": SUBMIT_TOOL, "property_order": ["abstention_detail", "abstention_reason"]},
        {"tool": SUBMIT_TOOL, "at": "properties/candidates/items",
         "property_order": ["claim", "requested_change"]},
    ])
    replayed, content = replay_task_data(payload, prefix, condition, tmp_path / "p.jsonl", {})
    (tmp_path / "p.jsonl").write_bytes(content)
    replay = SessionReplay.model_validate(replayed[SESSION_REPLAY_KEY])
    shown = {t["function"]["name"]: t["function"]["parameters"]
             for t in recorded_tools(load_prefix(replay))}[SUBMIT_TOOL]
    assert list(shown["properties"]) == ["abstention_detail", "abstention_reason", "candidates"]
    assert list(shown["properties"]["candidates"]["items"]["properties"])[:2] == [
        "claim", "requested_change"]

    # And the replayed arm task, run by the manager, is shown exactly that -- no drift today.
    task = create_task_from_data(replayed, CONFIG)
    task.session_replay = replay
    task.attempt_path = tmp_path
    manager = ApeAgentConversationManager(CONFIG, task=task)
    sent = manager._replay_tool_definitions(_registered_tools(task))
    assert {t["function"]["name"]: t["function"]["parameters"] for t in sent}[SUBMIT_TOOL] == shown
    assert '"tool_drift": []' in (tmp_path / "session_replay.json").read_text()


def test_the_accepted_submission_is_read_off_the_result():
    assert accepted_summary({"success": True, "candidates": [],
                             "abstention": {"reason": "already_correct"}}) == {
        "filed": False, "abstention_reason": "already_correct", "anchors": [],
        "candidate_keys": [], "model_confidence": []}
    filed = accepted_summary({"success": True, "candidates": [
        {"primary_change_id": "change:a", "concern_family": "naming",
         "issue_kind": "naming_convention_violation", "model_confidence": None}]})
    assert filed["anchors"] == ["change:a"] and filed["model_confidence"] == [None]
    assert accepted_summary({"success": False}) is None


# --- the pipeline, on a run tree built from the orchestrator's own classes -------------------


def _write_arm_task(run, tasks_root, invocation_id, nodes, result, config):
    """One arm task as a lead's nested orchestrator leaves it: sample, attempt, session."""

    import json
    from datetime import datetime

    from ape.orchestration.models import Attempt, ExecutionStatus, Sample, make_sample_id
    from ape.orchestration.persistence import TaskStorage

    global_index = str(abs(hash(invocation_id)))
    task_dir = tasks_root / global_index
    attempt_path = task_dir / "samples/0/attempts/attempt_1"
    attempt_path.mkdir(parents=True)
    (attempt_path / "ape_agent_session_20260913_000000__s.jsonl").write_text(
        "".join(json.dumps(node) + "\n" for node in nodes))
    now = datetime.now()
    sample = Sample(
        sample_id=make_sample_id(global_index, 0), sample_index=0,
        task_global_index=global_index, created_at=now, updated_at=now,
        attempts=[Attempt(attempt_id=1, path=attempt_path, status=ExecutionStatus.SUCCESS,
                          created_at=now, max_turns=40, cost_limit=0.3, result=result)])
    asyncio.run(TaskStorage(task_dir, global_index).save_sample(sample))
    (tasks_root.parent / "config.json").write_text(json.dumps({"config": config}))
    with (run / "execution_index.jsonl").open("a") as handle:
        handle.write(json.dumps({"semantic_id": invocation_id, "task_type": ARM_TASK_TYPE,
                                 "global_index": global_index, "task_dir": str(task_dir),
                                 "attempts": []}) + "\n")


@pytest.fixture
def recorded_run(tmp_path, monkeypatch, tools, payload):
    """A run with three arm sessions: two that submitted, one that never did."""

    import json

    import src.mathlib_review.review.replay as replay_module

    runs = tmp_path / "runs"
    monkeypatch.setattr(replay_module, "run_dir", lambda name: runs / name)
    run = runs / "source"
    run.mkdir(parents=True)
    config = CONFIG.model_dump(mode="json")
    accepted = {"success": True, "candidates": [], "abstention": {"reason": "already_correct"}}
    pool = []
    decided = []
    for _ in range(2):
        nodes = _session(tools)
        nodes[5]["message"]["usage"] = {"total_cost": 0.032, "cached_total_cost": 0.0095}
        decided.append(nodes)
    for arm, nodes in (("naming", decided[0]), ("docs", decided[1]),
                       ("style", _session(tools)[:5])):
        invocation_id = f"wu:a#{arm}"
        _write_arm_task(run, tmp_path / "nested" / arm / "tasks", invocation_id, nodes,
                        accepted, config)
        pool.append({"invocation_id": invocation_id, "task_data": {
            **payload, "invocation_id": invocation_id, "arm_id": arm}})
    (run / "arm_pool.jsonl").write_text("".join(json.dumps(row) + "\n" for row in pool))
    return runs


def _dataset(**fields):
    from src.mathlib_review.review.replay import ReplayDatasetConfig

    return ReplayDatasetConfig.model_validate({
        "of_run": "source", "run_name": "replay_null", "condition": {"name": "null"},
        "run_total_cost_cap": 10.0, **fields})


def test_sessions_are_found_through_the_index_and_storage(recorded_run):
    from src.mathlib_review.review.replay import select_sources

    sources, skipped = asyncio.run(select_sources(_dataset()))
    assert [s.invocation_id for s in sources] == ["wu:a#docs", "wu:a#naming"]
    assert skipped == [{"invocation_id": "wu:a#style",
                        "reason": "the session never called submit_candidates"}]
    only, _ = asyncio.run(select_sources(_dataset(arm_ids=["naming"])))
    assert [s.invocation_id for s in only] == ["wu:a#naming"]


def test_a_missing_arm_pool_is_refused_with_the_reason(recorded_run):
    from src.mathlib_review.review.replay import select_sources

    (recorded_run / "source/arm_pool.jsonl").unlink()
    with pytest.raises(ReplayRefused, match="gitignored"):
        asyncio.run(select_sources(_dataset()))


def test_a_replay_payload_is_capped_from_the_cut_and_writes_its_own_trace(recorded_run):
    from ape.orchestration.models import EXECUTION_LIMITS_KEY
    from src.mathlib_review.review.replay import replay_payload, select_sources

    sources, _ = asyncio.run(select_sources(_dataset()))
    out = recorded_run / "replay_null"
    built, content = replay_payload(sources[0], _dataset(decision_turns=3), out)
    assert built[EXECUTION_LIMITS_KEY] == {"max_turns": 1 + 3, "billed_cost_limit": 0.3}
    assert built["trace_path"] == str(out / "context_trace.jsonl")
    assert built[SESSION_REPLAY_KEY]["prefix_path"].startswith(str(out / "prefixes"))
    assert built[SESSION_REPLAY_KEY]["source"]["decision_node_index"] == 5
    assert sources[0].decision_stage_cost() == (0.0095, 0.032)
    assert built["task_type"] == ARM_TASK_TYPE


def test_sessions_under_different_models_are_not_replayed_together(recorded_run):
    from src.mathlib_review.review.replay import replay_scaffold, select_sources

    sources, _ = asyncio.run(select_sources(_dataset()))
    scaffold = replay_scaffold(sources, {"sample_count": 3})
    assert scaffold.execution.sample_count == 3
    assert scaffold.llm_config.model_name == "gpt_5.2"
    sources[1].scaffold_config["llm_config"]["temperature"] = 0.0
    with pytest.raises(ReplayRefused, match="different model"):
        replay_scaffold(sources, {})


def test_a_replay_config_cannot_change_the_model(tmp_path):
    from src.mathlib_review.review.replay import load_replay

    path = tmp_path / "r.yaml"
    path.write_text('llm_config: {model_name: other}\ndataset: {of_run: s, '
                    'condition: {name: "null"}, run_total_cost_cap: 1}\n')
    with pytest.raises(ReplayRefused, match="only `dataset` and `execution`"):
        load_replay(path)


def test_the_checked_in_config_loads_with_a_null_condition():
    """Bare `null` in YAML is None; the config quotes it."""

    from pathlib import Path

    from src.mathlib_review.review.replay import load_replay

    dataset, execution = load_replay(Path("configs/v5_replay.yaml"),
                                     {"dataset": {"of_run": "x"}})
    assert dataset.condition.name == "null" and dataset.condition.changes_nothing
    assert execution["sample_count"] == 3


@pytest.mark.parametrize("fields, match", [
    ({"run_name": "replay_other"}, "does not contain the condition"),
    ({"run_total_cost_cap": 0.0001}, "above run_total_cost_cap"),
])
def test_a_replay_is_refused_before_anything_is_written(recorded_run, fields, match):
    import logging

    from src.mathlib_review.review.replay import run_replay

    with pytest.raises((ReplayRefused, ValueError), match=match):
        asyncio.run(run_replay(_dataset(**fields), {}, logging.getLogger("t"), execute=True))
    assert not (recorded_run / "replay_null").exists()


def _row(invocation_id, arm, recorded_filed, replay_filed, condition="null", sample=0):
    def summary(filed):
        if filed is None:
            return None
        return {"filed": filed, "abstention_reason": None if filed else "already_correct",
                "anchors": ["change:a"] if filed else [],
                "candidate_keys": ["change:a|naming|None"] if filed else [],
                "model_confidence": [None] if filed else []}

    return {"invocation_id": invocation_id, "arm_id": arm, "condition": condition,
            "sample_index": sample, "status": "success", "cost": 0.03, "cached_cost": 0.01,
            "recorded": {"decision": {"refusals": []}, "accepted": summary(recorded_filed)},
            "replay": {"decision": {"turns": 1, "refusals": [],
                                    "first": {"model_confidence": [None] if replay_filed else []}},
                       "accepted": summary(replay_filed), "tool_drift": []}}


def test_the_report_reads_agreement_per_session_not_pooled():
    from src.mathlib_review.review.replay import replay_report

    rows = [_row("s1", "naming", False, False, sample=0), _row("s1", "naming", False, True, sample=1),
            _row("s2", "docs", True, True, sample=0), _row("s2", "docs", True, None, sample=1)]
    report = replay_report(rows)
    outcome = report["agreement_with_recorded"]["outcome"]
    assert (outcome["samples"], outcome["rate"]) == (3, round(2 / 3, 4))
    assert outcome["sessions_every_sample_agrees"] == 1
    assert report["samples_with_no_accepted_submission"] == 1
    assert report["filing_rate"] == {"recorded": 0.5, "replayed": round(2 / 3, 4)}
    assert report["by_arm"]["naming"]["replayed_filing_rate"] == 0.5


def test_a_condition_is_read_against_the_null_paired_by_session():
    from src.mathlib_review.review.replay import compare_replays

    null = [_row(f"s{i}", "naming", False, False) for i in range(10)]
    treated = [_row(f"s{i}", "naming", False, i < 9, condition="file_more") for i in range(10)]
    comparison = compare_replays(null, treated)
    assert comparison["paired_sessions"] == 10
    assert (comparison["sessions_treatment_files_more"],
            comparison["sessions_treatment_files_less"]) == (9, 0)
    assert comparison["filing_rate"]["mean_paired_difference"] == 0.9
    assert comparison["sign_test_p"] == 0.0039
