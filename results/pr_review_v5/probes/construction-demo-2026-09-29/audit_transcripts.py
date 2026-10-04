"""Leak audit: every tool call a reviewer or matcher made, from its transcript, checked against
its allowed directory. Prints counts and each flagged call (truncated), never file contents.

Three kinds of flag:
- `outside`: an absolute path outside the allowed directory (a reviewer's own `/tmp` files are
  allowed), git, the workspace store, a Mathlib checkout, or the web;
- `study scratch`: this study's scratch (`construction-demo/`), which holds every session's
  workdir and raw tool outputs, other than the session's own;
- `foreign scratch`: a path in the shared session scratchpad the reviewer did not itself write
  (reviewers there wrote snippet files, so one could read another's), and any mention of the
  round-1 feedback file, the match inputs, or an agent transcript.

Usage: python3 audit_transcripts.py <allowed_dir> <transcript.jsonl> [<allowed_dir> <transcript> ...]
"""
import json, re, sys

FLAG = re.compile(r"\bgit\b|data/code_execute|workspaces/|mathlib4|\.\./")
#: agent transcripts are `/tasks/a<16 hex>.output`; `/tasks/b....output` is a reviewer's own
#: background command.
SENSITIVE = re.compile(r"val60_feedback|asks_pr|/match/|k_index|/tasks/a[0-9a-f]{16}\.output|matches\.\d")
ROOTS = r"(?:research|common|home|tmp|opt|usr|etc|mnt|data|scratch|root|var|nfs|proc)"
ABS = re.compile(r"(?:^|(?<=[\s'\"=(<>|;:]))(/" + ROOTS + r"(?:/[\w.\-+]+)*)")
WRITES = re.compile(r"\bmkdir\b|>|\btee\b|\bcp\b|\bmv\b|cat\s*<<")
WRITE = re.compile(r"(?:>>?|\btee\s+(?:-a\s+)?|\bmkdir\s+(?:-p\s+)?|\btouch\s+)\s*['\"]?(/[\w.\-/+]+)")


def calls(path):
    for line in open(path):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        msg = row.get("message") or {}
        content = msg.get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                yield block.get("name"), block.get("input") or {}


def session_of(allowed):
    tail = allowed.rstrip("/").split("construction-demo-2026-09-29/")[-1]
    return tail  # e.g. pr34091/X1


args = sys.argv[1:]
for allowed, transcript in zip(args[::2], args[1::2]):
    own_session = session_of(allowed)
    items = list(calls(transcript))
    # A top-level entry of the shared scratchpad is the reviewer's own when its first appearance
    # in the transcript is in a call that writes (a Write, a mkdir, a redirection, a copy).
    first_seen = {}
    for name, inp in items:
        text = " ".join(str(v) for v in inp.values())
        writes = name in ("Write", "Edit", "NotebookEdit") or bool(WRITES.search(text))
        for p in ABS.findall(text):
            if "/scratchpad/" in p and "construction-demo" not in p:
                key = p.split("/scratchpad/", 1)[1].split("/", 1)[0]
                first_seen.setdefault(key, "write" if writes else "read")
    flagged = []
    for name, inp in items:
        text = " ".join(str(v) for v in inp.values())
        reasons = []
        if name in ("WebFetch", "WebSearch"):
            reasons.append("web")
        hit = FLAG.search(text.replace(allowed, ""))
        if hit:
            reasons.append(f"pattern {hit.group(0)!r}")
        if SENSITIVE.search(text):
            reasons.append(f"sensitive {SENSITIVE.search(text).group(0)!r}")
        for p in ABS.findall(text):
            if p.startswith(allowed) or p == "/dev/null":
                continue
            if "construction-demo/" in p:
                if f"/{own_session}" not in p and not p.rstrip("/").endswith("construction-demo"):
                    reasons.append(f"study scratch {p[-60:]}")
                elif p.rstrip("/").endswith("construction-demo"):
                    reasons.append(f"study scratch root {p[-40:]}")
            elif "/scratchpad" in p:
                key = p.split("/scratchpad/", 1)[1].split("/", 1)[0] if "/scratchpad/" in p else ""
                if not key:
                    reasons.append("scratchpad root listed or read")
                elif first_seen.get(key) == "read":
                    reasons.append(f"foreign scratch {key}")
            elif not p.startswith("/tmp/"):
                reasons.append(f"outside {p[:70]}")
        if reasons:
            flagged.append(f"{name} [{'; '.join(dict.fromkeys(reasons))}]: "
                           f"{text.replace(allowed, '<dir>')[:130]!r}")
    print(f"{own_session}: {len(items)} calls, {len(flagged)} flagged")
    for f in flagged:
        print("   ", f)
