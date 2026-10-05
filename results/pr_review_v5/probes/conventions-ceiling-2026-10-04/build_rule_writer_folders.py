"""Blind rule-writer folders for stage G: the rule set's entries (`stage_g_entries.json`), shuffled
and unmarked, each with its census sentence and up to four of the asks reader A filed under it,
split over two writers. The asks are on census PRs, which are disjoint from every probe PR; nothing
here comes from a probe PR or its feedback. Bodies are never committed, so they come from
`conventions-census-v1/provenance/materialise_bodies.py`'s output.

usage (repo root): python3 <this file> <bodies.json> <scratch dir>
"""
import glob
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
CENSUS = Path("results/pr_review_v5/adjudications/conventions-census-v1")
PROMPT = """You are a rule writer in a research study of Mathlib code review. Your working directory is `{dir}`.

Read `rule_writer_rubric.md` in that directory and do what it says. Its input, `entries.md`, is in the same directory.

Rules, which the study depends on:
- Read only files inside your working directory. Do not open, list or search anything outside it, do not run git, and do not use web search or web fetch.
- Put any temporary file in `tmp/` inside your working directory.
- The rules must be yours, written by reading each entry and its examples. A script may check your JSON, but must not write a rule.

When done, reply with one line: the number of rules written."""

bodies_path, root = Path(sys.argv[1]), Path(sys.argv[2])
spec = json.loads((HERE / "stage_g_entries.json").read_text())
seed = spec["seed"]
key = lambda *parts: hashlib.sha256("\0".join((seed,) + parts).encode()).hexdigest()
principle = {e["id"]: e["principle"] for e in json.loads((CENSUS / "reader_A/codebook.json").read_text())}
body = {r["cid"]: r for r in json.loads(bodies_path.read_text())["rows"] if r["set"] in ("val1000", "outside_years")}
filed = {}
for path in sorted(glob.glob(str(CENSUS / "reader_A/labels_*.jsonl"))):
    for row in map(json.loads, open(path, encoding="utf-8")):
        if row["principle_id"] != "none" and row["cid"] in body:
            filed.setdefault(row["principle_id"], []).append(row["cid"])
entries = sorted(spec["pool"] + spec["decoys"], key=lambda i: key("order", i))
half = (len(entries) + 1) // 2
for n, chunk in enumerate((entries[:half], entries[half:]), 1):
    d = root / f"writer{n}"
    if d.exists():
        shutil.rmtree(d)
    (d / "tmp").mkdir(parents=True)
    parts = [f"# {len(chunk)} conventions, each with review comments that asked for it\n"]
    for i in chunk:
        parts.append(f"\n## {i}\n\n**Convention:** {principle[i]}\n")
        for k, cid in enumerate(sorted(filed.get(i, []), key=lambda c: key("ask", i, c))[:4], 1):
            r = body[cid]
            parts.append(f"\n### Example {k} (`{r['path']}`)\n\n**The maintainer's comment:** {r['body'][:900]}\n\n"
                         f"**The code it was attached to:**\n```\n{(r['diff_hunk'] or '(no code: a comment on the PR as a whole)')[-800:]}\n```\n")
    (d / "entries.md").write_text("".join(parts))
    shutil.copy(HERE / "rule_writer_rubric.md", d / "rule_writer_rubric.md")
    print(json.dumps({"folder": str(d.resolve()), "description": f"Rule writer {n}",
                      "prompt": PROMPT.format(dir=d.resolve())}))
