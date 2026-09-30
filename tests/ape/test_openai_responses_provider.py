"""The Responses-API provider: routing, the request translation and the response translation.

Every response under `fixtures/openai/` was recorded from the live endpoint on 2026-09-30:
gpt-5.4 at high effort making two parallel tool calls, its second turn answering in text, a
high-effort reply cut off by `max_output_tokens`, and a gpt-5.5 stream with text and a call.
The request shapes asserted here are the ones those probes sent and the API accepted --
including the carry-over second turn, which returned 200 with the reasoning item before the
calls.

The client-level tests run the real `LLMClient` over an `httpx.MockTransport`, so the
formatter, the processors, `parse_usage` and `_calculate_cost` are all the production path.
"""

import asyncio
import json
import os
from pathlib import Path
from unittest import mock

import httpx
import pytest

from ape.llm_clients.adapters import MessageFormatter, OpenAIMessageFormatter
from ape.llm_clients.client import LLMClient
from ape.llm_clients.config import (
    ConfigurationError, LLMConfig, MalformedResponseError, ProviderError)
from ape.llm_clients.models import ContentBlock, ConversationSession
from ape.llm_clients.providers import OpenAIProvider, OpenAIResponsesProvider
from ape.llm_clients.providers.openai_provider import (
    responses_input, responses_to_chat_completion)

FIXTURES = Path(__file__).parent / "fixtures" / "openai"
TOOL = {"type": "function", "function": {
    "name": "get_weather", "description": "Weather for a city",
    "parameters": {"type": "object", "properties": {"city": {"type": "string"}},
                   "required": ["city"]}}}


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(autouse=True)
def keys():
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
        yield


def config(model="gpt_5.4", **overrides):
    overrides.setdefault("openai_api", "responses")
    return LLMConfig(model_name=model, retry_max_attempts=1, **overrides)


def session_with(*nodes):
    """A session built the way the client builds one."""

    session = ConversationSession(session_id="responses-test")
    for role, blocks in nodes:
        {"system": session.add_system_message, "user": session.add_user_message,
         "assistant": session.add_assistant_message}[role](blocks, cwd="/")
    return session


def user(text):
    return ("user", [ContentBlock.text_block(text)])


def call_api(cfg, answer, session=None, *, stream=False):
    """One `call_api` over a transport answering with `answer(request) -> httpx.Response`."""

    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return answer(request)

    async def go():
        client = LLMClient(cfg, enable_raw_logging=False)
        client.provider._session = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            return await client.call_api(session or session_with(user("Weather in Paris?")),
                                         tools=[TOOL], streaming=stream)
        finally:
            await client.close()

    return asyncio.run(go()), requests


def json_answer(body):
    return lambda request: httpx.Response(200, json=body)


def sse_answer(text):
    return lambda request: httpx.Response(
        200, content=text.encode(), headers={"content-type": "text/event-stream"})


# --- routing and config ------------------------------------------------------------------

def test_responses_is_opt_in_and_chat_completions_is_untouched():
    default = LLMClient(LLMConfig(model_name="gpt_5.4"), enable_raw_logging=False)
    assert type(default.provider) is OpenAIProvider
    assert type(default.message_formatter) is OpenAIMessageFormatter

    chosen = LLMClient(config(), enable_raw_logging=False)
    assert type(chosen.provider) is OpenAIResponsesProvider
    assert type(chosen.message_formatter) is MessageFormatter
    url, headers = chosen.provider.get_request_info("s")
    assert url == "https://api.openai.com/v1/responses"
    assert headers["Authorization"] == "Bearer sk-test"


def test_responses_is_refused_for_a_gateway_model():
    with pytest.raises(ConfigurationError, match="direct OpenAI models"):
        LLMConfig(model_name="elm_gpt_5.4", openai_api="responses")


def test_carryover_is_refused_without_responses():
    with pytest.raises(ConfigurationError, match="needs openai_api: responses"):
        LLMConfig(model_name="gpt_5.4", openai_responses_reasoning_carryover=True)


def test_both_fields_are_inside_the_provenance_hash():
    """`scaffold_config_sha256` hashes the llm_config dump; a run must say which endpoint and
    which carry-over produced it."""

    dumped = config(openai_responses_reasoning_carryover=True).model_dump(mode="json")
    assert dumped["openai_api"] == "responses"
    assert dumped["openai_responses_reasoning_carryover"] is True


# --- the request -------------------------------------------------------------------------

def payload_for(cfg, session, tools=(TOOL,)):
    client = LLMClient(cfg, enable_raw_logging=False)
    messages = client.message_formatter.format_for_api(session)
    return client.provider.build_request_payload(messages, tools=list(tools))


