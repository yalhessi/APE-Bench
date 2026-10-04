"""Claude Code on a subscription: the route with no relay, where the CLI runs a Claude model on
its own login.

Without the relay, four things the relay used to provide were missing: the login (the CLI runs
with HOME at the attempt's `workspaces/`), the usage record and so the `ExecutionLimits` check,
the session id and so the transcript, and any record of which model ran. A spent usage limit
also needed to fail the attempt rather than end it quietly. These tests pin each replacement,
with the message shapes taken from live probes of claude-agent-sdk 0.1.81 driving CLI 2.1.285
on claude-opus-5-5 (2026-10-01).
"""

from __future__ import annotations

import dataclasses
import inspect
import logging
from types import SimpleNamespace

import pytest

from ape.llm_clients.config import LLMConfig, TokenBudgetExhaustedError
from ape.scaffolds.base import MaxTurnsReachedError
from ape.scaffolds.claude_code.config import ClaudeCodeConfig
from ape.scaffolds.claude_code.conversation import (
    ClaudeCodeConversationManager, ClaudeSessionError)


def _config(**overrides) -> ClaudeCodeConfig:
    fields = dict(llm_config=LLMConfig(model_name=None), claude_model="claude-opus-5-5",
                  cli_version="2.1.285", effort="xhigh", contain_to_workspace=True,
                  setting_sources=[], strict_mcp_config=True)
    fields.update(overrides)
    return ClaudeCodeConfig(**fields)


# --- the config names the session ----------------------------------------------------------


def test_a_complete_subscription_config_is_accepted():
    config = _config()
    assert config.subscription_route
    assert config.resolved_cli_path().name == "claude-2.1.285-linux-x64"
    assert config.resolved_cli_path().parent.parts[-2:] == ("data", "resources")


def test_the_relay_route_is_unchanged():
    config = ClaudeCodeConfig(llm_config=LLMConfig(model_name="gpt_5.2"))
    assert not config.subscription_route
    assert config.resolved_cli_path() is None
    assert config.effort is None


@pytest.mark.parametrize("override,named", [
    ({"claude_model": "opus"}, "not a full model name"),
    ({"claude_model": "opus[1m]"}, "not a full model name"),
    ({"llm_config": LLMConfig(model_name="gpt_5.2")}, "starts the relay"),
    ({"cli_version": None}, "bundled CLI"),
    ({"effort": None}, "CLAUDE_EFFORT"),
    ({"contain_to_workspace": False}, "contain_to_workspace"),
    ({"setting_sources": None}, "setting_sources"),
    ({"strict_mcp_config": False}, "claude.ai connectors"),
])
def test_a_subscription_config_that_leaves_the_session_to_the_cli_is_refused(override, named):
    with pytest.raises(ValueError, match=named.replace("[", r"\[")):
        _config(**override)


def test_effort_on_the_relay_route_is_refused():
    """There the backend's reasoning is llm_config's; a CLI effort would be a second knob for
    the same thing that the relay does not forward."""

    with pytest.raises(ValueError, match="relay route"):
        ClaudeCodeConfig(llm_config=LLMConfig(model_name="gpt_5.2"), effort="high")


def test_the_sdk_accepts_the_pinned_cli_and_effort():
    from claude_agent_sdk import ClaudeAgentOptions

    names = {f.name for f in dataclasses.fields(ClaudeAgentOptions)}
    assert {"cli_path", "effort", "model"} <= names


def test_the_pins_reach_the_sdk_options():
    from ape.scaffolds.claude_code.scaffold import ClaudeCodeScaffold

    source = inspect.getsource(ClaudeCodeScaffold._run_batch_mode)
    assert "model=config.claude_model or config.llm_config.model_name" in source
    assert "cli_path=self._pinned_cli_path()" in source
    assert "effort=config.effort" in source
    assert "**self._subscription_environment()" in source


# --- the CLI binary --------------------------------------------------------------------------


def _scaffold(config):
    from ape.scaffolds.claude_code.scaffold import ClaudeCodeScaffold

    scaffold = ClaudeCodeScaffold()
    scaffold.task = SimpleNamespace(config=config)
    return scaffold


