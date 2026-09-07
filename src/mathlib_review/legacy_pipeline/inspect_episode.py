"""Inspect one episode and dereference its raw source events.

This is an audit utility. Event payloads include hidden maintainer feedback and must never be used as
reviewer input.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

from src.mathlib_review.release.events import payload_at_source_key
from src.mathlib_review.schema import DatasetManifest, ReviewEpisodeInput, ReviewRoundSegment, SourceEvent


def inspect_episode(
    release_dir: Path, pr_number: int, event_types: List[str], round_index: int = 1
) -> Dict:
    manifest = DatasetManifest.model_validate_json((release_dir / "manifest.json").read_text())
    episode_ref = next(
        artifact for artifact in manifest.input_artifacts if artifact.schema_version == "episode1"
    )
    episode = next(
        (
            ReviewEpisodeInput.model_validate_json(line)
            for line in (release_dir / episode_ref.path).read_text().splitlines()
            if line.strip()
            and json.loads(line).get("pr_number") == pr_number
            and json.loads(line).get("round_index") == round_index
        ),
        None,
    )
    segment_ref = next(
        (
            artifact
            for artifact in manifest.derived_artifacts
            if artifact.schema_version == "round-segment1"
        ),
        None,
    )
    segment = None
    if segment_ref:
        segment = next(
            (
                ReviewRoundSegment.model_validate_json(line)
                for line in (release_dir / segment_ref.path).read_text().splitlines()
                if line.strip()
                and json.loads(line).get("pr_number") == pr_number
                and json.loads(line).get("round_index") == round_index
            ),
            None,
        )
    if episode is None and segment is None:
        raise ValueError(f"PR {pr_number} round {round_index} is not in release")
    event_ref = next(
        (artifact for artifact in manifest.source_artifacts if artifact.schema_version == "event1"),
        None,
    )
    events: List[SourceEvent] = []
    if event_ref:
        events = [
            SourceEvent.model_validate_json(line)
            for line in (release_dir / event_ref.path).read_text().splitlines()
            if line.strip() and json.loads(line).get("pr_number") == pr_number
        ]
    allowed = set(event_types)
    if allowed:
        events = [event for event in events if event.event_type in allowed]
    bundle_cache: Dict[str, Dict] = {}
    rendered_events = []
    for event in events:
        source_path = event.source_object.path
        if source_path not in bundle_cache:
            bundle_cache[source_path] = json.loads(Path(source_path).read_text())
        rendered_events.append(
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "occurred_at": event.occurred_at,
                "actor": event.actor,
                "source": f"{source_path}{event.source_key}",
                "payload": payload_at_source_key(bundle_cache[source_path], event.source_key),
            }
        )
    return {
        "warning": "AUDIT ONLY: source events contain hidden maintainer feedback",
        "round_segment": segment.model_dump(mode="json") if segment else None,
        "episode_input": episode.model_dump(mode="json") if episode else None,
        "source_events": rendered_events,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect one PR Review v4 episode")
    parser.add_argument("release", type=Path)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--types", nargs="*", default=[])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    rendered = json.dumps(
        inspect_episode(args.release, args.pr, args.types, args.round),
        indent=2,
        ensure_ascii=False,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
