"""Offline gates for the frozen implementation registry and capability assessments."""

import pytest

from src.mathlib_review.opportunities.implementation_registry import (
    assess_capabilities,
    build_registry_files,
    default_contracts,
    default_implementations,
    load_contracts,
    load_implementations,
    validate_contracts,
    validate_implementations,
)
from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, sha256_bytes
from src.mathlib_review.schema import ChangeGraph, ChangeTarget, InvestigationTask


EPISODE = "episode:test"
PR = 100


def _target(change_id, code, path="Mathlib/Test.lean", kind="declaration"):
    return ChangeTarget(
        change_id=change_id,
        episode_id=EPISODE,
        pr_number=PR,
        kind=kind,
        path=path,
        declaration_kind="theorem" if kind == "declaration" else None,
        changed_range_ids=[],
        diff_fragments=[],
        reviewed_code=code,
        parse_status="semantic" if kind == "declaration" else "structural",
        source_sha256="target-hash",
    )


def _graph(targets):
    return ChangeGraph(
        graph_id="graph:test",
        episode_id=EPISODE,
        repo="leanprover-community/mathlib4",
        pr_number=PR,
        round_index=1,
        patch_sha256="patch-hash",
        parser_version="test/1",
        changed_ranges=[],
        entities=[],
        targets=targets,
        file_coverage=[],
        source_sha256="graph-hash",
    )


def _task(investigation_id, method_id, change_id, related=()):
    return InvestigationTask(
        investigation_id=investigation_id,
        method_id=method_id,
        work_unit_id="work-unit:test",
        episode_id=EPISODE,
        pr_number=PR,
        modification_ids=["modification:test"],
        primary_change_id=change_id,
        related_change_ids=list(related),
        expected_operators=["applicability_check"],
        method_registry_sha256="registry-hash",
        source_sha256="task-hash",
    )


NAMING_POSITIVE = (
    "lemma Metric.card_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :\n"
    "    (maximalSeparatedSet ε A).encard = packingNumber ε A := by\n"
    "  simp\n"
)
NAMING_NO_CARD_PREFIX = NAMING_POSITIVE.replace(
    "Metric.card_maximalSeparatedSet", "Metric.encard_eq_packingNumber"
)
NAMING_NO_SUBJECT = NAMING_POSITIVE.replace(".encard", ".ncard")

INSERT_SEPARATION_POSITIVE = (
    "theorem coveringNumber_pos : coveringNumber ε A ≤ 3 := by\n"
    "  let C := {x} ∪ maximalSeparatedSet ε A\n"
    "  have hx : x ∉ maximalSeparatedSet ε A := by\n"
    "    simp\n"
    "  push_neg at hd\n"
    "  have hsep : IsSeparated ε C := by\n"
    "    rcases hcase with h | h\n"
    "    exact bar h1 h2 h3\n"
    "  exact hsep.elim\n"
)
INSERT_SEPARATION_NEGATIVE = INSERT_SEPARATION_POSITIVE.replace("  push_neg at hd\n", "")

WRAPPER_PRIMARY = (
    "theorem coveringNumber_le_packingNumber :\n"
    "    coveringNumber ε A ≤ packingNumber ε A := by\n"
    "  sorry\n"
)
WRAPPER_CARDINALITY = (
    "lemma card_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :\n"
    "    (maximalSeparatedSet ε A).encard = packingNumber ε A := by\n"
    "  sorry\n"
)
WRAPPER_COVER = (
    "lemma isCover_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :\n"
    "    IsCover (maximalSeparatedSet ε A) ε A := by\n"
    "  sorry\n"
)
WRAPPER_SUBSET = (
    "lemma maximalSeparatedSet_subset : maximalSeparatedSet ε A ⊆ A := by\n"
    "  sorry\n"
)


def test_default_registries_are_sealed_deterministic_and_round_trip(tmp_path):
    assert jsonl_bytes(default_implementations()) == jsonl_bytes(default_implementations())
    assert jsonl_bytes(default_contracts()) == jsonl_bytes(default_contracts())
    implementations, contracts = build_registry_files(tmp_path)
    assert load_implementations(tmp_path / "implementations.jsonl") == implementations
    assert load_contracts(tmp_path / "method_expression_contracts.jsonl") == contracts
    assert [item.implementation_id for item in implementations] == [
        "baseline_failure.target_compile.v1",
        "canonical_api.insert_separation.v1",
        "wrapper_composition.packing_cover_chain.v1",
        "lint_norm.text_style.v1",
        "repository_policy.forbidden_construct.v1",
        "naming_contrast.encard_subject_prefix.v1",
        "naming_norm.subject_prefix.v1",
    ]
    # Rebuilding into the same directory must be byte-identical (write_once no-op).
    build_registry_files(tmp_path)


