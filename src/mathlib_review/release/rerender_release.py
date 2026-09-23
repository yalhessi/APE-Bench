"""Re-render a benchmark release's work units and prompts at a new renderer version.

A renderer bump is not an edit — it is a new release. `renderer_version` is inside the
work-unit identity payload (`work_units.py`), so `work_unit_id` changes with it and every
`wu:…` in the old release, its run plans, its candidate files and its sealed conditions
stops joining. Rewriting in place would silently break all of them at once.

Everything except `derived/work_units.jsonl` and `derived/rendered_prompts.jsonl` is carried
through byte-identically: the change graphs, the visible episodes and the hidden gold are
the same data, and a re-render must not be an opportunity for them to drift. The result is
self-contained, because every consumer reads gold and episodes from the release directory.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from src.mathlib_review.io import load_jsonl, pretty_json_bytes, sha256_file, write_once
from src.mathlib_review.paths import assert_repo_root
from src.mathlib_review.release.releases import ArtifactSpec, build_release, parent_release_ref
from src.mathlib_review.agenda.render_prompts import render_all
from src.mathlib_review.schema import (
    ChangeGraph,
    InterventionView,
    JudgmentNode,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)
from src.mathlib_review.release.work_units import build_work_units, validate_work_unit_coverage

VERSION = "rerender-release/1"

#: Artifacts copied through unchanged, as (release-relative path, schema, role). Only the
#: two derived prompt artifacts are rebuilt; carrying the rest by copy keeps the new release
#: self-contained without giving anything a chance to change.
_CARRIED = (
    ("source/events.jsonl", None, "raw_event_ledger"),
    ("input/episodes.jsonl", "episode1", "reviewer_visible_episodes"),
    ("derived/change_graphs.jsonl", "cg1", "complete_change_graphs"),
    ("gold/judgments.jsonl", "judgment-node1", "hidden_judgments"),
    ("gold/intervention_views.jsonl", "intervention-view1", "hidden_intervention_views"),
    ("gold/outcome_observations.jsonl", None, "hidden_outcomes"),
    ("gold/intervention_scope_migrations.jsonl", None, "hidden_scope_maps"),
    ("gold/pilot_cases.jsonl", None, "pilot_case_semantics"),
    ("gold/episode_boundaries.jsonl", "episode-boundary1", "hidden_episode_boundaries"),
)


#: Gold artifacts that name `change_id`s and therefore have to be re-anchored when the change
#: graph is rebuilt. Everything else under `gold/` addresses episodes, not targets.
_GOLD_WITH_CHANGE_IDS = ("gold/judgments.jsonl", "gold/intervention_scope_migrations.jsonl")


def _change_id_remap(old: Sequence[ChangeGraph], new: Sequence[ChangeGraph]) -> Dict[str, str]:
    """Map a rebuilt graph's `change_id`s back to the parent's, by everything except `kind`.

    A target's identity payload is `(episode, kind, path, base_entity_ids, reviewed_entity_ids,
    range_ids)`. A builder that only renames kinds therefore moves exactly the reclassified
    targets and nothing else, and the remainder of the payload identifies each one uniquely --
    so the mapping is mechanical rather than a judgement call, and it is total or it raises.

    Refuses an ambiguous key rather than guessing: two targets that agree on everything but
    `kind` would make the re-anchoring arbitrary, and silently re-anchoring gold to the wrong
    site is the one failure this release path must not have.
    """

    def key(target) -> Tuple:
        return (target.episode_id, target.path, tuple(target.base_entity_ids),
                tuple(target.reviewed_entity_ids), tuple(target.changed_range_ids))

    def index(graphs: Sequence[ChangeGraph]) -> Dict[Tuple, str]:
        seen: Dict[Tuple, str] = {}
        for graph in graphs:
            for target in graph.targets:
                if key(target) in seen:
                    raise ValueError(f"ambiguous target identity: {key(target)}")
                seen[key(target)] = target.change_id
        return seen

    old_index, new_index = index(old), index(new)
    missing = set(old_index) - set(new_index)
    if missing:
        raise ValueError(f"{len(missing)} parent target(s) absent from the rebuilt graphs")
    return {old_id: new_index[k] for k, old_id in old_index.items()
            if new_index[k] != old_id}


def rerender(parent: Path, out: Path, renderer_version: str, release_name: str,
             graphs_path: Optional[Path] = None) -> Dict:
    assert_repo_root()
    parent_graphs = load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
    graphs = load_jsonl(graphs_path, ChangeGraph) if graphs_path else parent_graphs
    remap = _change_id_remap(parent_graphs, graphs) if graphs_path else {}
    episodes = load_jsonl(parent / "input/episodes.jsonl", ReviewEpisodeInput)

    units = build_work_units(graphs, renderer_version=renderer_version)
    validate_work_unit_coverage(graphs, units)
    prompts = render_all(units, episodes, graphs, [])

    old_units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)
    old_prompts = load_jsonl(parent / "derived/rendered_prompts.jsonl", RenderedPrompt)

    # A rebuilt graph is not a carried artifact, and neither is gold that points into it.
    rebuilt = {"derived/change_graphs.jsonl", *_GOLD_WITH_CHANGE_IDS} if graphs_path else set()
    carried = []
    for relative, schema, role in _CARRIED:
        source = parent / relative
        if not source.is_file() or relative in rebuilt:
            continue
        # Copied as raw bytes, not re-serialized models: a model round-trip could normalise
        # a field and change bytes that the parent's manifest hash still vouches for.
        carried.append((relative, schema, role, source))

    specs_by_section: Dict[str, List[ArtifactSpec]] = {
        "source_artifacts": [], "input_artifacts": [], "gold_artifacts": [],
        "derived_artifacts": [],
    }
    for relative, schema, role, source in carried:
        section = {
            "source": "source_artifacts", "input": "input_artifacts",
            "gold": "gold_artifacts", "derived": "derived_artifacts",
        }[relative.split("/", 1)[0]]
        specs_by_section[section].append(
            ArtifactSpec(rel_path=relative, raw_bytes=source.read_bytes(),
                         schema_version=schema, role=role)
        )
    specs_by_section["derived_artifacts"].extend([
        ArtifactSpec("derived/work_units.jsonl", units, "work-unit1", "candidate_work_units"),
        ArtifactSpec("derived/rendered_prompts.jsonl", prompts, "rendered-prompt1",
                     "production_prompt_preview"),
    ])
    if graphs_path:
        specs_by_section["derived_artifacts"].append(
            ArtifactSpec(rel_path="derived/change_graphs.jsonl",
                         raw_bytes=graphs_path.read_bytes(),
                         schema_version="cg1", role="complete_change_graphs"))
        # Re-anchored by substituting ids in the raw bytes. The parent's gold is validated
        # JSONL whose `change:` ids are opaque and unique, so a textual substitution moves
        # exactly the anchors and leaves every other byte alone -- which a model round-trip
        # would not promise, and this module already refuses round-trips for that reason.
        for relative in _GOLD_WITH_CHANGE_IDS:
            source = parent / relative
            if not source.is_file():
                continue
            text = source.read_text(encoding="utf-8")
            for old_id, new_id in remap.items():
                text = text.replace(old_id, new_id)
            schema, role = {r: (s, ro) for r, s, ro in _CARRIED}[relative]
            specs_by_section["gold_artifacts"].append(
                ArtifactSpec(rel_path=relative, raw_bytes=text.encode("utf-8"),
                             schema_version=schema, role=role))

    parent_manifest = json.loads((parent / "manifest.json").read_text(encoding="utf-8"))
    build_release(
        out,
        dataset_id=parent_manifest["dataset_id"],
        release=release_name,
        pr_numbers=parent_manifest["pr_numbers"],
        corpus_cutoff_policy=parent_manifest["corpus_cutoff_policy"],
        generator_versions={
            **parent_manifest["generator_versions"],
            "renderer": renderer_version,
            "rerender": VERSION,
        },
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        sources=[parent_release_ref(parent)],
        split=parent_manifest.get("split", "development"),
        **specs_by_section,
    )
    report = {
        "schema_version": "rerender-release-report1",
        "version": VERSION,
        "parent": str(parent),
        "renderer_version": renderer_version,
        "work_units": len(units),
        "prompts": len(prompts),
        # The point of the whole exercise: identities move, content is re-rendered.
        "work_unit_ids_changed": sum(
            new.work_unit_id != old.work_unit_id for new, old in zip(units, old_units)
        ),
        "prompt_hashes_changed": sum(
            new.prompt_sha256 != old.prompt_sha256 for new, old in zip(prompts, old_prompts)
        ),
        "units_carrying_paths": sum(1 for unit in units if unit.paths_by_change),
        "carried_artifacts": [relative for relative, _s, _r, _p in carried],
        "graphs_rebuilt": bool(graphs_path),
        "change_ids_reanchored": len(remap),
        "gold_reanchored": list(_GOLD_WITH_CHANGE_IDS) if graphs_path else [],
        "manifest_sha256": sha256_file(out / "manifest.json"),
    }
    write_once(out / "rerender_report.json", pretty_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-render a release at a new renderer version")
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--renderer-version", required=True)
    parser.add_argument(
        "--graphs", type=Path, default=None,
        help="rebuilt derived/change_graphs.jsonl. A change-graph builder bump is a new release "
             "for the same reason a renderer bump is, and it additionally moves the `change_id`s "
             "of every target it reclassifies, so the gold that anchors on them is re-anchored.")
    parser.add_argument("--release-name", required=True)
    args = parser.parse_args()
    print(json.dumps(
        rerender(args.parent, args.out, args.renderer_version, args.release_name,
                 graphs_path=args.graphs), indent=2
    ))


if __name__ == "__main__":
    main()
