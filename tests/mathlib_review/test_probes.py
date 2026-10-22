"""The probe harness, held to what the post-cutoff probe committed (`docs/plans/2026-09-29-probe-harness.md`).

These read the PR store and the releases under `inputs/`, so they need the linked data stores.
"""

from __future__ import annotations

import hashlib
import json
import re
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


def _old_packet(tmp_path, pr=43192, session="X1"):
    """The packet the committed `make_packets.py` writes, rebuilt in `tmp_path`.

    The copies it wrote under the probe dir are gitignored as regenerable, so reading them made
    this test fail on every fresh checkout. The script writes beside itself and reads committed
    inputs, so a copy of it with its model files and wrapper template rebuilds the same bytes.
    """

    import shutil, subprocess, sys

    old = tmp_path / "old"
    (old / "bin").mkdir(parents=True)
    shutil.copy(POST_DIR / "make_packets.py", old)
    shutil.copy(POST_DIR / "bin/ptool.template", old / "bin")
    for model in POST_DIR.glob("model_pr*.md"):
        shutil.copy(model, old)
    subprocess.run([sys.executable, str(old / "make_packets.py"), str(tmp_path / "old_scratch")],
                   check=True, capture_output=True)
    return old / f"pr{pr}" / session


def test_a_packet_is_the_committed_one_but_for_its_paths_and_logger(tmp_path):
    spec = POST.model_copy(update={"probe_dir": tmp_path / "probe"})
    (d,) = probes.write_packets(spec, ["X1"], tmp_path / "scratch", prs=[43192])
    old = _old_packet(tmp_path)
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


def test_harness_blind_inputs_read_claude_as_a_solo_submission(tmp_path):
    """The one reviewer table's seals hold Claude sessions beside solo runs: with `harness_blind` a
    Claude finding's target reads `path:line` where it resolves, as a solo finding's does, no session
    is longer than the solo budget, and no text says "convention" (a word; "conventional" is
    prose); the default inputs are pinned above."""

    feedback, asks = json.loads(POST.feedback_file.read_text()), json.loads(POST.asks_file.read_text())
    seal = json.loads((G52_DIR / "blinding_SEALED.json").read_text())
    stats = probes.match_inputs(POST, feedback, asks, seal, _sources(), tmp_path, harness_blind=True)
    claude = {(pr, label) for pr, labels in seal.items() for label, s in labels.items() if s in ("X1", "X2")}
    located = total = 0
    for pr, label in claude:
        rows = json.loads((tmp_path / f"{label}_pr{pr}.json").read_text())
        assert len(rows) <= probes.SOLO_FINDING_BUDGET
        total += len(rows)
        located += sum(bool(re.fullmatch(r"Mathlib/\S+\.lean(:\d+)?", str(r["target"]))) for r in rows)
    assert total and located / total > 0.5, "most Claude targets resolve to a path"
    for f in tmp_path.glob("*_pr*.json"):
        if not f.name.startswith("asks_"):
            assert not re.search(r"\bconventions?\b", f.read_text(), re.I), f.name
    assert all("targets_unresolved" in st for pr in stats for s, st in stats[pr].items() if s in ("X1", "X2"))


def test_a_packet_ends_with_the_solo_context_section_byte_for_byte(tmp_path):
    """Claude + AP reads the section a DeepSeek AP session read: `--conventions-from` copies it."""

    text = "These are conventions...\n\n- P001 a sentence\n  > an example\n\nThey outrank your judgement."
    ctx = tmp_path / "context.jsonl"
    ctx.write_text(json.dumps({"pr_number": "43192", "sections": [
        {"title": "The PR model (pass 0)", "text": "model"},
        {"title": probes.CONVENTIONS_TITLE, "text": text}]}) + "\n"
        + json.dumps({"pr_number": "43167", "sections": [{"title": "The PR model (pass 0)", "text": "m"}]}) + "\n")
    sections = probes.context_sections(ctx)
    assert sections == {43192: text}, "a row without a conventions section is left out"
    spec = POST.model_copy(update={"probe_dir": tmp_path / "probe", "sessions_from": {}})
    [d] = probes.write_packets(spec, ["TA1"], tmp_path / "scratch", prs=[43192], root=tmp_path, sections=sections)
    assert (d / "brief.md").read_bytes() == probes.BRIEF_X.read_bytes() + f"\n## {probes.CONVENTIONS_TITLE}\n\n{text}".encode()
    with pytest.raises(KeyError, match="no section"):
        probes.write_packets(spec, ["TA1"], tmp_path / "scratch", prs=[43167], root=tmp_path, sections=sections)


