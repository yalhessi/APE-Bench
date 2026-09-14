"""Stable, complete candidate-generation work units over cg1 targets."""

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, sha256_bytes, write_once
from src.mathlib_review.schema import ChangeGraph, ChangeTarget, ReviewWorkUnit


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


def _pack_bundles(graph: ChangeGraph) -> List[List[ChangeTarget]]:
    """Pack same-file targets, keeping a declaration with its doc-comment and attributes.

    Two defects in the old packer, both measured on `dev-medium-0.3.0`:

    * **A declaration was separated from its own doc-comment.** The sort key is a content hash,
      so the two landed wherever it put them: the doc-comment for `IsMulIndecomposable.baseOf`
      went to `wu:d60bad80…` and the declaration to `wu:07d1ab97…`, and 38 of 59 doc-comments
      sat in a unit holding no declaration at all. Bundling by `attached_to` fixes it at the
      source, and the bundle is packed whole or not at all.

    * **The budget was charged on text the renderer prints once.** `size` summed every target's
      `diff_fragments`, but a work unit is related changes in one file, so its targets usually
      share a hunk and the renderer emits each distinct one once. PR 33145 has exactly one
      5,196-char fragment on all 12 targets; the packer charged 62,352 and split a six-theorem
      family across four units whose real content is 10,198 characters — 42% of one unit's
      budget. Charging a fragment once per unit takes the release from 203 units to 92, and
      PR 33149 from 108 to 12.

    Gated at `candidate-prompt/13`: `renderer_version` is inside the work-unit identity, so an
    earlier release re-derives to exactly the units it froze.
    """

    bundles: Dict[str, List[ChangeTarget]] = {}
    for target in sorted(graph.targets, key=lambda item: (item.path, item.change_id)):
        owner = target.attached_to if target.attached_to else target.change_id
        bundles.setdefault(owner, []).append(target)
    # An attachment whose owner is in another file, or absent, stands on its own rather than
    # being dragged across a file boundary.
    by_id = {item.change_id: item for item in graph.targets}
    ordered: List[Tuple[str, str, List[ChangeTarget]]] = []
    for owner, members in bundles.items():
        head = by_id.get(owner) or members[0]
        ordered.append((head.path, owner, members))

    groups: List[List[ChangeTarget]] = []
    current: List[ChangeTarget] = []
    current_path: Optional[str] = None
    current_chars = 0
    seen_fragments: set = set()
    for path, _owner, members in sorted(ordered, key=lambda row: (row[0], row[1])):
        size = 0
        fragments = set()
        for target in members:
            for fragment in target.diff_fragments:
                if fragment not in seen_fragments and fragment not in fragments:
                    fragments.add(fragment)
                    size += len(fragment)
            size += len(target.base_code or "") + len(target.reviewed_code or "") + 500
        if current and (path != current_path
                        or current_chars + size > MAX_TARGET_CONTENT_CHARS):
            groups.append(current)
            current, current_chars, seen_fragments = [], 0, set()
            size = sum(len(f) for target in members for f in set(target.diff_fragments))
            size += sum(len(t.base_code or "") + len(t.reviewed_code or "") + 500
                        for t in members)
        current.extend(members)
        seen_fragments |= fragments
        current_path, current_chars = path, current_chars + size
    if current:
        groups.append(current)
    return groups


def build_work_units(
    graphs: Iterable[ChangeGraph], renderer_version: str = RENDERER_VERSION,
) -> List[ReviewWorkUnit]:
    """Pack complete same-file targets without ever splitting or truncating a target."""
    graphs = list(graphs)
    units = []
    for graph in sorted(graphs, key=lambda item: (item.pr_number, item.round_index)):
        if _renderer_number(renderer_version) >= 13:
            groups = _pack_bundles(graph)
        else:
            groups, current, current_path, current_chars = [], [], None, 0
            for target in sorted(graph.targets, key=lambda item: (item.path, item.change_id)):
                size = sum(len(item) for item in target.diff_fragments)
                size += len(target.base_code or "") + len(target.reviewed_code or "") + 500
                if current and (target.path != current_path
                                or current_chars + size > MAX_TARGET_CONTENT_CHARS):
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
