"""The Codex scaffold drives `codex exec` with an attempt-local config, and audits what ran.

Each setting below is one the installed CLI (`codex-cli` 0.144.5) was shown to need against a
local recording server (2026-10-01, no model): MCP calls are cancelled in exec mode unless the
server's tools are pre-approved; the shell and the other built-ins go through `[features]`; the
model name selects Codex's own catalog entry.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def _config(**overrides):
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.codex.config import CodexConfig

    return CodexConfig(llm_config=LLMConfig(model_name="gpt_5.2"), **overrides)


def test_the_attempt_config_routes_through_the_relay_and_pre_approves_ape_tools(tmp_path):
    from ape.scaffolds.codex.scaffold import codex_config, codex_model_name

    config = _config(sandbox_mode="read-only", disabled_features=["shell_tool", "unified_exec"])
    model = codex_model_name(config)
    settings = codex_config(config, model, "http://localhost:4000", "http://localhost:5000/mcp",
                            tmp_path / "model_catalog.json")
    assert model == "gpt-5.2"
    assert settings["model_provider"] == "relay"
    assert settings["model_providers"]["relay"] == {
        "name": "relay", "base_url": "http://localhost:4000", "wire_api": "responses"}
    core = settings["mcp_servers"]["core"]
    assert core["url"] == "http://localhost:5000/mcp"
    assert core["default_tools_approval_mode"] == "approve", "exec mode cancels unapproved calls"
    assert settings["features"] == {"shell_tool": False, "unified_exec": False}
    assert settings["sandbox_mode"] == "read-only" and settings["web_search"] == "disabled"
    assert settings["project_doc_max_bytes"] == 0, "no AGENTS.md from the repository above"
    assert settings["model_catalog_json"] == str(tmp_path / "model_catalog.json")
    assert _config().mcp_server_name == "mcp__core__", "the names Claude Code gives the same tools"


def _manager(tmp_path):
    from ape.scaffolds.codex.conversation import CodexConversationManager

    manager = object.__new__(CodexConversationManager)
    manager._thread_id = None
    manager.task = SimpleNamespace(workspaces_dir=tmp_path / "workspaces")
    return manager


def test_the_first_turn_starts_a_thread_and_later_turns_resume_it(tmp_path):
    manager = _manager(tmp_path)
    assert manager.exec_command("Review PR 1.")[:3] == ["codex", "exec", "--json"]
    assert manager.exec_command("Review PR 1.")[-1] == "Review PR 1."
    manager._thread_id = "01a0f721"
    assert manager.exec_command("Continue.")[:4] == ["codex", "exec", "resume", "01a0f721"]


def test_the_cli_never_holds_a_model_key(tmp_path, monkeypatch):
    """The relay calls the model; a key in the CLI's environment could reach OpenAI directly."""

    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-pass")
    env = _manager(tmp_path)._environment()
    assert "OPENAI_API_KEY" not in env
    assert env["CODEX_HOME"].endswith("workspaces/.codex") and env["HOME"].endswith("workspaces")


def test_only_the_named_builtins_reach_the_model():
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.codex.relay import CodexRelaySession

    relay = CodexRelaySession(port=41013, llm_config=LLMConfig(model_name="gpt_5.2"),
                              relayed_builtin_tools=["update_plan"])
    tools = relay._backend_tools([
        {"type": "function", "name": "update_plan", "parameters": {}},
        {"type": "function", "name": "view_image", "parameters": {}},
        {"type": "function", "name": "request_user_input", "parameters": {}},
        {"type": "namespace", "name": "mcp__core",
         "tools": [{"type": "function", "name": "file_read", "parameters": {}}]}])
    assert [t["function"]["name"] for t in tools] == ["update_plan", "mcp__core__file_read"]


def _events(path: Path, items):
    path.write_text("".join(json.dumps({"type": "item.completed", "item": i}) + "\n" for i in items))
    return path


def test_the_audit_passes_a_session_that_used_only_ape_tools(tmp_path):
    from ape.scaffolds.codex.scaffold import audit_events

    report = audit_events(_events(tmp_path / "e.jsonl", [
        {"type": "mcp_tool_call", "server": "core", "tool": "file_read", "error": None},
        {"type": "todo_list"}, {"type": "agent_message", "text": "done"}]), _config())
    assert report["clean"] and report["usable"]
    assert report["by_kind"] == {"mcp_tool_call": 1, "todo_list": 1, "agent_message": 1}


@pytest.mark.parametrize("item", [
    {"type": "command_execution", "command": "git show HEAD:inputs/gold.json"},
    {"type": "file_change", "changes": [{"path": "/repo/inputs/gold.json"}]},
    {"type": "web_search", "query": "mathlib PR 43192 review"},
    {"type": "mcp_tool_call", "server": "elsewhere", "tool": "read"},
])
def test_the_audit_flags_anything_outside_ape_tools(tmp_path, item):
    from ape.scaffolds.codex.scaffold import audit_events

    report = audit_events(_events(tmp_path / "e.jsonl", [item]), _config())
    assert report["clean"] is False and report["leaks"]


def test_a_cancelled_mcp_call_makes_the_session_unusable(tmp_path):
    """What exec mode does to a call needing approval; seen before `default_tools_approval_mode`."""

    from ape.scaffolds.codex.scaffold import audit_events

    report = audit_events(_events(tmp_path / "e.jsonl", [
        {"type": "mcp_tool_call", "server": "core", "tool": "submit_findings",
         "error": {"message": "user cancelled MCP tool call"}}]), _config())
    assert report["clean"] is True and report["usable"] is False


def test_a_missing_event_log_is_unauditable(tmp_path):
    from ape.scaffolds.codex.scaffold import audit_events

    report = audit_events(tmp_path / "absent.jsonl", _config())
    assert report["clean"] is False and "error" in report
