"""Build and ingest the two-PR Phase 8 residual open-review smoke."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .candidates import candidates_from_response
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
from .runs import load_candidate_responses
from .schema import (
    AdjudicationConsensus,
    ArtifactRef,
    CandidateClaim,
    ChangeGraph,
    DatasetManifest,
    ModificationRecord,
    OracleOpportunity,
    RenderedPrompt,
    ResidualCandidateVerificationArtifact,
    ResidualReviewPass,
    ReviewEpisodeInput,
    ReviewOpportunity,
    ReviewWorkUnit,
    SynthesizedFinding,
    WorthinessDecision,
)
from .synthesis import DEFAULT_OUT as PHASE8_GATE, write_gate


TREATMENT_VERSION = "phase8-residual-review/2"
DEFAULT_PARENT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
DEFAULT_PHASE2 = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1")
DEFAULT_ORACLE = Path("inputs/pr_review_v4/treatments/oracle-evidence-probe-0.2.0")
DEFAULT_CANONICAL = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.1-canonical-smoke")
DEFAULT_PHASE7 = Path("results/pr_review_v4/audits/phase7-adjudication-gate-0.1.1")
DEFAULT_CONSENSUS = Path("results/pr_review_v4/runs/phase7-canonical-redundancy-smoke-0.1.1")
DEFAULT_OUT = Path("inputs/pr_review_v4/treatments/phase8-residual-smoke-0.1.1")
TARGET_PRS = (33098, 33438)


RESIDUAL_SYSTEM_PROMPT = """Act as a Mathlib maintainer performing the residual novelty pass after
structured review methods have completed. The prompt lists the complete changed-target inventory,
the methods already applied, and findings already accepted. Inspect every inventory row, but do not
repeat, paraphrase, broaden, or create a companion to an accepted finding. Search only for a concrete
actionable concern from a genuinely uncovered issue family or interaction.

Use repository and Lean tools to inspect code when the compact inventory is insufficient. Emit no
candidate for uncertainty, a check that passed, or a merely optional alternative. Every candidate
must identify a present problem and one checkable requested transformation.

`lean_verify` is only for standalone scratch code; it cannot validate `target/...`. Use
`lean_verify_edit(path=...)` for the reviewed file and in-file edits. Correctness, proof-golf,
duplication, and generalization candidates require a complete structured `proposed_edit`.
Submission recompiles the baseline and edit, rejecting missing or failing edits.

