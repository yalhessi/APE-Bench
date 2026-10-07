"""Does the server put an earlier assistant turn's thinking back in the prompt?

The APE client sends it as `reasoning_content` (local provider, since 5fd560ab). One tool round, sent
twice: without the field and with ~1k tokens of thinking in it. Pass = the prompt grows by >= 500
tokens. On 2026-10-07 it grew 355 -> 1,375 under `reasoning_content` and under `reasoning` alike.
usage: python probe_carry.py <base_url> <model>     exit 0 = pass
"""
import json
import sys

from common import chat

BASE, MODEL = sys.argv[1], sys.argv[2]
THINK = " ".join(f"step {i}: the sum of two and three is five, checked by counting." for i in range(60))
TOOLS = [{"type": "function", "function": {"name": "calc", "description": "Evaluate an arithmetic expression",
          "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}, "required": ["expr"]}}}]


def prompt_tokens(with_thinking: bool) -> int:
    asst = {"role": "assistant", "content": "", "tool_calls": [{"id": "call_1", "type": "function",
            "function": {"name": "calc", "arguments": json.dumps({"expr": "2+3"})}}]}
    if with_thinking:
        asst["reasoning_content"] = THINK
    msgs = [{"role": "system", "content": "You are a careful assistant."},
            {"role": "user", "content": "What is 2+3? Use the calc tool."}, asst,
            {"role": "tool", "tool_call_id": "call_1", "content": "5"}]
    _, r = chat(BASE, {"model": MODEL, "messages": msgs, "tools": TOOLS, "max_tokens": 1,
                       "reasoning_effort": "high"})
    return r["usage"]["prompt_tokens"]


without, with_ = prompt_tokens(False), prompt_tokens(True)
ok = with_ - without >= 500
print(f"thinking carried: prompt {without} without, {with_} with reasoning_content: {'ok' if ok else 'NOT CARRIED'}")
sys.exit(0 if ok else 1)
