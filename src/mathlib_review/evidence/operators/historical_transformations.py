"""Typed historical transformation store and temporally safe trigger retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from src.mathlib_review.io import canonical_json_bytes, sha256_bytes
from src.mathlib_review.schema import (
    ChangeGraph,
    ChangeTarget,
    HistoricalTransformationHit,
    HistoricalTransformationQuery,
    HistoricalTransformationRecord,
    HistoricalTransformationRequest,
    HistoricalTransformationResolution,
    HistoricalTransformationTrigger,
    ReviewEpisodeInput,
    RetrievalCutoff,
)


STORE_VERSION = "historical-transformation-store/1"
RETRIEVAL_VERSION = "method-trigger-feature-retrieval/1"
_FENCE_RE = re.compile(r"```(?:suggestion|lean)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class HistoricalStore:
    triggers: List[HistoricalTransformationTrigger]
    requests: List[HistoricalTransformationRequest]
    resolutions: List[HistoricalTransformationResolution]
    records: List[HistoricalTransformationRecord]


def _digest(payload: Mapping) -> str:
    return sha256_bytes(canonical_json_bytes(dict(payload)))


def method_family(concern: str, text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in (
        "with (rfl", "with rfl", "| rfl", "by_cases!", "case split", "empty branch",
        "branch binder", "pattern-match",
    )):
        return "structural_rewrite"
    if concern == "proof-golf" or any(token in lowered for token in (
        "grind", "simp_all", "one-liner", "shorter proof", "proof with", "proof to",
    )):
        return "proof_compression"
    return "other"


def trigger_features(code: str) -> List[str]:
    lowered = code.lower()
    features = set()
    if "by_cases" in code:
        features.add("explicit_by_cases")
    if "rcases" in code:
        features.add("explicit_rcases")
    if "eq_empty_or_nonempty" in code:
        features.add("empty_or_nonempty_split")
    if "eq_empty_or_nonempty" in code and re.search(r"\bh_empty\b", code):
        features.add("named_empty_branch")
    if "if h :" in code or "if h:" in code or "dite" in code:
        features.add("conditional_definition")
    if "grind" in lowered:
        features.add("grind_already_used")
    if "simp only" in lowered:
        features.add("explicit_simp_only")
    if "obtain " in lowered or "rcases " in lowered:
        features.add("explicit_destructuring")
    proof = code.split(":=", 1)[-1] if ":=" in code else code
    proof_lines = [line for line in proof.splitlines() if line.strip()]
    if len(proof_lines) <= 4:
        features.add("short_proof")
    elif len(proof_lines) >= 8:
        features.add("long_proof")
    if sum(1 for line in proof_lines if line.lstrip().startswith("·")) >= 2:
        features.add("multiple_explicit_branches")
    return sorted(features)


def transformation_features(text: str) -> List[str]:
    lowered = text.lower()
    features = set()
    if "grind" in lowered:
        features.add("uses_grind")
    if re.search(r"(?:with\s*\(?|\|\s*)rfl\b", text):
        features.add("uses_rfl_pattern")
    if "by_cases!" in text:
        features.add("uses_by_cases_bang")
    if "simp_all" in lowered:
        features.add("uses_simp_all")
    if re.search(r"\bsimp\b", lowered):
        features.add("uses_simp")
    if "attribute [grind" in lowered:
        features.add("adds_grind_attribute")
    if "one-liner" in lowered or "one line" in lowered:
        features.add("requests_one_line_proof")
    if "rename" in lowered or "name" in lowered and " to `" in lowered:
        features.add("renames_declaration")
    if "existing lemma" in lowered or "use the lemma" in lowered:
        features.add("uses_existing_lemma")
    if "remove" in lowered or "replace" in lowered:
        features.add("replacement_request")
    return sorted(features)


def _exact_replacement(comments: Sequence[Mapping]) -> Optional[str]:
    for comment in comments:
        match = _FENCE_RE.search(str(comment.get("body") or ""))
        if match:
            return match.group(1).strip()
    return None


def _target_span(graph: ChangeGraph, target: ChangeTarget) -> List[Tuple[int, int]]:
    ranges = {item.range_id: item for item in graph.changed_ranges}
    return [
        (ranges[range_id].reviewed_span.line_start, ranges[range_id].reviewed_span.line_end)
        for range_id in target.changed_range_ids
        if range_id in ranges and ranges[range_id].reviewed_span is not None
    ]


def _context_for_intervention(
    intervention: Mapping,
    graphs_by_pr: Mapping[int, Sequence[ChangeGraph]],
) -> Tuple[Optional[ChangeGraph], Optional[ChangeTarget], Optional[str]]:
    best = None
    ask = str(intervention.get("canonical_ask") or "")
    for anchor in intervention.get("anchors", []):
        for graph in graphs_by_pr.get(int(intervention["pr_number"]), []):
            for target in graph.targets:
                if target.path != anchor.get("path"):
                    continue
                spans = _target_span(graph, target)
                overlap = max((
                    max(0, min(end, int(anchor["line_end"])) - max(start, int(anchor["line_start"])) + 1)
                    for start, end in spans
                ), default=0)
                distance = min((abs(start - int(anchor["line_start"])) for start, _ in spans), default=10**9)
                leaf_name = (target.declaration_name or "").rsplit(".", 1)[-1]
                name_match = bool(leaf_name and leaf_name in ask)
                score = (name_match, overlap > 0, overlap, -distance, -graph.round_index)
                if best is None or score > best[0]:
                    best = (score, graph, target, str(anchor.get("path") or ""))
    if best is None:
        for graph in graphs_by_pr.get(int(intervention["pr_number"]), []):
            for target in graph.targets:
                leaf_name = (target.declaration_name or "").rsplit(".", 1)[-1]
                if leaf_name and leaf_name in ask:
                    score = (len(leaf_name), -graph.round_index, target.change_id)
                    if best is None or score > best[0]:
                        best = (score, graph, target, target.path)
    if best is None:
        return None, None, None
    return best[1], best[2], best[3]


def build_historical_store(
    interventions: Iterable[Mapping],
    graphs: Iterable[ChangeGraph],
    episodes: Iterable[ReviewEpisodeInput],
) -> HistoricalStore:
    graphs_by_pr: Dict[int, List[ChangeGraph]] = {}
    for graph in graphs:
        graphs_by_pr.setdefault(graph.pr_number, []).append(graph)
    episodes_by_pr: Dict[int, List[ReviewEpisodeInput]] = {}
    for episode in episodes:
        episodes_by_pr.setdefault(episode.pr_number, []).append(episode)

    triggers, requests, resolutions, records = [], [], [], []
    for intervention in sorted(interventions, key=lambda item: item["intervention_id"]):
        comments = sorted(
            intervention.get("source_comments", []),
            key=lambda item: (item.get("submitted_at") or "", item.get("id") or ""),
        )
        occurred_at = next((item.get("submitted_at") for item in comments if item.get("submitted_at")), None)
        reviewer = next((item.get("author") for item in comments if item.get("author")), None)
        all_text = "\n".join([
            str(intervention.get("canonical_ask") or ""),
            *[str(item.get("body") or "") for item in comments],
        ])
        family = method_family(str(intervention.get("concern") or ""), all_text)
        graph, target, context_path = _context_for_intervention(intervention, graphs_by_pr)
        fallback_episode = next(iter(episodes_by_pr.get(int(intervention["pr_number"]), [])), None)
        context_code = (target.reviewed_code or target.base_code) if target else None
        context_hash = sha256_bytes(context_code.encode()) if context_code else None
        trigger_payload = {
            "source_intervention_id": intervention["intervention_id"],
            "repo": "leanprover-community/mathlib4",
            "source_pr_number": int(intervention["pr_number"]),
            "source_episode_id": graph.episode_id if graph else (fallback_episode.episode_id if fallback_episode else None),
            "source_snapshot_sha": graph.reviewed_head_sha if graph else (
                fallback_episode.reviewed_head_sha if fallback_episode else None
            ),
            "method_family": family,
            "concern": str(intervention.get("concern") or ""),
            "context_path": context_path,
            "context_declaration": target.declaration_name if target else None,
            "context_code": context_code,
            "context_sha256": context_hash,
            "trigger_features": trigger_features(context_code or ""),
            "reviewer": reviewer,
            "occurred_at": occurred_at,
        }
        trigger_digest = _digest(trigger_payload)
        trigger = HistoricalTransformationTrigger(
            trigger_id=f"historical-trigger:{trigger_digest[:24]}",
            source_sha256=trigger_digest,
            **trigger_payload,
        )
        replacement = _exact_replacement(comments)
        request_payload = {
            "trigger_id": trigger.trigger_id,
            "canonical_ask": str(intervention.get("canonical_ask") or ""),
            "source_comment_ids": [str(item.get("id")) for item in comments if item.get("id")],
            "source_comment_bodies": [str(item.get("body") or "") for item in comments],
            "request_features": transformation_features(all_text),
        }
        request_digest = _digest(request_payload)
        request = HistoricalTransformationRequest(
            request_id=f"historical-request:{request_digest[:24]}",
            source_sha256=request_digest,
            **request_payload,
        )
        outcome = str(intervention.get("outcome") or "unknown")
        confidence = "high" if outcome in {"adopted", "dropped"} else (
            "medium" if outcome in {"partially_adopted", "contested"} else "low"
        )
        exceptions = []
        if outcome == "partially_adopted":
            exceptions.append("Only part of the requested transformation was adopted.")
        elif outcome == "dropped":
            exceptions.append("The source author did not adopt this request.")
        elif outcome == "unknown":
            exceptions.append("Available revision evidence cannot establish adoption.")
        resolution_payload = {
            "request_id": request.request_id,
            "outcome": outcome,
            "outcome_confidence": confidence,
            "resolution_evidence": str(intervention.get("outcome_evidence") or ""),
            "exact_replacement": replacement,
            "transformation_features": transformation_features(all_text + "\n" + (replacement or "")),
            "exceptions": exceptions,
        }
        resolution_digest = _digest(resolution_payload)
        resolution = HistoricalTransformationResolution(
            resolution_id=f"historical-resolution:{resolution_digest[:24]}",
            source_sha256=resolution_digest,
            **resolution_payload,
        )
        record_payload = {
            "trigger_id": trigger.trigger_id,
            "request_id": request.request_id,
            "resolution_id": resolution.resolution_id,
            "source_intervention_id": intervention["intervention_id"],
            "source_pr_number": int(intervention["pr_number"]),
            "method_family": family,
        }
        record_digest = _digest(record_payload)
        record = HistoricalTransformationRecord(
            record_id=f"historical-record:{record_digest[:24]}",
            source_sha256=record_digest,
            **record_payload,
        )
        triggers.append(trigger)
        requests.append(request)
        resolutions.append(resolution)
        records.append(record)
    return HistoricalStore(triggers, requests, resolutions, records)


def build_query(
    graph: ChangeGraph,
    cutoff: RetrievalCutoff,
    target: ChangeTarget,
    family: str,
) -> HistoricalTransformationQuery:
    code = target.reviewed_code or target.base_code or ""
    payload = {
        "target_episode_id": graph.episode_id,
        "target_pr_number": graph.pr_number,
        "primary_change_id": target.change_id,
        "declaration_name": target.declaration_name or target.change_id,
        "cutoff_at": cutoff.review_started_at,
        "method_family": family,
        "target_features": trigger_features(code),
        "target_code_sha256": sha256_bytes(code.encode()),
    }
    digest = _digest(payload)
    return HistoricalTransformationQuery(
        query_id=f"historical-query:{digest[:24]}", source_sha256=digest, **payload
    )


def _trigger_score(query: HistoricalTransformationQuery, trigger: HistoricalTransformationTrigger) -> Tuple[float, List[str]]:
    query_features = set(query.target_features)
    source_features = set(trigger.trigger_features)
    matched = sorted(query_features & source_features)
    union = query_features | source_features
    score = (len(matched) / len(union) * 10.0) if union else 0.0
    weights = {
        "named_empty_branch": 8.0,
        "empty_or_nonempty_split": 5.0,
        "conditional_definition": 4.0,
        "explicit_by_cases": 3.0,
        "multiple_explicit_branches": 2.0,
        "long_proof": 1.0,
    }
    score += sum(weights.get(feature, 0.5) for feature in matched)
    return round(score, 8), matched


def retrieve_historical_transformations(
    query: HistoricalTransformationQuery,
    store: HistoricalStore,
    limit: int = 5,
) -> List[HistoricalTransformationHit]:
    trigger_by_id = {item.trigger_id: item for item in store.triggers}
    resolution_by_id = {item.resolution_id: item for item in store.resolutions}
    cutoff = datetime.fromisoformat(query.cutoff_at.replace("Z", "+00:00"))
    ranked = []
    for record in store.records:
        trigger = trigger_by_id[record.trigger_id]
        if record.method_family != query.method_family:
            continue
        if record.source_pr_number == query.target_pr_number or not trigger.occurred_at:
            continue
        occurred = datetime.fromisoformat(trigger.occurred_at.replace("Z", "+00:00"))
        if occurred >= cutoff:
            continue
        score, matched = _trigger_score(query, trigger)
        ranked.append((score, occurred.timestamp(), record.record_id, record, trigger, matched))
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    hits = []
    for rank, (score, _timestamp, _record_id, record, trigger, matched) in enumerate(ranked[:limit], 1):
        resolution = resolution_by_id[record.resolution_id]
        payload = {
            "query_id": query.query_id,
            "record_id": record.record_id,
            "rank": rank,
            "trigger_score": score,
            "matched_features": matched,
            "outcome": resolution.outcome,
            "source_pr_number": record.source_pr_number,
            "occurred_at": trigger.occurred_at,
        }
        digest = _digest(payload)
        hits.append(HistoricalTransformationHit(
            hit_id=f"historical-hit:{digest[:24]}", source_sha256=digest, **payload
        ))
    return hits


def useful_hit(
    _query: HistoricalTransformationQuery,
    hit: HistoricalTransformationHit,
    store: HistoricalStore,
    expected_feature: str,
) -> bool:
    records = {item.record_id: item for item in store.records}
    resolutions = {item.resolution_id: item for item in store.resolutions}
    resolution = resolutions[records[hit.record_id].resolution_id]
    return resolution.outcome == "adopted" and expected_feature in resolution.transformation_features