def test_a_condition_context_file_keeps_its_controls_sections_and_adds_its_own(tmp_path):
    """The consumer test's strategies differ from the control only in what they append."""

    base = tmp_path / "base.jsonl"
    model = {"title": "The PR model (pass 0)", "text": "model ⁅H ⊔ K, N⁆  kept"}
    base.write_text(json.dumps({"pr_number": 1, "sections": [model]}, ensure_ascii=False) + "\n"
                    + json.dumps({"pr_number": 2, "sections": [{"title": "m", "text": "two"}]}) + "\n")
    added = {"title": "Decision context", "text": "a packet"}
    text = probes.context_with_sections(base, {1: [added]})
    rows = [json.loads(line) for line in text.split("\n") if line]
    assert rows == [{"pr_number": 1, "sections": [model, added]}], "only PR 1, its own section first"
    # At the far end: the solo task renders the control's section, then the added one.
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig, solo_context_block
    composed = tmp_path / "composed.jsonl"
    composed.write_text(text, encoding="utf-8")
    block = solo_context_block(SoloReviewConfig(context_file=composed), 1)
    assert block.index("## The PR model (pass 0)") < block.index("## Decision context") and "a packet" in block
    with pytest.raises(KeyError, match="no row for PRs \\[3\\]"):
        probes.context_with_sections(base, {3: [added]})


def test_a_solo_source_may_name_disjoint_runs_and_refuses_a_pr_in_two(monkeypatch):
    """AP in the one reviewer table is stage AP's ten-PR run and the apt run's four: one label, two runs."""

    by_run = {"a": {1: ("f1", {}), 2: ("f2", {})}, "b": {3: ("f3", {})}, "c": {2: ("g2", {})}}
    monkeypatch.setattr(probes, "_solo", lambda run: by_run[run])
    assert set(probes._solo_runs(["a", "b"])) == {1, 2, 3}
    assert probes._solo_runs("a") == by_run["a"]
    assert probes.Source(kind="solo", run=["a", "b"]).run == ["a", "b"]
    with pytest.raises(ValueError, match="in two of the runs"):
        probes._solo_runs(["a", "c"])


def test_an_unanchored_solo_finding_reads_as_pr_level():
    """A solo finding about the PR as a whole has no anchor (AP2 on 26755, 2026-10-10: "the PR has no
    description"); it reaches the matcher as PR level, not as `None:None`."""

    assert probes._solo_target(None) == probes.PR_LEVEL_TARGET
    assert probes._solo_target({"path": None, "line_start": None}) == probes.PR_LEVEL_TARGET
    assert probes._solo_target({"path": "Mathlib/X.lean", "line_start": 12}) == "Mathlib/X.lean:12"
    assert probes._solo_target({"path": "Mathlib/X.lean", "line_start": None}) == "Mathlib/X.lean"


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


def test_the_historical_unblind_refuses_a_matcher_file_that_misses_cells(tmp_path, capsys):
    """It used to read an absent cell as not reached; the shared report marks that forensic."""

    import shutil

    from src.mathlib_review.review import cli

    folder = tmp_path / "match_arms"
    shutil.copytree(G52_DIR / "match_arms", folder)
    first = json.loads((folder / "matches.1.json").read_text())
    dropped = first["asks"][0]
    first["asks"] = first["asks"][1:]
    (folder / "matches.1.json").write_text(json.dumps(first))
    argv = ["probe", "unblind", "--set", str(SETS / "postcutoff_2026_07_08_v1.yaml"),
            "--seal", str(G52_DIR / "blinding_arms_SEALED.json"), "--matches", str(folder)]
    with pytest.raises(SystemExit, match="miss cells"):
        cli.main(argv)
    assert cli.main(argv + ["--allow-incomplete"]) == 0
    got = json.loads(capsys.readouterr().out)
    assert got["forensic"] is True
    assert any(dropped["ask_id"] in cell for cell in got["missing_cells"]["1"])


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


