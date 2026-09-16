"""Decision-turn replay for review arms: what the arm decides, with its investigation held still.

Every change aimed at the submission decision -- abstention wording, the bar, field order,
confidence elicitation -- used to be tested with a whole rep, which re-samples the
investigation as well. A decision change then competes with investigation variance it did not
cause, read through a judge that splits its own vote on ~11% of pairs. Forcing the decision
alone moved issue recall 0.20 -> 0.50 on the same PRs, so the decision is where this system's
findings go missing (`docs/todo/replay-decision-turn.md`).

The replay itself is not review code. `ape.scaffolds.ape_agent.replay` runs any recorded task
again from a point inside its conversation, as the same task type; this module supplies the
two things that are review's own: where an arm's decision starts, and what it decided.

**Where the replay takes over is the run's choice**, stated as a `cut` in its config -- any
assistant turn from either end, a node index, or a tool call (`ape.scaffolds.ape_agent.replay`
resolves it per session). Three cuts this evidence makes worth asking about:

* `before_tool_call: {tool: submit_candidates, occurrence: first}` -- the decision turn, with
  the whole investigation held fixed. **The first call, not the last:** 26 / 31 / 28 of the
  321 / 316 / 322 sessions on the v2 reps had a first submission refused and then repaired it,
  and the arm task counts refusals on its instance (`_mute_abstentions`, `_forced_presses`),
  which a replayed instance starts at zero -- so a prefix holding a refusal would disagree with
  the contract it replays against. The repair turns are re-sampled as part of the decision.
* `before_turn: -1` -- the last turn the arm took, whatever it was.
* `before_turn: 1` -- the whole task from its recorded prompt, which is how a tool-schema or
  prompt change is tested against the investigation *and* the decision it would cause.

The cut is refused, per session, when it cannot resolve or would land inside a turn, and the
skipped sessions are named in the plan rather than silently dropped.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

from ape.scaffolds.ape_agent.replay import (
    REPLAY_RECORD_FILENAME, SESSION_REPLAY_KEY, CutPoint, ReplayCondition, ReplayRefused, cut,
    parse_cut, replay_task_data, tool_calls,
)
from src.mathlib_review.io import (
    canonical_json_bytes, git_state, jsonl_bytes, jsonl_rows, load_jsonl, pretty_json_bytes,
    sha256_bytes, sha256_file, write_once,
)
from src.mathlib_review.paths import run_dir

SUBMIT_TOOL = "submit_candidates"


def submission_summary(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """One `submit_candidates` call, reduced to the levels a replay is compared at.

    `argument_order` and `candidate_field_order` are the model's emission order, read off the
    call arguments -- a field-order condition is effective only if the model follows it, and the
    accepted result cannot say, because validation re-serialises it in schema order.
    """

    candidates = [item for item in (arguments.get("candidates") or []) if isinstance(item, dict)]
    return {
        "filed": bool(candidates),
        "abstention_reason": None if candidates else arguments.get("abstention_reason"),
        "anchors": sorted({str(item.get("primary_change_id")) for item in candidates}),
        "candidate_keys": sorted({
            "|".join(str(item.get(key)) for key in
                     ("primary_change_id", "concern_family", "issue_kind"))
            for item in candidates}),
        "model_confidence": [item.get("model_confidence") for item in candidates],
        "argument_order": list(arguments),
        "candidate_field_order": [list(item) for item in candidates],
    }


def accepted_summary(result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The submission the task accepted, from its result; None when nothing was accepted."""

    if not result or not result.get("success"):
        return None
    summary = submission_summary({
        "candidates": result.get("candidates") or [],
        "abstention_reason": (result.get("abstention") or {}).get("reason"),
    })
    for key in ("argument_order", "candidate_field_order"):
        summary.pop(key)
    return summary


def decision_record(nodes: List[Dict[str, Any]], start: int) -> Dict[str, Any]:
    """Every submission from `start` on: how many turns, what was refused, what came first."""

    calls = tool_calls(nodes, start, SUBMIT_TOOL)
    return {
        "turns": sum(1 for node in nodes[start:] if node.get("type") == "assistant"),
        "submissions": len(calls),
        "refusals": [call["message"] for call in calls if call["accepted"] is False],
        "first": submission_summary(calls[0]["arguments"]) if calls else None,
    }


