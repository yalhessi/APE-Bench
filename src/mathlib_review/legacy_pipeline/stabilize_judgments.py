"""Apply reviewed obligation decompositions to a draft judgment release."""

import argparse
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from src.mathlib_review.io import (
    canonical_json_bytes,
    display_path,
    git_state,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from src.mathlib_review.schema import (
    ArtifactRef,
    ChangeGraph,
    DatasetManifest,
    InterventionView,
    JudgmentAnnotation,
    JudgmentDecompositionDecision,
    JudgmentNode,
    JudgmentObligation,
    JudgmentScopeRelation,
    OutcomeObservation,
)


STABILIZER_VERSION = "judgment-decomposition/1"
DEFAULT_DRAFT = Path("inputs/pr_review_v4/releases/dev-judgment-draft-0.7.0")
DEFAULT_DECISIONS = Path("inputs/pr_review_v4/curation/judgment_decomposition_v1.json")
DEFAULT_RELEASE = Path("inputs/pr_review_v4/releases/dev-judgment-stable-0.9.0")
REPLACED_PATHS = {
    "gold/judgments.jsonl",
    "gold/outcome_observations.jsonl",
    "gold/intervention_views.jsonl",
    "gold/judgment_report.json",
}


def _load_decisions(path: Path) -> List[JudgmentDecompositionDecision]:
    """Seal human-readable curation records with deterministic provenance IDs."""
    raw_records = json.loads(path.read_text())
    decisions = []
    for raw in raw_records:
        source = {
            "schema_version": "judgment-decomposition1",
            **raw,
        }
        digest = sha256_bytes(canonical_json_bytes(source))
        decisions.append(JudgmentDecompositionDecision(
            decision_id=f"decomposition:{digest}",
            source_sha256=digest,
            **source,
        ))
    return decisions


def _hash_id(prefix: str, value: object) -> str:
    return f"{prefix}:{sha256_bytes(canonical_json_bytes(value))}"


def _obligation(parent: JudgmentNode, decision: JudgmentDecompositionDecision, spec):
    source = {
        "version": STABILIZER_VERSION,
        "parent_judgment_sha256": parent.source_sha256,
        "decision_sha256": decision.source_sha256,
        "obligation_key": spec.obligation_key,
        "claim": spec.claim,
        "resolution_criteria": spec.resolution_criteria,
        "required": spec.required,
        "change_ids": spec.change_ids,
        "source_event_ids": spec.source_event_ids,
    }
    digest = sha256_bytes(canonical_json_bytes(source))
    return JudgmentObligation(
        obligation_id=f"obligation:{digest}", claim=spec.claim,
        resolution_criteria=spec.resolution_criteria, required=spec.required,
        status="proposed_atomic", change_ids=spec.change_ids,
        source_event_ids=spec.source_event_ids, source_sha256=digest,
    )


def stabilize_artifacts(
    judgments: Iterable[JudgmentNode],
    outcomes: Iterable[OutcomeObservation],
    views: Iterable[InterventionView],
    decisions: Iterable[JudgmentDecompositionDecision],
    graphs: Iterable[ChangeGraph],
):
    judgments, outcomes, views = list(judgments), list(outcomes), list(views)
    decision_by_id = {item.source_intervention_id: item for item in decisions}
    pending_ids = {
        item.source_intervention_id for item in judgments
        if item.annotation.atomicity_status == "needs_decomposition"
    }
    if set(decision_by_id) != pending_ids:
        raise ValueError(
            f"decomposition decisions mismatch: missing={sorted(pending_ids-set(decision_by_id))} "
            f"extra={sorted(set(decision_by_id)-pending_ids)}"
        )
    graph_targets = {
        graph.episode_id: {target.change_id for target in graph.targets} for graph in graphs
    }
    outcome_by_judgment = {item.judgment_id: item for item in outcomes}
    view_by_intervention = {item.source_intervention_id: item for item in views}
    stable_judgments, stable_outcomes, stable_views = [], [], []
    for parent in judgments:
        decision = decision_by_id.get(parent.source_intervention_id)
        if decision is None:
            stable_judgments.append(parent)
            stable_outcomes.append(outcome_by_judgment[parent.judgment_id])
            stable_views.append(view_by_intervention[parent.source_intervention_id])
            continue
        if decision.decision == "not_evaluable":
            raise ValueError("not_evaluable decomposition decisions require an explicit exclusion design")
        if decision.decision == "accept_atomic" and len(decision.obligations) != 1:
            raise ValueError(f"{decision.source_intervention_id}: accept_atomic requires one obligation")
        if decision.decision == "split" and len(decision.obligations) < 2:
            raise ValueError(f"{decision.source_intervention_id}: split requires multiple obligations")
        allowed_targets = graph_targets[parent.episode_id]
        requested_targets = {
            change_id for spec in decision.obligations for change_id in spec.change_ids
        }
        unknown = requested_targets - allowed_targets
        if unknown:
            raise ValueError(f"{decision.source_intervention_id}: unknown change IDs {sorted(unknown)}")
        unknown_events = {
            event_id for spec in decision.obligations for event_id in spec.source_event_ids
            if event_id not in parent.source_event_ids
        }
        if unknown_events:
            raise ValueError(f"{decision.source_intervention_id}: unknown source events {sorted(unknown_events)}")
        obligations = [_obligation(parent, decision, spec) for spec in decision.obligations]
        judgment_source = {
            "version": STABILIZER_VERSION,
            "parent_judgment_sha256": parent.source_sha256,
            "decision_sha256": decision.source_sha256,
            "obligations": [item.model_dump(mode="json") for item in obligations],
            "scope_change_ids": sorted(requested_targets),
        }
        judgment_digest = sha256_bytes(canonical_json_bytes(judgment_source))
        judgment_id = f"judgment:{judgment_digest}"
        old_outcome = outcome_by_judgment[parent.judgment_id]
        outcome_source = {
            "version": STABILIZER_VERSION,
            "parent_observation_sha256": old_outcome.source_sha256,
            "judgment_id": judgment_id,
        }
        outcome_digest = sha256_bytes(canonical_json_bytes(outcome_source))
        observation_id = f"outcome:{outcome_digest}"
        stable = parent.model_copy(update={
            "judgment_id": judgment_id,
            "scope_relations": [
                JudgmentScopeRelation(change_id=change_id, relation="applies_to")
                for change_id in sorted(requested_targets)
            ],
            "obligations": obligations,
            "outcome_observation_ids": [observation_id],
            "annotation": JudgmentAnnotation(
                producer=STABILIZER_VERSION, source_schema=parent.annotation.source_schema,
                status="curator_confirmed", atomicity_status="reviewed_decomposed",
                atomicity_signals=parent.annotation.atomicity_signals,
            ),
            "source_sha256": judgment_digest,
        })
        outcome = old_outcome.model_copy(update={
            "observation_id": observation_id, "judgment_id": judgment_id,
            "producer": STABILIZER_VERSION, "source_sha256": outcome_digest,
        })
        view_source = {
            "version": STABILIZER_VERSION,
            "source_intervention_id": parent.source_intervention_id,
            "judgment_ids": [judgment_id],
            "obligation_ids": [item.obligation_id for item in obligations],
            "aggregation_policy": "all_required",
            "evaluation_eligibility": "included",
        }
        view_digest = sha256_bytes(canonical_json_bytes(view_source))
        view = InterventionView(
            view_id=f"view:{view_digest}", source_intervention_id=parent.source_intervention_id,
            judgment_ids=[judgment_id], obligation_ids=view_source["obligation_ids"],
            aggregation_policy="all_required", evaluation_eligibility="included",
            source_sha256=view_digest,
        )
        stable_judgments.append(stable)
        stable_outcomes.append(outcome)
        stable_views.append(view)
    report = {
        "schema_version": "judgment-stability-audit1",
        "stabilizer_version": STABILIZER_VERSION,
        "judgments": len(stable_judgments),
        "obligations": sum(len(item.obligations) for item in stable_judgments),
        "decisions": len(decision_by_id),
        "decomposed_obligations": sum(
            len(item.obligations) for item in stable_judgments
            if item.annotation.atomicity_status == "reviewed_decomposed"
        ),
        "atomicity_status": dict(sorted(Counter(
            item.annotation.atomicity_status for item in stable_judgments
        ).items())),
        "evaluation_eligibility": dict(sorted(Counter(
            item.evaluation_eligibility for item in stable_views
        ).items())),
        "judgments_sha256": sha256_bytes(jsonl_bytes(stable_judgments)),
        "outcomes_sha256": sha256_bytes(jsonl_bytes(stable_outcomes)),
        "views_sha256": sha256_bytes(jsonl_bytes(stable_views)),
    }
    return stable_judgments, stable_outcomes, stable_views, report


def build_stable_judgment_release(
    draft_release: Path, decisions_path: Path, release_dir: Path,
    release: str = "0.9.0-judgment-stable", created_at: Optional[str] = None,
) -> DatasetManifest:
    manifest_path = release_dir / "manifest.json"
    if manifest_path.exists():
        existing = DatasetManifest.model_validate_json(manifest_path.read_text())
        if existing.release != release:
            raise FileExistsError(f"existing release has incompatible identity: {manifest_path}")
        return existing
    draft_manifest = DatasetManifest.model_validate_json((draft_release / "manifest.json").read_text())
    inherited_refs = [
        item for item in (
            draft_manifest.source_artifacts + draft_manifest.input_artifacts
            + draft_manifest.gold_artifacts + draft_manifest.derived_artifacts
        ) if item.path not in REPLACED_PATHS
    ]
    for artifact in inherited_refs:
        write_once(release_dir / artifact.path, (draft_release / artifact.path).read_bytes())
    judgments, outcomes, views, report = stabilize_artifacts(
        load_jsonl(draft_release / "gold/judgments.jsonl", JudgmentNode),
        load_jsonl(draft_release / "gold/outcome_observations.jsonl", OutcomeObservation),
        load_jsonl(draft_release / "gold/intervention_views.jsonl", InterventionView),
        _load_decisions(decisions_path),
        load_jsonl(draft_release / "derived/change_graphs.jsonl", ChangeGraph),
    )
    artifacts = {
        "gold/judgments.jsonl": (judgments, "jg1", "reviewed_judgment_graph"),
        "gold/outcome_observations.jsonl": (
            outcomes, "outcome-observation1", "separate_outcome_observations"
        ),
        "gold/intervention_views.jsonl": (views, "view1", "reviewed_intervention_views"),
        "gold/judgment_report.json": (report, "judgment-stability-audit1", "judgment_stability_audit"),
    }
    refs = []
    for rel, (rows, schema, role) in artifacts.items():
        path = release_dir / rel
        content = pretty_json_bytes(rows) if isinstance(rows, dict) else jsonl_bytes(rows)
        write_once(path, content)
        refs.append(ArtifactRef(
            path=rel, role=role, schema_version=schema, sha256=sha256_file(path),
            records=len(rows) if not isinstance(rows, dict) else report["decisions"],
        ))
    retained_gold = [item for item in draft_manifest.gold_artifacts if item.path not in REPLACED_PATHS]
    git_commit, tree_state = git_state()
    manifest = draft_manifest.model_copy(update={
        "release": release,
        "sources": [*draft_manifest.sources, ArtifactRef(
            path=display_path(decisions_path), role="judgment_decomposition_decisions",
            schema_version="judgment-decomposition1", sha256=sha256_file(decisions_path),
            records=len(_load_decisions(decisions_path)),
        )],
        "gold_artifacts": [*retained_gold, *refs],
        "generator_git_commit": git_commit, "generator_tree_state": tree_state,
        "generator_versions": {
            **draft_manifest.generator_versions, "judgment_stabilizer": STABILIZER_VERSION,
        },
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
    })
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build reviewed stable v4 judgment release")
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--out", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--release", default="0.9.0-judgment-stable")
    parser.add_argument("--created-at", default=None)
    args = parser.parse_args()
    manifest = build_stable_judgment_release(
        args.draft, args.decisions, args.out, args.release, args.created_at
    )
    print(json.dumps({"release": str(args.out), "prs": len(manifest.pr_numbers)}, indent=2))


if __name__ == "__main__":
    main()
