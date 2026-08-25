"""Build and evaluate the Phase 6 historical adopted-transformation store."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from ..releases import artifact_ref
from ..io import (
    canonical_json_bytes,
    display_path,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    sha256_file,
    write_once,
)
from ..events import payload_at_source_key
from ..operators.historical_transformations import (
    RETRIEVAL_VERSION,
    STORE_VERSION,
    HistoricalStore,
    build_historical_store,
    build_query,
    retrieve_historical_transformations,
    useful_hit,
)
from ..paths import LEGACY_INTERVENTIONS_V5
from ..schema import (
    ArtifactRef,
    ChangeGraph,
    HistoricalTransformationQuery,
    HistoricalTransformationStoreManifest,
    ReviewEpisodeInput,
    RetrievalCutoff,
    SourceEvent,
)


DEFAULT_INTERVENTIONS = LEGACY_INTERVENTIONS_V5
DEFAULT_CORPUS_RELEASE = Path("inputs/pr_review_v4/releases/dev-scope-map-0.6.1")
DEFAULT_TARGET_RELEASE = Path("inputs/pr_review_v4/releases/dev-pilot-0.9.0")
DEFAULT_CUTOFF_RELEASE = Path("inputs/pr_review_v4/releases/dev-pilot-0.8.11")
DEFAULT_OUT = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1-phase6-history")

TARGETS = {
    "Metric.maximalSeparatedSet_subset": ("proof_compression", "uses_grind"),
    "Metric.card_maximalSeparatedSet": ("proof_compression", "uses_grind"),
    "Metric.coveringNumber_two_mul_le_externalCoveringNumber": (
        "structural_rewrite", "uses_rfl_pattern"
    ),
}


def _source_ref(path: Path, role: str, schema: str, records: int) -> ArtifactRef:
    return ArtifactRef(
        path=display_path(path), role=role, schema_version=schema,
        sha256=sha256_file(path), records=records,
    )


def build_store_rows(
    interventions_path: Path = DEFAULT_INTERVENTIONS,
    corpus_release: Path = DEFAULT_CORPUS_RELEASE,
) -> HistoricalStore:
    interventions = [
        json.loads(line) for line in interventions_path.read_text().splitlines() if line
    ]
    graphs = load_jsonl(corpus_release / "derived/change_graphs.jsonl", ChangeGraph)
    episodes = load_jsonl(corpus_release / "input/episodes.jsonl", ReviewEpisodeInput)
    return build_historical_store(interventions, graphs, episodes)


def build_smoke_queries(
    target_release: Path = DEFAULT_TARGET_RELEASE,
    cutoff_release: Path = DEFAULT_CUTOFF_RELEASE,
) -> List[HistoricalTransformationQuery]:
    graph = next(
        item for item in load_jsonl(target_release / "derived/change_graphs.jsonl", ChangeGraph)
        if item.pr_number == 33098
    )
    cutoff = next(
        item for item in load_jsonl(cutoff_release / "derived/retrieval_cutoffs.jsonl", RetrievalCutoff)
        if item.pr_number == 33098
    )
    target_by_name = {item.declaration_name: item for item in graph.targets}
    return [
        build_query(graph, cutoff, target_by_name[name], family)
        for name, (family, _expected) in TARGETS.items()
    ]


def _resolution_maps(store: HistoricalStore):
    records = {item.record_id: item for item in store.records}
    triggers = {item.trigger_id: item for item in store.triggers}
    resolutions = {item.resolution_id: item for item in store.resolutions}
    return records, triggers, resolutions


def _excluded_feature_sources(
    query: HistoricalTransformationQuery,
    expected_feature: str,
    store: HistoricalStore,
) -> Dict[str, int]:
    records, triggers, resolutions = _resolution_maps(store)
    cutoff = datetime.fromisoformat(query.cutoff_at.replace("Z", "+00:00"))
    counts = Counter()
    for record in records.values():
        if record.method_family != query.method_family:
            continue
        trigger = triggers[record.trigger_id]
        resolution = resolutions[record.resolution_id]
        if expected_feature not in resolution.transformation_features:
            continue
        if record.source_pr_number == query.target_pr_number:
            counts["same_target_pr"] += 1
        elif not trigger.occurred_at:
            counts["missing_timestamp"] += 1
        elif datetime.fromisoformat(trigger.occurred_at.replace("Z", "+00:00")) >= cutoff:
            counts["post_cutoff"] += 1
        elif resolution.outcome != "adopted":
            counts["eligible_not_adopted"] += 1
        else:
            counts["eligible_adopted"] += 1
    return dict(sorted(counts.items()))


def audit_raw_event_coverage(
    corpus_release: Path,
    query: HistoricalTransformationQuery,
) -> Dict:
    cutoff = datetime.fromisoformat(query.cutoff_at.replace("Z", "+00:00"))
    patterns = {
        "grind": re.compile(r"\bgrind\b", re.IGNORECASE),
        "rfl_pattern": re.compile(
            r"(?:with\s*\(?\s*rfl|\|\s*rfl\b|eq_empty_or_nonempty)", re.IGNORECASE
        ),
    }
    matches = {name: [] for name in patterns}
    events = load_jsonl(corpus_release / "source/events.jsonl", SourceEvent)
    for event in events:
        if (
            event.event_type not in {"review_comment", "review", "issue_comment"}
            or not event.occurred_at
            or event.pr_number == query.target_pr_number
            or datetime.fromisoformat(event.occurred_at.replace("Z", "+00:00")) >= cutoff
        ):
            continue
        payload = payload_at_source_key(
            json.loads(Path(event.source_object.path).read_text()), event.source_key
        )
        body = str(payload.get("body") or "") if isinstance(payload, dict) else str(payload)
        for name, pattern in patterns.items():
            if pattern.search(body):
                matches[name].append({
                    "event_id": event.event_id,
                    "pr_number": event.pr_number,
                    "occurred_at": event.occurred_at,
                    "actor": event.actor,
                    "path": payload.get("path") if isinstance(payload, dict) else None,
                    "body_sha256": sha256_bytes(body.encode()),
                })
    return {
        "events_scanned": len(events),
        "target_pr_excluded": query.target_pr_number,
        "cutoff_at": query.cutoff_at,
        "matches": matches,
        "counts": {name: len(rows) for name, rows in matches.items()},
    }


def evaluate_store(
    store: HistoricalStore,
    queries: List[HistoricalTransformationQuery],
    raw_event_audit: Dict | None = None,
) -> Tuple[List, Dict]:
    all_hits = []
    query_rows = []
    family_totals = Counter()
    family_hits = Counter()
    expected_by_name = {name: expected for name, (_family, expected) in TARGETS.items()}
    records, _triggers, resolutions = _resolution_maps(store)
    for query in queries:
        expected = expected_by_name[query.declaration_name]
        hits = retrieve_historical_transformations(query, store, limit=5)
        all_hits.extend(hits)
        useful = [hit for hit in hits if useful_hit(query, hit, store, expected)]
        family_totals[query.method_family] += 1
        family_hits[query.method_family] += bool(useful)
        query_rows.append({
            "query_id": query.query_id,
            "declaration_name": query.declaration_name,
            "method_family": query.method_family,
            "expected_feature_for_hidden_evaluation": expected,
            "retrieved": [
                {
                    "rank": hit.rank,
                    "source_intervention_id": records[hit.record_id].source_intervention_id,
                    "source_pr_number": hit.source_pr_number,
                    "outcome": hit.outcome,
                    "score": hit.trigger_score,
                    "matched_features": hit.matched_features,
                    "transformation_features": resolutions[
                        records[hit.record_id].resolution_id
                    ].transformation_features,
                    "useful": hit in useful,
                }
                for hit in hits
            ],
            "useful_hit_at_5": bool(useful),
            "feature_source_audit": _excluded_feature_sources(query, expected, store),
        })
    by_family = {
        family: {
            "queries": family_totals[family],
            "useful_hits_at_5": family_hits[family],
            "source_recall_at_5": family_hits[family] / family_totals[family],
        }
        for family in sorted(family_totals)
    }
    gate = (
        family_hits["proof_compression"] >= 1
        and family_hits["structural_rewrite"] >= 1
        and sum(family_hits.values()) >= 2
    )
    outcomes = Counter(item.outcome for item in store.resolutions)
    families = Counter(item.method_family for item in store.records)
    report = {
        "schema_version": "historical-transformation-retrieval-report1",
        "store_version": STORE_VERSION,
        "retrieval_version": RETRIEVAL_VERSION,
        "pre_registered_gate": (
            "At least one useful adopted source in each method family and at least two of three "
            "smoke queries with a useful source in the top five."
        ),
        "counts": {
            "records": len(store.records),
            "code_grounded_triggers": sum(item.context_code is not None for item in store.triggers),
            "queries": len(queries),
            "retrieval_hits": len(all_hits),
            "by_method_family": dict(sorted(families.items())),
            "by_outcome": dict(sorted(outcomes.items())),
        },
        "by_family": by_family,
        "queries": query_rows,
        "offline_gate": "pass" if gate else "fail",
        "stop_reason": None if gate else (
            "The current corpus contains no temporally eligible adopted grind transformation and "
            "no temporally eligible adopted empty-branch-to-rfl transformation for these targets."
        ),
        "real_smoke_authorized": gate,
        "raw_event_audit": raw_event_audit,
    }
    return all_hits, report


def build_release(
    interventions_path: Path = DEFAULT_INTERVENTIONS,
    corpus_release: Path = DEFAULT_CORPUS_RELEASE,
    target_release: Path = DEFAULT_TARGET_RELEASE,
    cutoff_release: Path = DEFAULT_CUTOFF_RELEASE,
    out: Path = DEFAULT_OUT,
) -> Tuple[HistoricalTransformationStoreManifest, Dict]:
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        return (
            HistoricalTransformationStoreManifest.model_validate_json(manifest_path.read_text()),
            json.loads((out / "derived/retrieval_report.json").read_text()),
        )
    store = build_store_rows(interventions_path, corpus_release)
    queries = build_smoke_queries(target_release, cutoff_release)
    raw_event_audit = audit_raw_event_coverage(corpus_release, queries[0])
    hits, report = evaluate_store(store, queries, raw_event_audit)
    files = {
        "store/triggers.jsonl": (
            store.triggers, "historical-transformation-trigger1", "historical_triggers"
        ),
        "store/requests.jsonl": (
            store.requests, "historical-transformation-request1", "historical_requests"
        ),
        "store/resolutions.jsonl": (
            store.resolutions, "historical-transformation-resolution1", "historical_resolutions"
        ),
        "store/records.jsonl": (
            store.records, "historical-transformation-record1", "historical_join_records"
        ),
        "derived/queries.jsonl": (
            queries, "historical-transformation-query1", "gold_free_smoke_queries"
        ),
        "derived/retrieval_hits.jsonl": (
            hits, "historical-transformation-hit1", "temporally_eligible_retrieval_hits"
        ),
    }
    refs = []
    for relative, (rows, schema, role) in files.items():
        path = out / relative
        write_once(path, jsonl_bytes(rows))
        refs.append(artifact_ref(path, out, role, schema, len(rows)))
    report_path = out / "derived/retrieval_report.json"
    write_once(report_path, pretty_json_bytes(report))
    refs.append(artifact_ref(
        report_path, out, "historical_retrieval_report",
        "historical-transformation-retrieval-report1", 1,
    ))
    source_refs = [
        _source_ref(interventions_path, "curated_historical_interventions", "i5", 113),
        _source_ref(
            corpus_release / "derived/change_graphs.jsonl", "historical_review_time_graphs",
            "cg1", 198,
        ),
        _source_ref(
            corpus_release / "input/episodes.jsonl", "historical_review_time_episodes",
            "episode1", 198,
        ),
        _source_ref(
            corpus_release / "source/events.jsonl", "complete_historical_event_ledger",
            "event1", 8161,
        ),
        _source_ref(
            target_release / "derived/change_graphs.jsonl", "smoke_target_graphs", "cg1", 9,
        ),
        _source_ref(
            cutoff_release / "derived/retrieval_cutoffs.jsonl", "generation_safe_cutoffs",
            "retrieval-cutoff1", 9,
        ),
    ]
    manifest_payload = {
        "store_id": "mathlib-pr-review-v4-historical-transformations-phase6",
        "corpus_version": STORE_VERSION,
        "retrieval_version": RETRIEVAL_VERSION,
        "sources": [item.model_dump(mode="json") for item in source_refs],
        "artifacts": [item.model_dump(mode="json") for item in refs],
        "created_at": "2026-07-17T00:00:00-05:00",
    }
    digest = sha256_bytes(canonical_json_bytes(manifest_payload))
    manifest = HistoricalTransformationStoreManifest(
        source_sha256=digest, **manifest_payload
    )
    write_once(manifest_path, pretty_json_bytes(manifest))
    return manifest, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interventions", type=Path, default=DEFAULT_INTERVENTIONS)
    parser.add_argument("--corpus-release", type=Path, default=DEFAULT_CORPUS_RELEASE)
    parser.add_argument("--target-release", type=Path, default=DEFAULT_TARGET_RELEASE)
    parser.add_argument("--cutoff-release", type=Path, default=DEFAULT_CUTOFF_RELEASE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    _, report = build_release(
        args.interventions, args.corpus_release, args.target_release, args.cutoff_release, args.out
    )
    print(json.dumps({
        "output": str(args.out),
        "offline_gate": report["offline_gate"],
        "real_smoke_authorized": report["real_smoke_authorized"],
        "by_family": report["by_family"],
        "stop_reason": report["stop_reason"],
    }, indent=2))


if __name__ == "__main__":
    main()
