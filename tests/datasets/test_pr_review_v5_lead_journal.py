"""A resumed lead remembers what it spent, ran and dispatched.

`_state()` lived on `self._delegation_state` behind a `hasattr`. A resumed lead is a fresh
object, so all four of these reset, and each one costs money:

* `delegated_spend` -> 0: the per-PR cap hands out a second full budget;
* `requested` -> empty: a job that already ran can be dispatched again;
* `floor_done` -> False: the coverage floor runs twice, and the floor is the expensive half
  (a measured $10.05 on PR 33149 against a $1.50 cap);
* `wave` -> 0: the second wave 1 writes into the first wave 1's subtask directory.

Nothing detected any of it, because from inside a resumed run looks exactly like a fresh one.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from ape.tasks.lean_tasks.formal_math.review import journal
from ape.tasks.lean_tasks.formal_math.review.delegation import JobOutcome, JobSpec


def _fresh_state():
    return {"wave": 0, "outcomes": {}, "requested": set(), "spend": 0.0,
            "delegated_spend": 0.0, "reserved": 0.0, "floor_done": False,
            "comprehension": None}


def _spec(invocation_id="wu:1#proof_golf", disposition="proposed"):
    return JobSpec(invocation_id=invocation_id, arm_id="proof_golf", work_unit_id="wu:1",
                   pr_number=1, payload={"task_type": "arm", "big": "x" * 100},
                   disposition=disposition)


def _outcome(invocation_id="wu:1#proof_golf", cost=0.25):
    return JobOutcome(invocation_id=invocation_id, arm_id="proof_golf", work_unit_id="wu:1",
                      pr_number=1, budget_tier="standard", status="completed", cost=cost)


def _pool(*invocation_ids):
    return {item: {"task_data": {"task_type": "arm", "big": "x" * 100}}
            for item in invocation_ids}


def _write(path: Path, *events):
    path.write_text("".join(json.dumps(e, default=str) + "\n" for e in events),
                    encoding="utf-8")


def _wave(wave, specs, floor=False):
    return {"event": journal.WAVE_OPENED, "wave": wave, "floor": floor,
            "specs": [journal.spec_row(s) for s in specs]}


def _settled(outcome, wave=1):
    return {"event": journal.SETTLED, "wave": wave, "outcome": asdict(outcome)}


def _replay(path, pool):
    state = _fresh_state()
    journal.replay(str(path), state, pool=pool, spec_cls=JobSpec, outcome_cls=JobOutcome)
    return state


# --- the four things a resume used to reset -----------------------------------------------


def test_a_resumed_lead_remembers_what_it_delegated(tmp_path):
    """The budget bug. A second full `per_pr_cost_cap` is exactly a doubled spend."""

    path = tmp_path / "j.jsonl"
    spec = _spec()
    _write(path, _wave(1, [spec]), _settled(_outcome(cost=0.75)))
    state = _replay(path, _pool(spec.invocation_id))
    assert state["delegated_spend"] == pytest.approx(0.75)
    assert state["spend"] == pytest.approx(0.75)


def test_the_coverage_floor_is_not_charged_to_the_routing_budget(tmp_path):
    """The distinction the in-memory state drew, preserved across replay: the floor is not a
    routing decision, so charging it to the routing budget makes the cap bind hardest on the
    largest PRs — the ones where routing matters most."""

    path = tmp_path / "j.jsonl"
    spec = _spec("wu:1#generalist", disposition="mandatory")
    _write(path, _wave(1, [spec], floor=True), _settled(_outcome("wu:1#generalist", 0.9)))
    state = _replay(path, _pool("wu:1#generalist"))
    assert state["spend"] == pytest.approx(0.9)
    assert state["delegated_spend"] == 0.0


def test_a_resumed_lead_does_not_run_the_floor_again(tmp_path):
    path = tmp_path / "j.jsonl"
    spec = _spec("wu:1#generalist", disposition="mandatory")
    _write(path, _wave(1, [spec], floor=True))
    assert _replay(path, _pool("wu:1#generalist"))["floor_done"] is True


def test_a_resumed_lead_keeps_its_dedup_set(tmp_path):
    path = tmp_path / "j.jsonl"
    spec = _spec()
    _write(path, _wave(1, [spec]), _settled(_outcome()))
    assert _replay(path, _pool(spec.invocation_id))["requested"] == {spec.invocation_id}


def test_a_resumed_lead_does_not_reuse_a_wave_number(tmp_path):
    """Wave numbers name subtask directories. Restarting at 1 overwrites wave 1's evidence."""

    path = tmp_path / "j.jsonl"
    first, second = _spec("wu:1#a"), _spec("wu:2#b")
    _write(path, _wave(1, [first]), _wave(2, [second]))
    assert _replay(path, _pool("wu:1#a", "wu:2#b"))["wave"] == 2


