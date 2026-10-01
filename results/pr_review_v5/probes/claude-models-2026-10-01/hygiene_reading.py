"""Layer 0's reading of a hygiene run (`docs/plans/2026-10-01-beyond-the-solo-baseline.md` §5).

The rule, stated before the run: no recall rule; the layer passes if the budget truncation and
the first message's contradiction are gone and held-out findings per rep are not below H-claude's
77. Beside it, what the new tools did under a live session: whether `Write`/`Edit` were used and
where, whether any write was refused, whether `lean_verify_edit` results carried the linter split,
budget refusals and resubmissions, hover/goto/goal outcomes, and `declaration_search` refusals.

Reads the run's Claude Code transcripts under `.ape/runs/<run>` (not committed) and, when the run
has finalized, `results/pr_review_v5/runs/<run>/findings.jsonl`. Run from the repository root:
`ape/bin/python results/pr_review_v5/probes/claude-models-2026-10-01/hygiene_reading.py [run]`.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tool_outcomes import calls_of, classify  # noqa: E402

DEFAULT_RUN = "probe_dev_opus55_contract2_hygiene_claude_sub_rep1"
HELD_OUT = [33117, 33145, 33149, 33285, 33294, 33304, 33305, 33315, 33321, 33337, 33362, 33421]
CONTROLS = {33304, 33315}


def main(run: str) -> int:
    base = ROOT / ".ape/runs" / run
    sessions = sorted(glob.glob(str(base / "tasks/*/samples/0/attempts/*/claude_code_conversation_*.jsonl")))
    print(f"## {run}: {len(sessions)} session transcripts\n")
    outcomes = defaultdict(Counter)
    writes, write_refusals, budget_refusals, resubmits, split_seen, roots_per_session = [], [], 0, 0, 0, []
    for conv in sessions:
        first = None
        n_submit = 0
        for line in open(conv, encoding="utf-8"):
            record = json.loads(line)
            if record.get("type") == "user" and first is None:
                content = record["message"]["content"]
                first = content if isinstance(content, str) else "\n".join(
                    b.get("text", "") for b in content if isinstance(b, dict))
        roots = {ln[ln.find("/research"):ln.find("/.ape/runs/")] for ln in (first or "").splitlines() if "/.ape/runs/" in ln}
        roots_per_session.append(len(roots))
        for name, tool_input, text, is_error in calls_of(conv):
            if name.endswith("submit_findings"):
                n_submit += 1
                if "exceed this review's budget" in text:
                    budget_refusals += 1
                continue
            cls, _detail = classify(name, text, is_error)
            outcomes[name][cls] += 1
            if name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
                writes.append((name, path.split("/workspaces/")[-1]))
                if "writes outside" in text or "leaves this review's workspace" in text:
                    write_refusals.append((name, path))
            if name.endswith("lean_verify_edit") and "warnings_introduced_by_your_edit" in text:
                split_seen += 1
        resubmits += max(0, n_submit - 1)

    print("| tool | calls | answered | negative | refused | error | env |\n|---|---|---|---|---|---|---|")
    for name, counts in sorted(outcomes.items(), key=lambda item: -sum(item[1].values())):
        print(f"| `{name}` | {sum(counts.values())} | {counts['answered']} | {counts['negative']} | "
              f"{counts['refused']} | {counts['error']} | {counts['env']} |")
    print(f"\n- first message names one root: {Counter(roots_per_session)} (sessions by root count)")
    print(f"- built-in writes: {len(writes)} ({Counter(n for n, _ in writes)}); refused: {len(write_refusals)}")
    for name, path in writes[:12]:
        print(f"  - {name} {path}")
    print(f"- lean_verify_edit results carrying the linter split: {split_seen}")
    print(f"- budget refusals: {budget_refusals}; sessions that submitted more than once: {resubmits}")

    findings_path = ROOT / "results/pr_review_v5/runs" / run / "findings.jsonl"
    if findings_path.is_file():
        findings = [json.loads(l) for l in findings_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        per_pr = Counter(f["pr_number"] for f in findings)
        held = sum(per_pr[pr] for pr in HELD_OUT)
        print(f"\n- held-out findings: {held} (H-claude reps: 77, 77); per PR: "
              + ", ".join(f"{pr}: {per_pr[pr]}" for pr in HELD_OUT))
        print(f"- control-PR findings: {', '.join(f'{pr}: {per_pr[pr]}' for pr in sorted(CONTROLS))} (H-claude: 1.0 per PR)")
        print(f"- Layer 0 rule, findings not below 77: {'PASS' if held >= 77 else 'FAIL'}")
    else:
        print("\n(run not finalized: no findings.jsonl yet)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RUN))
