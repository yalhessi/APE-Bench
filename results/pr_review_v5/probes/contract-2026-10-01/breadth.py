"""Breadth beside recall on the dev held-out 12: findings, change targets with a finding, judged pairs,
obligations hit and hits per finding per reviewer, and the reviewer's account in bullet lines.

The table in docs/todo/reviewer-model-gap.md (a394f572), recomputed here from the runs' own
`findings.jsonl` and the judge's `semantic_matches.jsonl`, so the contract run reads on the same code.
`notes bullets` counts lines opening with `-` or `*`: Claude's `notes.md` (dev median 26.5, val 23,
post-cutoff 18), and `review_notes` from a run's `task_result.json` when it has them.

Run from the repo root: `ape/bin/python results/pr_review_v5/probes/contract-2026-10-01/breadth.py`.
"""

import collections
import json
import re
import statistics
import sys
from pathlib import Path

# Run by path, the script's own directory is on sys.path and the repo root is not.
sys.path[:0] = [".", "src"]

HELD_OUT = [33117, 33145, 33149, 33285, 33294, 33304, 33305, 33315, 33321, 33337, 33362, 33421]
#: label -> (run under results/pr_review_v5/runs, judge audit under results/pr_review_v5/audits)
RUNS = {
    "Claude X1": ("probe_dev_claude_X1", "probe-dev-claude-X1"),
    "Claude X2": ("probe_dev_claude_X2", "probe-dev-claude-X2"),
    "Claude swap": ("probe_dev_claude_swap_S1", "probe-dev-claude-swap-S1"),
    "gpt-5.2 off": ("probe_dev_gpt52_G_rep1", "probe-dev-gpt52-G-rep1"),
    "gpt-5.2 carried": ("probe_dev_gpt52_Grc_rep1", "probe-dev-gpt52-Grc-rep1"),
    "gpt-5.5 carried": ("probe_dev_gpt55_Grc_rep1", "probe-dev-gpt55-Grc-rep1"),
    "gpt-5.4 carried": ("probe_dev_gpt54_Grc_rep1", "probe-dev-gpt54-Grc-rep1"),
    "gpt-5.2 contract": ("probe_dev_gpt52_Grc_contract_rep1", "probe-dev-gpt52-Grc-contract-rep1"),
    "gpt-5.2 contract2": ("probe_dev_gpt52_Grc_contract2_rep1", "probe-dev-gpt52-Grc-contract2-rep1"),
    "gpt-5.5 contract2": ("probe_dev_gpt55_Grc_contract2_rep1", "probe-dev-gpt55-Grc-contract2-rep1"),
    # docs/plans/2026-10-01-claude-models-under-the-harness.md: contract v2 under Claude Code.
    "H-claude opus55": ("probe_dev_opus55_contract2_claude_sub_rep1",
                        "probe-dev-opus55-contract2-claude-sub-rep1"),
    "M-5 opus5": ("probe_dev_opus5_contract2_claude_sub_rep1",
                  "probe-dev-opus5-contract2-claude-sub-rep1"),
}
BULLET = re.compile(r"^\s*[-*]\s+", re.M)
CLAUDE_NOTES = "results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr{pr}/{who}/notes.md"


def notes_bullets(label, run):
    """Median bullet lines per held-out PR in the reviewer's account, or None without one."""

    if label == "Claude swap":
        counts = []
        for pr in HELD_OUT:
            path = Path(f"results/pr_review_v5/probes/contract-2026-10-01/swap/pr{pr}/S1/submission.json")
            if path.is_file():
                counts.append(len(BULLET.findall(json.loads(path.read_text()).get("notes", ""))))
    elif label.startswith("Claude"):
        who = label.split()[-1]
        counts = [len(BULLET.findall(Path(CLAUDE_NOTES.format(pr=pr, who=who)).read_text()))
                  for pr in HELD_OUT if Path(CLAUDE_NOTES.format(pr=pr, who=who)).is_file()]
    else:
        counts = [len(BULLET.findall(result["review_notes"])) for result in _task_results(run)
                  if result.get("pr_number") in HELD_OUT and result.get("review_notes")]
    return statistics.median(counts) if counts else None


def _task_results(run):
    """Each task's successful result through `TaskStorage`, as `analysis.probes._solo` reads them."""

    import asyncio

    from ape.orchestration.persistence import TaskStorage

    async def load():
        out = []
        tasks = Path(".ape/runs") / run / "tasks"
        for task_dir in sorted(p for p in tasks.iterdir() if p.is_dir()) if tasks.is_dir() else []:
            result = await TaskStorage(task_dir, task_dir.name).load_task_result()
            if result and result.get("success"):
                out.append(result)
        return out

    return asyncio.run(load())


def main():
    targets = collections.Counter()
    for line in open("inputs/pr_review_v4/releases/dev-medium-0.3.0/derived/change_graphs.jsonl"):
        graph = json.loads(line)
        if graph["pr_number"] in HELD_OUT and ":round1:" in graph["episode_id"]:
            targets[graph["pr_number"]] = len(graph["targets"])
    total = sum(targets.values())
    print(f"held-out 12: {total} change targets in all\n")
    print(f"{'reviewer':17} {'findings':>8} {'per PR':>6} {'targets':>8} {'pairs':>6} "
          f"{'matched':>7} {'obligations':>11} {'hits/finding':>12} {'notes bullets':>13}")
    for label, (run, audit) in RUNS.items():
        findings_path = Path(f"results/pr_review_v5/runs/{run}/findings.jsonl")
        matches_path = Path(f"results/pr_review_v5/audits/{audit}/semantic_matches.jsonl")
        if not findings_path.is_file() or not matches_path.is_file():
            print(f"{label:17} (not judged yet)")
            continue
        findings = [json.loads(l) for l in findings_path.open() if l.strip()]
        findings = [f for f in findings if f["pr_number"] in HELD_OUT]
        hit_targets = {(f["pr_number"], c) for f in findings for c in f.get("change_ids") or []}
        matches = [json.loads(l) for l in matches_path.open() if l.strip()]
        obligations = {m["obligation_id"] for m in matches if m.get("issue_match")}
        bullets = notes_bullets(label, run)
        print(f"{label:17} {len(findings):8} {len(findings) / 12:6.1f} {len(hit_targets):8} "
              f"{len(matches):6} {sum(bool(m.get('issue_match')) for m in matches):7} "
              f"{len(obligations):11} {len(obligations) / max(len(findings), 1):12.3f} "
              f"{'-' if bullets is None else bullets:>13}")


if __name__ == "__main__":
    main()
