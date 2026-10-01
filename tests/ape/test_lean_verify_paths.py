"""`lean_verify(file_path=...)` must reach the reviewed file, and nothing outside the workspace.

Its first path check compared the *resolved* file with the *unresolved* workspace directory.
`target/` is a link into the shared reviewed-workspace store, so every `target/...` file resolved
outside it and was refused before the check meant for it (scratch or target, resolved) ran: 13 of
18 calls under ape_agent and 29 of 32 under claude_code on the post-cutoff set (2026-10-01).

The test drives the registered tool on a small copy of the real layout: `workspaces/target` linking
into a store that also holds another workspace, and a repository beside it holding gold. The
compile step is replaced, so what is measured is only which paths reach it.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest


def _layout(tmp_path):
    store = tmp_path / "store"
    reviewed = store / "base+pr" / "Mathlib"
    reviewed.mkdir(parents=True)
    (reviewed / "Foo.lean").write_text("theorem foo : True := trivial\n")
    other = store / "later"
    other.mkdir()
    (other / "Merged.lean").write_text("theorem merged : True := trivial\n")
    gold = tmp_path / "repo" / "gold.lean"
    gold.parent.mkdir()
    gold.write_text("-- gold\n")
    workspaces = tmp_path / "attempt" / "workspaces"
    (workspaces / "scratch").mkdir(parents=True)
    (workspaces / "scratch" / "Try.lean").write_text("example : True := trivial\n")
    (workspaces / "target").symlink_to(store / "base+pr")
    return workspaces, store, other, gold


def _lean_verify(workspaces, allows_target=True):
    from fastmcp import Client, FastMCP

    from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider

    provider = object.__new__(LeanVerifyToolsProvider)
    provider.task = SimpleNamespace(workspaces_dir=workspaces, lean_verify_allows_target=allows_target)
    provider.target_workspace = workspaces / "target"
    provider.scratch_workspace = workspaces / "scratch"
    provider.logger = SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None,
                                      warning=lambda *a, **k: None, debug=lambda *a, **k: None)

    async def compiled(code, max_messages=20):
        return {"success": True, "compiled": code}

    provider.execute = compiled
    mcp = FastMCP("probe")
    provider.register_tools(mcp, {"lean_verify"})

    def call(file_path):
        async def run():
            async with Client(mcp) as client:
                result = await client.call_tool("lean_verify", {"file_path": file_path})
                return result.data if hasattr(result, "data") else result
        return asyncio.run(run())

    return call


def test_a_reviewed_file_reaches_the_compiler(tmp_path):
    workspaces, store, _other, _gold = _layout(tmp_path)
    call = _lean_verify(workspaces)
    assert call("target/Mathlib/Foo.lean")["success"] is True
    # As Claude Code's preamble advertises it: the resolved store path.
    assert call(str(store / "base+pr" / "Mathlib" / "Foo.lean"))["success"] is True
    assert call("scratch/Try.lean")["success"] is True


@pytest.mark.parametrize("escape", ["../../repo/gold.lean", "target/../../../repo/gold.lean"])
def test_climbing_out_of_the_workspace_is_refused(tmp_path, escape):
    workspaces, _store, _other, _gold = _layout(tmp_path)
    result = _lean_verify(workspaces)(escape)
    assert result["success"] is False and "compiled" not in result


def test_another_workspace_in_the_store_and_the_gold_are_refused(tmp_path):
    workspaces, _store, other, gold = _layout(tmp_path)
    call = _lean_verify(workspaces)
    for path in (str(other / "Merged.lean"), str(gold)):
        result = call(path)
        assert result["success"] is False and "compiled" not in result, path


def test_a_task_that_does_not_opt_in_still_cannot_read_target(tmp_path):
    """proof_engineering's rule, that a submission compiles from scratch alone, is untouched."""

    workspaces, _store, _other, _gold = _layout(tmp_path)
    call = _lean_verify(workspaces, allows_target=False)
    assert call("target/Mathlib/Foo.lean")["success"] is False
    assert call("scratch/Try.lean")["success"] is True
