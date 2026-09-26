"""Reader packets (bodies, scratch only) and the id-only manifest (results) from a feedback draw.
usage: build_packets.py <feedback.json> <scratch_dir> <packet_prefix> <manifest_path> <batches>"""
import json, sys
from collections import Counter
from pathlib import Path
from src.datasets.pull_requests.store import PullRequestStore
from src.datasets.pull_requests.definitions import ai_authorship_evidence
fb_path, S, prefix, manifest, B = sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4], int(sys.argv[5])
fb = json.load(open(fb_path)); rows = fb["rows"]; by = {r["cid"]: r for r in rows}
store = PullRequestStore(); ai = {}
for n in sorted({r["pr"] for r in rows}):
    b = store.load_bundle(n); pr = b.get("pr") or {}
    ai[n] = sorted(ai_authorship_evidence(pr.get("labels") or [], pr.get("title"), pr.get("body"), b.get("commits") or []))
for r in rows: r["ai"] = bool(ai[r["pr"]])
print("rows", len(rows), "prs", len(ai), "ai prs", sum(1 for v in ai.values() if v), "kinds", dict(Counter(r["kind"] for r in rows)), "authors", len({r["author"] for r in rows}))
print("months", dict(sorted(Counter((r["created_at"] or "")[:7] for r in rows).items())))
size = (len(rows) + B - 1) // B
for k in range(B):
    batch = rows[k * size:(k + 1) * size]
    with open(S / f"{prefix}_b{k}.md", "w") as f:
        f.write(f"# Round-1 reviewer comments, batch {k} ({len(batch)} comments)\n")
        for r in batch:
            parent = by.get(r["reply_to_cid"]) if r.get("reply_to_cid") else None
            f.write(f"\n## {r['cid']}  PR {r['pr']} ({'AI' if r['ai'] else 'human'}) — {(r['pr_title'] or '')[:80]}\n{r['path']}:{r['line']}  kind={r['kind']}  by {r['author']}" + (f"  state={r['state']}" if r.get('state') else "") + "\n")
            if parent: f.write(f"> (in reply to) {parent['body'][:400]}\n")
            elif r.get("reply_to_cid"): f.write("> (in reply to a comment outside round 1)\n")
            f.write(f"**COMMENT:** {r['body'][:1500]}\n```\n{(r['diff_hunk'] or '')[-900:]}\n```\n")
    print("batch", k, len(batch))
json.dump({"seed": fb["seed"], "walked": len(fb["walked"]), "no_feedback": len(fb["no_feedback"]), "prs": sorted(ai), "ai_prs": sorted(n for n, v in ai.items() if v),
           "rows": [{"cid": r["cid"], "pr": r["pr"], "kind": r["kind"], "path": r["path"], "ai": r["ai"], "ai_evidence": ai[r["pr"]], "month": (r["created_at"] or "")[:7], "event_id": r["event_id"]} for r in rows]},
          open(manifest, "w"), indent=1)
