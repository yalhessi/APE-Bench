"""Basic checks against a local vLLM server: prefix caching (hit and reported), reasoning off,
and tool-call conformance on real logged requests.

usage: python probe_basic.py <base_url e.g. http://127.0.0.1:8011/v1> <served model name>
"""
import json
import random
import sys
import time

import jsonschema

from common import chat, usage, logged_sessions

BASE, MODEL = sys.argv[1], sys.argv[2]
words = [w.strip() for w in open("/usr/share/dict/words") if w.strip().isalpha()][:50000]

print("== 1. prefix cache: ~59.5k-token prompt, max_tokens 1")
for trial in range(3):
    rng = random.Random(time.time_ns())
    doc = " ".join(rng.choice(words) for _ in range(30000))
    base = [{"role": "system", "content": "You read documents."},
            {"role": "user", "content": doc + "\n\nReply with one word."}]
    ext = base + [{"role": "assistant", "content": "Okay."}, {"role": "user", "content": "Now say one more word."}]
    for label, msgs in [("cold", base), ("same", base), ("extended", ext)]:
        dt, r = chat(BASE, {"model": MODEL, "messages": msgs, "max_tokens": 1, "temperature": 0,
                            "reasoning_effort": "none"})
        p, c, _ = usage(r)
        print(f"  trial {trial} {label:9s} prompt={p:6d} cached={c}  latency={dt:6.2f}s", flush=True)

print("\n== 2. reasoning off: one short prompt, three ways of asking")
q = [{"role": "user", "content": "What is 17 * 23? Answer with the number only."}]
for label, extra in [("nothing sent", {}), ("reasoning_effort none", {"reasoning_effort": "none"}),
                     ("enable_thinking false", {"chat_template_kwargs": {"enable_thinking": False}})]:
    dt, r = chat(BASE, {"model": MODEL, "messages": q, "max_tokens": 4000, "temperature": 0, **extra})
    m = r["choices"][0]["message"]
    rc = m.get("reasoning_content") or m.get("reasoning") or ""
    print(f"  {label:24s} completion_tokens={usage(r)[2]:5d} reasoning_chars={len(rc):6d} "
          f"latency={dt:5.2f}s content={(m.get('content') or '')[:40]!r}", flush=True)

print("\n== 3. tool calls under tool_choice auto: first request of 16 logged sessions, as sent to ELM")
sessions = logged_sessions()
rng = random.Random(0)
picked = rng.sample(sessions, min(16, len(sessions)))
n_calls = n_ok = n_resp_with_calls = 0
for f, calls in picked:
    body = dict(calls[0][0])
    body["model"] = MODEL
    schemas = {t["function"]["name"]: t["function"].get("parameters", {}) for t in body.get("tools", [])}
    dt, r = chat(BASE, body)
    tcs = r["choices"][0]["message"].get("tool_calls") or []
    n_resp_with_calls += bool(tcs)
    for tc in tcs:
        n_calls += 1
        name = tc["function"]["name"]
        try:
            args = json.loads(tc["function"]["arguments"])
            jsonschema.validate(args, schemas[name])
            n_ok += 1
        except Exception as e:
            print(f"    nonconformant {name}: {str(e)[:160]}")
    print(f"  {f.split('/')[-1]} tool_calls={len(tcs)} latency={dt:5.2f}s prompt={usage(r)[0]}", flush=True)
print(f"  responses with a tool call {n_resp_with_calls}/{len(picked)}; calls schema-valid {n_ok}/{n_calls}")
