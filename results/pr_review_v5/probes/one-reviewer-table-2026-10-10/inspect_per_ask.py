"""Inspection 2 (2026-10-11): per PR and per ask, each row's hits; the asks where DX and AP differ
(hits of 3 reps) beside the other rows; AP and DX hits by family.

usage (repo root): python3 <this file> match_P14_val,match_P14_post [matcher]   or   ... match_D12
"""
import json, sys
from pathlib import Path
from collections import defaultdict
P = Path("results/pr_review_v5/probes/conventions-ceiling-2026-10-04")
T = Path("results/pr_review_v5/probes/one-reviewer-table-2026-10-10")
ASKS = {**json.loads((P / "briefs_exact.json").read_text())["asks"], **json.loads((P / "asks_dev_census.json").read_text())["asks"]}
dirs = sys.argv[1].split(",")
m = sys.argv[2] if len(sys.argv) > 2 else "1"
tab = {}
stats = {}
for d in dirs:
    u = json.loads((T / d / "unblinded.json").read_text())
    tab.update(u[m]["table"])
    stats.update(json.loads((T / d / "session_stats.json").read_text()))
rows = sorted({s.rstrip("0123456789") for r in tab.values() for s in r})
def cnt(c, row):
    return sum(v == "reached" for s, v in tab[c].items() if s.rstrip("0123456789") == row)
byp = defaultdict(list)
for c in sorted(tab): byp[str(ASKS[c]["pr"])].append(c)
hdr = ["X", "OP", "T", "TA", "GPT", "DX", "AP"]
hdr = [h for h in hdr if h in rows]
nreps = {h: len({s for r in tab.values() for s in r if s.rstrip('0123456789') == h}) for h in hdr}
print("per PR: asks, then each row's mean hits a session (and findings a session)")
print("pr     n  " + " ".join(f"{h:>11}" for h in hdr))
for pr in sorted(byp, key=int):
    cs = byp[pr]
    cells = []
    for h in hdr:
        hits = sum(cnt(c, h) for c in cs) / nreps[h]
        f = [v["findings"] for s, v in stats[pr].items() if s.rstrip("0123456789") == h]
        cells.append(f"{hits:4.1f}({sum(f)/len(f):4.1f})")
    print(f"{pr:6} {len(cs):2}  " + " ".join(f"{x:>11}" for x in cells))
print("\nasks where DX and AP differ (hits of 3 reps), with X, OP/T, GPT:")
for c in sorted(tab):
    if "AP" in rows and cnt(c, "DX") != cnt(c, "AP"):
        a = ASKS[c]
        print(f"  {c} pr{a['pr']} {a['family']:4} census={a['in_census']!s:5} DX {cnt(c,'DX')} AP {cnt(c,'AP')} | " + " ".join(f"{h} {cnt(c,h)}/{nreps[h]}" for h in hdr if h not in ('DX','AP')))
# family aggregates
fam = defaultdict(lambda: defaultdict(int))
for c in tab:
    f = ASKS[c]["family"]
    fam[f]["n"] += 1
    for h in ("DX", "AP"):
        if h in rows: fam[f][h] += cnt(c, h)
print("\nfamily: n, DX hits (of 3n), AP hits")
for f, d in sorted(fam.items()):
    print(f"  {f:4} n={d['n']:2} DX {d.get('DX',0):2} AP {d.get('AP',0):2}")
for k in (True, False):
    cs = [c for c in tab if ASKS[c]["in_census"] == k]
    print(f"in_census={k}: n={len(cs)} DX {sum(cnt(c,'DX') for c in cs)} AP {sum(cnt(c,'AP') for c in cs) if 'AP' in rows else '-'}")
