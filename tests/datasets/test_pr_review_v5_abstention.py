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

#: Every key an `arm_responses.jsonl` row carries, stated once here and once as the fields of
#: `ArmResponse`. Kept as a literal beside the model on purpose: the model is what the writers
#: use, and this is what the reader expects, so a field added to one and not meant by the other
#: fails here rather than in a condition that reports zero.
#:
#: It was three dict literals in two files, compared only by parsing their own source for
#: quoted keys. That comparison was worth having -- `abstention` was added to two of the three
#: and the solo builder went on writing nine keys -- and a shared constructor is the version of
#: it that cannot drift.
ARM_RESPONSE_KEYS = {
    "invocation_id", "arm_id", "work_unit_id", "spec_id", "pr_number", "status",
    "candidates", "verification_artifacts", "abstention", "rendered_prompt_sha256",
}


def test_the_arm_response_model_is_the_row():
    from src.mathlib_review.schema.review import ArmResponse

    assert set(ArmResponse.model_fields) == ARM_RESPONSE_KEYS


def test_no_builder_writes_the_row_by_hand_any_more():
    """The three literals are gone. A fourth would drift from the other three the way the
    third did, and nothing outside a source-reading test would say so."""

    import inspect

    from ape.tasks.lean_tasks.formal_math.review import lead
    from src.mathlib_review.review import runner

    for module in (lead, runner):
        source = inspect.getsource(module)
        assert "responses.append({" not in source, (
            f"{module.__name__} builds an arm response as a dict literal again; construct "
            f"`ArmResponse` so every routing mode emits one key set")


def test_every_builder_emits_exactly_those_keys():
    """All three routing modes, through the one constructor. The solo baseline is the one that
    differs -- no rendered work-unit prompt, so `rendered_prompt_sha256` is null and present
    rather than absent."""

    from src.mathlib_review.schema.review import ArmResponse

    lead_row = ArmResponse(invocation_id="wu:a#naming", arm_id="naming", work_unit_id="wu:a",
                           spec_id="naming.v1", pr_number=1, status="success").row()
    solo_row = ArmResponse(invocation_id="ep:1#solo_agent", arm_id="solo_agent",
                           work_unit_id="wu:a", spec_id="solo_agent", pr_number=1,
                           status="success", rendered_prompt_sha256=None).row()
    assert set(lead_row) == set(solo_row) == ARM_RESPONSE_KEYS
    assert solo_row["rendered_prompt_sha256"] is None and solo_row["abstention"] is None


def test_a_response_with_no_identity_is_refused():
    """`lead_smoke4_rep2` holds one such row: a failed job synthesised with every identity
    field null, which reconciliation then read as an orphan response. The runner stopped
    writing them; the model is what stops them coming back."""

    import pytest
    from pydantic import ValidationError

    from src.mathlib_review.schema.review import ArmResponse

    with pytest.raises(ValidationError):
        ArmResponse.model_validate({
            "invocation_id": None, "arm_id": None, "work_unit_id": None, "spec_id": None,
            "pr_number": None, "status": "failed", "candidates": [],
            "verification_artifacts": [], "abstention": None, "rendered_prompt_sha256": None})


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


# --- the forced-submission diagnostic ------------------------------------------------------
#
# Measured under `fanout` on 4 held-out PRs: specialists submitted on 16% of invocations (lead:
# 19%) and 104 of 136 abstentions were `already_correct`, with `correctness` and `family_design`
# filing nothing in 11 jobs each. That rate has three readings the abstention data cannot
# separate -- a bar set too high, arms that cannot see what maintainers want, or arms with
# nothing to say -- and under duress they predict different things.


@pytest.fixture
def forced():
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from tests.datasets.test_pr_review_v5_arm import _data
    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmTask

    task = ReviewArmTask(_data(forbid_abstention=True), ApeAgentConfig())
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    return mcp.tools["submit_candidates"], task


def test_an_abstention_is_refused_even_with_a_reason(forced):
    """The ordinary contract accepts a reasoned abstention; this one does not. That is the
    whole manipulation."""

    tool, _task = forced
    out = asyncio.run(tool(candidates=[], abstention_reason="already_correct",
                           abstention_detail="Looked; the code is fine."))
    assert out["evaluation_result"].success is False
    assert "not accepting abstentions" in out["evaluation_result"].message


