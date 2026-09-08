"""Tests for the D2 path-prefix fix and the target-coverage evaluator."""

from src.datasets.pr_review_v2.evaluate_d2 import (
    MatcherConfig,
    norm_path,
    candidate_pairs,
    evaluate_target,
)


def test_norm_path_strips_workspace_and_diff_prefixes():
    canon = "Mathlib/A.lean"
    for p in ("target/Mathlib/A.lean", "b/Mathlib/A.lean", "a/Mathlib/A.lean",
              "./Mathlib/A.lean", "/Mathlib/A.lean", "target/target/Mathlib/A.lean", canon):
        assert norm_path(p) == canon


def test_candidate_pairs_match_across_target_prefix():
    # the bug: gold path is repo-relative, pred path has the target/ workspace prefix
    gold = [{"anchor": {"path": "Mathlib/A.lean", "line": 100}, "stratum": "V2"}]
    pred = [{"anchor": {"path": "target/Mathlib/A.lean", "line_start": 102, "line_end": 102}}]
    pairs = candidate_pairs(gold, pred, line_slack=10, include_loose=False)
    assert any(p["tier"] == "anchor" for p in pairs), "path normalization should let them match"


def _rec(pr, comments):
    return {"pr_number": pr, "gold": {"verdict": "CHANGES_REQUESTED", "comments": comments}}


def test_evaluate_target_location_coverage_and_off_target():
    gold = {7: _rec(7, [
        {"id": "g1", "kind": "inline", "stratum": "V2", "anchor": {"path": "Mathlib/A.lean", "line": 100}},
        {"id": "g2", "kind": "inline", "stratum": "V2", "anchor": {"path": "Mathlib/A.lean", "line": 400}},
    ])}
    preds = [{
        "pr_number": 7, "parse_ok": True, "findings": [
            {"anchor": {"path": "target/Mathlib/A.lean", "line_start": 103}, "verified": True},  # covers g1
            {"anchor": {"path": "Mathlib/A.lean", "line_start": 999}, "verified": True},          # off-target
        ],
    }]
    cfg = MatcherConfig(gold="x", predictions="y", mode="target", line_slack=15, verified_only=True)
    r = evaluate_target(gold, preds, cfg, logger=None)
    assert r["recall_by_stratum"]["V2"] == {"gold": 2, "covered": 1, "recall": 0.5}
    assert r["on_target_predictions"] == 1
    assert r["off_target_predictions"] == 1  # the selectivity candidate


def test_evaluate_target_verified_only_filters_unverified():
    gold = {7: _rec(7, [{"id": "g1", "kind": "inline", "stratum": "V2",
                          "anchor": {"path": "Mathlib/A.lean", "line": 100}}])}
    preds = [{"pr_number": 7, "parse_ok": True, "findings": [
        {"anchor": {"path": "Mathlib/A.lean", "line_start": 100}, "verified": None},  # unverified -> ignored
    ]}]
    cfg = MatcherConfig(gold="x", predictions="y", mode="target", verified_only=True)
    r = evaluate_target(gold, preds, cfg, logger=None)
    assert r["gold_covered"] == 0 and r["anchored_predictions"] == 0


def _gold_pred_coincidental():
    # gold = a doc concern; pred = a golf at the same line (coincidental co-location)
    gold = {7: _rec(7, [{"id": "g1", "kind": "inline", "stratum": "V2", "body": "fix this docstring",
                         "anchor": {"path": "Mathlib/A.lean", "line": 100}}])}
    preds = [{"pr_number": 7, "parse_ok": True, "findings": [
        {"anchor": {"path": "target/Mathlib/A.lean", "line_start": 101}, "claim": "this proof can be golfed"},
    ]}]
    return gold, preds


def test_topical_gate_rejects_coincidental_colocation(monkeypatch):
    import src.datasets.pr_review_v2.evaluate_d2 as ev

    async def fake_judge(work, config, logger):  # the MATCH_PROMPT judge says "different concern"
        for item in work:
            item["pair"]["accept"] = False

    monkeypatch.setattr(ev, "judge_pairs_llm", fake_judge)
    gold, preds = _gold_pred_coincidental()
    cfg = ev.MatcherConfig(gold="x", predictions="y", mode="target", topical_gate=True)
    r = ev.evaluate_target(gold, preds, cfg, logger=None)
    # location matches, but the topical gate rejects -> not covered
    assert r["topical_gate"] is True
    assert r["gold_covered"] == 0 and r["on_target_predictions"] == 0


def test_topical_gate_keeps_same_concern(monkeypatch):
    import src.datasets.pr_review_v2.evaluate_d2 as ev

    async def fake_judge(work, config, logger):
        for item in work:
            item["pair"]["accept"] = True  # same concern

    monkeypatch.setattr(ev, "judge_pairs_llm", fake_judge)
    gold, preds = _gold_pred_coincidental()
    cfg = ev.MatcherConfig(gold="x", predictions="y", mode="target", topical_gate=True)
    r = ev.evaluate_target(gold, preds, cfg, logger=None)
    assert r["gold_covered"] == 1 and r["on_target_predictions"] == 1


def test_no_gate_is_pure_location(monkeypatch):
    import src.datasets.pr_review_v2.evaluate_d2 as ev
    # if the gate were on it would call the judge; off => must NOT call it
    called = {"n": 0}

    async def fake_judge(work, config, logger):
        called["n"] += 1

    monkeypatch.setattr(ev, "judge_pairs_llm", fake_judge)
    gold, preds = _gold_pred_coincidental()
    cfg = ev.MatcherConfig(gold="x", predictions="y", mode="target", topical_gate=False)
    r = ev.evaluate_target(gold, preds, cfg, logger=None)
    assert called["n"] == 0
    assert r["gold_covered"] == 1  # pure location counts the coincidental hit
