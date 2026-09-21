"""One node of a pipeline, run exactly the way its own command runs it.

This module is deliberately thin and deliberately boring: each adapter loads the same config
through the same loader, applies the same derivation, and calls the same entry point the CLI
calls. Nothing here decides anything a stage would not decide for itself -- a judge node
derives its audit from `derive_from_run(root, node)` because that is what `judge --of` does,
and reads the run through `StageInput` because that is what the judge does.

If an adapter ever needs to compute something a stage cannot, that is the signal that the
pipeline has started to be a scheduler over artifacts rather than an order over commands, and
the thing to move is the computation into the stage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from ape.utils.config_loader import deep_merge


def adapter(plan, name: str, logger) -> Callable[[], Awaitable[Any]]:
    """The coroutine that runs one node."""

    node = plan.stages[name]
    kind = node["kind"]
    builder = _ADAPTERS.get(kind)
    if builder is None:
        raise ValueError(f"stage {name!r} has unknown kind {kind!r}")
    return builder(plan, name, node, logger)


def _config_overrides(node: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    from src.mathlib_review.review.pipeline import _overrides

    return deep_merge(_overrides(node), extra)


def _run_node(plan, name, node, logger):
    async def go():
        from src.mathlib_review.review.runner import load_run, run

        dataset, scaffold, task_overrides = load_run(
            Path(node["config"]),
            _config_overrides(node, {"dataset": {"run_name": node["target"]["run_name"]}}))
        dataset.dry_run = False
        return str(await run(dataset, scaffold, task_overrides, logger))

    return go


def _judge_node(plan, name, node, logger):
    async def go():
        from src.mathlib_review.judge.runner import (
            assert_paths_agree, derive_from_run, load_run, run,
        )

        # Derived here the way `judge --of` derives it, and then checked by the judge's own
        # `assert_paths_agree` -- so a pipeline cannot point a judge at a run it does not name.
        derived = {key: str(value)
                   for key, value in derive_from_run(plan.root_run, name).items()}
        dataset, scaffold, task_overrides = load_run(
            Path(node["config"]), _config_overrides(node, {"dataset": derived}))
        assert_paths_agree(dataset, plan.root_run)
        dataset.dry_run = False
        return str(await run(dataset, scaffold, task_overrides, logger))

    return go


def _replay_node(plan, name, node, logger):
    async def go():
        from src.mathlib_review.review.replay import load_replay, run_replay

        dataset, execution = load_replay(
            Path(node["config"]),
            _config_overrides(node, {"dataset": {
                "of_run": plan.root_run,
                "run_name": node["target"]["run_name"],
                **({"selector": node["select"]} if node.get("select") else {}),
            }}))
        return str(await run_replay(dataset, execution, logger, execute=True))

    return go


def _adjudicate_node(plan, name, node, logger):
    async def go():
        from src.mathlib_review.judge.adjudicate import adjudicate_run

        return str(adjudicate_run(
            plan.root_run, labels=Path(node["labels"]) if node.get("labels") else None,
            logger=logger))

    return go


def _buckets_node(plan, name, node, logger):
    async def go():
        import json

        from src.mathlib_review.analysis.report import buckets

        payload = buckets([plan.root_run], audit=True)
        logger.info("buckets: %s", json.dumps(payload.get("coarse", {})))
        return payload

    return go


_ADAPTERS = {
    "run": _run_node,
    "judge": _judge_node,
    "replay": _replay_node,
    "adjudicate": _adjudicate_node,
    "report.buckets": _buckets_node,
}
