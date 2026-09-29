"""The seeded reading order and batch boundaries for the census, fixed before any label.

Unit: an agreed ask. val1000: both arm-coverage readers said `ask` (1,833). Outside sets: both
stage-1 readers said anything but `not_an_ask` (801 same-window, 269 out-of-window). Order within
each set is sha256(seed, cid); the outside sets are read after val1000, against the codebook it
produced, as the held-out saturation test. Family is the agreed arm-coverage family, `A|B` when the
readers split, and `-` for the outside sets (no F-family label exists there).
usage: build_order.py <order.json>
"""
import json, glob, hashlib, sys
from pathlib import Path
ADJ = Path("results/pr_review_v5/adjudications")
SEED = "conventions-census-2026-09-29"
BATCH = 125
def load(pattern):
    out = {}
    for f in sorted(glob.glob(str(pattern))):
        for r in map(json.loads, open(f)): out[r["cid"]] = r
    return out
A = load(ADJ / "arm-coverage-val1000-2025-06-2026-03-v1/reader_A.jsonl")
B = load(ADJ / "arm-coverage-val1000-2025-06-2026-03-v1/reader_B.jsonl")
val = {c: (A[c]["family"] if A[c]["family"] == B[c]["family"] else f"{A[c]['family']}|{B[c]['family']}")
       for c in A if A[c]["is_ask"] == "ask" and B[c]["is_ask"] == "ask"}
OUT = ADJ / "design-comparison-outside-v1"
def agreed_asks(pb, pc):
    b, c = load(OUT / pb), load(OUT / pc)
    return sorted(x for x in b if x in c and b[x]["ask_kind"] != "not_an_ask" and c[x]["ask_kind"] != "not_an_ask")
sets = {"val1000": sorted(val), "outside_window": agreed_asks("reader_B.b*.jsonl", "reader_C.b*.jsonl"),
        "outside_years": agreed_asks("reader_B.w*.jsonl", "reader_C.w*.jsonl")}
def key(c): return hashlib.sha256(f"{SEED}\0{c}".encode()).hexdigest()
order, batches = [], []
for tag, prefix in (("val1000", "b"), ("outside_window", "w"), ("outside_years", "y")):
    cids = sorted(sets[tag], key=key)
    for k in range(0, len(cids), BATCH):
        bid = f"{prefix}{k // BATCH:02d}"
        batches.append({"batch": bid, "set": tag, "cids": cids[k:k + BATCH]})
        order.extend({"cid": c, "set": tag, "batch": bid, "family": val.get(c, "-")} for c in cids[k:k + BATCH])
json.dump({"seed": SEED, "batch_size": BATCH, "counts": {t: len(v) for t, v in sets.items()},
           "batches": [{"batch": b["batch"], "set": b["set"], "n": len(b["cids"])} for b in batches],
           "order": order}, open(sys.argv[1], "w"), indent=0)
print({t: len(v) for t, v in sets.items()}, "batches", [(b["batch"], len(b["cids"])) for b in batches])
