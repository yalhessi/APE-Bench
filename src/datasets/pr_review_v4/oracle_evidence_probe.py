"""Build the two-call oracle evidence-sufficiency follow-up probe."""

import argparse
import json
from pathlib import Path

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
from .oracle_opportunities import (
    ADJUDICATION_SYSTEM_PROMPT,
    ARCTAN,
    ARCTAN_INV,
    CARD_MAX,
    CONTROL_CHANGE_IDS,
    CONTROL_SOURCE_IDS,
    COVER_LE_PACK,
    DEFAULT_PARENT,
    EMPTY_BRANCH,
    INTERVENTION_CHANGE_IDS,
    INTERVENTION_SOURCE_IDS,
    MAX_SUBSET,
    _current_evidence,
    _evidence,
    _merged_unit,
    _opportunity,
    _opportunity_block,
)
from .render_prompts import FACET_CHECKLIST, SYSTEM_PROMPT, render_work_unit
from .schema import (
    ArtifactRef,
    ChangeGraph,
    DatasetManifest,
    OracleOpportunity,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)


TREATMENT_VERSION = "oracle-evidence-sufficiency/1"
DEFAULT_OUT = Path("inputs/pr_review_v4/treatments/oracle-evidence-probe-0.2.0")


def _retag_unit(unit: ReviewWorkUnit, arm: str) -> ReviewWorkUnit:
    identity = {
        "treatment_version": TREATMENT_VERSION,
        "arm": arm,
        "source_unit_sha256": unit.source_sha256,
        "change_ids": unit.change_ids,
    }
    digest = sha256_bytes(canonical_json_bytes(identity))
    return unit.model_copy(update={
        "work_unit_id": f"wu:oracle-evidence:{digest[:20]}",
        "renderer_version": TREATMENT_VERSION,
        "source_sha256": digest,
    })


def _mechanical(source_ref: str, content: str, snapshot_sha: str):
    return _evidence("mechanical_check", source_ref, content, snapshot_sha)


def _quantitative(source_ref: str, content: str, snapshot_sha: str):
    return _evidence("quantitative_pattern", source_ref, content, snapshot_sha)


def _intervention_rows(
    unit: ReviewWorkUnit, graph: ChangeGraph, episode: ReviewEpisodeInput
) -> list[OracleOpportunity]:
    current = lambda change_id: _current_evidence(graph, episode, change_id)
    reviewed = episode.reviewed_head_sha
    base = episode.base_sha
    sources = INTERVENTION_SOURCE_IDS
    return [
        _opportunity(
            unit, sources, MAX_SUBSET, "proof_compression", "mechanical_simplification",
            "oracle_gold_targeted",
            "The proof unfolds the conditional definition with an explicit two-branch case split.",
            "Replace it with `by grind [maximalSeparatedSet]` after registering the empty-set facts for grind.",
            "Does the verified reduction establish a concrete simplification worth requesting?",
            [current(MAX_SUBSET), _mechanical(
                "oracle-check:maximalSeparatedSet_subset:coherent-patch-v1",
                "compiled=true; old proof body=6 nonblank lines; replacement=`by grind [maximalSeparatedSet]`; replacement body=1 line; coherent patch also adds `[grind .]` to `finite_empty` and `IsSeparated.empty`.",
                reviewed,
            )],
        ),
        _opportunity(
            unit, sources, CARD_MAX, "proof_compression", "mechanical_simplification",
            "oracle_gold_targeted",
            "The cardinality theorem repeats conditional reduction and projects a witness field.",
            "Preserve the current declaration name but replace its proof with `by grind [maximalSeparatedSet]`.",
            "Does the verified proof reduction warrant a simplification request independently of naming?",
            [current(CARD_MAX), _mechanical(
                "oracle-check:card_maximalSeparatedSet:proof-only-v1",
                "compiled=true; declaration name and statement unchanged; proof replacement=`by grind [maximalSeparatedSet]`; coherent patch also adds the required empty-set grind attributes.",
                reviewed,
            )],
        ),
        _opportunity(
            unit, sources, COVER_LE_PACK, "intra_pr_composition", "intra_pr_composition",
            "oracle_gold_targeted",
            "The proof reasons through the covering-number infimum instead of the local `IsCover` wrapper API.",
            "Use `encard_maximalSeparatedSet`, `isCover_maximalSeparatedSet`, and `IsCover.coveringNumber_le_encard` directly.",
            "Does the verified wrapper-based proof provide a materially better abstraction boundary?",
            [current(COVER_LE_PACK), _mechanical(
                "oracle-check:coveringNumber_le_packingNumber:coherent-patch-v1",
                "compiled=true; replacement uses `by_cases!`, rewrites by `encard_maximalSeparatedSet`, and applies `isCover_maximalSeparatedSet h_top |>.coveringNumber_le_encard maximalSeparatedSet_subset`; it removes direct uses of `iInf_le`, `iInf_pos`, and `le_of_eq` from the caller.",
                reviewed,
            ), _evidence(
                "repository_declaration",
                f"{base}:Mathlib/Topology/MetricSpace/CoveringNumbers.lean:135-136",
                "lemma IsCover.coveringNumber_le_encard (h_subset : C ⊆ A) (hC : IsCover ε A C) : coveringNumber ε A ≤ C.encard",
                base,
            )],
            related_change_ids=(CARD_MAX, MAX_SUBSET),
        ),
        _opportunity(
            unit, sources, EMPTY_BRANCH, "repository_pattern", "maintainer_preference",
            "oracle_gold_targeted",
            "The empty branch binds an equality and immediately rewrites with it.",
            "Pattern-match that branch as `rfl` and discharge it with `simp`.",
            "Do the verified edit and repository prevalence make this small rewrite request-worthy?",
            [current(EMPTY_BRANCH), _mechanical(
                "oracle-check:coveringNumber_two_mul_empty-branch:v1",
                "compiled=true; replacement changes `with (h_empty | h_nonempty); · simp [h_empty]` to `with rfl | h_nonempty; · simp`; theorem statement and nonempty branch are unchanged.",
                reviewed,
            ), _quantitative(
                f"{base}:mathlib-source-pattern-scan:eq-empty-rfl-v1",
                "Review-time source contains 111 `eq_empty_or_nonempty` case splits that pattern-match an empty branch with `rfl`, versus 52 that initially bind a named equality before `|`. Both forms exist; direct `rfl` is the majority pattern.",
                base,
            )],
        ),
        _opportunity(
            unit, sources, CARD_MAX, "naming_contrast", "repository_convention",
            "oracle_gold_targeted",
            "The declaration is named `card_maximalSeparatedSet`, but its statement is about `Set.encard`.",
            "Rename it to `encard_maximalSeparatedSet` and update uses.",
            "Does quantified declaration evidence make the rename a convention rather than a loose preference?",
            [current(CARD_MAX), _quantitative(
                f"{base}:mathlib-declaration-header-scan:encard-naming-v1",
                "Among review-time theorem/lemma headers whose first 12 declaration lines mention `encard`, 94 names start with `encard_`, 1 starts with `card_`, and 129 use a role-specific other prefix. The target's `card_` prefix conflicts with the dominant direct naming pattern for Set.encard results.",
                base,
            )],
        ),
    ]


