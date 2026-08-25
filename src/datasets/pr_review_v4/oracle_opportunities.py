"""Build and ingest the diagnostic oracle-opportunity adjudication probe."""

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

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
from .render_prompts import FACET_CHECKLIST, SYSTEM_PROMPT, render_work_unit
from .schema import (
    ArtifactRef,
    CandidateClaim,
    ChangeGraph,
    DatasetManifest,
    OpportunityAdjudication,
    OracleOpportunity,
    OracleOpportunityEvidence,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)


TREATMENT_VERSION = "oracle-opportunity-adjudication/1"
DEFAULT_PARENT = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
DEFAULT_OUT = Path("inputs/pr_review_v4/treatments/oracle-opportunity-probe-0.1.0")

INTERVENTION_SOURCE_IDS = (
    "wu:b017b7314c4bea62d8f968c3",
    "wu:9354e29b0912d17d60b1d3e1",
)
CONTROL_SOURCE_IDS = ("wu:20910b2d076223021ce8926e",)

CARD_MAX = "change:c5c9da88f1d990a90cb9913c331dedd39539e7c571bf7a0c98dce91de28c648f"
EMPTY_BRANCH = "change:c79e40846a8ccb396fbed4bb8a4aeb834a0eea561d9136e95e2a36763d603335"
MAX_SUBSET = "change:c7ef58137fa4b7b4ee0f8b13686be4a5afcefe2e8e8c434092e3c25c8510acc0"
IS_COVER = "change:d483f48d7e3a4447d26426246409ccd14c957a624be055ff2150a15e27d59768"
COVER_LE_PACK = "change:45cf88bca684cd3813871f4da143b9c827418cf9320465b788f860efac74900a"
ARCTAN_INV = "change:3ef5b17a805e3c6337189653431eef93e1c019e02cd250c400ab593a1ea7c57d"
ARCTAN = "change:5fd8ab92061fe7d82a0945fef55f5602c4a1249c8e62494cf1a96629aa48f303"

INTERVENTION_CHANGE_IDS = (CARD_MAX, EMPTY_BRANCH, MAX_SUBSET, IS_COVER, COVER_LE_PACK)
CONTROL_CHANGE_IDS = (ARCTAN_INV, ARCTAN)


ADJUDICATION_SYSTEM_PROMPT = """Act as a Mathlib maintainer adjudicating pre-discovered review
opportunities. Each opportunity is only a hypothesis and may be valid, invalid, too weakly normative,
or not worth mentioning. Inspect every opportunity exactly once. Distinguish three questions:
whether the alternative is valid, how strongly repository evidence supports it as an expectation,
and whether the difference warrants a review request in this PR. Mere frequency, similarity, or the
fact that an opportunity was supplied does not establish a defect.

Use repository and Lean tools when needed. Emit a candidate only when disposition is `request`.
Candidates must identify a present problem and one concrete requested transformation. For
`no_request` and `inconclusive`, record the decision without a candidate. Reference only evidence IDs
listed for that opportunity.

Finish by calling `submit_opportunity_adjudications` exactly once with one object per opportunity.
Each object has: `opportunity_id`, `disposition` (`request|no_request|inconclusive`), `validity`
(`valid|invalid|uncertain`), `norm_strength`
(`required|canonical|conventional|common|preference|unsupported|uncertain`), `review_worthiness`
(`blocking|advisory|not_worth_mentioning|uncertain`), `evidence_ids`, `rationale`, and `candidate`.
The candidate is null unless disposition is `request`; when present it follows the ordinary grounded
candidate contract with primary_change_id, primary_entity_id, primary_subject, change_ids,
concern_family, concern_label, severity, claim, requested_change, optional suggested_fix,
optional proposed_edit, and model_confidence."""


def _evidence(kind: str, source_ref: str, content: str, snapshot_sha: str):
    identity = {
        "kind": kind,
        "source_ref": source_ref,
        "content": content,
        "snapshot_sha": snapshot_sha,
    }
    digest = sha256_bytes(canonical_json_bytes(identity))
    return OracleOpportunityEvidence(
        evidence_id=f"opportunity-evidence:{digest[:24]}",
        source_sha256=digest,
        **identity,
    )


