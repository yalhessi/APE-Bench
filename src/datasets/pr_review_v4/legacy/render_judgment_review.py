"""Render atomicity and obligation review items from a jg1 draft release."""

import argparse
import json
from pathlib import Path

from ..schema import ChangeGraph, DatasetManifest, JudgmentNode


def render_judgment_review(release_dir: Path) -> str:
    manifest = DatasetManifest.model_validate_json((release_dir / "manifest.json").read_text())
    graph_ref = next(item for item in manifest.derived_artifacts if item.schema_version == "cg1")
    judgment_ref = next(item for item in manifest.gold_artifacts if item.schema_version == "jg1")
    report_ref = next(
        item for item in manifest.gold_artifacts if item.schema_version == "jg-audit1"
    )
    graphs = {
        item.episode_id: item
        for item in (
            ChangeGraph.model_validate_json(line)
            for line in (release_dir / graph_ref.path).read_text().splitlines()
            if line.strip()
        )
    }
    judgments = {
        item.source_intervention_id: item
        for item in (
            JudgmentNode.model_validate_json(line)
            for line in (release_dir / judgment_ref.path).read_text().splitlines()
            if line.strip()
        )
    }
    report = json.loads((release_dir / report_ref.path).read_text())
    lines = [
        "# PR Review v4 judgment decomposition review",
        "",
        f"Release: `{manifest.release}`",
        f"Presumed atomic: {report['atomicity_status'].get('presumed_atomic', 0)}",
        f"Needs decomposition review: {len(report['decomposition_review'])}",
        "",
        "For each item, choose one of: accept as one atomic obligation, split into independently "
        "satisfiable obligations, or mark non-evaluable. Supporting proof steps should normally "
        "remain inside one obligation.",
        "",
    ]
    for item in report["decomposition_review"]:
        judgment = judgments[item["intervention_id"]]
        graph = graphs[judgment.episode_id]
        targets = {target.change_id: target for target in graph.targets}
        lines.extend(
            [
                f"## {item['intervention_id']} (PR #{item['pr_number']})",
                "",
                "Signals: " + ", ".join(f"`{signal}`" for signal in item["atomicity_signals"]),
                "",
                f"**Current claim:** {item['claim']}",
                "",
                "**Scope targets:**",
            ]
        )
        for change_id in item["change_ids"]:
            target = targets[change_id]
            label = target.declaration_name or target.kind
            lines.append(f"- `{target.path}`: `{label}` (`{change_id}`)")
        if not item["change_ids"]:
            lines.append("- None")
        lines.extend(
            [
                "",
                "**Decision:** pending",
                "",
                "**Proposed obligations/corrections:**",
                "- ",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render jg1 atomicity review queue")
    parser.add_argument("release", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rendered = render_judgment_review(args.release)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered)
    print(json.dumps({"out": str(args.out), "bytes": len(rendered.encode("utf-8"))}, indent=2))


if __name__ == "__main__":
    main()
