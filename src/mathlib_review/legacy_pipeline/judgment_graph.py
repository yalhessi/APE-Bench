"""Build conservative jg1 migration proposals from i5 and reviewed cg1 scope maps."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, pretty_json_bytes, sha256_bytes, write_once
from .migrate_interventions import _load_source_events
from src.mathlib_review.paths import LEGACY_INTERVENTIONS_V5
from src.mathlib_review.schema import (
    InterventionScopeMigration,
    InterventionView,
    JudgmentAction,
    JudgmentAnnotation,
    JudgmentContextRelation,
    JudgmentNode,
    JudgmentObligation,
    JudgmentScopeRelation,
    OutcomeObservation,
)


JUDGMENT_MIGRATION_VERSION = "jg1_i5_migration_v1"
_TICK_RE = re.compile(r"`([^`\n]+)`")
_PROPAGATION_RE = re.compile(
    r"^\s*\(?\s*(same( comment| here| below| as above)?|ditto|likewise|also here|"
    r"and the other( ones?)?|as above)\b[\s\S]{0,40}$",
    re.I,
)
_ACTION_RE = re.compile(
    r"\b(rename|remove|replace|add|move|rewrite|refactor|fix|change|use|decide|"
    r"explain|document|reorder|generalize|avoid|clarify|reconsider|insert|wrap|split)\b",
    re.I,
)


def _hash_id(prefix: str, value: object) -> str:
    return f"{prefix}:{sha256_bytes(canonical_json_bytes(value))}"


def judgment_source_projection(
    intervention: Dict[str, Any], migration: InterventionScopeMigration
) -> Dict[str, Any]:
    """Allowlisted judgment fields; adoption labels and evidence are excluded."""
    return {
        "schema_version": intervention.get("schema_version"),
        "intervention_id": intervention.get("intervention_id"),
        "pr_number": intervention.get("pr_number"),
        "canonical_ask": intervention.get("canonical_ask") or "",
        "concern": intervention.get("concern") or "other",
        "severity": intervention.get("severity") or "advisory",
        "stratum": intervention.get("stratum"),
        "judgeable": bool(intervention.get("judgeable")),
        "meta": bool(intervention.get("meta")),
        "source_comments": [
            {
                "id": item.get("id"),
                "submitted_at": item.get("submitted_at"),
                "body": item.get("body") or "",
            }
            for item in intervention.get("source_comments") or []
        ],
        "scope_migration_id": migration.migration_id,
        "scope_status": migration.status,
        "change_ids": migration.resolved_change_ids,
        "source_event_ids": migration.source_event_ids,
    }


def _action(ask: str) -> JudgmentAction:
    match = _ACTION_RE.search(ask)
    kind = match.group(1).lower() if match else "other"
    identifiers = [item.strip() for item in _TICK_RE.findall(ask) if item.strip()]
    target = identifiers[0] if identifiers else ask.strip()[:180]
    return JudgmentAction(kind=kind, object=target)


def _speech_act(projection: Dict[str, Any]) -> str:
    ask = str(projection["canonical_ask"])
    lowered = ask.lower()
    if projection["meta"]:
        return "process"
    if re.search(r"\b(decide whether|reconsider|clarify|obtain consensus|do not proceed)\b", lowered):
        return "decision_target"
    if re.search(r"\b(optionally|suggest|if you want|consider)\b", lowered):
        return "suggestion"
    bodies = "\n".join(item["body"] for item in projection["source_comments"])
    if "?" in bodies and not _ACTION_RE.search(ask):
        return "question"
    return "request"


def atomicity_signals(ask: str) -> List[str]:
    signals = []
    if re.search(r"\(1\)[\s\S]+\(2\)", ask):
        signals.append("explicit_numbered_components")
    if re.search(r"\badditionally\b", ask, re.I):
        signals.append("additional_independent_clause")
    if re.search(
        r";\s*(?:and\s+)?(?:add|remove|rename|replace|move|rewrite|fix|change|"
        r"introduce|derive|update|document)\b",
        ask,
        re.I,
    ):
        signals.append("semicolon_imperative_clause")
    return signals


def _atomicity_status(
    projection: Dict[str, Any], migration: InterventionScopeMigration, signals: Sequence[str]
) -> str:
    if projection["meta"]:
        return "metadata"
    if not projection["judgeable"]:
        return "not_judgeable"
    if migration.status == "unresolved":
        return "unresolved_scope"
    if signals:
        return "needs_decomposition"
    return "presumed_atomic"


def _context_relations(
    projection: Dict[str, Any], event_map: Dict[Tuple[int, str], str]
) -> List[JudgmentContextRelation]:
    comments = sorted(
        projection["source_comments"], key=lambda item: item.get("submitted_at") or ""
    )
    relations = []
    first_event = None
    last_substantive = None
    pr_number = int(projection["pr_number"])
    for comment in comments:
        event_id = event_map.get((pr_number, str(comment.get("id") or "")))
        if not event_id:
            continue
        body = str(comment.get("body") or "").strip()
        if first_event is None:
            first_event = event_id
        if _PROPAGATION_RE.match(body) and last_substantive:
            relations.append(
                JudgmentContextRelation(
                    event_id=event_id,
                    antecedent_event_id=last_substantive,
                    relation="extends_scope",
                    confidence="mechanical",
                )
            )
        elif event_id != first_event:
            relations.append(
                JudgmentContextRelation(
                    event_id=event_id,
                    antecedent_event_id=first_event,
                    relation="coexpresses_judgment",
                    confidence="inherited_i5_grouping",
                )
            )
        if not _PROPAGATION_RE.match(body):
            last_substantive = event_id
    return relations


def build_judgment(
    intervention: Dict[str, Any],
    migration: InterventionScopeMigration,
    *,
    repo: str,
    event_map: Dict[Tuple[int, str], str],
) -> Tuple[JudgmentNode, OutcomeObservation, InterventionView]:
    projection = judgment_source_projection(intervention, migration)
    ask = str(projection["canonical_ask"])
    signals = atomicity_signals(ask)
    atomicity = _atomicity_status(projection, migration, signals)
    obligation_status = (
        "proposed_atomic"
        if atomicity == "presumed_atomic"
        else "needs_decomposition"
        if atomicity == "needs_decomposition"
        else "not_evaluable"
    )
    obligation_source = {
        "intervention_id": projection["intervention_id"],
        "claim": ask,
        "change_ids": projection["change_ids"],
        "status": obligation_status,
    }
    obligation = JudgmentObligation(
        obligation_id=_hash_id("obligation", obligation_source),
        claim=ask,
        resolution_criteria=(
            "The requested transformation is satisfied at every required target, and any "
            "superseded form named by the request is no longer used there."
            if obligation_status == "proposed_atomic"
            else None
        ),
        status=obligation_status,
        change_ids=list(projection["change_ids"]),
        source_sha256=sha256_bytes(canonical_json_bytes(obligation_source)),
    )
    context = _context_relations(projection, event_map)
    judgment_source = {
        "version": JUDGMENT_MIGRATION_VERSION,
        "projection": projection,
        "action": _action(ask).model_dump(mode="json"),
        "speech_act": _speech_act(projection),
        "scope_relations": projection["change_ids"],
        "obligation": obligation.model_dump(mode="json"),
        "context_relations": [item.model_dump(mode="json") for item in context],
        "atomicity_status": atomicity,
        "atomicity_signals": signals,
    }
    judgment_hash = sha256_bytes(canonical_json_bytes(judgment_source))
    judgment_id = f"judgment:{judgment_hash}"
    observation_id = _hash_id(
        "outcome", [projection["intervention_id"], judgment_id]
    )
    judgment = JudgmentNode(
        judgment_id=judgment_id,
        source_intervention_id=str(projection["intervention_id"]),
        repo=repo,
        pr_number=int(projection["pr_number"]),
        episode_id=migration.episode_id,
        action=_action(ask),
        speech_act=_speech_act(projection),
        blocking_force=(
            "blocking" if projection["severity"] == "blocking" else "advisory"
        ),
        concern_labels=[str(projection["concern"])],
        scope_relations=[
            JudgmentScopeRelation(change_id=change_id, relation="applies_to")
            for change_id in projection["change_ids"]
        ],
        obligations=[obligation],
        source_event_ids=list(projection["source_event_ids"]),
        context_relations=context,
        outcome_observation_ids=[observation_id],
        annotation=JudgmentAnnotation(
            producer=JUDGMENT_MIGRATION_VERSION,
            source_schema="i5",
            status="migration_proposal",
            atomicity_status=atomicity,
            atomicity_signals=signals,
        ),
        source_sha256=judgment_hash,
    )
    outcome_source = {
        "intervention_id": intervention["intervention_id"],
        "judgment_id": judgment_id,
        "outcome": intervention.get("outcome") or "unknown",
        "evidence": intervention.get("outcome_evidence") or "",
        "producer": "i5_outcome_v4",
    }
    outcome = OutcomeObservation(
        observation_id=observation_id,
        source_intervention_id=str(intervention["intervention_id"]),
        judgment_id=judgment_id,
        outcome=outcome_source["outcome"],
        evidence=outcome_source["evidence"],
        producer="i5_outcome_v4",
        source_sha256=sha256_bytes(canonical_json_bytes(outcome_source)),
    )
    eligibility = {
        "presumed_atomic": "included",
        "needs_decomposition": "pending_decomposition",
        "not_judgeable": "excluded_not_judgeable",
        "metadata": "metadata",
        "unresolved_scope": "unresolved_scope",
    }[atomicity]
    view_source = {
        "intervention_id": projection["intervention_id"],
        "judgment_ids": [judgment_id],
        "obligation_ids": [obligation.obligation_id],
        "aggregation_policy": "all_required",
        "evaluation_eligibility": eligibility,
    }
    view = InterventionView(
        view_id=_hash_id("view", view_source),
        source_intervention_id=str(projection["intervention_id"]),
        judgment_ids=[judgment_id],
        obligation_ids=[obligation.obligation_id],
        aggregation_policy="all_required",
        evaluation_eligibility=eligibility,
        source_sha256=sha256_bytes(canonical_json_bytes(view_source)),
    )
    return judgment, outcome, view


def build_judgment_artifacts(
    *,
    scope_release: Path,
    interventions_path: Path,
) -> Tuple[List[JudgmentNode], List[OutcomeObservation], List[InterventionView], Dict[str, Any]]:
    interventions = [
        json.loads(line) for line in interventions_path.read_text().splitlines() if line.strip()
    ]
    intervention_by_id = {item["intervention_id"]: item for item in interventions}
    mappings = [
        InterventionScopeMigration.model_validate_json(line)
        for line in (
            scope_release / "gold" / "intervention_scope_migrations.jsonl"
        ).read_text().splitlines()
        if line.strip()
    ]
    prs = {item.pr_number for item in mappings}
    event_map = _load_source_events(scope_release, prs)
    judgments = []
    outcomes = []
    views = []
    for mapping in mappings:
        judgment, outcome, view = build_judgment(
            intervention_by_id[mapping.intervention_id],
            mapping,
            repo="leanprover-community/mathlib4",
            event_map=event_map,
        )
        judgments.append(judgment)
        outcomes.append(outcome)
        views.append(view)
    atomicity = Counter(item.annotation.atomicity_status for item in judgments)
    eligibility = Counter(item.evaluation_eligibility for item in views)
    speech_acts = Counter(item.speech_act for item in judgments)
    report = {
        "schema_version": "jg-audit1",
        "migration_version": JUDGMENT_MIGRATION_VERSION,
        "judgments": len(judgments),
        "obligations": sum(len(item.obligations) for item in judgments),
        "outcome_observations": len(outcomes),
        "views": len(views),
        "context_relations": sum(len(item.context_relations) for item in judgments),
        "atomicity_status": dict(sorted(atomicity.items())),
        "evaluation_eligibility": dict(sorted(eligibility.items())),
        "speech_act": dict(sorted(speech_acts.items())),
        "outcomes": dict(sorted(Counter(item.outcome for item in outcomes).items())),
        "decomposition_review": [
            {
                "intervention_id": item.source_intervention_id,
                "pr_number": item.pr_number,
                "atomicity_signals": item.annotation.atomicity_signals,
                "claim": item.obligations[0].claim,
                "change_ids": [relation.change_id for relation in item.scope_relations],
            }
            for item in judgments
            if item.annotation.atomicity_status == "needs_decomposition"
        ],
        "judgments_sha256": sha256_bytes(jsonl_bytes(judgments)),
        "outcomes_sha256": sha256_bytes(jsonl_bytes(outcomes)),
        "views_sha256": sha256_bytes(jsonl_bytes(views)),
    }
    return judgments, outcomes, views, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build conservative PR Review v4 jg1 drafts")
    parser.add_argument("scope_release", type=Path)
    parser.add_argument(
        "--interventions",
        type=Path,
        default=LEGACY_INTERVENTIONS_V5,
    )
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--views", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    judgments, outcomes, views, report = build_judgment_artifacts(
        scope_release=args.scope_release,
        interventions_path=args.interventions,
    )
    write_once(args.judgments, jsonl_bytes(judgments))
    write_once(args.outcomes, jsonl_bytes(outcomes))
    write_once(args.views, jsonl_bytes(views))
    write_once(args.report, pretty_json_bytes(report))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
