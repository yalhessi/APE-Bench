"""Gates for the shared v4 primitives (io helpers, release writing, rep protocol)."""

import pytest

from src.datasets.pr_review_v4.io import (
    canonical_json_bytes,
    display_path,
    extract_json_object,
    git_state,
    jsonl_bytes,
    load_jsonl,
    load_jsonl_optional,
    sealed_from_payload,
    sealed_model,
    sha256_bytes,
)
from src.datasets.pr_review_v4.releases import (
    ArtifactSpec,
    artifact_ref,
    write_artifacts,
)
from src.datasets.pr_review_v4.reports import compare_conditions, rep_summary
from src.datasets.pr_review_v4.schema import InvestigationMethod, MethodApplicability, OperatorRun


# --- io ------------------------------------------------------------------------------


def test_load_jsonl_skips_blank_lines_and_reads_optional_absent_as_empty(tmp_path):
    path = tmp_path / "rows.jsonl"
    row = OperatorRun(
        operator_run_id="operator_run:1", investigation_id="investigation:1",
        operator="x", status="completed", source_sha256="h",
    )
    path.write_bytes(jsonl_bytes([row]) + b"\n   \n")
    assert load_jsonl(path, OperatorRun) == [row]
    assert load_jsonl_optional(tmp_path / "absent.jsonl", OperatorRun) == []


def test_extract_json_object_tolerates_fences_and_prose():
    assert extract_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json_object('verdict:\n{"a": [1, 2]}') == {"a": [1, 2]}
    with pytest.raises(ValueError):
        extract_json_object("no object here")


def test_display_path_is_repo_relative_and_git_state_reports_a_tree_state():
    from pathlib import Path

    assert display_path(Path("inputs/pr_review_v4")) == "inputs/pr_review_v4"
    _commit, tree_state = git_state()
    assert tree_state in {"clean", "dirty", "unknown"}


def test_the_two_sealing_conventions_are_distinct_and_each_is_stable():
    payload = {
        "investigation_id": "investigation:1", "operator": "x", "status": "completed",
        "artifact_ids": [], "result_count": 0, "failure_reason": None,
    }
    from_payload = sealed_from_payload(OperatorRun, "operator_run", payload)
    assert from_payload.operator_run_id == f"operator_run:{from_payload.source_sha256[:24]}"
    assert sealed_from_payload(OperatorRun, "operator_run", payload) == from_payload

    method = sealed_model(
        InvestigationMethod,
        method_id="m.v1",
        applies_when=MethodApplicability(
            subject_kinds=["theorem"], lifecycles=["added"], any_changed_components=["proof"],
        ),
        required_inputs=[], operators=["applicability_check"], max_opportunities=1,
        selection_policy="direct_failure.v1",
    )
    identity = method.model_dump(mode="json", exclude={"source_sha256"})
    assert method.source_sha256 == sha256_bytes(canonical_json_bytes(identity))

    # The conventions hash different things; merging them would rewrite frozen digests.
    as_payload = sealed_from_payload(OperatorRun, "operator_run", payload).source_sha256
    as_model = sealed_model(
        OperatorRun, operator_run_id="operator_run:fixed", **payload
    ).source_sha256
    assert as_payload != as_model


# --- releases ------------------------------------------------------------------------


def test_write_artifacts_hashes_each_artifact_relative_to_its_release_root(tmp_path):
    row = OperatorRun(
        operator_run_id="operator_run:1", investigation_id="investigation:1",
        operator="x", status="completed", source_sha256="h",
    )
    specs = [ArtifactSpec("derived/runs.jsonl", [row], "operator-run1", "operator_runs")]
    (refs,) = (write_artifacts(tmp_path, specs),)
    assert [ref.path for ref in refs] == ["derived/runs.jsonl"]
    assert refs[0].records == 1 and refs[0].role == "operator_runs"
    assert refs[0].sha256 == sha256_bytes(jsonl_bytes([row]))
    # Rewriting identical content is a silent no-op; write_once guards the rest.
    assert [ref.sha256 for ref in write_artifacts(tmp_path, specs)] == [refs[0].sha256]


