"""Blind pinpointing folders for stage G: one a PR, holding what a reviewer's packet holds (pr.md,
model.md, diff.patch, byte-identical to X1's), the stage's guarded rules as `rules.md`, and the
rubric. The rules are in one seeded order for every PR, with nothing marking which are behind an
ask. Nothing in a folder comes from a step that has seen a probe PR's feedback. Prints the JSON
lines `run_claude_batch.sh @file` takes.

usage (repo root, PYTHONPATH=$PWD/src): ape/bin/python <this file> <scratch dir> <set.yaml>:<pr> [...]
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

from src.mathlib_review.analysis import probes

HERE = Path(__file__).parent
CODEBOOK = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json")
PROMPT = """You are preparing notes for a reviewer in a research study of Mathlib code review. Your working directory is `{dir}`.

Read `pinpoint_rubric.md` in that directory and do what it says. Its inputs (`rules.md`, `pr.md`, `model.md`, `diff.patch`) are in the same directory.

Rules, which the study depends on:
- Read only files inside your working directory. Do not open, list or search anything outside it, do not run git, and do not use web search or web fetch.
- Put any temporary file in `tmp/` inside your working directory.
- The judgements must be yours, made by reading the pull request against every rule. A script may check your JSON, but must not choose.

When done, reply with one line: the number of items."""


def rules_markdown() -> str:
    seed = json.loads((HERE / "stage_g_entries.json").read_text())["seed"]
    principle = {e["id"]: e["principle"] for e in json.loads(CODEBOOK.read_text())}
    rules = sorted(json.loads((HERE / "rules.json").read_text()),
                   key=lambda r: hashlib.sha256(f"{seed}\0rules\0{r['id']}".encode()).hexdigest())
    parts = [f"# {len(rules)} conventions, as rules\n"]
    for r in rules:
        parts.append(f"\n## {r['id']}\n\n- **Convention:** {principle[r['id']]}\n- **Applies to:** {r['applies_to']}\n"
                     f"- **Trigger:** {r['trigger']}\n- **Preferred form:** {r['required']}\n"
                     f"- **How to tell a departure (`{r['check_kind']}`):** {r['check']}\n"
                     f"- **Not when:** {r['not_when'] or 'no exception recorded'}\n")
    return "".join(parts)


if __name__ == "__main__":
    root, rules = Path(sys.argv[1]), rules_markdown()
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
        (d / "rules.md").write_text(rules)
        shutil.copy(HERE / "pinpoint_rubric.md", d / "pinpoint_rubric.md")
        print(json.dumps({"folder": str(d.resolve()), "description": f"Pinpointer pr{pr}",
                          "prompt": PROMPT.format(dir=d.resolve())}))
