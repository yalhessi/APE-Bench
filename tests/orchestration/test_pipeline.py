"""Stages run in dependency order, as soon as their inputs exist, and a refusal is a result.

The primitive knows nothing about what a stage does: a node is a name, what it waits for, a
coroutine, and a predicate saying whether it already ran. That is what keeps a pipeline an
order over commands rather than a scheduler over artifacts -- every stage still runs by its own
command, reads what it reads for itself, and records what it read.
"""

from __future__ import annotations

import asyncio

import pytest

from ape.orchestration.pipeline import (
    PipelineCycle, StageNode, order, run_pipeline,
)


def _tracer():
    """Executors that record when each node starts and ends, so overlap is observable."""

    events = []

    def make(name, delay=0.02, raises=None):
        async def go():
            events.append(f"start {name}")
            await asyncio.sleep(delay)
            if raises is not None:
                raise raises
            events.append(f"end {name}")
            return name
        return go

    return events, make


def test_a_node_starts_the_moment_its_last_dependency_finishes():
    events, make = _tracer()
    nodes = [StageNode("run"), StageNode("judge", ["run"]), StageNode("judge2", ["run"])]
    table = asyncio.run(run_pipeline(
        nodes, execute={node.name: make(node.name) for node in nodes}, max_parallel=2))

    assert {name: status.status for name, status in table.items()} == {
        "run": "ran", "judge": "ran", "judge2": "ran"}
    # The two judges overlap, and neither starts before the run they read has finished.
    assert events.index("end run") < events.index("start judge")
    assert events.index("start judge2") < events.index("end judge")


def test_the_parallel_cap_is_a_cap():
    """Two whole stages already compete for the same Lean workspaces and the same provider
    concurrency, so `max_parallel=1` has to mean one."""

    events, make = _tracer()
    nodes = [StageNode("run"), StageNode("a", ["run"]), StageNode("b", ["run"])]
    asyncio.run(run_pipeline(
        nodes, execute={node.name: make(node.name) for node in nodes}, max_parallel=1))
    assert events.index("end a") < events.index("start b") or \
           events.index("end b") < events.index("start a")


def test_a_refusal_skips_what_reads_it_and_nothing_else():
    """Stages spend money: by the time one refuses, the ones before it have paid. So a refusal
    is recorded, its dependents are skipped with the reason, and everything independent keeps
    running -- a pipeline that discarded the first node's work over the second's refusal would
    repeat a failure this repository already has a name for."""

    events, make = _tracer()
    nodes = [StageNode("run"), StageNode("judge", ["run"]),
             StageNode("buckets", ["judge"]), StageNode("replay", ["run"])]
    table = asyncio.run(run_pipeline(nodes, execute={
        "run": make("run"),
        "judge": make("judge", raises=ValueError("closed as partial")),
        "buckets": make("buckets"),
        "replay": make("replay"),
    }, max_parallel=2))

    assert table["judge"].status == "refused" and "partial" in table["judge"].detail
    assert table["buckets"].status == "skipped" and "judge" in table["buckets"].detail
    assert table["run"].status == "ran" and table["replay"].status == "ran"
    assert "start buckets" not in events


def test_a_defect_is_recorded_as_failed_rather_than_raised():
    """Same reasoning, different word: a refusal is the stage declining, a failure is a bug,
    and neither may take down work that is already paid for."""

    _events, make = _tracer()
    nodes = [StageNode("run"), StageNode("judge", ["run"])]
    table = asyncio.run(run_pipeline(nodes, execute={
        "run": make("run"), "judge": make("judge", raises=KeyError("boom"))}, max_parallel=2))
    assert table["judge"].status == "failed" and "KeyError" in table["judge"].detail
    assert table["run"].status == "ran"


def test_work_that_already_exists_is_not_done_again():
    """Re-invoking a pipeline is how one that stopped is continued. `done` and `ran` stay
    different words: a report that collapsed them could not tell a resumed pipeline from one
    that paid twice."""

    events, make = _tracer()
    nodes = [StageNode("run"), StageNode("judge", ["run"])]
    table = asyncio.run(run_pipeline(
        nodes, execute={node.name: make(node.name) for node in nodes},
        is_done={"run": lambda: True}, max_parallel=2))

    assert table["run"].status == "done" and table["judge"].status == "ran"
    assert "start run" not in events
    assert table["run"].satisfied and table["judge"].satisfied


def test_a_done_check_that_raises_runs_the_stage_rather_than_skipping_it():
    """An unreadable check is not a done check. Running again is the safe answer: a stage that
    resumes costs little, and one that is skipped in error is missing from the result."""

    events, make = _tracer()
    nodes = [StageNode("run")]

    def explode():
        raise OSError("cannot read the ledger")

    table = asyncio.run(run_pipeline(
        nodes, execute={"run": make("run")}, is_done={"run": explode}, max_parallel=1))
    assert table["run"].status == "ran" and "start run" in events


@pytest.mark.parametrize("nodes, match", [
    ([StageNode("a", ["b"]), StageNode("b", ["a"])], "wait on each other"),
    ([StageNode("a", ["nope"])], "unknown stage"),
    ([StageNode("a"), StageNode("a")], "duplicate"),
])
def test_an_unorderable_graph_is_refused_before_anything_is_dispatched(nodes, match):
    """A cycle found after the first stage has spent money is a cycle found too late."""

    with pytest.raises(PipelineCycle, match=match):
        order(nodes)
    with pytest.raises(PipelineCycle):
        asyncio.run(run_pipeline(nodes, execute={}, max_parallel=1))
