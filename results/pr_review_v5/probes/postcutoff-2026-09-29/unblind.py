"""Unblind the post-cutoff probe and apply the reading rule in README.md.

Usage: python3 unblind.py <match_dir> <matcher id> [<matcher id> ...]
`match_dir` holds matches.<id>.json and ask_manifest.json (from build_match_inputs.py).
"""
import collections, json, sys
from pathlib import Path

Q = Path(__file__).parent
M = Path(sys.argv[1])
seal = json.load(open(Q / "blinding_SEALED.json"))
man = json.load(open(M / "ask_manifest.json"))
IN_FAMILY = {"v0105": "F1", "v0106": "F2", "v0107": "F2", "v0108": "F2", "v0109": "F10", "v0110": "F10",
             "v0060": "F2", "v0061": "F2", "v0062": "F1", "v0063": "F1", "v0090": "F3", "v0091": "F3",
             "v0092": "F1", "v0093": "F1", "v0094": "F1", "v0095": "F1"}
MECH = {"F1", "F2", "F3"}


def family(which, cid):
    return IN_FAMILY[cid] if which == "in" else man["families"].get(cid, "split")


def findings(pr, session):
    base = Path("results/pr_review_v5/probes/construction-demo-2026-09-29") if seal[pr]["set"] == "in" else Q
    path = base / f"pr{pr}" / session / "findings.json"
    return json.load(open(path)) if path.exists() else []


out = {}
for m in sys.argv[2:]:
    d = json.load(open(M / f"matches.{m}.json"))
    cell = {}                                   # (pr, cid, session) -> reached?
    for a in d["asks"]:
        pr = str(a["pr"])
        for label, session in seal[pr]["labels"].items():
            if label in a:
                cell[(pr, a["ask_id"], session)] = a[label] == "reached"
    res = {}
    for which in ("in", "post"):
        n = hits = 0
        fam = collections.defaultdict(lambda: [0, 0])
        for pr, ids in man["asks"][which].items():
            for cid in ids:
                for session in seal[pr]["labels"].values():
                    hit = cell.get((pr, cid, session), False)
                    n += 1; hits += hit
                    fam[family(which, cid)][0] += hit; fam[family(which, cid)][1] += 1
        mech = [sum(v[0] for f, v in fam.items() if f in MECH), sum(v[1] for f, v in fam.items() if f in MECH)]
        res[which] = {"reach": hits / n if n else None, "hits": hits, "cells": n,
                      "by_family": {f: f"{v[0]}/{v[1]}" for f, v in sorted(fam.items())},
                      "mechanical": mech}
    r = res["post"]["reach"] / res["in"]["reach"] if res["in"]["reach"] else None
    post_mech_asks = sum(1 for pr, ids in man["asks"]["post"].items() for c in ids if family("post", c) in MECH)
    r_mech = (res["post"]["mechanical"][0] / res["post"]["mechanical"][1]) / (res["in"]["mechanical"][0] / res["in"]["mechanical"][1]) \
        if post_mech_asks >= 8 and res["post"]["mechanical"][1] and res["in"]["mechanical"][0] else None
    stable = both = 0
    for pr, ids in man["asks"]["post"].items():
        for cid in ids:
            x1, x2 = cell.get((pr, cid, "X1"), False), cell.get((pr, cid, "X2"), False)
            both += x1 and x2; stable += (x1 or x2)
    controls = {pr: [len(findings(pr, s)) for s in ("X1", "X2")] for pr, e in seal.items()
                if e["set"] == "post" and not man["asks"]["post"].get(pr)}
    out[m] = {"in": res["in"], "post": res["post"], "r": r, "r_mechanical": r_mech,
              "post_mechanical_asks": post_mech_asks, "post_stability": f"{both} of {stable} reached by either run are reached by both",
              "control_findings_per_session": controls}
    print(f"matcher {m}: in {res['in']['hits']}/{res['in']['cells']} = {res['in']['reach']:.2f}; "
          f"post {res['post']['hits']}/{res['post']['cells']} = {res['post']['reach']:.2f}; r = {r:.2f}; "
          f"r (proof/interface/registration) = {r_mech if r_mech is None else round(r_mech, 2)}")
    print("   in by family:", res["in"]["by_family"]); print("   post by family:", res["post"]["by_family"])
    print("   post stability:", out[m]["post_stability"], "| controls:", controls)
rs = [out[m]["r"] for m in out]
reading = ("not mainly recall" if all(x >= 0.6 for x in rs) else
           "recall inflates the in-window reach" if all(x < 0.4 for x in rs) else "inconclusive at this size")
print("reading:", reading)
out["reading"] = reading
json.dump(out, open(Q / "unblinded.json", "w"), indent=1)
