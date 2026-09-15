"""Decision-turn replay: where a session is cut, what a condition may change, and what is read.

Built from real classes throughout -- the arm task, its registered `submit_candidates` schema as
the scaffold lists it, and sessions assembled with `ConversationSession` -- because a replay
that is wrong is wrong silently: it would still produce a submission, and the submission would
be read as the effect of a condition.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from ape.llm_clients.config import LLMConfig
from ape.llm_clients.models import ContentBlock, ConversationNode, ConversationSession
from ape.scaffolds.ape_agent.config import ApeAgentConfig
from ape.scaffolds.ape_agent.conversation import ApeAgentConversationManager
from ape.tasks.lean_tasks.formal_math.review.arm import (
    ReviewArmReplayData, ReviewArmReplayTask,
)
from src.mathlib_review.io import jsonl_rows, sha256_bytes
from src.mathlib_review.review.replay import (
    DecisionReplaySpec, ReplayCondition, ReplayRefused, accepted_summary, apply_condition,
    decision_prefix, decision_record, prefix_bytes, recorded_tools, tool_definition_sha256,
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


def _registered_tools(task):
    """The definitions the scaffold would send: registered on fastmcp, listed by the manager."""

    from fastmcp import Client, FastMCP

    async def listed():
        mcp = FastMCP("probe")
        await task.register_task_tools(mcp)
        async with Client(mcp) as client:
            manager = ApeAgentConversationManager(ApeAgentConfig(), task=None)
            return await manager._get_available_tools(client)

    return asyncio.run(listed())


@pytest.fixture(scope="module")
def tools():
    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmData, ReviewArmTask

    task = ReviewArmTask(ReviewArmData(**ARM_FIELDS),
                         ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    return _registered_tools(task)


def _call(session, call_id, name, arguments, result):
    session.add_assistant_message([ContentBlock.tool_use_block(call_id, name, arguments)],
                                  cwd="/w")
    session.add_tool_result(call_id, result, cwd="/w", tool_name=name)


def _session(tools):
    """Investigate, submit a mute abstention (refused), then resubmit it labelled."""

    session = ConversationSession()
    session.add_system_message([ContentBlock.text_block(ARM_FIELDS["rendered_system_prompt"])],
                               cwd="/w")
    session.add_tool_definitions(tools, cwd="/w")
    session.add_user_message([ContentBlock.text_block("Review Foo.bar.")], cwd="/w")
    _call(session, "c1", "file_read", {"path": "A.lean"}, {"content": "theorem Foo.bar"})
    _call(session, "c2", "submit_candidates", {"candidates": []},
          {"evaluation_result": {"success": False, "message": "Only the label is missing."}})
    _call(session, "c3", "submit_candidates",
          {"abstention_reason": "already_correct", "candidates": [],
           "abstention_detail": "Foo.bar matches the prefix."},
          {"evaluation_result": {"success": True, "message": "Recorded 0 candidates"}})
    return [node.model_dump(mode="json") for node in session.nodes]


# --- where a session is cut ----------------------------------------------------------------


def test_the_cut_is_before_the_first_submission_not_the_last(tools):
    """A replayed task counts refusals from zero, so a prefix holding a refused submission
    would disagree with the live contract about how many times it has already refused."""

    nodes = _session(tools)
    prefix, index = decision_prefix(nodes)
    assert index == 5
    assert [row["type"] for row in prefix] == [
        "system", "tool_definitions", "user", "assistant", "user"]
    assert "submit_candidates" not in json.dumps([r["message"] for r in prefix[3:]])


def test_a_session_that_never_submitted_is_refused(tools):
    nodes = _session(tools)[:5]
    with pytest.raises(ReplayRefused, match="never called"):
        decision_prefix(nodes)


def test_an_unanswered_tool_call_before_the_decision_is_refused(tools):
    """The manager drops an unanswered trailing call on resume, which would start the replay
    earlier than the point it reports."""

    nodes = _session(tools)
    del nodes[4]
    with pytest.raises(ReplayRefused, match="unanswered"):
        decision_prefix(nodes)


# --- what a condition may change -----------------------------------------------------------


def test_the_null_condition_changes_nothing(tools):
    prefix, _ = decision_prefix(_session(tools))
    assert apply_condition(prefix, ReplayCondition(name="null")) == prefix


@pytest.mark.parametrize("condition", [
    ReplayCondition(name="null", closing_instruction="Decide."),
    ReplayCondition(name="reason_first"),
])
def test_a_condition_must_be_named_for_what_it_does(tools, condition):
    prefix, _ = decision_prefix(_session(tools))
    with pytest.raises(ReplayRefused):
        apply_condition(prefix, condition)


def test_a_prompt_replacement_must_match_exactly_once(tools):
    prefix, _ = decision_prefix(_session(tools))
    edited = apply_condition(prefix, ReplayCondition(name="bar", prompt_replacements=[
        {"node": "system", "old": "Abstain when unsure.", "new": "File when plausible."}]))
    assert edited[0]["message"]["content"][0]["text"] == "NAMING CONTRACT. File when plausible."
    with pytest.raises(ReplayRefused, match="0 times"):
        apply_condition(prefix, ReplayCondition(name="bar", prompt_replacements=[
            {"node": "user", "old": "not in the prompt", "new": "x"}]))


def test_reason_before_verdict_reorders_the_schema_and_survives_the_prefix_file(tools, tmp_path):
    """The one thing a field-order condition changes is key order, and `jsonl_bytes` sorts keys
    -- so the prefix is written in the session file's encoding and read back with
    `jsonl_rows`, and the order the model is shown is asserted after that round trip."""

    prefix, _ = decision_prefix(_session(tools))
    condition = ReplayCondition(name="detail_first", tool_schema_edits=[
        {"at": "", "property_order": ["abstention_detail", "abstention_reason"]},
        {"at": "properties/candidates/items", "property_order": ["claim", "requested_change"],
         "descriptions": {"model_confidence": "Your probability that a maintainer asks for this."}},
    ])
    path = tmp_path / "prefix.jsonl"
    path.write_bytes(prefix_bytes(apply_condition(prefix, condition)))
    shown = {t["function"]["name"]: t["function"]["parameters"]
             for t in recorded_tools(jsonl_rows(path))}["submit_candidates"]

    assert list(shown["properties"])[:3] == [
        "abstention_detail", "abstention_reason", "candidates"]
    candidate = shown["properties"]["candidates"]["items"]
    assert list(candidate["properties"])[:2] == ["claim", "requested_change"]
    assert set(candidate["properties"]) == set(
        {t["function"]["name"]: t for t in recorded_tools(prefix)}["submit_candidates"]
        ["function"]["parameters"]["properties"]["candidates"]["items"]["properties"])
    assert candidate["properties"]["model_confidence"]["description"].startswith("Your prob")
    # The recording itself is untouched.
    original = {t["function"]["name"]: t for t in recorded_tools(prefix)}["submit_candidates"]
    assert list(original["function"]["parameters"]["properties"])[0] == "candidates"


def test_a_schema_edit_naming_a_field_that_does_not_exist_is_refused(tools):
    prefix, _ = decision_prefix(_session(tools))
    with pytest.raises(ReplayRefused, match="does not have"):
        apply_condition(prefix, ReplayCondition(name="typo", tool_schema_edits=[
            {"property_order": ["abstention_reasons"]}]))


def test_a_closing_instruction_is_a_user_message_the_session_model_accepts(tools):
    prefix, _ = decision_prefix(_session(tools))
    edited = apply_condition(prefix, ReplayCondition(
        name="closing", closing_instruction="Before submitting, name the best candidate."))
    node = ConversationNode.model_validate(edited[-1])
    assert node.type == "user" and node.parentUuid == prefix[-1]["uuid"]
    assert node.message.content[0].text.startswith("Before submitting")


# --- what was decided ----------------------------------------------------------------------


def test_the_decision_record_keeps_refusals_and_emission_order(tools):
    nodes = _session(tools)
    _, index = decision_prefix(nodes)
    record = decision_record(nodes, index)
    assert (record["turns"], record["submissions"]) == (2, 2)
    assert record["refusals"] == ["Only the label is missing."]
    assert record["first"]["filed"] is False and record["first"]["abstention_reason"] is None
    assert accepted_summary({"success": True, "candidates": [],
                             "abstention": {"reason": "already_correct"}}) == {
        "filed": False, "abstention_reason": "already_correct", "anchors": [],
        "candidate_keys": [], "model_confidence": []}
    assert accepted_summary({"success": False}) is None


# --- the task ------------------------------------------------------------------------------


def _replay_task(tools, tmp_path, condition=None, recorded=None):
    prefix, index = decision_prefix(_session(tools))
    rows = apply_condition(prefix, condition or ReplayCondition(name="null"))
    path = tmp_path / "prefix.jsonl"
    path.write_bytes(prefix_bytes(rows))
    spec = DecisionReplaySpec(
        source_run="r", source_invocation_id="wu:a#naming", source_session="s.jsonl",
        source_session_sha256="0" * 64, prefix_path=str(path),
        prefix_sha256=sha256_bytes(path.read_bytes()), decision_node_index=index,
        prefix_assistant_turns=1, condition="null", condition_sha256="0" * 64,
        recorded_tool_sha256=recorded if recorded is not None else {
            t["function"]["name"]: tool_definition_sha256(t) for t in recorded_tools(prefix)})
    task = ReviewArmReplayTask(ReviewArmReplayData(**ARM_FIELDS, replay=spec),
                               ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    return task, rows, path


def test_the_task_starts_from_the_sealed_prefix_and_refuses_a_different_one(tools, tmp_path):
    task, rows, path = _replay_task(tools, tmp_path)
    assert asyncio.run(task.session_prefix()) == rows
    task, _, path = _replay_task(tools, tmp_path)
    path.write_bytes(path.read_bytes().replace(b"NAMING CONTRACT", b"OTHER CONTRACT"))
    with pytest.raises(RuntimeError, match="sha256"):
        asyncio.run(task.session_prefix())


def test_the_task_shows_recorded_tools_and_names_drift(tools, tmp_path):
    condition = ReplayCondition(name="detail_first", tool_schema_edits=[
        {"property_order": ["abstention_detail"]}])
    recorded = {t["function"]["name"]: tool_definition_sha256(t) for t in tools}
    recorded["lean_verify_edit"] = "0" * 64         # registered today, recorded differently
    task, rows, _ = _replay_task(tools, tmp_path, condition, recorded)
    registered = _registered_tools(task)
    shown = task.adapt_tool_definitions(registered)
    assert shown == recorded_tools(rows)
    assert task._tool_drift == ["lean_verify_edit"]  # the swap itself is not drift
    with pytest.raises(RuntimeError, match="not registered"):
        task.adapt_tool_definitions([t for t in registered
                                     if t["function"]["name"] != "submit_candidates"])


def test_the_result_carries_the_replay_it_came_from(tools, tmp_path):
    task, _, _ = _replay_task(tools, tmp_path)
    result = task.create_result(success=True, score=1.0, pr_number=1, work_unit_id="wu:a",
                                rendered_prompt_sha256="a" * 64, findings=[],
                                review_message="")
    assert result.replay["source_invocation_id"] == "wu:a#naming"
    assert result.invocation_id == "wu:a#naming"