def _control_rows(
    unit: ReviewWorkUnit, graph: ChangeGraph, episode: ReviewEpisodeInput
) -> list[OracleOpportunity]:
    current = lambda change_id: _current_evidence(graph, episode, change_id)
    reviewed = episode.reviewed_head_sha
    base = episode.base_sha
    sources = CONTROL_SOURCE_IDS
    return [
        _opportunity(
            unit, sources, ARCTAN, "proof_compression", "mechanical_simplification",
            "matched_control",
            "The proof uses `all_goals` for side-condition discharge.",
            "An equivalent `<;>` sequencing variant compiles but changes only tactic punctuation.",
            "Does a compiling syntax-only variant establish a substantive simplification request?",
            [current(ARCTAN), _mechanical(
                "oracle-check:arctan_sqrt_three:syntax-variant-v1",
                "compiled=true; the alternative preserves the same rewrites, `field_simp`, and `norm_num`; semantic steps removed=0.",
                reviewed,
            )],
        ),
        _opportunity(
            unit, sources, ARCTAN_INV, "proof_compression", "mechanical_simplification",
            "matched_control",
            "The inverse-square-root proof repeats its sibling's short side-condition sequence.",
            "An equivalent sequencing variant compiles but removes no mathematical step.",
            "Does compilation alone make this alternative review-worthy?",
            [current(ARCTAN_INV), current(ARCTAN), _mechanical(
                "oracle-check:arctan_inv_sqrt_three:syntax-variant-v1",
                "compiled=true; semantic steps removed=0; no existing shared theorem replaces either proof.",
                reviewed,
            )],
            related_change_ids=(ARCTAN,),
        ),
        _opportunity(
            unit, sources, ARCTAN, "naming_contrast", "repository_convention",
            "matched_control",
            "The name `arctan_sqrt_three` mirrors its expression and nearby special-value names.",
            "Rename only if a stronger repository pattern contradicts the current name.",
            "Does the evidence expose an actual naming discrepancy?",
            [current(ARCTAN), _quantitative(
                f"{base}:local-special-value-name-scan:v1",
                "The nearby API uses expression-derived names such as `arctan_one`; both new declarations use the same expression-derived naming scheme. Contradicting local examples found=0.",
                base,
            )],
        ),
        _opportunity(
            unit, sources, ARCTAN_INV, "family_consistency", "intra_pr_composition",
            "matched_control",
            "The two declarations have parallel names, simp attributes, and proof structures.",
            "Introduce a shared abstraction only if it removes semantic duplication.",
            "Does the family comparison establish an inconsistency or abstraction request?",
            [current(ARCTAN_INV), current(ARCTAN), _quantitative(
                f"{reviewed}:changed-family-consistency-scan:v1",
                "Compared facets: name morphology, `[simp]` attribute, rewrite structure, side-condition tactics. Inconsistent facets=0; shared semantic replacement found=0.",
                reviewed,
            )],
            related_change_ids=(ARCTAN,),
        ),
        _opportunity(
            unit, sources, ARCTAN_INV, "canonical_api_search", "canonical_api",
            "matched_control",
            "The proof already uses `inv_eq_one_div`, `tan_pi_div_six`, and `arctan_tan`.",
            None,
            "Does canonical API evidence identify any missing replacement?",
            [current(ARCTAN_INV), _quantitative(
                f"{base}:arctan-api-usage-scan:v1",
                "Required canonical ingredients present=3/3 (`inv_eq_one_div`, `tan_pi_div_six`, `arctan_tan`); more direct matching declaration found=0.",
                base,
            )],
        ),
    ]