# --- the run -------------------------------------------------------------------------------


class ReplayDatasetConfig(BaseModel):
    """What a replay run is. Everything here is sealed into its plan."""

    model_config = ConfigDict(extra="forbid")

    #: The generation run whose arm sessions are replayed; `--of` on the command line.
    of_run: str
    run_name: str = "UNNAMED"
    condition: ReplayCondition
    arm_ids: List[str] = Field(default_factory=list)
    pr_numbers: List[int] = Field(default_factory=list)
    #: Exactly these sessions, for a case study on decisions someone has read. A requested id
    #: that the run does not hold is refused rather than dropped: a mistyped id would quietly
    #: shrink the run to the ones that matched, and the result would look like a measurement.
    invocation_ids: List[str] = Field(default_factory=list)
    invocation_limit: int = 0
    #: Where the model takes over. Required: nothing about a replay's cut is predetermined, and
    #: a default would quietly make one experiment look like the only one available.
    cut: CutPoint
    #: Assistant turns a replay may take after the cut. From the first-submission cut the
    #: recorded stage took one turn in 293 / 283 / 294 of the v2 sessions and at most 7, so 8
    #: truncates none of them; an earlier cut needs the turns that follow it too.
    turns_after_cut: int = 8
    per_task_cost_cap: float = 0.30
    #: Required. Checked before the first call against the recorded decision stage priced
    #: uncached, which is what a replay pays once its source's cache has expired.
    run_total_cost_cap: float = Field(gt=0)


class ReplayPlan(BaseModel):
    """Sealed before the first model call by `runner.seal_or_revise_plan`, whose resumable
    fields (`git_commit`, `git_tree_state`, `scaffold_config_sha256`) it shares by name."""

    model_config = ConfigDict(extra="forbid")

    run_name: str
    of_run: str
    condition: Dict[str, Any]
    condition_sha256: str
    selection: Dict[str, Any]
    cut: Dict[str, Any]
    cut_label: str
    turns_after_cut: int
    per_task_cost_cap: float
    run_total_cost_cap: float
    sample_count: int
    model_name: str
    prefix_sha256_by_invocation: Dict[str, str]
    skipped: List[Dict[str, str]]
    estimate: Dict[str, float]
    scaffold_config_sha256: str
    git_commit: str
    git_tree_state: str


class ReplaySource(BaseModel):
    """One recorded arm session, located through the run's own records."""

    invocation_id: str
    payload: Dict[str, Any]
    session_path: str
    session_sha256: str
    nodes: List[Dict[str, Any]]
    #: Where this run's cut resolved in this session.
    cut_index: int
    #: What the task accepted, from the successful attempt.
    result: Optional[Dict[str, Any]]
    #: The orchestrator config the arm ran under -- the nested one, not its lead's.
    scaffold_config: Dict[str, Any]

    def replayed_stage_cost(self) -> Tuple[float, float]:
        """`(billed, nominal)` over the recorded assistant turns this replay re-samples."""

        usage = [(node.get("message") or {}).get("usage") or {}
                 for node in self.nodes[self.cut_index:] if node.get("type") == "assistant"]
        billed = sum(float(u.get("cached_total_cost") or u.get("total_cost") or 0) for u in usage)
        return billed, sum(float(u.get("total_cost") or 0) for u in usage)


def load_replay(config_path, overrides: Optional[Dict[str, Any]] = None,
                cut_point: Optional[CutPoint] = None):
    """`(dataset, execution overrides)`. Model, tools and task config come from the source run.

    A replay under another model, tool grant or temperature is not a replay of the recorded
    decision, so a config sets only `dataset` and `execution` (concurrency, and `sample_count`
    -- the resamples per session).
    """

    from ape.utils.config_loader import deep_merge, load_yaml

    raw = load_yaml(config_path)
    if overrides:
        raw = deep_merge(raw, overrides)
    if cut_point is not None:
        # Replaces, never merges: a merged cut keeps the config's spelling beside the new one,
        # and a cut with two spellings is refused.
        raw.setdefault("dataset", {})["cut"] = cut_point.model_dump(exclude_none=True)
    dataset = ReplayDatasetConfig.model_validate(raw.pop("dataset"))
    extra = sorted(set(raw) - {"execution"})
    if extra:
        raise ReplayRefused(
            "a replay runs under the source run's model, tools and task config; a replay "
            f"config sets only `dataset` and `execution`, not {extra}")
    return dataset, raw.get("execution") or {}


