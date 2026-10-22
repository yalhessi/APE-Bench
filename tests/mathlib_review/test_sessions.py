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
    assert "{dir}" not in prompt and "submit_outputs" in prompt
    assert result.outputs["goal_brief.md"]["content"] == "the goal"
    assert PacketSessionTask.product_of(result)["outputs"]["ledger.json"]["sha256"]


def test_the_folder_in_the_brief_is_one_the_routes_file_tools_open(tmp_path):
    """On `ape_agent` the brief names the folder as APE's file tools take it; they refuse an
    absolute path. Asserted through the real provider's resolver and a real read, at the far end."""

    from ape.scaffolds.claude_code.config import ClaudeCodeConfig
    from ape.toolkits.file_system.core import FileSystemProvider

    payload = S.session_payloads(S.plan_sessions(
        _packets(tmp_path / "packets"), name="x", brief=EXTRACTOR_BRIEF, outputs=OUTPUTS,
        out_dir=tmp_path / "plan"))[0]
    task = create_task_from_data(payload, ApeAgentConfig())
    asyncio.run(_work_a_session(task, tmp_path / "attempt", "the goal"))
    prompt = asyncio.run(task.create_user_prompt())
    assert task.folder_reference == "scratch/packet" and "\nscratch/packet\n" in prompt
    files = FileSystemProvider(task=task, config=task.config)
    ok, resolved, _ = files._resolve_path(Path(task.folder_reference) / "instructions.md")
    assert ok and resolved == (task.packet_dir / "instructions.md").resolve()
    read = asyncio.run(files.file_read(Path(task.folder_reference) / "instructions.md"))
    assert "Extract the design decisions." in json.dumps(read)
    refused, _, why = files._resolve_path(task.packet_dir.resolve() / "instructions.md")
    assert not refused and "Absolute paths are not allowed" in why

    claude = create_task_from_data(payload, ClaudeCodeConfig())
    asyncio.run(claude.setup(None, "test", attempt_path=tmp_path / "attempt_claude"))
    assert claude.folder_reference == str(claude.packet_dir.resolve())
    assert claude.folder_reference in asyncio.run(claude.create_user_prompt())


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


def _base_context(path: Path) -> Path:
    """The control's rows, as a solo `context_file` holds them: one section a PR."""
    path.write_text("".join(json.dumps({"pr_number": pr, "sections": [
        {"title": "The PR model", "text": f"model of {pr}"}]}) + "\n" for pr in (33066, 33117)))
    return path


GOAL_SECTION = {"title": "Design goal", "lead": "Another session wrote this goal without the PR.",
                "output": "goal_brief.md"}


def test_the_evidence_assisted_consumer_composes_through_shared_records(monkeypatch, tmp_path):
    """Acquisition -> derived context -> reviewer prompt, through the shared records: the stored
    outputs, `derive_context` and its lineage, the input resolver and the solo renderer."""

    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig, solo_context_block
    from src.mathlib_review.review.inputs import pin_overrides, resolve_input_files

    root = _packets(tmp_path / "packets")
    base = _base_context(tmp_path / "base.jsonl")
    results = {}
    for name, goal in (("extractor_a", lambda pr: f"Goal A for {pr}"),
                       ("extractor_b", lambda pr: f"Goal B for {pr}")):
        plan_dir = tmp_path / name
        plan = S.plan_sessions(root, name=name, brief=EXTRACTOR_BRIEF + f"\n({name})",
                               outputs=OUTPUTS, out_dir=plan_dir)
        rows = _run(monkeypatch, tmp_path, plan, plan_dir, f"run_{name}", goal)
        assert sorted(r.packet_id for r in rows) == ["pr33066", "pr33117"]
        assert all(r.locator["run"] == f"run_{name}" and r.origin == "task" for r in rows)
        context = tmp_path / f"context_{name}.jsonl"
        lineage = S.derive_context(base=base, prs=[33066, 33117], out=context, sections=[
            {**GOAL_SECTION, "plan_dir": str(plan_dir), "producer": f"task-run_{name}"}])
        resolved = resolve_input_files({"context_file": str(context)})
        assert resolved["context_file"]["lineage_sha256"] == lineage.source_sha256
        config = SoloReviewConfig(context_file=context, **pin_overrides(resolved))
        results[name] = (resolved["context_file"]["sha256"], solo_context_block(config, 33117),
                         lineage.rows["33117"][0])
    # Swapping the acquisition producer changed the context, its lineage and the reviewer's
    # prompt, and nothing downstream of the session plan was written for it.
    (sha_a, block_a, ref_a), (sha_b, block_b, ref_b) = results["extractor_a"], results["extractor_b"]
    assert sha_a != sha_b and ref_a.producer == "task-run_extractor_a" != ref_b.producer
    assert "## The PR model" in block_a and block_a.index("The PR model") < block_a.index("Design goal")
    assert "Another session wrote this goal without the PR.\n\nGoal A for pr33117" in block_a
    assert "Goal B for pr33117" in block_b


