"""Phase 10 first increment: medium schedule treatment and static C0-C2 reachability census.

Builds the gold-free generation side (method registry, implementation registry, C1 contracts,
modification inventory, PR relations, investigation schedule, capability assessments) into an
immutable treatment directory, then runs the evaluation-side static census and reachability
gate into `results/pr_review_v4/audits/`. No model calls are made anywhere in this increment.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

from .implementation_registry import (
    ASSESSOR_VERSION,
    CONTRACTS_VERSION,
    IMPLEMENTATION_REGISTRY_VERSION,
    assess_capabilities,
    build_registry_files,
)
from .investigations import audit_smoke_schedule, schedule_investigations, schedule_report
from .releases import artifact_ref
from .io import (
    canonical_json_bytes,
    display_path,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from .method_coverage_census import build_static_census
from .method_registry import build_registry
from .modification_inventory import build_inventory, inventory_report
from .pr_relations import build_relations, relation_report
from .schema import (
    ArtifactRef,
    ChangeGraph,
    JudgmentNode,
    OpportunityTreatmentManifest,
    ReviewWorkUnit,
)


PHASE10_VERSION = "phase10-medium-static/1"
DEFAULT_PARENT = Path("inputs/pr_review_v4/releases/dev-medium-0.1.0")
DEFAULT_OUT = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1-medium-c1v2")
DEFAULT_CENSUS_OUT = Path("results/pr_review_v4/audits/phase10-medium-static-census-c1v2")
DEFAULT_SMOKE_AUDIT = Path(
    "results/pr_review_v4/audits/systematic-opportunities-v1-medium-phase2-audit.json"
)


def build_medium_treatment(parent: Path, out: Path, smoke_audit_out: Path) -> Tuple[OpportunityTreatmentManifest, Dict]:
    graphs = load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
    units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)

    methods = build_registry(out / "methods.jsonl")
    registry_hash = sha256_file(out / "methods.jsonl")
    implementations, _contracts = build_registry_files(out)

    inventory = build_inventory(graphs)
    relations, relation_evidence = build_relations(graphs)
    tasks = schedule_investigations(inventory, relations, units, methods, registry_hash)
    assessments = assess_capabilities(tasks, graphs, implementations)

    derived = out / "derived"
    outputs = {
        "modification_inventory": (derived / "modification_inventory.jsonl", inventory, "modification1"),
        "pr_relations": (derived / "pr_relations.jsonl", relations, "pr-relation1"),
        "relation_evidence": (derived / "relation_evidence.jsonl", relation_evidence, "relation-evidence1"),
        "investigation_tasks": (derived / "investigation_tasks.jsonl", tasks, "investigation-task1"),
        "capability_assessments": (derived / "capability_assessments.jsonl", assessments, "capability-assessment1"),
    }
    for path, rows, _schema in outputs.values():
        write_once(path, jsonl_bytes(rows))
    write_once(derived / "inventory_report.json", pretty_json_bytes(inventory_report(inventory)))
    write_once(derived / "relation_report.json", pretty_json_bytes(
        relation_report(relations, relation_evidence)
    ))
    write_once(derived / "schedule_report.json", pretty_json_bytes(schedule_report(tasks, units)))

    artifacts = [
        artifact_ref(path, out, role, schema, len(rows))
        for role, (path, rows, schema) in outputs.items()
    ] + [
        artifact_ref(derived / "inventory_report.json", out, "inventory_report", "modification-inventory-report1", 1),
        artifact_ref(derived / "relation_report.json", out, "relation_report", "pr-relation-report1", 1),
        artifact_ref(derived / "schedule_report.json", out, "schedule_report", "investigation-schedule-report1", 1),
        artifact_ref(out / "implementations.jsonl", out, "implementation_capability_registry", "implementation-capability1", len(implementations)),
        artifact_ref(out / "method_expression_contracts.jsonl", out, "method_expression_contracts", "method-expression-contract1", len(_contracts)),
    ]
    parent_manifest = parent / "manifest.json"
    source = {
        "treatment_id": "systematic-opportunities-v1-medium-phase2",
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
            "phase10": PHASE10_VERSION,
            "inventory": "modification-inventory/1",
            "relations": "pr-relations/1",
            "scheduler": "systematic-investigation-scheduler/1",
            "implementation_registry": IMPLEMENTATION_REGISTRY_VERSION,
            "contracts": CONTRACTS_VERSION,
            "capability_assessor": ASSESSOR_VERSION,
        },
    }
    digest = sha256_bytes(canonical_json_bytes(source))
    manifest = OpportunityTreatmentManifest(source_sha256=digest, **source)
    write_once(out / "manifest.json", pretty_json_bytes(manifest))

    judgments = load_jsonl(parent / "gold/judgments.jsonl", JudgmentNode)
    smoke_audit = audit_smoke_schedule(tasks, judgments, methods)
    write_once(smoke_audit_out, pretty_json_bytes(smoke_audit))
    return manifest, smoke_audit


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the Phase 10 medium schedule treatment and static C0-C2 census"
    )
    parser.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--census-out", type=Path, default=DEFAULT_CENSUS_OUT)
    parser.add_argument("--smoke-audit-out", type=Path, default=DEFAULT_SMOKE_AUDIT)
    args = parser.parse_args()
    manifest, smoke_audit = build_medium_treatment(args.parent, args.out, args.smoke_audit_out)
    census = build_static_census(args.parent, args.out, args.census_out)
    print(json.dumps({
        "treatment": str(args.out),
        "manifest_sha256": manifest.source_sha256,
        "phase2_smoke_gate": smoke_audit["gate_status"],
        "census": str(args.census_out),
        "included": census["included"],
        "outside_dev_pr": census["outside_dev_pr"],
        "reachability_decision": census["reachability_gate"]["decision"],
        "manual_audit_queue_size": census["manual_audit_queue_size"],
    }, indent=2))


if __name__ == "__main__":
    main()
