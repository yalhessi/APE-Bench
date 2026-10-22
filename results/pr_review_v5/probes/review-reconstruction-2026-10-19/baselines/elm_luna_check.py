"""Live check of a Responses route through the run's own client: two turns, a function tool at high
effort, the encrypted reasoning item carried back, a streamed second turn, and the prompt cache.

The same properties the 2026-10-05 measurement wrote down for the ELM gpt-5.x rows
(`src/ape/llm_clients/config.py`, above `elm_gpt_5.2`). Costs well under a penny at Luna's rates.

Usage (worktree root, ELM_API_KEY exported): ape/bin/python <this file> [model, default elm_gpt_6_luna]
Records the raw HTTP responses (the final `response.completed` of a stream).
Writes elm_luna_check.json beside this file; prints a summary. No key or reasoning text is written.
"""

import asyncio
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[4]))

from ape.llm_clients.client import LLMClient  # noqa: E402
from ape.llm_clients.config import LLMConfig  # noqa: E402
from ape.llm_clients.models import ContentBlock, ConversationSession  # noqa: E402

TOOL = {"type": "function", "function": {
    "name": "get_weather", "description": "Weather for a city",
    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}
# A long fixed prefix, so the second turn can show a cache hit (OpenAI caches from 1,024 tokens).
SYSTEM = "You are terse. Use tools when asked. " + " ".join(
    f"Rule {i}: answer weather questions in one sentence and name the city." for i in range(120))


# A trivial prompt drew 0 reasoning tokens at effort high (2026-10-20), leaving nothing to carry.
PROMPT = ("Let n be the number of primes p < 60 for which p + 2 is also prime. Of the cities "
          "Rome, Paris, Lisbon, Bologna, Valletta, Edinburgh, Amsterdam, Copenhagen, pick the one whose name has "
          "exactly n letters, then call the tool for its weather. State n in your final answer.")


def summarise(raw):
    out = raw.get("output") or []
    usage = raw.get("usage") or {}
    return {"model": raw.get("model"), "status": raw.get("status"),
            "items": [o.get("type") for o in out],
            "reasoning_encrypted": any(o.get("type") == "reasoning" and o.get("encrypted_content") for o in out),
            "reasoning_summary": any(o.get("type") == "reasoning" and o.get("summary") for o in out),
            "phases": [o.get("phase") for o in out if o.get("type") == "message"],
            "usage": {"input": usage.get("input_tokens"),
                      "cached": (usage.get("input_tokens_details") or {}).get("cached_tokens"),
                      "output": usage.get("output_tokens"),
                      "reasoning": (usage.get("output_tokens_details") or {}).get("reasoning_tokens")}}


async def main(model):
    cfg = LLMConfig(model_name=model, reasoning_effort="high", openai_api="responses",
                    openai_responses_reasoning_carryover=True, retry_max_attempts=1)
    sent, received = [], []
    client = LLMClient(cfg, enable_raw_logging=False)
    await client.provider.initialize()

    async def record(request):
        sent.append(json.loads(request.content))

    async def answer(response):
        body = (await response.aread()).decode()
        if body.lstrip().startswith("{"):
            received.append(json.loads(body))
        else:  # a stream: keep the final `response.completed` event's response
            done = [json.loads(line[5:]) for line in body.split("\n")
                    if line.startswith("data:") and '"response.completed"' in line]
            received.append(done[-1]["response"] if done else {"stream_without_completed": True})
    client.provider._session.event_hooks["request"].append(record)
    client.provider._session.event_hooks["response"].append(answer)

    session = ConversationSession(session_id="elm-luna-check")
    session.add_system_message([ContentBlock.text_block(SYSTEM)], cwd="/")
    session.add_user_message([ContentBlock.text_block(PROMPT)], cwd="/")
    report = {"model": model, "provider_model_name": cfg.formal_model_name if hasattr(cfg, "formal_model_name") else None}
    try:
        nodes, usage1, raw1 = await client.call_api(session, tools=[TOOL], streaming=False)
        report["turn1"] = summarise(received[-1])
        calls = [b for n in nodes for b in n.message.content if b.type == "tool_use"]
        report["turn1"]["tool_calls"] = [{"name": b.name, "input": b.input} for b in calls]
        session.nodes.extend(nodes)
        for b in calls:
            session.add_tool_result(b.id, f"{b.input.get('city')}: 14 C, light rain.", cwd="/")
        nodes2, usage2, raw2 = await client.call_api(session, tools=[TOOL], streaming=True)
        report["turn2"] = summarise(received[-1])
        report["turn2"]["text"] = " ".join(b.text for n in nodes2 for b in n.message.content
                                           if b.type == "text")[:300]
        second = sent[-1]
        report["turn2_request"] = {
            "input_items": [i.get("type", i.get("role")) for i in second["input"]],
            "reasoning_item_sent_with_encrypted_content": any(
                i.get("type") == "reasoning" and i.get("encrypted_content") for i in second["input"]),
            "store": second.get("store"), "include": second.get("include"),
            "echoed_reasoning_config": received[-1].get("reasoning"),
            "reasoning": second.get("reasoning"), "stream": second.get("stream")}
    finally:
        await client.close()
    return report


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "elm_gpt_6_luna"
    report = asyncio.run(main(model))
    (HERE / "elm_luna_check.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps(report, indent=1, sort_keys=True))
