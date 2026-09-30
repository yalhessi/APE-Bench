"""Per-session metrics: repeats, near-repeats, reasoning drift, compile loops, parallelism."""
import pickle, json, re, collections, statistics
SP = __import__("os").path.join(__import__("os").path.dirname(__file__), "out")
S = pickle.load(open(f"{SP}/sessions.pkl", "rb"))
CAPPED = {"42814", "26185", "32080", "34935", "33066", "33145", "33285", "33294", "33321", "33421"}

def lines_read(res):
    try:
        c = json.loads(res).get("content", "")
    except Exception:
        return None
    ns = [int(m.group(1)) for m in re.finditer(r"^\s*(\d+)\|", c, re.M)]
    return (min(ns), max(ns)) if ns else None

def toks(pat):
    return frozenset(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9_'.]{3,}", pat or ""))

def keyof(c):
    n, i = c["name"], c["input"] or {}
    if n == "file_read": return ("file", i.get("file_path"))
    if n == "content_search": return ("search", toks(i.get("content_pattern")))
    if n == "declaration_search": return ("decl", i.get("identifier"))
    if n == "lean_verify_edit": return ("edit", i.get("path"), i.get("declaration_name"))
    if n == "lean_verify": return ("check", frozenset(re.findall(r"#check\s+(\S+)", i.get("code") or "")))
    if n == "naming_norm": return ("naming", i.get("declaration"))
    return (n, json.dumps(i, sort_keys=True))

def analyse(sess):
    turns = sess["turns"]
    N = len(turns)
    seen_exact = set()
    reads = []          # (file, lo, hi)
    seen_search = []    # (tokset, path)
    seen_keys = set()
    seen_objects = set()
    rows = []
    for t in turns:
        for c in t["calls"]:
            n, i = c["name"], c["input"] or {}
            ex = (n, json.dumps(i, sort_keys=True))
            kind = "new"
            if ex in seen_exact:
                kind = "exact"
            else:
                if n == "file_read":
                    rng = lines_read(c["res"] or "")
                    fp = i.get("file_path")
                    if rng and any(f == fp and not (rng[1] < lo or rng[0] > hi) for f, lo, hi in reads):
                        kind = "near"
                    if rng: reads.append((fp, rng[0], rng[1]))
                elif n == "content_search":
                    ts = toks(i.get("content_pattern"))
                    if any(ts and (ts == s or ts <= s or s <= ts) and s for s, p in seen_search):
                        kind = "near"
                    seen_search.append((ts, i.get("path")))
                elif n == "declaration_search":
                    idf = i.get("identifier") or ""
                    if ("decl", idf.rstrip("'")) in seen_keys or ("decl", idf) in seen_keys:
                        kind = "near"
                elif n == "lean_verify":
                    ks = keyof(c)[1]
                    if any(k[0] == "check" and ks and ks <= k[1] for k in seen_keys):
                        kind = "near"
            seen_exact.add(ex)
            k = keyof(c)
            seen_keys.add(k)
            rows.append(dict(turn=t["turn"], name=n, kind=kind, ok=c["ok"], rsum=c["rsum"],
                             err=(c["rsum"] or "").startswith("ERROR") or c["rsum"] == "NO_RESULT",
                             decl=i.get("declaration_name"), has_new=bool(i.get("new_declaration"))))
    def window(a, b):
        w = [r for r in rows if a <= r["turn"] <= b]
        return dict(calls=len(w), exact=sum(r["kind"] == "exact" for r in w),
                    near=sum(r["kind"] == "near" for r in w), new=sum(r["kind"] == "new" for r in w),
                    by_tool=dict(collections.Counter(r["name"] for r in w)),
                    tool_errors=sum(r["err"] for r in w))
    last = window(max(1, N - 24), N)
    first = window(1, min(25, N))
    allw = window(1, N)
    edits = [r for r in rows if r["name"] == "lean_verify_edit"]
    edit_as_is = sum(1 for r in edits if not r["has_new"])
    edit_try = [r for r in edits if r["has_new"]]
    edit_ok = sum(1 for r in edit_try if "success=True" in r["rsum"] or "compiles=True" in r["rsum"])
    fails_per_decl = collections.Counter(r["decl"] for r in edit_try if not ("success=True" in r["rsum"]))
    r10a = [t["reasoning"] or 0 for t in turns[:10]]
    r10b = [t["reasoning"] or 0 for t in turns[-10:]]
    zero_r = lambda ts: sum(1 for t in ts if (t["reasoning"] or 0) == 0)
    cpt = [len(t["calls"]) for t in turns]
    q = max(1, N // 4)
    return dict(
        turns=N, calls=len(rows),
        calls_per_turn=round(len(rows) / N, 2),
        calls_per_turn_quartiles=[round(statistics.mean(cpt[i*q:(i+1)*q] or [0]), 2) for i in range(4)],
        single_call_turns_last25=sum(1 for c in cpt[-25:] if c == 1),
        prompt_first=turns[0]["prompt"], prompt_end=turns[-1]["prompt"],
        prompt_at_t40=turns[min(39, N-1)]["prompt"],
        reasoning_first10=sum(r10a), reasoning_last10=sum(r10b),
        zero_reasoning_turns_first10=zero_r(turns[:10]), zero_reasoning_turns_last10=zero_r(turns[-10:]),
        zero_reasoning_turns_total=zero_r(turns),
        all=allw, first25=first, last25=last,
        edits_as_is=edit_as_is, edits_tried=len(edit_try), edits_ok=edit_ok,
        edit_fails_per_decl=dict(fails_per_decl),
        tool_counts=dict(collections.Counter(r["name"] for r in rows)),
    ), rows

if __name__ == "__main__":
    out = {}
    for (run, pr), s in S.items():
        m, rows = analyse(s)
        m["run"] = run; m["capped"] = pr in CAPPED
        out[pr] = m
    json.dump(out, open(f"{SP}/metrics.json", "w"), indent=1, default=list)
    hdr = "pr     cap turns calls c/t  quart               p_end   r1st10 rlast10 z0-10 zlast10 last25:ex/near/new  err edits(asis/try/ok)"
    print(hdr)
    for pr, m in sorted(out.items(), key=lambda kv: (not kv[1]["capped"], kv[1]["run"], kv[0])):
        l = m["last25"]
        print(f"{pr:6} {'Y' if m['capped'] else '-'}  {m['turns']:4} {m['calls']:5} {m['calls_per_turn']:4} {str(m['calls_per_turn_quartiles']):20} {m['prompt_end']:7} {m['reasoning_first10']:6} {m['reasoning_last10']:6} {m['zero_reasoning_turns_first10']:3} {m['zero_reasoning_turns_last10']:3}   {l['exact']:3}/{l['near']:3}/{l['new']:3} of {l['calls']:3} {l['tool_errors']:3}  {m['edits_as_is']}/{m['edits_tried']}/{m['edits_ok']} {m['edit_fails_per_decl']}")