def _opportunity(
    unit: ReviewWorkUnit,
    source_work_unit_ids: Iterable[str],
    primary_change_id: str,
    method: str,
    information_class: str,
    selection_provenance: str,
    current_observation: str,
    proposed_alternative: str | None,
    question: str,
    evidence: List[OracleOpportunityEvidence],
    related_change_ids: Iterable[str] = (),
):
    identity = {
        "work_unit_id": unit.work_unit_id,
        "source_work_unit_ids": list(source_work_unit_ids),
        "episode_id": unit.episode_id,
        "pr_number": unit.pr_number,
        "primary_change_id": primary_change_id,
        "related_change_ids": list(related_change_ids),
        "method": method,
        "information_class": information_class,
        "selection_provenance": selection_provenance,
        "current_observation": current_observation,
        "proposed_alternative": proposed_alternative,
        "question": question,
        "evidence": [item.model_dump(mode="json") for item in evidence],
    }
    digest = sha256_bytes(canonical_json_bytes(identity))
    return OracleOpportunity(
        opportunity_id=f"opportunity:{digest[:24]}", source_sha256=digest, **identity
    )


def _merged_unit(
    source_units: List[ReviewWorkUnit], change_ids: Iterable[str], arm: str
) -> ReviewWorkUnit:
    change_ids = list(change_ids)
    base = source_units[0]
    source_by_change = {
        change_id: unit
        for unit in source_units
        for change_id in unit.change_ids
    }
    missing = set(change_ids) - set(source_by_change)
    if missing:
        raise ValueError(f"opportunity unit is missing change IDs: {sorted(missing)}")
    identity = {
        "treatment_version": TREATMENT_VERSION,
        "arm": arm,
        "source_work_unit_sha256s": [item.source_sha256 for item in source_units],
        "change_ids": change_ids,
    }
    digest = sha256_bytes(canonical_json_bytes(identity))
    return base.model_copy(update={
        "work_unit_id": f"wu:oracle-opportunity:{digest[:20]}",
        "change_ids": change_ids,
        "target_sha256s": {
            change_id: source_by_change[change_id].target_sha256s[change_id]
            for change_id in change_ids
        },
        "entity_ids_by_change": {
            change_id: source_by_change[change_id].entity_ids_by_change[change_id]
            for change_id in change_ids
        },
        "primary_subjects_by_change": {
            change_id: source_by_change[change_id].primary_subjects_by_change[change_id]
            for change_id in change_ids
        },
        "renderer_version": TREATMENT_VERSION,
        "source_sha256": digest,
    })


def _current_evidence(
    graph: ChangeGraph, episode: ReviewEpisodeInput, change_id: str
) -> OracleOpportunityEvidence:
    target = next(item for item in graph.targets if item.change_id == change_id)
    return _evidence(
        "reviewed_code",
        f"reviewed-change:{change_id}",
        target.reviewed_code or target.base_code or "",
        episode.reviewed_head_sha,
    )


