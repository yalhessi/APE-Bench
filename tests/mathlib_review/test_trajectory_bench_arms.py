"""A standalone bench's arms must reach the trajectory sidecar.

`_ARM_RESULT_GLOBS` assume an arm ran under a lead, nested inside `subtasks/<wave>/...`. A
bench has no lead, so `bench_cli` dispatches arms as *top-level* tasks and their results land
at exactly the depth the lead glob covers — which then rejected them, because a lead used to be
identified as "a top-level result with no `invocation_id`". A top-level result *with* one fell
through both paths and the entire bench was invisible.

That matters for the oracle ladder specifically: every rung runs as a bench, and a rung whose
queries cannot be read cannot be attributed to the factor the rung added.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.mathlib_review.analysis.trajectory import extract


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _task(root: Path, task_id: str, result: dict, *, tool_calls=()) -> None:
    task = root / "tasks" / task_id
    _write(task / "task_result.json", result)
    _write(task / "samples" / "0" / "sample.json",
           {"status": "success", "attempts": [{"status": "success", "cost": 0.05,
                                               "cached_cost": 0.02}]})
    attempt = task / "samples" / "0" / "attempts" / "attempt_1"
    attempt.mkdir(parents=True, exist_ok=True)
    rows = [{
        "type": "assistant",
        "timestamp": "2026-09-09T00:00:00Z",
        "message": {"content": [
            {"type": "tool_use", "name": name, "id": f"t{index}", "input": payload}
            for index, (name, payload) in enumerate(tool_calls)
        ]},
    }] if tool_calls else []
    (attempt / "ape_agent_session_x.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_a_top_level_arm_is_extracted_and_a_lead_is_still_a_lead(tmp_path, monkeypatch):
    root = tmp_path / "runs" / "bench_run"
    _task(root, "arm1", {
        "invocation_id": "wu:abc#proof_idiom", "arm_id": "proof_idiom",
        "work_unit_id": "wu:abc", "pr_number": 33098, "status": "success",
    }, tool_calls=[("content_search", {"content_pattern": r"\bgrind\b",
                                       "path": "target/Mathlib"})])
    _task(root, "lead1", {"pr_number": 33098, "status": "success", "episode_id": "e1"})

    extracted = extract("bench_run", ape_root=tmp_path / "runs")

    invocations = {item.invocation_id: item for item in extracted["invocations"]}
    assert "wu:abc#proof_idiom" in invocations, "the bench arm was dropped"
    arm = invocations["wu:abc#proof_idiom"]
    assert arm.arm_id == "proof_idiom"
    assert arm.work_unit_id == "wu:abc"
    assert arm.has_transcript
    assert arm.tool_calls == {"content_search": 1}
    # A bench has no waves or tiers; saying so beats inventing one.
    assert arm.wave is None and arm.tier is None
    assert arm.cost == 0.05

    # And the lead is still read as a lead, not as an arm.
    assert [lead.pr_number for lead in extracted["leads"]] == [33098]


def test_a_nested_arm_is_not_counted_twice(tmp_path):
    """The top-level pass must not re-add an arm the nested globs already found."""

    root = tmp_path / "runs" / "bench_run"
    nested = ("tasks/t1/samples/0/attempts/a1/subtasks/wave1/33098_w1/tasks/inner")
    _write(root / nested / "task_result.json", {
        "invocation_id": "wu:abc#proof_idiom", "arm_id": "proof_idiom",
        "work_unit_id": "wu:abc", "pr_number": 33098, "status": "success",
    })
    _task(root, "t1", {
        "invocation_id": "wu:abc#proof_idiom", "arm_id": "proof_idiom",
        "work_unit_id": "wu:abc", "pr_number": 33098, "status": "success",
    })

    extracted = extract("bench_run", ape_root=tmp_path / "runs")
    ids = [item.invocation_id for item in extracted["invocations"]]
    assert ids.count("wu:abc#proof_idiom") == 1
