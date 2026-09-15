"""Session replay: any recorded task, run again from a point inside its conversation.

A replay is the same task -- same type, payload, tools and contract -- started from a sealed
prefix. These tests pin the parts that fail silently if wrong: where the cut is, that a
condition changes exactly what it says, that the prefix survives being written, that the
recorded spend is not charged again, and that a replay can never quietly start from its prompt.
Review-specific behaviour is in `tests/mathlib_review/test_decision_replay.py`.
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

from ape.llm_clients.models import (
    ContentBlock, ConversationNode, ConversationSession, TokenUsage,
)
from ape.scaffolds.ape_agent.config import ApeAgentConfig
from ape.scaffolds.ape_agent.conversation import ApeAgentConversationManager
from ape.scaffolds.ape_agent.replay import (
    REPLAY_RECORD_FILENAME, SESSION_REPLAY_KEY, ReplayCondition, ReplayRefused, SessionReplay,
    apply_condition, cut_before_tool_call, load_prefix, recorded_tools, replay_task_data,
    tool_calls, tool_definition_sha256,
)

SUBMIT = {"type": "function", "function": {
    "name": "submit_result", "description": "submit",
    "parameters": {"type": "object", "properties": {
        "answer": {"type": "string"}, "reasoning": {"type": "string"}},
        "required": ["answer"]}}}
READ = {"type": "function", "function": {
    "name": "file_read", "description": "read", "parameters": {"type": "object",
                                                               "properties": {}}}}


def _call(session, call_id, name, arguments, result, usage=None):
    session.add_assistant_message([ContentBlock.tool_use_block(call_id, name, arguments)],
                                  cwd="/w", usage=usage)
    session.add_tool_result(call_id, result, cwd="/w", tool_name=name)


def _nodes():
    """Investigate once, submit (refused), resubmit (accepted)."""

    session = ConversationSession()
    session.add_system_message([ContentBlock.text_block("CONTRACT. Be careful.")], cwd="/w")
    session.add_tool_definitions([READ, SUBMIT], cwd="/w")
    session.add_user_message([ContentBlock.text_block("Prove it.")], cwd="/w")
    _call(session, "c1", "file_read", {"path": "A.lean"}, {"content": "theorem a"},
          usage=TokenUsage(input_tokens=900, total_cost=0.03, cached_total_cost=0.01))
    _call(session, "c2", "submit_result", {"answer": ""},
          {"evaluation_result": {"success": False, "message": "empty answer"}})
    _call(session, "c3", "submit_result", {"reasoning": "because", "answer": "rfl"},
          {"evaluation_result": {"success": True, "message": "ok"}})
    return [node.model_dump(mode="json") for node in session.nodes]


# --- the cut and the condition --------------------------------------------------------------


def test_the_cut_is_before_the_first_call_to_the_named_tool():
    prefix, index = cut_before_tool_call(_nodes(), "submit_result")
    assert index == 5
    assert [row["type"] for row in prefix] == [
        "system", "tool_definitions", "user", "assistant", "user"]


def test_a_session_that_never_called_the_tool_is_refused():
    with pytest.raises(ReplayRefused, match="never called"):
        cut_before_tool_call(_nodes()[:5], "submit_result")


def test_an_unanswered_call_before_the_cut_is_refused():
    """The manager drops an unanswered trailing call on resume, so the replay would start
    earlier than the point it reports."""

    nodes = _nodes()
    del nodes[4]
    with pytest.raises(ReplayRefused, match="unanswered"):
        cut_before_tool_call(nodes, "submit_result")


def test_null_changes_nothing_and_nothing_else_may_be_called_null():
    prefix, _ = cut_before_tool_call(_nodes(), "submit_result")
    assert apply_condition(prefix, ReplayCondition(name="null")) == prefix
    for condition in (ReplayCondition(name="null", closing_instruction="Decide."),
                      ReplayCondition(name="other"),
                      ReplayCondition(name="null", task_data_overrides={"x": 1})):
        with pytest.raises(ReplayRefused):
            apply_condition(prefix, condition)


def test_a_prompt_replacement_must_match_exactly_once():
    prefix, _ = cut_before_tool_call(_nodes(), "submit_result")
    edited = apply_condition(prefix, ReplayCondition(name="bold", prompt_replacements=[
        {"node": "system", "old": "Be careful.", "new": "Be bold."}]))
    assert edited[0]["message"]["content"][0]["text"] == "CONTRACT. Be bold."
    with pytest.raises(ReplayRefused, match="0 times"):
        apply_condition(prefix, ReplayCondition(name="bold", prompt_replacements=[
            {"node": "user", "old": "absent", "new": "x"}]))


def test_a_field_order_edit_survives_the_prefix_file(tmp_path):
    """Sorted-key JSON would erase the one thing a field-order condition changes, and would
    make the null replay show the model something it was not shown."""

    prefix, _ = cut_before_tool_call(_nodes(), "submit_result")
    condition = ReplayCondition(name="reason_first", tool_schema_edits=[
        {"tool": "submit_result", "property_order": ["reasoning"], "required": ["reasoning"],
         "descriptions": {"answer": "last"}}])
    payload, content = replay_task_data({"task_type": "t", "task_id": "x", "global_index": "g"},
                                        prefix, condition, tmp_path / "p.jsonl", {"run": "r"})
    (tmp_path / "p.jsonl").write_bytes(content)
    replay = SessionReplay.model_validate(payload[SESSION_REPLAY_KEY])
    shown = {t["function"]["name"]: t for t in recorded_tools(load_prefix(replay))}
    parameters = shown["submit_result"]["function"]["parameters"]
    assert list(parameters["properties"]) == ["reasoning", "answer"]
    assert parameters["required"] == ["reasoning"]
    assert parameters["properties"]["answer"]["description"] == "last"
    # Recorded hashes are of what was recorded, so a swap is never reported as drift.
    assert replay.recorded_tool_sha256["submit_result"] == tool_definition_sha256(SUBMIT)
    assert payload["task_type"] == "t" and payload["task_id"] == "x"
    assert "global_index" not in payload


def test_a_schema_edit_naming_a_missing_field_is_refused():
    prefix, _ = cut_before_tool_call(_nodes(), "submit_result")
    with pytest.raises(ReplayRefused, match="does not have"):
        apply_condition(prefix, ReplayCondition(name="typo", tool_schema_edits=[
            {"tool": "submit_result", "property_order": ["answers"]}]))


def test_a_closing_instruction_is_a_user_message_the_session_model_accepts():
    prefix, _ = cut_before_tool_call(_nodes(), "submit_result")
    edited = apply_condition(prefix, ReplayCondition(name="closing",
                                                     closing_instruction="Now decide."))
    node = ConversationNode.model_validate(edited[-1])
    assert node.type == "user" and node.parentUuid == prefix[-1]["uuid"]


def test_task_data_overrides_change_the_contract_not_the_prompt(tmp_path):
    prefix, _ = cut_before_tool_call(_nodes(), "submit_result")
    payload, content = replay_task_data(
        {"task_type": "t", "task_id": "x", "strict": False}, prefix,
        ReplayCondition(name="strict", task_data_overrides={"strict": True}),
        tmp_path / "p.jsonl", {})
    assert payload["strict"] is True
    assert json.loads(content.split(b"\n")[0]) == prefix[0]


def test_tool_calls_read_result_content_and_acceptance():
    nodes = _nodes()
    calls = tool_calls(nodes, 5, "submit_result")
    assert [(c["accepted"], c["message"]) for c in calls] == [(False, "empty answer"),
                                                              (True, "ok")]
    assert list(calls[1]["arguments"]) == ["reasoning", "answer"]


# --- the conversation manager honours it ----------------------------------------------------


def _replaying_task(tmp_path, condition=None, recorded=None):
    prefix, _ = cut_before_tool_call(_nodes(), "submit_result")
    payload, content = replay_task_data({"task_type": "t", "task_id": "x"}, prefix,
                                        condition or ReplayCondition(name="null"),
                                        tmp_path / "prefix.jsonl", {})
    (tmp_path / "prefix.jsonl").write_bytes(content)
    replay = SessionReplay.model_validate(payload[SESSION_REPLAY_KEY])
    if recorded is not None:
        replay.recorded_tool_sha256.update(recorded)
    attempt = tmp_path / "attempt"
    attempt.mkdir(exist_ok=True)
    return SimpleNamespace(session_replay=replay, attempt_path=attempt,
                           scratch_workspace=None), prefix


def test_a_replay_starts_from_the_prefix_with_a_fresh_identity(tmp_path):
    task, prefix = _replaying_task(tmp_path)
    manager = ApeAgentConversationManager(ApeAgentConfig(), task=task)
    session = asyncio.run(manager.resume_or_create_session())
    assert [n.type for n in session.nodes] == [row["type"] for row in prefix]
    assert session.session_id != prefix[0]["sessionId"]
    assert ApeAgentConversationManager.find_latest_session_path(task.attempt_path) is not None


def test_the_recorded_spend_is_not_charged_again(tmp_path):
    task, _ = _replaying_task(tmp_path)
    manager = ApeAgentConversationManager(ApeAgentConfig(), task=task)
    asyncio.run(manager.resume_or_create_session())
    assert manager.get_total_usage().cached_total_cost == 0
    persisted = ApeAgentConversationManager.find_latest_session_path(task.attempt_path)
    assert all(json.loads(line)["message"].get("usage") is None
               for line in persisted.open() if json.loads(line)["type"] == "assistant")


def test_a_paused_replay_resumes_its_own_file(tmp_path):
    task, _ = _replaying_task(tmp_path)
    first = ApeAgentConversationManager(ApeAgentConfig(), task=task)
    started = asyncio.run(first.resume_or_create_session())
    started.add_assistant_message([ContentBlock.text_block("deciding")], cwd="/w")
    asyncio.run(first._save_session(started, incremental=True))
    task.session_replay.prefix_sha256 = "0" * 64  # reseeding would now refuse loudly
    resumed = asyncio.run(ApeAgentConversationManager(ApeAgentConfig(), task=task)
                          .resume_or_create_session())
    assert resumed.session_id == started.session_id
    assert resumed.get_assistant_count() == 2


def test_a_tampered_prefix_is_refused(tmp_path):
    task, _ = _replaying_task(tmp_path)
    path = tmp_path / "prefix.jsonl"
    path.write_bytes(path.read_bytes().replace(b"CONTRACT", b"CONTRACX"))
    with pytest.raises(ReplayRefused, match="sha256"):
        asyncio.run(ApeAgentConversationManager(ApeAgentConfig(), task=task)
                    .resume_or_create_session())


def test_a_replay_without_an_attempt_path_never_starts_from_its_prompt(tmp_path):
    task, _ = _replaying_task(tmp_path)
    task.attempt_path = None
    with pytest.raises(ReplayRefused, match="refusing to start"):
        asyncio.run(ApeAgentConversationManager(ApeAgentConfig(), task=task)
                    .resume_or_create_session())


def test_the_model_is_shown_the_recorded_tools_and_drift_is_written_down(tmp_path):
    condition = ReplayCondition(name="reason_first", tool_schema_edits=[
        {"tool": "submit_result", "property_order": ["reasoning"]}])
    task, _ = _replaying_task(tmp_path, condition)
    changed_read = json.loads(json.dumps(READ))
    changed_read["function"]["description"] = "read, differently"
    extra = {"type": "function", "function": {"name": "new_tool", "parameters": {}}}
    manager = ApeAgentConversationManager(ApeAgentConfig(), task=task)

    shown = manager._replay_tool_definitions([SUBMIT, changed_read, extra])
    assert [t["function"]["name"] for t in shown] == ["file_read", "submit_result"]
    assert list(shown[1]["function"]["parameters"]["properties"]) == ["reasoning", "answer"]
    record = json.loads((task.attempt_path / REPLAY_RECORD_FILENAME).read_text())
    assert record["tool_drift"] == ["file_read"]  # the condition's own swap is not drift
    assert record["registered_not_shown"] == ["new_tool"]
    with pytest.raises(ReplayRefused, match="not registered"):
        manager._replay_tool_definitions([SUBMIT])


def test_without_a_replay_the_registered_tools_are_shown():
    task = SimpleNamespace(session_replay=None, attempt_path=None)
    manager = ApeAgentConversationManager(ApeAgentConfig(), task=task)
    assert manager._replay_tool_definitions([READ]) == [READ]


# --- the runtime boundary --------------------------------------------------------------------


def _capture_runtime(monkeypatch):
    import ape.scaffolds.runner as runner

    seen = {}

    async def fake_run_task(self, task, **kwargs):
        seen["replay"] = task.session_replay
        return None, None

    monkeypatch.setattr(runner.TaskRunner, "run_task", fake_run_task)
    monkeypatch.setattr("ape.tasks.base.create_task_from_data",
                        lambda data, config, task_config_overrides=None:
                        SimpleNamespace(session_replay=None))
    return runner, seen


def test_the_runtime_attaches_a_replay_to_whatever_task_the_data_builds(monkeypatch, tmp_path):
    runner, seen = _capture_runtime(monkeypatch)
    replay = {"prefix_path": "p", "prefix_sha256": "0" * 64, "recorded_tool_sha256": {}}
    asyncio.run(runner.main_from_params({
        "task_data": {"task_type": "t", SESSION_REPLAY_KEY: replay},
        "config": ApeAgentConfig().model_dump(mode="json"), "scaffold_type": "ape_agent"}))
    assert isinstance(seen["replay"], SessionReplay)


def test_a_scaffold_without_a_session_format_refuses_a_replay(monkeypatch):
    runner, _ = _capture_runtime(monkeypatch)
    monkeypatch.setattr("ape.scaffolds.get_scaffold_class",
                        lambda name: type("S", (), {"config_class": ApeAgentConfig}))
    with pytest.raises(ValueError, match="only by the ape_agent scaffold"):
        asyncio.run(runner.main_from_params({
            "task_data": {"task_type": "t", SESSION_REPLAY_KEY: {
                "prefix_path": "p", "prefix_sha256": "0", "recorded_tool_sha256": {}}},
            "config": ApeAgentConfig().model_dump(mode="json"), "scaffold_type": "codex"}))
