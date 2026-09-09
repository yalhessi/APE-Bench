"""Which obligations a bench counts as an arm's own.

`benches.build_bench` matched the arm's concern family against the gold concern label. That
label is not a statement about which arm could answer the request: 13 of PR33098's 14
obligations carry `style`, including the seven that ask for `grind`. So the arm whose warrant
is tactic idiom was measured on three cases and the arm built for families on one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.analysis.benches import build_all
from src.mathlib_review.agenda.registry import ARM_DEFINITIONS

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
ARMS = {arm.arm_id: [arm.concern_family] for arm in ARM_DEFINITIONS}


def _built(selector):
    if not (RELEASE / "gold/judgments.jsonl").is_file():
        pytest.skip("no release in this checkout")
    return build_all(RELEASE, ARMS, selector=selector)


def test_an_unknown_selector_is_refused():
    with pytest.raises(ValueError):
        build_all(RELEASE, ARMS, selector="whatever")


def test_the_audited_selector_gives_the_family_arm_a_bench_at_all():
    """`family_design` had one positive case in the whole release under the label rule."""

    by_label = _built("gold_label")
    audited = _built("audited")
    assert len(by_label["family_design"].positives) == 1
    assert len(audited["family_design"].positives) == 14
    assert len(by_label["proof_idiom"].positives) == 3
    assert len(audited["proof_idiom"].positives) == 8


def test_the_label_rule_floods_style_with_other_arms_work():
    assert len(_built("gold_label")["style"].positives) == 12
    assert len(_built("audited")["style"].positives) == 4


def test_the_selector_is_part_of_the_fixture_identity():
    """Two different experiments must not share a fixture hash."""

    by_label = _built("gold_label")
    audited = _built("audited")
    for arm_id in ARMS:
        assert by_label[arm_id].selector == "gold_label"
        assert audited[arm_id].selector == "audited"
        assert by_label[arm_id].identity() != audited[arm_id].identity(), arm_id
