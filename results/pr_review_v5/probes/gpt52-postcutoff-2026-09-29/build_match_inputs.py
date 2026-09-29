"""Blind matcher inputs for test (b): per PR, the gpt_5.2 solo sessions (G1, G2, K1, K2, read from
each run's task results through TaskStorage) and Claude's post-cutoff sessions (X1, X2), relabelled
by blinding_SEALED.json and stripped to target / claim / requested_change / severity, with condition
cues redacted. The asks are the post-cutoff probe's agreed asks on these PRs.

The arms condition adds the two lead runs (L1, L2), read from each run's `findings.jsonl`, all
channels, under its own seal (`blinding_arms_SEALED.json`). A lead finding's target is its primary
change's reviewed span, from the release's change graph.

A solo finding's location is under `anchor` (path, line_start). Until 2026-09-29 this read the top
level, so all 73 of test (b)'s gpt_5.2 findings reached the matchers as `None:None` while Claude's
carried a file and declaration; test (b) was re-matched on the corrected inputs. A finding with no
target is now refused.

Usage (repo root, PYTHONPATH=$PWD:$PWD/src):
    python build_match_inputs.py <probe_feedback.json> <out_dir> [<seal file name>]
Also writes session_stats.json: findings and compiles per session, and for L which findings the gate
published (by index, for the published-only reading; the matchers never see it).
"""
import asyncio, json, re, sys
from pathlib import Path

from ape.orchestration.persistence import TaskStorage

G = Path(__file__).parent
POST = Path("results/pr_review_v5/probes/postcutoff-2026-09-29")
RUNS = {"G1": "probe_postcutoff_gpt52_G_rep1", "G2": "probe_postcutoff_gpt52_G_rep2",
        "K1": "probe_postcutoff_gpt52_K_rep1", "K2": "probe_postcutoff_gpt52_K_rep2"}
LEAD_RUNS = {"L1": "probe_postcutoff_lead_rep1", "L2": "probe_postcutoff_lead_rep2"}
RELEASE = Path("inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl")
GRAPHS = Path("inputs/probes/probe-2026-07-08-v1/derived/change_graphs.jsonl")
KEEP = ("target", "claim", "requested_change", "severity")
_REDACT = [(re.compile(r"\bpass \d(?:'s)?\s+"), ""), (re.compile(r"\bc\d{1,3}\b"), "a compiled check")]


def redact(text):
    if not isinstance(text, str):
        return text
    for pattern, repl in _REDACT:
        text = pattern.sub(repl, text)
    return text


def compile_calls(run: str) -> dict:
    """{pr_number: compile calls} for a run, from the project's trajectory reader. The solo grant
    holds `lean_verify` (compile given Lean text) beside `lean_verify_edit`; Claude's harness held
    only the latter, so both count as a compile here, and the split is reported separately."""
    from src.mathlib_review.analysis.trajectory import extract

    calls = {}
    for inv in extract(run)["invocations"]:
        row = inv if isinstance(inv, dict) else inv.__dict__
        counts = row.get("tool_calls") or {}
        calls[int(row["pr_number"])] = {
            "lean_verify_edit": sum(v for k, v in counts.items() if k.endswith("lean_verify_edit")),
            "lean_verify": sum(v for k, v in counts.items() if k.endswith("lean_verify"))}
    return calls


async def solo_sessions(run: str):
    """{pr_number: (findings as the matcher sees them, stats)} for one solo run."""
    out = {}
    compiles = compile_calls(run)
    tasks = Path(".ape/runs") / run / "tasks"
    for task_dir in sorted(p for p in tasks.iterdir() if p.is_dir()):
        storage = TaskStorage(task_dir, task_dir.name)
        samples = await storage.load_all_samples()
        result = await storage.load_task_result()
        for _i, sample in sorted(samples.items()):
            attempt = sample.successful_attempt
            if attempt is None or not result or not result.get("success"):
                continue
            pr = int(result["pr_number"])
            found = [{"target": f"{(f.get('anchor') or {}).get('path')}:{(f.get('anchor') or {}).get('line_start')}",
                      "claim": f.get("claim"),
                      "requested_change": f.get("suggested_fix"), "severity": f.get("severity")}
                     for f in result.get("findings") or []]
            split = compiles.get(pr, {"lean_verify_edit": -1, "lean_verify": -1})
            out[pr] = (found, {"findings": len(found), "compiles": split["lean_verify_edit"] + split["lean_verify"],
                               "compile_split": split})
            break
    return out


