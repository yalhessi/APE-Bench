"""Build and evaluate the cheap manual inventory-agenda probe."""

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

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
from src.mathlib_review.agenda.render_prompts import FACET_CHECKLIST, SYSTEM_PROMPT
from src.mathlib_review.schema import (
    ArtifactRef,
    CandidateClaim,
    ChangeGraph,
    DatasetManifest,
    ManualAgendaProbeTask,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)


PROBE_VERSION = "manual-agenda-probe/1"
DEFAULT_PARENT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
DEFAULT_OUT = Path("inputs/pr_review_v4/treatments/manual-agenda-probe-0.1.1")
SOURCE_WORK_UNIT_IDS = (
    "wu:b017b7314c4bea62d8f968c3",  # PR 33098 intervention-bearing unit
    "wu:20910b2d076223021ce8926e",  # PR 33438 theorem control
)


PASS_SPECS = {
    "statement_api": {
        "title": "Statement and API investigation",
        "investigation_kinds": [
            "statement_semantics", "statement_generality", "existing_api_duplication",
            "declaration_naming", "namespace_fit", "attributes_and_documentation",
        ],
        "questions": [
            "Does the statement express the intended reusable result with appropriate assumptions?",
            "Can its types or hypotheses be generalized without weakening the intended result?",
            "Does an existing declaration or constructor already provide the same API role?",
            "Does the declaration name and namespace match its type and nearby sibling conventions?",
            "Are attributes and documentation appropriate and accurate for this public declaration?",
        ],
    },
    "proof": {
        "title": "Proof implementation investigation",
        "investigation_kinds": [
            "proof_canonicalization", "proof_simplification", "proof_robustness",
            "proof_local_style",
        ],
        "questions": [
            "Can the proof use a canonical existing lemma, tactic, or direct proof structure?",
            "Does it contain unnecessary manual case analysis, rewriting, or intermediate machinery?",
            "Does it rely on fragile elaboration details or implementation facts unnecessarily?",
            "Does its local proof structure follow the conventions used by nearby analogous proofs?",
        ],
    },
    "relational": {
        "title": "Relational and family investigation",
        "investigation_kinds": [
            "sibling_consistency", "shared_abstraction", "counterpart_completeness",
            "pr_scope_fit",
        ],
        "questions": [
            "Do the changed declarations form a family that should use consistent names and shapes?",
            "Is implementation or proof structure repeated where a shared abstraction should be used?",
            "Is a sibling or counterpart declaration missing or treated inconsistently?",
            "Do these declarations fit the stated contribution and scope of the pull request?",
        ],
    },
}


_PROBE_LEAD = """Act as a Mathlib maintainer executing one assigned investigation pass over complete
change targets. Inspect every target for the assigned questions. Other specialist passes cover other
questions, so do not substitute an easier concern outside this assignment. Predict concrete changes
a maintainer would plausibly request, not general risks, questions, defenses, or reports that a check
was performed. There is no quota: submit only actionable requests supported by the reviewed code,
and submit none when this pass finds no warranted request."""
PROBE_SYSTEM_PROMPT = _PROBE_LEAD + "\n\n" + SYSTEM_PROMPT.split("\n\n", 1)[1]


def _lifecycle(target) -> str:
    if target.base_code is None and target.reviewed_code is not None:
        return "added"
    if target.base_code is not None and target.reviewed_code is None:
        return "removed"
    if target.base_code is not None and target.reviewed_code is not None:
        return "modified"
    return "structural"


def _target_agenda(spec: Dict) -> str:
    questions = "\n".join(f"{index}. {question}" for index, question in enumerate(spec["questions"], 1))
    return (
        f"### Assigned pass for this target: {spec['title']}\n"
        "Inspect this target for every question below. Submit candidates only for concrete requests "
        "arising from this assigned pass. An empty result is valid.\n"
        f"{questions}"
    )


