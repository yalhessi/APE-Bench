"""The run state machine, and the property it exists to hold.

Every transition here was already enforced somewhere -- `TaskExecutionStatus` in the
orchestrator, `completion_status` on the manifest, the judge's refusal to score an incomplete
run. What did not exist was a place that states the machine, so the guarantee had to be
assembled by reading three files and hoping they agreed.

These tests also pin the agreement, which is the part that would rot: the manifest's own
vocabulary is `complete` / `partial` / `failed`, and it is deliberately not renamed.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.run_state import (
    SCOREABLE, TRANSITIONS, IllegalTransition, RunState, assert_transition, from_manifest,
)


def test_paused_is_not_partial():
    """The distinction that voided two September runs. `paused` stopped on a limit and can
    resume; `partial` is closed and cannot satisfy required coverage, so its recall is measured
    against a denominator including units nobody looked at."""

    assert RunState.PAUSED in TRANSITIONS[RunState.RUNNING]
    assert RunState.PARTIAL in TRANSITIONS[RunState.RUNNING]
    # Resumable.
    assert TRANSITIONS[RunState.PAUSED] == frozenset({RunState.RUNNING})
    # Closed.
    assert TRANSITIONS[RunState.PARTIAL] == frozenset()


def test_a_partial_run_never_enters_the_successful_chain():
    for target in (RunState.GENERATED, RunState.FINALIZED, RunState.JUDGED):
        with pytest.raises(IllegalTransition):
            assert_transition(RunState.PARTIAL, target)


def test_a_resume_goes_back_to_running_not_straight_to_a_verdict():
    """What closes a run is reconciliation, and that only happens after work stops."""

    assert_transition(RunState.PAUSED, RunState.RUNNING)
    with pytest.raises(IllegalTransition):
        assert_transition(RunState.PAUSED, RunState.GENERATED)


def test_only_a_closed_covered_run_is_scoreable():
    assert SCOREABLE == frozenset({RunState.GENERATED, RunState.FINALIZED})
    assert RunState.PARTIAL not in SCOREABLE
    assert RunState.PAUSED not in SCOREABLE


def test_the_error_says_what_the_legal_moves_are():
    """"Illegal transition" alone tells you nothing you can act on."""

    with pytest.raises(IllegalTransition) as excinfo:
        assert_transition(RunState.PLANNED, RunState.JUDGED)
    message = str(excinfo.value)
    assert "planned -> judged" in message
    assert "running" in message


def test_the_manifest_vocabulary_maps_on_without_being_renamed():
    """`complete` / `partial` / `failed` are in every manifest in the tree. Renaming them to
    say the same thing in different words would make old runs unreadable."""

    assert from_manifest("complete") is RunState.GENERATED
    assert from_manifest("partial") is RunState.PARTIAL
    assert from_manifest("failed") is RunState.FAILED
    # An unknown status is not silently optimistic.
    assert from_manifest("something-new") is RunState.FAILED


def test_the_manifest_states_and_the_machine_agree():
    """The manifest's `Literal` is the source of the strings; every one must map."""

    from src.mathlib_review.schema.runs import RunManifest

    declared = set(RunManifest.model_fields["completion_status"].annotation.__args__)
    for status in declared:
        assert isinstance(from_manifest(status), RunState), status


def test_every_state_is_reachable_from_planned():
    """A state nothing can reach is a state that does not exist, and would be a lie in the
    diagram."""

    seen, frontier = {RunState.PLANNED}, [RunState.PLANNED]
    while frontier:
        for nxt in TRANSITIONS.get(frontier.pop(), frozenset()):
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    assert seen == set(RunState)


def test_the_judge_asks_the_machine_rather_than_comparing_a_string():
    """The machine is only worth having if it is the thing consulted. A literal `== "complete"`
    in the judge would be a second place that has to agree with it, and nothing would check."""

    import inspect

    from src.mathlib_review.judge import runner

    source = inspect.getsource(runner.assert_source_run_is_complete)
    assert "SCOREABLE" in source
    assert '== "complete"' not in source
