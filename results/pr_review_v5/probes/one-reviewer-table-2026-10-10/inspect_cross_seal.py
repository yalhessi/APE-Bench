"""Inspection 1 (2026-10-11): the same sessions under the older seals and the table's, per matcher --
reached cells old and new, and the asks gained and lost. Checks that harness-blind inputs and
13-session seals change what the matchers credit no more for AP than for anyone.

usage (repo root): python3 <this file> match_AP_val,match_AP_post match_D1_val,match_D1_post,match_D23_val,match_D23_post
"""
import json, sys
from pathlib import Path
P = Path("results/pr_review_v5/probes/conventions-ceiling-2026-10-04")
T = Path("results/pr_review_v5/probes/one-reviewer-table-2026-10-10")
ASKS = {**json.loads((P / "briefs_exact.json").read_text())["asks"], **json.loads((P / "asks_dev_census.json").read_text())["asks"]}
def tab(d, m):
    u = json.loads((d / "unblinded.json").read_text())
    return u[m]["table"]
new = {}
for m in "12":
    new[m] = {}
    for d in (T/"match_P14_val", T/"match_P14_post"):
        new[m].update(tab(d, m))
for old in sys.argv[1:]:
    for m in "12":
        o = {}
        for d in old.split(","):
            o.update(tab(P/d, m))
        sessions = sorted({s for r in o.values() for s in r})
        cids = sorted(o)
        missing = [c for c in cids if c not in new[m]]
        prs = sorted({ASKS[c]["pr"] for c in cids})
        print(f"== {old} m{m}: {len(cids)} asks on {len(prs)} PRs; missing in new {len(missing)}")
        for s in sessions:
            ho = sum(o[c][s] == "reached" for c in cids)
            hn = sum(new[m][c].get(s) == "reached" for c in cids)
            po = sum(o[c][s] == "partial" for c in cids)
            pn = sum(new[m][c].get(s) == "partial" for c in cids)
            gain = sorted(c for c in cids if new[m][c].get(s) == "reached" and o[c][s] != "reached")
            loss = sorted(c for c in cids if new[m][c].get(s) != "reached" and o[c][s] == "reached")
            print(f"  {s:4} old {ho:2} (p{po}) new {hn:2} (p{pn})  +{len(gain)} -{len(loss)}  gain {gain} loss {loss}")
