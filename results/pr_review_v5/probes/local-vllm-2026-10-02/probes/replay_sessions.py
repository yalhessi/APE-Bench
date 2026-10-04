"""Replay logged ELM Qwen agent sessions against a local vLLM server, `concurrency` sessions at a time.

Each session's requests are sent in order exactly as logged (so each extends the previous one, as
1,172 of 1,172 logged pairs do), with the completion forced to the logged length (min_tokens =
max_tokens = logged completion_tokens), so decode load matches. Tool execution time is not replayed:
compare LLM time, local against ELM's logged latency for the same requests.

usage: python replay_sessions.py <base_url> <model> <concurrency> <n_sessions> <out.jsonl>
                                 [--files a.jsonl,b.jsonl] [--cap N]
--files replays exactly those logged sessions (any model; reasoning forced off), --cap bounds the
forced completion length (for logs whose completion counts include another model's reasoning).
"""
import json
import random
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from common import chat, usage, logged_sessions

BASE, MODEL, CONC, N, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
opts = dict(zip(sys.argv[6::2], sys.argv[7::2]))
FILES = opts["--files"].split(",") if "--files" in opts else None
CAP = int(opts.get("--cap", 10 ** 9))
sessions = logged_sessions(files=FILES)
random.Random(1).shuffle(sessions)
sessions = sessions[:N]


def run(session):
    f, calls = session
    rows = []
    for i, (body, elm_latency, elm_usage) in enumerate(calls):
        body = dict(body)
        n = min(CAP, max(1, elm_usage.get("completion_tokens", 1)))
        body.update(model=MODEL, max_completion_tokens=n, min_tokens=n, reasoning_effort="none")
        dt, r = chat(BASE, body)
        p, c, comp = usage(r)
        rows.append(dict(session=f.split("/")[-1], turn=i, latency=dt, elm_latency=elm_latency,
                         prompt=p, cached=c or 0, completion=comp, elm_prompt=elm_usage.get("prompt_tokens")))
    return rows


t0 = time.time()
with ThreadPoolExecutor(CONC) as ex:
    results = [row for rows in ex.map(run, sessions) for row in rows]
wall = time.time() - t0
with open(OUT, "w") as fh:
    for row in results:
        fh.write(json.dumps(row) + "\n")

P = sum(r["prompt"] for r in results); C = sum(r["cached"] for r in results)
loc = [r["latency"] for r in results]; elm = [r["elm_latency"] for r in results]
q = lambda xs, p: sorted(xs)[int(p * (len(xs) - 1))]
print(f"sessions {len(sessions)} calls {len(results)} concurrency {CONC} wall {wall:.0f}s")
print(f"prompt tokens {P}, cached {C} ({C / max(P, 1):.1%})")
print(f"latency local median {statistics.median(loc):.2f}s p90 {q(loc, .9):.2f}s max {max(loc):.1f}s | "
      f"ELM logged median {statistics.median(elm):.2f}s p90 {q(elm, .9):.2f}s max {max(elm):.1f}s")
print(f"LLM time summed: local {sum(loc):.0f}s, ELM {sum(elm):.0f}s")
late = [r for r in results if r["turn"] >= 5]
if late:
    lc = sum(r["cached"] for r in late) / max(sum(r["prompt"] for r in late), 1)
    print(f"turns >= 5: cached share {lc:.1%}, local median {statistics.median(r['latency'] for r in late):.2f}s")
