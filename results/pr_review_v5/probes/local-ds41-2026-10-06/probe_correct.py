"""Is a local server computing correctly? Run before any review on a patched stack.

A wrong KV geometry on SM120 boots cleanly and returns garbage (vllm#59203: all-NaN logits), so a
server that starts proves nothing. Two checks, both must pass:
  1. 17 x 19 with thinking off -> "323";
  2. the first 20 GSM8K test questions with light reasoning -> at least 17 correct
     (the patched SM120 stack in #59203 scored 99/100).
usage: python probe_correct.py <base_url> <model>     exit 0 = pass
"""
import json
import re
import sys
import urllib.request

from common import chat

BASE, MODEL = sys.argv[1], sys.argv[2]
GSM8K = "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl"

_, r = chat(BASE, {"model": MODEL, "max_tokens": 50, "temperature": 0, "reasoning_effort": "none",
                   "messages": [{"role": "user", "content": "What is 17*19? Answer with just the number."}]})
arith = (r["choices"][0]["message"].get("content") or "").strip()
arith_ok = arith.replace(",", "").strip().rstrip(".") == "323"
print(f"17x19 -> {arith!r}: {'ok' if arith_ok else 'WRONG'}", flush=True)

rows = [json.loads(l) for l in urllib.request.urlopen(GSM8K, timeout=60).read().decode().splitlines()[:20]]
correct = 0
for i, row in enumerate(rows):
    gold = row["answer"].split("####")[-1].strip().replace(",", "")
    _, r = chat(BASE, {"model": MODEL, "max_tokens": 4096, "temperature": 0, "reasoning_effort": "low",
                       "messages": [{"role": "user", "content": row["question"]
                                     + "\n\nEnd with a line 'Answer: <number>'."}]})
    text = r["choices"][0]["message"].get("content") or ""
    m = re.findall(r"Answer:\s*\$?(-?[\d,]*\.?\d+)", text) or re.findall(r"-?[\d,]*\.?\d+", text)
    got = m[-1].replace(",", "").rstrip(".") if m else ""
    ok = got != "" and float(got) == float(gold)
    correct += ok
    print(f"gsm8k {i + 1:2d}: gold {gold:>6} got {got:>8} {'ok' if ok else 'x'}", flush=True)
print(f"gsm8k {correct}/20", flush=True)
sys.exit(0 if arith_ok and correct >= 17 else 1)
