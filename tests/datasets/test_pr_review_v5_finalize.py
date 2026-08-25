"""Admission: what the system is allowed to say, and who is allowed to decide it.

The lead routes. It does not publish. These tests pin the two gates it cannot reach, plus
the property that makes the three-mode comparison fair — the deterministic arm is identical
in all of them because it involves no model call.

Both gates are *closed by default* on purpose. `generalist_findings` treats
`supported_candidate_ids=None` as "publish everything", so reaching that branch by omission
would silently convert a publication warrant into a rubber stamp for the 53% of the corpus
no collector can support.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.datasets.pr_review_v4.io import load_jsonl
from src.datasets.pr_review_v4.schema import ReviewWorkUnit
from src.datasets.pr_review_v5.finalize import finalize, ingest_responses

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.fixture(scope="module")
def unit():
    """A real work unit with at least one declaration target, so a claim can anchor."""

    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    for candidate in units:
        change_id = candidate.change_ids[0]
        if candidate.primary_subjects_by_change.get(change_id) and \
                candidate.entity_ids_by_change.get(change_id):
            return candidate
    pytest.skip("no suitable work unit in the release")


def _candidate(unit, **overrides):
    change_id = unit.change_ids[0]
    payload = {
        "primary_change_id": change_id,
        "primary_entity_id": unit.entity_ids_by_change[change_id][0],
        "primary_subject": unit.primary_subjects_by_change[change_id],
        "change_ids": [change_id],
        "concern_family": "proof-golf",
        "issue_kind": "proof_simplification",
        "concern_label": "proof-golf",
        "severity": "advisory",
        "claim": f"The proof of {unit.primary_subjects_by_change[change_id]} can be shorter.",
        "requested_change": (
            f"Shorten the proof of {unit.primary_subjects_by_change[change_id]}."),
        "proposed_edit": {
            "path": unit.paths_by_change.get(change_id) or "Mathlib/A.lean",
            "declaration_name": "Foo.bar",
            "new_declaration": "theorem Foo.bar : True := trivial",
        },
    }
    payload.update(overrides)
    return payload


def _response(unit, arm_id, candidates, artifacts=(), spec_id=None):
    return {
        "invocation_id": f"{unit.work_unit_id}#{arm_id}",
        "arm_id": arm_id,
        "work_unit_id": unit.work_unit_id,
        "spec_id": spec_id,
        "pr_number": unit.pr_number,
        "status": "success",
        "candidates": list(candidates),
        "verification_artifacts": list(artifacts),
    }


def _artifact(unit, ordinal, success=True):
    return {
        "schema_version": "residual-candidate-verification1",
        "artifact_id": f"residual-candidate-verification:{ordinal:024d}",
        "work_unit_id": unit.work_unit_id,
        "candidate_ordinal": ordinal,
        "stage": "proposed_edit",
        "kind": "lean_compile",
        "success": success,
        "path": "Mathlib/A.lean",
        "content": "compiled",
        "snapshot_sha": "abc",
        "source_sha256": "d" * 64,
    }


def test_ingestion_splits_by_arm_and_takes_spec_from_the_invocation(unit):
    """A model is not trusted to say which agent it is: golf and idiom both declare
    `proof_simplification`, and the verifier keys its warrant on the spec."""

    generalist, specialist, evidence_specialist, artifacts, rejections = ingest_responses(
        [unit],
        [
            _response(unit, "generalist", [_candidate(unit)]),
            _response(unit, "proof_golf", [_candidate(unit)], [_artifact(unit, 0)],
                      spec_id="proof_golf"),
        ],
    )
    assert len(generalist) == 1 and generalist[0].spec_id is None
    assert len(specialist) == 1 and specialist[0].spec_id == "proof_golf"
    assert len(artifacts) == 1 and not rejections


def test_a_failed_job_contributes_nothing(unit):
    generalist, specialist, _evidence, _artifacts, _rejections = ingest_responses(
        [unit], [dict(_response(unit, "proof_golf", [_candidate(unit)]), status="failed")])
    assert not generalist and not specialist


def test_one_malformed_candidate_does_not_sink_the_batch(unit):
    """Raising would discard every other candidate and leave the drop rate unmeasurable,
    which makes the system look more precise than it is."""

    good, bad = _candidate(unit), _candidate(unit, change_ids=["change:nonexistent"])
    generalist, _spec, _evidence, _artifacts, rejections = ingest_responses(
        [unit], [_response(unit, "generalist", [good, bad])])
    assert len(generalist) == 1
    assert len(rejections) == 1


def test_generalist_claims_cannot_publish_without_evidence(unit, tmp_path):
    """The gate the lead cannot reach. Retained and counted, never published."""

    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "generalist", [_candidate(unit)])],
    )
    assert report["candidates_generalist"] == 1
    assert report["generalist_evidence_gate"] == "closed"
    issues = [json.loads(x) for x in
              (tmp_path / "run" / "issues.jsonl").read_text().splitlines() if x.strip()]
    assert issues, "the claim is retained"
    assert all(item["admission"] != "published" for item in issues)


def test_a_specialist_claim_without_a_verification_artifact_is_dropped(unit, tmp_path):
    """Dropped, not downgraded. Downgrading would smuggle an unverified claim into the one
    arm whose entire premise is that the compiler agreed."""

    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "proof_golf", [_candidate(unit)], spec_id="proof_golf")],
    )
    assert report["candidates_specialist"] == 1
    assert report["issues_total"] == 0


def test_a_specialist_claim_with_a_failed_artifact_is_dropped(unit, tmp_path):
    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "proof_golf", [_candidate(unit)],
                             [_artifact(unit, 0, success=False)], spec_id="proof_golf")],
    )
    assert report["issues_total"] == 0


def test_a_verified_specialist_claim_publishes(unit, tmp_path):
    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "proof_golf", [_candidate(unit)],
                             [_artifact(unit, 0)], spec_id="proof_golf")],
    )
    assert report["issues_published"] >= 1


def test_the_lead_assessment_changes_nothing(unit, tmp_path):
    """v1 records arbitration and applies none of it. `finalize` has no parameter through
    which an assessment could reach admission — this pins that absence."""

    import inspect

    assert "assessment" not in inspect.signature(finalize).parameters
    responses = [_response(unit, "proof_golf", [_candidate(unit)], [_artifact(unit, 0)],
                           spec_id="proof_golf")]
    first = finalize(tmp_path / "a", units=[unit], routing_mode="lead", responses=responses)
    second = finalize(tmp_path / "b", units=[unit], routing_mode="fanout", responses=responses)
    assert first["issues_sha256"] == second["issues_sha256"]


def test_routing_mode_does_not_change_the_assembler(unit, tmp_path):
    """Identical arm output must produce identical issues in every mode, or a comparison
    between modes is measuring two assemblers rather than two routers."""

    responses = [
        _response(unit, "generalist", [_candidate(unit)]),
        _response(unit, "proof_golf", [_candidate(unit)], [_artifact(unit, 0)],
                  spec_id="proof_golf"),
    ]
    digests = {
        mode: finalize(tmp_path / mode, units=[unit], routing_mode=mode,
                       responses=responses)["issues_sha256"]
        for mode in ("fanout", "rules", "lead")
    }
    assert len(set(digests.values())) == 1


def test_a_response_for_an_unknown_work_unit_is_skipped(unit, tmp_path):
    other = unit.model_copy(update={"work_unit_id": "wu:not-in-this-run"})
    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(other, "generalist", [_candidate(unit)])],
    )
    assert report["candidates_generalist"] == 0


def test_dropped_specialist_candidates_are_counted_not_just_dropped(unit, tmp_path):
    """`focused_findings` drops any specialist claim with no successful verification
    artifact — correctly, but silently. A run where every specialist claim evaporated then
    looks exactly like a run where the specialists found nothing, which is a very different
    fact about the system."""

    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "generality", [_candidate(unit)], spec_id="generality")],
    )
    assert report["candidates_specialist"] == 1
    assert report["candidates_specialist_dropped_unverified"] == 1
    assert report["dropped_unverified_by_concern"]
    assert report["issues_total"] == 0


def test_a_verified_specialist_candidate_is_not_counted_as_dropped(unit, tmp_path):
    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "proof_golf", [_candidate(unit)],
                             [_artifact(unit, 0)], spec_id="proof_golf")],
    )
    assert report["candidates_specialist_dropped_unverified"] == 0
