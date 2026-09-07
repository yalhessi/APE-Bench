"""Where a task ran, written down instead of inferred from where its directory sits.

`trajectory.py` recovered "which arm, which wave" by parsing paths, and said so: "the
orchestrator encodes them in the directory it creates for each batch, so the path *is* the
provenance." It cost two things:

* `samples/0` hardcoded, so any sample index but 0 is invisible;
* a depth-sensitive glob, so retiring budget tiers turned `subtasks/wave<N>/<tier>/<id>/` into
  `subtasks/wave<N>/<id>/` and the reader needed a second glob. The next change needs a third.

Neither is a reader bug. The information is known at dispatch and thrown away.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from ape.orchestration import execution_index


class _Attempt:
    def __init__(self, path, status="completed", cost=0.1, cached_cost=0.04, attempt_id="a1"):
        self.path, self.status, self.cost = path, status, cost
        self.cached_cost, self.attempt_id = cached_cost, attempt_id

    def model_dump(self, mode="json"):
        return {"path": str(self.path), "status": self.status, "cost": self.cost,
                "cached_cost": self.cached_cost, "attempt_id": self.attempt_id}


class _Sample:
    def __init__(self, index, attempts):
        self.index, self.attempts = index, attempts

    def model_dump(self, mode="json"):
        return {"sample_index": self.index,
                "attempts": [a.model_dump() for a in self.attempts]}


def test_a_row_names_the_attempt_paths_the_orchestrator_recorded(tmp_path):
    """Rather than rebuilding them as `samples/0/attempts/attempt_*`, which is the hardcoding
    this replaces."""

    rows = execution_index.attempt_rows([
        _Sample(0, [_Attempt(tmp_path / "a0", cost=0.1)]),
        _Sample(1, [_Attempt(tmp_path / "a1", cost=0.2)]),
    ])
    assert [r["sample_index"] for r in rows] == [0, 1]
    assert rows[1]["path"].endswith("a1")


def test_a_sample_index_other_than_zero_is_visible(tmp_path):
    """It was not. `_sample_cost` reads `samples/0/sample.json` and nothing else."""

    rows = execution_index.attempt_rows([_Sample(2, [_Attempt(tmp_path / "x")])])
    assert rows[0]["sample_index"] == 2


def test_rows_round_trip(tmp_path):
    path = tmp_path / "execution_index.jsonl"
    execution_index.append(path, {"semantic_id": "wu:1#proof_golf", "group": "wave1"})
    execution_index.append(path, {"semantic_id": "wu:2#duplication", "group": "wave2"})
    rows = execution_index.load(path)
    assert [r["semantic_id"] for r in rows] == ["wu:1#proof_golf", "wu:2#duplication"]
    assert all(r["version"] == execution_index.INDEX_VERSION for r in rows)


def test_a_retry_replaces_its_earlier_row(tmp_path):
    """Append-only, so both lines exist; the resolver keeps the last, which is the retry."""

    path = tmp_path / "i.jsonl"
    execution_index.append(path, {"semantic_id": "wu:1#a", "task_dir": "first"})
    execution_index.append(path, {"semantic_id": "wu:1#a", "task_dir": "second"})
    assert execution_index.by_semantic_id(path)["wu:1#a"]["task_dir"] == "second"


def test_a_truncated_final_line_does_not_lose_the_rest(tmp_path):
    path = tmp_path / "i.jsonl"
    execution_index.append(path, {"semantic_id": "wu:1#a"})
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"semantic_id": "wu:2')
    assert [r["semantic_id"] for r in execution_index.load(path)] == ["wu:1#a"]


def test_a_write_failure_never_propagates(tmp_path):
    """Losing the index must not lose the work it indexes."""

    execution_index.append(None, {"semantic_id": "x"})
    assert execution_index.load(None) == []
    assert execution_index.by_semantic_id(tmp_path / "absent.jsonl") == {}


# --- what `record` writes -----------------------------------------------------------------


class _Result:
    def __init__(self, task_id, global_index, task_type="arm"):
        self.data = {"task_id": task_id, "global_index": global_index,
                     "task_type": task_type, "success": True}

    def model_dump(self, mode="json"):
        return dict(self.data)


class _Results:
    def __init__(self, results):
        self.task_results = results


class _Orchestrator:
    def __init__(self, tasks_dir):
        self.tasks_dir = tasks_dir


def test_record_maps_the_semantic_id_the_caller_dispatched_under(tmp_path, monkeypatch):
    path = tmp_path / "i.jsonl"
    orchestrator = _Orchestrator(tmp_path / "tasks")
    results = _Results([_Result("pr5_wu1_golf", 3)])

    asyncio.run(execution_index.record(
        path, orchestrator, results,
        semantic_ids={"pr5_wu1_golf": "wu:1#proof_golf"}, group="wave2", parent="ep:1"))

    row = execution_index.by_semantic_id(path)["wu:1#proof_golf"]
    assert row["group"] == "wave2"
    assert row["parent"] == "ep:1"
    assert row["task_dir"].endswith("tasks/3")


def test_a_task_with_no_semantic_id_is_still_indexed(tmp_path):
    """An unindexed task is worse than a coarsely-indexed one: it is the row a reader needs
    when something ran that the caller did not expect."""

    path = tmp_path / "i.jsonl"
    asyncio.run(execution_index.record(
        path, _Orchestrator(tmp_path / "tasks"), _Results([_Result("stray", 9)]),
        semantic_ids={}, group="wave1"))
    assert "stray" in execution_index.by_semantic_id(path)


def test_recording_without_a_path_is_a_no_op(tmp_path):
    asyncio.run(execution_index.record(
        None, _Orchestrator(tmp_path), _Results([_Result("t", 1)]),
        semantic_ids={}, group="g"))


# --- the reader ----------------------------------------------------------------------------


def test_trajectory_prefers_the_index_over_the_globs(tmp_path, monkeypatch):
    """The point of the whole file: a run that wrote an index is read through it, so the
    subtask depth stops being load-bearing."""

    from src.datasets.pr_review_v5 import trajectory

    task_dir = tmp_path / "somewhere" / "entirely" / "different"
    task_dir.mkdir(parents=True)
    (task_dir / "task_result.json").write_text(json.dumps({
        "invocation_id": "wu:1#proof_golf", "arm_id": "proof_golf",
        "work_unit_id": "wu:1", "pr_number": 33117, "status": "completed",
    }), encoding="utf-8")

    root = tmp_path / "ape" / "run1"
    root.mkdir(parents=True)
    monkeypatch.setattr(trajectory, "_indexed_arms", lambda name: {
        "wu:1#proof_golf": {"task_dir": str(task_dir), "group": "wave3",
                            "attempts": [{"path": str(task_dir), "status": "completed",
                                          "cost": 0.3, "cached_cost": 0.1}]},
    })
    out = trajectory.extract("run1", ape_root=tmp_path / "ape")
    assert len(out["invocations"]) == 1
    found = out["invocations"][0]
    assert found.invocation_id == "wu:1#proof_golf"
    # Wave comes from the dispatcher's group, not from counting path segments -- and is
    # spelled exactly as the glob path spells it, or the field cannot be grouped on.
    assert found.wave == "wave3"
    assert found.cost == pytest.approx(0.3)
    assert found.cached_cost == pytest.approx(0.1)


def test_a_run_without_an_index_still_reads(tmp_path, monkeypatch):
    """Every September run. The globs stay for exactly this."""

    from src.datasets.pr_review_v5 import trajectory

    root = tmp_path / "ape" / "run1"
    task = (root / "tasks/0/samples/0/attempts/a/subtasks/wave1/orch/tasks/0")
    task.mkdir(parents=True)
    (task / "task_result.json").write_text(json.dumps({
        "invocation_id": "wu:1#duplication", "arm_id": "duplication",
        "work_unit_id": "wu:1", "pr_number": 33117, "status": "completed",
    }), encoding="utf-8")
    monkeypatch.setattr(trajectory, "_indexed_arms", lambda name: {})
    out = trajectory.extract("run1", ape_root=tmp_path / "ape")
    assert [i.invocation_id for i in out["invocations"]] == ["wu:1#duplication"]
    assert out["invocations"][0].wave == "wave1"


def test_both_readers_spell_the_wave_the_same_way(tmp_path, monkeypatch):
    """One field, one format. The index path and the glob path have to agree or grouping by
    wave silently splits each wave in two."""

    from src.datasets.pr_review_v5 import trajectory

    result = json.dumps({"invocation_id": "wu:1#a", "arm_id": "a", "work_unit_id": "wu:1",
                         "pr_number": 1, "status": "completed"})

    indexed_dir = tmp_path / "indexed"
    indexed_dir.mkdir()
    (indexed_dir / "task_result.json").write_text(result, encoding="utf-8")
    root = tmp_path / "ape" / "r"
    globbed = root / "tasks/0/samples/0/attempts/a/subtasks/wave1/orch/tasks/0"
    globbed.mkdir(parents=True)
    (globbed / "task_result.json").write_text(result, encoding="utf-8")

    monkeypatch.setattr(trajectory, "_indexed_arms", lambda name: {})
    by_glob = trajectory.extract("r", ape_root=tmp_path / "ape")["invocations"][0].wave

    monkeypatch.setattr(trajectory, "_indexed_arms", lambda name: {
        "wu:1#a": {"task_dir": str(indexed_dir), "group": "wave1", "attempts": []}})
    by_index = trajectory.extract("r", ape_root=tmp_path / "ape")["invocations"][0].wave

    assert by_glob == by_index == "wave1"
