"""The corpus is a projection that tags reviewers, and it is a strict superset of what the old
collector kept.

Synthetic cases pin each rule; then the acceptance report runs on real payloads -- every inline
comment in the 201 seeded PRs, against the decisions the old association-only gate made on exactly
those comments -- where it must pass and must attribute the 144 roster reviewers the old gate dropped.
"""

from __future__ import annotations

import json

import pytest

from src.datasets.pull_reviews.projections.corpus import (
    CORPUS_ROW_VERSION, _old_gate, acceptance_report, corpus_row, project_corpus, reviewer_view,
)
from src.datasets.pull_reviews.seed import seed_from_legacy
from src.datasets.pull_reviews.store import PullReviewStore
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, LEGACY_V2_ROSTER

ROSTER = {"rev1"}


def _c(i, login, assoc, *, pr=1, path="Mathlib/A.lean", body="please golf this", created="2025-08-10T00:00:00Z",
       updated=None):
    return {"id": i, "user": {"login": login}, "author_association": assoc, "path": path, "body": body,
            "created_at": created, "updated_at": updated or created, "diff_hunk": "@@ -1 +1 @@\n+x",
            "pull_request_url": f"https://api.github.com/repos/leanprover-community/mathlib4/pulls/{pr}",
            "html_url": f"https://x/{i}", "commit_id": "abc", "in_reply_to_id": None, "line": 1}


def _store(tmp_path, comments, *, author="alice", pr=1):
    store = PullReviewStore(tmp_path / "store")
    store.write_endpoint(pr, "listing", {"number": pr, "user": {"login": author}}, request="l",
                         fetched_at="t", source="github")
    store.write_endpoint(pr, "review_comments", comments, request="c", fetched_at="t", source="github")
    return store


CASES = [
    _c(1, "rev1", "CONTRIBUTOR"),                       # roster reviewer the old gate dropped
    _c(2, "maint", "MEMBER"),                           # reviewer by association: in both
    _c(3, "alice", "COLLABORATOR"),                     # PR author replying: old kept it
    _c(4, "bob", "CONTRIBUTOR"),                        # neither roster nor association
    _c(5, "mathlib-bot", "MEMBER"),                     # a bot: in neither
    _c(6, "rev1", "CONTRIBUTOR", path="docs/x.md"),     # not a Lean anchor: in neither
    _c(7, "rev1", "CONTRIBUTOR", body="LGTM, thanks!"), # no substance: in neither
    _c(8, "alice", "CONTRIBUTOR"),                      # PR author, contributor: old dropped it
]


def test_rows_are_tagged_not_filtered(tmp_path):
    store = _store(tmp_path, CASES)
    rows = {r["comment_id"]: r for r in project_corpus(store, roster=ROSTER, exclude=[])}
    assert sorted(rows) == [1, 2, 3, 4, 8]
    assert all(r["schema_version"] == CORPUS_ROW_VERSION for r in rows.values())
    assert (rows[1]["is_reviewer"], rows[1]["reviewer_basis"]) == (True, "roster")
    assert (rows[2]["is_reviewer"], rows[2]["reviewer_basis"]) == (True, "association")
    assert (rows[3]["is_reviewer"], rows[3]["commenter_is_author"]) == (False, True)
    assert (rows[4]["is_reviewer"], rows[4]["reviewer_basis"]) == (False, "none")
    assert [r["comment_id"] for r in reviewer_view(rows.values())] == [1, 2]


def test_scored_prs_are_excluded_by_the_projection_not_the_store(tmp_path):
    store = _store(tmp_path, [_c(1, "rev1", "CONTRIBUTOR", pr=33098)], pr=33098)
    assert store.has(33098)                                   # collected like any PR
    assert project_corpus(store, roster=ROSTER) == []         # but never in the corpus


def test_acceptance_passes_and_attributes_every_added_row(tmp_path):
    store = _store(tmp_path, CASES)
    new = project_corpus(store, roster=ROSTER, exclude=[])
    baseline = [corpus_row(c) for c in CASES if _old_gate(corpus_row(c))]
    assert sorted(r["comment_id"] for r in baseline) == [2, 3]
    report = acceptance_report(new, baseline, store)
    assert report["passed"] and report["superset"] and report["fields_agree"]
    assert report["added_by_cause"] == {"roster_reviewer": 1, "non_reviewer_contributor": 1,
                                        "author_self_comment": 1}


def test_a_row_the_projection_loses_is_a_failure_unless_github_deleted_it(tmp_path):
    store = _store(tmp_path, CASES)
    new = [r for r in project_corpus(store, roster=ROSTER, exclude=[]) if r["comment_id"] != 2]
    baseline = [corpus_row(c) for c in CASES if _old_gate(corpus_row(c))]
    report = acceptance_report(new, baseline, store)
    assert not report["passed"] and report["missing_failures"] == [2]

    gone = _c(99, "maint", "MEMBER")                          # in the baseline, deleted upstream since
    report = acceptance_report(project_corpus(store, roster=ROSTER, exclude=[]),
                               baseline + [corpus_row(gone)], store)
    assert report["passed"] and report["missing"] == {"deleted_upstream": 1}


def test_a_changed_shared_row_needs_a_reason(tmp_path):
    edited = _c(2, "maint", "MEMBER", body="please golf this, and rename", updated="2025-08-12T00:00:00Z")
    store = _store(tmp_path, [edited] + CASES[2:])
    baseline = [corpus_row(_c(2, "maint", "MEMBER"))]
    report = acceptance_report(project_corpus(store, roster=ROSTER, exclude=[]), baseline, store)
    assert report["passed"] and report["shared_row_mismatches"] == {"edited_upstream": 1}

    silent = _c(2, "maint", "MEMBER", body="changed with no edit timestamp")
    store2 = _store(tmp_path / "b", [silent])
    report = acceptance_report(project_corpus(store2, roster=ROSTER, exclude=[]), baseline, store2)
    assert not report["passed"] and report["mismatch_failures"] == [(2, ["body"])]


def test_on_the_201_seeded_prs_the_projection_is_a_superset_of_the_old_gate(tmp_path):
    """Real payloads, real roster. The baseline is what `keep_comment` would have kept from exactly
    these comments; the projection must contain all of it and attribute everything else."""

    if not LEGACY_V2_BUNDLES.is_dir():
        pytest.skip("no legacy bundle cache")
    from src.datasets.pull_reviews.definitions import load_roster

    store = PullReviewStore(tmp_path / "store")
    seed_from_legacy(store)
    baseline = []
    for number in store.numbers():
        for comment in store.read(number, "review_comments") or []:
            row = corpus_row(comment)
            if _old_gate(row):
                baseline.append(row)
    new = project_corpus(store, roster=load_roster(LEGACY_V2_ROSTER), exclude=[])
    report = acceptance_report(new, baseline, store)
    assert report["passed"], report
    assert report["baseline_rows"] == 115
    assert report["added_by_cause"]["roster_reviewer"] == 144
    assert report["reviewer_view_rows"] == 71 + 144
    assert "old_collection_gap" not in report["added_by_cause"]
