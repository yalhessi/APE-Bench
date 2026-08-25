"""Package conservative jg1 proposals as an immutable PR Review v4 release."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from ..io import (
    display_path,
    git_state,
    jsonl_bytes,
    pretty_json_bytes,
    sha256_file,
    write_once,
)
from .judgment_graph import JUDGMENT_MIGRATION_VERSION, build_judgment_artifacts
from ..schema import ArtifactRef, DatasetManifest
from ..paths import LEGACY_INTERVENTIONS_V5


DEFAULT_BASE_RELEASE = Path("inputs/pr_review_v4/releases/dev-scope-map-0.6.1")
DEFAULT_RELEASE = Path("inputs/pr_review_v4/releases/dev-judgment-draft-0.7.0")
DEFAULT_INTERVENTIONS = LEGACY_INTERVENTIONS_V5


def build_judgment_release(
    *,
    base_release: Path,
    interventions_path: Path,
    release_dir: Path,
    release: str = "0.7.0-judgment-draft",
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

    judgments, outcomes, views, report = build_judgment_artifacts(
        scope_release=base_release,
        interventions_path=interventions_path,
    )
    judgments_path = release_dir / "gold" / "judgments.jsonl"
    outcomes_path = release_dir / "gold" / "outcome_observations.jsonl"
    views_path = release_dir / "gold" / "intervention_views.jsonl"
    report_path = release_dir / "gold" / "judgment_report.json"
    write_once(judgments_path, jsonl_bytes(judgments))
    write_once(outcomes_path, jsonl_bytes(outcomes))
    write_once(views_path, jsonl_bytes(views))
    write_once(report_path, pretty_json_bytes(report))
    additions = [
        ArtifactRef(
            path="gold/judgments.jsonl",
            role="judgment_graph_proposals",
            schema_version="jg1",
            sha256=sha256_file(judgments_path),
            records=len(judgments),
        ),
        ArtifactRef(
            path="gold/outcome_observations.jsonl",
            role="separate_outcome_observations",
            schema_version="outcome-observation1",
            sha256=sha256_file(outcomes_path),
            records=len(outcomes),
        ),
        ArtifactRef(
            path="gold/intervention_views.jsonl",
            role="intervention_evaluation_views",
            schema_version="view1",
            sha256=sha256_file(views_path),
            records=len(views),
        ),
        ArtifactRef(
            path="gold/judgment_report.json",
            role="judgment_migration_review_report",
            schema_version="jg-audit1",
            sha256=sha256_file(report_path),
            records=len(report["decomposition_review"]),
        ),
    ]
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
            ],
            "gold_artifacts": [*base.gold_artifacts, *additions],
            "generator_git_commit": git_commit,
            "generator_tree_state": tree_state,
            "generator_versions": {
                **base.generator_versions,
                "judgment_graph": JUDGMENT_MIGRATION_VERSION,
            },
            "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        }
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build immutable PR Review v4 jg1 draft")
    parser.add_argument("--base-release", type=Path, default=DEFAULT_BASE_RELEASE)
    parser.add_argument("--interventions", type=Path, default=DEFAULT_INTERVENTIONS)
    parser.add_argument("--out", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--release", default="0.7.0-judgment-draft")
    parser.add_argument("--created-at", default=None)
    args = parser.parse_args()
    manifest = build_judgment_release(
        base_release=args.base_release,
        interventions_path=args.interventions,
        release_dir=args.out,
        release=args.release,
        created_at=args.created_at,
    )
    judgments_ref = next(item for item in manifest.gold_artifacts if item.schema_version == "jg1")
    print(
        json.dumps(
            {
                "release": str(args.out),
                "prs": len(manifest.pr_numbers),
                "judgments": judgments_ref.records,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
