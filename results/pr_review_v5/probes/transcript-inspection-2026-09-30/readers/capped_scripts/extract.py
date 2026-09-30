"""Extract a compact per-turn trace for each gpt_5.2 Gr1 session (read-only)."""
import json, glob, re, os, sys, collections
W = __import__("os").path.abspath(__import__("os").path.join(__import__("os").path.dirname(__file__), *[".."] * 6))
SP = __import__("os").path.join(__import__("os").path.dirname(__file__), "out")
M = json.load(open(__import__("os").path.join(__import__("os").path.dirname(__file__), "..", "..", "gpt_sessions.json")))

def turn_no(p):
    return int(re.search(r"__turn_(\d+)__", p).group(1))

def short(s, n):
    s = str(s).replace("\n", "\\n")
    return s if len(s) <= n else s[:n] + "…"

def summ_input(name, inp):
    inp = dict(inp or {})
    if name == "file_read":
        return f"{inp.get('file_path')} [{inp.get('line_start')},{inp.get('line_end')}){' full' if inp.get('omit_details') is False else ''}{' lr='+str(inp.get('line_range')) if inp.get('line_range') else ''}"
    if name == "content_search":
        return f"/{inp.get('content_pattern')}/ in {inp.get('path')}" + (" re" if inp.get("use_regex") else "")
    if name == "declaration_search":
        return f"{inp.get('identifier') or inp}"
    if name in ("lean_verify_edit",):
        nd = inp.get("new_declaration")
        return f"{inp.get('path')} decl={inp.get('declaration_name')} new={short(nd, 260) if nd else None}" + (f" other={short({k:v for k,v in inp.items() if k not in ('path','declaration_name','new_declaration','max_messages')},200)}" )
    if name == "lean_verify":
        return short(inp.get("code") or inp, 300)
    if name == "submit_findings":
        return f"{len(inp.get('findings',[]))} findings"
    return short(json.dumps(inp, ensure_ascii=False), 250)

def summ_result(name, rc):
    try:
        r = json.loads(rc)
    except Exception:
        return "RAW:" + short(rc, 200), None
    ok = r.get("success", r.get("compiles"))
    if r.get("error"):
        return "ERROR:" + short(r["error"], 250), False
    if name == "file_read":
        c = r.get("content", "")
        return f"{c.count(chr(10))} lines", ok
    if name == "content_search":
        res = r.get("results") or []
        nm = sum(len(x.get("matches", [])) for x in res) if isinstance(res, list) else "?"
        files = [x.get("path", "").replace("target/", "") for x in res] if isinstance(res, list) else []
        return f"{nm} matches in {r.get('files_with_matches')} files {short(files[:4],200)}", ok
    if name == "declaration_search":
        return short(r.get("results"), 300), ok
    if name == "lean_verify_edit":
        if r.get("mode") == "as_is_compile_check":
            return f"AS_IS compiles={r.get('compiles')} errs={short(r.get('errors_already_in_the_file'),150)}", r.get("compiles")
        errs = r.get("errors") or r.get("errors_introduced_by_your_edit") or []
        e0 = short([e.get("data") if isinstance(e, dict) else e for e in errs][:2], 300)
        return f"mode={r.get('mode')} success={r.get('success', r.get('compiles'))} nerr={len(errs)} {e0 if errs else ''} {short(r.get('message',''),80)}", ok
    if name == "lean_verify":
        errs = r.get("errors") or []
        infos = r.get("infos") or []
        return f"success={r.get('success')} nerr={len(errs)} {short([e.get('data') for e in errs][:2],250)} infos={short([i.get('data') for i in infos][:3],300)}", ok
    if name == "naming_norm":
        return f"verdict={r.get('verdict')} subject={r.get('subject')} cands={r.get('candidates')}", ok
    if name in ("zulip_search", "precedent_search"):
        return short(r.get("results") or r, 300), ok
    return short(json.dumps(r, ensure_ascii=False), 300), ok

def load(run, pr):
    x = M[run][pr]
    lf = f"{W}/{x['last_turn_file']}"
    att = f"{W}/{x['attempt']}"
    recs = [json.loads(l) for l in open(lf)]
    raws = sorted(glob.glob(att + "/conversations/*_raw.jsonl"), key=turn_no)
    usage = {}
    for p in raws:
        for l in open(p):
            d = json.loads(l)
            usage[turn_no(p)] = d.get("usage", {})
    results = {}
    for r in recs:
        if r["type"] == "user":
            for c in r["message"]["content"]:
                if c.get("type") == "tool_result":
                    results[c["tool_use_id"]] = c
    turns = []
    for r in recs:
        if r["type"] != "assistant":
            continue
        k = len(turns) + 1
        calls = []
        text = []
        for c in r["message"]["content"]:
            if c.get("type") == "tool_use":
                res = results.get(c["id"])
                rc = res["result_content"] if res else None
                s, ok = summ_result(c["name"], rc) if rc is not None else ("NO_RESULT", None)
                calls.append(dict(name=c["name"], input=c["input"], res=rc, rsum=s, ok=ok, rlen=len(rc or "")))
            elif c.get("text"):
                text.append(c["text"])
        u = usage.get(k, {})
        turns.append(dict(turn=k, calls=calls, text=text,
                          prompt=u.get("prompt_tokens"), completion=u.get("completion_tokens"),
                          reasoning=(u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                          cached=(u.get("prompt_tokens_details") or {}).get("cached_tokens")))
    user0 = next(r for r in recs if r["type"] == "user")["message"]["content"][0]["text"]
    return dict(run=run, pr=pr, att=att, turns=turns, user0=user0)

def trace(sess):
    out = []
    for t in sess["turns"]:
        out.append(f"T{t['turn']:02d} p={t['prompt']} r={t['reasoning']} n={len(t['calls'])}" + (f" TEXT={short(' '.join(t['text']),200)}" if t['text'] else ""))
        for c in t["calls"]:
            out.append(f"   {c['name']}: {summ_input(c['name'], c['input'])}\n      -> {c['rsum']} (len {c['rlen']})")
    return "\n".join(out)

if __name__ == "__main__":
    import pickle
    allsess = {}
    for run, v in M.items():
        if "calib" in run: continue
        for pr in v:
            s = load(run, pr)
            allsess[(run, pr)] = s
            open(f"{SP}/traces/{pr}.txt", "w").write(trace(s))
    pickle.dump(allsess, open(f"{SP}/sessions.pkl", "wb"))
    print(len(allsess))
