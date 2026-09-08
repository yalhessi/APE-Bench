"""Regression gates for Phase 8 PR-level synthesis."""

import asyncio
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from ape.tasks.lean_tasks.formal_math.review.candidates import (
    LeanPRReviewV4CandidateTask,
)

from src.mathlib_review.schema import (
    CandidateClaim,
    CandidateOpportunityLink,
    PRRelation,
    SemanticMatch,
    SynthesisAnchor,
    SynthesizedFinding,
    RenderedPrompt,
    ResidualReviewPass,
    ReviewWorkUnit,
)
from src.mathlib_review.legacy_pipeline.phase8_residual import build_release, ingest_run
from src.mathlib_review.opportunities.synthesis import (
    build_gate_artifacts,
    project_semantic_matches,
    synthesize_findings,
)


def _candidate(identifier, change_id, subject, family="naming"):
    return CandidateClaim(
        candidate_id=f"candidate:{identifier}",
        work_unit_id=f"wu:{identifier}",
        episode_id="episode:1",
        pr_number=1,
        change_ids=[change_id],
        primary_change_id=change_id,
        primary_subject=subject,
        requested_change=f"Apply the shared transformation to {subject}.",
        concern_family=family,
        concern_label="shared transformation",
        severity="advisory",
        claim=f"{subject} uses the old form.",
        evidence_requests=[],
        model_confidence=0.8,
        source_sha256=f"candidate-hash:{identifier}",
    )


def _link(candidate, opportunity, symbols=("NewForm",), context=()):
    return CandidateOpportunityLink(
        link_id=f"link:{candidate.candidate_id}",
        candidate_id=candidate.candidate_id,
        opportunity_id=f"opportunity:{opportunity}",
        investigation_id=f"investigation:{opportunity}",
        pr_number=candidate.pr_number,
        method_id="naming_contrast.v1",
        primary_change_id=candidate.primary_change_id,
        context_change_ids=list(context),
        relation_ids=[],
        action_kind="rename",
        action_symbols=list(symbols),
        evidence_artifact_ids=[f"evidence:{opportunity}"],
        source_sha256=f"link-hash:{opportunity}",
    )


def _relation(left, right):
    return PRRelation(
        relation_id=f"relation:{left}:{right}",
        episode_id="episode:1",
        pr_number=1,
        relation_kind="name_family",
        source_change_id=left,
        related_change_ids=[right],
        confidence="high",
        producer="deterministic",
        source_sha256=f"relation-hash:{left}:{right}",
    )


def _match(candidate, obligation, issue=True, resolution=False):
    return SemanticMatch(
        match_id=f"match:{candidate.candidate_id}:{obligation}",
        candidate_id=candidate.candidate_id,
        obligation_id=f"obligation:{obligation}",
        issue_match=issue,
        resolution_match=resolution,
        reason="Synthetic regression fixture.",
        judge_model="test",
        judge_version="test",
        candidate_source_sha256=candidate.source_sha256,
        obligation_source_sha256=f"obligation-hash:{obligation}",
        source_sha256=f"match-hash:{candidate.candidate_id}:{obligation}",
    )


def test_real_two_pr_gate_retains_matches_and_control_abstention():
    artifacts, report = build_gate_artifacts()
    assert report["complete"] is True
    assert report["counts"] == {
        "candidates": 3,
        "accepted_candidates": 3,
        "links": 3,
        "findings": 3,
        "synthesis_decisions": 3,
        "match_projections": 5,
        "residual_passes": 2,
    }
    assert report["gates"] == {
        "supported_issue_matches_retained": True,
        "exact_duplicate_findings": True,
        "control_findings": 0,
        "all_findings_have_complete_lineage": True,
        "residual_pass_scheduled_for_both_prs": True,
    }
    assert report["issue_matched_obligations_before"] == report[
        "issue_matched_obligations_after"
    ]
    assert len(artifacts["residual_review_passes"]) == 2


def test_duplicate_stochastic_variants_collapse_without_losing_lineage():
    first = _candidate("one", "change:a", "Namespace.a")
    second = _candidate("two", "change:a", "Namespace.a")
    links = [_link(first, "one"), _link(second, "two")]
    findings, decisions = synthesize_findings(
        [first, second], links, {"opportunity:one", "opportunity:two"}
    )
    assert len(findings) == 1
    assert findings[0].source_candidate_ids == ["candidate:one", "candidate:two"]
    assert {item.action for item in decisions} == {"group", "suppress_duplicate"}
    assert all(item.finding_id == findings[0].finding_id for item in decisions)


