"""Arm plumbing: a third arm must be counted, attributed and evidenced like the other two.

Each assertion here guards a way an arm can be *silently* wrong rather than loudly broken:

* A hand-written arm list in a report does not fail when an arm is added — it reports zero
  for it, which is indistinguishable from that arm having found nothing.
* `finding_from_candidate` used to hard-code `arm="generalist"`, so every focused finding would
  have been filed under the arm it is supposed to be measured against.
* A focused source with no verification artifact would publish at `verified_compile` on the
  strength of nothing, in the one arm whose entire premise is that the compiler agreed.
* A method missing from the concern/evidence tables silently defaults to `lexical_rule`, the
  weakest non-assertion tier, and loses every merge tie it takes part in.
"""

import ast
import inspect
from pathlib import Path

import pytest

from src.mathlib_review.review import conditions

from src.mathlib_review.review import merge
from src.mathlib_review.opportunities.method_registry import default_methods
from src.mathlib_review.schema import ARMS, PRODUCING_ARMS, FindingSource


def test_the_arm_vocabulary_is_derived_from_the_model():
    assert set(PRODUCING_ARMS) == set(ARMS) - {"merged"}
    assert "focused_agent" in ARMS


def test_reports_never_hard_code_the_arm_list():
    """`by_arm` must enumerate ARMS, not a literal tuple that silently omits a new arm."""

    tree = ast.parse(inspect.getsource(merge))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Dict) and node.keys):
            continue
    source = inspect.getsource(merge)
    assert "for arm in ARMS" in source, "by_arm must iterate the derived arm vocabulary"
    assert '"deterministic", "holistic", "merged"' not in source, (
        "a literal arm list in merge.py will under-report any arm added later"
    )


def test_a_focused_source_must_carry_its_lineage():
    """Candidate, spec and verification are each required, and each for its own reason."""

    with pytest.raises(ValueError, match="must name its candidate"):
        FindingSource(arm="focused_agent", spec_id="proof_golf",
                      evidence_artifact_ids=["a"])
    with pytest.raises(ValueError, match="must name the spec"):
        FindingSource(arm="focused_agent", candidate_id="candidate:x",
                      evidence_artifact_ids=["a"])
    with pytest.raises(ValueError, match="verification artifacts"):
        FindingSource(arm="focused_agent", candidate_id="candidate:x",
                      spec_id="proof_golf")
    # All three present is the only accepted shape.
    source = FindingSource(arm="focused_agent", candidate_id="candidate:x",
                           spec_id="proof_golf", evidence_artifact_ids=["a"])
    assert source.spec_id == "proof_golf"


def test_a_holistic_source_is_not_held_to_the_focused_requirements():
    """Widening the validator must not retroactively invalidate the other arms."""

    holistic = FindingSource(arm="generalist", candidate_id="candidate:x")
    assert holistic.evidence_artifact_ids == []
    deterministic = FindingSource(arm="deterministic", opportunity_id="opp:1",
                                  evidence_artifact_ids=["a"])
    assert deterministic.spec_id is None


def _candidate(spec_id=None, requested_change="shorten the proof", change_id="change:a"):
    from src.mathlib_review.schema import CandidateClaim

    return CandidateClaim(
        candidate_id="candidate:abc", source_sha256="0" * 64, work_unit_id="wu:1",
        ordinal=0, episode_id="ep:1", pr_number=7, change_ids=[change_id],
        primary_change_id=change_id, primary_subject="Foo.bar",
        requested_change=requested_change, concern_family="proof-golf",
        concern_label="golf", severity="advisory", claim="the proof is long",
        spec_id=spec_id, issue_kind="proof_simplification",
        evidence_requests=[],
    )


def test_the_arm_is_read_from_the_candidate_not_assumed():
    holistic = merge.finding_from_candidate(
        _candidate(), admission="diagnostic", admission_reason="x"
    )
    assert holistic.arm == "generalist"
    assert holistic.sources[0].arm == "generalist"

    focused = merge.finding_from_candidate(
        _candidate(spec_id="proof_golf"), admission="published", admission_reason="x",
        evidence_tier="verified_compile", evidence_artifact_ids=["artifact:1"],
    )
    assert focused.arm == "focused_agent"
    assert focused.sources[0].spec_id == "proof_golf"


def test_by_arm_counts_every_arm_including_the_new_one():
    # Deliberately different asks at different targets: two findings that agree would fold
    # into one `merged` finding, which is correct behaviour but tests nothing about counting.
    findings = [
        merge.finding_from_candidate(_candidate(), admission="diagnostic",
                                     admission_reason="x"),
        merge.finding_from_candidate(
            _candidate(spec_id="proof_golf", requested_change="use grind here",
                       change_id="change:b"),
            admission="published", admission_reason="x",
            evidence_tier="verified_compile", evidence_artifact_ids=["artifact:1"],
        ),
    ]
    _kept, _conflicts, report = merge.merge_findings(findings)
    assert set(report["by_arm"]) == set(ARMS)
    assert report["by_arm"]["focused_agent"] == 1


