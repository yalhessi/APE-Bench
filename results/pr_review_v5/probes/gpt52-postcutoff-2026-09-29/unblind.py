"""Unblind test (b) and apply the reading rule in README.md.

Usage: python3 unblind.py <match_dir> <matcher id> [<matcher id> ...]
`match_dir` holds matches.<id>.json and session_stats.json (from build_match_inputs.py).
"""
import json, sys
from pathlib import Path

G = Path(__file__).parent
M = Path(sys.argv[1])
seal = json.load(open(G / "blinding_SEALED.json"))
man = json.load(open(Path("results/pr_review_v5/probes/postcutoff-2026-09-29/match/ask_manifest.json")))
stats = json.load(open(M / "session_stats.json"))
PASS34 = {"F1", "F2", "F3", "F4", "F5", "F6", "F7"}
asks = [(pr, cid) for pr in seal for cid in man["asks"]["post"][pr]]
scope = [(pr, cid) for pr, cid in asks if man["families"].get(cid) in PASS34]

out = {}
for m in sys.argv[2:]:
    d = json.load(open(M / f"matches.{m}.json"))
    reached = {}
    for a in d["asks"]:
        for label, session in seal[str(a["pr"])].items():
            reached[(str(a["pr"]), a["ask_id"], session)] = a.get(label) == "reached"

    def reach(sessions, items):
        cells = [(pr, cid, s) for pr, cid in items for s in sessions]
        return sum(reached.get(c, False) for c in cells) / len(cells) if cells else None

    def stable(sessions, items):
        return {(pr, cid) for pr, cid in items if all(reached.get((pr, cid, s), False) for s in sessions)}

    rg, rk, rx = reach(("G1", "G2"), asks), reach(("K1", "K2"), asks), reach(("X1", "X2"), asks)
    q = rg / rx if rx else None
    g_st, k_st = stable(("G1", "G2"), scope), stable(("K1", "K2"), scope)
    findings = {s: sum(stats[pr][s]["findings"] for pr in seal) / len(seal) for s in ("G1", "G2", "K1", "K2", "X1", "X2")}
    k_per_run = (findings["K1"] + findings["K2"]) / 2; g_per_run = (findings["G1"] + findings["G2"]) / 2
    construction = len(k_st) - len(g_st) >= 2 and k_per_run <= g_per_run
    compiles = {s: sum(stats[pr][s]["compiles"] for pr in seal) / len(seal) for s in ("G1", "G2", "K1", "K2", "X1", "X2")}
    out[m] = {"reach_all16": {"G": rg, "K": rk, "X_claude": rx}, "q": q,
              "scope_asks": len(scope), "reach_scope": {"G": reach(("G1", "G2"), scope), "K": reach(("K1", "K2"), scope),
                                                         "X_claude": reach(("X1", "X2"), scope)},
              "stable_scope": {"G": sorted(map(list, g_st)), "K": sorted(map(list, k_st))},
              "construction_supported": construction,
              "findings_per_pr": findings, "compiles_per_session": compiles}
    print(f"matcher {m}: reach(16) G {rg:.2f} K {rk:.2f} Claude X {rx:.2f}; q = {q:.2f} | "
          f"scope({len(scope)}) stable G {len(g_st)} K {len(k_st)}; findings/PR/run G {g_per_run:.1f} K {k_per_run:.1f}; "
          f"construction supported: {construction}")
    print("   compiles per session:", {k: round(v, 1) for k, v in compiles.items()})
qs = [out[m]["q"] for m in sys.argv[2:]]
out["model_gap_reading"] = ("markedly less" if all(x <= 0.5 for x in qs) else
                            "comparable" if all(x >= 0.8 for x in qs) else "inconclusive at this size")
out["construction_reading"] = "supported" if all(out[m]["construction_supported"] for m in sys.argv[2:]) else "not supported"
print("model gap:", out["model_gap_reading"], "| construction brief:", out["construction_reading"])
json.dump(out, open(G / "unblinded.json", "w"), indent=1)