def test_same_action_siblings_group_only_over_validated_relation():
    first = _candidate("one", "change:a", "Namespace.a")
    second = _candidate("two", "change:b", "Namespace.b")
    links = [_link(first, "one"), _link(second, "two")]
    accepted = {"opportunity:one", "opportunity:two"}
    separate, _ = synthesize_findings([first, second], links, accepted)
    assert len(separate) == 2

    grouped, decisions = synthesize_findings(
        [first, second], links, accepted, [_relation("change:a", "change:b")]
    )
    assert len(grouped) == 1
    assert grouped[0].change_ids == ["change:a", "change:b"]
    assert {item.change_id for item in grouped[0].anchors} == {"change:a", "change:b"}
    assert any(item.action == "group" for item in decisions)


def test_equal_conflict_defers_and_strict_evidence_dominance_selects_one():
    first = _candidate("one", "change:a", "Namespace.a")
    second = _candidate("two", "change:a", "Namespace.a")
    links = [
        _link(first, "one", symbols=("AlternativeA",)),
        _link(second, "two", symbols=("AlternativeB",)),
    ]
    accepted = {"opportunity:one", "opportunity:two"}
    findings, decisions = synthesize_findings([first, second], links, accepted)
    assert findings == []
    assert [item.action for item in decisions] == ["defer_conflict"]

    findings, decisions = synthesize_findings(
        [first, second], links, accepted,
        support_scores={"opportunity:one": 10.0, "opportunity:two": 5.0},
    )
    assert len(findings) == 1
    assert findings[0].source_candidate_ids == ["candidate:one"]
    assert {item.action for item in decisions} == {"retain", "suppress_dominated"}


def test_grouped_finding_projects_every_atomic_source_match():
    first = _candidate("one", "change:a", "Namespace.a")
    second = _candidate("two", "change:b", "Namespace.b")
    links = [_link(first, "one"), _link(second, "two")]
    findings, _ = synthesize_findings(
        [first, second], links, {"opportunity:one", "opportunity:two"},
        [_relation("change:a", "change:b")],
    )
    projections = project_semantic_matches(
        findings, [_match(first, "one", resolution=True), _match(second, "two")]
    )
    assert {item.obligation_id for item in projections} == {
        "obligation:one", "obligation:two"
    }
    assert all(item.issue_match for item in projections)
    assert sum(item.resolution_match for item in projections) == 1


def test_real_wrapper_context_is_not_promoted_to_issue_anchor():
    artifacts, _report = build_gate_artifacts()
    wrapper = next(
        item for item in artifacts["synthesized_findings"]
        if "intra_pr_composition" in item.method_ids
    )
    assert wrapper.change_ids == [
        "change:45cf88bca684cd3813871f4da143b9c827418cf9320465b788f860efac74900a"
    ]
    assert set(wrapper.context_change_ids) == {
        "change:c5c9da88f1d990a90cb9913c331dedd39539e7c571bf7a0c98dce91de28c648f",
        "change:c7ef58137fa4b7b4ee0f8b13686be4a5afcefe2e8e8c434092e3c25c8510acc0",
    }


def test_synthesized_finding_rejects_context_anchor_conflation():
    with pytest.raises(ValidationError, match="must be disjoint"):
        SynthesizedFinding(
            finding_id="finding:1",
            pr_number=1,
            source_candidate_ids=["candidate:1"],
            source_opportunity_ids=["opportunity:1"],
            change_ids=["change:1"],
            context_change_ids=["change:1"],
            anchors=[SynthesisAnchor(
                change_id="change:1",
                source_candidate_ids=["candidate:1"],
                source_opportunity_ids=["opportunity:1"],
            )],
            method_ids=["method:1"],
            action_key="action:1",
            concern_family="style",
            severity="advisory",
            claim="Supported claim.",
            requested_change="Apply the supported change.",
            evidence_artifact_ids=["evidence:1"],
            rank_key="00000000:action:1",
            source_sha256="hash",
        )


def test_residual_release_is_compact_complete_and_gold_free():
    release = Path("inputs/pr_review_v4/treatments/phase8-residual-smoke-0.1.1")
    manifest = build_release(out=release)
    units = [
        ReviewWorkUnit.model_validate_json(line)
        for line in (release / "derived/work_units.jsonl").read_text().splitlines()
        if line
    ]
    prompts = [
        RenderedPrompt.model_validate_json(line)
        for line in (release / "derived/rendered_prompts.jsonl").read_text().splitlines()
        if line
    ]
    assert manifest.pr_numbers == [33098, 33438]
    assert {item.pr_number: len(item.change_ids) for item in units} == {33098: 26, 33438: 2}
    assert all(not item.omitted_change_ids for item in prompts)
    assert all(
        item.submission_verification_policy == "verify_checkable_edits"
        for item in prompts
    )
    assert max(item.estimated_tokens for item in prompts) < 4000
    rendered = "\n".join(item.user_prompt.lower() for item in prompts)
    for forbidden in (
        "maintainer comment", "gold obligation", "oracle_gold", "matched_control",
        "accepted later", "post-review",
    ):
        assert forbidden not in rendered
    intervention = next(item for item in prompts if "# pr #33098:" in item.user_prompt.lower())
    assert intervention.user_prompt.count("finding=`synthesized-finding:") == 3
    assert "lean_verify` is only for standalone scratch code" in rendered
    assert "lean_verify_edit(path=...)" in rendered


