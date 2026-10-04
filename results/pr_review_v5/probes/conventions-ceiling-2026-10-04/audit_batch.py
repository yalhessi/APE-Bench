"""Audit every subagent a `run_claude_batch.sh` stream started.

Per subagent transcript: the folder it was given, the (model, CLI, effort) of its assistant entries,
`cli probe audit` of its tool calls against that folder, and what it wrote. Exits 1 on any flag, so
a caller can hold back a commit until the flag has been read by hand.

usage (repo root, PYTHONPATH=$PWD/src): python3 <this file> <batch>.jsonl
"""
import collections
import glob
import json
import os
import re
import subprocess
import sys

session = None
with open(sys.argv[1], encoding="utf-8") as handle:
    for line in handle:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "system" and d.get("subtype") == "init":
            session = d["session_id"]
            break
(root,) = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{session}"))
flags = 0
for transcript in sorted(glob.glob(f"{root}/subagents/agent-*.jsonl")):
    first, meta = None, collections.Counter()
    with open(transcript, encoding="utf-8") as handle:
        for line in handle:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            msg = d.get("message") or {}
            if first is None and d.get("type") == "user":
                content = msg.get("content")
                first = content if isinstance(content, str) else " ".join(
                    b.get("text", "") for b in content if isinstance(b, dict))
            if d.get("type") == "assistant":
                meta[(msg.get("model"), d.get("version"), d.get("effort"))] += 1
    m = re.search(r"working directory is `([^`]+)`|working folder is:\s*(\S+)", first or "")
    folder = m.group(1) or m.group(2)
    run = subprocess.run(["ape/bin/python", "-m", "src.mathlib_review.review.cli", "probe", "audit",
                          "--folder", folder, "--transcript", transcript], capture_output=True, text=True)
    report = json.loads(run.stdout)
    flags += len(report["flagged"])
    wrote = [name for name in ("findings.json", "notes.md", "matches.json") if os.path.exists(f"{folder}/{name}")]
    count = len(json.load(open(f"{folder}/findings.json"))) if "findings.json" in wrote else None
    print(f"{folder.split('/probes/')[-1].split('/scratchpad/')[-1]} | {dict(meta)} | {report['calls']} tool calls, "
          f"{len(report['flagged'])} flagged | wrote {wrote}" + (f", {count} findings" if count is not None else ""))
    for flag in report["flagged"]:
        print("   FLAG", flag.get("why"), "|", str(flag.get("input"))[:400])
print(f"session {session}: {flags} flag(s)")
sys.exit(1 if flags else 0)
