"""Classify declaration_search 'before this PR' hits as genuine or leaf-only (phantom), approximately,
against a base snapshot; then count calls that follow phantom hits."""
import pickle, json, re, os, collections
SP = __import__("os").path.join(__import__("os").path.dirname(__file__), "out")
WS = __import__("os").path.abspath(__import__("os").path.join(__import__("os").path.dirname(__file__), *[".."] * 6, "data/code_execute/repos/mathlib4/workspaces"))
S = pickle.load(open(f"{SP}/sessions.pkl", "rb"))
CAPPED = {"42814", "26185", "32080", "34935", "33066", "33145", "33285", "33294", "33321", "33421"}
KNOWN = {"32080": "a73de4ba4b59f748f4d79b55f3a26487c62d6b84", "33145": "c2a50c83a4e2a63ad850c97e30d2cb6fa72b3c8d",
         "33285": "4be5c6872db6d8714540445c7773fa4d05236a53", "33321": "0bf098cae72555897ba57d242cda46bac4b006d1",
         "33421": "473b57441bc20a2e6d10ff18d4f10afdb025a57e", "32875": "26fffffcccd7299b26cf63fac902165bc553fd56",
         "33362": "cc0ebd15d3addc96bf3ff0cb4fc04e936f7bb1d8", "34091": "7ee74e7d3f87077723e124e2e62a6dd1a9509c13",
         "41930": "c81c5cbb1cbf71482901fd2f72ab66909ac54fe1", "26185": "d05defbd00f934e85df3c9e4befcecc2bfb6b272"}
FALLBACK = "c2a50c83a4e2a63ad850c97e30d2cb6fa72b3c8d"
DECL = r"(?:theorem|lemma|def|abbrev|instance|structure|class|inductive|alias)"

def genuine(root, path, query):
    if "." not in query: return None
    prefix, leaf = query.rsplit(".", 1)
    last = prefix.rsplit(".", 1)[-1]
    fp = os.path.join(root, path)
    if not os.path.isfile(fp): return False if path.startswith(".lake") else None
    t = open(fp, errors="ignore").read()
    if re.search(rf"{DECL}\s+(?:[\w.']*\.)?{re.escape(last)}\.{re.escape(leaf)}(?![\w'])", t): return True
    if re.search(rf"namespace\s+(?:[\w.]*\.)?{re.escape(last)}\b", t) and re.search(rf"{DECL}\s+{re.escape(leaf)}(?![\w'])", t): return True
    return False

out = {}
for (run, pr), s in S.items():
    sha = KNOWN.get(pr, FALLBACK); root = os.path.join(WS, sha)
    hits = {}  # path -> (turn, query, genuine)
    n_ns = n_ph = n_gen = 0
    queries_with_phantom = set()
    for t in s["turns"]:
        for c in t["calls"]:
            if c["name"] != "declaration_search": continue
            q = (c["input"] or {}).get("identifier") or ""
            try: r = json.loads(c["res"] or "{}")
            except Exception: continue
            if "." not in q or not r.get("declared_before_this_pr"): continue
            n_ns += 1
            ph_here = False
            for m in re.finditer(r"declared in `([^`]+)` \(before this PR\)", r.get("results", "")):
                g = genuine(root, m.group(1), q)
                if g is False:
                    ph_here = True
                    hits.setdefault(m.group(1), (t["turn"], q))
            if ph_here:
                n_ph += 1; queries_with_phantom.add(q)
    follow = []
    for t in s["turns"]:
        for c in t["calls"]:
            i = c["input"] or {}
            if c["name"] in ("file_read", "content_search", "code_goto", "code_hover"):
                p = (i.get("file_path") or i.get("path") or "").replace("target/", "")
                if p in hits and t["turn"] > hits[p][0]:
                    follow.append(t["turn"])
            if c["name"] == "declaration_search" and (i.get("identifier") in queries_with_phantom) and c is not None:
                pass
    # repeated declaration_search of a query that already returned a phantom
    seen = set(); redo = 0
    for t in s["turns"]:
        for c in t["calls"]:
            if c["name"] == "declaration_search":
                q = (c["input"] or {}).get("identifier")
                if q in queries_with_phantom and q in seen: redo += 1
                seen.add(q)
    turns_touched = sorted(set(follow))
    out[pr] = dict(capped=pr in CAPPED, snapshot=sha, snapshot_exact=pr in KNOWN, ns_queries_with_base_hits=n_ns,
                   queries_returning_phantom=n_ph, phantom_queries=sorted(queries_with_phantom),
                   phantom_files=len(hits), follow_calls=len(follow), redo_decl_searches=redo,
                   turns_with_follow=len(turns_touched), follow_turns=turns_touched)
json.dump(out, open(f"{SP}/phantom.json", "w"), indent=1)
print("pr     cap  nsq ph  files follow redo turns  turns_total  sample")
for pr, v in sorted(out.items(), key=lambda kv: (not kv[1]["capped"], kv[0])):
    print(f"{pr:6} {'Y' if v['capped'] else '-'} {v['ns_queries_with_base_hits']:4} {v['queries_returning_phantom']:3} {v['phantom_files']:5} {v['follow_calls']:6} {v['redo_decl_searches']:4} {v['turns_with_follow']:5}  {len(S[[k for k in S if k[1]==pr][0]]['turns']):4}  {v['phantom_queries'][:3]}")