def test_grepping_the_packets_diff_headers_is_not_git(tmp_path):
    """A reader outlining diff.patch greps for its `diff --git` header lines; that runs no git.
    Running git itself, even in the same command, is still flagged."""
    folder = tmp_path / "m1"
    folder.mkdir()
    calls = [{"type": "tool_use", "name": "Bash",
              "input": {"command": f"cd {folder}/pr1; grep -n \"^diff --git\\|^@@\" diff.patch"}},
             {"type": "tool_use", "name": "Bash",
              "input": {"command": f"cd {folder}; grep -c 'diff --git' diff.patch; git log -1"}}]
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("\n".join(json.dumps({"message": {"content": [c]}}) for c in calls))
    report = probes.audit_transcript(folder, transcript)
    assert [f["why"] for f in report["flagged"]] == [["git"]]
    assert "git log" in report["flagged"][0]["input"]


DEV = probes.load_probe_set(SETS / "dev_medium_0_3_0.yaml")


def _dev_graph(pr):
    from src.mathlib_review.io import jsonl_rows
    from src.mathlib_review.schema import ChangeGraph
    for row in jsonl_rows(DEV.release / "derived/change_graphs.jsonl"):
        if row["pr_number"] == pr and ":round1:" in row["episode_id"]:
            return ChangeGraph.model_validate(row)


def test_a_probe_target_resolves_to_the_declaration_line_the_solo_prompt_asks_for():
    """Real graph. A full name, a unique dotted suffix and a unique short name each land on the
    reviewed entity's first line; a file lands on its first changed line; prose lands nowhere."""
    graph = _dev_graph(33337)
    entity = next(e for e in graph.entities if e.side == "reviewed" and e.fullname and "." in e.fullname
                  and sum(x.fullname == e.fullname for x in graph.entities if x.side == "reviewed") == 1)
    spot = (entity.path, entity.span.line_start)
    assert probes.resolve_target(entity.fullname, graph) == (*spot, "fullname")
    assert probes.resolve_target(f"`{entity.fullname}`", graph) == (*spot, "fullname")
    assert probes.resolve_target(f"{entity.fullname}, Some.other_decl", graph) == (*spot, "fullname")
    changed = sorted(r.reviewed_span.line_start for r in graph.changed_ranges
                     if r.reviewed_span and r.path == entity.path)
    assert probes.resolve_target(entity.path, graph) == (entity.path, changed[0], "file")
    assert probes.resolve_target("the PR description", graph) == (None, None, "unresolved")


def test_a_probe_session_imports_through_the_solo_tail(tmp_path):
    """Two committed Claude sessions' PRs, through `solo_responses` and `finalize`: every
    finding either anchors or is counted as lost, every row the judge will read carries its
    change targets, and the import says what it did not do."""
    spec = DEV.model_copy(update={"pr_numbers": [33337, 33421]})
    report = probes.import_probe_session(spec, "X1", tmp_path / "run")
    assert report["findings_in"] == report["anchored"] + round(report["unanchored_rate"] * report["findings_in"])
    rows = [json.loads(line) for line in (tmp_path / "run" / "findings.jsonl").read_text().splitlines() if line]
    assert rows and all(r["change_ids"] and r["arm"] == "solo_agent" for r in rows)
    assert {r["pr_number"] for r in rows} <= {33337, 33421}
    provenance = json.loads((tmp_path / "run" / "probe_import.json").read_text())
    assert provenance["session"] == "X1" and provenance["issue_kind_placeholder"] == probes.IMPORT_ISSUE_KIND
    assert set(provenance["packets_findings_sha256"]) == {"33337", "33421"}
    assert not (tmp_path / "run" / "run_manifest.json").exists()
    with pytest.raises(FileExistsError):
        probes.import_probe_session(spec, "X1", tmp_path / "run")
    with pytest.raises(FileNotFoundError, match="no findings.json"):
        probes.import_probe_session(spec, "X9", tmp_path / "other")


def test_the_solo_context_file_is_the_one_test_b_used():
    ref = (G52_DIR / "model_context.jsonl").read_text()
    assert probes.model_context(POST, [41930, 42184, 42814, 43024, 43167, 43192]) == ref


