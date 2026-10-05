"""Stage G's briefs and its retrieval reading, from the blind pinpointing pass. Calls no model.

Reads `pinpoints/pr<n>.json` (each pinpointer's `candidates.json`, copied in as written), the rules
and the codebook. Writes `briefs_candidates.json` (`{"prs": {pr: [items]}}`, what
`cli probe packets --candidates` delivers) and `candidate_retrieval.json`: for each in-census ask on
the ten PRs, whether a candidate of the PR carries an entry behind the ask (`entry`), and whether
one such candidate sits at the ask's place (`place`). The place is mechanical: an ask with no code
attached (a comment on the PR) is at its place wherever its entry fires; otherwise the candidate
must name the ask's file and a declaration whose name occurs in the code the ask is attached to.
What that misses is listed, to be read by hand.

usage (repo root): python3 <this file> [--write]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
CODEBOOK = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json")
FEEDBACK = {"val": Path("results/pr_review_v5/probes/model-gap-val-small12/feedback.json"),
            "post": Path("results/pr_review_v5/probes/postcutoff-2026-09-29/feedback.json")}
spec = json.loads((HERE / "stage_g_entries.json").read_text())
rules = {r["id"]: r for r in json.loads((HERE / "rules.json").read_text())}
principle = {e["id"]: e["principle"] for e in json.loads(CODEBOOK.read_text())}
asks = json.loads((HERE / "briefs_exact.json").read_text())["asks"]
comment = {r["cid"]: r for path in FEEDBACK.values() for r in json.loads(path.read_text())["rows"]}
pool = set(spec["pool"])

briefs, found = {}, {}
for pr in spec["prs"]:
    items = json.loads((HERE / f"pinpoints/pr{pr}.json").read_text())
    per_rule = Counter(i["id"] for i in items)
    bad = [i for i in items if i["id"] not in rules or i["status"] not in ("departs", "check")]
    if bad or max(per_rule.values(), default=0) > 3:
        raise SystemExit(f"pr{pr}: {len(bad)} invalid items, most places a rule {max(per_rule.values(), default=0)}")
    found[pr] = items
    briefs[str(pr)] = [{"id": i["id"], "file": i["file"], "declaration": i["declaration"], "fact": i["fact"].strip(),
                        "convention": principle[i["id"]], "status": i["status"],
                        "check": rules[i["id"]]["check"], "not_when": rules[i["id"]]["not_when"]}
                       for i in sorted(items, key=lambda i: (i["file"], i["declaration"], i["id"]))]

retrieval, by_hand = {}, []
for cid, a in asks.items():
    if a["pr"] not in found or not a["in_census"]:
        continue
    entries = set(a["r1"]) | set(a["r2"])
    hits = [i for i in found[a["pr"]] if i["id"] in entries]
    row = comment[cid]
    code = row.get("diff_hunk") or ""
    def at_place(item):
        if not code or not row.get("path"):
            return True
        names = [n for n in re.findall(r"[A-Za-z_][\w.'!?₀-₉]*", item["declaration"]) if len(n) > 3]
        return item["file"] == row["path"] and any(n in code or n.split(".")[-1] in code for n in names)
    retrieval[cid] = {"entry": bool(hits), "place": any(at_place(i) for i in hits)}
    if hits and not retrieval[cid]["place"]:
        by_hand.append((a["pr"], cid, row.get("path"), row.get("line"), [(i["id"], i["file"], i["declaration"]) for i in hits]))

n = len(retrieval)
print(f"in-census asks on the ten PRs: {n}")
print(f"  a candidate carries an entry behind the ask: {sum(r['entry'] for r in retrieval.values())}")
print(f"  ... and sits at the ask's place (mechanical): {sum(r['place'] for r in retrieval.values())}")
for pr, cid, path, line, hits in by_hand:
    print(f"  to read by hand: {pr} {cid} at {path}:{line} | candidates {hits}")
print("\ncandidates a PR:        total  from the pool  decoys  departs  check  rules fired")
for pr in spec["prs"]:
    items = found[pr]
    print(f"  {pr}                 {len(items):5d}  {sum(i['id'] in pool for i in items):13d}  {sum(i['id'] not in pool for i in items):6d}"
          f"  {sum(i['status'] == 'departs' for i in items):7d}  {sum(i['status'] == 'check' for i in items):5d}  {len({i['id'] for i in items}):11d}")
every = [i for items in found.values() for i in items]
print(f"  all ten               {len(every):5d}  {sum(i['id'] in pool for i in every):13d}  {sum(i['id'] not in pool for i in every):6d}"
      f"  {sum(i['status'] == 'departs' for i in every):7d}  {sum(i['status'] == 'check' for i in every):5d}")
print(f"\ngate: an entry behind the ask is delivered for {sum(r['entry'] for r in retrieval.values())} of {n} asks (sessions run at 11 or more)")
if "--write" in sys.argv:
    (HERE / "briefs_candidates.json").write_text(json.dumps({"prs": briefs}, indent=1, ensure_ascii=False) + "\n")
    (HERE / "candidate_retrieval.json").write_text(json.dumps(retrieval, indent=1) + "\n")
