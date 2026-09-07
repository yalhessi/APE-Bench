"""Regression gates for the cheap manual inventory-agenda probe."""

import json
from pathlib import Path

import pytest

from src.mathlib_review.opportunities.agenda_probe import (
    PASS_SPECS,
    SOURCE_WORK_UNIT_IDS,
    build_probe_artifacts,
    compare_reports,
    deduplicate_probe_candidates,
)
from src.mathlib_review.review.candidates import candidates_from_response
from src.mathlib_review.agenda.render_prompts import FACET_CHECKLIST
from src.mathlib_review.schema import (
    CandidateClaim,
    ChangeGraph,
    RenderedPrompt,
    ReviewWorkUnit,
)


PILOT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
RUNS = Path("results/pr_review_v4/runs")


def _load(relative, cls):
    path = PILOT / relative
    return [cls.model_validate_json(line) for line in path.read_text().splitlines() if line]


def _artifacts():
    return build_probe_artifacts(
        _load("derived/work_units.jsonl", ReviewWorkUnit),
        _load("derived/rendered_prompts.jsonl", RenderedPrompt),
        _load("derived/change_graphs.jsonl", ChangeGraph),
    )


def test_probe_builds_three_frozen_passes_for_intervention_and_control():
    units, prompts, tasks = _artifacts()
    assert len(units) == len(prompts) == len(tasks) == 6
    assert len({item.work_unit_id for item in units}) == 6
    assert {item.pass_id for item in tasks} == set(PASS_SPECS)
    assert {item.source_work_unit_id for item in tasks} == set(SOURCE_WORK_UNIT_IDS)
    assert all(item.renderer_version == "manual-agenda-probe/1" for item in units)
    assert all(not item.omitted_change_ids for item in prompts)
    assert all(FACET_CHECKLIST not in item.user_prompt for item in prompts)
    assert all("# Manual inventory-agenda probe" in item.user_prompt for item in prompts)
    task_by_probe = {item.probe_work_unit_id: item for item in tasks}
    unit_by_probe = {item.work_unit_id: item for item in units}
    source_units = {
        item.work_unit_id: item for item in _load("derived/work_units.jsonl", ReviewWorkUnit)
    }
    for prompt in prompts:
        task = task_by_probe[prompt.work_unit_id]
        unit = unit_by_probe[prompt.work_unit_id]
        source = source_units[task.source_work_unit_id]
        assert unit.change_ids == source.change_ids
        assert f"Pass ID: `{task.pass_id}`" in prompt.user_prompt
        assert set(prompt.included_change_ids) == set(source.change_ids)
        assert prompt.user_prompt.count("### Assigned pass for this target") == len(
            source.change_ids
        )


def test_probe_prompt_generation_is_deterministic():
    first = _artifacts()
    second = _artifacts()
    assert [item.model_dump() for item in first[0]] == [item.model_dump() for item in second[0]]
    assert [item.model_dump() for item in first[1]] == [item.model_dump() for item in second[1]]
    assert [item.model_dump() for item in first[2]] == [item.model_dump() for item in second[2]]


def test_probe_candidate_merge_removes_exact_cross_pass_duplicates():
    units, _prompts, tasks = _artifacts()
    intervention_tasks = [
        item for item in tasks if item.source_work_unit_id == SOURCE_WORK_UNIT_IDS[0]
    ]
    unit_by_id = {item.work_unit_id: item for item in units}
    candidates = []
    for task in intervention_tasks[:2]:
        unit = unit_by_id[task.probe_work_unit_id]
        change_id = unit.change_ids[0]
        subject = unit.primary_subjects_by_change[change_id]
        response = {"candidates": [{
            "primary_change_id": change_id,
            "primary_entity_id": unit.entity_ids_by_change[change_id][0],
            "primary_subject": subject,
            "change_ids": [change_id],
            "concern_family": "naming",
            "concern_label": "name consistency",
            "severity": "advisory",
            "claim": f"{subject} uses a name inconsistent with its return type.",
            "requested_change": f"Rename {subject} to follow the sibling convention.",
        }]}
        candidates.extend(candidates_from_response(unit, response))
    assert candidates[0].candidate_id != candidates[1].candidate_id
    merged, report = deduplicate_probe_candidates(candidates)
    assert len(merged) == 1
    assert report["exact_duplicates_removed"] == 1
    assert len(report["clusters"]) == 1


def test_probe_comparison_reconstructs_existing_baseline_union():
    names = [
        "dev-pilot-0.9.0-stable-smoke3",
        "dev-pilot-0.9.0-stable-smoke3-rep2",
        "dev-pilot-0.9.0-stable-smoke3-rep3",
    ]
    baselines = [json.loads((RUNS / name / "evaluation.json").read_text()) for name in names]
    candidate_sets = [
        [
            CandidateClaim.model_validate_json(line)
            for line in (RUNS / name / "candidates.jsonl").read_text().splitlines()
            if line
        ]
        for name in names
    ]
    report = compare_reports(baselines[0], baselines, candidate_sets[0], candidate_sets)
    assert report["baseline_mean_issue_recall"] == pytest.approx(1 / 3)
    assert report["baseline_union_issue_recall"] == pytest.approx(4 / 6)
    assert report["baseline_stable_issue_recall"] == 0
    assert len(report["baseline_raw_control_candidates_per_rep"]) == 3
    assert report["screen_verdict"] == "ambiguous_repeat_once"
