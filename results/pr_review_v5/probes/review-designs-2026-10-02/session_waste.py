"""Where the turns and the tokens of a Claude Code run went: repetition, failures, bookkeeping.

For each session of a run under `.ape/runs/<run>/tasks/*/samples/0/attempts/*/`, reads the CLI's
stream-json transcript (`claude_code_conversation_*.jsonl`) and reports turns, processed tokens,
tool calls by tool, identical calls repeated, files read more than once, calls that came back as
errors, bookkeeping calls (TodoWrite, scratch Write/Edit), and the design tools' own churn
(record_ledger and submit_findings calls, and the refusals among them). Spends nothing.

    PYTHONPATH=$PWD/src ape/bin/python results/pr_review_v5/probes/review-designs-2026-10-02/session_waste.py <run_name> [--json out.json]
"""

import collections
import glob
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
APE = ROOT / ".ape/runs"


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(item.get("text", "") for item in content if isinstance(item, dict))
    return str(content or "")


def session(attempt: Path) -> dict:
    result = json.loads((attempt.parents[3] / "task_result.json").read_text()) \
        if (attempt.parents[3] / "task_result.json").is_file() else {}
    conv = sorted(attempt.glob("claude_code_conversation_*.jsonl"))[-1]
    rows = [json.loads(line) for line in open(conv, encoding="utf-8") if line.strip()]
    usage, first_prompt = {}, 0
    calls, results = [], {}
    for row in rows:
        message = row.get("message") or {}
        if row.get("type") == "assistant":
            mid = message.get("id")
            if mid and message.get("usage"):
                usage[mid] = message["usage"]
            for block in message.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    calls.append((block["id"], block["name"], block.get("input") or {}))
        elif row.get("type") == "user":
            content = message.get("content")
            if isinstance(content, str) and not first_prompt:
                first_prompt = len(content)
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    results[block["tool_use_id"]] = (bool(block.get("is_error")), text_of(block.get("content")))
                elif isinstance(block, dict) and block.get("type") == "text" and not first_prompt:
                    first_prompt = len(block.get("text", ""))
    processed = sum(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                    + u.get("cache_read_input_tokens", 0) + u.get("output_tokens", 0) for u in usage.values())
    last = list(usage.values())[-1] if usage else {}
    final_context = (last.get("input_tokens", 0) + last.get("cache_creation_input_tokens", 0)
                     + last.get("cache_read_input_tokens", 0))
    by_tool = collections.Counter(name.replace("mcp__core__", "") for _, name, _ in calls)
    signature = collections.Counter(
        (name, hashlib.sha256(json.dumps(inp, sort_keys=True).encode()).hexdigest()) for _, name, inp in calls)
    repeated = sum(n - 1 for n in signature.values() if n > 1)
    reads = collections.Counter(inp.get("file_path") for _, name, inp in calls if name == "Read")
    reread = {path: n for path, n in reads.items() if n > 1}
    errors, refusals = [], collections.Counter()
    for cid, name, inp in calls:
        is_error, text = results.get(cid, (False, ""))
        short = name.replace("mcp__core__", "")
        if is_error or '"success": false' in text or '"success":false' in text \
                or "invalid_request" in text or text.startswith("Not recorded") or "Nothing recorded" in text:
            errors.append((short, text[:160].replace("\n", " ")))
        if short in ("submit_findings", "record_ledger") and (
                "inconsistent" in text or "Not recorded" in text or "Nothing recorded" in text
                or "contradicted by the tools" in text or "needs a ledger entry" in text):
            refusals[short] += 1
    return {
        "attempt": str(attempt.relative_to(APE)), "pr": result.get("pr_number"),
        "turns": len(usage), "processed_tokens": processed, "final_context": final_context,
        "first_prompt_chars": first_prompt, "output_tokens": sum(u.get("output_tokens", 0) for u in usage.values()),
        "tool_calls": len(calls), "by_tool": dict(by_tool.most_common()),
        "identical_repeats": repeated, "files_reread": len(reread), "rereads": sum(n - 1 for n in reread.values()),
        "errors": len(errors), "error_samples": errors[:6], "refusals": dict(refusals),
        "bookkeeping": by_tool.get("TodoWrite", 0) + by_tool.get("Write", 0) + by_tool.get("Edit", 0),
        "findings": len(result.get("findings") or []),
    }


