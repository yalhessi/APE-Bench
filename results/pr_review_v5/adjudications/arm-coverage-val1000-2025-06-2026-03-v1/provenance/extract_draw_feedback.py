"""Round-1 reviewer feedback for every PR a sealed draw accepted. Refuses any test-set PR."""
import json, sys
from pathlib import Path
from src.datasets.pull_requests.store import PullRequestStore
from src.datasets.pull_requests.definitions import load_roster
from src.datasets.pull_requests.projections.frame import load_sealed, Draw, seal_dir
from src.datasets.pull_requests.projections.episodes import project_episodes
from src.mathlib_review.release.events import events_from_bundle

name, out_path = sys.argv[1], sys.argv[2]
TEST = set(json.load(open("inputs/pr_review_v4/releases/eval-2025-06-2026-03-v1/manifest.json"))["pr_numbers"])
spec, members, seal_sha = load_sealed(name)
draw = Draw.model_validate_json((seal_dir(name) / "draw.json").read_text())
assert draw.frame_seal_sha256 == seal_sha and draw.complete
accepted = draw.accepted
assert not ({a.pr_number for a in accepted} & TEST), "a test-set PR in the draw"
store, roster = PullRequestStore(), load_roster(Path(spec.roster_path))
rows, no_feedback = [], []
for a in accepted:
    n = a.pr_number
    proj = project_episodes(store, roster=roster, prs=[n])
    (b,) = [x for x in proj.boundaries if x.episode_id == a.episode_id]
    want = set(b.feedback_event_ids)
    if not want:
        no_feedback.append(n); continue
    bundle = store.load_bundle(n)
    ids = {e.source_key: e.event_id for e in events_from_bundle(bundle, source_object=store.bundle_ref(n),
                                                              repo="leanprover-community/mathlib4")}
    gh_to_row = {}
    got = []
    for kind, key in (("review", "reviews"), ("review_comment", "review_comments"), ("issue_comment", "issue_comments")):
        for i, item in enumerate(bundle.get(key) or []):
            eid = ids.get(f"/{key}/{i}")
            if eid not in want: continue
            r = {"pr": n, "event_id": eid, "kind": kind, "author": (item.get("user") or {}).get("login"),
                 "at": item.get("submitted_at") or item.get("created_at"), "state": item.get("state"),
                 "path": item.get("path"), "line": item.get("line") or item.get("original_line"),
                 "gh_id": item.get("id"), "in_reply_to": item.get("in_reply_to_id"),
                 "diff_hunk": (item.get("diff_hunk") or "")[-600:], "body": item.get("body") or "",
                 "pr_title": bundle["pr"].get("title"), "stratum": a.stratum, "month": a.month,
                 "targets": a.targets, "ai": bool(a.ai_evidence), "pr_author": a.author}
            got.append(r)
    if len(got) != len(want):
        print("MISMATCH", n, len(got), len(want), file=sys.stderr)
    got.sort(key=lambda r: (r["at"] or "", r["kind"]))
    rows.extend(got)
rows.sort(key=lambda r: (r["pr"], r["at"] or ""))
ghmap = {}
for i, r in enumerate(rows):
    r["cid"] = f"v{i:04d}"
    if r["gh_id"] is not None and r["kind"] == "review_comment": ghmap[r["gh_id"]] = r["cid"]
for r in rows:
    r["reply_to_cid"] = (ghmap.get(r["in_reply_to"], "(parent outside round 1)") if r["in_reply_to"] else None)
json.dump({"name": name, "seal": seal_sha, "accepted": len(accepted), "no_feedback": no_feedback, "rows": rows},
          open(out_path, "w"), ensure_ascii=False, indent=1)
print("accepted", len(accepted), "with feedback", len({r['pr'] for r in rows}), "events", len(rows),
      "no-feedback PRs", len(no_feedback))
