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
from typing import Dict, List

from .io import load_jsonl, pretty_json_bytes, sha256_file, write_once
from .paths import assert_repo_root
from .releases import ArtifactSpec, build_release, parent_release_ref
from .render_prompts import render_all
from .schema import (
    ChangeGraph,
    InterventionView,
    JudgmentNode,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)
from .work_units import build_work_units, validate_work_unit_coverage

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


def rerender(parent: Path, out: Path, renderer_version: str, release_name: str) -> Dict:
    assert_repo_root()
    graphs = load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
    episodes = load_jsonl(parent / "input/episodes.jsonl", ReviewEpisodeInput)

    units = build_work_units(graphs, renderer_version=renderer_version)
    validate_work_unit_coverage(graphs, units)
    prompts = render_all(units, episodes, graphs, [])

    old_units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)
    old_prompts = load_jsonl(parent / "derived/rendered_prompts.jsonl", RenderedPrompt)

    carried = []
    for relative, schema, role in _CARRIED:
        source = parent / relative
        if not source.is_file():
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
        "manifest_sha256": sha256_file(out / "manifest.json"),
    }
    write_once(out / "rerender_report.json", pretty_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-render a release at a new renderer version")
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--renderer-version", required=True)
    parser.add_argument("--release-name", required=True)
    args = parser.parse_args()
    print(json.dumps(
        rerender(args.parent, args.out, args.renderer_version, args.release_name), indent=2
    ))


if __name__ == "__main__":
    main()
