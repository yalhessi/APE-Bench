"""Offline invariants for the PR Review v4 release foundation."""

import copy
import json
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.datasets.pr_review_v4.change_graph import (
    build_change_graph,
    changed_ranges,
    parse_unified_diff,
)
from src.datasets.pr_review_v4.episodes import changed_files_from_diff, project_legacy_record
from src.datasets.pr_review_v4.episode_builder import load_roster, segment_review_rounds
from src.datasets.pr_review_v4.events import build_event_ledger, events_from_bundle
from src.datasets.pr_review_v4.io import jsonl_bytes, sha256_bytes, write_once
from src.datasets.pr_review_v4.legacy.judgment_graph import atomicity_signals, build_judgment
from src.datasets.pr_review_v4.legacy.migrate_interventions import (
    _load_source_events,
    intervention_scope_projection,
)
from src.datasets.pr_review_v4.schema import (
    InterventionScopeMigration,
    ReviewEpisodeInput,
    VisibleText,
)
from src.datasets.pr_review_v4.validate import validate_release


REAL_RECORDS = Path("inputs/pr_review_v2/mathlib_pr_review_v2_annotated_20260612.jsonl")
REAL_BUNDLES = Path("data/pr_review_v2/cache/bundles")
REAL_COMPARES = Path("data/pr_review_v2/cache/compares")
REAL_ROSTER = Path("src/datasets/pr_review_v2/data/mathlib_roster.txt")
REAL_FIRST_ROUND_RELEASE = Path(
    "inputs/pr_review_v4/releases/dev-raw-0.3.0/input/episodes.jsonl"
)
REAL_CHANGE_GRAPH_RELEASE = Path(
    "inputs/pr_review_v4/releases/dev-change-graph-0.5.1"
)
REAL_SCOPE_RELEASE = Path("inputs/pr_review_v4/releases/dev-scope-map-0.6.1")
REAL_JUDGMENT_RELEASE = Path(
    "inputs/pr_review_v4/releases/dev-judgment-draft-0.7.0"
)
REAL_INTERVENTIONS = Path("inputs/pr_review_v3/interventions_v5.jsonl")


DIFF = """diff --git a/Mathlib/A.lean b/Mathlib/A.lean
--- a/Mathlib/A.lean
+++ b/Mathlib/A.lean
@@ -1,1 +1,2 @@
 theorem old : True := by trivial
+theorem added : True := by trivial
"""


def _legacy_record():
    return {
        "schema_version": "pr_review_v2/0.1",
        "repo": "leanprover-community/mathlib4",
        "pr_number": 123,
        "slices": {"merged": True},
        "input": {
            "title": "Add a theorem",
            "description": "A review-time description",
            "description_maybe_post_edited": False,
            "base_sha": "base",
            "head_sha": "reviewed",
            "h0_resolution": "review_commit_id",
            "diff": DIFF,
        },
        "gold": {"comments": [{"body": "rename it"}], "delta_total": [{"patch": "future"}]},
        "validation": {"final_head_sha": "future"},
    }


def test_legacy_projection_is_gold_and_validation_independent():
    original = _legacy_record()
    poisoned = copy.deepcopy(original)
    poisoned["gold"] = {"comments": [{"body": "THE ANSWER"}], "delta_total": ["future code"]}
    poisoned["validation"] = {"final_head_sha": "different", "new_future_field": "leak"}
    poisoned["slices"] = {"merged": False, "new_outcome": "leak"}
    assert jsonl_bytes([project_legacy_record(original)]) == jsonl_bytes(
        [project_legacy_record(poisoned)]
    )


def test_all_real_episode_inputs_are_future_state_independent():
    records = [json.loads(line) for line in REAL_RECORDS.read_text().splitlines() if line.strip()]
    poisoned = copy.deepcopy(records)
    for record in poisoned:
        record["gold"] = {"poison": "future comments, revisions, and outcomes"}
        record["validation"] = {"poison": "post-review timeline"}
        record["slices"] = {"poison": "outcome-derived population tags"}
    expected = jsonl_bytes(project_legacy_record(record) for record in records)
    actual = jsonl_bytes(project_legacy_record(record) for record in poisoned)
    assert actual == expected


