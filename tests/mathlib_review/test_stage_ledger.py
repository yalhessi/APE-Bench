"""Every stage leaves a row saying what it read, what it wrote, and under what identity.

A v5 experiment is several processes chained by a run name, and nothing recorded that the
chain happened. Whether a run had been judged was answered by looking for a directory; which
judge produced it, by reading the report inside; whether a replay came from this run, by its
name. Each is a reconstruction, and reconstruction is the class of mistake `judge --of` exists
to remove.

The state machine has existed since `052430c` and nothing wrote to it -- `FINALIZED` and
`JUDGED` had no writer and `assert_transition` no caller outside its own tests. These tests are
what make it code rather than a diagram.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.mathlib_review.io import append_jsonl, canonical_json_bytes, jsonl_rows
from src.mathlib_review.run_state import (
    RunState, append_stage, ledger, stage_record, state_of,
)


def test_a_ledger_is_appended_never_rewritten(tmp_path):
    """`write_once` is what makes a run reproducible -- a second write with different bytes is
    refused. That guarantee is exactly wrong for a record written while work happens: a stage
    that crashes between its artifacts and its row must leave the artifacts findable."""

    append_stage(tmp_path, stage_record("run", run_name="x"))
    append_stage(tmp_path, stage_record("judge", run_name="x"))
    rows = ledger(tmp_path)
    assert [row["stage"] for row in rows] == ["run", "judge"]
    assert (tmp_path / "stages.jsonl").read_bytes().count(b"\n") == 2


def test_a_row_carries_its_own_provenance(tmp_path):
    """Git state and the timestamp are filled by `stage_record`, not by each caller: a row
    whose provenance depends on which stage remembered to add it is not provenance."""

    row = stage_record("run", run_name="x", identity={"a": 1}).model_dump(mode="json")
    assert row["git_tree_state"] in {"clean", "dirty", "unknown"}
    assert row["written_at"].endswith("+00:00")
    assert row["schema_version"] == "v5-stage1"


def test_a_truncated_final_row_does_not_lose_the_rows_before_it(tmp_path):
    """A crash mid-write truncates the last line. Everything before it is intact, and stopping
    there is right: the rows are ordered, so a later one cannot be trusted once one is
    unreadable."""

    append_stage(tmp_path, stage_record("run", run_name="x"))
    with (tmp_path / "stages.jsonl").open("a") as handle:
        handle.write('{"stage": "judge", "run_na')
    assert [row["stage"] for row in ledger(tmp_path)] == ["run"]


def test_the_generation_run_asserts_its_transition_and_records_it():
    """`assert_transition` had no caller outside its tests. The run is the first."""

    from src.mathlib_review.review import runner

    source = inspect.getsource(runner._record_stage)
    assert "assert_transition" in source
    assert "RunState.FINALIZED" in source
    # Called where the manifest has just been written, so the row describes a closed run.
    run_source = inspect.getsource(runner.run)
    assert run_source.index("_record_stage") > run_source.index('"run_manifest.json"')


def test_the_generation_row_says_what_it_produced_and_under_what_plan(tmp_path):
    from src.mathlib_review.review import runner

    out = tmp_path / "pr5_probe_rep1"
    out.mkdir()
    (out / "findings.jsonl").write_bytes(b'{"finding_id": "finding:a"}\n')
    (out / "run_manifest.json").write_bytes(canonical_json_bytes({"completion_status": "complete"}))
    plan = SimpleNamespace(release_manifest_sha256="r" * 64, agenda_sha256="a" * 64,
                           source_sha256="p" * 64, scaffold_config_sha256="s" * 64)
    manifest = SimpleNamespace(completion_status="complete")
    logger = SimpleNamespace(warning=lambda *a, **k: None, info=lambda *a, **k: None)

    runner._record_stage(out, SimpleNamespace(run_name="pr5_probe_rep1", routing_mode="lead"),
                         plan, manifest, {"findings_sha256": "f" * 64}, logger)
    row = ledger(out)[0]
    assert row["stage"] == "run"
    assert row["identity"]["run_plan_sha256"] == "p" * 64
    assert row["transition"] == "running -> generated, generated -> finalized"
    assert row["forensic"] is False
    assert any(key.endswith("findings.jsonl") for key in row["produced"])


def test_a_partial_run_records_itself_as_forensic(tmp_path):
    from src.mathlib_review.review import runner

    out = tmp_path / "pr5_probe_rep2"
    out.mkdir()
    (out / "run_manifest.json").write_bytes(canonical_json_bytes({"completion_status": "partial"}))
    plan = SimpleNamespace(release_manifest_sha256=None, agenda_sha256="a" * 64,
                           source_sha256="p" * 64, scaffold_config_sha256="s" * 64)
    logger = SimpleNamespace(warning=lambda *a, **k: None, info=lambda *a, **k: None)

    runner._record_stage(out, SimpleNamespace(run_name="pr5_probe_rep2", routing_mode="lead"),
                         plan, SimpleNamespace(completion_status="partial"), {}, logger)
    row = ledger(out)[0]
    assert row["forensic"] is True
    assert row["transition"] == "running -> partial"
    assert state_of(out) is RunState.PARTIAL


def test_recording_a_row_can_never_fail_a_finished_run(tmp_path):
    """The work is paid for and the artifacts are on disk. A provenance row that could fail the
    stage it describes would be worse than a missing one."""

    from src.mathlib_review.review import runner

    warned = []
    logger = SimpleNamespace(warning=lambda *a, **k: warned.append(a), info=lambda *a, **k: None)
    runner._record_stage(tmp_path / "nonexistent", SimpleNamespace(run_name="x"),
                         SimpleNamespace(), SimpleNamespace(completion_status="complete"),
                         {}, logger)
    assert warned


def test_the_judge_row_lands_in_the_source_runs_ledger_and_carries_no_gold():
    """In the run's ledger because "this run was judged, under this identity, into that
    directory" is a fact about the RUN -- it is what `state_of` reads and what the next judge
    reads to refuse a second identity. Gold is hashed as files, never quoted: a row carrying an
    obligation's text would put gold into the run directory by the back door."""

    from src.mathlib_review.judge import runner as judge_runner

    source = inspect.getsource(judge_runner._record_stage)
    assert "append_stage(stage.run_dir" in source
    assert "digests_of" in source and "gold/judgments.jsonl" in source
    assert "claim" not in source and "obligation_id" not in source


def test_report_stages_names_the_two_ways_a_ledger_and_a_run_disagree(tmp_path, monkeypatch):
    """Both are what a crash produces, and both are worth saying rather than papering over."""

    from src.mathlib_review.analysis import report

    out = tmp_path / "runs" / "pr5_probe_rep1"
    out.mkdir(parents=True)
    (out / "run_manifest.json").write_bytes(canonical_json_bytes(
        {"completion_status": "complete"}))
    (out / "findings.jsonl").write_bytes(b'{"finding_id": "finding:a"}\n')
    monkeypatch.setattr(report, "run_dir", lambda name: out)
    monkeypatch.setattr("src.mathlib_review.paths.AUDITS", tmp_path / "audits")

    payload = report.stages("pr5_probe_rep1")
    assert payload["state"] == "finalized"
    assert payload["stages"] == []
    assert payload["reconciliation"]["ledger_missing_run_row"] is True

    append_stage(out, stage_record("run", run_name="pr5_probe_rep1"))
    assert report.stages("pr5_probe_rep1")["reconciliation"]["ledger_missing_run_row"] is False


def test_report_stages_is_read_only():
    from src.mathlib_review.review.cli import SPENDS

    assert "report" not in SPENDS
