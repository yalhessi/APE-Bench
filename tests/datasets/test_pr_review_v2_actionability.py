"""Tests for the gold-quality actionability re-audit (apply logic, no network)."""

from src.datasets.pr_review_v2.actionability import apply_actionability


def _rec(pr, comments):
    return {"pr_number": pr, "gold": {"verdict": "CHANGES_REQUESTED", "comments": comments}}


def test_apply_reclassifies_non_actionable_to_P():
    records = [_rec(7, [
        {"id": "a", "stratum": "V2", "body": "golf this proof"},
        {"id": "b", "stratum": "V4", "body": "I like this the best"},   # approval
        {"id": "c", "stratum": "V2", "body": "Same here"},              # pointer
        {"id": "d", "stratum": "P", "body": "bors merge"},              # already non-finding
    ])]
    sidecar = [
        {"pr_number": 7, "comment_id": "a", "verdict": "ACTIONABLE", "reason": "golf"},
        {"pr_number": 7, "comment_id": "b", "verdict": "APPROVAL", "reason": "praise"},
        {"pr_number": 7, "comment_id": "c", "verdict": "POINTER", "reason": "content-free"},
    ]
    stats = apply_actionability(records, sidecar)
    assert stats["finding_comments_seen"] == 3  # a, b, c (d is already P)
    assert stats["reclassified_to_P"] == 2
    assert stats["by_category"] == {"APPROVAL": 1, "POINTER": 1}
    assert stats["remaining_findings"] == 1

    comments = {c["id"]: c for c in records[0]["gold"]["comments"]}
    assert comments["a"]["stratum"] == "V2"                       # actionable kept
    assert comments["b"]["stratum"] == "P" and comments["b"]["orig_stratum"] == "V4"
    assert comments["c"]["stratum"] == "P" and comments["c"]["actionability"] == "POINTER"
    assert comments["d"]["stratum"] == "P"                        # untouched


def test_apply_is_noop_without_sidecar_entries():
    records = [_rec(7, [{"id": "a", "stratum": "V3", "body": "rename this"}])]
    stats = apply_actionability(records, [])
    assert stats["reclassified_to_P"] == 0
    assert records[0]["gold"]["comments"][0]["stratum"] == "V3"
