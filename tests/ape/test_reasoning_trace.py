"""The model's reasoning trace reaches the session record, whatever the wire calls it.

There is no single convention for the field. OpenAI does not return the text at all; DeepSeek
and older vLLM builds call it `reasoning_content`; the vLLM build behind the Edinburgh ELM
gateway calls it `reasoning`. This repo read only the first spelling, so on an ELM model with
reasoning on it kept the answer and dropped the thinking -- measured 2026-09-22, a 2,551
character trace and about 75% of the completion tokens, gone from the record, on a project
whose method is reading what the agent did (`cli trajectory`, the "replay its own queries"
rule, the abstention analysis).

Both transports are covered because they drop it by different mechanisms: the non-streaming
reader looked up one key, and the streaming merge matched one key in an if/elif chain where an
unmatched delta falls through to nothing (the `choice['message']` branch below it never fires
on a streaming chunk, which carries `delta`).
"""

from __future__ import annotations

import pytest

from ape.llm_clients.models import REASONING_KEYS, reasoning_text


def test_both_spellings_are_read():
    assert reasoning_text({"reasoning_content": "thought"}) == "thought"
    assert reasoning_text({"reasoning": "thought"}) == "thought"


def test_a_message_with_no_trace_reads_empty_rather_than_none():
    assert reasoning_text({"content": "answer"}) == ""
    assert reasoning_text({}) == ""


def test_an_empty_trace_is_not_mistaken_for_a_missing_one():
    """`reasoning: null` is what the gateway sends when reasoning is off, and it must not
    shadow the other spelling if both were ever present."""

    assert reasoning_text({"reasoning": None, "reasoning_content": "thought"}) == "thought"
    assert reasoning_text({"reasoning": "", "reasoning_content": "thought"}) == "thought"


def test_the_key_list_is_ordered_and_not_empty():
    assert REASONING_KEYS and REASONING_KEYS[0] == "reasoning_content"


# --- non-streaming -------------------------------------------------------------------------


def _node(message_data):
    from ape.llm_clients.adapters.response_processor import parse_message_to_node
    from ape.llm_clients.models import TokenUsage

    return parse_message_to_node(
        message_data=message_data, session_id="s", cwd=".", usage=TokenUsage())


@pytest.mark.parametrize("key", REASONING_KEYS)
def test_a_trace_becomes_a_thinking_block(key):
    node = _node({"role": "assistant", key: "step one, step two", "content": "391"})
    kinds = [block.type for block in node.message.content]

    assert kinds == ["thinking", "text"], kinds
    assert node.message.content[0].reasoning_content == "step one, step two"


def test_an_answer_with_no_trace_is_just_text():
    node = _node({"role": "assistant", "content": "391"})
    assert [block.type for block in node.message.content] == ["text"]


# --- streaming -----------------------------------------------------------------------------


def _merge(deltas):
    """Merge real SSE bytes through the real processor.

    A hand-built merge would be free to disagree with the class it stands in for -- the
    failure this file exists for was an if/elif chain, and only the real chain can show it.
    """

    import asyncio
    import json

    from ape.llm_clients.adapters.streaming_processor import StreamingProcessor

    lines = [
        f"data: {json.dumps({'choices': [{'index': 0, 'delta': delta}]})}"
        for delta in deltas
    ] + ["data: [DONE]"]

    class _Stream:
        """The one method `_parse_sse_stream` calls on the response."""

        async def aiter_lines(self):
            for line in lines:
                yield line

    async def run():
        merged, _finish = await StreamingProcessor()._merge_sse_chunks(
            _Stream(), callback=None, relay_mode=False, interrupt_event=None)
        return merged

    return asyncio.run(run())


@pytest.mark.parametrize("key", REASONING_KEYS)
def test_a_streamed_trace_is_accumulated_onto_one_key(key):
    """Normalised at the boundary: everything downstream reads `reasoning_content`, so a
    second spelling must not survive past the merge as a second field."""

    merged = _merge([
        {"role": "assistant"},
        {key: "step one, "},
        {key: "step two"},
        {"content": "391"},
    ])
    message = merged["choices"][0]["message"]

    assert message["reasoning_content"] == "step one, step two"
    assert message.get("content") == "391"
    assert "reasoning" not in message, "the wire spelling must not leak past the merge"


def test_a_streamed_answer_with_no_trace_carries_no_reasoning():
    merged = _merge([{"role": "assistant"}, {"content": "391"}])
    assert not merged["choices"][0]["message"].get("reasoning_content")
