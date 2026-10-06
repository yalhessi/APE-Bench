"""Rebuild a design run's ledgers.jsonl from its own stored task results, through the runner's writer.

Why it exists: `_ledger_rows` tested `raw.get("ledger")`, so a PR whose ledger is empty -- one that
leaves no declaration in place, 33305 on dev -- got no row, and the critic stage refused D1's first
dev run for the missing PR (2026-10-02). The writer now tests for the key. This re-derives the file
from what the run stored, and refuses to write unless every row the old file had comes back byte for
byte, so the only change it can make is the rows the bug dropped.

Reads each task's `task_result.json` through `TaskStorage` (never by globbing attempts), spends
nothing. Run from the repository root:
    PYTHONPATH=$PWD/src ape/bin/python results/pr_review_v5/probes/review-designs-2026-10-02/rebuild_ledgers.py <run_name>
"""

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


async def main(run_name: str) -> int:
    from ape.orchestration.persistence import TaskStorage
    from src.mathlib_review.io import jsonl_bytes, jsonl_rows
    from src.mathlib_review.paths import run_dir
    from src.mathlib_review.review.runner import _ledger_rows

    tasks = ROOT / ".ape/runs" / run_name / "tasks"
    results = []
    for task_dir in sorted(path for path in tasks.iterdir() if path.is_dir()):
        raw = await TaskStorage(task_dir, task_dir.name).load_task_result()
        if raw:
            results.append(raw)
    design = {row.get("design") for row in results if row.get("design")}
    if len(design) != 1:
        print(f"expected one design among the results, found {sorted(design)}")
        return 1
    rebuilt = _ledger_rows(SimpleNamespace(task_results=results), design.pop())
    target = run_dir(run_name) / "ledgers.jsonl"
    old = list(jsonl_rows(target)) if target.is_file() else []
    old_bytes = {row["episode_id"]: jsonl_bytes([row]) for row in old}
    new_bytes = {row["episode_id"]: jsonl_bytes([row]) for row in rebuilt}
    changed = [episode for episode, data in old_bytes.items() if new_bytes.get(episode) != data]
    if changed:
        print(f"refused: {len(changed)} existing row(s) would change, e.g. {changed[0]}")
        return 1
    added = sorted(set(new_bytes) - set(old_bytes))
    print(f"{len(results)} task results; {len(old)} rows kept byte for byte; added {len(added)}: "
          + ", ".join(f"{row['pr_number']} ({len(row['ledger'])} cells, {len(row['findings'])} findings)"
                      for row in rebuilt if row["episode_id"] in added))
    if added:
        target.write_bytes(jsonl_bytes(rebuilt))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1])))