def _imported(tmp_path, name="ex", goal=lambda pr: f"goal of {pr}"):
    """An extraction plan with one imported observation a packet."""
    root = _packets(tmp_path / f"packets_{name}")
    plan_dir = tmp_path / name
    plan = S.plan_sessions(root, name=name, brief=EXTRACTOR_BRIEF, outputs=OUTPUTS, out_dir=plan_dir)
    folders = {pid: _finished(tmp_path / f"done_{name}" / pid, goal(pid))
               for pid in ("pr33066", "pr33117")}
    S.import_session_outputs(plan, plan_dir, folders, name=name)
    return plan_dir


def test_a_missing_or_tampered_upstream_output_never_reaches_a_reviewer(tmp_path):
    from src.mathlib_review.review.inputs import resolve_input_files

    plan_dir = _imported(tmp_path)
    context = tmp_path / "ctx.jsonl"
    S.derive_context(base=_base_context(tmp_path / "base.jsonl"), prs=[33066, 33117], out=context,
                     sections=[{**GOAL_SECTION, "plan_dir": str(plan_dir), "producer": "import-ex"}])
    assert S.verify_context(context).rows["33066"][0].packet_id == "pr33066"
    # Deriving again is a no-op; the file is written once.
    S.derive_context(base=tmp_path / "base.jsonl", prs=[33066, 33117], out=context,
                     sections=[{**GOAL_SECTION, "plan_dir": str(plan_dir), "producer": "import-ex"}])

    stored = Path(S.session_outputs(plan_dir)[0].outputs["goal_brief.md"]["path"])
    original = stored.read_text()
    stored.write_text("tampered")
    with pytest.raises(ValueError, match="changed after it was stored"):
        resolve_input_files({"context_file": str(context)})
    stored.write_text(original)

    index = plan_dir / S.OUTPUTS_DIR / "import-ex.jsonl"
    kept = index.read_text()
    index.write_text(kept.split("\n", 1)[1])            # pr33066's observation is gone
    with pytest.raises(ValueError, match="no longer holds"):
        resolve_input_files({"context_file": str(context)})
    index.write_text(kept)

    context.write_text(context.read_text().replace("goal of", "goal  of"))
    with pytest.raises(ValueError, match="not the file its lineage derived"):
        resolve_input_files({"context_file": str(context)})


