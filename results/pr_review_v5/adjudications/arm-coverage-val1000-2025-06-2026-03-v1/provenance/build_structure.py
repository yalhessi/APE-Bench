"""Change graphs, work units and per-PR inventories for val1000, catching per-PR failures."""
import json, sys, traceback
from pathlib import Path
from src.datasets.pull_requests.store import PullRequestStore
from src.datasets.pull_requests.definitions import load_roster
from src.datasets.pull_requests.projections.frame import load_sealed, Draw, seal_dir, BASE_FILE_CACHE, DEFAULT_RENDERER
from src.datasets.pull_requests.projections.episodes import project_episodes, REPO
from src.mathlib_review.paths import MATHLIB_CLONE
from src.mathlib_review.release.change_graph import build_change_graph, hydrate_blob_cache_from_git
from src.mathlib_review.release.modification_inventory import build_inventory
from src.mathlib_review.release.work_units import build_work_units
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
name = "val1000-2025-06-2026-03-v1"
spec, members, _ = load_sealed(name)
draw = Draw.model_validate_json((seal_dir(name) / "draw.json").read_text())
store = PullRequestStore()
prs = sorted(a.pr_number for a in draw.accepted)
projection = project_episodes(store, roster=load_roster(Path(spec.roster_path)), prs=prs, repo=REPO)
graphs, failures = [], []
for ep in projection.episodes:
    try:
        if hydrate_blob_cache_from_git(ep, cache_root=BASE_FILE_CACHE, clone=MATHLIB_CLONE)["missing"]:
            failures.append({"pr": ep.pr_number, "stage": "graph", "error": "base files missing"}); continue
        graphs.append(build_change_graph(ep, workspace_root=BASE_FILE_CACHE / "_no_workspaces", blob_cache_root=BASE_FILE_CACHE))
    except Exception as exc:
        failures.append({"pr": ep.pr_number, "stage": "graph", "error": repr(exc)[:300]})
with open(out / "change_graphs.jsonl", "w") as f:
    for g in graphs: f.write(g.model_dump_json() + "\n")
units = build_work_units(graphs, renderer_version=DEFAULT_RENDERER)
with open(out / "work_units.jsonl", "w") as f:
    for u in units: f.write(u.model_dump_json() + "\n")
inv = []
for g in graphs:
    try:
        inv.extend(build_inventory([g]))
    except Exception as exc:
        failures.append({"pr": g.pr_number, "stage": "inventory", "error": repr(exc)[:300]})
with open(out / "modification_inventory.jsonl", "w") as f:
    for r in inv: f.write(r.model_dump_json() + "\n")
with open(out / "episodes.jsonl", "w") as f:
    for e in projection.episodes: f.write(e.model_dump_json() + "\n")
json.dump(failures, open(out / "failures.json", "w"), indent=1)
print(len(projection.episodes), "episodes;", len(graphs), "graphs;", len(units), "units;", len(inv), "inventory records;", len(failures), "failures")
