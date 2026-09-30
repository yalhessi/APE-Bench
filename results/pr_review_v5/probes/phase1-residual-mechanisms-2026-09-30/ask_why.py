"""Replay each carried gpt_5.2 session (its encrypted reasoning included) on a PR with residual asks,
tools off, and ask about each ask it did not reach: noticed? concluded what? what was missing?

Usage, from the repo root, with OPENAI_API_KEY set:
    python results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30/ask_why.py OUT.json

The answers are the model's own account after the fact; the readers label from them and the
transcript together, never from the answers alone.

Known defect (2026-09-30, found after the readers had these files): with tools defined and
`tool_choice: none`, gpt-5.2 wrote tool calls as text instead of answering. 17 of 23 answers open
with pseudo tool-call JSON (`{"tool_uses": ...}`), one fabricates a tool result, and three are
unusable: val 29842 (no answer), post 43167 (garbled), post 42814 (3 of 4 answers before the
6,000-token cap). They were not regenerated, because both readers of a split must see the same
inputs. Next time: send no `tools` (function_call history items do not need them), say in the
question that tools are unavailable, and check each answer for its numbered items before use.
"""
import glob
import importlib.util
import json
import os
import sys

import httpx

sys.path.insert(0, "src")
from ape.llm_clients.providers.openai_provider import responses_input, responses_tool  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "coh", "results/pr_review_v5/probes/carryover-coherence-2026-09-30/coherence.py")
coh = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(coh)

POPULATION = "results/pr_review_v5/probes/phase0-carried-baseline-2026-09-30/phase1_population.json"
RUNS = {"post": "probe_postcutoff_gpt52_Grc_rep1", "val": "probe_val_small12_gpt52_Grc_rep1",
        "dev": "probe_dev_gpt52_Grc_rep1"}
MODEL = "gpt-5.2-2025-12-11"
CLASSES = ("nobody", "claude_only")


def messages_of(task):
    rows = [json.loads(l) for l in open(coh.last_conversation(task))]
    msgs, tools = [], None
    for r in rows:
        m = r.get("message") or {}
        if r["type"] == "tool_definitions":
            tools = m.get("tools"); continue
        blocks = m.get("content") or []
        if r["type"] == "system":
            msgs.append({"role": "system", "content": "".join(b.get("text") or "" for b in blocks)})
        elif r["type"] == "assistant":
            calls = [{"id": b["id"], "type": "function",
                      "function": {"name": b["name"], "arguments": json.dumps(b.get("input") or {}, ensure_ascii=False)}}
                     for b in blocks if b.get("type") == "tool_use"]
            msg = {"role": "assistant", "content": "".join(b.get("text") or "" for b in blocks if b.get("type") == "text") or None}
            if calls: msg["tool_calls"] = calls
            if m.get("signature"): msg["signature"] = m["signature"]
            msgs.append(msg)
        elif r["type"] == "user":
            for b in blocks:
                if b.get("type") == "tool_result":
                    msgs.append({"role": "tool", "tool_call_id": b.get("tool_use_id"), "content": b.get("result_content") or ""})
                elif b.get("type") == "text":
                    msgs.append({"role": "user", "content": b.get("text") or ""})
    answered = {m["tool_call_id"] for m in msgs if m["role"] == "tool"}
    for m in [m for m in msgs if m["role"] == "assistant"]:
        for c in m.get("tool_calls") or []:
            if c["id"] not in answered:  # the closing submit_findings ended the session unanswered
                msgs.append({"role": "tool", "tool_call_id": c["id"], "content": '{"success": true, "message": "Review recorded."}'})
    return msgs, tools


def question(asks):
    items = "\n".join(f"{i + 1}. [{a['ask_id']}] {a['text'].strip()}" for i, a in enumerate(asks))
    return ("Your review has been submitted. This is a follow-up for a research study; it does not change "
            "your review. The maintainers' round-1 review of this PR asked for the following, which your "
            "submission did not raise:\n\n" + items +
            "\n\nFor each numbered item, answer in at most 60 words: (a) did you notice this issue or consider "
            "this change during your review? (b) if yes, what did you conclude, and why did you not file it? "
            "(c) if no, what information or check would have led you to it? Be concrete about what you looked "
            "at. Number your answers to match.")


def main(out_path):
    pop = json.load(open(POPULATION))["sets"]
    out = []
    for set_name, run in RUNS.items():
        rows = pop[set_name]["rows"]
        by_pr = {}
        for ask_id, r in rows.items():
            if r["class"] in CLASSES:
                by_pr.setdefault(r["pr"], []).append({"ask_id": ask_id, "text": r["text"], "class": r["class"]})
        for pr, asks in sorted(by_pr.items()):
            task = next(t for t in glob.glob(f".ape/runs/{run}/tasks/*") if coh.session(t)["pr"] == pr)
            msgs, tools = messages_of(task)
            msgs.append({"role": "user", "content": question(asks)})
            instructions, items = responses_input(msgs, carryover=True)
            payload = {"model": MODEL, "input": items, "instructions": instructions, "store": False,
                       "reasoning": {"effort": "high"}, "include": ["reasoning.encrypted_content"],
                       "max_output_tokens": 6000, "tool_choice": "none"}
            if tools:
                payload["tools"] = [responses_tool(t) for t in tools]
            r = httpx.post("https://api.openai.com/v1/responses", json=payload, timeout=900,
                           headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
            d = r.json()
            if r.status_code != 200:
                print(f"{set_name} {pr}: HTTP {r.status_code} {json.dumps(d)[:300]}", flush=True); continue
            text = "".join(p.get("text", "") for it in d.get("output", []) if it.get("type") == "message" for p in it.get("content", []))
            out.append({"set": set_name, "run": run, "pr": pr, "asks": asks, "answer": text, "usage": d.get("usage"),
                        "carried_items": sum(1 for it in items if it.get("type") == "reasoning")})
            print(f"{set_name} {pr}: {len(asks)} asks, {len(text)} chars, in {d['usage']['input_tokens']:,} out {d['usage']['output_tokens']:,}", flush=True)
            json.dump(out, open(out_path, "w"), indent=1, ensure_ascii=False)
    print("done", len(out), "PR-sessions")


if __name__ == "__main__":
    main(sys.argv[1])
