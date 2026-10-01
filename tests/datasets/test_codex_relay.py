"""The Codex relay speaks the Responses API the installed CLI (`codex-cli` 0.144.5) sends.

The request shapes are the ones captured from that CLI against a local recording server
(2026-10-01, no model): MCP tools inside a `namespace`, reasoning items returned without their
`id`, developer messages, a streamed answer. End to end, the CLI ran an MCP tool through this relay
with only the model call faked, and the turn's carried reasoning came back intact.
"""

from __future__ import annotations

import json

import pytest


@pytest.fixture()
def relay():
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.codex.relay import CodexRelaySession

    return CodexRelaySession(port=41010, llm_config=LLMConfig(model_name="gpt_5.2"))


CODEX_TOOLS = [
    {"type": "function", "name": "update_plan", "description": "plan", "parameters": {"type": "object"}},
    {"type": "custom", "name": "apply_patch", "description": "edit", "format": {}},
    {"type": "namespace", "name": "mcp__core", "description": "Tools in the mcp__core namespace.",
     "tools": [{"type": "function", "name": "submit_findings", "description": "submit",
                "parameters": {"type": "object", "properties": {}}}]},
]


def test_namespace_tools_are_flattened_and_answered_namespaced(relay):
    """Codex executes a namespaced call only as `{name, namespace}`; the flat name is refused."""

    from ape.llm_clients.models import ContentBlock, ConversationSession, TokenUsage

    tools = relay._backend_tools(CODEX_TOOLS)
    assert [t["function"]["name"] for t in tools] == ["update_plan", "mcp__core__submit_findings"]

    out = ConversationSession()
    out.add_assistant_message([ContentBlock.tool_use_block("call_1", "mcp__core__submit_findings", {"findings": []})], "/w")
    response = relay._nodes_to_response(out.nodes, TokenUsage(input_tokens=10, output_tokens=2), "gpt-5.2")
    (item,) = response["output"]
    assert (item["type"], item["name"], item["namespace"], item["call_id"]) == (
        "function_call", "submit_findings", "mcp__core", "call_1")
    assert json.loads(item["arguments"]) == {"findings": []}


def test_carried_reasoning_round_trips_with_its_id_restored(relay):
    """The backend's reasoning goes out as a reasoning item; Codex returns it without the id, and
    the turn is rebuilt with the signature `openai_provider` carries."""

    from ape.llm_clients.models import ContentBlock, ConversationSession, TokenUsage

    relay._backend_tools(CODEX_TOOLS)
    out = ConversationSession()
    node = out.add_assistant_message([ContentBlock.tool_use_block("call_1", "mcp__core__submit_findings", {})], "/w")
    node.message.signature = json.dumps({"responses_output": [
        {"type": "reasoning", "id": "rs_1", "encrypted_content": "ENC", "summary": []},
        {"type": "function_call", "call_id": "call_1"}]})
    sent = relay._nodes_to_response(out.nodes, TokenUsage(), "gpt-5.2")["output"]
    assert [i["type"] for i in sent] == ["reasoning", "function_call"]

    returned = {"instructions": "You are Codex.", "input": [
        {"type": "message", "role": "developer", "content": [{"type": "input_text", "text": "read-only"}]},
        {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Review PR 1."}]},
        {**{k: v for k, v in sent[0].items() if k != "id"}},
        {k: v for k, v in sent[1].items() if k not in ("id", "status")},
        {"type": "function_call_output", "call_id": "call_1", "output": "Wall time: 0s\nOutput:\nok"}]}
    session = relay._responses_to_session(returned, relay._backend_tools(CODEX_TOOLS))
    system = session.nodes[0]
    assert system.type == "system"
    assert system.message.content[0].text == "You are Codex.\n\nread-only", (
        "the instructions survive the developer message: a second system message replaces the first")
    (assistant,) = [n for n in session.nodes if n.type == "assistant"]
    carried = json.loads(assistant.message.signature)["responses_output"]
    assert carried[0] == {"type": "reasoning", "encrypted_content": "ENC", "summary": [], "id": "rs_1"}
    assert [b.name for b in assistant.message.content] == ["mcp__core__submit_findings"]


def test_a_late_developer_message_keeps_its_place(relay):
    session = relay._responses_to_session({"instructions": "I", "input": [
        {"type": "message", "role": "user", "content": "Review."},
        {"type": "message", "role": "developer", "content": "Context changed."}]}, [])
    texts = [(n.type, n.message.content[0].text) for n in session.nodes]
    assert texts == [("system", "I"), ("user", "Review."), ("user", "Context changed.")]


def test_a_reasoning_item_with_nothing_after_it_is_not_sent(relay):
    session = relay._responses_to_session({"input": [
        {"type": "message", "role": "user", "content": "Review."},
        {"type": "reasoning", "summary": [], "encrypted_content": "ENC"}]}, [])
    assert not [n for n in session.nodes if n.type == "assistant"]


def test_the_answer_is_a_responses_event_stream(relay):
    from ape.llm_clients.models import ContentBlock, ConversationSession, TokenUsage
    from ape.scaffolds.codex.relay import response_event_stream

    out = ConversationSession()
    out.add_assistant_message([ContentBlock.text_block("No findings.")], "/w")
    response = relay._nodes_to_response(out.nodes, TokenUsage(input_tokens=5, output_tokens=1,
                                                               cache_read_input_tokens=3), "gpt-5.2")
    events = [json.loads(chunk.split("\ndata: ", 1)[1]) for chunk in
              response_event_stream(response).strip().split("\n\n")]
    assert [e["type"] for e in events] == ["response.created", "response.output_item.added",
                                           "response.output_item.done", "response.completed"]
    done = events[-1]["response"]
    assert done["output"][0]["content"][0]["text"] == "No findings."
    assert done["usage"]["input_tokens_details"]["cached_tokens"] == 3


def test_only_the_responses_route_is_served():
    """codex-cli 0.144 refuses `wire_api = "chat"`, so the chat route that used to be here is gone."""

    from ape.scaffolds.codex.relay import CodexRelaySession

    from ape.llm_clients.config import LLMConfig

    from fastapi import FastAPI

    relay = CodexRelaySession(port=41011, llm_config=LLMConfig(model_name="gpt_5.2"))
    relay._app = FastAPI()  # built by start(); the routes are what is under test
    relay._setup_routes()
    paths = {route.path for route in relay._app.routes if hasattr(route, "path")}
    assert {"/responses", "/v1/responses"} <= paths
    assert "/chat/completions" not in paths
