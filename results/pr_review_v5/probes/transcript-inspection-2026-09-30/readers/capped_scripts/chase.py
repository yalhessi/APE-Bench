"""Count calls spent following declaration_search 'before this PR' hits whose file never declares the queried name."""
import pickle, json, re, collections
SP = __import__("os").path.join(__import__("os").path.dirname(__file__), "out")
S = pickle.load(open(f"{SP}/sessions.pkl", "rb"))
CAPPED = {"42814", "26185", "32080", "34935", "33066", "33145", "33285", "33294", "33321", "33421"}
out = {}
for (run, pr), s in S.items():
    hits = {}   # file -> (turn, query)
    nds = nds_ns_hit = 0
    follow = []
    for t in s["turns"]:
        for c in t["calls"]:
            i = c["input"] or {}
            if c["name"] == "declaration_search":
                nds += 1
                try: r = json.loads(c["res"] or "{}")
                except Exception: r = {}
                q = i.get("identifier") or ""
                if "." in q and r.get("declared_before_this_pr"):
                    nds_ns_hit += 1
                    for m in re.finditer(r"declared in `([^`]+)` \(before this PR\)", r.get("results", "")):
                        hits.setdefault(m.group(1), (t["turn"], q))
            elif c["name"] in ("file_read", "content_search"):
                p = (i.get("file_path") or i.get("path") or "").replace("target/", "")
                if p in hits and t["turn"] > hits[p][0]:
                    zero = c["name"] == "content_search" and '"files_with_matches": 0' in (c["res"] or "")
                    follow.append((t["turn"], c["name"], p, zero))
    out[pr] = dict(capped=pr in CAPPED, decl_searches=nds, ns_queries_with_base_hits=nds_ns_hit,
                   follow_calls=len(follow), follow_zero=sum(f[3] for f in follow),
                   follow_turns=sorted({f[0] for f in follow}), follow_files=dict(collections.Counter(f[2] for f in follow)))
json.dump(out, open(f"{SP}/chase.json", "w"), indent=1)
for pr, v in sorted(out.items(), key=lambda kv: not kv[1]["capped"]):
    print(pr, "Y" if v["capped"] else "-", v["decl_searches"], v["ns_queries_with_base_hits"], "follow", v["follow_calls"], "zero", v["follow_zero"], "turns", len(v["follow_turns"]), list(v["follow_files"].items())[:4])
