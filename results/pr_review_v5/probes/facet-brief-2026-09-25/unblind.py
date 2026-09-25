"""Unblind the probe's matches and apply the reading rule stated in README.md before any run."""
import json, collections, sys
from pathlib import Path
P = Path(__file__).parent
seal = {int(k): v for k, v in json.load(open(P / "blinding_SEALED.json")).items()}
fam = {int(k): v for k, v in json.load(open(P / "ask_families_SEALED.json")).items()}
UNOWNED = {"F3", "F4", "F6", "F7", "F12"}
out = {}
for m in sys.argv[1:]:
    d = json.load(open(P / "match" / f"matches.{m}.json"))
    per = collections.defaultdict(lambda: collections.Counter())
    gains, losses = [], []
    for a in d["asks"]:
        pr, s = int(a["pr"]), seal[int(a["pr"])]
        v = {s["R1"]: a["R1"], s["R2"]: a["R2"]}
        f = fam[pr][a["ask_id"]]
        for c in ("X", "Y"):
            per[c][v[c]] += 1
            per[(c, pr)][v[c]] += 1
        if v["Y"] == "reached" and v["X"] != "reached": gains.append((pr, a["ask_id"], f, v["X"]))
        if v["X"] == "reached" and v["Y"] != "reached": losses.append((pr, a["ask_id"], f, v["Y"]))
    un = {c: sum(d["unmatched"][str(pr)][lab] for pr in seal for lab, cc in seal[pr].items() if cc == c) for c in ("X", "Y")}
    nfind = {c: sum(len(json.load(open(P / f"pr{pr}" / c / "findings.json"))) for pr in seal) for c in ("X", "Y")}
    gain_unowned = [g for g in gains if set(g[2].split("/")) & UNOWNED]
    delta = per["Y"]["reached"] - per["X"]["reached"]
    verdict = delta >= 4 and len(gain_unowned) >= 2 and len(losses) <= 1
    out[m] = {"reached": {c: per[c]["reached"] for c in "XY"}, "partial": {c: per[c]["partial"] for c in "XY"},
              "findings": nfind, "unmatched": un, "delta_reached": delta, "gains": gains, "losses": losses,
              "gains_in_unowned_families": len(gain_unowned), "moves_the_needle": verdict,
              "per_pr": {pr: {c: dict(per[(c, pr)]) for c in "XY"} for pr in seal}}
    print(f"matcher {m}: reached X {per['X']['reached']} / Y {per['Y']['reached']} (partial X {per['X']['partial']} / Y {per['Y']['partial']}); "
          f"findings X {nfind['X']} / Y {nfind['Y']}; unmatched X {un['X']} / Y {un['Y']}")
    print(f"  delta {delta}; gains {len(gains)} ({len(gain_unowned)} in F3/F4/F6/F7/F12); losses {len(losses)}; moves the needle: {verdict}")
    print("  gains:", gains); print("  losses:", losses)
    for pr in seal: print("  ", pr, {c: dict(per[(c, pr)]) for c in "XY"})
json.dump(out, open(P / "unblinded.json", "w"), indent=1)
