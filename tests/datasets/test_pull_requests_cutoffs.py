"""The retrieval cutoff comes off the frozen cache without moving by a second.

`agenda/cutoffs` gates every context read on the committer time of the reviewed head. It read that
from the v2 bundle cache, which eleven frozen manifests hash as a tree -- so no PR outside the 201
it holds could ever resolve a cutoff, and no new PR could become a task. It now reads the PR store
first. For the store to be a safe replacement, every cutoff any existing release implies must be
identical from either source; this checks all of them, in every release.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.datasets.pull_requests.seed import seed_from_legacy
from src.datasets.pull_requests.store import PullRequestStore
from src.mathlib_review.agenda.cutoffs import CutoffUnavailable, commit_timestamp, episode_cutoff
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, V4_RELEASES
from src.mathlib_review.schema import ReviewEpisodeInput


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    if not LEGACY_V2_BUNDLES.is_dir():
        pytest.skip("no legacy bundle cache")
    store = PullRequestStore(tmp_path_factory.mktemp("store"))
    seed_from_legacy(store)
    return store


def _all_release_episodes():
    seen = {}
    for path in sorted(V4_RELEASES.glob("*/input/episodes.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                seen[(row["pr_number"], row["reviewed_head_sha"])] = row
    return seen


def test_every_release_episode_has_the_same_cutoff_from_the_store_and_the_cache(store):
    pairs = _all_release_episodes()
    assert len(pairs) > 190          # every distinct (PR, reviewed head) across all 32 releases
    for (number, head) in pairs:
        from_store = commit_timestamp(number, head, store=store, legacy_bundles=None)
        from_cache = commit_timestamp(number, head, store=None)
        assert from_store is not None and from_store == from_cache, (number, head)


def test_a_collected_pr_resolves_with_no_cache_at_all(store, tmp_path):
    fresh = PullRequestStore(tmp_path / "fresh")
    commits = store.read(33098, "commits")
    fresh.write_endpoint(33098, "commits", commits, request="/commits",
                         fetched_at="2026-09-11T00:00:00Z", source="github")
    head = commits[-1]["sha"]
    assert commit_timestamp(33098, head, store=fresh, legacy_bundles=None) == \
        commits[-1]["commit"]["committer"]["date"]


def test_an_unresolvable_cutoff_names_both_sources_and_the_collector():
    episode = ReviewEpisodeInput.model_validate(next(iter(_all_release_episodes().values())))
    broken = episode.model_copy(update={"reviewed_head_sha": "0" * 40})
    with pytest.raises(CutoffUnavailable) as excinfo:
        episode_cutoff(broken)
    message = str(excinfo.value)
    assert "PR store" in message and "cached v2" in message
    assert "pull_requests.collect" in message
