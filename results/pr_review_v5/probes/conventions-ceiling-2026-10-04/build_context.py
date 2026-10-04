"""The solo task's context files for the conventions ceiling probe (`probes.model_context`).

`base` is each PR's pass-0 model, on every PR of the set. A briefed level (`exact`, `common`, `all`)
adds the PR's conventions section after the model, on the PRs `briefs_<level>.json` names: a map
`{"prs": {"<pr>": ["P012", ...]}}` of reader A's codebook ids. Sentences are printed in codebook
order whatever order the brief lists them in.

usage (repo root, PYTHONPATH=$PWD/src): ape/bin/python <this file> <base|exact|common|all>
"""
import sys
from pathlib import Path

from src.mathlib_review.analysis import probes

HERE = Path(__file__).parent
CODEBOOK = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json")
SETS = {"val": "configs/probe_sets/val_small12.yaml", "post": "configs/probe_sets/postcutoff_2026_07_08_v1.yaml"}

level = sys.argv[1]
briefs = None if level == "base" else probes.load_conventions(HERE / f"briefs_{level}.json", CODEBOOK)
for tag, path in SETS.items():
    spec = probes.load_probe_set(Path(path))
    prs = [pr for pr in spec.pr_numbers if briefs is None or pr in briefs]
    conventions = None if briefs is None else {pr: briefs[pr] for pr in prs}
    out = HERE / f"context_{tag}_{level}.jsonl"
    out.write_text(probes.model_context(spec, prs, conventions))
    held = "" if conventions is None else f", {sum(map(len, conventions.values()))} sentences"
    print(f"{out}: {len(prs)} PRs{held}")