def test_conventions_follow_the_model_as_a_second_section_and_no_pr_is_skipped():
    from src.mathlib_review.io import jsonl_rows

    ref = jsonl_rows(G52_DIR / "model_context.jsonl")[:2]
    prs = [41930, 42184]
    rows = [json.loads(line) for line in probes.model_context(
        POST, prs, conventions={41930: ["A is written as B.", "C is named D."], 42184: []}).split("\n") if line]
    assert rows[0]["sections"][0] == ref[0]["sections"][0]
    assert rows[0]["sections"][1] == {
        "title": probes.CONVENTIONS_TITLE,
        "text": probes.CONVENTIONS_LEAD + "\n\n- A is written as B.\n- C is named D.\n"}
    # An empty brief is the model alone, byte for byte what the unbriefed condition reads.
    assert rows[1] == ref[1]
    with pytest.raises(KeyError, match="42184"):
        probes.model_context(POST, prs, conventions={41930: ["A is written as B."]})


def test_a_conventions_section_can_close_with_a_paragraph_and_an_empty_brief_still_reads_none():
    from src.mathlib_review.io import jsonl_rows

    ref = jsonl_rows(G52_DIR / "model_context.jsonl")[:2]
    rows = [json.loads(line) for line in probes.model_context(
        POST, [41930, 42184], conventions={41930: ["A is written as B."], 42184: []},
        closing=probes.CONVENTIONS_DISPOSITION).split("\n") if line]
    assert rows[0]["sections"][1]["text"] == (
        probes.CONVENTIONS_LEAD + "\n\n- A is written as B.\n\n" + probes.CONVENTIONS_DISPOSITION + "\n")
    assert rows[1] == ref[1]
    assert "would insist on it are not grounds" in probes.CONVENTIONS_DISPOSITION


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


def test_the_question_form_rubric_is_the_old_one_with_one_paragraph_more():
    old = probes.MATCHER_RUBRIC.read_text()
    new = probes.MATCHER_RUBRIC_QUESTIONS.read_text()
    added = new.replace(old.split("\nAlso give the index")[0], "", 1).split("\nAlso give the index")[0]
    assert added.startswith("\nA finding may be a question to the author.") and added.count("\n\n") == 0
    assert new.replace(added, "", 1) == old
    five = probes.matcher_rubric(5, 8, probes.MATCHER_RUBRIC_QUESTIONS)
    assert "Five anonymous reviewers, `R1` to `R5`" in five and "question to the author" in five
    assert "question to the author" not in probes.matcher_rubric(5, 8)


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


def test_a_sessions_own_overflow_file_is_not_flagged_but_anothers_is(tmp_path):
    folder = tmp_path / "m1"
    folder.mkdir()
    own, other = "/common/x/tool-results/b111.txt", "/common/x/tool-results/b222.txt"
    rows = [{"message": {"content": [{"type": "tool_result", "content": f"Output saved to {own}"}]}},
            {"message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": own}}]}},
            {"message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": other}}]}}]
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("\n".join(json.dumps(r) for r in rows))
    report = probes.audit_transcript(folder, transcript)
    assert len(report["flagged"]) == 1 and report["flagged"][0]["input"] == other


def test_unblinding_may_leave_a_matched_pr_out_of_the_seal():
    asks = json.loads(POST.asks_file.read_text())
    seal = json.loads((G52_DIR / "blinding_SEALED.json").read_text())
    matches = {m: json.loads((G52_DIR / "match_rematch" / f"matches.{m}.json").read_text()) for m in ("1", "2")}
    stats = json.loads((G52_DIR / "match_rematch/session_stats.json").read_text())
    without = probes.unblind(asks, {k: v for k, v in seal.items() if k != "43192"}, matches, stats)
    assert without["asks"] == 16 - 4


def test_a_capped_session_is_matched_as_submitting_nothing():
    runs = probes._solo("probe_postcutoff_gpt52_Gr_rep1")
    found, stats = runs[42814]
    assert found == [] and stats["capped"] == "paused_max_turns"
    assert all("capped" not in st for pr, (_f, st) in runs.items() if pr != 42814)


