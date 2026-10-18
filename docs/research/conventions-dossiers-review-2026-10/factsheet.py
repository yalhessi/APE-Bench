"""The fact sheet the 2026-10-08 adversarial round was given: each in-census probe ask on stage L/D's two
sets with reader A's entry, that entry's rank and ask count over val1000, and stage D rep 1's reach per
session; with the census bodies, how many census asks carry a ```suggestion block per entry.

Reads the stage README's files on branch `conventions-ds41` (`briefs_exact.json`, `match_D1_*`), so run
it with that branch's probe directory as the first argument. Spends nothing.

usage (repo root): python3 <this file> <conventions-ceiling probe dir> [<census bodies json>]
    the bodies are `materialise_bodies.py`'s output, never committed
"""
import glob
import json
import re
import sys
from collections import Counter

CENSUS = "results/pr_review_v5/adjudications/conventions-census-v1"
probe = sys.argv[1]
bodies = sys.argv[2] if len(sys.argv) > 2 else None

entries = {e["id"]: e for e in json.load(open(f"{CENSUS}/reader_A/codebook.json"))}
counts = Counter()
for f in sorted(glob.glob(f"{CENSUS}/reader_A/labels_b*.jsonl")):
    for line in open(f):
        pid = json.loads(line).get("principle_id")
        if pid and pid != "none":
            counts[pid] += 1
ranked = [p for p, _ in counts.most_common()]
rank = {p: i + 1 for i, p in enumerate(ranked)}
total = sum(counts.values())
print(f"reader A val1000: {total} principled asks over {len(counts)} used entries")
for k in (10, 25, 50, 100, 200):
    print(f"  top {k}: {sum(counts[p] for p in ranked[:k]) / total:.3f}")

asks = json.load(open(f"{probe}/briefs_exact.json"))["asks"]
reach = {}
for s in ("val", "post"):
    reach.update(json.load(open(f"{probe}/match_D1_{s}/unblinded.json"))["1"]["table"])
print("\nin-census probe asks: cid pr set entry rank n | X1 X2 DX1 DE1 DP1 (matcher 1) | sentence")
in_census = [(c, a) for c, a in asks.items() if a["in_census"]]
for cid, a in sorted(in_census, key=lambda x: rank.get(x[1]["r1"][0], 999)):
    e, row = a["r1"][0], reach.get(cid, {})
    cells = " ".join(f"{s}={row.get(s, '-')[:4]}" for s in ("X1", "X2", "DX1", "DE1", "DP1"))
    print(f"{cid} {a['pr']} {a['set']} {e} rank={rank.get(e, 'unused')} n={counts.get(e, 0)} | {cells} | "
          f"{entries.get(e, {}).get('principle', '')[:110]}")
band = Counter()
for _, a in in_census:
    r = rank.get(a["r1"][0], 999)
    band["top10" if r <= 10 else "11-50" if r <= 50 else "51-100" if r <= 100 else ">100"] += 1
print("\nprobe in-census asks by entry rank:", dict(band))

if bodies:
    labels = {}
    for f in sorted(glob.glob(f"{CENSUS}/reader_A/labels_*.jsonl")):
        for line in open(f):
            r = json.loads(line)
            labels[r["cid"]] = r
    with_entry, with_block = Counter(), Counter()
    for r in json.load(open(bodies))["rows"]:
        pid = (labels.get(r["cid"]) or {}).get("principle_id")
        if not pid or pid == "none":
            continue
        with_entry[pid] += 1
        with_block[pid] += bool(re.search(r"```suggestion", r.get("body") or ""))
    order = [p for p, _ in with_entry.most_common()]
    print(f"\nsuggestion blocks: {sum(with_block.values())} of {sum(with_entry.values())} asks with a reader-A entry")
    for k in (10, 50):
        n, b = sum(with_entry[p] for p in order[:k]), sum(with_block[p] for p in order[:k])
        print(f"  top {k}: {b} of {n} ({b / n:.2f})")
    for p in order[:15]:
        print(f"  {p} {with_entry[p]} asks, {with_block[p]} with a block")
