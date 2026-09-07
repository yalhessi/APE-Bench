"""Invariants that were comments, made into checks.

Each of these was documented on the field it governs and enforced by nothing. A comment
cannot check itself, and at least one of them has already been read wrong in a way that cost
a run.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from src.mathlib_review.review.runner import (
    CoverageGapAtPlanTime, PlanChangedSemantically, RESUMABLE_PLAN_FIELDS,
    assert_coverage_is_reachable, assert_the_judge_model_is_pinned, seal_or_revise_plan,
)

LOGGER = logging.getLogger("test")


class _Dataset:
    def __init__(self, **kwargs):
        self.generalist_floor = kwargs.get("generalist_floor", True)
        self.skip_evidence_chain = kwargs.get("skip_evidence_chain", False)


# --- coverage ------------------------------------------------------------------------------


def test_a_specialist_only_run_over_uncovered_units_is_refused():
    """The comment: "Only turn it off on a set where the specialists already cover every work
    unit". Without the floor those units are not reviewed at all, so a recall drop measures
    the units nobody looked at."""

    with pytest.raises(CoverageGapAtPlanTime) as excinfo:
        assert_coverage_is_reachable(
            _Dataset(generalist_floor=False),
            {"units_without_specialist": ["wu:1", "wu:2"]}, LOGGER)
    message = str(excinfo.value)
    assert "wu:1" in message
    assert "coverage loss rather than arm quality" in message


def test_a_specialist_only_run_with_full_coverage_passes():
    assert_coverage_is_reachable(
        _Dataset(generalist_floor=False), {"units_without_specialist": []}, LOGGER) is None


def test_the_floor_being_on_makes_the_question_moot():
    """With the floor, every unit draws a generalist by construction."""

    assert_coverage_is_reachable(
        _Dataset(generalist_floor=True),
        {"units_without_specialist": ["wu:1"]}, LOGGER)


def test_a_closed_evidence_gate_announces_itself(caplog):
    """Eight runs reported publication rates under a closed gate as if they were strictness
    results. If it is turned back on, that has to be said before the money is spent."""

    with caplog.at_level(logging.WARNING):
        assert_the_judge_model_is_pinned(_Dataset(skip_evidence_chain=True), LOGGER)
    assert "not strictness results" in caplog.text


def test_an_open_gate_says_nothing(caplog):
    with caplog.at_level(logging.WARNING):
        assert_the_judge_model_is_pinned(_Dataset(skip_evidence_chain=False), LOGGER)
    assert caplog.text == ""


# --- the sealed plan, and what a resume may change -------------------------------------------


def _plan(**overrides):
    from src.mathlib_review.schema.review import V5RunPlan

    base = dict(
        run_id="v5run:t", run_name="t", routing_mode="lead", agenda_sha256="a" * 64,
        release="rel", prompt_sha256_by_invocation={"wu:1#golf": "b" * 64},
        arm_sha256_by_id={"proof_golf": "c" * 64}, model_name="gpt_5.2",
        scaffold_config_sha256="d" * 64, lead_cost_cap=1.0, standard_budget_cap=0.3,
        per_pr_cost_cap=1.5, source_sha256="e" * 64,
    )
    base.update(overrides)
    return V5RunPlan(**base)


def test_the_first_write_seals_the_plan(tmp_path):
    path = seal_or_revise_plan(tmp_path, _plan(), LOGGER)
    assert path.name == "run_plan.json"
    assert json.loads(path.read_text())["run_name"] == "t"


def test_writing_the_same_plan_again_is_a_no_op(tmp_path):
    seal_or_revise_plan(tmp_path, _plan(), LOGGER)
    assert seal_or_revise_plan(tmp_path, _plan(), LOGGER).name == "run_plan.json"
    assert not (tmp_path / "run_plan_revision_2.json").exists()


def test_raising_a_budget_on_resume_writes_a_revision(tmp_path, caplog):
    """A run paused on budget can only be finished by raising the budget, which made the plan
    differ, which made `write_once` refuse the resume at its first write. The two ways out
    were a new run name -- forfeiting every completed attempt in the orchestrator cache -- or
    deleting the pre-registration."""

    seal_or_revise_plan(tmp_path, _plan(), LOGGER)
    with caplog.at_level(logging.WARNING):
        path = seal_or_revise_plan(tmp_path, _plan(per_pr_cost_cap=3.0), LOGGER)
    assert path.name == "run_plan_revision_2.json"
    assert json.loads(path.read_text())["per_pr_cost_cap"] == 3.0
    # The original stands.
    assert json.loads((tmp_path / "run_plan.json").read_text())["per_pr_cost_cap"] == 1.5


def test_revisions_accumulate_monotonically(tmp_path):
    seal_or_revise_plan(tmp_path, _plan(), LOGGER)
    seal_or_revise_plan(tmp_path, _plan(per_pr_cost_cap=3.0), LOGGER)
    third = seal_or_revise_plan(tmp_path, _plan(per_pr_cost_cap=4.0), LOGGER)
    assert third.name == "run_plan_revision_3.json"


@pytest.mark.parametrize("field,value", [
    ("agenda_sha256", "f" * 64),
    ("model_name", "gpt_5_mini"),
    ("routing_mode", "rules"),
    ("prompt_sha256_by_invocation", {"wu:1#golf": "0" * 64}),
    ("arm_sha256_by_id", {"proof_golf": "0" * 64}),
    ("evaluation_settings", {"generalist_floor": False}),
])
def test_a_semantic_change_is_refused_and_names_the_field(tmp_path, field, value):
    """Not "the plan differs" -- which field, so it can be acted on."""

    seal_or_revise_plan(tmp_path, _plan(), LOGGER)
    with pytest.raises(PlanChangedSemantically) as excinfo:
        seal_or_revise_plan(tmp_path, _plan(**{field: value}), LOGGER)
    message = str(excinfo.value)
    assert field in message
    assert "new run_name" in message


def test_the_resumable_set_is_only_about_spending():
    """The line is "does this change what the run measures". If a field creeps into this set
    that changes the experiment, a resume silently becomes a second experiment."""

    assert RESUMABLE_PLAN_FIELDS == {
        "lead_cost_cap", "standard_budget_cap", "per_pr_cost_cap",
        "scaffold_config_sha256", "git_commit", "git_tree_state", "source_sha256",
    }


# --- what a run's numbers mean ---------------------------------------------------------------


def test_the_plan_records_what_makes_its_numbers_readable():
    """Four settings decide what a recall figure means, and all four were comments."""

    from src.mathlib_review.schema.review import V5RunPlan

    fields = V5RunPlan.model_fields
    assert "evaluation_settings" in fields
    assert "evaluation_contract_version" in fields


def test_the_contract_version_is_separate_from_the_schema_version():
    """`schema_version` says the file parses. The contract version says the numbers compare.
    Widening `pairing_tiers` can only raise recall and changes no field, so without this a run
    that widened it and one that did not are separated by nothing readable."""

    from src.mathlib_review.schema.review import EVALUATION_CONTRACT_VERSION, V5RunPlan

    plan = _plan()
    assert plan.evaluation_contract_version == EVALUATION_CONTRACT_VERSION
    assert plan.evaluation_contract_version != plan.schema_version
