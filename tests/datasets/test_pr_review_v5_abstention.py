"""Silence has to say which silence it is.

`submit_candidates([])` carried no reason, so every kind of abstention arrived identically:
81% of specialist invocations on `pr5_A_lead_heldout12_rep1` were empty, and the only way to
tell them apart was to reconstruct each session's last tool result from the transcripts. That
inference put 20 of 82 at "read something and judged it not worth reporting", 14 at "verified
its own edit and reported nothing anyway" and 5 at an evidence gap — distinctions the arm knew
at the time and had nowhere to put. `.claude/rules/mathlib-review.md` states the cost plainly:
"there was never a rationale to aim a prompt at".

`schema/evidence.py:88` already rules for the evidence layer that "we did not check" and "we
checked and found nothing" must not look alike. These tests hold the arm layer to it.

The second half of the file guards the *path*, not the tool. Between the tool and
`arm_responses.jsonl` sit four closed literal dicts, no pydantic schema, and — until this
file — no test asserting a row's key set. A field added correctly at the source and dropped at
`lead.py` would have left the whole suite green, which is exactly how `documentation`/`docs`,
the retrieval gate's Literal and `CONTEXT_TOOLS`/`naming_norm` each cost a paid run.
"""

from __future__ import annotations

import asyncio

import pytest

