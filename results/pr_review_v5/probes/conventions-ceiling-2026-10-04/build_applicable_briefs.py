"""The applicable brief of each PR, from the blind selectors' `selected.json`, and how much of the
exact brief it holds.

Writes `selectors/pr<N>.json` (each selection as written) and `briefs_applicable.json`
(`{"prs": {pr: [ids]}}`, what `cli probe packets --conventions` reads). Then, with the asks, which the
selectors never saw: for each in-census ask on these PRs, whether an entry behind it is in the brief.

usage (repo root): python3 <this file> <selector scratch dir>
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
CODEBOOK = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json")
ids = {e["id"] for e in json.loads(CODEBOOK.read_text())}
exact = json.loads((HERE / "briefs_exact.json").read_text())
briefs, held = {}, {}
(HERE / "selectors").mkdir(exist_ok=True)
for folder in sorted(Path(sys.argv[1]).glob("pr*")):
    rows = json.loads((folder / "selected.json").read_text())
    picked = [r["id"] for r in rows]
    assert all(set(r) == {"id", "where", "why"} for r in rows), f"{folder.name}: keys"
    assert set(picked) <= ids and len(set(picked)) == len(picked) <= 25, f"{folder.name}: ids"
    pr = folder.name[2:]
    briefs[pr] = picked
    (HERE / "selectors" / f"{folder.name}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
(HERE / "briefs_applicable.json").write_text(json.dumps({"prs": briefs}, indent=1) + "\n")

asks = {c: a for c, a in exact["asks"].items() if a["in_census"] and str(a["pr"]) in briefs}
for cid, a in asks.items():
    held[cid] = bool(set(a["r1"] + a["r2"]) & set(briefs[str(a["pr"])]))
print("entries a brief:", {pr: len(v) for pr, v in briefs.items()})
print(f"in-census asks whose entry the applicable brief holds: {sum(held.values())} of {len(held)}")
for pr in briefs:
    mine = [c for c in asks if str(asks[c]["pr"]) == pr]
    wanted = sorted(set(exact["prs"][pr]))
    print(f"  {pr}: asks {sum(held[c] for c in mine)}/{len(mine)} | exact entries selected "
          f"{sorted(set(wanted) & set(briefs[pr]))} of {wanted}")
(HERE / "applicable_retrieval.json").write_text(json.dumps(held, indent=1) + "\n")
