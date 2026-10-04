"""Stage F's decomposition: retrieval against application, per in-census ask on the run PRs.

Retrieval is whether an entry behind the ask is in the PR's applicable brief
(`applicable_retrieval.json`); application is whether the briefed reviewer A1 then reached the ask.
Read beside E1 (the exact brief) and X1, X2 (no brief), all judged under stage F's own seals.

usage (repo root): python3 <this file>
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
asks = json.loads((HERE / "briefs_exact.json").read_text())["asks"]
held = json.loads((HERE / "applicable_retrieval.json").read_text())
tables = {}
for tag in ("val", "post"):
    u = json.loads((HERE / f"match_F_{tag}/unblinded.json").read_text())
    for m in ("1", "2"):
        tables.setdefault(m, {}).update(u[m]["table"])
for m, table in tables.items():
    rows = {c: r for c, r in table.items() if c in held}
    hit = lambda c, s: rows[c].get(s) == "reached"
    x_any = lambda c: hit(c, "X1") or hit(c, "X2")
    print(f"\nmatcher {m}: {len(rows)} in-census asks on the run PRs")
    for name, keep in (("entry in the applicable brief", lambda c: held[c]), ("entry not in the brief", lambda c: not held[c])):
        cs = [c for c in rows if keep(c)]
        print(f"  {name}: {len(cs)} asks | A reaches {sum(hit(c, 'A1') for c in cs)} | E {sum(hit(c, 'E1') for c in cs)} "
              f"| X a session {sum(hit(c, 'X1') + hit(c, 'X2') for c in cs) / 2:.1f}")
    gains = [c for c in rows if hit(c, "E1") and not x_any(c)]
    print(f"  asks only the exact brief reached (E yes, X1 and X2 no): {len(gains)} | A reaches {sum(hit(c, 'A1') for c in gains)} "
          f"| entry in A's brief for {sum(held[c] for c in gains)}, of which A reaches {sum(hit(c, 'A1') for c in gains if held[c])}")
    print(f"  asks A reaches that neither X session does: {sum(hit(c, 'A1') and not x_any(c) for c in rows)} "
          f"| asks an X session reaches that A does not: {sum(x_any(c) and not hit(c, 'A1') for c in rows)}")
    for c in rows:
        if hit(c, "A1") != hit(c, "E1"):
            a = asks[c]
            print(f"    {a['pr']} {c} {a['family']:4} entry {'in' if held[c] else 'NOT in'} brief | A {rows[c].get('A1')} "
                  f"E {rows[c].get('E1')} X {rows[c].get('X1')},{rows[c].get('X2')}")
