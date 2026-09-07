"""Human-readable audit summaries for PR Review v4 releases."""

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from src.mathlib_review.schema import DatasetManifest, ReviewEpisodeInput, ReviewRoundSegment, SourceEvent
from src.mathlib_review.release.validate import validate_release


def _distribution(values: Iterable[int]) -> Dict[str, float]:
    ordered = sorted(values)
    if not ordered:
        return {"min": 0, "median": 0, "p95": 0, "max": 0}
    p95_index = min(len(ordered) - 1, int(0.95 * (len(ordered) - 1)))
    return {
        "min": ordered[0],
        "median": statistics.median(ordered),
        "p95": ordered[p95_index],
        "max": ordered[-1],
    }


def audit_release(release_dir: Path, *, sample_prs: Iterable[int] = ()) -> Dict[str, Any]:
    validation = validate_release(release_dir)
    manifest = DatasetManifest.model_validate_json((release_dir / "manifest.json").read_text())
    episode_ref = next(
        artifact for artifact in manifest.input_artifacts if artifact.schema_version == "episode1"
    )
    episodes = [
        ReviewEpisodeInput.model_validate_json(line)
        for line in (release_dir / episode_ref.path).read_text().splitlines()
        if line.strip()
    ]
    event_ref = next(
        (artifact for artifact in manifest.source_artifacts if artifact.schema_version == "event1"),
        None,
    )
    events: List[SourceEvent] = []
    if event_ref:
        events = [
            SourceEvent.model_validate_json(line)
            for line in (release_dir / event_ref.path).read_text().splitlines()
            if line.strip()
        ]

    event_counts = Counter(event.event_type for event in events)
    missing_times = Counter(event.event_type for event in events if event.occurred_at is None)
    events_by_pr: Dict[int, Counter] = defaultdict(Counter)
    for event in events:
        events_by_pr[event.pr_number][event.event_type] += 1
    requested = list(sample_prs)
    if not requested:
        requested = [episode.pr_number for episode in episodes[:3]]
    by_pr = {episode.pr_number: episode for episode in episodes if episode.round_index == 1}
    samples = []
    for pr_number in requested:
        episode = by_pr.get(pr_number)
        if episode is None:
            samples.append({"pr_number": pr_number, "error": "not in release"})
            continue
        samples.append(
            {
                "pr_number": pr_number,
                "episode_id": episode.episode_id,
                "title": episode.title.text,
                "title_provenance": episode.title.provenance,
                "description_provenance": episode.description.provenance,
                "changed_files": episode.changed_files,
                "diff_chars": len(episode.diff),
                "events_by_type": dict(sorted(events_by_pr[pr_number].items())),
            }
        )

    segment_ref = next(
        (
            artifact
            for artifact in manifest.derived_artifacts
            if artifact.schema_version == "round-segment1"
        ),
        None,
    )
    segments: List[ReviewRoundSegment] = []
    if segment_ref:
        segments = [
            ReviewRoundSegment.model_validate_json(line)
            for line in (release_dir / segment_ref.path).read_text().splitlines()
            if line.strip()
        ]
    segment_counts = Counter(item.pr_number for item in segments)
    unhydrated = [
        {
            "segment_id": item.segment_id,
            "pr_number": item.pr_number,
            "round_index": item.round_index,
            "reviewed_head_sha": item.reviewed_head_sha,
            "reason": item.exclusion_reason,
        }
        for item in segments
        if item.hydration_status != "hydrated"
    ]
    warnings = [
        "Legacy migration episodes are not a frozen benchmark release."
        if manifest.source_kind == "legacy_migration"
        else None,
        "Generator worktree was dirty; rely on artifact hashes, not commit alone."
        if manifest.generator_tree_state == "dirty"
        else None,
    ]
    return {
        "release": {
            "dataset_id": manifest.dataset_id,
            "version": manifest.release,
            "source_kind": manifest.source_kind,
            "split": manifest.split,
            "manifest_tree_state": manifest.generator_tree_state,
        },
        "validation": validation,
        "input": {
            "description_provenance": dict(
                sorted(Counter(e.description.provenance for e in episodes).items())
            ),
            "title_provenance": dict(sorted(Counter(e.title.provenance for e in episodes).items())),
            "changed_files_per_episode": _distribution(len(e.changed_files) for e in episodes),
            "diff_chars": _distribution(len(e.diff) for e in episodes),
        },
        "events": {
            "by_type": dict(sorted(event_counts.items())),
            "missing_timestamp_by_type": dict(sorted(missing_times.items())),
        },
        "rounds": {
            "segments": len(segments),
            "hydrated_episodes": sum(
                item.hydration_status == "hydrated" for item in segments
            ),
            "hydration_status": dict(
                sorted(Counter(item.hydration_status for item in segments).items())
            ),
            "segments_by_round_index": dict(
                sorted(Counter(item.round_index for item in segments).items())
            ),
            "prs_by_segment_count": dict(
                sorted(Counter(segment_counts.values()).items())
            ),
            "segments_per_pr": _distribution(segment_counts.values()),
            "unhydrated": unhydrated,
        },
        "samples": samples,
        "warnings": [warning for warning in warnings if warning],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a PR Review v4 release")
    parser.add_argument("release", type=Path)
    parser.add_argument("--prs", type=int, nargs="*", default=[])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = audit_release(args.release, sample_prs=args.prs)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
