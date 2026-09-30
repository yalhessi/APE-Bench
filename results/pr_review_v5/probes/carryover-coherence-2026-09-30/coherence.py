"""Coherence of gpt solo sessions, and whether their reasoning reached the next turn.

Usage, from the repo root:
    python results/pr_review_v5/probes/carryover-coherence-2026-09-30/coherence.py RUN[:PR,...] ...

Per session, from the last cumulative conversation file (the per-turn files are cumulative) and the
raw turn files:
  far repeats      a call identical in tool and arguments to one made >= FAR assistant turns
                   earlier, plus a file_read overlapping a range of the same file read >= FAR turns
                   earlier; per 100 calls
  negative repeats a call identical to an earlier call whose result was empty or a failure; per 100
                   turns (the earlier inspection's forgetting signature)
  zero-reasoning   turns that spent no reasoning tokens
  signatures       turns whose assistant message carries encrypted reasoning items for the next turn

Carried reasoning, per run: y(n) = prompt(n+1) - prompt(n) - visible_output(n) is regressed on
reasoning(n) and the characters of turn n's tool results. Reasoning re-sent at turn n+1 is billed as
its input, so the coefficient on reasoning(n) is about 1 when it was carried and about 0 when not.
"""
import glob
import json
import re
import sys
from pathlib import Path

import numpy as np

FAR = 5


def turn_no(path):
    return int(re.search(r"__turn_(\d+)__", path).group(1))


def last_conversation(task):
    convs = [f for f in glob.glob(f"{task}/samples/0/attempts/*/conversations/*.jsonl")
             if not f.endswith("_raw.jsonl")]
    return max(convs, key=lambda f: (Path(f).parts[-3], turn_no(f))) if convs else None


def raw_usage(task):
    rows = []
    for f in glob.glob(f"{task}/samples/0/attempts/*/conversations/*_raw.jsonl"):
        u = json.loads(open(f).readline()).get("usage") or {}
        rows.append(((Path(f).parts[-3], turn_no(f)), u.get("prompt_tokens") or 0, u.get("completion_tokens") or 0,
                     (u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0))
    return [r[1:] for r in sorted(rows)]


def negative(content):
    c = content or ""
    return ('"success": false' in c[:40] or c.startswith('{"success": true, "results": []')
            or c.startswith('{"success": true, "count": 0,'))


def conversation(task):
    """Calls as (turn, id, tool, arguments); tool results by call id; characters of tool results
    after each assistant turn; and (reasoning items, with encrypted content) each turn carried."""
    calls, results, chars, carried, turn = [], {}, [], [], 0
    for line in open(last_conversation(task)):
        r = json.loads(line)
        message = r.get("message") if isinstance(r.get("message"), dict) else {}
        if r["type"] == "assistant":
            turn += 1
            chars.append(0)
            signature = message.get("signature")
            items = [e for e in json.loads(signature)["responses_output"] if e.get("type") == "reasoning"] if signature else []
            carried.append((len(items), sum(bool(e.get("encrypted_content")) for e in items)))
        for b in message.get("content") or []:
            if r["type"] == "assistant" and b.get("type") == "tool_use":
                calls.append((turn, b["id"], b["name"], b.get("input") or {}))
            elif b.get("type") == "tool_result":
                results[b.get("tool_use_id")] = b.get("result_content")
                if chars:
                    chars[-1] += len(b.get("result_content") or "")
    return calls, results, chars, carried


def session(task):
    if not last_conversation(task):
        return None
    calls, results, _, carried = conversation(task)
    first, neg, reads = {}, set(), {}
    far = negrep = 0
    for t, cid, name, a in calls:
        k = name + json.dumps(a, sort_keys=True, default=str)
        far += k in first and t - first[k] >= FAR
        negrep += k in neg
        first.setdefault(k, t)
        if negative(results.get(cid)):
            neg.add(k)
        if name == "file_read":
            p, lo, hi = a.get("file_path"), a.get("line_start") or 1, a.get("line_end") or 10**9
            far += any(l <= hi and lo <= h and t - tt >= FAR for tt, l, h in reads.get(p, []))
            reads.setdefault(p, []).append((t, lo, hi))
    usage = raw_usage(task)
    out = json.loads((Path(task) / "task_outcome.json").read_text())
    sample = (out.get("samples") or [{}])[0]
    return {"pr": int(re.search(r"_(\d+)_round", out["task_id"]).group(1)), "status": sample.get("status"),
            "turns": len(carried), "calls": len(calls), "far": far, "neg": negrep,
            "zero": sum(u[2] == 0 for u in usage), "reasoning": sum(u[2] for u in usage),
            "signed": sum(1 for c in carried if c[1]),
            "billed": sum(a.get("billed_cost") or 0 for a in sample.get("attempts") or [])}


def carried_coefficient(tasks):
    X, Y = [], []
    for task in tasks:
        if not last_conversation(task):
            continue
        usage, chars = raw_usage(task), conversation(task)[2]
        for n in range(min(len(usage), len(chars)) - 1):
            (p0, c0, r0), p1 = usage[n], usage[n + 1][0]
            X.append([r0, chars[n], 1.0])
            Y.append(p1 - p0 - (c0 - r0))
    if len(Y) < 3:
        return None, len(Y)
    coef, *_ = np.linalg.lstsq(np.array(X), np.array(Y), rcond=None)
    return coef[0], len(Y)


def main(specs):
    print("| run | PR | status | turns | calls | far repeats /100 calls | negative repeats /100 turns "
          "| zero-reasoning turns | reasoning tokens | turns carrying reasoning | billed |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    coefficients = []
    for spec in specs:
        name, _, prs = spec.partition(":")
        wanted = {int(p) for p in prs.split(",")} if prs else None
        tasks = [t for t in sorted(glob.glob(f".ape/runs/{name}/tasks/*"))
                 if (s := session(t)) and (not wanted or s["pr"] in wanted)]
        for s in sorted((session(t) for t in tasks), key=lambda s: s["pr"]):
            print(f"| {name.removeprefix('probe_')} | {s['pr']} | {s['status']} | {s['turns']} | {s['calls']} | "
                  f"{100 * s['far'] / max(s['calls'], 1):.1f} | {100 * s['neg'] / max(s['turns'], 1):.1f} | "
                  f"{s['zero'] / max(s['turns'], 1):.0%} | {s['reasoning']:,} | {s['signed']}/{s['turns']} | ${s['billed']:.2f} |")
        coefficients.append((name, *carried_coefficient(tasks)))
    print("\n| run | turn pairs | coefficient on the previous turn's reasoning |\n|---|---|---|")
    for name, coef, n in coefficients:
        print(f"| {name.removeprefix('probe_')} | {n} | {'-' if coef is None else f'{coef:.2f}'} |")


if __name__ == "__main__":
    main(sys.argv[1:])