def test_every_registered_method_has_an_explicit_concern_and_evidence_tier():
    """The `.get(..., default)` fallbacks must never actually be reached.

    `lexical_rule` is the weakest tier above assertion, so a method that falls through is
    not merely mislabelled — it loses every merge tie, and the loss is invisible.
    """

    method_ids = {item.method_id for item in default_methods()}
    assert method_ids, "expected a non-empty method registry"
    assert method_ids <= set(conditions._CONCERN_BY_METHOD), (
        f"methods with no concern family: "
        f"{sorted(method_ids - set(conditions._CONCERN_BY_METHOD))}"
    )
    assert method_ids <= set(conditions._EVIDENCE_BY_METHOD), (
        f"methods with no evidence tier: "
        f"{sorted(method_ids - set(conditions._EVIDENCE_BY_METHOD))}"
    )


def test_the_two_new_conditions_exist_and_the_baseline_is_untouched():
    assert "focused_only" in conditions.CONDITIONS
    assert "merged_ensemble_v2" in conditions.CONDITIONS
    # The locked baseline keeps its name and therefore its meaning.
    assert "merged_ensemble" in conditions.CONDITIONS


def test_focused_conditions_demand_focused_candidates(tmp_path):
    for condition in ("focused_only", "merged_ensemble_v2"):
        with pytest.raises(ValueError, match="focused-candidates|execution-release"):
            conditions.build_condition(condition, tmp_path / condition)


def test_a_candidate_without_a_spec_cannot_enter_the_focused_condition(tmp_path):
    """Otherwise the focused arm's numbers would quietly include another arm's output.

    Both directions matter: a generalist candidate carries no spec, and a file-scoped one
    carries `file_coherence`, which is a spec in the plumbing sense but not a focused agent.
    """

    from src.mathlib_review.io import jsonl_bytes

    path = tmp_path / "candidates.jsonl"
    path.write_bytes(jsonl_bytes([_candidate()]))
    with pytest.raises(ValueError, match="carries no focused spec_id"):
        conditions.focused_findings(path, None)


def test_a_focused_candidate_with_no_verification_is_dropped_not_downgraded(tmp_path):
    """Dropping loses a finding; downgrading would publish an unverified one as verified."""

    from src.mathlib_review.io import jsonl_bytes

    path = tmp_path / "candidates.jsonl"
    path.write_bytes(jsonl_bytes([_candidate(spec_id="proof_golf")]))
    assert conditions.focused_findings(path, None) == []

    artifacts = tmp_path / "verification.jsonl"
    artifacts.write_text(
        '{"artifact_id": "artifact:1", "work_unit_id": "wu:1", "candidate_ordinal": 0, '
        '"stage": "proposed_edit", "success": true}\n'
    )
    findings = conditions.focused_findings(path, artifacts)
    assert len(findings) == 1
    assert findings[0].evidence_tier == "verified_compile"
    assert findings[0].sources[0].evidence_artifact_ids == ["artifact:1"]


def test_a_failed_compile_does_not_count_as_verification(tmp_path):
    from src.mathlib_review.io import jsonl_bytes

    path = tmp_path / "candidates.jsonl"
    path.write_bytes(jsonl_bytes([_candidate(spec_id="proof_golf")]))
    artifacts = tmp_path / "verification.jsonl"
    artifacts.write_text(
        '{"artifact_id": "artifact:1", "work_unit_id": "wu:1", "candidate_ordinal": 0, '
        '"stage": "proposed_edit", "success": false}\n'
    )
    assert conditions.focused_findings(path, artifacts) == []


def _focused_plan(**overrides):
    from src.mathlib_review.release.contracts import seal_generation_plan
    from src.mathlib_review.agenda.focused_specs import default_specs

    values = dict(
        condition="merged_ensemble_v2",
        release_path="inputs/pr_review_v4/releases/dev-medium-0.3.0",
        release_manifest_sha256="a" * 64,
        expected_work_unit_ids=["wu:1#proof_golf"], expected_pr_numbers=[33098],
        prompt_sha256_by_work_unit={"wu:1#proof_golf": "b" * 64},
        renderer_version="focused-prompt/1",
        focused_candidates_path="results/pr_review_v4/runs/focused-rep1/candidates.jsonl",
        focused_candidates_sha256="c" * 64,
        focused_verification_path="results/pr_review_v4/runs/focused-rep1/verify.jsonl",
        focused_verification_sha256="d" * 64,
        focused_spec_versions=[
            f"{item.spec_id}@{item.spec_version}" for item in default_specs()
        ],
        merge_version="arm-neutral-merge/1", admission_policy="published-only",
        pr_finding_limit=20, model_name="gpt_5.2", repetitions=3,
        scaffold_config_sha256="e" * 64,
    )
    values.update(overrides)
    return seal_generation_plan(**values)