def test_allowed_input_change_changes_projection():
    original = _legacy_record()
    changed = copy.deepcopy(original)
    changed["input"]["title"] = "Different title"
    assert jsonl_bytes([project_legacy_record(original)]) != jsonl_bytes(
        [project_legacy_record(changed)]
    )


def test_post_edited_description_is_omitted():
    record = _legacy_record()
    record["input"]["description_maybe_post_edited"] = True
    episode = project_legacy_record(record)
    assert episode.description.text is None
    assert episode.description.provenance == "legacy_post_edit_risk_omitted"


def test_changed_files_include_modifications_additions_and_deletions():
    diff = """diff --git a/Mathlib/A.lean b/Mathlib/A.lean
--- a/Mathlib/A.lean
+++ b/Mathlib/A.lean
diff --git a/dev/null b/Mathlib/New.lean
--- /dev/null
+++ b/Mathlib/New.lean
diff --git a/Mathlib/Old.lean b/dev/null
--- a/Mathlib/Old.lean
+++ /dev/null
"""
    assert changed_files_from_diff(diff) == [
        "Mathlib/A.lean", "Mathlib/New.lean", "Mathlib/Old.lean"
    ]


def _change_graph_episode(diff: str) -> ReviewEpisodeInput:
    return ReviewEpisodeInput(
        episode_id="leanprover-community/mathlib4:123:round1:reviewed",
        repo="leanprover-community/mathlib4",
        pr_number=123,
        round_index=1,
        title=VisibleText(text="Rename theorem", provenance="review_time_verified"),
        description=VisibleText(text="", provenance="absent"),
        base_sha="base",
        reviewed_head_sha="reviewed",
        diff=diff,
        changed_files=changed_files_from_diff(diff),
        patch_sha256=sha256_bytes(diff.encode("utf-8")),
        source_projection_sha256="synthetic",
    )


def test_change_graph_maps_complete_declarations_and_is_deterministic(tmp_path):
    base = """import Mathlib

namespace Demo

theorem old : True := by
  trivial

end Demo
"""
    diff = """diff --git a/Mathlib/A.lean b/Mathlib/A.lean
--- a/Mathlib/A.lean
+++ b/Mathlib/A.lean
@@ -1,8 +1,8 @@
 import Mathlib
 
 namespace Demo
 
-theorem old : True := by
+theorem better : True := by
   trivial
 
 end Demo
"""
    workspace = tmp_path / "base" / "Mathlib"
    workspace.mkdir(parents=True)
    (workspace / "A.lean").write_text(base)
    episode = _change_graph_episode(diff)
    first = build_change_graph(episode, workspace_root=tmp_path)
    second = build_change_graph(episode, workspace_root=tmp_path)
    assert first == second
    assert len(first.changed_ranges) == 1
    declaration = next(item for item in first.targets if item.kind == "declaration")
    assert declaration.declaration_name == "Demo.better"
    assert "theorem old" in declaration.base_code
    assert "theorem better" in declaration.reviewed_code
    assert declaration.changed_range_ids == [first.changed_ranges[0].range_id]
    assert first.file_coverage[0].source_status == "full"
    assert first.file_coverage[0].base_source_sha256
    assert first.file_coverage[0].reviewed_source_sha256


def test_change_graph_keeps_missing_snapshot_as_explicit_coverage(tmp_path):
    diff = """diff --git a/Mathlib/A.lean b/Mathlib/A.lean
--- a/Mathlib/A.lean
+++ b/Mathlib/A.lean
@@ -1 +1 @@
-theorem old : True := by trivial
+theorem better : True := by trivial
"""
    graph = build_change_graph(_change_graph_episode(diff), workspace_root=tmp_path)
    assert graph.file_coverage[0].source_status == "missing_base_snapshot"
    assert graph.file_coverage[0].exclusion_reason == (
        "base file unavailable: base:Mathlib/A.lean"
    )
    assert {item.range_id for item in graph.changed_ranges} == {
        range_id for item in graph.targets for range_id in item.changed_range_ids
    }


