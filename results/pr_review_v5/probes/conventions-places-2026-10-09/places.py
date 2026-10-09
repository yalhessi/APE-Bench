"""The places test: does a convention's question, asked at every changed place of a PR, pick out the
places where maintainers asked? Pre-registered in this directory's README before any call.

Per probe PR: its changed declaration segments (`segments`) plus one place for the PR as a whole. For
each place, each of the PR's exact census entries (exact pairs; the ones behind its maintainers'
asks) and five of stage F's blind picks that sit behind no ask on the PR (decoy pairs), one turn in
the ladder's U form with a stated confidence. Single turn, no tools.

  build      prompts (uncommitted, large) and items.json (pairs, asked flags, digests)
  run <base_url> <model> [workers]    the calls, resumable, into outputs.jsonl and reasoning.jsonl
  read       the pre-registered reading

usage (repo root, PYTHONPATH=$PWD:$PWD/src): ape/bin/python <this file> <command> [args]
"""
import hashlib
import importlib.util
import json
import random
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from src.mathlib_review.analysis import probes
from src.mathlib_review.io import jsonl_rows

HERE = Path(__file__).parent
CEILING = HERE.parent / "conventions-ceiling-2026-10-04"
spec = importlib.util.spec_from_file_location("ladder", HERE.parent / "conventions-ladder-2026-10-08" / "ladder.py")
ladder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ladder)

PROMPTS = HERE / "prompts"
SEED = "conventions-places-2026-10-09"
SAMPLES = {"exact": 2, "decoy": 1}
DECOYS_PER_PR = 5
MAX_TOKENS = 65536
#: A segment starts at a declaration header or a top-level command, so a docstring (`/--`) opens the
#: segment of the declaration it documents.
START = re.compile(
    r"^\s*(/--|/-!|@\[|import\b|variable\b|section\b|namespace\b|end\b|open\b|universe\b|"
    r"((private|protected|noncomputable|nonrec|scoped|unsafe|partial)\s+)*"
    r"(theorem|lemma|def|instance|abbrev|structure|class|inductive|alias|example|irreducible_def)\b)")
ASK = ("Here is a convention Mathlib's maintainers apply:\n\n- {sentence}\n\nDoes the code at this place "
       "conform to this convention? If it departs from it, write the change the convention calls for.")
FORM = ("Answer in exactly this form and nothing else:\nVERDICT: departs | conforms\n"
        "CONFIDENCE: <a number from 0 to 100: how likely it is that the code at this place departs from this convention>\n"
        "CHANGE: <the change, as code or in one or two sentences; `none` if the code conforms>\n"
        "WHY: <one sentence>")


def segments(diff: str) -> list:
    """The diff's changed segments: (path, lines). A hunk is split where a line (without its diff
    marker) opens a declaration or a top-level command; segments without a `+` or `-` line are
    dropped. A preceding docstring stays with its declaration."""
    out, path, current = [], None, []
    state = {"kind": "empty"}  # empty | lead (docstring/attributes so far) | body

    def flush():
        if current and any(l[:1] in "+-" for l in current):
            out.append((path, list(current)))
        current.clear()
        state["kind"] = "empty"

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            flush()
            path = line.split(" b/", 1)[-1]
            continue
        if line.startswith(("+++ ", "--- ", "index ", "new file", "deleted file", "similarity", "rename ", "\\ No newline")):
            continue
        if line.startswith("@@"):
            flush()
            continue
        body = (line[1:] if line[:1] in "+- " else line).lstrip()
        if START.match(body):
            prefix = body.startswith(("/--", "@["))
            if state["kind"] == "body":
                flush()
            # a docstring or attribute leads its declaration: the header that follows joins the lead
            state["kind"] = "lead" if prefix and state["kind"] != "lead" else ("lead" if prefix else "body")
        elif state["kind"] == "empty":
            state["kind"] = "body"  # lines continuing a declaration that began above the hunk
        current.append(line)
    flush()
    return out


def place_text(path: str, lines: list) -> str:
    return f"`{path}`, the changed code below (lines starting `+` are added, `-` removed):\n\n```\n" + "\n".join(lines) + "\n```"