def test_a_swap_packet_holds_the_delivered_messages_with_only_the_tool_line_changed(tmp_path):
    """The swap gives another reviewer a solo session's messages as its instructions. They are read
    from the session's last, cumulative turn file (never a `_raw` one), and only the tool line is
    rewritten to what `ptool` holds."""

    turn = tmp_path / "task" / "samples/0/attempts/attempt_1/conversations"
    turn.mkdir(parents=True)
    user = "# Pull request #1\n\n**Tools available:** read files, compile/verify Lean code (lean_verify)\n\nReview."
    nodes = [{"type": "system", "message": {"content": [{"type": "text", "text": "SYSTEM"}]}},
             {"type": "tool_definitions", "message": {"content": []}},
             {"type": "user", "message": {"content": [{"type": "text", "text": user}]}},
             {"type": "user", "message": {"content": [{"type": "text", "text": "a later tool result"}]}}]
    (turn / "20261001_000001__turn_1__a.jsonl").write_text(json.dumps(nodes[0]) + "\n")
    (turn / "20261001_000002__turn_2__b.jsonl").write_text("".join(json.dumps(n) + "\n" for n in nodes))
    (turn / "20261001_000002__turn_2__b_raw.jsonl").write_text("not json\n")
    system, delivered = probes.delivered_messages(tmp_path / "task")
    assert (system, delivered) == ("SYSTEM", user)
    swapped = probes.swap_user_message(delivered)
    assert swapped.split("\n")[2] == probes.PTOOL_TOOLS_LINE and "lean_verify)" not in swapped
    assert swapped.replace(probes.PTOOL_TOOLS_LINE, "") == user.replace(user.split("\n")[2], "")
    with pytest.raises(ValueError, match="one 'Tools available' line"):
        probes.swap_user_message("no tool line")


def test_a_swap_session_keeps_the_rules_and_submits_the_tools_arguments(tmp_path):
    """Every rule X's sessions ran under is in the swap prompt, word for word but for the `ptool`
    line, which also says the instructions' `target/...` paths are its paths."""

    (tmp_path / "x").mkdir()
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "user.md").write_text("u")
    assert "brief.md" in probes.session_prompt(tmp_path / "x")
    swap = probes.session_prompt(tmp_path / "s")
    assert "submission.json" in swap and '{"notes": "...", "findings": [...]}' in swap
    rules = [line.strip() for line in probes.SESSION_PROMPT.splitlines() if line.strip().startswith("- ")]
    for rule in rules:
        if "ptool" not in rule:
            assert rule in swap, rule
    assert probes.finished(tmp_path / "s") is False
    (tmp_path / "s" / "submission.json").write_text("{}")
    assert probes.finished(tmp_path / "s") is True


def test_a_swap_submission_imports_located_by_path_and_line(tmp_path):
    """A swap session's findings carry `path` and `line_start`, as gpt's do, and are anchored on
    them by the solo tail, not re-resolved from a name."""

    graph = _dev_graph(33337)
    by_id = {e.entity_id: e for e in graph.entities}
    # A change target's own reviewed declaration: a location the anchoring pass can map.
    entity = next(by_id[t.reviewed_entity_ids[0]] for t in graph.targets
                  if t.declaration_name and t.reviewed_entity_ids and t.reviewed_entity_ids[0] in by_id)
    spec = DEV.model_copy(update={"pr_numbers": [33337], "probe_dir": tmp_path / "probe"})
    packet = tmp_path / "probe" / "pr33337" / "S9"
    packet.mkdir(parents=True)
    submission = {"notes": "- one entry", "findings": [
        {"path": entity.path, "line_start": entity.span.line_start, "severity": "advisory",
         "claim": f"`{entity.fullname}` should be renamed.", "suggested_fix": "Rename it."}]
        + [{"claim": f"filler {i}"} for i in range(21)]}
    (packet / "submission.json").write_text(json.dumps(submission))
    report = probes.import_probe_session(spec, "S9", tmp_path / "run")
    assert report["resolution"]["path_and_line"] == 1 and report["anchored"] >= 1
    provenance = json.loads((tmp_path / "run" / "probe_import.json").read_text())
    assert provenance["findings_past_the_budget"] == {"33337": 2}
    rows = [json.loads(l) for l in (tmp_path / "run" / "findings.jsonl").read_text().splitlines() if l]
    assert any(r["requested_change"] == "Rename it." for r in rows)


