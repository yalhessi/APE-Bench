"""One statement of what something cost, in every way this project counts cost.

Three axes get conflated, and each conflation has already cost a run:

* **billed vs nominal** -- what was paid versus the no-cache counterfactual, ~2.5x apart.
  specialist4 was $0.1218 billed against $0.3017 nominal. Caps enforce billed; the manifest
  reported nominal; nothing said which was which.
* **self vs nested** -- an agent's own conversation versus what its children spent. A lead
  that does not bubble is how the floor's $14.52 went missing for a whole run.
* **charged** -- what a particular cap counted, which is neither: the coverage floor is exempt
  from `per_pr_cost_cap` by design, so a lead's charged figure is smaller than its billed
  figure and both are correct.

Every one of those numbers was already computed somewhere. None could be stated together.
"""

from __future__ import annotations

import pytest

from ape.orchestration.models import UsageBreakdown


def test_billed_and_nominal_are_separate_and_inclusive():
    usage = UsageBreakdown.of_self(billed=0.1218, nominal=0.3017)
    usage = usage.with_nested(billed=0.5, nominal=1.4)
    assert usage.billed == pytest.approx(0.6218)
    assert usage.nominal == pytest.approx(1.7017)


def test_self_and_nested_do_not_collapse():
    """A lead's own conversation and what it delegated are different facts. Reporting only the
    sum makes "the lead spent its whole budget on itself" indistinguishable from "the lead
    spent nothing and its arms spent everything"."""

    usage = UsageBreakdown.of_self(billed=0.2, nominal=0.5).with_nested(billed=1.8, nominal=4.0)
    assert usage.self_billed == pytest.approx(0.2)
    assert usage.nested_billed == pytest.approx(1.8)
    assert usage.billed == pytest.approx(2.0)


def test_budget_charged_is_neither_self_nor_billed():
    """The floor is exempt from `per_pr_cost_cap`, so a lead can be billed $2.00 and charged
    $0.50 against that cap, with both numbers right."""

    usage = UsageBreakdown(self_billed=0.2, nested_billed=1.8, budget_charged=0.5)
    assert usage.billed == pytest.approx(2.0)
    assert usage.budget_charged == pytest.approx(0.5)


def test_a_default_breakdown_is_all_zero_and_says_nothing():
    """`budget_charged=0` means no cap looked at this, not that it was free."""

    assert UsageBreakdown().summary() == {
        "self_billed": 0.0, "self_nominal": 0.0, "nested_billed": 0.0,
        "nested_nominal": 0.0, "billed": 0.0, "nominal": 0.0, "budget_charged": 0.0,
    }


def test_every_summary_key_names_its_axis():
    """A key called `cost` is how this went wrong. Each one has to say billed or nominal, self
    or nested, or be the explicit inclusive total."""

    keys = set(UsageBreakdown().summary())
    assert keys == {"self_billed", "self_nominal", "nested_billed", "nested_nominal",
                    "billed", "nominal", "budget_charged"}
    assert not any(key in ("cost", "total_cost") for key in keys)


def test_a_task_outcome_carries_its_own_usage():
    from ape.orchestration.models import (
        AttemptOutcome, SampleOutcome, TaskOutcome, TaskExecutionStatus,
    )

    outcome = TaskOutcome(
        task_id="t", task_type="arm", global_index="1",
        execution_status=TaskExecutionStatus.COMPLETED,
        billed_cost=0.12, nominal_cost=0.30,
        usage=UsageBreakdown.of_self(billed=0.12, nominal=0.30),
    )
    assert outcome.usage.billed == pytest.approx(0.12)
    assert outcome.usage.nested_billed == 0.0


def test_from_samples_fills_the_self_half(tmp_path):
    """And only the self half: a task does not know what its children spent until its parent
    tells it, and inventing a nested figure here would double-count."""

    from ape.orchestration.models import TaskOutcome
    from tests.orchestration.test_task_outcome import _attempt, _sample

    sample = _sample([_attempt(1, "success", nominal=0.30, billed=0.12)])
    outcome = TaskOutcome.from_samples(
        task_id="t", task_type="arm", global_index="1", samples={0: sample},
        max_retries=1, max_turns=40, sample_max_cost=1.0, has_result=True)
    assert outcome.usage.self_billed == pytest.approx(0.12)
    assert outcome.usage.self_nominal == pytest.approx(0.30)
    assert outcome.usage.nested_billed == 0.0
    # The scalars stay, and stay equal to the self half: files in the tree carry them.
    assert outcome.billed_cost == pytest.approx(outcome.usage.self_billed)
    assert outcome.nominal_cost == pytest.approx(outcome.usage.self_nominal)
