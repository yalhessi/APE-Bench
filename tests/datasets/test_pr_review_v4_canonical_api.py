"""Offline and production-boundary gates for canonical API discovery."""

import json
from pathlib import Path

from src.datasets.pr_review_v4.io import jsonl_bytes, sha256_file
from src.datasets.pr_review_v4.operators.canonical_api import (
    build_declaration_index,
    is_high_confidence_insert_separation,
    propose_insert_separation_replacement,
    rank_declarations,
)
from src.datasets.pr_review_v4.phase3_canonical_smoke import (
    DEFAULT_OUT,
    DEFAULT_PARENT,
    DEFAULT_PHASE2,
    DEFAULT_WORKSPACES,
    build_artifacts,
)
from src.datasets.pr_review_v4.schema import (
    CanonicalRetrievalHit,
    ChangeGraph,
    DatasetManifest,
    InvestigationTask,
    OpportunityEvidenceArtifact,
    RepositoryDeclaration,
    ReviewEpisodeInput,
    ReviewOpportunity,
)


POSITIVE_CHANGE = "change:d483f48d7e3a4447d26426246409ccd14c957a624be055ff2150a15e27d59768"
CONTROL_CHANGE = "change:3ef5b17a805e3c6337189653431eef93e1c019e02cd250c400ab593a1ea7c57d"


def _load(path, cls):
    return [cls.model_validate_json(line) for line in path.read_text().splitlines() if line]


def _source_rows(change_id):
    graphs = _load(DEFAULT_PARENT / "derived/change_graphs.jsonl", ChangeGraph)
    episodes = _load(DEFAULT_PARENT / "input/episodes.jsonl", ReviewEpisodeInput)
    tasks = _load(
        DEFAULT_PHASE2 / "derived/investigation_tasks.jsonl", InvestigationTask
    )
    graph = next(item for item in graphs if any(
        target.change_id == change_id for target in item.targets
    ))
    target = next(item for item in graph.targets if item.change_id == change_id)
    episode = next(item for item in episodes if item.episode_id == target.episode_id)
    task = next(item for item in tasks if (
        item.method_id == "canonical_api_search.v1"
        and item.primary_change_id == change_id
    ))
    workspace = DEFAULT_WORKSPACES / episode.base_sha
    return target, episode, task, workspace


def test_positive_retrieval_finds_exact_api_without_oracle_text():
    target, episode, task, workspace = _source_rows(POSITIVE_CHANGE)
    declarations = build_declaration_index(workspace, episode.base_sha, target.path)
    hits = rank_declarations(task, target, declarations)
    declaration_by_id = {item.declaration_id: item for item in declarations}
    top = declaration_by_id[hits[0].declaration_id]

    assert len(declarations) == 382
    assert top.fullname == "Metric.isSeparated_insert_of_notMem"
    assert hits[0].rank == 1
    assert hits[0].score == 28
    assert not hits[0].already_used
    assert is_high_confidence_insert_separation(hits[0], top)
    proposal = propose_insert_separation_replacement(target.reviewed_code or "", top)
    assert proposal is not None
    assert "Metric.isSeparated_insert_of_notMem hx_not_mem" in proposal.new_block


def test_canonical_control_suppresses_an_api_already_used_by_target():
    target, episode, task, workspace = _source_rows(CONTROL_CHANGE)
    declarations = build_declaration_index(workspace, episode.base_sha, target.path)
    hits = rank_declarations(task, target, declarations)
    declaration_by_id = {item.declaration_id: item for item in declarations}
    top = declaration_by_id[hits[0].declaration_id]

    assert len(declarations) == 125
    assert top.fullname == "Real.arctan_tan"
    assert hits[0].already_used
    assert not is_high_confidence_insert_separation(hits[0], top)


def test_canonical_index_and_ranking_are_byte_deterministic():
    target, episode, task, workspace = _source_rows(POSITIVE_CHANGE)
    first = build_declaration_index(workspace, episode.base_sha, target.path)
    second = build_declaration_index(workspace, episode.base_sha, target.path)
    assert jsonl_bytes(first) == jsonl_bytes(second)
    assert jsonl_bytes(rank_declarations(task, target, first)) == jsonl_bytes(
        rank_declarations(task, target, second)
    )


def test_phase3_generation_never_reads_gold(monkeypatch):
    original = Path.read_text

    def deny_gold(path, *args, **kwargs):
        assert "gold" not in path.parts
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", deny_gold)
    rows = build_artifacts(
        DEFAULT_PARENT, DEFAULT_PHASE2, DEFAULT_WORKSPACES
    )
    assert len(rows["opportunities"]) == 2


def test_frozen_phase3_release_has_complete_production_lineage():
    manifest = DatasetManifest.model_validate_json((DEFAULT_OUT / "manifest.json").read_text())
    report = json.loads(
        (DEFAULT_OUT / "derived/canonical_retrieval_report.json").read_text()
    )
    declarations = _load(
        DEFAULT_OUT / "derived/repository_declarations.jsonl", RepositoryDeclaration
    )
    hits = _load(
        DEFAULT_OUT / "derived/canonical_retrieval_hits.jsonl", CanonicalRetrievalHit
    )
    evidence = _load(
        DEFAULT_OUT / "derived/opportunity_evidence.jsonl", OpportunityEvidenceArtifact
    )
    opportunities = _load(
        DEFAULT_OUT / "derived/opportunities.jsonl", ReviewOpportunity
    )

    assert report["source_retrieval_gate"] == "pass"
    assert (len(declarations), len(hits), len(evidence), len(opportunities)) == (507, 40, 8, 2)
    evidence_ids = {item.artifact_id for item in evidence}
    assert all(set(item.source_artifact_ids) <= evidence_ids for item in opportunities)
    assert all("gold" not in Path(item.path).parts for item in manifest.derived_artifacts)
    for artifact in manifest.input_artifacts + manifest.derived_artifacts:
        assert sha256_file(DEFAULT_OUT / artifact.path) == artifact.sha256
