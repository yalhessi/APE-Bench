"""Regression gates for oracle-opportunity adjudication."""

import json
from pathlib import Path

from src.mathlib_review.opportunities.oracle import (
    COVER_LE_PACK,
    DEFAULT_OUT,
    build_artifacts,
    ingest_run,
)
from src.mathlib_review.schema import (
    ChangeGraph,
    OpportunityAdjudication,
    OracleOpportunity,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)
from src.mathlib_review.review.task_adapter import build_opportunity_task_data


PILOT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")


def _load(root, relative, cls):
    return [
        cls.model_validate_json(line)
        for line in (root / relative).read_text().splitlines()
        if line
    ]


def _artifacts():
    return build_artifacts(
        _load(PILOT, "derived/work_units.jsonl", ReviewWorkUnit),
        _load(PILOT, "derived/change_graphs.jsonl", ChangeGraph),
        _load(PILOT, "input/episodes.jsonl", ReviewEpisodeInput),
    )


def test_oracle_probe_builds_complete_intervention_and_matched_control_calls():
    units, prompts, opportunities = _artifacts()
    assert len(units) == len(prompts) == 2
    assert len(opportunities) == 12
    assert {item.pr_number for item in units} == {33098, 33438}
    assert {item.selection_provenance for item in opportunities} == {
        "oracle_gold_targeted",
        "matched_control",
    }
    assert all(item.renderer_version == "oracle-opportunity-adjudication/1" for item in units)
    assert all(not item.omitted_change_ids for item in prompts)
    assert all(prompt.user_prompt.count("## Opportunity `") == 6 for prompt in prompts)
    assert all("submit_opportunity_adjudications" in prompt.user_prompt for prompt in prompts)
    assert all("submit_candidates exactly once" not in prompt.user_prompt for prompt in prompts)
    assert all("oracle_gold_targeted" not in prompt.user_prompt for prompt in prompts)


def test_intervention_unit_expands_scope_to_covering_number_primary_target():
    units, prompts, opportunities = _artifacts()
    unit = next(item for item in units if item.pr_number == 33098)
    prompt = next(item for item in prompts if item.work_unit_id == unit.work_unit_id)
    composition = next(item for item in opportunities if item.method == "intra_pr_composition")
    assert COVER_LE_PACK in unit.change_ids
    assert composition.primary_change_id == COVER_LE_PACK
    assert "Metric.coveringNumber_le_packingNumber" in prompt.user_prompt


def test_opportunity_evidence_is_review_time_scoped_and_comment_free():
    units, _prompts, opportunities = _artifacts()
    episodes = {
        item.episode_id: item
        for item in _load(PILOT, "input/episodes.jsonl", ReviewEpisodeInput)
    }
    unit_by_id = {item.work_unit_id: item for item in units}
    for opportunity in opportunities:
        episode = episodes[unit_by_id[opportunity.work_unit_id].episode_id]
        for evidence in opportunity.evidence:
            assert evidence.snapshot_sha in {episode.base_sha, episode.reviewed_head_sha}
            assert "event:" not in evidence.source_ref
            assert "comment" not in evidence.source_ref
            assert "outcome" not in evidence.source_ref


def test_opportunity_task_adapter_exposes_exact_terminal_contract():
    units = _load(DEFAULT_OUT, "derived/work_units.jsonl", ReviewWorkUnit)
    prompts = _load(DEFAULT_OUT, "derived/rendered_prompts.jsonl", RenderedPrompt)
    opportunities = _load(DEFAULT_OUT, "derived/oracle_opportunities.jsonl", OracleOpportunity)
    episodes = {
        item.episode_id: item
        for item in _load(DEFAULT_OUT, "input/episodes.jsonl", ReviewEpisodeInput)
    }
    unit = units[0]
    prompt = next(item for item in prompts if item.work_unit_id == unit.work_unit_id)
    rows = [item for item in opportunities if item.work_unit_id == unit.work_unit_id]
    data = build_opportunity_task_data(unit, episodes[unit.episode_id], prompt, rows)
    assert data.task_type == "lean_pr_review_v4_opportunity_adjudication"
    assert data.opportunity_ids == [item.opportunity_id for item in rows]
    assert set(data.change_ids_by_opportunity[rows[0].opportunity_id]) <= set(unit.change_ids)


def test_ingest_preserves_rejections_and_links_request_candidate(tmp_path):
    units = _load(DEFAULT_OUT, "derived/work_units.jsonl", ReviewWorkUnit)
    opportunities = _load(DEFAULT_OUT, "derived/oracle_opportunities.jsonl", OracleOpportunity)
    opportunities_by_unit = {}
    for item in opportunities:
        opportunities_by_unit.setdefault(item.work_unit_id, []).append(item)
    responses = []
    for unit in units:
        decisions = []
        candidates = []
        for index, opportunity in enumerate(opportunities_by_unit[unit.work_unit_id]):
            request = unit.pr_number == 33098 and index == 0
            decision = {
                "opportunity_id": opportunity.opportunity_id,
                "disposition": "request" if request else "no_request",
                "validity": "valid" if request else "invalid",
                "norm_strength": "canonical" if request else "unsupported",
                "review_worthiness": "advisory" if request else "not_worth_mentioning",
                "evidence_ids": [opportunity.evidence[0].evidence_id],
                "rationale": "The supplied evidence supports this disposition.",
                "candidate_ordinal": 0 if request else None,
            }
            decisions.append(decision)
            if request:
                change_id = opportunity.primary_change_id
                candidates.append({
                    "primary_change_id": change_id,
                    "primary_entity_id": unit.entity_ids_by_change[change_id][0],
                    "primary_subject": unit.primary_subjects_by_change[change_id],
                    "change_ids": [change_id],
                    "concern_family": "proof-golf",
                    "concern_label": "proof compression",
                    "severity": "advisory",
                    "claim": "Metric.maximalSeparatedSet_subset contains a redundant case split.",
                    "requested_change": "Simplify Metric.maximalSeparatedSet_subset to remove the redundant case split.",
                })
        responses.append({
            "work_unit_id": unit.work_unit_id,
            "success": True,
            "response": {"adjudications": decisions, "candidates": candidates},
        })
    response_path = tmp_path / "candidate_responses.jsonl"
    response_path.write_text("".join(json.dumps(item) + "\n" for item in responses))
    report = ingest_run(DEFAULT_OUT, response_path, tmp_path / "processed")
    assert report["counts"] == {"opportunities": 12, "adjudications": 12, "candidates": 1}
    assert report["dispositions_by_arm"]["matched_control"] == {"no_request": 6}
    adjudications = _load(
        tmp_path / "processed", "adjudications.jsonl", OpportunityAdjudication
    )
    assert sum(item.candidate_id is not None for item in adjudications) == 1
