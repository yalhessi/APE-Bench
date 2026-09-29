"""Re-materialise the round-1 comment bodies for the val1000 and outside-sets readings, by event id.

Bodies are never committed; the committed artifacts carry (cid, pr, event_id). This rebuilds the
reader rows from the PR store so a later reading uses exactly the comments the earlier ones did.
usage: materialise_bodies.py <out.json>     (run from the repo root; spends nothing)
"""
import json, sys
from pathlib import Path
from src.datasets.pull_requests.store import PullRequestStore
from src.mathlib_review.release.events import events_from_bundle

ADJ = Path("results/pr_review_v5/adjudications")
SOURCES = [  # (set tag, rows with cid/pr/event_id)
    ("val1000", [json.loads(l) for l in open(ADJ / "arm-coverage-val1000-2025-06-2026-03-v1/events.jsonl")]),
    ("outside_window", json.load(open(ADJ / "design-comparison-outside-v1/packet_manifest.json"))["rows"]),
    ("outside_years", json.load(open(ADJ / "design-comparison-outside-v1/packet_manifest_window.json"))["rows"]),
]
store = PullRequestStore()
out, missing = [], []
for tag, rows in SOURCES:
    by_pr = {}
    for r in rows: by_pr.setdefault(int(r["pr"]), []).append(r)
    for n, prs_rows in sorted(by_pr.items()):
        bundle = store.load_bundle(n)
        key_of = {e.event_id: e.source_key for e in events_from_bundle(
            bundle, source_object=store.bundle_ref(n), repo="leanprover-community/mathlib4")}
        gh_to_cid = {}
        got = []
        for r in prs_rows:
            key = key_of.get(r["event_id"])
            if not key or key == "/pr":
                missing.append((tag, r["cid"], r["event_id"])); continue
            _, coll, idx = key.split("/")
            item = (bundle.get(coll) or [])[int(idx)]
            kind = {"reviews": "review", "review_comments": "review_comment", "issue_comments": "issue_comment"}[coll]
            row = {"set": tag, "cid": r["cid"], "pr": n, "event_id": r["event_id"], "kind": kind,
                   "author": (item.get("user") or {}).get("login"), "state": item.get("state"),
                   "path": item.get("path"), "line": item.get("line") or item.get("original_line"),
                   "gh_id": item.get("id"), "in_reply_to": item.get("in_reply_to_id"),
                   "diff_hunk": (item.get("diff_hunk") or "")[-900:], "body": item.get("body") or "",
                   "pr_title": (bundle.get("pr") or {}).get("title"), "ai": bool(r.get("ai")),
                   "month": r.get("month")}
            if row["gh_id"] is not None and kind == "review_comment": gh_to_cid[row["gh_id"]] = row["cid"]
            got.append(row)
        for row in got:
            row["reply_to_cid"] = gh_to_cid.get(row["in_reply_to"]) if row["in_reply_to"] else None
            row["reply_outside_round1"] = bool(row["in_reply_to"]) and row["reply_to_cid"] is None
        out.extend(got)
json.dump({"rows": out, "missing": missing}, open(sys.argv[1], "w"), ensure_ascii=False, indent=0)
from collections import Counter
print("rows", len(out), dict(Counter(r["set"] for r in out)), "missing", len(missing))