def test_a_session_plan_takes_its_inputs_from_upstream_observations_and_says_which(tmp_path):
    """Session to session: a sketch plan whose goal brief is the extraction's stored output."""

    extract = _imported(tmp_path)
    sketch_root = tmp_path / "sketch"
    for pid in ("pr33066", "pr33117"):
        (sketch_root / pid).mkdir(parents=True)
        (sketch_root / pid / "instructions.md").write_text("Sketch the design.\n")
    sketch_outputs = [{"name": "sketch.md", "kind": "text"}]
    plan = S.plan_sessions(sketch_root, name="sketch", brief="Folder: {dir}", outputs=sketch_outputs,
                           out_dir=tmp_path / "sketch_plan",
                           inputs_from={"goal_brief.md": {"plan_dir": str(extract),
                                                          "producer": "import-ex"}})
    assert plan.packets[0].files["goal_brief.md"] == "goal of pr33066"
    lineage = S.load_input_lineage(tmp_path / "sketch_plan")
    assert lineage.bound["pr33117"]["goal_brief.md"].producer == "import-ex"
    assert lineage.unmatched == {}

    # Its output, then a context section from it: the chain walks back to the extraction.
    S.import_session_outputs(plan, tmp_path / "sketch_plan",
                             {"pr33066": _sketched(tmp_path / "s1", "sketch one")}, name="sk")
    ref = S.observation(tmp_path / "sketch_plan", "import-sk", "pr33066", "sketch.md")
    chain = S.lineage_chain(ref)
    assert chain["inputs"]["goal_brief.md"]["observation"]["plan_id"] == "ex"

    # A historical folder is checked, not copied: equal bytes bind, other bytes are refused unless
    # recorded as unmatched.
    done = tmp_path / "sketch_done"
    for pid, brief in (("pr33066", "goal of pr33066"), ("pr33117", "a revised goal")):
        (done / pid).mkdir(parents=True)
        (done / pid / "instructions.md").write_text("Sketch the design.\n")
        (done / pid / "goal_brief.md").write_text(brief)
        (done / pid / "sketch.md").write_text("done")
    bind = {"goal_brief.md": {"plan_dir": str(extract), "producer": "import-ex"}}
    with pytest.raises(ValueError, match="no upstream observation holds"):
        S.plan_sessions(done, name="h", brief="Folder: {dir}", outputs=sketch_outputs,
                        out_dir=tmp_path / "h1", include=["instructions.md", "goal_brief.md"],
                        inputs_from=bind)
    S.plan_sessions(done, name="h", brief="Folder: {dir}", outputs=sketch_outputs,
                    out_dir=tmp_path / "h2", include=["instructions.md", "goal_brief.md"],
                    inputs_from=bind, allow_unmatched=True)
    held = S.load_input_lineage(tmp_path / "h2")
    assert set(held.bound) == {"pr33066", "pr33117"} and "goal_brief.md" in held.bound["pr33066"]
    assert "has these bytes" in held.unmatched["pr33117"]["goal_brief.md"]

    # An upstream whose stored bytes changed cannot feed a new plan.
    Path(S.session_outputs(extract)[1].outputs["goal_brief.md"]["path"]).write_text("tampered")
    with pytest.raises(ValueError, match="changed after it was stored"):
        S.plan_sessions(sketch_root, name="sketch2", brief="Folder: {dir}", outputs=sketch_outputs,
                        out_dir=tmp_path / "sketch_plan2",
                        inputs_from={"goal_brief.md": {"plan_dir": str(extract),
                                                       "producer": "import-ex"}})


def _sketched(folder: Path, text: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "sketch.md").write_text(text)
    return folder


def test_a_glob_include_plans_a_tree_of_inputs(tmp_path):
    root = _packets(tmp_path / "packets")
    for pid in ("pr33066", "pr33117"):
        (root / pid / "goal_brief.md").write_text("done")
        (root / pid / "ledger.json").write_text("[]")
    plan = S.plan_sessions(root, name="g", brief=EXTRACTOR_BRIEF, outputs=OUTPUTS,
                           out_dir=tmp_path / "plan", include=["instructions.md", "base/**/*.lean"])
    assert set(plan.packets[0].files) == {"instructions.md", "base/Mathlib/X.lean"}
    with pytest.raises(ValueError, match="lacks the named input files"):
        S.plan_sessions(root, name="g2", brief=EXTRACTOR_BRIEF, outputs=OUTPUTS,
                        out_dir=tmp_path / "plan2", include=["instructions.md", "nothing/**/*.md"])




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
    assert "claude_code claude-opus-5-5 at effort xhigh, CLI 2.1.285" in err

    assert cli.main(["session", "--plan", str(tmp_path / "plan"), "--config",
                     "configs/session/packet_session_elm_luna.yaml", "--run-name", "x"]) == 0
    assert "ape_agent elm_gpt_6_luna at effort high" in capsys.readouterr().err


# --- each execution or import keeps its own bytes (implementation review 2026-10-22, finding 1) --


def _finished(folder: Path, goal: str):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "goal_brief.md").write_text(goal)
    (folder / "ledger.json").write_text("[]")
    return folder