async def select_sources(dataset: ReplayDatasetConfig):
    """`(sources, skipped)`: the recorded arm sessions to replay, and why any others were not.

    Located through the run's `execution_index.jsonl` and each task's `TaskStorage`, never by
    globbing; a repeated invocation keeps its last row, which is the retry.
    """

    from ape.orchestration.execution_index import INDEX_FILENAME, by_semantic_id
    from ape.orchestration.persistence import TaskStorage
    from ape.scaffolds.ape_agent.conversation import ApeAgentConversationManager
    from ape.tasks.lean_tasks.formal_math.review.arm import ARM_TASK_TYPE

    source = run_dir(dataset.of_run)
    index_path, pool_path = source / INDEX_FILENAME, source / "arm_pool.jsonl"
    for required in (index_path, pool_path):
        if not required.is_file():
            raise ReplayRefused(
                f"{required} is missing. A replay rebuilds each task from the run's own arm "
                "pool and finds each session through its execution index. arm_pool.jsonl is "
                "gitignored, so a worktree has it only if linked from the main checkout; the "
                "rel050 reps lost theirs with a deleted worktree (docs/todo/operational-floor.md).")
    wanted_arms, wanted_ids = set(dataset.arm_ids), set(dataset.invocation_ids)
    rows = {invocation_id: row for invocation_id, row in by_semantic_id(index_path).items()
            if row.get("task_type") == ARM_TASK_TYPE
            and (not wanted_arms or invocation_id.rsplit("#", 1)[-1] in wanted_arms)
            and (not wanted_ids or invocation_id in wanted_ids)}
    missing = sorted(wanted_ids - set(rows))
    if missing:
        raise ReplayRefused(
            f"{dataset.of_run} holds no arm session for {missing}; a replay of named sessions "
            "does not quietly become a replay of the ones that matched")
    pool = {row["invocation_id"]: row["task_data"] for row in jsonl_rows(pool_path)
            if row.get("invocation_id") in rows}

    sources: List[ReplaySource] = []
    skipped: List[Dict[str, str]] = []
    for invocation_id in sorted(rows):
        if dataset.invocation_limit and len(sources) >= dataset.invocation_limit:
            break
        row, payload = rows[invocation_id], pool.get(invocation_id)
        if payload is None:
            skipped.append({"invocation_id": invocation_id, "reason": "not in arm_pool.jsonl"})
            continue
        if dataset.pr_numbers and payload.get("pr_number") not in dataset.pr_numbers:
            continue
        samples = await TaskStorage(Path(row["task_dir"]), row["global_index"]).load_all_samples()
        attempt = next((samples[i].successful_attempt for i in sorted(samples)
                        if samples[i].successful_attempt is not None), None)
        session = (ApeAgentConversationManager.find_latest_session_path(Path(attempt.path))
                   if attempt is not None else None)
        if session is None:
            skipped.append({"invocation_id": invocation_id, "reason": (
                "no successful attempt" if attempt is None else "the attempt kept no session")})
            continue
        nodes = jsonl_rows(session)
        try:
            _, index = cut(nodes, dataset.cut)
        except ReplayRefused as exc:
            skipped.append({"invocation_id": invocation_id, "reason": str(exc)})
            continue
        config = json.loads((Path(row["task_dir"]).parent.parent / "config.json").read_text())
        result = attempt.result
        sources.append(ReplaySource(
            invocation_id=invocation_id, payload=payload, session_path=str(session),
            session_sha256=sha256_file(session), nodes=nodes, cut_index=index,
            result=result.model_dump(mode="json") if hasattr(result, "model_dump") else result,
            scaffold_config=config["config"]))
    return sources, skipped


#: The parts of an orchestrator config that decide what the model does. Every replayed session
#: must agree on them, and the replay runs under them.
_SEMANTIC_SCAFFOLD_KEYS = ("scaffold_type", "llm_config", "task_config_overrides",
                           "tools_config", "skills")


