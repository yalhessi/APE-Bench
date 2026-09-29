"""The probe harness, held to what the post-cutoff probe committed (`docs/plans/2026-09-29-probe-harness.md`).

These read the PR store and the releases under `inputs/`, so they need the linked data stores.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis import probes

SETS = Path("configs/probe_sets")
POST = probes.load_probe_set(SETS / "postcutoff_2026_07_08_v1.yaml")
#: The digest recorded when the validation feedback was first extracted, before this harness.
VAL_FEEDBACK_SHA256 = "215c28a3da9fd9dbf045622c32dd019791a7406f5748678d063a666bc506c10d"


def test_every_set_spec_loads():
    names = {probes.load_probe_set(p).name for p in SETS.glob("*.yaml")}
    assert {"postcutoff_2026_07_08_v1", "val_small12", "dev_medium_0_3_0"} <= names


def test_a_feedback_source_is_a_draw_or_the_release_never_both():
    with pytest.raises(ValueError, match="not both"):
        probes.FeedbackSource(draw="x", prs_of_release=True)
    with pytest.raises(ValueError, match="not both"):
        probes.FeedbackSource()


def test_the_post_cutoff_feedback_re_extracts_exactly():
    assert probes.extract_feedback(POST) == json.loads(POST.feedback_file.read_text())


def test_the_validation_feedback_re_extracts_to_its_recorded_digest():
    val = probes.extract_feedback(probes.load_probe_set(SETS / "val_small12.yaml"))
    digest = hashlib.sha256(json.dumps(val, ensure_ascii=False, indent=1).encode()).hexdigest()
    assert digest == VAL_FEEDBACK_SHA256


def test_a_test_set_pr_is_refused(tmp_path):
    test_pr = sorted(json.loads(probes.TEST_MANIFEST.read_text())["pr_numbers"])[0]
    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "episodes.jsonl").write_text(
        json.dumps({"pr_number": test_pr, "episode_id": "x"}) + "\n")
    spec = probes.ProbeSet(name="t", release=tmp_path, dataset_config=Path("x.yaml"),
                           pr_numbers=[test_pr], feedback={"prs_of_release": True},
                           probe_dir=tmp_path / "probe")
    with pytest.raises(ValueError, match="test-set PRs"):
        probes.extract_feedback(spec)


POST_DIR = Path("results/pr_review_v5/probes/postcutoff-2026-09-29")
VAL_AUDIT = Path("results/pr_review_v5/adjudications/arm-coverage-val-2025-06-2026-03-v1")
VAL_PROBE = Path("results/pr_review_v5/probes/val-small12-2026-09-25")


def test_the_post_cutoff_asks_rebuild_from_the_committed_labels():
    feedback = json.loads(POST.feedback_file.read_text())
    got = probes.agreed_asks(feedback, probes.load_labels(POST_DIR / "readers/labels.A.jsonl"),
                             probes.load_labels(POST_DIR / "readers/labels.B.jsonl"), POST.pr_numbers)
    manifest = json.loads((POST_DIR / "match/ask_manifest.json").read_text())
    assert got["asks"] == manifest["asks"]["post"]
    assert got["families"] == manifest["families"]
    assert got["controls"] == [41271, 41280, 41314, 42238]
    assert {k: v for k, v in json.loads(POST.asks_file.read_text()).items() if k != "source"} == got


def test_the_validation_asks_rebuild_from_the_audit_readers_by_event_id():
    val = probes.load_probe_set(SETS / "val_small12.yaml")
    feedback = probes.extract_feedback(val)
    events = [json.loads(l) for l in (VAL_AUDIT / "events.jsonl").read_text().splitlines()]
    a = probes.relabel_by_event(probes.load_labels(VAL_AUDIT / "reader_A.jsonl"), events, feedback)
    b = probes.relabel_by_event(probes.load_labels(VAL_AUDIT / "reader_B.jsonl"), events, feedback)
    audited = json.loads((VAL_AUDIT / "families.json").read_text())["validation"]["asks"]
    families = probes.relabel_by_event({c: {"family": f} for c, f in audited.items()}, events, feedback)
    got = probes.agreed_asks(feedback, a, b, val.pr_numbers,
                             families={c: v["family"] for c, v in families.items()})
    ids = json.loads((VAL_PROBE / "match/ask_ids.json").read_text())
    sealed = json.loads((VAL_PROBE / "ask_families_SEALED.json").read_text())
    assert {k: v for k, v in got["asks"].items() if v} == {k: sorted(v) for k, v in ids.items()}
    assert got["families"] == {c: f for pr in sealed["families"].values() for c, f in pr.items()}
    # 32080 has round-1 comments, none of which both readers call an ask.
    assert got["controls"] == [26185, 32080, 34935]


def test_a_reader_sees_the_comment_and_its_context_only():
    batch = probes.reader_batch(json.loads(POST.feedback_file.read_text()), POST.pr_numbers)
    assert len(batch) == 17 and all(tuple(r) == probes.READER_FIELDS for r in batch)


DEMO_DIR = Path("results/pr_review_v5/probes/construction-demo-2026-09-29")


def test_the_pass0_models_render_byte_identically_on_both_sets():
    models = probes.render_models(POST.release, POST.pr_numbers)
    assert all(models[pr] == (POST_DIR / f"model_pr{pr}.md").read_text() for pr in POST.pr_numbers)
    val = probes.load_probe_set(SETS / "val_small12.yaml")
    demo = probes.render_models(val.release, [34091, 30458, 32875])
    assert all(demo[pr] == (DEMO_DIR / f"model_pr{pr}.md").read_text() for pr in demo)


def test_a_packet_is_the_committed_one_but_for_its_paths_and_logger(tmp_path):
    spec = POST.model_copy(update={"probe_dir": tmp_path / "probe"})
    (d,) = probes.write_packets(spec, ["X1"], tmp_path / "scratch", prs=[43192])
    old = POST_DIR / "pr43192/X1"
    for name in ("brief.md", "pr.md", "model.md", "diff.patch"):
        assert (d / name).read_bytes() == (old / name).read_bytes(), name
    new_lines, old_lines = (d / "ptool").read_text().splitlines(), (old / "ptool").read_text().splitlines()
    differ = [i for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b]
    assert len(new_lines) == len(old_lines) and differ == [4, 13]  # the session's paths; the logger
    assert "probe log-call" in new_lines[13]


def test_a_finished_session_is_not_rewritten(tmp_path):
    spec = POST.model_copy(update={"probe_dir": tmp_path / "probe"})
    (d,) = probes.write_packets(spec, ["X1"], tmp_path / "scratch", prs=[43192])
    (d / "findings.json").write_text("[]")
    with pytest.raises(FileExistsError, match="finished session"):
        probes.write_packets(spec, ["X1"], tmp_path / "scratch", prs=[43192])


def test_the_logger_writes_the_row_the_old_script_did(tmp_path):
    import subprocess, sys

    out = tmp_path / "out.json"
    out.write_text(json.dumps({"success": True, "compiles": False, "mode": "edit",
                               "errors_introduced_by_your_edit": [1, 2]}))
    probes.log_call(tmp_path / "new.jsonl", "1-2", "lean_verify_edit", '{"path": "x"}', out, 1)
    subprocess.run([sys.executable, str(DEMO_DIR / "bin/log_call.py"), str(tmp_path / "old.jsonl"),
                    "1-2", "lean_verify_edit", '{"path": "x"}', str(out), "1"], check=True)
    assert (tmp_path / "new.jsonl").read_bytes() == (tmp_path / "old.jsonl").read_bytes()


G52_DIR = Path("results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29")
#: Digests of the matcher inputs the committed matchings judged, rebuilt by this harness and checked
#: byte-for-byte against those inputs on 2026-09-29.
MATCH_INPUT_DIGESTS = {
"blinding_SEALED.json": "6b3086faec3e65c8e393e602d8a60f677f35d5db3cf308ee546002f58168bb55",
"blinding_arms_SEALED.json": "14b4794fa6255a2cbc482b436e71564d720f1d1836db114b5db9b71741b72fdc",
"blinding_calib_SEALED.json": "d3ab7faadd7800772125d1adcb08db3dc7920a24eea73935f2f5a2ffe2ead98c",
}
PASS34 = {"F1", "F2", "F3", "F4", "F5", "F6", "F7"}


def _sources():
    solo = lambda run: probes.Source(kind="solo", run=run)
    return {"G1": solo("probe_postcutoff_gpt52_G_rep1"), "G2": solo("probe_postcutoff_gpt52_G_rep2"),
            "K1": solo("probe_postcutoff_gpt52_K_rep1"), "K2": solo("probe_postcutoff_gpt52_K_rep2"),
            "X1": probes.Source(kind="claude"), "X2": probes.Source(kind="claude"),
            "L1": probes.Source(kind="lead", run="probe_postcutoff_lead_rep1"),
            "L2": probes.Source(kind="lead", run="probe_postcutoff_lead_rep2"),
            "Hc": solo("probe_postcutoff_gpt52_Gr_calib2"), "Mc": solo("probe_postcutoff_gpt52_Gm_calib")}


@pytest.mark.parametrize("seal_name", sorted(MATCH_INPUT_DIGESTS))
def test_the_committed_matchings_inputs_rebuild(seal_name, tmp_path):
    feedback, asks = json.loads(POST.feedback_file.read_text()), json.loads(POST.asks_file.read_text())
    probes.match_inputs(POST, feedback, asks, json.loads((G52_DIR / seal_name).read_text()), _sources(), tmp_path)
    h = hashlib.sha256()
    for p in sorted(tmp_path.iterdir()):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    assert h.hexdigest() == MATCH_INPUT_DIGESTS[seal_name]


@pytest.mark.parametrize("seal_name, match_dir, expected, published", [
    ("blinding_SEALED.json", "match_rematch", {"G": 0.125, "K": 0.0625, "X": 0.46875}, {}),
    ("blinding_arms_SEALED.json", "match_arms", {"G": 0.125, "L": 0.125, "X": 0.46875},
     {"L1": 0.0, "L2": 0.0}),
    ("blinding_calib_SEALED.json", "match_calib", {"G": 0.25, "Hc": 0.75, "Mc": 0.25, "X": 1.0}, {}),
])
def test_the_committed_readings_recompute(seal_name, match_dir, expected, published):
    asks = json.loads(POST.asks_file.read_text())
    seal = json.loads((G52_DIR / seal_name).read_text())
    matches = {m: json.loads((G52_DIR / match_dir / f"matches.{m}.json").read_text()) for m in ("1", "2")}
    stats = json.loads((G52_DIR / match_dir / "session_stats.json").read_text())
    got = probes.unblind(asks, seal, matches, stats)
    for m in ("1", "2"):
        assert got[m]["condition_reach"] == pytest.approx(expected)
        assert got[m]["published_reach"] == published
    assert got["agreement"]["three_valued"] == got["agreement"]["cells"]
    in_scope = probes.unblind(asks, seal, matches, stats, scope=PASS34)
    if seal_name == "blinding_SEALED.json":
        assert in_scope["asks"] == 9 and in_scope["1"]["condition_reach"]["X"] == pytest.approx(4 / 9)


def test_a_session_without_a_source_is_refused(tmp_path):
    seal = {"43192": {"R1": "Z1"}}
    with pytest.raises(ValueError, match="no source"):
        probes.match_inputs(POST, {"rows": []}, {"asks": {"43192": []}}, seal, {}, tmp_path)


def test_feedback_is_not_written_while_a_session_is_unfinished(tmp_path):
    import yaml

    from src.mathlib_review.review import cli

    # The post-cutoff set with an empty probe directory: every session is unfinished.
    spec = POST.model_copy(update={"probe_dir": tmp_path / "probe"})
    assert len(probes.unfinished_sessions(spec, ["X1", "X2"])) == 20
    path = tmp_path / "set.yaml"
    path.write_text(yaml.safe_dump(json.loads(spec.model_dump_json())))
    with pytest.raises(SystemExit, match="only after every session"):
        cli.main(["probe", "feedback", "--set", str(path), "--write"])
    assert not spec.feedback_file.exists()
    assert probes.unfinished_sessions(POST, ["X1", "X2"]) == []  # the real set is complete


def test_the_cli_unblinds_as_the_function_does(capsys):
    from src.mathlib_review.review import cli

    assert cli.main(["probe", "unblind", "--set", str(SETS / "postcutoff_2026_07_08_v1.yaml"),
                     "--seal", str(G52_DIR / "blinding_arms_SEALED.json"),
                     "--matches", str(G52_DIR / "match_arms")]) == 0
    got = json.loads(capsys.readouterr().out)
    assert got["1"]["condition_reach"]["L"] == pytest.approx(0.125)


def test_the_audit_flags_what_leaves_the_folder(tmp_path):
    folder = tmp_path / "m1"
    folder.mkdir()
    calls = [{"type": "tool_use", "name": "Read", "input": {"file_path": str(folder / "asks.json")}},
             {"type": "tool_use", "name": "Read", "input": {"file_path": "/research/elsewhere/x.json"}},
             {"type": "tool_use", "name": "Bash", "input": {"command": f"cd {folder} && git log"}},
             {"type": "tool_use", "name": "WebSearch", "input": {"query": "mathlib"}}]
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("\n".join(json.dumps({"message": {"content": [c]}}) for c in calls))
    report = probes.audit_transcript(folder, transcript)
    assert report["calls"] == 4
    assert [f["why"] for f in report["flagged"]] == [
        ["file tool outside", "outside /research/elsewhere/x.json"], ["git"], ["web"]]


def test_the_solo_context_file_is_the_one_test_b_used():
    ref = (G52_DIR / "model_context.jsonl").read_text()
    assert probes.model_context(POST, [41930, 42184, 42814, 43024, 43167, 43192]) == ref


def test_a_set_can_name_its_own_modification_inventory():
    dev = probes.load_probe_set(SETS / "dev_medium_0_3_0.yaml")
    assert dev.inventory != dev.release / "derived/modification_inventory.jsonl"
    models = probes.render_models(dev.release, [33337], dev.inventory)
    assert models[33337].startswith("# The PR model for #33337 (pass 0)")
    assert POST.inventory == POST.release / "derived/modification_inventory.jsonl"


def test_the_matcher_rubric_is_rendered_for_the_counts_and_unchanged_for_six():
    assert probes.matcher_rubric(6, 6) == probes.MATCHER_RUBRIC.read_text()
    five = probes.matcher_rubric(5, 8)
    assert "on eight Mathlib pull requests. Five anonymous reviewers, `R1` to `R5`" in five
    assert "R6" not in five
    one = probes.matcher_rubric(6, 1)
    assert "on one Mathlib pull request. Six anonymous reviewers" in one


def test_a_packet_relative_tmp_path_is_not_flagged_but_a_real_one_is(tmp_path):
    folder = tmp_path / "pr1" / "X1"
    (folder / "tmp").mkdir(parents=True)
    (folder / "tmp" / "a3.json").write_text("{}")
    (folder / "tmp" / "b0.json").write_text("{}")
    calls = [{"type": "tool_use", "name": "Bash",
              "input": {"command": f"D={folder}; python3 -c \"open(D+'/tmp/a3.json')\""}},
             {"type": "tool_use", "name": "Bash",
              "input": {"command": f"D={folder}; python3 -c \"open(D+f'/tmp/b{{i}}.json')\""}},
             {"type": "tool_use", "name": "Bash", "input": {"command": "cat '/tmp/other.json'"}}]
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("\n".join(json.dumps({"message": {"content": [c]}}) for c in calls))
    report = probes.audit_transcript(folder, transcript)
    assert [f["why"] for f in report["flagged"]] == [["outside /tmp/other.json"]]
