"""The task pipeline produces the frozen raw releases byte for byte -- from the v2 cache *and* from
the PR store.

`dev-raw-0.3.0` (first review rounds: 201 funnel decisions, 138 episodes, 138 boundaries) and
`dev-raw-multiround-0.4.0` (every round: 198 episodes and boundaries, 202 round segments) were built
by `legacy_pipeline/raw_release.py` from the 201 cached bundles, the 223 cached compares and the
59-login roster, each with an event ledger over the bundles. All of it rebuilds in about a second.

That makes them the oracle for this refactor twice over. Rebuilt from the legacy cache, they prove
that consolidating the funnel's definitions changed no behaviour. Rebuilt from the store seeded
with the same bytes, they prove the store can *replace* the cache: same reviewer events, same
diffs, same provenance hashes, same event ids. If either source moves one byte, this fails.

The roster is the one each release's manifest pins. Membership is time-varying, so a newer
snapshot would shift reviewer events and fail this test for a reason unrelated to the code.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.datasets.pull_requests.projections.episodes import (
    project_episodes, write_episode_release,
)
from src.datasets.pull_requests.seed import seed_from_legacy
from src.datasets.pull_requests.store import PullRequestStore
from src.mathlib_review.io import jsonl_bytes, sha256_file
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, LEGACY_V2_COMPARES, LEGACY_V2_ROSTER
from src.mathlib_review.release.episode_builder import (
    funnel_and_first_round, load_roster, segment_review_rounds,
)
from src.mathlib_review.release.events import build_event_ledger

FIRST_ROUND = Path("inputs/pr_review_v4/releases/dev-raw-0.3.0")
ALL_ROUNDS = Path("inputs/pr_review_v4/releases/dev-raw-multiround-0.4.0")


def _pinned_roster(release: Path) -> Path:
    manifest = json.loads((release / "manifest.json").read_text())
    ref = next(r for r in manifest["sources"] if r["role"] == "reviewer_roster")
    assert sha256_file(Path(ref["path"])) == ref["sha256"]
    return Path(ref["path"])


def _from_legacy(all_rounds: bool, tmp_path: Path):
    roster = load_roster(_pinned_roster(ALL_ROUNDS if all_rounds else FIRST_ROUND))
    funnel, episodes, boundaries, segments = [], [], [], []
    for bundle_path in sorted(LEGACY_V2_BUNDLES.glob("pr_*.json")):
        bundle = json.loads(bundle_path.read_text())
        if all_rounds:
            decision, multi = segment_review_rounds(bundle, bundle_path=bundle_path,
                                                    compare_cache=LEGACY_V2_COMPARES, roster=roster)
            if multi:
                episodes += multi.episodes
                boundaries += multi.boundaries
                segments += multi.segments
        else:
            decision, result = funnel_and_first_round(bundle, bundle_path=bundle_path,
                                                      compare_cache=LEGACY_V2_COMPARES, roster=roster)
            if result:
                episodes.append(result.episode)
                boundaries.append(result.boundary)
        funnel.append(decision)
    key = lambda item: (item.pr_number, item.round_index)  # noqa: E731
    events, _ = build_event_ledger(bundles_dir=LEGACY_V2_BUNDLES, out=tmp_path / "events.jsonl")
    return {"derived/funnel.jsonl": sorted(funnel, key=lambda f: f.pr_number),
            "input/episodes.jsonl": sorted(episodes, key=key),
            "gold/episode_boundaries.jsonl": sorted(boundaries, key=key),
            "derived/round_segments.jsonl": sorted(segments, key=key),
            "source/events.jsonl": events}


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    if not LEGACY_V2_BUNDLES.is_dir():
        pytest.skip("no legacy bundle cache")
    store = PullRequestStore(tmp_path_factory.mktemp("store"))
    seed_from_legacy(store)
    return store


def _from_store(store: PullRequestStore, all_rounds: bool):
    roster = load_roster(_pinned_roster(ALL_ROUNDS if all_rounds else FIRST_ROUND))
    projection = project_episodes(store, roster=roster, all_rounds=all_rounds)
    return {"derived/funnel.jsonl": projection.funnel, "input/episodes.jsonl": projection.episodes,
            "gold/episode_boundaries.jsonl": projection.boundaries,
            "derived/round_segments.jsonl": projection.segments,
            "source/events.jsonl": projection.events}


CASES = [
    (FIRST_ROUND, False, {"derived/funnel.jsonl": 201, "input/episodes.jsonl": 138,
                          "gold/episode_boundaries.jsonl": 138}),
    (ALL_ROUNDS, True, {"derived/funnel.jsonl": 201, "input/episodes.jsonl": 198,
                        "gold/episode_boundaries.jsonl": 198, "derived/round_segments.jsonl": 202}),
]


def test_the_rosters_the_releases_pin_are_the_legacy_roster():
    assert _pinned_roster(FIRST_ROUND) == _pinned_roster(ALL_ROUNDS) == LEGACY_V2_ROSTER


@pytest.mark.parametrize("source", ["legacy_cache", "store"])
@pytest.mark.parametrize("release,all_rounds,counts", CASES, ids=["first-round", "all-rounds"])
def test_the_frozen_release_reproduces_byte_for_byte(source, release, all_rounds, counts, store, tmp_path):
    if not release.is_dir():
        pytest.skip(f"{release} absent")
    rebuilt = _from_legacy(all_rounds, tmp_path) if source == "legacy_cache" else _from_store(store, all_rounds)
    for relpath, count in counts.items():
        assert len(rebuilt[relpath]) == count, relpath
    for relpath in list(counts) + ["source/events.jsonl"]:
        assert jsonl_bytes(rebuilt[relpath]) == (release / relpath).read_bytes(), (
            f"{relpath} from the {source} no longer matches {release.name}")


def test_a_store_built_release_seals_and_carries_the_same_episodes(store, tmp_path):
    from src.mathlib_review.release.validate import validate_release

    out = tmp_path / "release"
    manifest = write_episode_release(out, store, roster_path=LEGACY_V2_ROSTER,
                                     dataset_id="pull-requests-test", release="0.0.0-test")
    assert (out / "input/episodes.jsonl").read_bytes() == \
        (FIRST_ROUND / "input/episodes.jsonl").read_bytes()
    roles = {ref.role: ref for ref in manifest.sources}
    assert roles["pull_request_store"].sha256 == store.content_digest()
    assert roles["reviewer_roster"].sha256 == sha256_file(LEGACY_V2_ROSTER)
    assert manifest.generator_versions["events"] == "pull_request_store_v1"
    validate_release(out)


def test_a_collected_pr_needs_no_legacy_cache_and_changes_only_its_provenance(store, tmp_path):
    """A PR fetched into the store -- not seeded -- cites its store directory and the assembled
    bundle's sha. Its episode must carry the same reviewer-visible content as the frozen one; only
    `source_projection_sha256`, which hashes the bundle's provenance, may differ. And its events
    must dereference through the store, since no bundle file exists for them to open."""

    from src.mathlib_review.release.events import resolve_payload
    from src.datasets.pull_requests.store import BUNDLE_ENDPOINTS

    fresh = PullRequestStore(tmp_path / "fresh")
    number = 33098
    for endpoint in BUNDLE_ENDPOINTS:
        fresh.write_endpoint(number, endpoint, store.read(number, endpoint),
                             request=f"/repos/x/pulls/{number}/{endpoint}", fetched_at="2026-09-11T00:00:00Z",
                             source="github")
    for head in store.ledger(number)["compares"]:
        raw = (store.pr_dir(number) / f"compares/{head}.json").read_bytes()
        fresh.write_compare(number, head, raw, base_ref="master", request="compare",
                            fetched_at="2026-09-11T00:00:00Z", source="github")
    assert fresh.bundle_ref(number).role == "pull_request_dir"

    projection = project_episodes(fresh, roster=load_roster(LEGACY_V2_ROSTER))
    (episode,) = projection.episodes
    frozen = next(json.loads(line) for line in (FIRST_ROUND / "input/episodes.jsonl").read_text().splitlines()
                  if json.loads(line)["pr_number"] == number)
    ours = json.loads(episode.model_dump_json())
    assert ours["source_projection_sha256"] != frozen["source_projection_sha256"]
    for field in ("episode_id", "diff", "base_sha", "reviewed_head_sha", "title", "description",
                  "changed_files", "patch_sha256"):
        assert ours[field] == frozen[field], field

    comment = next(e for e in projection.events if e.event_type == "review_comment")
    assert comment.source_object.role == "pull_request_dir"
    assert "grind" in resolve_payload(comment)["body"]
