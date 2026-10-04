"""Per-session process profile: gpt_5.2 solo sessions (G, K) against Claude's post-cutoff sessions (X).

gpt sessions are read through `analysis.trajectory.extract`; Claude sessions through the probe
wrapper's `calls.jsonl` (every review-tool call, with a compile's outcome) and `findings.json`.
Usage (repo root, PYTHONPATH=$PWD:$PWD/src): python inspect_sessions.py
                                   or: python inspect_sessions.py <pr> <session> ...
"""
import collections, json, re
from pathlib import Path

from src.mathlib_review.analysis.trajectory import extract

PRS = [41930, 42184, 42814, 43024, 43167, 43192]
POST = Path("results/pr_review_v5/probes/postcutoff-2026-09-29")
from build_match_inputs import CALIBRATION, RUNS  # the solo runs, one table for both scripts

#: the six-PR solo sessions whose runs exist, then Claude's; a condition is a label without its digit
GPT = [s for s in RUNS if (Path(".ape/runs") / RUNS[s]).exists() and s not in CALIBRATION]
SESSIONS = GPT + ["X1", "X2"]


def condition(session):
    return session.rstrip("0123456789")
REVIEW_TOOLS = {"file_read", "content_search", "file_search", "declaration_search", "naming_norm",
                "precedent_search", "zulip_search", "proof_profile", "lean_verify", "lean_verify_edit",
                "get_lean_goal", "code_hover", "code_goto"}


def short(name):
    return name.split("__")[-1]


def gpt_profiles(run):
    x = extract(run)
    by_pr = {}
    for inv in x["invocations"]:
        row = inv if isinstance(inv, dict) else inv.__dict__
        pr = int(row["pr_number"])
        turns = [t if isinstance(t, dict) else t.__dict__ for t in x["turns_by_pr"].get(str(pr), [])
                 if (t if isinstance(t, dict) else t.__dict__)["conversation_id"] == row["invocation_id"]]
        calls, errors, compiles, files, tool_misuse = collections.Counter(), 0, [], set(), {}
        pending = {}
        for t in turns:
            items = t["items"] if isinstance(t["items"], list) else []
            for it in items:
                if it.get("t") in ("use", "tool_use"):
                    name = short(it.get("name", ""))
                    calls[name] += 1
                    args = it.get("v") or it.get("input") or {}
                    if isinstance(args, str):
                        try: args = json.loads(args)
                        except ValueError: args = {}
                    if name == "file_read" and isinstance(args, dict):
                        files.add(args.get("file_path"))
                    pending[it.get("id")] = name
                elif it.get("t") in ("res", "tool_result"):
                    name = pending.get(it.get("id"), it.get("name", "?"))
                    text = str(it.get("v", ""))
                    if re.search(r'"success":\s*false|"error":\s*"', text[:300]) and name not in ("lean_verify", "lean_verify_edit"):
                        errors += 1
                    if name in ("lean_verify", "lean_verify_edit") and re.search(r'"error":\s*"', text[:300]):
                        tool_misuse[name] = tool_misuse.get(name, 0) + 1
                    if name in ("lean_verify", "lean_verify_edit"):
                        ok = bool(re.search(r'"success":\s*true|"compiles":\s*true', text))
                        compiles.append(ok)
        by_pr[pr] = {"turns": row["turns"], "calls": dict(calls),
                     "review_calls": sum(v for k, v in calls.items() if k in REVIEW_TOOLS),
                     "compiles": len(compiles), "compiles_ok": sum(compiles), "tool_errors_seen": errors,
                     "files_read": len(files - {None}), "cost": row.get("cost"), "compile_tool_errors": tool_misuse,
                     "seconds": row.get("execution_time")}
    return by_pr


def claude_profile(pr, session):
    d = POST / f"pr{pr}" / session
    calls = [json.loads(l) for l in open(d / "calls.jsonl")]
    by = collections.Counter(c["tool"] for c in calls)
    comp = [c for c in calls if c["tool"] == "lean_verify_edit"]
    ok = sum(1 for c in comp if (c.get("result") or {}).get("success") or (c.get("result") or {}).get("compiles"))
    files = {(c.get("arguments") or {}).get("file_path") for c in calls
             if c["tool"] == "file_read" and isinstance(c.get("arguments"), dict)}
    errs = sum(1 for c in calls if c.get("exit") != 0)
    return {"calls": dict(by), "review_calls": sum(v for k, v in by.items() if k in REVIEW_TOOLS),
            "compiles": len(comp), "compiles_ok": ok, "tool_errors_seen": errs,
            "files_read": len(files - {None}),
            "findings": len(json.load(open(d / "findings.json")))}


