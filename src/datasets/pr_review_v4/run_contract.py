"""Create immutable execution plans and seal complete v4 runs."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from .releases import artifact_ref
from .io import (
    canonical_json_bytes,
    display_path,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from .schema import (
    ArtifactRef,
    CandidateClaim,
    DatasetManifest,
    EvidencePacket,
    InvestigationRecord,
    InvestigationTask,
    OperatorRun,
    RenderedPrompt,
    ReviewOpportunity,
    ReviewWorkUnit,
    RunManifest,
    RunPlan,
    SelectedFinding,
)


RUN_CONTRACT_VERSION = "run-contract/1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def select_units(
    units: Iterable[ReviewWorkUnit],
    pr_numbers: Iterable[int] = (),
    work_unit_ids: Iterable[str] = (),
    limit: int = 0,
) -> List[ReviewWorkUnit]:
    selected = list(units)
    if pr_numbers:
        wanted_prs = set(pr_numbers)
        selected = [item for item in selected if item.pr_number in wanted_prs]
        missing_prs = wanted_prs - {item.pr_number for item in selected}
        if missing_prs:
            raise ValueError(f"unknown requested PR numbers: {sorted(missing_prs)}")
    if work_unit_ids:
        wanted_units = set(work_unit_ids)
        selected = [item for item in selected if item.work_unit_id in wanted_units]
        missing_units = wanted_units - {item.work_unit_id for item in selected}
        if missing_units:
            raise ValueError(f"unknown requested work-unit IDs: {sorted(missing_units)}")
    if limit:
        selected = selected[:limit]
    if not selected:
        raise ValueError("run plan selects no work units")
    return selected


def create_run_plan(
    release: Path,
    out: Path,
    run_id: str,
    model_name: str,
    units: Iterable[ReviewWorkUnit],
    prompts: Iterable[RenderedPrompt],
    created_at: Optional[str] = None,
    investigations: Iterable[InvestigationTask] = (),
    method_registry_path: Optional[Path] = None,
    orchestrator_id: Optional[str] = None,
    scaffold_config_sha256: Optional[str] = None,
) -> RunPlan:
    units = list(units)
    investigations = list(investigations)
    prompts = list(prompts)
    # Keyed on the *invocation*, which is the work unit for every holistic run and
    # `wu:…#spec_id` for a focused one. The focused arm runs four specs against one unit, so
    # a unit-keyed plan would record one prompt hash where four were sent and silently
    # accept three responses whose prompts it never vouched for.
    prompt_by_id = {(item.invocation_id or item.work_unit_id): item for item in prompts}
    expected_ids = (
        [item.invocation_id or item.work_unit_id for item in prompts]
        if any(item.invocation_id for item in prompts)
        else [item.work_unit_id for item in units]
    )
    missing_prompts = set(expected_ids) - set(prompt_by_id)
    if missing_prompts:
        raise ValueError(f"run plan has work units without prompts: {sorted(missing_prompts)}")
    investigation_ids = [item.investigation_id for item in investigations]
    if len(investigation_ids) != len(set(investigation_ids)):
        raise ValueError("run plan contains duplicate investigation IDs")
    registry_sha256 = sha256_file(method_registry_path) if method_registry_path else None
    if investigations and registry_sha256 is None:
        raise ValueError("investigation run plans require a method registry")
    mismatched_registry = [
        item.investigation_id for item in investigations
        if item.method_registry_sha256 != registry_sha256
    ]
    if mismatched_registry:
        raise ValueError(
            f"investigations reference a different method registry: {mismatched_registry}"
        )
    dataset_manifest = release / "manifest.json"
    DatasetManifest.model_validate_json(dataset_manifest.read_text())
    source = {
        "run_id": run_id,
        "orchestrator_id": orchestrator_id or run_id,
        "scaffold_config_sha256": scaffold_config_sha256,
        "dataset_manifest_path": display_path(dataset_manifest),
        "dataset_manifest_sha256": sha256_file(dataset_manifest),
        "expected_work_unit_ids": expected_ids,
        "expected_pr_numbers": sorted({item.pr_number for item in units}),
        "expected_investigation_ids": investigation_ids,
        "method_registry_sha256": registry_sha256,
        "prompt_sha256_by_work_unit": {
            invocation_id: prompt_by_id[invocation_id].prompt_sha256
            for invocation_id in expected_ids
        },
        # Union of the units' and the prompts' renderers, because for a focused run they
        # differ: the units are `candidate-prompt/12` but what was actually sent is
        # `focused-prompt/1`, and a plan that named only the unit's renderer would vouch for
        # a prompt nobody rendered. For holistic runs the two sets are equal, so every
        # existing plan's value is unchanged.
        "renderer_versions": sorted(
            {item.renderer_version for item in units}
            | {item.renderer_version for item in prompts}
        ),
        "model_name": model_name,
        "created_at": created_at or _now(),
    }
    digest = sha256_bytes(canonical_json_bytes(source))
    plan = RunPlan(source_sha256=digest, **source)
    if out.exists():
        existing = RunPlan.model_validate_json(out.read_text())
        comparable = ("run_id", "orchestrator_id", "scaffold_config_sha256",
                      "dataset_manifest_sha256", "expected_work_unit_ids",
                      "expected_investigation_ids", "method_registry_sha256",
                      "prompt_sha256_by_work_unit", "renderer_versions", "model_name")
        if any(getattr(existing, key) != getattr(plan, key) for key in comparable):
            raise FileExistsError(f"existing run plan has incompatible identity: {out}")
        return existing
    write_once(out, pretty_json_bytes(plan))
    return plan


def seal_run(run_dir: Path, created_at: Optional[str] = None) -> RunManifest:
    plan_path = run_dir / "run_plan.json"
    plan = RunPlan.model_validate_json(plan_path.read_text())
    response_path = run_dir / "candidate_responses.jsonl"
    responses = [json.loads(line) for line in response_path.read_text().splitlines() if line]
    expected = set(plan.expected_work_unit_ids)
    response_ids = [
        item.get("invocation_id") or item.get("work_unit_id") for item in responses
    ]
    unknown = set(response_ids) - expected
    missing = expected - set(response_ids)
    if unknown or missing:
        raise ValueError(f"terminal response coverage mismatch: missing={sorted(missing)} extra={sorted(unknown)}")
    successful = Counter(
        item.get("invocation_id") or item.get("work_unit_id")
        for item in responses if item.get("success")
    )
    duplicate_success = sorted(key for key, count in successful.items() if count != 1)
    if duplicate_success:
        raise ValueError(f"work units require exactly one successful terminal response: {duplicate_success}")
    for response in responses:
        if not response.get("success"):
            continue
        key = response.get("invocation_id") or response["work_unit_id"]
        expected_prompt = plan.prompt_sha256_by_work_unit[key]
        if response.get("prompt_sha256") != expected_prompt:
            raise ValueError(f"prompt hash mismatch for {key}")

    candidate_path = run_dir / "candidates.jsonl"
    packet_path = run_dir / "evidence/packets.jsonl"
    finding_path = run_dir / "findings.jsonl"
    candidates = load_jsonl(candidate_path, CandidateClaim)
    packets = load_jsonl(packet_path, EvidencePacket)
    findings = load_jsonl(finding_path, SelectedFinding)
    candidate_ids = [item.candidate_id for item in candidates]
    packet_candidate_ids = [item.candidate_id for item in packets]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate artifact contains duplicate candidate IDs")

    investigations = []
    operator_runs = []
    opportunities = []
    investigation_artifact_specs = []
    if plan.expected_investigation_ids:
        task_path = run_dir / "investigation_tasks.jsonl"
        record_path = run_dir / "investigation_records.jsonl"
        operator_path = run_dir / "operator_runs.jsonl"
        opportunity_path = run_dir / "opportunities.jsonl"
        tasks = load_jsonl(task_path, InvestigationTask)
        investigations = load_jsonl(record_path, InvestigationRecord)
        operator_runs = load_jsonl(operator_path, OperatorRun)
        opportunities = load_jsonl(opportunity_path, ReviewOpportunity)

        expected_investigations = plan.expected_investigation_ids
        task_ids = [item.investigation_id for item in tasks]
        record_ids = [item.investigation_id for item in investigations]
        if task_ids != expected_investigations:
            raise ValueError("investigation task artifact does not match the frozen run plan")
        if Counter(record_ids) != Counter(expected_investigations):
            raise ValueError("every expected investigation requires exactly one terminal record")

        task_by_id = {item.investigation_id: item for item in tasks}
        operator_by_id = {item.operator_run_id: item for item in operator_runs}
        opportunity_by_id = {item.opportunity_id: item for item in opportunities}
        if len(operator_by_id) != len(operator_runs):
            raise ValueError("operator run artifact contains duplicate IDs")
        if len(opportunity_by_id) != len(opportunities):
            raise ValueError("opportunity artifact contains duplicate IDs")

        referenced_operator_ids = []
        referenced_opportunity_ids = []
        for record in investigations:
            task = task_by_id[record.investigation_id]
            for operator_id in record.operator_run_ids:
                operator = operator_by_id.get(operator_id)
                if operator is None or operator.investigation_id != record.investigation_id:
                    raise ValueError(f"invalid operator lineage for {record.investigation_id}")
                if operator.operator not in task.expected_operators:
                    raise ValueError(f"unexpected operator for {record.investigation_id}")
                referenced_operator_ids.append(operator_id)
            for opportunity_id in record.opportunity_ids:
                opportunity = opportunity_by_id.get(opportunity_id)
                if opportunity is None or opportunity.investigation_id != record.investigation_id:
                    raise ValueError(f"invalid opportunity lineage for {record.investigation_id}")
                if opportunity.method_id != task.method_id:
                    raise ValueError(f"opportunity method mismatch for {opportunity_id}")
                if opportunity.primary_change_id != task.primary_change_id and (
                    opportunity.primary_change_id not in task.related_change_ids
                ):
                    raise ValueError(f"opportunity escapes investigation scope: {opportunity_id}")
                referenced_opportunity_ids.append(opportunity_id)
        if Counter(referenced_operator_ids) != Counter(operator_by_id.keys()):
            raise ValueError("every operator run must be referenced exactly once")
        if Counter(referenced_opportunity_ids) != Counter(opportunity_by_id.keys()):
            raise ValueError("every opportunity must be referenced exactly once")

        for candidate in candidates:
            if candidate.producer == "model" and not candidate.opportunity_ids:
                raise ValueError(
                    f"model candidate lacks production opportunity lineage: {candidate.candidate_id}"
                )
            if set(candidate.opportunity_ids) - set(opportunity_by_id):
                raise ValueError(f"candidate references unknown opportunity: {candidate.candidate_id}")
            if candidate.investigation_id and candidate.investigation_id not in task_by_id:
                raise ValueError(f"candidate references unknown investigation: {candidate.candidate_id}")

        investigation_artifact_specs = [
            (task_path, "investigation_tasks", "investigation-task1", len(tasks)),
            (record_path, "investigation_records", "investigation-record1", len(investigations)),
            (operator_path, "operator_runs", "operator-run1", len(operator_runs)),
            (opportunity_path, "review_opportunities", "review-opportunity1", len(opportunities)),
        ]
    if Counter(packet_candidate_ids) != Counter(candidate_ids):
        raise ValueError("every candidate must have exactly one evidence packet")
    packet_ids = {item.packet_id for item in packets}
    candidate_id_set = set(candidate_ids)
    for finding in findings:
        if finding.candidate_id not in candidate_id_set or finding.packet_id not in packet_ids:
            raise ValueError(f"finding lineage is incomplete: {finding.finding_id}")

    successful_ids = sorted(successful)
    failed_ids = sorted(expected - set(successful_ids))
    failed_investigations = [
        item.investigation_id for item in investigations if item.execution_status == "failed"
    ]
    completion = "complete" if not failed_ids and not failed_investigations else "failed"
    artifact_specs = [
        (response_path, "terminal_candidate_responses", None, len(responses)),
        (candidate_path, "candidate_claims", "c1", len(candidates)),
        (packet_path, "evidence_packets", "evidence-packet1", len(packets)),
        (finding_path, "selected_findings", "finding1", len(findings)),
    ] + investigation_artifact_specs
    for path, role, schema in (
        (run_dir / "evidence/artifacts.jsonl", "evidence_artifacts", "evidence-artifact1"),
        (run_dir / "evidence/assertions.jsonl", "evidence_assertions", "evidence-assertion1"),
        (run_dir / "evaluation.json", "funnel_evaluation", "v4-evaluation1"),
        (run_dir / "semantic-judge-v1/matches.jsonl", "semantic_matches", "semantic-match1"),
        (run_dir / "semantic-judge-v1/report.json", "semantic_evaluation", "v4-semantic-report1"),
        (run_dir / "candidates-unmerged.jsonl", "unmerged_candidate_claims", "c1"),
        (run_dir / "candidate_merge_report.json", "candidate_merge_report", "manual-agenda-probe-merge1"),
        (run_dir / "agenda_probe_comparison.json", "agenda_probe_comparison", "manual-agenda-probe-comparison1"),
    ):
        if path.is_file():
            records = (len(path.read_text().splitlines()) if path.suffix == ".jsonl" else 1)
            artifact_specs.append((path, role, schema, records))
    artifacts = [
        artifact_ref(path, run_dir, role, schema, records)
        for path, role, schema, records in artifact_specs
    ]
    source = {
        "run_id": plan.run_id,
        "run_plan_path": plan_path.relative_to(run_dir).as_posix(),
        "run_plan_sha256": sha256_file(plan_path),
        "dataset_manifest_path": plan.dataset_manifest_path,
        "dataset_manifest_sha256": plan.dataset_manifest_sha256,
        "expected_work_unit_ids": plan.expected_work_unit_ids,
        "successful_work_unit_ids": successful_ids,
        "failed_work_unit_ids": failed_ids,
        "investigations": len(investigations),
        "operator_runs": len(operator_runs),
        "opportunities": len(opportunities),
        "candidates": len(candidates),
        "evidence_packets": len(packets),
        "findings": len(findings),
        "artifacts": [item.model_dump(mode="json") for item in artifacts],
        "completion_status": completion,
        "created_at": created_at or _now(),
    }
    digest = sha256_bytes(canonical_json_bytes(source))
    manifest = RunManifest(source_sha256=digest, **source)
    write_once(run_dir / "run_manifest.json", pretty_json_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or seal a v4 run contract")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init")
    init.add_argument("--release", type=Path, required=True)
    init.add_argument("--run-dir", type=Path, required=True)
    init.add_argument("--run-id", required=True)
    init.add_argument("--model", required=True)
    init.add_argument("--pr-numbers", type=int, nargs="*", default=[])
    init.add_argument("--work-unit-ids", nargs="*", default=[])
    init.add_argument("--work-unit-limit", type=int, default=0)
    init.add_argument("--investigations", type=Path)
    init.add_argument("--method-registry", type=Path)
    seal = subparsers.add_parser("seal")
    seal.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "init":
        units = select_units(
            load_jsonl(args.release / "derived/work_units.jsonl", ReviewWorkUnit),
            args.pr_numbers,
            args.work_unit_ids,
            args.work_unit_limit,
        )
        plan = create_run_plan(
            args.release,
            args.run_dir / "run_plan.json",
            args.run_id,
            args.model,
            units,
            load_jsonl(args.release / "derived/rendered_prompts.jsonl", RenderedPrompt),
            investigations=(
                load_jsonl(args.investigations, InvestigationTask) if args.investigations else []
            ),
            method_registry_path=args.method_registry,
        )
        print(json.dumps({"run_plan": str(args.run_dir / "run_plan.json"),
                          "work_units": len(plan.expected_work_unit_ids)}, indent=2))
    else:
        manifest = seal_run(args.run_dir)
        print(json.dumps({"run_manifest": str(args.run_dir / "run_manifest.json"),
                          "completion_status": manifest.completion_status}, indent=2))


if __name__ == "__main__":
    main()