def main(argv) -> int:
    run = argv[1]
    attempts = sorted(Path(p) for p in glob.glob(str(APE / run / "tasks/*/samples/0/attempts/*"))
                      if list(Path(p).glob("claude_code_conversation_*.jsonl")))
    sessions_by_attempt = [session(a) for a in attempts]
    sessions = sorted(sessions_by_attempt, key=lambda s: -s["processed_tokens"])
    print(f"| PR | turns | processed tokens | final context | prompt chars | tool calls | repeats | re-reads | errors | refusals | bookkeeping | findings |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in sessions:
        print(f"| {s['pr']} | {s['turns']} | {s['processed_tokens']:,} | {s['final_context']:,} | {s['first_prompt_chars']:,} | "
              f"{s['tool_calls']} | {s['identical_repeats']} | {s['rereads']} | {s['errors']} | {s['refusals'] or ''} | "
              f"{s['bookkeeping']} | {s['findings']} |")
    total = collections.Counter()
    for s in sessions:
        total.update(s["by_tool"])
    print("\ncalls by tool, whole run:", dict(total.most_common()))
    print("sum: turns", sum(s["turns"] for s in sessions), "| processed", f"{sum(s['processed_tokens'] for s in sessions):,}",
          "| repeats", sum(s["identical_repeats"] for s in sessions), "| re-reads", sum(s["rereads"] for s in sessions),
          "| errors", sum(s["errors"] for s in sessions), "| bookkeeping", sum(s["bookkeeping"] for s in sessions))
    for s in sessions:
        for tool, text in s["error_samples"]:
            print(f"  error {s['pr']} {tool}: {text}")
    print("\n| PR | turns | prompt tokens (turn 1) | prompt share of processed | ledger chars | first ledger turn | edits submitted | of them compiled already in-session |")
    print("|---|---|---|---|---|---|---|---|")
    totals = collections.Counter()
    for attempt, s in zip(attempts, sessions_by_attempt):
        c = costs(attempt)
        totals.update(processed=c["processed"], prompt_reread=c["prompt_tokens"] * c["turns"],
                      ledger_carried=c["ledger_carried_tokens_est"], edits=c["submitted_edits"],
                      already=c["already_compiled"])
        print(f"| {s['pr']} | {c['turns']} | {c['prompt_tokens']:,} | {c['prompt_share']} | {c['ledger_chars']:,} | "
              f"{c['first_ledger_turn']} | {c['submitted_edits']} | {c['already_compiled']} |")
    if totals["processed"]:
        print(f"\nprompt re-read: {totals['prompt_reread']:,} of {totals['processed']:,} processed tokens "
              f"({totals['prompt_reread'] / totals['processed']:.0%}); ledger carried after recording: "
              f"~{totals['ledger_carried']:,} ({totals['ledger_carried'] / totals['processed']:.1%}); "
              f"submitted edits already compiled in-session: {totals['already']} of {totals['edits']}")
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(sessions, indent=1))
    return 0


def costs(attempt: Path) -> dict:
    """Three measured costs: the prompt re-read every turn, the ledger text carried after it is
    recorded, and submission compiles of edits the reviewer had already compiled."""

    conv = sorted(attempt.glob("claude_code_conversation_*.jsonl"))[-1]
    rows = [json.loads(line) for line in open(conv, encoding="utf-8") if line.strip()]
    turns, seen = [], set()
    calls = []  # (turn index, name, input)
    results = {}
    for row in rows:
        message = row.get("message") or {}
        if row.get("type") == "assistant":
            mid = message.get("id")
            if mid and mid not in seen and message.get("usage"):
                seen.add(mid)
                turns.append(message["usage"])
            for block in message.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    calls.append((len(turns) - 1, block["name"].replace("mcp__core__", ""), block.get("input") or {}, block["id"]))
        elif row.get("type") == "user":
            for block in message.get("content") if isinstance(message.get("content"), list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    results[block["tool_use_id"]] = text_of(block.get("content"))
    context = [u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0) for u in turns]
    processed = sum(context) + sum(u.get("output_tokens", 0) for u in turns)
    prompt_tokens = context[0] if context else 0
    prompt_share = prompt_tokens * len(turns) / processed if processed else 0
    ledger_chars = sum(len(json.dumps(inp)) for _, name, inp, _ in calls if name in ("record_ledger",))
    ledger_chars += sum(len(json.dumps(inp.get("ledger") or [])) for _, name, inp, _ in calls if name == "submit_findings")
    first_ledger_turn = min((t for t, name, _, _ in calls if name == "record_ledger"), default=None)
    carried = (ledger_chars / 3.5) * (len(turns) - first_ledger_turn) if first_ledger_turn is not None else 0
    compiled_ok = set()
    for _, name, inp, cid in calls:
        if name == "lean_verify_edit" and (inp.get("new_declaration") or inp.get("replacement")):
            text = results.get(cid, "")
            if '"success":true' in text.replace(" ", "") or "compiles with" in text:
                compiled_ok.add((inp.get("path"), inp.get("declaration_name"), (inp.get("new_declaration") or inp.get("replacement") or "").strip()))
    submitted_edits, recompiled = 0, 0
    for _, name, inp, _ in calls:
        if name != "submit_findings":
            continue
        for finding in inp.get("findings") or []:
            edit = finding.get("edit")
            if not edit:
                continue
            submitted_edits += 1
            key = (finding.get("path"), edit.get("declaration_name"), (edit.get("new_declaration") or edit.get("replacement") or "").strip())
            recompiled += key in compiled_ok
    last_call = calls[-1][1] if calls else None
    last_text = results.get(calls[-1][3], "")[:60] if calls else ""
    return {"turns": len(turns), "processed": processed, "prompt_tokens": prompt_tokens,
            "prompt_share": round(prompt_share, 3), "ledger_chars": ledger_chars,
            "first_ledger_turn": first_ledger_turn, "ledger_carried_tokens_est": int(carried),
            "submitted_edits": submitted_edits, "already_compiled": recompiled,
            "last_call": last_call, "last_result": last_text,
            "submit_calls": sum(1 for _, n, _, _ in calls if n == "submit_findings")}


if __name__ == "__main__":
    sys.exit(main(sys.argv))
