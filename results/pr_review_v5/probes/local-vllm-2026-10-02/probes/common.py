"""Shared helpers for the local-model probes: one chat call, and the logged ELM Qwen sessions."""
import glob
import json
import time
import urllib.request

LOGS = "/research/projects/proofedit/ya475/APE-Bench/data/llm_logs"


def chat(base_url, body, timeout=1800):
    """POST one chat completion; returns (latency_s, response_json)."""
    req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer local"})
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return time.time() - t, r


def usage(r):
    u = r.get("usage") or {}
    det = u.get("prompt_tokens_details") or {}
    return u.get("prompt_tokens", 0), det.get("cached_tokens"), u.get("completion_tokens", 0)


def logged_sessions(min_requests=3, files=None):
    """Logged sessions as (file, [(request_body, logged_latency, logged_usage), ...]): every ELM
    Qwen session by default, or exactly `files` whatever their model."""
    out = []
    if files is None:
        candidates = sorted(glob.glob(f"{LOGS}/2026-09-2*/**/*.jsonl", recursive=True)
                            + glob.glob(f"{LOGS}/2026-09-3*/**/*.jsonl", recursive=True))
    else:
        candidates = files
    for f in candidates:
        recs = [json.loads(l) for l in open(f)]
        if not recs or (files is None and "Qwen3.5" not in str(recs[0].get("data", {}).get("model", ""))):
            continue
        calls, req = [], None
        for r in recs:
            if r.get("type") == "request":
                req = r
            elif r.get("type") == "response" and req is not None:
                calls.append((req["data"], r["timestamp"] - req["timestamp"], r["data"].get("usage") or {}))
                req = None
        if len(calls) >= min_requests:
            out.append((f, calls))
    return out
