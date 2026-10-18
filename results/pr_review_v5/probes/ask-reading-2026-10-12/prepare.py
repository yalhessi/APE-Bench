"""Lay every ask of P14 and D12 out with its DeepSeek sessions, for the per-ask reading (2026-10-12).

For each set (D12, P14_post, P14_val) and each PR: the asks (maintainer text, family, census entries),
each session's matched outcome (both matchers, finding index and text, the matchers' notes), the
DeepSeek sessions' transcripts (DX1-3 solo, AP1-3 solo + the applicable-conventions section), and
the section each AP session was given. Everything is read from the one reviewer table's record
(`one-reviewer-table-2026-10-10`, its seals and matches), the matcher inputs kept in
`/research/projects/proofedit/ya475/table_scratch`, the probe sets' feedback, and the runs.

usage (worktree root): ape/bin/python results/pr_review_v5/probes/ask-reading-2026-10-12/prepare.py
writes: packets/<set>/<pr>.json, ap_sections/<set>_<pr>.md, asks_all.tsv, sessions.json
"""
import asyncio
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
T = ROOT / "results/pr_review_v5/probes/one-reviewer-table-2026-10-10"
C = ROOT / "results/pr_review_v5/probes/conventions-ceiling-2026-10-04"
SCRATCH = Path("/research/projects/proofedit/ya475/table_scratch")
SETS = {
    "D12": dict(seal="blinding_D12_SEALED.json", sources="sources_D12.json",
                feedback="results/pr_review_v5/probes/model-gap-dev-medium-0.3.0"),
    "P14_post": dict(seal="blinding_P14_post_SEALED.json", sources="sources_P14_post.json",
                     feedback="results/pr_review_v5/probes/postcutoff-2026-09-29"),
    "P14_val": dict(seal="blinding_P14_val_SEALED.json", sources="sources_P14_val.json",
                    feedback="results/pr_review_v5/probes/model-gap-val-small12"),
}
LABELS_READ = ("DX1", "DX2", "DX3", "AP1", "AP2", "AP3")


def jload(p):
    return json.loads(Path(p).read_text())


ASKS = {**jload(C / "briefs_exact.json")["asks"], **jload(C / "asks_dev_census.json")["asks"]}
CODEBOOK = {e["id"]: e.get("principle") for e in
            jload(ROOT / "results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json")}


_SESSIONS_BY_RUN: dict = {}


def _sessions_of(run: str) -> dict:
    """PR -> session transcript for every attempt of `run`, through the persisted samples
    (`tool_outcomes._attempt_dirs`, which reads `TaskStorage`), never the directory layout."""
    if run in _SESSIONS_BY_RUN:
        return _SESSIONS_BY_RUN[run]
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "src"))
    from src.mathlib_review.analysis.tool_outcomes import _attempt_dirs  # noqa: E402
    from src.mathlib_review.analysis.trajectory import _SESSION_GLOB  # noqa: E402
    root = ROOT / ".ape/runs" / run
    out: dict = {}
    for attempt in asyncio.run(_attempt_dirs(root / "tasks", root)):
        task_dir = next((p for p in attempt.parents if (p / "task_result.json").is_file()), None)
        if task_dir is None:
            continue
        r = jload(task_dir / "task_result.json")
        n = r.get("pr_number") or (r.get("metadata") or {}).get("pr_number")
        if n is None:
            m = re.search(r"mathlib4:(\d+):round", json.dumps(r))
            n = int(m.group(1)) if m else None
        sessions = sorted(attempt.glob(_SESSION_GLOB))
        if n is not None and sessions:
            out[int(n)] = str(sessions[-1])  # a later attempt of the same PR replaces an earlier one
    _SESSIONS_BY_RUN[run] = out
    return out


def session_file(run: str, pr: int):
    """The transcript of `run`'s session on `pr`, or None."""
    if not (ROOT / ".ape/runs" / run / "tasks").is_dir():
        return None
    return _sessions_of(run).get(int(pr))


def ap_section(transcript: str):
    """The conventions section of an AP session's first user message, as delivered (ids stripped)."""
    for line in open(transcript):
        if not line.strip():
            continue
        e = json.loads(line)
        if e.get("type") != "user":
            continue
        txt = "".join(c.get("text") or "" for c in e["message"]["content"] if c.get("type") == "text")
        k = txt.find("Under each convention are up to two comments")
        if k < 0:
            return None
        start = txt.rfind("\n## ", 0, k)
        end = txt.find("\n## The diff", k)
        return txt[start:end if end > 0 else k + 2000]
    return None