def test_a_packet_brief_ends_with_its_conventions_and_an_empty_brief_is_brief_x(tmp_path):
    spec = POST.model_copy(update={"probe_dir": tmp_path / "probe"})
    briefed, bare = probes.write_packets(spec, ["E1"], tmp_path / "scratch", prs=[43192, 43024],
                                         conventions={43192: ["A is written as B."], 43024: []})
    brief_x = probes.BRIEF_X.read_text()
    assert (briefed / "brief.md").read_text() == (
        brief_x + f"\n## {probes.CONVENTIONS_TITLE}\n\n{probes.CONVENTIONS_LEAD}\n\n- A is written as B.\n")
    assert (bare / "brief.md").read_text() == brief_x
    with pytest.raises(KeyError, match="43024"):
        probes.write_packets(spec, ["E2"], tmp_path / "scratch", prs=[43192, 43024],
                             conventions={43192: ["A is written as B."]})


def test_a_packet_brief_can_end_with_pinpointed_candidates_instead(tmp_path):
    spec = POST.model_copy(update={"probe_dir": tmp_path / "probe"})
    read = {"file": "Mathlib/A.lean", "declaration": "foo_of_bar", "fact": "It takes `h : Bar x` first.",
            "convention": "A is named in B's namespace.", "status": "departs", "check": "", "not_when": ""}
    run = {"file": "Mathlib/A.lean", "declaration": "baz", "fact": "The step is a monotonicity step.",
           "convention": "Such a step is closed by `gcongr`.", "status": "check",
           "check": "Replace the step by `gcongr`; it departs if that compiles.", "not_when": "the function is not tagged."}
    briefed, bare = probes.write_packets(spec, ["G1"], tmp_path / "scratch", prs=[43192, 43024],
                                         candidates={43192: [read, run], 43024: []})
    brief_x = probes.BRIEF_X.read_text()
    assert (briefed / "brief.md").read_text() == (
        brief_x + f"\n## {probes.CANDIDATES_TITLE}\n\n{probes.CANDIDATES_LEAD}\n\n"
        "- `Mathlib/A.lean`, `foo_of_bar`: It takes `h : Bar x` first. Convention: A is named in B's namespace. "
        "Decided by reading: the code departs.\n"
        "- `Mathlib/A.lean`, `baz`: The step is a monotonicity step. Convention: Such a step is closed by `gcongr`. "
        "Check: Replace the step by `gcongr`; it departs if that compiles. Not when: the function is not tagged.\n")
    assert (bare / "brief.md").read_text() == brief_x
    with pytest.raises(KeyError, match="43024"):
        probes.write_packets(spec, ["G2"], tmp_path / "scratch", prs=[43192, 43024], candidates={43192: [read]})
    with pytest.raises(ValueError, match="not both"):
        probes.write_packets(spec, ["G3"], tmp_path / "scratch", prs=[43192], candidates={43192: [read]},
                             conventions={43192: ["A is written as B."]})
    briefs = tmp_path / "candidates.json"
    briefs.write_text(json.dumps({"prs": {"43192": [read], "43024": []}}))
    assert probes.load_candidates(briefs) == {43192: [read], 43024: []}


def test_the_candidates_lead_is_chosen_by_name_and_stage_g_stays_the_default(tmp_path):
    spec = POST.model_copy(update={"probe_dir": tmp_path / "probe"})
    item = {"file": "Mathlib/A.lean", "declaration": "foo", "fact": "It is stated with `theorem`.",
            "convention": "A minor lemma is a `lemma`.", "status": "departs", "check": "", "not_when": ""}
    line = ("- `Mathlib/A.lean`, `foo`: It is stated with `theorem`. Convention: A minor lemma is a "
            "`lemma`. Decided by reading: the code departs.\n")
    brief_x = probes.BRIEF_X.read_text()
    assert probes.CANDIDATES_LEADS["verify"] is probes.CANDIDATES_LEAD
    for name in ("disposition", "ledger"):
        (packet,) = probes.write_packets(spec, [f"{name[0].upper()}1"], tmp_path / "scratch", prs=[43192],
                                         candidates={43192: [item]}, candidates_lead=name)
        lead = probes.CANDIDATES_LEADS[name]
        assert (packet / "brief.md").read_text() == (
            brief_x + f"\n## {probes.CANDIDATES_TITLE}\n\n{lead}\n\n{line}")
        # Neither lead may give a guess about maintainers as a reason to leave a change out.
        assert "would insist" in lead or "decide `file`" in lead
        assert "say nothing" not in lead
    with pytest.raises(KeyError):
        probes.write_packets(spec, ["Z1"], tmp_path / "scratch", prs=[43192],
                             candidates={43192: [item]}, candidates_lead="assert")


