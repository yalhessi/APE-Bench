"""A review comment's position inside its hunk survives collection and indexing.

The review-comment join attaches each comment to a declaration in its `diff_hunk`. Without the
comment's position it can only pick *some* declaration in the hunk, and on a hand-read fifty
that was the right one 27 times. GitHub's raw comment carries `original_position` (1-based
over the hunk's lines after the `@@` header, stable across force-pushes); the corpus collector
dropped it, and so did the index's `meta.jsonl`. Both now carry it, and this pins that they do.
"""

from __future__ import annotations

from src.datasets.pr_review_v2.corpus import corpus_row
from src.mathlib_review.retrieval.precedent_index import meta_row

# The shape GitHub returns from /repos/{repo}/pulls/comments (keys observed on a cached
# December-2025 bundle), trimmed to the fields the two builders read.
RAW = {
    "id": 2631668700,
    "pull_request_url": "https://api.github.com/repos/leanprover-community/mathlib4/pulls/33046",
    "path": "Mathlib/Topology/MetricSpace/CoveringNumbers.lean",
    "line": 176, "original_line": 176, "start_line": None, "original_start_line": None,
    "position": 151, "original_position": 149, "side": "RIGHT", "subject_type": "line",
    "diff_hunk": "@@ -170,7 +170,9 @@ theorem foo : True := by\n   trivial\n",
    "body": "this and the next three lemmas can be proven with `grind [minimalCover]`",
    "user": {"login": "maintainer"}, "author_association": "MEMBER",
    "created_at": "2025-12-18T16:02:31Z", "in_reply_to_id": None,
    "commit_id": "abc", "html_url": "https://github.com/x",
}


def test_the_corpus_row_keeps_the_comment_position():
    row = corpus_row(RAW)
    assert row["original_position"] == 149
    assert row["original_line"] == 176
    assert row["side"] == "RIGHT"
    assert row["subject_type"] == "line"
    # `position` is the live value and moves under force-pushes; only the original is kept.
    assert "position" not in row


def test_the_index_row_keeps_the_comment_position():
    meta = meta_row(corpus_row(RAW))
    assert meta["original_position"] == 149
    assert meta["original_line"] == 176
    assert meta["side"] == "RIGHT"
    assert meta["subject_type"] == "line"
    assert meta["created_epoch"] > 0


def test_a_legacy_row_without_positions_indexes_as_unpositioned_not_as_an_error():
    """Every row of the current 34,640-row index was collected before these fields existed."""

    legacy = {k: v for k, v in corpus_row(RAW).items()
              if k not in ("original_position", "original_line", "side", "subject_type")}
    meta = meta_row(legacy)
    assert meta["original_position"] is None
    assert meta["original_line"] == 176      # falls back to `line`
    assert meta["side"] is None