def test_the_payload_is_what_the_probes_sent():
    payload = payload_for(config(reasoning_effort="high", max_tokens=4000),
                          session_with(("system", [ContentBlock.text_block("You are terse.")]),
                                       user("Weather in Paris?")))

    assert payload["model"] == "gpt-5.4"
    assert payload["instructions"] == "You are terse."
    assert payload["input"] == [{"role": "user", "content": "Weather in Paris?"}]
    assert payload["reasoning"] == {"effort": "high"}
    assert payload["max_output_tokens"] == 4000
    assert payload["store"] is False
    assert payload["temperature"] == 1.0
    assert "include" not in payload, "encrypted reasoning is requested only to carry it"
    assert "messages" not in payload and "max_completion_tokens" not in payload


def test_a_tool_is_flattened_and_never_made_strict():
    """Responses made a qualifying probe tool strict by default (constrained decoding);
    Chat Completions never does."""

    (tool,) = payload_for(config(), session_with(user("x")))["tools"]
    assert tool == {"type": "function", "name": "get_weather",
                    "description": "Weather for a city",
                    "parameters": TOOL["function"]["parameters"], "strict": False}


def test_no_effort_sends_no_reasoning_block():
    assert "reasoning" not in payload_for(config(), session_with(user("x")))


def test_a_tool_conversation_becomes_function_call_items():
    session = session_with(
        ("system", [ContentBlock.text_block("sys")]),
        user("Weather in Paris and Rome?"),
        ("assistant", [ContentBlock.text_block("Checking."),
                       ContentBlock.tool_use_block("call_a", "get_weather", {"city": "Paris"}),
                       ContentBlock.tool_use_block("call_b", "get_weather", {"city": "Rome"})]))
    session.add_tool_result("call_a", "sunny, 21C", cwd="/", tool_name="get_weather")
    session.add_tool_result("call_b", "rain, 15C", cwd="/", tool_name="get_weather")
    session.add_assistant_message([ContentBlock.text_block("Paris sunny, Rome rain.")], cwd="/")
    session.add_user_message([ContentBlock.text_block("Thanks.")], cwd="/")

    payload = payload_for(config(), session)

    assert payload["instructions"] == "sys"
    assert payload["input"] == [
        {"role": "user", "content": "Weather in Paris and Rome?"},
        {"role": "assistant", "content": "Checking."},
        {"type": "function_call", "call_id": "call_a", "name": "get_weather",
         "arguments": '{"city": "Paris"}'},
        {"type": "function_call", "call_id": "call_b", "name": "get_weather",
         "arguments": '{"city": "Rome"}'},
        {"type": "function_call_output", "call_id": "call_a", "output": "sunny, 21C"},
        {"type": "function_call_output", "call_id": "call_b", "output": "rain, 15C"},
        {"role": "assistant", "content": "Paris sunny, Rome rain."},
        {"role": "user", "content": "Thanks."},
    ]


def test_a_system_message_after_the_start_stays_in_place():
    instructions, items = responses_input(
        [{"role": "system", "content": "a"}, {"role": "user", "content": "u"},
         {"role": "system", "content": "b"}], carryover=False)
    assert instructions == "a"
    assert items == [{"role": "user", "content": "u"}, {"role": "system", "content": "b"}]


# --- the response ------------------------------------------------------------------------

def test_two_parallel_tool_calls_become_tool_use_blocks():
    (nodes, usage, _), _ = call_api(
        config(reasoning_effort="high"),
        json_answer(fixture("responses_gpt54_high_two_tool_calls.json")))

    (node,) = nodes
    calls = [b for b in node.message.content if b.type == "tool_use"]
    assert [(c.id, c.name, c.input) for c in calls] == [
        ("call_Ek1Doh5KKLDdXRhpTKxrGAGy", "get_weather", {"city": "Paris"}),
        ("call_gbeTsKnFM1upcOVOjzcKt2pZ", "get_weather", {"city": "Rome"})]
    assert node.message.signature is None, "carry-over is off: nothing rides to the next turn"


def test_usage_and_cost_read_as_chat_completions_would():
    """62 input, 127 output of which 77 reasoning, at gpt_5.4's $2.50 / $15.00 per 1M."""

    (_, usage, _), _ = call_api(
        config(reasoning_effort="high"),
        json_answer(fixture("responses_gpt54_high_two_tool_calls.json")))

    assert (usage.input_tokens, usage.output_tokens, usage.total_tokens) == (62, 127, 189)
    assert usage.reasoning_tokens == 77
    assert usage.cached_total_cost == pytest.approx(62 * 2.50e-6 + 127 * 15.00e-6)