def test_change_graph_uses_hashed_blob_cache_when_workspace_is_missing(tmp_path):
    base = "theorem old : True := by trivial\n"
    diff = """diff --git a/Mathlib/A.lean b/Mathlib/A.lean
--- a/Mathlib/A.lean
+++ b/Mathlib/A.lean
@@ -1 +1 @@
-theorem old : True := by trivial
+theorem better : True := by trivial
"""
    cached = tmp_path / "blobs" / "base" / "Mathlib"
    cached.mkdir(parents=True)
    (cached / "A.lean").write_text(base)
    graph = build_change_graph(
        _change_graph_episode(diff),
        workspace_root=tmp_path / "workspaces",
        blob_cache_root=tmp_path / "blobs",
    )
    assert graph.file_coverage[0].source_status == "full_blob_cache"
    assert graph.file_coverage[0].base_source_sha256 == sha256_bytes(base.encode())
    assert any(item.kind == "declaration" for item in graph.targets)


def test_diff_parser_does_not_treat_removed_lean_comment_as_file_header():
    diff = """diff --git a/Mathlib/A.lean b/Mathlib/A.lean
--- a/Mathlib/A.lean
+++ b/Mathlib/A.lean
@@ -1,2 +1 @@
 theorem x : True := by trivial
--- TODO: remove this comment
"""
    episode = _change_graph_episode(diff)
    files = parse_unified_diff(diff)
    ranges = changed_ranges(episode, files)
    assert files[0].old_path == "Mathlib/A.lean"
    assert ranges[0].diff_fragment.endswith("--- TODO: remove this comment\n")
    assert ranges[0].old_span.line_start == 2


def test_episode_schema_rejects_hidden_extra_fields():
    payload = project_legacy_record(_legacy_record()).model_dump(mode="json")
    payload["gold"] = {"comments": []}
    with pytest.raises(ValidationError):
        ReviewEpisodeInput.model_validate(payload)


def test_immutable_write_allows_identical_content_only(tmp_path):
    path = tmp_path / "artifact.jsonl"
    assert write_once(path, b"one\n") is True
    assert write_once(path, b"one\n") is False
    with pytest.raises(FileExistsError):
        write_once(path, b"two\n")


def _raw_bundle():
    return {
        "pr": {
            "number": 123,
            "id": 1000,
            "title": "Add a theorem",
            "created_at": "2025-01-01T00:00:00Z",
            "user": {"login": "author"},
        },
        "reviews": [
            {
                "id": 2000,
                "submitted_at": "2025-01-02T00:00:00Z",
                "user": {"login": "reviewer"},
            }
        ],
        "review_comments": [],
        "issue_comments": [],
        "commits": [
            {
                "sha": "abc",
                "commit": {"committer": {"date": "2025-01-01T12:00:00Z"}},
            }
        ],
        "files": [{"filename": "Mathlib/A.lean", "status": "modified"}],
        "timeline": [],
        "review_threads": [],
        "body_edits": [{"edited_at": "2025-01-01T06:00:00Z"}],
    }


def test_event_extraction_is_deterministic_and_source_addressed(tmp_path):
    bundle_path = tmp_path / "pr_123.json"
    bundle_path.write_text(json.dumps(_raw_bundle()))
    first = events_from_bundle(
        _raw_bundle(), bundle_path=bundle_path, repo="leanprover-community/mathlib4"
    )
    second = events_from_bundle(
        copy.deepcopy(_raw_bundle()),
        bundle_path=bundle_path,
        repo="leanprover-community/mathlib4",
    )
    assert jsonl_bytes(first) == jsonl_bytes(second)
    assert len(first) == 5
    assert len({event.event_id for event in first}) == len(first)
    assert all(event.source_object.sha256 for event in first)
    assert all(event.source_key.startswith("/") for event in first)


