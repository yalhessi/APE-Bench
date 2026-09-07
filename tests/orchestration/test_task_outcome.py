"""Every scheduled task leaves an execution record, and caps are enforced on billed cost.

Both properties come from one incident. A `family_design` arm on PR 33117 ran for 184 seconds
and was billed real money, then reached the delegation ledger as `status=failed, cost=0.0`.
That row satisfied a mandatory-coverage check, which set `units_without_specialist` to empty,
which is the field used to green-light a specialist-only run — and the arm was written up as
having abstained.

Two independent defects produced it:

* the conversation paused on **nominal** cost while `Sample.can_execute` decided resumability
  on **billed** cost, so a job that had exhausted its cap looked resumable;
* `_try_aggregate` returned early for a resumable task without writing anything at all, so the
  spend had nowhere to be recorded.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ape.orchestration.models import (
    Attempt, ExecutionStatus, Sample, TaskExecutionStatus, TaskOutcome,
)


def _attempt(attempt_id, status, *, nominal, billed, turns=3):
    start = datetime(2026, 9, 7, 12, 0, 0)
    return Attempt(
        attempt_id=attempt_id,
        path=f"/tmp/attempt_{attempt_id}",
        status=status,
        created_at=start,
        started_at=start,
        completed_at=start + timedelta(seconds=30),
        cost=nominal,
        cached_cost=billed,
        turns=turns,
        max_turns=40,
        cost_limit=0.30,
    )


def _sample(attempts, index=0):
    return Sample(
        sample_id=f"s{index}",
        task_global_index="gi",
        sample_index=index,
        attempts=attempts,
        created_at=datetime(2026, 9, 7, 12, 0, 0),
        updated_at=datetime(2026, 9, 7, 12, 1, 0),
    )


def test_a_cost_paused_sample_is_not_resumable_once_billed_reaches_the_cap():
    """The exact 33117 numbers: nominal $0.3017, billed $0.1218, cap $0.30.

    Under the old rule this returned True — the sample looked resumable, so it was never
    aggregated and its spend was never booked. The conversation now pauses on billed too, so a
    sample only reaches this state having actually been billed the cap.
    """

    exhausted = _sample([_attempt(1, ExecutionStatus.PAUSED_COST_LIMIT,
                                 nominal=0.75, billed=0.30)])
    assert exhausted.can_execute(max_retries=3, max_turns=40, sample_max_cost=0.30) is False


def test_billed_cost_accumulates_across_attempts():
    """Charging only the last attempt let a sample pause and resume indefinitely, each attempt
    staying under the cap on its own."""

    sample = _sample([
        _attempt(1, ExecutionStatus.PAUSED_COST_LIMIT, nominal=0.40, billed=0.18),
        _attempt(2, ExecutionStatus.PAUSED_COST_LIMIT, nominal=0.40, billed=0.17),
    ])
    assert sample.get_accumulated_cached_cost() == pytest.approx(0.35)
    assert sample.can_execute(max_retries=3, max_turns=40, sample_max_cost=0.30) is False


def test_a_paused_task_records_its_spend_rather_than_reading_as_a_free_failure():
    """The property the ledger needed: paused is not failed, and it is not $0.00."""

    samples = {0: _sample([_attempt(1, ExecutionStatus.PAUSED_COST_LIMIT,
                                    nominal=0.3017, billed=0.1218)])}
    outcome = TaskOutcome.from_samples(
        task_id="t", task_type="arm", global_index="gi", samples=samples,
        max_retries=3, max_turns=40, sample_max_cost=0.30, has_result=False)

    assert outcome.execution_status is TaskExecutionStatus.PAUSED
    assert outcome.has_result is False
    assert outcome.billed_cost == pytest.approx(0.1218)
    assert outcome.nominal_cost == pytest.approx(0.3017)
    assert outcome.reason


def test_execution_status_is_independent_of_the_domain_verdict():
    """A judgment task that correctly returns a negative verdict completed successfully.

    `BaseTaskResult.success` is the domain answer; `execution_status` is whether the task ran.
    Conflating them is what makes a valid negative judgment look like an infrastructure
    failure.
    """

    samples = {0: _sample([_attempt(1, ExecutionStatus.SUCCESS, nominal=0.10, billed=0.04)])}
    outcome = TaskOutcome.from_samples(
        task_id="t", task_type="judge", global_index="gi", samples=samples,
        max_retries=3, max_turns=40, sample_max_cost=1.0, has_result=True)

    assert outcome.execution_status is TaskExecutionStatus.COMPLETED
    assert outcome.has_result is True


def test_the_sample_level_survives_because_the_judge_votes():
    """task -> samples -> attempts, not task -> attempts: the judge runs sample_count 3, and
    collapsing the sample level would lose the majority-vote structure it depends on."""

    samples = {
        i: _sample([_attempt(1, ExecutionStatus.SUCCESS, nominal=0.10, billed=0.04)], index=i)
        for i in range(3)
    }
    outcome = TaskOutcome.from_samples(
        task_id="t", task_type="judge", global_index="gi", samples=samples,
        max_retries=3, max_turns=40, sample_max_cost=1.0, has_result=True)

    assert [s.sample_index for s in outcome.samples] == [0, 1, 2]
    assert outcome.billed_cost == pytest.approx(0.12)


def test_a_failed_task_is_distinguishable_from_a_paused_one():
    samples = {0: _sample([_attempt(1, ExecutionStatus.FAILED_MODEL, nominal=0.05, billed=0.02)])}
    outcome = TaskOutcome.from_samples(
        task_id="t", task_type="arm", global_index="gi", samples=samples,
        max_retries=0, max_turns=40, sample_max_cost=0.30, has_result=False)

    assert outcome.execution_status is TaskExecutionStatus.FAILED
    assert outcome.billed_cost == pytest.approx(0.02)
