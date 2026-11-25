"""Exercise the pilot via the real Claude first-message renderer and registered MCP tool."""

import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from pydantic import ValidationError

from ape.scaffolds.claude_code.config import ClaudeCodeConfig
from ape.scaffolds.claude_code.scaffold import ClaudeCodeScaffold
from ape.tasks.base import create_task_from_data
from ape.tasks.models import WorkspaceInfo
from ape.tasks.lean_tasks.formal_math.review.whole_pr import WholePRConfig


@pytest.fixture
def anyio_backend():
    return "asyncio"


def reviewer(tmp_path, *, tools=(), context=None):
    config = ClaudeCodeConfig(batch_preamble="plain", workspace_environment=False)
    overrides = {}
    if context is not None:
        path = tmp_path / "context.jsonl"
        path.write_text(json.dumps(context) + "\n")
        overrides["context_file"] = str(path)
    task = create_task_from_data({
        "task_type": "lean_pr_review_v5_whole_pr", "task_id": "r", "pr_number": 12,
        "episode_id": "ep", "invocation_id": "ep#solo", "snapshot_head_sha": "abc123",
        "pr_title": "Library change", "pr_description": "Public description", "diff": "-old\n+new",
        "target_workspace": {"name": "target"}, "changed_files": ["Mathlib/F.lean"],
        "context_tools": list(tools), "retrieval_cutoff": "2026-01-01T00:00:00Z",
    }, config, task_config_overrides=overrides)
    task.workspaces_dir = tmp_path / "r001"
    task.scratch_workspace = WorkspaceInfo(name="scratch", path=task.workspaces_dir / "scratch")
    task.target_workspace = WorkspaceInfo(name="target", path=task.workspaces_dir / "target",
                                          read_only_path_patterns=["**/*"])
    task.termination_callback = AsyncMock()
    return task


async def first_message(task):
    scaffold = ClaudeCodeScaffold()
    scaffold.task = task
    return await scaffold._initial_prompt(scaffold._session_cwd())


@pytest.mark.anyio
async def test_search_grant_and_delivered_lists_are_the_only_differences(tmp_path):
    solo = reviewer(tmp_path, tools=["declaration_search"])
    source = reviewer(tmp_path, tools=["declaration_search", "precedent_search"])
    plain = await first_message(solo)
    assert await first_message(source) == plain
    assert "What changes, if any" in plain and "abc123" in plain and "-old\n+new" in plain
    assert "Every response MUST" not in plain and "merge_ready" not in plain and "concern_family" not in plain
    servers = []
    for task in [solo, source]:
        mcp = FastMCP("test")
        await task.register_task_tools(mcp)
        servers.append({tool.name: tool.parameters for tool in await mcp.list_tools()})
    common, search = servers
    assert set(search) == set(common) | {"precedent_search"}
    assert all(search[k] == v for k, v in common.items())
    assert common["submit_findings"]["required"] == ["findings"]
    assert set(common["submit_findings"]["properties"]) == {"findings", "message"}
    row = {"pr_number": 12, "episode_id": "ep", "reviewed_head_sha": "abc123", "sections": []}
    assert await first_message(reviewer(tmp_path, context=row)) == plain
    row["sections"] = [{"title": "Conventions", "text": "An advisory convention."}]
    assert await first_message(reviewer(tmp_path, context=row)) == plain + "\n\n## Conventions\n\nAn advisory convention."
    with pytest.raises(ValueError, match="either excerpt search"):
        await first_message(reviewer(tmp_path, tools=["precedent_search"], context=row))
    row["reviewed_head_sha"] = "another"
    with pytest.raises(ValueError, match="reviewed head"):
        await first_message(reviewer(tmp_path, context=row))
    row.update(reviewed_head_sha="abc123", sections=[{"title": "PR map", "text": "old checklist"}])
    with pytest.raises(ValueError, match="Conventions section"):
        await first_message(reviewer(tmp_path, context=row))


@pytest.mark.anyio
async def test_submit_tool_preserves_exact_order_fields_and_successful_empty_review(tmp_path):
    task = reviewer(tmp_path)
    mcp = FastMCP("test")
    await task.register_task_tools(mcp)
    findings = [{"claim": "  A general concern.  ", "suggested_fix": "Please explain.\n"}]
    findings.extend({"claim": f"Reason {i}", "suggested_fix": f"Change {i}", "path": "Mathlib/F.lean",
                     "line_start": i} for i in range(1, 22))
    for submitted in [findings, []]:
        await mcp.call_tool("submit_findings", {"findings": submitted, "message": "Summary."})
        result, = task.termination_callback.await_args.args
        assert result.success and result.merge_ready_as_is is None and result.review_message == "Summary."
        assert result.submitted_findings == submitted
        assert [f["claim"] for f in result.findings] == [f["claim"] for f in submitted]
        assert [f["suggested_fix"] for f in result.findings] == [f["suggested_fix"] for f in submitted]
    with pytest.raises(ValidationError):
        WholePRConfig(system_prompt_file=__file__)
