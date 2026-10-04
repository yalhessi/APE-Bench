"""Replay a finished carry-over session (its encrypted reasoning included) and ask why verified
edits were not filed. Tools off (tool_choice none). One call per session; prints the answer."""
import glob, json, os, sys, importlib.util
import httpx
sys.path.insert(0, "src")
from ape.llm_clients.providers.openai_provider import responses_input, responses_tool
spec = importlib.util.spec_from_file_location("coh", "results/pr_review_v5/probes/carryover-coherence-2026-09-30/coherence.py")
coh = importlib.util.module_from_spec(spec); spec.loader.exec_module(coh)
MODELS = {"54": "gpt-5.4", "55": "gpt-5.5-2026-04-23"}

def messages_of(task):
    rows = [json.loads(l) for l in open(coh.last_conversation(task))]
    msgs, tools = [], None
    for r in rows:
        if r["type"] == "tool_definitions":
            tools = r.get("tools") or r.get("message", {}).get("tools") or r.get("definitions")
            if tools is None:
                tools = next((v for v in r.values() if isinstance(v, list)), None)
            continue
        m = r.get("message") or {}
        blocks = m.get("content") or []
        if r["type"] == "system":
            msgs.append({"role": "system", "content": "".join(b.get("text") or "" for b in blocks)})
        elif r["type"] == "assistant":
            calls = [{"id": b["id"], "type": "function", "function": {"name": b["name"], "arguments": json.dumps(b.get("input") or {}, ensure_ascii=False)}}
                     for b in blocks if b.get("type") == "tool_use"]
            text = "".join(b.get("text") or "" for b in blocks if b.get("type") == "text") or None
            msg = {"role": "assistant", "content": text}
            if calls: msg["tool_calls"] = calls
            if m.get("signature"): msg["signature"] = m["signature"]
            msgs.append(msg)
        elif r["type"] == "user":
            for b in blocks:
                if b.get("type") == "tool_result":
                    msgs.append({"role": "tool", "tool_call_id": b.get("tool_use_id"), "content": b.get("result_content") or ""})
                elif b.get("type") == "text":
                    msgs.append({"role": "user", "content": b.get("text") or ""})
    return msgs, tools

def ask(model_key, pr, question):
    run = f"probe_postcutoff_gpt{model_key}_Grc_rep1"
    task = next(t for t in glob.glob(f".ape/runs/{run}/tasks/*") if coh.session(t)["pr"] == pr)
    msgs, tools = messages_of(task)
    answered = {m["tool_call_id"] for m in msgs if m["role"] == "tool"}
    for m in [m for m in msgs if m["role"] == "assistant"]:
        for c in m.get("tool_calls") or []:
            if c["id"] not in answered:  # the closing submit_findings call ended the session unanswered
                msgs.append({"role": "tool", "tool_call_id": c["id"], "content": '{"success": true, "message": "Review recorded."}'})
    msgs.append({"role": "user", "content": question})
    instructions, items = responses_input(msgs, carryover=True)
    payload = {"model": MODELS[model_key], "input": items, "instructions": instructions, "store": False,
               "reasoning": {"effort": "high"}, "include": ["reasoning.encrypted_content"],
               "max_output_tokens": 8000, "tool_choice": "none"}
    if tools:
        payload["tools"] = [responses_tool(t) for t in tools]
    r = httpx.post("https://api.openai.com/v1/responses", json=payload, timeout=600,
                   headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
    d = r.json()
    if r.status_code != 200:
        print("HTTP", r.status_code, json.dumps(d)[:800]); return None
    text = "".join(p.get("text", "") for it in d.get("output", []) if it.get("type") == "message" for p in it.get("content", []))
    carried = sum(1 for it in items if it.get("type") == "reasoning")
    print(f"## gpt{model_key} on {pr}: {carried} carried reasoning items, usage {d.get('usage')}\n{text}\n")
    return {"model": MODELS[model_key], "pr": pr, "question": question, "answer": text, "usage": d.get("usage"), "carried_items": carried}

if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    out = [a for j in jobs if (a := ask(j["model"], j["pr"], j["question"]))]
    json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