# --- Where the calls point, and what the compiles are -------------------------------------
# A lookup is PR-side when it reads or searches a changed file, or looks up an identifier the diff
# adds; library-side otherwise (the comparison objects the maintainers cite live there). A compile
# is `usage` when it writes an `example` or `#check`, `own` when at least 90% of its non-blank lines
# are lines of the PR's post-image files (a re-verification), and `variant` otherwise (an
# alternative the reviewer wrote). The post-image is the base file with the episode's diff applied.
RELEASE = Path("inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl")
MATHLIB = Path("data/code_execute/repos/mathlib4/source")
SEARCH = {"file_read", "content_search", "file_search", "declaration_search", "naming_norm",
          "precedent_search", "zulip_search"}
COMPILE = {"lean_verify", "lean_verify_edit"}


def post_images():
    """Per PR: changed files, the post-image's stripped lines, and the identifiers the diff adds.

    The line set is the base files' lines minus the diff's removed lines, plus its added and context
    lines. That is a membership test, not a reconstruction (the diffs do not all apply to `base_sha`
    as stored), and it keeps a restored pre-PR line out of `own`.
    """
    import subprocess
    out = {}
    for line in open(RELEASE):
        e = json.loads(line)
        if e["pr_number"] not in PRS:
            continue
        base = set()
        for f in e["changed_files"]:
            got = subprocess.run(["git", "-C", str(MATHLIB), "show", f"{e['base_sha']}:{f}"],
                                 capture_output=True, text=True)
            base |= {l.strip() for l in got.stdout.splitlines() if l.strip()}
        hunks = [l for l in e["diff"].splitlines() if not l.startswith(("+++", "---", "diff ", "@@", "index "))]
        removed = {l[1:].strip() for l in hunks if l.startswith("-")}
        kept = {l[1:].strip() for l in hunks if l.startswith(("+", " "))}
        added = {m.group(1) for m in re.finditer(r"^\+.*?\b(?:theorem|lemma|def|abbrev|structure|class|instance)\s+([\w.']+)",
                                                  e["diff"], re.M)}
        out[e["pr_number"]] = {"files": set(e["changed_files"]), "lines": ((base - removed) | kept) - {""},
                               "added": added | {a.split(".")[-1] for a in added}}
    return out


def lookup_side(tool, args, pr):
    """`pr`: reads or searches a changed file, or looks up a name the diff adds. `own_names`: a
    library-wide search for a name the diff adds (where the PR's objects are used). `library`: a
    lookup of anything else, which is where a comparison object lives."""
    target = str(args.get("file_path") or args.get("path") or "")
    target = target.removeprefix("target/")
    if tool in ("file_read", "file_search"):
        return "pr" if target in pr["files"] else "library"
    if tool == "declaration_search":
        return "pr" if str(args.get("identifier", "")).split(".")[-1] in pr["added"] else "library"
    if tool == "content_search":
        if target in pr["files"]:
            return "pr"
        pattern = str(args.get("content_pattern", ""))
        return "own_names" if any(n in pattern for n in pr["added"] if len(n) > 3) else "library"
    return "library"


def compile_kind(tool, args, pr):
    code = str(args.get("new_declaration") or args.get("replacement") or args.get("content") or args.get("code") or "")
    if re.search(r"^\s*(example\b|#check|#eval)", code, re.M) or (tool == "lean_verify" and "Mathlib/" not in str(args.get("path", ""))):
        return "usage"
    lines = [l.strip() for l in code.splitlines() if l.strip()]
    if lines and sum(l in pr["lines"] for l in lines) >= 0.9 * len(lines):
        return "own"
    return "variant"


