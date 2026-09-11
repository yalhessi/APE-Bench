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

    def __init__(self, prs, comments, *, cap_override=None):
        self.prs, self.comments = prs, comments
        self.cap_override = cap_override      # {(lo, hi): total_count} to simulate the cap
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
    kept, rows, client, _ = _run(pathlib.Path(tempfile.mkdtemp()), prs, comments)
    assert sorted(r["comment_id"] for r in rows) == [10, 11]     # 12 and 13 are outside the window
    read = sorted(int(p.split("/pulls/")[1].split("/")[0]) for p in client.requests if "/pulls/" in p)
    assert read == [1, 2]


def test_eval_prs_are_never_fetched(tmp_path):
    prs = [_pr(1, "2025-12-05", "2025-12-20"), _pr(33098, "2025-12-19", "2025-12-30")]
    comments = [_comment(10, 1, "2025-12-06"), _comment(11, 33098, "2025-12-23")]
    kept, rows, client, _ = _run(tmp_path, prs, comments, exclude={33098})
    assert [r["comment_id"] for r in rows] == [10]
    assert not any("/pulls/33098/" in p for p in client.requests)


def test_a_slice_at_the_search_cap_is_split(tmp_path):
    prs = [_pr(i, "2025-12-03", "2025-12-10") for i in range(1, 6)]
    client = FakeGitHub(prs, [], cap_override={("2025-12-01", "2025-12-07"): 1000})
    kept, rows, client, _ = _run(tmp_path, prs, [], client=client)
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
    client2 = FakeGitHub(prs, comments)
    again = corpus.build_corpus_per_pr("2025-12-01", "2025-12-31", out, exclude_prs=set(),
                                       logger=logging.getLogger("t"), client=client2)
    assert again == 0
    assert not any("/pulls/" in p for p in client2.requests)   # nothing re-read
    assert len(out.read_text().splitlines()) == 2


def test_the_log_gives_prs_done_over_prs_found(tmp_path, caplog):
    prs = [_pr(i, "2025-12-05", "2025-12-20") for i in range(1, 8)]
    comments = [_comment(100 + i, i, "2025-12-06") for i in range(1, 8)]
    with caplog.at_level(logging.INFO, logger="per-pr-test"):
        _run(tmp_path, prs, comments, log_every_prs=3)
    text = caplog.text
    assert "PLAN  window 2025-12-01..2025-12-31 (per-pr route)" in text
    assert "stage A done: 7 PRs active in the window" in text
    assert "PR 3/7" in text and "DONE  PR 7/7" in text
