"""What every tool call in the Opus subscription runs came back with (2026-10-01).

Reads the Claude Code conversation transcripts of the runs under `.ape/runs/` (not committed) and
classifies each tool call's result:

- `answered`: the tool ran and answered (a compile, a hit list, a file);
- `negative`: the tool ran and found nothing (`compile_errors`, no matches, no files, an empty
  census), which is an answer about the world, not a failure;
- `refused`: the tool refused the call's arguments (`invalid_request`, a bad path, a name it would
  not search), so the reviewer spent a turn and learned nothing about the code;
- `error`: the call never ran (malformed input, a tool that does not exist, a containment refusal,
  a CLI parameter the installed version lacks);
- `env`: the tool ran and could not answer (`environment_failure`, `timeout`, a missing store).

`submit_findings` is counted separately: the scaffold ends the session at submission, so the SDK
records the result of that one call as "rejected" whatever happened; `task_result.json` is the
record of it.

The measurement behind the hygiene layer's tool commits (`docs/plans/2026-10-01-beyond-the-solo-baseline.md`
§4, Layer 0). Run from the repository root:
`ape/bin/python results/pr_review_v5/probes/claude-models-2026-10-01/tool_outcomes.py [run ...]`.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RUNS = (
    "probe_dev_opus55_contract2_claude_sub_rep1",
    "probe_dev_opus55_contract2_claude_sub_rep2",
    "probe_dev_opus5_contract2_claude_sub_rep1",
)
NEGATIVE_OUTCOMES = {"compile_errors", "no_result"}
REFUSED_OUTCOMES = {"invalid_request", "blocked"}
ENV_OUTCOMES = {"environment_failure", "timeout"}


def classify(name: str, text: str, is_error: bool) -> tuple[str, str]:
    """(class, detail) for one tool result."""

    head = text[:400]
    if "<tool_use_error>" in head or is_error:
        if "No such tool available" in head:
            return "error", "no such tool"
        if "could not be parsed as JSON" in head:
            return "error", "malformed input"
        if "unexpected parameter" in head:
            return "error", "parameter the CLI lacks"
        return "error", head[:60]
    if head.startswith("PreToolUse:") and "hook error" in head:
        return "error", "containment refusal"
    if name in ("Grep", "Glob", "Read"):
        if "No matches found" in head or "No files found" in head:
            return "negative", ""
        if "File does not exist" in head or "Search failed" in head:
            return "refused", head[:60]
        return "answered", ""
    try:
        payload = json.loads(text)
    except (ValueError, TypeError):
        payload = None
    if not isinstance(payload, dict):
        return "answered", ""
    outcome = payload.get("outcome")
    if outcome in REFUSED_OUTCOMES:
        return "refused", str(payload.get("error", ""))[:70]
    if outcome in ENV_OUTCOMES:
        return "env", str(payload.get("message") or payload.get("error", ""))[:70]
    if outcome == "tool_error":
        return "error", str(payload.get("error", ""))[:70]
    if outcome in NEGATIVE_OUTCOMES:
        return "negative", ""
    if payload.get("success") is False:
        error = str(payload.get("error", ""))
        if "no declaration table" in error:
            return "env", "no declaration table"
        return "refused", error[:70]
    if payload.get("count") == 0 or payload.get("verdict") == "insufficient_evidence":
        return "negative", str(payload.get("empty_because", ""))
    return "answered", ""


def calls_of(conversation: str):
    uses, results = {}, {}
    for line in open(conversation, encoding="utf-8"):
        record = json.loads(line)
        kind = record.get("type")
        if kind == "assistant":
            for block in record.get("message", {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    uses[block["id"]] = (block["name"], block.get("input") or {})
        elif kind == "user":
            content = record.get("message", {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    raw = block.get("content")
                    text = (raw if isinstance(raw, str)
                            else "\n".join(b.get("text", "") for b in raw if isinstance(b, dict))
                            if isinstance(raw, list) else str(raw))
                    results[block["tool_use_id"]] = (text, bool(block.get("is_error")))
    for use_id, (name, tool_input) in uses.items():
        text, is_error = results.get(use_id, ("", False))
        yield name, tool_input, text, is_error


def main(runs) -> int:
    table = defaultdict(Counter)
    details = defaultdict(Counter)
    for run in runs:
        pattern = str(ROOT / ".ape/runs" / run / "tasks/*/samples/0/attempts/*/claude_code_conversation_*.jsonl")
        for conversation in glob.glob(pattern):
            for name, _tool_input, text, is_error in calls_of(conversation):
                if name.endswith("submit_findings"):
                    table[name]["submissions"] += 1
                    continue
                cls, detail = classify(name, text, is_error)
                table[name][cls] += 1
                if cls in ("refused", "error", "env") and detail:
                    details[(name, cls)][detail] += 1
    print("| tool | calls | answered | negative | refused | error | env |\n|---|---|---|---|---|---|---|")
    for name, counts in sorted(table.items(), key=lambda item: -sum(item[1].values())):
        total = sum(counts.values())
        print(f"| `{name}` | {total} | {counts['answered']} | {counts['negative']} | {counts['refused']} | "
              f"{counts['error']} | {counts['env']} |" if "submissions" not in counts
              else f"| `{name}` | {total} | (ends the session) | | | | |")
    print("\nWhy, where a call was refused, errored or could not answer:\n")
    for (name, cls), reasons in sorted(details.items()):
        for reason, count in reasons.most_common(4):
            print(f"- `{name}` {cls} x{count}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or DEFAULT_RUNS))
