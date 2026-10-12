"""Print a session's turns in order, compactly: reasoning and text in full (or cut), tool calls as one
line, tool results as a short head. For reading what a session did between two line numbers.

usage: ape/bin/python show_session.py <transcript.jsonl> [--from L] [--to L] [--cut N] [--submission]
`--submission` prints only the submit_findings call (the findings and the message) and exits.
"""
import json
import sys


def main():
    args = sys.argv[1:]
    path = args[0]
    lo, hi, cut, sub = 1, 10 ** 9, 1200, False
    if "--from" in args:
        lo = int(args[args.index("--from") + 1])
    if "--to" in args:
        hi = int(args[args.index("--to") + 1])
    if "--cut" in args:
        cut = int(args[args.index("--cut") + 1])
    if "--submission" in args:
        sub = True
    for ln, line in enumerate(open(path), 1):
        if not line.strip():
            continue
        e = json.loads(line)
        for c in (e.get("message") or {}).get("content") or []:
            kind = c.get("type")
            if sub:
                if kind == "tool_use" and c.get("name") == "submit_findings":
                    print(json.dumps(c.get("input"), indent=1, ensure_ascii=False))
                    return
                continue
            if ln < lo or ln > hi:
                continue
            if kind == "thinking":
                print(f"[{ln}] REASONING: {(c.get('reasoning_content') or '')[:cut]}")
            elif kind == "text":
                print(f"[{ln}] TEXT({e.get('type')}): {(c.get('text') or '')[:cut]}")
            elif kind == "tool_use":
                print(f"[{ln}] TOOL {c.get('name')}: {json.dumps(c.get('input'))[:300]}")
            elif kind == "tool_result":
                body = c.get("result_content") or ""
                if not isinstance(body, str):
                    body = json.dumps(body)
                print(f"[{ln}] RESULT {c.get('name')}: {body[:200].replace(chr(10), ' ')}")
    if sub:
        print("[no submit_findings call found]")


if __name__ == "__main__":
    main()
