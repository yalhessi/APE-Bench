"""Build the production wrapper-composition smoke release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from src.mathlib_review.release.releases import artifact_ref
from src.mathlib_review.io import (
    canonical_json_bytes,
    display_path,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from src.mathlib_review.opportunities.method_registry import load_registry
from src.mathlib_review.evidence.operators.canonical_api import evidence_artifact
from src.mathlib_review.evidence.operators.wrapper_composition import COMPOSITION_VERSION, discover_wrapper_composition
from src.mathlib_review.opportunities.oracle import ADJUDICATION_SYSTEM_PROMPT
from src.mathlib_review.agenda.render_prompts import FACET_CHECKLIST, SYSTEM_PROMPT, render_work_unit
from src.mathlib_review.schema import (
    ArtifactRef,
    ChangeGraph,
    CompositionSource,
    DatasetManifest,
    InvestigationRecord,
    InvestigationTask,
    OperatorRun,
    OpportunityEvidenceArtifact,
    OpportunityTransformation,
    PRRelation,
    RelationEvidence,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewOpportunity,
    ReviewWorkUnit,
    WrapperCompositionPlan,
)


TREATMENT_VERSION = "wrapper-composition-smoke/1"
DEFAULT_PARENT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
DEFAULT_PHASE2 = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1")
DEFAULT_WORKSPACES = Path("data/code_execute/repos/mathlib4/workspaces")
DEFAULT_OUT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.3-wrapper-smoke")

TARGETS = {
    33098: "Metric.coveringNumber_le_packingNumber",
    33438: "Real.arctan_inv_sqrt_three",
}


def _clone_unit(source: ReviewWorkUnit, change_id: str) -> ReviewWorkUnit:
    identity = {
        "treatment_version": TREATMENT_VERSION,
        "source_work_unit_sha256": source.source_sha256,
        "change_id": change_id,
    }
    digest = sha256_bytes(canonical_json_bytes(identity))
    return source.model_copy(update={
        "work_unit_id": f"wu:wrapper-smoke:{digest[:20]}",
        "change_ids": [change_id],
        "target_sha256s": {change_id: source.target_sha256s[change_id]},
        "entity_ids_by_change": {change_id: source.entity_ids_by_change.get(change_id, [])},
        "primary_subjects_by_change": {change_id: source.primary_subjects_by_change[change_id]},
        "renderer_version": TREATMENT_VERSION,
        "source_sha256": digest,
    })


def _clone_task(
    source: InvestigationTask, unit: ReviewWorkUnit, registry_sha: str
) -> InvestigationTask:
    payload = {
        "method_id": source.method_id,
        "work_unit_id": unit.work_unit_id,
        "episode_id": source.episode_id,
        "pr_number": source.pr_number,
        "modification_ids": source.modification_ids,
        "primary_change_id": source.primary_change_id,
        "related_change_ids": source.related_change_ids,
        "expected_operators": source.expected_operators,
        "method_registry_sha256": registry_sha,
    }
    digest = sha256_bytes(canonical_json_bytes({"treatment_version": TREATMENT_VERSION, **payload}))
    return InvestigationTask(
        investigation_id=f"investigation:wrapper-smoke:{digest[:20]}",
        source_sha256=digest,
        **payload,
    )


def _operator_run(
    task: InvestigationTask,
    operator: str,
    status: str,
    artifact_ids: Iterable[str],
    result_count: int,
    failure_reason: str | None = None,
) -> OperatorRun:
    payload = {
        "investigation_id": task.investigation_id,
        "operator": operator,
        "status": status,
        "query_sha256": None,
        "artifact_ids": list(artifact_ids),
        "result_count": result_count,
        "failure_reason": failure_reason,
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return OperatorRun(
        operator_run_id=f"operator-run:{digest[:24]}", source_sha256=digest, **payload
    )


def _opportunity(
    task: InvestigationTask,
    plan: WrapperCompositionPlan,
    artifact_ids: List[str],
    source_names: List[str],
) -> ReviewOpportunity:
    if plan.status == "composed":
        observed = (
            "The target reconstructs an inequality through low-level infimum reasoning even though "
            "a frozen repository wrapper composes with three current-PR witnesses."
        )
        transformation = OpportunityTransformation(
            kind="compose_repository_wrapper",
            symbols=source_names,
            description=(
                "Replace the reconstructed implementation proof with the generated composition of "
                "the repository wrapper and current-PR cardinality, cover, and subset witnesses."
            ),
        )
        score = 1.0
    else:
        observed = (
            "A related current-PR declaration has parallel proof shape, but no repository wrapper "
            "and compatible changed-sibling chain was found."
        )
        transformation = None
        score = 0.0
    payload = {
        "investigation_id": task.investigation_id,
        "method_id": task.method_id,
        "episode_id": task.episode_id,
        "pr_number": task.pr_number,
        "primary_change_id": task.primary_change_id,
        "related_change_ids": plan.related_change_ids,
        "observed_pattern": observed,
        "proposed_transformation": transformation.model_dump(mode="json") if transformation else None,
        "source_artifact_ids": artifact_ids,
        "discovery_rank": 1,
        "discovery_score": score,
        "source_provenance": "automatic",
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return ReviewOpportunity(
        opportunity_id=f"opportunity:{digest[:24]}", source_sha256=digest, **payload
    )


def _render_prompt(
    unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput,
    graph: ChangeGraph,
    opportunity: ReviewOpportunity,
    evidence_by_id: Dict[str, OpportunityEvidenceArtifact],
) -> RenderedPrompt:
    evidence = "\n".join(
        f"- `{artifact_id}` [{evidence_by_id[artifact_id].kind}] "
        f"{evidence_by_id[artifact_id].source_ref}\n  {evidence_by_id[artifact_id].content}"
        for artifact_id in opportunity.source_artifact_ids
    )
    transformation = opportunity.proposed_transformation
    alternative = transformation.description if transformation else "No composition was discovered."
    block = (
        "# Automatically discovered wrapper-composition opportunity\n"
        "Treat this record as a bounded hypothesis, not proof that a request is warranted. Distinguish "
        "source retrieval, edit construction, Lean validity, abstraction improvement, and review "
        "worthiness. A parallel sibling alone is insufficient.\n\n"
        f"## Opportunity `{opportunity.opportunity_id}`\n"
        f"Method: `{opportunity.method_id}`\n"
        f"Primary change: `{opportunity.primary_change_id}`\n"
        f"Observed pattern: {opportunity.observed_pattern}\n"
        f"Proposed alternative: {alternative}\n"
        "Question: Does this exact source chain support a valid and review-worthy request to compose "
        "the higher-level API? Verify the proposed declaration with Lean when one is supplied. Do not "
        "request a change merely because the alternative is shorter.\n"
        f"### Evidence\n{evidence}"
    )
    baseline = render_work_unit(unit, episode, graph)
    user = baseline.user_prompt.replace(SYSTEM_PROMPT, ADJUDICATION_SYSTEM_PROMPT, 1)
    user = user.replace(
        FACET_CHECKLIST,
        "### Adjudication context\nThis target is context for one automatically discovered "
        "wrapper-composition hypothesis. Do not perform an unscoped review.",
    )
    user = user.replace("# PR #", block + "\n\n# PR #", 1)
    system_hash = sha256_bytes(ADJUDICATION_SYSTEM_PROMPT.encode())
    user_hash = sha256_bytes(user.encode())
    prompt_hash = sha256_bytes(canonical_json_bytes({
        "system": ADJUDICATION_SYSTEM_PROMPT, "user": user,
    }))
    return RenderedPrompt(
        work_unit_id=unit.work_unit_id,
        renderer_version=TREATMENT_VERSION,
        system_prompt=ADJUDICATION_SYSTEM_PROMPT,
        user_prompt=user,
        system_sha256=system_hash,
        user_sha256=user_hash,
        prompt_sha256=prompt_hash,
        rendered_chars=len(ADJUDICATION_SYSTEM_PROMPT) + len(user),
        estimated_tokens=(len(ADJUDICATION_SYSTEM_PROMPT.encode()) + len(user.encode()) + 3) // 4,
        included_change_ids=list(unit.change_ids),
        omitted_change_ids=[],
    )


def _relation_content(
    task: InvestigationTask,
    relations: List[PRRelation],
    relation_evidence: List[RelationEvidence],
) -> str:
    relevant = [
        relation for relation in relations
        if relation.source_change_id == task.primary_change_id
        and set(relation.related_change_ids) & set(task.related_change_ids)
    ]
    evidence_by_id = {item.evidence_id: item for item in relation_evidence}
    rows = []
    for relation in relevant:
        observations = [
            evidence_by_id[evidence_id].content
            for evidence_id in relation.evidence_artifact_ids
            if evidence_id in evidence_by_id
        ]
        rows.append({
            "relation_id": relation.relation_id,
            "kind": relation.relation_kind,
            "related_change_ids": relation.related_change_ids,
            "confidence": relation.confidence,
            "observations": observations,
        })
    return json.dumps(rows, ensure_ascii=False, sort_keys=True)


def build_artifacts(parent: Path, phase2: Path, workspaces: Path) -> Dict[str, List]:
    episodes = load_jsonl(parent / "input/episodes.jsonl", ReviewEpisodeInput)
    graphs = load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
    units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)
    tasks = load_jsonl(phase2 / "derived/investigation_tasks.jsonl", InvestigationTask)
    relations = load_jsonl(phase2 / "derived/pr_relations.jsonl", PRRelation)
    relation_evidence = load_jsonl(phase2 / "derived/relation_evidence.jsonl", RelationEvidence)
    registry_sha = sha256_file(phase2 / "methods.jsonl")
    graph_by_pr = {item.pr_number: item for item in graphs}
    episode_by_pr = {item.pr_number: item for item in episodes}
    output = {
        "episodes": [], "graphs": [], "units": [], "tasks": [], "sources": [], "plans": [],
        "evidence": [], "operator_runs": [], "records": [], "opportunities": [], "prompts": [],
    }
    for pr_number, declaration_name in TARGETS.items():
        graph = graph_by_pr[pr_number]
        episode = episode_by_pr[pr_number]
        target = next(item for item in graph.targets if item.declaration_name == declaration_name)
        source_unit = next(item for item in units if target.change_id in item.change_ids)
        unit = _clone_unit(source_unit, target.change_id)
        source_task = next(
            item for item in tasks
            if item.method_id == "wrapper_composition.v1" and item.primary_change_id == target.change_id
        )
        task = _clone_task(source_task, unit, registry_sha)
        discovery = discover_wrapper_composition(
            task, graph, episode, workspaces / episode.base_sha
        )
        reviewed = evidence_artifact(
            task, "reviewed_code", f"reviewed-change:{target.change_id}",
            target.reviewed_code or target.base_code or "", episode.reviewed_head_sha,
        )
        relation = evidence_artifact(
            task, "pr_relation", f"phase2-relations:{task.primary_change_id}",
            _relation_content(task, relations, relation_evidence), episode.reviewed_head_sha,
        )
        source_lines = "\n".join(
            f"{source.role}: {source.declaration_name}\n{source.signature}"
            for source in discovery.sources
        ) or "No compatible repository wrapper and changed-sibling chain was found."
        source_kind = "repository_declaration" if discovery.plan.status == "composed" else "negative_control"
        source_evidence = evidence_artifact(
            task, source_kind, f"composition-sources:{task.investigation_id}",
            source_lines, episode.base_sha,
        )
        plan_evidence = evidence_artifact(
            task, "composition_plan", discovery.plan.plan_id,
            discovery.plan.replacement_declaration or "No composition plan was produced.",
            episode.reviewed_head_sha,
        )
        dependency_evidence = evidence_artifact(
            task, "dependency_reduction", f"dependency-delta:{discovery.plan.plan_id}",
            json.dumps({
                "old": discovery.plan.old_dependencies,
                "new": discovery.plan.new_dependencies,
                "removed": discovery.plan.removed_dependencies,
            }, ensure_ascii=False, sort_keys=True),
            episode.reviewed_head_sha,
        )
        applicability_content = discovery.applicability.content
        if discovery.applicability.replacement:
            applicability_content += "\nProposed replacement:\n" + discovery.applicability.replacement.new_block
        applicability = evidence_artifact(
            task,
            "applicability_check" if discovery.plan.status == "composed" else "negative_control",
            f"wrapper-applicability:{task.investigation_id}", applicability_content,
            episode.reviewed_head_sha,
        )
        evidence = [reviewed, relation, source_evidence, plan_evidence, dependency_evidence, applicability]
        opportunity = _opportunity(
            task, discovery.plan, [item.artifact_id for item in evidence],
            [source.declaration_name for source in discovery.sources],
        )
        search_run = _operator_run(
            task, "pr_composition_search", "completed",
            [relation.artifact_id, source_evidence.artifact_id, plan_evidence.artifact_id],
            1 if discovery.plan.status == "composed" else 0,
        )
        applicability_run = _operator_run(
            task, "applicability_check", "completed",
            [plan_evidence.artifact_id, dependency_evidence.artifact_id],
            1 if discovery.plan.status == "composed" else 0,
        )
        if discovery.plan.status == "no_composition":
            compile_run = _operator_run(
                task, "compile_composed_edit", "completed", [applicability.artifact_id], 0,
            )
        elif discovery.applicability.status in {"compiled", "failed"}:
            compile_run = _operator_run(
                task, "compile_composed_edit", "completed", [applicability.artifact_id],
                1 if discovery.applicability.status == "compiled" else 0,
            )
        else:
            compile_run = _operator_run(
                task, "compile_composed_edit", "unavailable", [applicability.artifact_id], 0,
                failure_reason=discovery.applicability.content,
            )
        operator_runs = [search_run, applicability_run, compile_run]
        record_payload = {
            "investigation_id": task.investigation_id,
            "execution_status": "completed",
            "disposition": "opportunities",
            "operator_run_ids": [item.operator_run_id for item in operator_runs],
            "artifact_ids": [item.artifact_id for item in evidence],
            "opportunity_ids": [opportunity.opportunity_id],
            "followup_ids": [],
            "basis": (
                "The source chain and concrete composition are exposed for independent Lean and "
                "review-worthiness adjudication."
                if discovery.plan.status == "composed"
                else "The matched parallel-proof control is exposed for no-request adjudication."
            ),
            "producer": "deterministic",
        }
        record_digest = sha256_bytes(canonical_json_bytes(record_payload))
        record = InvestigationRecord(source_sha256=record_digest, **record_payload)
        prompt = _render_prompt(
            unit, episode, graph, opportunity, {item.artifact_id: item for item in evidence}
        )
        output["episodes"].append(episode)
        output["graphs"].append(graph)
        output["units"].append(unit)
        output["tasks"].append(task)
        output["sources"].extend(discovery.sources)
        output["plans"].append(discovery.plan)
        output["evidence"].extend(evidence)
        output["operator_runs"].extend(operator_runs)
        output["records"].append(record)
        output["opportunities"].append(opportunity)
        output["prompts"].append(prompt)
    return output


def build_release(
    parent: Path = DEFAULT_PARENT,
    phase2: Path = DEFAULT_PHASE2,
    workspaces: Path = DEFAULT_WORKSPACES,
    out: Path = DEFAULT_OUT,
) -> Tuple[DatasetManifest, Dict]:
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        return (
            DatasetManifest.model_validate_json(manifest_path.read_text()),
            json.loads((out / "derived/wrapper_composition_report.json").read_text()),
        )
    parent_manifest = DatasetManifest.model_validate_json((parent / "manifest.json").read_text())
    rows = build_artifacts(parent, phase2, workspaces)
    methods = load_registry(phase2 / "methods.jsonl")
    registry_path = out / "methods.jsonl"
    write_once(registry_path, jsonl_bytes(methods))
    files = {
        "input/episodes.jsonl": (rows["episodes"], "episode1", "reviewer_visible_episodes"),
        "derived/change_graphs.jsonl": (rows["graphs"], "cg1", "complete_change_graphs"),
        "derived/work_units.jsonl": (rows["units"], "work-unit1", "wrapper_smoke_units"),
        "derived/rendered_prompts.jsonl": (rows["prompts"], "rendered-prompt1", "wrapper_opportunity_prompts"),
        "derived/investigation_tasks.jsonl": (rows["tasks"], "investigation-task1", "wrapper_investigation_tasks"),
        "derived/composition_sources.jsonl": (rows["sources"], "composition-source1", "composition_sources"),
        "derived/composition_plans.jsonl": (rows["plans"], "wrapper-composition-plan1", "composition_plans"),
        "derived/opportunity_evidence.jsonl": (rows["evidence"], "opportunity-evidence-artifact1", "opportunity_evidence"),
        "derived/operator_runs.jsonl": (rows["operator_runs"], "operator-run1", "operator_runs"),
        "derived/investigation_records.jsonl": (rows["records"], "investigation-record1", "investigation_records"),
        "derived/opportunities.jsonl": (rows["opportunities"], "review-opportunity1", "automatic_review_opportunities"),
    }
    refs = {}
    for relative, (records, schema, role) in files.items():
        path = out / relative
        write_once(path, jsonl_bytes(records))
        refs[relative] = artifact_ref(path, out, role, schema, len(records))
    positive, control = rows["plans"]
    positive_sources = rows["sources"][:4]
    compile_run = rows["operator_runs"][2]
    report = {
        "schema_version": "wrapper-composition-report1",
        "composition_version": COMPOSITION_VERSION,
        "counts": {"targets": 2, "sources": len(rows["sources"]), "plans": 2},
        "positive": {
            "primary_change_id": positive.primary_change_id,
            "status": positive.status,
            "source_roles": [source.role for source in positive_sources],
            "source_names": [source.declaration_name for source in positive_sources],
            "related_change_ids": positive.related_change_ids,
            "removed_dependencies": positive.removed_dependencies,
            "compile_status": compile_run.status,
        },
        "control": {
            "primary_change_id": control.primary_change_id,
            "status": control.status,
            "related_change_ids": control.related_change_ids,
        },
        "offline_gate": (
            "pass"
            if positive.status == "composed"
            and [source.role for source in positive_sources] == [
                "repository_wrapper", "cardinality_bridge", "cover_witness", "subset_witness"
            ]
            and positive_sources[0].declaration_name == "Metric.IsCover.coveringNumber_le_encard"
            and {"iInf_le", "iInf_pos", "le_of_eq"} <= set(positive.removed_dependencies)
            and len(positive.related_change_ids) == 3
            and control.status == "no_composition"
            else "fail"
        ),
    }
    report_path = out / "derived/wrapper_composition_report.json"
    write_once(report_path, pretty_json_bytes(report))
    report_ref = artifact_ref(
        report_path, out, "wrapper_composition_report", "wrapper-composition-report1", 1
    )
    registry_ref = artifact_ref(
        registry_path, out, "investigation_method_registry", "investigation-method1", len(methods)
    )
    manifest = DatasetManifest(
        dataset_id="mathlib-pr-review-v4-wrapper-composition-smoke",
        release="0.9.3-wrapper-composition-smoke",
        source_kind=parent_manifest.source_kind,
        split="development",
        sources=[
            ArtifactRef(
                path=display_path(parent / "manifest.json"), role="parent_stable_release",
                schema_version=parent_manifest.schema_version,
                sha256=sha256_file(parent / "manifest.json"), records=1,
            ),
            ArtifactRef(
                path=display_path(phase2 / "manifest.json"), role="parent_opportunity_treatment",
                schema_version="systematic-opportunity-treatment1",
                sha256=sha256_file(phase2 / "manifest.json"), records=1,
            ),
        ],
        input_artifacts=[refs["input/episodes.jsonl"]],
        derived_artifacts=[
            registry_ref, *[refs[key] for key in files if key.startswith("derived/")], report_ref,
        ],
        pr_numbers=sorted(TARGETS),
        corpus_cutoff_policy=(
            "Wrapper discovery uses only frozen review-base declarations and deterministic relations "
            "among current-PR changes. Generation excludes gold, comments, outcomes, and future code."
        ),
        generator_tree_state="unknown",
        generator_versions={
            **parent_manifest.generator_versions,
            "wrapper_smoke": TREATMENT_VERSION,
            "wrapper_composition": COMPOSITION_VERSION,
        },
        created_at="2026-07-17T00:00:00-05:00",
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--phase2", type=Path, default=DEFAULT_PHASE2)
    parser.add_argument("--workspaces", type=Path, default=DEFAULT_WORKSPACES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    _, report = build_release(args.parent, args.phase2, args.workspaces, args.out)
    print(json.dumps({
        "release": str(args.out),
        "manifest_sha256": sha256_file(args.out / "manifest.json"),
        "offline_gate": report["offline_gate"],
        "positive": report["positive"],
        "control": report["control"],
    }, indent=2))


if __name__ == "__main__":
    main()
