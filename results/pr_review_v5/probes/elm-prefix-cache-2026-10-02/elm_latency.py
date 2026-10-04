"""Per-call latency of ELM Qwen calls against total prompt, new prompt (vs the previous call in the
same client session) and completion tokens. If vLLM prefix caching hits, latency should follow new
prompt tokens, not total prompt tokens."""
import json, glob, sys
import numpy as np
rows = []
for f in glob.glob("data/llm_logs/2026-09-2*/**/*.jsonl", recursive=True) + glob.glob("data/llm_logs/2026-09-3*/**/*.jsonl", recursive=True) + glob.glob("data/llm_logs/2026-10-*/**/*.jsonl", recursive=True):
    try:
        recs = [json.loads(l) for l in open(f)]
    except Exception:
        continue
    if not recs or "Qwen3.5" not in str(recs[0].get("data", {}).get("model", "")):
        continue
    prev_prompt = None; req_t = None; streamed = False
    for r in recs:
        d = r.get("data", {})
        if r.get("type") == "request":
            req_t = r["timestamp"]; streamed = bool(d.get("stream"))
        elif r.get("type") == "response" and req_t is not None:
            u = d.get("usage") or {}
            p, c = u.get("prompt_tokens"), u.get("completion_tokens")
            if p is None or c is None:
                continue
            new = p - prev_prompt if prev_prompt is not None and p >= prev_prompt else p
            rows.append((r["timestamp"] - req_t, p, new, c, streamed, f))
            prev_prompt = p; req_t = None
rows = [r for r in rows if r[0] > 0]
print("calls", len(rows), "sessions", len({r[5] for r in rows}), "streamed", sum(r[4] for r in rows))
L = np.array([r[0] for r in rows]); P = np.array([r[1] for r in rows]); N = np.array([r[2] for r in rows]); C = np.array([r[3] for r in rows])
def fit(X, name):
    X1 = np.column_stack([np.ones(len(L))] + X)
    beta, res, *_ = np.linalg.lstsq(X1, L, rcond=None)
    pred = X1 @ beta; r2 = 1 - ((L - pred) ** 2).sum() / ((L - L.mean()) ** 2).sum()
    print(f"{name:32s} R2={r2:.3f} coef={np.round(beta, 6)}")
fit([C], "completion only")
fit([P, C], "total prompt + completion")
fit([N, C], "new prompt + completion")
fit([P, N, C], "total + new + completion")
# Latency per completion token, binned by total prompt size, among short-new-prompt calls
print("\nseconds per completion token (calls with new prompt < 3k), by total prompt:")
for lo, hi in [(0, 15e3), (15e3, 30e3), (30e3, 50e3), (50e3, 80e3), (80e3, 1e9)]:
    m = (P >= lo) & (P < hi) & (N < 3000) & (C >= 50)
    if m.sum():
        print(f"  {int(lo/1e3):>3}-{'inf' if hi>1e8 else int(hi/1e3)}k  n={m.sum():4d}  median latency {np.median(L[m]):6.1f}s  median s/token {np.median(L[m]/C[m]):.3f}  median completion {np.median(C[m]):.0f}")
print("\nlatency with small completion (<60 tokens), by total prompt (prefill-dominated):")
for lo, hi in [(0, 15e3), (15e3, 30e3), (30e3, 50e3), (50e3, 80e3), (80e3, 1e9)]:
    m = (P >= lo) & (P < hi) & (C < 60)
    if m.sum():
        print(f"  {int(lo/1e3):>3}-{'inf' if hi>1e8 else int(hi/1e3)}k  n={m.sum():4d}  median latency {np.median(L[m]):6.1f}s  p90 {np.percentile(L[m],90):6.1f}s  median new prompt {np.median(N[m]):.0f}")
