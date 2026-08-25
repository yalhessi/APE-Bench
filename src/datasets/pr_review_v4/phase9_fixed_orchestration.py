"""Build, ingest, and evaluate the Phase 9 fixed-orchestration smoke."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Iterable, Sequence

from .candidates import candidates_from_response, ingest_responses, plan_evidence
from .io import (
    canonical_json_bytes,
    display_path,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from .phase7_adjudication import (
    AdjudicationArtifacts,
    _verification_artifact_from_raw,
    adjudicate,
    production_cases,
)
from .runs import load_candidate_responses
from .schema import (
    AdjudicationBundle,
    AdjudicationVerificationArtifact,
    ArtifactRef,
    CandidateClaim,
    ChangeGraph,
    CitedAdjudicationClaim,
    DatasetManifest,
    FixedPipelineOpportunityLedger,
    InvestigationMethod,
    InvestigationRecord,
    InvestigationTask,
    NormAssessment,
    NormRecord,
    InterventionView,
    OpportunityAdjudication,
    OpportunityEvidenceArtifact,
    OperatorRun,
    PRRelation,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewOpportunity,
    ReviewWorkUnit,
    SemanticMatch,
    TechnicalAssessment,
    JudgmentNode,
    WorthinessDecision,
)
from .semantic_judge import eligible_obligations
from .synthesis import (
    accepted_opportunity_ids,
    link_candidates,
    project_semantic_matches,
    synthesize_findings,
)


VERSION = "phase9-fixed-orchestration/1"
PARENT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
PHASE2 = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1")
SOURCE_RELEASES = (
    Path("inputs/pr_review_v4/releases/dev-pilot-0.9.1-canonical-smoke"),
    Path("inputs/pr_review_v4/releases/dev-pilot-0.9.2-naming-smoke"),
    Path("inputs/pr_review_v4/releases/dev-pilot-0.9.3-wrapper-smoke"),
)
DEFAULT_OUT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.4-fixed-smoke")


def _dedupe(rows: Iterable, key: str) -> list:
    output = {}
    for item in rows:
        identifier = getattr(item, key)
        previous = output.get(identifier)
        if previous is not None and previous != item:
            raise ValueError(f"conflicting duplicate {key}={identifier}")
        output[identifier] = item
    return [output[item] for item in sorted(output)]


def _adjudication_artifacts() -> AdjudicationArtifacts:
    output = AdjudicationArtifacts()
    for release in SOURCE_RELEASES:
        for case in production_cases(release):
            output.extend(adjudicate(case))
    return output


def _candidate_digest(candidate: CandidateClaim, **updates) -> CandidateClaim:
    candidate = candidate.model_copy(update=updates)
    payload = candidate.model_dump(mode="json", exclude={"candidate_id", "source_sha256"})
    digest = sha256_bytes(canonical_json_bytes(payload))
    return candidate.model_copy(update={
        "candidate_id": f"candidate:phase9:{digest[:20]}",
        "source_sha256": digest,
    })


def _deterministic_candidate(
    opportunity: ReviewOpportunity,
    decision: WorthinessDecision,
    task: InvestigationTask,
    unit: ReviewWorkUnit,
) -> CandidateClaim:
    transformation = opportunity.proposed_transformation
    if transformation is None:
        raise ValueError("deterministic request has no proposed transformation")
    change_id = opportunity.primary_change_id
    subject = unit.primary_subjects_by_change[change_id]
    entities = unit.entity_ids_by_change.get(change_id, [])
    family = "naming" if opportunity.method_id.startswith("naming_contrast") else "style"
    requests = plan_evidence(family, subject, transformation.description, None)
    draft = CandidateClaim(
        candidate_id="candidate:pending",
        producer="deterministic",
        investigation_id=task.investigation_id,
        opportunity_ids=[opportunity.opportunity_id],
        work_unit_id=task.work_unit_id,
        episode_id=task.episode_id,
        pr_number=task.pr_number,
        change_ids=[change_id],
        entity_ids=entities[:1],
        primary_change_id=change_id,
        primary_entity_id=entities[0] if entities else None,
        primary_subject=subject,
        requested_change=transformation.description,
        concern_family=family,
        concern_label=opportunity.method_id,
        severity="blocking" if decision.request_force == "blocking" else "advisory",
        claim=opportunity.observed_pattern,
        suggested_fix=transformation.description,
        proposed_edit=None,
        evidence_requests=requests,
        model_confidence=opportunity.discovery_score,
        source_sha256="pending",
    )
    return _candidate_digest(draft)


def _artifact_ref(path: Path, root: Path, schema: str | None, role: str, records: int) -> ArtifactRef:
    return ArtifactRef(
        path=path.relative_to(root).as_posix(), schema_version=schema, role=role,
        sha256=sha256_file(path), records=records,
    )


def build_release(out: Path = DEFAULT_OUT) -> DatasetManifest:
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        return DatasetManifest.model_validate_json(manifest_path.read_text())

    opportunities = _dedupe((
        item for release in SOURCE_RELEASES
        for item in load_jsonl(release / "derived/opportunities.jsonl", ReviewOpportunity)
    ), "opportunity_id")
    evidence = _dedupe((
        item for release in SOURCE_RELEASES
        for item in load_jsonl(release / "derived/opportunity_evidence.jsonl", OpportunityEvidenceArtifact)
    ), "artifact_id")
    tasks = _dedupe((
        item for release in SOURCE_RELEASES
        for item in load_jsonl(release / "derived/investigation_tasks.jsonl", InvestigationTask)
    ), "investigation_id")
    all_units = _dedupe((
        item for release in SOURCE_RELEASES
        for item in load_jsonl(release / "derived/work_units.jsonl", ReviewWorkUnit)
    ), "work_unit_id")
    all_prompts = _dedupe((
        item for release in SOURCE_RELEASES
        for item in load_jsonl(release / "derived/rendered_prompts.jsonl", RenderedPrompt)
    ), "work_unit_id")
    episodes = _dedupe((
        item for release in SOURCE_RELEASES
        for item in load_jsonl(release / "input/episodes.jsonl", ReviewEpisodeInput)
    ), "episode_id")
    graphs = _dedupe((
        item for release in SOURCE_RELEASES
        for item in load_jsonl(release / "derived/change_graphs.jsonl", ChangeGraph)
    ), "graph_id")
    operator_runs = _dedupe((
        item for release in SOURCE_RELEASES
        for item in load_jsonl(release / "derived/operator_runs.jsonl", OperatorRun)
    ), "operator_run_id")
    records = _dedupe((
        item for release in SOURCE_RELEASES
        for item in load_jsonl(release / "derived/investigation_records.jsonl", InvestigationRecord)
    ), "investigation_id")
    methods = load_jsonl(PHASE2 / "methods.jsonl", InvestigationMethod)

    artifacts = _adjudication_artifacts()
    decision_by_id = {item.opportunity_id: item for item in artifacts.worthiness_decisions}
    bundle_by_id = {item.opportunity_id: item for item in artifacts.bundles}
    task_by_id = {item.investigation_id: item for item in tasks}
    unit_by_id = {item.work_unit_id: item for item in all_units}
    record_by_id = {item.investigation_id: item for item in records}
    model_ids = {
        item.opportunity_id for item in artifacts.bundles
        if item.route == "redundant_adjudication"
    }
    selected_unit_ids = {
        task_by_id[item.investigation_id].work_unit_id
        for item in opportunities if item.opportunity_id in model_ids
    }
    units = [item for item in all_units if item.work_unit_id in selected_unit_ids]
    prompts = [item for item in all_prompts if item.work_unit_id in selected_unit_ids]

    ledgers = []
    for opportunity in opportunities:
        decision = decision_by_id[opportunity.opportunity_id]
        record = record_by_id[opportunity.investigation_id]
        payload = {
            "opportunity_id": opportunity.opportunity_id,
            "investigation_id": opportunity.investigation_id,
            "method_id": opportunity.method_id,
            "pr_number": opportunity.pr_number,
            "primary_change_id": opportunity.primary_change_id,
            "source_status": (
                "failed" if record.execution_status == "failed"
                else "opportunity" if record.disposition == "opportunities"
                else "checked_no_opportunity"
            ),
            "transformation_status": (
                "constructed" if opportunity.proposed_transformation else "none"
            ),
            "initial_worthiness": decision.review_worthiness,
            "adjudication_route": (
                "model" if bundle_by_id[opportunity.opportunity_id].route == "redundant_adjudication"
                else "deterministic"
            ),
            "source_artifact_ids": opportunity.source_artifact_ids,
        }
        digest = sha256_bytes(canonical_json_bytes(payload))
        ledgers.append(FixedPipelineOpportunityLedger(source_sha256=digest, **payload))

    deterministic_candidates = []
    for opportunity in opportunities:
        decision = decision_by_id[opportunity.opportunity_id]
        if decision.review_worthiness != "request":
            continue
        task = task_by_id[opportunity.investigation_id]
        deterministic_candidates.append(_deterministic_candidate(
            opportunity, decision, task, unit_by_id[task.work_unit_id]
        ))

    parent_units = load_jsonl(PARENT / "derived/work_units.jsonl", ReviewWorkUnit)
    positive_change_ids = {
        item.primary_change_id for item in opportunities
        if item.pr_number == 33098 and item.proposed_transformation is not None
    }
    matched_units = [
        item for item in parent_units
        if item.pr_number == 33098 and set(item.change_ids) & positive_change_ids
    ]
    matched_changes = {change_id for item in matched_units for change_id in item.change_ids}
    evaluation_source_scope = {
        "schema_version": "phase9-evaluation-source-scope1",
        "pr_number": 33098,
        "source_work_unit_ids": sorted(item.work_unit_id for item in matched_units),
        "change_ids": sorted(matched_changes),
    }
    evaluation_source_scope["source_sha256"] = sha256_bytes(
        canonical_json_bytes(evaluation_source_scope)
    )

    rows = {
        "input/episodes.jsonl": (episodes, "episode1", "reviewer_visible_episodes"),
        "derived/change_graphs.jsonl": (graphs, "cg1", "change_graphs"),
        "derived/work_units.jsonl": (units, "work-unit1", "model_adjudication_units"),
        "derived/rendered_prompts.jsonl": (prompts, "rendered-prompt1", "model_adjudication_prompts"),
        "derived/investigation_tasks.jsonl": (tasks, "investigation-task1", "all_method_tasks"),
        "derived/operator_runs.jsonl": (operator_runs, "operator-run1", "operator_runs"),
        "derived/investigation_records.jsonl": (records, "investigation-record1", "terminal_investigations"),
        "derived/opportunities.jsonl": (opportunities, "review-opportunity1", "all_opportunities"),
        "derived/opportunity_evidence.jsonl": (evidence, "opportunity-evidence1", "opportunity_evidence"),
        "derived/technical_assessments.jsonl": (artifacts.technical_assessments, "technical-assessment1", "initial_technical_assessments"),
        "derived/norm_records.jsonl": (artifacts.norm_records, "norm-record1", "initial_norm_records"),
        "derived/norm_assessments.jsonl": (artifacts.norm_assessments, "norm-assessment1", "initial_norm_assessments"),
        "derived/worthiness_decisions.jsonl": (artifacts.worthiness_decisions, "worthiness-decision1", "initial_worthiness"),
        "derived/cited_claims.jsonl": (artifacts.cited_claims, "cited-adjudication-claim1", "adjudication_claims"),
        "derived/adjudication_bundles.jsonl": (artifacts.bundles, "adjudication-bundle1", "adjudication_routes"),
        "derived/redundancy_requests.jsonl": (artifacts.redundancy_requests, "redundancy-request1", "model_adjudication_requests"),
        "derived/deterministic_candidates.jsonl": (deterministic_candidates, "c1", "deterministic_requests"),
        "derived/pipeline_ledger.jsonl": (ledgers, "fixed-pipeline-opportunity1", "fixed_routes"),
    }
    refs = []
    for rel, (items, schema, role) in rows.items():
        path = out / rel
        write_once(path, jsonl_bytes(items))
        refs.append(_artifact_ref(path, out, schema, role, len(items)))
    write_once(out / "methods.jsonl", jsonl_bytes(methods))
    write_once(out / "evaluation_source_scope.json", pretty_json_bytes(evaluation_source_scope))
    refs.extend([
        _artifact_ref(out / "methods.jsonl", out, "investigation-method1", "method_registry", len(methods)),
        _artifact_ref(
            out / "evaluation_source_scope.json", out,
            "phase9-evaluation-source-scope1", "gold_free_evaluation_source_scope", 1,
        ),
    ])
    parent_manifest = DatasetManifest.model_validate_json((PARENT / "manifest.json").read_text())
    manifest = DatasetManifest(
        dataset_id="mathlib-pr-review-v4-phase9-fixed-smoke",
        release="0.9.4-phase9-fixed-smoke",
        source_kind=parent_manifest.source_kind,
        split="development",
        sources=[ArtifactRef(
            path=display_path(release / "manifest.json"), role="accepted_method_smoke",
            schema_version="dataset-manifest1", sha256=sha256_file(release / "manifest.json"),
            records=1,
        ) for release in SOURCE_RELEASES],
        input_artifacts=[item for item in refs if item.path.startswith("input/")],
        derived_artifacts=[item for item in refs if not item.path.startswith("input/")],
        pr_numbers=[33098, 33438],
        corpus_cutoff_policy=(
            "Fixed composition of accepted review-time production operators. The release contains "
            "only source work-unit scope; obligation IDs are derived separately during evaluation."
        ),
        generator_tree_state="unknown",
        generator_versions={
            **parent_manifest.generator_versions,
            "phase9_fixed_orchestration": VERSION,
        },
        created_at="2026-07-17T13:00:00-05:00",
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def _validate_verification(raw: dict) -> AdjudicationVerificationArtifact:
    artifact, _repaired = _verification_artifact_from_raw(raw)
    identity = artifact.model_dump(
        mode="json", exclude={"schema_version", "artifact_id", "source_sha256"}
    )
    digest = sha256_bytes(canonical_json_bytes(identity))
    if artifact.source_sha256 != digest or artifact.artifact_id != (
        f"adjudication-verification:{digest[:24]}"
    ):
        raise ValueError("Phase 9 verification artifact failed identity validation")
    return artifact


def build_evaluation_scope(release: Path, out: Path) -> dict:
    source = json.loads((release / "evaluation_source_scope.json").read_text())
    judgments = load_jsonl(PARENT / "gold/judgments.jsonl", JudgmentNode)
    views = load_jsonl(PARENT / "gold/intervention_views.jsonl", InterventionView)
    all_pr_obligations = [
        obligation for judgment, obligation in eligible_obligations(judgments, views)
        if judgment.pr_number == source["pr_number"]
    ]
    changes = set(source["change_ids"])
    payload = {
        "schema_version": "phase9-evaluation-scope1",
        "pr_number": source["pr_number"],
        "source_work_unit_ids": source["source_work_unit_ids"],
        "obligation_ids": sorted(
            item.obligation_id for item in all_pr_obligations
            if set(item.change_ids) & changes
        ),
        "full_pr_obligation_ids": sorted(item.obligation_id for item in all_pr_obligations),
    }
    payload["source_sha256"] = sha256_bytes(canonical_json_bytes(payload))
    write_once(out, pretty_json_bytes(payload))
    return payload


def ingest_repetition(release: Path, responses: Path, out: Path) -> dict:
    units = load_jsonl(release / "derived/work_units.jsonl", ReviewWorkUnit)
    tasks = load_jsonl(release / "derived/investigation_tasks.jsonl", InvestigationTask)
    opportunities = load_jsonl(release / "derived/opportunities.jsonl", ReviewOpportunity)
    deterministic = load_jsonl(release / "derived/deterministic_candidates.jsonl", CandidateClaim)
    rows = load_candidate_responses(responses)
    by_unit = {item.work_unit_id: item for item in units}
    successful = {item.get("work_unit_id"): item for item in rows if item.get("success")}
    if set(successful) != set(by_unit):
        raise ValueError("Phase 9 repetition requires one successful response per model unit")
    task_by_unit = {item.work_unit_id: item for item in tasks}
    task_by_investigation = {item.investigation_id: item for item in tasks}
    opportunity_by_unit = {
        task_by_investigation[item.investigation_id].work_unit_id: item
        for item in opportunities
        if task_by_investigation[item.investigation_id].work_unit_id in by_unit
    }
    if set(opportunity_by_unit) != set(by_unit):
        raise ValueError("Phase 9 model units must each map to exactly one opportunity")

    model_candidates = []
    adjudications = []
    verification = []
    for work_unit_id, unit in by_unit.items():
        opportunity = opportunity_by_unit[work_unit_id]
        response = successful[work_unit_id].get("response") or {}
        decisions = [
            item for item in response.get("adjudications") or []
            if item.get("opportunity_id") == opportunity.opportunity_id
        ]
        if len(decisions) != 1:
            raise ValueError("Phase 9 response must adjudicate its frozen opportunity exactly once")
        raw = decisions[0]
        generated = candidates_from_response(unit, response)
        ordinal = raw.get("candidate_ordinal")
        candidate = None
        if ordinal is not None:
            if ordinal >= len(generated):
                raise ValueError("Phase 9 adjudication has an invalid candidate ordinal")
            task = task_by_unit[work_unit_id]
            candidate = _candidate_digest(
                generated[ordinal], investigation_id=task.investigation_id,
                opportunity_ids=[opportunity.opportunity_id],
            )
            model_candidates.append(candidate)
        if raw["disposition"] == "request" and candidate is None:
            raise ValueError("Phase 9 request has no candidate")
        if raw["disposition"] != "request" and candidate is not None:
            raise ValueError("Phase 9 non-request carries a candidate")
        artifacts = [
            _validate_verification(item) for item in response.get("verification_artifacts") or []
            if item.get("opportunity_id") == opportunity.opportunity_id
        ]
        if candidate is not None and raw["disposition"] == "request":
            if candidate.proposed_edit is None:
                raise ValueError("Phase 9 canonical/wrapper request lacks a structured edit")
            if not artifacts:
                raise ValueError("Phase 9 edited candidate lacks persisted Lean verification")
        verification.extend(artifacts)
        payload = {
            "opportunity_id": opportunity.opportunity_id,
            "work_unit_id": work_unit_id,
            "disposition": raw["disposition"],
            "validity": raw["validity"],
            "norm_strength": raw["norm_strength"],
            "review_worthiness": raw["review_worthiness"],
            "evidence_ids": list(dict.fromkeys(raw.get("evidence_ids") or [])),
            "rationale": raw["rationale"],
            "candidate_id": candidate.candidate_id if candidate else None,
            "producer": "model",
        }
        digest = sha256_bytes(canonical_json_bytes(payload))
        adjudications.append(OpportunityAdjudication(
            adjudication_id=f"opportunity-adjudication:{digest[:24]}",
            source_sha256=digest, **payload,
        ))

    candidates = [*deterministic, *model_candidates]
    report = {
        "schema_version": "phase9-repetition-ingest-report1",
        "complete": len(adjudications) == len(units),
        "counts": {
            "model_units": len(units),
            "adjudications": len(adjudications),
            "deterministic_candidates": len(deterministic),
            "model_candidates": len(model_candidates),
            "candidates": len(candidates),
            "verification_artifacts": len(verification),
        },
        "dispositions": {
            item.opportunity_id: item.disposition for item in adjudications
        },
    }
    write_once(out / "opportunity_adjudications.jsonl", jsonl_bytes(adjudications))
    write_once(out / "verification_artifacts.jsonl", jsonl_bytes(verification))
    write_once(out / "candidates.jsonl", jsonl_bytes(candidates))
    write_once(out / "report.json", pretty_json_bytes(report))
    return report


def build_baseline_union(
    release: Path, primary_responses: Path, extension_responses: Path, out: Path,
) -> dict:
    """Combine one frozen holistic sample with its missing matched-scope work unit."""

    source_scope = json.loads((release / "evaluation_source_scope.json").read_text())
    units = load_jsonl(PARENT / "derived/work_units.jsonl", ReviewWorkUnit)
    unit_by_id = {item.work_unit_id: item for item in units}
    matched_ids = set(source_scope["source_work_unit_ids"])
    control_ids = {item.work_unit_id for item in units if item.pr_number == 33438}
    selected_ids = matched_ids | control_ids
    rows = [
        row
        for path in (primary_responses, extension_responses)
        for row in load_candidate_responses(path)
    ]
    selected_rows = [item for item in rows if item.get("work_unit_id") in selected_ids]
    counts = {work_unit_id: 0 for work_unit_id in selected_ids}
    for item in selected_rows:
        counts[item["work_unit_id"]] += 1
    if any(value != 1 for value in counts.values()):
        raise ValueError(f"baseline union requires one response per selected unit: {counts}")
    selected_units = [unit_by_id[item] for item in sorted(selected_ids)]
    candidates = ingest_responses(selected_units, selected_rows)
    report = {
        "schema_version": "phase9-baseline-union-report1",
        "complete": True,
        "source_work_unit_ids": sorted(matched_ids),
        "control_work_unit_ids": sorted(control_ids),
        "positive_model_calls": len(matched_ids),
        "control_model_calls": len(control_ids),
        "candidates": len(candidates),
    }
    write_once(out / "candidates.jsonl", jsonl_bytes(candidates))
    write_once(out / "report.json", pretty_json_bytes(report))
    return report


def _accepted_for_repetition(release: Path, adjudications: Sequence[OpportunityAdjudication]) -> set[str]:
    decisions = load_jsonl(release / "derived/worthiness_decisions.jsonl", WorthinessDecision)
    accepted = accepted_opportunity_ids(decisions)
    for item in adjudications:
        if item.disposition == "request" and item.validity == "valid" and item.review_worthiness in {
            "blocking", "advisory",
        }:
            accepted.add(item.opportunity_id)
        else:
            accepted.discard(item.opportunity_id)
    return accepted


def finalize_repetition(release: Path, ingested: Path, semantic: Path, out: Path) -> dict:
    candidates = load_jsonl(ingested / "candidates.jsonl", CandidateClaim)
    adjudications = load_jsonl(ingested / "opportunity_adjudications.jsonl", OpportunityAdjudication)
    opportunities = load_jsonl(release / "derived/opportunities.jsonl", ReviewOpportunity)
    tasks = load_jsonl(release / "derived/investigation_tasks.jsonl", InvestigationTask)
    relations = load_jsonl(PHASE2 / "derived/pr_relations.jsonl", PRRelation)
    matches = load_jsonl(semantic / "matches.jsonl", SemanticMatch)
    semantic_report = json.loads((semantic / "report.json").read_text())
    accepted = _accepted_for_repetition(release, adjudications)
    links = link_candidates(
        candidates, production_opportunities=opportunities,
        investigation_tasks=tasks, relations=relations,
    )
    scores = {
        item.opportunity_id: 5.0 + len(item.source_artifact_ids) / 100.0
        for item in opportunities if item.opportunity_id in accepted
    }
    findings, decisions = synthesize_findings(candidates, links, accepted, relations, scores)
    projections = project_semantic_matches(findings, matches)

    scope_path = semantic / "evaluation_scope.json"
    if not scope_path.is_file():
        raise ValueError(f"semantic directory is missing Phase 9 evaluation scope: {scope_path}")
    scope = json.loads(scope_path.read_text())
    judgments = load_jsonl(PARENT / "gold/judgments.jsonl", JudgmentNode)
    views = load_jsonl(PARENT / "gold/intervention_views.jsonl", InterventionView)
    obligations = {
        item.obligation_id: item for judgment, item in eligible_obligations(judgments, views)
        if judgment.pr_number == scope["pr_number"]
    }
    opportunity_by_id = {item.opportunity_id: item for item in opportunities}
    adjudication_by_id = {item.opportunity_id: item for item in adjudications}
    issue_candidate_pairs = {
        (item.candidate_id, item.obligation_id) for item in matches if item.issue_match
    }
    issue_finding_pairs = {
        (item.finding_id, item.obligation_id) for item in projections if item.issue_match
    }
    findings_by_candidate = {
        candidate_id: finding.finding_id
        for finding in findings for candidate_id in finding.source_candidate_ids
    }
    attributions = []
    for obligation_id in scope["full_pr_obligation_ids"]:
        obligation = obligations[obligation_id]
        overlapping_opportunities = [
            item for item in opportunities
            if item.pr_number == scope["pr_number"]
            # Related changes are evidence context, not additional issue anchors.
            and item.primary_change_id in set(obligation.change_ids)
        ]
        overlapping_candidates = [
            item for item in candidates
            if item.pr_number == scope["pr_number"]
            and set(obligation.change_ids) & set(item.change_ids)
        ]
        matched_candidate_ids = [
            item.candidate_id for item in overlapping_candidates
            if (item.candidate_id, obligation_id) in issue_candidate_pairs
        ]
        if any(
            (findings_by_candidate.get(item), obligation_id) in issue_finding_pairs
            for item in matched_candidate_ids
        ):
            stage = "recovered"
        elif matched_candidate_ids:
            stage = "synthesis"
        elif overlapping_candidates:
            stage = "candidate_semantics"
        elif any(item.opportunity_id in accepted for item in overlapping_opportunities):
            stage = "candidate_construction"
        elif overlapping_opportunities:
            transformed = [item for item in overlapping_opportunities if item.proposed_transformation]
            routed = [
                adjudication_by_id.get(item.opportunity_id)
                for item in transformed if item.opportunity_id in adjudication_by_id
            ]
            stage = "worthiness" if transformed and routed else "transformation"
        else:
            stage = "source_retrieval"
        attributions.append({
            "obligation_id": obligation_id,
            "in_matched_scope": obligation_id in scope["obligation_ids"],
            "stage": stage,
            "opportunity_ids": [item.opportunity_id for item in overlapping_opportunities],
            "candidate_ids": [item.candidate_id for item in overlapping_candidates],
            "issue_candidate_ids": matched_candidate_ids,
        })

    control_findings = sum(item.pr_number == 33438 for item in findings)
    report = {
        "schema_version": "phase9-repetition-report1",
        "complete": (
            len(attributions) == len(scope["full_pr_obligation_ids"])
            and control_findings == 0
        ),
        "semantic": semantic_report,
        "counts": {
            "candidates": len(candidates),
            "accepted_opportunities": len(accepted),
            "links": len(links),
            "findings": len(findings),
            "control_findings": control_findings,
            "matched_obligations": len(scope["obligation_ids"]),
            "full_pr_obligations": len(scope["full_pr_obligation_ids"]),
        },
        "stage_counts": {
            stage: sum(item["stage"] == stage for item in attributions)
            for stage in sorted({item["stage"] for item in attributions})
        },
    }
    write_once(out / "candidate_opportunity_links.jsonl", jsonl_bytes(links))
    write_once(out / "synthesized_findings.jsonl", jsonl_bytes(findings))
    write_once(out / "synthesis_decisions.jsonl", jsonl_bytes(decisions))
    write_once(out / "match_projections.jsonl", jsonl_bytes(projections))
    write_once(out / "miss_attributions.jsonl", jsonl_bytes(attributions))
    write_once(out / "report.json", pretty_json_bytes(report))
    return report


def aggregate_reports(
    repetition_reports: Sequence[Path], baseline_reports: Sequence[Path], out: Path,
    fixed_costs: Sequence[float] = (), baseline_positive_costs: Sequence[float] = (),
    baseline_control_costs: Sequence[float] = (),
) -> dict:
    if len(repetition_reports) != 3 or len(baseline_reports) != 3:
        raise ValueError("Phase 9 aggregate requires exactly three fixed and three baseline reports")
    fixed = [json.loads(path.read_text()) for path in repetition_reports]
    baseline = [json.loads(path.read_text()) for path in baseline_reports]

    def metric(rows, name):
        values = [item["semantic"].get(name) if "semantic" in item else item.get(name) for item in rows]
        return mean(value for value in values if value is not None)

    fixed_issue = metric(fixed, "issue_recall")
    fixed_resolution = metric(fixed, "resolution_recall")
    baseline_issue = metric(baseline, "issue_recall")
    baseline_resolution = metric(baseline, "resolution_recall")

    obligation_ids = sorted({
        item["obligation_id"]
        for row in fixed for item in row["semantic"].get("per_obligation", [])
    } | {
        item["obligation_id"]
        for row in baseline for item in row.get("per_obligation", [])
    })

    def obligation_hits(rows, obligation_id, key, nested):
        reports = [row["semantic"] if nested else row for row in rows]
        return sum(
            item.get(key, False)
            for report in reports for item in report.get("per_obligation", [])
            if item["obligation_id"] == obligation_id
        )

    per_obligation = [{
        "obligation_id": obligation_id,
        "fixed_issue_hits": obligation_hits(fixed, obligation_id, "issue_hit", True),
        "fixed_resolution_hits": obligation_hits(fixed, obligation_id, "resolution_hit", True),
        "baseline_issue_hits": obligation_hits(baseline, obligation_id, "issue_hit", False),
        "baseline_resolution_hits": obligation_hits(
            baseline, obligation_id, "resolution_hit", False
        ),
    } for obligation_id in obligation_ids]

    def candidate_pressure(paths, fixed_run):
        totals = []
        controls = []
        accepted_opportunities = []
        for path in paths:
            run_dir = path.parent.parent
            candidate_path = (
                run_dir / "ingested/candidates.jsonl" if fixed_run
                else run_dir / "candidates.jsonl"
            )
            if not candidate_path.is_file():
                continue
            candidates = load_jsonl(candidate_path, CandidateClaim)
            totals.append(len(candidates))
            controls.append(sum(item.pr_number == 33438 for item in candidates))
            accepted_opportunities.append(sorted({
                opportunity_id for item in candidates for opportunity_id in item.opportunity_ids
            }))
        return {
            "raw_candidates_by_repetition": totals,
            "raw_control_candidates_by_repetition": controls,
            "accepted_opportunity_ids_by_repetition": accepted_opportunities,
        }

    fixed_pressure = candidate_pressure(repetition_reports, True)
    baseline_pressure = candidate_pressure(baseline_reports, False)
    report = {
        "schema_version": "phase9-fixed-orchestration-report1",
        "implementation_ready": all(item.get("complete") for item in fixed) and all(
            item["counts"]["control_findings"] == 0 for item in fixed
        ),
        "repetitions": 3,
        "fixed": {
            "mean_issue_recall": fixed_issue,
            "mean_resolution_recall": fixed_resolution,
            "mean_paired_precision": metric(fixed, "paired_candidate_issue_precision"),
            **fixed_pressure,
        },
        "call_matched_baseline_union": {
            "mean_issue_recall": baseline_issue,
            "mean_resolution_recall": baseline_resolution,
            "mean_paired_precision": metric(baseline, "paired_candidate_issue_precision"),
            **baseline_pressure,
        },
        "descriptive_deltas": {
            "issue_recall": fixed_issue - baseline_issue,
            "resolution_recall": fixed_resolution - baseline_resolution,
        },
        "cost": {
            "fixed_by_repetition": list(fixed_costs),
            "baseline_positive_by_repetition": list(baseline_positive_costs),
            "baseline_control_by_repetition": list(baseline_control_costs),
            "mean_fixed": mean(fixed_costs) if fixed_costs else None,
            "mean_baseline_positive": (
                mean(baseline_positive_costs) if baseline_positive_costs else None
            ),
            "mean_baseline_with_control": (
                mean([
                    positive + control
                    for positive, control in zip(
                        baseline_positive_costs, baseline_control_costs, strict=True
                    )
                ])
                if baseline_positive_costs and baseline_control_costs else None
            ),
        },
        "stage_counts_by_repetition": [item["stage_counts"] for item in fixed],
        "per_obligation": per_obligation,
        "stable_issue_hits_at_least_two_of_three": {
            "fixed": sum(item["fixed_issue_hits"] >= 2 for item in per_obligation),
            "baseline": sum(item["baseline_issue_hits"] >= 2 for item in per_obligation),
        },
        "decision": (
            "implementation_ready_for_broader_pilot"
            if all(item.get("complete") for item in fixed)
            else "repair_orchestration_before_expansion"
        ),
    }
    write_once(out / "report.json", pretty_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ingest = sub.add_parser("ingest")
    ingest.add_argument("--release", type=Path, default=DEFAULT_OUT)
    ingest.add_argument("--responses", type=Path, required=True)
    ingest.add_argument("--out", type=Path, required=True)
    scope = sub.add_parser("scope")
    scope.add_argument("--release", type=Path, default=DEFAULT_OUT)
    scope.add_argument("--out", type=Path, required=True)
    baseline = sub.add_parser("baseline-union")
    baseline.add_argument("--release", type=Path, default=DEFAULT_OUT)
    baseline.add_argument("--primary-responses", type=Path, required=True)
    baseline.add_argument("--extension-responses", type=Path, required=True)
    baseline.add_argument("--out", type=Path, required=True)
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--release", type=Path, default=DEFAULT_OUT)
    finalize.add_argument("--ingested", type=Path, required=True)
    finalize.add_argument("--semantic", type=Path, required=True)
    finalize.add_argument("--out", type=Path, required=True)
    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--repetition-report", type=Path, action="append", required=True)
    aggregate.add_argument("--baseline-report", type=Path, action="append", required=True)
    aggregate.add_argument("--fixed-cost", type=float, action="append", default=[])
    aggregate.add_argument("--baseline-positive-cost", type=float, action="append", default=[])
    aggregate.add_argument("--baseline-control-cost", type=float, action="append", default=[])
    aggregate.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        manifest = build_release(args.out)
        print(json.dumps({"release": str(args.out), "pr_numbers": manifest.pr_numbers}, indent=2))
    elif args.command == "ingest":
        print(json.dumps(ingest_repetition(args.release, args.responses, args.out), indent=2))
    elif args.command == "scope":
        print(json.dumps(build_evaluation_scope(args.release, args.out), indent=2))
    elif args.command == "baseline-union":
        print(json.dumps(build_baseline_union(
            args.release, args.primary_responses, args.extension_responses, args.out
        ), indent=2))
    elif args.command == "finalize":
        print(json.dumps(finalize_repetition(
            args.release, args.ingested, args.semantic, args.out
        ), indent=2))
    else:
        print(json.dumps(aggregate_reports(
            args.repetition_report, args.baseline_report, args.out,
            args.fixed_cost, args.baseline_positive_cost, args.baseline_control_cost,
        ), indent=2))


if __name__ == "__main__":
    main()
