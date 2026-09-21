"""Decision-turn replay of a review arm: the arm task itself, cut before it submits.

Built from real classes -- the arm task, its `submit_candidates` schema as the scaffold lists
it, sessions assembled with `ConversationSession` -- because a wrong replay is wrong silently:
it still produces a submission, and the submission would be read as a condition's effect.
The generic mechanics are pinned in `tests/ape/test_session_replay.py`.
"""

from __future__ import annotations

import asyncio

import pytest

from ape.llm_clients.config import LLMConfig
from ape.llm_clients.models import ContentBlock, ConversationSession
from ape.scaffolds.ape_agent.config import ApeAgentConfig
from ape.scaffolds.ape_agent.conversation import ApeAgentConversationManager
from ape.scaffolds.ape_agent.replay import (
    SESSION_REPLAY_KEY, CutPoint, ReplayCondition, ReplayRefused, SessionReplay, cut,
    load_prefix, recorded_tools, replay_task_data,
)
from ape.tasks.base import create_task_from_data
from ape.tasks.lean_tasks.formal_math.review.arm import (
    ARM_TASK_TYPE, ReviewArmData, ReviewArmTask,
)
from src.mathlib_review.review.replay import (
    SUBMIT_TOOL, accepted_summary, decision_record,
)

ARM_FIELDS = dict(
    task_id="t", invocation_id="wu:a#naming", arm_id="naming", spec_id="naming",
    work_unit_id="wu:a", episode_id="ep:1", pr_number=1, diff="d", changed_files=["A.lean"],
    change_ids=["change:a"], entity_ids_by_change={"change:a": []},
    primary_subjects_by_change={"change:a": "Foo.bar"}, paths_by_change={"change:a": "A.lean"},
    rendered_system_prompt="NAMING CONTRACT. Abstain when unsure.",
    rendered_user_prompt="Review Foo.bar.", rendered_prompt_sha256="a" * 64,
    target_workspace={"name": "target", "commit_hash": "c" * 40,
                      "repo_url": "https://e.invalid/m.git", "default_target": "Mathlib"},
)
CONFIG = ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2"))
#: The decision turn is one cut among many; the pipeline takes it from the run config.
DECISION_CUT = CutPoint(before_tool_call={"tool": SUBMIT_TOOL, "occurrence": "first"})


def _registered_tools(task):
    """What the scaffold sends: registered on fastmcp, listed by the conversation manager."""

    from fastmcp import Client, FastMCP

    async def listed():
        mcp = FastMCP("probe")
        await task.register_task_tools(mcp)
        async with Client(mcp) as client:
            return await ApeAgentConversationManager(ApeAgentConfig())._get_available_tools(
                client)

    return asyncio.run(listed())


@pytest.fixture(scope="module")
def payload():
    return ReviewArmData(**ARM_FIELDS).model_dump(mode="json")


@pytest.fixture(scope="module")
def tools(payload):
    return _registered_tools(create_task_from_data(payload, CONFIG))


def _call(session, call_id, name, arguments, result):
    session.add_assistant_message([ContentBlock.tool_use_block(call_id, name, arguments)],
                                  cwd="/w")
    session.add_tool_result(call_id, result, cwd="/w", tool_name=name)


def _session(tools):
    """Investigate, submit a mute abstention (refused), resubmit it labelled -- the shape of
    26 of 321 arm sessions on the v2 held-out rep."""

    session = ConversationSession()
    session.add_system_message([ContentBlock.text_block(ARM_FIELDS["rendered_system_prompt"])],
                               cwd="/w")
    session.add_tool_definitions(tools, cwd="/w")
    session.add_user_message([ContentBlock.text_block("Review Foo.bar.")], cwd="/w")
    _call(session, "c1", "lean_verify_edit", {"path": "A.lean"}, {"success": True})
    _call(session, "c2", SUBMIT_TOOL, {"candidates": []},
          {"evaluation_result": {"success": False, "message": "Only the label is missing."}})
    _call(session, "c3", SUBMIT_TOOL,
          {"abstention_reason": "already_correct", "candidates": [],
           "abstention_detail": "Foo.bar matches the prefix."},
          {"evaluation_result": {"success": True, "message": "Recorded 0 candidates"}})
    return [node.model_dump(mode="json") for node in session.nodes]


