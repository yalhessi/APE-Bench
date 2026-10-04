"""Within each logged ELM Qwen session: does request n+1 begin with request n's messages unchanged,
with the same tools? If not, no server-side prefix cache can hit past the first change."""
import json, glob, collections
pairs = 0; extends = 0; tools_same = 0; first_diff = collections.Counter()
for f in glob.glob("data/llm_logs/2026-09-2*/**/*.jsonl", recursive=True) + glob.glob("data/llm_logs/2026-09-3*/**/*.jsonl", recursive=True):
    recs = [json.loads(l) for l in open(f)]
    reqs = [r["data"] for r in recs if r.get("type") == "request"]
    if not reqs or "Qwen3.5" not in str(reqs[0].get("model", "")):
        continue
    for a, b in zip(reqs, reqs[1:]):
        pairs += 1
        ma, mb = a["messages"], b["messages"]
        ok = len(mb) >= len(ma) and mb[:len(ma)] == ma
        extends += ok
        tools_same += a.get("tools") == b.get("tools")
        if not ok:
            i = next((k for k, (x, y) in enumerate(zip(ma, mb)) if x != y), min(len(ma), len(mb)))
            first_diff[(mb[i]["role"] if i < len(mb) else "shorter", "index0" if i == 0 else "later")] += 1
print(f"consecutive request pairs {pairs}; next extends previous exactly {extends}; tools identical {tools_same}")
print("where the first change falls:", dict(first_diff))
