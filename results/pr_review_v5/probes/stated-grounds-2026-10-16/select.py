"""Select the census asks that state a ground (PROTOCOL.md) and build reader packets in scratch.

usage (repo root): ape/bin/python <this file> <bodies.json from materialise_bodies.py> <scratch packet dir>
writes selected.jsonl here (cid, PR, path, markers; no body) and the packets in scratch.
"""
import glob
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = "results/pr_review_v5/adjudications/conventions-census-v1/reader_A/labels_b*.jsonl"
CODEBOOK = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json")
MARKERS = {
    "reason": r"\b(because|since|so that|in order to|otherwise|to avoid|to make (it|this|the)|this (makes|allows|lets|would|avoids|ensures)|which (means|makes|would|allows)|the (reason|point) is)\b",
    "consistency": r"\b(consisten\w*|conventions?|as (elsewhere|in the rest|we do|is done)|in mathlib,? we|mathlib (style|usually|prefers|tends|generally)|style guide|the rest of (the|this) (file|library)|like the other|for coherence|elsewhere in)\b",
    "external": r"(https?://|zulip|\B#\d{4,6}\b|library note|naming convention)",
    "currency": r"\b(deprecat\w*|nowadays|these days|now that|newer|modern|we now|no longer|old[- ]style|legacy|going forward|from now on)\b",
    "preference": r"\b(I (prefer|would prefer|personally)|my preference|personally|nicer|cleaner|more readable|easier to read|ugly)\b",
}
SEED, BATCHES = 20261016, 4


def strip_code(text: str) -> str:
    return re.sub(r"```.*?```", " ", text or "", flags=re.S)


def shorten_code(text: str, keep: int = 8) -> str:
    def cut(m):
        lines = m.group(0).splitlines()
        return "\n".join(lines[:keep + 1] + (["…", "```"] if len(lines) > keep + 2 else lines[keep + 1:]))
    return re.sub(r"```.*?```", cut, text or "", flags=re.S)


def main() -> int:
    bodies, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    rows = json.loads(bodies.read_text())
    rows = {r["cid"]: r for r in (rows if isinstance(rows, list) else rows["rows"])}
    labels = {}
    for f in sorted(glob.glob(LABELS)):
        for line in open(f):
            x = json.loads(line)
            labels[x["cid"]] = x
    order = [e["id"] for e in json.loads(CODEBOOK.read_text())]
    counts = {}
    for x in labels.values():
        counts[x["principle_id"]] = counts.get(x["principle_id"], 0) + 1
    rank = {p: i + 1 for i, (p, _) in enumerate(sorted(counts.items(), key=lambda kv: -kv[1]))}
    selected = []
    for cid, lab in sorted(labels.items()):
        text = strip_code(rows[cid]["body"])
        found = [k for k, p in MARKERS.items() if re.search(p, text, re.I)]
        if found:
            selected.append({"cid": cid, "pr": rows[cid]["pr"], "path": rows[cid]["path"], "markers": found,
                             "ai": rows[cid].get("ai") == "True", "rank": rank.get(lab["principle_id"])})
    random.Random(SEED).shuffle(selected)
    for n, s in enumerate(selected):
        s["batch"] = n % BATCHES + 1
    (HERE / "selected.jsonl").write_text("".join(json.dumps(s) + "\n" for s in selected))
    out_dir.mkdir(parents=True, exist_ok=True)
    for b in range(1, BATCHES + 1):
        parts = []
        for s in [s for s in selected if s["batch"] == b]:
            r = rows[s["cid"]]
            parent = rows.get(r.get("reply_to_cid")) if r.get("reply_to_cid") not in (None, "None") else None
            hunk = "\n".join((r.get("diff_hunk") or "").splitlines()[-12:])
            parts.append(f"## {s['cid']}\n\nPR title: {r.get('pr_title')}\nFile: {r.get('path')}\n\n"
                         + (f"In reply to: {shorten_code(parent['body'])}\n\n" if parent else "")
                         + f"Code at the comment (last lines of the diff hunk):\n```diff\n{hunk}\n```\n\n"
                         + f"The maintainer's comment:\n\n{shorten_code(r['body'])}\n")
        (out_dir / f"batch_{b}.md").write_text("\n\n---\n\n".join(parts))
    print(len(selected), "selected; batches", [sum(1 for s in selected if s["batch"] == b) for b in range(1, BATCHES + 1)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