def test_a_focused_generation_plan_binds_its_inputs_and_stays_gold_free():
    """The focused arm is bound like the deterministic one, and the sweep still applies."""

    plan = _focused_plan()
    assert plan.focused_candidates_sha256 == "c" * 64
    assert plan.focused_verification_sha256 == "d" * 64
    assert len(plan.focused_spec_versions) == 4
    # Composite invocation ids survive into the plan's expected set.
    assert plan.expected_work_unit_ids == ["wu:1#proof_golf"]


def test_the_gold_sweep_still_covers_the_new_focused_fields():
    """Fields added to the plan must be swept too, not merely added."""

    from src.mathlib_review.release.contracts import GoldLeakError

    with pytest.raises(GoldLeakError):
        _focused_plan(
            focused_candidates_path="results/pr_review_v4/gold/candidates.jsonl"
        )


def test_single_pr_template_operators_are_not_scheduled():
    """Three operators only ever fired on PR 33098, the PR they were written from.

    Measured on medium: `canonical_api_search.v1`, `wrapper_composition.v1` and
    `naming_contrast.v1` produced every one of their opportunities on 33098 and none
    anywhere else — `wrapper_composition` requires `coveringNumber` AND `packingNumber` AND
    `IsCover` AND `maximalSeparatedSet` in the goal, and `naming_contrast` hardcodes
    `Set.encard`. They entered the merge at `verified_compile`, the top tier, so they won
    every tie and every per-PR budget cut they took part in, and made the arm look general
    when three of its seven operators were memorised.

    `naming_norm.v1` is the counter-example that must stay scheduled: it mines the subject
    from the conclusion and fires on 33098 *and* 33145.
    """

    from src.mathlib_review.opportunities.method_registry import (
        RETIRED_SINGLE_PR_METHODS,
        all_methods,
        default_methods,
    )

    scheduled = {item.method_id for item in default_methods()}
    assert scheduled.isdisjoint(RETIRED_SINGLE_PR_METHODS), (
        f"retired single-PR operators are still scheduled: "
        f"{sorted(scheduled & set(RETIRED_SINGLE_PR_METHODS))}"
    )
    assert "naming_norm.v1" in scheduled, "the general naming operator must survive"
    # Still constructible, so frozen runs scheduled against `/3` remain replayable.
    assert set(RETIRED_SINGLE_PR_METHODS) <= {item.method_id for item in all_methods()}


def test_retirement_is_in_the_registry_not_a_caller_flag():
    """A flag that every call site must remember is one that some call site will forget.

    `SUBSUMED_METHODS` named `naming_contrast.v1` for months while `build_condition`
    defaulted `exclude_methods` to empty, so the exclusion never actually applied.
    """

    from src.mathlib_review.opportunities.method_registry import default_methods

    assert conditions.SUBSUMED_METHODS == ()
    # The guarantee holds with no exclusions passed at all.
    assert {item.method_id for item in default_methods()} == {
        "baseline_failure.v1", "naming_norm.v1", "lint_norm.v1", "repository_policy.v1",
    }


def test_the_frozen_v3_registry_still_loads():
    """Retiring methods must not strand the runs that were scheduled against them."""

    from src.mathlib_review.opportunities.method_registry import (
        DEFAULT_REGISTRY,
        LEGACY_REGISTRY_V3,
        load_registry,
    )

    if not LEGACY_REGISTRY_V3.is_file():
        pytest.skip("the /3 registry is not present")
    legacy = load_registry(LEGACY_REGISTRY_V3)
    assert legacy, "the frozen registry must still validate and load"
    assert DEFAULT_REGISTRY != LEGACY_REGISTRY_V3, (
        "the new registry must be a new file; the old one is bound into frozen run plans"
    )


def test_a_file_scoped_candidate_is_not_a_focused_candidate(tmp_path):
    """`file_coherence` is a spec id, but the file arm is not a focused agent."""

    from src.mathlib_review.io import jsonl_bytes
    from src.mathlib_review.schema import FILE_COHERENCE_SPEC

    path = tmp_path / "candidates.jsonl"
    path.write_bytes(jsonl_bytes([_candidate(spec_id=FILE_COHERENCE_SPEC)]))
    with pytest.raises(ValueError, match="not a focused candidate"):
        conditions.focused_findings(path, None)


def test_the_two_generalists_are_separate_arms():
    """Control and component must be countable apart, which means separate arm values."""

    from src.mathlib_review.schema import FILE_COHERENCE_SPEC

    control = merge.finding_from_candidate(
        _candidate(), admission="published", admission_reason="x"
    )
    component = merge.finding_from_candidate(
        _candidate(spec_id=FILE_COHERENCE_SPEC), admission="published",
        admission_reason="x",
    )
    assert control.arm == "generalist"
    assert component.arm == "file_generalist"
    assert control.arm != component.arm
    assert "file_generalist" in ARMS


def test_the_file_arm_needs_no_verification_artifacts():
    """It is a vantage point, not a compile; demanding evidence would make it unpublishable."""

    source = FindingSource(arm="file_generalist", candidate_id="candidate:x")
    assert source.evidence_artifact_ids == []
    with pytest.raises(ValueError, match="must name its candidate"):
        FindingSource(arm="file_generalist")
