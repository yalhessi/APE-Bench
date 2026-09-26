"""Rebuild the reader packet: the 95 F6 asks with agreed reference, from the validation feedback
store (bodies are not committed; ids are). Run from the repo root."""
import json, glob, sys
from collections import defaultdict
FEEDBACK = sys.argv[1]  # the val1000 feedback json (dict with "rows": [{cid, body, diff_hunk, ...}])
OUT = sys.argv[2]
D = "results/pr_review_v5/adjudications/facet-relabel-val1000-v1/"
A = {r["cid"]: r for r in map(json.loads, open(D + "reader_A.jsonl"))}
B = {r["cid"]: r for r in map(json.loads, open(D + "reader_B.jsonl"))}
fam = defaultdict(dict)
for f in glob.glob("results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/*.jsonl"):
    for r in map(json.loads, open(f)):
        if "cid" in r and "family" in r: fam[r["cid"]][f] = r["family"]
agreed = {c: list(v.values())[0] for c, v in fam.items() if len(set(v.values())) == 1 and len(v) >= 2}
rows = {r["cid"]: r for r in json.load(open(FEEDBACK))["rows"]}
order = ["variant", "library", "siblings", "norms", "mechanism", "intent", "process", "module_graph"]
packet = [c for c in sorted(A.keys() & B.keys()) if agreed.get(c) == "F6" and A[c]["reference"] == B[c]["reference"]]
with open(OUT, "w") as f:
    for ref in order:
        grp = [c for c in packet if A[c]["reference"] == ref]
        if not grp: continue
        f.write(f"\n\n# reference = {ref} ({len(grp)})\n")
        for c in grp:
            r = rows[c]; parent = rows.get(r.get("reply_to_cid")) if r.get("reply_to_cid") else None
            f.write(f"\n## {c}  PR {r['pr']} ({'AI' if r['ai'] else 'human'}) — {r['pr_title'][:80]}\n{r['path']}:{r['line']}  by {r['author']}  object={A[c]['object']} warrant={A[c]['warrant']}\n")
            if parent: f.write(f"> (in reply to) {parent['body'][:400]}\n")
            f.write(f"**ASK:** {r['body'][:1200]}\n```\n{(r['diff_hunk'] or '')[-900:]}\n```\n")
json.dump([{"cid": c, "reference": A[c]["reference"], "pr": rows[c]["pr"], "path": rows[c]["path"]} for c in packet],
          open(OUT.rsplit(".", 1)[0] + "_manifest.json", "w"), indent=1)
