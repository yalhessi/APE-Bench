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
from src.mathlib_review.io import jsonl_rows
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, V4_RELEASES
from src.mathlib_review.schema import ReviewEpisodeInput


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    if not LEGACY_V2_BUNDLES.is_dir():
        pytest.skip("no legacy bundle cache")
    store = PullRequestStore(tmp_path_factory.mktemp("store"))
    seed_from_legacy(store)
    return store


def _store_built(release: Path) -> bool:
    manifest = json.loads((release / "manifest.json").read_text())
    return any(ref.get("role") == "pull_request_store" for ref in manifest.get("sources") or ())


def _all_release_episodes(*, store_built: bool):
    seen = {}
    for path in sorted(V4_RELEASES.glob("*/input/episodes.jsonl")):
        if _store_built(path.parent.parent) != store_built:
            continue
        for row in jsonl_rows(path):
            seen[(row["pr_number"], row["reviewed_head_sha"])] = row
    return seen


def test_every_release_episode_has_the_same_cutoff_from_the_store_and_the_cache(store):
    pairs = _all_release_episodes(store_built=False)
    assert len(pairs) > 190          # every distinct (PR, reviewed head) across the legacy-built releases
    for (number, head) in pairs:
        from_store = commit_timestamp(number, head, store=store, legacy_bundles=None)
        from_cache = commit_timestamp(number, head, store=None)
        assert from_store is not None and from_store == from_cache, (number, head)


def test_a_store_built_release_resolves_every_cutoff_from_the_store_alone():
    """A release drawn from the PR store (eval-2025-06-2026-03-v1) has no legacy cache to agree
    with; its cutoffs must come from the store, with the cache switched off."""

    pairs = _all_release_episodes(store_built=True)
    if not pairs:
        pytest.skip("no store-built release")
    real = PullRequestStore()
    if not (real.root / "pr").is_dir():
        pytest.skip("no PR store")
    for (number, head) in pairs:
        assert commit_timestamp(number, head, store=real, legacy_bundles=None) is not None, (number, head)


def test_a_collected_pr_resolves_with_no_cache_at_all(store, tmp_path):
    fresh = PullRequestStore(tmp_path / "fresh")
    commits = store.read(33098, "commits")
    fresh.write_endpoint(33098, "commits", commits, request="/commits",
                         fetched_at="2026-09-11T00:00:00Z", source="github")
    head = commits[-1]["sha"]
    assert commit_timestamp(33098, head, store=fresh, legacy_bundles=None) == \
        commits[-1]["commit"]["committer"]["date"]


def test_an_unresolvable_cutoff_names_both_sources_and_the_collector():
    episode = ReviewEpisodeInput.model_validate(next(iter(_all_release_episodes(store_built=False).values())))
    broken = episode.model_copy(update={"reviewed_head_sha": "0" * 40})
    with pytest.raises(CutoffUnavailable) as excinfo:
        episode_cutoff(broken)
    message = str(excinfo.value)
    assert "PR store" in message and "cached v2" in message
    assert "pull_requests.collect" in message
