"""A declared experiment: one generation run and the stages that read it, in order.

An experiment here is several commands chained by a run name typed correctly each time --
generate, judge, maybe judge again under a widened rule, maybe replay the decisions the judge
says were missed. Each is a separate process on purpose, and that stays true: **every node runs
the same code path its own command runs, under its own config, and writes the same artifacts
and the same ledger row either way.** What this adds is ordering, dispatch and one sealed
statement of what was going to happen.

It is emphatically not a scheduler over artifacts. No node's paths are computed here that the
node would not compute for itself: a judge node still derives its audit from
`derive_from_run(root, node)` exactly as `judge --of` does, and reads the run through
`StageInput`, so its row records what it read rather than what this file told it to read. The
hand-off stays named provenance; the graph only says what may start when.

**Ordering is stage-granular.** A node starts when every node it waits for has produced its
output, and independent nodes overlap under a cap. Judging PR X while PR Y is still under
review would need per-PR finalization, which `finalize` does not do -- it is recorded as a todo
rather than half-built here.

**Re-invoking resumes.** A node whose output already exists is reported `done` and not run, so
a pipeline that stopped is continued by running it again.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ape.orchestration.pipeline import StageNode, run_pipeline
from ape.utils.config_loader import load_yaml, parse_cli_args

from src.mathlib_review.io import (
    canonical_json_bytes, git_state, pretty_json_bytes, sha256_bytes, sha256_file, write_once,
)
from src.mathlib_review.paths import run_dir
from src.mathlib_review.schema.runs import PipelinePlan, PipelineSpec


class PipelineRefused(ValueError):
    """A pipeline that cannot be run as declared, refused before anything spends."""


def load_pipeline(config_path: Path, overrides: Optional[Dict[str, Any]] = None) -> PipelineSpec:
    """The declared graph, validated before any of its nodes' configs are opened."""

    raw = load_yaml(config_path)
    if overrides:
        from ape.utils.config_loader import deep_merge

        raw = deep_merge(raw, overrides)
    return PipelineSpec.model_validate(raw)


def target_of(spec: PipelineSpec, node: str, root_run: str) -> Dict[str, str]:
    """Where this node's output goes, derived the way the node itself derives it.

    Nothing invented here. A judge node's audit is `derive_from_run(root, node)`, which is what
    `judge --of` computes; a replay's run name carries its condition and its cut, because
    `run_replay` refuses a name that does not.
    """

    from src.mathlib_review.judge.runner import derive_from_run

    stage = spec.stages[node]
    if stage.kind == "run":
        return {"run_name": root_run}
    if stage.kind == "judge":
        derived = derive_from_run(root_run, node)
        return {"run_name": derived["run_name"], "out_dir": str(derived["out_dir"])}
    if stage.kind == "replay":
        return {"run_name": f"{root_run}_{node}"}
    if stage.kind == "adjudicate":
        return {"out_dir": str(derive_from_run(root_run, "judge")["out_dir"])}
    return {"of": root_run}


def build_plan(spec: PipelineSpec, root_run: str, config_path: Path) -> PipelinePlan:
    """Resolve the graph and every node's config, and hash all of it.

    Every config is OPENED here, before the first node starts. A judge config that does not
    parse is worth discovering before the generation run spends, not four hours later.
    """

    stages: Dict[str, Dict[str, Any]] = {}
    edges = spec.edges()
    for name, node in spec.stages.items():
        config = Path(node.config) if node.config else None
        if config is not None and not config.is_file():
            raise PipelineRefused(
                f"stage {name!r} names config {config}, which does not exist. Every node's "
                f"config is resolved before the first one runs, so a typo here costs nothing "
                f"instead of being found after the run has spent.")
        stages[name] = {
            "kind": node.kind,
            "config": str(config) if config else None,
            "config_sha256": sha256_file(config) if config else None,
            "of": node.of or (spec.root if name != spec.root else None),
            "needs": edges[name],
            "overrides": dict(node.overrides),
            "select": node.select,
            "labels": node.labels,
            "target": target_of(spec, name, root_run),
        }
    payload = spec.model_dump(mode="json")
    commit, tree_state = git_state()
    return PipelinePlan(
        pipeline_id=f"pipeline:{sha256_bytes(canonical_json_bytes(payload))[:24]}",
        root_run=root_run,
        spec_sha256=sha256_bytes(canonical_json_bytes(payload)),
        max_parallel_stages=spec.max_parallel_stages,
        stages=stages, git_commit=commit, git_tree_state=tree_state,
    )


def _overrides(node: Dict[str, Any]) -> Dict[str, Any]:
    """A node's overrides in the shape every command's `--set` produces, so a node config and a
    hand-typed invocation cannot mean different things."""

    return parse_cli_args([f"{key}={value}" for key, value in (node["overrides"] or {}).items()])


