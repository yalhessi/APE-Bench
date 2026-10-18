"""DeepSeek as stage F's selector: can the reviewer's own model choose the conventions that apply to a
PR, without the asks, as well as stage F's Opus selector? Pre-registered in this directory's README
before any call.

One turn per (PR, sample): stage F's rubric (`../conventions-ceiling-2026-10-04/selector_rubric.md`),
its selection sections verbatim, with the inputs inline instead of as files, built exactly as
`build_selector_folders.py` builds them: every census entry as `P### sentence`, `probes.pr_markdown`,
`probes.render_models`, the episode's diff. Three samples a PR on the 14 probe PRs with in-census
asks.

  build                          prompts (uncommitted) and items.json
  run <base_url> <model> [workers]   the calls, resumable, into outputs.jsonl
  read                           the pre-registered reading

usage (repo root, PYTHONPATH=$PWD:$PWD/src): ape/bin/python <this file> <command> [args]
"""
import importlib.util
import json
import re
import statistics
import sys
from pathlib import Path

from src.mathlib_review.analysis import probes
from src.mathlib_review.io import jsonl_rows

HERE = Path(__file__).parent
CEILING = HERE.parent / "conventions-ceiling-2026-10-04"
spec = importlib.util.spec_from_file_location("ladder", HERE.parent / "conventions-ladder-2026-10-08" / "ladder.py")
ladder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ladder)
PROMPTS = HERE / "prompts"
SAMPLES = 3
MAX_TOKENS = 65536

#: stage F's rubric with its two file-bound paragraphs replaced; every selection sentence is verbatim
INTRO = """# Which conventions apply to this pull request?

You are choosing, for a reviewer, which of Mathlib's review conventions are relevant to one pull
request. Below are 438 conventions the maintainers hold, one a line, `P001` to `P438`. Each names a
situation and the form preferred in it. They were written from maintainers' review comments on other
pull requests. Below them is the pull request: its title, description and changed files, every
changed object and what changed, and its diff.
"""
OUTPUT = """## Output

Answer with a JSON list and nothing else, most squarely applicable first, of objects with exactly
these keys:

- `id`: the convention's id, as in the list of conventions.
- `where`: the declaration or declarations, file, or part of the PR where its situation occurs.
- `why`: at most 20 words: what in the PR is the convention's situation.

Every `id` must be one in the list, no id may repeat, and there must be at most 25.
"""


def rubric_selection() -> str:
    """The rubric's "What to select" and "How many" sections, verbatim."""
    text = (CEILING / "selector_rubric.md").read_text()
    return text[text.index("## What to select"):text.index("## Output")].rstrip() + "\n"


def build() -> None:
    asks = json.loads((CEILING / "briefs_exact.json").read_text())["asks"]
    prs = sorted({a["pr"] for a in asks.values() if a["in_census"]})
    conventions = "".join(f"{e['id']} {e['principle']}\n" for e in json.loads(ladder.CODEBOOK.read_text()))
    PROMPTS.mkdir(exist_ok=True)
    items = []
    for path in ladder.SETS.values():
        s = probes.load_probe_set(Path(path))
        mine = [pr for pr in s.pr_numbers if pr in prs]
        if not mine:
            continue
        models = probes.render_models(s.release, mine, s.inventory)
        episodes = {e["pr_number"]: e for e in jsonl_rows(s.release / "input/episodes.jsonl")}
        for pr in mine:
            e = episodes[pr]
            text = (INTRO + "\n" + rubric_selection() + "\n" + OUTPUT + "\n## The conventions\n\n" + conventions
                    + "\n## The pull request\n\n" + probes.pr_markdown(e).rstrip() + "\n\n## Every changed object\n\n"
                    + models[pr].rstrip() + "\n\n## The diff\n\n```\n" + e["diff"].rstrip() + "\n```\n")
            (PROMPTS / f"pr{pr}.txt").write_text(text)
            items.append({"pr": pr, "chars": len(text), "sha256": ladder.digest(text)})
    (HERE / "items.json").write_text(json.dumps({"samples": SAMPLES, "max_tokens": MAX_TOKENS, "items": items}, indent=1) + "\n")
    print(f"{len(items)} prompts, {min(i['chars'] for i in items)}-{max(i['chars'] for i in items)} chars; {len(items) * SAMPLES} calls")


