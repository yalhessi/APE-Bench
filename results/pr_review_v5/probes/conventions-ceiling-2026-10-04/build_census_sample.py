"""Stage H's census sample: a seeded draw of val1000 PRs, and a release-shaped folder for them so the
probe harness can render each PR's model and packet files exactly as for the probe sets.

The draw: val1000's 973 accepted PRs (`val1000-2025-06-2026-03-v1`; PR-disjoint from every probe
set), at most 40 change targets (the post-cutoff probe set's cap), ordered by sha256 of the seed and
the PR number; the first N whose change graph builds. AI-authored PRs are kept and labelled.
Writes `<out>/input/episodes.jsonl`, `<out>/derived/change_graphs.jsonl`,
`<out>/derived/modification_inventory.jsonl`, and the committed manifest `census_sample.json`.
Calls no model.

usage (repo root, PYTHONPATH=$PWD:$PWD/src): ape/bin/python <this file> <out dir> <N>
"""
import hashlib
import json
import sys
from pathlib import Path

from src.datasets.pull_requests.definitions import load_roster
from src.datasets.pull_requests.projections.episodes import REPO, project_episodes
from src.datasets.pull_requests.projections.frame import BASE_FILE_CACHE, Draw, load_sealed, seal_dir
from src.datasets.pull_requests.store import PullRequestStore
from src.mathlib_review.paths import MATHLIB_CLONE
from src.mathlib_review.release.change_graph import build_change_graph, hydrate_blob_cache_from_git
from src.mathlib_review.release.modification_inventory import build_inventory

HERE = Path(__file__).parent
NAME, SEED, CAP = "val1000-2025-06-2026-03-v1", "stage-h-census-2026-10-06", 40
out, want = Path(sys.argv[1]), int(sys.argv[2])
spec, _members, _sha = load_sealed(NAME)
draw = Draw.model_validate_json((seal_dir(NAME) / "draw.json").read_text())
probe_prs = {33066, 33098, 33117, 33145, 33149, 33285, 33294, 33304, 33305, 33315, 33321, 33337, 33362, 33421,
             33438, 41271, 41280, 41314, 41930, 42184, 42238, 42814, 43024, 43167, 43192, 26185, 26755,
             28649, 29842, 30458, 30641, 32080, 32875, 34091, 34935, 36822}
pool = sorted((a for a in draw.accepted if a.targets <= CAP and a.pr_number not in probe_prs),
              key=lambda a: hashlib.sha256(f"{SEED}\0{a.pr_number}".encode()).hexdigest())
store, roster = PullRequestStore(), load_roster(Path(spec.roster_path))
kept, skipped, episodes, graphs, inventory = [], [], [], [], []
for a in pool:
    if len(kept) >= want:
        break
    proj = project_episodes(store, roster=roster, prs=[a.pr_number], repo=REPO)
    eps = [e for e in proj.episodes if e.episode_id == a.episode_id]
    if not eps:
        skipped.append((a.pr_number, "no episode")); continue
    ep = eps[0]
    try:
        if hydrate_blob_cache_from_git(ep, cache_root=BASE_FILE_CACHE, clone=MATHLIB_CLONE)["missing"]:
            skipped.append((a.pr_number, "base files missing")); continue
        g = build_change_graph(ep, workspace_root=BASE_FILE_CACHE / "_no_workspaces", blob_cache_root=BASE_FILE_CACHE)
        inv = build_inventory([g])
    except Exception as exc:  # a PR whose graph does not build is skipped, as build_structure did
        skipped.append((a.pr_number, repr(exc)[:120])); continue
    kept.append(a); episodes.append(ep); graphs.append(g); inventory.extend(inv)
(out / "input").mkdir(parents=True, exist_ok=True); (out / "derived").mkdir(parents=True, exist_ok=True)
(out / "input/episodes.jsonl").write_text("".join(e.model_dump_json() + "\n" for e in episodes))
(out / "derived/change_graphs.jsonl").write_text("".join(g.model_dump_json() + "\n" for g in graphs))
(out / "derived/modification_inventory.jsonl").write_text("".join(r.model_dump_json() + "\n" for r in inventory))
manifest = {"draw": NAME, "seed": SEED, "max_targets": CAP, "eligible": len(pool),
            "prs": [{"pr": a.pr_number, "month": a.month, "stratum": a.stratum, "targets": a.targets,
                     "ai": bool(a.ai_evidence)} for a in kept], "skipped": skipped}
(HERE / "census_sample.json").write_text(json.dumps(manifest, indent=1) + "\n")
print(f"eligible {len(pool)}; kept {len(kept)}; skipped {len(skipped)}: {skipped}")
print("PRs:", [a.pr_number for a in kept], "| AI:", sum(bool(a.ai_evidence) for a in kept),
      "| targets:", [a.targets for a in kept])
