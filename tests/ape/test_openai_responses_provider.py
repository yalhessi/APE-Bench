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


def test_carryover_sends_no_reasoning_context():
    """`current_turn`, the default, already keeps every carried item in an unbroken tool loop, as
    a review session is. gpt-5.2 answers `all_turns` with a 400 ("Supported values are: 'auto' and
    'current_turn'"), so sending it would refuse the gpt_5.2 carry-over condition."""

    payload = payload_for(config(reasoning_effort="high", openai_responses_reasoning_carryover=True),
                          session_with(user("x")))
    assert payload["reasoning"] == {"effort": "high"}


# --- message phase -----------------------------------------------------------------------

@pytest.mark.parametrize("carryover", [False, True])
def test_a_commentary_phase_goes_back_on_the_replayed_text(carryover):
    """gpt-5.5's recorded preamble before a tool call. Replayed without its phase, it reads to the
    model as a final answer (OpenAI's reasoning guide); 111 were sent back that way through the
    Codex relay on 2026-10-01."""

    cfg = config("gpt_5.5", reasoning_effort="low", openai_responses_reasoning_carryover=carryover)
    (nodes, _, _), _ = call_api(
        cfg, sse_answer((FIXTURES / "responses_gpt55_stream_text_and_tool_call.sse").read_text()),
        stream=True)

    session = session_with(user("Weather in Paris?"))
    session.nodes.extend(nodes)
    session.add_tool_result(nodes[0].message.content[1].id, "sunny", cwd="/")
    items = payload_for(cfg, session)["input"]

    assert [item.get("type", item.get("role")) for item in items] == [
        "user", "assistant", "function_call", "function_call_output"]
    assert items[1] == {"role": "assistant", "content": "I'll check Paris weather now.",
                        "phase": "commentary"}


def test_a_final_answer_keeps_its_phase():
    message = responses_to_chat_completion(
        fixture("responses_gpt54_high_turn2_text.json"), carryover=False)["choices"][0]["message"]
    _, (item,) = responses_input([message], carryover=False)
    assert (item["role"], item["phase"]) == ("assistant", "final_answer")


def test_a_turn_with_no_phase_and_no_carryover_records_nothing():
    """So a request from a run that never saw a phase is what it was before: gpt-5.2 sets none,
    and the gpt-5.4 and gpt-5.5 APE-Agent review sessions wrote no message to carry one."""

    calls = responses_to_chat_completion(
        fixture("responses_gpt54_high_two_tool_calls.json"), carryover=False)["choices"][0]["message"]
    assert "signature" not in calls

    plain = {"output": [{"type": "message", "role": "assistant",
                         "content": [{"type": "output_text", "text": "hello"}]}],
             "status": "completed"}
    message = responses_to_chat_completion(plain, carryover=False)["choices"][0]["message"]
    assert "signature" not in message
    assert responses_input([message], carryover=False)[1] == [{"role": "assistant", "content": "hello"}]


def test_carryover_off_keeps_the_phase_and_no_reasoning():
    output = [{"type": "reasoning", "id": "rs_1", "encrypted_content": "e1", "summary": []},
              {"type": "message", "role": "assistant", "phase": "commentary",
               "content": [{"type": "output_text", "text": "Checking."}]},
              {"type": "function_call", "call_id": "c1", "name": "f", "arguments": "{}"}]
    response = {"output": output, "status": "completed"}

    recorded_off = responses_to_chat_completion(response, carryover=False)["choices"][0]["message"]
    assert json.loads(recorded_off["signature"])["responses_output"] == [
        {"type": "message", "phase": "commentary"}, {"type": "function_call", "call_id": "c1"}]

    recorded_on = responses_to_chat_completion(response, carryover=True)["choices"][0]["message"]
    for message in (recorded_off, recorded_on):
        _, items = responses_input([message], carryover=False)
        assert items == [{"role": "assistant", "content": "Checking.", "phase": "commentary"},
                         {"type": "function_call", "call_id": "c1", "name": "f", "arguments": "{}"}]
    _, items = responses_input([recorded_on], carryover=True)
    assert [item.get("type", item.get("phase")) for item in items] == [
        "reasoning", "commentary", "function_call"]


