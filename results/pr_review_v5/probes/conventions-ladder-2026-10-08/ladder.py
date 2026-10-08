"""The oracle ladder: at the place of each in-census probe ask, what does DeepSeek produce from each
representation of the convention? Pre-registered in this directory's README before any call.

Five arms per ask (README, "The arms"): F the place alone; U the sentence, judged; UX the sentence
with DP's two census examples, judged; A the sentence, asserted; AX the sentence with the examples,
asserted. Three samples each. Single turn, no tools.

  build <bodies.json>        prompts (uncommitted: the X arms quote census bodies) and items.json
  run <base_url> <model>     the calls, resumable, into outputs.jsonl (answers) and reasoning.jsonl
  match-inputs <out dir>     the seal and two blind matcher folders
  unblind                    matcher files -> unblinded.json
  read                       the pre-registered reading

usage (repo root, PYTHONPATH=$PWD/src): ape/bin/python <this file> <command> [args]
"""
import concurrent.futures
import hashlib
import json
import random
import re
import sys
import threading
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

from src.mathlib_review.analysis import probes

HERE = Path(__file__).parent
CEILING = HERE.parent / "conventions-ceiling-2026-10-04"
CODEBOOK = Path("results/pr_review_v5/adjudications/conventions-census-v1/reader_A/codebook.json")
SETS = {"val": "configs/probe_sets/val_small12.yaml", "post": "configs/probe_sets/postcutoff_2026_07_08_v1.yaml"}
FEEDBACK = ["results/pr_review_v5/probes/model-gap-val-small12/feedback.json",
            "results/pr_review_v5/probes/postcutoff-2026-09-29/feedback.json"]
PROMPTS = HERE / "prompts"
ARMS = ["F", "U", "UX", "A", "AX"]
SAMPLES = 3
SEED = "conventions-ladder-2026-10-08"

HEAD = """You are reviewing a pull request to Mathlib, the Lean 4 mathematics library.

<pull_request>
{pr}
</pull_request>

<diff>
{diff}
</diff>

The place: {place}
"""
ASKED = "A Mathlib maintainer reviewing this pull request asked the author for a change at this place"
ARM_TEXT = {
    "F": ASKED + ". What change did they most likely ask for?",
    "U": "Here is a convention Mathlib's maintainers apply:\n\n{conventions}\n\nDoes the code at this place "
         "conform to this convention? If it departs from it, write the change the convention calls for.",
    "UX": "Here is a convention Mathlib's maintainers apply, with up to two comments in which a maintainer "
          "asked for it on another pull request:\n\n{conventions}\n\nDoes the code at this place conform to "
          "this convention? If it departs from it, write the change the convention calls for.",
    "A": ASKED + ", under this convention:\n\n{conventions}\n\nWrite the change they asked for.",
    "AX": ASKED + ", under this convention (beneath it, up to two comments in which a maintainer asked for "
          "it on another pull request):\n\n{conventions}\n\nWrite the change they asked for.",
}
FORM_JUDGED = ("Answer in exactly this form and nothing else:\nVERDICT: departs | conforms\n"
               "CHANGE: <the change, as code or in one or two sentences; `none` if the code conforms>\n"
               "WHY: <one sentence>")
FORM_ASKED = ("Answer in exactly this form and nothing else:\n"
              "CHANGE: <the change, as code or in one or two sentences>\nWHY: <one sentence>")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def asks_in_census() -> dict:
    asks = json.loads((CEILING / "briefs_exact.json").read_text())["asks"]
    return {cid: a for cid, a in sorted(asks.items()) if a["in_census"]}


def place(row: dict) -> str:
    if row["kind"] == "issue_comment":
        return "the pull request as a whole (the maintainer's comment is on the pull request, not on a line)."
    hunk = (row.get("diff_hunk") or "").rstrip()
    if not hunk:
        return f"the file `{row['path']}` as a whole."
    return f"`{row['path']}`, at the last line of this excerpt of the diff:\n\n```\n{hunk}\n```"