def replay_scaffold(sources: List[ReplaySource], execution: Dict[str, Any]):
    """The source's own scaffold config with only `execution` and the runs root replaced."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.scaffolds.config import BaseScaffoldConfig
    from ape.utils.config_loader import deep_merge

    def semantic(config):
        return {key: config.get(key) for key in _SEMANTIC_SCAFFOLD_KEYS}

    first = sources[0].scaffold_config
    differing = sorted(item.invocation_id for item in sources
                       if semantic(item.scaffold_config) != semantic(first))
    if differing:
        raise ReplayRefused("the selected sessions ran under different model or tool configs, "
                            f"e.g. {differing[:3]}; replay them separately")
    raw = copy.deepcopy(first)
    # The nested config's root is inside its lead's attempt; a replay runs top-level.
    raw["runs_base_dir"] = str(BaseScaffoldConfig.model_fields["runs_base_dir"].default)
    raw["execution"] = deep_merge(raw.get("execution") or {}, execution)
    return ApeAgentConfig.model_validate(raw)


def replay_payload(source: ReplaySource, dataset: ReplayDatasetConfig, out: Path):
    """`(payload, prefix bytes)`: the recorded arm task, started from this run's cut."""

    from ape.orchestration.models import EXECUTION_LIMITS_KEY

    prefix, index = cut(source.nodes, dataset.cut)
    task_data = {**source.payload,
                 # Never the source run's trace: a call made while deciding is this run's.
                 "trace_path": str(out / "context_trace.jsonl")}
    payload, content = replay_task_data(
        task_data, prefix, dataset.condition,
        # Named by hash: an invocation id carries `:` and `#`.
        out / "prefixes" / f"{sha256_bytes(source.invocation_id.encode())[:24]}.jsonl",
        {"run": dataset.of_run, "invocation_id": source.invocation_id,
         "session": source.session_path, "session_sha256": source.session_sha256,
         "cut": dataset.cut.model_dump(mode="json", exclude_none=True),
         "cut_label": dataset.cut.name, "cut_node_index": index})
    turns = payload[SESSION_REPLAY_KEY]["source"]["prefix_assistant_turns"]
    payload[EXECUTION_LIMITS_KEY] = {"max_turns": turns + dataset.turns_after_cut,
                                     "billed_cost_limit": dataset.per_task_cost_cap}
    return payload, content


def build_plan(dataset: ReplayDatasetConfig, scaffold, sources: List[ReplaySource],
               skipped, built) -> ReplayPlan:
    billed = sum(source.replayed_stage_cost()[0] for source in sources)
    nominal = sum(source.replayed_stage_cost()[1] for source in sources)
    samples = scaffold.execution.sample_count
    commit, tree_state = git_state()
    return ReplayPlan(
        run_name=dataset.run_name, of_run=dataset.of_run,
        condition=dataset.condition.model_dump(mode="json"),
        condition_sha256=dataset.condition.sha256(),
        selection={"arm_ids": dataset.arm_ids, "pr_numbers": dataset.pr_numbers,
                   "invocation_limit": dataset.invocation_limit},
        cut=dataset.cut.model_dump(mode="json", exclude_none=True),
        cut_label=dataset.cut.name, turns_after_cut=dataset.turns_after_cut,
        per_task_cost_cap=dataset.per_task_cost_cap,
        run_total_cost_cap=dataset.run_total_cost_cap, sample_count=samples,
        model_name=scaffold.llm_config.model_name or "",
        prefix_sha256_by_invocation={
            payload["invocation_id"]: payload[SESSION_REPLAY_KEY]["prefix_sha256"]
            for payload, _ in built},
        skipped=skipped,
        estimate={
            "recorded_replayed_stage_billed": round(billed, 4),
            "recorded_replayed_stage_nominal": round(nominal, 4),
            "expected_billed_if_cached": round(billed * samples, 2),
            "expected_billed_if_uncached": round(nominal * samples, 2),
            "ceiling_at_task_caps": round(len(sources) * samples * dataset.per_task_cost_cap, 2),
        },
        scaffold_config_sha256=sha256_bytes(canonical_json_bytes(
            {key: scaffold.model_dump(mode="json").get(key) for key in _SEMANTIC_SCAFFOLD_KEYS})),
        git_commit=commit, git_tree_state=tree_state,
    )


#: Written only after the orchestrator returns; their presence means the name is spent.
_TERMINAL_OUTPUTS = ("replay_outcomes.jsonl", "replay_report.json")


