"""Offline and production-boundary gates for semantic naming contrast."""

import json
from pathlib import Path

from src.datasets.pr_review_v4.io import sha256_file
from src.datasets.pr_review_v4.operators.naming_contrast import (
    NamingPopulationScan,
    declaration_conclusion,
    infer_semantic_subject,
    outer_lhs,
    population_counts,
    proposed_subject_name,
    strong_subject_prefix_norm,
)
from src.datasets.pr_review_v4.phase4_naming_smoke import (
    DEFAULT_OUT,
    DEFAULT_PARENT,
    DEFAULT_PHASE2,
    DEFAULT_WORKSPACES,
    build_artifacts,
)
from src.datasets.pr_review_v4.schema import (
    ChangeGraph,
    DatasetManifest,
    InvestigationTask,
    NameCollisionResult,
    NamingPopulationMember,
    NormRecord,
    ReviewOpportunity,
    SemanticSubjectInference,
)


POSITIVE = "change:c5c9da88f1d990a90cb9913c331dedd39539e7c571bf7a0c98dce91de28c648f"
CONTROL = "change:1fb113759e6725f85c7cfb4533f6c6f4774df50b67fad5c755161b1d1f121f9e"


def _load(path, cls):
    return [cls.model_validate_json(line) for line in path.read_text().splitlines() if line]


def test_conclusion_subject_parser_distinguishes_direct_and_role_conditioned_encard():
    direct = (
        "lemma card_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :\n"
        "    (maximalSeparatedSet ε A).encard = packingNumber ε A :="
    )
    existential = (
        "lemma exists_set_encard_eq_packingNumber (h : packingNumber ε A ≠ ⊤) :\n"
        "    ∃ C, C ⊆ A ∧ C.encard = packingNumber ε A :="
    )
    assert outer_lhs(declaration_conclusion(direct)) == "(maximalSeparatedSet ε A).encard"
    assert outer_lhs(declaration_conclusion(existential)) is None


def test_phase4_subject_inferences_and_proposed_name_are_method_specific():
    graph = next(
        item for item in _load(DEFAULT_PARENT / "derived/change_graphs.jsonl", ChangeGraph)
        if item.pr_number == 33098
    )
    tasks = _load(DEFAULT_PHASE2 / "derived/investigation_tasks.jsonl", InvestigationTask)
    target_by_change = {item.change_id: item for item in graph.targets}
    task_by_change = {
        item.primary_change_id: item for item in tasks
        if item.method_id == "naming_contrast.v1" and item.pr_number == 33098
    }
    positive = infer_semantic_subject(task_by_change[POSITIVE], target_by_change[POSITIVE])
    control = infer_semantic_subject(task_by_change[CONTROL], target_by_change[CONTROL])

    assert (positive.subject, positive.subject_role, positive.confidence) == (
        "Set.encard", "direct_lhs", "high"
    )
    assert proposed_subject_name("Metric.card_maximalSeparatedSet", positive) == (
        "Metric.encard_maximalSeparatedSet"
    )
    assert (control.subject, control.subject_role) == ("Set.encard", "role_conditioned")
    assert proposed_subject_name("Metric.exists_set_encard_eq_packingNumber", control) is None


def test_frozen_naming_population_is_complete_scoped_and_strong():
    members = _load(
        DEFAULT_OUT / "derived/naming_population.jsonl", NamingPopulationMember
    )
    assert len(members) == 91
    assert population_counts(members) == {
        "subject_prefix": 87,
        "subject_elsewhere": 4,
        "conflicting_prefix": 0,
        "role_specific_other": 0,
    }
    assert strong_subject_prefix_norm(members)
    assert len({item.member_id for item in members}) == 91
    assert all(item.snapshot_sha == "af239326a46dea977a6d5444466c14aa423f4b10" for item in members)


def test_phase4_generation_never_reads_gold(monkeypatch):
    members = _load(
        DEFAULT_OUT / "derived/naming_population.jsonl", NamingPopulationMember
    )
    scan = NamingPopulationScan(
        members=members,
        all_fullnames={item.fullname for item in members},
        parsed_files=7409,
        parse_failures=[],
    )
    monkeypatch.setattr(
        "src.datasets.pr_review_v4.phase4_naming_smoke.scan_repository_population",
        lambda _workspace, _snapshot: scan,
    )
    original = Path.read_text

    def deny_gold(path, *args, **kwargs):
        assert "gold" not in path.parts
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", deny_gold)
    rows = build_artifacts(DEFAULT_PARENT, DEFAULT_PHASE2, DEFAULT_WORKSPACES)
    assert len(rows["opportunities"]) == 2
    assert rows["opportunities"][0].proposed_transformation is not None
    assert rows["opportunities"][1].proposed_transformation is None


def test_frozen_phase4_release_has_complete_lineage_and_no_gold_artifacts():
    manifest = DatasetManifest.model_validate_json((DEFAULT_OUT / "manifest.json").read_text())
    report = json.loads((DEFAULT_OUT / "derived/naming_contrast_report.json").read_text())
    inferences = _load(
        DEFAULT_OUT / "derived/semantic_subjects.jsonl", SemanticSubjectInference
    )
    collisions = _load(
        DEFAULT_OUT / "derived/name_collisions.jsonl", NameCollisionResult
    )
    norms = _load(DEFAULT_OUT / "derived/norm_records.jsonl", NormRecord)
    opportunities = _load(
        DEFAULT_OUT / "derived/opportunities.jsonl", ReviewOpportunity
    )

    assert report["offline_gate"] == "pass"
    assert [item.subject_role for item in inferences] == ["direct_lhs", "role_conditioned"]
    assert collisions[0].proposed_fullname == "Metric.encard_maximalSeparatedSet"
    assert not collisions[0].collision
    assert norms[0].strength == "strong_convention"
    assert (norms[0].support_count, norms[0].counterexample_count) == (87, 0)
    assert opportunities[0].proposed_transformation is not None
    assert opportunities[1].proposed_transformation is None
    assert all("gold" not in Path(item.path).parts for item in manifest.derived_artifacts)
    for artifact in manifest.input_artifacts + manifest.derived_artifacts:
        assert sha256_file(DEFAULT_OUT / artifact.path) == artifact.sha256
