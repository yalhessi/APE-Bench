"""Offline gates for the Phase 9 fixed-orchestration smoke."""

import json
from pathlib import Path

import pytest

from ape.tasks.lean_tasks.formal_math.pr_review_v4.opportunities import (
    build_verification_artifact,
)
from src.datasets.pr_review_v4.phase9_fixed_orchestration import (
    DEFAULT_OUT,
    build_baseline_union,
    build_evaluation_scope,
    build_release,
    aggregate_reports,
    finalize_repetition,
    ingest_repetition,
)
from src.datasets.pr_review_v4.schema import (
    ChangeGraph,
    OpportunityEvidenceArtifact,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewOpportunity,
    ReviewWorkUnit,
)
from src.datasets.pr_review_v4.task_adapter import build_review_opportunity_task_data


def _load(path, cls):
    return [cls.model_validate_json(line) for line in path.read_text().splitlines() if line]


def test_fixed_release_is_gold_free_and_routes_only_deferred_work():
    manifest = build_release(DEFAULT_OUT)
    units = _load(DEFAULT_OUT / "derived/work_units.jsonl", ReviewWorkUnit)
    prompts = _load(DEFAULT_OUT / "derived/rendered_prompts.jsonl", RenderedPrompt)
    ledger = [
        json.loads(line)
        for line in (DEFAULT_OUT / "derived/pipeline_ledger.jsonl").read_text().splitlines()
    ]
    assert manifest.pr_numbers == [33098, 33438]
    assert len(units) == len(prompts) == 2
    assert sum(item["adjudication_route"] == "model" for item in ledger) == 2
    assert sum(item["adjudication_route"] == "deterministic" for item in ledger) == 4
    prompt_text = "\n".join(item.user_prompt.lower() for item in prompts)
    assert "gold obligation" not in prompt_text and "maintainer comment" not in prompt_text
    assert "obligation:" not in (DEFAULT_OUT / "manifest.json").read_text()
    assert not (DEFAULT_OUT / "evaluation_scope.json").exists()


def test_evaluation_scope_is_separate_and_current(tmp_path):
    scope = build_evaluation_scope(DEFAULT_OUT, tmp_path / "scope.json")
    assert len(scope["source_work_unit_ids"]) == 2
    assert len(scope["obligation_ids"]) == 8
    assert len(scope["full_pr_obligation_ids"]) == 14
    assert set(scope["obligation_ids"]) < set(scope["full_pr_obligation_ids"])


def _synthetic_responses(tmp_path):
    units = _load(DEFAULT_OUT / "derived/work_units.jsonl", ReviewWorkUnit)
    opportunities = _load(DEFAULT_OUT / "derived/opportunities.jsonl", ReviewOpportunity)
    evidence = _load(
        DEFAULT_OUT / "derived/opportunity_evidence.jsonl", OpportunityEvidenceArtifact
    )
    task_rows = [
        json.loads(line)
        for line in (DEFAULT_OUT / "derived/investigation_tasks.jsonl").read_text().splitlines()
    ]
    task_by_investigation = {item["investigation_id"]: item for item in task_rows}
    opportunity_by_unit = {
        task_by_investigation[item.investigation_id]["work_unit_id"]: item
        for item in opportunities
        if task_by_investigation[item.investigation_id]["work_unit_id"] in {
            unit.work_unit_id for unit in units
        }
    }
    evidence_by_id = {item.artifact_id: item for item in evidence}
    rows = []
    for unit in units:
        opportunity = opportunity_by_unit[unit.work_unit_id]
        change_id = opportunity.primary_change_id
        subject = unit.primary_subjects_by_change[change_id]
        entities = unit.entity_ids_by_change[change_id]
        path = next(
            graph_target.path
            for graph in _load(DEFAULT_OUT / "derived/change_graphs.jsonl", ChangeGraph)
            for graph_target in graph.targets
            if graph_target.change_id == change_id
        )
        edit = {
            "path": path,
            "declaration_name": subject,
            "new_declaration": f"theorem {subject.rsplit('.', 1)[-1]} : True := by trivial",
            "line_start": None,
            "line_end": None,
            "replacement": None,
        }
        artifact = build_verification_artifact(
            opportunity.opportunity_id,
            edit,
            opportunity.source_artifact_ids,
            evidence_by_id[opportunity.source_artifact_ids[0]].snapshot_sha,
        )
        rows.append({
            "work_unit_id": unit.work_unit_id,
            "success": True,
            "error": None,
            "response": {
                "candidates": [{
                    "primary_change_id": change_id,
                    "primary_entity_id": entities[0] if entities else None,
                    "primary_subject": subject,
                    "change_ids": [change_id],
                    "concern_family": "style",
                    "concern_label": opportunity.method_id,
                    "severity": "advisory",
                    "claim": f"{subject} uses a lower-level implementation.",
                    "requested_change": f"Replace {subject} with the discovered transformation.",
                    "suggested_fix": "Use the discovered source chain.",
                    "proposed_edit": edit,
                    "model_confidence": 0.8,
                }],
                "adjudications": [{
                    "opportunity_id": opportunity.opportunity_id,
                    "disposition": "request",
                    "validity": "valid",
                    "norm_strength": "canonical",
                    "review_worthiness": "advisory",
                    "evidence_ids": [*opportunity.source_artifact_ids, artifact["artifact_id"]],
                    "rationale": "The replacement is valid and review-worthy.",
                    "candidate_ordinal": 0,
                }],
                "verification_artifacts": [artifact],
            },
        })
    path = tmp_path / "responses.jsonl"
    path.write_text("".join(json.dumps(item) + "\n" for item in rows))
    return path, rows


