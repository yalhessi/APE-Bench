"""Unblind test (b), or the arms condition, and apply the reading rule in README.md.

Usage: python3 unblind.py [--seal <file>] [--out <file>] <match_dir> <matcher id> [<matcher id> ...]
`match_dir` holds matches.<id>.json and session_stats.json (from build_match_inputs.py). The default
seal is test (b)'s `blinding_SEALED.json` and the default output `unblinded.json`. A seal holding the
lead runs (L1, L2) is the arms condition, and one holding Gr1, Gr2 is test (d), each read by its own
pre-registered rule.
"""
import json, sys
from pathlib import Path

G = Path(__file__).parent
args = sys.argv[1:]
seal_name, out_name = "blinding_SEALED.json", "unblinded.json"
while args and args[0].startswith("--"):
    seal_name, out_name = (args[1], out_name) if args[0] == "--seal" else (seal_name, args[1])
    args = args[2:]
M, MATCHERS = Path(args[0]), args[1:]
seal = json.load(open(G / seal_name))
man = json.load(open(Path("results/pr_review_v5/probes/postcutoff-2026-09-29/match/ask_manifest.json")))
stats = json.load(open(M / "session_stats.json"))
PASS34 = {"F1", "F2", "F3", "F4", "F5", "F6", "F7"}
asks = [(pr, cid) for pr in seal for cid in man["asks"]["post"][pr]]
scope = [(pr, cid) for pr, cid in asks if man["families"].get(cid) in PASS34]


def load(m):
    """{(pr, ask, session): (value, finding index)} for one matcher."""
    d = json.load(open(M / f"matches.{m}.json"))
    return {(str(a["pr"]), a["ask_id"], session): (a.get(label), a.get(f"{label}_finding"))
            for a in d["asks"] for label, session in seal[str(a["pr"])].items()}


def reach(cells, sessions, items, published_only=False):
    hits = total = 0
    for pr, cid in items:
        for s in sessions:
            value, i = cells.get((pr, cid, s), (None, None))
            ok = value == "reached"
            if ok and published_only:
                ok = i in stats[pr][s].get("published", [])
            hits += ok
            total += 1
    return hits / total if total else None


def arms_reading():
    out = {}
    for m in MATCHERS:
        cells = load(m)
        r = {k: reach(cells, (f"{k}1", f"{k}2"), asks) for k in "LGX"}
        out[m] = {"reach_all16": r,
                  "reach_L_published_only": reach(cells, ("L1", "L2"), asks, published_only=True),
                  "reach_scope": {k: reach(cells, (f"{k}1", f"{k}2"), scope) for k in "LGX"},
                  "findings_per_pr_per_run": {k: sum(stats[pr][s]["findings"] for pr in seal for s in (f"{k}1", f"{k}2"))
                                              / (2 * len(seal)) for k in "LGX"},
                  "L_published_per_pr_per_run": sum(len(stats[pr][s]["published"]) for pr in seal for s in ("L1", "L2"))
                                                / (2 * len(seal)),
                  "reading": ("recovers at least half the gap" if r["L"] >= 0.30 else
                              "does not help; the model dominates" if r["L"] <= 0.18 else "partial")}
        print(f"matcher {m}: reach(16) L {r['L']:.2f} G {r['G']:.2f} X {r['X']:.2f}; "
              f"L published-only {out[m]['reach_L_published_only']:.2f}; scope({len(scope)}) "
              + " ".join(f"{k} {v:.2f}" for k, v in out[m]["reach_scope"].items())
              + f" | {out[m]['reading']}")
    readings = {out[m]["reading"] for m in MATCHERS}
    out["arms_reading"] = readings.pop() if len(readings) == 1 else "the matchers disagree"
    print("arms condition:", out["arms_reading"])
    json.dump(out, open(G / out_name, "w"), indent=1)


def comparison_lookups(sessions):
    """Mean library lookups of comparison objects per session, by inspect_sessions' classification."""
    sys.path.insert(0, str(G))
    import inspect_sessions as I
    posts = I.post_images()
    n = hits = 0
    for pr in I.PRS:
        for s in sessions:
            n += 1
            hits += sum(1 for tool, args in I.session_calls(s, pr)
                        if tool in I.SEARCH and I.lookup_side(tool, args, posts[pr]) == "library")
    return hits / n


def reasoning_reading():
    """Test (d): reach crossed with comparison lookups, the rule in README.md."""
    looks = comparison_lookups(("Gr1", "Gr2"))
    out = {"Gr_comparison_lookups_per_session": looks}
    for m in MATCHERS:
        cells = load(m)
        r = {k: reach(cells, (f"{k}1", f"{k}2"), asks) for k in ("Gr", "G", "X")}
        high, low = r["Gr"] >= 0.30, r["Gr"] <= 0.18
        reading = ("partial" if not (high or low) else
                   "reasoning is the lever: it restores both the looking and the reaching" if high and looks >= 8 else
                   "reasoning is the lever, by inference from what is in view" if high else
                   "reasoning makes it look and the model still does not conclude" if looks >= 8 else
                   "reasoning does not move this reviewer; the gap is the model")
        out[m] = {"reach_all16": r, "reach_scope": {k: reach(cells, (f"{k}1", f"{k}2"), scope) for k in ("Gr", "G", "X")},
                  "findings_per_pr_per_run": {k: sum(stats[pr][s]["findings"] for pr in seal for s in (f"{k}1", f"{k}2"))
                                              / (2 * len(seal)) for k in ("Gr", "G", "X")},
                  "reading": reading}
        print(f"matcher {m}: reach(16) Gr {r['Gr']:.2f} G {r['G']:.2f} X {r['X']:.2f}; scope({len(scope)}) "
              + " ".join(f"{k} {v:.2f}" for k, v in out[m]["reach_scope"].items())
              + f"; Gr comparison lookups {looks:.1f} | {reading}")
    readings = {out[m]["reading"] for m in MATCHERS}
    out["reasoning_reading"] = readings.pop() if len(readings) == 1 else "the matchers disagree"
    print("test (d):", out["reasoning_reading"])
    json.dump(out, open(G / out_name, "w"), indent=1)


if any(s.startswith("Gr") for labels in seal.values() for s in labels.values()):
    reasoning_reading()
    sys.exit(0)
if any(s.startswith("L") for labels in seal.values() for s in labels.values()):
    arms_reading()
    sys.exit(0)

out = {}
for m in MATCHERS:
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
qs = [out[m]["q"] for m in MATCHERS]
out["model_gap_reading"] = ("markedly less" if all(x <= 0.5 for x in qs) else
                            "comparable" if all(x >= 0.8 for x in qs) else "inconclusive at this size")
out["construction_reading"] = "supported" if all(out[m]["construction_supported"] for m in MATCHERS) else "not supported"
print("model gap:", out["model_gap_reading"], "| construction brief:", out["construction_reading"])
json.dump(out, open(G / out_name, "w"), indent=1)