def build(bodies_path: str) -> None:
    feedback = {r["cid"]: r for f in FEEDBACK for r in json.loads(Path(f).read_text())["rows"]}
    episodes = {}
    for path in SETS.values():
        spec = probes.load_probe_set(Path(path))
        for line in (spec.release / "input/episodes.jsonl").read_text().splitlines():
            e = json.loads(line)
            episodes[e["pr_number"]] = e
    principle = {e["id"]: e["principle"] for e in json.loads(CODEBOOK.read_text())}
    chosen = json.loads((CEILING / "examples_prec.json").read_text())["entries"]
    body = {r["cid"]: r for r in json.loads(Path(bodies_path).read_text())["rows"]
            if r["set"] in ("val1000", "outside_years")}
    # DP's cuts (build_context.census_examples): comment to 900 characters, the hunk's last 800.
    examples = {i: [{"path": body[x["cid"]]["path"], "comment": body[x["cid"]]["body"][:900],
                     "code": (body[x["cid"]]["diff_hunk"] or "")[-800:]} for x in xs] for i, xs in chosen.items()}
    PROMPTS.mkdir(exist_ok=True)
    items = []
    for cid, a in asks_in_census().items():
        row, episode = feedback[cid], episodes[a["pr"]]
        head = HEAD.format(pr=probes.pr_markdown(episode).rstrip(), diff=episode["diff"].rstrip(), place=place(row))
        entries = a["r1"]
        for arm in ARMS:
            if arm == "F":
                conventions = ""
            elif arm.endswith("X"):
                conventions = "\n\n".join("- " + probes.exemplified(principle[i], examples.get(i, [])) for i in entries)
            else:
                conventions = "\n".join(f"- {principle[i]}" for i in entries)
            text = head + "\n" + ARM_TEXT[arm].format(conventions=conventions) + "\n\n" + (
                FORM_JUDGED if arm in ("U", "UX") else FORM_ASKED) + "\n"
            (PROMPTS / f"{cid}__{arm}.txt").write_text(text)
            items.append({"cid": cid, "pr": a["pr"], "set": a["set"], "arm": arm, "entries": entries,
                          "examples": sum(len(examples.get(i, [])) for i in entries) if arm.endswith("X") else 0,
                          "chars": len(text), "sha256": digest(text)})
    (HERE / "items.json").write_text(json.dumps({"seed": SEED, "samples": SAMPLES, "items": items}, indent=1) + "\n")
    print(f"{len(items)} prompts for {len(items) // len(ARMS)} asks; chars {min(i['chars'] for i in items)}"
          f"-{max(i['chars'] for i in items)}")


def chat(base: str, payload: dict, timeout: int = 3600) -> dict:
    request = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer local"})
    return json.load(urllib.request.urlopen(request, timeout=timeout))


def run(base: str, model: str, workers: str = "24") -> None:
    items = json.loads((HERE / "items.json").read_text())["items"]
    out, thought = HERE / "outputs.jsonl", HERE / "reasoning.jsonl"
    done = {(r["cid"], r["arm"], r["sample"]) for r in map(json.loads, out.open())} if out.exists() else set()
    todo = []
    for item in items:
        text = (PROMPTS / f"{item['cid']}__{item['arm']}.txt").read_text()
        if digest(text) != item["sha256"]:
            sys.exit(f"{item['cid']} {item['arm']}: the prompt is not the pre-registered bytes")
        todo += [(item, text, n) for n in range(1, SAMPLES + 1) if (item["cid"], item["arm"], n) not in done]
    lock = threading.Lock()
    print(f"{len(done)} done, {len(todo)} to run", flush=True)

    def one(job):
        item, text, n = job
        started = time.time()
        r = chat(base, {"model": model, "messages": [{"role": "user", "content": text}],
                        "reasoning_effort": "high", "max_tokens": 32768})
        message, usage = r["choices"][0]["message"], r.get("usage") or {}
        row = {"cid": item["cid"], "arm": item["arm"], "sample": n, "content": message.get("content") or "",
               "finish_reason": r["choices"][0].get("finish_reason"), "prompt_tokens": usage.get("prompt_tokens"),
               "completion_tokens": usage.get("completion_tokens"), "seconds": round(time.time() - started, 1)}
        with lock:
            with out.open("a") as f:
                f.write(json.dumps(row) + "\n")
            with thought.open("a") as f:
                f.write(json.dumps({k: row[k] for k in ("cid", "arm", "sample")}
                                   | {"reasoning": message.get("reasoning_content") or message.get("reasoning") or ""}) + "\n")
        return row

    finished = 0
    with concurrent.futures.ThreadPoolExecutor(int(workers)) as pool:
        for future in concurrent.futures.as_completed([pool.submit(one, job) for job in todo]):
            row = future.result()
            finished += 1
            if finished % 25 == 0 or finished == len(todo):
                print(f"{time.strftime('%H:%M:%S')} {finished}/{len(todo)} (last {row['cid']} {row['arm']} "
                      f"{row['completion_tokens']} tokens, {row['seconds']} s)", flush=True)