def change_locations(pr: int) -> dict:
    """{change_id: "path:line"} from the release's change graph: the reviewed span of the change's
    first changed range, which is where the pipeline anchors a finding."""
    for line in open(GRAPHS):
        g = json.loads(line)
        if g["pr_number"] != pr:
            continue
        ranges = {r["range_id"]: r for r in g["changed_ranges"]}
        out = {}
        for t in g["targets"]:
            r = ranges[t["changed_range_ids"][0]]
            out[t["change_id"]] = f"{r['path']}:{(r.get('reviewed_span') or {}).get('line_start')}"
        return out
    return {}


def lead_sessions(run: str) -> dict:
    """{pr_number: (findings as the matcher sees them, stats)} for one lead run, all channels."""
    prs = {json.loads(l)["pr_number"] for l in open(RELEASE)}
    by_pr = {}
    for l in open(Path("results/pr_review_v5/runs") / run / "findings.jsonl"):
        by_pr.setdefault(json.loads(l)["pr_number"], []).append(json.loads(l))
    out = {}
    for pr in prs:
        where = change_locations(pr)
        found, published = [], []
        for n, f in enumerate(by_pr.get(pr, [])):
            found.append({"target": where[f["primary_change_id"]], "claim": f.get("claim"),
                          "requested_change": f.get("requested_change"), "severity": f.get("severity")})
            if f.get("admission") == "published":
                published.append(n)
        out[pr] = (found, {"findings": len(found), "published": published})
    return out


def main():
    feedback, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    seal = json.load(open(G / (sys.argv[3] if len(sys.argv) > 3 else "blinding_SEALED.json")))
    manifest = json.load(open(POST / "match/ask_manifest.json"))
    rows = {r["cid"]: r for r in json.load(open(feedback))["rows"]}
    used = {s for labels in seal.values() for s in labels.values()}
    solo = {session: asyncio.run(solo_sessions(run)) for session, run in RUNS.items() if session in used}
    solo.update({session: lead_sessions(run) for session, run in LEAD_RUNS.items() if session in used})
    stats = {}
    for pr, labels in seal.items():
        ids = manifest["asks"]["post"][pr]
        packet = []
        for cid in ids:
            r = rows[cid]
            parent = rows.get(r["reply_to_cid"]) if r.get("reply_to_cid") else None
            packet.append({"ask_id": cid, "path": r["path"], "code_at_comment": r["diff_hunk"],
                           "comment": r["body"], "replies_to": parent["body"] if parent else None})
        json.dump(packet, open(out / f"asks_pr{pr}.json", "w"), indent=1, ensure_ascii=False)
        for label, session in labels.items():
            if session.startswith("X"):
                found = json.load(open(POST / f"pr{pr}" / session / "findings.json"))
                calls = [json.loads(l) for l in open(POST / f"pr{pr}" / session / "calls.jsonl")]
                st = {"findings": len(found), "compiles": sum(c["tool"] == "lean_verify_edit" for c in calls)}
            else:
                if int(pr) not in solo[session]:
                    raise SystemExit(f"{session} has no successful session for PR {pr}")
                found, st = solo[session][int(pr)]
            stats.setdefault(pr, {})[session] = st
            stripped = [{"i": n, **{k: redact(f.get(k)) for k in KEEP}} for n, f in enumerate(found)]
            lost = [f["i"] for f in stripped if not f["target"] or str(f["target"]).startswith("None")]
            if lost:
                raise SystemExit(f"{session} on PR {pr}: findings {lost} have no target; a matcher "
                                 f"would judge them without a location")
            json.dump(stripped, open(out / f"{label}_pr{pr}.json", "w"), indent=1, ensure_ascii=False)
    json.dump(stats, open(out / "session_stats.json", "w"), indent=1)
    print("inputs for", len(seal), "PRs; stats:", json.dumps(stats))


if __name__ == "__main__":
    main()