def test_residual_ingest_closes_every_pr_even_when_both_abstain(tmp_path):
    release = Path("inputs/pr_review_v4/treatments/phase8-residual-smoke-0.1.1")
    units = [
        ReviewWorkUnit.model_validate_json(line)
        for line in (release / "derived/work_units.jsonl").read_text().splitlines()
        if line
    ]
    responses = tmp_path / "candidate_responses.jsonl"
    responses.write_text("".join(json.dumps({
        "work_unit_id": unit.work_unit_id,
        "response": {"candidates": []},
        "success": True,
        "error": None,
    }) + "\n" for unit in units))
    report = ingest_run(release, responses, tmp_path / "ingested")
    assert report == {
        "schema_version": "phase8-residual-ingest-report1",
        "complete": True,
        "counts": {
            "pr_units": 2,
            "terminal_passes": 2,
            "candidates": 0,
            "verification_artifacts": 0,
        },
        "candidates_by_pr": {"33098": 0, "33438": 0},
    }
    terminal = [
        ResidualReviewPass.model_validate_json(line)
        for line in (tmp_path / "ingested/residual_review_passes.jsonl").read_text().splitlines()
        if line
    ]
    assert all(item.status == "completed" and item.terminal_reason for item in terminal)


def test_residual_ingest_rejects_checkable_candidate_without_verification(tmp_path):
    release = Path("inputs/pr_review_v4/treatments/phase8-residual-smoke-0.1.1")
    units = [
        ReviewWorkUnit.model_validate_json(line)
        for line in (release / "derived/work_units.jsonl").read_text().splitlines()
        if line
    ]
    unit = units[0]
    change_id = unit.change_ids[0]
    subject = unit.primary_subjects_by_change[change_id]
    responses = tmp_path / "candidate_responses.jsonl"
    rows = []
    for candidate_unit in units:
        candidates = []
        if candidate_unit.work_unit_id == unit.work_unit_id:
            candidates = [{
                "primary_change_id": change_id,
                "primary_entity_id": unit.entity_ids_by_change[change_id][0],
                "primary_subject": subject,
                "change_ids": [change_id],
                "concern_family": "correctness",
                "concern_label": "unverified compile concern",
                "severity": "blocking",
                "claim": f"{subject} may fail.",
                "requested_change": f"Repair {subject}.",
            }]
        rows.append({
            "work_unit_id": candidate_unit.work_unit_id,
            "response": {"candidates": candidates, "verification_artifacts": []},
            "success": True,
            "error": None,
        })
    responses.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(ValueError, match="no structured proposed edit"):
        ingest_run(release, responses, tmp_path / "rejected")


def test_strict_candidate_verification_uses_reviewed_file_and_edit(monkeypatch, tmp_path):
    reviewed = tmp_path / "Mathlib/Test.lean"
    reviewed.parent.mkdir(parents=True)
    reviewed.write_text("theorem demo : True := by\n  trivial\n")
    compiled = []

    class FakeLeanVerify:
        def __init__(self, **_kwargs):
            pass

        async def execute(self, code, **_kwargs):
            compiled.append(code)
            return {"success": "BROKEN" not in code, "errors": [{"data": "broken edit"}]}

    monkeypatch.setattr(
        "ape.toolkits.execute.lean.tools.LeanVerifyToolsProvider", FakeLeanVerify
    )
    task = LeanPRReviewV4CandidateTask.__new__(LeanPRReviewV4CandidateTask)
    task.data = SimpleNamespace(
        submission_verification_policy="verify_checkable_edits",
        work_unit_id="wu:test",
        snapshot_head_sha="reviewed-head",
    )
    task.target_workspace = SimpleNamespace(path=tmp_path)
    task.config = None
    task.logger = logging.getLogger("candidate-verification-test")
    candidate = {
        "concern_family": "correctness",
        "proposed_edit": {
            "path": "Mathlib/Test.lean",
            "declaration_name": None,
            "new_declaration": None,
            "line_start": 2,
            "line_end": 2,
            "replacement": "  exact True.intro",
        },
    }
    artifacts, error = asyncio.run(task._verify_candidate_submission(0, candidate))
    assert error is None
    assert [item["stage"] for item in artifacts] == ["baseline", "proposed_edit"]
    assert all(item["success"] for item in artifacts)
    assert "trivial" in compiled[0]
    assert "exact True.intro" in compiled[1]

    candidate["proposed_edit"]["replacement"] = "  BROKEN"
    artifacts, error = asyncio.run(task._verify_candidate_submission(0, candidate))
    assert [item["stage"] for item in artifacts] == ["baseline"]
    assert "proposed edit failed" in error