def _intervention_opportunities(
    unit: ReviewWorkUnit, graph: ChangeGraph, episode: ReviewEpisodeInput
) -> List[OracleOpportunity]:
    current = lambda change_id: _current_evidence(graph, episode, change_id)
    base = episode.base_sha
    sources = INTERVENTION_SOURCE_IDS
    return [
        _opportunity(
            unit, sources, MAX_SUBSET, "proof_compression", "mechanical_simplification",
            "oracle_gold_targeted",
            "The proof unfolds the conditional definition with an explicit two-branch case split.",
            "Try a concise proof driven by `grind [maximalSeparatedSet]`, with the empty-set separation fact available to the tactic.",
            "Is the explicit case split sufficiently redundant that a maintainer should request the concise proof?",
            [current(MAX_SUBSET), _evidence(
                "repository_declaration",
                f"{base}:Mathlib/Topology/MetricSpace/MetricSeparated.lean:48",
                "protected lemma IsSeparated.empty : IsSeparated ε (∅ : Set X) := pairwise_empty _",
                base,
            )],
        ),
        _opportunity(
            unit, sources, CARD_MAX, "proof_compression", "mechanical_simplification",
            "oracle_gold_targeted",
            "The cardinality theorem repeats the conditional-definition reduction and projects a stored witness field.",
            "Try replacing the explicit reduction with one concise `grind` or equivalently direct proof.",
            "Does a shorter proof preserve clarity while removing redundant implementation detail?",
            [current(CARD_MAX), current(MAX_SUBSET)],
        ),
        _opportunity(
            unit, sources, CARD_MAX, "naming_contrast", "repository_convention",
            "oracle_gold_targeted",
            "The declaration is named `card_maximalSeparatedSet`, but its statement is about `Set.encard`.",
            "Rename it to `encard_maximalSeparatedSet` and update uses.",
            "Does the repository's cardinality naming convention make the current name misleading enough to request a rename?",
            [current(CARD_MAX), _evidence(
                "repository_pattern",
                f"{base}:Mathlib/Data/Set/Card.lean:112-138",
                "Representative names for Set.encard statements include `encard_ne_zero`, `encard_union_eq`, and `encard_insert_of_notMem`.",
                base,
            )],
        ),
        _opportunity(
            unit, sources, IS_COVER, "canonical_api_search", "canonical_api",
            "oracle_gold_targeted",
            "The proof manually establishes that inserting `x` into a separated set remains separated.",
            "Use `Metric.isSeparated_insert_of_notMem` with `hx_not_mem` and the existing distance hypothesis instead of the manual pairwise case analysis.",
            "Does the exact existing insert API make the manual separation block a concrete canonicalization issue?",
            [current(IS_COVER), _evidence(
                "repository_declaration",
                f"{base}:Mathlib/Topology/MetricSpace/MetricSeparated.lean:65-67",
                "lemma isSeparated_insert_of_notMem (hx : x ∉ s) : IsSeparated ε (insert x s) ↔ IsSeparated ε s ∧ ∀ y ∈ s, ε < edist x y",
                base,
            ), _evidence(
                "repository_declaration",
                f"{base}:Mathlib/Data/Set/Card.lean:138",
                "theorem encard_insert_of_notMem {a : α} (has : a ∉ s) : (insert a s).encard = s.encard + 1",
                base,
            )],
        ),
        _opportunity(
            unit, sources, COVER_LE_PACK, "intra_pr_composition", "intra_pr_composition",
            "oracle_gold_targeted",
            "The proof unfolds the covering-number infimum even though the PR constructs a maximal separated set and proves it is a cover.",
            "Compose the maximal-set cardinality equality, `isCover_maximalSeparatedSet`, and `IsCover.coveringNumber_le_encard` directly; keep the top case explicit.",
            "Do the existing API and new sibling theorems establish a more canonical proof that should be requested?",
            [current(COVER_LE_PACK), current(CARD_MAX), current(IS_COVER), _evidence(
                "repository_declaration",
                f"{base}:Mathlib/Topology/MetricSpace/CoveringNumbers.lean:135-136",
                "lemma IsCover.coveringNumber_le_encard (h_subset : C ⊆ A) (hC : IsCover ε A C) : coveringNumber ε A ≤ C.encard",
                base,
            )],
            related_change_ids=(CARD_MAX, IS_COVER, MAX_SUBSET),
        ),
        _opportunity(
            unit, sources, EMPTY_BRANCH, "repository_pattern", "maintainer_preference",
            "oracle_gold_targeted",
            "The empty-set branch binds an equality as `h_empty` and immediately rewrites with it.",
            "Pattern-match the empty equality as `rfl` and discharge that branch by simplification.",
            "Is the direct `rfl` branch a sufficiently established and clearer local idiom to warrant an advisory request?",
            [current(EMPTY_BRANCH), _evidence(
                "repository_pattern",
                f"{base}:Mathlib/Data/Set/Pairwise/Basic.lean:120",
                "rcases s.eq_empty_or_nonempty with (rfl | hne); · simp; · ...",
                base,
            ), _evidence(
                "repository_pattern",
                f"{base}:Mathlib/Probability/UniformOn.lean:167",
                "rcases s.eq_empty_or_nonempty with (rfl | hs')",
                base,
            )],
        ),
    ]


