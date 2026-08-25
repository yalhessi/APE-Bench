"""Regression gates for the executable v4 evidence pipeline."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ape.tasks.lean_tasks.formal_math.pr_review_v4.candidates import (
    CandidateSubmission,
    normalize_proposed_edit_path,
)
from src.datasets.pr_review_v4.candidates import (
    candidates_from_response, discover_deterministic_candidates, ingest_responses,
)
from src.datasets.pr_review_v4.evidence import collect_candidate
from src.datasets.pr_review_v4.evaluate import evaluate_funnel
from src.datasets.pr_review_v4.io import sha256_bytes
from src.datasets.pr_review_v4.render_prompts import render_all, render_precedent_block
from src.datasets.pr_review_v4.run_contract import create_run_plan, seal_run
from src.datasets.pr_review_v4.retrieval import (
    build_prompt_precedents, build_retrieval_cutoffs, load_reviewer_roster,
    validate_precedents,
)
from src.datasets.pr_review_v4.semantic_judge import (
    JUDGE_VERSION, _match, build_pairs, eligible_obligations, parse_verdict, semantic_report,
)
from src.datasets.pr_review_v4.schema import (
    ArtifactRef, ChangeGraph, EvidenceRequest, PromptPrecedent,
    ReviewEpisodeBoundary, RetrievalCutoff, ReviewRoundSegment, InterventionView, JudgmentNode, PilotCase,
    RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit, SourceEvent,
)
from src.datasets.pr_review_v4.select import select_findings
from src.datasets.pr_review_v4.task_adapter import build_candidate_task_data
from src.datasets.pr_review_v4.validate import validate_release
from src.datasets.pr_review_v4.work_units import build_work_units, validate_work_unit_coverage


PILOT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
RETRIEVAL_PILOT = Path("inputs/pr_review_v4/releases/dev-pilot-0.8.11")


def _load(name, cls):
    return [cls.model_validate_json(line) for line in (PILOT / name).read_text().splitlines() if line]


def _load_from(release, name, cls):
    return [cls.model_validate_json(line) for line in (release / name).read_text().splitlines() if line]


def _grounding(unit, change_id=None, requested_change=None):
    change_id = change_id or unit.change_ids[0]
    subject = unit.primary_subjects_by_change[change_id]
    entities = unit.entity_ids_by_change[change_id]
    return {
        "primary_change_id": change_id,
        "primary_entity_id": entities[0] if entities else None,
        "primary_subject": subject,
        "requested_change": requested_change or f"Revise {subject}.",
    }


def _candidate(unit, label="duplication", query="ExistingFoo"):
    payload = {**_grounding(unit, requested_change=f"Replace {unit.primary_subjects_by_change[unit.change_ids[0]]} with {query}."),
               "work_unit_id": unit.work_unit_id, "change_ids": unit.change_ids,
               "concern_family": label, "concern_label": f"possible {label}",
               "severity": "advisory",
               "claim": f"{unit.primary_subjects_by_change[unit.change_ids[0]]} duplicates {query}."}
    return candidates_from_response(unit, {"candidates": [payload]})[0]


def test_pilot_release_validates_and_has_explicit_mixed_controls():
    report = validate_release(PILOT)
    assert report["prs"] == 9
    cases = [json.loads(line) for line in (PILOT / "gold/pilot_cases.jsonl").read_text().splitlines()]
    assert sum(item["case_kind"] == "intervention" for item in cases) == 6
    assert sum(item["case_kind"] == "control" for item in cases) == 3
    assert all(item["control_semantics"] for item in cases if item["case_kind"] == "control")


def test_semantic_judge_can_scope_one_obligation_on_a_shared_change_target():
    judgments = _load("gold/judgments.jsonl", JudgmentNode)
    views = _load("gold/intervention_views.jsonl", InterventionView)
    naming_id = "obligation:45433fc367bdd15dc606eaabeadaa16ad98077afec83ca662fe39bcf938632ad"
    scoped = eligible_obligations(judgments, views, [naming_id])
    assert [obligation.obligation_id for _judgment, obligation in scoped] == [naming_id]


def test_semantic_judge_recovers_explicit_booleans_from_truncated_reason():
    verdict = parse_verdict(
        '{"issue_match": true, "resolution_match": false, "reason": "truncated'
    )
    assert (verdict.issue_match, verdict.resolution_match) == (True, False)
    assert verdict.reason.startswith("judge_partial_json:")
    # Salvaged, not parsed — and above all not scored as an error.
    assert verdict.status == "salvaged"


def test_work_units_cover_once_and_renderer_is_lossless_and_reusable():
    graphs = _load("derived/change_graphs.jsonl", ChangeGraph)
    episodes = _load("input/episodes.jsonl", ReviewEpisodeInput)
    units = build_work_units(graphs)
    validate_work_unit_coverage(graphs, units)
    precedents = []
    prompts = render_all(units, episodes, graphs, precedents)
    stored = _load("derived/rendered_prompts.jsonl", type(prompts[0]))
    assert [item.prompt_sha256 for item in prompts] == [item.prompt_sha256 for item in stored]
    assert all(not item.omitted_change_ids for item in prompts)
    assert all("# Review contract" in item.user_prompt for item in prompts)
    assert all("submit_candidates" in item.user_prompt for item in prompts)
    assert all("requested_change" in item.user_prompt for item in prompts)
    assert all("do not submit evidence requests" in item.user_prompt for item in prompts)
    assert all(item.user_prompt.count("Maintainer ask checklist for this target") ==
               len(item.included_change_ids) for item in prompts)
    assert all("Synthetic maintainer-request exemplars" not in item.user_prompt for item in prompts)
    assert all("Temporally prior maintainer asks" not in item.user_prompt for item in prompts)
    assert all(item.renderer_version == "candidate-prompt/11" for item in prompts)
    assert {cid for unit in units for cid in unit.change_ids} == {
        target.change_id for graph in graphs for target in graph.targets
    }
    task_data = build_candidate_task_data(units[0], {e.episode_id: e for e in episodes}[units[0].episode_id], prompts[0])
    assert task_data.rendered_user_prompt == prompts[0].user_prompt
    assert task_data.rendered_prompt_sha256 == prompts[0].prompt_sha256
    properties = CandidateSubmission.model_json_schema()["properties"]
    assert {"primary_change_id", "primary_entity_id", "primary_subject", "requested_change"} <= properties.keys()
    assert "evidence_requests" not in properties


def test_0811_diff_is_only_the_temporal_retrieval_treatment():
    baseline = Path("inputs/pr_review_v4/releases/dev-pilot-0.8.9")
    for relative in (
        "source/events.jsonl", "input/episodes.jsonl", "derived/change_graphs.jsonl",
        "gold/judgments.jsonl", "gold/intervention_views.jsonl", "gold/pilot_cases.jsonl",
    ):
        assert (RETRIEVAL_PILOT / relative).read_bytes() == (baseline / relative).read_bytes()
    old_units = [ReviewWorkUnit.model_validate_json(line) for line in
                 (baseline / "derived/work_units.jsonl").read_text().splitlines() if line]
    new_units = _load_from(RETRIEVAL_PILOT, "derived/work_units.jsonl", ReviewWorkUnit)
    assert [item.change_ids for item in new_units] == [item.change_ids for item in old_units]
    assert [item.entity_ids_by_change for item in new_units] == [item.entity_ids_by_change
                                                                 for item in old_units]
    old_prompts = [json.loads(line) for line in
                   (baseline / "derived/rendered_prompts.jsonl").read_text().splitlines() if line]
    new_prompts = [json.loads(line) for line in
                   (RETRIEVAL_PILOT / "derived/rendered_prompts.jsonl").read_text().splitlines() if line]
    precedents = _load_from(RETRIEVAL_PILOT, "derived/prompt_precedents.jsonl", PromptPrecedent)
    by_unit = {}
    for precedent in precedents:
        by_unit.setdefault(precedent.work_unit_id, []).append(precedent)
    assert all(new["system_prompt"] == old["system_prompt"]
               for old, new in zip(old_prompts, new_prompts))
    for old, new in zip(old_prompts, new_prompts):
        block = render_precedent_block(by_unit.get(new["work_unit_id"], []))
        treatment = block + "\n\n" if block else ""
        assert new["user_prompt"].replace(treatment, "", 1) == old["user_prompt"]


def test_0811_prompt_precedents_rebuild_and_obey_temporal_roster_contract():
    parent = Path("inputs/pr_review_v4/releases/dev-judgment-draft-0.7.0")
    units = _load_from(RETRIEVAL_PILOT, "derived/work_units.jsonl", ReviewWorkUnit)
    graphs = _load_from(RETRIEVAL_PILOT, "derived/change_graphs.jsonl", ChangeGraph)
    episode_ids = {unit.episode_id for unit in units}
    segments = [ReviewRoundSegment.model_validate_json(line) for line in
                (parent / "derived/round_segments.jsonl").read_text().splitlines() if line]
    segments = [item for item in segments if item.episode_id in episode_ids]
    rebuilt_cutoffs = build_retrieval_cutoffs(segments)
    stored_cutoffs = _load_from(RETRIEVAL_PILOT, "derived/retrieval_cutoffs.jsonl", RetrievalCutoff)
    assert [item.model_dump() for item in rebuilt_cutoffs] == [item.model_dump()
                                                               for item in stored_cutoffs]
    assert all("feedback_event_ids" not in item.model_dump() for item in stored_cutoffs)
    events = [SourceEvent.model_validate_json(line) for line in
              (parent / "source/events.jsonl").read_text().splitlines() if line]
    roster = load_reviewer_roster(Path("src/datasets/pr_review_v2/data/mathlib_roster.txt"))
    rebuilt = build_prompt_precedents(units, graphs, stored_cutoffs, events, roster)
    stored = _load_from(RETRIEVAL_PILOT, "derived/prompt_precedents.jsonl", PromptPrecedent)
    assert [item.model_dump() for item in rebuilt] == [item.model_dump() for item in stored]
    event_by_id = {item.event_id: item for item in events}
    for item in stored:
        source = event_by_id[item.source_event_id]
        assert source.event_type == "review_comment"
        assert source.actor.lower() in roster
        assert source.pr_number != item.target_pr_number
        assert source.occurred_at < item.cutoff_at
        assert item.matched_terms
        assert item.context
        assert item.context_sha256 == sha256_bytes(item.context.encode())
        assert not any(phrase in item.body.lower() for phrase in
                       ("same here", "same as", "as above", "ditto", "same comment"))


def test_candidate_contract_allows_abstention_and_rejects_foreign_target():
    unit = _load("derived/work_units.jsonl", ReviewWorkUnit)[0]
    assert candidates_from_response(unit, {"candidates": []}) == []
    bare = unit.change_ids[0].removeprefix("change:")
    normalized = candidates_from_response(unit, {"candidates": [{
        **_grounding(unit), "primary_change_id": bare, "change_ids": [bare],
        "concern_family": "style", "concern_label": "isolated by",
        "severity": "advisory",
        "claim": f"{unit.primary_subjects_by_change[unit.change_ids[0]]} uses isolated by.",
    }]})
    assert normalized[0].change_ids == [unit.change_ids[0]]
    assert normalized[0].concern_family == "style"
    assert normalized[0].concern_label == "isolated by"
    assert {item.collector for item in normalized[0].evidence_requests} == {
        "local_context", "policy", "repository_search"
    }
    with pytest.raises(ValueError, match="does not name its primary subject"):
        candidates_from_response(unit, {"candidates": [{
            **_grounding(unit, requested_change="Change Neighbor.theorem."),
            "change_ids": [unit.change_ids[0]], "concern_family": "style",
            "concern_label": "neighbor", "severity": "advisory",
            "claim": "Neighbor.theorem has the wrong layout.",
        }]})
    with pytest.raises(ValueError, match="must not plan"):
        candidates_from_response(unit, {"candidates": [{
            **_grounding(unit), "change_ids": [unit.change_ids[0]],
            "concern_family": "style", "concern_label": "style", "severity": "advisory",
            "claim": f"{unit.primary_subjects_by_change[unit.change_ids[0]]} has bad style.",
            "evidence_requests": [{"collector": "policy", "query": "style"}],
        }]})
    with pytest.raises(ValueError, match="concern_family"):
        candidates_from_response(unit, {"candidates": [{
            **_grounding(unit), "primary_change_id": bare, "change_ids": [bare],
            "concern_family": "proof_robustness", "concern_label": "fragile proof",
            "severity": "advisory",
            "claim": f"{unit.primary_subjects_by_change[unit.change_ids[0]]} is fragile.",
        }]})
    with pytest.raises(ValueError, match="outside"):
        candidates_from_response(unit, {"candidates": [{
            **_grounding(unit), "primary_change_id": "foreign", "change_ids": ["foreign"],
            "concern_family": "style",
            "concern_label": "isolated by", "severity": "advisory",
            "claim": "foreign uses isolated by.",
        }]})


def test_response_ingestion_replaces_failed_attempt_with_one_retry_success():
    unit = _load("derived/work_units.jsonl", ReviewWorkUnit)[0]
    failed = {"work_unit_id": unit.work_unit_id, "success": False,
              "error": "All samples failed: ['failed_error']"}
    retry = {"work_unit_id": unit.work_unit_id, "success": True,
             "response": {"candidates": []}}
    assert ingest_responses([unit], [failed, retry]) == []
    with pytest.raises(ValueError, match="0 successful"):
        ingest_responses([unit], [failed])
    with pytest.raises(ValueError, match="2 successful"):
        ingest_responses([unit], [retry, retry])


def test_repository_evidence_excludes_target_file_and_gates_selection(tmp_path):
    unit = _load("derived/work_units.jsonl", ReviewWorkUnit)[0]
    graph = {g.episode_id: g for g in _load("derived/change_graphs.jsonl", ChangeGraph)}[unit.episode_id]
    candidate = _candidate(unit)
    target_path = next(t.path for t in graph.targets if t.change_id == unit.change_ids[0])
    target_file = tmp_path / target_path
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text("theorem ExistingFoo : True := by trivial\n")
    artifacts, assertions, packet = collect_candidate(candidate, graph, tmp_path)
    assert packet.status == "contradicted"
    assert select_findings([candidate], [packet], assertions) == []

    other = tmp_path / "Mathlib" / "Other.lean"
    other.parent.mkdir(parents=True, exist_ok=True)
    other.write_text("theorem ExistingFoo : True := by trivial\n")
    artifacts, assertions, packet = collect_candidate(candidate, graph, tmp_path)
    findings = select_findings([candidate], [packet], assertions)
    assert packet.status == "supported"
    assert len(findings) == 1
    assert findings[0].candidate_id == candidate.candidate_id


def test_repository_hits_are_not_independent_support_for_naming(tmp_path):
    unit = _load("derived/work_units.jsonl", ReviewWorkUnit)[0]
    graph = {g.episode_id: g for g in _load("derived/change_graphs.jsonl", ChangeGraph)}[
        unit.episode_id
    ]
    candidate = _candidate(unit, label="naming", query="ExistingFoo")
    other = tmp_path / "Mathlib" / "Other.lean"
    other.parent.mkdir(parents=True)
    other.write_text("theorem ExistingFoo : True := by trivial\n")
    _artifacts, assertions, packet = collect_candidate(candidate, graph, tmp_path)
    assert packet.status == "inconclusive"
    assert not any(item.polarity == "supports" for item in assertions)
    assert select_findings([candidate], [packet], assertions) == []


def test_proof_golf_requires_structured_edit_and_external_compile_result(tmp_path, monkeypatch):
    units = _load("derived/work_units.jsonl", ReviewWorkUnit)
    graphs = {g.episode_id: g for g in _load("derived/change_graphs.jsonl", ChangeGraph)}
    unit = next(unit for unit in units if any(
        target.reviewed_code for target in graphs[unit.episode_id].targets
        if target.change_id in unit.change_ids
    ))
    graph = graphs[unit.episode_id]
    target = next(target for target in graph.targets
                  if target.change_id in unit.change_ids and target.reviewed_code)
    source_path = tmp_path / target.path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(target.reviewed_code)
    response = {"candidates": [{
        **_grounding(unit, target.change_id, f"Shorten {target.declaration_name}."),
        "change_ids": [target.change_id], "concern_family": "proof-golf",
        "concern_label": "shorter proof", "severity": "advisory",
        "claim": f"{target.declaration_name} has a needlessly long proof.", "proposed_edit": {
            "path": target.path, "declaration_name": target.declaration_name,
            "new_declaration": "theorem tiny : True := by trivial",
        },
    }]}
    candidate = candidates_from_response(unit, response)[0]
    monkeypatch.setattr("src.datasets.pr_review_v4.evidence.subprocess.run",
                        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""))
    _artifacts, assertions, packet = collect_candidate(candidate, graph, tmp_path)
    assert packet.status == "supported"
    assert any(item.polarity == "supports" for item in assertions)


def test_candidate_ingestion_normalizes_workspace_edit_path_prefixes():
    units = _load("derived/work_units.jsonl", ReviewWorkUnit)
    graphs = {g.episode_id: g for g in _load("derived/change_graphs.jsonl", ChangeGraph)}
    unit = next(unit for unit in units if any(
        target.reviewed_code for target in graphs[unit.episode_id].targets
        if target.change_id in unit.change_ids
    ))
    target = next(
        target for target in graphs[unit.episode_id].targets
        if target.change_id in unit.change_ids and target.reviewed_code
    )
    response = {"candidates": [{
        **_grounding(unit, target.change_id, f"Revise {target.declaration_name}."),
        "change_ids": [target.change_id],
        "concern_family": "style",
        "concern_label": "structured edit",
        "severity": "advisory",
        "claim": f"{target.declaration_name} should use the structured edit.",
        "proposed_edit": {
            "path": f"target/target/{target.path}",
            "declaration_name": target.declaration_name,
            "new_declaration": target.reviewed_code,
        },
    }]}
    candidate = candidates_from_response(unit, response)[0]
    assert candidate.proposed_edit.path == target.path
    assert normalize_proposed_edit_path(f"./b/target/{target.path}") == target.path


def test_correctness_compile_support_requires_target_local_baseline_error(tmp_path, monkeypatch):
    units = _load("derived/work_units.jsonl", ReviewWorkUnit)
    graphs = {g.episode_id: g for g in _load("derived/change_graphs.jsonl", ChangeGraph)}
    unit = next(unit for unit in units if any(
        target.reviewed_entity_ids for target in graphs[unit.episode_id].targets
        if target.change_id in unit.change_ids
    ))
    graph = graphs[unit.episode_id]
    target = next(target for target in graph.targets
                  if target.change_id in unit.change_ids and target.reviewed_entity_ids)
    entity = next(entity for entity in graph.entities
                  if entity.entity_id == target.reviewed_entity_ids[0])
    source_path = tmp_path / target.path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(target.reviewed_code or "")
    (tmp_path / ".elan" / "bin").mkdir(parents=True)
    response = {"candidates": [{
        **_grounding(unit, target.change_id, f"Fix {target.declaration_name} so it compiles."),
        "change_ids": [target.change_id], "concern_family": "correctness",
        "concern_label": "reviewed declaration does not compile", "severity": "blocking",
        "claim": "The changed declaration has a compile error.", "suggested_fix": "Use this edit.",
        "proposed_edit": {"path": target.path, "declaration_name": target.declaration_name,
                          "new_declaration": (target.reviewed_code or "") + "\n-- still broken"},
    }]}
    candidate = candidates_from_response(unit, response)[0]
    calls = []

    def fail_at_target(*args, **kwargs):
        calls.append((args, kwargs))
        if len(calls) > 1:
            return SimpleNamespace(returncode=1, stdout="", stderr="candidate edit failed")
        return SimpleNamespace(
            returncode=1, stdout="",
            stderr=f"{target.path}:{entity.span.line_start}:1: error: failed",
        )

    monkeypatch.setattr("src.datasets.pr_review_v4.evidence.subprocess.run", fail_at_target)
    _artifacts, assertions, packet = collect_candidate(candidate, graph, tmp_path)
    assert packet.status == "supported"
    assert any(item.polarity == "supports" for item in assertions)
    assert any(item.assertion_scope == "proposed_edit" and item.polarity == "contradicts"
               for item in assertions)
    findings = select_findings([candidate], [packet], assertions)
    assert len(findings) == 1
    assert findings[0].suggested_fix is None
    assert findings[0].severity == "blocking"
    assert "does not compile in the reviewed state" in findings[0].claim
    assert str(tmp_path / ".elan" / "bin") in calls[0][1]["env"]["PATH"]


def test_style_policy_uses_repository_checker_and_target_local_diagnostic(tmp_path, monkeypatch):
    unit = _load("derived/work_units.jsonl", ReviewWorkUnit)[0]
    graph = {g.episode_id: g for g in _load("derived/change_graphs.jsonl", ChangeGraph)}[unit.episode_id]
    target = next(target for target in graph.targets if target.change_id == unit.change_ids[0])
    ranges = {item.range_id: item for item in graph.changed_ranges}
    line = next(ranges[item].reviewed_span.line_start for item in target.changed_range_ids
                if ranges[item].reviewed_span is not None)
    script = tmp_path / "scripts" / "lint-style.py"
    script.parent.mkdir(parents=True)
    script.write_text("# registered repository checker\n")
    candidate = candidates_from_response(unit, {"candidates": [{
        **_grounding(unit, target.change_id, f"Restyle {target.declaration_name or target.path}."),
        "change_ids": [target.change_id], "concern_family": "style",
        "concern_label": "repository style violation", "severity": "advisory",
        "claim": "The changed lines violate the repository style checker.",
    }]})[0]
    monkeypatch.setattr(
        "src.datasets.pr_review_v4.evidence.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout=f"::error file={target.path},line={line},code=ERR::{target.path}:{line} ERR",
            stderr="",
        ),
    )
    _artifacts, assertions, packet = collect_candidate(candidate, graph, tmp_path)
    assert packet.status == "supported"
    assert any(item.polarity == "supports" for item in assertions)


def test_baseline_compile_is_cached_across_candidates(tmp_path, monkeypatch):
    unit = _load("derived/work_units.jsonl", ReviewWorkUnit)[0]
    graph = {g.episode_id: g for g in _load("derived/change_graphs.jsonl", ChangeGraph)}[unit.episode_id]
    target = next(target for target in graph.targets if target.change_id == unit.change_ids[0])
    source_path = tmp_path / target.path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(target.reviewed_code or "")
    candidate = candidates_from_response(unit, {"candidates": [{
        **_grounding(unit, target.change_id, f"Fix {target.declaration_name or target.path}."),
        "change_ids": [target.change_id], "concern_family": "correctness",
        "concern_label": "compile concern", "severity": "advisory",
        "claim": f"{target.declaration_name or target.path} may not compile.",
    }]})[0]
    calls = []

    def compile_ok(*args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("src.datasets.pr_review_v4.evidence.subprocess.run", compile_ok)
    cache = {}
    collect_candidate(candidate, graph, tmp_path, baseline_compile_cache=cache)
    collect_candidate(candidate, graph, tmp_path, baseline_compile_cache=cache)
    assert len(calls) == 1


def test_deterministic_discovery_maps_tool_failures_to_scheduled_target(tmp_path):
    unit = _load("derived/work_units.jsonl", ReviewWorkUnit)[0]
    graph = {g.episode_id: g for g in _load("derived/change_graphs.jsonl", ChangeGraph)}[unit.episode_id]
    target = next(target for target in graph.targets
                  if target.change_id in unit.change_ids and target.reviewed_entity_ids)
    entity = next(item for item in graph.entities if item.entity_id == target.reviewed_entity_ids[0])
    source = tmp_path / target.path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(target.reviewed_code or "")
    style_script = tmp_path / "scripts" / "lint-style.py"
    style_script.parent.mkdir(parents=True)
    style_script.write_text("# repository checker\n")
    calls = []

    def tool(command, **kwargs):
        calls.append(command)
        if command[0] == "lake":
            return SimpleNamespace(
                returncode=1, stdout="",
                stderr=f"{target.path}:{entity.span.line_start}:1: error: failed",
            )
        return SimpleNamespace(
            returncode=1,
            stdout=(f"::error file={target.path},line={entity.span.line_start},code=ERR::"
                    f"{target.path}:{entity.span.line_start} ERR"),
            stderr="",
        )

    discovered, failures = discover_deterministic_candidates(
        [unit], [graph], {unit.episode_id: str(tmp_path)}, run_command=tool)
    assert failures == {}
    assert {item.concern_family for item in discovered} == {"correctness", "style"}
    assert all(item.producer == "deterministic" for item in discovered)
    assert all(item.primary_change_id == target.change_id for item in discovered)
    assert len(calls) == 2


def test_evaluator_explicitly_scopes_smoke_denominators():
    judgments = _load("gold/judgments.jsonl", JudgmentNode)
    views = _load("gold/intervention_views.jsonl", InterventionView)
    cases = _load("gold/pilot_cases.jsonl", PilotCase)
    report = evaluate_funnel(judgments, views, [], [], cases, [33057, 33098, 33438])
    assert report["evaluated_pr_numbers"] == [33057, 33098, 33438]
    assert report["counts"]["obligations"] == 14
    assert report["counts"]["eligible_interventions"] == 5
    assert report["counts"]["intervention_prs"] == 2
    assert report["counts"]["control_prs"] == 1


def test_semantic_judge_pairs_stable_targets_and_separates_issue_resolution():
    units = _load("derived/work_units.jsonl", ReviewWorkUnit)
    unit = next(item for item in units if
                "change:c79e40846a8ccb396fbed4bb8a4aeb834a0eea561d9136e95e2a36763d603335"
                in item.change_ids)
    change_id = "change:c79e40846a8ccb396fbed4bb8a4aeb834a0eea561d9136e95e2a36763d603335"
    candidate = candidates_from_response(unit, {"candidates": [{
        **_grounding(unit, change_id,
                     "Remove the unused nonempty binder from "
                     "Metric.coveringNumber_two_mul_le_externalCoveringNumber."),
        "change_ids": [change_id], "concern_family": "style",
        "concern_label": "unused binder", "severity": "advisory",
        "claim": ("Metric.coveringNumber_two_mul_le_externalCoveringNumber has an unused "
                  "nonempty binder."),
    }]})[0]
    judgments = _load("gold/judgments.jsonl", JudgmentNode)
    views = _load("gold/intervention_views.jsonl", InterventionView)
    pairs = build_pairs(judgments, views, [candidate], unit.change_ids)
    assert len(pairs) == 1
    assert pairs[0]["candidate"].candidate_id == candidate.candidate_id
    assert pairs[0]["obligation"].claim.startswith("In `coveringNumber_two_mul")
    match = _match(pairs[0], "test-model", False, True, "Different branch transformation.")
    assert match.judge_version == JUDGE_VERSION
    assert not match.issue_match
    assert not match.resolution_match
    report = semantic_report(judgments, views, [candidate], [match], unit.change_ids)
    assert report["counts"]["obligations"] == 6
    assert report["location_recall"] == pytest.approx(1 / 6)
    assert report["issue_recall"] == 0
    clamped = parse_verdict('{"issue_match": false, "resolution_match": true, "reason": "x"}')
    assert (clamped.issue_match, clamped.resolution_match, clamped.reason) == (False, False, "x")


def test_temporal_retrieval_rejects_future_and_current_pr_events():
    boundary = ReviewEpisodeBoundary(
        episode_id="e", repo="r", pr_number=2, round_index=1,
        review_started_at="2026-01-02T00:00:00Z", reviewed_head_sha="h",
        reviewed_head_resolution="review_commit_id", triggering_event_ids=[], feedback_event_ids=[],
        source_bundle_sha256="s", compare_sha256="c",
    )
    ref = ArtifactRef(path="x", sha256="s")
    prior = SourceEvent(event_id="prior", repo="r", pr_number=1, event_type="review_comment",
                        occurred_at="2026-01-01T00:00:00Z", source_object=ref,
                        source_key="/review_comments/0", payload_sha256="p")
    current = prior.model_copy(update={"event_id": "current", "pr_number": 2})
    assert validate_precedents(boundary, [prior, current]) == [prior]
    future = prior.model_copy(update={"event_id": "future", "occurred_at": "2026-01-03T00:00:00Z"})
    with pytest.raises(ValueError, match="future precedent"):
        validate_precedents(boundary, [future])


def test_precedent_artifact_cannot_select_by_itself(tmp_path):
    unit = _load("derived/work_units.jsonl", ReviewWorkUnit)[0]
    graph = {g.episode_id: g for g in _load("derived/change_graphs.jsonl", ChangeGraph)}[unit.episode_id]
    response = {"candidates": [{
        **_grounding(unit), "change_ids": unit.change_ids, "concern_family": "style",
        "concern_label": "different style", "severity": "advisory",
        "claim": f"{unit.primary_subjects_by_change[unit.change_ids[0]]} uses the wrong style.",
    }]}
    candidate = candidates_from_response(unit, response)[0]
    candidate = candidate.model_copy(update={"evidence_requests": [EvidenceRequest(
        collector="precedent", query="different style", purpose="both")]
    })
    bundle = tmp_path / "bundle.json"
    bundle.write_text(json.dumps({"review_comments": [{"body": "Please use a different style."}]}))
    event = SourceEvent(event_id="old", repo="r", pr_number=1, event_type="review_comment",
                        occurred_at="2025-01-01T00:00:00Z",
                        source_object=ArtifactRef(path=str(bundle), sha256="unused"),
                        source_key="/review_comments/0", payload_sha256="unused")
    boundary = ReviewEpisodeBoundary(
        episode_id=unit.episode_id, repo="r", pr_number=unit.pr_number, round_index=1,
        review_started_at="2026-01-01T00:00:00Z", reviewed_head_sha="h",
        reviewed_head_resolution="review_commit_id", triggering_event_ids=[], feedback_event_ids=[],
        source_bundle_sha256="s", compare_sha256="c",
    )
    _artifacts, assertions, packet = collect_candidate(candidate, graph, boundary=boundary, events=[event])
    assert packet.status == "inconclusive"
    assert select_findings([candidate], [packet], assertions) == []


def test_stable_release_has_reviewed_atomic_decompositions():
    stable = Path("inputs/pr_review_v4/releases/dev-judgment-stable-0.9.0")
    judgments = _load_from(stable, "gold/judgments.jsonl", JudgmentNode)
    views = _load_from(stable, "gold/intervention_views.jsonl", InterventionView)
    reviewed = [
        item for item in judgments
        if item.annotation.atomicity_status == "reviewed_decomposed"
    ]
    assert len(reviewed) == 9
    assert sum(len(item.obligations) for item in reviewed) == 25
    assert all(obligation.source_event_ids for item in reviewed for obligation in item.obligations)
    assert all(item.annotation.atomicity_status != "needs_decomposition" for item in judgments)
    view_by_intervention = {item.source_intervention_id: item for item in views}
    assert all(
        view_by_intervention[item.source_intervention_id].evaluation_eligibility == "included"
        for item in reviewed
    )


def test_run_contract_seals_exact_terminal_and_evidence_coverage(tmp_path):
    unit = _load("derived/work_units.jsonl", ReviewWorkUnit)[0]
    prompt = next(
        item for item in _load("derived/rendered_prompts.jsonl", RenderedPrompt)
        if item.work_unit_id == unit.work_unit_id
    )
    plan = create_run_plan(
        PILOT, tmp_path / "run_plan.json", "test-run", "test-model", [unit], [prompt],
        created_at="2026-07-14T00:00:00Z",
    )
    (tmp_path / "candidate_responses.jsonl").write_text(json.dumps({
        "work_unit_id": unit.work_unit_id,
        "prompt_sha256": prompt.prompt_sha256,
        "response": {"candidates": []},
        "success": True,
        "error": None,
    }) + "\n")
    (tmp_path / "candidates.jsonl").write_text("")
    (tmp_path / "evidence").mkdir()
    (tmp_path / "evidence/packets.jsonl").write_text("")
    (tmp_path / "findings.jsonl").write_text("")
    manifest = seal_run(tmp_path, created_at="2026-07-14T00:01:00Z")
    assert plan.expected_work_unit_ids == [unit.work_unit_id]
    assert manifest.completion_status == "complete"
    assert manifest.successful_work_unit_ids == [unit.work_unit_id]
    assert manifest.candidates == manifest.evidence_packets == manifest.findings == 0
