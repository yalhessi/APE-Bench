"""The smoke's harness health checks (README, amendment 1), fixed before any session ran.

Every smoke session ends with a submitted result; at most 10% of a session's cells are `unstated`;
no session stops on its turn or token limit. Prints one line per session and exits 1 if any check
fails. Reads `run_manifest.json`, `ledgers.jsonl` and each task's `task_outcome.json`; no ask is read.

usage (repo root): ape/bin/python <this file> <run name> [<run name> ...]
"""
import json
import sys
from pathlib import Path

RUNS = Path("results/pr_review_v5/runs")
APE = Path(".ape/runs")
LIMIT_STOPS = {"paused_max_turns", "paused_token_limit", "paused_cost_limit"}


def rows(path: Path):
    from src.mathlib_review.io import jsonl_rows

    return list(jsonl_rows(path)) if path.is_file() else []


#: What every G session's first message must carry: the conventions section and the contract.
MARKS = {"the conventions section": "Under each convention are up to two comments",
         "the contract": "## The review contract"}


def first_messages(run: str) -> dict:
    """PR -> the text of the session's first user message, through the persisted samples."""
    import asyncio

    from src.mathlib_review.analysis.tool_outcomes import _attempt_dirs
    from src.mathlib_review.analysis.trajectory import _SESSION_GLOB
    from src.mathlib_review.io import jsonl_rows

    root = APE / run
    out = {}
    for attempt in asyncio.run(_attempt_dirs(root / "tasks", root)):
        task_dir = next((p for p in attempt.parents if (p / "task_result.json").is_file()), None)
        sessions = sorted(attempt.glob(_SESSION_GLOB))
        if task_dir is None or not sessions:
            continue
        result = json.loads((task_dir / "task_result.json").read_text())
        pr = result.get("pr_number") or (result.get("metadata") or {}).get("pr_number")
        if pr is None:
            import re

            found = re.search(r"mathlib4:(\d+):round", json.dumps(result))
            pr = int(found.group(1)) if found else None
        for row in jsonl_rows(sessions[-1]):
            if row.get("type") == "user":
                out[pr] = "".join(c.get("text") or "" for c in (row.get("message") or {}).get("content") or []
                                  if c.get("type") == "text")
                break
    return out


def main() -> int:
    ok = True
    for run in sys.argv[1:]:
        manifest = RUNS / run / "run_manifest.json"
        status = json.loads(manifest.read_text()).get("completion_status") if manifest.is_file() else None
        ledgers = {row["pr_number"]: row for row in rows(RUNS / run / "ledgers.jsonl")}
        outcomes = {}
        for outcome in sorted((APE / run / "tasks").glob("*/task_outcome.json")):
            data = json.loads(outcome.read_text())
            outcomes[data["task_id"]] = data
        print(f"{run}: completion {status}; {len(ledgers)} ledger(s); {len(outcomes)} task(s)")
        if status != "complete":
            ok = False
        for task_id, data in outcomes.items():
            stop = data.get("execution_status")
            if stop in LIMIT_STOPS or not data.get("has_result"):
                ok = False
                print(f"  FAIL {task_id}: {stop}, result {data.get('has_result')}")
        for pr, delivered in sorted(first_messages(run).items()):
            missing = [label for label, mark in MARKS.items() if mark not in delivered]
            if missing:
                ok = False
                print(f"  FAIL PR {pr}: the first message lacks {', '.join(missing)}")
        for pr, row in sorted(ledgers.items()):
            cells = row.get("ledger") or []
            unstated = sum(1 for cell in cells if cell.get("disposition") == "unstated")
            share = unstated / len(cells) if cells else 1.0
            filed = len(row.get("findings") or [])
            refused = row.get("conforms_refused")
            verdict = "ok" if share <= 0.10 else "FAIL"
            ok = ok and share <= 0.10
            print(f"  {verdict} PR {pr}: {len(cells)} cells, {unstated} unstated ({share:.0%}), "
                  f"{filed} filed, {refused} conforms refused")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
