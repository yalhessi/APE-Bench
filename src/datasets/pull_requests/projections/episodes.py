"""Review episodes from the PR store: the funnel, first or every review round, and the event index.

This is the one path from collected PR data to a reviewable task. It runs the release builder's own
funnel (`release/episode_builder`) over bundles read from the store, with compares resolved from the
store and the retrieval cutoff's commit dates available from it -- so no step reads or writes the
frozen v2 caches.

For the 201 PRs seeded from those caches the output is **byte-identical** to the frozen releases
they built: `dev-raw-0.3.0` (first rounds) and `dev-raw-multiround-0.4.0` (every round), funnel,
episodes, boundaries, segments and event ledger alike. `test_pull_requests_reproduces_raw_release`
rebuilds both from each source. That is the evidence the store can replace the caches.

A store-built release records the store's content digest and the roster's sha among its sources,
so its every episode traces to the raw bytes and the reviewer definition it came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from src.datasets.pull_requests.definitions import DEFINITIONS_VERSION, load_roster, roster_sha256
from src.datasets.pull_requests.store import STORE_VERSION, PullRequestStore
from src.mathlib_review.io import display_path
from src.mathlib_review.release.episode_builder import (
    MULTI_ROUND_BUILDER_VERSION, RAW_EPISODE_BUILDER_VERSION, funnel_and_first_round,
    segment_review_rounds,
)
from src.mathlib_review.release.events import (
    STORE_EVENT_LEDGER_VERSION, events_from_bundle, order_events,
)
from src.mathlib_review.release.releases import ArtifactSpec, build_release
from src.mathlib_review.schema import (
    ArtifactRef, DatasetManifest, FunnelDecision, ReviewEpisodeBoundary, ReviewEpisodeInput, ReviewRoundSegment,
    SourceEvent,
)

REPO = "leanprover-community/mathlib4"


@dataclass
class EpisodeProjection:
    funnel: List[FunnelDecision] = field(default_factory=list)
    episodes: List[ReviewEpisodeInput] = field(default_factory=list)
    boundaries: List[ReviewEpisodeBoundary] = field(default_factory=list)
    segments: List[ReviewRoundSegment] = field(default_factory=list)
    events: List[SourceEvent] = field(default_factory=list)


def eligible_numbers(store: PullRequestStore, prs: Optional[Iterable[int]] = None) -> List[int]:
    """PRs the funnel can run on: those collected to tier 2. Anything else has no bundle."""

    wanted = sorted(set(prs)) if prs is not None else store.numbers()
    return [n for n in wanted if 2 in store.tiers(n)]


def project_episodes(
    store: PullRequestStore, *, roster: Iterable[str], prs: Optional[Iterable[int]] = None,
    all_rounds: bool = False, repo: str = REPO,
) -> EpisodeProjection:
    """Run the funnel over the store, in the order and shape `legacy_pipeline/raw_release.py`
    writes, so the result can be compared byte for byte with a frozen release."""

    roster = set(roster)
    out = EpisodeProjection()
    for number in eligible_numbers(store, prs):
        bundle = store.load_bundle(number)
        kwargs = dict(bundle_sha256=store.bundle_sha256(number), compares=store.compares(number),
                      repo=repo, roster=roster)
        if all_rounds:
            decision, multi = segment_review_rounds(bundle, **kwargs)
            if multi:
                out.episodes.extend(multi.episodes)
                out.boundaries.extend(multi.boundaries)
                out.segments.extend(multi.segments)
        else:
            decision, result = funnel_and_first_round(bundle, **kwargs)
            if result:
                out.episodes.append(result.episode)
                out.boundaries.append(result.boundary)
        out.funnel.append(decision)
        out.events.extend(events_from_bundle(bundle, source_object=store.bundle_ref(number),
                                             repo=repo))
    key = lambda item: (item.pr_number, item.round_index)  # noqa: E731
    out.episodes.sort(key=key)
    out.boundaries.sort(key=key)
    out.segments.sort(key=key)
    out.funnel.sort(key=lambda item: item.pr_number)
    out.events = order_events(out.events)
    return out


def write_episode_release(
    out: Path, store: PullRequestStore, *, roster_path: Path, dataset_id: str, release: str,
    prs: Optional[Iterable[int]] = None, all_rounds: bool = False, split: str = "development",
) -> DatasetManifest:
    """Seal a release of store-derived episodes with `releases.build_release`."""

    projection = project_episodes(store, roster=load_roster(roster_path), prs=prs,
                                  all_rounds=all_rounds)
    included = sorted({episode.pr_number for episode in projection.episodes})
    derived = [ArtifactSpec("derived/funnel.jsonl", projection.funnel, "funnel1", "eligibility_funnel")]
    if all_rounds:
        derived.append(ArtifactSpec("derived/round_segments.jsonl", projection.segments,
                                    "round-segment1", "review_round_segments"))
    manifest = build_release(
        out, dataset_id=dataset_id, release=release, pr_numbers=included,
        corpus_cutoff_policy="No historical review corpus is visible during generation.",
        generator_versions={
            "episodes": MULTI_ROUND_BUILDER_VERSION if all_rounds else RAW_EPISODE_BUILDER_VERSION,
            "funnel": RAW_EPISODE_BUILDER_VERSION, "events": STORE_EVENT_LEDGER_VERSION,
            "store": STORE_VERSION, "definitions": DEFINITIONS_VERSION,
        },
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        sources=[
            ArtifactRef(path=display_path(store.root), role="pull_request_store",
                        sha256=store.content_digest(), records=len(eligible_numbers(store, prs))),
            ArtifactRef(path=display_path(roster_path), role="reviewer_roster",
                        sha256=roster_sha256(roster_path), records=len(load_roster(roster_path))),
        ],
        source_artifacts=[ArtifactSpec("source/events.jsonl", projection.events, "event1",
                                       "raw_event_index")],
        input_artifacts=[ArtifactSpec("input/episodes.jsonl", projection.episodes, "episode1",
                                      "reviewer_visible_episodes")],
        gold_artifacts=[ArtifactSpec("gold/episode_boundaries.jsonl", projection.boundaries,
                                     "episode-boundary1", "hidden_episode_boundaries")],
        derived_artifacts=derived, split=split,
    )
    return manifest