def test_two_executions_of_one_plan_keep_their_own_outputs(tmp_path):
    plan = S.plan_sessions(_packets(tmp_path / "packets"), name="p", brief=EXTRACTOR_BRIEF,
                           outputs=OUTPUTS, out_dir=tmp_path / "plan")
    (a,) = S.import_session_outputs(plan, tmp_path / "plan", {"pr33066": _finished(tmp_path / "a", "A output")},
                                    name="run_A")
    (b,) = S.import_session_outputs(plan, tmp_path / "plan", {"pr33066": _finished(tmp_path / "b", "B output")},
                                    name="run_B")
    assert a.producer == "import-run_A" and b.producer == "import-run_B"
    assert a.outputs["goal_brief.md"]["path"] != b.outputs["goal_brief.md"]["path"]
    rows = S.session_outputs(tmp_path / "plan")
    assert [S.read_output(r, "goal_brief.md") for r in rows] == ["A output", "B output"]
    assert [r.producer for r in S.session_outputs(tmp_path / "plan", producer="import-run_A")] == ["import-run_A"]
    # Re-exporting the same observation is a no-op; different bytes under it are refused.
    S.import_session_outputs(plan, tmp_path / "plan", {"pr33066": tmp_path / "a"}, name="run_A")
    with pytest.raises(FileExistsError):
        S.import_session_outputs(plan, tmp_path / "plan",
                                 {"pr33066": _finished(tmp_path / "a2", "A changed")}, name="run_A")
    # A stored value edited after the fact is refused on read.
    Path(a.outputs["goal_brief.md"]["path"]).write_text("tampered")
    with pytest.raises(ValueError, match="changed after it was stored"):
        S.read_output(a, "goal_brief.md")


def test_a_session_resume_on_another_route_is_refused(monkeypatch, tmp_path):
    from ape.orchestration import orchestrator as orchestrator_module

    plan = S.plan_sessions(_packets(tmp_path / "packets"), name="p", brief=EXTRACTOR_BRIEF,
                           outputs=OUTPUTS, out_dir=tmp_path / "plan")

    async def fake_run(self, tasks):
        return SimpleNamespace(task_results=[], total_token_usage=None)

    monkeypatch.setattr(orchestrator_module.TaskOrchestrator, "run", fake_run)
    first = ApeAgentConfig(runs_base_dir=tmp_path / "runs")
    first.llm_config.model_name = "gpt_5_mini"
    asyncio.run(S.run_sessions(plan, tmp_path / "plan", first, "r", logger=None))
    other = ApeAgentConfig(runs_base_dir=tmp_path / "runs")
    other.llm_config.model_name = "gpt_5.2"
    with pytest.raises(ValueError, match="A run continues on one route"):
        asyncio.run(S.run_sessions(plan, tmp_path / "plan", other, "r", logger=None))


def test_a_finished_folder_is_planned_from_its_named_inputs(tmp_path):
    root = _packets(tmp_path / "packets")
    _finished(root / "pr33066", "done")
    (root / "pr33066" / "leaks.json").write_text("{}")        # an audit written beside them
    with pytest.raises(ValueError, match="finished session"):
        S.plan_sessions(root, name="x", brief=EXTRACTOR_BRIEF, outputs=OUTPUTS, out_dir=tmp_path / "p0")
    plan = S.plan_sessions(root, name="hist", brief=EXTRACTOR_BRIEF, outputs=OUTPUTS,
                           out_dir=tmp_path / "p1", packet_ids=["pr33066"],
                           include=["instructions.md", "pr.md", "model.md", "diff.patch"])
    assert set(plan.packets[0].files) == {"instructions.md", "pr.md", "model.md", "diff.patch"}
    with pytest.raises(ValueError, match="lacks the named input files"):
        S.plan_sessions(root, name="bad", brief=EXTRACTOR_BRIEF, outputs=OUTPUTS,
                        out_dir=tmp_path / "p2", include=["missing.md"])


def test_the_trace_finds_a_reviewers_context_lineage_by_content(tmp_path):
    """A run made before lineage existed names only a path; the bytes find the derivation."""

    from src.mathlib_review.analysis.trace import context_lineage_of
    from src.mathlib_review.io import sha256_file

    plan_dir = _imported(tmp_path)
    context = tmp_path / "ctx.jsonl"
    S.derive_context(base=_base_context(tmp_path / "base.jsonl"), prs=[33066, 33117], out=context,
                     sections=[{**GOAL_SECTION, "plan_dir": str(plan_dir), "producer": "import-ex"}])
    elsewhere = tmp_path / "elsewhere" / "context_ctx_dev.jsonl"   # same bytes, another path
    elsewhere.parent.mkdir()
    elsewhere.write_bytes(context.read_bytes())
    found = context_lineage_of(sha256_file(elsewhere), elsewhere,
                               {"lineage_snapshot": str(S.context_lineage_path(context))}, pr=33117)
    assert found["status"].startswith("recomputed") and found["sections"] == ["Design goal"]
    upstream = found["upstream"]["Design goal"]["observation"]
    assert (upstream["plan_id"], upstream["producer"], upstream["packet_id"]) == (
        "ex", "import-ex", "pr33117")
    assert context_lineage_of("0" * 64, elsewhere, {}, pr=33117) is None


