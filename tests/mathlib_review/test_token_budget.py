"""The run-level token budget: calibration, refusal, and what the plan records.

The dollar caps are vacuous on a model priced `0.0`, which is what the four locally hosted
`elm_*` models cost. These pin the three things that make the token block a real budget rather
than a second set of numbers: the caps keep the dollar caps' *ratios* (so a lead buys the same
number of jobs), a run that has neither ceiling is refused before it spends anything, and the
ceilings are sealed into the plan so two runs under different ones are not silently comparable.

Calibration: docs/research/2026-09-22-token-budget-calibration.md.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.mathlib_review.agenda.arms import (
    COST_HINT_PER_WORK_UNIT, TOKEN_HINT_PER_WORK_UNIT)
from src.mathlib_review.review.runner import (
    RESUMABLE_PLAN_FIELDS, BudgetTooSmall, V5DatasetConfig, _assert_a_ceiling_binds,
    _model_is_free, _report_token_budget)


def _logger():
    return SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None)


def _scaffold(model_name: str):
    return SimpleNamespace(llm_config=SimpleNamespace(model_name=model_name))


def _dataset(**overrides):
    return V5DatasetConfig(run_name="t", release="inputs/pr_review_v4/releases/x",
                           modification_inventory="inputs/pr_review_v4/x.jsonl",
                           **overrides)


# --- parity with the dollar caps ----------------------------------------------------------


def test_the_shipped_caps_keep_the_dollar_caps_ratios():
    """Ratios, not absolute values, are what govern behaviour: `per_pr / standard` is how many
    standard jobs a lead may buy before the reservation check refuses the next one. Setting one
    cap by a different method changes what the lead does rather than what it is measured in."""

    from pathlib import Path

    from ape.utils.config_loader import load_yaml

    dataset = load_yaml(Path("configs/bases/v5_generation.yaml"))["dataset"]
    assert (dataset["per_pr_token_cap"] / dataset["standard_budget_tokens"]
            == pytest.approx(dataset["per_pr_cost_cap"] / dataset["standard_budget_cap"]))
    assert (dataset["lead_token_cap"] / dataset["standard_budget_tokens"]
            == pytest.approx(dataset["lead_cost_cap"] / dataset["standard_budget_cap"]))
    assert (dataset["run_total_token_cap"] / dataset["standard_budget_tokens"]
            == pytest.approx(dataset["run_total_cost_cap"] / dataset["standard_budget_cap"]))


def test_one_exchange_rate_produced_every_cap():
    """1,200,000 processed tokens per billed dollar, measured over 16 v5 runs. The rate is
    applied nowhere at runtime; this checks the numbers it was used to pick, in both the
    shipped config and the model defaults it leaves alone."""

    from pathlib import Path

    from ape.utils.config_loader import load_yaml

    rate = 1_200_000
    defaults = V5DatasetConfig.model_fields
    for dollars, tokens in (("standard_budget_cap", "standard_budget_tokens"),
                            ("lead_cost_cap", "lead_token_cap"),
                            ("per_pr_cost_cap", "per_pr_token_cap"),
                            ("solo_cost_cap", "solo_token_cap")):
        assert (defaults[tokens].default
                == pytest.approx(defaults[dollars].default * rate, rel=1e-9)), tokens

    dataset = load_yaml(Path("configs/bases/v5_generation.yaml"))["dataset"]
    for dollars, tokens in (("standard_budget_cap", "standard_budget_tokens"),
                            ("lead_cost_cap", "lead_token_cap"),
                            ("per_pr_cost_cap", "per_pr_token_cap"),
                            ("run_total_cost_cap", "run_total_token_cap")):
        assert dataset[tokens] == pytest.approx(dataset[dollars] * rate, rel=1e-9), tokens

    assert TOKEN_HINT_PER_WORK_UNIT == pytest.approx(COST_HINT_PER_WORK_UNIT * rate)


def test_a_job_tier_scales_both_ceilings_the_same_way():
    from ape.tasks.lean_tasks.formal_math.review.delegation import JobSpec

    deep = JobSpec(invocation_id="i", arm_id="a", work_unit_id="w", pr_number=1,
                   payload={"task_type": "arm"}, budget_tier="deep")
    spec = deep.execution_spec(0.30, 360_000)
    assert spec.billed_cost_limit == 0.60
    assert spec.token_limit == 720_000


def test_a_run_that_states_no_token_cap_gets_no_token_ceiling_on_its_jobs():
    """0 disables a cap. It must reach the job as "absent" rather than as a ceiling of zero,
    which would stop every arm before its first turn."""

    from ape.tasks.lean_tasks.formal_math.review.delegation import JobSpec

    job = JobSpec(invocation_id="i", arm_id="a", work_unit_id="w", pr_number=1,
                  payload={"task_type": "arm"})
    assert job.execution_spec(0.30, 0).token_limit is None


# --- the refusal ---------------------------------------------------------------------------


def test_a_zero_priced_model_is_recognised_as_free():
    assert _model_is_free(_scaffold("elm_qwen_3.5"))
    assert _model_is_free(_scaffold("elm_llama_3.3"))
    assert not _model_is_free(_scaffold("gpt_5.2"))
    assert not _model_is_free(_scaffold("elm_gpt_5.2"))


def test_an_unknown_model_is_treated_as_paid():
    """A model with no pricing row cannot be *asserted* to be free, and guessing "free" would
    turn the refusal below into a false alarm on every new model name."""

    assert not _model_is_free(_scaffold("some-model-added-next-week"))
    assert not _model_is_free(_scaffold(None))


@pytest.mark.parametrize("mode,off", [
    ("lead", {"standard_budget_tokens": 0, "per_pr_token_cap": 0}),
    ("lead", {"per_pr_token_cap": 0}),
    ("solo", {"solo_token_cap": 0}),
    ("fanout", {"standard_budget_tokens": 0}),
])
def test_a_free_model_with_no_token_ceiling_is_refused(mode, off):
    """The hole this closes: every dollar cap is satisfied by any run whatsoever, so the budget
    report would print "fits" while describing a run nothing bounds."""

    dataset = _dataset(routing_mode=mode, **off)
    with pytest.raises(BudgetTooSmall) as caught:
        _assert_a_ceiling_binds(dataset, _scaffold("elm_qwen_3.5"), _logger(), enforce=True)
    assert "0.0 per token" in str(caught.value)


def test_a_free_model_with_its_token_ceilings_set_is_allowed():
    for mode in ("lead", "solo", "fanout"):
        _assert_a_ceiling_binds(_dataset(routing_mode=mode), _scaffold("elm_qwen_3.5"),
                                _logger(), enforce=True)


def test_a_paid_model_is_never_refused_for_want_of_a_token_ceiling():
    """A paid model is bounded by its dollar caps whatever the token block says."""

    dataset = _dataset(routing_mode="lead", standard_budget_tokens=0, per_pr_token_cap=0,
                       solo_token_cap=0, lead_token_cap=0)
    _assert_a_ceiling_binds(dataset, _scaffold("gpt_5.2"), _logger(), enforce=True)


def test_a_dry_run_warns_where_a_real_run_refuses():
    """The one command whose job is to say what the real run would do has to be able to say
    it would not start."""

    dataset = _dataset(routing_mode="lead", standard_budget_tokens=0, per_pr_token_cap=0)
    said = []
    logger = SimpleNamespace(info=lambda *a, **k: None,
                             warning=lambda fmt, *a: said.append(fmt % a if a else fmt))
    _assert_a_ceiling_binds(dataset, _scaffold("elm_qwen_3.5"), logger, enforce=False)
    assert said and "0.0 per token" in said[0]


# --- the run total --------------------------------------------------------------------------


def test_a_coverage_floor_above_the_run_token_cap_is_refused():
    """Same rule as the dollar side: the floor is not optional and not capped per PR, so a run
    whose floor alone exceeds the total cannot fit however the rest is configured."""

    dataset = _dataset(routing_mode="lead", run_total_token_cap=1_000_000)
    with pytest.raises(BudgetTooSmall) as caught:
        _report_token_budget(dataset, {"mandatory_floor_tokens": 5_000_000}, 12, _logger(),
                             enforce=True)
    assert "5,000,000" in str(caught.value)


def test_a_run_total_of_zero_disables_the_check():
    _report_token_budget(_dataset(routing_mode="lead", run_total_token_cap=0),
                         {"mandatory_floor_tokens": 99_000_000}, 12, _logger(), enforce=True)


def test_solo_is_checked_against_its_own_per_task_cap_and_no_floor():
    """`solo` schedules no work-unit job, so the agenda's floor describes work it will never
    do -- counting it would refuse a run for tokens it cannot spend."""

    dataset = _dataset(routing_mode="solo", solo_token_cap=1_800_000,
                       run_total_token_cap=1_000_000)
    with pytest.raises(BudgetTooSmall) as caught:
        _report_token_budget(dataset, {"mandatory_floor_tokens": 99_000_000}, 1, _logger(),
                             enforce=True)
    assert "solo_token_cap" in str(caught.value)


def test_the_agenda_reports_its_floor_in_both_denominations():
    from src.mathlib_review.agenda import agenda as agenda_module

    import inspect

    source = inspect.getsource(agenda_module)
    assert '"mandatory_floor_tokens"' in source
    assert "TOKEN_HINT_PER_WORK_UNIT" in source


# --- what the plan records --------------------------------------------------------------------


def test_the_plan_seals_the_token_caps():
    from src.mathlib_review.schema.review import V5RunPlan

    for field in ("lead_token_cap", "standard_budget_tokens", "per_pr_token_cap"):
        assert field in V5RunPlan.model_fields


def test_raising_a_token_cap_is_a_resume_not_a_different_experiment():
    """A budget does not change what a run measures. A resumed run with a raised ceiling
    answers the same question, having been allowed to finish asking it."""

    for field in ("lead_token_cap", "standard_budget_tokens", "per_pr_token_cap"):
        assert field in RESUMABLE_PLAN_FIELDS


def test_a_resumed_lead_remembers_the_tokens_it_delegated():
    """The dollar version of this bug hands out a second full `per_pr_cost_cap`. On a
    zero-priced model the dollar figure is 0.0 throughout, so the token half is the only one
    that can be doubled."""

    import json
    from dataclasses import asdict
    from pathlib import Path
    import tempfile

    from ape.tasks.lean_tasks.formal_math.review import journal
    from ape.tasks.lean_tasks.formal_math.review.delegation import JobOutcome, JobSpec

    spec = JobSpec(invocation_id="wu:1#proof_golf", arm_id="proof_golf", work_unit_id="wu:1",
                   pr_number=1, payload={"task_type": "arm"}, disposition="proposed")
    outcome = JobOutcome(invocation_id=spec.invocation_id, arm_id="proof_golf",
                         work_unit_id="wu:1", pr_number=1, budget_tier="standard",
                         status="success", cost=0.0, tokens=300_000)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "journal.jsonl"
        path.write_text("".join(json.dumps(row, default=str) + "\n" for row in (
            {"event": journal.WAVE_OPENED, "wave": 1, "floor": False,
             "specs": [journal.spec_row(spec)]},
            {"event": journal.SETTLED, "wave": 1, "outcome": asdict(outcome)},
        )), encoding="utf-8")
        state = {"wave": 0, "outcomes": {}, "requested": set(), "spend": 0.0,
                 "delegated_spend": 0.0, "reserved": 0.0, "tokens": 0,
                 "delegated_tokens": 0, "reserved_tokens": 0, "floor_done": False,
                 "comprehension": None}
        journal.replay(str(path), state,
                       pool={spec.invocation_id: {"task_data": {"task_type": "arm"}}},
                       spec_cls=JobSpec, outcome_cls=JobOutcome)

    assert state["tokens"] == 300_000
    assert state["delegated_tokens"] == 300_000
    # Reservations are deliberately not journaled: after a restart nothing is in flight.
    assert state["reserved_tokens"] == 0


def test_the_lead_reserves_and_settles_in_both_denominations():
    import inspect

    from ape.tasks.lean_tasks.formal_math.review.lead import ReviewLeadTask

    source = inspect.getsource(ReviewLeadTask)
    assert "per-PR token cap would be exceeded" in source
    assert 'state["reserved_tokens"] += max_tokens' in source
    assert 'state["delegated_tokens"] += outcome.tokens' in source


# --- keeping the two blocks in step ---------------------------------------------------------


def _drift(**overrides):
    from src.mathlib_review.review.runner import _warn_on_denomination_drift

    said = []
    logger = SimpleNamespace(info=lambda *a, **k: None,
                             warning=lambda fmt, *a: said.append(fmt % a if a else fmt))
    _warn_on_denomination_drift(_dataset(**overrides), logger)
    return said


def test_a_config_that_retunes_one_block_and_not_the_other_says_so():
    """The live case: `pr_review_v5_smoke4.yaml` set `per_pr_cost_cap: 2.0` against the base's
    `standard_budget_cap: 0.30` -- 6.7 standard jobs -- while the token block it did not touch
    bought 5. Two runs "under the same config" then differ by a quarter of the fan-out
    depending on which model they ran."""

    said = _drift(standard_budget_cap=0.30, per_pr_cost_cap=2.0,
                  standard_budget_tokens=360_000, per_pr_token_cap=1_800_000)
    assert any("buys 6.7 standard jobs but per_pr_token_cap buys 5.0" in line
               for line in said)


def test_matched_blocks_are_silent():
    assert _drift(standard_budget_cap=0.30, per_pr_cost_cap=1.50, lead_cost_cap=1.00,
                  run_total_cost_cap=10.0, standard_budget_tokens=360_000,
                  per_pr_token_cap=1_800_000, lead_token_cap=1_200_000,
                  run_total_token_cap=12_000_000) == []


def test_a_disabled_cap_is_not_drift():
    """0 means "off", and an off cap authorises nothing to compare."""

    assert _drift(standard_budget_tokens=360_000, per_pr_token_cap=0,
                  lead_token_cap=0, run_total_token_cap=0) == []


def test_every_shipped_config_keeps_its_two_blocks_in_step():
    """The guard exists because a child config restates only what it varies. This is the
    guard applied to the tree, so a new config cannot land half-retuned."""

    from pathlib import Path

    from ape.utils.config_loader import load_yaml
    from src.mathlib_review.review.runner import _warn_on_denomination_drift

    drifted = {}
    for path in sorted(Path("configs").rglob("*.yaml")):
        try:
            raw = load_yaml(path)
        except Exception:  # noqa: BLE001 - a config this test cannot read is not its subject
            continue
        caps = {key: value for key, value in (raw.get("dataset") or {}).items()
                if key.endswith(("_cost_cap", "_budget_cap", "_token_cap", "_budget_tokens"))}
        if not caps:
            continue
        said = []
        logger = SimpleNamespace(
            info=lambda *a, **k: None,
            warning=lambda fmt, *a: said.append(fmt % a if a else fmt))
        try:
            _warn_on_denomination_drift(_dataset(**caps), logger)
        except Exception:  # noqa: BLE001 - replay configs are a different model
            continue
        if said:
            drifted[str(path)] = said
    assert not drifted, drifted
