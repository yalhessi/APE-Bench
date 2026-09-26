"""Prevalence and agreement for the outside-sets reading. Run from the repo root.
usage: analyse.py [b|w]  -- b: same window (packet_manifest.json, reader_*.b*.jsonl, results.json);
                          w: outside the window (packet_manifest_window.json, reader_*.w*.jsonl, results_window.json)"""
import json, glob, math, sys
TAG = sys.argv[1] if len(sys.argv) > 1 else "b"
MANIFEST = "packet_manifest.json" if TAG == "b" else "packet_manifest_window.json"
RESULTS = "results.json" if TAG == "b" else "results_window.json"
from collections import Counter, defaultdict
from pathlib import Path
D = Path(__file__).parent
man = json.load(open(D / MANIFEST)); meta = {r["cid"]: r for r in man["rows"]}
def load(reader):
    out = {}
    for f in sorted(glob.glob(str(D / f"reader_{reader}.{TAG}*.jsonl"))):
        for l in open(f):
            l = l.strip()
            if l: r = json.loads(l); out[r["cid"]] = r
    return out
B, C = load("B"), load("C")
both = sorted(B.keys() & C.keys())
def kappa(pairs):
    n = len(pairs)
    if not n: return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0
DESIGN = {"design_library", "design_siblings", "design_variant", "design_norm", "design_other"}
COMPARE = {"design_library", "design_siblings"}
out = {"n": {"B": len(B), "C": len(C), "both": len(both), "packet": len(meta)}}
pairs = [(B[c]["ask_kind"], C[c]["ask_kind"]) for c in both]
out["stage1"] = {"kappa": kappa(pairs), "agreement": round(sum(a == b for a, b in pairs) / len(pairs), 3) if pairs else None,
                 "B": dict(Counter(a for a, _ in pairs).most_common()), "C": dict(Counter(b for _, b in pairs).most_common()),
                 "agreed": dict(Counter(a for a, b in pairs if a == b).most_common())}
# coarse agreement: ask vs not, design vs not, compare vs not
def coarse(k): return "not_an_ask" if k == "not_an_ask" else ("compare" if k in COMPARE else ("design" if k in DESIGN else "other"))
cp = [(coarse(a), coarse(b)) for a, b in pairs]
out["stage1_coarse"] = {"kappa": kappa(cp), "agreed": dict(Counter(a for a, b in cp if a == b).most_common()), "split": sum(a != b for a, b in cp)}
asks_B = [c for c in both if B[c]["ask_kind"] != "not_an_ask"]; asks_C = [c for c in both if C[c]["ask_kind"] != "not_an_ask"]
asks_both = [c for c in both if B[c]["ask_kind"] != "not_an_ask" and C[c]["ask_kind"] != "not_an_ask"]
comp_agreed = [c for c in both if B[c]["ask_kind"] in COMPARE and C[c]["ask_kind"] in COMPARE]
comp_either = [c for c in both if B[c]["ask_kind"] in COMPARE or C[c]["ask_kind"] in COMPARE]
design_agreed = [c for c in both if B[c]["ask_kind"] in DESIGN and C[c]["ask_kind"] in DESIGN]
def share(k, n): return {"k": k, "n": n, "share": round(k / n, 4) if n else None, "ci95": [round(x, 4) for x in wilson(k, n)] if n else None}
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)
out["prevalence"] = {
    "asks_agreed": len(asks_both), "asks_B": len(asks_B), "asks_C": len(asks_C),
    "design_agreed_over_asks_agreed": share(len(design_agreed), len(asks_both)),
    "compare_agreed_over_asks_agreed": share(len(comp_agreed), len(asks_both)),
    "compare_either_over_asks_either": share(len(comp_either), len(set(asks_B) | set(asks_C))),
    "prs_with_compare_agreed": len({meta[c]["pr"] for c in comp_agreed}), "prs_in_sample": len(man["prs"]),
    "compare_agreed_by_ai": dict(Counter("ai" if meta[c]["ai"] else "human" for c in comp_agreed)),
    "asks_agreed_by_ai": dict(Counter("ai" if meta[c]["ai"] else "human" for c in asks_both)),
    "compare_agreed_by_month": dict(sorted(Counter(meta[c]["month"] for c in comp_agreed).items())),
    "asks_agreed_by_month": dict(sorted(Counter(meta[c]["month"] for c in asks_both).items())),
}
# stage 2 on agreed compare asks
s2 = {}
for f in ("analogue_named", "findable_by", "wrong_analogue_plausible"):
    pp = [(B[c].get(f), C[c].get(f)) for c in comp_agreed]
    s2[f] = {"n": len(pp), "kappa": kappa(pp), "agreed": dict(Counter(a for a, b in pp if a == b).most_common()), "split": sum(a != b for a, b in pp),
             "B": dict(Counter(a for a, _ in pp).most_common()), "C": dict(Counter(b for _, b in pp).most_common())}
out["stage2_on_agreed_compare"] = s2
out["stage2_findable_either"] = dict(Counter(x.get("findable_by") for c in comp_either for x in (B[c], C[c]) if x.get("findable_by")).most_common())
out["wrong_analogue_yes_either"] = sorted(c for c in comp_either if B[c].get("wrong_analogue_plausible") == "yes" or C[c].get("wrong_analogue_plausible") == "yes")
out["compare_agreed_cids"] = comp_agreed
json.dump(out, open(D / RESULTS, "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in out.items() if k not in ("compare_agreed_cids",)}, indent=1, ensure_ascii=False))
