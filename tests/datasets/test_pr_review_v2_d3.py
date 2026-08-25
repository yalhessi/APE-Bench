"""Unit tests for D3 localization geometry (no network, no LLM)."""

from src.datasets.pr_review_v2.evaluate_d3 import (
    diff_new_side_spans,
    evaluate_pr,
    removed_spans,
)


def test_removed_spans_only_uses_removed_op():
    hunks = [
        {"op": "removed_in_revision", "path": "A.lean", "new_start": 10, "new_lines": 3},
        {"op": "added_in_revision", "path": "A.lean", "new_start": 50, "new_lines": 4},
    ]
    assert removed_spans(hunks) == {"A.lean": [(10, 12)]}


def test_diff_new_side_spans_parses_assembled_diff():
    diff = (
        "diff --git a/Mathlib/A.lean b/Mathlib/A.lean\n"
        "--- a/Mathlib/A.lean\n"
        "+++ b/Mathlib/A.lean\n"
        "@@ -5,2 +5,3 @@ theorem foo\n"
        " ctx\n+added\n ctx2\n"
    )
    assert diff_new_side_spans(diff) == {"Mathlib/A.lean": [(5, 7)]}


def _record(delta_near, delta_total, diff="", h0="review_commit_id", verdict="CHANGES_REQUESTED"):
    return {
        "input": {"diff": diff, "h0_resolution": h0},
        "gold": {"verdict": verdict, "delta_near": delta_near, "delta_total": delta_total},
    }


def _pred(findings, pr_number=1):
    return {"pr_number": pr_number, "parse_ok": True, "findings": findings}


def _finding(path, start, end=None, severity="blocking"):
    return {"anchor": {"path": path, "line_start": start, "line_end": end},
            "severity": severity, "claim": "x"}


class TestEvaluatePr:
    def test_hit_and_recall(self):
        near = [{"op": "removed_in_revision", "path": "A.lean", "new_start": 20, "new_lines": 5}]
        record = _record(near, near)
        pred = _pred([_finding("A.lean", 22)])  # 22 ∈ [20,24]
        out = evaluate_pr(record, pred, target="near")
        assert out["hits"] == 1
        assert out["gold_covered"] == 1 and out["gold_removed_spans"] == 1

    def test_control_fp_on_untouched_diff_line(self):
        near = [{"op": "removed_in_revision", "path": "A.lean", "new_start": 20, "new_lines": 2}]
        # δ₀ touches lines 5-30; merge only changed 20-21, so a finding at line 8 is on
        # untouched-but-in-PR code → control false positive.
        diff = (
            "diff --git a/A.lean b/A.lean\n--- a/A.lean\n+++ b/A.lean\n"
            "@@ -5,25 +5,26 @@\n" + " ctx\n" * 26
        )
        record = _record(near, near, diff=diff)
        pred = _pred([_finding("A.lean", 8)])
        out = evaluate_pr(record, pred, target="near")
        assert out["hits"] == 0
        assert out["control_fp"] == 1 and out["off_diff"] == 0

    def test_off_diff_when_anchor_outside_pr(self):
        near = [{"op": "removed_in_revision", "path": "A.lean", "new_start": 20, "new_lines": 2}]
        record = _record(near, near, diff="")  # no δ₀ spans known
        pred = _pred([_finding("A.lean", 999)])
        out = evaluate_pr(record, pred, target="near")
        assert out["off_diff"] == 1 and out["control_fp"] == 0

    def test_unlocalized_findings_counted_separately(self):
        near = [{"op": "removed_in_revision", "path": "A.lean", "new_start": 20, "new_lines": 2}]
        record = _record(near, near)
        pred = _pred([
            {"anchor": None, "severity": "advisory", "claim": "PR-level"},
            {"anchor": {"path": "A.lean", "line_start": None}, "severity": "advisory", "claim": "file"},
        ])
        out = evaluate_pr(record, pred, target="near")
        assert out["pr_level"] == 1 and out["file_only"] == 1 and out["line_anchored"] == 0

    def test_control_pr_flagged(self):
        record = _record([], [], verdict="APPROVED")
        pred = _pred([_finding("A.lean", 5)])
        out = evaluate_pr(record, pred, target="near")
        assert out["is_control_pr"] is True and out["gold_removed_spans"] == 0