def test_the_cut_a_run_asks_for_is_where_the_replay_starts(tools):
    nodes = _session(tools)
    prefix, index = cut(nodes, DECISION_CUT)
    assert index == 5 and prefix[-1]["type"] == "user"
    record = decision_record(nodes, index)
    assert (record["turns"], record["submissions"]) == (2, 2)
    assert record["refusals"] == ["Only the label is missing."]
    assert record["first"]["filed"] is False and record["first"]["abstention_reason"] is None


def test_a_replay_is_the_arm_task_not_a_new_task_type(tools, payload, tmp_path):
    """Its results are ordinary arm results, so finalize and the judge read them unchanged."""

    prefix, _ = cut(_session(tools), DECISION_CUT)
    replayed, content = replay_task_data(payload, prefix, ReplayCondition(name="null"),
                                         tmp_path / "p.jsonl", {"run": "r"})
    task = create_task_from_data(replayed, CONFIG)
    assert type(task) is ReviewArmTask and task.data.task_type == ARM_TASK_TYPE
    assert task.data.task_id == payload["task_id"]
    # `session_replay` is not a task field: the runtime attaches it.
    assert not hasattr(task.data, SESSION_REPLAY_KEY)


def test_reason_before_verdict_on_the_real_candidate_schema(tools, payload, tmp_path):
    """fastmcp inlines `$defs`, so one candidate's schema is at `properties/candidates/items`."""

    prefix, _ = cut(_session(tools), DECISION_CUT)
    condition = ReplayCondition(name="claim_first", tool_schema_edits=[
        {"tool": SUBMIT_TOOL, "property_order": ["abstention_detail", "abstention_reason"]},
        {"tool": SUBMIT_TOOL, "at": "properties/candidates/items",
         "property_order": ["claim", "requested_change"]},
    ])
    replayed, content = replay_task_data(payload, prefix, condition, tmp_path / "p.jsonl", {})
    (tmp_path / "p.jsonl").write_bytes(content)
    replay = SessionReplay.model_validate(replayed[SESSION_REPLAY_KEY])
    shown = {t["function"]["name"]: t["function"]["parameters"]
             for t in recorded_tools(load_prefix(replay))}[SUBMIT_TOOL]
    assert list(shown["properties"]) == ["abstention_detail", "abstention_reason", "candidates"]
    assert list(shown["properties"]["candidates"]["items"]["properties"])[:2] == [
        "claim", "requested_change"]

    # And the replayed arm task, run by the manager, is shown exactly that -- no drift today.
    task = create_task_from_data(replayed, CONFIG)
    task.session_replay = replay
    task.attempt_path = tmp_path
    manager = ApeAgentConversationManager(CONFIG, task=task)
    sent = manager._replay_tool_definitions(_registered_tools(task))
    assert {t["function"]["name"]: t["function"]["parameters"] for t in sent}[SUBMIT_TOOL] == shown
    assert '"tool_drift": []' in (tmp_path / "session_replay.json").read_text()


def test_the_accepted_submission_is_read_off_the_result():
    """The detail travels with the reason. The reason alone is not evidence about a silence:
    17 of the 45 gold-site sessions replayed on 2026-09-21 produced a different one with the
    outcome unchanged, so a diagnosis built on it is a coin flip."""

    assert accepted_summary({"success": True, "candidates": [],
                             "abstention": {"reason": "already_correct",
                                            "detail": "checked all five; they match"}}) == {
        "filed": False, "abstention_reason": "already_correct",
        "abstention_detail": "checked all five; they match", "anchors": [],
        "candidate_keys": [], "model_confidence": []}
    # A filed submission has no abstention of either kind.
    assert accepted_summary({"success": True, "candidates": [],
                             "abstention": {"reason": "already_correct"}})[
        "abstention_detail"] is None
    filed = accepted_summary({"success": True, "candidates": [
        {"primary_change_id": "change:a", "concern_family": "naming",
         "issue_kind": "naming_convention_violation", "model_confidence": None}]})
    assert filed["anchors"] == ["change:a"] and filed["model_confidence"] == [None]
    assert accepted_summary({"success": False}) is None


# --- the pipeline, on a run tree built from the orchestrator's own classes -------------------


