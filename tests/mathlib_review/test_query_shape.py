"""What the arms asked the repository, not just what they concluded.

The oracle ladder has to separate "never asked the right question" from "asked and it did not
help". That distinction is invisible in the run artifacts, which record conclusions, and it is
the reason `trajectory.py` makes the transcripts durable and this analysis reads them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis.queries import (
    TACTIC_VOCABULARY, WIDE_TACTIC_VOCABULARY, is_tactic_shaped, scope_class_of,
)

RUN = Path("results/pr_review_v5/runs/pr5_smoke4_rep9/trajectory")


def test_scope_is_classified_not_string_matched():
    """The hand count keyed on `path == "target/Mathlib"`, which a trailing slash defeats."""

    assert scope_class_of(None) == "corpus"
    assert scope_class_of("target/Mathlib") == "corpus"
    assert scope_class_of("target/Mathlib/") == "corpus"
    assert scope_class_of("target") == "corpus"
    assert scope_class_of("target/Mathlib/Topology") == "subtree"
    assert scope_class_of("target/Mathlib/Topology/MetricSpace/CoveringNumbers.lean") == "file"


def test_a_regex_query_for_a_tactic_is_recognised_as_one():
    """The case that forced normalization: the generalist searched the literal `\\bgrind\\b`,
    and a naive word-boundary test scores that as NOT asking about grind, because the `b` of
    the escape closes the boundary against the `g`. Reading a grind search as a non-tactic
    search is the exact error this analysis exists to avoid."""

    assert is_tactic_shaped(r"\bgrind\b")
    assert is_tactic_shaped(r"by_cases h : .* ≠ ⊤")
    assert is_tactic_shaped(r"\bomega\b|\bdecide\b")


def test_identifiers_that_merely_contain_a_tactic_name_are_not_tactic_queries():
    """`decide` and `bound` sit inside ordinary Mathlib identifiers, so a substring test would
    score name lookups as tactic questions and wash out the whole distinction."""

    assert not is_tactic_shaped("decide_eq_true_eq")
    assert not is_tactic_shaped("bounded_of_isCompact")
    assert not is_tactic_shaped("Metric.isCover_maximalSeparatedSet")
    assert not is_tactic_shaped("coeff.*expand")


def test_the_wide_vocabulary_is_a_superset():
    assert set(TACTIC_VOCABULARY) < set(WIDE_TACTIC_VOCABULARY)
    assert is_tactic_shaped("simp only [foo]", WIDE_TACTIC_VOCABULARY)
    assert not is_tactic_shaped("simp only [foo]", TACTIC_VOCABULARY)


def _report():
    path = RUN / "queries_report.json"
    if not path.is_file():
        pytest.skip("no query report; run `python -m src.mathlib_review.analysis.queries`")
    return json.loads(path.read_text(encoding="utf-8"))


def test_the_run_reproduces_the_hand_counted_total():
    report = _report()
    searches = sum(row["content_search"] for row in report["by_arm"].values())
    assert searches == 176


def test_the_proof_arms_never_asked_about_a_tactic_under_either_vocabulary():
    """The finding must not rest on where the vocabulary line is drawn. Widening it takes the
    run's tactic-shaped queries from 2 to 14 and takes `style` from 1 to 9, while the two arms
    whose warrant IS tactic idiom stay at zero."""

    report = _report()
    for arm in ("proof_idiom", "proof_golf"):
        row = report["by_arm"][arm]
        assert row["tactic_shaped"] == 0, arm
        assert row["tactic_shaped_wide"] == 0, arm
        # And they never left the file they were handed, while naming and duplication did.
        assert row["corpus_scope"] == 0, arm
    assert report["by_arm"]["style"]["tactic_shaped_wide"] == 9
    assert report["by_arm"]["duplication"]["corpus_scope"] == 36
