"""Where the reviewer-model gap lives in the process: Claude (X) against gpt_5.2 (G off, Gr1 high).

Every number in this directory's README that is not a reader's judgement comes from here. It reads
the three sets' committed matchings (`match_reasoning/`, `unblinded_reasoning.json`), the test (e)
matching (`unblinded_models.json`), the gpt runs under `.ape/runs/` (`gpt_sessions.json`), the
Claude sessions' `calls.jsonl`, and, when present, Claude's subagent transcripts, which live outside
the repository (`CLAUDE_TRANSCRIPTS`; that table is skipped when they are absent).

Usage, from the repo root: python results/pr_review_v5/probes/transcript-inspection-2026-09-30/process_profile.py
"""
import collections
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PROBES = os.path.dirname(HERE)
SETS = {  # name: (matching dir, Claude session dir, Gr1 run, G runs)
    "post": ("gpt52-postcutoff-2026-09-29", "postcutoff-2026-09-29", "probe_postcutoff_gpt52_Gr_rep1",
             ["probe_postcutoff_gpt52_G_rep1", "probe_postcutoff_gpt52_G_rep2"]),
    "val": ("model-gap-val-small12", "model-gap-val-small12", "probe_val_small12_gpt52_Gr_rep1",
            ["probe_val_small12_gpt52_G_rep1", "probe_val_small12_gpt52_G_rep2"]),
    "dev": ("model-gap-dev-medium-0.3.0", "model-gap-dev-medium-0.3.0", "probe_dev_gpt52_Gr_rep1",
            ["probe_dev_gpt52_G_rep1", "probe_dev_gpt52_G_rep2"]),
}
MODEL_RUNS = ["probe_postcutoff_gpt55_G_rep1", "probe_postcutoff_gpt55_G_rep2", "probe_postcutoff_gpt54_G_rep1",
              "probe_postcutoff_gpt54_G_rep2"]
CLAUDE_TRANSCRIPTS = os.path.expanduser(
    "~/.claude/projects/-research-projects-proofedit-ya475-APE-Bench/029323d7-a6e4-45de-bea4-7052b7e4f379/subagents")


def turn_no(path):
    return int(re.search(r"__turn_(\d+)__", path).group(1))


def load(path):
    return json.load(open(os.path.join(PROBES, path)))


# 1. Volume against hits per finding, per session, from the reasoning seal of each set.
def volume():
    print("## 1. Findings filed against asks reached (matcher 1; matcher 2 in brackets)\n")
    print("| set | session | findings/PR | asks reached | reach | ask hits per finding | capped PRs |")
    print("|---|---|---|---|---|---|---|")
    for name, (mdir, *_ ) in SETS.items():
        stats = load(f"{mdir}/match_reasoning/session_stats.json")
        ub = load(f"{mdir}/unblinded_reasoning.json")
        ub = ub.get("all", ub)
        per = collections.defaultdict(collections.Counter)
        for pr, sessions in stats.items():
            for s, v in sessions.items():
                per[s]["prs"] += 1
                per[s]["findings"] += v.get("findings") or 0
                per[s]["capped"] += bool(v.get("capped"))
        for m in ("1", "2"):
            for ask, row in ub[m]["table"].items():
                for s, verdict in row.items():
                    per[s][f"reached{m}"] += verdict == "reached"
                    per[s][f"asks{m}"] += 1
        for s in sorted(per):
            c = per[s]
            print(f"| {name} | {s} | {c['findings'] / c['prs']:.2f} | {c['reached1']} ({c['reached2']}) | "
                  f"{c['reached1'] / c['asks1']:.2f} | {c['reached1'] / max(c['findings'], 1):.2f} | {c['capped']} |")
    ub = load("gpt52-postcutoff-2026-09-29/unblinded_models.json")
    stats = load("gpt52-postcutoff-2026-09-29/match_models/session_stats.json")
    found = collections.Counter()
    for pr, sessions in stats.items():
        for s, v in sessions.items():
            found[s] += v.get("findings") or 0
    print("\nTest (e)'s seal, post-cutoff, matcher 1 (matcher 2 agrees on every cell):\n")
    print("| session | findings | asks reached | ask hits per finding | union with its twin |")
    print("|---|---|---|---|---|")
    table = ub["1"]["table"]
    reached = {s: {a for a, row in table.items() if row[s] == "reached"} for s in found}
    twins = {"X1": "X2", "X2": "X1", "Gb1": "Gb2", "Gb2": "Gb1", "Ga1": "Ga2", "Ga2": "Ga1"}
    for s in sorted(found):
        union = len(reached[s] | reached.get(twins.get(s), set())) if s in twins else "-"
        print(f"| {s} | {found[s]} | {len(reached[s])} | {len(reached[s]) / max(found[s], 1):.2f} | {union} |")


def gpt_sessions(run):
    for att in glob.glob(os.path.join(".ape/runs", run, "tasks/*/samples/0/attempts/*")):
        raws = sorted(glob.glob(att + "/conversations/*_raw.jsonl"), key=turn_no)
        convs = [p for p in glob.glob(att + "/conversations/*.jsonl") if not p.endswith("_raw.jsonl")]
        if raws and convs:
            yield att, raws, max(convs, key=turn_no)