def _control_opportunities(
    unit: ReviewWorkUnit, graph: ChangeGraph, episode: ReviewEpisodeInput
) -> List[OracleOpportunity]:
    current = lambda change_id: _current_evidence(graph, episode, change_id)
    base = episode.base_sha
    sources = CONTROL_SOURCE_IDS
    shared = {
        "selection_provenance": "matched_control",
        "unit": unit,
        "source_work_unit_ids": sources,
    }
    return [
        _opportunity(
            **shared, primary_change_id=ARCTAN, method="naming_contrast",
            information_class="repository_convention",
            current_observation="The name `arctan_sqrt_three` directly mirrors the left-hand expression and nearby special-value theorem names.",
            proposed_alternative=None,
            question="Is there any concrete naming discrepancy that warrants a rename?",
            evidence=[current(ARCTAN), _evidence(
                "counterexample", f"{base}:Mathlib/Analysis/SpecialFunctions/Trigonometric/Arctan.lean:202",
                "Nearby theorem: `arctan_one : arctan 1 = π / 4`.", base,
            )],
        ),
        _opportunity(
            **shared, primary_change_id=ARCTAN, method="canonical_api_search",
            information_class="canonical_api",
            current_observation="The proof already rewrites with `tan_pi_div_three` and applies the canonical `arctan_tan` API.",
            proposed_alternative=None,
            question="Does this proof manually reconstruct behavior already available through a more canonical API?",
            evidence=[current(ARCTAN)],
        ),
        _opportunity(
            **shared, primary_change_id=ARCTAN, method="proof_compression",
            information_class="mechanical_simplification",
            current_observation="The proof uses `all_goals` before `field_simp` and `norm_num`.",
            proposed_alternative="Consider an equivalent local sequencing form only if it is demonstrably clearer or shorter.",
            question="Is this merely a valid stylistic choice, or is there a concrete proof simplification worth requesting?",
            evidence=[current(ARCTAN)],
        ),
        _opportunity(
            **shared, primary_change_id=ARCTAN_INV, method="canonical_api_search",
            information_class="canonical_api",
            current_observation="The proof already normalizes inversion, rewrites with `tan_pi_div_six`, and applies `arctan_tan`.",
            proposed_alternative=None,
            question="Is a more direct existing API available, or is the current proof already canonical for this statement?",
            evidence=[current(ARCTAN_INV)],
        ),
        _opportunity(
            **shared, primary_change_id=ARCTAN_INV, method="proof_compression",
            information_class="mechanical_simplification",
            current_observation="The inverse-square-root proof has the same short side-condition sequence as its sibling.",
            proposed_alternative="Use a shorter compiling proof only if one removes substantive redundancy rather than changing syntax.",
            question="Does the current proof contain a concrete redundant step that warrants a request?",
            evidence=[current(ARCTAN_INV), current(ARCTAN)],
            related_change_ids=(ARCTAN,),
        ),
        _opportunity(
            **shared, primary_change_id=ARCTAN_INV, method="family_consistency",
            information_class="intra_pr_composition",
            current_observation="The two new special-value theorems use parallel names, attributes, and proof structures.",
            proposed_alternative=None,
            question="Does the sibling comparison expose an inconsistency or justified shared abstraction request?",
            evidence=[current(ARCTAN_INV), current(ARCTAN)],
            related_change_ids=(ARCTAN,),
        ),
    ]


def _opportunity_block(opportunities: Iterable[OracleOpportunity]) -> str:
    blocks = [
        "# Pre-discovered opportunities",
        "Adjudicate each opportunity independently. Their presence is not evidence that a request is warranted.",
    ]
    for item in opportunities:
        evidence = "\n".join(
            f"- `{source.evidence_id}` [{source.kind}] {source.source_ref}\n  {source.content}"
            for source in item.evidence
        )
        blocks.append(
            f"## Opportunity `{item.opportunity_id}`\n"
            f"Method: `{item.method}`\n"
            f"Information class: `{item.information_class}`\n"
            f"Primary change: `{item.primary_change_id}`\n"
            f"Related changes: {', '.join(f'`{value}`' for value in item.related_change_ids) or '(none)'}\n"
            f"Current observation: {item.current_observation}\n"
            f"Proposed alternative: {item.proposed_alternative or '(none supplied)'}\n"
            f"Question: {item.question}\n"
            f"### Evidence\n{evidence}"
        )
    return "\n\n".join(blocks)


