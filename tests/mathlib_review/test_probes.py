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