def test_event_ledger_reports_complete_bundle_coverage(tmp_path):
    bundles = tmp_path / "bundles"
    bundles.mkdir()
    for pr_number in (123, 124):
        bundle = _raw_bundle()
        bundle["pr"]["number"] = pr_number
        bundle["pr"]["id"] = 1000 + pr_number
        (bundles / f"pr_{pr_number}.json").write_text(json.dumps(bundle))
    events, report = build_event_ledger(
        bundles_dir=bundles, out=tmp_path / "events.jsonl", prs=[123, 124]
    )
    assert report["bundles"] == 2
    assert report["prs"] == 2
    assert report["events"] == len(events) == 10
    assert report["by_type"]["pull_request"] == 2
    assert report["by_type"]["metadata_edit"] == 2


def test_raw_multi_round_reconstruction_preserves_first_round_and_exposes_gaps():
    legacy = {
        int(record["pr_number"]): record
        for record in (
            json.loads(line) for line in REAL_RECORDS.read_text().splitlines() if line.strip()
        )
    }
    frozen_first_round = {
        episode.pr_number: episode
        for episode in (
            ReviewEpisodeInput.model_validate_json(line)
            for line in REAL_FIRST_ROUND_RELEASE.read_text().splitlines()
            if line.strip()
        )
    }
    roster = load_roster(REAL_ROSTER)
    raw = {}
    segment_counts = Counter()
    hydrated = 0
    missing = []
    for bundle_path in sorted(REAL_BUNDLES.glob("pr_*.json")):
        decision, result = segment_review_rounds(
            json.loads(bundle_path.read_text()),
            bundle_path=bundle_path,
            compare_cache=REAL_COMPARES,
            roster=roster,
        )
        if result:
            raw[decision.pr_number] = (result.episodes[0], result.boundaries[0])
            segment_counts[len(result.segments)] += 1
            hydrated += sum(
                segment.hydration_status == "hydrated" for segment in result.segments
            )
            missing.extend(
                (segment.pr_number, segment.round_index, segment.reviewed_head_sha)
                for segment in result.segments
                if segment.hydration_status == "missing_compare"
            )
    assert set(raw) == set(legacy)
    assert set(raw) == set(frozen_first_round)
    assert segment_counts == Counter({1: 92, 2: 31, 3: 13, 4: 1, 5: 1})
    assert sum(rounds * prs for rounds, prs in segment_counts.items()) == 202
    assert hydrated == 198
    assert sorted(missing) == [
        (33047, 3, "038a2a32914fbb36ef756ef20f834904dc5445f2"),
        (33047, 4, "499fd2c74e8b2d12176aad7d1e0a2207b964670f"),
        (33117, 3, "e7f14f3991519baa8a7633ac7ccb4c7c1249f49d"),
        (33152, 2, "1a511fe6ec770785931ce6b56344f3c3f4ca65ce"),
    ]
    for pr_number, (episode, boundary) in raw.items():
        record = legacy[pr_number]
        assert episode == frozen_first_round[pr_number]
        assert episode.title.text == record["input"]["title"]
        assert episode.base_sha == record["input"]["base_sha"]
        assert episode.reviewed_head_sha == record["input"]["head_sha"]
        assert episode.diff == record["input"]["diff"]
        assert boundary.review_started_at == record["validation"]["t1"]
        assert boundary.feedback_window_end == record["validation"]["t_push"]
        if record["input"]["description_maybe_post_edited"]:
            assert episode.description.text is None
        else:
            assert episode.description.text == record["input"]["description"]


def test_real_change_graph_release_has_complete_range_coverage():
    validation = validate_release(REAL_CHANGE_GRAPH_RELEASE)
    report = json.loads(
        (REAL_CHANGE_GRAPH_RELEASE / "derived" / "change_graph_report.json").read_text()
    )
    assert validation["change_graphs"] == 198
    assert validation["changed_ranges"] == 2662
    assert report["range_mapping"] == {
        "semantic": 2536,
        "structural_only": 126,
        "unparsed_only": 0,
    }
    assert report["source_status"] == {
        "full": 653,
        "full_blob_cache": 200,
        "not_lean": 1,
    }


