"""Tallies for `review-coordination-design-2026-09.md` §6.2-6.3, from `pass_labels.jsonl`.

Run from the repo root: `python3 results/pr_review_v5/adjudications/coordination-design-check-2026-09-29/analyse.py`.
"""
import collections, json, pathlib

rows = [json.loads(l) for l in pathlib.Path(__file__).with_name("pass_labels.jsonl").read_text().splitlines() if l.strip()]
by_source = collections.defaultdict(list)
for r in rows:
    by_source[r["source"].split(" ")[0]].append(r)
for source, items in by_source.items():
    print(f"== {source}: {len(items)} rows")
    print("  by pass:", dict(sorted(collections.Counter(r["pass"] for r in items).items())))
    print("  by construction:", collections.Counter(r["construction"] for r in items).most_common())
    produced = [r for r in items if (r.get("battery") or "").startswith("found")]
    if produced:
        print("  battery produced (found*):", dict(sorted(collections.Counter(r["pass"] for r in produced).items())))
        print("  battery tried:", collections.Counter(r.get("battery") for r in items if r.get("battery") and r["battery"] != "not_tried"))
