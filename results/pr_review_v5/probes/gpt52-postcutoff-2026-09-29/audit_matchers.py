"""Matcher audit: every tool call's absolute paths must lie in the matcher's own folder; no git, no web.
Usage: python audit_matchers.py <folder> <transcript.jsonl> [<folder> <transcript> ...]"""
import json, re, sys
ABS = re.compile(r"(?:^|(?<=[\s'\"=(<>|;:]))(/(?:research|common|home|tmp|opt|usr|etc|mnt|data|scratch|root|var|nfs|proc)(?:/[\w.\-+]+)*)")
args = sys.argv[1:]
for folder, transcript in zip(args[::2], args[1::2]):
    n, flagged = 0, []
    for line in open(transcript):
        try: row = json.loads(line)
        except ValueError: continue
        content = (row.get("message") or {}).get("content")
        for b in content if isinstance(content, list) else []:
            if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                continue
            n += 1
            text = " ".join(str(v) for v in (b.get("input") or {}).values())
            why = []
            if b.get("name") in ("WebFetch", "WebSearch"): why.append("web")
            if re.search(r"\bgit\b", text): why.append("git")
            for p in ABS.findall(text):
                if not (p.startswith(folder) or p == "/dev/null" or p.startswith("/usr/bin") or p == "/tmp"):
                    why.append("outside " + p[-70:])
            if b.get("name") in ("Read", "Write", "Edit") and not str((b.get("input") or {}).get("file_path", "")).startswith(folder):
                why.append("file tool outside")
            if why: flagged.append(f"{b.get('name')} [{'; '.join(dict.fromkeys(why))}]: {text.replace(folder, '<dir>')[:140]!r}")
    print(f"{folder.rsplit('scratchpad/',1)[-1]}: {n} calls, {len(flagged)} flagged")
    for f in flagged: print("   ", f)