def change(content: str) -> str:
    """The answer's CHANGE line(s): what a matcher sees. Without one, the whole answer, cut."""
    m = re.search(r"CHANGE:\s*(.*?)(?:\n\s*WHY:|\Z)", content, flags=re.S)
    return (m.group(1).strip() if m else content.strip())[:1500]


def match_inputs(out_dir: str) -> None:
    outputs = defaultdict(dict)
    for r in map(json.loads, (HERE / "outputs.jsonl").open()):
        outputs[r["cid"]][(r["arm"], r["sample"])] = r
    asks, feedback = asks_in_census(), {r["cid"]: r for f in FEEDBACK for r in json.loads(Path(f).read_text())["rows"]}
    missing = [(c, k) for c in asks for k in [(a, n) for a in ARMS for n in range(1, SAMPLES + 1)] if k not in outputs[c]]
    if missing:
        sys.exit(f"{len(missing)} outputs missing, e.g. {missing[:3]}")
    seal, folders = {}, [Path(out_dir) / "m1", Path(out_dir) / "m2"]
    per_pr = defaultdict(list)
    for cid in asks:
        keys = [(a, n) for a in ARMS for n in range(1, SAMPLES + 1)]
        random.Random(f"{SEED}:{cid}").shuffle(keys)
        labels = {f"O{i}": k for i, k in enumerate(keys, 1)}
        seal[cid] = {label: list(k) for label, k in labels.items()}
        row = feedback[cid]
        reply = feedback.get(row.get("reply_to_cid") or "")
        per_pr[asks[cid]["pr"]].append({
            "ask_id": cid, "path": row["path"], "code_at_comment": row.get("diff_hunk") or "", "comment": row["body"],
            "in_reply_to": reply["body"] if reply else None,
            "outputs": {label: change(outputs[cid][k]["content"]) for label, k in labels.items()}})
    (HERE / "blinding_SEALED.json").write_text(json.dumps(seal, indent=1) + "\n")
    rubric = (HERE / "matcher_rubric.md").read_text()
    for folder in folders:
        (folder / "tmp").mkdir(parents=True, exist_ok=True)
        (folder / "matcher_rubric.md").write_text(rubric)
        for pr, rows in per_pr.items():
            (folder / f"asks_pr{pr}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    for folder in folders:
        print(json.dumps({"folder": str(folder.resolve()), "prompt": MATCHER_PROMPT.format(folder=folder.resolve())}))


MATCHER_PROMPT = """You are a blind judge in a research study on code review of Mathlib (Lean 4) pull requests.

Your working folder is:
{folder}

Rules:
- Read `matcher_rubric.md` in that folder first and follow it exactly.
- Read only files inside that folder. Do not open, list or search anything outside it, do not use git, and do not use the web.
- If you need scratch files (for example a helper script), put them in the folder's `tmp/` subfolder.
- Judge every output for every ask yourself, by reading it. A script may help you assemble the JSON, but the judgments must be yours.
- Write `matches.json` in the working folder, in the format the rubric gives.

When done, reply with what the rubric asks for: the counts of `reached` and `partial` over all outputs."""


def unblind(m1: str, m2: str) -> None:
    seal = json.loads((HERE / "blinding_SEALED.json").read_text())
    table = {}
    for name, path in (("1", m1), ("2", m2)):
        rows = {r["ask_id"]: r for r in json.loads(Path(path).read_text())["asks"]}
        if set(rows) != set(seal):
            sys.exit(f"matcher {name}: asks differ from the seal")
        table[name] = {cid: {f"{arm}{n}": rows[cid][label] for label, (arm, n) in labels.items()}
                       for cid, labels in seal.items()}
    (HERE / "unblinded.json").write_text(json.dumps(table, indent=1) + "\n")
    print("unblinded", {m: sum(v == "reached" for row in t.values() for v in row.values()) for m, t in table.items()})


def review_reach(matcher: str) -> dict:
    """Stage D's three reps: sessions reaching each in-census ask, per condition (Result 7's tables)."""
    reach = defaultdict(lambda: defaultdict(int))
    for rnd in ("D1", "D23"):
        for tag in ("val", "post"):
            u = json.loads((CEILING / f"match_{rnd}_{tag}" / "unblinded.json").read_text())[matcher]["table"]
            for cid, row in u.items():
                for session, value in row.items():
                    if session[:2] in ("DX", "DE", "DP"):
                        reach[cid][session[:2]] += value == "reached"
    return reach


def read() -> None:
    table = json.loads((HERE / "unblinded.json").read_text())
    asks = asks_in_census()
    groups = lambda reach: ([c for c in asks if reach[c]["DP"] <= 1],
                            [c for c in asks if reach[c]["DP"] - reach[c]["DE"] >= 2])
    # The groups are fixed from Result 7's matcher 1 tables (README); matcher 2's own are reported beside.
    missed, gained = groups(review_reach("1"))
    print("groups (matcher 1, fixed):", len(missed), "misses,", len(gained), "gains; matcher 2's own:",
          [len(g) for g in groups(review_reach("2"))])
    for m in ("1", "2"):
        passed = {cid: {arm: sum(table[m][cid][f"{arm}{n}"] == "reached" for n in range(1, SAMPLES + 1)) >= 2
                        for arm in ARMS} for cid in asks}
        reach = review_reach(m)
        print(f"\n===== matcher {m} =====")
        print("asks passing (>= 2 of 3 samples reached), of 39:", {arm: sum(p[arm] for p in passed.values()) for arm in ARMS})
        for name, group in (("DP's misses (DP reached in <= 1 of 3 reps)", missed),
                            ("DP's gains (DP reached in >= 2 more reps than DE)", gained)):
            u = [c for c in group if passed[c]["UX"]]
            s = [c for c in group if not passed[c]["UX"] and passed[c]["AX"]]
            f = [c for c in group if not passed[c]["UX"] and not passed[c]["AX"]]
            print(f"{name}: {len(group)} asks")
            print(f"  u, UX pass {len(u)} {u}\n  s, UX fail and AX pass {len(s)} {s}\n  f, UX and AX fail {len(f)} {f}")
            print("  U pass", [c for c in group if passed[c]["U"]], " A pass", [c for c in group if passed[c]["A"]],
                  " F pass", [c for c in group if passed[c]["F"]])
        for a, b in (("U", "UX"), ("A", "AX"), ("U", "A"), ("UX", "AX"), ("F", "A")):
            gain = sum(passed[c][b] and not passed[c][a] for c in asks)
            loss = sum(passed[c][a] and not passed[c][b] for c in asks)
            print(f"{b} against {a}: +{gain} / -{loss} asks")
        for arm, cond in (("U", "DE"), ("UX", "DP"), ("A", "DE"), ("AX", "DP")):
            both = sum(passed[c][arm] and reach[c][cond] >= 2 for c in asks)
            only_arm = sum(passed[c][arm] and reach[c][cond] < 2 for c in asks)
            only_review = sum(not passed[c][arm] and reach[c][cond] >= 2 for c in asks)
            neither = sum(not passed[c][arm] and reach[c][cond] < 2 for c in asks)
            print(f"{arm} pass x {cond} reached >= 2 of 3: both {both}, ladder only {only_arm}, "
                  f"review only {only_review}, neither {neither}")


if __name__ == "__main__":
    command, args = sys.argv[1], sys.argv[2:]
    {"build": build, "run": run, "match-inputs": match_inputs, "unblind": unblind, "read": read}[command](*args)
