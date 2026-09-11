"""The collector fills the store by tier, resumably, and its pre-gate never drops a PR the funnel keeps.

Checked against a fake GitHub for the mechanics, and against the real funnel on the 201 seeded PRs
for the one claim that matters most: the pre-gate decides which PRs get tier 2 from tier-1 data
alone, and it must not skip any PR the funnel would include. An approximation of the same test,
written separately from the funnel, missed 14 of 138; this one calls the funnel's own function.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.datasets.pull_reviews.collect import Collector, pre_gate
from src.datasets.pull_reviews.projections.episodes import project_episodes
from src.datasets.pull_reviews.seed import seed_from_legacy
from src.datasets.pull_reviews.store import PullReviewStore
from src.mathlib_review.agenda.cutoffs import commit_timestamp
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, LEGACY_V2_ROSTER

LOG = logging.getLogger("collect-test")
REVIEWER = "j-loreaux"


def _user(login):
    return {"login": login}


def _pr(n, *, title="feat: a lemma", author="author1", state="closed", merged=True,
        created="2025-12-01T00:00:00Z", updated="2025-12-05T00:00:00Z", head="h1"):
    return {"number": n, "title": title, "user": _user(author), "state": state,
            "merged_at": "2025-12-05T00:00:00Z" if merged else None, "draft": False,
            "created_at": created, "updated_at": updated, "closed_at": updated if state == "closed" else None,
            "body": "Adds a lemma.", "labels": [], "author_association": "CONTRIBUTOR",
            "base": {"sha": "base0", "ref": "master"}, "head": {"sha": f"{head}-{n}", "repo": None},
            "additions": 20, "deletions": 0, "changed_files": 1}


def _comment(i, login, *, n, created="2025-12-02T00:00:00Z", body="please use `grind` here", commit=None):
    return {"id": i, "user": _user(login), "author_association": "CONTRIBUTOR", "created_at": created,
            "body": body, "path": "Mathlib/A.lean", "diff_hunk": "@@ -1,1 +1,2 @@\n theorem a : True := by\n+  trivial",
            "original_commit_id": commit or f"h1-{n}", "commit_id": commit or f"h1-{n}"}


class FakeGitHub:
    authenticated = True

    def __init__(self, prs: Dict[int, Dict[str, Any]]):
        self.prs = prs
        self.requests: List[str] = []

    def pages(self, path, *, params=None, per_page=100, max_pages=None):
        assert path.endswith("/pulls")
        rows = sorted((p["listing"] for p in self.prs.values()), key=lambda r: r["updated_at"], reverse=True)
        for index, offset in enumerate(range(0, len(rows), 100)):
            if max_pages is not None and index >= max_pages:
                return
            self.requests.append(path)
            yield rows[offset:offset + 100]

    def paginate_all(self, path, **kwargs):
        self.requests.append(path)
        n = int(re.search(r"/(?:pulls|issues)/(\d+)/", path).group(1))
        kind = path.rsplit("/", 1)[1]
        key = {"comments": "issue_comments" if "/issues/" in path else "review_comments",
               "reviews": "reviews", "commits": "commits", "files": "files", "timeline": "timeline"}[kind]
        return list(self.prs[n].get(key, []))

    def get_json(self, path, params=None):
        self.requests.append(path)
        if "/compare/" in path:
            head = path.rsplit("...", 1)[1]
            return {"merge_base_commit": {"sha": "base0"},
                    "files": [{"filename": "Mathlib/A.lean", "status": "modified", "additions": 20,
                               "deletions": 0, "patch": "@@ -1,1 +1,21 @@\n" + "\n".join(f"+line {k}" for k in range(20)),
                               "head": head}]}
        n = int(path.rsplit("/", 1)[1])
        return self.prs[n]["pr"]

    def graphql(self, query, variables):
        self.requests.append("graphql")
        if "reviewThreads" in query:
            return {"repository": {"pullRequest": {"reviewThreads": {
                "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": []}}}}
        return {"repository": {"pullRequest": {"userContentEdits": {"nodes": []}}}}

    def close(self):
        pass


def _fixture_prs():
    def pr(n, **kw):
        listing = _pr(n, **{k: v for k, v in kw.items() if k in ("title", "author", "state", "merged", "created", "updated")})
        return {"listing": listing, "pr": listing,
                "review_comments": kw.get("review_comments", []), "reviews": kw.get("reviews", []),
                "issue_comments": kw.get("issue_comments", []),
                "commits": [{"sha": f"h1-{n}", "commit": {"committer": {"date": "2025-12-01T10:00:00Z"},
                                                          "author": {"date": "2025-12-01T10:00:00Z"}}}],
                "files": [{"filename": "Mathlib/A.lean", "status": "modified", "additions": 20, "deletions": 0}],
                "timeline": []}
    return {
        101: pr(101, review_comments=[_comment(1, REVIEWER, n=101)]),                     # passes
        102: pr(102, reviews=[{"id": 2, "user": _user(REVIEWER), "state": "APPROVED",     # approval only:
                               "submitted_at": "2025-12-02T00:00:00Z", "body": "bors r+",  # the case an
                               "commit_id": "h1-102", "author_association": "CONTRIBUTOR"}]),  # inline-only gate missed
        103: pr(103, state="open", merged=False, review_comments=[_comment(3, REVIEWER, n=103)]),
        104: pr(104, author="dependabot[bot]", review_comments=[_comment(4, REVIEWER, n=104)]),
        105: pr(105, title="Revert \"feat: x\"", review_comments=[_comment(5, REVIEWER, n=105)]),
        106: pr(106, review_comments=[_comment(6, "author1", n=106)]),                     # only self-comments
        107: pr(107, created="2026-02-01T00:00:00Z", updated="2026-02-02T00:00:00Z",       # outside the window
                review_comments=[_comment(7, REVIEWER, n=107)]),
    }


@pytest.fixture
def collected(tmp_path):
    roster = tmp_path / "roster.txt"
    roster.write_text(f"# test roster\n{REVIEWER}\n")
    store = PullReviewStore(tmp_path / "store")
    fake = FakeGitHub(_fixture_prs())
    collector = Collector(store, fake, LOG, roster_path=roster, state_path=tmp_path / "state.json")
    prs = collector.window_prs("2025-12-01", "2025-12-31")
    collector.tier1(prs)
    return store, fake, collector, prs


def test_the_window_holds_exactly_the_prs_that_can_carry_its_comments(collected):
    store, _, _, prs = collected
    assert prs == [101, 102, 103, 104, 105, 106]           # 107 was opened after the window
    for n in prs:
        assert store.tiers(n) == {0, 1}
    assert not store.has(107)


def test_a_resumed_run_fetches_nothing_already_recorded(collected, tmp_path):
    store, fake, collector, prs = collected
    before = len(fake.requests)
    assert collector.window_prs("2025-12-01", "2025-12-31") == prs    # cached, not re-walked
    collector.tier1(prs)
    assert len(fake.requests) == before


def test_the_pre_gate(collected):
    store, _, collector, prs = collected
    verdicts = {n: pre_gate(store, n, collector.roster) for n in prs}
    assert verdicts == {
        101: (True, "pass"),
        102: (True, "pass"),                                  # an approval with no inline comment
        103: (False, "still_open"),
        104: (False, "bot_author"),
        105: (False, "revert"),
        106: (False, "no_reviewer_decision"),                 # the PR author is not a reviewer
    }


def test_tier_2_then_the_funnel_then_the_cutoff_with_no_legacy_cache(collected):
    """The decoupling proof in miniature: collected -> tier 2 -> episode -> cutoff, and nothing
    read from or written to `data/pr_review_v2/`."""

    store, fake, collector, prs = collected
    gate = collector.gate_report(prs)
    assert gate["passing_prs"] == [101, 102]
    collector.tier2(gate["passing_prs"])
    for n in (101, 102):
        assert store.tiers(n) == {0, 1, 2}
        assert f"h1-{n}" in store.ledger(n)["compares"]       # the head the funnel asked for
    projection = project_episodes(store, roster={REVIEWER}, prs=[101, 102])
    assert {e.pr_number for e in projection.episodes} == {101, 102}
    for episode in projection.episodes:
        assert episode.base_sha == "base0"
        assert episode.description.text == "Adds a lemma."     # body_edits recorded as [] -> kept
        assert commit_timestamp(episode.pr_number, episode.reviewed_head_sha, store=store,
                                legacy_bundles=None) == "2025-12-01T10:00:00Z"


def test_tier_2_refuses_to_run_without_a_token(collected):
    store, fake, collector, prs = collected
    fake.authenticated = False
    with pytest.raises(PermissionError) as excinfo:
        collector.tier2([101])
    assert "GITHUB_TOKEN" in str(excinfo.value)


def test_on_the_real_201_the_pre_gate_keeps_every_pr_the_funnel_includes(tmp_path):
    """Measured, not assumed. Seeded PRs have no listing row, so the gate reads `pr.json` -- the
    same GitHub object -- and only the three tier-1 conversation endpoints beyond it."""

    if not LEGACY_V2_BUNDLES.is_dir():
        pytest.skip("no legacy bundle cache")
    from src.datasets.pull_reviews.definitions import load_roster

    store = PullReviewStore(tmp_path / "store")
    seed_from_legacy(store)
    roster = load_roster(LEGACY_V2_ROSTER)
    funnel = [json.loads(line) for line in
              Path("inputs/pr_review_v4/releases/dev-raw-0.3.0/derived/funnel.jsonl").read_text().splitlines()]
    included = [row["pr_number"] for row in funnel if row["included"]]
    assert len(included) == 138
    missed = [n for n in included if not pre_gate(store, n, roster)[0]]
    assert missed == []
