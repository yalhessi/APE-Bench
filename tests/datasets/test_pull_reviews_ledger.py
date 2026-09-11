"""The A→B ledger pairs each reviewer suggestion with exactly the code it replaces."""

from __future__ import annotations

import pytest

from src.datasets.pull_reviews.projections.ledger import commented_lines, leading_token, ledger_rows


def _row(cid, body, hunk, *, is_reviewer=True, author=False, **positions):
    return {"comment_id": cid, "pr_number": 1, "created_at": "2025-12-10T00:00:00Z", "commenter": "rev",
            "reviewer_basis": "roster", "path": "Mathlib/A.lean", "body": body, "diff_hunk": hunk,
            "is_reviewer": is_reviewer, "commenter_is_author": author, "html_url": "u", **positions}


HUNK = ("@@ -10,3 +10,5 @@ theorem tanh_lt_one (x : ℝ) : tanh x < 1 := by\n"
        " theorem tanh_lt_one (x : ℝ) : tanh x < 1 := by\n"
        "   rw [tanh_eq]\n"
        "-  nlinarith\n"
        "+  have := exp_pos x\n"
        "+  positivity")


def test_a_single_line_suggestion_pairs_the_tail_with_the_block():
    (row,) = ledger_rows([_row(1, "```suggestion\n  grind [exp_pos]\n```", HUNK,
                               original_line=14, original_position=5, side="RIGHT")])
    assert row["a_lines"] == ["  positivity"] and row["a_span"] == "single"
    assert row["b_lines"] == ["  grind [exp_pos]"]
    assert row["transformation"] == "positivity -> grind"
    assert row["declaration"] == "tanh_lt_one" and row["resolved_via"] == "line"


def test_a_multi_line_range_walks_back_on_the_comments_side_only():
    lines, span = commented_lines(_row(2, "", HUNK, original_start_line=13, original_line=14,
                                       original_position=5, side="RIGHT"))
    assert span == "range"
    assert lines == ["  have := exp_pos x", "  positivity"]     # the removed `nlinarith` is skipped


def test_rows_without_positions_take_the_tail_and_say_so():
    (row,) = ledger_rows([_row(3, "```suggestion\n  simp\n```", HUNK)])
    assert row["a_span"] == "tail_only" and row["a_lines"] == ["  positivity"]


def test_only_reviewer_view_rows_with_a_block_enter():
    rows = [_row(4, "please golf", HUNK),                                   # prose, no block
            _row(5, "```suggestion\n  grind\n```", HUNK, is_reviewer=False),  # not a reviewer
            _row(6, "```suggestion\n  grind\n```", HUNK, author=True, is_reviewer=False)]
    assert ledger_rows(rows) == []


def test_a_deletion_suggestion_is_recorded_as_deleted():
    (row,) = ledger_rows([_row(7, "```suggestion\n```", HUNK)])
    assert row["b_lines"] == [] and row["transformation"] == "positivity -> (deleted)"


@pytest.mark.parametrize("line,token", [("  · exact h", "exact"), ("@[simp] theorem", "@["),
                                        ("  simp only [foo]", "simp"), ("  by_cases! h : x", "by_cases!")])
def test_leading_tokens(line, token):
    assert leading_token(line) == token