def _render_prompt(
    unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput,
    graph: ChangeGraph,
    opportunities: List[OracleOpportunity],
) -> RenderedPrompt:
    baseline = render_work_unit(unit, episode, graph)
    user = baseline.user_prompt.replace(SYSTEM_PROMPT, ADJUDICATION_SYSTEM_PROMPT, 1)
    user = user.replace(
        FACET_CHECKLIST,
        "### Adjudication context\nThis target is context for the supplied opportunities. Do not perform an unscoped review.",
    )
    marker = "# PR #"
    user = user.replace(marker, _opportunity_block(opportunities) + "\n\n" + marker, 1)
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
    units: Iterable[ReviewWorkUnit],
    graphs: Iterable[ChangeGraph],
    episodes: Iterable[ReviewEpisodeInput],
) -> Tuple[List[ReviewWorkUnit], List[RenderedPrompt], List[OracleOpportunity]]:
    units = list(units)
    graph_by_episode = {item.episode_id: item for item in graphs}
    episode_by_id = {item.episode_id: item for item in episodes}
    unit_by_id = {item.work_unit_id: item for item in units}
    intervention_sources = [unit_by_id[item] for item in INTERVENTION_SOURCE_IDS]
    control_sources = [unit_by_id[item] for item in CONTROL_SOURCE_IDS]
    intervention_unit = _merged_unit(intervention_sources, INTERVENTION_CHANGE_IDS, "intervention")
    control_unit = _merged_unit(control_sources, CONTROL_CHANGE_IDS, "control")
    output_units = [intervention_unit, control_unit]
    opportunities = []
    prompts = []
    for unit, builder in (
        (intervention_unit, _intervention_opportunities),
        (control_unit, _control_opportunities),
    ):
        graph = graph_by_episode[unit.episode_id]
        episode = episode_by_id[unit.episode_id]
        rows = builder(unit, graph, episode)
        opportunities.extend(rows)
        prompts.append(_render_prompt(unit, episode, graph, rows))
    return output_units, prompts, opportunities