def _write_arm_task(run, tasks_root, invocation_id, nodes, result, config):
    """One arm task as a lead's nested orchestrator leaves it: sample, attempt, session."""

    import json
    from datetime import datetime
    from pathlib import Path

    from ape.orchestration.models import Attempt, ExecutionStatus, Sample, make_sample_id
    from ape.orchestration.persistence import TaskStorage

    global_index = str(abs(hash(invocation_id)))
    task_dir = tasks_root / global_index
    attempt_path = task_dir / "samples/0/attempts/attempt_1"
    attempt_path.mkdir(parents=True)
    (attempt_path / "ape_agent_session_20260913_000000__s.jsonl").write_text(
        "".join(json.dumps(node) + "\n" for node in nodes))
    now = datetime.now()
    sample = Sample(
        sample_id=make_sample_id(global_index, 0), sample_index=0,
        task_global_index=global_index, created_at=now, updated_at=now,
        attempts=[Attempt(attempt_id=1, path=attempt_path, status=ExecutionStatus.SUCCESS,
                          created_at=now, max_turns=40, cost_limit=0.3, result=result)])
    asyncio.run(TaskStorage(task_dir, global_index).save_sample(sample))
    (tasks_root.parent / "config.json").write_text(json.dumps({"config": config}))
    with (run / "execution_index.jsonl").open("a") as handle:
        handle.write(json.dumps({"semantic_id": invocation_id, "task_type": ARM_TASK_TYPE,
                                 "global_index": global_index, "task_dir": str(task_dir),
                                 "attempts": []}) + "\n")


@pytest.fixture
def recorded_run(tmp_path, monkeypatch, tools, payload):
    """A run with three arm sessions: two that submitted, one that never did."""

    import json

    import src.mathlib_review.review.replay as replay_module

    runs = tmp_path / "runs"
    monkeypatch.setattr(replay_module, "run_dir", lambda name: runs / name)
    run = runs / "source"
    run.mkdir(parents=True)
    config = CONFIG.model_dump(mode="json")
    accepted = {"success": True, "candidates": [], "abstention": {"reason": "already_correct"}}
    pool = []
    decided = []
    for _ in range(2):
        nodes = _session(tools)
        nodes[5]["message"]["usage"] = {"total_cost": 0.032, "cached_total_cost": 0.0095}
        decided.append(nodes)
    for arm, nodes in (("naming", decided[0]), ("docs", decided[1]),
                       ("style", _session(tools)[:5])):
        invocation_id = f"wu:a#{arm}"
        _write_arm_task(run, tmp_path / "nested" / arm / "tasks", invocation_id, nodes,
                        accepted, config)
        pool.append({"invocation_id": invocation_id, "task_data": {
            **payload, "invocation_id": invocation_id, "arm_id": arm}})
    (run / "arm_pool.jsonl").write_text("".join(json.dumps(row) + "\n" for row in pool))
    return runs


def _dataset(**fields):
    from src.mathlib_review.review.replay import ReplayDatasetConfig

    return ReplayDatasetConfig.model_validate({
        "of_run": "source", "run_name": "replay_null_first_submit_candidates",
        "condition": {"name": "null"}, "run_total_cost_cap": 10.0,
        "cut": {"before_tool_call": {"tool": SUBMIT_TOOL}}, **fields})


def test_sessions_are_found_through_the_index_and_storage(recorded_run):
    from src.mathlib_review.review.replay import select_sources

    sources, skipped = asyncio.run(select_sources(_dataset()))
    assert [s.invocation_id for s in sources] == ["wu:a#docs", "wu:a#naming"]
    assert skipped == [{"invocation_id": "wu:a#style",
                        "reason": "the session never called submit_candidates"}]
    assert [s.cut_index for s in sources] == [5, 5]
    only, _ = asyncio.run(select_sources(_dataset(arm_ids=["naming"])))
    assert [s.invocation_id for s in only] == ["wu:a#naming"]


def test_another_cut_of_the_same_sessions_replays_more_of_each(recorded_run):
    """The point of a configurable cut: the same recordings, taken over earlier. `before_turn:
    1` re-runs the whole task from its recorded prompt, so the re-sampled stage is the whole
    session and the turn cap is counted from a prefix with no assistant turns in it."""

    from ape.orchestration.models import EXECUTION_LIMITS_KEY
    from src.mathlib_review.review.replay import replay_payload, select_sources

    dataset = _dataset(cut={"before_turn": 1}, run_name="replay_null_turn1",
                       turns_after_cut=12)
    sources, skipped = asyncio.run(select_sources(dataset))
    # Three, not two: the session that never submitted is replayable from its prompt, so a
    # cut decides which recordings are even eligible.
    assert [s.cut_index for s in sources] == [3, 3, 3]
    assert skipped == []
    built, _ = replay_payload(sources[0], dataset, recorded_run / "replay_null_turn1")
    assert built[EXECUTION_LIMITS_KEY]["max_turns"] == 0 + 12
    assert built[SESSION_REPLAY_KEY]["source"]["cut_label"] == "turn1"
    assert sources[0].replayed_stage_cost() == (0.0095, 0.032)   # every recorded turn