async def run_replay(dataset: ReplayDatasetConfig, execution: Dict[str, Any], logger, *,
                     execute: bool):
    """Preflight, and with `execute`, run the replay and write its outcomes and report.

    Without `execute` this selects, cuts and conditions every session, prices the run against
    its cap and checks the verification environment -- every refusal the real run would raise
    -- and writes nothing.
    """

    from ape.orchestration import TaskOrchestrator, execution_index
    from ape.tasks.base import create_task_from_data
    from src.mathlib_review.review.preflight import (
        assert_ready, assert_reviewed_workspaces_prebuilt, assert_workspaces_prebuilt,
    )
    from src.mathlib_review.review.runner import seal_or_revise_plan
    from src.mathlib_review.schema import ReviewEpisodeInput

    dataset.condition.assert_named_honestly()
    if dataset.run_name == "UNNAMED":
        raise ReplayRefused("a replay needs --run-name")
    for what, value in (("condition", dataset.condition.name), ("cut", dataset.cut.name)):
        if value not in dataset.run_name:
            raise ReplayRefused(
                f"run name {dataset.run_name!r} does not contain the {what} {value!r}; a "
                "replay's name is how its outcomes are told apart, and one task identity per "
                "session means one cut per run")

    sources, skipped = await select_sources(dataset)
    if not sources:
        raise ReplayRefused(f"nothing to replay in {dataset.of_run}; skipped: {skipped[:5]}")
    scaffold = replay_scaffold(sources, execution)
    out = run_dir(dataset.run_name)
    built = [replay_payload(source, dataset, out) for source in sources]
    plan = build_plan(dataset, scaffold, sources, skipped, built)
    logger.info("replay %s of %s: %d session(s) x %d sample(s), %d skipped; cut %s, "
                "condition %s (%s)", dataset.run_name, dataset.of_run, len(sources),
                plan.sample_count, len(skipped), plan.cut_label, dataset.condition.name,
                plan.condition_sha256[:12])
    logger.info("estimate: %s", json.dumps(plan.estimate))
    if plan.estimate["expected_billed_if_uncached"] > dataset.run_total_cost_cap:
        message = (f"the recorded decision stage priced uncached is "
                   f"${plan.estimate['expected_billed_if_uncached']:.2f} at "
                   f"{plan.sample_count} sample(s), above run_total_cost_cap "
                   f"${dataset.run_total_cost_cap:.2f}")
        if execute:
            raise ReplayRefused(message)
        logger.warning("%s; the real run will refuse", message)

    # Required, not configurable: submissions that compile in another environment than the
    # recorded run's are not a replay of its decisions.
    release = Path(json.loads((run_dir(dataset.of_run) / "run_plan.json").read_text())["release"])
    episode_ids = {payload["episode_id"] for payload, _ in built}
    episodes = [episode for episode in load_jsonl(release / "input/episodes.jsonl",
                                                  ReviewEpisodeInput)
                if episode.episode_id in episode_ids]
    assert_ready(scaffold, logger, enforce=execute)
    missing = await assert_reviewed_workspaces_prebuilt(episodes, required=execute, logger=logger)
    if not execute:
        logger.info("reviewed workspaces: %d of %d episode(s) prebuilt",
                    len(episodes) - len(missing), len(episodes))
        return plan
    await assert_workspaces_prebuilt([payload for payload, _ in built], required=True)

    existing = [name for name in _TERMINAL_OUTPUTS if (out / name).is_file()]
    if existing:
        raise ReplayRefused(f"run {dataset.run_name!r} already produced {existing}; a replay's "
                            "name is its resume key, so use a new one")
    for payload, content in built:
        write_once(Path(payload[SESSION_REPLAY_KEY]["prefix_path"]), content)
    seal_or_revise_plan(out, plan, logger)

    tasks = [create_task_from_data(payload, scaffold,
                                   task_config_overrides=scaffold.task_config_overrides)
             for payload, _ in built]
    orchestrator = TaskOrchestrator(config=scaffold, orchestrator_id=dataset.run_name,
                                    logger=logger)
    results = await orchestrator.run(tasks)
    index_path = out / execution_index.INDEX_FILENAME
    await execution_index.record(
        index_path, orchestrator, results, group="replay",
        semantic_ids={payload["task_id"]: payload["invocation_id"] for payload, _ in built})

    outcomes = await collect_outcomes(index_path, sources, built, dataset.condition.name,
                                      dataset.cut.name)
    write_once(out / "replay_outcomes.jsonl", jsonl_bytes(outcomes))
    report = replay_report(outcomes)
    write_once(out / "replay_report.json", pretty_json_bytes(report))
    logger.info("agreement with the recorded decision: %s",
                json.dumps(report["agreement_with_recorded"]))
    return out


