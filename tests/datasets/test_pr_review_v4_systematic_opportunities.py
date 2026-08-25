"""Offline gates for the systematic opportunity pipeline contracts."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.datasets.pr_review_v4.io import canonical_json_bytes, jsonl_bytes, sha256_bytes, sha256_file
from src.datasets.pr_review_v4.investigations import (
    audit_smoke_schedule,
    schedule_investigations,
    schedule_report,
)
from src.datasets.pr_review_v4.method_registry import (
    EXECUTION_ORDER,
    build_registry,
    default_methods,
    load_registry,
    registry_sha256,
    validate_registry,
)
from src.datasets.pr_review_v4.modification_inventory import build_inventory, inventory_report
from src.datasets.pr_review_v4.pr_relations import build_relations, relation_report
from src.datasets.pr_review_v4.run_contract import create_run_plan, seal_run
from src.datasets.pr_review_v4.schema import (
    ChangeGraph,
    InvestigationRecord,
    InvestigationTask,
    JudgmentNode,
    OperatorRun,
    OpportunityTreatmentManifest,
    RenderedPrompt,
    ReviewOpportunity,
    ReviewWorkUnit,
    WorthinessDecision,
)
from src.datasets.pr_review_v4.systematic_baseline import (
    _oracle_evidence_confirmation,
    inspect_baseline,
    write_baseline,
)


PILOT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")


def _load(relative, cls):
    return [
        cls.model_validate_json(line)
        for line in (PILOT / relative).read_text().splitlines()
        if line
    ]


def _digest(values):
    return sha256_bytes(canonical_json_bytes(values))


def test_minimal_method_registry_is_deterministic_and_method_specific(tmp_path):
    first = default_methods()
    second = default_methods()
    assert jsonl_bytes(first) == jsonl_bytes(second)
    assert [item.method_id for item in first] == EXECUTION_ORDER
    assert len({tuple(item.operators) for item in first}) == len(first)
    path = tmp_path / "methods.jsonl"
    built = build_registry(path)
    assert load_registry(path) == built
    assert registry_sha256(built) == sha256_bytes(path.read_bytes())


def test_method_registry_rejects_tampering_and_prompt_only_resources():
    methods = default_methods()
    tampered = methods[0].model_copy(update={"max_opportunities": 99})
    with pytest.raises(ValueError, match="source hash mismatch"):
        validate_registry([tampered, *methods[1:]])
    unknown = methods[0].model_copy(update={
        "operators": ["tell_model_to_check_everything"],
        "source_sha256": "invalid",
    })
    identity = unknown.model_dump(mode="json", exclude={"source_sha256"})
    unknown = unknown.model_copy(update={"source_sha256": _digest(identity)})
    with pytest.raises(ValueError, match="unknown method resources"):
        validate_registry([unknown, *methods[1:]])


def test_investigation_records_require_executed_methods_not_only_prose():
    with pytest.raises(ValidationError, match="operator run"):
        InvestigationRecord(
            investigation_id="investigation:1",
            execution_status="completed",
            disposition="checked_no_opportunity",
            basis="I checked this and found nothing.",
            producer="model",
            source_sha256="hash",
        )
    with pytest.raises(ValidationError, match="opportunity ID"):
        InvestigationRecord(
            investigation_id="investigation:1",
            execution_status="completed",
            disposition="opportunities",
            operator_run_ids=["operator-run:1"],
            basis="A source was found.",
            producer="deterministic",
            source_sha256="hash",
        )


def test_worthiness_keeps_request_force_separate():
    base = {
        "decision_id": "decision:1",
        "opportunity_id": "opportunity:1",
        "technical_assessment_id": "technical:1",
        "evidence_artifact_ids": ["artifact:1"],
        "rationale": "Canonical replacement.",
        "producer": "policy",
        "source_sha256": "hash",
    }
    with pytest.raises(ValidationError, match="require blocking or advisory"):
        WorthinessDecision(**base, review_worthiness="request")
    with pytest.raises(ValidationError, match="only request"):
        WorthinessDecision(
            **base, review_worthiness="advisory_option", request_force="advisory"
        )
    decision = WorthinessDecision(
        **base, review_worthiness="request", request_force="advisory"
    )
    assert decision.request_force == "advisory"


def test_production_opportunity_cannot_claim_oracle_provenance():
    with pytest.raises(ValidationError):
        ReviewOpportunity(
            opportunity_id="opportunity:1",
            investigation_id="investigation:1",
            method_id="canonical_api_search.v1",
            episode_id="episode:1",
            pr_number=1,
            primary_change_id="change:1",
            observed_pattern="manual reconstruction",
            source_artifact_ids=["artifact:1"],
            discovery_rank=1,
            source_provenance="oracle_development",
            source_sha256="hash",
        )


def test_run_contract_seals_complete_investigation_lineage(tmp_path):
    unit = _load("derived/work_units.jsonl", ReviewWorkUnit)[0]
    prompt = next(
        item for item in _load("derived/rendered_prompts.jsonl", RenderedPrompt)
        if item.work_unit_id == unit.work_unit_id
    )
    registry_path = tmp_path / "methods.jsonl"
    methods = build_registry(registry_path)
    registry_hash = sha256_file(registry_path)
    # Any shipping method serves; `canonical_api_search.v1` was retired at registry `/4`
    # for firing only on the PR it was written from.
    method = next(item for item in methods if item.method_id == "baseline_failure.v1")
    investigation = InvestigationTask(
        investigation_id="investigation:test",
        method_id=method.method_id,
        work_unit_id=unit.work_unit_id,
        episode_id=unit.episode_id,
        pr_number=unit.pr_number,
        modification_ids=["modification:test"],
        primary_change_id=unit.change_ids[0],
        expected_operators=["target_local_compile"],
        method_registry_sha256=registry_hash,
        source_sha256="investigation-hash",
    )
    create_run_plan(
        PILOT,
        tmp_path / "run_plan.json",
        "systematic-test-run",
        "test-model",
        [unit],
        [prompt],
        created_at="2026-07-17T00:00:00Z",
        investigations=[investigation],
        method_registry_path=registry_path,
    )
    (tmp_path / "candidate_responses.jsonl").write_text(json.dumps({
        "work_unit_id": unit.work_unit_id,
        "prompt_sha256": prompt.prompt_sha256,
        "response": {"candidates": []},
        "success": True,
        "error": None,
    }) + "\n")
    (tmp_path / "investigation_tasks.jsonl").write_bytes(jsonl_bytes([investigation]))
    operator = OperatorRun(
        operator_run_id="operator-run:test",
        investigation_id=investigation.investigation_id,
        operator="target_local_compile",
        status="completed",
        artifact_ids=["artifact:test"],
        result_count=1,
        source_sha256="operator-hash",
    )
    opportunity = ReviewOpportunity(
        opportunity_id="opportunity:test",
        investigation_id=investigation.investigation_id,
        method_id=investigation.method_id,
        episode_id=unit.episode_id,
        pr_number=unit.pr_number,
        primary_change_id=unit.change_ids[0],
        observed_pattern="The proof reconstructs a repository operation.",
        source_artifact_ids=["artifact:test"],
        discovery_rank=1,
        discovery_score=1.0,
        source_sha256="opportunity-hash",
    )
    record = InvestigationRecord(
        investigation_id=investigation.investigation_id,
        execution_status="completed",
        disposition="opportunities",
        operator_run_ids=[operator.operator_run_id],
        artifact_ids=["artifact:test"],
        opportunity_ids=[opportunity.opportunity_id],
        basis="Type-shape retrieval found one applicable declaration.",
        producer="deterministic",
        source_sha256="record-hash",
    )
    (tmp_path / "investigation_records.jsonl").write_bytes(jsonl_bytes([record]))
    (tmp_path / "operator_runs.jsonl").write_bytes(jsonl_bytes([operator]))
    (tmp_path / "opportunities.jsonl").write_bytes(jsonl_bytes([opportunity]))
    (tmp_path / "candidates.jsonl").write_text("")
    (tmp_path / "evidence").mkdir()
    (tmp_path / "evidence/packets.jsonl").write_text("")
    (tmp_path / "findings.jsonl").write_text("")

    manifest = seal_run(tmp_path, created_at="2026-07-17T00:01:00Z")
    assert manifest.completion_status == "complete"
    assert (manifest.investigations, manifest.operator_runs, manifest.opportunities) == (1, 1, 1)
    assert {item.schema_version for item in manifest.artifacts} >= {
        "investigation-task1", "investigation-record1", "operator-run1", "review-opportunity1"
    }


def test_baseline_preflight_never_promotes_unproven_retrieval(tmp_path):
    inspected = inspect_baseline()
    claims = {item["claim_id"]: item for item in inspected["claims"]["claims"]}
    assert claims["automatic_source_recovery"]["status"] == "unproven"
    result = write_baseline(tmp_path, allow_pending=True)
    assert json.loads((tmp_path / "baseline_lock.json").read_text()) == result["lock"]
    assert json.loads((tmp_path / "claim_matrix.json").read_text()) == result["claims"]


def test_baseline_confirmation_records_semantics_without_requiring_a_favorable_result(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps({
        "schema_version": "v4-semantic-report1",
        "judge_version": "test",
        "per_obligation": [
            {"issue_hit": True, "resolution_hit": True},
            {"issue_hit": True, "resolution_hit": True},
            {"issue_hit": False, "resolution_hit": False},
        ],
    }))
    payload = json.loads(report.read_text())
    payload["counts"] = {"candidates": 2, "paired_candidates": 2}
    report.write_text(json.dumps(payload))
    confirmation = _oracle_evidence_confirmation(report)
    assert confirmation["status"] == "complete"
    assert (confirmation["issue_hits"], confirmation["resolution_hits"]) == (2, 2)
    payload = json.loads(report.read_text())
    payload["per_obligation"][1]["resolution_hit"] = False
    report.write_text(json.dumps(payload))
    confirmation = _oracle_evidence_confirmation(report)
    assert confirmation["status"] == "complete"
    assert (confirmation["issue_hits"], confirmation["resolution_hits"]) == (2, 1)


def test_phase2_inventory_covers_every_target_and_uses_parser_components():
    graphs = _load("derived/change_graphs.jsonl", ChangeGraph)
    inventory = build_inventory(graphs)
    assert len(inventory) == sum(len(graph.targets) for graph in graphs) == 184
    assert len({item.primary_change_id for item in inventory}) == 184
    assert all(item.classification_status == "complete" for item in inventory)
    report = inventory_report(inventory)
    assert report["by_lifecycle"] == {"added": 116, "modified": 67, "removed": 1}
    assert report["unknown_reasons"] == {}

    target_by_name = {
        target.declaration_name: target
        for graph in graphs
        for target in graph.targets
        if target.declaration_name
    }
    record_by_change = {item.primary_change_id: item for item in inventory}
    proof_edit = record_by_change[target_by_name["PowerSeries.support_expand"].change_id]
    statuses = {item.component: item.status for item in proof_edit.component_deltas}
    assert statuses["statement_or_type"] == "unchanged"
    assert statuses["proof"] == "modified"
    assert statuses["name"] == "unchanged"

    statement_edit = record_by_change[target_by_name["continuousOn_floor"].change_id]
    statuses = {item.component: item.status for item in statement_edit.component_deltas}
    assert statuses["statement_or_type"] == "modified"
    assert statuses["proof"] == "modified"

    added = record_by_change[target_by_name["Metric.card_maximalSeparatedSet"].change_id]
    statuses = {item.component: item.status for item in added.component_deltas}
    assert {"name", "statement_or_type", "proof"} <= {
        component for component, status in statuses.items() if status == "added"
    }

    trailing_comment = record_by_change[target_by_name["Vector3.unexpandNil"].change_id]
    statuses = {item.component: item.status for item in trailing_comment.component_deltas}
    assert statuses["documentation"] == "modified"
    assert all(
        any(component.status != "unchanged" for component in item.component_deltas)
        for item in inventory
        if item.lifecycle == "modified"
    )


def test_phase2_relations_are_deterministic_scoped_and_evidence_backed():
    graphs = _load("derived/change_graphs.jsonl", ChangeGraph)
    first_relations, first_evidence = build_relations(graphs)
    second_relations, second_evidence = build_relations(list(reversed(graphs)))
    assert jsonl_bytes(first_relations) == jsonl_bytes(second_relations)
    assert jsonl_bytes(first_evidence) == jsonl_bytes(second_evidence)
    assert len(first_relations) == len(first_evidence)
    assert relation_report(first_relations, first_evidence)["by_kind"] == {
        "changed_siblings": 94,
        "declaration_dependency": 47,
        "direct_use_of_changed_declaration": 64,
        "name_family": 78,
    }
    evidence_ids = {item.evidence_id for item in first_evidence}
    assert all(set(item.evidence_artifact_ids) <= evidence_ids for item in first_relations)

    graph = next(item for item in graphs if item.pr_number == 33098)
    targets = {item.declaration_name: item for item in graph.targets if item.declaration_name}
    wrapper = targets["Metric.coveringNumber_le_packingNumber"]
    cardinality = targets["Metric.card_maximalSeparatedSet"]
    maximal_cover = targets["Metric.isCover_maximalSeparatedSet"]
    relation_keys = {
        (item.relation_kind, item.source_change_id, item.related_change_ids[0])
        for item in first_relations
    }
    assert (
        "direct_use_of_changed_declaration", wrapper.change_id, cardinality.change_id
    ) in relation_keys
    assert (
        "name_family", cardinality.change_id, maximal_cover.change_id
    ) in relation_keys


def test_phase2_schedule_covers_active_methods_and_exposes_deferred_method_gaps():
    graphs = _load("derived/change_graphs.jsonl", ChangeGraph)
    inventory = build_inventory(graphs)
    relations, _evidence = build_relations(graphs)
    units = _load("derived/work_units.jsonl", ReviewWorkUnit)
    # Explicitly the `/3` registry: every number below is that registry's frozen schedule,
    # and `load_registry()` now defaults to `/4`, which retired three single-PR operators.
    legacy_path = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1/methods.jsonl")
    methods = load_registry(legacy_path)
    registry_hash = sha256_file(legacy_path)
    tasks = schedule_investigations(inventory, relations, units, methods, registry_hash)
    assert len(tasks) == 421
    assert all(item.method_registry_sha256 == registry_hash for item in tasks)
    report = schedule_report(tasks, units)
    assert report["by_method"] == {
        "baseline_failure.v1": 155,
        "canonical_api_search.v1": 93,
        "naming_contrast.v1": 80,
        "wrapper_composition.v1": 93,
    }
    judgments = _load("gold/judgments.jsonl", JudgmentNode)
    audit = audit_smoke_schedule(tasks, judgments, methods)
    assert audit["gate_status"] == "pass"
    assert audit["active_method_coverage"] == {"covered": 3, "total": 3}
    assert audit["planned_method_gaps"] == 3
    assert audit["overall_accounted"] == 6
    assert {item["audit_status"] for item in audit["rows"]} == {"scheduled", "method_gap"}


def test_phase2_manifest_seals_production_artifacts_without_gold_lineage():
    treatment = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1")
    manifest_path = treatment / "manifest.json"
    manifest = OpportunityTreatmentManifest.model_validate_json(manifest_path.read_text())
    artifacts = [manifest.method_registry, *manifest.derived_artifacts]

    identity = manifest.model_dump(
        mode="json", exclude={"schema_version", "source_sha256"}
    )
    assert manifest.source_sha256 == _digest(identity)
    assert all(
        artifact.sha256 == sha256_file(treatment / artifact.path)
        for artifact in artifacts
    )
    assert not any("gold" in Path(artifact.path).parts for artifact in artifacts)
