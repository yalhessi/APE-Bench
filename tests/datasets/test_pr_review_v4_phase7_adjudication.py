"""Offline regression gates for Phase 7 three-axis adjudication."""

import json

import pytest
from pydantic import ValidationError

from ape.tasks.lean_tasks.formal_math.pr_review_v4.opportunities import (
    build_verification_artifact,
)
from src.datasets.pr_review_v4.phase7_adjudication import (
    DEFAULT_PRODUCTION_RELEASES,
    EvidenceView,
    OpportunityView,
    adjudicate,
    build_gate_artifacts,
    ingest_redundancy_runs,
    production_cases,
    resolve_redundancy,
    validate_bundle,
    _verification_artifact_from_raw,
)
from src.datasets.pr_review_v4.io import jsonl_bytes
from src.datasets.pr_review_v4.schema import (
    AdjudicationBundle,
    AdjudicationVote,
    NormAssessment,
)


def test_three_axis_replay_preserves_controls_and_request_precision():
    artifacts, report = build_gate_artifacts()
    assert report["counts"] == {
        "opportunities": 16,
        "production_opportunities": 6,
        "oracle_opportunities": 10,
        "oracle_controls": 5,
        "oracle_targeted": 5,
        "requests": 3,
        "redundancy_requests": 2,
    }
    assert report["gates"] == {
        "oracle_controls_no_request": True,
        "minor_proofs_not_published": True,
        "oracle_request_precision": 1.0,
        "production_request_precision": 1.0,
        "all_records_citation_validated": True,
        "candidate_issue_precision_no_decline": True,
    }
    assert len(artifacts.technical_assessments) == 16
    assert len(artifacts.norm_assessments) == 16
    assert len(artifacts.worthiness_decisions) == 16
    assert len(artifacts.bundles) == 16


def test_fixed_evidence_replay_is_byte_stable():
    first, first_report = build_gate_artifacts()
    second, second_report = build_gate_artifacts()
    assert first == second
    assert first_report == second_report


def test_canonical_and_wrapper_without_frozen_compile_route_to_redundancy():
    cases = [
        case
        for release in DEFAULT_PRODUCTION_RELEASES
        for case in production_cases(release)
        if case.proposed_alternative is not None
    ]
    by_method = {case.method: adjudicate(case) for case in cases}
    for method in ("canonical_api_search.v1", "wrapper_composition.v1"):
        result = by_method[method]
        assert result.technical_assessments[0].status == "uncertain"
        assert result.norm_assessments[0].status == "applicable"
        assert result.worthiness_decisions[0].review_worthiness == "defer"
        assert result.bundles[0].route == "redundant_adjudication"
    naming = by_method["naming_contrast.v1"]
    assert naming.technical_assessments[0].status == "valid"
    assert naming.norm_assessments[0].status == "applicable"
    assert naming.worthiness_decisions[0].review_worthiness == "request"
    assert naming.bundles[0].route == "deterministic"


def test_direct_failure_policy_is_blocking_and_deterministic():
    case = OpportunityView(
        opportunity_id="opportunity:failure",
        method="baseline_failure.v1",
        pr_number=33057,
        primary_change_id="change:failure",
        proposed_alternative="Repair the reviewed declaration.",
        evidence=(EvidenceView(
            evidence_id="evidence:compile",
            kind="mechanical_check",
            content="The reviewed declaration fails to compile.",
            snapshot_sha="reviewed-head",
        ),),
        provenance="production",
    )
    result = adjudicate(case)
    assert result.technical_assessments[0].status == "valid"
    assert result.norm_assessments[0].status == "applicable"
    decision = result.worthiness_decisions[0]
    assert (decision.review_worthiness, decision.request_force) == ("request", "blocking")
    assert not result.redundancy_requests


def test_citation_validation_rejects_foreign_evidence():
    case = production_cases(DEFAULT_PRODUCTION_RELEASES[1])[0]
    result = adjudicate(case)
    result.technical_assessments[0] = result.technical_assessments[0].model_copy(update={
        "evidence_artifact_ids": ["evidence:foreign"]
    })
    with pytest.raises(ValueError, match="outside the opportunity"):
        validate_bundle(case, result)


def test_redundant_judges_must_be_distinct_and_disagreement_defers():
    case = production_cases(DEFAULT_PRODUCTION_RELEASES[0])[0]
    result = adjudicate(case)
    request = result.redundancy_requests[0]

    def vote(index, worthiness):
        return AdjudicationVote(
            vote_id=f"vote:{index}",
            request_id=request.request_id,
            opportunity_id=request.opportunity_id,
            assessor_id=f"assessor:{index}",
            technical_status="valid" if worthiness == "request" else "uncertain",
            norm_status="applicable",
            review_worthiness=worthiness,
            evidence_artifact_ids=request.evidence_artifact_ids,
            producer="model",
            source_sha256=f"hash:{index}",
        )

    consensus = resolve_redundancy(request, [vote(1, "request"), vote(2, "defer")])
    assert (consensus.status, consensus.final_worthiness) == ("disagreement", "defer")
    duplicate = vote(1, "request").model_copy(update={"vote_id": "vote:duplicate"})
    with pytest.raises(ValueError, match="distinct assessors"):
        resolve_redundancy(request, [vote(1, "request"), duplicate])


