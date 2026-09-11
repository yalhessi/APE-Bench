"""The index is a faithful, deterministic cache that refuses to be read stale.

It exists so "which comments in December carry a suggestion block" does not walk 23,000
directories. Three properties make it safe to depend on: every comment in the store appears once;
rebuilding from the same store yields the same rows; and an index built from a different store is
refused rather than read -- the failure the precedent index was found in (36,695 rows indexed
against a 43,874-row corpus, and nothing noticed).
"""

from __future__ import annotations

import pytest

from src.datasets.pull_requests.index import (
    StaleIndex, build_index, index_content_sha256, open_index, pr_export_rows, store_manifest,
)
from src.datasets.pull_requests.seed import seed_from_legacy
from src.datasets.pull_requests.store import PullRequestStore
from src.mathlib_review.paths import LEGACY_V2_BUNDLES


@pytest.fixture(scope="module")
def indexed(tmp_path_factory):
    if not LEGACY_V2_BUNDLES.is_dir():
        pytest.skip("no legacy bundle cache")
    store = PullRequestStore(tmp_path_factory.mktemp("store"))
    seed_from_legacy(store)
    summary = build_index(store)
    return store, summary


def test_every_conversation_row_is_indexed_once(indexed):
    store, summary = indexed
    expected = {"review_comment": 0, "review": 0, "issue_comment": 0}
    for number in store.numbers():
        for endpoint, kind in (("review_comments", "review_comment"), ("reviews", "review"),
                               ("issue_comments", "issue_comment")):
            expected[kind] += len(store.read(number, endpoint) or [])
    assert summary["comments"] == expected
    assert summary["prs"] == 201


def test_facts_not_policy(indexed):
    """The index knows who wrote a comment and whether they authored the PR; it does not decide
    who is a reviewer, which depends on a roster snapshot."""

    store, _ = indexed
    con = open_index(store)
    columns = {row[1] for row in con.execute("PRAGMA table_info(comments)")}
    assert {"is_pr_author", "has_suggestion", "author_association"} <= columns
    assert not {"is_reviewer", "reviewer_basis"} & columns
    # PR 33098: nine inline comments, all by the reviewer, none by the PR author.
    rows = con.execute("SELECT author, is_pr_author FROM comments "
                       "WHERE pr_number = 33098 AND kind = 'review_comment'").fetchall()
    assert len(rows) == 9 and all(not self_ for _, self_ in rows)
    self_comments = con.execute("SELECT COUNT(*) FROM comments WHERE is_pr_author = 1").fetchone()[0]
    assert self_comments > 0
    con.close()


def test_rebuilding_the_same_store_yields_the_same_rows(indexed, tmp_path):
    store, summary = indexed
    again = build_index(store, tmp_path / "again.sqlite3")
    assert again["index_content_sha256"] == summary["index_content_sha256"]


def test_an_index_from_a_different_store_is_refused(indexed, tmp_path):
    store, _ = indexed
    other = PullRequestStore(tmp_path / "other")
    seed_from_legacy(other)
    build_index(other)
    other.write_endpoint(99999999, "review_comments", [], request="r", fetched_at="t",
                         source="github")
    with pytest.raises(StaleIndex):
        open_index(other)


def test_the_tracked_export_covers_every_pr_compactly(indexed):
    store, _ = indexed
    rows = pr_export_rows(store)
    assert [r["pr_number"] for r in rows] == store.numbers()
    assert all(len(r["digest"]) == 64 and r["tiers"] == [1, 2] for r in rows)
    manifest = store_manifest(store)
    assert manifest["prs"] == 201
    assert manifest["prs_by_complete_tier"] == {"1": 201, "2": 201}
    assert manifest["content_sha256"] == store.content_digest()
