"""Does the whole-file compile's commandStart warning at EOF come from the file or from our strip?

Found by the D1 gpt-5.2 test (2026-10-02): the reviewer filed "will fail CI" twice from it. Spends
nothing: two local compiles of 33337's reviewed Submodule.lean, and one as-is `lean_verify_edit`.
Measured: the file ends with a newline; stripped (what `LeanVerifyToolsProvider.execute` sends)
-> 1 warning, `commandStart`, "starts on column 9"; with the final newline -> 0 warnings.
After the fix (`execute` keeps one final newline) the third line, through `execute`, reports 0.
"""
import asyncio, json, sys
from pathlib import Path
from types import SimpleNamespace
ROOT = Path("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/review-designs")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))

async def main():
    from ape.tasks.base import create_task_from_data
    from mcp.server.fastmcp import FastMCP
    from src.mathlib_review.agenda.cutoffs import cutoffs_by_episode
    from src.mathlib_review.review.runner import _solo_task_data, load_release, load_run, select_units_and_episodes
    from ape.tasks.lean_tasks.formal_math.review.base import WHOLE_FILE_OPTIONS
    from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider

    cfg = ROOT / "configs/designs/structured_dev_gpt52.yaml"
    dataset, scaffold, overrides = load_run(cfg, {"dataset": {"run_name": "eof_check", "pr_numbers": [33337]}})
    release = load_release(dataset)
    units, episodes = select_units_and_episodes(dataset, release)
    agenda = SimpleNamespace(proposals=[SimpleNamespace(episode_id=e.episode_id) for e in episodes])
    attempt = ROOT / ".ape/runs/review_designs_eof_check/tasks/0/samples/0/attempts/check"
    [payload] = _solo_task_data(agenda, episodes, dataset, cutoffs_by_episode(episodes), attempt / "t.jsonl", graphs=release["graphs"])
    task = create_task_from_data(payload, scaffold, task_config_overrides=overrides)
    async def term(r): pass
    await task.setup(term, "eof_check", attempt)
    mcp = FastMCP("x"); await task.register_task_tools(mcp)
    rel = "Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean"
    raw = (Path(task.target_workspace.path) / rel).read_bytes()
    print("file ends with newline:", raw.endswith(b"\n"), "| last 20 bytes:", raw[-20:])
    # 1. the reviewer's own tool, as-is
    out = await mcp.call_tool("lean_verify_edit", {"path": rel})
    text = json.dumps([getattr(c, "text", str(c)) for c in (out[0] if isinstance(out, tuple) else out)])
    print("lean_verify_edit as-is mentions commandStart:", "commandStart" in text)
    # 2. the engine directly, with and without the final newline
    tool = LeanVerifyToolsProvider(task=task, config=task.config, logger=task.logger)
    src = raw.decode("utf-8")
    for label, code in (("stripped (what execute sent before the fix)", src.strip()), ("with final newline", src.rstrip() + "\n")):
        res = await tool.verification_engine.verify(code=code, working_dir=tool.target_workspace, timeout=tool.tool_config.timeout,
            max_memory_gb=tool.tool_config.max_memory_gb, allow_sorries=tool.tool_config.allow_sorries,
            accepted_axioms=tool.tool_config.accepted_axioms, nproc=tool.tool_config.nproc, options=WHOLE_FILE_OPTIONS)
        warns = [m.data for m in res.warnings if "commandStart" in m.data or "linter" in m.data]
        print(label, "-> warnings:", len(res.warnings), "| commandStart:", sum("commandStart" in w for w in warns))
        for w in warns[:2]: print("    ", w[:300].replace("\n", " "))
    # 3. the path every review tool takes, `execute`, which since the fix keeps the final newline
    out = await tool.execute(code=src, max_messages=20, options=WHOLE_FILE_OPTIONS)
    warns = [w.get("data", "") for w in out.get("warnings") or []]
    print("through execute -> warnings:", len(warns), "| commandStart:", sum("commandStart" in w for w in warns))
asyncio.run(main())
