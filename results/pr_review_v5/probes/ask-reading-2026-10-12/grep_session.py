"""Find where a session touched something: every block of a transcript whose reasoning, text, tool
call or tool result matches a pattern, printed compactly with its line number.

usage: ape/bin/python grep_session.py <transcript.jsonl> <regex> [<regex> ...] [--context N] [--max M]
A block matches when any pattern matches (case-insensitive). `--context N` prints N characters around
each match (default 400); `--max M` caps the blocks printed (default 40). Tool results are searched
but printed only as a one-line summary (tool name, the matching snippet), so a file dump cannot
flood the reading.
"""
import json
import re
import sys


def main():
    args = [a for a in sys.argv[1:]]
    ctx, mx = 400, 40
    if "--context" in args:
        i = args.index("--context"); ctx = int(args[i + 1]); del args[i:i + 2]
    if "--max" in args:
        i = args.index("--max"); mx = int(args[i + 1]); del args[i:i + 2]
    path, pats = args[0], [re.compile(p, re.I) for p in args[1:]]
    n = 0
    for ln, line in enumerate(open(path), 1):
        if not line.strip():
            continue
        e = json.loads(line)
        for c in (e.get("message") or {}).get("content") or []:
            kind = c.get("type")
            if kind == "thinking":
                body, tag = c.get("reasoning_content") or "", "REASONING"
            elif kind == "text":
                body, tag = c.get("text") or "", f"TEXT[{e.get('type')}]"
            elif kind == "tool_use":
                body, tag = json.dumps(c.get("input")), f"TOOL_USE {c.get('name')}"
            elif kind == "tool_result":
                body, tag = c.get("result_content") or "", f"TOOL_RESULT {c.get('name')}"
                if not isinstance(body, str):
                    body = json.dumps(body)
            else:
                continue
            for p in pats:
                m = p.search(body)
                if not m:
                    continue
                n += 1
                s, t = max(0, m.start() - ctx), min(len(body), m.end() + ctx)
                snippet = body[s:t].replace("\n", " ")
                if kind == "tool_result":
                    snippet = body[max(0, m.start() - 120):m.end() + 120].replace("\n", " ")
                print(f"--- line {ln} {tag} (match {p.pattern!r})\n{snippet}\n")
                break
            if n >= mx:
                print(f"[stopped at --max {mx} blocks]")
                return
    print(f"[{n} matching blocks]")


if __name__ == "__main__":
    main()
