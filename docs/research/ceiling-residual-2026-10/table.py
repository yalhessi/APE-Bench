"""Every matched session at every probe ask: which asks no ceiling condition reaches.

Reads every `match_*/unblinded.json` of the conventions ceiling probe and of the generation-suppression
probe (the latter from branch `generation-suppression`, given as a directory of its `match_*`
folders), merges sessions over rounds (an anchor re-matched in a later round counts as reached if any
round reached it), and prints per ask: census status, reader 1's entry and its val1000 rank, the
unbriefed sessions that reached it, and the ceiling sessions that did -- those briefed with the
exact conventions in any form (E1, GE, GD, GR, DE, DP, LE, and the targeted Claude D/G runs on 42184).
An ask reached by no ceiling session on either matcher is the residual. Spends nothing.

usage (repo root): python3 <this file> <ceiling probe dir> <generation-suppression match dirs parent>
  e.g. for d in match_W_val match_W_post match_28649 match_42184; do mkdir -p gs/$d; git show \
    generation-suppression:results/pr_review_v5/probes/generation-suppression-2026-10-06/$d/unblinded.json > gs/$d/unblinded.json; done
"""
import glob
import json
import sys
from collections import Counter, defaultdict

P, GS = sys.argv[1], sys.argv[2]
asks = json.load(open(f"{P}/briefs_exact.json"))["asks"]
cells = defaultdict(lambda: defaultdict(dict))
for f in sorted(glob.glob(f"{P}/match_*/unblinded.json")) + sorted(glob.glob(f"{GS}/*/unblinded.json")):
    tag = f.split("/")[-2]
    u = json.load(open(f))
    for m in ("1", "2"):
        for cid, row in (u.get(m) or {}).get("table", {}).items():
            for s, v in row.items():
                key = s if not s.startswith(("GE", "GD")) or "W" in tag else f"{s}@{tag}"
                if cells[cid][key].get(m) != "reached":
                    cells[cid][key][m] = v
feedback = {r["cid"]: r for f in ("results/pr_review_v5/probes/model-gap-val-small12/feedback.json",
                                  "results/pr_review_v5/probes/postcutoff-2026-09-29/feedback.json")
            for r in json.load(open(f))["rows"]}
counts = Counter()
for f in sorted(glob.glob("results/pr_review_v5/adjudications/conventions-census-v1/reader_A/labels_b*.jsonl")):
    for line in open(f):
        p = json.loads(line).get("principle_id")
        if p and p != "none":
            counts[p] += 1
rank = {p: i + 1 for i, (p, _) in enumerate(counts.most_common())}
unbriefed = lambda s: s.startswith(("X", "DX", "GB", "LB"))
ceiling = lambda s: (s.startswith(("E1", "GE", "GD", "GR", "DE", "DP", "LE"))
                     or s.split("@")[0] in ("D1", "D2", "D3", "G2", "G3"))
reached = lambda cid, pred: sorted(s for s, d in cells[cid].items() if pred(s) and "reached" in d.values())
residual = []
print(f"{'cid':6} {'pr':6} {'in':3} {'entry':10} {'rank':5} | unbriefed reached | ceiling reached (any session, either matcher)")
for cid in sorted(asks, key=lambda c: (asks[c]["pr"], c)):
    a = asks[cid]
    entry = (a["r1"] or ["-"])[0] if a["in_census"] else "-"
    ub, ce = reached(cid, unbriefed), reached(cid, ceiling)
    if not ce:
        residual.append(cid)
    print(f"{cid:6} {a['pr']:6} {'in' if a['in_census'] else 'OUT':3} {entry:10} {rank.get(entry, '-')!s:5} | "
          f"{len(ub):2} {','.join(ub)[:40]:40} | {len(ce):2} {','.join(ce)[:60]}{'' if ce else '  <== RESIDUAL'}")
print(f"\nRESIDUAL (no ceiling session reached it on either matcher): {len(residual)}")
for cid in residual:
    print(f"  {cid} pr{asks[cid]['pr']}: {feedback[cid]['body'][:200]!r}")
