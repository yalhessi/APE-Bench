"""`precedent_search` returns distinct hunks, shows the commented line, and names who wrote it.

Four defects measured over every precedent delivered to an arm in the v5 runs (2,825 hits in
565 calls), all of which a trace-row audit is blind to because the rows themselves were
correctly gated:

* **The hunk was truncated from the front.** GitHub builds a review comment's `diff_hunk` so
  that it ENDS at the commented line, so the first N characters are the context *before* the
  point. 711 of 2,825 hits (25%) were longer than the render budget, and every one showed the
  arm code the comment was not about.
* **Thread replies filled the slots.** Every comment in one review thread carries the same
  hunk and therefore the same score; a k=5 answer held about 3 distinct hunks.
* **Everything was labelled "maintainer wrote".** The corpus keeps comments by GitHub
  `author_association`, which a PR's own author carries on their own PR, so 46% of delivered
  hits were the author replying to a reviewer ("Done.", "My bad, thanks.") presented as a
  maintainer's judgement.
* **A comment naming the PR under review was eligible.** `eligible_mask` excludes by the row's
  own `pr_number`, so a pre-cutoff comment on a *different* PR that announces this one passed.
  3 of 43,881 corpus rows name a scored PR; one is eligible for two real episodes of #33302.

Deliberately NOT fixed with a score threshold: measured over representative queries the top-5
similarities sit in 0.59-0.63 whether the hits are relevant or not, so no cutoff separates them
and one would only hide the problem. The tool says so in its result instead.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.mathlib_review.retrieval.precedent_index import PrecedentIndex, references_pr


@pytest.mark.parametrize("text,pr,expected", [
    ("I've opened #33302 adding map_zero", 33302, True),
    ("see https://github.com/leanprover-community/mathlib4/pull/33302", 33302, True),
    ("fixed in #333021", 33302, False),          # a longer number is a different PR
    ("about #3330", 33302, False),
    ("no reference at all", 33302, True if False else False),
    (None, 33302, False),
    ("#33302", None, False),                      # nothing to exclude against
])
def test_pr_reference_detection(text, pr, expected):
    assert references_pr(text, pr) is expected


def _index(monkeypatch, rows, vectors):
    index = PrecedentIndex.__new__(PrecedentIndex)
    index._np = np
    index.meta = rows
    index.embeddings = np.asarray(vectors, dtype="float32")
    index._created = np.asarray([r["created_epoch"] for r in rows])
    index._pr = np.asarray([r["pr_number"] for r in rows])
    monkeypatch.setattr(PrecedentIndex, "_encode",
                        lambda self, text: np.asarray([1.0, 0.0], dtype="float32"))
    return index


def _row(cid, pr, hunk, body="looks wrong", created=1_000, commenter="alice"):
    return {"comment_id": cid, "pr_number": pr, "path": "M/A.lean", "created_at": "2025-01-01T00:00:00Z",
            "created_epoch": created, "commenter": commenter, "body": body, "diff_hunk": hunk,
            "original_line": 10, "original_position": None, "side": None, "subject_type": None,
            "html_url": "u"}


def test_one_slot_per_distinct_hunk(monkeypatch):
    """A whole review thread shares a hunk and a score; without dedupe it fills the answer."""

    rows = [_row(i, 100, "SHARED HUNK") for i in range(6)] + [
        _row(90, 101, "OTHER HUNK A"), _row(91, 102, "OTHER HUNK B")]
    vectors = [[1.0, 0.0]] * 6 + [[0.99, 0.14], [0.98, 0.2]]
    index = _index(monkeypatch, rows, vectors)

    hits = index.search("q", k=3, as_of=None, exclude_pr=None)

    assert [h["diff_hunk"] for h in hits] == ["SHARED HUNK", "OTHER HUNK A", "OTHER HUNK B"]


def test_fewer_than_k_distinct_hunks_returns_fewer(monkeypatch):
    """Returning 2 is a real answer about the corpus; padding to 5 would not be."""

    rows = [_row(i, 100, "SHARED") for i in range(4)] + [_row(90, 101, "OTHER")]
    index = _index(monkeypatch, rows, [[1.0, 0.0]] * 4 + [[0.9, 0.4]])

    assert len(index.search("q", k=5, as_of=None, exclude_pr=None)) == 2


def test_a_precedent_naming_the_pr_under_review_is_dropped(monkeypatch):
    """The demonstrated case: a comment on another PR announcing the one being reviewed."""

    rows = [_row(1, 31707, "HUNK A", body="I've opened #33302 adding map_zero for ShiftedHom"),
            _row(2, 31708, "HUNK B", body="unrelated remark")]
    index = _index(monkeypatch, rows, [[1.0, 0.0], [0.9, 0.4]])

    hits = index.search("q", k=5, as_of=None, exclude_pr=33302)

    assert [h["comment_id"] for h in hits] == [2], "the announcement must not be returned"
    assert index.search("q", k=5, as_of=None, exclude_pr=999)[0]["comment_id"] == 1, (
        "and it is returned when it is not about the PR under review")


def test_the_cutoff_still_runs_before_ranking(monkeypatch):
    """Dedupe must not have moved the gate: an ineligible row is never a candidate."""

    from src.datasets.zulip.datetimes import epoch_to_iso

    rows = [_row(1, 100, "FUTURE", created=9_000), _row(2, 101, "PAST", created=1_000)]
    index = _index(monkeypatch, rows, [[1.0, 0.0], [0.5, 0.86]])

    hits = index.search("q", k=5, as_of=epoch_to_iso(5_000), exclude_pr=None)

    assert [h["comment_id"] for h in hits] == [2]