def test_the_press_does_not_dictate_what_to_find(forced):
    """It asks for the best candidate already considered and for confidence to carry the
    weakness. An instruction to find a *particular kind* of problem would plant the finding
    rather than measure whether the arm had one."""

    tool, _task = forced
    msg = asyncio.run(tool(candidates=[]))["evaluation_result"].message
    assert "best candidate you considered" in msg
    assert "below your usual bar" in msg
    assert "model_confidence" in msg


def test_it_gives_up_before_starving_the_job(forced):
    """`termination_callback` fires on success alone, so an unbounded press would burn the
    arm's turns, record the job as failed, and -- if mandatory -- make a coverage gap. That
    would turn "this arm had nothing" into a hole in the run."""

    from ape.tasks.lean_tasks.formal_math.review.candidates import (
        FORCED_EMPTY_REASON, _FORCED_SUBMISSION_ATTEMPTS,
    )

    tool, task = forced
    recorded = {}
    original = task.create_result

    def capture(**kwargs):
        recorded.update(kwargs)
        return original(**kwargs)

    task.create_result = capture
    for _ in range(_FORCED_SUBMISSION_ATTEMPTS):
        assert asyncio.run(tool(candidates=[]))["evaluation_result"].success is False
    final = asyncio.run(tool(candidates=[]))
    assert final["evaluation_result"].success is True
    assert recorded["abstention"]["reason"] == FORCED_EMPTY_REASON, (
        "pressed-and-still-nothing must stay distinguishable from an ordinary abstention")


def test_the_forced_reason_is_never_offered_to_the_model():
    """It is an outcome the system assigns, not a choice. If it were in the tool schema an arm
    could select it to escape the press, and the experiment would measure nothing."""

    from ape.tasks.lean_tasks.formal_math.review.candidates import (
        ABSTENTION_REASONS, FORCED_EMPTY_REASON,
    )

    assert FORCED_EMPTY_REASON not in ABSTENTION_REASONS


def test_a_submission_with_candidates_is_unaffected(forced):
    from tests.datasets.test_pr_review_v5_arm import _candidate

    tool, _task = forced
    out = asyncio.run(tool(candidates=[_candidate()]))
    assert out["evaluation_result"].success is True


def test_the_default_run_is_untouched(submit):
    """The knob defaults off and an ordinary run must behave exactly as before, or every run
    this diagnostic is compared against becomes incomparable."""

    tool, _task = submit
    out = asyncio.run(tool(candidates=[], abstention_reason="already_correct",
                           abstention_detail="Looked; the code is fine."))
    assert out["evaluation_result"].success is True


def test_the_dataset_knob_exists_and_defaults_off():
    from src.mathlib_review.review.runner import V5DatasetConfig

    assert V5DatasetConfig.model_fields["forbid_abstention"].default is False


def test_the_flag_survives_the_payload_hop_into_task_data():
    """The hop that has silently dropped a value three times in this repo: a thing set in the
    authoritative-looking place and lost by a layer nothing checks it against. Here the risk is
    real in both directions -- task data is `extra='forbid'`, so an undeclared key would raise,
    and a declared-but-unstamped one would read as "the experiment changed nothing"."""

    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmData
    from tests.datasets.test_pr_review_v5_arm import _data

    payload = _data().model_dump(mode="json")
    payload["forbid_abstention"] = True          # exactly what the runner stamps on the pool
    assert ReviewArmData(**payload).forbid_abstention is True


def test_the_fanout_path_carries_the_flag():
    """`fanout` is the mode this experiment runs in, and it builds task data through its own
    branch (`_direct_arm_task_data`) rather than the lead's."""

    import inspect

    from src.mathlib_review.review import runner

    src = inspect.getsource(runner._direct_arm_task_data)
    assert "dict(pool[proposal.invocation_id])" in src, (
        "the fanout branch must copy the whole pool payload; a hand-built dict here would drop "
        "any field the runner stamps")
