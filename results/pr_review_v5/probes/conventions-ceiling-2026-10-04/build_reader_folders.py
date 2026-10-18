"""The assign-only reading's batch and its two reader folders.

The 46 agreed asks of the two probe sets, in one seeded order, in the census's batch format
(`conventions-census-v1/provenance/build_batches.py`). Each reader folder holds the rubric, a copy
of reader A's codebook and the batch, and nothing else; a reader writes `labels.jsonl` there.

With sets named after the scratch dir (the one reviewer table's dev census share, 2026-10-10), the
batch is `reader_batch_<stem>.md` and the rubric's counts are the named sets'; stage L's batch is not
rewritten. Each folder's prompt is printed as a JSON line for `run_claude_batch.sh @file`.

usage (repo root, PYTHONPATH=$PWD/src): ape/bin/python <this file> <scratch dir for the folders> [set.yaml ...]
"""
import hashlib
import json
import sys
from pathlib import Path

from src.mathlib_review.analysis import probes

HERE = Path(__file__).parent
CODEBOOK = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json")
SETS = ("configs/probe_sets/val_small12.yaml", "configs/probe_sets/postcutoff_2026_07_08_v1.yaml")
SEED = "conventions-ceiling-2026-10-04"
FAM = {"F1": "proof", "F2": "interface", "F3": "registration", "F4": "derive, don't restate",
       "F5": "redundancy", "F6": "statement and API design", "F7": "generality", "F8": "naming",
       "F9": "formatting", "F10": "documentation", "F11": "meta-code correctness", "F12": "PR level"}

PROMPT = """You are a labeller in a research study of Mathlib code review. Your working directory is `{dir}`.

Read `reader_rubric.md` in that directory and do what it says. Its inputs (`codebook.json`, `batch.md`) are in the same directory.

Rules, which the study depends on:
- Read only files inside your working directory. Do not open, list or search anything outside it, do not run git, and do not use web search or web fetch.
- Put any temporary file in `tmp/` inside your working directory.

When done, reply as the rubric asks."""
custom = tuple(sys.argv[2:])
if custom:
    SETS = custom
asks = []
for path in SETS:
    spec = probes.load_probe_set(Path(path))
    agreed = json.loads(spec.asks_file.read_text())
    rows = {r["cid"]: r for r in json.loads(spec.feedback_file.read_text())["rows"]}
    for cids in agreed["asks"].values():
        asks.extend((rows[c], agreed["families"][c], rows) for c in cids)
asks.sort(key=lambda a: hashlib.sha256(f"{SEED}\0{a[0]['cid']}".encode()).hexdigest())

lines = [f"# {len(asks)} asks\n"]
for r, family, rows in asks:
    parent = rows.get(r["reply_to_cid"]) if r.get("reply_to_cid") else None
    lines.append(f"\n## {r['cid']}  PR {r['pr']} ({'AI' if r['ai'] else 'human'}) — {(r['pr_title'] or '')[:80]}\n"
                 f"{r['path']}:{r['line']}  kind={r['kind']}  by {r['author']}  family={family} {FAM.get(family, '')}\n")
    if parent:
        lines.append(f"> (in reply to) {parent['body'][:500]}\n")
    lines.append(f"**ASK:** {r['body'][:1500]}\n```\n{(r['diff_hunk'] or '')[-900:]}\n```\n")
batch = HERE / (f"reader_batch_{'_'.join(Path(s).stem for s in custom)}.md" if custom else "reader_batch.md")
batch.write_text("".join(lines))
rubric = (HERE / "reader_rubric_assign.md").read_text()
if custom:
    rubric = rubric.replace("46 round-1 maintainer asks on 14 pull requests",
                            f"{len(asks)} round-1 maintainer asks on {len({r['pr'] for r, _f, _rows in asks})} pull requests")

for d in probes.judge_folders(Path(sys.argv[1]), 2, [batch, CODEBOOK], HERE / "reader_rubric_assign.md", rubric_text=rubric):
    (d / batch.name).rename(d / "batch.md")
    (d / "reader_rubric_assign.md").rename(d / "reader_rubric.md")
    print(json.dumps({"folder": str(d.resolve()), "description": f"Reader {d.name}", "prompt": PROMPT.format(dir=d.resolve())}))
print(f"{batch}: {len(asks)} asks, order sha256({SEED!r}, cid)")