def test_comprehension_survives_so_delegation_is_not_re_gated(tmp_path):
    """`delegate` refuses until comprehension is submitted. A resumed lead that had already
    read the PR would be sent back to read it again — and pay for it again."""

    path = tmp_path / "j.jsonl"
    _write(path, {"event": journal.COMPREHENSION,
                  "comprehension": {"summary": "renames encard_", "questions": ["why?"]}})
    assert _replay(path, {})["comprehension"]["summary"] == "renames encard_"


# --- what must NOT be replayed ------------------------------------------------------------


def test_a_reservation_is_not_replayed(tmp_path):
    """`reserved` bounds jobs dispatched and not yet settled. After a restart nothing is in
    flight, so carrying a reservation forward consumes budget for work that is not running."""

    path = tmp_path / "j.jsonl"
    spec = _spec()
    _write(path, _wave(1, [spec]), _settled(_outcome()))
    assert _replay(path, _pool(spec.invocation_id))["reserved"] == 0.0


def test_a_failed_wave_releases_its_jobs(tmp_path):
    """The in-memory path already does this: a wave that raised never ran, so its jobs must be
    re-dispatchable. Replay has to agree or a crash strands them permanently."""

    path = tmp_path / "j.jsonl"
    spec = _spec()
    _write(path, _wave(1, [spec]),
           {"event": journal.WAVE_FAILED, "wave": 1, "invocation_ids": [spec.invocation_id]})
    state = _replay(path, _pool(spec.invocation_id))
    assert state["requested"] == set()
    assert state["spend"] == 0.0


def test_the_payload_is_not_written_to_the_journal(tmp_path):
    """It is the arm's whole rendered task data and it is already in the pool file, unchanged.
    Journaling it would copy the pool on every dispatch."""

    row = journal.spec_row(_spec())
    assert "payload" not in row
    assert row["invocation_id"] == "wu:1#proof_golf"


def test_the_payload_is_rejoined_from_the_pool(tmp_path):
    path = tmp_path / "j.jsonl"
    spec = _spec()
    _write(path, _wave(1, [spec]), _settled(_outcome()))
    state = _replay(path, _pool(spec.invocation_id))
    _outcome_back, spec_back = state["outcomes"][spec.invocation_id]
    assert spec_back.payload == {"task_type": "arm", "big": "x" * 100}
    assert spec_back.disposition == "proposed"


# --- robustness ---------------------------------------------------------------------------


def test_replaying_twice_gives_the_same_state(tmp_path):
    """Idempotence is the property that makes this safe to run on every construction."""

    path = tmp_path / "j.jsonl"
    spec = _spec()
    _write(path, _wave(1, [spec]), _settled(_outcome(cost=0.4)))
    pool = _pool(spec.invocation_id)
    once, twice = _replay(path, pool), _replay(path, pool)
    assert once["spend"] == twice["spend"] == pytest.approx(0.4)
    assert once["requested"] == twice["requested"]


def test_a_truncated_last_line_stops_replay_without_losing_the_rest(tmp_path):
    """A crash mid-write truncates one line. Everything before it is intact."""

    path = tmp_path / "j.jsonl"
    spec = _spec()
    text = "".join(json.dumps(e, default=str) + "\n"
                   for e in (_wave(1, [spec]), _settled(_outcome(cost=0.5))))
    path.write_text(text + '{"event": "settled", "outcome": {"invoc', encoding="utf-8")
    state = _replay(path, _pool(spec.invocation_id))
    assert state["spend"] == pytest.approx(0.5)


