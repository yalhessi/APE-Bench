"""Inspect one stored cg1 graph without exposing hidden review feedback."""

import argparse
import json
from pathlib import Path

from src.mathlib_review.schema import ChangeGraph, DatasetManifest


def inspect_change_graph(
    release_dir: Path,
    *,
    pr_number: int,
    round_index: int,
    path: str | None = None,
    kind: str | None = None,
    full: bool = False,
) -> dict:
    manifest = DatasetManifest.model_validate_json((release_dir / "manifest.json").read_text())
    graph_ref = next(
        item for item in manifest.derived_artifacts if item.schema_version == "cg1"
    )
    graph = next(
        (
            ChangeGraph.model_validate_json(line)
            for line in (release_dir / graph_ref.path).read_text().splitlines()
            if line.strip()
            and json.loads(line).get("pr_number") == pr_number
            and json.loads(line).get("round_index") == round_index
        ),
        None,
    )
    if graph is None:
        raise ValueError(f"PR {pr_number} round {round_index} has no change graph")
    if full:
        return graph.model_dump(mode="json")
    targets = [
        item
        for item in graph.targets
        if (path is None or item.path == path) and (kind is None or item.kind == kind)
    ]
    return {
        "graph_id": graph.graph_id,
        "episode_id": graph.episode_id,
        "pr_number": graph.pr_number,
        "round_index": graph.round_index,
        "changed_ranges": len(graph.changed_ranges),
        "semantic_entities": len(graph.entities),
        "targets": [
            {
                "change_id": item.change_id,
                "kind": item.kind,
                "path": item.path,
                "declaration_name": item.declaration_name,
                "declaration_kind": item.declaration_kind,
                "changed_range_ids": item.changed_range_ids,
                "parse_status": item.parse_status,
            }
            for item in targets
        ],
        "file_coverage": [
            item.model_dump(mode="json")
            for item in graph.file_coverage
            if path is None or item.path == path
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect one PR Review v4 change graph")
    parser.add_argument("release", type=Path)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--path", default=None)
    parser.add_argument("--kind", default=None)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    rendered = json.dumps(
        inspect_change_graph(
            args.release,
            pr_number=args.pr,
            round_index=args.round,
            path=args.path,
            kind=args.kind,
            full=args.full,
        ),
        indent=2,
        ensure_ascii=False,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