def test_registry_rejects_tampering_and_target_specific_tokens():
    implementations = default_implementations()
    tampered = implementations[0].model_copy(update={"max_opportunities": 99})
    with pytest.raises(ValueError, match="source hash mismatch"):
        validate_implementations([tampered, *implementations[1:]])

    poisoned = implementations[1].model_copy(update={"operator_version": "tuned-for-33098/1"})
    identity = poisoned.model_dump(mode="json", exclude={"source_sha256"})
    poisoned = poisoned.model_copy(
        update={"source_sha256": sha256_bytes(canonical_json_bytes(identity))}
    )
    with pytest.raises(ValueError, match="target-specific or gold token"):
        validate_implementations([implementations[0], poisoned, *implementations[2:]])

    contracts = default_contracts()
    with pytest.raises(ValueError, match="cover the frozen method registry"):
        validate_contracts(contracts[:-1])


def test_capability_predicates_accept_supported_and_reject_nearby_shapes():
    targets = [
        _target("change:naming-pos", NAMING_POSITIVE),
        _target("change:naming-noprefix", NAMING_NO_CARD_PREFIX),
        _target("change:naming-nosubject", NAMING_NO_SUBJECT),
        _target("change:insert-pos", INSERT_SEPARATION_POSITIVE),
        _target("change:insert-neg", INSERT_SEPARATION_NEGATIVE),
        _target("change:wrapper-pos", WRAPPER_PRIMARY),
        _target("change:wrapper-cardinality", WRAPPER_CARDINALITY),
        _target("change:wrapper-cover", WRAPPER_COVER),
        _target("change:wrapper-subset", WRAPPER_SUBSET),
        _target("change:non-lean", "Some prose.", path="docs/readme.md", kind="non_lean"),
    ]
    graph = _graph(targets)
    wrapper_related = [
        "change:wrapper-cardinality", "change:wrapper-cover", "change:wrapper-subset",
    ]
    tasks = [
        _task("investigation:n1", "naming_contrast.v1", "change:naming-pos"),
        _task("investigation:n2", "naming_contrast.v1", "change:naming-noprefix"),
        _task("investigation:n3", "naming_contrast.v1", "change:naming-nosubject"),
        _task("investigation:c1", "canonical_api_search.v1", "change:insert-pos"),
        _task("investigation:c2", "canonical_api_search.v1", "change:insert-neg"),
        _task("investigation:w1", "wrapper_composition.v1", "change:wrapper-pos", wrapper_related),
        _task("investigation:w2", "wrapper_composition.v1", "change:wrapper-pos", wrapper_related[:2]),
        _task("investigation:b1", "baseline_failure.v1", "change:naming-pos"),
        _task("investigation:b2", "baseline_failure.v1", "change:non-lean"),
    ]
    assessments = assess_capabilities(tasks, [graph], default_implementations())
    by_task = {item.investigation_id: item for item in assessments}
    assert len(assessments) == len(tasks)

    assert by_task["investigation:n1"].status == "supported"
    assert by_task["investigation:n2"].status == "not_applicable"
    assert by_task["investigation:n2"].reason_code == "encard_subject_without_card_prefix"
    assert by_task["investigation:n3"].status == "unsupported_shape"

    assert by_task["investigation:c1"].status == "supported"
    assert by_task["investigation:c2"].status == "unsupported_shape"
    assert by_task["investigation:c2"].reason_code == "no_insert_separation_template"

    assert by_task["investigation:w1"].status == "supported"
    assert by_task["investigation:w2"].status == "not_applicable"
    assert "subset_witness" in by_task["investigation:w2"].reason_code

    assert by_task["investigation:b1"].status == "supported"
    assert by_task["investigation:b2"].status == "unsupported_shape"
    assert by_task["investigation:b2"].reason_code == "non_lean_target"

    # Determinism: identical inputs must produce byte-identical assessments.
    again = assess_capabilities(tasks, [graph], default_implementations())
    assert jsonl_bytes(assessments) == jsonl_bytes(again)


def test_assessments_have_one_terminal_status_and_explicit_reasons():
    graph = _graph([_target("change:naming-pos", NAMING_POSITIVE)])
    task = _task("investigation:n1", "naming_contrast.v1", "change:naming-pos")
    (assessment,) = assess_capabilities([task], [graph], default_implementations())
    assert assessment.status == "supported"
    assert assessment.reason_code
    assert assessment.required_input_status["reviewed_declaration"] == "available"

    # A task whose target is absent from every change graph is an explicit failure,
    # not a silent drop.
    orphan = _task("investigation:x1", "naming_contrast.v1", "change:missing")
    (failed,) = assess_capabilities([orphan], [graph], default_implementations())
    assert failed.status == "failed"
    assert failed.reason_code == "missing_change_graph_target"
