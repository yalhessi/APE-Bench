"""The readings of G's sessions that need no ask (README: bar 2's volume half, and "reported, not bars").

Per PR: cells, findings filed (All(G): every candidate and question), how many are questions, `conforms`
refused, `conforms` closed by a self-lookup alone (amendment 2), and what A(G) would withhold (a candidate
whose `would_clear_on` is `change_may_be_wrong` and which carries a verified `check`). Then the controls'
volume, the grounds over every filed finding, and the solo reviewer's published findings on the same PRs
beside G's (DX, AP: the sessions the per-ask reading read). Nothing here reads an ask.

A run still in progress is read from its finished sessions' results; a complete one from `ledgers.jsonl`.

usage (repo root): ape/bin/python <this file> <G run> [<G run> ...]
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.mathlib_review.io import jsonl_rows  # noqa: E402

from smoke_check import self_lookup_only  # noqa: E402

RUNS = Path("results/pr_review_v5/runs")
APE = Path(".ape/runs")
CONTROLS = {33304, 33315, 33438}
#: The solo reviewer's sessions the per-ask reading read, per PR: an AP session on val or post sits in
#: `..._ap_rep<n>` or `..._apt_rep<n>` depending on the PR, so the map names the run, not a pattern.
SESSIONS = json.loads(Path("results/pr_review_v5/probes/ask-reading-2026-10-12/sessions.json").read_text())
SET_KEY = {"dev": "D12", "val": "P14_val", "post": "P14_post"}
LABELS = ("DX1", "DX2", "DX3", "AP1", "AP2", "AP3")
#: The controls have no asks and so no entry in the map; the dev runs cover them.
CONTROL_RUN = {"DX": "iter_ds41_conv_dev_base_rep{}", "AP": "iter_ds41_conv_dev_apt_rep{}"}


def ledger_rows(run: str) -> list:
    """The run's ledger rows; for a run still going, its finished sessions' results."""
    path = RUNS / run / "ledgers.jsonl"
    if path.is_file():
        return list(jsonl_rows(path))
    rows = []
    for result in sorted((APE / run / "tasks").glob("*/task_result.json")):
        raw = json.loads(result.read_text())
        if raw.get("success") and "ledger" in raw:
            rows.append(raw)
    return rows


_PUBLISHED: dict = {}


def published_by_pr(run: str) -> Counter:
    """PR -> findings in the run's `findings.jsonl` (what a solo run published)."""
    if run not in _PUBLISHED:
        counts = Counter()
        for row in jsonl_rows(RUNS / run / "findings.jsonl"):
            found = re.search(r"mathlib4:(\d+):round", row.get("episode_id") or "")
            if found:
                counts[int(found.group(1))] += 1
        _PUBLISHED[run] = counts
    return _PUBLISHED[run]


def solo_published(tag: str, pr: int, label: str) -> int:
    """The solo session `label` (DX1..AP3) on this PR: its published findings."""
    entry = SESSIONS.get(f"{SET_KEY[tag]}/{pr}", {}).get(label)
    run = entry["run"] if entry else CONTROL_RUN[label[:2]].format(label[2])
    return published_by_pr(run)[pr]


def cell_of(row: dict) -> dict:
    """(subject, concern) -> cell, the subject being a declaration, a file path or "PR"."""
    return {(cell.get("declaration"), cell.get("concern")): cell for cell in row.get("ledger") or []}


def withheld_by_policy(finding: dict, cell: dict) -> bool:
    """A(G), fixed in the README: a candidate on `change_may_be_wrong` with a verified check."""
    return (cell.get("disposition") == "candidate" and cell.get("would_clear_on") == "change_may_be_wrong"
            and any(item.get("kind") == "check" and item.get("verified") for item in cell.get("evidence") or []))


def main() -> int:
    grounds = {"ask PRs": Counter(), "controls": Counter()}
    filed_by_set = defaultdict(dict)
    total_filed = total_withheld = 0
    for run in sys.argv[1:]:
        tag = run.split("_")[2]
        rows = sorted(ledger_rows(run), key=lambda row: row["pr_number"])
        print(f"\n{run}: {len(rows)} session(s)")
        print("  PR      cells  filed  questions  conforms-refused  self-lookup-only  A(G)-withholds")
        for row in rows:
            pr, cells = row["pr_number"], row.get("ledger") or []
            by_cell = cell_of(row)
            findings = row.get("findings") or []
            questions = withheld = 0
            for finding in findings:
                cell = by_cell.get((finding.get("declaration"), finding.get("concern"))) or {}
                questions += cell.get("disposition") == "ask_author"
                withheld += withheld_by_policy(finding, cell)
                grounds["controls" if pr in CONTROLS else "ask PRs"][cell.get("would_clear_on") or "no cell"] += 1
            conforming = [cell for cell in cells if cell.get("disposition") == "conforms"]
            self_only = sum(1 for cell in conforming if self_lookup_only(cell))
            mark = "  (control)" if pr in CONTROLS else ""
            print(f"  {pr}  {len(cells):5}  {len(findings):5}  {questions:9}  {row.get('conforms_refused', 0):16}"
                  f"  {self_only:7} of {len(conforming):<5}  {withheld:8}{mark}")
            filed_by_set[tag].setdefault(pr, []).append(len(findings))  # one entry a rep, not the last rep's
            total_filed += len(findings)
            total_withheld += withheld
    print(f"\nA(G) withholds {total_withheld} of {total_filed} filed findings "
          f"({total_withheld / max(total_filed, 1):.1%}; the README's threshold for its own seal is 10%)")
    for label, counter in grounds.items():
        if counter:
            print(f"would_clear_on over filed findings, {label}: {dict(counter.most_common())}")
    print("\nFindings a PR beside the solo reviewer's published findings on the same PRs (rep 1-3):")
    for tag, filed in filed_by_set.items():
        solo = {label: {pr: solo_published(tag, pr, label) for pr in filed} for label in LABELS}
        print(f"  {tag}: PR      G (mean of {max(map(len, filed.values()))} reps)  " + "  ".join(solo))
        for pr in sorted(filed):
            print(f"    {pr}{'*' if pr in CONTROLS else ' '} {sum(filed[pr]) / len(filed[pr]):5.1f}  "
                  + "  ".join(f"{solo[name][pr]:>{len(name)}}" for name in solo))
        means = ([sum(sum(v) / len(v) for v in filed.values()) / len(filed)]
                 + [sum(solo[name].values()) / len(filed) for name in solo])
        print(f"    mean   " + "  ".join(f"{mean:.1f}" for mean in means))
    controls = [n for filed in filed_by_set.values() for pr, ns in filed.items() if pr in CONTROLS for n in ns]
    if controls:
        print(f"\nControls: {controls}, mean {sum(controls) / len(controls):.1f} a PR (bar 2: at most 2.0, "
              "over three controls and three reps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
