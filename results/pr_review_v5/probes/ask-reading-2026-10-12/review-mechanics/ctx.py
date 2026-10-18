"""Context for re-coding one reading row from its transcript: the ask, the reader's code and quote,
the session's submitted findings at the ask's file, and the transcript turns around the quoted line.

usage: ape/bin/python ctx.py <set> <pr> <ask> <session> [--around N] [--cut N] [--grep REGEX ...]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from load import PROBE, packets, rows, sessions

HERE = Path(__file__).resolve().parent


def main():
    a = sys.argv[1:]
    st, pr, ask, ses = a[0], int(a[1]), a[2], a[3]
    around = int(a[a.index("--around") + 1]) if "--around" in a else 2
    cut = int(a[a.index("--cut") + 1]) if "--cut" in a else 1800
    greps = a[a.index("--grep") + 1:] if "--grep" in a else []
    pk = packets()[(st, pr)]
    A = next(x for x in pk["asks"] if x["id"] == ask)
    r = next(x for x in rows() if x["set"] == st and x["ask"] == ask and x["session"] == ses)
    print(f"=== {st} {pr} {ask} {ses} [{r['batch']}]  family {A['family']}  {A['path']}:{A['line']}")
    print("ASK:", " ".join((A["text"] or "").split())[:500])
    mt = A.get("matcher_text") or {}
    if mt.get("code_at_comment"):
        print("CODE AT COMMENT:", mt["code_at_comment"][-500:].replace("\n", " | "))
    o = A["outcomes"].get(ses, {})
    print(f"MATCHER: m1 {o.get('m1')} ({o.get('note_m1')}) | m2 {o.get('m2')} ({o.get('note_m2')})")
    print(f"READER: {r['behaviour']} l.{r['line']} ap={r.get('ap')}/{r.get('ap_use')} know={r.get('knowledge')}\n  quote: {r['quote']}")
    tr = pk["sessions"][ses]["transcript"]
    # submission findings at the ask's file
    sub = None
    for line in open(tr):
        if not line.strip():
            continue
        e = json.loads(line)
        for c in (e.get("message") or {}).get("content") or []:
            if c.get("type") == "tool_use" and c.get("name") == "submit_findings":
                sub = c.get("input")
    base = Path(A["path"] or "").name
    print("SUBMITTED FINDINGS at that file:")
    for i, f in enumerate((sub or {}).get("findings") or []):
        tgt = f.get("target") or f.get("path") or ""
        if base and base in tgt:
            txt = " ".join((f.get("claim") or f.get("title") or json.dumps(f))[:220].split())
            print(f"  [{i}] {tgt}: {txt}")
    print(f"TRANSCRIPT around l.{r['line']} (+-{around}):")
    if r["line"]:
        lo, hi = max(1, int(r["line"]) - around), int(r["line"]) + around
        out = subprocess.run([sys.executable, str(PROBE / "show_session.py"), tr, "--from", str(lo), "--to", str(hi), "--cut", str(cut)],
                             capture_output=True, text=True).stdout
        print(out)
    for g in greps:
        print(f"GREP {g!r}:")
        out = subprocess.run([sys.executable, str(PROBE / "grep_session.py"), tr, g, "--context", "220", "--max", "7"],
                             capture_output=True, text=True).stdout
        print(out)


if __name__ == "__main__":
    main()
