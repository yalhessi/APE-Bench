"""Offline and production-boundary gates for wrapper composition."""

import json
from pathlib import Path

from src.mathlib_review.io import sha256_file
from src.mathlib_review.evidence.operators.wrapper_composition import discover_wrapper_composition
from src.mathlib_review.legacy_pipeline.phase5_wrapper_smoke import (
    DEFAULT_OUT,
    DEFAULT_PARENT,
    DEFAULT_PHASE2,
    DEFAULT_WORKSPACES,
    build_artifacts,
)
from src.mathlib_review.schema import (
    ChangeGraph,
    CompositionSource,
    DatasetManifest,
    InvestigationTask,
    OpportunityEvidenceArtifact,
    OperatorRun,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewOpportunity,
    ReviewWorkUnit,
    WrapperCompositionPlan,
)


POSITIVE = "change:45cf88bca684cd3813871f4da143b9c827418cf9320465b788f860efac74900a"
CONTROL = "change:3ef5b17a805e3c6337189653431eef93e1c019e02cd250c400ab593a1ea7c57d"
RELATED = {
    "change:c5c9da88f1d990a90cb9913c331dedd39539e7c571bf7a0c98dce91de28c648f",
    "change:c7ef58137fa4b7b4ee0f8b13686be4a5afcefe2e8e8c434092e3c25c8510acc0",
    "change:d483f48d7e3a4447d26426246409ccd14c957a624be055ff2150a15e27d59768",
}


def _load(path, cls):
    return [cls.model_validate_json(line) for line in path.read_text().splitlines() if line]


def _source_inputs(primary_change_id):
    graphs = _load(DEFAULT_PARENT / "derived/change_graphs.jsonl", ChangeGraph)
    episodes = _load(DEFAULT_PARENT / "input/episodes.jsonl", ReviewEpisodeInput)
    tasks = _load(DEFAULT_PHASE2 / "derived/investigation_tasks.jsonl", InvestigationTask)
    graph = next(item for item in graphs if any(
        target.change_id == primary_change_id for target in item.targets
    ))
    episode = next(item for item in episodes if item.pr_number == graph.pr_number)
    task = next(item for item in tasks if
        item.primary_change_id == primary_change_id and item.method_id == "wrapper_composition.v1"
    )
    return task, graph, episode


def test_wrapper_discovery_composes_exact_repository_and_pr_sources():
    task, graph, episode = _source_inputs(POSITIVE)
    result = discover_wrapper_composition(
        task, graph, episode, DEFAULT_WORKSPACES / episode.base_sha
    )

    assert result.plan.status == "composed"
    assert [item.role for item in result.sources] == [
        "repository_wrapper", "cardinality_bridge", "cover_witness", "subset_witness"
    ]
    assert result.sources[0].declaration_name == "Metric.IsCover.coveringNumber_le_encard"
    assert set(result.plan.related_change_ids) == RELATED
    assert {"iInf_le", "iInf_pos", "le_of_eq"} <= set(result.plan.removed_dependencies)
    assert "coveringNumber_le_encard maximalSeparatedSet_subset" in (
        result.plan.replacement_declaration or ""
    )


def test_parallel_proof_control_does_not_create_composition():
    task, graph, episode = _source_inputs(CONTROL)
    result = discover_wrapper_composition(
        task, graph, episode, DEFAULT_WORKSPACES / episode.base_sha
    )

    assert result.plan.status == "no_composition"
    assert result.plan.replacement_declaration is None
    assert [(item.role, item.declaration_name) for item in result.sources] == [
        ("parallel_sibling", "Real.arctan_sqrt_three")
    ]


def test_frozen_phase5_release_passes_offline_gate_and_preserves_scope():
    report = json.loads((DEFAULT_OUT / "derived/wrapper_composition_report.json").read_text())
    plans = _load(DEFAULT_OUT / "derived/composition_plans.jsonl", WrapperCompositionPlan)
    sources = _load(DEFAULT_OUT / "derived/composition_sources.jsonl", CompositionSource)
    units = _load(DEFAULT_OUT / "derived/work_units.jsonl", ReviewWorkUnit)

    assert report["offline_gate"] == "pass"
    assert [item.status for item in plans] == ["composed", "no_composition"]
    assert set(plans[0].related_change_ids) == RELATED
    assert set(units[0].change_ids) == {POSITIVE}
    assert RELATED.isdisjoint(units[0].change_ids)
    assert {item.source_id for item in sources[1:4]} == RELATED


def test_phase5_operator_accounting_separates_search_applicability_and_compile():
    runs = _load(DEFAULT_OUT / "derived/operator_runs.jsonl", OperatorRun)

    assert [item.operator for item in runs[:3]] == [
        "pr_composition_search", "applicability_check", "compile_composed_edit"
    ]
    assert [item.status for item in runs[:3]] == ["completed", "completed", "unavailable"]
    assert [item.operator for item in runs[3:]] == [
        "pr_composition_search", "applicability_check", "compile_composed_edit"
    ]
    assert all(item.status == "completed" for item in runs[3:])


def test_phase5_prompts_expose_exact_chain_without_gold_or_unscoped_agenda():
    prompts = _load(DEFAULT_OUT / "derived/rendered_prompts.jsonl", RenderedPrompt)
    opportunities = _load(DEFAULT_OUT / "derived/opportunities.jsonl", ReviewOpportunity)
    evidence = _load(
        DEFAULT_OUT / "derived/opportunity_evidence.jsonl", OpportunityEvidenceArtifact
    )

    assert "Metric.IsCover.coveringNumber_le_encard" in prompts[0].user_prompt
    assert "Do not perform an unscoped review" in prompts[0].user_prompt
    assert "No composition was discovered" in prompts[1].user_prompt
    assert all("gold" not in item.user_prompt.lower() for item in prompts)
    assert opportunities[0].proposed_transformation is not None
    assert opportunities[1].proposed_transformation is None
    assert [item.kind for item in evidence if item.pr_number == 33098] == [
        "reviewed_code", "pr_relation", "repository_declaration", "composition_plan",
        "dependency_reduction", "applicability_check",
    ]


def test_phase5_generation_never_reads_gold(monkeypatch):
    original = Path.read_text

    def deny_gold(path, *args, **kwargs):
        assert "gold" not in path.parts
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", deny_gold)
    rows = build_artifacts(DEFAULT_PARENT, DEFAULT_PHASE2, DEFAULT_WORKSPACES)
    assert [item.status for item in rows["plans"]] == ["composed", "no_composition"]


def test_frozen_phase5_manifest_hashes_every_artifact_and_contains_no_gold():
    manifest = DatasetManifest.model_validate_json((DEFAULT_OUT / "manifest.json").read_text())

    assert manifest.release == "0.9.3-wrapper-composition-smoke"
    assert manifest.pr_numbers == [33098, 33438]
    assert all("gold" not in Path(item.path).parts for item in manifest.derived_artifacts)
    for artifact in manifest.input_artifacts + manifest.derived_artifacts:
        assert sha256_file(DEFAULT_OUT / artifact.path) == artifact.sha256
