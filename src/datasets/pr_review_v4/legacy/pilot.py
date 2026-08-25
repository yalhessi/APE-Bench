"""Build the frozen, treatment-neutral nine-PR v4 development smoke release."""

import argparse
import json
from pathlib import Path

from ..io import (
    canonical_json_bytes,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from ..render_prompts import render_all
from ..retrieval import (
    PROMPT_PRECEDENT_CORPUS_VERSION,
    build_prompt_precedents,
    build_retrieval_cutoffs,
    load_reviewer_roster,
)
from ..schema import (
    ArtifactRef, ChangeGraph, DatasetManifest, InterventionScopeMigration, InterventionView,
    JudgmentNode, OutcomeObservation, PilotCase, ReviewEpisodeBoundary, ReviewEpisodeInput,
    ReviewRoundSegment, SourceEvent,
)
from ..work_units import RENDERER_VERSION, build_work_units
from ..paths import LEGACY_V2_ROSTER


PILOT_CASES = {
    33066: ("intervention", ["duplication", "docs", "style"],
            "Mixed repository-evidence and local-style judgments in one compact PR."),
    33057: ("intervention", ["correctness", "blocking", "local-semantics"],
            "Focused blocking correctness case tests judgment without broad PR-size confounding."),
    33098: ("intervention", ["proof-golf", "multi-obligation"],
            "Several same-label obligations test candidate breadth and intervention aggregation."),
    33117: ("intervention", ["duplication", "repository-search"],
            "Focused duplication case exercises external repository evidence."),
    33305: ("intervention", ["style", "blocking", "structural-target"],
            "Blocking style case exercises a target not reducible to proof compilation."),
    33421: ("intervention", ["naming", "generalization", "duplication", "retrieval"],
            "Cross-facet case tests local judgment, repository search, and precedent ablation."),
    33304: ("control", ["approved", "documentation", "no-revision"],
            "Approved documentation PR with no recorded actionable comment or revision."),
    33315: ("control", ["approved", "documentation", "no-revision"],
            "Second approved documentation PR guards against memorizing one control shape."),
    33438: ("control", ["approved", "theorem", "no-revision"],
            "Approved theorem PR controls false findings on substantive Lean code."),
}
MEDIUM_CASES = {
    **PILOT_CASES,
    33149: ("intervention", ["correctness", "policy", "duplication"],
            "Only correctness-rich PR: no-axioms policy and existing-Parseval duplication test "
            "policy routing beyond compile failures."),
    33362: ("intervention", ["scope", "namespace-placement"],
            "Adopted namespace-placement ask is the scope family's cleanest case."),
    33145: ("intervention", ["duplication", "style", "multi-anchor", "synthesis"],
            "Dualization sibling-lemma family: one judgment across sibling anchors tests "
            "propagation and synthesis retention."),
    33337: ("intervention", ["naming"],
            "Adopted toLinearMap_ prefix renames give naming a case that did not motivate "
            "the naming_contrast operator."),
    33321: ("intervention", ["docs", "style", "dropped-outcome"],
            "Docs-heavy PR with dropped asks calibrates review-worthiness against requests "
            "authors ignored."),
    33294: ("intervention", ["naming", "style", "size-stress"],
            "Largest change surface in the corpus (51 sites) stresses batching and context "
            "assembly."),
    33285: ("intervention", ["proof-golf"],
            "Knowledge-frontier proof golf outside 33098; non-motivating case for historical "
            "transformation methods."),
}
CASE_REGISTRIES = {"pilot": PILOT_CASES, "medium": MEDIUM_CASES}
CONTROL_SEMANTICS = (
    "The review episode ended APPROVED, merged, and has no recorded actionable review comment or "
    "near/total revision in the frozen v2 outcome reference. This is a negative-pressure control, "
    "not proof that every possible advisory comment would be invalid."
)
REVIEWER_ROSTER = LEGACY_V2_ROSTER


def _case(pr_number, episode_ids, kind, facets, rationale):
    payload = {"pr_number": pr_number, "episode_ids": episode_ids, "case_kind": kind,
               "target_facets": facets, "rationale": rationale,
               "control_semantics": CONTROL_SEMANTICS if kind == "control" else None}
    return PilotCase(source_sha256=sha256_bytes(canonical_json_bytes(payload)), **payload)


def build_pilot(
    parent: Path,
    out: Path,
    treatment: str = "baseline",
    release: str = "0.9.0-pilot-stable",
    cases: dict = None,
    dataset_id: str = "mathlib-pr-review-v4-dev-smoke",
    created_at: str = "2026-07-14T00:00:00-05:00",
) -> DatasetManifest:
    if treatment not in {"baseline", "temporal_precedents"}:
        raise ValueError(f"unknown prompt treatment: {treatment}")
    cases_registry = PILOT_CASES if cases is None else cases
    wanted = set(cases_registry)
    episodes = [item for item in load_jsonl(parent / "input/episodes.jsonl", ReviewEpisodeInput)
                if item.pr_number in wanted and item.round_index == 1]
    graphs = [item for item in load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
              if item.pr_number in wanted and item.round_index == 1]
    if {item.pr_number for item in episodes} != wanted or {item.pr_number for item in graphs} != wanted:
        raise ValueError("pilot selection is not fully represented by round-one episodes and graphs")
    renderer_version = RENDERER_VERSION if treatment == "baseline" else "candidate-prompt/10"
    units = build_work_units(graphs, renderer_version=renderer_version)
    all_events = load_jsonl(parent / "source/events.jsonl", SourceEvent)
    segments = [
        item for item in load_jsonl(parent / "derived/round_segments.jsonl", ReviewRoundSegment)
        if item.episode_id in {episode.episode_id for episode in episodes}
    ]
    retrieval_cutoffs = build_retrieval_cutoffs(segments) if treatment == "temporal_precedents" else []
    precedents = (build_prompt_precedents(
        units, graphs, retrieval_cutoffs, all_events, load_reviewer_roster(REVIEWER_ROSTER)
    ) if treatment == "temporal_precedents" else [])
    prompts = render_all(units, episodes, graphs, precedents)
    events = [item for item in all_events
              if item.pr_number in wanted]
    boundaries = [item for item in load_jsonl(parent / "gold/episode_boundaries.jsonl", ReviewEpisodeBoundary)
                  if item.episode_id in {episode.episode_id for episode in episodes}]
    judgments = [item for item in load_jsonl(parent / "gold/judgments.jsonl", JudgmentNode)
                 if item.pr_number in wanted]
    judgment_ids = {item.judgment_id for item in judgments}
    views = [item for item in load_jsonl(parent / "gold/intervention_views.jsonl", InterventionView)
             if judgment_ids.intersection(item.judgment_ids)]
    outcomes = [item for item in load_jsonl(parent / "gold/outcome_observations.jsonl", OutcomeObservation)
                if item.judgment_id in judgment_ids]
    migrations = [item for item in load_jsonl(parent / "gold/intervention_scope_migrations.jsonl",
                                          InterventionScopeMigration) if item.pr_number in wanted]
    cases = [_case(pr, [item.episode_id for item in episodes if item.pr_number == pr],
                   *cases_registry[pr])
             for pr in sorted(wanted)]
    artifacts = {
        "source/events.jsonl": (events, "event1", "raw_event_index"),
        "input/episodes.jsonl": (episodes, "episode1", "reviewer_visible_episodes"),
        "derived/change_graphs.jsonl": (graphs, "cg1", "complete_change_graphs"),
        "derived/work_units.jsonl": (units, "work-unit1", "candidate_work_units"),
        "derived/rendered_prompts.jsonl": (prompts, "rendered-prompt1", "production_prompt_preview"),
        "gold/judgments.jsonl": (judgments, "jg1", "hidden_judgments"),
        "gold/intervention_views.jsonl": (views, "view1", "hidden_intervention_views"),
        "gold/outcome_observations.jsonl": (outcomes, "outcome-observation1", "hidden_outcomes"),
        "gold/intervention_scope_migrations.jsonl": (migrations, "i5-cg1-map1", "hidden_scope_maps"),
        "gold/pilot_cases.jsonl": (cases, "pilot-case1", "pilot_case_semantics"),
        "gold/episode_boundaries.jsonl": (boundaries, "episode-boundary1", "hidden_episode_boundaries"),
    }
    if treatment == "temporal_precedents":
        artifacts.update({
            "derived/retrieval_cutoffs.jsonl": (
                retrieval_cutoffs, "retrieval-cutoff1", "generation_safe_review_start_cutoffs"
            ),
            "derived/prompt_precedents.jsonl": (
                precedents, "prompt-precedent1", "temporally_prior_maintainer_asks"
            ),
        })
    for rel, (rows, _schema, _role) in artifacts.items():
        write_once(out / rel, jsonl_bytes(rows))
    refs = {rel: ArtifactRef(path=rel, schema_version=schema, role=role,
                             sha256=sha256_file(out / rel), records=len(rows))
            for rel, (rows, schema, role) in artifacts.items()}
    parent_manifest = DatasetManifest.model_validate_json((parent / "manifest.json").read_text())
    versions = dict(parent_manifest.generator_versions)
    versions.update({"pilot": "pilot/2", "work_units": "work-units/1",
                     "renderer": renderer_version, "candidate_contract": "grounded-ask/1",
                     "generation_prior": (
                         "none" if treatment == "baseline" else "temporal-maintainer-asks/1"
                     ),
                     "deterministic_discovery": "compile-style/1",
                     "evidence": "evidence-collectors/2"})
    if treatment == "temporal_precedents":
        versions["prompt_retrieval"] = PROMPT_PRECEDENT_CORPUS_VERSION
    sources = [
        ArtifactRef(path=str(parent), role="parent_release", schema_version="pr4-manifest-1",
                    sha256=sha256_file(parent / "manifest.json"), records=len(wanted)),
    ]
    if treatment == "temporal_precedents":
        sources.extend([
            ArtifactRef(path=str(parent / "source/events.jsonl"), role="precedent_event_corpus",
                        schema_version="event1", sha256=sha256_file(parent / "source/events.jsonl"),
                        records=len(all_events)),
            ArtifactRef(path=str(REVIEWER_ROSTER), role="reviewer_roster",
                        sha256=sha256_file(REVIEWER_ROSTER),
                        records=len(load_reviewer_roster(REVIEWER_ROSTER))),
        ])
    manifest = DatasetManifest(
        dataset_id=dataset_id, release=release, split="development",
        source_kind="raw_event_ledger",
        sources=sources,
        source_artifacts=[refs["source/events.jsonl"]],
        input_artifacts=[refs["input/episodes.jsonl"]], gold_artifacts=[refs[k] for k in refs if k.startswith("gold/")],
        derived_artifacts=[refs[k] for k in refs if k.startswith("derived/")],
        pr_numbers=sorted(wanted),
        corpus_cutoff_policy=("No historical review corpus is visible during generation."
        if treatment == "baseline" else
            "Rostered-maintainer review comments only; source PR differs from target and "
            "comment.occurred_at < episode review start"
        ),
        generator_tree_state="unknown",
        generator_versions=versions, created_at=created_at,
    )
    write_once(out / "manifest.json", pretty_json_bytes(manifest))
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=Path, default=Path(
        "inputs/pr_review_v4/releases/dev-judgment-stable-0.9.0"))
    parser.add_argument("--out", type=Path, default=Path(
        "inputs/pr_review_v4/releases/dev-pilot-0.9.0"))
    parser.add_argument("--treatment", choices=("baseline", "temporal_precedents"),
                        default="baseline")
    parser.add_argument("--release", default="0.9.0-pilot-stable")
    parser.add_argument("--cases", choices=sorted(CASE_REGISTRIES), default="pilot")
    parser.add_argument("--dataset-id", default=None)
    parser.add_argument("--created-at", default=None)
    args = parser.parse_args()
    kwargs = {"cases": CASE_REGISTRIES[args.cases]}
    if args.dataset_id:
        kwargs["dataset_id"] = args.dataset_id
    if args.created_at:
        kwargs["created_at"] = args.created_at
    manifest = build_pilot(args.parent, args.out, args.treatment, args.release, **kwargs)
    print(json.dumps({"release": str(args.out), "prs": len(manifest.pr_numbers),
                      "pr_numbers": manifest.pr_numbers}, indent=2))


if __name__ == "__main__":
    main()