def test_a_historical_input_binds_to_whichever_producer_holds_its_bytes(tmp_path):
    """The probe's goal briefs came from first extractions, revisions or repairs: three plans."""

    first = _imported(tmp_path, "first")
    revised = _imported(tmp_path, "revised", goal=lambda pr: f"revised goal of {pr}")
    done = tmp_path / "decision"
    for pid, brief in (("pr33066", "goal of pr33066"), ("pr33117", "revised goal of pr33117")):
        (done / pid).mkdir(parents=True)
        (done / pid / "goal_brief.md").write_text(brief)
        (done / pid / "decision_context.md").write_text("done")
    sources = [{"plan_dir": str(first), "producer": "import-first"},
               {"plan_dir": str(revised), "producer": "import-revised"}]
    S.plan_sessions(done, name="d", brief="Folder: {dir}", out_dir=tmp_path / "d",
                    outputs=[{"name": "decision_context.md"}], include=["goal_brief.md"],
                    inputs_from={"goal_brief.md": sources})
    bound = S.load_input_lineage(tmp_path / "d").bound
    assert bound["pr33066"]["goal_brief.md"].plan_id == "first"
    assert bound["pr33117"]["goal_brief.md"].plan_id == "revised"

    # The same bytes from two producers, for another packet than the folder's: refused, not chosen.
    twin = _imported(tmp_path, "twin")
    (done / "pr33066_r2").mkdir()
    (done / "pr33066_r2" / "goal_brief.md").write_text("goal of pr33066")
    with pytest.raises(ValueError, match="several observations"):
        S.plan_sessions(done, name="d2", brief="Folder: {dir}", out_dir=tmp_path / "d2",
                        outputs=[{"name": "decision_context.md"}], include=["goal_brief.md"],
                        packet_ids=["pr33066_r2"],
                        inputs_from={"goal_brief.md": sources + [
                            {"plan_dir": str(twin), "producer": "import-twin"}]})


def test_a_reviewers_prompt_finds_the_derivation_that_accounts_for_all_of_it(monkeypatch, tmp_path):
    """A Phase A run names a context path on another branch. Its first message holds what it was
    shown; the control's block sits inside every strategy's, so the longest match is the one."""

    from ape.tasks.lean_tasks.formal_math.review.solo import SoloReviewConfig, solo_context_block
    from src.mathlib_review.analysis.trace import context_lineage_from_prompt

    plan_dir = _imported(tmp_path)
    monkeypatch.chdir(tmp_path)
    kept = Path("results/pr_review_v5/probes/x/measurements/ctx")
    kept.mkdir(parents=True)
    base = _base_context(tmp_path / "base.jsonl")
    S.derive_context(base=base, prs=[33066, 33117], out=kept / "context_ctl.jsonl", sections=[])
    S.derive_context(base=base, prs=[33066, 33117], out=kept / "context_ctx.jsonl",
                     sections=[{**GOAL_SECTION, "plan_dir": str(plan_dir), "producer": "import-ex"}])
    shown = solo_context_block(SoloReviewConfig(context_file=kept / "context_ctx.jsonl"), 33117)
    prompt = f"Review PR 33117.\n\n{shown}\n\nSubmit your findings."
    found = context_lineage_from_prompt(prompt, 33117)
    assert found["derived_file"].endswith("context_ctx.jsonl")
    assert found["upstream"]["Design goal"]["observation"]["packet_id"] == "pr33117"
    control = solo_context_block(SoloReviewConfig(context_file=kept / "context_ctl.jsonl"), 33117)
    assert context_lineage_from_prompt(f"Review.\n\n{control}\n", 33117)["sections"] == []
    assert context_lineage_from_prompt("Review PR 33117 with nothing added.", 33117) is None