def test_a_missing_pinned_cli_is_refused_not_replaced(tmp_path, monkeypatch):
    import ape.utils.project

    monkeypatch.setattr(ape.utils.project, "PROJECT_ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="claude-2.1.285-linux-x64"):
        _scaffold(_config())._pinned_cli_path()

    binary = tmp_path / "data" / "resources" / "claude-2.1.285-linux-x64"
    binary.parent.mkdir(parents=True)
    binary.write_text("")
    assert _scaffold(_config())._pinned_cli_path() == str(binary)


def test_the_relay_route_keeps_the_bundled_cli():
    assert _scaffold(ClaudeCodeConfig(llm_config=LLMConfig(model_name="gpt_5.2"))
                     )._pinned_cli_path() is None


# --- the login and the launching shell -------------------------------------------------------


def test_the_login_travels_as_the_oauth_token(monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="claude setup-token"):
        _scaffold(_config())._subscription_environment()

    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "sk-ant-oat01-test")
    assert _scaffold(_config())._subscription_environment()[
        "CLAUDE_CODE_OAUTH_TOKEN"] == "sk-ant-oat01-test"


def test_the_launching_sessions_claude_variables_are_blanked(monkeypatch):
    """A run launched from a Claude Code session inherits these through the SDK; options.env
    can override a variable but not remove one."""

    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "sk-ant-oat01-test")
    monkeypatch.setenv("CLAUDE_EFFORT", "xhigh")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "parent")
    monkeypatch.setenv("CLAUDE_CODE_MESSAGING_SOCKET", "/run/parent.sock")
    env = _scaffold(_config())._subscription_environment()
    assert env["CLAUDE_EFFORT"] == ""
    assert env["CLAUDE_CODE_SESSION_ID"] == ""
    assert env["CLAUDE_CODE_MESSAGING_SOCKET"] == ""
    assert "CLAUDE_CODE_ENTRYPOINT" not in env  # the SDK's own, left to it
    assert env["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"


@pytest.mark.parametrize("variable", ["ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL"])
def test_an_inherited_anthropic_variable_is_refused(monkeypatch, variable):
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "sk-ant-oat01-test")
    monkeypatch.setenv(variable, "x")
    with pytest.raises(RuntimeError, match=variable):
        _scaffold(_config())._subscription_environment()


def test_the_relay_route_environment_is_untouched(monkeypatch):
    monkeypatch.setenv("CLAUDE_EFFORT", "xhigh")
    assert _scaffold(ClaudeCodeConfig(llm_config=LLMConfig(model_name="gpt_5.2"))
                     )._subscription_environment() == {}


# --- the SDK's messages in place of the relay ------------------------------------------------


def _manager(**limits) -> ClaudeCodeConversationManager:
    config = _config()
    config.execution.max_turns = limits.pop("max_turns", 100)
    return ClaudeCodeConversationManager(config=config, task=None,
                                         logger=logging.getLogger(__name__), **limits)


def _init(**data):
    from claude_agent_sdk import SystemMessage

    return SystemMessage(subtype="init", data={
        "session_id": "a16dd0d0", "model": "claude-opus-5-5", "claude_code_version": "2.1.285",
        "apiKeySource": "none", **data})


def _stream(event):
    from claude_agent_sdk import StreamEvent

    return StreamEvent(uuid="u", session_id="a16dd0d0", event=event)


def _reply(message_id, opened, final):
    """A main-model reply's two usage-bearing stream events, as the CLI emits them."""
    return [
        _stream({"type": "message_start", "message": {
            "id": message_id, "model": "claude-opus-5-5", "usage": opened}}),
        _stream({"type": "message_delta", "usage": final}),
    ]


# The first live probe's two replies (one Read call, then the answer).
FIRST = _reply("msg_1",
               {"input_tokens": 2, "cache_creation_input_tokens": 1464,
                "cache_read_input_tokens": 0, "output_tokens": 16},
               {"input_tokens": 2, "cache_creation_input_tokens": 1464,
                "cache_read_input_tokens": 0, "output_tokens": 124})
SECOND = _reply("msg_2",
                {"input_tokens": 2, "cache_creation_input_tokens": 3720,
                 "cache_read_input_tokens": 1464, "output_tokens": 8},
                {"input_tokens": 2, "cache_creation_input_tokens": 3720,
                 "cache_read_input_tokens": 1464, "output_tokens": 163,
                 "output_tokens_details": {"thinking_tokens": 155}})


