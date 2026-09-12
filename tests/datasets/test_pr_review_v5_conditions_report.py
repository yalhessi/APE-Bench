"""`report conditions`: the comparison the design question is read on.

The first production caller of `analysis.reports.compare_conditions`, which implemented the
mean / union / stable protocol in Phase 9 and was called only by its tests since. It reports
sets and not just rates because Phase 9's finding was two arms tied on mean recall while
recovering nearly disjoint obligations -- and at one repetition the sets are the only honest
output, since a rate delta at these denominators is inside the judge's disagreement with
itself.

The real fixture is `pr5-smoke4-rep9`, whose `denominator_correction.json` records the hit
counts by hand: location 14, issue 6, resolution 3, over 17. The synthetic fixtures exercise
the two refusals that make the comparison meaningful: one judge, one denominator.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis import report as report_module

REAL_AUDIT = Path("results/pr_review_v5/audits/pr5-smoke4-rep9/semantic_report.json")
RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.mark.skipif(not REAL_AUDIT.is_file(), reason="needs the rep9 audit on disk")
def test_the_funnel_reproduces_the_audits_own_hand_recorded_counts():
    out = report_module.conditions({"A": "pr5_smoke4_rep9"})

    assert out["denominator"] == 17
    assert out["funnel"]["A"]["location"]["hit"] == 14
    assert out["funnel"]["A"]["issue"]["hit"] == 6
    assert out["funnel"]["A"]["resolution"]["hit"] == 3
    assert out["one_flip_pp"] == 5.9
    assert out["repetitions"] == {"A": 1}


@pytest.mark.skipif(not REAL_AUDIT.is_file() or not RELEASE.is_dir(),
                    reason="needs the rep9 audit and the release on disk")
def test_attention_and_redundancy_are_facts_about_one_run():
    """Neither needs a repetition: the concern distribution of what a run raised, against the
    maintainers', and how many times it wrote up one change target."""

    out = report_module.conditions({"A": "pr5_smoke4_rep9"}, RELEASE)

    attention = out["attention"]
    assert attention["maintainers"]["n"] == 17
    assert 0.0 <= attention["A"]["distance_from_maintainers"] <= 1.0
    # `documentation` (arm spelling) must have been bridged to `docs` (gold spelling), or the
    # docs family reads as disjoint attention when it is the same family.
    assert "documentation" not in attention["A"]["share"]

    redundancy = out["redundancy"]["A"]
    assert redundancy["findings"] == 54
    assert redundancy["findings_per_target"] > 1.0


# --- the two refusals ----------------------------------------------------------------------


def _audit(tmp_path, name, *, identity, obligations, hits):
    """A minimal scored semantic_report.json under a fake audit root."""

    out = tmp_path / "audits" / name
    out.mkdir(parents=True)
    rows = [{"obligation_id": ob,
             "location_hit": ob in hits["location"],
             "issue_status": "hit" if ob in hits["issue"] else "miss",
             "resolution_status": "hit" if ob in hits["resolution"] else "miss"}
            for ob in obligations]
    (out / "semantic_report.json").write_text(json.dumps({
        "scored": True, "judge_identity": identity, "per_obligation": rows,
        "silent_pr_emission": {"candidates": 0, "candidates_per_control_pr": 0.0,
                               "control_pr_numbers": []},
    }))
    return out


def _point_audits_at(monkeypatch, tmp_path):
    def fake_derive(run_name):
        return {"out_dir": tmp_path / "audits" / run_name}
    import src.mathlib_review.judge.runner as judge_runner
    monkeypatch.setattr(judge_runner, "derive_from_run", fake_derive)


def test_conditions_judged_by_different_instruments_are_refused(tmp_path, monkeypatch):
    """`judge_identity` hashes rubric, model, sampling and decode budgets; R0 found two judge
    arms disagreeing on 4 of 18 pairs from decode budgets alone."""

    obs = ["ob:1", "ob:2", "ob:3"]
    _audit(tmp_path, "a", identity="judge-x", obligations=obs,
           hits={"location": obs, "issue": ["ob:1"], "resolution": []})
    _audit(tmp_path, "b", identity="judge-y", obligations=obs,
           hits={"location": obs, "issue": ["ob:2"], "resolution": []})
    _point_audits_at(monkeypatch, tmp_path)

    with pytest.raises(SystemExit, match="different instruments"):
        report_module.conditions({"A": "a", "B": "b"})