def test_a_brief_is_its_entries_sentences_in_codebook_order(tmp_path):
    codebook, briefs = tmp_path / "codebook.json", tmp_path / "briefs.json"
    codebook.write_text(json.dumps([{"id": "P001", "principle": "first"}, {"id": "P002", "principle": "second"}]))
    briefs.write_text(json.dumps({"prs": {"7": ["P002", "P001", "P002"], "8": []}}))
    assert probes.load_conventions(briefs, codebook) == {7: ["first", "second"], 8: []}


def test_a_convention_can_carry_maintainers_asks_beneath_it_inside_its_list_item(tmp_path):
    codebook, briefs = tmp_path / "codebook.json", tmp_path / "briefs.json"
    codebook.write_text(json.dumps([{"id": "P001", "principle": "first"}, {"id": "P002", "principle": "second"}]))
    briefs.write_text(json.dumps({"prs": {"7": ["P002", "P001"], "8": []}}))
    examples = {"P001": [{"path": "Mathlib/A.lean", "comment": "Use `simp`.\n\nPlease.", "code": "@@ -1 +1 @@\n\n+x"},
                         {"path": None, "comment": "Why?", "code": ""}]}
    first = ("first\n\n  Example 1, asked on another PR at `Mathlib/A.lean`. The maintainer's comment:\n\n"
             "  > Use `simp`.\n  >\n  > Please.\n\n  The code it was on:\n\n  ```\n  @@ -1 +1 @@\n\n  +x\n  ```"
             "\n\n  Example 2, asked on another PR on the PR as a whole. The maintainer's comment:\n\n  > Why?")
    held = probes.load_conventions(briefs, codebook, examples)
    assert held == {7: [first, "second"], 8: []}
    # The sentences and the lead are the exact section's; the examples sit inside each item, the
    # precedence paragraph after the list.
    section = probes.conventions_section(held[7], probes.CONVENTIONS_PRECEDENCE)
    assert section == (probes.CONVENTIONS_LEAD + f"\n\n- {first}\n- second\n\n"
                       + probes.CONVENTIONS_PRECEDENCE + "\n")
    assert probes.conventions_section(["first", "second"]) == probes.conventions_section(
        probes.load_conventions(briefs, codebook)[7])
    for ground in ("outrank your own judgement", "matter of taste", "does not require it",
                   "file it as a question", "not to raise questions"):
        assert ground in probes.CONVENTIONS_PRECEDENCE


def test_a_new_packet_goes_where_the_prs_earlier_sessions_live(tmp_path):
    spec = POST.model_copy(update={"probe_dir": tmp_path / "probe", "sessions_from": {43192: tmp_path / "old"}})
    moved, plain = probes.write_packets(spec, ["E1"], tmp_path / "scratch", prs=[43192, 43024])
    assert moved == tmp_path / "old" / "pr43192" / "E1" == spec.session_dir(43192, "E1")
    assert plain == tmp_path / "probe" / "pr43024" / "E1"
    assert f"OUT={tmp_path / 'old' / 'pr43192' / 'E1'}" in (moved / "ptool").read_text()



def test_a_review_task_says_its_pr_by_its_result_or_its_id(tmp_path):
    from src.mathlib_review.analysis.runs import task_pr_number

    assert task_pr_number(tmp_path, {"pr_number": 33117, "task_id": "x"}) == 33117
    (tmp_path / "task_outcome.json").write_text(json.dumps(
        {"task_id": "pr5solo_mathlib4_42814_round1_abc"}))
    assert task_pr_number(tmp_path) == 42814       # a capped session: no result, the id says it
    (tmp_path / "task_outcome.json").write_text(json.dumps({"task_id": "no number here"}))
    assert task_pr_number(tmp_path) is None
