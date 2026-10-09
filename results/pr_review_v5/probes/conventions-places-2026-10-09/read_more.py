"""The places test's further readings: those declared during the run, before any reading
(README, "Also read, added during the run"), and two scores added after the reading, labelled so.

Declared before reading:
- within-PR AUC, asked against decoy pairs, over the PRs that hold both;
- the leave-one-PR-out range of the pooled AUC;
- the AUC on sample 1 only;
- agreement as confidence (exact pairs: both, one or neither sample says `departs`);
- asked pairs kept on asks DX misses (reached in at most 1 of its 3 reps, matcher 1);
- per-rule suppression, simulated leave-PR-out.

Added after the reading, because the stated CONFIDENCE turned out to be confidence in the verdict
(`departs` and `conforms` answers both median 95):
- signed confidence (CONFIDENCE if `departs`, 100 - CONFIDENCE if `conforms`);
- the departs rate as the score.

usage (repo root, PYTHONPATH=$PWD:$PWD/src): ape/bin/python <this file>
"""
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
CEILING = HERE.parent / "conventions-ceiling-2026-10-04"


def parse(content):
    v = re.search(r"VERDICT:\s*(departs|conforms)", content, re.I)
    c = re.search(r"CONFIDENCE:\s*(\d+(?:\.\d+)?)", content)
    return (v.group(1).lower() if v else None, min(100.0, float(c.group(1))) if c else None)


def auc(pos, neg):
    if not pos or not neg:
        return float("nan")
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


items = json.loads((HERE / "items.json").read_text())["items"]
rows = defaultdict(list)
for r in map(json.loads, (HERE / "outputs.jsonl").open()):
    rows[r["name"]].append(r)

pairs = []
for it in items:
    got = sorted(rows.get(it["name"], []), key=lambda r: r["sample"])
    parsed = [parse(r["content"]) for r in got]
    if not parsed:
        continue
    departs = [v == "departs" for v, _ in parsed]
    stated = [c for _, c in parsed if c is not None]
    signed = [(c if v == "departs" else 100 - c) for v, c in parsed if v and c is not None]
    group = "asked" if it["asked"] else ("unasked" if it["kind"] == "exact" else "decoy")
    pairs.append({"it": it, "group": group, "rate": sum(departs) / len(departs),
                  "stated": statistics.mean(stated) if stated else None,
                  "signed": statistics.mean(signed) if signed else None,
                  "s1_stated": parsed[0][1], "s1_signed": (parsed[0][1] if parsed[0][0] == "departs" else 100 - parsed[0][1]) if parsed[0][1] is not None and parsed[0][0] else None,
                  "s1_rate": float(departs[0]), "n_depart": sum(departs), "n": len(departs)})

score_names = ("stated", "signed", "rate", "s1_stated", "s1_signed", "s1_rate")


def group_scores(group, score, pr=None):
    return [p[score] for p in pairs if p["group"] == group and p[score] is not None and (pr is None or p["it"]["pr"] == pr)]


print("== pooled AUC, asked against decoy / against unasked exact ==")
for s in score_names:
    tag = "" if s in ("stated", "s1_stated") else "  (added after the reading)" if "signed" in s or s == "rate" else ""
    print(f"  {s:10} vs decoy {auc(group_scores('asked', s), group_scores('decoy', s)):.3f}   "
          f"vs unasked {auc(group_scores('asked', s), group_scores('unasked', s)):.3f}{tag}")

prs = sorted({p["it"]["pr"] for p in pairs})
both = [pr for pr in prs if group_scores("asked", "rate", pr) and group_scores("decoy", "rate", pr)]
print(f"\n== within-PR AUC, asked against decoy, over the {len(both)} PRs holding both: mean of per-PR AUCs ==")
for s in ("stated", "signed", "rate"):
    vals = [auc(group_scores("asked", s, pr), group_scores("decoy", s, pr)) for pr in both]
    print(f"  {s:8} mean {statistics.mean(vals):.3f}  per PR {[round(v, 2) for v in vals]}")

print("\n== leave-one-PR-out range of the pooled AUC, asked against decoy ==")
for s in ("stated", "signed", "rate"):
    vals = []
    for pr in prs:
        pos = [p[s] for p in pairs if p["group"] == "asked" and p["it"]["pr"] != pr and p[s] is not None]
        neg = [p[s] for p in pairs if p["group"] == "decoy" and p["it"]["pr"] != pr and p[s] is not None]
        vals.append(auc(pos, neg))
    print(f"  {s:8} {min(vals):.3f} - {max(vals):.3f}")

print("\n== agreement as confidence, exact pairs (two samples): asked share in each bucket ==")
for k in (2, 1, 0):
    b = [p for p in pairs if p["it"]["kind"] == "exact" and p["n"] == 2 and p["n_depart"] == k]
    a = sum(p["group"] == "asked" for p in b)
    print(f"  {k} of 2 depart: {len(b):4} pairs, {a} asked ({a / len(b):.3f})" if b else f"  {k} of 2: none")

# asked pairs on asks DX misses (matcher 1, reached in <= 1 of 3 reps)
reach = defaultdict(int)
for rnd in ("D1", "D23"):
    for tag in ("val", "post"):
        u = json.loads((CEILING / f"match_{rnd}_{tag}" / "unblinded.json").read_text())["1"]["table"]
        for cid, row in u.items():
            reach[cid] += sum(v == "reached" for s, v in row.items() if s.startswith("DX"))
asked = [p for p in pairs if p["group"] == "asked"]
missed = [p for p in asked if all(reach[c] <= 1 for c in p["it"]["asked"])]
print(f"\n== asked pairs on asks DX misses (<= 1 of 3 reps): {len(missed)} of {len(asked)}; "
      f"departs rate there {statistics.mean(p['rate'] for p in missed):.2f} (all asked {statistics.mean(p['rate'] for p in asked):.2f}) ==")

print("\n== per-rule suppression, leave-PR-out: drop an entry whose non-asked departs rate on the other PRs exceeds the cut ==")
nonasked = defaultdict(list)
for p in pairs:
    if p["group"] != "asked":
        nonasked[p["it"]["entry"]].append((p["it"]["pr"], p["rate"]))
for cut in (0.5, 0.3, 0.1):
    kept_asked = filed = 0
    for p in pairs:
        others = [r for pr, r in nonasked[p["it"]["entry"]] if pr != p["it"]["pr"]]
        if others and statistics.mean(others) > cut:
            continue
        if p["group"] == "asked":
            kept_asked += p["rate"]
        filed += p["rate"]
    n_asked = sum(p["rate"] for p in pairs if p["group"] == "asked")
    print(f"  cut {cut}: asked departs kept {kept_asked:.1f} of {n_asked:.1f}; filings (all pairs, expected) {filed:.0f} "
          f"= {filed / len(prs):.1f} a PR over the test's pairs")
print(f"  no cut: filings {sum(p['rate'] for p in pairs):.0f} = {sum(p['rate'] for p in pairs) / len(prs):.1f} a PR over the test's pairs")
precision = sum(p["rate"] for p in pairs if p["group"] == "asked") / sum(p["rate"] for p in pairs)
print(f"\n== share of all departs filings that sit at an asked pair: {precision:.3f} ==")
