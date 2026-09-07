"""Build the production canonical-API discovery smoke release."""

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
from src.mathlib_review.opportunities.method_registry import DEFAULT_REGISTRY, load_registry
from src.mathlib_review.evidence.operators.canonical_api import (
    INDEX_VERSION,
    RETRIEVAL_VERSION,
    build_declaration_index,
    check_applicability,
    evidence_artifact,
    is_high_confidence_insert_separation,
    propose_insert_separation_replacement,
    rank_declarations,
)
from src.mathlib_review.opportunities.oracle import ADJUDICATION_SYSTEM_PROMPT
from src.mathlib_review.agenda.render_prompts import FACET_CHECKLIST, SYSTEM_PROMPT, render_work_unit
from src.mathlib_review.schema import (
    ArtifactRef,
    CanonicalRetrievalHit,
    ChangeGraph,
    DatasetManifest,
    InvestigationRecord,
    InvestigationTask,
    OperatorRun,
    OpportunityEvidenceArtifact,
    OpportunityTransformation,
    RenderedPrompt,
    RepositoryDeclaration,
    ReviewEpisodeInput,
    ReviewOpportunity,
    ReviewWorkUnit,
)


TREATMENT_VERSION = "canonical-api-smoke/1"
DEFAULT_PARENT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
DEFAULT_PHASE2 = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1")
DEFAULT_WORKSPACES = Path("data/code_execute/repos/mathlib4/workspaces")
DEFAULT_OUT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.1-canonical-smoke")