def test_a_cut_that_does_not_resolve_skips_that_session_only(recorded_run):
    from src.mathlib_review.review.replay import select_sources

    sources, skipped = asyncio.run(select_sources(
        _dataset(cut={"before_turn": 9}, run_name="replay_null_turn9")))
    assert sources == []
    assert {row["invocation_id"] for row in skipped} == {
        "wu:a#naming", "wu:a#docs", "wu:a#style"}
    assert all("assistant turn" in row["reason"] for row in skipped)


def test_a_missing_arm_pool_is_refused_with_the_reason(recorded_run):
    from src.mathlib_review.review.replay import select_sources

    (recorded_run / "source/arm_pool.jsonl").unlink()
    with pytest.raises(ReplayRefused, match="gitignored"):
        asyncio.run(select_sources(_dataset()))


def test_a_replay_payload_is_capped_from_the_cut_and_writes_its_own_trace(recorded_run):
    from ape.orchestration.models import EXECUTION_LIMITS_KEY
    from src.mathlib_review.review.replay import replay_payload, select_sources

    sources, _ = asyncio.run(select_sources(_dataset()))
    out = recorded_run / "replay_null"
    built, content = replay_payload(sources[0], _dataset(turns_after_cut=3), out)
    assert built[EXECUTION_LIMITS_KEY] == {"max_turns": 1 + 3, "billed_cost_limit": 0.3}
    assert built["trace_path"] == str(out / "context_trace.jsonl")
    assert built[SESSION_REPLAY_KEY]["prefix_path"].startswith(str(out / "prefixes"))
    assert built[SESSION_REPLAY_KEY]["source"]["cut_node_index"] == 5
    assert built[SESSION_REPLAY_KEY]["source"]["cut_label"] == "first_submit_candidates"
    assert sources[0].replayed_stage_cost() == (0.0095, 0.032)
    assert built["task_type"] == ARM_TASK_TYPE


def test_sessions_under_different_models_are_not_replayed_together(recorded_run):
    from src.mathlib_review.review.replay import replay_scaffold, select_sources

    sources, _ = asyncio.run(select_sources(_dataset()))
    scaffold = replay_scaffold(sources, {"sample_count": 3})
    assert scaffold.execution.sample_count == 3
    assert scaffold.llm_config.model_name == "gpt_5.2"
    sources[1].scaffold_config["llm_config"]["temperature"] = 0.0
    with pytest.raises(ReplayRefused, match="different model"):
        replay_scaffold(sources, {})


def test_a_replay_config_cannot_change_the_model(tmp_path):
    from src.mathlib_review.review.replay import load_replay

    path = tmp_path / "r.yaml"
    path.write_text('llm_config: {model_name: other}\ndataset: {of_run: s, '
                    'condition: {name: "null"}, run_total_cost_cap: 1, '
                    'cut: {before_turn: -1}}\n')
    with pytest.raises(ReplayRefused, match="only `dataset` and `execution`"):
        load_replay(path)


def test_the_checked_in_config_loads_with_a_null_condition():
    """Bare `null` in YAML is None; the config quotes it."""

    from pathlib import Path

    from src.mathlib_review.review.replay import load_replay

    dataset, execution = load_replay(Path("configs/v5_replay.yaml"),
                                     {"dataset": {"of_run": "x"}})
    assert dataset.condition.name == "null" and dataset.condition.changes_nothing
    assert execution["sample_count"] == 3


@pytest.mark.parametrize("fields, match", [
    ({"run_name": "replay_other_first_submit_candidates"}, "does not contain the condition"),
    ({"run_name": "replay_null"}, "does not contain the cut"),
    ({"run_total_cost_cap": 0.0001}, "above run_total_cost_cap"),
])
def test_a_replay_is_refused_before_anything_is_written(recorded_run, fields, match):
    import logging

    from src.mathlib_review.review.replay import run_replay

    with pytest.raises((ReplayRefused, ValueError), match=match):
        asyncio.run(run_replay(_dataset(**fields), {}, logging.getLogger("t"), execute=True))
    assert not (recorded_run / "replay_null_first_submit_candidates").exists()


