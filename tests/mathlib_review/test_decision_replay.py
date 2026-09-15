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
    SESSION_REPLAY_KEY, ReplayCondition, SessionReplay, cut_before_tool_call, load_prefix,
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
