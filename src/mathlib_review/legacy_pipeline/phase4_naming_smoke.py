"""Build the production semantic-subject naming-contrast smoke release."""

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
from src.mathlib_review.evidence.operators.naming_contrast import (
    POPULATION_VERSION,
    SUBJECT,
    SUBJECT_CLASSIFIER_VERSION,
    check_name_collision,
    infer_semantic_subject,
    population_counts,
    proposed_subject_name,
    scan_repository_population,
    strong_subject_prefix_norm,
)
from src.mathlib_review.opportunities.oracle import ADJUDICATION_SYSTEM_PROMPT
from src.mathlib_review.agenda.render_prompts import FACET_CHECKLIST, SYSTEM_PROMPT, render_work_unit
from src.mathlib_review.schema import (
    ArtifactRef,
    ChangeGraph,
    DatasetManifest,
    InvestigationRecord,
    InvestigationTask,
    NameCollisionResult,
    NamingPopulationMember,
    NormRecord,
    NormScope,
    OperatorRun,
    OpportunityEvidenceArtifact,
    OpportunityTransformation,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewOpportunity,
    ReviewWorkUnit,
    SemanticSubjectInference,
)


TREATMENT_VERSION = "semantic-naming-smoke/1"
DEFAULT_PARENT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
DEFAULT_PHASE2 = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1")
DEFAULT_WORKSPACES = Path("data/code_execute/repos/mathlib4/workspaces")
DEFAULT_OUT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.2-naming-smoke")

TARGETS = {
    "positive": "Metric.card_maximalSeparatedSet",
    "control": "Metric.exists_set_encard_eq_packingNumber",
}


def _clone_unit(source: ReviewWorkUnit, change_id: str, arm: str) -> ReviewWorkUnit:
    identity = {
        "treatment_version": TREATMENT_VERSION,
        "arm": arm,
        "source_work_unit_sha256": source.source_sha256,
        "change_id": change_id,
    }
    digest = sha256_bytes(canonical_json_bytes(identity))
    return source.model_copy(update={
        "work_unit_id": f"wu:naming-smoke:{digest[:20]}",
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
    source: InvestigationTask, unit: ReviewWorkUnit, registry_sha: str, arm: str
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
        "arm": arm,
        **payload,
    }))
    return InvestigationTask(
        investigation_id=f"investigation:naming-smoke:{digest[:20]}",
        source_sha256=digest,
        **payload,
    )


def _operator_run(
    task: InvestigationTask,
    operator: str,
    artifact_ids: Iterable[str],
    result_count: int,
    query_sha256: str | None = None,
) -> OperatorRun:
    payload = {
        "investigation_id": task.investigation_id,
        "operator": operator,
        "status": "completed",
        "query_sha256": query_sha256,
        "artifact_ids": list(artifact_ids),
        "result_count": result_count,
        "failure_reason": None,
    }
    digest = sha256_bytes(canonical_json_bytes(payload))
    return OperatorRun(
        operator_run_id=f"operator-run:{digest[:24]}", source_sha256=digest, **payload
    )