def _row(invocation_id, arm, recorded_filed, replay_filed, condition="null", sample=0,
         cut="first_submit_candidates"):
    def summary(filed):
        if filed is None:
            return None
        return {"filed": filed, "abstention_reason": None if filed else "already_correct",
                "anchors": ["change:a"] if filed else [],
                "candidate_keys": ["change:a|naming|None"] if filed else [],
                "model_confidence": [None] if filed else []}

    return {"invocation_id": invocation_id, "arm_id": arm, "condition": condition,
            "cut": cut, "sample_index": sample, "status": "success", "cost": 0.03, "cached_cost": 0.01,
            "recorded": {"decision": {"refusals": []}, "accepted": summary(recorded_filed)},
            "replay": {"replayed_from_prefix": True,
                       "decision": {"turns": 1, "refusals": [],
                                    "first": {"model_confidence": [None] if replay_filed else []}},
                       "accepted": summary(replay_filed), "tool_drift": []}}


def test_the_report_reads_agreement_per_session_not_pooled():
    from src.mathlib_review.review.replay import replay_report

    rows = [_row("s1", "naming", False, False, sample=0), _row("s1", "naming", False, True, sample=1),
            _row("s2", "docs", True, True, sample=0), _row("s2", "docs", True, None, sample=1)]
    report = replay_report(rows)
    outcome = report["agreement_with_recorded"]["outcome"]
    assert (outcome["samples"], outcome["rate"]) == (3, round(2 / 3, 4))
    assert outcome["sessions_every_sample_agrees"] == 1
    assert report["samples_with_no_accepted_submission"] == 1
    assert report["filing_rate"] == {"recorded": 0.5, "replayed": round(2 / 3, 4)}
    assert report["by_arm"]["naming"]["replayed_filing_rate"] == 0.5


def test_a_replayed_decision_records_the_sentence_as_well_as_the_label():
    """What the condition experiments will be read from.

    The decision record is the only place a replayed arm's own words are kept in the results
    tree -- the session files live in whichever worktree ran the replay, and the first
    diagnostic's texts were only reachable there. Since the label swaps under re-sampling on
    better than a third of sessions, a run that kept the label and dropped the sentence
    recorded the unreliable half.
    """

    from src.mathlib_review.review.replay import submission_summary

    silent = submission_summary({
        "candidates": [],
        "abstention_reason": "below_my_bar",
        "abstention_detail": "`toLinearMap_` leads 21 to 7 but is not established.",
    })
    assert silent["abstention_reason"] == "below_my_bar"
    assert silent["abstention_detail"] == "`toLinearMap_` leads 21 to 7 but is not established."

    # A filed submission carries neither, and an empty detail is None rather than "".
    filed = submission_summary({"candidates": [{"primary_change_id": "change:a"}],
                                "abstention_detail": "ignored when candidates are present"})
    assert filed["abstention_reason"] is None and filed["abstention_detail"] is None
    assert submission_summary({"candidates": [], "abstention_detail": ""})[
        "abstention_detail"] is None


def test_a_condition_is_read_against_the_null_paired_by_session():
    from src.mathlib_review.review.replay import compare_replays

    null = [_row(f"s{i}", "naming", False, False) for i in range(10)]
    treated = [_row(f"s{i}", "naming", False, i < 9, condition="file_more") for i in range(10)]
    comparison = compare_replays(null, treated)
    assert comparison["paired_sessions"] == 10
    assert (comparison["sessions_treatment_files_more"],
            comparison["sessions_treatment_files_less"]) == (9, 0)
    assert comparison["filing_rate"]["mean_paired_difference"] == 0.9
    assert comparison["sign_test_p"] == 0.0039


def test_two_cuts_of_one_session_are_two_measurements(tools):
    from src.mathlib_review.review.replay import compare_replays, replay_report

    rows = [_row("s1", "naming", False, False, cut="first_submit_candidates"),
            _row("s1", "naming", False, True, cut="turn1")]
    report = replay_report(rows)
    assert report["cuts"] == ["first_submit_candidates", "turn1"]
    assert report["sessions"] == 2            # one invocation, two cuts, never pooled
    # Two runs of one condition at different cuts ask how much the cut decides, so they pair
    # on the invocation; two runs at the same cut pair on the prefix and compare conditions.
    early = [_row("s1", "naming", False, False, cut="turn1")]
    late = [_row("s1", "naming", False, True, cut="first_submit_candidates")]
    across = compare_replays(early, late)
    assert across["compared_axis"] == "cut" and across["paired_sessions"] == 1
    same = compare_replays(early, [_row("s1", "naming", False, True, condition="forced",
                                        cut="turn1")])
    assert same["compared_axis"] == "condition" and same["paired_sessions"] == 1