def main():
    (HERE / "packets").mkdir(exist_ok=True)
    (HERE / "ap_sections").mkdir(exist_ok=True)
    rows_all = []
    sessions_all = {}
    for set_name, cfg in SETS.items():
        seal = jload(T / cfg["seal"])  # pr -> {R: label}
        sources = jload(T / cfg["sources"])  # label -> {kind, run}
        matches = {m: jload(T / f"match_{set_name}/matches.{m}.json")["asks"] for m in ("1", "2")}
        fb = jload(ROOT / cfg["feedback"] / "feedback.json")["rows"]
        fb_by_cid = {r["cid"]: r for r in fb if r.get("cid")}
        inputs = {}
        for b in sorted((SCRATCH / f"match_{set_name}").glob("b*/inputs")):
            for f in b.glob("*.json"):
                inputs[f.name] = jload(f)
        by_pr = defaultdict(lambda: {"asks": []})
        for m, lst in matches.items():
            for row in lst:
                pr = str(row["pr"]);
                d = by_pr[pr]
                ask = next((a for a in d["asks"] if a["id"] == row["ask_id"]), None)
                if ask is None:
                    meta = ASKS.get(row["ask_id"], {})
                    fbr = fb_by_cid.get(row["ask_id"], {})
                    ask = {"id": row["ask_id"], "pr": int(pr), "family": meta.get("family"),
                           "in_census": meta.get("in_census"),
                           "entries": sorted(set((meta.get("r1") or []) + (meta.get("r2") or []))),
                           "text": fbr.get("body"), "path": fbr.get("path"), "line": fbr.get("line"),
                           "author": fbr.get("author"), "at": fbr.get("at"),
                           "matcher_text": None, "outcomes": {}}
                    ask["entries_text"] = {e: CODEBOOK.get(e) for e in ask["entries"]}
                    ma = inputs.get(f"asks_pr{pr}.json")
                    if ma:
                        hit = next((x for x in ma if x.get("ask_id") == row["ask_id"] or x.get("id") == row["ask_id"]), None)
                        ask["matcher_text"] = hit
                    d["asks"].append(ask)
                labels = seal[pr]
                for R, label in labels.items():
                    o = ask["outcomes"].setdefault(label, {"R": R})
                    o[f"m{m}"] = row.get(R)
                    o[f"m{m}_finding"] = row.get(f"{R}_finding")
                    fi = row.get(f"{R}_finding")
                    if fi is not None and f"{R}_pr{pr}.json" in inputs:
                        lst_f = inputs[f"{R}_pr{pr}.json"]
                        if 0 <= fi < len(lst_f):
                            o[f"m{m}_finding_text"] = lst_f[fi]
                    o["note_m" + m] = row.get("note")
        # sessions: per PR, per label, the run and transcript; findings as matched
        for pr, d in by_pr.items():
            d["pr"] = int(pr)
            d["sessions"] = {}
            for label, src in sources.items():
                R = next((r for r, l in seal[pr].items() if l == label), None)
                findings = inputs.get(f"{R}_pr{pr}.json") if R else None
                ent = {"R": R, "kind": src.get("kind"), "run": src.get("run"),
                       "findings_as_matched": findings}
                if label in LABELS_READ and src.get("kind") == "solo":
                    runs = src["run"] if isinstance(src["run"], list) else [src["run"]]
                    for run in runs:
                        tf = session_file(run, int(pr))
                        if tf:
                            ent["run"] = run
                            ent["transcript"] = tf
                            break
                d["sessions"][label] = ent
            ap = d["sessions"].get("AP1") or {}
            if ap.get("transcript"):
                sec = ap_section(ap["transcript"])
                if sec:
                    p = HERE / "ap_sections" / f"{set_name}_{pr}.md"
                    p.write_text(sec)
                    d["ap_section"] = str(p.relative_to(ROOT))
            (HERE / "packets" / set_name).mkdir(exist_ok=True)
            (HERE / "packets" / set_name / f"{pr}.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))
            sessions_all[f"{set_name}/{pr}"] = {l: {k: v for k, v in e.items() if k != "findings_as_matched"}
                                               for l, e in d["sessions"].items()}
            for a in d["asks"]:
                def hits(prefix):
                    return sum(1 for l, o in a["outcomes"].items() if l.startswith(prefix) and o.get("m1") == "reached")
                rows_all.append({"set": set_name, "ask": a["id"], "pr": pr, "family": a["family"],
                                 "in_census": a["in_census"], "entries": " ".join(a["entries"]),
                                 "DX": hits("DX"), "AP": hits("AP"), "X": hits("X"), "T": hits("T"),
                                 "TA": hits("TA"), "OP": hits("OP"), "GPT": hits("GPT"),
                                 "text": (a["text"] or "").replace("\n", " ")[:160]})
    with open(HERE / "asks_all.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_all[0].keys()), delimiter="\t")
        w.writeheader(); w.writerows(sorted(rows_all, key=lambda r: (r["set"], r["pr"], r["ask"])))
    (HERE / "sessions.json").write_text(json.dumps(sessions_all, indent=1))
    n_tr = sum(1 for v in sessions_all.values() for e in v.values() if e.get("transcript"))
    print(f"asks {len(rows_all)}; PRs {len(sessions_all)}; DeepSeek transcripts located {n_tr} of "
          f"{sum(1 for v in sessions_all.values() for l in v if l in LABELS_READ)}; "
          f"AP sections {len(list((HERE / 'ap_sections').glob('*.md')))}")


if __name__ == "__main__":
    main()
