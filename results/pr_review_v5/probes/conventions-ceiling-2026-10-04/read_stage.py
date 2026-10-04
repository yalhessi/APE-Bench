"""The stage's reading: per-session reach on in-census asks, per matcher, per set and pooled.

Reads, per set, `match_<stage>_<set>/unblinded.json` (`cli probe unblind`: the per-ask table of each
matcher) and `match_<stage>_<set>/session_stats.json` (findings per session), and
`briefs_exact.json` (which asks are in census). Per-session reach of a condition is its `reached`
cells over (asks x its sessions); a condition is a session label less its digits (LB1 -> LB).

usage (repo root): python3 <this file> <stage, e.g. L> <treated condition> <control condition>
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
stage, treated, control = sys.argv[1:4]
asks = json.loads((HERE / "briefs_exact.json").read_text())["asks"]


def condition(session: str) -> str:
    return session.rstrip("0123456789")


def cells(table: dict, cond: str, keep) -> tuple:
    hit = total = 0
    for cid, row in table.items():
        if not keep(asks[cid]):
            continue
        for session, value in row.items():
            if condition(session) == cond:
                hit += value == "reached"
                total += 1
    return hit, total


def rate(pair: tuple) -> str:
    return f"{pair[0]:3}/{pair[1]:3} = {pair[0] / pair[1]:.2f}" if pair[1] else "  -"


sets = {tag: (json.loads((HERE / f"match_{stage}_{tag}/unblinded.json").read_text()),
              json.loads((HERE / f"match_{stage}_{tag}/session_stats.json").read_text()))
        for tag in ("val", "post") if (HERE / f"match_{stage}_{tag}/unblinded.json").exists()}
matchers = sorted(k for k in next(iter(sets.values()))[0] if isinstance(next(iter(sets.values()))[0][k], dict) and "table" in next(iter(sets.values()))[0][k])
conds = sorted({condition(s) for u, _ in sets.values() for row in u[matchers[0]]["table"].values() for s in row})
for scope, keep in (("in-census asks", lambda a: a["in_census"]), ("out-of-census asks", lambda a: not a["in_census"]),
                    ("all asks", lambda a: True)):
    print(f"\n== {scope} ==")
    for m in matchers:
        pooled = {c: [0, 0] for c in conds}
        for tag, (u, _) in sets.items():
            got = {c: cells(u[m]["table"], c, keep) for c in conds}
            for c in conds:
                pooled[c][0] += got[c][0]
                pooled[c][1] += got[c][1]
            print(f"{m} {tag:6}", " | ".join(f"{c} {rate(got[c])}" for c in conds))
        print(f"{m} pooled", " | ".join(f"{c} {rate(tuple(pooled[c]))}" for c in conds), end="")
        t, k = pooled[treated], pooled[control]
        if t[1] and k[1]:
            print(f" | {treated} - {control} = {t[0] / t[1] - k[0] / k[1]:+.3f}")
        else:
            print()

print("\n== asks reached per finding, PRs with asks, all asks ==")
for m in matchers:
    for c in conds:
        hits = found = 0
        for tag, (u, stats) in sets.items():
            hits += cells(u[m]["table"], c, lambda a: True)[0]
            found += sum(st["findings"] for per_pr in stats.values() for s, st in per_pr.items() if condition(s) == c)
        print(f"{m} {c}: {hits} reached / {found} findings = {hits / found:.3f}" if found else f"{m} {c}: no findings")
for tag, (u, _) in sets.items():
    print(f"\n{tag} agreement:", u.get("agreement"))
