"""Offline release validation for PR Review v4."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from .episodes import changed_files_from_diff
from .change_graph import validate_change_graph
from .events import expected_source_keys, payload_at_source_key
from .io import canonical_json_bytes, sha256_bytes, sha256_directory, sha256_file
from .schema import (
    DatasetManifest,
    ChangeGraph,
    FunnelDecision,
    ReviewEpisodeBoundary,
    ReviewEpisodeInput,
    ReviewRoundSegment,
    InterventionScopeMigration,
    InterventionView,
    JudgmentNode,
    OutcomeObservation,
    SourceEvent,
)


def validate_release(release_dir: Path) -> Dict[str, int]:
    manifest = DatasetManifest.model_validate_json((release_dir / "manifest.json").read_text())
    artifacts = (
        manifest.source_artifacts
        + manifest.input_artifacts
        + manifest.gold_artifacts
        + manifest.derived_artifacts
    )
    for artifact in artifacts:
        path = release_dir / artifact.path
        if not path.is_file():
            raise ValueError(f"manifest artifact missing: {artifact.path}")
        actual = sha256_file(path)
        if actual != artifact.sha256:
            raise ValueError(
                f"artifact hash mismatch for {artifact.path}: {actual} != {artifact.sha256}"
            )

    episode_ref = next(
        (artifact for artifact in manifest.input_artifacts if artifact.schema_version == "episode1"),
        None,
    )
    if episode_ref is None:
        raise ValueError("manifest contains no episode1 input artifact")
    episode_path = release_dir / episode_ref.path
    episodes: List[ReviewEpisodeInput] = [
        ReviewEpisodeInput.model_validate_json(line)
        for line in episode_path.read_text().splitlines()
        if line.strip()
    ]
    if sorted({episode.pr_number for episode in episodes}) != manifest.pr_numbers:
        raise ValueError("episode PR set does not match manifest")
    if len({episode.episode_id for episode in episodes}) != len(episodes):
        raise ValueError("duplicate episode_id")
    for episode in episodes:
        if sha256_bytes(episode.diff.encode("utf-8")) != episode.patch_sha256:
            raise ValueError(f"{episode.episode_id}: patch hash mismatch")
        if changed_files_from_diff(episode.diff) != episode.changed_files:
            raise ValueError(f"{episode.episode_id}: changed-files index mismatch")
        if episode.description.provenance == "legacy_post_edit_risk_omitted":
            if episode.description.text is not None:
                raise ValueError(f"{episode.episode_id}: risky legacy description was not omitted")

    events: List[SourceEvent] = []
    event_ref = next(
        (artifact for artifact in manifest.source_artifacts if artifact.schema_version == "event1"),
        None,
    )
    if event_ref:
        events = [
            SourceEvent.model_validate_json(line)
            for line in (release_dir / event_ref.path).read_text().splitlines()
            if line.strip()
        ]
        if len({event.event_id for event in events}) != len(events):
            raise ValueError("duplicate event_id")
        if not set(manifest.pr_numbers).issubset({event.pr_number for event in events}):
            raise ValueError("event ledger does not cover every episode PR")
        by_source: Dict[str, List[SourceEvent]] = defaultdict(list)
        for event in events:
            by_source[event.source_object.path].append(event)
        for source_path, source_events in by_source.items():
            path = Path(source_path)
            if not path.is_file():
                raise ValueError(f"event source bundle missing: {source_path}")
            expected_hash = source_events[0].source_object.sha256
            if sha256_file(path) != expected_hash:
                raise ValueError(f"event source bundle hash mismatch: {source_path}")
            if any(event.source_object.sha256 != expected_hash for event in source_events):
                raise ValueError(f"inconsistent source bundle hashes: {source_path}")
            bundle = json.loads(path.read_text())
            actual_keys = {event.source_key for event in source_events}
            expected_keys = set(expected_source_keys(bundle))
            if actual_keys != expected_keys:
                raise ValueError(f"event source coverage mismatch: {source_path}")
            for event in source_events:
                payload = payload_at_source_key(bundle, event.source_key)
                payload_hash = sha256_bytes(canonical_json_bytes(payload))
                if payload_hash != event.payload_sha256:
                    raise ValueError(
                        f"event payload hash mismatch: {source_path}{event.source_key}"
                    )

    boundary_ref = next(
        (
            artifact
            for artifact in manifest.gold_artifacts
            if artifact.schema_version == "episode-boundary1"
        ),
        None,
    )
    boundaries: List[ReviewEpisodeBoundary] = []
    if boundary_ref:
        boundaries = [
            ReviewEpisodeBoundary.model_validate_json(line)
            for line in (release_dir / boundary_ref.path).read_text().splitlines()
            if line.strip()
        ]
        if {item.episode_id for item in boundaries} != {item.episode_id for item in episodes}:
            raise ValueError("episode boundary IDs do not match episode input IDs")
        compare_source = next(
            (item for item in manifest.sources if item.role == "git_compare_cache"), None
        )
        if compare_source:
            compare_dir = Path(compare_source.path)
            if not compare_dir.is_dir() or sha256_directory(compare_dir) != compare_source.sha256:
                raise ValueError("Git compare cache source hash mismatch")
            for boundary in boundaries:
                matches = list(compare_dir.glob(f"*...{boundary.reviewed_head_sha}.json"))
                if len(matches) != 1 or sha256_file(matches[0]) != boundary.compare_sha256:
                    raise ValueError(f"compare provenance mismatch: {boundary.episode_id}")

    funnel_ref = next(
        (
            artifact
            for artifact in manifest.derived_artifacts
            if artifact.schema_version == "funnel1"
        ),
        None,
    )
    funnels: List[FunnelDecision] = []
    if funnel_ref:
        funnels = [
            FunnelDecision.model_validate_json(line)
            for line in (release_dir / funnel_ref.path).read_text().splitlines()
            if line.strip()
        ]
        included = {item.pr_number for item in funnels if item.included}
        if included != set(manifest.pr_numbers):
            raise ValueError("included funnel PRs do not match episode PRs")

    segment_ref = next(
        (
            artifact
            for artifact in manifest.derived_artifacts
            if artifact.schema_version == "round-segment1"
        ),
        None,
    )
    segments: List[ReviewRoundSegment] = []
    if segment_ref:
        segments = [
            ReviewRoundSegment.model_validate_json(line)
            for line in (release_dir / segment_ref.path).read_text().splitlines()
            if line.strip()
        ]
        if len({item.segment_id for item in segments}) != len(segments):
            raise ValueError("duplicate round segment ID")
        hydrated_ids = {
            item.episode_id for item in segments if item.hydration_status == "hydrated"
        }
        if hydrated_ids != {item.episode_id for item in episodes}:
            raise ValueError("hydrated round segments do not match episode inputs")
        for item in segments:
            if item.hydration_status == "missing_compare" and item.episode_id is not None:
                raise ValueError(f"unhydrated segment has episode ID: {item.segment_id}")
        by_pr: Dict[int, List[int]] = defaultdict(list)
        for item in segments:
            by_pr[item.pr_number].append(item.round_index)
        for pr_number, indices in by_pr.items():
            if sorted(indices) != list(range(1, len(indices) + 1)):
                raise ValueError(f"non-contiguous round indices for PR {pr_number}: {indices}")

    graph_ref = next(
        (
            artifact
            for artifact in manifest.derived_artifacts
            if artifact.schema_version == "cg1"
        ),
        None,
    )
    graphs: List[ChangeGraph] = []
    if graph_ref:
        graphs = [
            ChangeGraph.model_validate_json(line)
            for line in (release_dir / graph_ref.path).read_text().splitlines()
            if line.strip()
        ]
        by_episode = {episode.episode_id: episode for episode in episodes}
        if len({graph.graph_id for graph in graphs}) != len(graphs):
            raise ValueError("duplicate change graph ID")
        if {graph.episode_id for graph in graphs} != set(by_episode):
            raise ValueError("change graph episode IDs do not match episode inputs")
        for graph in graphs:
            validate_change_graph(graph, by_episode[graph.episode_id])

    scope_ref = next(
        (
            artifact
            for artifact in manifest.gold_artifacts
            if artifact.schema_version == "i5-cg1-map1"
        ),
        None,
    )
    scope_migrations: List[InterventionScopeMigration] = []
    if scope_ref:
        scope_migrations = [
            InterventionScopeMigration.model_validate_json(line)
            for line in (release_dir / scope_ref.path).read_text().splitlines()
            if line.strip()
        ]
        if len({item.migration_id for item in scope_migrations}) != len(scope_migrations):
            raise ValueError("duplicate intervention scope migration ID")
        if len({item.intervention_id for item in scope_migrations}) != len(scope_migrations):
            raise ValueError("duplicate intervention ID in scope migrations")
        graphs_by_id = {graph.graph_id: graph for graph in graphs}
        event_ids = {event.event_id for event in events}
        for migration in scope_migrations:
            graph = graphs_by_id.get(migration.graph_id)
            if graph is None or graph.episode_id != migration.episode_id:
                raise ValueError(f"{migration.intervention_id}: unknown change graph")
            change_ids = {item.change_id for item in graph.targets}
            entity_ids = {item.entity_id for item in graph.entities}
            if not set(migration.resolved_change_ids).issubset(change_ids):
                raise ValueError(f"{migration.intervention_id}: unknown resolved change ID")
            if not set(migration.resolved_entity_ids).issubset(entity_ids):
                raise ValueError(f"{migration.intervention_id}: unknown resolved entity ID")
            if not set(migration.source_event_ids).issubset(event_ids):
                raise ValueError(f"{migration.intervention_id}: unknown source event ID")
            contributed = {
                change_id
                for resolution in migration.resolutions
                if resolution.contributes_to_scope
                for change_id in resolution.change_ids
            }
            if contributed != set(migration.resolved_change_ids):
                raise ValueError(f"{migration.intervention_id}: contributing scope mismatch")
            for resolution in migration.resolutions:
                if not set(resolution.change_ids).issubset(change_ids):
                    raise ValueError(f"{resolution.resolution_id}: unknown change ID")
                if not set(resolution.entity_ids).issubset(entity_ids):
                    raise ValueError(f"{resolution.resolution_id}: unknown entity ID")
            if migration.status in {"unresolved", "metadata"} and migration.resolved_change_ids:
                raise ValueError(f"{migration.intervention_id}: status has code targets")
            migration_source = {
                "version": manifest.generator_versions.get("scope_mapping"),
                "intervention_sha256": migration.intervention_sha256,
                "graph_id": migration.graph_id,
                "status": migration.status,
                "resolved_change_ids": migration.resolved_change_ids,
                "source_event_ids": migration.source_event_ids,
                "resolutions": [
                    item.model_dump(mode="json") for item in migration.resolutions
                ],
                "exception_codes": migration.exception_codes,
            }
            source_hash = sha256_bytes(canonical_json_bytes(migration_source))
            if source_hash != migration.source_sha256:
                raise ValueError(f"{migration.intervention_id}: scope source hash mismatch")
            if f"i5-cg1:{source_hash}" != migration.migration_id:
                raise ValueError(f"{migration.intervention_id}: migration ID mismatch")

    judgment_ref = next(
        (item for item in manifest.gold_artifacts if item.schema_version == "jg1"), None
    )
    outcome_ref = next(
        (
            item
            for item in manifest.gold_artifacts
            if item.schema_version == "outcome-observation1"
        ),
        None,
    )
    view_ref = next(
        (item for item in manifest.gold_artifacts if item.schema_version == "view1"), None
    )
    judgments: List[JudgmentNode] = []
    outcomes: List[OutcomeObservation] = []
    views: List[InterventionView] = []
    if any((judgment_ref, outcome_ref, view_ref)):
        if not all((judgment_ref, outcome_ref, view_ref)):
            raise ValueError("judgment, outcome, and view artifacts must be released together")
        judgments = [
            JudgmentNode.model_validate_json(line)
            for line in (release_dir / judgment_ref.path).read_text().splitlines()
            if line.strip()
        ]
        outcomes = [
            OutcomeObservation.model_validate_json(line)
            for line in (release_dir / outcome_ref.path).read_text().splitlines()
            if line.strip()
        ]
        views = [
            InterventionView.model_validate_json(line)
            for line in (release_dir / view_ref.path).read_text().splitlines()
            if line.strip()
        ]
        if len({item.judgment_id for item in judgments}) != len(judgments):
            raise ValueError("duplicate judgment ID")
        if len({item.observation_id for item in outcomes}) != len(outcomes):
            raise ValueError("duplicate outcome observation ID")
        if len({item.view_id for item in views}) != len(views):
            raise ValueError("duplicate intervention view ID")
        mappings_by_intervention = {
            item.intervention_id: item for item in scope_migrations
        }
        judgments_by_id = {item.judgment_id: item for item in judgments}
        outcomes_by_id = {item.observation_id: item for item in outcomes}
        obligation_ids = {
            obligation.obligation_id
            for judgment in judgments
            for obligation in judgment.obligations
        }
        if len(obligation_ids) != sum(len(item.obligations) for item in judgments):
            raise ValueError("duplicate obligation ID")
        for judgment in judgments:
            mapping = mappings_by_intervention.get(judgment.source_intervention_id)
            if mapping is None or mapping.episode_id != judgment.episode_id:
                raise ValueError(f"{judgment.judgment_id}: missing scope migration")
            if judgment.judgment_id != f"judgment:{judgment.source_sha256}":
                raise ValueError(f"{judgment.judgment_id}: judgment ID/source mismatch")
            scoped = {item.change_id for item in judgment.scope_relations}
            reviewed = judgment.annotation.atomicity_status == "reviewed_decomposed"
            if not reviewed and scoped != set(mapping.resolved_change_ids):
                raise ValueError(f"{judgment.judgment_id}: judgment scope differs from migration")
            if not set(judgment.source_event_ids).issubset(event_ids):
                raise ValueError(f"{judgment.judgment_id}: unknown judgment source event")
            for relation in judgment.context_relations:
                if relation.event_id not in judgment.source_event_ids:
                    raise ValueError(f"{judgment.judgment_id}: context event outside source events")
                if relation.antecedent_event_id not in judgment.source_event_ids:
                    raise ValueError(f"{judgment.judgment_id}: context antecedent outside source events")
            for obligation in judgment.obligations:
                if obligation.obligation_id != f"obligation:{obligation.source_sha256}":
                    raise ValueError(f"{obligation.obligation_id}: obligation ID mismatch")
                if reviewed:
                    if not set(obligation.change_ids).issubset(scoped):
                        raise ValueError(f"{obligation.obligation_id}: obligation outside scope")
                    if not set(obligation.source_event_ids).issubset(judgment.source_event_ids):
                        raise ValueError(f"{obligation.obligation_id}: source event outside judgment")
                elif set(obligation.change_ids) != scoped:
                    raise ValueError(f"{obligation.obligation_id}: obligation scope mismatch")
                if not reviewed:
                    source = {
                        "intervention_id": judgment.source_intervention_id,
                        "claim": obligation.claim,
                        "change_ids": obligation.change_ids,
                        "status": obligation.status,
                    }
                    if sha256_bytes(canonical_json_bytes(source)) != obligation.source_sha256:
                        raise ValueError(f"{obligation.obligation_id}: obligation source mismatch")
            if reviewed and {
                change_id for obligation in judgment.obligations
                for change_id in obligation.change_ids
            } != scoped:
                raise ValueError(f"{judgment.judgment_id}: decomposed obligations do not cover scope")
            if set(judgment.outcome_observation_ids) - set(outcomes_by_id):
                raise ValueError(f"{judgment.judgment_id}: unknown outcome observation")
        for outcome in outcomes:
            judgment = judgments_by_id.get(outcome.judgment_id)
            if judgment is None or judgment.source_intervention_id != outcome.source_intervention_id:
                raise ValueError(f"{outcome.observation_id}: unknown judgment")
            reviewed = judgment.annotation.atomicity_status == "reviewed_decomposed"
            if reviewed:
                if outcome.observation_id != f"outcome:{outcome.source_sha256}":
                    raise ValueError(f"{outcome.observation_id}: outcome ID/source mismatch")
            else:
                stable_id = sha256_bytes(
                    canonical_json_bytes([outcome.source_intervention_id, outcome.judgment_id])
                )
                if outcome.observation_id != f"outcome:{stable_id}":
                    raise ValueError(f"{outcome.observation_id}: unstable outcome ID")
            source = {
                "intervention_id": outcome.source_intervention_id,
                "judgment_id": outcome.judgment_id,
                "outcome": outcome.outcome,
                "evidence": outcome.evidence,
                "producer": outcome.producer,
            }
            if not reviewed and sha256_bytes(canonical_json_bytes(source)) != outcome.source_sha256:
                raise ValueError(f"{outcome.observation_id}: outcome source mismatch")
        for view in views:
            if not set(view.judgment_ids).issubset(judgments_by_id):
                raise ValueError(f"{view.view_id}: unknown judgment ID")
            if not set(view.obligation_ids).issubset(obligation_ids):
                raise ValueError(f"{view.view_id}: unknown obligation ID")
            source = {
                "intervention_id": view.source_intervention_id,
                "judgment_ids": view.judgment_ids,
                "obligation_ids": view.obligation_ids,
                "aggregation_policy": view.aggregation_policy,
                "evaluation_eligibility": view.evaluation_eligibility,
            }
            source_hash = sha256_bytes(canonical_json_bytes(source))
            reviewed = any(
                judgments_by_id[item].annotation.atomicity_status == "reviewed_decomposed"
                for item in view.judgment_ids
            )
            valid_source = reviewed or source_hash == view.source_sha256
            if not valid_source or view.view_id != f"view:{view.source_sha256}":
                raise ValueError(f"{view.view_id}: view source mismatch")
    return {
        "episodes": len(episodes),
        "prs": len(set(manifest.pr_numbers)),
        "events": len(events),
        "boundaries": len(boundaries),
        "funnel_candidates": len(funnels),
        "round_segments": len(segments),
        "unhydrated_rounds": sum(
            item.hydration_status != "hydrated" for item in segments
        ),
        "change_graphs": len(graphs),
        "changed_ranges": sum(len(graph.changed_ranges) for graph in graphs),
        "change_targets": sum(len(graph.targets) for graph in graphs),
        "scope_migrations": len(scope_migrations),
        "unresolved_scope_migrations": sum(
            item.status == "unresolved" for item in scope_migrations
        ),
        "judgments": len(judgments),
        "obligations": sum(len(item.obligations) for item in judgments),
        "outcome_observations": len(outcomes),
        "intervention_views": len(views),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Validate a PR Review v4 release")
    parser.add_argument("release", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_release(args.release), indent=2))


if __name__ == "__main__":
    main()
