"""Sessions over folders as tasks, and the reconstruction consumer walked through the shared records.

Slice B of the task/data refactor. The spike found the one recurring mechanic still bespoke after
the evaluation and context slices: hand-launched sessions over prepared folders, read back by path,
with only the inputs' digests kept. These tests drive the real `packet_session` task with no model
-- real setup, outputs written into the real folder, the real `submit_outputs` -- and then walk the
evidence-assisted consumer (the reconstruction probe's extractor -> context section -> reviewer)
through the shared records: session outputs with digests, a context file sealed by content (slice
A2), and a reviewer prompt that carries it. Replacing the acquisition is a different plan; nothing
downstream changes.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from ape.scaffolds.ape_agent.config import ApeAgentConfig
from ape.tasks.base import create_task_from_data
from ape.tasks.packet_session import PacketSessionTask
from src.mathlib_review.analysis import sessions as S

#: The reconstruction probe's extractor session prompt, in its convention ({dir}).
EXTRACTOR_BRIEF = """You are preparing inputs for a research study of code review on Mathlib (Lean 4) pull requests.

Your working folder is:
{dir}

Rules:
- Read `instructions.md` in that folder first and follow it exactly.
- Read only files inside that folder.
- Write `goal_brief.md` and `ledger.json` in the working folder."""
OUTPUTS = [{"name": "goal_brief.md", "kind": "text"}, {"name": "ledger.json", "kind": "json"}]


def _packets(root: Path) -> Path:
    """Two folders shaped like `make_packets.py extract` writes them."""
    for pr in (33066, 33117):
        d = root / f"pr{pr}"
        (d / "base" / "Mathlib").mkdir(parents=True)
        (d / "instructions.md").write_text("Extract the design decisions.\n")
        (d / "pr.md").write_text(f"# PR {pr}\n")
        (d / "model.md").write_text("model\n")
        (d / "diff.patch").write_text("--- a\n+++ b\n")
        (d / "base" / "Mathlib" / "X.lean").write_text("theorem x : True := trivial\n")
        (d / "tmp").mkdir()
        (d / "tmp" / "scratch.txt").write_text("not part of the packet")
    return root


class _MCP:
    def __init__(self):
        self.tools = {}

    def tool(self, description=""):
        def register(fn):
            self.tools[fn.__name__] = fn
            return fn
        return register


async def _work_a_session(task, attempt: Path, goal: str):
    """What a session does, without a model: set up, write the outputs, hand them in."""
    submitted = []

    async def callback(result):
        submitted.append(result)

    await task.setup(callback, "test", attempt_path=attempt)
    mcp = _MCP()
    await task.register_task_tools(mcp)
    refused = await mcp.tools["submit_outputs"]()
    assert refused["accepted"] is False and len(refused["problems"]) == 2
    (task.packet_dir / "goal_brief.md").write_text(goal)
    (task.packet_dir / "ledger.json").write_text(json.dumps([{"decision": "name"}]))
    accepted = await mcp.tools["submit_outputs"]()
    assert accepted["accepted"] is True
    return submitted[0]


def test_a_packet_session_lays_its_folder_out_and_hands_in_declared_outputs(tmp_path):
    payload = S.session_payloads(S.plan_sessions(
        _packets(tmp_path / "packets"), name="x", brief=EXTRACTOR_BRIEF, outputs=OUTPUTS,
        out_dir=tmp_path / "plan"))[0]
    task = create_task_from_data(payload, ApeAgentConfig())
    result = asyncio.run(_work_a_session(task, tmp_path / "attempt", "the goal"))
    assert (task.packet_dir / "base" / "Mathlib" / "X.lean").read_text().startswith("theorem")
    assert not (task.packet_dir / "tmp" / "scratch.txt").exists()   # tmp/ is not a packet file
    prompt = asyncio.run(task.create_user_prompt())
    assert str(task.packet_dir.resolve()) in prompt and "{dir}" not in prompt
    assert "submit_outputs" in prompt
    assert result.outputs["goal_brief.md"]["content"] == "the goal"
    assert PacketSessionTask.product_of(result)["outputs"]["ledger.json"]["sha256"]


@pytest.mark.parametrize("bad, message", [
    ({"files": [{"path": "../escape.md", "content": "x"}]}, "relative path inside"),
    ({"files": [{"path": "goal_brief.md", "content": "x"}]}, "already input files"),
])
def test_a_packet_that_escapes_its_folder_or_holds_its_output_is_refused(bad, message):
    payload = {"task_type": "packet_session", "task_id": "t", "brief": "{dir}",
               "files": [{"path": "a.md", "content": "a"}], "outputs": OUTPUTS, **bad}
    with pytest.raises(Exception, match=message):
        create_task_from_data(payload, ApeAgentConfig())


def test_a_session_plan_holds_every_input_and_refuses_a_finished_folder(tmp_path):
    root = _packets(tmp_path / "packets")
    plan = S.plan_sessions(root, name="extract_v1", brief=EXTRACTOR_BRIEF, outputs=OUTPUTS,
                           out_dir=tmp_path / "plan")
    assert [p.packet_id for p in plan.packets] == ["pr33066", "pr33117"]
    assert set(plan.packets[0].files) == {"instructions.md", "pr.md", "model.md", "diff.patch",
                                          "base/Mathlib/X.lean"}
    assert S.load_session_plan(tmp_path / "plan") == plan
    (root / "pr33066" / "goal_brief.md").write_text("done")
    with pytest.raises(ValueError, match="finished session"):
        S.plan_sessions(root, name="again", brief=EXTRACTOR_BRIEF, outputs=OUTPUTS,
                        out_dir=tmp_path / "plan2")
    with pytest.raises(ValueError, match="never says where"):
        S.plan_sessions(root, name="nodir", brief="no folder here", outputs=OUTPUTS,
                        out_dir=tmp_path / "plan3", packet_ids=["pr33117"])


def _run(monkeypatch, tmp_path, plan, plan_dir, run_name, goal):
    """`run_sessions` with the orchestrator's execution done by real tasks and no model."""
    from ape.orchestration import orchestrator as orchestrator_module
    from ape.orchestration.models import Attempt, ExecutionStatus, Sample
    from ape.orchestration.persistence import TaskStorage

    async def fake_run(self, tasks):
        for task in tasks:
            storage = TaskStorage(self.tasks_dir / task.data.global_index, task.data.global_index)
            attempt = storage.task_dir / "samples" / "0" / "attempts" / "a1"
            result = await _work_a_session(task, attempt, goal(task.data.packet_id))
            now = datetime.now()
            await storage.save_sample(Sample(
                sample_id="s", task_global_index=task.data.global_index, sample_index=0,
                status=ExecutionStatus.SUCCESS, created_at=now, updated_at=now,
                attempts=[Attempt(attempt_id=1, path=attempt, status=ExecutionStatus.SUCCESS,
                                  created_at=now, max_turns=5, cost_limit=None,
                                  result=result.model_dump(mode="json"))]))
        return SimpleNamespace(task_results=[], total_token_usage=None)

    monkeypatch.setattr(orchestrator_module.TaskOrchestrator, "run", fake_run)
    config = ApeAgentConfig(runs_base_dir=tmp_path / "runs" / run_name)
    return asyncio.run(S.run_sessions(plan, plan_dir, config, run_name, logger=None))


