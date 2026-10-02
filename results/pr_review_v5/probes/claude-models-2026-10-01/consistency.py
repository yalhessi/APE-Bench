"""Run-to-run consistency of the solo reviewer on the dev held-out 12 (2026-10-01).

Reads the committed judge audits (`results/pr_review_v5/audits/<audit>/semantic_report.json`) and
the committed runs' `findings.jsonl`, and prints:

1. the per-obligation spine: every reviewer cell's status on each of the 23 obligations
   (`HIT` = issue hit, `loc` = a finding anchored at the gold change without the gold issue,
   `.` = nothing there), with the union and the stable set over the Opus 5.x cells;
2. how much two cells revisit the same change targets (Jaccard over `(pr, primary_change_id)`),
   which says whether reps differ in *where* they look or in *what they ask*;
3. control-PR emission and candidate counts per cell;
4. when `.ape/runs/<run>` is present (it is not committed): per-session visible text and the
   finding-budget truncations the solo task logged.

Run from the repository root: `ape/bin/python results/pr_review_v5/probes/claude-models-2026-10-01/consistency.py`.
Written for `docs/plans/2026-10-01-beyond-the-solo-baseline.md`.

`--runs a,b,c` adds cells for further judged runs -- a design's reps beside the baseline's
(`docs/plans/2026-10-02-review-designs.md` §2) -- each labelled by its run name (or `label=run`),
its audit found by the judge's convention (`pr_review_v5_judge_<run>` resolves to the audit directory
named like the run with `_` as `-`); a run with no audit yet is reported and skipped. `--cells` keeps
only the named labels, so a design can be read against the cells it is compared with.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AUDITS = ROOT / "results/pr_review_v5/audits"
RUNS = ROOT / "results/pr_review_v5/runs"
APE_RUNS = ROOT / ".ape/runs"

#: label -> (judge audit, generation run or None). The swap and X1/X2 came through `probe import`
#: and have no run under `results/pr_review_v5/runs/`.
CELLS = {
    "X1": ("probe-dev-claude-X1", None),
    "X2": ("probe-dev-claude-X2", None),
    "swap": ("probe-dev-claude-swap-S1", None),
    "H55r1": ("probe-dev-opus55-contract2-claude-sub-rep1", "probe_dev_opus55_contract2_claude_sub_rep1"),
    "H55r2": ("probe-dev-opus55-contract2-claude-sub-rep2", "probe_dev_opus55_contract2_claude_sub_rep2"),
    "M5": ("probe-dev-opus5-contract2-claude-sub-rep1", "probe_dev_opus5_contract2_claude_sub_rep1"),
    "Hyg1": ("probe-dev-opus55-contract2-hygiene-claude-sub-rep1", "probe_dev_opus55_contract2_hygiene_claude_sub_rep1"),
    "M48": ("probe-dev-opus48-contract2-claude-sub-rep1", "probe_dev_opus48_contract2_claude_sub_rep1"),
    "g55v2": ("probe-dev-gpt55-Grc-contract2-rep1", "probe_dev_gpt55_Grc_contract2_rep1"),
    "g52v2": ("probe-dev-gpt52-Grc-contract2-rep1", "probe_dev_gpt52_Grc_contract2_rep1"),
}
OPUS5X = ["X1", "X2", "swap", "H55r1", "H55r2", "M5", "Hyg1"]
#: The same harness, model, prompt and effort: the only pair that is a repetition in the strict sense.
SAME_CONFIG = ["H55r1", "H55r2"]
HELD_OUT = [33117, 33145, 33149, 33285, 33294, 33304, 33305, 33315, 33321, 33337, 33362, 33421]


def report(audit: str) -> dict:
    return json.loads((AUDITS / audit / "semantic_report.json").read_text())


def findings(run: str) -> list:
    return [json.loads(line) for line in (RUNS / run / "findings.jsonl").read_text().splitlines() if line.strip()]


def spine(reports: dict) -> None:
    status = {}
    for label, rep in reports.items():
        status[label] = {o["obligation_id"]: ("HIT" if o["issue_status"] == "hit" else "loc" if o["location_hit"] else ".")
                         for o in rep["per_obligation"]}
    obligations = sorted(next(iter(status.values())))
    print("## Per-obligation spine (dev held-out 12, judge v9)\n")
    print("| obligation | " + " | ".join(reports) + " |")
    print("|---|" + "---|" * len(reports))
    for ob in obligations:
        print(f"| `{ob[11:19]}` | " + " | ".join(status[k].get(ob, "?") for k in reports) + " |")
    hits = {k: {ob for ob, s in v.items() if s == "HIT"} for k, v in status.items()}
    print("\n| cells | hit per cell | union | stable (all) |\n|---|---|---|---|")
    for name, cells in (("same config (H55 r1, r2)", SAME_CONFIG), ("Opus 5.x", OPUS5X), ("every cell", list(reports))):
        cells = [c for c in cells if c in hits]
        if not cells:
            continue
        name = f"{name} ({len(cells)} cells)" if name != "every cell" else name
        sets = [hits[c] for c in cells]
        union = set().union(*sets)
        stable = set.intersection(*sets)
        print(f"| {name} | {', '.join(str(len(s)) for s in sets)} | {len(union)} ({len(union) / 23:.2f}) | {len(stable)} |")
    never = [ob for ob in obligations if not any(ob in h for h in hits.values())]
    print(f"\nNever hit by any cell: {len(never)} — " + ", ".join(f"`{ob[11:19]}`" for ob in never))


def overlap(runs: dict) -> None:
    def keys(rows):
        return {(f["pr_number"], f.get("primary_change_id") or (f.get("change_ids") or [None])[0])
                for f in rows if f["pr_number"] in HELD_OUT}
    print("\n## Change targets shared between cells (held-out 12, Jaccard over (pr, primary_change_id))\n")
    print("| a | b | targets a | targets b | shared | Jaccard |\n|---|---|---|---|---|---|")
    names = list(runs)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A, B = keys(runs[a]), keys(runs[b])
            print(f"| {a} | {b} | {len(A)} | {len(B)} | {len(A & B)} | {len(A & B) / len(A | B):.2f} |")


def emission(reports: dict) -> None:
    print("\n## Volume and control emission\n")
    print("| cell | issue recall | candidates | paired | control-PR findings (per PR) | gold alignment |\n|---|---|---|---|---|---|")
    for label, rep in reports.items():
        s, c = rep["silent_pr_emission"], rep["counts"]
        print(f"| {label} | {rep['issue_recall']:.3f} | {c['candidates']} | {c['paired_candidates']} | "
              f"{s['candidates']} ({s['candidates_per_control_pr']}) | {rep['gold_alignment_rate']:.3f} |")


def sessions(run: str) -> None:
    """Visible text per session and budget truncations; needs the uncommitted `.ape/runs/<run>`."""
    base = APE_RUNS / run
    if not base.is_dir():
        print(f"\n(no `.ape/runs/{run}`: session profile skipped)")
        return
    rows, truncations = [], 0
    for conv in glob.glob(str(base / "tasks/*/samples/0/attempts/*/claude_code_conversation_*.jsonl")):
        attempt = os.path.dirname(conv)
        for log in glob.glob(os.path.join(attempt, "logs", "scaffold_*.log")):
            truncations += sum("past the budget" in line for line in open(log, encoding="utf-8", errors="replace"))
        text_blocks = text_chars = n_tools = 0
        for line in open(conv, encoding="utf-8"):
            msg = json.loads(line)
            if msg.get("type") != "assistant":
                continue
            for block in msg.get("message", {}).get("content", []) or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    text_blocks += 1
                    text_chars += len(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    n_tools += 1
        rows.append((n_tools, text_blocks, text_chars))
    rows.sort()
    med = rows[len(rows) // 2] if rows else (0, 0, 0)
    print(f"\n## Sessions of `{run}`\n")
    print(f"- sessions: {len(rows)}; median tool calls {med[0]}; visible text blocks per session "
          f"{min(r[1] for r in rows)}-{max(r[1] for r in rows)} ({min(r[2] for r in rows)}-{max(r[2] for r in rows)} characters)")
    print(f"- submissions truncated by the finding budget: {truncations}")


def audit_of(run: str) -> str:
    """The audit directory a judge run of `run` writes, by the judge's naming convention."""
    return run.replace("_", "-")