def _opportunity(
    task: InvestigationTask,
    observed_pattern: str,
    evidence_ids: List[str],
    transformation: OpportunityTransformation | None,
    score: float,
) -> ReviewOpportunity:
    payload = {
        "investigation_id": task.investigation_id,
        "method_id": task.method_id,
        "episode_id": task.episode_id,
        "pr_number": task.pr_number,
        "primary_change_id": task.primary_change_id,
        "related_change_ids": [],
        "observed_pattern": observed_pattern,
        "proposed_transformation": transformation.model_dump(mode="json") if transformation else None,
        "source_artifact_ids": evidence_ids,
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
    alternative = transformation.description if transformation else "No rename was discovered."
    block = (
        "# Automatically discovered naming opportunity\n"
        "Treat this record as a hypothesis, not as proof that a rename is warranted. A global token "
        "count alone is insufficient; account for semantic subject, declaration role, exceptions, "
        "and collisions.\n\n"
        f"## Opportunity `{opportunity.opportunity_id}`\n"
        f"Method: `{opportunity.method_id}`\n"
        f"Primary change: `{opportunity.primary_change_id}`\n"
        f"Observed pattern: {opportunity.observed_pattern}\n"
        f"Proposed alternative: {alternative}\n"
        "Question: Does the subject-conditioned evidence establish a collision-free, conventional, "
        "and review-worthy rename for this declaration?\n"
        f"### Evidence\n{evidence}"
    )
    baseline = render_work_unit(unit, episode, graph)
    user = baseline.user_prompt.replace(SYSTEM_PROMPT, ADJUDICATION_SYSTEM_PROMPT, 1)
    user = user.replace(
        FACET_CHECKLIST,
        "### Adjudication context\nThis target is context for one automatically discovered naming "
        "hypothesis. Do not perform an unscoped review.",
    )
    user = user.replace("# PR #", block + "\n\n# PR #", 1)
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


def build_artifacts(parent: Path, phase2: Path, workspaces: Path) -> Dict[str, List]:
    episodes = load_jsonl(parent / "input/episodes.jsonl", ReviewEpisodeInput)
    graphs = load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
    units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)
    phase2_tasks = load_jsonl(phase2 / "derived/investigation_tasks.jsonl", InvestigationTask)
    registry_sha = sha256_file(phase2 / "methods.jsonl")
    graph = next(item for item in graphs if item.pr_number == 33098)
    episode = next(item for item in episodes if item.pr_number == 33098)
    workspace = workspaces / episode.base_sha
    scan = scan_repository_population(workspace, episode.base_sha)
    counts = population_counts(scan.members)
    strong_norm = strong_subject_prefix_norm(scan.members)
    pr_fullnames = [
        target.declaration_name for target in graph.targets if target.declaration_name
    ]
    target_by_name = {
        target.declaration_name: target for target in graph.targets if target.declaration_name
    }
    output = {
        "episodes": [episode], "graphs": [graph], "units": [], "tasks": [],
        "inferences": [], "population": scan.members, "collisions": [], "norms": [],
        "evidence": [], "operator_runs": [], "records": [], "opportunities": [], "prompts": [],
    }

    positive_population_evidence_id = None
    for arm, declaration_name in TARGETS.items():
        target = target_by_name[declaration_name]
        source_unit = next(item for item in units if target.change_id in item.change_ids)
        unit = _clone_unit(source_unit, target.change_id, arm)
        source_task = next(
            item for item in phase2_tasks
            if item.method_id == "naming_contrast.v1"
            and item.primary_change_id == target.change_id
        )
        task = _clone_task(source_task, unit, registry_sha, arm)
        inference = infer_semantic_subject(task, target)
        proposed = proposed_subject_name(declaration_name, inference) if strong_norm else None
        collision = check_name_collision(
            task, declaration_name, proposed, episode.base_sha,
            scan.all_fullnames, pr_fullnames,
        )
        reviewed = evidence_artifact(
            task, "reviewed_code", f"reviewed-change:{target.change_id}",
            target.reviewed_code or target.base_code or "", episode.reviewed_head_sha,
        )
        subject_evidence = evidence_artifact(
            task, "semantic_subject", f"semantic-subject:{inference.inference_id}",
            f"subject={inference.subject}; role={inference.subject_role}; "
            f"confidence={inference.confidence}; subject_expression="
            f"{inference.subject_expression or '(role-conditioned)'}; "
            f"conclusion={inference.conclusion}",
            episode.reviewed_head_sha,
        )
        exceptions = [
            f"{member.fullname}@{member.path}:{member.line_start}"
            for member in scan.members if member.naming_form != "subject_prefix"
        ]
        examples = [
            f"{member.fullname}@{member.path}:{member.line_start}"
            for member in scan.members if member.naming_form == "subject_prefix"
        ][:12]
        population_content = (
            "population=all review-base theorem/lemma conclusions whose outer left side contains "
            f"the exact `encard` identifier; snapshot={episode.base_sha}; parsed_files="
            f"{scan.parsed_files}; parse_failures={len(scan.parse_failures)}; total={len(scan.members)}; "
            f"subject_prefix={counts['subject_prefix']}; subject_elsewhere="
            f"{counts['subject_elsewhere']}; conflicting_prefix={counts['conflicting_prefix']}; "
            f"role_specific_other={counts['role_specific_other']}; complete_population_artifact="
            "derived/naming_population.jsonl; support_examples=" + "; ".join(examples)
            + "; exceptions=" + ("; ".join(exceptions) or "none")
        )
        population_evidence = evidence_artifact(
            task, "naming_population",
            f"naming-population:{POPULATION_VERSION}:{episode.base_sha}",
            population_content, episode.base_sha,
        )
        collision_evidence = evidence_artifact(
            task,
            "name_collision" if proposed else "negative_control",
            f"name-collision:{collision.collision_id}",
            f"current={declaration_name}; proposed={proposed or '(none)'}; "
            f"repository_matches={collision.repository_matches}; pr_matches={collision.pr_matches}; "
            f"collision={str(collision.collision).lower()}",
            episode.base_sha,
        )
        evidence = [reviewed, subject_evidence, population_evidence, collision_evidence]
        if arm == "positive":
            positive_population_evidence_id = population_evidence.artifact_id
        if proposed and not collision.collision:
            transformation = OpportunityTransformation(
                kind="rename_to_semantic_subject_prefix",
                symbols=[declaration_name, proposed],
                description=(
                    f"Rename `{declaration_name}` to `{proposed}` and update all references in the "
                    "PR so the declaration's direct `Set.encard` subject is reflected in its leaf name."
                ),
            )
            observed = (
                f"`{declaration_name}` has direct left-hand subject `{SUBJECT}` but uses the "
                f"conflicting `card_` prefix. The scoped review-base population has "
                f"{counts['subject_prefix']}/{len(scan.members)} direct-subject declarations with an "
                "`encard_` leaf prefix and no `card_` examples."
            )
        else:
            transformation = None
            observed = (
                f"`{declaration_name}` has subject `{SUBJECT}` under the "
                f"`{inference.subject_role}` role and already contains `encard` in a meaningful "
                "existential declaration name; no conflicting prefix or collision-free rename was inferred."
            )
        opportunity = _opportunity(
            task, observed, [item.artifact_id for item in evidence], transformation,
            counts["subject_prefix"] / max(len(scan.members), 1),
        )
        operator_runs = [
            _operator_run(
                task, "semantic_subject_inference", [subject_evidence.artifact_id], 1,
                inference.source_sha256,
            ),
            _operator_run(
                task, "scoped_naming_statistics", [population_evidence.artifact_id],
                len(scan.members), sha256_bytes(jsonl_bytes(scan.members)),
            ),
            _operator_run(
                task, "name_collision_check", [collision_evidence.artifact_id], 1,
                collision.source_sha256,
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
                "A strong direct-subject naming contrast and collision-free rename were found."
                if transformation else
                "The same-subject role-conditioned control is exposed for no-request adjudication."
            ),
            "producer": "deterministic",
        }
        record_digest = sha256_bytes(canonical_json_bytes(record_payload))
        record = InvestigationRecord(source_sha256=record_digest, **record_payload)
        prompt = _render_prompt(
            unit, episode, graph, opportunity,
            {item.artifact_id: item for item in evidence},
        )
        output["units"].append(unit)
        output["tasks"].append(task)
        output["inferences"].append(inference)
        output["collisions"].append(collision)
        output["evidence"].extend(evidence)
        output["operator_runs"].extend(operator_runs)
        output["records"].append(record)
        output["opportunities"].append(opportunity)
        output["prompts"].append(prompt)

    norm_payload = {
        "norm_kind": "naming_pattern",
        "trigger_predicate": (
            "public theorem or lemma has Set.encard on the left side of its outer conclusion relation"
        ),
        "recommended_action": "use encard_ as the leaf declaration-name prefix",
        "scope": NormScope(
            namespace=None, subject=SUBJECT, snapshot_sha=episode.base_sha
        ).model_dump(mode="json"),
        "support_count": counts["subject_prefix"],
        "counterexample_count": counts["conflicting_prefix"] + counts["role_specific_other"],
        "counterexample_refs": [
            f"{member.fullname}@{member.path}:{member.line_start}"
            for member in scan.members
            if member.naming_form in {"conflicting_prefix", "role_specific_other"}
        ],
        "effective_before": f"snapshot:{episode.base_sha}",
        "source_artifact_ids": [positive_population_evidence_id],
        "strength": "strong_convention" if strong_norm else "weak_prior",
    }
    norm_digest = sha256_bytes(canonical_json_bytes(norm_payload))
    output["norms"].append(NormRecord(
        norm_id=f"norm:{norm_digest[:24]}", source_sha256=norm_digest, **norm_payload
    ))
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
        report = json.loads((out / "derived/naming_contrast_report.json").read_text())
        return manifest, report
    parent_manifest = DatasetManifest.model_validate_json((parent / "manifest.json").read_text())
    rows = build_artifacts(parent, phase2, workspaces)
    methods = load_registry(phase2 / "methods.jsonl")
    registry_path = out / "methods.jsonl"
    write_once(registry_path, jsonl_bytes(methods))
    files = {
        "input/episodes.jsonl": (rows["episodes"], "episode1", "reviewer_visible_episodes"),
        "derived/change_graphs.jsonl": (rows["graphs"], "cg1", "complete_change_graphs"),
        "derived/work_units.jsonl": (rows["units"], "work-unit1", "naming_smoke_units"),
        "derived/rendered_prompts.jsonl": (
            rows["prompts"], "rendered-prompt1", "naming_opportunity_prompts"
        ),
        "derived/investigation_tasks.jsonl": (
            rows["tasks"], "investigation-task1", "naming_investigation_tasks"
        ),
        "derived/semantic_subjects.jsonl": (
            rows["inferences"], "semantic-subject-inference1", "semantic_subject_inferences"
        ),
        "derived/naming_population.jsonl": (
            rows["population"], "naming-population-member1", "scoped_naming_population"
        ),
        "derived/name_collisions.jsonl": (
            rows["collisions"], "name-collision-result1", "name_collision_checks"
        ),
        "derived/norm_records.jsonl": (rows["norms"], "norm-record1", "naming_norm_records"),
        "derived/opportunity_evidence.jsonl": (
            rows["evidence"], "opportunity-evidence-artifact1", "opportunity_evidence"
        ),
        "derived/operator_runs.jsonl": (rows["operator_runs"], "operator-run1", "operator_runs"),
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
    counts = population_counts(rows["population"])
    positive, control = rows["opportunities"]
    positive_collision, control_collision = rows["collisions"]
    report = {
        "schema_version": "naming-contrast-report1",
        "subject_classifier_version": SUBJECT_CLASSIFIER_VERSION,
        "population_version": POPULATION_VERSION,
        "counts": {
            "targets": len(rows["units"]),
            "population_members": len(rows["population"]),
            **counts,
        },
        "positive": {
            "primary_change_id": positive.primary_change_id,
            "current_name": positive_collision.current_fullname,
            "proposed_name": positive_collision.proposed_fullname,
            "collision": positive_collision.collision,
            "subject_role": rows["inferences"][0].subject_role,
            "opportunity": positive.proposed_transformation is not None,
        },
        "control": {
            "primary_change_id": control.primary_change_id,
            "current_name": control_collision.current_fullname,
            "proposed_name": control_collision.proposed_fullname,
            "collision": control_collision.collision,
            "subject_role": rows["inferences"][1].subject_role,
            "opportunity": control.proposed_transformation is not None,
        },
        "offline_gate": (
            "pass"
            if strong_subject_prefix_norm(rows["population"])
            and positive.proposed_transformation is not None
            and not positive_collision.collision
            and control.proposed_transformation is None
            and rows["inferences"][1].subject_role == "role_conditioned"
            else "fail"
        ),
    }
    report_path = out / "derived/naming_contrast_report.json"
    write_once(report_path, pretty_json_bytes(report))
    report_ref = artifact_ref(
        report_path, out, "naming_contrast_report", "naming-contrast-report1", 1
    )
    registry_ref = artifact_ref(
        registry_path, out, "investigation_method_registry", "investigation-method1", len(methods)
    )
    manifest = DatasetManifest(
        dataset_id="mathlib-pr-review-v4-naming-contrast-smoke",
        release="0.9.2-naming-contrast-smoke",
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
        pr_numbers=[33098],
        corpus_cutoff_policy=(
            "Naming statistics use only theorem and lemma declarations in the frozen review-base "
            "Mathlib source tree. Generation excludes the target PR, gold, comments, and outcomes."
        ),
        generator_tree_state="unknown",
        generator_versions={
            **parent_manifest.generator_versions,
            "naming_smoke": TREATMENT_VERSION,
            "semantic_subject": SUBJECT_CLASSIFIER_VERSION,
            "naming_population": POPULATION_VERSION,
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
        "offline_gate": report["offline_gate"],
        "counts": report["counts"],
        "positive": report["positive"],
        "control": report["control"],
    }, indent=2))


if __name__ == "__main__":
    main()