def _result(**fields):
    from claude_agent_sdk import ResultMessage

    defaults = dict(subtype="success", duration_ms=1, duration_api_ms=1, is_error=False,
                    num_turns=2, session_id="a16dd0d0", total_cost_usd=0.0485,
                    model_usage={
                        "claude-haiku-4-5-20251001": {
                            "inputTokens": 910, "outputTokens": 12,
                            "cacheReadInputTokens": 0, "cacheCreationInputTokens": 0},
                        "claude-opus-5-5": {
                            "inputTokens": 4, "outputTokens": 287,
                            "cacheReadInputTokens": 1464, "cacheCreationInputTokens": 5184,
                            "thinkingTokens": 155}})
    defaults.update(fields)
    return ResultMessage(**defaults)


def _feed(manager, messages):
    for message in messages:
        manager._read_sdk_message(message)


def test_usage_is_read_from_the_stream_not_the_assistant_message():
    """An AssistantMessage carries the usage its reply opened with -- 16 output tokens of a
    reply that ended at 124 -- so counting it would undercount every reply's output."""

    from claude_agent_sdk import AssistantMessage, ToolUseBlock

    manager = _manager()
    _feed(manager, [_init(), *FIRST[:1],
                    AssistantMessage(content=[ToolUseBlock(id="t", name="Read", input={})],
                                     model="claude-opus-5-5", usage=FIRST[0].event[
                                         "message"]["usage"]),
                    *FIRST[1:]])
    usage = manager.get_token_usage()
    assert usage.output_tokens == 124
    assert usage.input_tokens == 2 + 1464  # cache writes inside the prompt
    assert usage.processed_tokens == 1590
    assert usage.cached_total_cost == 0.0  # nothing billed on a subscription
    assert manager.get_current_turns() == 1


def test_the_result_total_covers_the_background_calls_and_replaces_the_stream_sum():
    """`model_usage` is cumulative over the session and includes the Haiku housekeeping
    calls, which never reach the SDK as stream events (910 + 12 tokens in the probe)."""

    manager = _manager()
    _feed(manager, [_init(), *FIRST, *SECOND])
    assert manager.get_token_usage().processed_tokens == 1590 + 5349
    _feed(manager, [_result()])
    assert manager.get_token_usage().processed_tokens == 922 + 4 + 287 + 1464 + 5184
    _feed(manager, _reply("msg_3", {"input_tokens": 10, "output_tokens": 1},
                          {"input_tokens": 10, "output_tokens": 5}))
    assert manager.get_token_usage().processed_tokens == 7861 + 15
    assert manager.get_current_turns() == 3


def test_the_token_ceiling_stops_the_session_as_the_next_reply_starts():
    """Checked before a reply, as the relay checks before forwarding a request: the reply
    that crossed the ceiling has its tool calls run, a submission among them."""

    manager = _manager(token_limit=6_000)
    _feed(manager, [_init(), *FIRST, *SECOND])  # 6,939 tokens, crossed during the second
    with pytest.raises(TokenBudgetExhaustedError, match="6,939 >= 6,000"):
        _feed(manager, _reply("msg_3", {"input_tokens": 1}, {"output_tokens": 1})[:1])


def test_the_turn_limit_stops_the_session_as_the_next_reply_starts():
    manager = _manager(max_turns=2)
    _feed(manager, [_init(), *FIRST, *SECOND])
    with pytest.raises(MaxTurnsReachedError):
        _feed(manager, _reply("msg_3", {"input_tokens": 1}, {"output_tokens": 1})[:1])


def test_the_session_id_comes_from_the_sdk():
    manager = _manager()
    assert manager.get_claude_code_session_id() is None
    _feed(manager, [_init()])
    assert manager.get_claude_code_session_id() == "a16dd0d0"


@pytest.mark.parametrize("field,value", [
    ("model", "claude-sonnet-5-5"),
    ("claude_code_version", "2.1.139"),
    ("apiKeySource", "ANTHROPIC_API_KEY"),
])
def test_a_session_that_is_not_the_pin_is_refused_at_start(field, value):
    with pytest.raises(ClaudeSessionError, match=field):
        _feed(_manager(), [_init(**{field: value})])