def _probe_prompt(
    source_prompt: RenderedPrompt,
    probe_unit: ReviewWorkUnit,
    source_unit: ReviewWorkUnit,
    graph: ChangeGraph,
    pass_id: str,
) -> RenderedPrompt:
    spec = PASS_SPECS[pass_id]
    targets = {item.change_id: item for item in graph.targets}
    inventory = "\n".join(
        f"- `{change_id}`: lifecycle={_lifecycle(targets[change_id])}; "
        f"kind={targets[change_id].declaration_kind or targets[change_id].kind}; "
        f"subject=`{source_unit.primary_subjects_by_change[change_id]}`"
        for change_id in source_unit.change_ids
    )
    treatment = (
        "# Manual inventory-agenda probe\n"
        f"Pass ID: `{pass_id}`\n"
        f"Assigned specialist: {spec['title']}\n"
        "This inventory is derived only from the review-time change graph.\n"
        f"{inventory}\n\n"
        "## Pass-level contract\n"
        "Inspect every listed target under the assigned questions. Use repository tools when they "
        "would resolve the assigned question. Do not emit no-change conclusions as candidates, and "
        "do not broaden into concerns assigned to another pass.\n\n"
    )
    user = source_prompt.user_prompt
    if SYSTEM_PROMPT not in user or FACET_CHECKLIST not in user:
        raise ValueError("source prompt does not contain the frozen baseline contract")
    user = user.replace(SYSTEM_PROMPT, PROBE_SYSTEM_PROMPT, 1)
    user = user.replace(FACET_CHECKLIST, _target_agenda(spec))
    marker = "# PR #"
    if marker not in user:
        raise ValueError("source prompt has no PR marker")
    user = user.replace(marker, treatment + marker, 1)
    system_hash = sha256_bytes(PROBE_SYSTEM_PROMPT.encode())
    user_hash = sha256_bytes(user.encode())
    prompt_hash = sha256_bytes(canonical_json_bytes({
        "system": PROBE_SYSTEM_PROMPT,
        "user": user,
    }))
    return RenderedPrompt(
        work_unit_id=probe_unit.work_unit_id,
        renderer_version=PROBE_VERSION,
        system_prompt=PROBE_SYSTEM_PROMPT,
        user_prompt=user,
        system_sha256=system_hash,
        user_sha256=user_hash,
        prompt_sha256=prompt_hash,
        rendered_chars=len(PROBE_SYSTEM_PROMPT) + len(user),
        estimated_tokens=(len(PROBE_SYSTEM_PROMPT.encode()) + len(user.encode()) + 3) // 4,
        included_change_ids=list(probe_unit.change_ids),
        omitted_change_ids=[],
    )


def build_probe_artifacts(
    units: Iterable[ReviewWorkUnit],
    prompts: Iterable[RenderedPrompt],
    graphs: Iterable[ChangeGraph],
) -> Tuple[List[ReviewWorkUnit], List[RenderedPrompt], List[ManualAgendaProbeTask]]:
    unit_by_id = {item.work_unit_id: item for item in units}
    prompt_by_id = {item.work_unit_id: item for item in prompts}
    graph_by_id = {item.graph_id: item for item in graphs}
    missing = set(SOURCE_WORK_UNIT_IDS) - set(unit_by_id)
    if missing:
        raise ValueError(f"probe source work units are missing: {sorted(missing)}")
    probe_units, probe_prompts, tasks = [], [], []
    for source_id in SOURCE_WORK_UNIT_IDS:
        source = unit_by_id[source_id]
        graph = graph_by_id[source.graph_id]
        for pass_id, spec in PASS_SPECS.items():
            identity = {
                "probe_version": PROBE_VERSION,
                "source_work_unit_sha256": source.source_sha256,
                "pass_id": pass_id,
                "investigation_kinds": spec["investigation_kinds"],
            }
            digest = sha256_bytes(canonical_json_bytes(identity))
            probe_id = f"wu:agenda-probe:{digest[:20]}"
            probe_unit = source.model_copy(update={
                "work_unit_id": probe_id,
                "renderer_version": PROBE_VERSION,
                "source_sha256": digest,
            })
            task_source = {
                "probe_work_unit_id": probe_id,
                "source_work_unit_id": source_id,
                "pass_id": pass_id,
                "investigation_kinds": spec["investigation_kinds"],
                "probe_version": PROBE_VERSION,
            }
            task_digest = sha256_bytes(canonical_json_bytes(task_source))
            task = ManualAgendaProbeTask(
                probe_work_unit_id=probe_id,
                source_work_unit_id=source_id,
                pass_id=pass_id,
                investigation_kinds=spec["investigation_kinds"],
                source_sha256=task_digest,
            )
            probe_units.append(probe_unit)
            tasks.append(task)
            probe_prompts.append(_probe_prompt(
                prompt_by_id[source_id], probe_unit, source, graph, pass_id
            ))
    return probe_units, probe_prompts, tasks


