"""Package a validated cg1 artifact as a new immutable PR Review v4 release."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from ..change_graph import CHANGE_GRAPH_BUILDER_VERSION, build_graph_artifact
from ..io import (
    display_path,
    git_state,
    pretty_json_bytes,
    sha256_directory,
    sha256_file,
    write_once,
)
from ..schema import ArtifactRef, DatasetManifest


DEFAULT_BASE_RELEASE = Path("inputs/pr_review_v4/releases/dev-raw-multiround-0.4.0")
DEFAULT_RELEASE = Path("inputs/pr_review_v4/releases/dev-change-graph-0.5.1")


def build_change_graph_release(
    *,
    base_release: Path,
    workspace_root: Path,
    blob_cache_root: Path,
    release_dir: Path,
    release: str = "0.5.1-change-graph",
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
        source = base_release / artifact.path
        write_once(release_dir / artifact.path, source.read_bytes())

    graph_path = release_dir / "derived" / "change_graphs.jsonl"
    report_path = release_dir / "derived" / "change_graph_report.json"
    report = build_graph_artifact(
        release_dir=release_dir,
        workspace_root=workspace_root,
        blob_cache_root=blob_cache_root,
        out=graph_path,
        report_out=report_path,
    )
    graph_ref = ArtifactRef(
        path="derived/change_graphs.jsonl",
        role="review_time_change_graphs",
        schema_version="cg1",
        sha256=sha256_file(graph_path),
        records=int(report["episodes"]),
    )
    report_ref = ArtifactRef(
        path="derived/change_graph_report.json",
        role="change_graph_coverage_report",
        schema_version="cg-audit1",
        sha256=sha256_file(report_path),
        records=int(report["file_coverage"]),
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
                    path=display_path(blob_cache_root),
                    role="change_graph_base_file_cache",
                    sha256=sha256_directory(blob_cache_root),
                    records=sum(1 for item in blob_cache_root.rglob("*") if item.is_file()),
                ),
            ],
            "derived_artifacts": [*base.derived_artifacts, graph_ref, report_ref],
            "generator_git_commit": git_commit,
            "generator_tree_state": tree_state,
            "generator_versions": {
                **base.generator_versions,
                "change_graph": CHANGE_GRAPH_BUILDER_VERSION,
            },
            "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        }
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build immutable PR Review v4 cg1 release")
    parser.add_argument("--base-release", type=Path, default=DEFAULT_BASE_RELEASE)
    parser.add_argument(
        "--workspaces",
        type=Path,
        default=Path("data/code_execute/repos/mathlib4/workspaces"),
    )
    parser.add_argument(
        "--blob-cache",
        type=Path,
        default=Path("data/pr_review_v4/cache/base_files"),
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--release", default="0.5.1-change-graph")
    parser.add_argument("--created-at", default=None)
    args = parser.parse_args()
    manifest = build_change_graph_release(
        base_release=args.base_release,
        workspace_root=args.workspaces,
        blob_cache_root=args.blob_cache,
        release_dir=args.out,
        release=args.release,
        created_at=args.created_at,
    )
    graph_ref = next(
        item for item in manifest.derived_artifacts if item.schema_version == "cg1"
    )
    print(
        json.dumps(
            {
                "release": str(args.out),
                "prs": len(manifest.pr_numbers),
                "change_graphs": graph_ref.records,
                "source_kind": manifest.source_kind,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
