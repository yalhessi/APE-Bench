"""Coordination is a recorded choice, and a policy the code cannot honour is refused.

Every one of these was a constant in `lead.py` or `delegation.py`: two waves, a pair may run
at most once, the parent sees a truncated summary, a child sees nothing of its siblings, the
lead may drop and fold but not rewrite. None of it was written down as a choice, so none of it
could be varied as an experiment — which is why coordination is the part of this design that
has never been measured.

The defaults are exactly today's behaviour, so the first run after this is unchanged and the
second can differ in one respect.
"""

from __future__ import annotations

import pytest

from src.datasets.pr_review_v5.coordination import (
    COORDINATION_VERSION, CoordinationConfig, CoordinationPolicy, SynthesisPolicy,
    assert_implemented,
)


def test_the_defaults_are_what_the_code_actually_does():
    config = CoordinationConfig()
    assert config.coordination.max_rounds == 2
    # A pair may run at most once: `delegate` rejects one already requested.
    assert config.coordination.max_redispatches_per_pair == 0
    assert config.coordination.parent_view == "summary"
    assert config.coordination.sibling_view == "none"
    # `synthesis.apply_assessments` drops and folds; no rewrite path exists.
    assert config.synthesis.authority == "subtractive"
    assert_implemented(config)


def test_scheduling_and_synthesis_are_separate_objects():
    """Folding them together would mean a coordination experiment silently changed what got
    published, and neither result would be readable."""

    config = CoordinationConfig()
    assert isinstance(config.coordination, CoordinationPolicy)
    assert isinstance(config.synthesis, SynthesisPolicy)
    report = config.report()
    assert set(report["coordination"]) & set(report["synthesis"]) == {"schema_version"}


def test_every_policy_is_bounded_before_it_runs():
    """A policy whose cost cannot be computed in advance cannot be preflighted, and an
    unbounded budget is the thing this pipeline keeps discovering on the invoice."""

    policy = CoordinationPolicy(max_rounds=3, max_jobs=10, max_redispatches_per_pair=1)
    assert policy.bounds() == {
        "max_rounds": 3, "max_jobs": 10, "max_redispatches_per_pair": 1}
    assert policy.worst_case_jobs() == 20


def test_authority_says_what_it_permits():
    assert not SynthesisPolicy(authority="router_only").applies_removals()
    assert SynthesisPolicy(authority="subtractive").applies_removals()
    assert not SynthesisPolicy(authority="subtractive").allows_rewrites()
    assert SynthesisPolicy(authority="final_arbiter").allows_rewrites()


@pytest.mark.parametrize("kwargs,expected", [
    ({"sibling_view": "blackboard"}, "sibling_view"),
    ({"parent_view": "full"}, "parent_view"),
    ({"parent_view": "counts"}, "parent_view"),
    ({"max_redispatches_per_pair": 1}, "max_redispatches_per_pair"),
])
def test_an_unimplemented_coordination_option_is_refused(kwargs, expected):
    """A field that is read but not implemented is worse than no field: the run records a
    policy it did not follow, and the result is attributed to a mechanism that never ran."""

    config = CoordinationConfig(coordination=CoordinationPolicy(**kwargs))
    with pytest.raises(ValueError) as excinfo:
        assert_implemented(config)
    assert expected in str(excinfo.value)


def test_final_arbiter_is_refused_because_evidence_does_not_transfer():
    """A rewritten finding is a new revision, and claim-scoped evidence gathered for the
    previous wording does not apply to it."""

    config = CoordinationConfig(synthesis=SynthesisPolicy(authority="final_arbiter"))
    with pytest.raises(ValueError) as excinfo:
        assert_implemented(config)
    assert "final_arbiter" in str(excinfo.value)
    assert "evidence" in str(excinfo.value)


def test_router_only_is_permitted_since_applying_nothing_needs_no_new_code():
    assert_implemented(CoordinationConfig(synthesis=SynthesisPolicy(authority="router_only")))


def test_the_policy_is_sealed_into_the_run_plan():
    """A result attributed to a mechanism the run does not record is not attributable."""

    from pathlib import Path

    from src.datasets.pr_review_v5.runner import coordination_config, load_run

    config_path = Path("configs/pr_review_v5_specialist4.yaml")
    if not config_path.is_file():
        pytest.skip("config not present")
    dataset, _scaffold, _overrides = load_run(config_path)
    report = coordination_config(dataset).report()

    assert report["coordination_version"] == COORDINATION_VERSION
    # `max_jobs` mirrors `max_delegations` rather than duplicating it, so the plan and the
    # enforcement cannot disagree about what the run was allowed to do.
    assert report["coordination"]["max_jobs"] == dataset.max_delegations
    assert report["synthesis"]["authority"] == "subtractive"


def test_an_unknown_field_is_refused():
    with pytest.raises(Exception):
        CoordinationPolicy(max_roundz=3)
