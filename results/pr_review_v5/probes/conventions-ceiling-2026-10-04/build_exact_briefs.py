"""The exact brief of each PR: the union of the two readers' entries over the PR's asks.

Reads `readers/labels_1.jsonl` and `readers/labels_2.jsonl` (the assign-only reading), checks each
against the batch and the codebook, and writes `briefs_exact.json`:
`{"prs": {pr: [ids]}, "asks": {cid: {"pr", "family", "r1": [ids], "r2": [ids], "in_census"}}}`.
An ask is in census when either reader assigned it an entry. Prints the in-census share per reader
and in union, the readers' agreement, and every PR's brief.

usage (repo root): python3 <this file> [--print-briefs]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
CODEBOOK = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json")
PROBES = Path("results/pr_review_v5/probes")
SETS = {"val": PROBES / "model-gap-val-small12/asks.json", "post": PROBES / "postcutoff-2026-09-29/asks.json"}
REASONS = {"out_of_census", "specific", "unreadable"}

codebook = {e["id"]: e["principle"] for e in json.loads(CODEBOOK.read_text())}
order = re.findall(r"^## (\S+)  PR (\d+)", (HERE / "reader_batch.md").read_text(), flags=re.M)
family, which = {}, {}
for tag, path in SETS.items():
    agreed = json.loads(path.read_text())
    family.update(agreed["families"])
    which.update({cid: tag for cids in agreed["asks"].values() for cid in cids})


def load(n: int) -> dict:
    rows = [json.loads(line) for line in (HERE / f"readers/labels_{n}.jsonl").read_text().splitlines() if line.strip()]
    assert [r["cid"] for r in rows] == [cid for cid, _ in order], f"reader {n}: cids are not the batch, in order"
    for r in rows:
        ids = [i for i in (r["principle_id"], r["second_principle_id"]) if i and i != "none"]
        assert all(i in codebook for i in ids), f"reader {n} {r['cid']}: unknown entry in {ids}"
        assert (r["principle_id"] == "none") == (r["none_reason"] in REASONS), f"reader {n} {r['cid']}: none_reason"
        assert r["principle_id"] != "none" or not r["second_principle_id"], f"reader {n} {r['cid']}: second without first"
        r["ids"] = ids
    return {r["cid"]: r for r in rows}


r1, r2 = load(1), load(2)
asks = {cid: {"pr": int(pr), "set": which[cid], "family": family[cid], "r1": r1[cid]["ids"], "r2": r2[cid]["ids"],
              "r1_none": r1[cid]["none_reason"], "r2_none": r2[cid]["none_reason"],
              "in_census": bool(r1[cid]["ids"] or r2[cid]["ids"])} for cid, pr in order}
prs = {}
for a in asks.values():
    prs.setdefault(a["pr"], set()).update(a["r1"] + a["r2"])
briefs = {str(pr): sorted(ids) for pr, ids in sorted(prs.items())}
(HERE / "briefs_exact.json").write_text(json.dumps({"prs": briefs, "asks": asks}, indent=1) + "\n")

n = len(asks)
for tag in ("val", "post", None):
    rows = [a for a in asks.values() if tag in (None, a["set"])]
    print(f"{tag or 'both':5} asks {len(rows):2} | reader 1 assigned {sum(bool(a['r1']) for a in rows):2} | "
          f"reader 2 {sum(bool(a['r2']) for a in rows):2} | in census (either) {sum(a['in_census'] for a in rows):2} | "
          f"both {sum(bool(a['r1']) and bool(a['r2']) for a in rows):2} | "
          f"share an entry {sum(bool(set(a['r1']) & set(a['r2'])) for a in rows):2}")
print("none, by reason: reader 1", dict(Counter(a["r1_none"] for a in asks.values() if a["r1_none"])),
      "| reader 2", dict(Counter(a["r2_none"] for a in asks.values() if a["r2_none"])))
print("in census by family:", {f: f"{sum(a['in_census'] for a in asks.values() if a['family'] == f)}/"
                                  f"{sum(a['family'] == f for a in asks.values())}" for f in sorted(set(family[c] for c in asks))})
print("entries per brief:", {pr: len(ids) for pr, ids in briefs.items()}, "| distinct entries:",
      len({i for ids in briefs.values() for i in ids}))
if "--print-briefs" in sys.argv:
    for pr, ids in briefs.items():
        print(f"\n## PR {pr}: {sum(a['pr'] == int(pr) for a in asks.values())} asks, {len(ids)} entries")
        for i in ids:
            print(f"- [{i}] {codebook[i]}")