Finish by calling submit_candidates exactly once. Each candidate has: primary_change_id,
primary_entity_id, primary_subject, change_ids, concern_family, concern_label, severity, claim,
requested_change, optional suggested_fix, optional proposed_edit, and model_confidence. Copy IDs and
subjects exactly from the inventory. An empty candidates list is valid and preferred when structured
review already covers every request-worthy issue."""


def _merge_unit(graph: ChangeGraph, units: list[ReviewWorkUnit]) -> ReviewWorkUnit:
    by_change = {
        change_id: unit for unit in units for change_id in unit.change_ids
    }
    change_ids = [item.change_id for item in graph.targets]
    missing = set(change_ids) - set(by_change)
    if missing:
        raise ValueError(f"residual unit is missing change targets: {sorted(missing)}")
    base = units[0]
    identity = {
        "treatment_version": TREATMENT_VERSION,
        "graph_sha256": graph.source_sha256,
        "source_unit_sha256s": sorted(item.source_sha256 for item in units),
        "change_ids": change_ids,
    }
    digest = sha256_bytes(canonical_json_bytes(identity))
    return ReviewWorkUnit(
        work_unit_id=f"wu:phase8-residual:{digest[:20]}",
        episode_id=graph.episode_id,
        graph_id=graph.graph_id,
        repo=graph.repo,
        pr_number=graph.pr_number,
        round_index=graph.round_index,
        change_ids=change_ids,
        target_sha256s={
            change_id: by_change[change_id].target_sha256s[change_id]
            for change_id in change_ids
        },
        entity_ids_by_change={
            change_id: by_change[change_id].entity_ids_by_change.get(change_id, [])
            for change_id in change_ids
        },
        primary_subjects_by_change={
            change_id: by_change[change_id].primary_subjects_by_change[change_id]
            for change_id in change_ids
        },
        renderer_version=TREATMENT_VERSION,
        source_sha256=digest,
    )


def _render_prompt(
    unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput,
    graph: ChangeGraph,
    inventory: list[ModificationRecord],
    findings: list[SynthesizedFinding],
    outcome_rows: list[dict],
) -> RenderedPrompt:
    inventory_by_change = {item.primary_change_id: item for item in inventory}
    target_by_change = {item.change_id: item for item in graph.targets}
    rows = []
    for index, change_id in enumerate(unit.change_ids, start=1):
        target = target_by_change[change_id]
        record = inventory_by_change[change_id]
        changed_components = [
            item.component for item in record.component_deltas if item.status != "unchanged"
        ]
        entities = target.reviewed_entity_ids or target.base_entity_ids
        rows.append(
            f"{index}. change_id=`{change_id}`; subject=`{unit.primary_subjects_by_change[change_id]}`; "
            f"entity_id=`{entities[0] if entities else 'null'}`; path={target.path}; "
            f"kind={record.subject_kind}; lifecycle={record.lifecycle}; "
            f"changed_components={','.join(changed_components) or 'none'}"
        )
    covered = [
        f"- finding=`{item.finding_id}`; methods={','.join(item.method_ids)}; "
        f"anchors={','.join(item.change_ids)}; claim={item.claim}; request={item.requested_change}"
        for item in findings
    ] or ["- none"]
    methods = [
        f"- method={item['method']}; target={item['change_id']}; disposition={item['disposition']}"
        for item in outcome_rows
    ] or ["- none"]
    user = (
        f"# Residual review contract\n{RESIDUAL_SYSTEM_PROMPT}\n\n"
        f"# PR #{episode.pr_number}: {episode.title.text or ''}\n"
        f"Description: {episode.description.text or '(unavailable)'}\n"
        f"Changed files: {', '.join(episode.changed_files)}\n"
        f"Reviewed snapshot: `{episode.reviewed_head_sha}`\n\n"
        "## Already accepted structured findings\n" + "\n".join(covered) + "\n\n"
        "## Completed structured method outcomes\n" + "\n".join(methods) + "\n\n"
        "## Complete changed-target inventory\n" + "\n".join(rows)
    )
    system_hash = sha256_bytes(RESIDUAL_SYSTEM_PROMPT.encode())
    user_hash = sha256_bytes(user.encode())
    prompt_hash = sha256_bytes(canonical_json_bytes({
        "system": RESIDUAL_SYSTEM_PROMPT, "user": user,
    }))
    return RenderedPrompt(
        work_unit_id=unit.work_unit_id,
        renderer_version=TREATMENT_VERSION,
        system_prompt=RESIDUAL_SYSTEM_PROMPT,
        user_prompt=user,
        system_sha256=system_hash,
        user_sha256=user_hash,
        prompt_sha256=prompt_hash,
        rendered_chars=len(RESIDUAL_SYSTEM_PROMPT) + len(user),
        estimated_tokens=(len(RESIDUAL_SYSTEM_PROMPT.encode()) + len(user.encode()) + 3) // 4,
        included_change_ids=list(unit.change_ids),
        omitted_change_ids=[],
        submission_verification_policy="verify_checkable_edits",
    )


def _method_outcomes(
    oracle: list[OracleOpportunity],
    canonical: list[ReviewOpportunity],
    decisions: list[WorthinessDecision],
    consensus: list[AdjudicationConsensus],
) -> list[dict]:
    disposition = {item.opportunity_id: item.review_worthiness for item in decisions}
    disposition.update({item.opportunity_id: item.final_worthiness for item in consensus})
    rows = [
        {
            "opportunity_id": item.opportunity_id,
            "pr_number": item.pr_number,
            "method": item.method,
            "change_id": item.primary_change_id,
            "disposition": disposition.get(item.opportunity_id, "unresolved"),
        }
        for item in oracle
    ]
    rows.extend({
        "opportunity_id": item.opportunity_id,
        "pr_number": item.pr_number,
        "method": item.method_id,
        "change_id": item.primary_change_id,
        "disposition": disposition.get(item.opportunity_id, "unresolved"),
    } for item in canonical)
    return sorted(rows, key=lambda item: (item["pr_number"], item["change_id"], item["method"]))


def build_release(
    parent: Path = DEFAULT_PARENT,
    out: Path = DEFAULT_OUT,
) -> DatasetManifest:
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        return DatasetManifest.model_validate_json(manifest_path.read_text())
    if not (PHASE8_GATE / "report.json").is_file():
        write_gate(PHASE8_GATE)
    parent_manifest = DatasetManifest.model_validate_json((parent / "manifest.json").read_text())
    episodes = [
        item for item in load_jsonl(parent / "input/episodes.jsonl", ReviewEpisodeInput)
        if item.pr_number in TARGET_PRS
    ]
    graphs = [
        item for item in load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
        if item.pr_number in TARGET_PRS
    ]
    source_units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)
    inventory = load_jsonl(DEFAULT_PHASE2 / "derived/modification_inventory.jsonl", ModificationRecord)
    findings = load_jsonl(PHASE8_GATE / "synthesized_findings.jsonl", SynthesizedFinding)
    residual = load_jsonl(PHASE8_GATE / "residual_review_passes.jsonl", ResidualReviewPass)
    oracle = load_jsonl(DEFAULT_ORACLE / "derived/oracle_opportunities.jsonl", OracleOpportunity)
    canonical = load_jsonl(DEFAULT_CANONICAL / "derived/opportunities.jsonl", ReviewOpportunity)
    decisions = load_jsonl(DEFAULT_PHASE7 / "worthiness_decisions.jsonl", WorthinessDecision)
    consensus = load_jsonl(DEFAULT_CONSENSUS / "adjudication_consensuses.jsonl", AdjudicationConsensus)
    outcomes = _method_outcomes(oracle, canonical, decisions, consensus)
    episode_by_id = {item.episode_id: item for item in episodes}
    units = []
    prompts = []
    for graph in sorted(graphs, key=lambda item: item.pr_number):
        unit = _merge_unit(
            graph, [item for item in source_units if item.episode_id == graph.episode_id]
        )
        units.append(unit)
        prompts.append(_render_prompt(
            unit,
            episode_by_id[graph.episode_id],
            graph,
            [item for item in inventory if item.episode_id == graph.episode_id],
            [item for item in findings if item.pr_number == graph.pr_number],
            [item for item in outcomes if item["pr_number"] == graph.pr_number],
        ))
    artifacts = {
        "input/episodes.jsonl": (episodes, "episode1", "reviewer_visible_episodes"),
        "derived/change_graphs.jsonl": (graphs, "cg1", "complete_change_graphs"),
        "derived/work_units.jsonl": (units, "work-unit1", "residual_pr_units"),
        "derived/rendered_prompts.jsonl": (prompts, "rendered-prompt1", "residual_review_prompts"),
        "derived/synthesized_findings.jsonl": (
            findings, "synthesized-finding1", "already_accepted_findings"
        ),
        "derived/residual_review_passes.jsonl": (
            residual, "residual-review-pass1", "scheduled_residual_passes"
        ),
    }
    refs = {}
    for rel, (rows, schema, role) in artifacts.items():
        path = out / rel
        write_once(path, jsonl_bytes(rows))
        refs[rel] = ArtifactRef(
            path=rel, schema_version=schema, role=role,
            sha256=sha256_file(path), records=len(rows),
        )
    manifest = DatasetManifest(
        dataset_id="mathlib-pr-review-v4-phase8-residual-smoke",
        release="0.1.1-phase8-residual-smoke",
        source_kind=parent_manifest.source_kind,
        split="development",
        sources=[
            ArtifactRef(
                path=display_path(parent / "manifest.json"), role="parent_stable_release",
                schema_version=parent_manifest.schema_version,
                sha256=sha256_file(parent / "manifest.json"), records=len(TARGET_PRS),
            ),
            ArtifactRef(
                path=display_path(PHASE8_GATE / "report.json"), role="phase8_synthesis_gate",
                schema_version="phase8-synthesis-gate-report1",
                sha256=sha256_file(PHASE8_GATE / "report.json"), records=1,
            ),
        ],
        input_artifacts=[refs["input/episodes.jsonl"]],
        derived_artifacts=[refs[rel] for rel in refs if rel.startswith("derived/")],
        pr_numbers=list(TARGET_PRS),
        corpus_cutoff_policy=(
            "Diagnostic development smoke. Prompts expose review-time inventory, method outcomes, "
            "and accepted finding text but no maintainer comments, gold obligations, or post-review outcomes."
        ),
        generator_tree_state="unknown",
        generator_versions={
            **parent_manifest.generator_versions,
            "phase8_residual_review": TREATMENT_VERSION,
        },
        created_at="2026-07-17T12:00:00-05:00",
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def ingest_run(release: Path, responses_path: Path, out: Path) -> dict:
    units = load_jsonl(release / "derived/work_units.jsonl", ReviewWorkUnit)
    prompts = load_jsonl(release / "derived/rendered_prompts.jsonl", RenderedPrompt)
    residual = load_jsonl(release / "derived/residual_review_passes.jsonl", ResidualReviewPass)
    rows = load_candidate_responses(responses_path)
    by_unit = {item.work_unit_id: item for item in units}
    policy_by_unit = {
        item.work_unit_id: item.submission_verification_policy for item in prompts
    }
    if set(policy_by_unit) != set(by_unit):
        raise ValueError("residual prompts do not cover every PR unit")
    successful = {
        row.get("work_unit_id"): row for row in rows if row.get("success")
    }
    if set(successful) != set(by_unit):
        raise ValueError("residual run requires one successful terminal response per PR unit")
    candidates = []
    verification = []
    candidates_by_pr = {}
    for work_unit_id, unit in by_unit.items():
        response = successful[work_unit_id].get("response") or {}
        generated = candidates_from_response(unit, response)
        raw_verification = [
            ResidualCandidateVerificationArtifact.model_validate(item)
            for item in response.get("verification_artifacts") or []
        ]
        for item in raw_verification:
            identity = item.model_dump(
                mode="json", exclude={"schema_version", "artifact_id", "source_sha256"}
            )
            digest = sha256_bytes(canonical_json_bytes(identity))
            if item.source_sha256 != digest or item.artifact_id != (
                f"residual-candidate-verification:{digest[:24]}"
            ):
                raise ValueError("residual verification artifact failed identity validation")
        if any(item.work_unit_id != work_unit_id for item in raw_verification):
            raise ValueError("residual verification artifact belongs to another work unit")
        if any(item.candidate_ordinal >= len(generated) for item in raw_verification):
            raise ValueError("residual verification artifact has an invalid candidate ordinal")
        artifacts_by_candidate = {
            index: [item for item in raw_verification if item.candidate_ordinal == index]
            for index in range(len(generated))
        }
        strict_verification = (
            policy_by_unit[work_unit_id] == "verify_checkable_edits"
        )
        for index, candidate in enumerate(generated):
            candidate_artifacts = artifacts_by_candidate[index]
            if strict_verification and candidate.concern_family in {
                "correctness", "proof-golf", "duplication", "generalization",
            } and candidate.proposed_edit is None:
                raise ValueError(
                    f"checkable residual candidate {index} has no structured proposed edit"
                )
            if strict_verification and candidate.proposed_edit is not None:
                stages = {item.stage: item for item in candidate_artifacts}
                if set(stages) != {"baseline", "proposed_edit"}:
                    raise ValueError(
                        f"residual candidate {index} lacks complete persisted verification"
                    )
                if not stages["proposed_edit"].success:
                    raise ValueError(
                        f"residual candidate {index} persisted a failing proposed edit"
                    )
        verification.extend(raw_verification)
        finalized = []
        residual_id = next(item.residual_id for item in residual if item.pr_number == unit.pr_number)
        for candidate in generated:
            payload = candidate.model_dump(
                mode="json", exclude={"candidate_id", "source_sha256"}
            )
            payload["investigation_id"] = residual_id
            digest = sha256_bytes(canonical_json_bytes(payload))
            finalized.append(candidate.model_copy(update={
                "candidate_id": f"candidate:residual:{digest[:20]}",
                "investigation_id": residual_id,
                "source_sha256": digest,
            }))
        candidates.extend(finalized)
        candidates_by_pr[unit.pr_number] = finalized
    terminal = []
    for item in residual:
        ids = [candidate.candidate_id for candidate in candidates_by_pr[item.pr_number]]
        payload = item.model_dump(mode="json", exclude={"residual_id", "source_sha256"})
        payload.update({
            "status": "completed",
            "candidate_ids": ids,
            "terminal_reason": (
                f"Residual pass completed with {len(ids)} candidate(s)."
            ),
        })
        digest = sha256_bytes(canonical_json_bytes(payload))
        terminal.append(ResidualReviewPass(
            residual_id=f"residual-review:{digest[:24]}", source_sha256=digest, **payload
        ))
    report = {
        "schema_version": "phase8-residual-ingest-report1",
        "complete": len(terminal) == len(units),
        "counts": {
            "pr_units": len(units),
            "terminal_passes": len(terminal),
            "candidates": len(candidates),
            "verification_artifacts": len(verification),
        },
        "candidates_by_pr": {
            str(pr): len(items) for pr, items in sorted(candidates_by_pr.items())
        },
    }
    write_once(out / "candidates.jsonl", jsonl_bytes(candidates))
    write_once(out / "verification_artifacts.jsonl", jsonl_bytes(verification))
    write_once(out / "residual_review_passes.jsonl", jsonl_bytes(terminal))
    write_once(out / "report.json", pretty_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--responses", type=Path)
    parser.add_argument("--release", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.responses:
        print(json.dumps(ingest_run(args.release, args.responses, args.out), indent=2))
    else:
        manifest = build_release(args.parent, args.out)
        print(json.dumps({
            "release": str(args.out), "pr_numbers": manifest.pr_numbers,
            "derived_artifacts": len(manifest.derived_artifacts),
        }, indent=2))


if __name__ == "__main__":
    main()
