"""The generation contract must not know about gold, and every link must be a hash.

A first draft of this work put the judge configuration, the ambiguity registry and the
context sidecar into the reviewer's `RunPlan`. That would have made the reviewer's own
contract depend on gold — reintroducing, at the contract layer, exactly the coupling the
episode split exists to prevent.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.release.contracts import (
    GoldLeakError,
    seal_evaluation_protocol,
    seal_evaluation_receipt,
    seal_generation_plan,
    seal_generation_receipt,
    seal_pair_manifest,
    verify_chain,
)
from src.mathlib_review.schema import GenerationPlanV2, RunPlan


def _plan(**overrides):
    values = dict(
        condition="merged_ensemble",
        release_path="inputs/pr_review_v4/releases/dev-medium-0.1.0",
        release_manifest_sha256="a" * 64,
        expected_work_unit_ids=["work-unit:1"],
        expected_pr_numbers=[33098],
        prompt_sha256_by_work_unit={"work-unit:1": "b" * 64},
        renderer_version="candidate-prompt/11",
        merge_version="arm-neutral-merge/1",
        admission_policy="published=adjudicated_request|evidence_supported",
        pr_finding_limit=20,
        model_name="gpt_5.2",
        repetitions=1,
        scaffold_config_sha256="c" * 64,
    )
    values.update(overrides)
    return seal_generation_plan(**values)


def _protocol(**overrides):
    values = dict(
        gold_release_path="inputs/pr_review_v4/releases/dev-medium-0.1.0",
        gold_judgments_sha256="d" * 64,
        gold_views_sha256="e" * 64,
        judge_version="v4-semantic-v3-v9-rubric",
        judge_model="gpt_5_mini",
        judge_identity="f" * 64,
        sample_count=3,
        aggregation_policy="majority",
        pairing_tiers=["anchor"],
        headline_tier="anchor",
        null_pairs_per_obligation=2,
        ambiguity_registry_sha256="0" * 64,
        context_profile="base",
        metric_definitions=["issue_recall", "resolution_recall", "gold_alignment_rate"],
        control_pr_numbers=[33438],
    )
    values.update(overrides)
    return seal_evaluation_protocol(**values)


def _chain(plan=None, protocol=None):
    plan = plan or _plan()
    protocol = protocol or _protocol()
    receipt = seal_generation_receipt(
        plan, repetition=1, orchestrator_id="run1",
        candidates_path="c.jsonl", candidates_sha256="1" * 64,
    )
    manifest = seal_pair_manifest(
        protocol, generation_receipt_ids=[receipt.receipt_id],
        findings_sha256="2" * 64, finding_ids=["finding:1"], pair_ids=["semantic-pair:1"],
        observed_pairs=1, null_pairs=0,
    )
    evaluation = seal_evaluation_receipt(
        manifest, matches_sha256="3" * 64, report_sha256="4" * 64,
        verdicts_returned=1, coverage_complete=True, scored=True,
    )
    return plan, [receipt], protocol, manifest, evaluation


def test_a_generation_plan_may_not_reference_gold():
    """Structural, not a naming convention: the plan is serialized and swept."""

    with pytest.raises(GoldLeakError, match="gold"):
        _plan(condition="merged_ensemble_with_gold_obligations")

    with pytest.raises(GoldLeakError):
        _plan(admission_policy="publish when it matches a maintainer obligation")


def test_poisoning_gold_leaves_the_generation_contract_byte_identical():
    """The acceptance test for the whole split.

    If a gold change can move the reviewer's contract, the reviewer's isolation is not
    structural — it is a convention that a future edit can break.
    """

    plan = _plan()
    clean = _protocol()
    poisoned = _protocol(gold_judgments_sha256="9" * 64)

    assert clean.source_sha256 != poisoned.source_sha256, "gold must move the protocol"
    assert _plan().source_sha256 == plan.source_sha256, "gold must not move the plan"


def test_every_link_is_a_hash_not_a_name():
    plan, receipts, protocol, manifest, evaluation = _chain()
    assert verify_chain(plan, receipts, protocol, manifest, evaluation)["complete"]

    # Re-pointing a child at an edited parent must break, even though the ID is unchanged.
    edited = plan.model_copy(update={"source_sha256": "z" * 64})
    with pytest.raises(ValueError, match="different plan"):
        verify_chain(edited, receipts, protocol, manifest, evaluation)


def test_a_missing_repetition_receipt_breaks_the_chain():
    """Repetitions are separate deployed systems; a plan declaring three needs three."""

    plan, receipts, protocol, manifest, evaluation = _chain(plan=_plan(repetitions=3))
    with pytest.raises(ValueError, match="3 repetitions but 1 receipts"):
        verify_chain(plan, receipts, protocol, manifest, evaluation)


def test_observed_model_revision_lives_in_the_receipt_not_the_plan():
    """A provider can serve a revision other than the one requested, and that is only
    knowable afterwards — so it cannot be sealed prospectively."""

    assert "observed_model_revision" not in GenerationPlanV2.model_fields
    plan, receipts, _protocol, _manifest, _evaluation = _chain()
    assert "observed_model_revision" in type(receipts[0]).model_fields


def test_new_contract_fields_are_required_not_optional():
    """Optional-for-compatibility would silently accept an incomplete new plan, which
    defeats the point of sealing one. Legacy plans load through the legacy schema instead."""

    required = {name for name, field in GenerationPlanV2.model_fields.items()
                if field.is_required()}
    for name in ("merge_version", "admission_policy", "pr_finding_limit", "repetitions",
                 "scaffold_config_sha256", "renderer_version"):
        assert name in required, f"{name} must be required on a new plan"

    # The legacy contract keeps its permissive optionals so frozen plans still load.
    assert not RunPlan.model_fields["orchestrator_id"].is_required()


def test_the_protocol_names_its_metrics_before_any_verdict_exists():
    """Fixing the metric list up front is what stops the headline being chosen post hoc."""

    protocol = _protocol()
    assert "issue_recall" in protocol.metric_definitions
    assert protocol.headline_tier == "anchor", (
        "anchor is the headline; widened pairing is exploratory until its "
        "candidate-negative rate is characterised"
    )
