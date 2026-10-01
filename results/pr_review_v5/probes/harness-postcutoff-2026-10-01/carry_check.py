"""Scan data/llm_logs for gpt-5.2 Responses requests of the post-cutoff carried runs. Per set: the
first-turn payload fingerprints per PR, carry-over on later turns, and input growth against the
previous turn's reasoning. Read-only; run from the repo root. A log file holds every request of one
client (APE-Agent: one per session; the Claude Code relay: one per request)."""
import collections, glob, hashlib, json, re, sys

PRS = {"41930", "42184", "42814", "43024", "43167", "43192"}
SETS = {  # name: (minute-dir glob, harness, first minute to include as "HH:MM")
    "Grc1 (30 Sep 08)": ("data/llm_logs/2026-09-30/08/*", "ape", None),
    "Grc2+3 (30 Sep 09)": ("data/llm_logs/2026-09-30/09/*", "ape", None),
    "A, mine (1 Oct 06)": ("data/llm_logs/2026-10-01/06/*", "ape", "06:25"),
    "C, mine (1 Oct 06)": ("data/llm_logs/2026-10-01/06/*", "claude", "06:25"),
}


def h(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True).encode()).hexdigest()[:10]


def text_of(item):
    c = item.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(p.get("text", "") for p in c if isinstance(p, dict))
    return ""


def harness(req):
    names = {t.get("name") for t in req.get("tools") or []}
    return "claude" if ("Read" in names or "Grep" in names) else "ape"


def pr_of(req):
    for it in req.get("input") or []:
        if it.get("role") == "user":
            found = PRS & set(re.findall(r"\b(4\d{4})\b", text_of(it)))
            if found:
                return sorted(found)[0]
    return None


def assistant_turns(inp):
    """Maximal runs of model-output items (reasoning, function_call, assistant message)."""
    runs, cur = [], None
    for it in inp:
        kind = it.get("type") or it.get("role")
        is_output = kind in ("reasoning", "function_call") or it.get("role") == "assistant"
        if is_output:
            if cur is None:
                cur = []
                runs.append(cur)
            cur.append("reasoning" if kind == "reasoning" else "other")
        else:
            cur = None
    return runs


def usage(resp):
    u = (resp or {}).get("usage") or {}
    return (u.get("input_tokens"), (u.get("output_tokens_details") or {}).get("reasoning_tokens"),
            u.get("output_tokens"))


def minute_ok(d, earliest):
    if not earliest:
        return True
    hh, mm = d.split("/")[-2], d.split("/")[-1]
    return (hh, mm) >= tuple(earliest.split(":"))


def scan():
    report = {}
    for name, (pattern, want, earliest) in SETS.items():
        first = collections.defaultdict(set)
        later, growth = [], []
        for d in sorted(glob.glob(pattern)):
            if not minute_ok(d, earliest):
                continue
            for f in glob.glob(f"{d}/*.jsonl"):
                rows = [json.loads(l) for l in open(f)]
                pairs, pending = [], None
                for r in rows:
                    if r.get("type") in ("request", "streaming_request"):
                        pending = r["data"]
                    elif r.get("type") == "response" and pending is not None:
                        pairs.append((pending, r["data"]))
                        pending = None
                prev = None
                for req, resp in pairs:
                    if not isinstance(req, dict) or "input" not in req:
                        continue
                    if not str(req.get("model", "")).startswith("gpt-5.2") or harness(req) != want:
                        continue
                    pr = pr_of(req)
                    if pr is None:
                        continue
                    turns = assistant_turns(req["input"])
                    if not turns:
                        user = next(text_of(it) for it in req["input"] if it.get("role") == "user")
                        tools = sorted((t.get("name"), t.get("description"),
                                        json.dumps(t.get("parameters"), sort_keys=True))
                                       for t in req.get("tools") or [])
                        settings = (json.dumps(req.get("reasoning")), json.dumps(req.get("include")),
                                    req.get("max_output_tokens"), req.get("temperature"), req.get("store"))
                        first[pr].add((h(req.get("instructions")), h(tools), h(user), h(settings)))
                    else:
                        later.append((len(turns), sum(1 for t in turns if "reasoning" in t)))
                    # growth: same client file, consecutive pair whose input extends the previous
                    cur_in, _, _ = usage(resp)
                    if prev is not None and cur_in is not None:
                        p_req, p_resp = prev
                        p_in, p_reason, _ = usage(p_resp)
                        if (p_in and p_reason and len(req["input"]) > len(p_req["input"])
                                and req["input"][:len(p_req["input"])] == p_req["input"]):
                            growth.append((cur_in - p_in, p_reason))
                    prev = (req, resp)
        turns_total = sum(a for a, _ in later)
        carried = sum(c for _, c in later)
        print(f"== {name}: first turns {sum(len(v) for v in first.values())} (distinct fingerprints per PR: "
              f"{ {pr: len(v) for pr, v in sorted(first.items())} }); later requests {len(later)}, "
              f"{sum(1 for a, c in later if c)} carrying reasoning; earlier turns carried {carried} of {turns_total}")
        if growth:
            # with carry-over the input grows by at least the previous turn's reasoning
            ratios = sorted(g / r for g, r in growth if r > 0)
            below = sum(1 for g, r in growth if g < r)
            print(f"   consecutive pairs {len(growth)}: input growth / previous reasoning, median "
                  f"{ratios[len(ratios)//2]:.2f}; pairs where growth < previous reasoning: {below}")
        report[name] = {pr: sorted(v) for pr, v in first.items()}
    return report


if __name__ == "__main__":
    out = scan()
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    sets = list(out)
    ape = [s for s in sets if "Grc" in s or s.startswith("A,")]
    same = all(out[ape[0]].get(pr) == out[s].get(pr) for s in ape[1:] for pr in PRS)
    print("APE-Agent first-turn payloads identical across", ape, ":", same)
