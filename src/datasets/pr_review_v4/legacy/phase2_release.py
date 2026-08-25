"""Build the production-safe Phase 2 inventory, relations, and schedule treatment."""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

from ..investigations import audit_smoke_schedule, schedule_investigations, schedule_report
from ..releases import artifact_ref
from ..io import (
    canonical_json_bytes,
    display_path,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from ..method_registry import load_registry
from ..modification_inventory import build_inventory, inventory_report
from ..pr_relations import build_relations, relation_report
from ..schema import (
    ArtifactRef,
    ChangeGraph,
    JudgmentNode,
    OpportunityTreatmentManifest,
    ReviewWorkUnit,
)


PHASE2_VERSION = "systematic-opportunity-phase2/1"
DEFAULT_PARENT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
DEFAULT_OUT = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1")
DEFAULT_AUDIT = Path("results/pr_review_v4/audits/systematic-opportunities-v1-phase2-audit.json")


def build_phase2(
    parent: Path = DEFAULT_PARENT,
    out: Path = DEFAULT_OUT,
    audit_out: Path = DEFAULT_AUDIT,
) -> Tuple[OpportunityTreatmentManifest, Dict]:
    graphs = load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
    units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)
    registry_path = out / "methods.jsonl"
    methods = load_registry(registry_path)
    registry_hash = sha256_file(registry_path)

    inventory = build_inventory(graphs)
    relations, relation_evidence = build_relations(graphs)
    tasks = schedule_investigations(inventory, relations, units, methods, registry_hash)

    derived = out / "derived"
    paths = {
        "inventory": derived / "modification_inventory.jsonl",
        "inventory_report": derived / "inventory_report.json",
        "relations": derived / "pr_relations.jsonl",
        "relation_evidence": derived / "relation_evidence.jsonl",
        "relation_report": derived / "relation_report.json",
        "tasks": derived / "investigation_tasks.jsonl",
        "schedule_report": derived / "schedule_report.json",
    }
    write_once(paths["inventory"], jsonl_bytes(inventory))
    write_once(paths["inventory_report"], pretty_json_bytes(inventory_report(inventory)))
    write_once(paths["relations"], jsonl_bytes(relations))
    write_once(paths["relation_evidence"], jsonl_bytes(relation_evidence))
    write_once(paths["relation_report"], pretty_json_bytes(
        relation_report(relations, relation_evidence)
    ))
    write_once(paths["tasks"], jsonl_bytes(tasks))
    write_once(paths["schedule_report"], pretty_json_bytes(schedule_report(tasks, units)))

    artifacts = [
        artifact_ref(paths["inventory"], out, "modification_inventory", "modification1", len(inventory)),
        artifact_ref(paths["inventory_report"], out, "inventory_report", "modification-inventory-report1", 1),
        artifact_ref(paths["relations"], out, "pr_relations", "pr-relation1", len(relations)),
        artifact_ref(paths["relation_evidence"], out, "relation_evidence", "relation-evidence1", len(relation_evidence)),
        artifact_ref(paths["relation_report"], out, "relation_report", "pr-relation-report1", 1),
        artifact_ref(paths["tasks"], out, "investigation_tasks", "investigation-task1", len(tasks)),
        artifact_ref(paths["schedule_report"], out, "schedule_report", "investigation-schedule-report1", 1),
    ]
    parent_manifest = parent / "manifest.json"
    source = {
        "treatment_id": "systematic-opportunities-v1-phase2",
        "parent_dataset_manifest": ArtifactRef(
            path=display_path(parent_manifest),
            role="parent_dataset_manifest",
            schema_version="pr4-manifest-1",
            sha256=sha256_file(parent_manifest),
            records=1,
        ).model_dump(mode="json"),
        "method_registry": ArtifactRef(
            path="methods.jsonl",
            role="investigation_method_registry",
            schema_version="investigation-method1",
            sha256=registry_hash,
            records=len(methods),
        ).model_dump(mode="json"),
        "derived_artifacts": [item.model_dump(mode="json") for item in artifacts],
        "generator_versions": {
            "phase2": PHASE2_VERSION,
            "inventory": "modification-inventory/1",
            "relations": "pr-relations/1",
            "scheduler": "systematic-investigation-scheduler/1",
        },
    }
    digest = sha256_bytes(canonical_json_bytes(source))
    manifest = OpportunityTreatmentManifest(source_sha256=digest, **source)
    write_once(out / "manifest.json", pretty_json_bytes(manifest))

    judgments = load_jsonl(parent / "gold/judgments.jsonl", JudgmentNode)
    audit = audit_smoke_schedule(tasks, judgments, methods)
    write_once(audit_out, pretty_json_bytes(audit))
    return manifest, audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Build systematic-opportunity Phase 2 artifacts")
    parser.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--audit-out", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args()
    manifest, audit = build_phase2(args.parent, args.out, args.audit_out)
    print(json.dumps({
        "treatment": str(args.out),
        "manifest_sha256": manifest.source_sha256,
        "schedule_opportunity_gate": audit["gate_status"],
        "active_method_coverage": audit["active_method_coverage"],
        "planned_method_gaps": audit["planned_method_gaps"],
    }, indent=2))


if __name__ == "__main__":
    main()