def test_artifact_ref_records_a_root_relative_path(tmp_path):
    path = tmp_path / "derived" / "x.jsonl"
    path.parent.mkdir()
    path.write_bytes(b"{}\n")
    ref = artifact_ref(path, tmp_path, role="r", schema_version="s", records=1)
    assert ref.path == "derived/x.jsonl"


# --- the three-repetition protocol ----------------------------------------------------


def test_rep_summary_separates_mean_from_union_on_an_unstable_condition():
    """The 0.9.0-shaped reading: per-run recall well below the union across runs.

    Modelled on the 0.9.0 baseline's 3/6, 2/6, 1/6 per-repetition scores, which is what
    established that single-run numbers are noise at these denominators. The historical
    "stable 0/6" figure used the stricter all-repetitions rule; `stable_min_repetitions`
    below is the two-thirds rule Phase 9 reported against, so it is asserted explicitly
    rather than assumed.
    """

    denominator = [f"o{i}" for i in range(1, 7)]
    summary = rep_summary([{"o1", "o2", "o3"}, {"o2", "o4"}, {"o5"}], denominator)

    assert summary.per_repetition_hits == [3, 2, 1]
    assert summary.mean_recall == pytest.approx(2 / 6)
    assert summary.union_ids == ["o1", "o2", "o3", "o4", "o5"]
    assert summary.stable_min_repetitions == 2
    assert summary.stable_ids == ["o2"]  # the only obligation hit twice
    # Under the stricter all-reps rule nothing is stable, as 0.9.0 reported.
    strict = rep_summary(
        [{"o1", "o2", "o3"}, {"o2", "o4"}, {"o5"}], denominator, stable_min_repetitions=3
    )
    assert strict.stable_ids == []
    # The mean/union gap is what says "present in the distribution, under-sampled per run".
    assert summary.sampling_gap == pytest.approx(5 / 6 - 2 / 6)


def test_rep_summary_ignores_hits_outside_the_denominator():
    summary = rep_summary([{"o1", "not_eligible"}], ["o1", "o2"])
    assert summary.per_repetition_hits == [1]
    assert summary.union_ids == ["o1"]


def test_rep_summary_reports_a_fully_reproducible_condition_with_no_sampling_gap():
    """Phase 9's fixed pipeline accepted the identical opportunities in all 3 reps."""

    hits = {"o1", "o5", "o7"}
    summary = rep_summary([hits, hits, hits], [f"o{i}" for i in range(1, 9)])
    assert summary.sampling_gap == pytest.approx(0.0)
    assert summary.stable_ids == sorted(hits)
    assert set(summary.hit_frequency.values()) == {3}


def test_compare_conditions_surfaces_disjointness_not_just_means():
    """Two arms tied on mean recall can still recover disjoint obligations."""

    denominator = [f"o{i}" for i in range(1, 9)]
    summaries = {
        "fixed": rep_summary([{"o1", "o5", "o7"}] * 3, denominator),
        "holistic": rep_summary([{"o2", "o6", "o8"}] * 3, denominator),
    }
    report = compare_conditions(summaries)
    assert report["conditions"]["fixed"]["mean_recall"] == (
        report["conditions"]["holistic"]["mean_recall"]
    )
    assert report["combined_union_recall"] == pytest.approx(6 / 8)
    assert report["exclusive_ids"]["fixed"] == ["o1", "o5", "o7"]


def test_compare_conditions_rejects_mismatched_denominators():
    with pytest.raises(ValueError, match="one denominator"):
        compare_conditions({
            "a": rep_summary([{"o1"}], ["o1", "o2"]),
            "b": rep_summary([{"o1"}], ["o1"]),
        })
