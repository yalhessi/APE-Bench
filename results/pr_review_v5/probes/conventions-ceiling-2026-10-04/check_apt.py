"""The `apt` context files against what the runs already on disk read (one reviewer table, review
finding 6): each of the ten stage F PRs' rows equals its `ap` row byte for byte, and each PR's
model section equals the model section its solo runs read (`context_<set>_base.jsonl` on the probe
sets, the dev probe's `model_context.jsonl` on dev). Exits non-zero on any difference.

usage (repo root): python3 <this file>
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
BASE = {"val": HERE / "context_val_base.jsonl", "post": HERE / "context_post_base.jsonl",
        "dev": Path("results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/model_context.jsonl")}


def rows(path: Path) -> dict:
    return {json.loads(line)["pr_number"]: line for line in path.read_text(encoding="utf-8").split("\n") if line}


bad = 0
for tag, base_path in BASE.items():
    apt = rows(HERE / f"context_{tag}_apt.jsonl")
    ap = rows(HERE / f"context_{tag}_ap.jsonl") if tag != "dev" else {}
    base = rows(base_path)
    same_ap = sum(apt[pr] == line for pr, line in ap.items())
    bad += len(ap) - same_ap
    same_model = 0
    for pr, line in apt.items():
        model = json.loads(line)["sections"][0]
        ok = model == json.loads(base[pr])["sections"][0]
        same_model += ok
        bad += not ok
    print(f"{tag}: {len(apt)} PRs; ap rows equal {same_ap} of {len(ap)}; model sections equal {same_model} of {len(apt)}")
sys.exit(1 if bad else 0)
