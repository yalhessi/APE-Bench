"""Offline gates for the Phase 6 historical transformation store."""

import json
from pathlib import Path

from src.mathlib_review.io import sha256_file
from src.mathlib_review.evidence.operators.historical_transformations import (
    build_historical_store,
    retrieve_historical_transformations,
)
from src.mathlib_review.legacy_pipeline.phase6_historical_store import (
    DEFAULT_CORPUS_RELEASE,
    DEFAULT_CUTOFF_RELEASE,
    DEFAULT_INTERVENTIONS,
    DEFAULT_OUT,
    DEFAULT_TARGET_RELEASE,
    build_smoke_queries,
    build_store_rows,
    evaluate_store,
)
from src.mathlib_review.schema import (
    ChangeGraph,
    HistoricalTransformationHit,
    HistoricalTransformationRecord,
    HistoricalTransformationRequest,
    HistoricalTransformationResolution,
    HistoricalTransformationStoreManifest,
    HistoricalTransformationTrigger,
    ReviewEpisodeInput,
)


def _load(path, cls):
    return [cls.model_validate_json(line) for line in path.read_text().splitlines() if line]


def test_store_materializes_separately_hashed_trigger_request_and_resolution_objects():
    triggers = _load(DEFAULT_OUT / "store/triggers.jsonl", HistoricalTransformationTrigger)
    requests = _load(DEFAULT_OUT / "store/requests.jsonl", HistoricalTransformationRequest)
    resolutions = _load(
        DEFAULT_OUT / "store/resolutions.jsonl", HistoricalTransformationResolution
    )
    records = _load(DEFAULT_OUT / "store/records.jsonl", HistoricalTransformationRecord)

    assert len(triggers) == len(requests) == len(resolutions) == len(records) == 113
    assert len({item.trigger_id for item in triggers}) == 113
    assert len({item.request_id for item in requests}) == 113
    assert len({item.resolution_id for item in resolutions}) == 113
    assert all(record.trigger_id != record.request_id != record.resolution_id for record in records)


def test_store_grounds_broad_and_anchorless_annotations_to_the_right_declarations():
    triggers = {
        item.source_intervention_id: item
        for item in _load(DEFAULT_OUT / "store/triggers.jsonl", HistoricalTransformationTrigger)
    }

    assert triggers["pr33098_i04"].context_declaration == (
        "Metric.coveringNumber_two_mul_le_externalCoveringNumber"
    )
    assert {"empty_or_nonempty_split", "named_empty_branch"} <= set(
        triggers["pr33098_i04"].trigger_features
    )
    assert triggers["pr33111_i02"].context_declaration == "injective_of_lt_imp_ne"
    assert "grind_already_used" in triggers["pr33111_i02"].trigger_features


def test_queries_use_only_target_code_features_and_temporally_filter_every_hit():
    store = build_store_rows()
    queries = build_smoke_queries()
    triggers = {item.trigger_id: item for item in store.triggers}
    records = {item.record_id: item for item in store.records}

    assert [item.method_family for item in queries] == [
        "proof_compression", "proof_compression", "structural_rewrite"
    ]
    assert "conditional_definition" in queries[0].target_features
    assert "named_empty_branch" in queries[2].target_features
    for query in queries:
        hits = retrieve_historical_transformations(query, store)
        for hit in hits:
            record = records[hit.record_id]
            trigger = triggers[record.trigger_id]
            assert hit.source_pr_number != query.target_pr_number
            assert trigger.occurred_at < query.cutoff_at


def test_offline_gate_fails_for_source_absence_not_a_hidden_relevant_hit():
    store = build_store_rows()
    queries = build_smoke_queries()
    hits, report = evaluate_store(store, queries)

    assert report["offline_gate"] == "fail"
    assert not report["real_smoke_authorized"]
    assert report["by_family"]["proof_compression"]["useful_hits_at_5"] == 0
    assert report["by_family"]["structural_rewrite"]["useful_hits_at_5"] == 0
    assert all(not item["useful_hit_at_5"] for item in report["queries"])
    assert report["queries"][0]["feature_source_audit"] == {
        "eligible_not_adopted": 1,
        "post_cutoff": 1,
        "same_target_pr": 1,
    }
    assert report["queries"][2]["feature_source_audit"] == {"same_target_pr": 1}
    assert all(isinstance(item, HistoricalTransformationHit) for item in hits)


def test_store_and_query_construction_never_read_target_gold(monkeypatch):
    original = Path.read_text

    def deny_gold(path, *args, **kwargs):
        assert "gold" not in path.parts
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", deny_gold)
    store = build_store_rows()
    queries = build_smoke_queries()
    assert len(store.records) == 113
    assert len(queries) == 3


def test_store_build_is_invariant_to_intervention_order():
    interventions = [
        json.loads(line) for line in DEFAULT_INTERVENTIONS.read_text().splitlines() if line
    ]
    graphs = _load(DEFAULT_CORPUS_RELEASE / "derived/change_graphs.jsonl", ChangeGraph)
    episodes = _load(DEFAULT_CORPUS_RELEASE / "input/episodes.jsonl", ReviewEpisodeInput)
    forward = build_historical_store(interventions, graphs, episodes)
    reverse = build_historical_store(reversed(interventions), graphs, episodes)

    assert [item.source_sha256 for item in forward.triggers] == [
        item.source_sha256 for item in reverse.triggers
    ]
    assert [item.source_sha256 for item in forward.records] == [
        item.source_sha256 for item in reverse.records
    ]


def test_frozen_phase6_manifest_hashes_every_artifact():
    manifest = HistoricalTransformationStoreManifest.model_validate_json(
        (DEFAULT_OUT / "manifest.json").read_text()
    )
    report = json.loads((DEFAULT_OUT / "derived/retrieval_report.json").read_text())

    assert report["offline_gate"] == "fail"
    assert not report["real_smoke_authorized"]
    assert report["raw_event_audit"]["events_scanned"] == 8161
    assert report["raw_event_audit"]["counts"] == {"grind": 2, "rfl_pattern": 0}
    assert {item["pr_number"] for item in report["raw_event_audit"]["matches"]["grind"]} == {
        33111
    }
    for artifact in manifest.artifacts:
        assert sha256_file(DEFAULT_OUT / artifact.path) == artifact.sha256
    for source in manifest.sources:
        assert sha256_file(Path(source.path)) == source.sha256