def test_scope_projection_is_outcome_independent():
    intervention = json.loads(REAL_INTERVENTIONS.read_text().splitlines()[0])
    poisoned = copy.deepcopy(intervention)
    poisoned["outcome"] = "POISON"
    poisoned["outcome_evidence"] = "future revision state"
    poisoned["new_future_field"] = {"answer": True}
    assert intervention_scope_projection(poisoned) == intervention_scope_projection(intervention)


def test_real_scope_release_maps_all_anchored_judgeable_code_interventions():
    validation = validate_release(REAL_SCOPE_RELEASE)
    interventions = {
        item["intervention_id"]: item
        for item in (
            json.loads(line) for line in REAL_INTERVENTIONS.read_text().splitlines()
        )
    }
    mappings = [
        json.loads(line)
        for line in (
            REAL_SCOPE_RELEASE / "gold" / "intervention_scope_migrations.jsonl"
        ).read_text().splitlines()
    ]
    anchored = [
        item
        for item in mappings
        if interventions[item["intervention_id"]].get("anchors")
        and interventions[item["intervention_id"]].get("judgeable")
        and not interventions[item["intervention_id"]].get("meta")
    ]
    assert validation["scope_migrations"] == 113
    assert len(anchored) == 80
    assert all(item["status"] == "resolved" and item["resolved_change_ids"] for item in anchored)
    assert all(not item["resolved_change_ids"] for item in mappings if item["status"] == "metadata")
    report = json.loads(
        (REAL_SCOPE_RELEASE / "gold" / "intervention_scope_report.json").read_text()
    )
    assert report["source_event_coverage"] == {
        "referenced_comments": 154,
        "resolved_events": 154,
    }
    assert len(report["review_queue"]) == 14


def test_atomicity_detection_is_conservative():
    assert atomicity_signals(
        "Replace the proof by (1) adding lemma A, (2) adding lemma B."
    ) == ["explicit_numbered_components"]
    assert atomicity_signals(
        "Replace the specialized lemma with a generalized version, adjusting its proof to use hk."
    ) == []


def test_outcome_poison_changes_only_outcome_observation():
    intervention = next(
        json.loads(line)
        for line in REAL_INTERVENTIONS.read_text().splitlines()
        if json.loads(line)["intervention_id"] == "pr33421_i01"
    )
    mapping = next(
        InterventionScopeMigration.model_validate_json(line)
        for line in (
            REAL_SCOPE_RELEASE / "gold" / "intervention_scope_migrations.jsonl"
        ).read_text().splitlines()
        if json.loads(line)["intervention_id"] == "pr33421_i01"
    )
    event_map = _load_source_events(REAL_SCOPE_RELEASE, {33421})
    judgment, outcome, view = build_judgment(
        intervention,
        mapping,
        repo="leanprover-community/mathlib4",
        event_map=event_map,
    )
    poisoned = copy.deepcopy(intervention)
    poisoned["outcome"] = "dropped"
    poisoned["outcome_evidence"] = "poisoned future state"
    poisoned_judgment, poisoned_outcome, poisoned_view = build_judgment(
        poisoned,
        mapping,
        repo="leanprover-community/mathlib4",
        event_map=event_map,
    )
    assert judgment == poisoned_judgment
    assert view == poisoned_view
    assert outcome.observation_id == poisoned_outcome.observation_id
    assert outcome.source_sha256 != poisoned_outcome.source_sha256


def test_real_judgment_draft_release_separates_pending_obligations_and_outcomes():
    validation = validate_release(REAL_JUDGMENT_RELEASE)
    report = json.loads(
        (REAL_JUDGMENT_RELEASE / "gold" / "judgment_report.json").read_text()
    )
    assert validation["judgments"] == 113
    assert validation["outcome_observations"] == 113
    assert validation["intervention_views"] == 113
    assert report["atomicity_status"] == {
        "metadata": 4,
        "needs_decomposition": 9,
        "not_judgeable": 17,
        "presumed_atomic": 80,
        "unresolved_scope": 3,
    }
    assert report["evaluation_eligibility"]["included"] == 80
    assert report["evaluation_eligibility"]["pending_decomposition"] == 9
    assert report["context_relations"] == 41