# 2. The shape of a session: turns, text, calls a turn, reasoning.
def shape():
    print("\n## 2. Session shape (mean per session)\n")
    print("| run | sessions | turns | turns with any text | calls | calls/turn | reasoning tokens | submitted |")
    print("|---|---|---|---|---|---|---|---|")
    runs = [r for _, (_, _, gr, gs) in SETS.items() for r in gs + [gr]] + MODEL_RUNS
    for run in runs:
        rows = []
        for _, raws, _ in gpt_sessions(run):
            turns = text = calls = reasoning = 0
            submitted = False
            for p in raws:
                d = json.loads(open(p).readline())
                msg = d["choices"][0]["message"]
                turns += 1
                text += bool(msg.get("content"))
                calls += len(msg.get("tool_calls") or [])
                reasoning += ((d.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
                submitted |= any(tc["function"]["name"].endswith("submit_findings") for tc in msg.get("tool_calls") or [])
            rows.append((turns, text, calls, reasoning, submitted))
        n = len(rows)
        mean = lambda i: sum(r[i] for r in rows) / n
        print(f"| {run} | {n} | {mean(0):.1f} | {mean(1):.1f} | {mean(2):.1f} | {mean(2) / mean(0):.1f} | "
              f"{mean(3):,.0f} | {sum(r[4] for r in rows)}/{n} |")
    if not os.path.isdir(CLAUDE_TRANSCRIPTS):
        print("\n(Claude transcripts absent; its shape is skipped.)")
        return
    sessions = json.load(open(os.path.join(HERE, "claude_sessions.json")))
    per = collections.defaultdict(list)
    for key, fname in sessions.items():
        msgs = collections.OrderedDict()
        for line in open(os.path.join(CLAUDE_TRANSCRIPTS, fname)):
            r = json.loads(line)
            if r.get("type") != "assistant":
                continue
            m = msgs.setdefault(r["message"].get("id"), collections.Counter())
            for b in r["message"]["content"]:
                m[b["type"]] += 1
                if b["type"] == "text":
                    m["chars"] += len(b["text"])
        per[key.split("|")[0]].append(list(msgs.values()))
    print("\n| Claude set | sessions | API messages | calls | calls/message | messages with thinking | text characters |")
    print("|---|---|---|---|---|---|---|")
    for s, sessions_ in per.items():
        n = len(sessions_)
        msgs = sum(len(x) for x in sessions_) / n
        calls = sum(m["tool_use"] for x in sessions_ for m in x) / n
        think = sum(sum(1 for m in x if m["thinking"]) / len(x) for x in sessions_) / n
        chars = sum(m["chars"] for x in sessions_ for m in x) / n
        print(f"| {s} | {n} | {msgs:.1f} | {calls:.1f} | {calls / msgs:.2f} | {think:.2f} | {chars:.0f} |")


# 3. Construction breadth: edits compiled, and distinct targets edited, per session.
def edits():
    print("\n## 3. Construction breadth (lean_verify_edit calls that change code, per session)\n")
    print("| set | Gr1 edits | Gr1 distinct targets | Claude edits | Claude distinct targets |")
    print("|---|---|---|---|---|")
    gpt = json.load(open(os.path.join(HERE, "gpt_sessions.json")))
    is_edit = lambda a: bool(a.get("new_declaration") or a.get("replacement"))
    target = lambda a: str(a.get("declaration_name") or (a.get("path"), a.get("line_start")))
    for name, (_, cdir, gr, _) in SETS.items():
        g, x = [], []
        for pr, v in gpt[gr].items():
            recs = [json.loads(line) for line in open(v["last_turn_file"])]
            e = [it["input"] for r in recs if r["type"] == "assistant" for it in r["message"]["content"]
                 if it.get("type") == "tool_use" and it["name"].endswith("lean_verify_edit") and is_edit(it["input"])]
            g.append((len(e), len({target(a) for a in e})))
            for s in ("X1", "X2"):
                path = os.path.join(PROBES, cdir, f"pr{pr}", s, "calls.jsonl")
                if not os.path.exists(path):
                    continue
                calls = [json.loads(line) for line in open(path)]
                e = [c["arguments"] for c in calls if c["tool"] == "lean_verify_edit" and is_edit(c.get("arguments") or {})]
                x.append((len(e), len({target(a) for a in e})))
        mean = lambda rows, i: sum(r[i] for r in rows) / len(rows)
        print(f"| {name} | {mean(g, 0):.1f} | {mean(g, 1):.1f} | {mean(x, 0):.1f} | {mean(x, 1):.1f} |")


# 4. The asks Claude reached and Gr1 missed, split by whether Gr1's session on that PR was capped.
def gap():
    print("\n## 4. Asks reached by Claude (>= 2 of 4 cells) and by Gr1 in neither cell\n")
    print("| set | on PRs where Gr1 submitted | on PRs where Gr1 was capped | asks |")
    print("|---|---|---|---|")
    for name, (mdir, *_ ) in SETS.items():
        ub = load(f"{mdir}/unblinded_reasoning.json")
        ub = ub.get("all", ub)
        stats = load(f"{mdir}/match_reasoning/session_stats.json")
        pr_of = {a["ask_id"]: a["pr"] for a in load(f"{mdir}/match_reasoning/matches.1.json")["asks"]}
        t1, t2 = ub["1"]["table"], ub["2"]["table"]
        split = collections.defaultdict(list)
        for a in t1:
            x = sum(t[a][s] == "reached" for t in (t1, t2) for s in ("X1", "X2"))
            g = sum(t[a]["Gr1"] == "reached" for t in (t1, t2))
            if x >= 2 and g == 0:
                capped = bool(stats[str(pr_of[a])].get("Gr1", {}).get("capped"))
                split["capped" if capped else "submitted"].append(a)
        print(f"| {name} | {len(split['submitted'])} | {len(split['capped'])} | "
              f"{', '.join(split['submitted'] + split['capped'])} |")


if __name__ == "__main__":
    volume()
    shape()
    edits()
    gap()