def test_conditions_scored_over_different_denominators_are_refused(tmp_path, monkeypatch):
    """The judge scopes obligations to the PRs a run reviewed, so a mismatch means the runs
    did not review the same PRs -- and a recall from one is not a recall from the other."""

    _audit(tmp_path, "a", identity="j", obligations=["ob:1", "ob:2"],
           hits={"location": [], "issue": [], "resolution": []})
    _audit(tmp_path, "b", identity="j", obligations=["ob:1", "ob:2", "ob:3"],
           hits={"location": [], "issue": [], "resolution": []})
    _point_audits_at(monkeypatch, tmp_path)

    with pytest.raises(SystemExit, match="different denominator"):
        report_module.conditions({"A": "a", "B": "b"})


def test_union_and_exclusive_sets_are_the_output_not_just_the_rates(tmp_path, monkeypatch):
    """Phase 9: two arms tied on mean recall while recovering nearly disjoint obligations. A
    report that printed only the two rates would have called them equivalent."""

    obs = ["ob:1", "ob:2", "ob:3", "ob:4"]
    _audit(tmp_path, "a", identity="j", obligations=obs,
           hits={"location": obs, "issue": ["ob:1", "ob:2"], "resolution": []})
    _audit(tmp_path, "b", identity="j", obligations=obs,
           hits={"location": obs, "issue": ["ob:3", "ob:4"], "resolution": []})
    _point_audits_at(monkeypatch, tmp_path)

    out = report_module.conditions({"A": "a", "B": "b"})
    issue = out["by_level"]["issue"]

    assert out["funnel"]["A"]["issue"]["recall"] == out["funnel"]["B"]["issue"]["recall"] == 0.5
    assert issue["exclusive_ids"] == {"A": ["ob:1", "ob:2"], "B": ["ob:3", "ob:4"]}
    assert issue["combined_union_recall"] == 1.0


# --- examination depth: the claim that one call does not look deeply -------------------------

PROBE_RUN = "pr5_solo_ape_33438_probe"
PROBE_TRANSCRIPTS = Path(".ape/runs") / PROBE_RUN


@pytest.mark.skipif(not PROBE_TRANSCRIPTS.is_dir() or not RELEASE.is_dir(),
                    reason="needs the probe run's orchestrator tree and the release on disk")
def test_examination_is_read_from_the_transcript_not_asserted_from_the_floor():
    """On 33438 the solo agent made one `file_read` of lines 160-260 of Arctan.lean; the PR's
    two change targets sit at 205-211 and 212-218, and both were also named in searches. So
    2 of 2 examined, from one read -- and on a 912-character PR that is the expected result.
    The exhibit only bites on 33294 (46k characters, 11 files), which is why size is reported
    beside it."""

    out = report_module._examination(PROBE_RUN, RELEASE)
    assert out is not None and "33438" in out, out
    row = out["33438"]

    assert row["targets_total"] == 2
    assert row["targets_examined"] == 2 and row["examined_share"] == 1.0
    assert row["file_reads"] == 1 and row["distinct_files_read"] == 1
    # `searches` counts DISTINCT query strings: `arctan_sqrt_three` was both content-searched
    # and declaration-searched, so seven search calls are six distinct questions. The metric
    # is what the agent asked about, not how many times it pressed the button.
    assert row["searches"] == 6
    assert row["tool_calls"].get("content_search") == 5
    assert row["tool_calls"].get("declaration_search") == 2
    assert row["diff_chars"] == 912 and row["changed_files"] == 1


def test_a_target_counts_as_examined_by_span_overlap_or_by_name(tmp_path, monkeypatch):
    """Two ways to have looked at a declaration: read the lines it lives on, or search for it
    by name. A read that stops short of it and a search for something else count as neither
    -- the metric must be able to say "not examined", or it is the floor restated."""

    import json as _json

    from src.mathlib_review.analysis import trajectory

    class _Turn:
        def __init__(self, items):
            self.items = items

    def use(name, **payload):
        return {"t": "use", "name": name, "v": _json.dumps(payload), "bytes": 1}

    turns = [_Turn([use("file_read", file_path="target/Mathlib/A.lean", line_range=[1, 10]),
                    use("declaration_search", identifier="Foo.named")])]
    monkeypatch.setattr(trajectory, "extract",
                        lambda run_name, *a, **k: {"present": True, "turns_by_pr": {"7": turns}})

    release = tmp_path / "rel"
    (release / "input").mkdir(parents=True)
    (release / "derived").mkdir()
    (release / "input/episodes.jsonl").write_text(_json.dumps(
        {"pr_number": 7, "diff": "x" * 100, "changed_files": ["Mathlib/A.lean"]}) + "\n")

    def target(cid, name, start, end):
        return {"schema_version": "change-target1", "change_id": cid, "episode_id": "ep:7",
                "pr_number": 7, "kind": "declaration", "path": "Mathlib/A.lean",
                "declaration_name": name, "base_entity_ids": [],
                "reviewed_entity_ids": [f"ent:{cid}"], "changed_range_ids": [],
                "diff_fragments": [], "parse_status": "semantic", "source_sha256": "0" * 64}

    def entity(cid, start, end):
        return {"schema_version": "semantic-entity1", "entity_id": f"ent:{cid}",
                "side": "reviewed", "path": "Mathlib/A.lean", "kind": "theorem",
                "name": cid, "span": {"line_start": start, "line_end": end},
                "code": "theorem x : True := trivial", "source_sha256": "0" * 64,
                "parser_version": "test"}

    graph = {"schema_version": "cg1", "graph_id": "g:7", "episode_id": "ep:7", "repo": "r",
             "pr_number": 7, "round_index": 1, "patch_sha256": "0" * 64, "parser_version": "p",
             "changed_ranges": [], "file_coverage": [], "source_sha256": "0" * 64,
             "entities": [entity("a", 2, 5), entity("b", 40, 45), entity("c", 80, 85)],
             "targets": [target("a", "Foo.in_read", 2, 5),
                         target("b", "Foo.named", 40, 45),
                         target("c", "Foo.untouched", 80, 85)]}
    # The fixture must be a real graph or the test tests nothing -- and a skip here would be
    # a structural guard going vacuous, which this repository has been bitten by before. Fail.
    from src.mathlib_review.schema import ChangeGraph
    try:
        ChangeGraph.model_validate(graph)
    except Exception as exc:
        pytest.fail(f"fixture graph does not validate against the schema: {exc}")
    (release / "derived/change_graphs.jsonl").write_text(_json.dumps(graph) + "\n")

    row = report_module._examination("any", release)["7"]
    assert row["targets_total"] == 3
    assert row["targets_examined"] == 2, row   # by read, by name; not the untouched one