def test_named_sessions_are_replayed_and_a_mistyped_name_is_refused(recorded_run):
    """A case study names its sessions. A typo must not quietly shrink the run to the rest."""

    from src.mathlib_review.review.replay import select_sources

    sources, _ = asyncio.run(select_sources(_dataset(invocation_ids=["wu:a#naming"])))
    assert [s.invocation_id for s in sources] == ["wu:a#naming"]
    with pytest.raises(ReplayRefused, match="holds no arm session"):
        asyncio.run(select_sources(_dataset(invocation_ids=["wu:a#naming", "wu:a#typo"])))


def test_a_sample_that_did_not_start_from_its_prefix_refuses_the_report():
    """It ran the task from its prompt, submitted, and looks like every other row. Pooling it
    would report the variance of a whole re-run as the variance of a decision -- which is what
    happened on the first real replay, before the orchestrator carried the directive."""

    from src.mathlib_review.review.replay import replay_report

    rows = [_row("s1", "naming", False, False), _row("s2", "docs", True, True)]
    rows[1]["replay"]["replayed_from_prefix"] = False
    with pytest.raises(ReplayRefused, match="did not start from their recorded prefix"):
        replay_report(rows)


def test_a_paused_sample_is_reported_and_does_not_hide_its_siblings(recorded_run, tmp_path):
    """A task with any paused sample returns no result, so the execution index never names it.
    Reading outcomes through the index lost two whole sessions of a real run -- their successful
    samples included -- and the run still reported a clean agreement rate."""

    import json
    from datetime import datetime
    from pathlib import Path

    from ape.orchestration.models import Attempt, ExecutionStatus, Sample, make_sample_id
    from ape.orchestration.persistence import TaskStorage
    from src.mathlib_review.review.replay import collect_outcomes, replay_payload, select_sources

    dataset = _dataset(invocation_ids=["wu:a#naming"])
    sources, _ = asyncio.run(select_sources(dataset))
    out = recorded_run / "replay_null_first_submit_candidates"
    payload, content = replay_payload(sources[0], dataset, out)
    Path(payload[SESSION_REPLAY_KEY]["prefix_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(payload[SESSION_REPLAY_KEY]["prefix_path"]).write_bytes(content)

    task_dir = tmp_path / "gi"
    now = datetime.now()
    for index, status in ((0, ExecutionStatus.SUCCESS), (1, ExecutionStatus.PAUSED_MAX_TURNS)):
        attempt_path = task_dir / f"samples/{index}/attempts/attempt_1"
        attempt_path.mkdir(parents=True)
        (attempt_path / "session_replay.json").write_text(json.dumps(
            {"prefix_sha256": payload[SESSION_REPLAY_KEY]["prefix_sha256"], "tool_drift": []}))
        (attempt_path / "ape_agent_session_20260921_000000__s.jsonl").write_bytes(content)
        asyncio.run(TaskStorage(task_dir, "gi").save_sample(Sample(
            sample_id=make_sample_id("gi", index), sample_index=index, task_global_index="gi",
            created_at=now, updated_at=now,
            attempts=[Attempt(attempt_id=1, path=attempt_path, status=status, created_at=now,
                              max_turns=9, cost_limit=0.3,
                              result={"success": True, "candidates": [], "task_id": "t",
                                      "task_type": ARM_TASK_TYPE,
                                      "abstention": {"reason": "already_correct"}}
                              if status is ExecutionStatus.SUCCESS else None)])))

    rows = asyncio.run(collect_outcomes({"wu:a#naming": task_dir}, sources,
                                        [(payload, content)], "null", "first_submit_candidates"))
    assert len(rows) == 2                                   # both samples, not just the good one
    assert [r["status"] for r in rows] == ["success", "paused_max_turns"]
    assert rows[0]["replay"]["accepted"]["abstention_reason"] == "already_correct"
    assert rows[1]["replay"]["accepted"] is None            # it never submitted legally
    assert all(r["replay"]["replayed_from_prefix"] for r in rows)


def test_a_replay_leaves_its_row_in_the_source_runs_ledger(tmp_path):
    """Where the judge's row goes, for the same reason: "these sessions were re-decided, under
    this condition, at this cut" is a fact about the run that recorded them.

    A replay makes no transition -- the source run is exactly as generated and as judged as it
    was -- so `transition` is None, which is a legitimate row rather than a missing one."""

    from types import SimpleNamespace

    from src.mathlib_review.review import replay as replay_module
    from src.mathlib_review.run_state import RunState, ledger

    source = tmp_path / "source"
    source.mkdir()
    out = tmp_path / "replay_null_first_submit_candidates"
    out.mkdir()
    (out / "replay_report.json").write_bytes(b"{}")

    stage = SimpleNamespace(run_dir=source, run_name="source", consumed={"arm_pool": "a" * 64},
                            state=RunState.FINALIZED, forensic=False)
    plan = SimpleNamespace(condition_sha256="c" * 64, cut_label="first_submit_candidates",
                           sample_count=3, model_name="gpt_5.2",
                           prefix_sha256_by_invocation={"wu:a#naming": "p" * 64})
    dataset = SimpleNamespace(run_name="replay_null_first_submit_candidates",
                              condition=SimpleNamespace(name="null"))

    replay_module._record_stage(dataset, stage, plan, out,
                                SimpleNamespace(warning=lambda *a, **k: None))
    row = ledger(source)[0]
    assert row["stage"] == "replay" and row["run_name"] == "source"
    assert row["transition"] is None
    assert row["identity"]["cut"] == "first_submit_candidates"
    assert row["identity"]["condition"] == "null"
    assert row["produced"]["run"] == "replay_null_first_submit_candidates"


def test_the_replay_takes_the_release_from_the_run_it_replays():
    """From the source run's own sealed agenda, for the reason `judge --of` derives its paths:
    the config that produced a run is not recoverable from the run, and the agenda is. Verified
    equal to `run_plan.json`'s copy on all 59 committed runs that carry both."""

    import inspect

    from src.mathlib_review.review import replay as replay_module

    source = inspect.getsource(replay_module.run_replay)
    assert "release = stage.release" in source
    assert '"run_plan.json"' not in source


# --- named selectors ------------------------------------------------------------------------


from pathlib import Path


RUN = "pr5_A_lead_heldout12_v2_rep1"
_has_run = pytest.mark.skipif(
    not Path(f"results/pr_review_v5/runs/{RUN}/findings.jsonl").is_file(),
    reason="the held-out reps are not in this tree")


def _selector_dataset(**fields):
    from types import SimpleNamespace

    base = dict(of_run=RUN, selector="all", arm_ids=[], invocation_ids=[])
    base.update(fields)
    return SimpleNamespace(**base)


def test_a_selector_that_needs_arguments_refuses_rather_than_meaning_everything():
    """`--select arm` with no arms is `all` under a name that says otherwise, and a replay of
    "named sessions" that names none is a replay of everything with the fact hidden."""

    from src.mathlib_review.review.replay import select_invocations

    for selector in ("arm", "invocation_ids"):
        with pytest.raises(ReplayRefused, match="needs"):
            select_invocations(_selector_dataset(selector=selector))


def test_an_explicit_list_restricts_whatever_the_selector_says():
    """Naming sessions is how a case study runs; a selector narrows that rather than widening
    it."""

    from src.mathlib_review.review.replay import select_invocations

    ids, provenance = select_invocations(
        _selector_dataset(invocation_ids=["wu:a#naming"]))
    assert ids == {"wu:a#naming"} and provenance["gold_derived"] is False


@_has_run
def test_the_gold_derived_selectors_name_what_a_scratch_join_used_to():
    """Choosing the sessions for the first planned diagnostic took an ad-hoc join across four
    files, written in a scratchpad and thrown away -- and it is not reproducible: it selected 45
    where this selects 58, because it filtered on required gold changes rather than on gold
    sites. That is the argument for naming one, not against."""

    from src.mathlib_review.review.replay import select_invocations

    silent, provenance = select_invocations(
        _selector_dataset(selector="gold-site-abstentions"))
    assert len(silent) == 58
    assert provenance["gold_derived"] is True and len(provenance["obligation_ids"]) == 22

    # Narrowed by arm, which is what a single-arm case study wants.
    naming, _ = select_invocations(
        _selector_dataset(selector="gold-site-abstentions", arm_ids=["naming"]))
    assert len(naming) == 11 and naming < silent

    missed, provenance = select_invocations(_selector_dataset(selector="missed-obligations"))
    assert len(missed) == 142
    # Only the obligations the judge did not score as hits: 22 counted, 7 covered.
    assert len(provenance["obligation_ids"]) == 15


@_has_run
@_has_run
def test_the_control_selector_is_the_guard_every_replay_so_far_lacked():
    """A condition that turns silences into asks is an improvement only if it leaves alone the
    PRs where maintainers wanted nothing. No replay could measure that: the diagnostic's 45
    sessions and the named gold-site selector both draw only from PRs that carry gold, so the
    precision side was unobservable at any price.

    Which PRs are controls comes from the release -- a PR it records no `proposed_atomic`
    obligation for -- and not from a config list, because a list could name a control gold
    disagrees about and the resulting number would be a fiction.
    """

    from src.mathlib_review.review.replay import select_invocations

    controls, provenance = select_invocations(_selector_dataset(selector="control-abstentions"))
    assert provenance["control_pr_numbers"] == [33304, 33315]
    assert provenance["gold_derived"] is True
    assert len(controls) == 7
    assert all(invocation.split("#")[-1] != "generalist" for invocation in controls)

    # Disjoint from the gold-site population by construction: that is what makes it a control.
    gold_site, _ = select_invocations(_selector_dataset(selector="gold-site-abstentions"))
    assert not (controls & gold_site)

    # And narrowable by arm like the others.
    docs, _ = select_invocations(
        _selector_dataset(selector="control-abstentions", arm_ids=["docs"]))
    assert docs < controls and len(docs) == 5


def test_a_set_with_no_control_pr_is_refused_rather_than_measured_without_one(
        tmp_path, monkeypatch):
    """Two of this project's PR sets have no control -- both controls are larger than every PR
    in them -- and a condition run there has no precision guard at all. Saying so is the
    selector's job; returning nothing would read as "no silences to fix".

    Built as a real run directory rather than a stand-in: a fake `StageInput` would be free to
    disagree with the class, which is how a fixture here once passed while the code it stood
    for was broken.
    """

    import json as json_module

    import src.mathlib_review.review.replay as replay_module
    from src.mathlib_review.io import append_jsonl, pretty_json_bytes
    from src.mathlib_review.review.replay import select_invocations
    from src.mathlib_review.schema.review import ArmResponse

    release = tmp_path / "release"
    (release / "gold").mkdir(parents=True)
    (release / "gold" / "judgments.jsonl").write_text(json_module.dumps({
        "pr_number": 33057, "obligations": [
            {"obligation_id": "obligation:a", "status": "proposed_atomic",
             "change_ids": ["change:a"], "claim": "fix the last error"}]}) + "\n")

    directory = tmp_path / "runs" / "every_pr_has_gold"
    directory.mkdir(parents=True)
    (directory / "agenda.json").write_bytes(pretty_json_bytes({
        "release": str(release), "proposals": [{"pr_number": 33057}]}))
    append_jsonl(directory / "arm_responses.jsonl", ArmResponse(
        invocation_id="wu:a#docs", arm_id="docs", work_unit_id="wu:a", spec_id="docs",
        pr_number=33057, status="success", candidates=[],
        abstention={"reason": "already_correct", "detail": "checked"}))

    monkeypatch.setattr(replay_module, "run_dir", lambda _name: directory)
    with pytest.raises(ReplayRefused, match="no control PR"):
        select_invocations(
            _selector_dataset(selector="control-abstentions", of_run="every_pr_has_gold"))


def test_missed_obligations_refuses_without_the_judges_verdicts(monkeypatch):
    """Which obligations were missed is not knowable without them, and guessing would make the
    selection a fiction."""

    from src.mathlib_review.analysis import report as report_module
    from src.mathlib_review.review.replay import select_invocations

    def no_audit(*args, **kwargs):
        raise FileNotFoundError("semantic_report.json does not exist")

    monkeypatch.setattr(report_module, "buckets", no_audit)
    with pytest.raises(ReplayRefused, match="Judge the run first"):
        select_invocations(_selector_dataset(selector="missed-obligations"))


def test_the_selection_is_sealed_into_the_plan_and_is_not_resumable():
    """A selector changed under one run name would make two different experiments share an
    identity. `selection` is outside `RESUMABLE_PLAN_FIELDS`, so the second is refused."""

    import inspect

    from src.mathlib_review.review import replay as replay_module
    from src.mathlib_review.review.runner import RESUMABLE_PLAN_FIELDS

    assert "selection" not in RESUMABLE_PLAN_FIELDS
    source = inspect.getsource(replay_module.build_plan)
    assert "select_invocations(dataset)[1]" in source
    assert "resolved_invocation_ids" in source
