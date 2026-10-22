"""The registered matcher: its prompt is the instrument's, its submission is refused until it
covers the batch, and its samples are kept as separate blind matchers."""

from __future__ import annotations

import asyncio

import pytest

from ape.scaffolds.ape_agent.config import ApeAgentConfig
from ape.tasks.base import create_task_from_data, get_task_class
from ape.tasks.lean_tasks.formal_math.review.ask_matching import (
    ASK_MATCHING_TASK_TYPE, AskMatchingResult, AskMatchingTask,
)
from src.mathlib_review.judge import ask_matching as M
from src.mathlib_review.schema import BlindAsk, BlindFinding, BlindPacket


def _packet(pr=7):
    return BlindPacket(
        pr=pr, asks=[BlindAsk(ask_id="a1", comment="rename it")],
        reviewers={label: [BlindFinding(i=0, target="Mathlib/X.lean:3", claim="c",
                                        requested_change="rename", severity="advisory")]
                   for label in ("R1", "R2")})


def _payload(**extra):
    return {"task_type": ASK_MATCHING_TASK_TYPE, "task_id": "match_p_b1", "plan_id": "p",
            "batch_id": "b1", "packets": [_packet().model_dump(mode="json")], **extra}


class _MCP:
    """Records the tools a task registers, so the real submit tool can be called."""

    def __init__(self):
        self.tools = {}

    def tool(self, description=""):
        def register(fn):
            self.tools[fn.__name__] = fn
            return fn
        return register


def _task():
    task = create_task_from_data(_payload(), ApeAgentConfig())
    submitted = []

    async def callback(result):
        submitted.append(result)

    task.termination_callback = callback
    mcp = _MCP()
    asyncio.run(task.register_task_tools(mcp))
    return task, mcp.tools["submit_matches"], submitted


def test_the_task_is_registered_and_names_its_submit_tool():
    assert get_task_class(ASK_MATCHING_TASK_TYPE) is AskMatchingTask
    assert AskMatchingTask.submit_tool == "submit_matches"


def test_the_prompt_is_the_instruments():
    task, _submit, _ = _task()
    prompt = asyncio.run(task.create_user_prompt())
    assert prompt == M.render_matcher_prompt([_packet()], "request_only")


def test_a_1_session_task_is_refused():
    task = create_task_from_data(_payload(instrument_version=M.V1_SESSION), ApeAgentConfig())
    with pytest.raises(ValueError, match="imported"):
        asyncio.run(task.create_user_prompt())


def test_an_incomplete_submission_is_refused_and_a_complete_one_ends_the_session():
    _task_, submit, submitted = _task()
    incomplete = asyncio.run(submit(
        asks=[{"pr": 7, "ask_id": "a1", "verdicts": [{"reviewer": "R1", "value": "reached",
                                                       "finding": 0}]}],
        unmatched={"7": {"R1": 0, "R2": 1}}))
    assert incomplete["accepted"] is False and submitted == []
    assert any("R2" in p for p in incomplete["problems"])
    done = asyncio.run(submit(
        asks=[{"pr": 7, "ask_id": "a1", "verdicts": [
            {"reviewer": "R1", "value": "reached", "finding": 0},
            {"reviewer": "R2", "value": "no", "finding": None}], "note": "R1 names it"}],
        unmatched={"7": {"R1": 0, "R2": 1}}))
    assert done["accepted"] is True
    (result,) = submitted
    assert result.asks == [{"pr": 7, "ask_id": "a1", "R1": "reached", "R1_finding": 0,
                            "R2": "no", "R2_finding": None, "note": "R1 names it"}]
    assert result.prompt_sha256 and result.batch_id == "b1"


def test_replicates_are_not_merged():
    one = AskMatchingResult(task_id="t", task_type=ASK_MATCHING_TASK_TYPE, global_index="g",
                            success=True, score=1.0, asks=[{"pr": 7, "ask_id": "a1", "R1": "no"}])
    two = one.model_copy(update={"asks": [{"pr": 7, "ask_id": "a1", "R1": "reached"}]})
    kept = AskMatchingTask.aggregate_results([one, two])
    assert kept.asks == one.asks
    assert kept.custom_metrics["replicates_succeeded"] == 2.0
    assert AskMatchingTask.aggregate_results([]) is None


def test_the_same_inputs_in_another_plan_are_another_task():
    a = create_task_from_data(_payload(), ApeAgentConfig())
    b = create_task_from_data(_payload(plan_id="q"), ApeAgentConfig())
    assert a.data.global_index != b.data.global_index
