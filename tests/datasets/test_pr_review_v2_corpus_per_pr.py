"""The per-PR collection route: complete for the window, shallow, resumable, with a real
denominator in its progress line.

The repo-level listing endpoint now answers HTTP 500 on its first page for `since` windows on
mathlib4 (the user's September run made zero successful requests), so the corpus is collected
PR by PR: search the PRs that can carry a comment in the window, read each one's comments.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from src.datasets.pr_review_v2 import corpus


def _pr(number: int, created: str, updated: str) -> Dict[str, Any]:
    return {"number": number, "created_at": created + "T00:00:00Z", "updated_at": updated + "T00:00:00Z"}


def _comment(i: int, pr: int, created: str, *, assoc="MEMBER", path="Mathlib/A.lean") -> Dict[str, Any]:
    return {
        "id": i, "created_at": created + "T12:00:00Z",
        "pull_request_url": f"https://api.github.com/repos/leanprover-community/mathlib4/pulls/{pr}",
        "path": path, "diff_hunk": "@@ -1,2 +1,2 @@\n theorem foo : True := by\n-  simp\n+  trivial",
        "body": "please use dot notation here", "user": {"login": "maintainer"},
        "author_association": assoc, "line": 3, "original_line": 3, "original_position": 3,
        "side": "RIGHT", "subject_type": "line", "html_url": "https://github.com/x",
        "commit_id": "abc", "in_reply_to_id": None,
    }


class FakeGitHub:
    """Answers `/search/issues` from a PR list (honouring created:lo..hi and updated:>=x) and
    `/pulls/{n}/comments` from a comment list. Records every request."""

    authenticated = True

    def __init__(self, prs, comments, *, cap_override=None, bump_after=None, bump_pr=None):
        self.prs, self.comments = prs, comments
        self.cap_override = cap_override      # {(lo, hi): total_count} to simulate the cap
        self.bump_after = bump_after          # page index after which `bump_pr` jumps to the top
        self.bump_pr = bump_pr
        self.requests: List[str] = []

    def _search(self, q: str):
        import re
        lo, hi = re.search(r"created:(\S+)\.\.(\S+)", q).groups()
        since = re.search(r"updated:>=(\S+)", q).group(1)
        hits = [p for p in self.prs if lo <= p["created_at"][:10] <= hi and p["updated_at"][:10] >= since]
        total = self.cap_override.get((lo, hi), len(hits)) if self.cap_override else len(hits)
        return hits, total

    def get_json(self, path, *, params=None):
        self.requests.append(path)
        hits, total = self._search(params["q"])
        return {"total_count": total, "items": hits[:100]}

    def pages(self, path, *, params=None, per_page=100, max_pages=None):
        if path.endswith("/pulls"):                      # the core listing, updated desc
            rows = sorted(self.prs, key=lambda p: p["updated_at"], reverse=True)
            for index, offset in enumerate(range(0, len(rows), 100)):
                if max_pages is not None and index >= max_pages:
                    return
                self.requests.append(path)
                yield rows[offset:offset + 100]
                if self.bump_after and index + 1 == self.bump_after:
                    # A PR is updated mid-walk and jumps to the top of the list.
                    for row in self.prs:
                        if row["number"] == self.bump_pr:
                            row["updated_at"] = "2026-09-11T00:00:00Z"
                    rows = sorted(self.prs, key=lambda p: p["updated_at"], reverse=True)
            return
        if path == "/search/issues":
            hits, _ = self._search(params["q"])
            start = (params.get("page", 1) - 1) * 100
            for offset in range(start, len(hits), 100):
                self.requests.append(path)
                yield hits[offset:offset + 100]
            return
        number = int(path.split("/pulls/")[1].split("/")[0])
        rows = [c for c in self.comments if c["pull_request_url"].endswith(f"/{number}")]
        self.requests.append(path)
        yield rows

    def close(self):
        pass


def _run(tmp_path, prs, comments, *, start="2025-12-01", end="2025-12-31", exclude=(), **kw):
    out = tmp_path / "corpus.jsonl"
    client = kw.pop("client", None) or FakeGitHub(prs, comments)
    kept = corpus.build_corpus_per_pr(start, end, out, exclude_prs=set(exclude),
                                      logger=logging.getLogger("per-pr-test"), client=client, **kw)
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    return kept, rows, client, out


def test_every_pr_that_can_carry_a_comment_in_the_window_is_read():
    """Created on or before the window's end and updated on or after its start -- including a
    PR opened months earlier and one still being edited in January."""

    prs = [
        _pr(1, "2025-12-05", "2025-12-20"),   # inside
        _pr(2, "2025-06-01", "2026-01-15"),   # old, still active: has a December comment
        _pr(3, "2025-11-20", "2025-11-28"),   # went quiet before the window
        _pr(4, "2026-01-02", "2026-01-03"),   # opened after the window
    ]
    comments = [_comment(10, 1, "2025-12-06"), _comment(11, 2, "2025-12-10"),
                _comment(12, 2, "2026-01-10"), _comment(13, 3, "2025-11-25")]
    import tempfile, pathlib
    kept, rows, client, _ = _run(pathlib.Path(tempfile.mkdtemp()), prs, comments, stage_a="search")
    assert sorted(r["comment_id"] for r in rows) == [10, 11]     # 12 and 13 are outside the window
    read = sorted(int(p.split("/pulls/")[1].split("/")[0]) for p in client.requests if "/pulls/" in p)
    assert read == [1, 2]


def test_the_listing_route_walks_until_the_window_and_no_further(tmp_path):
    """The default stage A. `/repos/{repo}/pulls?sort=updated&direction=desc` is on the 5,000/hour
    core bucket; the search API allows 30 requests a minute, which is what stopped the first
    attempt after 27 of them. The walk stops at the first page that has fallen below the window."""

    prs = ([_pr(i, "2025-12-05", f"2026-0{1 + i // 60}-{1 + i % 27:02d}") for i in range(1, 120)]
           + [_pr(500, "2025-06-01", "2025-12-20"),      # old PR, active in the window
              _pr(501, "2025-11-20", "2025-11-28"),      # fell quiet before the window
              _pr(502, "2026-02-02", "2026-03-03")])     # opened after the window
    kept, rows, client, _ = _run(tmp_path, prs, [_comment(10, 500, "2025-12-20")])
    assert [r["comment_id"] for r in rows] == [10]
    read = {int(p.split("/pulls/")[1].split("/")[0]) for p in client.requests if "/pulls/" in p and p.endswith("/comments")}
    assert 500 in read and 501 not in read and 502 not in read
    assert not any(p == "/search/issues" for p in client.requests)


def test_a_pr_bumped_past_the_cursor_mid_walk_is_caught_by_the_recheck(tmp_path):
    """An update moves a PR *up* the list, so one below the cursor can jump above it and be
    stepped over. The first pages are read again at the end for exactly this."""

    prs = [_pr(i, "2025-12-05", f"2026-01-{1 + i % 28:02d}") for i in range(1, 250)]
    prs.append(_pr(999, "2025-12-10", "2025-12-11"))      # last in the list, then bumped to top
    client = FakeGitHub(prs, [_comment(77, 999, "2025-12-10")], bump_after=1, bump_pr=999)
    kept, rows, client, _ = _run(tmp_path, prs, [_comment(77, 999, "2025-12-10")], client=client)
    assert [r["comment_id"] for r in rows] == [77]


def test_eval_prs_are_never_fetched(tmp_path):
    prs = [_pr(1, "2025-12-05", "2025-12-20"), _pr(33098, "2025-12-19", "2025-12-30")]
    comments = [_comment(10, 1, "2025-12-06"), _comment(11, 33098, "2025-12-23")]
    kept, rows, client, _ = _run(tmp_path, prs, comments, exclude={33098})
    assert [r["comment_id"] for r in rows] == [10]
    assert not any("/pulls/33098/" in p for p in client.requests)


def test_a_slice_at_the_search_cap_is_split(tmp_path):
    prs = [_pr(i, "2025-12-03", "2025-12-10") for i in range(1, 6)]
    client = FakeGitHub(prs, [], cap_override={("2025-12-01", "2025-12-07"): 1000})
    kept, rows, client, _ = _run(tmp_path, prs, [], client=client, stage_a="search")
    searches = [p for p in client.requests if p == "/search/issues"]
    assert len(searches) > 6          # the week was split rather than truncated
    read = {int(p.split("/pulls/")[1].split("/")[0]) for p in client.requests if "/pulls/" in p}
    assert read == {1, 2, 3, 4, 5}


def test_a_rerun_skips_finished_prs_and_adds_nothing(tmp_path):
    prs = [_pr(1, "2025-12-05", "2025-12-20"), _pr(2, "2025-12-06", "2025-12-21")]
    comments = [_comment(10, 1, "2025-12-06"), _comment(11, 2, "2025-12-07")]
    kept, rows, client, out = _run(tmp_path, prs, comments)
    assert kept == 2
    state = json.loads(corpus._state_path(out).read_text())
    assert state["mode"] == "per-pr" and state["done"] is True and state["done_prs"] == [1, 2]
    assert state["prs_found"] == [1, 2]          # stage A is cached, never repeated
    client2 = FakeGitHub(prs, comments)
    again = corpus.build_corpus_per_pr("2025-12-01", "2025-12-31", out, exclude_prs=set(),
                                       logger=logging.getLogger("t"), client=client2)
    assert again == 0
    assert not client2.requests                  # neither stage A nor stage B ran again
    assert len(out.read_text().splitlines()) == 2


def test_the_log_gives_prs_done_over_prs_found(tmp_path, caplog):
    prs = [_pr(i, "2025-12-05", "2025-12-20") for i in range(1, 8)]
    comments = [_comment(100 + i, i, "2025-12-06") for i in range(1, 8)]
    with caplog.at_level(logging.INFO, logger="per-pr-test"):
        _run(tmp_path, prs, comments, log_every_prs=3)
    text = caplog.text
    assert "PLAN  window 2025-12-01..2025-12-31 | per-pr route" in text
    assert "stage A done: 7 PRs active in the window" in text
    assert "PR 3/7" in text and "DONE  PR 7/7" in text


def test_the_highest_numbered_prs_are_read_first(tmp_path):
    """Newest first. Of the 2,636 PRs a December window turned up, 1,479 were opened before
    September and merely touched inside it, yielding ~0.25 comments each; the ~1,150 opened in
    December carry the mass. Ascending order put those last, so half an hour of a real run looked
    like it was keeping nothing, and an interrupted run had done only the low-yield tail."""

    prs = [_pr(n, "2025-12-05", "2025-12-20") for n in (100, 33444, 5000, 32900)]
    _, _, client, _ = _run(tmp_path, prs, [])
    order = [int(p.split("/pulls/")[1].split("/")[0])
             for p in client.requests if p.endswith("/comments")]
    assert order == [33444, 32900, 5000, 100]


def test_the_progress_line_says_comments_and_counts_the_prs_that_yielded_any(tmp_path, caplog):
    """`scanned`/`kept` count comments, not PRs -- the unlabelled version was read as PRs and
    looked like a bug. A PR's comment list carries every comment it ever received."""

    prs = [_pr(n, "2025-12-05", "2025-12-20") for n in (1, 2, 3, 4)]
    # Only PR 3 has a comment inside the window; PR 4's is a year earlier.
    comments = [_comment(30, 3, "2025-12-06"), _comment(40, 4, "2024-12-06")]
    with caplog.at_level(logging.INFO, logger="per-pr-test"):
        kept, rows, _, _ = _run(tmp_path, prs, comments, log_every_prs=2)
    assert kept == 1
    assert "comments scanned 2, kept 1 from 1 PRs" in caplog.text
    assert "from 1 of 4 PRs" in caplog.text
