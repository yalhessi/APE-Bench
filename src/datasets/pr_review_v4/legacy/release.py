"""Build an immutable PR Review v4 development release.

The current command creates a `legacy_migration` episode release. It is deliberately labeled as a
bootstrap artifact until a raw-event builder reproduces these first-round episodes.
"""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from ..episodes import LEGACY_EPISODE_ADAPTER_VERSION, project_legacy_record
from ..events import EVENT_LEDGER_VERSION, build_event_ledger
from ..io import (
    display_path,
    git_state,
    jsonl_bytes,
    pretty_json_bytes,
    sha256_directory,
    sha256_file,
    write_once,
)
from ..schema import ArtifactRef, DatasetManifest, ReviewEpisodeInput
from ..paths import LEGACY_INTERVENTIONS_V5, LEGACY_V2_ANNOTATED, LEGACY_V2_BUNDLES


DEFAULT_RECORDS = LEGACY_V2_ANNOTATED
DEFAULT_BUNDLES = LEGACY_V2_BUNDLES
DEFAULT_INTERVENTIONS = LEGACY_INTERVENTIONS_V5
DEFAULT_RELEASE = Path("inputs/pr_review_v4/releases/dev-migration-0.1.0")


def _load_records(path: Path, prs: Optional[Iterable[int]] = None) -> List[Dict]:
    wanted = set(prs or [])
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if wanted:
        records = [record for record in records if int(record["pr_number"]) in wanted]
        missing = wanted - {int(record["pr_number"]) for record in records}
        if missing:
            raise ValueError(f"requested PRs absent from migration source: {sorted(missing)}")
    return sorted(records, key=lambda record: int(record["pr_number"]))


def build_legacy_migration_release(
    *,
    records_path: Path,
    release_dir: Path,
    raw_bundles: Optional[Path] = None,
    interventions_path: Optional[Path] = None,
    dataset_id: str = "mathlib-pr-review-v4-dev",
    release: str = "0.1.0-migration",
    split: str = "development",
    prs: Optional[Iterable[int]] = None,
    created_at: Optional[str] = None,
    include_events: bool = False,
) -> DatasetManifest:
    records = _load_records(records_path, prs)
    episodes: List[ReviewEpisodeInput] = [project_legacy_record(record) for record in records]
    episodes_path = release_dir / "input" / "episodes.jsonl"
    episodes_content = jsonl_bytes(episodes)
    write_once(episodes_path, episodes_content)

    manifest_path = release_dir / "manifest.json"
    if manifest_path.exists():
        existing = DatasetManifest.model_validate_json(manifest_path.read_text())
        expected_hash = sha256_file(episodes_path)
        episode_ref = next(
            (item for item in existing.input_artifacts if item.schema_version == "episode1"), None
        )
        requested = (dataset_id, release, split, [episode.pr_number for episode in episodes])
        recorded = (existing.dataset_id, existing.release, existing.split, existing.pr_numbers)
        if requested != recorded or episode_ref is None or episode_ref.sha256 != expected_hash:
            raise FileExistsError(
                f"existing release manifest is incompatible with requested build: {manifest_path}"
            )
        has_events = any(item.schema_version == "event1" for item in existing.source_artifacts)
        if include_events != has_events:
            raise FileExistsError(
                f"existing release event-ledger setting differs from requested build: {manifest_path}"
            )
        return existing

    sources = [
        ArtifactRef(
            path=display_path(records_path),
            role="episode_parity_reference",
            schema_version="pr_review_v2/0.1",
            sha256=sha256_file(records_path),
            records=len(records),
        )
    ]
    if raw_bundles and raw_bundles.exists():
        sources.append(
            ArtifactRef(
                path=display_path(raw_bundles),
                role="raw_github_bundles",
                sha256=sha256_directory(raw_bundles),
                records=sum(1 for path in raw_bundles.glob("*.json") if path.is_file()),
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

    source_artifacts = []
    event_version = "pending"
    if include_events:
        if not raw_bundles or not raw_bundles.exists():
            raise ValueError("--include-events requires an existing raw bundle directory")
        events_path = release_dir / "source" / "events.jsonl"
        events, _event_report = build_event_ledger(
            bundles_dir=raw_bundles,
            out=events_path,
            prs=[episode.pr_number for episode in episodes],
        )
        source_artifacts.append(
            ArtifactRef(
                path="source/events.jsonl",
                role="raw_event_index",
                schema_version="event1",
                sha256=sha256_file(events_path),
                records=len(events),
            )
        )
        event_version = EVENT_LEDGER_VERSION

    created_at = created_at or datetime.now(timezone.utc).isoformat()
    git_commit, tree_state = git_state()
    manifest = DatasetManifest(
        dataset_id=dataset_id,
        release=release,
        source_kind="legacy_migration",
        split=split,
        sources=sources,
        source_artifacts=source_artifacts,
        input_artifacts=[
            ArtifactRef(
                path="input/episodes.jsonl",
                role="reviewer_visible_episodes",
                schema_version="episode1",
                sha256=sha256_file(episodes_path),
                records=len(episodes),
            )
        ],
        pr_numbers=[episode.pr_number for episode in episodes],
        corpus_cutoff_policy="comment.submitted_at < episode review start",
        generator_git_commit=git_commit,
        generator_tree_state=tree_state,
        generator_versions={
            "events": event_version,
            "episodes": LEGACY_EPISODE_ADAPTER_VERSION,
        },
        created_at=created_at,
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a PR Review v4 migration release")
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--raw-bundles", type=Path, default=DEFAULT_BUNDLES)
    parser.add_argument("--interventions", type=Path, default=DEFAULT_INTERVENTIONS)
    parser.add_argument("--out", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--dataset-id", default="mathlib-pr-review-v4-dev")
    parser.add_argument("--release", default="0.1.0-migration")
    parser.add_argument("--split", choices=("development", "validation", "test"),
                        default="development")
    parser.add_argument("--prs", type=int, nargs="*")
    parser.add_argument("--created-at", default=None)
    parser.add_argument("--include-events", action="store_true")
    args = parser.parse_args()
    manifest = build_legacy_migration_release(
        records_path=args.records,
        release_dir=args.out,
        raw_bundles=args.raw_bundles,
        interventions_path=args.interventions,
        dataset_id=args.dataset_id,
        release=args.release,
        split=args.split,
        prs=args.prs,
        created_at=args.created_at,
        include_events=args.include_events,
    )
    print(
        json.dumps(
            {
                "release": str(args.out),
                "episodes": len(manifest.pr_numbers),
                "source_kind": manifest.source_kind,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
