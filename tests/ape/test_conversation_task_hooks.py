"""A task may supply the conversation it starts from, and the tool definitions it is shown.

Both are optional hooks on the conversation manager, in the pattern `create_system_prompt`
already follows. They exist for decision-turn replay: resume a recorded arm session just
before its submission, with one thing changed, instead of paying for the investigation again.
Asserted on the persisted session file and the manager's own state, because those are what a
replay's cost and turn count are read from.
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

from ape.llm_clients.models import ContentBlock, ConversationSession, TokenUsage
from ape.scaffolds.ape_agent.config import ApeAgentConfig
from ape.scaffolds.ape_agent.conversation import ApeAgentConversationManager


def _recorded_prefix():
    """A real session up to a decision: prompt, one investigated tool call, its result."""

    session = ConversationSession()
    session.add_system_message([ContentBlock.text_block("SYSTEM CONTRACT")], cwd="/w")
    session.add_tool_definitions([{"type": "function", "function": {
        "name": "file_read", "description": "read", "parameters": {"type": "object"}}}],
        cwd="/w")
    session.add_user_message([ContentBlock.text_block("review this")], cwd="/w")
    session.add_assistant_message(
        [ContentBlock.tool_use_block("call_1", "file_read", {"path": "A.lean"})], cwd="/w",
        usage=TokenUsage(input_tokens=900, output_tokens=40, total_cost=0.03,
                         cached_total_cost=0.01))
    session.add_tool_result("call_1", {"content": "theorem foo"}, cwd="/w",
                            tool_name="file_read")
    return session


class _Task(SimpleNamespace):
    calls = 0

    async def session_prefix(self):
        type(self).calls += 1
        return [node.model_dump(mode="json") for node in self.prefix.nodes]


def _manager(tmp_path, task):
    task.attempt_path = tmp_path
    task.scratch_workspace = None
    return ApeAgentConversationManager(ApeAgentConfig(), task=task)


def test_a_task_prefix_starts_the_session(tmp_path):
    prefix = _recorded_prefix()
    task = _Task(prefix=prefix)
    manager = _manager(tmp_path, task)
    session = asyncio.run(manager.resume_or_create_session())

    assert [n.type for n in session.nodes] == [n.type for n in prefix.nodes]
    assert session.get_assistant_count() == 1
    # A fresh identity: N resamples of one prefix are N conversations.
    assert session.session_id != prefix.session_id
    assert {n.sessionId for n in session.nodes} == {session.session_id}
    # Persisted where a resume looks for it.
    found = ApeAgentConversationManager.find_latest_session_path(tmp_path)
    assert found is not None and session.session_id in found.name


def test_the_recorded_spend_is_not_charged_to_the_new_attempt(tmp_path):
    """The prefix's $0.01 was billed to the run that produced it. Restoring it would count it
    against this attempt's cap and report it as this attempt's cost."""

    manager = _manager(tmp_path, _Task(prefix=_recorded_prefix()))
    asyncio.run(manager.resume_or_create_session())
    assert manager.get_total_usage().cached_total_cost == 0
    persisted = [json.loads(line) for line in
                 ApeAgentConversationManager.find_latest_session_path(tmp_path).open()]
    assert all(row["message"].get("usage") is None
               for row in persisted if row["type"] == "assistant")


def test_a_paused_attempt_resumes_its_own_file_and_is_not_reseeded(tmp_path):
    _Task.calls = 0
    first = _manager(tmp_path, _Task(prefix=_recorded_prefix()))
    started = asyncio.run(first.resume_or_create_session())
    started.add_assistant_message([ContentBlock.text_block("deciding")], cwd="/w")
    asyncio.run(first._save_session(started, incremental=True))

    second = _manager(tmp_path, _Task(prefix=_recorded_prefix()))
    resumed = asyncio.run(second.resume_or_create_session())
    assert _Task.calls == 1
    assert resumed.session_id == started.session_id
    assert resumed.get_assistant_count() == 2


def test_a_task_without_a_prefix_starts_fresh(tmp_path):
    manager = _manager(tmp_path, SimpleNamespace())
    session = asyncio.run(manager.resume_or_create_session())
    assert session.nodes == []


def test_a_task_decides_the_tool_definitions_sent():
    registered = [{"type": "function", "function": {"name": "a", "parameters": {}}}]
    shown = [{"type": "function", "function": {"name": "a", "description": "recorded",
                                               "parameters": {}}}]
    task = SimpleNamespace(adapt_tool_definitions=lambda tools: shown if tools else [])
    manager = ApeAgentConversationManager(ApeAgentConfig(), task=task)
    assert manager._task_tool_definitions(registered) == shown
    plain = ApeAgentConversationManager(ApeAgentConfig(), task=SimpleNamespace())
    assert plain._task_tool_definitions(registered) == registered