async def collect_outcomes(index_path: Path, sources: List[ReplaySource], built,
                           condition: str, cut_label: str) -> List[Dict[str, Any]]:
    """One row per replayed sample, beside the recorded decision it replays."""

    from ape.orchestration.execution_index import by_semantic_id
    from ape.orchestration.persistence import TaskStorage
    from ape.scaffolds.ape_agent.conversation import ApeAgentConversationManager

    index = by_semantic_id(index_path)
    rows: List[Dict[str, Any]] = []
    for source, (payload, content) in zip(sources, built):
        start = len([line for line in content.split(b"\n") if line.strip()])
        recorded = {"decision": decision_record(source.nodes, source.cut_index),
                    "accepted": accepted_summary(source.result)}
        row = index.get(source.invocation_id)
        samples = (await TaskStorage(Path(row["task_dir"]), row["global_index"])
                   .load_all_samples()) if row else {}
        for sample_index in sorted(samples):
            attempt = samples[sample_index].successful_attempt or \
                samples[sample_index].current_attempt
            if attempt is None:
                continue
            result = attempt.result
            if hasattr(result, "model_dump"):
                result = result.model_dump(mode="json")
            session = ApeAgentConversationManager.find_latest_session_path(Path(attempt.path))
            drift_file = Path(attempt.path) / REPLAY_RECORD_FILENAME
            # The attempt's own proof that it started from the sealed prefix. Written by the
            # conversation manager when it is shown the recorded tools; absent means the
            # directive never arrived and the attempt ran the task from its prompt -- which
            # still submits, and would otherwise be read as replay consistency.
            record = json.loads(drift_file.read_text()) if drift_file.is_file() else {}
            from_prefix = (record.get("prefix_sha256")
                           == payload[SESSION_REPLAY_KEY]["prefix_sha256"])
            rows.append({
                "invocation_id": source.invocation_id,
                "arm_id": source.payload.get("arm_id"),
                "pr_number": source.payload.get("pr_number"),
                "work_unit_id": source.payload.get("work_unit_id"),
                "condition": condition,
                "cut": cut_label,
                "sample_index": sample_index,
                "status": getattr(attempt.status, "value", str(attempt.status)),
                "cost": attempt.cost,
                "cached_cost": attempt.cached_cost,
                "recorded": recorded,
                "replay": {
                    "replayed_from_prefix": from_prefix,
                    "decision": (decision_record(jsonl_rows(session), start)
                                 if session is not None and from_prefix else None),
                    "accepted": accepted_summary(result),
                    "tool_drift": record.get("tool_drift"),
                },
            })
    return rows


# --- reading it ----------------------------------------------------------------------------

#: How closely a replayed decision matches the recorded one, coarsest first. Every level
#: requires the same filed/abstained outcome; the finer two then compare the abstention reason
#: when both abstained, or the anchors (`primary_change_id`s) / candidate keys
#: (`primary_change_id|concern_family|issue_kind`) when both filed.
AGREEMENT_LEVELS = ("outcome", "reason_or_anchors", "reason_or_candidates")

READING = (
    "The null condition's agreement with the recorded decision is the noise floor: at "
    "temperature 1 a decision re-sampled from an identical prefix does not reproduce itself. "
    "A condition's effect is its paired difference from the null on the same sessions "
    "(`report replay --against <null run>`), not its agreement with the recording, and is "
    "provisional until it holds on all three source reps.")


def _agrees(recorded: Optional[Dict[str, Any]], replayed: Optional[Dict[str, Any]],
            level: str) -> Optional[bool]:
    if recorded is None or replayed is None:
        return None
    if recorded["filed"] != replayed["filed"]:
        return False
    if level == "outcome":
        return True
    if not recorded["filed"]:
        return recorded["abstention_reason"] == replayed["abstention_reason"]
    key = "anchors" if level == "reason_or_anchors" else "candidate_keys"
    return recorded[key] == replayed[key]