def _render(
    unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput,
    graph: ChangeGraph,
    opportunities: list[OracleOpportunity],
) -> RenderedPrompt:
    baseline = render_work_unit(unit, episode, graph)
    user = baseline.user_prompt.replace(SYSTEM_PROMPT, ADJUDICATION_SYSTEM_PROMPT, 1)
    user = user.replace(
        FACET_CHECKLIST,
        "### Adjudication context\nThis target is context for the supplied opportunities. Do not perform an unscoped review.",
    )
    user = user.replace("# PR #", _opportunity_block(opportunities) + "\n\n# PR #", 1)
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


def build_artifacts(units, graphs, episodes):
    unit_by_id = {item.work_unit_id: item for item in units}
    graph_by_episode = {item.episode_id: item for item in graphs}
    episode_by_id = {item.episode_id: item for item in episodes}
    intervention = _retag_unit(_merged_unit(
        [unit_by_id[item] for item in INTERVENTION_SOURCE_IDS],
        INTERVENTION_CHANGE_IDS,
        "evidence-intervention",
    ), "intervention")
    control = _retag_unit(_merged_unit(
        [unit_by_id[item] for item in CONTROL_SOURCE_IDS],
        CONTROL_CHANGE_IDS,
        "evidence-control",
    ), "control")
    output_units = [intervention, control]
    opportunities = []
    prompts = []
    for unit, builder in ((intervention, _intervention_rows), (control, _control_rows)):
        graph = graph_by_episode[unit.episode_id]
        episode = episode_by_id[unit.episode_id]
        rows = builder(unit, graph, episode)
        opportunities.extend(rows)
        prompts.append(_render(unit, episode, graph, rows))
    return output_units, prompts, opportunities


def build_release(parent: Path = DEFAULT_PARENT, out: Path = DEFAULT_OUT) -> DatasetManifest:
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        return DatasetManifest.model_validate_json(manifest_path.read_text())
    parent_manifest = DatasetManifest.model_validate_json((parent / "manifest.json").read_text())
    all_units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)
    all_graphs = load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
    all_episodes = load_jsonl(parent / "input/episodes.jsonl", ReviewEpisodeInput)
    units, prompts, opportunities = build_artifacts(all_units, all_graphs, all_episodes)
    episode_ids = {item.episode_id for item in units}
    graph_ids = {item.graph_id for item in units}
    episodes = [item for item in all_episodes if item.episode_id in episode_ids]
    graphs = [item for item in all_graphs if item.graph_id in graph_ids]
    artifacts = {
        "input/episodes.jsonl": (episodes, "episode1", "reviewer_visible_episodes"),
        "derived/change_graphs.jsonl": (graphs, "cg1", "complete_change_graphs"),
        "derived/work_units.jsonl": (units, "work-unit1", "oracle_evidence_units"),
        "derived/rendered_prompts.jsonl": (
            prompts, "rendered-prompt1", "oracle_evidence_adjudication_prompts"
        ),
        "derived/oracle_opportunities.jsonl": (
            opportunities, "oracle-opportunity1", "diagnostic_oracle_evidence_opportunities"
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
        dataset_id="mathlib-pr-review-v4-oracle-evidence-probe",
        release="0.2.0-oracle-evidence-probe",
        source_kind=parent_manifest.source_kind,
        split="development",
        sources=[ArtifactRef(
            path=display_path(parent / "manifest.json"),
            role="parent_stable_release",
            schema_version=parent_manifest.schema_version,
            sha256=sha256_file(parent / "manifest.json"),
            records=2,
        )],
        input_artifacts=[refs["input/episodes.jsonl"]],
        derived_artifacts=[refs[rel] for rel in refs if rel.startswith("derived/")],
        pr_numbers=sorted({item.pr_number for item in episodes}),
        corpus_cutoff_policy=(
            "Diagnostic-only oracle evidence may use development outcomes to instantiate mechanically "
            "verified alternatives. Repository prevalence is computed at the review-time snapshot. "
            "No maintainer comment or adoption label is rendered."
        ),
        generator_tree_state="unknown",
        generator_versions={
            **parent_manifest.generator_versions,
            "oracle_evidence_probe": TREATMENT_VERSION,
        },
        created_at="2026-07-17T00:00:00-05:00",
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    manifest = build_release(args.parent, args.out)
    print(json.dumps({
        "release": str(args.out),
        "pr_numbers": manifest.pr_numbers,
        "derived_artifacts": len(manifest.derived_artifacts),
    }, indent=2))


if __name__ == "__main__":
    main()
