"""Stage 2 of the convention-detector probe: the census PRs as a probe set, and the reading.

  layout <structure_dir> <feedback.json> <out_dir>
      Lays the val1000 census out the way `cli producer bench --set` reads a probe set:
      <out_dir>/release/derived/change_graphs.jsonl (a link to the structure build),
      <out_dir>/probe/{asks.json, feedback.json} and <out_dir>/census.yaml. Every reader-A-labelled
      ask is an ask; an accepted PR with no labelled ask is a control.
  read <bench_dir>/summary.json <bench_dir>/facts.jsonl [P113,P211]
      Joins the bench's located asks to reader A's labels: recall on the 49 target asks by
      convention, demand (facts at a target ask, and at any ask, over facts), volume, and the
      seeded validity sample. Prints JSON.

Run from the repository root with PYTHONPATH=$PWD:$PWD/src. Pre-registered in README.md, stage 2.
"""

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

from src.mathlib_review.io import jsonl_rows

HERE = Path(__file__).parent
CENSUS = Path("results/pr_review_v5/adjudications/conventions-census-v1")
EVENTS = Path("results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/events.jsonl")
TARGET = {"P057", "P034", "P108"}
SEED = "dot-notation-census-2026-10-06"


def labels():
    rows = [r for f in sorted((CENSUS / "reader_A").glob("labels_b*.jsonl")) for r in jsonl_rows(f)]
    return {r["cid"]: {i for i in (r["principle_id"], r["second_principle_id"]) if i} for r in rows}


def layout(structure: Path, feedback: Path, out: Path) -> None:
    graphs = {row["pr_number"] for row in jsonl_rows(structure / "change_graphs.jsonl")}
    fb = json.loads(feedback.read_text(encoding="utf-8"))
    events = {r["cid"]: r for r in jsonl_rows(EVENTS)}
    # The committed events and the rebuilt feedback must be the same comments under the same ids.
    for row in fb["rows"]:
        assert events[row["cid"]]["event_id"] == row["event_id"], row["cid"]
    labelled = {cid: ids for cid, ids in labels().items() if ids}
    asks, prs = {}, sorted(graphs)
    for row in fb["rows"]:
        if row["cid"] in labelled and row["pr"] in graphs:
            asks.setdefault(str(row["pr"]), []).append(row["cid"])
    controls = [pr for pr in prs if str(pr) not in asks]
    (out / "release/derived").mkdir(parents=True, exist_ok=True)
    link = out / "release/derived/change_graphs.jsonl"
    if not link.exists():
        link.symlink_to((structure / "change_graphs.jsonl").resolve())
    (out / "probe").mkdir(exist_ok=True)
    (out / "probe/asks.json").write_text(json.dumps({"asks": asks, "controls": controls, "families": {}}))
    (out / "probe/feedback.json").write_text(json.dumps({"rows": fb["rows"]}, ensure_ascii=False))
    (out / "census.yaml").write_text(yaml.safe_dump({
        "name": "census_val1000", "release": str(out / "release"),
        "dataset_config": "configs/pr_review_v5_val_2025_06_2026_03_v1_small12.yaml",
        "pr_numbers": prs, "feedback": {"draw": "val1000-2025-06-2026-03-v1"}, "cid_prefix": "v",
        "probe_dir": str(out / "probe")}))
    print(json.dumps({"graphs": len(graphs), "prs_with_asks": len(asks),
                      "asks": sum(len(v) for v in asks.values()), "controls": len(controls)}))


def read(summary_path: Path, facts_path: Path, target=TARGET) -> None:
    summary = json.loads(summary_path.read_text())
    facts = jsonl_rows(facts_path)
    lab = labels()
    targets = {cid for cid, ids in lab.items() if ids & target}
    events = {r["cid"]: r for r in jsonl_rows(EVENTS)}
    located = {row["cid"] for row in summary["located"]}
    by_conv = Counter()
    for cid in targets:
        conv = sorted(lab[cid] & target)[0]
        by_conv[(conv, "asks")] += 1
        by_conv[(conv, "located")] += cid in located
    at_target = [f for f in facts if set(f["located_asks"]) & targets]
    at_any = [f for f in facts if f["located_asks"]]
    pool = sorted(facts, key=lambda f: hashlib.sha256(
        (SEED + f["path"] + str(f["line"]) + f["text"]).encode()).hexdigest())
    print(json.dumps({
        "facts": len(facts), "prs": summary["prs"],
        "prs_with_a_fact": sum(1 for v in summary["facts_per_pr"].values() if v),
        "control_prs": len(summary["control_prs"]),
        "control_facts": sum(summary["control_facts"].values()),
        "targets": len(targets), "targets_with_a_graph": sum(1 for c in targets if str(events[c]["pr"]) in summary["facts_per_pr"]),
        "targets_located": sorted(targets & located),
        "by_convention": {f"{c}:{k}": v for (c, k), v in sorted(by_conv.items())},
        "demand_target": f"{len(at_target)}/{len(facts)}",
        "demand_any_ask": f"{len(at_any)}/{len(facts)}",
        "by_shape": dict(Counter(f["convention"] for f in facts)),
        "validity_sample": [{"pr": f["pr_number"], "at": f"{f['path']}:{f['line']}", "fact": f["text"]}
                            for f in pool[:20]],
    }, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    if sys.argv[1] == "layout":
        layout(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    else:
        read(Path(sys.argv[2]), Path(sys.argv[3]),
             set(sys.argv[4].split(",")) if len(sys.argv) > 4 else TARGET)
