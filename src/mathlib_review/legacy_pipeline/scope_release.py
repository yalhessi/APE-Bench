"""Package i5-to-cg1 scope proposals as an immutable gold-only v4 release."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from src.mathlib_review.io import (
    display_path,
    git_state,
    jsonl_bytes,
    pretty_json_bytes,
    sha256_file,
    write_once,
)
from .migrate_interventions import SCOPE_MIGRATION_VERSION, build_scope_migrations
from src.mathlib_review.schema import ArtifactRef, DatasetManifest
from src.mathlib_review.paths import LEGACY_INTERVENTIONS_V5, LEGACY_V2_ANNOTATED


DEFAULT_BASE_RELEASE = Path("inputs/pr_review_v4/releases/dev-change-graph-0.5.1")
DEFAULT_RELEASE = Path("inputs/pr_review_v4/releases/dev-scope-map-0.6.1")
DEFAULT_INTERVENTIONS = LEGACY_INTERVENTIONS_V5
DEFAULT_RECORDS = LEGACY_V2_ANNOTATED


def build_scope_release(
    *,
    base_release: Path,
    interventions_path: Path,
    records_path: Path,
    release_dir: Path,
    release: str = "0.6.1-scope-map",
    created_at: Optional[str] = None,
) -> DatasetManifest:
    manifest_path = release_dir / "manifest.json"
    if manifest_path.exists():
        existing = DatasetManifest.model_validate_json(manifest_path.read_text())
        if existing.release != release:
            raise FileExistsError(f"existing release has incompatible identity: {manifest_path}")
        return existing

    base_manifest_path = base_release / "manifest.json"
    base = DatasetManifest.model_validate_json(base_manifest_path.read_text())
    inherited = (
        base.source_artifacts
        + base.input_artifacts
        + base.gold_artifacts
        + base.derived_artifacts
    )
    for artifact in inherited:
        write_once(release_dir / artifact.path, (base_release / artifact.path).read_bytes())

    migrations, report = build_scope_migrations(
        release_dir=base_release,
        interventions_path=interventions_path,
        records_path=records_path,
    )
    mapping_path = release_dir / "gold" / "intervention_scope_migrations.jsonl"
    report_path = release_dir / "gold" / "intervention_scope_report.json"
    write_once(mapping_path, jsonl_bytes(migrations))
    write_once(report_path, pretty_json_bytes(report))
    mapping_ref = ArtifactRef(
        path="gold/intervention_scope_migrations.jsonl",
        role="i5_to_cg1_scope_proposals",
        schema_version="i5-cg1-map1",
        sha256=sha256_file(mapping_path),
        records=len(migrations),
    )
    report_ref = ArtifactRef(
        path="gold/intervention_scope_report.json",
        role="scope_mapping_review_report",
        schema_version="scope-map-audit1",
        sha256=sha256_file(report_path),
        records=len(report["review_queue"]),
    )
    git_commit, tree_state = git_state()
    manifest = base.model_copy(
        update={
            "release": release,
            "sources": [
                *base.sources,
                ArtifactRef(
                    path=display_path(base_manifest_path),
                    role="parent_release_manifest",
                    schema_version=base.schema_version,
                    sha256=sha256_file(base_manifest_path),
                    records=len(base.pr_numbers),
                ),
                ArtifactRef(
                    path=display_path(interventions_path),
                    role="scope_migration_source",
                    schema_version="i5",
                    sha256=sha256_file(interventions_path),
                    records=len(migrations),
                ),
            ],
            "gold_artifacts": [*base.gold_artifacts, mapping_ref, report_ref],
            "generator_git_commit": git_commit,
            "generator_tree_state": tree_state,
            "generator_versions": {
                **base.generator_versions,
                "scope_mapping": SCOPE_MIGRATION_VERSION,
            },
            "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        }
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build immutable v4 scope-map release")
    parser.add_argument("--base-release", type=Path, default=DEFAULT_BASE_RELEASE)
    parser.add_argument("--interventions", type=Path, default=DEFAULT_INTERVENTIONS)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    parser.add_argument("--out", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--release", default="0.6.1-scope-map")
    parser.add_argument("--created-at", default=None)
    args = parser.parse_args()
    manifest = build_scope_release(
        base_release=args.base_release,
        interventions_path=args.interventions,
        records_path=args.records,
        release_dir=args.out,
        release=args.release,
        created_at=args.created_at,
    )
    mapping_ref = next(
        item for item in manifest.gold_artifacts if item.schema_version == "i5-cg1-map1"
    )
    print(
        json.dumps(
            {
                "release": str(args.out),
                "prs": len(manifest.pr_numbers),
                "scope_migrations": mapping_ref.records,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
