"""The local-unlock screen beside its base: per run, obligations and resolution hits (judge v9),
findings on the dev held-out 12, held-out PRs with no finding, change targets with a finding, judged
pairs, obligations hit per finding, and findings on the two control PRs.

Run from the worktree or repo root: `ape/bin/python results/pr_review_v5/probes/local-unlock-2026-10-03/screen.py`.
A run not yet judged prints as such. Reads only each run's `findings.jsonl` and its audit's
`semantic_matches.jsonl`, as `../contract-2026-10-01/breadth.py` does.
"""

import json
from pathlib import Path

HELD_OUT = [33117, 33145, 33149, 33285, 33294, 33304, 33305, 33315, 33321, 33337, 33362, 33421]
CONTROLS = {33304, 33315}
#: label -> run name; the audit is the run name with dashes, as `judge --of` derives it.
RUNS = {
    "base r1": "iter_local397_contract2_dev_rep1",
    "base r2": "iter_local397_contract2_dev_rep2",
    "base r3": "iter_local397_contract2_dev_rep3",
    "base high": "iter_local397_contract2_high_dev_rep1",
    **{f"{label} r{n}": f"iter_local397_unlock_{label}_rep{n}"
       for label in ["U", "O", "C", "T", "E", "B", "R", "D", "N", "V", "H", "S1", "S2", "S3", "Q", "K"]
       for n in range(1, 6)},
}


def main():
    print(f"{'run':10} {'obl':>3} {'res':>3} {'findings':>8} {'per PR':>6} {'empty PRs':>9} "
          f"{'targets':>7} {'pairs':>5} {'hits/finding':>12} {'control':>7}")
    for label, run in RUNS.items():
        findings_path = Path(f"results/pr_review_v5/runs/{run}/findings.jsonl")
        matches_path = Path(f"results/pr_review_v5/audits/{run.replace('_', '-')}/semantic_matches.jsonl")
        if not findings_path.is_file():
            continue
        if not matches_path.is_file():
            print(f"{label:10} (not judged yet)")
            continue
        findings = [json.loads(l) for l in findings_path.open() if l.strip()]
        held = [f for f in findings if f["pr_number"] in HELD_OUT]
        real = [pr for pr in HELD_OUT if pr not in CONTROLS]
        empty = sum(1 for pr in real if not any(f["pr_number"] == pr for f in held))
        targets = {(f["pr_number"], c) for f in held for c in f.get("change_ids") or []}
        matches = [json.loads(l) for l in matches_path.open() if l.strip()]
        obligations = {m["obligation_id"] for m in matches if m.get("issue_match")}
        resolved = {m["obligation_id"] for m in matches if m.get("resolution_match")}
        control = sum(1 for f in held if f["pr_number"] in CONTROLS)
        print(f"{label:10} {len(obligations):3} {len(resolved):3} {len(held):8} {len(held) / 12:6.1f} "
              f"{empty:6} / 10 {len(targets):7} {len(matches):5} "
              f"{len(obligations) / max(len(held), 1):12.3f} {control:7}")


if __name__ == "__main__":
    main()
