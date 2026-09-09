"""Which eligible obligations the gold is capable of being matched on.

Distinct from eligibility, which is a property of the release, and from difficulty: an
obligation nobody has ever hit is still hittable. A row is NOT hittable when the migration
overstated what the maintainer asked for, so an agent doing exactly what was requested scores
a miss -- PR33321's module-doc row is the worked case, and its own outcome observation records
it dropped on the evidence that the maintainer's actual one-line suggestion was adopted.

Evaluation-only. Nothing in generation reads it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.judge.semantic_judge import (
    HITTABILITY_REGISTRY, load_hittability,
)

OVERSTATED = (
    "obligation:0bb42bd28332beb5c9981a746053cf175213a08300871b86f8bf57e1c259d559"
)


def test_a_missing_registry_reports_nothing_rather_than_guessing():
    assert load_hittability(Path("does/not/exist.json")) is None


def test_the_installed_registry_covers_the_whole_eligible_set():
    if not HITTABILITY_REGISTRY.is_file():
        pytest.skip("no hittability registry in this checkout")
    payload = json.loads(HITTABILITY_REGISTRY.read_text(encoding="utf-8"))
    assert payload["counts"]["eligible"] == 40
    assert len(payload["rows"]) == 40
    # Every row carries a reason, so an exclusion can never be a bare flag.
    assert all(row["reason"] for row in payload["rows"])


def test_the_overstated_row_is_the_only_exclusion():
    if not HITTABILITY_REGISTRY.is_file():
        pytest.skip("no hittability registry in this checkout")
    mapping = load_hittability()
    excluded = [key for key, value in mapping.items() if not value]
    assert excluded == [OVERSTATED]


def test_the_registry_never_names_a_not_evaluable_row():
    """The three `not_evaluable` rows are already outside the eligible set. Listing one here
    would double-exclude it and make the two populations disagree."""

    if not HITTABILITY_REGISTRY.is_file():
        pytest.skip("no hittability registry in this checkout")
    release = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
    if not (release / "gold/judgments.jsonl").is_file():
        pytest.skip("no release in this checkout")
    from src.mathlib_review.io import load_jsonl
    from src.mathlib_review.schema import JudgmentNode

    not_evaluable = {
        obligation.obligation_id
        for judgment in load_jsonl(release / "gold/judgments.jsonl", JudgmentNode)
        for obligation in judgment.obligations
        if obligation.status != "proposed_atomic"
    }
    assert not_evaluable
    assert not (set(load_hittability()) & not_evaluable)
