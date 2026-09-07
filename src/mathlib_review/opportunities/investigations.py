"""Schedule method-specific investigations and audit Phase 2 opportunity coverage."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Set

from src.mathlib_review.io import (
    canonical_json_bytes,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from src.mathlib_review.opportunities.method_registry import load_registry
from src.mathlib_review.schema import (
    InvestigationMethod,
    InvestigationTask,
    JudgmentNode,
    ModificationRecord,
    PRRelation,
    ReviewWorkUnit,
)


SCHEDULER_VERSION = "systematic-investigation-scheduler/1"

RELATIONS_BY_METHOD = {
    "baseline_failure.v1": set(),
    "canonical_api_search.v1": {
        "declaration_dependency", "direct_use_of_changed_declaration",
    },
    "wrapper_composition.v1": {
        "declaration_dependency", "direct_use_of_changed_declaration", "changed_siblings",
        "name_family",
    },
    "naming_contrast.v1": {"changed_siblings", "name_family"},
}

SMOKE_EXPECTATIONS = {
    "obligation:d1a4bd4608f602339557fe7eb8f0a36d668e3c0e3fcef83163d08013f8043118": {
        "method_id": "canonical_api_search.v1", "implementation_status": "active"
    },
    "obligation:a58d0d5ea6ca1dcb635a19a06e272cb7e73adefa96272448dca2e373aeb72a4b": {
        "method_id": "wrapper_composition.v1", "implementation_status": "active"
    },
    "obligation:45433fc367bdd15dc606eaabeadaa16ad98077afec83ca662fe39bcf938632ad": {
        "method_id": "naming_contrast.v1", "implementation_status": "active"
    },
    "obligation:f4d1ab7fb96fc89956e85c9ab1bbbf82a1b6b3a94e6e4f500d784bfe0de1d5f6": {
        "method_id": "proof_compression.v1", "implementation_status": "planned_method_gap"
    },
    "obligation:a73a79ae9a7b9d20d97ee71366b3d5dfabdbff23c81aceb09d84753f6ba67ad5": {
        "method_id": "proof_compression.v1", "implementation_status": "planned_method_gap"
    },
    "obligation:48ec1f14120b2955dc5842b5621da621b0ee960ab0de07a3297e0898b0478443": {
        "method_id": "structural_rewrite.v1", "implementation_status": "planned_method_gap"
    },
}


def method_applies(method: InvestigationMethod, modification: ModificationRecord) -> bool:
    changed = {
        item.component
        for item in modification.component_deltas
        if item.status != "unchanged"
    }
    applicability = method.applies_when
    return (
        modification.subject_kind in applicability.subject_kinds
        and modification.lifecycle in applicability.lifecycles
        and modification.visibility in applicability.visibilities
        and bool(changed & set(applicability.any_changed_components))
    )


def schedule_investigations(
    modifications: Iterable[ModificationRecord],
    relations: Iterable[PRRelation],
    work_units: Iterable[ReviewWorkUnit],
    methods: Iterable[InvestigationMethod],
    method_registry_sha256: str,
) -> List[InvestigationTask]:
    modifications = sorted(
        modifications, key=lambda item: (item.pr_number, item.primary_change_id)
    )
    methods = list(methods)
    work_unit_by_change = {
        change_id: unit
        for unit in work_units
        for change_id in unit.change_ids
    }
    related = defaultdict(lambda: defaultdict(set))
    for relation in relations:
        related[relation.source_change_id][relation.relation_kind].update(
            relation.related_change_ids
        )
        for target in relation.related_change_ids:
            related[target][relation.relation_kind].add(relation.source_change_id)

    tasks = []
    for modification in modifications:
        unit = work_unit_by_change.get(modification.primary_change_id)
        if unit is None:
            raise ValueError(
                f"modification has no physical work unit: {modification.modification_id}"
            )
        for method in methods:
            if not method_applies(method, modification):
                continue
            accepted_relation_kinds = RELATIONS_BY_METHOD.get(method.method_id, set())
            related_change_ids = sorted({
                change_id
                for kind in accepted_relation_kinds
                for change_id in related[modification.primary_change_id][kind]
            })
            identity = {
                "scheduler_version": SCHEDULER_VERSION,
                "method_registry_sha256": method_registry_sha256,
                "method_id": method.method_id,
                "work_unit_id": unit.work_unit_id,
                "modification_id": modification.modification_id,
                "modification_sha256": modification.source_sha256,
                "primary_change_id": modification.primary_change_id,
                "related_change_ids": related_change_ids,
                "expected_operators": method.operators,
            }
            digest = sha256_bytes(canonical_json_bytes(identity))
            tasks.append(InvestigationTask(
                investigation_id=f"investigation:{digest[:24]}",
                method_id=method.method_id,
                work_unit_id=unit.work_unit_id,
                episode_id=modification.episode_id,
                pr_number=modification.pr_number,
                modification_ids=[modification.modification_id],
                primary_change_id=modification.primary_change_id,
                related_change_ids=related_change_ids,
                expected_operators=method.operators,
                method_registry_sha256=method_registry_sha256,
                source_sha256=digest,
            ))
    tasks.sort(key=lambda item: (item.pr_number, item.method_id, item.primary_change_id))
    validate_schedule(modifications, methods, tasks, method_registry_sha256)
    return tasks


def validate_schedule(
    modifications: Iterable[ModificationRecord],
    methods: Iterable[InvestigationMethod],
    tasks: Iterable[InvestigationTask],
    method_registry_sha256: str,
) -> None:
    modifications = list(modifications)
    methods = list(methods)
    tasks = list(tasks)
    modification_by_id = {item.modification_id: item for item in modifications}
    method_by_id = {item.method_id: item for item in methods}
    expected = {
        (modification.modification_id, method.method_id)
        for modification in modifications
        for method in methods
        if method_applies(method, modification)
    }
    actual = []
    for task in tasks:
        if task.method_registry_sha256 != method_registry_sha256:
            raise ValueError(f"task references the wrong method registry: {task.investigation_id}")
        if len(task.modification_ids) != 1:
            raise ValueError(f"Phase 2 tasks require one primary modification: {task.investigation_id}")
        modification = modification_by_id.get(task.modification_ids[0])
        method = method_by_id.get(task.method_id)
        if modification is None or method is None or not method_applies(method, modification):
            raise ValueError(f"non-applicable investigation task: {task.investigation_id}")
        if task.primary_change_id != modification.primary_change_id:
            raise ValueError(f"task primary change mismatch: {task.investigation_id}")
        if task.expected_operators != method.operators:
            raise ValueError(f"task operator contract mismatch: {task.investigation_id}")
        actual.append((modification.modification_id, method.method_id))
    if Counter(actual) != Counter(expected):
        raise ValueError("scheduled investigations do not exactly cover applicable method pairs")
    if len({item.investigation_id for item in tasks}) != len(tasks):
        raise ValueError("scheduled investigations contain duplicate IDs")


def schedule_report(
    tasks: Iterable[InvestigationTask], work_units: Iterable[ReviewWorkUnit]
) -> Dict:
    tasks = list(tasks)
    work_unit_by_change = {
        change_id: unit.work_unit_id
        for unit in work_units
        for change_id in unit.change_ids
    }
    cross_unit_tasks = sum(
        any(work_unit_by_change.get(change_id) != item.work_unit_id
            for change_id in item.related_change_ids)
        for item in tasks
    )
    source = {
        "schema_version": "investigation-schedule-report1",
        "scheduler_version": SCHEDULER_VERSION,
        "tasks": len(tasks),
        "prs": len({item.pr_number for item in tasks}),
        "by_method": dict(sorted(Counter(item.method_id for item in tasks).items())),
        "tasks_with_related_changes": sum(bool(item.related_change_ids) for item in tasks),
        "cross_work_unit_tasks": cross_unit_tasks,
        "max_related_changes": max((len(item.related_change_ids) for item in tasks), default=0),
    }
    return {**source, "source_sha256": sha256_bytes(canonical_json_bytes(source))}


def audit_smoke_schedule(
    tasks: Iterable[InvestigationTask], judgments: Iterable[JudgmentNode], methods: Iterable[InvestigationMethod]
) -> Dict:
    tasks = list(tasks)
    obligation_by_id = {
        obligation.obligation_id: obligation
        for judgment in judgments
        for obligation in judgment.obligations
    }
    method_ids = {item.method_id for item in methods}
    rows = []
    for obligation_id, expectation in SMOKE_EXPECTATIONS.items():
        obligation = obligation_by_id.get(obligation_id)
        if obligation is None:
            raise ValueError(f"smoke obligation is absent from frozen gold: {obligation_id}")
        matching_tasks = [
            task.investigation_id
            for task in tasks
            if task.method_id == expectation["method_id"]
            and task.primary_change_id in obligation.change_ids
        ]
        active = expectation["implementation_status"] == "active"
        status = (
            "scheduled" if active and matching_tasks
            else "missing_active_method" if active
            else "method_gap" if expectation["method_id"] not in method_ids
            else "unexpectedly_implemented_without_task"
        )
        rows.append({
            "obligation_id": obligation_id,
            "expected_method_id": expectation["method_id"],
            "implementation_status": expectation["implementation_status"],
            "change_ids": obligation.change_ids,
            "matching_investigation_ids": matching_tasks,
            "audit_status": status,
        })
    active_rows = [item for item in rows if item["implementation_status"] == "active"]
    gap_rows = [item for item in rows if item["implementation_status"] == "planned_method_gap"]
    gate_pass = (
        all(item["audit_status"] == "scheduled" for item in active_rows)
        and all(item["audit_status"] == "method_gap" for item in gap_rows)
    )
    source = {
        "schema_version": "phase2-schedule-opportunity-audit1",
        "gate_status": "pass" if gate_pass else "fail",
        "active_method_coverage": {
            "covered": sum(item["audit_status"] == "scheduled" for item in active_rows),
            "total": len(active_rows),
        },
        "planned_method_gaps": len(gap_rows),
        "overall_accounted": len(rows),
        "rows": rows,
    }
    return {**source, "source_sha256": sha256_bytes(canonical_json_bytes(source))}


def main() -> None:
    parser = argparse.ArgumentParser(description="Schedule and audit systematic v4 investigations")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--relations", type=Path, required=True)
    parser.add_argument("--work-units", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--judgments", type=Path)
    parser.add_argument("--audit-out", type=Path)
    args = parser.parse_args()
    modifications = load_jsonl(args.inventory, ModificationRecord)
    relations = load_jsonl(args.relations, PRRelation)
    units = load_jsonl(args.work_units, ReviewWorkUnit)
    methods = load_registry(args.registry)
    registry_hash = sha256_file(args.registry)
    tasks = schedule_investigations(modifications, relations, units, methods, registry_hash)
    write_once(args.out, jsonl_bytes(tasks))
    report = schedule_report(tasks, units)
    write_once(args.report, pretty_json_bytes(report))
    output = {"schedule": str(args.out), **report}
    if args.judgments or args.audit_out:
        if not args.judgments or not args.audit_out:
            raise ValueError("--judgments and --audit-out must be supplied together")
        audit = audit_smoke_schedule(tasks, load_jsonl(args.judgments, JudgmentNode), methods)
        write_once(args.audit_out, pretty_json_bytes(audit))
        output["smoke_audit"] = audit
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
