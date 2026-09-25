"""Unblind probe 3 and apply the reading rule stated in README.md before any run."""
import json, math, sys
from pathlib import Path
P = Path(__file__).parent
seal = {int(k): v for k, v in json.load(open(P / "blinding_SEALED.json")).items()}
meta = json.load(open(P / "ask_families_SEALED.json"))
fam = {int(k): v for k, v in meta["families"].items()}
AI = set(meta["ai"])
F12 = {(pr, a) for pr, d in fam.items() for a, f in d.items() if f == "F12"}
ALL = {(pr, a) for pr, d in fam.items() for a in d}
out = {}
for m in sys.argv[1:]:
    d = json.load(open(P / "match" / f"matches.{m}.json"))
    reached = {c: set() for c in ("C", "P1", "P2")}
    for a in d["asks"]:
        pr = int(a["pr"])
        for lab, cond in seal[pr].items():
            if a[lab] == "reached": reached[cond].add((pr, a["ask_id"]))
    p_any, p_both = (reached["P1"] | reached["P2"]) & F12, (reached["P1"] & reached["P2"]) & F12
    c12 = reached["C"] & F12
    nf = {c: sum(len(json.load(open(P / f"pr{pr}" / c / "findings.json"))) for pr in seal) for c in ("C", "P1", "P2")}
    reach_ok = len(p_any) >= math.ceil(0.30 * len(F12)) and len(p_any) >= 3 * len(c12)
    stable = len(p_both) / len(p_any) if p_any else 0.0
    noise = max(nf["P1"], nf["P2"]) / len(seal)
    verdict = reach_ok and stable >= 0.5 and noise <= 4
    split = {g: {"F12": len([x for x in F12 if (x[0] in AI) == (g == "ai")]),
                 "C": len([x for x in c12 if (x[0] in AI) == (g == "ai")]),
                 "P_any": len([x for x in p_any if (x[0] in AI) == (g == "ai")])} for g in ("ai", "main")}
    out[m] = {"F12_total": len(F12), "C_F12": len(c12), "P_any_F12": len(p_any), "P_both_F12": len(p_both),
              "stability": round(stable, 2), "findings": nf, "findings_per_pr_per_P_run": round(noise, 2),
              "reach_ok": reach_ok, "supported": verdict, "split": split,
              "all_asks": {"C": len(reached["C"] & ALL), "C_or_P1": len((reached["C"] | reached["P1"]) & ALL), "total": len(ALL)}}
    print(f"matcher {m}: F12 {len(F12)}; C {len(c12)}; P either {len(p_any)}, both {len(p_both)} (stability {stable:.2f}); "
          f"findings {nf} ({noise:.1f}/PR/P-run); supported: {verdict}")
    print("   split:", split, "| all asks:", out[m]["all_asks"])
json.dump(out, open(P / "unblinded.json", "w"), indent=1)
