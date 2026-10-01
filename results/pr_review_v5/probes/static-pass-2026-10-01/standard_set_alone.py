"""The standard linter set, run alone over the dev PRs' changed files (2026-10-01).

Layer 1 of `docs/plans/2026-10-01-beyond-the-solo-baseline.md` and step 2 of
`docs/todo/static-analysis-pass.md`: before any model reads the pass, measure what the pass alone
says. For every dev episode with a reviewed workspace, each changed `.lean` file is compiled in
that workspace with `-Dweak.linter.mathlibStandardSet=true` (the package build's own option set),
every warning and error with a position is kept, and each is mapped through the release's change
graph: a line inside a changed range's `reviewed_span` is in the diff, and it belongs to the change
targets whose reviewed entity (the narrowest declaration span containing the line) it falls in,
or, where no entity contains it, to the targets citing the range. The entity step matters: a new
file is one changed range, so by range alone every hit in 33149 located every obligation there.
A hit outside every changed range is pre-existing and is counted apart, never charged to the PR.

Scored without a judge: a gold obligation is *located* when a diff hit shares a change target with
it (the same notion as the judge's `location_hit`; whether the linter's message is the
maintainer's ask is read by hand from `hits.jsonl`), and the two control PRs' diff hits are the
pass's false-positive floor at zero model cost.

Writes `messages.jsonl` (every message, raw), `hits.jsonl`, `summary.json` and `compiles.jsonl`
beside this file. Run from the repository root (84 compiles of 2-35 s, up to WORKERS at a time):
`ape/bin/python results/pr_review_v5/probes/static-pass-2026-10-01/standard_set_alone.py`;
`--remap` reuses `messages.jsonl` and only redoes the mapping and the summary.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RELEASE = ROOT / "inputs/pr_review_v4/releases/dev-medium-0.3.0"
#: The episode -> reviewed workspace map of a completed dev run (every dev run writes one).
WORKSPACES = ROOT / "results/pr_review_v5/runs/probe_dev_opus55_contract2_claude_sub_rep1/reviewed_workspaces.json"
OPTION = "-Dweak.linter.mathlibStandardSet=true"
HELD_OUT = {33117, 33145, 33149, 33285, 33294, 33304, 33305, 33315, 33321, 33337, 33362, 33421}
CONTROLS = {33304, 33315}
WORKERS = 5
TIMEOUT = 1500


def rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def compile_file(workspace: Path, rel: str) -> dict:
    """`lake env lean` on the reviewed file in its workspace; the JSON messages, or why not."""

    started = time.time()
    try:
        proc = subprocess.run(
            ["lake", "env", "lean", OPTION, "--json", str(workspace / rel)],
            cwd=workspace, capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"path": rel, "status": "timeout", "seconds": round(time.time() - started), "messages": []}
    messages = []
    for line in proc.stdout.splitlines():
        try:
            message = json.loads(line)
        except ValueError:
            continue
        if isinstance(message, dict) and message.get("pos"):
            messages.append(message)
    status = "compiled" if proc.returncode == 0 else ("compile_errors" if messages else "environment_failure")
    return {"path": rel, "status": status, "returncode": proc.returncode,
            "seconds": round(time.time() - started), "messages": messages,
            "stderr_tail": proc.stderr[-600:]}


def main() -> int:
    workspaces = json.loads(WORKSPACES.read_text(encoding="utf-8"))
    graphs = {g["episode_id"]: g for g in rows(RELEASE / "derived/change_graphs.jsonl")}
    gold = defaultdict(list)
    for judgment in rows(RELEASE / "gold/judgments.jsonl"):
        for obligation in judgment["obligations"]:
            gold[int(judgment["pr_number"])].append({
                "obligation_id": obligation["obligation_id"], "change_ids": set(obligation["change_ids"]),
                "claim": obligation.get("claim", ""), "concern": judgment.get("concern_labels")})

    jobs = []
    for episode_id, workspace in workspaces.items():
        graph = graphs.get(episode_id)
        if graph is None:
            continue
        for cover in graph["file_coverage"]:
            if cover.get("file_status") == "deleted" or not cover["path"].endswith(".lean"):
                continue
            jobs.append((episode_id, Path(workspace), cover["path"]))
    print(f"{len(jobs)} files over {len(workspaces)} episodes, {WORKERS} at a time", flush=True)

    results = {}
    if "--remap" in sys.argv and (HERE / "messages.jsonl").is_file():
        for row in rows(HERE / "messages.jsonl"):
            results[(row["episode_id"], row["path"])] = row
        compiles = rows(HERE / "compiles.jsonl")
    else:
        compiles = []
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(compile_file, workspace, rel): (episode_id, rel) for episode_id, workspace, rel in jobs}
            for future in futures:
                episode_id, rel = futures[future]
                result = future.result()
                pr = int(graphs[episode_id]["pr_number"])
                compiles.append({"episode_id": episode_id, "pr_number": pr, "path": rel, "status": result["status"],
                                 "seconds": result["seconds"], "messages": len(result["messages"]),
                                 "stderr_tail": result.get("stderr_tail", "")})
                print(f"{pr} {rel}: {result['status']} in {result['seconds']}s, {len(result['messages'])} messages", flush=True)
                results[(episode_id, rel)] = {"episode_id": episode_id, "path": rel, "messages": result["messages"]}
        (HERE / "messages.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in results.values()), encoding="utf-8")
        (HERE / "compiles.jsonl").write_text("".join(json.dumps(c) + "\n" for c in compiles), encoding="utf-8")

    hits = []
    for (episode_id, rel), result in results.items():
        graph = graphs[episode_id]
        pr = int(graph["pr_number"])
        ranges = [r for r in graph["changed_ranges"] if r["path"] == rel]
        targets_by_range, targets_by_entity = defaultdict(list), defaultdict(list)
        for target in graph["targets"]:
            for range_id in target["changed_range_ids"]:
                targets_by_range[range_id].append(target)
            for entity_id in target.get("reviewed_entity_ids") or []:
                targets_by_entity[entity_id].append(target)
        entities = [e for e in graph["entities"]
                    if e["path"] == rel and e.get("side") == "reviewed" and e.get("span")]
        for message in result["messages"]:
            line = message["pos"]["line"]
            in_ranges = [r for r in ranges
                         if r["reviewed_span"]["line_start"] <= line <= r["reviewed_span"]["line_end"]]
            containing = [e for e in entities if e["span"]["line_start"] <= line <= e["span"]["line_end"]]
            targets = {}
            if containing:
                narrowest = min(containing, key=lambda e: e["span"]["line_end"] - e["span"]["line_start"])
                targets = {t["change_id"]: t for t in targets_by_entity.get(narrowest["entity_id"], [])}
            if not targets:
                targets = {t["change_id"]: t for r in in_ranges for t in targets_by_range.get(r["range_id"], [])}
            hits.append({
                "pr_number": pr, "episode_id": episode_id, "path": rel, "line": line,
                "severity": message.get("severity"), "kind": message.get("kind"),
                "message": (message.get("data") or "").split("\n")[0][:200],
                "in_diff": bool(in_ranges), "mapped_by": "entity" if containing and targets else "range",
                "change_ids": sorted(targets),
                "declarations": sorted({t.get("declaration_name") or t.get("kind", "") for t in targets.values()}),
            })

    (HERE / "hits.jsonl").write_text("".join(json.dumps(h, ensure_ascii=False) + "\n" for h in hits), encoding="utf-8")

    per_pr = defaultdict(Counter)
    for h in hits:
        per_pr[h["pr_number"]]["diff" if h["in_diff"] else "pre_existing"] += 1
    located = {}
    for pr, obligations in gold.items():
        if pr not in HELD_OUT:
            continue
        diff_targets = {c for h in hits if h["pr_number"] == pr and h["in_diff"] for c in h["change_ids"]}
        for ob in obligations:
            located[ob["obligation_id"]] = bool(ob["change_ids"] & diff_targets)
    kinds = Counter(h["kind"] for h in hits if h["in_diff"])
    summary = {
        "files": len(jobs), "compiled": sum(c["status"] == "compiled" for c in compiles),
        "statuses": dict(Counter(c["status"] for c in compiles)),
        "hits_in_diff": sum(h["in_diff"] for h in hits), "hits_pre_existing": sum(not h["in_diff"] for h in hits),
        "per_pr": {str(pr): dict(c) for pr, c in sorted(per_pr.items())},
        "control_pr_hits_in_diff": {str(pr): per_pr[pr]["diff"] for pr in sorted(CONTROLS)},
        "kinds_in_diff": dict(kinds.most_common()),
        "gold_obligations_held_out": len(located),
        "gold_obligations_located_by_a_diff_hit": sum(located.values()),
        "located": located,
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "located"}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