# --- repetitions: several runs under one label ------------------------------------------------


@pytest.mark.skipif(not REAL_AUDIT.is_file(), reason="needs the rep9 audit on disk")
def test_several_runs_under_one_label_are_repetitions_of_one_condition():
    """`hit_frequency` is what answers "does it find this every time or once in ten". With the
    same audit twice, every hit is found 2 of 2, mean equals union, and `stable` (two-thirds
    rule: ceil(2*2/3) = 2) equals both -- the degenerate case that pins the plumbing."""

    out = report_module.conditions({"A": ["pr5_smoke4_rep9", "pr5_smoke4_rep9"]})

    assert out["repetitions"] == {"A": 2}
    assert out["runs"] == {"A": ["pr5_smoke4_rep9", "pr5_smoke4_rep9"]}
    issue = out["by_level"]["issue"]["conditions"]["A"]
    assert issue["per_repetition_hits"] == [6, 6]
    assert set(issue["hit_frequency"].values()) == {2}
    assert issue["mean_recall"] == issue["union_recall"] == issue["stable_recall"]
    assert out["funnel"]["A"]["issue"]["hit"] == 6.0
    assert out["funnel"]["A"]["issue"]["per_repetition_hits"] == [6, 6]
    # Control emission is per repetition, never pooled.
    assert len(out["control_emission"]["A"]) == 2


def test_a_condition_found_in_one_repetition_but_not_another_shows_in_the_frequency(
        tmp_path, monkeypatch):
    """The reason to repeat at all. One design that finds an obligation in 1 of 3 runs and one
    that finds it in 3 of 3 have the same union and are not the same reviewer."""

    obs = ["ob:1", "ob:2"]
    _audit(tmp_path, "r1", identity="j", obligations=obs,
           hits={"location": obs, "issue": ["ob:1"], "resolution": []})
    _audit(tmp_path, "r2", identity="j", obligations=obs,
           hits={"location": obs, "issue": [], "resolution": []})
    _audit(tmp_path, "r3", identity="j", obligations=obs,
           hits={"location": obs, "issue": ["ob:1"], "resolution": []})
    _point_audits_at(monkeypatch, tmp_path)

    out = report_module.conditions({"B": ["r1", "r2", "r3"]})
    issue = out["by_level"]["issue"]["conditions"]["B"]

    assert issue["per_repetition_hits"] == [1, 0, 1]
    assert issue["hit_frequency"] == {"ob:1": 2}
    assert issue["stable_min_repetitions"] == 2          # ceil(2 * 3 / 3)
    assert issue["stable_ids"] == ["ob:1"]               # 2 of 3 clears the two-thirds rule
    assert round(issue["mean_recall"], 3) == round(2 / 3 / 2, 3)
    assert issue["union_recall"] == 0.5


def test_the_cli_accepts_comma_separated_repetitions_and_repeated_labels():
    """Either spelling aggregates; a typo that split one condition into two labels would
    silently compare a condition against itself."""

    import inspect

    from src.mathlib_review.review import cli

    source = inspect.getsource(cli._report)
    assert 'names.split(",")' in source
    assert "pairs.setdefault(label, [])" in source
