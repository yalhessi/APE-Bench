"""An accepted empty review can be reread. A failed attempt cannot occupy that cell."""

import asyncio
import json
from pathlib import Path

import pytest

from src.mathlib_review.io import pretty_json_bytes, sha256_bytes

from src.mathlib_review.analysis import submissions as measure


def put(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pretty_json_bytes(obj))


@pytest.mark.parametrize("findings", [[], [
    {"claim": "Reason one.", "suggested_fix": "Change one."},
    {"claim": "Reason two.", "suggested_fix": "Change two.", "path": "Mathlib/A.lean", "line_start": 9},
]])
def test_archive_selects_accepted_attempt_and_preserves_order(tmp_path, monkeypatch, findings):
    monkeypatch.chdir(tmp_path)
    out, name = Path("sample"), "r123"
    task = Path(".ape/runs") / name / "tasks/key"
    folder = task / "samples/0"
    attempt = folder / "attempts/accepted"
    put(out / "generation.json", {})
    put(Path("results/pr_review_v5/runs") / name / "run_manifest.json", {"completion_status": "complete"})
    put(Path("results/pr_review_v5/runs") / name / "run_plan.json",
        {"run_name": name, "evaluation_settings": {"design": "whole_pr"}})
    cwd = str(attempt / "workspaces")
    put(attempt / "claude_code_session.json", {
        "init": {"model": "model", "claude_code_version": "version", "cwd": cwd, "tools": ["Read"],
                 "permissionMode": "dontAsk", "mcp_servers": [{"name": "core", "status": "connected"}]},
        "effort": "level"})
    put(attempt / "containment_audit.json", {"clean": True, "usable": True, "transcripts": [{"by_tool": {}}]})
    msg = {"type": "user", "message": {"content": "Work at " + cwd}}
    (attempt / "claude_code_conversation_1.jsonl").write_text(json.dumps(msg) + "\n")
    sample = {"sample_id": "s", "sample_index": 0, "task_global_index": "key",
              "created_at": "2026-11-25", "updated_at": "2026-11-25",
              "attempts": [{"attempt_id": 1, "path": str(attempt), "status": "success",
                            "created_at": "2026-11-25", "max_turns": 2, "cost_limit": 1.5, "token_limit": 100}]}
    raw = {"pr_number": 9, "episode_id": "e", "success": True, "submitted_findings": findings,
           "review_message": "Optional summary", "findings": []}
    sample["attempts"][0]["result"] = raw
    put(folder / "sample.json", sample)
    put(task / "task_result.json", raw)
    runs = {"solo": {"run": name, "episodes": {"9": {"episode_id": "e", "model": "model",
            "cli_version": "version", "effort": "level", "mcp": [], "builtins": ["Read"],
            "max_turns": 2, "token_cap": 100, "cost_cap": 1.5,
            "message_sha256": sha256_bytes(b"Work at {attempt_workspaces}")}}}}

    receipt = asyncio.run(measure.capture(out, runs))
    assert measure.read(out / "submissions/r123/9/task_result.json") == raw
    projection = measure.read(Path(receipt["sources"]["solo"]["path"]))["9"]
    assert [f["requested_change"] for f in projection] == [f["suggested_fix"] for f in findings]
    if projection:
        assert [f["target"] for f in projection] == [measure.probes.PR_LEVEL_TARGET, "Mathlib/A.lean:9"]
    sample["attempts"][0]["status"] = "failed_error"
    put(folder / "sample.json", sample)
    with pytest.raises(ValueError, match="no accepted submission"):
        asyncio.run(measure.capture(out, runs))


def test_study_cli_rescores_a_saved_sample_without_generation(tmp_path):
    from src.mathlib_review.review.cli import main
    from src.mathlib_review.io import sha256_file
    import yaml

    spec = yaml.safe_load(Path("configs/studies/familiar-conventions.yaml").read_text())
    spec["heads"].pop(41930)
    spec.update(name="one-reviewed-head", output=str(tmp_path), history="unavailable")
    config = tmp_path / "study.yaml"
    config.write_text(yaml.safe_dump(spec))
    out = tmp_path / "sample-2"
    sources = {}
    for arm in ("solo", "history", "automatic", "exact"):
        path = out / arm / "findings.json"
        put(path, {"42184": []})
        sources[arm] = {"kind": "findings_file", "path": str(path)}
    put(out / "generation.json", {"fixture": False, "runs": {arm: {"episodes": {"42184": {}}} for arm in sources}})
    records = []
    for arm in sources:
        # One accepted task result per arm and head, as `capture` records it.
        result = out / arm / "42184" / "task_result.json"
        put(result, {"pr_number": 42184, "success": True, "submitted_findings": []})
        records.append({"strategy": arm, "pr": "42184", "run_files": {},
                        "files": {"task_result.json": {"path": str(result), "sha256": sha256_file(result)}}})
    put(out / "archive.json", {"generation_sha256": sha256_file(out / "generation.json"), "sources": sources,
                               "records": records,
                               "projection_sha256": {a: sha256_file(Path(v["path"])) for a, v in sources.items()}})
    for flags in ([], ["--question-form"]):
        assert main(["study", "score", str(config), "--sample", "2", *flags]) == 0
    plans = [measure.matching.load_plan(path) for path in (out / "readings").iterdir()]
    assert len(plans) == 2 and plans[0].packets == plans[1].packets
    assert plans[0].identity.rubric_sha256 != plans[1].identity.rubric_sha256
    assert not (tmp_path / "conventions").exists()