#: Fields of a sealed pipeline plan a later invocation may legitimately differ in.
#:
#: The same set, and the same reasoning, as `runner.RESUMABLE_PLAN_FIELDS`: these are
#: provenance of *this attempt*, not of the experiment. Everything else -- the graph, the
#: nodes, their configs and their digests -- is what the plan pre-registers, and a change
#: there is a different pipeline under one name.
RESUMABLE_PIPELINE_FIELDS = frozenset({"git_commit", "git_tree_state"})


class PipelineChangedSemantically(RuntimeError):
    """A re-invocation would run a different graph than the one sealed under this name."""


def seal_or_revise(out: Path, plan: PipelinePlan, logger) -> Path:
    """Write the pipeline plan, or record a revision when only provenance moved.

    `write_once` refuses a differing artifact, which is right for the graph and too blunt for
    re-invocation -- and re-invoking IS the documented way to resume a pipeline that stopped.
    Found by doing it: the second invocation died on `FileExistsError` before reaching the
    resume logic at all, because the plan embeds `git_commit` and `git_tree_state` and the tree
    had moved. That is not an edge case; it is what happens whenever anything is committed
    between two invocations, which is most of the time.

    So the plan follows `runner.seal_or_revise_plan`, the convention this repository already
    settled on for exactly this problem: `pipeline.json` is what was sealed first,
    `pipeline_revision_2.json` is what the second invocation ran under, and a change to the
    GRAPH is still refused with the differing fields named.
    """

    sealed = out / "pipeline.json"
    payload = pretty_json_bytes(plan.model_dump(mode="json"))
    if not sealed.exists():
        write_once(sealed, payload)
        return sealed
    if sealed.read_bytes() == payload:
        return sealed

    before = json.loads(sealed.read_text(encoding="utf-8"))
    after = plan.model_dump(mode="json")
    changed = {key for key in set(before) | set(after) if before.get(key) != after.get(key)}
    semantic = sorted(changed - RESUMABLE_PIPELINE_FIELDS)
    if semantic:
        raise PipelineChangedSemantically(
            f"the pipeline sealed for {plan.root_run!r} differs in {semantic}, which changes "
            f"what the experiment IS rather than when it ran. Re-invoking under the same name "
            f"would attribute two graphs to one pre-registration. Use a new --run-name."
        )

    revision = 2
    while (out / f"pipeline_revision_{revision}.json").exists():
        revision += 1
    path = out / f"pipeline_revision_{revision}.json"
    write_once(path, payload)
    logger.info("re-invoked %s: %s changed. The original pipeline.json stands; %s records this "
                "invocation.", plan.root_run, sorted(changed), path.name)
    return path


def _is_done(plan: PipelinePlan, name: str) -> Callable[[], bool]:
    """Whether this node's work already exists.

    The generation stage is asked of its artifacts -- the run's own state. Every other stage is
    asked of the LEDGER, and deliberately not of its output directory: an audit on disk says a
    judgement happened, not that it was this one's, and a pipeline that called a foreign audit
    "done" would silently not run the judge it was asked for.

    Being conservative here costs almost nothing and buys the refusal. Re-running a judge over
    an audit it already produced is a resume -- resume is the judge's cache, so no pair is
    called twice and `write_once` no-ops on identical bytes -- while re-running one over an
    audit written under a DIFFERENT identity is refused before it spends, with both identities
    named. Skipping the node would have skipped that refusal too.
    """

    node = plan.stages[name]
    target = node["target"]

    def done() -> bool:
        from src.mathlib_review.run_state import ledger, state_of

        if node["kind"] == "run":
            return state_of(run_dir(plan.root_run)) in _closed_states()
        rows = ledger(run_dir(plan.root_run))
        if node["kind"] == "judge":
            return any(
                row.get("stage") == "judge"
                and row.get("produced", {}).get("out_dir") == target.get("out_dir")
                for row in rows)
        if node["kind"] == "replay":
            return any(row.get("stage") == "replay"
                       and row.get("produced", {}).get("run") == target.get("run_name")
                       for row in rows)
        return False

    return done


def _nodes(plan: PipelinePlan) -> List[StageNode]:
    return [StageNode(name, tuple(node["needs"])) for name, node in sorted(plan.stages.items())]


