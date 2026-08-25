"""Offline tests for the Phase-B two-level judge + tiered evaluator (pr_review_v3)."""

from src.datasets.legacy.pr_review_v3.judge import parse_verdict
from src.datasets.legacy.pr_review_v3.evaluate_tiers import (co_located, _select_top_k, tier_metrics,
                                                      build_pairs, filter_evaluable)


def test_filter_evaluable_excludes_out_of_run_prs():
    ivs = [{"intervention_id": "a", "pr_number": 1}, {"intervention_id": "b", "pr_number": 2}]
    inrun, excluded = filter_evaluable(ivs, {1: {"pr_number": 1, "findings": []}})
    assert [x["intervention_id"] for x in inrun] == ["a"]
    assert [x["intervention_id"] for x in excluded] == ["b"]


def test_parse_verdict_enforces_resolution_implies_issue():
    i, r, _ = parse_verdict('{"issue_match": false, "resolution_match": true, "reason": "x"}')
    assert (i, r) == (False, False)  # resolution without issue is coerced off
    i, r, _ = parse_verdict('{"issue_match": true, "resolution_match": true, "reason": "x"}')
    assert (i, r) == (True, True)
    i, r, reason = parse_verdict("not json at all")
    assert (i, r) == (False, False) and "unparseable" in reason


def _iv(iid="pr1_i01", pr=1, anchors=None, outcome="adopted", stratum="V2"):
    return {"intervention_id": iid, "pr_number": pr, "stratum": stratum, "outcome": outcome,
            "concern": "naming", "canonical_ask": "rename a to b", "judgeable": True,
            "anchors": anchors if anchors is not None else
            [{"path": "Mathlib/A.lean", "line_start": 10, "line_end": 20, "hunk_id": "h"}]}


def _finding(path="target/Mathlib/A.lean", ls=12, conf=None, claim="c"):
    return {"anchor": {"path": path, "line_start": ls, "line_end": ls}, "claim": claim,
            "severity": "advisory", "confidence": conf}


def test_co_located_any_anchor_with_slack_and_path_norm():
    iv = _iv()
    hit, gap = co_located(iv, _finding(ls=25), slack=10)   # 5 over line_end, within slack
    assert hit and gap == "5"
    hit, _ = co_located(iv, _finding(ls=45), slack=10)     # 25 past end
    assert not hit
    hit, _ = co_located(iv, _finding(path="target/Mathlib/B.lean"), slack=10)
    assert not hit
    hit, gap = co_located(_iv(anchors=[]), _finding(), slack=10)  # unanchored => PR-level
    assert hit and "unanchored" in gap


def test_top_k_selection_prefers_confidence_then_order():
    fs = [_finding(conf=None), _finding(conf=0.9), _finding(conf=0.2), _finding(conf=0.9)]
    assert _select_top_k(fs, 2) == [1, 3]          # ties keep order; None sorts last
    assert _select_top_k(fs, 4) == [1, 3, 2, 0]


def test_tier_metrics_counts_t1_t2_t3():
    iv1, iv2 = _iv("pr1_i01"), _iv("pr1_i02", anchors=[
        {"path": "Mathlib/A.lean", "line_start": 100, "line_end": 110, "hunk_id": "h2"}])
    f_hit = _finding(ls=12, conf=0.9, claim="rename a to b")
    f_low = _finding(ls=105, conf=0.1, claim="something else")
    preds = {1: {"pr_number": 1, "findings": [f_hit, f_low]}}
    pairs = build_pairs([iv1, iv2], preds, slack=10)
    assert len(pairs) == 2
    for p in pairs:  # simulate judge: only the iv1/f_hit pair issue+resolution matches
        p["issue_match"] = p["iv"] is iv1
        p["resolution_match"] = p["iv"] is iv1
    rep = tier_metrics([iv1, iv2], preds, pairs, k=1)
    assert rep["overall"]["n"] == 2
    assert rep["overall"]["T1_identified"].startswith("2/2")
    assert rep["overall"]["T2_issue"].startswith("1/2")
    assert rep["overall"]["T2_resolution"].startswith("1/2")
    # top-1 selects f_hit (conf 0.9) -> iv1 covered at k, iv2 not
    assert rep["overall"]["T3_issue_at_top1"].startswith("1/2")
    assert rep["T3_precision_at_top1"].startswith("1/1")
