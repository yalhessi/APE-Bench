"""Run declared stages in dependency order, starting each as soon as its inputs exist.

A stage here is not a task. `TaskOrchestrator` runs many samples of one task type inside one
process; this runs a handful of *whole stages*, each of which is an ordinary command that could
have been typed by hand -- generate, judge, replay, adjudicate -- in the order their inputs
allow, with independent ones overlapping.

**It orders and dispatches, and does nothing else.** It computes no paths, reads no artifacts
and knows nothing about what any stage does: a node is a name, what it waits for, a coroutine
that runs it, and a predicate that says whether it already ran. Every stage remains
independently runnable by its own command and produces identical outputs either way. That
separation is the point rather than an implementation detail -- the stages are separable
because each writes immutable artifacts under one run name, and a layer that hid which
artifacts a stage read would remove the property that makes a run reproducible at all.

**A refusal is a result, not an exception.** Stages spend money; by the time one refuses, the
ones before it have paid. So a refusal is recorded against that node, its dependents are marked
skipped with the reason, everything independent of it keeps running, and the table comes back
for the caller to exit on. A pipeline that died on its second node and discarded the first
node's work would repeat the failure this repository already has a name for.

**Re-invoking is resuming.** A node whose work is already done is reported `done` without
running, so the way to continue a pipeline that stopped is to run it again.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence

#: How many stages may run at once. Small: a stage is a whole orchestrator, and two of them
#: are already competing for the same Lean workspaces and the same provider concurrency.
DEFAULT_MAX_PARALLEL_STAGES = 2


class PipelineCycle(ValueError):
    """The declared graph cannot be ordered, so nothing is dispatched."""


@dataclass(frozen=True)
class StageNode:
    """One stage in the graph: its name, and the nodes whose outputs it reads."""

    name: str
    needs: Sequence[str] = ()


@dataclass
class StageStatus:
    """What became of one node.

    `ran` and `done` are deliberately different words. `done` means the work already existed
    when the pipeline looked, which is what makes re-invoking a resume; `ran` means this
    invocation did it. A report that collapsed them could not tell a resumed pipeline from one
    that paid twice.
    """

    name: str
    #: `ran` | `done` | `refused` | `failed` | `skipped`
    status: str
    detail: Optional[str] = None
    result: Any = None
    seconds: float = 0.0

    @property
    def satisfied(self) -> bool:
        """Whether the node's output now exists, however it came to."""

        return self.status in {"ran", "done"}


def order(nodes: Sequence[StageNode]) -> List[str]:
    """Node names in a legal order, refusing a graph that has none.

    Refused before dispatch rather than discovered halfway: a cycle found after the first stage
    has spent money is a cycle found too late.
    """

    names = [node.name for node in nodes]
    if len(set(names)) != len(names):
        raise PipelineCycle(f"duplicate stage name(s) in {names}")
    by_name = {node.name: node for node in nodes}
    for node in nodes:
        unknown = [item for item in node.needs if item not in by_name]
        if unknown:
            raise PipelineCycle(f"stage {node.name!r} waits for unknown stage(s) {unknown}")

    ordered: List[str] = []
    pending = {node.name: set(node.needs) for node in nodes}
    while pending:
        ready = sorted(name for name, needs in pending.items() if not needs - set(ordered))
        if not ready:
            raise PipelineCycle(
                f"these stages wait on each other and none can start: {sorted(pending)}")
        ordered.extend(ready)
        for name in ready:
            pending.pop(name)
    return ordered


async def run_pipeline(
    nodes: Sequence[StageNode],
    *,
    execute: Dict[str, Callable[[], Awaitable[Any]]],
    is_done: Optional[Dict[str, Callable[[], bool]]] = None,
    max_parallel: int = DEFAULT_MAX_PARALLEL_STAGES,
    logger=None,
    refusals: Sequence[type] = (ValueError,),
) -> Dict[str, StageStatus]:
    """Run every node whose dependencies are satisfied, as soon as they are.

    `refusals` are the exception types that mean "this stage declined", as opposed to a defect:
    they are recorded with their message and the run continues elsewhere. Anything else is
    recorded as `failed` with its repr, for the same reason -- by the time it is raised, other
    nodes have already spent.
    """

    order(nodes)
    is_done = dict(is_done or {})
    statuses: Dict[str, StageStatus] = {}
    by_name = {node.name: node for node in nodes}
    limit = asyncio.Semaphore(max(1, int(max_parallel)))
    started: Dict[str, asyncio.Task] = {}

    async def run_one(node: StageNode) -> StageStatus:
        # Wait here rather than in a scheduler loop: a node starts the instant its last
        # dependency finishes, which is what lets two judges of one run overlap.
        for need in node.needs:
            await asyncio.shield(asyncio.ensure_future(started[need]))
        blocked = [need for need in node.needs if not statuses[need].satisfied]
        if blocked:
            return StageStatus(node.name, "skipped",
                               f"waits for {blocked}, which did not produce its output")
        check = is_done.get(node.name)
        try:
            if check is not None and check():
                if logger:
                    logger.info("stage %s: already done, not run again", node.name)
                return StageStatus(node.name, "done", "its output already existed")
        except Exception as error:  # noqa: BLE001 - an unreadable check is not a done check
            if logger:
                logger.warning("stage %s: could not tell whether it had already run (%s); "
                               "running it", node.name, error)
        async with limit:
            loop = asyncio.get_event_loop()
            started_at = loop.time()
            if logger:
                logger.info("stage %s: starting", node.name)
            try:
                result = await execute[node.name]()
                return StageStatus(node.name, "ran", result=result,
                                   seconds=round(loop.time() - started_at, 3))
            except tuple(refusals) as error:
                if logger:
                    logger.error("stage %s refused: %s", node.name, error)
                return StageStatus(node.name, "refused", str(error),
                                   seconds=round(loop.time() - started_at, 3))
            except Exception as error:  # noqa: BLE001 - see the docstring
                if logger:
                    logger.error("stage %s failed: %r", node.name, error, exc_info=True)
                return StageStatus(node.name, "failed", repr(error),
                                   seconds=round(loop.time() - started_at, 3))

    async def record(node: StageNode) -> None:
        statuses[node.name] = await run_one(node)

    for name in order(nodes):
        started[name] = asyncio.ensure_future(record(by_name[name]))
    await asyncio.gather(*started.values())
    return {name: statuses[name] for name in order(nodes)}