def test_a_text_answer_becomes_a_text_block():
    (nodes, _, _), _ = call_api(config(reasoning_effort="high"),
                                json_answer(fixture("responses_gpt54_high_turn2_text.json")))

    (block,) = nodes[0].message.content
    assert block.type == "text" and block.text.startswith("Paris: sunny, 21C")


def test_a_reply_cut_off_before_any_output_is_malformed_as_on_chat_completions():
    """All 64 output tokens went to reasoning. Chat Completions returns an empty message with
    finish_reason length, which the processor already treats as malformed."""

    completion = responses_to_chat_completion(
        fixture("responses_gpt54_high_incomplete.json"), carryover=False)
    assert completion["choices"][0]["finish_reason"] == "length"
    with pytest.raises(MalformedResponseError):
        call_api(config(reasoning_effort="high"),
                 json_answer(fixture("responses_gpt54_high_incomplete.json")))


def test_a_stream_keeps_only_its_completed_event():
    (nodes, usage, _), requests = call_api(
        config("gpt_5.5", reasoning_effort="low"),
        sse_answer((FIXTURES / "responses_gpt55_stream_text_and_tool_call.sse").read_text()),
        stream=True)

    assert requests[0]["stream"] is True
    kinds = [b.type for b in nodes[0].message.content]
    assert kinds == ["text", "tool_use"]
    assert nodes[0].message.content[1].input == {"city": "Paris"}
    assert (usage.input_tokens, usage.output_tokens) == (60, 31)


def test_a_failed_stream_raises():
    failed = ('event: response.failed\ndata: {"type":"response.failed","response":'
              '{"status":"failed","error":{"code":"server_error","message":"boom"}}}\n\n')
    with pytest.raises(ProviderError, match="boom"):
        call_api(config(), sse_answer(failed), stream=True)


def test_a_stream_that_never_completes_raises():
    truncated = 'event: response.created\ndata: {"type":"response.created","response":{}}\n\n'
    with pytest.raises(ProviderError, match="without a response.completed"):
        call_api(config(), sse_answer(truncated), stream=True)


# --- reasoning carry-over ----------------------------------------------------------------

def test_carryover_sends_the_reasoning_item_before_the_calls():
    """The exact second-turn input the live API accepted (HTTP 200, 2026-09-30)."""

    first = fixture("responses_gpt54_high_two_tool_calls.json")
    cfg = config(reasoning_effort="high", openai_responses_reasoning_carryover=True)
    (nodes, _, _), _ = call_api(cfg, json_answer(first))

    session = session_with(user("Weather in Paris and Rome?"))
    session.nodes.extend(nodes)
    for block in nodes[0].message.content:
        session.add_tool_result(block.id, f"weather for {block.input['city']}", cwd="/")
    payload = payload_for(cfg, session)

    reasoning = first["output"][0]
    assert payload["include"] == ["reasoning.encrypted_content"]
    assert [item.get("type", item.get("role")) for item in payload["input"]] == [
        "user", "reasoning", "function_call", "function_call",
        "function_call_output", "function_call_output"]
    assert payload["input"][1] == {"type": "reasoning", "id": reasoning["id"],
                                   "encrypted_content": reasoning["encrypted_content"],
                                   "summary": []}


def test_carryover_keeps_interleaved_reasoning_in_order():
    """The API refuses a reasoning item passed without the item that followed it."""

    output = [{"type": "reasoning", "id": "rs_1", "encrypted_content": "e1", "summary": []},
              {"type": "function_call", "call_id": "c1", "name": "f", "arguments": "{}"},
              {"type": "reasoning", "id": "rs_2", "encrypted_content": "e2", "summary": []},
              {"type": "function_call", "call_id": "c2", "name": "f", "arguments": "{}"}]
    message = responses_to_chat_completion({"output": output, "status": "completed"},
                                           carryover=True)["choices"][0]["message"]
    _, items = responses_input([message], carryover=True)
    assert [item.get("id") or item.get("call_id") for item in items] == ["rs_1", "c1", "rs_2", "c2"]


def test_carryover_off_sends_no_reasoning_even_if_a_signature_exists():
    message = responses_to_chat_completion(
        fixture("responses_gpt54_high_two_tool_calls.json"), carryover=True)["choices"][0]["message"]
    _, items = responses_input([message], carryover=False)
    assert [item["type"] for item in items] == ["function_call", "function_call"]