# --- reasoning summaries -----------------------------------------------------------------

def summarised(name, text="Paris first, then Rome; one call each."):
    """A recorded response with its reasoning item summarised, in the shape OpenAI's reasoning
    guide documents (`summary: [{"type": "summary_text", "text": ...}]`). Not recorded live: the
    key was refused on 2026-10-05, so the knob's first real call is still owed."""

    response = fixture(name)
    for item in response["output"]:
        if item["type"] == "reasoning":
            item["summary"] = [{"type": "summary_text", "text": text}]
    return response


def test_a_summary_is_asked_for_only_when_the_knob_is_set():
    session = session_with(user("x"))
    asked = config(reasoning_effort="high", openai_responses_reasoning_summary="auto")
    assert payload_for(asked, session)["reasoning"] == {"effort": "high", "summary": "auto"}
    assert payload_for(config(openai_responses_reasoning_summary="concise"),
                       session)["reasoning"] == {"summary": "concise"}
    assert payload_for(config(reasoning_effort="high"), session)["reasoning"] == {"effort": "high"}
    assert asked.model_dump(mode="json")["openai_responses_reasoning_summary"] == "auto", (
        "inside the provenance hash, as the endpoint and the carry-over are")

    with pytest.raises(ConfigurationError, match="needs openai_api: responses"):
        LLMConfig(model_name="gpt_5.4", openai_responses_reasoning_summary="auto")


@pytest.mark.parametrize("carryover", [False, True])
def test_a_summary_is_kept_as_the_turns_thinking_block_and_only_the_item_goes_back(carryover):
    """Where a transcript can be read. Until this knob, all 1,998 reasoning items in the gpt-5.4
    and gpt-5.5 review sessions came back with `summary: []`."""

    cfg = config(reasoning_effort="high", openai_responses_reasoning_carryover=carryover,
                 openai_responses_reasoning_summary="auto")
    (nodes, _, _), _ = call_api(cfg, json_answer(summarised("responses_gpt54_high_two_tool_calls.json")))
    blocks = nodes[0].message.content
    assert [b.type for b in blocks] == ["thinking", "tool_use", "tool_use"]
    assert blocks[0].reasoning_content == "Paris first, then Rome; one call each."

    session = session_with(user("Weather in Paris and Rome?"))
    session.nodes.extend(nodes)
    for block in blocks[1:]:
        session.add_tool_result(block.id, "sunny", cwd="/")
    items = payload_for(cfg, session)["input"]
    kinds = [item.get("type", item.get("role")) for item in items]
    carried = ["reasoning"] if carryover else []
    assert kinds == ["user", *carried, "function_call", "function_call",
                     "function_call_output", "function_call_output"]
    if carryover:
        assert items[1]["summary"] == [{"type": "summary_text",
                                        "text": "Paris first, then Rome; one call each."}]
    assert all("reasoning_content" not in item for item in items)


def test_a_summarised_stream_keeps_its_thinking_block_too():
    stream = "event: response.completed\ndata: " + json.dumps({
        "type": "response.completed",
        "response": summarised("responses_gpt54_high_two_tool_calls.json")}) + "\n\n"
    (nodes, _, _), _ = call_api(config(openai_responses_reasoning_summary="auto"),
                                sse_answer(stream), stream=True)
    assert [b.type for b in nodes[0].message.content] == ["thinking", "tool_use", "tool_use"]


def test_a_reply_that_is_only_summarised_reasoning_is_still_an_empty_reply():
    """A summary alone must not turn a cut-off reply into a turn: the session would then replay a
    reasoning item with nothing after it, which the API refuses."""

    cut_off = summarised("responses_gpt54_high_incomplete.json")
    message = responses_to_chat_completion(cut_off, carryover=True)["choices"][0]["message"]
    assert "reasoning_content" not in message
    with pytest.raises(MalformedResponseError):
        call_api(config(reasoning_effort="high", openai_responses_reasoning_summary="auto"),
                 json_answer(cut_off))
