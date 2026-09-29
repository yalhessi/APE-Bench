"""Reader batch files (bodies, scratch only) from the materialised bodies and the fixed order.
usage: build_batches.py <bodies.json> <order.json> <scratch_dir>   (run from the repo root)
"""
import json, sys
from pathlib import Path
bodies_path, order_path, S = sys.argv[1], sys.argv[2], Path(sys.argv[3])
S.mkdir(parents=True, exist_ok=True)
rows = {(r["set"], r["cid"]): r for r in json.load(open(bodies_path))["rows"]}
order = json.load(open(order_path))
by_batch = {}
for o in order["order"]: by_batch.setdefault(o["batch"], []).append(o)
FAM = {"F1": "proof", "F2": "interface", "F3": "registration", "F4": "derive, don't restate",
       "F5": "redundancy", "F6": "statement and API design", "F7": "generality", "F8": "naming",
       "F9": "formatting", "F10": "documentation", "F11": "meta-code correctness", "F12": "PR level",
       "CORR": "correctness", "NEW": "new family", "-": "-"}
def fam(code): return " | ".join(f"{c} {FAM.get(c, '?')}" for c in code.split("|")) if code != "-" else "- (held-out set, no family label)"
for bid, items in by_batch.items():
    with open(S / f"batch_{bid}.md", "w") as f:
        f.write(f"# Batch {bid}: {len(items)} asks, set {items[0]['set']}\n")
        for o in items:
            r = rows[(o["set"], o["cid"])]
            parent = rows.get((o["set"], r["reply_to_cid"])) if r.get("reply_to_cid") else None
            f.write(f"\n## {o['cid']}  PR {r['pr']} ({'AI' if r['ai'] else 'human'}) — {(r['pr_title'] or '')[:80]}\n"
                    f"{r['path']}:{r['line']}  kind={r['kind']}  by {r['author']}  family={fam(o['family'])}\n")
            if parent: f.write(f"> (in reply to) {parent['body'][:500]}\n")
            elif r.get("reply_outside_round1"): f.write("> (in reply to a comment outside round 1)\n")
            f.write(f"**ASK:** {r['body'][:1500]}\n```\n{(r['diff_hunk'] or '')[-900:]}\n```\n")
print("batches", len(by_batch), "->", S)