def _mean(values) -> Optional[float]:
    values = [float(value) for value in values]
    return round(sum(values) / len(values), 4) if values else None


def _session_key(row: Dict[str, Any]) -> str:
    """One replayed session: an invocation at one cut. Two cuts of one session are two
    measurements and must never be pooled into one rate."""

    return f"{row['invocation_id']}@{row.get('cut') or ''}"


def _by_session(rows) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(_session_key(row), []).append(row)
    return grouped


def replay_report(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """One replay run against the decisions it replayed.

    Refuses outright if any sample did not start from its prefix. Such a sample is a fresh run
    of the task: it submits, it looks like every other row, and pooling it into an agreement
    rate would report the variance of a whole re-run as the variance of a decision.
    """

    stray = [row["invocation_id"] for row in rows
             if not (row["replay"] or {}).get("replayed_from_prefix")]
    if stray:
        raise ReplayRefused(
            f"{len(stray)} of {len(rows)} sample(s) did not start from their recorded prefix "
            f"(e.g. {stray[:3]}); they are ordinary runs of the task and their agreement with "
            "the recorded decision would measure a re-run, not a decision")

    sessions = _by_session(rows)
    accepted = [row for row in rows if row["replay"]["accepted"] is not None]
    agreement = {}
    for level in AGREEMENT_LEVELS:
        per_session = {
            invocation_id: [_agrees(r["recorded"]["accepted"], r["replay"]["accepted"], level)
                            for r in items if r["replay"]["accepted"] is not None]
            for invocation_id, items in sessions.items()}
        per_session = {k: [v for v in votes if v is not None]
                       for k, votes in per_session.items()}
        votes = [vote for session_votes in per_session.values() for vote in session_votes]
        agreement[level] = {
            "rate": _mean(votes), "samples": len(votes),
            "sessions_every_sample_agrees": sum(1 for v in per_session.values() if v and all(v)),
            "sessions_no_sample_agrees": sum(1 for v in per_session.values()
                                             if v and not any(v)),
        }
    by_arm: Dict[str, Dict[str, Any]] = {}
    for arm_id in sorted({row["arm_id"] for row in rows}):
        arm_rows = [row for row in accepted if row["arm_id"] == arm_id]
        arm_sessions = {_session_key(row): row for row in rows if row["arm_id"] == arm_id}
        by_arm[arm_id] = {
            "sessions": len(arm_sessions),
            "recorded_filing_rate": _mean(
                (row["recorded"]["accepted"] or {}).get("filed", False)
                for row in arm_sessions.values()),
            "replayed_filing_rate": _mean(row["replay"]["accepted"]["filed"]
                                          for row in arm_rows),
            "outcome_agreement": _mean(
                vote for vote in (_agrees(r["recorded"]["accepted"], r["replay"]["accepted"],
                                          "outcome") for r in arm_rows) if vote is not None),
        }
    first_calls = [row["replay"]["decision"]["first"] for row in rows
                   if (row["replay"]["decision"] or {}).get("first")]
    confidences = [value for call in first_calls for value in call["model_confidence"]]
    statuses: Dict[str, int] = {}
    for row in rows:
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    return {
        "condition": rows[0]["condition"] if rows else None,
        "cuts": sorted({row.get("cut") for row in rows if row.get("cut")}),
        "sessions": len(sessions),
        "samples": len(rows),
        "samples_with_no_accepted_submission": len(rows) - len(accepted),
        "statuses": statuses,
        "agreement_with_recorded": agreement,
        "filing_rate": {
            "recorded": _mean((items[0]["recorded"]["accepted"] or {}).get("filed", False)
                              for items in sessions.values()),
            "replayed": _mean(row["replay"]["accepted"]["filed"] for row in accepted),
        },
        "refusals": {
            "recorded_sessions_with_a_refusal": sum(
                1 for items in sessions.values() if items[0]["recorded"]["decision"]["refusals"]),
            "replayed_samples_with_a_refusal": sum(
                1 for row in rows if (row["replay"]["decision"] or {}).get("refusals")),
        },
        "replayed_turns_max": max((row["replay"]["decision"] or {}).get("turns", 0)
                                  for row in rows) if rows else 0,
        "model_confidence_null_rate_first_call": _mean(value is None for value in confidences),
        "tool_drift": sorted({name for row in rows
                              for name in (row["replay"]["tool_drift"] or [])}),
        "cost": {"billed": round(sum(row["cached_cost"] or 0 for row in rows), 4),
                 "nominal": round(sum(row["cost"] or 0 for row in rows), 4)},
        "by_arm": by_arm,
        "reading": READING,
    }


def _sign_test(more: int, less: int) -> Optional[float]:
    """Two-sided exact sign test over sessions whose filing rate moved; ties are dropped."""

    from math import comb

    n = more + less
    if not n:
        return None
    tail = sum(comb(n, k) for k in range(min(more, less) + 1)) / 2 ** n
    return round(min(1.0, 2 * tail), 4)


def compare_replays(baseline: List[Dict[str, Any]],
                    treatment: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Two replay runs, paired session by session; normally a condition against the null.

    Per session, the filing rate over its accepted samples in each run; differences are read
    per session and never pooled, because samples of one prefix are not independent of it.

    Which axis moved decides how sessions pair, and the answer is stated rather than assumed.
    Two runs at the same cut pair on the invocation *and* that cut, so a condition is compared
    against a baseline that saw the same prefix. Two runs of the same condition at different
    cuts pair on the invocation alone, which asks the other question -- how much the cut
    itself decides. A run holding several cuts pairs on both and compares nothing across them.
    """

    def cuts(rows):
        return sorted({row.get("cut") for row in rows if row.get("cut")})

    base_cuts, treat_cuts = cuts(baseline), cuts(treatment)
    axis = ("cut" if len(base_cuts) == len(treat_cuts) == 1 and base_cuts != treat_cuts
            else "condition" if len(base_cuts) <= 1 and len(treat_cuts) <= 1 else "mixed")
    key = (lambda row: row["invocation_id"]) if axis == "cut" else _session_key

    def filing(rows):
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(key(row), []).append(row)
        return {session: _mean(r["replay"]["accepted"]["filed"] for r in items
                               if r["replay"]["accepted"] is not None)
                for session, items in grouped.items()}

    base, treat = filing(baseline), filing(treatment)
    paired = sorted(k for k in set(base) & set(treat)
                    if base[k] is not None and treat[k] is not None)
    differences = {k: treat[k] - base[k] for k in paired}
    more = sum(1 for d in differences.values() if d > 0)
    less = sum(1 for d in differences.values() if d < 0)
    arm_of = {key(row): row["arm_id"] for row in baseline + treatment}
    by_arm: Dict[str, Dict[str, Any]] = {}
    for arm_id in sorted({arm_of[k] for k in paired}):
        keys = [k for k in paired if arm_of[k] == arm_id]
        by_arm[arm_id] = {
            "sessions": len(keys),
            "baseline_filing_rate": _mean(base[k] for k in keys),
            "treatment_filing_rate": _mean(treat[k] for k in keys),
            "files_more": sum(1 for k in keys if differences[k] > 0),
            "files_less": sum(1 for k in keys if differences[k] < 0),
        }
    return {
        "baseline_condition": baseline[0]["condition"] if baseline else None,
        "treatment_condition": treatment[0]["condition"] if treatment else None,
        "baseline_cuts": base_cuts,
        "treatment_cuts": treat_cuts,
        "compared_axis": axis,
        "paired_sessions": len(paired),
        "unpaired_sessions": len(set(base) ^ set(treat)),
        "filing_rate": {"baseline": _mean(base[k] for k in paired),
                        "treatment": _mean(treat[k] for k in paired),
                        "mean_paired_difference": _mean(differences.values())},
        "sessions_treatment_files_more": more,
        "sessions_treatment_files_less": less,
        "sign_test_p": _sign_test(more, less),
        "agreement_with_recorded": {
            "baseline": replay_report(baseline)["agreement_with_recorded"],
            "treatment": replay_report(treatment)["agreement_with_recorded"]},
        "by_arm": by_arm,
        "reading": READING,
    }


def load_outcomes(run_name: str) -> List[Dict[str, Any]]:
    path = run_dir(run_name) / "replay_outcomes.jsonl"
    if not path.is_file():
        raise ReplayRefused(f"{path} does not exist; has `replay --run-name {run_name} "
                            "--execute` finished?")
    return jsonl_rows(path)
