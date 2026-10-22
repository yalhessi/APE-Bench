"""`report tools`: what every tool call in a run came back with, on either scaffold.

The reading behind the hygiene layer's nine fixes was a probe script over one scaffold's
transcripts. These pin what the shared version must do that the script did not: read both
transcript formats, walk attempts through the persisted samples (failed attempts included), and
descend into a lead's nested subtask batches.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

import pytest

from ape.orchestration.models import Attempt, Sample
from ape.orchestration.persistence import TaskStorage
from src.mathlib_review.analysis import tool_outcomes as T


def _write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _claude_code(attempt: Path, calls) -> None:
    """The Claude SDK's shape: results in `content` (a string or text blocks) with `is_error`."""
    rows = []
    for i, (name, result, is_error) in enumerate(calls):
        rows.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": f"u{i}", "name": name, "input": {"q": i}}]}})
        rows.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"u{i}", "is_error": is_error,
             "content": [{"type": "text", "text": result}]}]}})
    _write_jsonl(attempt / "claude_code_conversation_1__x.jsonl", rows)


def _ape_agent(attempt: Path, calls) -> None:
    """ape_agent's shape: results in `result_content`; `content` is never populated."""
    rows = []
    for i, (name, result) in enumerate(calls):
        rows.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": f"c{i}", "name": name, "input": {}}]}})
        rows.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"c{i}", "name": name,
             "result_content": result, "content": None}]}})
    _write_jsonl(attempt / "ape_agent_session_1__y.jsonl", rows)


def test_both_transcript_formats_pair_each_call_with_its_result(tmp_path):
    cc, ape = tmp_path / "cc", tmp_path / "ape"
    _claude_code(cc, [("Grep", "No matches found", False), ("mcp__core__x", "boom", True)])
    _ape_agent(ape, [("file_read", json.dumps({"success": True, "content": "..."}))])

    assert [(c.name, c.text, c.is_error) for c in T.tool_calls(cc)] == [
        ("Grep", "No matches found", False), ("mcp__core__x", "boom", True)]
    assert [(c.name, json.loads(c.text)["success"]) for c in T.tool_calls(ape)] == [
        ("file_read", True)]


@pytest.mark.parametrize("name,text,is_error,expected", [
    ("Grep", "No matches found", False, "negative"),
    ("Read", "File does not exist.", False, "refused"),
    ("x", "<tool_use_error>No such tool available: y</tool_use_error>", False, "error"),
    ("x", "PreToolUse:Bash hook error: refused", False, "error"),
    ("lean_verify_edit", json.dumps({"outcome": "compile_errors"}), False, "negative"),
    ("declaration_search", json.dumps({"outcome": "invalid_request", "error": "bad"}), False, "refused"),
    ("proof_profile", json.dumps({"success": False, "error": "no declaration table"}), False, "env"),
    ("naming_norm", json.dumps({"verdict": "insufficient_evidence"}), False, "negative"),
    ("lean_verify", json.dumps({"success": True}), False, "answered"),
])
def test_a_result_is_classified_by_what_it_says(name, text, is_error, expected):
    assert T.classify(name, text, is_error)[0] == expected


def _task(tasks_dir: Path, name: str, attempts: int) -> list:
    """A real persisted sample with `attempts` attempts, each with its directory on disk."""
    task_dir = tasks_dir / name
    now = datetime.now()
    paths = [task_dir / "samples" / "0" / "attempts" / f"attempt_{i}_x" for i in range(1, attempts + 1)]
    for path in paths:
        path.mkdir(parents=True)
    sample = Sample(sample_id=f"{name}_0", sample_index=0, task_global_index=name, created_at=now,
                    updated_at=now, attempts=[Attempt(attempt_id=i, path=p, created_at=now,
                                                      max_turns=1, cost_limit=None)
                                              for i, p in enumerate(paths, start=1)])
    asyncio.run(TaskStorage(task_dir, name).save_sample(sample))
    return paths


def test_every_attempt_is_read_and_a_leads_nested_arms_with_it(tmp_path, monkeypatch):
    root = tmp_path / "runs" / "r"
    lead_first, lead_retry = _task(root / "tasks", "lead", attempts=2)
    (arm,) = _task(lead_retry / "subtasks" / "wave1" / "batch" / "tasks", "arm", attempts=1)

    _ape_agent(lead_first, [("delegate", json.dumps({"outcome": "tool_error", "error": "x"}))])
    _ape_agent(lead_retry, [("delegate", json.dumps({"success": True}))])
    _ape_agent(arm, [("declaration_search", json.dumps({"count": 0})),
                     ("submit_candidates", json.dumps({"success": True}))])

    out = T.tool_outcomes("r", ape_root=tmp_path / "runs")

    assert out["attempts"] == 3
    assert out["tools"]["delegate"] == {"calls": 2, "answered": 1, "negative": 0, "refused": 0,
                                        "error": 1, "env": 0, "missing": 0}
    assert out["attempts_without_transcript"] == 0
    assert out["tools"]["declaration_search"]["negative"] == 1
    assert out["why"]["delegate"]["error"] == [["x", 1]]


def test_a_run_with_no_orchestrator_tree_says_where_the_transcripts_live(tmp_path):
    with pytest.raises(SystemExit, match="gitignored"):
        T.tool_outcomes("absent", ape_root=tmp_path)


def test_a_call_with_no_recorded_result_is_missing_never_answered(tmp_path):
    """A session cut off after a `lean_verify_edit` call: the transcript has the call and no
    result. It paired with empty text and `is_error=False`, which classified as answered, so an
    interrupted check read as one that ran."""

    attempt = tmp_path / "a"
    _write_jsonl(attempt / "ape_agent_session_1__z.jsonl", [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "c0", "name": "lean_verify_edit", "input": {}},
            {"type": "tool_use", "id": "c1", "name": "file_read", "input": {}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "c1", "result_content": "{}"}]}},
    ])
    calls = {c.name: c for c in T.tool_calls(attempt)}
    assert calls["lean_verify_edit"].has_result is False
    assert T.classify("lean_verify_edit", calls["lean_verify_edit"].text, False,
                      calls["lean_verify_edit"].has_result)[0] == "missing"
    assert T.classify("file_read", calls["file_read"].text, False)[0] == "answered"


def test_an_attempt_with_no_transcript_is_counted(tmp_path):
    root = tmp_path / "runs" / "r"
    (with_one,) = _task(root / "tasks", "t1", attempts=1)
    _task(root / "tasks", "t2", attempts=1)          # its directory exists, no transcript
    _ape_agent(with_one, [("file_read", "{}")])
    out = T.tool_outcomes("r", ape_root=tmp_path / "runs")
    assert out["attempts"] == 2
    assert out["attempts_without_transcript"] == 1