from ape.tasks.lean_tasks.formal_math.review.candidates import ABSTENTION_REASONS


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **_kwargs):
        def decorate(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorate


@pytest.fixture
def submit():
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from tests.datasets.test_pr_review_v5_arm import _data
    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmTask

    task = ReviewArmTask(_data(), ApeAgentConfig())
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    return mcp.tools["submit_candidates"], task


def test_a_mute_abstention_is_refused(submit):
    tool, _task = submit
    out = asyncio.run(tool(candidates=[]))
    assert out["evaluation_result"].success is False


def test_the_refusal_does_not_ask_for_a_finding(submit):
    """The one way this change could do real damage. An arm that reads the refusal as
    pressure to produce something would cost the control-PR result — 0 candidates per control
    PR per rep — which is the most reproducible number this project has."""

    tool, _task = submit
    message = asyncio.run(tool(candidates=[]))["evaluation_result"].message
    assert "valid and expected outcome" in message
    assert "NOT a request to find something" in message
    assert "do not add a candidate" in message.lower()


def test_the_refusal_names_every_reason_it_will_accept(submit):
    """A closed vocabulary the model has to guess at is a closed vocabulary that silently
    filters. It is spelled out in the refusal and enumerated in the tool schema."""

    tool, _task = submit
    message = asyncio.run(tool(candidates=[]))["evaluation_result"].message
    for reason in ABSTENTION_REASONS:
        assert reason in message


def test_an_abstention_with_a_reason_is_accepted_and_recorded(submit):
    tool, task = submit
    recorded = {}
    task.termination_callback = None
    original = task.create_result

    def capture(**kwargs):
        recorded.update(kwargs)
        return original(**kwargs)

    task.create_result = capture
    out = asyncio.run(tool(candidates=[], abstention_reason="already_correct",
                           abstention_detail="All three names match the counted population."))
    assert out["evaluation_result"].success is True
    assert recorded["abstention"] == {
        "reason": "already_correct",
        "detail": "All three names match the counted population."}


def test_a_submission_with_candidates_records_no_abstention(submit):
    """An arm that found something did not abstain, whatever it passed."""

    from tests.datasets.test_pr_review_v5_arm import _candidate

    tool, task = submit
    recorded = {}
    original = task.create_result

    def capture(**kwargs):
        recorded.update(kwargs)
        return original(**kwargs)

    task.create_result = capture
    asyncio.run(tool(candidates=[_candidate()], abstention_reason="already_correct"))
    assert recorded["abstention"] is None


def test_the_reason_survives_into_the_result_model():
    """`BaseTaskResult` is pydantic with the default `extra='ignore'`, so an undeclared
    keyword reaches `create_result` and is dropped with no error whatsoever."""

    from ape.tasks.lean_tasks.formal_math.review.candidates import (
        LeanPRReviewV4CandidateResult,
    )

    assert "abstention" in LeanPRReviewV4CandidateResult.model_fields


# --- the path from the tool to the artifact ------------------------------------------------

#: Every key an `arm_responses.jsonl` row carries. There is no pydantic model for a row, so
#: this literal is the schema, and the three builders below must agree with it exactly.
#: Pinned because the failure mode is silent in both directions: a key dropped by one builder
#: makes an arm's output unreadable, and a key added by one and not the others makes rows from
#: different routing modes incomparable.
ARM_RESPONSE_KEYS = {
    "invocation_id", "arm_id", "work_unit_id", "spec_id", "pr_number", "status",
    "candidates", "verification_artifacts", "abstention", "rendered_prompt_sha256",
}


def test_the_lead_builds_a_row_with_exactly_these_keys():
    import inspect

    from ape.tasks.lean_tasks.formal_math.review import lead

    source = inspect.getsource(lead)
    block = source.split('responses.append({', 1)[1].split('})', 1)[0]
    assert {line.split('"')[1] for line in block.strip().splitlines()
            if line.strip().startswith('"')} == ARM_RESPONSE_KEYS


def test_the_non_lead_builder_agrees_with_the_lead():
    """Two literal dicts in two files, and nothing compared them. `fanout` and `rules` runs
    go through this one; `lead` runs never touch it."""

    import inspect

    from src.mathlib_review.review import runner

    block = inspect.getsource(runner._responses_from_results)
    block = block.split('responses.append({', 1)[1].split('})', 1)[0]
    assert {line.split('"')[1] for line in block.strip().splitlines()
            if line.strip().startswith('"')} == ARM_RESPONSE_KEYS


def test_the_solo_builder_agrees_too():
    import inspect

    from src.mathlib_review.review import runner

    block = inspect.getsource(runner._solo_responses)
    block = block.split('responses.append({', 1)[1].split('})', 1)[0]
    assert {line.split('"')[1] for line in block.strip().splitlines()
            if line.strip().startswith('"')} == ARM_RESPONSE_KEYS


def test_the_job_outcome_carries_the_reason():
    """The hop between the child's `task_result.json` and the lead's response row. A
    dataclass with fixed fields, so an undeclared one is dropped here instead."""

    from dataclasses import fields

    from ape.tasks.lean_tasks.formal_math.review.delegation import JobOutcome

    assert "abstention" in {f.name for f in fields(JobOutcome)}


# --- and something reads it ----------------------------------------------------------------

def test_the_report_breaks_abstentions_down_by_arm(tmp_path, monkeypatch):
    """A recorded field nothing reads is not instrumentation. This is the analysis that took
    three wrong attempts to reconstruct from transcripts, now a dict lookup."""

    from src.mathlib_review.analysis import report
    from src.mathlib_review.io import jsonl_bytes

    run = tmp_path / "run"
    run.mkdir()
    (run / "arm_responses.jsonl").write_bytes(jsonl_bytes([
        {"arm_id": "naming", "candidates": [],
         "abstention": {"reason": "already_correct", "detail": "d"}},
        {"arm_id": "naming", "candidates": [],
         "abstention": {"reason": "could_not_establish", "detail": "d"}},
        {"arm_id": "naming", "candidates": [{"claim": "x"}],
         "abstention": None},
        {"arm_id": "docs", "candidates": []},
    ]))
    monkeypatch.setattr(report, "run_dir", lambda _name: run)
    out = report._abstentions("whatever")

    assert out["naming"] == {"already_correct": 1, "could_not_establish": 1}, (
        "a submission with candidates is not an abstention")
    assert out["docs"] == {"unstated": 1}, (
        "a row from before the reason was required is reported, not hidden in a denominator")


def test_a_second_mute_submission_is_accepted_as_unstated(submit):
    """The contract asks once and never twice.

    `termination_callback` fires on the success path alone, so an arm that kept omitting the
    reason would never submit legally -- it would burn its turns, be recorded as a failed job,
    and if the job were mandatory become a coverage gap. That converts the cleanest outcome an
    arm has, looking properly and finding nothing, into a hole in the run. An unlabelled
    silence is much the lesser error, and the report already counts it.
    """

    tool, task = submit
    recorded = {}
    original = task.create_result

    def capture(**kwargs):
        recorded.update(kwargs)
        return original(**kwargs)

    task.create_result = capture

    first = asyncio.run(tool(candidates=[]))
    assert first["evaluation_result"].success is False

    second = asyncio.run(tool(candidates=[]))
    assert second["evaluation_result"].success is True, (
        "a second mute submission must not be refused again -- that is an infinite loop that "
        "ends in a failed job")
    assert recorded["abstention"]["reason"] == "unstated"