async def preflight(plan: PipelinePlan, logger) -> Dict[str, Any]:
    """Run what each node can check before anything has happened, and say what it cannot.

    Hashing every config catches the typo and the missing file. It does not catch the config
    that would be REFUSED -- a budget that cannot fit its own coverage floor, an episode with no
    reviewed workspace, a set whose retrieval cutoffs do not resolve. Those refusals are the
    generation stage's own, and they are free: `plan` is `run` with `dry_run`, so the root node
    is preflighted exactly the way `cli plan` preflights it.

    A downstream node cannot be preflighted this side of the run, and saying so is the honest
    answer rather than implying a check happened. `judge` refuses a partial source run, a
    second judge identity in one audit, and a PR the run never reviewed -- every one of those
    reads artifacts that do not exist yet. What IS checked for it here is that its config loads
    and its paths derive, which `build_plan` did.
    """

    results: Dict[str, Any] = {}
    for name in sorted(plan.stages):
        node = plan.stages[name]
        if node["kind"] != "run":
            results[name] = {
                "checked": "config loads, paths derive",
                "deferred": ("this stage's own refusals read artifacts the root run has not "
                             "produced yet"),
            }
            continue
        try:
            from src.mathlib_review.review.runner import load_run, run as run_generation

            from src.mathlib_review.review.stage_adapters import _config_overrides

            # Through the adapter's own merge, not a dict `|`: `_overrides(node)` already puts
            # the node's settings under `dataset`, and a shallow merge REPLACES that key --
            # which silently priced all twelve PRs for a config whose node narrows it to one.
            # The preflight must resolve exactly what the adapter will run, or it is a check on
            # a different run.
            dataset, scaffold, task_overrides = load_run(
                Path(node["config"]),
                _config_overrides(node, {"dataset": {"run_name": node["target"]["run_name"]}}))
            dataset.dry_run = True
            await run_generation(dataset, scaffold, task_overrides, logger)
            results[name] = {"checked": "full generation preflight (plan)"}
        except Exception as error:  # noqa: BLE001 - a refusal here is the answer, not a crash
            logger.error("stage %s would be refused: %s", name, error)
            results[name] = {"refused": str(error)}
    refused = sorted(key for key, value in results.items() if "refused" in value)
    if refused:
        logger.error("PIPELINE WOULD NOT START: %s", ", ".join(refused))
    return results


async def run(spec: PipelineSpec, root_run: str, config_path: Path, logger, *,
              execute: bool) -> Dict[str, Any]:
    """Preflight the whole graph, and with `execute`, run it.

    Without `execute` nothing is written and no model is called: the graph is resolved, every
    node's config is opened and hashed, each node that can be preflighted is, and the plan is
    printed. That is the same rule every other verb here follows, and it matters more rather
    than less for a pipeline -- the cost of discovering a bad generation config after the
    generation run is the generation run.
    """

    plan = build_plan(spec, root_run, config_path)
    logger.info("pipeline %s over %d stage(s), %d at a time",
                plan.pipeline_id[-12:], len(plan.stages), plan.max_parallel_stages)
    for name in sorted(plan.stages):
        node = plan.stages[name]
        logger.info("  %-18s %-14s needs=%-22s -> %s", name, node["kind"],
                    ",".join(node["needs"]) or "-", json.dumps(node["target"]))

    if not execute:
        return {"plan": plan.model_dump(mode="json"), "ran": False,
                "preflight": await preflight(plan, logger)}

    out = run_dir(root_run)
    out.mkdir(parents=True, exist_ok=True)
    seal_or_revise(out, plan, logger)

    from src.mathlib_review.review import stage_adapters

    table = await run_pipeline(
        _nodes(plan),
        execute={name: stage_adapters.adapter(plan, name, logger)
                 for name in plan.stages},
        is_done={name: _is_done(plan, name) for name in plan.stages},
        max_parallel=plan.max_parallel_stages,
        logger=logger,
        refusals=(ValueError, FileNotFoundError),
    )
    summary = {
        "pipeline": plan.pipeline_id,
        "root_run": root_run,
        "stages": {name: {"status": status.status, "detail": status.detail,
                          "seconds": status.seconds}
                   for name, status in table.items()},
        "ran": True,
    }
    unfinished = sorted(name for name, status in table.items() if not status.satisfied)
    summary["unfinished"] = unfinished
    for name in unfinished:
        logger.error("stage %s: %s -- %s", name, table[name].status, table[name].detail)
    return summary


def _closed_states():
    """Run states that mean the generation stage's work exists.

    `PARTIAL` counts. It closed, it produced artifacts, and re-running the name would be
    refused anyway -- what a partial run must not do is get judged silently, and that refusal
    belongs to the judge, not here. A pipeline over a partial run therefore reports its judge
    node as refused, with the judge's own words.
    """

    from src.mathlib_review.run_state import RunState

    return {RunState.GENERATED, RunState.FINALIZED, RunState.JUDGED, RunState.PARTIAL}
