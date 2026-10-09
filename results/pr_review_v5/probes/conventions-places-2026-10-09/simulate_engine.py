"""A simulated deployable per-place engine on the ten stage F PRs, built from measured parts (added
after the places reading; an in-sample estimate, not a run).

- Selection: stage F's blind picks, 25 per PR, chosen without the asks (`briefs_applicable.json`).
- The check at the place: the ladder's blind U-arm cells, the per-sample reach of the bare sentence
  at the ask's place (`../conventions-ladder-2026-10-08/unblinded.json`). An ask counts only if its
  entry is among the PR's picks.
- Volume: the places test's decoy `departs` rate on the PR × its places × 25 picks.
- Compared with solo DeepSeek (stage D's DX1-3), one rep and two reps unioned, by matcher.

usage (repo root): python3 <this file>
"""
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
C, L = HERE.parent / "conventions-ceiling-2026-10-04", HERE.parent / "conventions-ladder-2026-10-08"
asks = json.loads((C / "briefs_exact.json").read_text())["asks"]
picks = json.loads((C / "briefs_applicable.json").read_text())["prs"]
ladder = json.loads((L / "unblinded.json").read_text())
items = json.loads((HERE / "items.json").read_text())["items"]
places, decoy, rows = defaultdict(set), defaultdict(list), defaultdict(list)
for i in items:
    places[i["pr"]].add(i["place"])
for r in map(json.loads, (HERE / "outputs.jsonl").open()):
    rows[r["name"]].append(r)
for i in items:
    if i["kind"] == "decoy":
        decoy[i["pr"]] += [bool(re.search(r"VERDICT:\s*departs", r["content"], re.I)) for r in rows[i["name"]]]
prs = sorted(int(p) for p in picks)
for m in ("1", "2"):
    dx = defaultdict(dict)
    for rnd in ("D1", "D23"):
        for tag in ("val", "post"):
            for cid, row in json.loads((C / f"match_{rnd}_{tag}" / "unblinded.json").read_text())[m]["table"].items():
                dx[cid].update({int(s[2]): v == "reached" for s, v in row.items() if s.startswith("DX")})
    inc = [c for c, a in asks.items() if a["in_census"] and a["pr"] in prs]

    def engine(c):
        a = asks[c]
        if not set(a["r1"]) & set(picks[str(a["pr"])]):
            return 0.0
        return sum(ladder[m][c][f"U{n}"] == "reached" for n in (1, 2, 3)) / 3

    pairs = ((1, 2), (1, 3), (2, 3))
    print(f"matcher {m}: {len(inc)} in-census asks; DX one rep {statistics.mean(dx[c][i] for c in inc for i in (1, 2, 3)):.3f}; "
          f"DX two reps unioned {statistics.mean(dx[c][i] or dx[c][j] for c in inc for i, j in pairs):.3f}; "
          f"engine alone {statistics.mean(engine(c) for c in inc):.3f}; "
          f"engine u DX_i {statistics.mean(1 - (1 - engine(c)) * (1 - dx[c][i]) for c in inc for i in (1, 2, 3)):.3f}")
vol = {pr: statistics.mean(decoy[pr]) * len(places[pr]) * 25 for pr in prs}
print("engine filings a PR (decoy departs x places x 25):", {pr: round(v) for pr, v in vol.items()},
      "median", round(statistics.median(vol.values())))