def test_a_spent_usage_limit_fails_the_attempt():
    from claude_agent_sdk import RateLimitEvent
    from claude_agent_sdk.types import RateLimitInfo

    manager = _manager()
    _feed(manager, [_init(), RateLimitEvent(
        rate_limit_info=RateLimitInfo(status="allowed", resets_at=1, rate_limit_type="five_hour"),
        uuid="u", session_id="a16dd0d0")])
    with pytest.raises(ClaudeSessionError, match="five_hour usage limit is spent"):
        _feed(manager, [RateLimitEvent(
            rate_limit_info=RateLimitInfo(status="rejected", resets_at=2,
                                          rate_limit_type="five_hour"),
            uuid="u", session_id="a16dd0d0")])
    assert [state["status"] for state in manager.session_record["rate_limits"]] == [
        "allowed", "rejected"]


@pytest.mark.parametrize("fields,named", [
    ({"error": "rate_limit"}, "rate_limit"),
    ({"error": "authentication_failed"}, "authentication_failed"),
    ({"model": "claude-sonnet-5-5"}, "fell back"),
    ({"stop_reason": "refusal"}, "safety refusal"),
])
def test_a_reply_the_attempt_cannot_be_read_through_fails_it(fields, named):
    from claude_agent_sdk import AssistantMessage, TextBlock

    message = AssistantMessage(**{"content": [TextBlock(text="")], "model": "claude-opus-5-5",
                                  **fields})
    with pytest.raises(ClaudeSessionError, match=named):
        _feed(_manager(), [_init(), message])


def test_a_subagents_reply_may_come_from_another_model():
    from claude_agent_sdk import AssistantMessage, TextBlock

    _feed(_manager(), [_init(), AssistantMessage(
        content=[TextBlock(text="")], model="claude-haiku-4-5", parent_tool_use_id="t")])


def test_an_error_result_fails_the_attempt_though_its_subtype_says_success():
    """The bundled 2.1.139 CLI answered claude-opus-5-5 with exactly this: subtype
    "success", is_error true, status 400, "does not support this model"."""

    with pytest.raises(ClaudeSessionError, match="API status 400"):
        _feed(_manager(), [_init(), _result(
            is_error=True, api_error_status=400, model_usage={},
            result="API Error: 400 Claude Code 2.1.139 does not support this model")])


def test_the_clis_turn_limit_is_a_turn_limit():
    with pytest.raises(MaxTurnsReachedError):
        _feed(_manager(), [_init(), _result(is_error=True, subtype="error_max_turns")])


def test_every_result_is_recorded_with_its_notional_cost():
    manager = _manager()
    _feed(manager, [_init(), *FIRST, *SECOND, _result()])
    (result,) = manager.session_record["results"]
    assert result["notional_cost_usd"] == 0.0485
    assert manager.session_record["init"]["model"] == "claude-opus-5-5"


def test_the_relay_route_reads_no_sdk_message():
    from ape.scaffolds.claude_code.conversation import ClaudeCodeConversationManager

    source = inspect.getsource(ClaudeCodeConversationManager._execute_turn)
    assert "self._relay_session is None and self.config.subscription_route" in source


# --- the plan and the preflight --------------------------------------------------------------


def test_the_plan_names_the_claude_model_and_counts_it_free():
    from src.mathlib_review.review.runner import _model_is_free, _plan_model_name

    assert _plan_model_name(_config()) == "claude-opus-5-5"
    assert _model_is_free(_config())
    relay = ClaudeCodeConfig(llm_config=LLMConfig(model_name="gpt_5.2"))
    assert _plan_model_name(relay) == "gpt_5.2"
    assert not _model_is_free(relay)


def test_the_preflight_refuses_a_subscription_run_with_no_login(monkeypatch):
    from src.mathlib_review.review.preflight import _check_model_credential

    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    unmet = _check_model_credential(_config())
    assert unmet is not None and "claude setup-token" in unmet.remedy
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "sk-ant-oat01-test")
    assert _check_model_credential(_config()) is None


def test_a_near_limit_warning_is_logged_once_per_state(caplog):
    from claude_agent_sdk import RateLimitEvent
    from claude_agent_sdk.types import RateLimitInfo

    def event(status):
        return RateLimitEvent(rate_limit_info=RateLimitInfo(
            status=status, resets_at=1, rate_limit_type="five_hour"), uuid="u", session_id="s")

    manager = _manager()
    with caplog.at_level(logging.WARNING):
        _feed(manager, [_init(), event("allowed_warning"), event("allowed_warning"),
                        event("allowed_warning")])
    assert sum("near its five_hour limit" in r.message for r in caplog.records) == 1
    assert [s["status"] for s in manager.session_record["rate_limits"]] == ["allowed_warning"]
