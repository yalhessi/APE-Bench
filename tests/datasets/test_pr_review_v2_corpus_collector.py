"""The review-comment collector walks shallow, says how far it is, and can be resumed.

A 21-month window is ~2,000 pages of `/pulls/comments`; GitHub answers 5xx once a `next`-link
chain runs deep, and the user's run died there with a log that said only "scanned 500". The
walk is now re-anchored on `since` every few pages, progress is the share of the date window
reached, and a state file records the frontier after every page.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import pytest

from src.datasets.pr_review_v2 import corpus


def _comment(i: int, created: str, *, login="maintainer", assoc="MEMBER", path="Mathlib/A.lean",
             body="please use dot notation here") -> Dict[str, Any]:
    return {
        "id": i, "created_at": created, "updated_at": created,
        "pull_request_url": f"https://api.github.com/repos/leanprover-community/mathlib4/pulls/{1000 + i % 7}",
        "path": path, "diff_hunk": "@@ -1,2 +1,2 @@\n theorem foo : True := by\n-  simp\n+  trivial",
        "body": body, "user": {"login": login}, "author_association": assoc,
        "line": 3, "original_line": 3, "original_position": 3, "side": "RIGHT", "subject_type": "line",
        "html_url": "https://github.com/x", "commit_id": "abc", "in_reply_to_id": None,
    }


class FakeClient:
    """Serves a created-ascending list of comments 100 per page, honouring `since` on updated_at
    like GitHub does, and records every `since` it was asked for."""

    authenticated = True

    def __init__(self, comments: List[Dict[str, Any]], *, per_page: int = 100):
        self.comments = comments
        self.per_page = per_page
        self.anchors: List[str] = []
        self.requests = 0

    def pages(self, path, *, params=None, per_page=100, max_pages=None):
        since = (params or {}).get("since")
        self.anchors.append(since)
        rows = [c for c in self.comments if c["updated_at"] >= since]
        for offset in range(0, len(rows), self.per_page):
            if max_pages is not None and offset // self.per_page >= max_pages:
                return
            self.requests += 1
            yield rows[offset:offset + self.per_page]

    def close(self):
        pass


def _run(tmp_path, comments, **kw):
    out = tmp_path / "corpus.jsonl"
    client = FakeClient(comments, per_page=kw.pop("per_page", 100))
    logger = logging.getLogger("collector-test")
    kept = corpus.build_corpus(kw.pop("start", "2025-09-01"), kw.pop("end", "2025-09-30"), out,
                               exclude_prs=set(), max_pages=kw.pop("max_pages", 10_000),
                               logger=logger, client=client, **kw)
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    return kept, rows, client, out


def test_the_walk_is_reanchored_instead_of_following_a_deep_chain(tmp_path):
    comments = [_comment(i, f"2025-09-{1 + i // 40:02d}T{(i % 40) // 2:02d}:{(i % 2) * 30:02d}:00Z")
                for i in range(1000)]           # 25 days, 1000 comments, 10 pages of 100
    kept, rows, client, _ = _run(tmp_path, comments, reanchor_every_pages=3)
    assert kept == 1000 and len(rows) == 1000
    assert len({r["comment_id"] for r in rows}) == 1000
    # Chains were cut at three pages and restarted from the last created_at seen.
    assert len(client.anchors) >= 4
    assert client.anchors[0] == "2025-09-01T00:00:00Z"
    assert all(a < b for a, b in zip(client.anchors, client.anchors[1:]))
    assert client.anchors[1] == comments[299]["created_at"]


def test_comments_created_in_the_anchors_own_second_are_not_duplicated(tmp_path):
    same_second = [_comment(i, "2025-09-10T10:00:00Z") for i in range(250)]
    later = [_comment(1000 + i, "2025-09-11T10:00:00Z") for i in range(50)]
    kept, rows, client, _ = _run(tmp_path, same_second + later, reanchor_every_pages=1)
    assert kept == 300
    assert len({r["comment_id"] for r in rows}) == 300


def test_the_walk_stops_at_the_first_comment_after_the_window(tmp_path):
    inside = [_comment(i, "2025-09-15T00:00:00Z") for i in range(30)]
    outside = [_comment(100 + i, "2025-10-01T00:00:00Z") for i in range(30)]
    kept, rows, client, _ = _run(tmp_path, inside + outside)
    assert kept == 30
    assert client.requests == 1


def test_a_chain_of_only_prewindow_comments_is_followed_not_reanchored(tmp_path):
    """Old comments edited recently sort first (created-ascending, `since` on updated_at). If the
    first pages are all of them, the frontier has not moved, and a re-anchor at the same `since`
    would loop forever; the chain is followed instead."""

    old = [dict(_comment(i, "2024-01-01T00:00:00Z"), updated_at="2025-09-05T00:00:00Z")
           for i in range(500)]
    new = [_comment(1000 + i, "2025-09-20T00:00:00Z") for i in range(10)]
    kept, rows, client, _ = _run(tmp_path, old + new, reanchor_every_pages=2)
    assert kept == 10
    # The first chain ran past the two-page mark without a re-anchor (the frontier had not
    # moved); once it reached the new comments a re-anchor followed, and no anchor repeats.
    assert client.anchors[0] == "2025-09-01T00:00:00Z"
    assert len(client.anchors) == len(set(client.anchors))
    assert client.requests <= 8


def test_only_maintainer_lean_comments_are_kept_and_reruns_add_nothing(tmp_path):
    comments = [
        _comment(1, "2025-09-02T00:00:00Z"),
        _comment(2, "2025-09-02T00:00:00Z", assoc="CONTRIBUTOR"),
        _comment(3, "2025-09-02T00:00:00Z", path="docs/README.md"),
        _comment(4, "2025-09-02T00:00:00Z", body="Thanks!"),
    ]
    kept, rows, client, out = _run(tmp_path, comments)
    assert kept == 1 and [r["comment_id"] for r in rows] == [1]
    assert rows[0]["original_position"] == 3
    client2 = FakeClient(comments)
    again = corpus.build_corpus("2025-09-01", "2025-09-30", out, exclude_prs=set(), max_pages=100,
                                logger=logging.getLogger("t"), client=client2)
    assert again == 0
    assert len(out.read_text().splitlines()) == 1


def test_the_log_says_how_far_through_the_window_the_walk_is(tmp_path, caplog):
    comments = [_comment(i, f"2025-09-{1 + i // 10:02d}T00:00:00Z") for i in range(300)]
    with caplog.at_level(logging.INFO, logger="collector-test"):
        _run(tmp_path, comments, per_page=50, log_every_pages=2)
    text = caplog.text
    assert "PLAN  window 2025-09-01..2025-09-30" in text
    assert "% of window" in text
    assert "pages left" in text
    assert "DONE" in text


def test_the_state_file_records_the_frontier_for_a_resume(tmp_path):
    comments = [_comment(i, f"2025-09-{1 + i // 10:02d}T00:00:00Z") for i in range(300)]
    _, _, _, out = _run(tmp_path, comments)
    state = json.loads(corpus._state_path(out).read_text())
    assert state["done"] is True
    assert state["frontier_created_at"] == comments[-1]["created_at"]
    assert state["resume_hint"] == "--start 2025-09-30 --end 2025-09-30"


def test_max_pages_stops_the_walk_and_says_how_to_resume(tmp_path, caplog):
    comments = [_comment(i, f"2025-09-{1 + i // 40:02d}T00:00:00Z") for i in range(1000)]
    with caplog.at_level(logging.WARNING, logger="collector-test"):
        kept, rows, client, out = _run(tmp_path, comments, max_pages=3)
    assert client.requests == 3 and kept == 300
    assert "resume with --start 2025-09-08" in caplog.text