def run(base: str, model: str, workers: str = "16") -> None:
    import concurrent.futures, threading, time
    meta = json.loads((HERE / "items.json").read_text())
    out = HERE / "outputs.jsonl"
    done = {(r["pr"], r["sample"]) for r in map(json.loads, out.open())} if out.exists() else set()
    todo = []
    for item in meta["items"]:
        text = (PROMPTS / f"pr{item['pr']}.txt").read_text()
        if ladder.digest(text) != item["sha256"]:
            sys.exit(f"pr{item['pr']}: the prompt is not the pre-registered bytes")
        todo += [(item, text, n) for n in range(1, meta["samples"] + 1) if (item["pr"], n) not in done]
    lock = threading.Lock()
    print(f"{len(done)} done, {len(todo)} to run", flush=True)

    def one(job):
        item, text, n = job
        started = time.time()
        r = ladder.chat(base, {"model": model, "messages": [{"role": "user", "content": text}],
                               "reasoning_effort": "high", "max_tokens": meta["max_tokens"]}, timeout=7200)
        message, usage = r["choices"][0]["message"], r.get("usage") or {}
        row = {"pr": item["pr"], "sample": n, "content": message.get("content") or "",
               "finish_reason": r["choices"][0].get("finish_reason"), "prompt_tokens": usage.get("prompt_tokens"),
               "completion_tokens": usage.get("completion_tokens"), "seconds": round(time.time() - started, 1)}
        with lock:
            with out.open("a") as f:
                f.write(json.dumps(row) + "\n")
        return row

    with concurrent.futures.ThreadPoolExecutor(int(workers)) as pool:
        for k, future in enumerate(concurrent.futures.as_completed([pool.submit(one, j) for j in todo]), 1):
            row = future.result()
            print(f"{time.strftime('%H:%M:%S')} {k}/{len(todo)} pr{row['pr']} s{row['sample']}: {row['finish_reason']}, "
                  f"{row['completion_tokens']} tokens, {row['seconds']} s", flush=True)


def picks_of(content: str) -> list:
    """The ordered ids of a selector's answer; ids not in the codebook and repeats dropped, at most 25."""
    known = {e["id"] for e in json.loads(ladder.CODEBOOK.read_text())}
    try:
        body = content[content.index("["):content.rindex("]") + 1]
        ids = [x.get("id") for x in json.loads(body) if isinstance(x, dict)]
    except (ValueError, json.JSONDecodeError):
        ids = re.findall(r"\bP\d{3}\b", content)
    out = []
    for i in ids:
        if i in known and i not in out:
            out.append(i)
    return out[:25]


def read() -> None:
    asks = json.loads((CEILING / "briefs_exact.json").read_text())["asks"]
    opus = {int(f.stem[2:]): [x["id"] for x in json.loads(f.read_text())] for f in (CEILING / "selectors").glob("pr*.json")}
    rows = [json.loads(l) for l in (HERE / "outputs.jsonl").open()]
    ds = {}
    for r in rows:
        ds.setdefault(r["pr"], {})[r["sample"]] = picks_of(r["content"])
    inc = {c: a for c, a in asks.items() if a["in_census"]}

    def recall(picks_by_pr, prs, k):
        cs = [c for c, a in inc.items() if a["pr"] in prs]
        return sum(bool(set(inc[c]["r1"]) & set(picks_by_pr[inc[c]["pr"]][:k])) for c in cs) / len(cs), len(cs)

    print("answers:", len(rows), "| unparsed or empty:", sum(not picks_of(r["content"]) for r in rows),
          "| truncated:", sum(r["finish_reason"] == "length" for r in rows),
          "| picks a sample, median:", statistics.median(len(p) for d in ds.values() for p in d.values()))
    ten = sorted(opus)
    for name, prs in (("the 10 stage F PRs", ten), ("all 14 probe PRs", sorted(ds))):
        print(f"\n== {name} ==")
        for k in (5, 10, 25):
            per_sample = [recall({pr: ds[pr][n] for pr in prs}, prs, k)[0] for n in range(1, SAMPLES + 1)]
            line = f"  recall@{k}: DeepSeek per sample {', '.join(f'{x:.2f}' for x in per_sample)} (mean {statistics.mean(per_sample):.3f})"
            if prs == ten:
                line += f" | Opus {recall(opus, prs, k)[0]:.3f}"
            print(line)
        union = {pr: sorted(set().union(*ds[pr].values())) for pr in prs}
        r, n = recall(union, prs, 999)
        print(f"  union of the three samples' picks: recall {r:.3f} of {n} asks; picks a PR, mean {statistics.mean(len(v) for v in union.values()):.1f}")
        if prs == ten:
            agree = [len(set(ds[pr][n][:25]) & set(opus[pr])) for pr in prs for n in range(1, SAMPLES + 1)]
            print(f"  overlap with Opus's 25, entries a sample: mean {statistics.mean(agree):.1f}")


if __name__ == "__main__":
    command, args = sys.argv[1], sys.argv[2:]
    {"build": build, "run": run, "read": read}[command](*args)
