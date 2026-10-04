"""Blind selector folders for the floor stage: one a PR, holding what a reviewer's packet holds
(pr.md, model.md, diff.patch), every census convention as `P### sentence`, and the rubric. Nothing in
a folder comes from a step that has seen feedback. Prints the JSON lines `run_claude_batch.sh @file`
takes: a folder, a description and the prompt.

usage (repo root, PYTHONPATH=$PWD/src): ape/bin/python <this file> <scratch dir> <set.yaml>:<pr> [...]
"""
import json
import shutil
import sys
from pathlib import Path

from src.mathlib_review.analysis import probes

HERE = Path(__file__).parent
CODEBOOK = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json")
PROMPT = """You are a selector in a research study of Mathlib code review. Your working directory is `{dir}`.

Read `selector_rubric.md` in that directory and do what it says. Its inputs (`conventions.md`, `pr.md`, `model.md`, `diff.patch`) are in the same directory.

Rules, which the study depends on:
- Read only files inside your working directory. Do not open, list or search anything outside it, do not run git, and do not use web search or web fetch.
- Put any temporary file in `tmp/` inside your working directory.
- The choices must be yours, made by reading the pull request and every convention. A script may check your JSON, but must not choose.

When done, reply with one line: the number of conventions selected."""

root = Path(sys.argv[1])
conventions = "".join(f"{e['id']} {e['principle']}\n" for e in json.loads(CODEBOOK.read_text()))
for item in sys.argv[2:]:
    spec_path, pr = item.rsplit(":", 1)
    spec = probes.load_probe_set(Path(spec_path))
    models = probes.render_models(spec.release, [int(pr)], spec.inventory)
    with (spec.release / "input/episodes.jsonl").open(encoding="utf-8") as handle:
        episode = next(e for e in map(json.loads, handle) if e["pr_number"] == int(pr))
    d = root / f"pr{pr}"
    if d.exists():
        shutil.rmtree(d)
    (d / "tmp").mkdir(parents=True)
    (d / "pr.md").write_text(probes.pr_markdown(episode))
    (d / "model.md").write_text(models[int(pr)])
    (d / "diff.patch").write_text(episode["diff"])
    (d / "conventions.md").write_text(conventions)
    shutil.copy(HERE / "selector_rubric.md", d / "selector_rubric.md")
    print(json.dumps({"folder": str(d.resolve()), "description": f"Selector pr{pr}",
                      "prompt": PROMPT.format(dir=d.resolve())}))
