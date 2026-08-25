"""Render the scope-migration review queue as a compact Markdown audit."""

import argparse
import json
from pathlib import Path

from ..schema import ChangeGraph, DatasetManifest, InterventionScopeMigration
from ..paths import LEGACY_INTERVENTIONS_V5


def render_scope_review(release_dir: Path, interventions_path: Path) -> str:
    manifest = DatasetManifest.model_validate_json((release_dir / "manifest.json").read_text())
    graph_ref = next(item for item in manifest.derived_artifacts if item.schema_version == "cg1")
    mapping_ref = next(
        item for item in manifest.gold_artifacts if item.schema_version == "i5-cg1-map1"
    )
    report_ref = next(
        item for item in manifest.gold_artifacts if item.schema_version == "scope-map-audit1"
    )
    graphs = {
        item.graph_id: item
        for item in (
            ChangeGraph.model_validate_json(line)
            for line in (release_dir / graph_ref.path).read_text().splitlines()
            if line.strip()
        )
    }
    mappings = {
        item.intervention_id: item
        for item in (
            InterventionScopeMigration.model_validate_json(line)
            for line in (release_dir / mapping_ref.path).read_text().splitlines()
            if line.strip()
        )
    }
    interventions = {
        item["intervention_id"]: item
        for item in (
            json.loads(line) for line in interventions_path.read_text().splitlines() if line.strip()
        )
    }
    report = json.loads((release_dir / report_ref.path).read_text())
    lines = [
        "# PR Review v4 scope-mapping review queue",
        "",
        f"Release: `{manifest.release}`",
        f"Items requiring review: {len(report['review_queue'])}",
        "",
        "Accept or correct the proposed primary targets. Revision-hunk resolutions are audit-only "
        "unless `contributes_to_scope` is true.",
        "",
    ]
    for queued in report["review_queue"]:
        intervention_id = queued["intervention_id"]
        mapping = mappings[intervention_id]
        graph = graphs[mapping.graph_id]
        targets = {item.change_id: item for item in graph.targets}
        lines.extend(
            [
                f"## {intervention_id} (PR #{mapping.pr_number})",
                "",
                f"Status: `{mapping.status}` | Review reasons: "
                + ", ".join(f"`{item}`" for item in queued["reasons"]),
                "",
                f"**Ask:** {interventions[intervention_id].get('canonical_ask') or ''}",
                "",
                "**Proposed primary targets:**",
            ]
        )
        if mapping.resolved_change_ids:
            for change_id in mapping.resolved_change_ids:
                target = targets[change_id]
                label = target.declaration_name or target.kind
                lines.append(f"- `{target.path}`: `{label}` (`{change_id}`)")
        else:
            lines.append("- None")
        lines.extend(["", "**Resolution evidence:**"])
        for resolution in mapping.resolutions:
            contribution = "primary" if resolution.contributes_to_scope else "audit-only"
            lines.append(
                f"- `{resolution.method}` / `{resolution.confidence}` / {contribution}: "
                f"`{resolution.source_ref}` -> {len(resolution.change_ids)} target(s)"
            )
        if mapping.exception_codes:
            lines.extend(
                [
                    "",
                    "**Exceptions:** "
                    + ", ".join(f"`{item}`" for item in mapping.exception_codes),
                ]
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render v4 scope migration review queue")
    parser.add_argument("release", type=Path)
    parser.add_argument(
        "--interventions",
        type=Path,
        default=LEGACY_INTERVENTIONS_V5,
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rendered = render_scope_review(args.release, args.interventions)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered)
    print(json.dumps({"out": str(args.out), "bytes": len(rendered.encode("utf-8"))}, indent=2))


if __name__ == "__main__":
    main()
