"""Rule-by-rule tests for the reimplemented Mathlib text-style linters.

Each rule gets a positive case and a negative case. The negatives matter more than the
positives: this checker's value rests on staying silent on code Mathlib accepts, and the
excusal rules (hanging `by`, `←%`) are exactly where a naive reimplementation over-fires.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.evidence.operators.lint_policy import (
    find_forbidden_construct,
    find_long_lines,
    lint_target,
)
from src.mathlib_review.schema import ChangeTarget


def _target(code: str, *, base: str = "", kind: str = "declaration") -> ChangeTarget:
    return ChangeTarget(
        change_id="change:test",
        episode_id="episode:test",
        pr_number=1,
        kind="declaration",
        path="Mathlib/Test.lean",
        declaration_name="Test.lemma",
        declaration_kind=kind,
        changed_range_ids=["range:test"],
        diff_fragments=[],
        base_code=base,
        reviewed_code=code,
        parse_status="semantic",
        source_sha256="0" * 64,
    )


def _codes(code: str) -> list:
    finding = lint_target(_target(code))
    return finding.codes if finding else []


@pytest.mark.parametrize(
    "code, expected",
    [
        ("x" * 101, "ERR_LIN"),
        ("theorem foo :\r", "ERR_WIN"),
        ("theorem foo := by  ", "ERR_TWS"),
        ("simp ; ring", "ERR_SEM"),
        ("theorem foo", "ERR_NSP"),
        ("-- adaptation note: this is temporary", "ERR_ADN"),
        ("theorem foo : True :=\n  by\n  trivial", "ERR_IBY"),
        ("theorem foo : True :=\n  by trivial", "ERR_IBY"),
        ("def foo : Nat :=\n  where\n  bar := 1", "ERR_IWH"),
        ("theorem foo\n    : True := trivial", "ERR_CLN"),
        ("rw [←foo]", "ERR_ARR"),
        ("exact fun x => λ y => y", "ERR_LAM"),
    ],
)
def test_rule_fires(code, expected):
    assert expected in _codes(code)


@pytest.mark.parametrize(
    "code, forbidden",
    [
        # Exactly at the limit is fine; the linter warns *above* 100.
        ("x" * 100, "ERR_LIN"),
        ("theorem foo := by trivial", "ERR_TWS"),
        ("simp; ring", "ERR_SEM"),
        ("theorem foo : True := trivial", "ERR_NSP"),
        # Hanging `by` after a comma is explicitly excused by Mathlib's linter.
        ("refine ⟨foo,\n  by simp⟩", "ERR_IBY"),
        # As is `by` on its own line after `, fun x =>`.
        ("exact ⟨1, fun x =>\n  by\n  simp⟩", "ERR_IBY"),
        # `←%` and ``←` `` are permitted; only `←`(` is not.
        ("rw [←% foo]", "ERR_ARR"),
        ("exact ← `bar", "ERR_ARR"),
        ("theorem foo :\n    True := trivial", "ERR_CLN"),
    ],
)
def test_rule_silent(code, forbidden):
    assert forbidden not in _codes(code)


def test_arrow_fires_on_antiquotation_paren():
    """Mathlib excuses `←` before a backtick, but not before `` `( `` or ``` ``( ```."""
    assert "ERR_ARR" in _codes("exact ←`(foo)")
    assert "ERR_ARR" in _codes("exact ←``(foo)")


def test_isolated_by_excused_after_a_long_previous_line():
    """`by ` after `:=` is only reported when the previous line can absorb it (≤97 chars)."""
    long_line = "theorem foo " + "x" * 90 + " :="
    assert len(long_line) > 97
    assert "ERR_IBY" not in _codes(long_line + "\n  by simp")


def test_clean_code_produces_no_finding():
    code = "theorem foo (h : p) : p := by\n  exact h\n"
    assert lint_target(_target(code)) is None


def test_only_reviewed_code_is_examined():
    """A violation living only in the base is not this review's finding."""
    assert lint_target(_target("", base="x" * 200)) is None


def test_long_line_view_is_a_subset():
    code = "x" * 101 + "  \n"
    full = lint_target(_target(code))
    narrow = find_long_lines(_target(code))
    assert set(full.codes) == {"ERR_LIN", "ERR_TWS"}
    assert narrow.codes == ["ERR_LIN"]


def test_observed_pattern_names_rules_and_lines():
    pattern = lint_target(_target("x" * 101 + "\nsimp ; ring")).observed_pattern()
    assert "ERR_LIN" in pattern and "ERR_SEM" in pattern
    assert "line 1" in pattern and "line 2" in pattern


def test_forbidden_construct_requires_introduction():
    added = _target("axiom foo : True", kind="axiom")
    assert find_forbidden_construct(added).construct == "axiom"
    moved = _target("axiom foo : True", base="axiom foo : True", kind="axiom")
    assert find_forbidden_construct(moved) is None


def test_sorry_detection_ignores_identifier_substrings():
    assert find_forbidden_construct(_target("theorem foo := sorry")).construct == "sorry"
    assert find_forbidden_construct(_target("def sorryAx' := 1")) is None
