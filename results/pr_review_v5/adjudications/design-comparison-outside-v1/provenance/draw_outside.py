"""Round-1 reviewer feedback for a seeded sample of tier-2 PRs outside every evaluation and
development set (same window as val1000, different PRs and reviewers). Refuses test-set PRs."""
import json, sys, hashlib
from pathlib import Path
from src.datasets.pull_requests.store import PullRequestStore
from src.datasets.pull_requests.definitions import load_roster, ai_authorship_evidence
from src.datasets.pull_requests.projections.episodes import project_episodes
from src.mathlib_review.release.events import events_from_bundle
S = Path(sys.argv[1]); target_prs = int(sys.argv[2]); seed = sys.argv[3] if len(sys.argv) > 3 else "outside-sets-2026-09-26"
pool_file = sys.argv[4] if len(sys.argv) > 4 else "tier2_outside_sets.json"; prefix = sys.argv[5] if len(sys.argv) > 5 else "o"; out_name = sys.argv[6] if len(sys.argv) > 6 else "outside_feedback.json"
TEST = set(json.load(open("inputs/pr_review_v4/releases/eval-2025-06-2026-03-v1/manifest.json"))["pr_numbers"])
pool = json.load(open(S / pool_file)); pool = pool if isinstance(pool, list) else [x["pr"] for x in pool["early"] + pool["late"]]; assert not (set(pool) & TEST)
order = sorted(pool, key=lambda n: hashlib.sha256(f"{seed}\0{n}".encode()).hexdigest())
store, roster = PullRequestStore(), load_roster(Path("inputs/pull_requests/rosters/mathlib_roster_2026-09-11.txt"))
rows, walked, no_feedback, errors = [], [], [], []
for n in order:
    if len({r["pr"] for r in rows}) >= target_prs: break
    walked.append(n)
    try:
        proj = project_episodes(store, roster=roster, prs=[n])
        bs = sorted(proj.boundaries, key=lambda b: b.episode_id)
        if not bs: no_feedback.append(n); continue
        b = bs[0]; want = set(b.feedback_event_ids)
        if not want: no_feedback.append(n); continue
        bundle = store.load_bundle(n)
        ids = {e.source_key: e.event_id for e in events_from_bundle(bundle, source_object=store.bundle_ref(n), repo="leanprover-community/mathlib4")}
        ai = None
        try: ai = bool(ai_authorship_evidence(bundle))
        except Exception: pass
        got = []
        for kind, key in (("review", "reviews"), ("review_comment", "review_comments"), ("issue_comment", "issue_comments")):
            for i, item in enumerate(bundle.get(key) or []):
                eid = ids.get(f"/{key}/{i}")
                if eid not in want: continue
                got.append({"pr": n, "event_id": eid, "kind": kind, "author": (item.get("user") or {}).get("login"),
                            "at": item.get("submitted_at") or item.get("created_at"), "state": item.get("state"),
                            "path": item.get("path"), "line": item.get("line") or item.get("original_line"),
                            "gh_id": item.get("id"), "in_reply_to": item.get("in_reply_to_id"),
                            "diff_hunk": (item.get("diff_hunk") or "")[-900:], "body": item.get("body") or "",
                            "pr_title": bundle["pr"].get("title"), "created_at": bundle["pr"].get("created_at"),
                            "ai": ai, "pr_author": (bundle["pr"].get("user") or {}).get("login"), "episode_id": b.episode_id})
        got.sort(key=lambda r: (r["at"] or "", r["kind"])); rows.extend(got)
    except Exception as e:
        errors.append((n, str(e)[:200]))
    if len(walked) % 25 == 0: print("walked", len(walked), "prs with rows", len({r["pr"] for r in rows}), "rows", len(rows), flush=True)
ghmap = {}
for i, r in enumerate(rows):
    r["cid"] = f"{prefix}{i:04d}"
    if r["gh_id"] is not None and r["kind"] == "review_comment": ghmap[r["gh_id"]] = r["cid"]
for r in rows: r["reply_to_cid"] = (ghmap.get(r["in_reply_to"], "(parent outside round 1)") if r["in_reply_to"] else None)
json.dump({"seed": seed, "walked": walked, "no_feedback": no_feedback, "errors": errors, "rows": rows}, open(S / out_name, "w"), ensure_ascii=False, indent=1)
print("DONE walked", len(walked), "prs with rows", len({r["pr"] for r in rows}), "rows", len(rows), "no_feedback", len(no_feedback), "errors", len(errors))