def build_probe_release(parent: Path = DEFAULT_PARENT, out: Path = DEFAULT_OUT) -> DatasetManifest:
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        return DatasetManifest.model_validate_json(manifest_path.read_text())
    parent_manifest = DatasetManifest.model_validate_json((parent / "manifest.json").read_text())
    all_units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)
    all_prompts = load_jsonl(parent / "derived/rendered_prompts.jsonl", RenderedPrompt)
    all_graphs = load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
    source_units = [item for item in all_units if item.work_unit_id in SOURCE_WORK_UNIT_IDS]
    episode_ids = {item.episode_id for item in source_units}
    graph_ids = {item.graph_id for item in source_units}
    episodes = [
        item for item in load_jsonl(parent / "input/episodes.jsonl", ReviewEpisodeInput)
        if item.episode_id in episode_ids
    ]
    graphs = [item for item in all_graphs if item.graph_id in graph_ids]
    probe_units, probe_prompts, tasks = build_probe_artifacts(all_units, all_prompts, all_graphs)
    artifacts = {
        "input/episodes.jsonl": (episodes, "episode1", "reviewer_visible_episodes"),
        "derived/change_graphs.jsonl": (graphs, "cg1", "complete_change_graphs"),
        "derived/work_units.jsonl": (probe_units, "work-unit1", "manual_agenda_probe_units"),
        "derived/rendered_prompts.jsonl": (
            probe_prompts, "rendered-prompt1", "manual_agenda_probe_prompts"
        ),
        "derived/agenda_probe_tasks.jsonl": (
            tasks, "manual-agenda-probe-task1", "manual_agenda_probe_mapping"
        ),
    }
    refs = {}
    for rel, (rows, schema, role) in artifacts.items():
        path = out / rel
        write_once(path, jsonl_bytes(rows))
        refs[rel] = ArtifactRef(
            path=rel,
            schema_version=schema,
            role=role,
            sha256=sha256_file(path),
            records=len(rows),
        )
    manifest = DatasetManifest(
        dataset_id="mathlib-pr-review-v4-manual-agenda-probe",
        release="0.1.1-manual-agenda-probe",
        source_kind=parent_manifest.source_kind,
        split="development",
        sources=[ArtifactRef(
            path=display_path(parent / "manifest.json"),
            role="parent_stable_release",
            schema_version=parent_manifest.schema_version,
            sha256=sha256_file(parent / "manifest.json"),
            records=len(SOURCE_WORK_UNIT_IDS),
        )],
        input_artifacts=[refs["input/episodes.jsonl"]],
        derived_artifacts=[refs[rel] for rel in refs if rel.startswith("derived/")],
        pr_numbers=sorted({item.pr_number for item in episodes}),
        corpus_cutoff_policy=parent_manifest.corpus_cutoff_policy,
        generator_tree_state="unknown",
        generator_versions={
            **parent_manifest.generator_versions,
            "manual_agenda_probe": PROBE_VERSION,
            "generation_prior": "none",
            "evidence": "evidence-collectors/3",
        },
        created_at="2026-07-17T00:00:00-05:00",
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def _candidate_key(candidate: CandidateClaim) -> str:
    value = {
        "episode_id": candidate.episode_id,
        "pr_number": candidate.pr_number,
        "change_ids": sorted(candidate.change_ids),
        "entity_ids": sorted(candidate.entity_ids),
        "primary_change_id": candidate.primary_change_id,
        "primary_entity_id": candidate.primary_entity_id,
        "primary_subject": candidate.primary_subject,
        "requested_change": candidate.requested_change,
        "concern_family": candidate.concern_family,
        "concern_label": candidate.concern_label,
        "severity": candidate.severity,
        "claim": candidate.claim,
        "suggested_fix": candidate.suggested_fix,
        "proposed_edit": (
            candidate.proposed_edit.model_dump(mode="json") if candidate.proposed_edit else None
        ),
    }
    return sha256_bytes(canonical_json_bytes(value))


def deduplicate_probe_candidates(
    candidates: Iterable[CandidateClaim],
) -> Tuple[List[CandidateClaim], Dict]:
    clusters: Dict[str, List[CandidateClaim]] = {}
    for candidate in candidates:
        clusters.setdefault(_candidate_key(candidate), []).append(candidate)
    selected = [
        sorted(items, key=lambda item: item.candidate_id)[0]
        for _key, items in sorted(clusters.items())
    ]
    report = {
        "schema_version": "manual-agenda-probe-merge1",
        "input_candidates": sum(len(items) for items in clusters.values()),
        "output_candidates": len(selected),
        "exact_duplicates_removed": sum(len(items) - 1 for items in clusters.values()),
        "clusters": [
            {
                "semantic_key": key,
                "candidate_ids": sorted(item.candidate_id for item in items),
                "selected_candidate_id": sorted(item.candidate_id for item in items)[0],
            }
            for key, items in sorted(clusters.items())
            if len(items) > 1
        ],
    }
    return selected, report


def compare_reports(
    probe_evaluation: Dict,
    baseline_evaluations: Iterable[Dict],
    probe_candidates: Iterable[CandidateClaim] = (),
    baseline_candidate_sets: Iterable[Iterable[CandidateClaim]] = (),
    control_pr_number: int = 33438,
) -> Dict:
    baselines = list(baseline_evaluations)
    probe_candidates = list(probe_candidates)
    baseline_candidate_sets = [list(items) for items in baseline_candidate_sets]
    if baseline_candidate_sets and len(baseline_candidate_sets) != len(baselines):
        raise ValueError("baseline candidate sets must align with baseline evaluations")
    baseline_obligations: Dict[str, Dict[str, int]] = {}
    for report in baselines:
        for item in report["semantic"]["per_obligation"]:
            counts = baseline_obligations.setdefault(
                item["obligation_id"], {"issue_hits": 0, "resolution_hits": 0}
            )
            counts["issue_hits"] += int(item["issue_hit"])
            counts["resolution_hits"] += int(item["resolution_hit"])
    probe_items = {
        item["obligation_id"]: item for item in probe_evaluation["semantic"]["per_obligation"]
    }
    if set(probe_items) != set(baseline_obligations):
        raise ValueError("probe and baseline reports use different obligation denominators")
    issue_count = sum(item["issue_hit"] for item in probe_items.values())
    if issue_count >= 5:
        verdict = "very_strong_pass"
    elif issue_count == 4:
        verdict = "strong_pass"
    elif issue_count == 3:
        verdict = "ambiguous_repeat_once"
    else:
        verdict = "fail_or_revise"
    return {
        "schema_version": "manual-agenda-probe-comparison1",
        "baseline_repetitions": len(baselines),
        "obligations": len(probe_items),
        "baseline_mean_issue_recall": (
            sum(item["semantic"]["issue_recall"] for item in baselines) / len(baselines)
        ),
        "baseline_union_issue_recall": (
            sum(item["issue_hits"] > 0 for item in baseline_obligations.values())
            / len(baseline_obligations)
        ),
        "baseline_stable_issue_recall": (
            sum(item["issue_hits"] == len(baselines) for item in baseline_obligations.values())
            / len(baseline_obligations)
        ),
        "probe_issue_recall": probe_evaluation["semantic"]["issue_recall"],
        "probe_resolution_recall": probe_evaluation["semantic"]["resolution_recall"],
        "probe_paired_candidate_issue_precision": probe_evaluation["semantic"][
            "paired_candidate_issue_precision"
        ],
        "probe_candidates": len(probe_candidates),
        "probe_raw_control_candidates": sum(
            item.pr_number == control_pr_number for item in probe_candidates
        ),
        "baseline_raw_control_candidates_per_rep": [
            sum(item.pr_number == control_pr_number for item in items)
            for items in baseline_candidate_sets
        ] or None,
        "probe_selected_control_false_finding_rate": probe_evaluation[
            "control_false_finding_rate"
        ],
        "screen_verdict": verdict,
        "per_obligation": [
            {
                "obligation_id": obligation_id,
                "baseline_issue_hit_repetitions": baseline_obligations[obligation_id]["issue_hits"],
                "baseline_resolution_hit_repetitions": baseline_obligations[obligation_id][
                    "resolution_hits"
                ],
                "probe_issue_hit": probe_items[obligation_id]["issue_hit"],
                "probe_resolution_hit": probe_items[obligation_id]["resolution_hit"],
            }
            for obligation_id in sorted(probe_items)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and evaluate the manual agenda probe")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    build.add_argument("--out", type=Path, default=DEFAULT_OUT)
    merge = subparsers.add_parser("merge-candidates")
    merge.add_argument("--input", type=Path, required=True)
    merge.add_argument("--out", type=Path, required=True)
    merge.add_argument("--report", type=Path, required=True)
    compare = subparsers.add_parser("compare")
    compare.add_argument("--probe-evaluation", type=Path, required=True)
    compare.add_argument("--probe-candidates", type=Path, required=True)
    compare.add_argument("--baseline-evaluations", type=Path, nargs="+", required=True)
    compare.add_argument("--baseline-candidates", type=Path, nargs="+", required=True)
    compare.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        manifest = build_probe_release(args.parent, args.out)
        print(json.dumps({
            "release": str(args.out),
            "release_version": manifest.release,
            "prs": manifest.pr_numbers,
            "calls": 6,
        }, indent=2))
    elif args.command == "merge-candidates":
        candidates = load_jsonl(args.input, CandidateClaim)
        merged, report = deduplicate_probe_candidates(candidates)
        write_once(args.out, jsonl_bytes(merged))
        write_once(args.report, pretty_json_bytes(report))
        print(json.dumps(report, indent=2))
    else:
        report = compare_reports(
            json.loads(args.probe_evaluation.read_text()),
            [json.loads(path.read_text()) for path in args.baseline_evaluations],
            load_jsonl(args.probe_candidates, CandidateClaim),
            [load_jsonl(path, CandidateClaim) for path in args.baseline_candidates],
        )
        write_once(args.out, pretty_json_bytes(report))
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
