"""What one `run_claude_batch.sh` stream says: who ran, what each reviewer cost, and the window.

Per reviewer subagent: whether it was handed its prompt verbatim, its model, replies, tool calls and
processed tokens (prompt + completion, cache-inclusive, one count per assistant message id). The
five-hour window's utilisation is read from the stream's first and last `rate_limit_event`, which
gives processed tokens per point of the window.

usage: python3 <this file> <batch>.jsonl [<batch>.prompt]
"""
import json
import re
import sys
from collections import Counter

stream = sys.argv[1]
expected = {}
if len(sys.argv) > 2:
    for m in re.finditer(r"description: (.+)\nprompt:\n<<<\n(.*?)\n>>>", open(sys.argv[2]).read(), flags=re.S):
        expected[m.group(1)] = m.group(2)

agents, usage, tools, models, limits, init, result = {}, {}, Counter(), {}, [], {}, {}
with open(stream, encoding="utf-8") as handle:
    for line in handle:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        kind, parent = d.get("type"), d.get("parent_tool_use_id")
        msg = d.get("message") or {}
        if kind == "system" and d.get("subtype") == "init":
            init = {k: d.get(k) for k in ("session_id", "model", "claude_code_version", "apiKeySource", "permissionMode")}
        elif kind == "rate_limit_event":
            info = d.get("rate_limit_info") or d
            window = (info.get("unifiedWindows") or {}).get("five_hour") or {}
            limits.append((info.get("status"), window.get("utilization"), (info.get("unifiedWindows") or {}).get("seven_day", {}).get("utilization")))
        elif kind == "assistant":
            for block in msg.get("content") or []:
                if block.get("type") != "tool_use":
                    continue
                if parent is None and block["name"] == "Agent":
                    agents[block["id"]] = block["input"]
                elif parent is not None:
                    tools[parent] += 1
            if msg.get("id"):
                usage.setdefault(parent, {})[msg["id"]] = msg.get("usage") or {}
                if parent is not None:
                    models[parent] = msg.get("model")
        elif kind == "result":
            result = {"subtype": d.get("subtype"), "is_error": d.get("is_error"), "text": str(d.get("result"))}


def processed(rows: dict) -> int:
    return sum((u.get(k) or 0) for u in rows.values()
               for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))


print("session:", init)
total = processed(usage.get(None, {}))
print(f"orchestrator: {len(usage.get(None, {}))} replies, {total / 1e6:.2f}M processed")
for tool_id, spec in agents.items():
    name = spec.get("description")
    verbatim = expected.get(name) == spec.get("prompt") if expected else None
    cost = processed(usage.get(tool_id, {}))
    total += cost
    print(f"{name}: subagent_type {spec.get('subagent_type')} | prompt verbatim {verbatim} | model {models.get(tool_id)} | "
          f"{len(usage.get(tool_id, {}))} replies, {tools[tool_id]} tool calls, {cost / 1e6:.2f}M processed")
seen = [u for _, u, _ in limits if u is not None]
if seen:
    used = seen[-1] - seen[0]
    print(f"five-hour window: {seen[0]:.2f} -> {seen[-1]:.2f} over {total / 1e6:.2f}M processed"
          + (f" = {total / 1e6 / (used * 100):.2f}M a point" if used > 0 else "") + f" | statuses {sorted({s for s, _, _ in limits})}"
          f" | seven-day {limits[0][2]} -> {limits[-1][2]}")
print("result:", result.get("subtype"), "| error", result.get("is_error"))
print(result.get("text", "")[:1200])
