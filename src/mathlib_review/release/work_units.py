"""Stable, complete candidate-generation work units over cg1 targets."""

import argparse
import json
from pathlib import Path
from typing import Iterable, List

from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, sha256_bytes, write_once
from src.mathlib_review.schema import ChangeGraph, ReviewWorkUnit


WORK_UNIT_VERSION = "work-units/1"
RENDERER_VERSION = "candidate-prompt/11"


def _renderer_number(renderer_version: str) -> int:
    try:
        return int(renderer_version.rsplit("/", 1)[-1])
    except (ValueError, IndexError):
        return 0
MAX_TARGET_CONTENT_CHARS = 24_000


def _load_graphs(path: Path) -> List[ChangeGraph]:
    return [ChangeGraph.model_validate_json(line) for line in path.read_text().splitlines() if line]


def build_work_units(
    graphs: Iterable[ChangeGraph], renderer_version: str = RENDERER_VERSION,
) -> List[ReviewWorkUnit]:
    """Pack complete same-file targets without ever splitting or truncating a target."""
    graphs = list(graphs)
    units = []
    for graph in sorted(graphs, key=lambda item: (item.pr_number, item.round_index)):
        groups, current, current_path, current_chars = [], [], None, 0
        for target in sorted(graph.targets, key=lambda item: (item.path, item.change_id)):
            size = sum(len(item) for item in target.diff_fragments)
            size += len(target.base_code or "") + len(target.reviewed_code or "") + 500
            if current and (target.path != current_path or current_chars + size > MAX_TARGET_CONTENT_CHARS):
                groups.append(current)
                current, current_chars = [], 0
            current.append(target)
            current_path, current_chars = target.path, current_chars + size
        if current:
            groups.append(current)
        for group in groups:
            change_ids = [target.change_id for target in group]
            identity = {
                "episode_id": graph.episode_id,
                "graph_id": graph.graph_id,
                "change_ids": change_ids,
                "target_sha256s": {target.change_id: target.source_sha256 for target in group},
                "entity_ids_by_change": {
                    target.change_id: target.reviewed_entity_ids + target.base_entity_ids
                    for target in group
                },
                "primary_subjects_by_change": {
                    target.change_id: target.declaration_name or target.path for target in group
                },
                "renderer_version": renderer_version,
            }
            # Only from /12, in the identity *and* on the record. Adding it to the identity
            # unconditionally would change every frozen `work_unit_id`; populating it on a
            # /11 record would make a rebuilt unit unequal to its frozen counterpart while
            # claiming to record data that release never captured.
            paths_by_change = (
                {target.change_id: target.path for target in group}
                if _renderer_number(renderer_version) >= 12 else {}
            )
            if paths_by_change:
                identity["paths_by_change"] = paths_by_change
            digest = sha256_bytes(canonical_json_bytes(identity))
            units.append(ReviewWorkUnit(
                work_unit_id=f"wu:{digest[:24]}", episode_id=graph.episode_id,
                graph_id=graph.graph_id, repo=graph.repo, pr_number=graph.pr_number,
                round_index=graph.round_index, change_ids=change_ids,
                target_sha256s=identity["target_sha256s"],
                paths_by_change=paths_by_change,
                entity_ids_by_change=identity["entity_ids_by_change"],
                primary_subjects_by_change=identity["primary_subjects_by_change"],
                renderer_version=renderer_version, source_sha256=digest,
            ))
    validate_work_unit_coverage(graphs, units)
    return units


def validate_work_unit_coverage(graphs: Iterable[ChangeGraph], units: Iterable[ReviewWorkUnit]) -> None:
    expected = [target.change_id for graph in graphs for target in graph.targets]
    actual = [change_id for unit in units for change_id in unit.change_ids]
    if len(actual) != len(set(actual)):
        raise ValueError("work-unit schedule contains duplicate change IDs")
    if set(expected) != set(actual):
        raise ValueError(
            f"work-unit coverage mismatch: missing={sorted(set(expected)-set(actual))[:5]} "
            f"extra={sorted(set(actual)-set(expected))[:5]}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graphs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    graphs = _load_graphs(args.graphs)
    units = build_work_units(graphs)
    write_once(args.out, jsonl_bytes(units))
    print(json.dumps({"work_units": len(units), "targets": len(units)}, indent=2))


if __name__ == "__main__":
    main()