def test_redundancy_ingest_requires_and_preserves_mechanical_evidence(tmp_path):
    artifacts, _report = build_gate_artifacts()
    request = next(
        item for item in artifacts.redundancy_requests
        if "canonical" in next(
            bundle.policy_id for bundle in artifacts.bundles
            if bundle.opportunity_id == item.opportunity_id
        )
    )
    gate = tmp_path / "gate"
    gate.mkdir()
    (gate / "redundancy_requests.jsonl").write_bytes(jsonl_bytes([request]))
    response_paths = []
    for index in (1, 2):
        run = tmp_path / f"run-{index}"
        run.mkdir()
        artifact_id = f"adjudication-verification:{index}"
        verification = {
            "schema_version": "adjudication-verification-artifact1",
            "artifact_id": artifact_id,
            "opportunity_id": request.opportunity_id,
            "kind": "lean_compile",
            "success": True,
            "source_evidence_artifact_ids": request.evidence_artifact_ids,
            "edit_sha256": f"edit:{index}",
            "content": "Lean successfully recompiled the reviewed file with the submitted edit.",
            "snapshot_sha": "reviewed-head",
            "source_sha256": f"verification:{index}",
        }
        row = {
            "success": True,
            "response": {
                "adjudications": [{
                    "opportunity_id": request.opportunity_id,
                    "disposition": "request",
                    "validity": "valid",
                    "norm_strength": "canonical",
                    "review_worthiness": "advisory",
                    "evidence_ids": [*request.evidence_artifact_ids, artifact_id],
                    "rationale": "Verified canonical replacement.",
                }],
                "verification_artifacts": [verification],
            },
        }
        path = run / "candidate_responses.jsonl"
        path.write_text(json.dumps(row) + "\n")
        response_paths.append(path)

    report = ingest_redundancy_runs(gate, response_paths, tmp_path / "ingested")
    assert report["complete"] is True
    assert report["counts"] == {
        "requests": 1,
        "votes": 2,
        "verification_artifacts": 2,
        "repaired_legacy_aliases": 0,
        "consensuses": 1,
    }
    assert next(iter(report["outcomes"].values())) == {
        "status": "agreement",
        "final_worthiness": "request",
    }

    without_verification = json.loads(response_paths[0].read_text())
    without_verification["response"]["verification_artifacts"] = []
    without_verification["response"]["adjudications"][0]["evidence_ids"] = (
        request.evidence_artifact_ids
    )
    response_paths[0].write_text(json.dumps(without_verification) + "\n")
    with pytest.raises(ValueError, match="without a persisted verification artifact"):
        ingest_redundancy_runs(gate, response_paths, tmp_path / "rejected")


def test_verification_artifact_source_lineage_does_not_alias_decision_evidence():
    decision_evidence = ["evidence:source"]
    artifact = build_verification_artifact(
        "opportunity:1",
        {"path": "Mathlib/Test.lean", "replacement": "by simp"},
        decision_evidence,
        "reviewed-head",
    )
    decision_evidence.append(artifact["artifact_id"])
    assert artifact["source_evidence_artifact_ids"] == ["evidence:source"]


def test_ingest_repairs_only_hash_proven_self_reference():
    raw = build_verification_artifact(
        "opportunity:1",
        {"path": "Mathlib/Test.lean", "replacement": "by simp"},
        ["evidence:source"],
        "reviewed-head",
    )
    raw["source_evidence_artifact_ids"].append(raw["artifact_id"])
    repaired, migrated = _verification_artifact_from_raw(raw)
    assert migrated is True
    assert repaired.source_evidence_artifact_ids == ["evidence:source"]

    raw["source_evidence_artifact_ids"].append("evidence:tampered")
    with pytest.raises(ValueError, match="cannot be hash-verified"):
        _verification_artifact_from_raw(raw)


def test_phase7_schema_invariants_reject_disconnected_records():
    with pytest.raises(ValidationError, match="at least one norm ID"):
        NormAssessment(
            assessment_id="norm-assessment:1",
            opportunity_id="opportunity:1",
            status="applicable",
            evidence_artifact_ids=["evidence:1"],
            rationale="Policy result.",
            producer="policy",
            source_sha256="hash",
        )
    with pytest.raises(ValidationError, match="requires a request ID"):
        AdjudicationBundle(
            bundle_id="bundle:1",
            opportunity_id="opportunity:1",
            policy_id="policy:1",
            technical_assessment_id="technical:1",
            norm_assessment_id="norm:1",
            worthiness_decision_id="decision:1",
            cited_claim_ids=["claim:1"],
            route="redundant_adjudication",
            source_sha256="hash",
        )
