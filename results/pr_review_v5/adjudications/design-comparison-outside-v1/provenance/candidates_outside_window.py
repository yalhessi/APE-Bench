"""Seeded pre-gate candidates created OUTSIDE 2025-06..2026-03, for tier-2 collection. Early
window 2024-03-01..2025-05-31, late window 2026-04-01..2026-08-31. Test-set PRs cannot occur
(created inside the window), asserted anyway."""
import json, sys, hashlib
from pathlib import Path
from src.datasets.pull_requests.store import PullRequestStore
from src.datasets.pull_requests.definitions import load_roster
from src.datasets.pull_requests.collect import pre_gate
S = Path(sys.argv[1]); n_early, n_late = int(sys.argv[2]), int(sys.argv[3]); seed = "outside-window-2026-09-26"
TEST = set(json.load(open("inputs/pr_review_v4/releases/eval-2025-06-2026-03-v1/manifest.json"))["pr_numbers"])
store = PullRequestStore(); roster = load_roster(Path("inputs/pull_requests/rosters/mathlib_roster_2026-09-11.txt"))
listing = [json.loads(l) for l in open("inputs/pull_requests/prs.jsonl")]
nums = [r["pr_number"] for r in listing if 1 in r["tiers"]]
order = sorted(nums, key=lambda n: hashlib.sha256(f"{seed}\0{n}".encode()).hexdigest())
early, late, checked, reasons = [], [], 0, {}
for n in order:
    if len(early) >= n_early and len(late) >= n_late: break
    try:
        pr = store.read(n, "listing")
    except Exception:
        continue
    created = str((pr or {}).get("created_at") or "")[:10]
    if "2024-03-01" <= created <= "2025-05-31": bucket = early
    elif "2026-04-01" <= created <= "2026-08-31": bucket = late
    else: continue
    want = n_early if bucket is early else n_late
    if len(bucket) >= want: continue
    checked += 1
    ok, reason = pre_gate(store, n, roster); reasons[reason] = reasons.get(reason, 0) + 1
    if ok:
        assert n not in TEST; bucket.append({"pr": n, "created": created})
    if checked % 100 == 0: print("checked", checked, "early", len(early), "late", len(late), reasons, flush=True)
json.dump({"seed": seed, "early": early, "late": late, "checked": checked, "reasons": reasons}, open(S / "outside_window_candidates.json", "w"), indent=1)
with open(S / "outside_window_prs.txt", "w") as f:
    f.write("# seeded pre-gate passes outside 2025-06..2026-03; seed " + seed + "\n")
    for x in early + late: f.write(f"{x['pr']}\n")
print("DONE checked", checked, "early", len(early), "late", len(late), reasons)