def test_ingest_requires_and_preserves_verified_model_requests(tmp_path):
    responses, rows = _synthetic_responses(tmp_path)
    report = ingest_repetition(DEFAULT_OUT, responses, tmp_path / "ingested")
    assert report["complete"] is True
    assert report["counts"] == {
        "model_units": 2,
        "adjudications": 2,
        "deterministic_candidates": 1,
        "model_candidates": 2,
        "candidates": 3,
        "verification_artifacts": 2,
    }
    candidates = [
        json.loads(line)
        for line in (tmp_path / "ingested/candidates.jsonl").read_text().splitlines()
    ]
    assert all(item["opportunity_ids"] for item in candidates)

    rows[0]["response"]["verification_artifacts"] = []
    rejected = tmp_path / "rejected.jsonl"
    rejected.write_text("".join(json.dumps(item) + "\n" for item in rows))
    with pytest.raises(ValueError, match="lacks persisted Lean verification"):
        ingest_repetition(DEFAULT_OUT, rejected, tmp_path / "rejected")


def test_finalize_attributes_every_full_pr_obligation(tmp_path):
    responses, _rows = _synthetic_responses(tmp_path)
    ingested = tmp_path / "ingested"
    ingest_repetition(DEFAULT_OUT, responses, ingested)
    semantic = tmp_path / "semantic"
    semantic.mkdir()
    scope = build_evaluation_scope(DEFAULT_OUT, semantic / "evaluation_scope.json")
    (semantic / "matches.jsonl").write_text("")
    (semantic / "report.json").write_text(json.dumps({
        "schema_version": "v4-semantic-report1",
        "counts": {"obligations": 8, "candidates": 3},
        "location_recall": 0.375,
        "issue_recall": 0.0,
        "resolution_recall": 0.0,
        "paired_candidate_issue_precision": 0.0,
        "per_obligation": [],
    }))
    report = finalize_repetition(DEFAULT_OUT, ingested, semantic, tmp_path / "final")
    assert report["complete"] is True
    assert report["counts"]["matched_obligations"] == len(scope["obligation_ids"]) == 8
    assert report["counts"]["full_pr_obligations"] == 14
    attributions = [
        json.loads(line)
        for line in (tmp_path / "final/miss_attributions.jsonl").read_text().splitlines()
    ]
    assert len(attributions) == 14
    assert sum(item["in_matched_scope"] for item in attributions) == 8


def test_phase9_task_adapter_requires_verified_edits_for_bounded_methods():
    units = _load(DEFAULT_OUT / "derived/work_units.jsonl", ReviewWorkUnit)
    prompts = _load(DEFAULT_OUT / "derived/rendered_prompts.jsonl", RenderedPrompt)
    episodes = _load(DEFAULT_OUT / "input/episodes.jsonl", ReviewEpisodeInput)
    opportunities = _load(DEFAULT_OUT / "derived/opportunities.jsonl", ReviewOpportunity)
    evidence = _load(
        DEFAULT_OUT / "derived/opportunity_evidence.jsonl", OpportunityEvidenceArtifact
    )
    task_rows = [
        json.loads(line)
        for line in (DEFAULT_OUT / "derived/investigation_tasks.jsonl").read_text().splitlines()
    ]
    task_by_investigation = {item["investigation_id"]: item for item in task_rows}
    unit = units[0]
    relevant = [
        item for item in opportunities
        if task_by_investigation[item.investigation_id]["work_unit_id"] == unit.work_unit_id
    ]
    data = build_review_opportunity_task_data(
        unit,
        next(item for item in episodes if item.episode_id == unit.episode_id),
        next(item for item in prompts if item.work_unit_id == unit.work_unit_id),
        relevant,
        evidence,
    )
    assert data.verification_required_opportunity_ids == [relevant[0].opportunity_id]


def test_baseline_union_adds_only_the_missing_matched_work_unit(tmp_path):
    source_scope = json.loads((DEFAULT_OUT / "evaluation_source_scope.json").read_text())
    missing_id = next(
        item for item in source_scope["source_work_unit_ids"]
        if item != "wu:b017b7314c4bea62d8f968c3"
    )
    extension = tmp_path / "extension.jsonl"
    extension.write_text(json.dumps({
        "work_unit_id": missing_id,
        "success": True,
        "error": None,
        "response": {"candidates": []},
    }) + "\n")
    report = build_baseline_union(
        DEFAULT_OUT,
        Path("results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidate_responses.jsonl"),
        extension,
        tmp_path / "union",
    )
    assert report["complete"] is True
    assert report["positive_model_calls"] == 2
    assert report["control_model_calls"] == 1


def test_aggregate_separates_implementation_readiness_from_efficacy(tmp_path):
    fixed_paths = []
    baseline_paths = []
    for index in range(3):
        fixed = tmp_path / f"fixed-{index}.json"
        fixed.write_text(json.dumps({
            "complete": True,
            "counts": {"control_findings": 0},
            "semantic": {
                "issue_recall": 0.25,
                "resolution_recall": 0.125,
                "paired_candidate_issue_precision": 1.0,
            },
            "stage_counts": {"recovered": 2, "source_retrieval": 12},
        }))
        baseline = tmp_path / f"baseline-{index}.json"
        baseline.write_text(json.dumps({
            "issue_recall": 0.5,
            "resolution_recall": 0.25,
            "paired_candidate_issue_precision": 0.75,
        }))
        fixed_paths.append(fixed)
        baseline_paths.append(baseline)
    report = aggregate_reports(fixed_paths, baseline_paths, tmp_path / "aggregate")
    assert report["implementation_ready"] is True
    assert report["decision"] == "implementation_ready_for_broader_pilot"
    assert report["descriptive_deltas"]["issue_recall"] == -0.25
    assert "call_matched_baseline_union" in report
