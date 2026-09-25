"""Unblind probe 2 and apply the reading rule stated in README.md before any run."""
import json, collections, sys
from pathlib import Path
P = Path(__file__).parent
P1 = P.parent / "facet-brief-2026-09-25"  # round 1, committed beside this probe
seal = {int(k): v for k, v in json.load(open(P / "blinding_SEALED.json")).items()}
fam = {int(k): v for k, v in json.load(open(P1 / "ask_families_SEALED.json")).items()}
UNOWNED = {"F3", "F4", "F6", "F7", "F12"}
out = {}
for m in sys.argv[1:]:
    d = json.load(open(P / "match" / f"matches.{m}.json"))
    reached = collections.defaultdict(set)
    partial = collections.Counter()
    for a in d["asks"]:
        pr = int(a["pr"])
        for lab, cond in seal[pr].items():
            if a[lab] == "reached": reached[cond].add((pr, a["ask_id"]))
            if a[lab] == "partial": partial[cond] += 1
    uXH, uXX = reached["X"] | reached["H"], reached["X"] | reached["Xp"]
    gains = sorted(uXH - uXX); losses = sorted(uXX - uXH)
    gain_unowned = [g for g in gains if set(fam[g[0]][g[1]].split("/")) & UNOWNED]
    nfind = {c: sum(len(json.load(open((P1 if c == "X" else P) / f"pr{pr}" / c / "findings.json"))) for pr in seal) for c in ("X", "Xp", "H")}
    un = {c: sum(d["unmatched"][str(pr)][lab] for pr in seal for lab, cc in seal[pr].items() if cc == c) for c in ("X", "Xp", "H")}
    verdict = len(uXH) - len(uXX) >= 4 and len(gain_unowned) >= 2 and nfind["H"] <= nfind["Xp"]
    out[m] = {"reached": {c: len(reached[c]) for c in ("X", "Xp", "H")}, "partial": dict(partial),
              "union_X_H": len(uXH), "union_X_Xp": len(uXX), "gains": gains, "losses": losses,
              "gains_in_unowned_families": len(gain_unowned), "findings": nfind, "unmatched": un,
              "complement_supported": verdict,
              "per_pr": {pr: {c: sum(1 for (p, _) in reached[c] if p == pr) for c in ("X", "Xp", "H")} for pr in seal}}
    print(f"matcher {m}: reached X {len(reached['X'])}, X' {len(reached['Xp'])}, H {len(reached['H'])}; "
          f"union X+H {len(uXH)} vs X+X' {len(uXX)}; gains {len(gains)} ({len(gain_unowned)} unowned), losses {len(losses)}; "
          f"findings {nfind}; complement supported: {verdict}")
    print("  per PR:", out[m]["per_pr"])
    print("  gains:", [(g, fam[g[0]][g[1]]) for g in gains])
    print("  losses:", [(l, fam[l[0]][l[1]]) for l in losses])
json.dump(out, open(P / "unblinded.json", "w"), indent=1)