def build() -> None:
    asks = json.loads((CEILING / "briefs_exact.json").read_text())["asks"]
    exact = json.loads((CEILING / "briefs_exact.json").read_text())["prs"]
    applicable = json.loads((CEILING / "briefs_applicable.json").read_text())["prs"]
    feedback = {r["cid"]: r for f in ladder.FEEDBACK for r in json.loads(Path(f).read_text())["rows"]}
    episodes = {}
    for path in ladder.SETS.values():
        s = probes.load_probe_set(Path(path))
        for e in jsonl_rows(s.release / "input/episodes.jsonl"):
            episodes[e["pr_number"]] = e
    principle = {e["id"]: e["principle"] for e in json.loads(ladder.CODEBOOK.read_text())}
    PROMPTS.mkdir(exist_ok=True)
    items, unplaced = [], []
    for pr in sorted({a["pr"] for a in asks.values() if a["in_census"]}):
        episode = episodes[pr]
        segs = segments(episode["diff"])
        places = [{"place": f"s{i:02d}", "path": p, "lines": ls} for i, (p, ls) in enumerate(segs)]
        places.append({"place": "pr", "path": None, "lines": None})
        # which place each in-census ask sits at, by its commented line (the hunk's last line)
        at = defaultdict(set)
        for cid, a in asks.items():
            if a["pr"] != pr or not a["in_census"]:
                continue
            row = feedback[cid]
            if row["kind"] == "issue_comment":
                target = "pr"
            else:
                last = next((l for l in reversed((row.get("diff_hunk") or "").splitlines()) if l.strip()), "")
                target = None if not last.strip() else next(
                    (p["place"] for p in places[:-1] if p["path"] == row["path"]
                     and any(l.rstrip() == last.rstrip() for l in p["lines"])), None)
            if target is None:
                unplaced.append(cid)
                continue
            for entry in a["r1"]:
                at[(entry, target)].add(cid)
        behind = {e for a in asks.values() if a["pr"] == pr for e in a["r1"] + a["r2"]}
        decoys = sorted(set(applicable.get(str(pr), [])) - behind)
        random.Random(f"{SEED}:{pr}").shuffle(decoys)
        entries = [(e, "exact") for e in sorted(set(exact.get(str(pr), [])))] + [(e, "decoy") for e in decoys[:DECOYS_PER_PR]]
        head_pr = probes.pr_markdown(episode).rstrip()
        for p in places:
            where = "the pull request as a whole." if p["place"] == "pr" else place_text(p["path"], p["lines"])
            head = ladder.HEAD.format(pr=head_pr, diff=episode["diff"].rstrip(), place=where)
            for entry, kind in entries:
                text = head + "\n" + ASK.format(sentence=principle[entry]) + "\n\n" + FORM + "\n"
                name = f"pr{pr}__{p['place']}__{entry}"
                (PROMPTS / f"{name}.txt").write_text(text)
                items.append({"name": name, "pr": pr, "place": p["place"], "path": p["path"], "entry": entry, "kind": kind,
                              "asked": sorted(at.get((entry, p["place"]), [])), "chars": len(text),
                              "sha256": ladder.digest(text)})
    (HERE / "items.json").write_text(json.dumps({"seed": SEED, "samples": SAMPLES, "max_tokens": MAX_TOKENS,
                                                "unplaced": sorted(unplaced), "items": items}, indent=1) + "\n")
    calls = sum(SAMPLES[i["kind"]] for i in items)
    print(f"{len(items)} pairs ({sum(i['kind'] == 'exact' for i in items)} exact, {sum(i['kind'] == 'decoy' for i in items)} decoy), "
          f"{sum(bool(i['asked']) for i in items)} asked; {calls} calls; unplaced asks {sorted(unplaced)}")


def run(base: str, model: str, workers: str = "24") -> None:
    import concurrent.futures, threading, time
    meta = json.loads((HERE / "items.json").read_text())
    out, thought = HERE / "outputs.jsonl", HERE / "reasoning.jsonl"
    done = {(r["name"], r["sample"]) for r in map(json.loads, out.open())} if out.exists() else set()
    todo = []
    for item in meta["items"]:
        text = (PROMPTS / f"{item['name']}.txt").read_text()
        if ladder.digest(text) != item["sha256"]:
            sys.exit(f"{item['name']}: the prompt is not the pre-registered bytes")
        todo += [(item, text, n) for n in range(1, meta["samples"][item["kind"]] + 1) if (item["name"], n) not in done]
    # asked pairs first, then exact, then decoys: a run cut short keeps the discrimination's core
    todo.sort(key=lambda j: (not j[0]["asked"], j[0]["kind"] != "exact", j[2]))
    lock = threading.Lock()
    print(f"{len(done)} done, {len(todo)} to run", flush=True)

    def one(job):
        item, text, n = job
        started = time.time()
        r = ladder.chat(base, {"model": model, "messages": [{"role": "user", "content": text}],
                               "reasoning_effort": "high", "max_tokens": meta["max_tokens"]})
        message, usage = r["choices"][0]["message"], r.get("usage") or {}
        row = {"name": item["name"], "sample": n, "content": message.get("content") or "",
               "finish_reason": r["choices"][0].get("finish_reason"), "prompt_tokens": usage.get("prompt_tokens"),
               "completion_tokens": usage.get("completion_tokens"), "seconds": round(time.time() - started, 1)}
        with lock:
            with out.open("a") as f:
                f.write(json.dumps(row) + "\n")
            with thought.open("a") as f:
                f.write(json.dumps({"name": item["name"], "sample": n,
                                    "reasoning": message.get("reasoning_content") or message.get("reasoning") or ""}) + "\n")
        return row

    finished = 0
    with concurrent.futures.ThreadPoolExecutor(int(workers)) as pool:
        for future in concurrent.futures.as_completed([pool.submit(one, j) for j in todo]):
            row = future.result()
            finished += 1
            if finished % 50 == 0 or finished == len(todo):
                print(f"{time.strftime('%H:%M:%S')} {finished}/{len(todo)} (last {row['name']} "
                      f"{row['completion_tokens']} tokens, {row['seconds']} s)", flush=True)