def test_a_settlement_whose_dispatch_is_missing_still_counts_its_spend(tmp_path):
    """The object cannot be rebuilt, but the money was spent. Dropping the cost would be the
    same class of error as the reset this whole file is about."""

    path = tmp_path / "j.jsonl"
    _write(path, _settled(_outcome(cost=0.6)))
    state = _replay(path, {})
    assert state["spend"] == pytest.approx(0.6)
    assert state["outcomes"] == {}


def test_no_journal_path_means_no_replay_and_no_error(tmp_path):
    """Every existing caller constructs a lead without one — a task exercised in a test, or a
    routing mode that does not delegate."""

    state = _fresh_state()
    journal.replay(None, state, pool={}, spec_cls=JobSpec, outcome_cls=JobOutcome)
    journal.replay(str(tmp_path / "absent.jsonl"), state, pool={},
                   spec_cls=JobSpec, outcome_cls=JobOutcome)
    assert state == _fresh_state()


def test_a_journal_write_never_raises(tmp_path):
    """A wave's results must not be lost because the journal could not be written."""

    journal.append(str(tmp_path / "no" / "such" / "dir" / "j.jsonl"), {"event": "x"})
    journal.append(None, {"event": "x"})
    assert (tmp_path / "no" / "such" / "dir" / "j.jsonl").is_file()


# --- the wiring, not just the module ------------------------------------------------------
#
# The module being correct proves nothing about whether the lead uses it. These drive the
# actual task: build one, have it act, throw it away, build a second on the same journal.


def _lead(tmp_path, journal_path):
    import asyncio

    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.lead import (
        ReviewLeadData, ReviewLeadTask,
    )
    from tests.datasets.test_pr_review_v5_lead import CENSUS, PROPOSALS, FakeMCP, _pool_file

    data = ReviewLeadData(
        task_id="pr5lead_test", episode_id="ep:1", pr_number=33098,
        pr_title="t", pr_description="d", diff="--- a\n+++ b\n",
        changed_files=["Mathlib/A.lean"], proposals=list(PROPOSALS), census=list(CENSUS),
        arm_pool_path=str(_pool_file(tmp_path)),
        trace_path=str(tmp_path / "trace.jsonl"),
        journal_path=str(journal_path),
        target_workspace={"name": "target", "commit_hash": "c" * 40,
                          "repo_url": "https://example.invalid/m.git",
                          "default_target": "Mathlib"},
    )
    task = ReviewLeadTask(data, ApeAgentConfig())
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    return task, mcp.tools


def test_the_lead_writes_its_comprehension_and_a_new_lead_reads_it_back(tmp_path):
    import asyncio

    path = tmp_path / "j.jsonl"
    _task, tools = _lead(tmp_path, path)
    asyncio.run(tools["submit_comprehension"](
        summary="Renames encard_ lemmas across the file to the new spelling.",
        questions=[{"kind": "convention", "question": "Does `grind` close these?"}]))
    assert path.is_file()

    # A second lead on the same journal: a resume, as far as the task is concerned.
    resumed, tools = _lead(tmp_path, path)
    state = resumed._state()
    assert state["comprehension"]["summary"].startswith("Renames encard_")

    # And `delegate` no longer sends it back to read the PR again.
    result = asyncio.run(tools["delegate"](jobs=[]))
    assert "submit_comprehension" not in str(result.get("message") or "")


def test_a_lead_with_no_journal_path_still_works(tmp_path):
    """Every routing mode that does not delegate, and every test that predates this."""

    import asyncio

    task, tools = _lead(tmp_path, tmp_path / "unused.jsonl")
    task.data.journal_path = None
    asyncio.run(tools["submit_comprehension"](
        summary="Renames encard_ lemmas across the file to the new spelling.",
        questions=[{"kind": "convention", "question": "Does `grind` close these?"}]))
    assert task._state()["comprehension"] is not None
