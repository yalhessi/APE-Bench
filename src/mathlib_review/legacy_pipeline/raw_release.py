"""Build a raw-event-derived PR Review v4 first-round development release."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from src.mathlib_review.release.episode_builder import (
    MULTI_ROUND_BUILDER_VERSION,
    RAW_EPISODE_BUILDER_VERSION,
    funnel_and_first_round,
    load_roster,
    segment_review_rounds,
)
from src.mathlib_review.release.events import EVENT_LEDGER_VERSION, build_event_ledger
from src.mathlib_review.io import (
    display_path,
    git_state,
    jsonl_bytes,
    pretty_json_bytes,
    sha256_directory,
    sha256_file,
    write_once,
)
from src.mathlib_review.paths import (
    LEGACY_INTERVENTIONS_V5,
    LEGACY_V2_ANNOTATED,
    LEGACY_V2_BUNDLES,
    LEGACY_V2_COMPARES,
    LEGACY_V2_ROSTER,
)
from src.mathlib_review.schema import (
    ArtifactRef,
    DatasetManifest,
    FunnelDecision,
    ReviewEpisodeBoundary,
    ReviewEpisodeInput,
    ReviewRoundSegment,
)


DEFAULT_BUNDLES = LEGACY_V2_BUNDLES
DEFAULT_COMPARES = LEGACY_V2_COMPARES
DEFAULT_ROSTER = LEGACY_V2_ROSTER
DEFAULT_PARITY_RECORDS = LEGACY_V2_ANNOTATED
DEFAULT_INTERVENTIONS = LEGACY_INTERVENTIONS_V5
DEFAULT_RELEASE = Path("inputs/pr_review_v4/releases/dev-raw-0.3.0")


def build_raw_release(
    *,
    bundles_dir: Path,
    compare_cache: Path,
    roster_path: Path,
    release_dir: Path,
    parity_records: Optional[Path] = None,
    interventions_path: Optional[Path] = None,
    dataset_id: str = "mathlib-pr-review-v4-dev",
    release: str = "0.3.0-raw-first-round",
    created_at: Optional[str] = None,
    all_rounds: bool = False,
) -> DatasetManifest:
    manifest_path = release_dir / "manifest.json"
    if manifest_path.exists():
        existing = DatasetManifest.model_validate_json(manifest_path.read_text())
        if existing.dataset_id != dataset_id or existing.release != release:
            raise FileExistsError(f"existing release has incompatible identity: {manifest_path}")
        return existing

    roster = load_roster(roster_path)
    funnels: List[FunnelDecision] = []
    episodes: List[ReviewEpisodeInput] = []
    boundaries: List[ReviewEpisodeBoundary] = []
    segments: List[ReviewRoundSegment] = []
    for bundle_path in sorted(bundles_dir.glob("pr_*.json")):
        bundle = json.loads(bundle_path.read_text())
        if all_rounds:
            decision, multi = segment_review_rounds(
                bundle,
                bundle_path=bundle_path,
                compare_cache=compare_cache,
                roster=roster,
            )
            result = None
            if multi:
                episodes.extend(multi.episodes)
                boundaries.extend(multi.boundaries)
                segments.extend(multi.segments)
        else:
            decision, result = funnel_and_first_round(
                bundle,
                bundle_path=bundle_path,
                compare_cache=compare_cache,
                roster=roster,
            )
        funnels.append(decision)
        if result:
            episodes.append(result.episode)
            boundaries.append(result.boundary)
    episodes.sort(key=lambda item: (item.pr_number, item.round_index))
    boundaries.sort(key=lambda item: (item.pr_number, item.round_index))
    segments.sort(key=lambda item: (item.pr_number, item.round_index))
    funnels.sort(key=lambda item: item.pr_number)

    episodes_path = release_dir / "input" / "episodes.jsonl"
    boundaries_path = release_dir / "gold" / "episode_boundaries.jsonl"
    funnel_path = release_dir / "derived" / "funnel.jsonl"
    segments_path = release_dir / "derived" / "round_segments.jsonl"
    events_path = release_dir / "source" / "events.jsonl"
    write_once(episodes_path, jsonl_bytes(episodes))
    write_once(boundaries_path, jsonl_bytes(boundaries))
    write_once(funnel_path, jsonl_bytes(funnels))
    if all_rounds:
        write_once(segments_path, jsonl_bytes(segments))
    events, _event_report = build_event_ledger(bundles_dir=bundles_dir, out=events_path)

    sources = [
        ArtifactRef(
            path=display_path(bundles_dir),
            role="raw_github_bundles",
            sha256=sha256_directory(bundles_dir),
            records=sum(1 for path in bundles_dir.glob("*.json") if path.is_file()),
        ),
        ArtifactRef(
            path=display_path(compare_cache),
            role="git_compare_cache",
            sha256=sha256_directory(compare_cache),
            records=sum(1 for path in compare_cache.glob("*.json") if path.is_file()),
        ),
        ArtifactRef(
            path=display_path(roster_path),
            role="reviewer_roster",
            sha256=sha256_file(roster_path),
            records=len(roster),
        ),
    ]
    if parity_records and parity_records.exists():
        sources.append(
            ArtifactRef(
                path=display_path(parity_records),
                role="episode_parity_reference",
                schema_version="pr_review_v2/0.1",
                sha256=sha256_file(parity_records),
                records=sum(1 for line in parity_records.read_text().splitlines() if line.strip()),
            )
        )
    if interventions_path and interventions_path.exists():
        sources.append(
            ArtifactRef(
                path=display_path(interventions_path),
                role="judgment_migration_reference",
                schema_version="i5",
                sha256=sha256_file(interventions_path),
                records=sum(1 for line in interventions_path.read_text().splitlines() if line.strip()),
            )
        )

    git_commit, tree_state = git_state()
    derived_artifacts = [
        ArtifactRef(
            path="derived/funnel.jsonl",
            role="eligibility_funnel",
            schema_version="funnel1",
            sha256=sha256_file(funnel_path),
            records=len(funnels),
        )
    ]
    if all_rounds:
        derived_artifacts.append(
            ArtifactRef(
                path="derived/round_segments.jsonl",
                role="review_round_segments",
                schema_version="round-segment1",
                sha256=sha256_file(segments_path),
                records=len(segments),
            )
        )

    episode_version = MULTI_ROUND_BUILDER_VERSION if all_rounds else RAW_EPISODE_BUILDER_VERSION
    manifest = DatasetManifest(
        dataset_id=dataset_id,
        release=release,
        source_kind="raw_event_ledger",
        split="development",
        sources=sources,
        source_artifacts=[
            ArtifactRef(
                path="source/events.jsonl",
                role="raw_event_index",
                schema_version="event1",
                sha256=sha256_file(events_path),
                records=len(events),
            )
        ],
        input_artifacts=[
            ArtifactRef(
                path="input/episodes.jsonl",
                role="reviewer_visible_episodes",
                schema_version="episode1",
                sha256=sha256_file(episodes_path),
                records=len(episodes),
            )
        ],
        gold_artifacts=[
            ArtifactRef(
                path="gold/episode_boundaries.jsonl",
                role="hidden_episode_boundaries",
                schema_version="episode-boundary1",
                sha256=sha256_file(boundaries_path),
                records=len(boundaries),
            )
        ],
        derived_artifacts=derived_artifacts,
        pr_numbers=sorted({episode.pr_number for episode in episodes}),
        corpus_cutoff_policy="comment.submitted_at < episode review start",
        generator_git_commit=git_commit,
        generator_tree_state=tree_state,
        generator_versions={
            "events": EVENT_LEDGER_VERSION,
            "episodes": episode_version,
            "funnel": RAW_EPISODE_BUILDER_VERSION,
        },
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build raw first-round PR Review v4 release")
    parser.add_argument("--bundles", type=Path, default=DEFAULT_BUNDLES)
    parser.add_argument("--compares", type=Path, default=DEFAULT_COMPARES)
    parser.add_argument("--roster", type=Path, default=DEFAULT_ROSTER)
    parser.add_argument("--parity-records", type=Path, default=DEFAULT_PARITY_RECORDS)
    parser.add_argument("--interventions", type=Path, default=DEFAULT_INTERVENTIONS)
    parser.add_argument("--out", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--dataset-id", default="mathlib-pr-review-v4-dev")
    parser.add_argument("--release", default="0.3.0-raw-first-round")
    parser.add_argument("--created-at", default=None)
    parser.add_argument("--all-rounds", action="store_true")
    args = parser.parse_args()
    manifest = build_raw_release(
        bundles_dir=args.bundles,
        compare_cache=args.compares,
        roster_path=args.roster,
        release_dir=args.out,
        parity_records=args.parity_records,
        interventions_path=args.interventions,
        dataset_id=args.dataset_id,
        release=args.release,
        created_at=args.created_at,
        all_rounds=args.all_rounds,
    )
    episode_ref = next(
        artifact
        for artifact in manifest.input_artifacts
        if artifact.schema_version == "episode1"
    )
    segment_ref = next(
        (
            artifact
            for artifact in manifest.derived_artifacts
            if artifact.schema_version == "round-segment1"
        ),
        None,
    )
    print(
        json.dumps(
            {
                "release": str(args.out),
                "prs": len(manifest.pr_numbers),
                "episodes": episode_ref.records,
                "round_segments": segment_ref.records if segment_ref else 0,
                "source_kind": manifest.source_kind,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