def parse(content: str) -> tuple:
    verdict = re.search(r"VERDICT:\s*(departs|conforms)", content, re.I)
    confidence = re.search(r"CONFIDENCE:\s*(\d+(?:\.\d+)?)", content)
    return (verdict.group(1).lower() if verdict else None,
            min(100.0, float(confidence.group(1))) if confidence else None)


def auc(positive: list, negative: list) -> float:
    pairs = [(p > n) + 0.5 * (p == n) for p in positive for n in negative]
    return sum(pairs) / len(pairs) if pairs else float("nan")


def read() -> None:
    meta = json.loads((HERE / "items.json").read_text())
    rows = defaultdict(list)
    for r in map(json.loads, (HERE / "outputs.jsonl").open()):
        rows[r["name"]].append(r)
    stats = defaultdict(list)
    for item in meta["items"]:
        got = [parse(r["content"]) for r in rows.get(item["name"], [])]
        if not got:
            continue
        departs = sum(v == "departs" for v, _ in got) / len(got)
        conf = [c for _, c in got if c is not None]
        group = "asked" if item["asked"] else ("unasked" if item["kind"] == "exact" else "decoy")
        stats[group].append({"item": item, "departs": departs, "conf": statistics.mean(conf) if conf else None,
                             "unparsed": sum(v is None for v, _ in got), "truncated": sum(r["finish_reason"] == "length" for r in rows[item["name"]])})
    for group in ("asked", "unasked", "decoy"):
        g = stats[group]
        if g:
            print(f"{group:8} pairs {len(g):4}  departs rate {statistics.mean(s['departs'] for s in g):.2f}  "
                  f"unparsed {sum(s['unparsed'] for s in g)}  truncated {sum(s['truncated'] for s in g)}")
    pos = [s["conf"] for s in stats["asked"] if s["conf"] is not None]
    for name, neg in (("asked vs unasked (exact)", stats["unasked"]), ("asked vs decoy", stats["decoy"])):
        n = [s["conf"] for s in neg if s["conf"] is not None]
        print(f"AUC of CONFIDENCE, {name}: {auc(pos, n):.3f}  (positives {len(pos)}, negatives {len(n)})")
    per_pr = defaultdict(lambda: {"places": set(), "decoy_departs": []})
    for s in stats["decoy"]:
        per_pr[s["item"]["pr"]]["places"].add(s["item"]["place"])
        per_pr[s["item"]["pr"]]["decoy_departs"].append(s["departs"])
    proj = [statistics.mean(v["decoy_departs"]) * len(v["places"]) * 25 for v in per_pr.values() if v["decoy_departs"]]
    if proj:
        print(f"projected filings a PR from stage F's 25 at every place (decoy departs rate x places x 25): "
              f"median {statistics.median(proj):.1f}, range {min(proj):.1f}-{max(proj):.1f}")
    # a capped engine: per PR, every pair (exact and decoy) ranked by stated confidence, ties by name
    ranked = defaultdict(list)
    for group in ("asked", "unasked", "decoy"):
        for s in stats[group]:
            ranked[s["item"]["pr"]].append((-(s["conf"] if s["conf"] is not None else -1), s["item"]["name"], group == "asked"))
    asked_total = sum(1 for s in stats["asked"])
    for k in (5, 10, 20):
        hit = sum(sum(a for _, _, a in sorted(v)[:k]) for v in ranked.values())
        print(f"capped at {k} a PR by confidence: {hit} of {asked_total} asked pairs kept ({hit / asked_total:.2f})")
    print("\nper exact entry: asked departs / unasked departs (pairs)")
    by_entry = defaultdict(lambda: {"asked": [], "unasked": []})
    for group in ("asked", "unasked"):
        for s in stats[group]:
            by_entry[(s["item"]["pr"], s["item"]["entry"])][group].append(s["departs"])
    for (pr, entry), d in sorted(by_entry.items()):
        a = f"{statistics.mean(d['asked']):.2f} ({len(d['asked'])})" if d["asked"] else "-"
        u = f"{statistics.mean(d['unasked']):.2f} ({len(d['unasked'])})" if d["unasked"] else "-"
        print(f"  pr{pr} {entry}: {a} / {u}")


if __name__ == "__main__":
    command, args = sys.argv[1], sys.argv[2:]
    {"build": build, "run": run, "read": read}[command](*args)