TARGETS = {
    33098: "Metric.isCover_maximalSeparatedSet",
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
        "work_unit_id": f"wu:canonical-smoke:{digest[:20]}",
        "change_ids": [change_id],
        "target_sha256s": {change_id: source.target_sha256s[change_id]},
        "entity_ids_by_change": {
            change_id: source.entity_ids_by_change.get(change_id, [])
        },
        "primary_subjects_by_change": {
            change_id: source.primary_subjects_by_change[change_id]
        },
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
    digest = sha256_bytes(canonical_json_bytes({
        "treatment_version": TREATMENT_VERSION,
        **payload,
    }))
    return InvestigationTask(
        investigation_id=f"investigation:canonical-smoke:{digest[:20]}",
        source_sha256=digest,
        **payload,
    )


def _operator_run(
    task: InvestigationTask,
    operator: str,
    status: str,
    artifact_ids: Iterable[str],
    result_count: int,
    query_sha256: str | None = None,
    failure_reason: str | None = None,
) -> OperatorRun:
    payload = {
        "investigation_id": task.investigation_id,
        "operator": operator,
        "status": status,
        "query_sha256": query_sha256,
        "artifact_ids": list(artifact_ids),
        "result_count": result_count,
        "failure_reason": failure_reason,
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return OperatorRun(
        operator_run_id=f"operator-run:{digest[:24]}", source_sha256=digest, **payload
    )


def _review_opportunity(
    task: InvestigationTask,
    observed_pattern: str,
    artifact_ids: List[str],
    score: float,
    transformation: OpportunityTransformation | None,
) -> ReviewOpportunity:
    payload = {
        "investigation_id": task.investigation_id,
        "method_id": task.method_id,
        "episode_id": task.episode_id,
        "pr_number": task.pr_number,
        "primary_change_id": task.primary_change_id,
        "related_change_ids": [],
        "observed_pattern": observed_pattern,
        "proposed_transformation": (
            transformation.model_dump(mode="json") if transformation else None
        ),
        "source_artifact_ids": artifact_ids,
        "discovery_rank": 1,
        "discovery_score": score,
        "source_provenance": "automatic",
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return ReviewOpportunity(
        opportunity_id=f"opportunity:{digest[:24]}", source_sha256=digest, **payload
    )


def _render_block(
    opportunity: ReviewOpportunity,
    evidence_by_id: Dict[str, OpportunityEvidenceArtifact],
) -> str:
    evidence = "\n".join(
        f"- `{artifact_id}` [{evidence_by_id[artifact_id].kind}] "
        f"{evidence_by_id[artifact_id].source_ref}\n  {evidence_by_id[artifact_id].content}"
        for artifact_id in opportunity.source_artifact_ids
    )
    transformation = opportunity.proposed_transformation
    alternative = transformation.description if transformation else "No replacement was discovered."
    return (
        "# Automatically discovered opportunity\n"
        "Treat this record as a hypothesis, not as proof that a review request is warranted.\n\n"
        f"## Opportunity `{opportunity.opportunity_id}`\n"
        f"Method: `{opportunity.method_id}`\n"
        f"Primary change: `{opportunity.primary_change_id}`\n"
        f"Observed pattern: {opportunity.observed_pattern}\n"
        f"Proposed alternative: {alternative}\n"
        "Question: Does the retrieved API establish a valid, canonical, and review-worthy "
        "replacement for this target? Verify any proposed edit with Lean before requesting it.\n"
        f"### Evidence\n{evidence}"
    )


def _render_prompt(
    unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput,
    graph: ChangeGraph,
    opportunity: ReviewOpportunity,
    evidence_by_id: Dict[str, OpportunityEvidenceArtifact],
) -> RenderedPrompt:
    baseline = render_work_unit(unit, episode, graph)
    user = baseline.user_prompt.replace(SYSTEM_PROMPT, ADJUDICATION_SYSTEM_PROMPT, 1)
    user = user.replace(
        FACET_CHECKLIST,
        "### Adjudication context\nThis target is context for one automatically discovered "
        "canonical-API hypothesis. Do not perform an unscoped review.",
    )
    user = user.replace(
        "# PR #", _render_block(opportunity, evidence_by_id) + "\n\n# PR #", 1
    )
    system_hash = sha256_bytes(ADJUDICATION_SYSTEM_PROMPT.encode())
    user_hash = sha256_bytes(user.encode())
    prompt_hash = sha256_bytes(canonical_json_bytes({
        "system": ADJUDICATION_SYSTEM_PROMPT,
        "user": user,
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


def build_artifacts(
    parent: Path,
    phase2: Path,
    workspaces: Path,
) -> Dict[str, List]:
    episodes = load_jsonl(parent / "input/episodes.jsonl", ReviewEpisodeInput)
    graphs = load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
    units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)
    phase2_tasks = load_jsonl(phase2 / "derived/investigation_tasks.jsonl", InvestigationTask)
    registry_sha = sha256_file(phase2 / "methods.jsonl")

    graph_by_pr = {item.pr_number: item for item in graphs}
    episode_by_pr = {item.pr_number: item for item in episodes}
    output = {
        "episodes": [], "graphs": [], "units": [], "tasks": [], "declarations": [],
        "hits": [], "evidence": [], "operator_runs": [], "records": [],
        "opportunities": [], "prompts": [],
    }
    for pr_number, declaration_name in TARGETS.items():
        graph = graph_by_pr[pr_number]
        episode = episode_by_pr[pr_number]
        target = next(
            item for item in graph.targets if item.declaration_name == declaration_name
        )
        source_unit = next(item for item in units if target.change_id in item.change_ids)
        unit = _clone_unit(source_unit, target.change_id)
        source_task = next(
            item for item in phase2_tasks
            if item.method_id == "canonical_api_search.v1"
            and item.primary_change_id == target.change_id
        )
        task = _clone_task(source_task, unit, registry_sha)
        workspace = workspaces / episode.base_sha
        declarations = build_declaration_index(workspace, episode.base_sha, target.path)
        hits = rank_declarations(task, target, declarations)
        if not hits:
            raise ValueError(f"canonical retrieval returned no results for {target.change_id}")
        declaration_by_id = {item.declaration_id: item for item in declarations}
        top = hits[0]
        top_declaration = declaration_by_id[top.declaration_id]
        high_confidence = is_high_confidence_insert_separation(top, top_declaration)
        proposal = (
            propose_insert_separation_replacement(
                target.reviewed_code or target.base_code or "", top_declaration
            )
            if high_confidence
            else None
        )
        applicability = check_applicability(workspace, episode, target, proposal)

        reviewed_evidence = evidence_artifact(
            task,
            "reviewed_code",
            f"reviewed-change:{target.change_id}",
            target.reviewed_code or target.base_code or "",
            episode.reviewed_head_sha,
        )
        declaration_evidence = evidence_artifact(
            task,
            "repository_declaration",
            f"{episode.base_sha}:{top_declaration.path}:{top_declaration.line_start}",
            top_declaration.signature,
            episode.base_sha,
        )
        trace_content = "; ".join(
            f"rank={hit.rank} name={declaration_by_id[hit.declaration_id].fullname} "
            f"score={hit.score:g} already_used={str(hit.already_used).lower()} "
            f"matched={','.join(hit.matched_tokens)}"
            for hit in hits[:10]
        )
        trace_evidence = evidence_artifact(
            task,
            "retrieval_trace",
            f"canonical-retrieval:{top.query_sha256}",
            trace_content,
            episode.base_sha,
        )
        applicability_content = applicability.content
        if applicability.replacement:
            applicability_content += (
                "\nProposed replacement:\n" + applicability.replacement.new_block
            )
        applicability_evidence = evidence_artifact(
            task,
            "applicability_check" if high_confidence else "negative_control",
            f"canonical-applicability:{task.investigation_id}",
            applicability_content,
            episode.reviewed_head_sha,
        )
        evidence = [
            reviewed_evidence, declaration_evidence, trace_evidence, applicability_evidence
        ]
        if high_confidence:
            observed = (
                f"`{declaration_name}` manually reconstructs an inserted-set separation proof. "
                f"`{top_declaration.fullname}` is the top dependency-neighborhood retrieval "
                f"(score {top.score:g}) and is not used by the target."
            )
            transformation = OpportunityTransformation(
                kind="replace_reconstructed_operation",
                symbols=[top_declaration.fullname],
                description=proposal.description if proposal else (
                    f"Use `{top_declaration.fullname}` in place of the reconstructed operation."
                ),
            )
        else:
            observed = (
                f"The top canonical-API retrieval for `{declaration_name}` is "
                f"`{top_declaration.fullname}` (score {top.score:g}); it is already used by the "
                "target or does not meet the high-confidence opportunity threshold."
            )
            transformation = None
        opportunity = _review_opportunity(
            task,
            observed,
            [item.artifact_id for item in evidence],
            min(top.score / 40.0, 1.0),
            transformation,
        )
        operator_runs = [
            _operator_run(
                task, "dependency_neighborhood", "completed",
                [declaration_evidence.artifact_id], len(declarations),
            ),
            _operator_run(
                task, "type_shape_retrieval", "completed",
                [trace_evidence.artifact_id], len(hits), top.query_sha256,
            ),
            _operator_run(
                task,
                "applicability_check",
                "completed" if applicability.status in {"compiled", "failed"} or not high_confidence
                else "unavailable",
                [applicability_evidence.artifact_id],
                1 if applicability.status == "compiled" else 0,
                failure_reason=(
                    None
                    if applicability.status in {"compiled", "failed"} or not high_confidence
                    else applicability.content
                ),
            ),
        ]
        record_payload = {
            "investigation_id": task.investigation_id,
            "execution_status": "completed",
            "disposition": "opportunities",
            "operator_run_ids": [item.operator_run_id for item in operator_runs],
            "artifact_ids": [item.artifact_id for item in evidence],
            "opportunity_ids": [opportunity.opportunity_id],
            "followup_ids": [],
            "basis": (
                "A high-confidence canonical replacement was retrieved; Lean verification remains "
                "part of adjudication."
                if high_confidence
                else "The matched control is exposed for no-request adjudication because retrieval "
                "found no missing high-confidence canonical API."
            ),
            "producer": "deterministic",
        }
        record_digest = sha256_bytes(canonical_json_bytes(record_payload))
        record = InvestigationRecord(
            source_sha256=record_digest, **record_payload
        )
        evidence_by_id = {item.artifact_id: item for item in evidence}
        prompt = _render_prompt(unit, episode, graph, opportunity, evidence_by_id)

        output["episodes"].append(episode)
        output["graphs"].append(graph)
        output["units"].append(unit)
        output["tasks"].append(task)
        output["declarations"].extend(declarations)
        output["hits"].extend(hits)
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
        manifest = DatasetManifest.model_validate_json(manifest_path.read_text())
        report = json.loads((out / "derived/canonical_retrieval_report.json").read_text())
        return manifest, report
    parent_manifest = DatasetManifest.model_validate_json((parent / "manifest.json").read_text())
    rows = build_artifacts(parent, phase2, workspaces)
    methods = load_registry(phase2 / "methods.jsonl")
    registry_path = out / "methods.jsonl"
    write_once(registry_path, jsonl_bytes(methods))
    files = {
        "input/episodes.jsonl": (rows["episodes"], "episode1", "reviewer_visible_episodes"),
        "derived/change_graphs.jsonl": (rows["graphs"], "cg1", "complete_change_graphs"),
        "derived/work_units.jsonl": (rows["units"], "work-unit1", "canonical_smoke_units"),
        "derived/rendered_prompts.jsonl": (
            rows["prompts"], "rendered-prompt1", "canonical_opportunity_prompts"
        ),
        "derived/investigation_tasks.jsonl": (
            rows["tasks"], "investigation-task1", "canonical_investigation_tasks"
        ),
        "derived/repository_declarations.jsonl": (
            rows["declarations"], "repository-declaration1", "dependency_neighborhood_index"
        ),
        "derived/canonical_retrieval_hits.jsonl": (
            rows["hits"], "canonical-retrieval-hit1", "canonical_retrieval_hits"
        ),
        "derived/opportunity_evidence.jsonl": (
            rows["evidence"], "opportunity-evidence-artifact1", "opportunity_evidence"
        ),
        "derived/operator_runs.jsonl": (
            rows["operator_runs"], "operator-run1", "operator_runs"
        ),
        "derived/investigation_records.jsonl": (
            rows["records"], "investigation-record1", "investigation_records"
        ),
        "derived/opportunities.jsonl": (
            rows["opportunities"], "review-opportunity1", "automatic_review_opportunities"
        ),
    }
    refs = {}
    for relative, (records, schema, role) in files.items():
        path = out / relative
        write_once(path, jsonl_bytes(records))
        refs[relative] = artifact_ref(path, out, role, schema, len(records))
    declaration_by_id = {
        item.declaration_id: item for item in rows["declarations"]
    }
    top_hits = [item for item in rows["hits"] if item.rank == 1]
    report = {
        "schema_version": "canonical-retrieval-report1",
        "index_version": INDEX_VERSION,
        "retrieval_version": RETRIEVAL_VERSION,
        "counts": {
            "targets": len(rows["units"]),
            "declarations": len(rows["declarations"]),
            "retrieval_hits": len(rows["hits"]),
            "opportunities": len(rows["opportunities"]),
        },
        "targets": [
            {
                "pr_number": task.pr_number,
                "primary_change_id": task.primary_change_id,
                "top_declaration": declaration_by_id[hit.declaration_id].fullname,
                "top_score": hit.score,
                "top_already_used": hit.already_used,
                "high_confidence_opportunity": bool(
                    rows["opportunities"][index].proposed_transformation
                ),
                "applicability_status": rows["operator_runs"][index * 3 + 2].status,
            }
            for index, (task, hit) in enumerate(zip(rows["tasks"], top_hits))
        ],
        "source_retrieval_gate": (
            "pass"
            if declaration_by_id[top_hits[0].declaration_id].fullname
            == "Metric.isSeparated_insert_of_notMem"
            and top_hits[0].rank == 1
            and top_hits[1].already_used
            and not rows["opportunities"][1].proposed_transformation
            else "fail"
        ),
    }
    report_path = out / "derived/canonical_retrieval_report.json"
    write_once(report_path, pretty_json_bytes(report))
    report_ref = artifact_ref(
        report_path, out, "canonical_retrieval_report", "canonical-retrieval-report1", 1
    )
    registry_ref = artifact_ref(
        registry_path, out, "investigation_method_registry", "investigation-method1", len(methods)
    )
    manifest = DatasetManifest(
        dataset_id="mathlib-pr-review-v4-canonical-api-smoke",
        release="0.9.1-canonical-api-smoke",
        source_kind=parent_manifest.source_kind,
        split="development",
        sources=[
            ArtifactRef(
                path=display_path(parent / "manifest.json"),
                role="parent_stable_release",
                schema_version=parent_manifest.schema_version,
                sha256=sha256_file(parent / "manifest.json"),
                records=1,
            ),
            ArtifactRef(
                path=display_path(phase2 / "manifest.json"),
                role="parent_opportunity_treatment",
                schema_version="systematic-opportunity-treatment1",
                sha256=sha256_file(phase2 / "manifest.json"),
                records=1,
            ),
        ],
        input_artifacts=[refs["input/episodes.jsonl"]],
        derived_artifacts=[
            registry_ref,
            *[refs[key] for key in files if key.startswith("derived/")],
            report_ref,
        ],
        pr_numbers=sorted(TARGETS),
        corpus_cutoff_policy=(
            "Canonical retrieval indexes only the frozen base snapshot's target module and direct "
            "imports. Generation does not read gold, review comments, outcomes, or future code."
        ),
        generator_tree_state="unknown",
        generator_versions={
            **parent_manifest.generator_versions,
            "canonical_smoke": TREATMENT_VERSION,
            "canonical_index": INDEX_VERSION,
            "canonical_retrieval": RETRIEVAL_VERSION,
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
    manifest, report = build_release(args.parent, args.phase2, args.workspaces, args.out)
    print(json.dumps({
        "release": str(args.out),
        "manifest_sha256": sha256_file(args.out / "manifest.json"),
        "source_retrieval_gate": report["source_retrieval_gate"],
        "targets": report["targets"],
    }, indent=2))


if __name__ == "__main__":
    main()