def _context_file(plan_dir: Path, path: Path) -> Path:
    """The study's own step (it stays beside the study): a context section per PR from the
    stored extractor outputs, read from the store, never from a scratch folder."""
    rows = []
    for out in S.session_outputs(plan_dir):
        goal = Path(out.outputs["goal_brief.md"]["path"]).read_text()
        rows.append({"pr_number": int(out.packet_id.removeprefix("pr")),
                     "sections": [{"title": "Design goal", "text": goal}]})
    path.write_text("".join(json.dumps(r) + "\n" for r in sorted(rows, key=lambda r: r["pr_number"])))
    return path


def test_the_evidence_assisted_consumer_composes_through_shared_records(monkeypatch, tmp_path):
    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig, solo_context_block
    from src.mathlib_review.review.inputs import pin_overrides, resolve_input_files

    root = _packets(tmp_path / "packets")
    results = {}
    for name, goal in (("extractor_a", lambda pr: f"Goal A for {pr}"),
                       ("extractor_b", lambda pr: f"Goal B for {pr}")):
        plan_dir = tmp_path / name
        plan = S.plan_sessions(root, name=name, brief=EXTRACTOR_BRIEF + f"\n({name})",
                               outputs=OUTPUTS, out_dir=plan_dir)
        rows = _run(monkeypatch, tmp_path, plan, plan_dir, f"run_{name}", goal)
        assert sorted(r.packet_id for r in rows) == ["pr33066", "pr33117"]
        assert all(r.locator["run"] == f"run_{name}" and r.origin == "task" for r in rows)
        context = _context_file(plan_dir, tmp_path / f"context_{name}.jsonl")
        resolved = resolve_input_files({"context_file": str(context)})
        config = SoloReviewConfig(context_file=context, **pin_overrides(resolved))
        results[name] = (resolved["context_file"]["sha256"], solo_context_block(config, 33117))
    # Replacing the acquisition changed the sealed context and the reviewer's prompt, and nothing
    # downstream of the session plan was written for it.
    (sha_a, block_a), (sha_b, block_b) = results["extractor_a"], results["extractor_b"]
    assert sha_a != sha_b
    assert "Goal A for pr33117" in block_a and "Goal B for pr33117" in block_b


def test_a_hand_launched_sessions_outputs_import_against_the_plan(tmp_path):
    root = _packets(tmp_path / "packets")
    plan = S.plan_sessions(root, name="hist", brief=EXTRACTOR_BRIEF, outputs=OUTPUTS,
                           out_dir=tmp_path / "plan")
    done = tmp_path / "done" / "pr33066"
    done.mkdir(parents=True)
    (done / "goal_brief.md").write_text("old goal")
    with pytest.raises(ValueError, match="ledger.json is missing"):
        S.import_session_outputs(plan, tmp_path / "plan", {"pr33066": done}, name="hist")
    (done / "ledger.json").write_text("[]")
    (row,) = S.import_session_outputs(plan, tmp_path / "plan", {"pr33066": done}, name="hist",
                                      executor={"model": "claude-opus-5-5"})
    assert row.origin == "external_import" and row.executor["route"] == "unknown"
    assert Path(row.outputs["goal_brief.md"]["path"]).read_text() == "old goal"


def test_session_without_execute_runs_nothing(monkeypatch, tmp_path, capsys):
    from src.mathlib_review.review import cli

    S.plan_sessions(_packets(tmp_path / "packets"), name="p", brief=EXTRACTOR_BRIEF,
                    outputs=OUTPUTS, out_dir=tmp_path / "plan", replicates=2)
    monkeypatch.setattr(S, "run_sessions", lambda *a, **k: pytest.fail("ran"))
    assert cli.main(["session", "--plan", str(tmp_path / "plan"), "--config",
                     "configs/session/packet_session_opus55_claude_sub.yaml", "--run-name", "x"]) == 0
    err = capsys.readouterr().err
    assert "NOTHING RAN" in err and "2 session(s) x 2 replicate(s)" in err