def cells_for(runs_arg: str | None, only: str | None) -> dict:
    """`CELLS` plus one cell per `--runs` entry, restricted to `--cells` when given."""
    cells = dict(CELLS)
    for item in [piece.strip() for piece in (runs_arg or "").split(",") if piece.strip()]:
        label, _, run = item.rpartition("=")
        label = label or run
        audit = audit_of(run)
        if not (AUDITS / audit).is_dir():
            print(f"(no audit `{audit}` for run `{run}`: judge it first; cell `{label}` skipped)")
            continue
        cells[label] = (audit, run if (RUNS / run).is_dir() else None)
    if only:
        wanted = [piece.strip() for piece in only.split(",") if piece.strip()]
        unknown = [name for name in wanted if name not in cells]
        if unknown:
            print(f"(unknown cell(s) {unknown}; known: {sorted(cells)})")
        cells = {name: cells[name] for name in wanted if name in cells}
    return cells


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--runs", default=None,
                        help="comma-separated run names (or label=run) to add as cells")
    parser.add_argument("--cells", default=None, help="comma-separated labels to keep")
    args = parser.parse_args(argv)
    cells = cells_for(args.runs, args.cells)
    reports = {label: report(audit) for label, (audit, _) in cells.items() if (AUDITS / audit).is_dir()}
    runs = {label: findings(run) for label, (_, run) in cells.items() if run and (RUNS / run).is_dir()}
    if not reports:
        print("no cells to read")
        return 1
    spine(reports)
    overlap(runs)
    emission(reports)
    for label in SAME_CONFIG:
        if label in cells:
            sessions(cells[label][1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
