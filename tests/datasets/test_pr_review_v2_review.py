"""Tests for the composed (decomposed) review aggregation — no network."""

from src.datasets.pr_review_v2.predictions import (
    PredictedAnchor,
    PredictedFinding,
    PredictionRecord,
)
from src.datasets.pr_review_v2.review import _split_task_id, aggregate_pr


def _rec(pr, findings, confidence=None, parse_ok=True, parse_error=None):
    return PredictionRecord(
        pr_number=pr, model="m", mode="workspace", confidence=confidence,
        findings=findings, parse_ok=parse_ok, parse_error=parse_error,
    )


def _f(path, line, claim, severity="blocking", verified=True):
    return PredictedFinding(
        anchor=PredictedAnchor(path=path, line_start=line) if path else None,
        severity=severity, claim=claim, verified=verified,
    )


def test_split_task_id():
    assert _split_task_id("lean_pr_review_golf_33440") == ("lean_pr_review_golf", 33440)
    assert _split_task_id("bad") == (None, None)


def test_aggregate_unions_and_tags_source():
    preds = [
        ("golf", _rec(7, [_f("A.lean", 10, "shorten this proof")], confidence=0.8)),
        ("dup", _rec(7, [_f("A.lean", 20, "duplicates B")], confidence=0.6)),
        ("gen", _rec(7, [], confidence=0.9)),
    ]
    out = aggregate_pr(7, preds, "m")
    assert out.parse_ok and out.pr_number == 7
    assert len(out.findings) == 2
    assert {f.source for f in out.findings} == {"golf", "dup"}
    assert out.merge_ready_as_is is False  # findings present
    assert out.confidence == 0.6  # min across checkers


def test_aggregate_dedup_merges_sources():
    # two checkers flag the same location+claim -> one finding, both sources
    preds = [
        ("golf", _rec(7, [_f("A.lean", 10, "this proof is non-idiomatic")])),
        ("gen", _rec(7, [_f("A.lean", 10, "this proof is non-idiomatic")])),
    ]
    out = aggregate_pr(7, preds, "m")
    assert len(out.findings) == 1
    assert set(out.findings[0].source.split("+")) == {"golf", "gen"}


def test_aggregate_empty_is_merge_ready():
    out = aggregate_pr(7, [("golf", _rec(7, [])), ("dup", _rec(7, []))], "m")
    assert out.merge_ready_as_is is True and out.findings == []


def test_aggregate_all_failed_is_parse_error():
    preds = [("golf", _rec(7, [], parse_ok=False, parse_error="setup failed")),
             ("dup", _rec(7, [], parse_ok=False, parse_error="setup failed"))]
    out = aggregate_pr(7, preds, "m")
    assert out.parse_ok is False and "all checkers failed" in out.parse_error
