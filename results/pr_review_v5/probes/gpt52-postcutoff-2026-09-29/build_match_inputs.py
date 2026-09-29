"""Blind matcher inputs for test (b): per PR, the gpt_5.2 solo sessions (G1, G2, K1, K2, read from
each run's task results through TaskStorage) and Claude's post-cutoff sessions (X1, X2), relabelled
by blinding_SEALED.json and stripped to target / claim / requested_change / severity, with condition
cues redacted. The asks are the post-cutoff probe's agreed asks on these PRs.

Usage (repo root, PYTHONPATH=$PWD:$PWD/src): python build_match_inputs.py <probe_feedback.json> <out_dir>
Also writes session_stats.json: findings and lean_verify_edit calls per session.
"""
import asyncio, json, re, sys
from pathlib import Path

from ape.orchestration.persistence import TaskStorage

G = Path(__file__).parent
POST = Path("results/pr_review_v5/probes/postcutoff-2026-09-29")
RUNS = {"G1": "probe_postcutoff_gpt52_G_rep1", "G2": "probe_postcutoff_gpt52_G_rep2",
        "K1": "probe_postcutoff_gpt52_K_rep1", "K2": "probe_postcutoff_gpt52_K_rep2"}
KEEP = ("target", "claim", "requested_change", "severity")
_REDACT = [(re.compile(r"\bpass \d(?:'s)?\s+"), ""), (re.compile(r"\bc\d{1,3}\b"), "a compiled check")]


def redact(text):
    if not isinstance(text, str):
        return text
    for pattern, repl in _REDACT:
        text = pattern.sub(repl, text)
    return text


def compile_calls(attempt: Path) -> int:
    """lean_verify_edit calls in the attempt's last (cumulative) conversation file."""
    files = sorted((attempt / "conversations").glob("*.json")) if (attempt / "conversations").is_dir() else []
    if not files:
        return -1
    text = files[-1].read_text(encoding="utf-8")
    return len(re.findall(r'"name":\s*"[^"]*lean_verify_edit"', text))


async def solo_sessions(run: str):
    """{pr_number: (findings as the matcher sees them, stats)} for one solo run."""
    out = {}
    tasks = Path(".ape/runs") / run / "tasks"
    for task_dir in sorted(p for p in tasks.iterdir() if p.is_dir()):
        samples = await TaskStorage(task_dir, task_dir.name).load_all_samples()
        for _i, sample in sorted(samples.items()):
            attempt = sample.successful_attempt
            if attempt is None:
                continue
            result = json.loads((Path(attempt.path) / "task_result.json").read_text(encoding="utf-8"))
            pr = int(result["pr_number"])
            found = [{"target": f"{f.get('path')}:{f.get('line_start')}", "claim": f.get("claim"),
                      "requested_change": f.get("suggested_fix"), "severity": f.get("severity")}
                     for f in result.get("findings") or []]
            out[pr] = (found, {"findings": len(found), "compiles": compile_calls(Path(attempt.path))})
            break
    return out


def main():
    feedback, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    seal = json.load(open(G / "blinding_SEALED.json"))
    manifest = json.load(open(POST / "match/ask_manifest.json"))
    rows = {r["cid"]: r for r in json.load(open(feedback))["rows"]}
    solo = {session: asyncio.run(solo_sessions(run)) for session, run in RUNS.items()}
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
            json.dump(stripped, open(out / f"{label}_pr{pr}.json", "w"), indent=1, ensure_ascii=False)
    json.dump(stats, open(out / "session_stats.json", "w"), indent=1)
    print("inputs for", len(seal), "PRs; stats:", json.dumps(stats))


if __name__ == "__main__":
    main()
