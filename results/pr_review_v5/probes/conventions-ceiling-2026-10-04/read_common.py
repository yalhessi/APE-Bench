"""Every condition of stages L, C, F, M, D, AP (and stage W, from branch `generation-suppression`) on
one footing: per-session reach on in-census asks, per matcher, over the asks its round judged and
over the ten stage F PRs' 33 (the asks stage AP judged). Each condition is read from the round that
measured it; X, the two Claude sessions matched again in every round, is printed per round, which
shows how far one pair of sessions moves between seals. No imputation: a round that ran ten PRs
reads over ten.

usage (repo root): python3 <this file>
"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
asks = json.loads((HERE / "briefs_exact.json").read_text())["asks"]
W = "results/pr_review_v5/probes/generation-suppression-2026-10-06"


def table(stage: str, tag: str, m: str):
    folder = HERE / f"match_{stage}_{tag}" / "unblinded.json"
    if folder.exists():
        return json.loads(folder.read_text())[m]["table"]
    if stage == "W":
        got = subprocess.run(["git", "show", f"generation-suppression:{W}/match_W_{tag}/unblinded.json"],
                             capture_output=True, text=True)
        return json.loads(got.stdout)[m]["table"] if got.returncode == 0 else None
    return None


def merged(stages: str, m: str) -> dict:
    out = {}
    for stage in stages.split(","):
        for tag in ("val", "post"):
            for cid, row in (table(stage, tag, m) or {}).items():
                out.setdefault(cid, {}).update(row)
    return out


def reach(t: dict, cond: str, keep) -> tuple:
    hit = total = 0
    judged = set()
    for cid, row in t.items():
        if asks[cid]["in_census"] and keep(cid):
            for s, v in row.items():
                if s.rstrip("0123456789") == cond:
                    hit += v == "reached"
                    total += 1
                    judged.add(cid)
    return hit, total, len(judged)


def cell(got: tuple) -> str:
    return f"{got[0] / got[1]:.2f} ({got[2]:2} asks)" if got[1] else "      -       "


ap_asks = set(merged("AP", "1"))
rows = [("LB", "L"), ("LE", "L"), ("GB", "M"), ("GE", "M"), ("GE", "W"), ("GD", "W"), ("DX", "D1,D23"),
        ("DX", "AP"), ("DE", "D1,D23"), ("DP", "D1,D23"), ("AP", "AP"), ("A", "F"), ("E", "C1,C2"), ("E", "F")]
rows += [("X", s) for s in ("L", "C1,C2", "F", "M", "W", "D1,D23", "AP")]
print(f"{'cond':4} {'round':7} {'sessions, val/post':19} | {'m1, its round':16} {'m2, its round':16} | {'m1, 10 PRs':16} {'m2, 10 PRs':16}")
for cond, stage in rows:
    t1, t2 = merged(stage, "1"), merged(stage, "2")
    if not t1:
        print(f"{cond:4} {stage:7} (tables not found)")
        continue
    n = "/".join(str(len({s for cid, row in t1.items() if asks[cid]["set"] == tag for s in row if s.rstrip("0123456789") == cond}))
                 for tag in ("val", "post"))
    print(f"{cond:4} {stage:7} {n:19} | {cell(reach(t1, cond, lambda c: True)):16} {cell(reach(t2, cond, lambda c: True)):16} | "
          f"{cell(reach(t1, cond, ap_asks.__contains__)):16} {cell(reach(t2, cond, ap_asks.__contains__)):16}")