def build_release(parent: Path = DEFAULT_PARENT, out: Path = DEFAULT_OUT) -> DatasetManifest:
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        return DatasetManifest.model_validate_json(manifest_path.read_text())
    parent_manifest = DatasetManifest.model_validate_json((parent / "manifest.json").read_text())
    all_units = load_jsonl(parent / "derived/work_units.jsonl", ReviewWorkUnit)
    all_graphs = load_jsonl(parent / "derived/change_graphs.jsonl", ChangeGraph)
    all_episodes = load_jsonl(parent / "input/episodes.jsonl", ReviewEpisodeInput)
    output_units, prompts, opportunities = build_artifacts(all_units, all_graphs, all_episodes)
    episode_ids = {item.episode_id for item in output_units}
    graph_ids = {item.graph_id for item in output_units}
    episodes = [item for item in all_episodes if item.episode_id in episode_ids]
    graphs = [item for item in all_graphs if item.graph_id in graph_ids]
    artifacts = {
        "input/episodes.jsonl": (episodes, "episode1", "reviewer_visible_episodes"),
        "derived/change_graphs.jsonl": (graphs, "cg1", "complete_change_graphs"),
        "derived/work_units.jsonl": (output_units, "work-unit1", "oracle_opportunity_units"),
        "derived/rendered_prompts.jsonl": (
            prompts, "rendered-prompt1", "oracle_opportunity_adjudication_prompts"
        ),
        "derived/oracle_opportunities.jsonl": (
            opportunities, "oracle-opportunity1", "diagnostic_oracle_opportunities"
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
        dataset_id="mathlib-pr-review-v4-oracle-opportunity-probe",
        release="0.1.0-oracle-opportunity-probe",
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
            "Diagnostic-only oracle selection may use development gold to choose contrasts; rendered "
            "evidence is restricted to review-time code and repository snapshots, with no comments or outcomes."
        ),
        generator_tree_state="unknown",
        generator_versions={
            **parent_manifest.generator_versions,
            "oracle_opportunities": TREATMENT_VERSION,
        },
        created_at="2026-07-17T00:00:00-05:00",
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def ingest_run(release: Path, responses_path: Path, out_dir: Path) -> Dict:
    units = load_jsonl(release / "derived/work_units.jsonl", ReviewWorkUnit)
    opportunities = load_jsonl(release / "derived/oracle_opportunities.jsonl", OracleOpportunity)
    responses = [json.loads(line) for line in responses_path.read_text().splitlines() if line]
    unit_by_id = {item.work_unit_id: item for item in units}
    opportunity_by_id = {item.opportunity_id: item for item in opportunities}
    response_by_unit = {}
    for row in responses:
        if row.get("success"):
            response_by_unit.setdefault(row.get("work_unit_id"), []).append(row)
    if set(response_by_unit) != set(unit_by_id) or any(len(rows) != 1 for rows in response_by_unit.values()):
        raise ValueError("run must contain exactly one successful response for every opportunity unit")

    candidates: List[CandidateClaim] = []
    adjudications: List[OpportunityAdjudication] = []
    seen = set()
    for work_unit_id, rows in response_by_unit.items():
        response = rows[0].get("response") or rows[0]
        unit_candidates = candidates_from_response(unit_by_id[work_unit_id], response)
        candidates.extend(unit_candidates)
        raw_decisions = response.get("adjudications")
        if not isinstance(raw_decisions, list):
            raise ValueError(f"work unit {work_unit_id} has no adjudications list")
        for raw in raw_decisions:
            opportunity_id = raw.get("opportunity_id")
            opportunity = opportunity_by_id.get(opportunity_id)
            if opportunity is None or opportunity.work_unit_id != work_unit_id:
                raise ValueError(f"unknown opportunity adjudication: {opportunity_id}")
            if opportunity_id in seen:
                raise ValueError(f"duplicate opportunity adjudication: {opportunity_id}")
            seen.add(opportunity_id)
            ordinal = raw.get("candidate_ordinal")
            candidate_id = None
            if ordinal is not None:
                if not isinstance(ordinal, int) or not 0 <= ordinal < len(unit_candidates):
                    raise ValueError(f"invalid candidate ordinal for {opportunity_id}")
                candidate_id = unit_candidates[ordinal].candidate_id
            if (raw.get("disposition") == "request") != (candidate_id is not None):
                raise ValueError(f"candidate/disposition mismatch for {opportunity_id}")
            evidence_ids = list(dict.fromkeys(raw.get("evidence_ids") or []))
            allowed_evidence = {item.evidence_id for item in opportunity.evidence}
            if not set(evidence_ids).issubset(allowed_evidence):
                raise ValueError(f"foreign evidence referenced by {opportunity_id}")
            payload = {
                "opportunity_id": opportunity_id,
                "work_unit_id": work_unit_id,
                "disposition": raw.get("disposition"),
                "validity": raw.get("validity"),
                "norm_strength": raw.get("norm_strength"),
                "review_worthiness": raw.get("review_worthiness"),
                "evidence_ids": evidence_ids,
                "rationale": str(raw.get("rationale") or "").strip(),
                "candidate_id": candidate_id,
                "producer": "model",
            }
            digest = sha256_bytes(canonical_json_bytes(payload))
            adjudications.append(OpportunityAdjudication(
                adjudication_id=f"opportunity-adjudication:{digest[:24]}",
                source_sha256=digest,
                **payload,
            ))
    missing = set(opportunity_by_id) - seen
    if missing:
        raise ValueError(f"missing opportunity adjudications: {sorted(missing)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    write_once(out_dir / "candidates.jsonl", jsonl_bytes(candidates))
    write_once(out_dir / "adjudications.jsonl", jsonl_bytes(adjudications))
    disposition_by_arm = {}
    for item in adjudications:
        arm = opportunity_by_id[item.opportunity_id].selection_provenance
        disposition_by_arm.setdefault(arm, Counter())[item.disposition] += 1
    report = {
        "schema_version": "oracle-opportunity-ingest-report1",
        "counts": {
            "opportunities": len(opportunities),
            "adjudications": len(adjudications),
            "candidates": len(candidates),
        },
        "dispositions_by_arm": {
            arm: dict(sorted(counts.items())) for arm, counts in sorted(disposition_by_arm.items())
        },
        "complete": len(adjudications) == len(opportunities),
    }
    write_once(out_dir / "adjudication_report.json", pretty_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--parent", type=Path, default=DEFAULT_PARENT)
    build.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("--release", type=Path, default=DEFAULT_OUT)
    ingest.add_argument("--responses", type=Path, required=True)
    ingest.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        manifest = build_release(args.parent, args.out)
        print(json.dumps({
            "release": str(args.out),
            "pr_numbers": manifest.pr_numbers,
            "derived_artifacts": len(manifest.derived_artifacts),
        }, indent=2))
    else:
        print(json.dumps(ingest_run(args.release, args.responses, args.out_dir), indent=2))


if __name__ == "__main__":
    main()