def session_calls(session, pr):
    """(tool, args) for every review-tool call of one session on one PR."""
    if session.startswith("X"):
        return [(c["tool"], c.get("arguments") or {}) for c in
                (json.loads(l) for l in open(POST / f"pr{pr}" / session / "calls.jsonl"))]
    x = _EXTRACTS.setdefault(session, extract(RUNS[session]))
    out = []
    for t in x["turns_by_pr"].get(str(pr), []):
        t = t if isinstance(t, dict) else t.__dict__
        for it in t["items"] if isinstance(t["items"], list) else []:
            if it.get("t") == "use":
                args = it.get("v")
                if isinstance(args, str):
                    try: args = json.loads(args)
                    except ValueError: args = {}
                out.append((short(it.get("name", "")), args if isinstance(args, dict) else {}))
    return out


_EXTRACTS = {}


def lookups_and_compiles():
    posts = post_images()
    agg = collections.defaultdict(collections.Counter)
    for pr in PRS:
        for s in SESSIONS:
            c = agg[condition(s)]
            c["sessions"] += 1
            for tool, args in session_calls(s, pr):
                if tool in SEARCH:
                    c["lookup_" + lookup_side(tool, args, posts[pr])] += 1
                if tool in COMPILE:
                    c["compile_" + compile_kind(tool, args, posts[pr])] += 1
    print("\nper session, mean: lookups (PR-side / own names library-wide / library) and compiles (own / usage / variant)")
    for k in dict.fromkeys(map(condition, SESSIONS)):
        c, n = agg[k], agg[k]["sessions"]
        print(f"  {k}: lookups {c['lookup_pr']/n:.1f} / {c['lookup_own_names']/n:.1f} / {c['lookup_library']/n:.1f}   "
              f"compiles {c['compile_own']/n:.1f} / {c['compile_usage']/n:.1f} / {c['compile_variant']/n:.1f}")



def main():
    gpt = {s: gpt_profiles(RUNS[s]) for s in GPT}
    rows = []
    for pr in PRS:
        for s in GPT:
            p = gpt[s].get(pr, {})
            rows.append((pr, s, p.get("turns"), p.get("review_calls"), p.get("compiles"), p.get("compiles_ok"),
                         p.get("files_read"), p.get("tool_errors_seen"), round(p.get("seconds") or 0),
                         {**p.get("calls", {}), "compile_tool_errors": p.get("compile_tool_errors")}))
        for s in ("X1", "X2"):
            p = claude_profile(pr, s)
            rows.append((pr, s, None, p["review_calls"], p["compiles"], p["compiles_ok"], p["files_read"],
                         p["tool_errors_seen"], None, p["calls"]))
    print("pr     sess turns review_calls compiles ok files errs secs  calls")
    for r in rows:
        print(f"{r[0]} {r[1]:>4} {str(r[2]):>5} {str(r[3]):>12} {str(r[4]):>8} {str(r[5]):>2} {str(r[6]):>5} {str(r[7]):>4} {str(r[8]):>5}  {r[9]}")
    agg = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        c = condition(r[1])
        agg[c]["sessions"] += 1
        for i, k in ((3, "review_calls"), (4, "compiles"), (5, "compiles_ok"), (6, "files_read")):
            agg[c][k] += r[i] or 0
    print("\nper session, mean:")
    for c, a in sorted(agg.items()):
        n = a["sessions"]
        print(f"  {c}: review calls {a['review_calls']/n:.1f}, compiles {a['compiles']/n:.1f} "
              f"({a['compiles_ok']} of {a['compiles']} ok), files read {a['files_read']/n:.1f}")
    lookups_and_compiles()


def one_pr(pr, sessions):
    """Per session on one PR: review calls, lookups by side, compiles by kind."""
    post = post_images()[pr]
    print(f"PR {pr}: session  calls  lookups PR / own names / library  compiles own / usage / variant")
    for s in sessions:
        c = collections.Counter()
        for tool, args in session_calls(s, pr):
            c["calls"] += tool in REVIEW_TOOLS
            if tool in SEARCH:
                c["lookup_" + lookup_side(tool, args, post)] += 1
            if tool in COMPILE:
                c["compile_" + compile_kind(tool, args, post)] += 1
        print(f"  {s:>4}  {c['calls']:5}  {c['lookup_pr']:3} / {c['lookup_own_names']:3} / {c['lookup_library']:3}"
              f"   {c['compile_own']:3} / {c['compile_usage']:3} / {c['compile_variant']:3}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:  # inspect_sessions.py <pr> <session> ...: one PR, the named sessions
        one_pr(int(sys.argv[1]), sys.argv[2:])
    else:
        main()
