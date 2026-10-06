"""Stage H: which pinpointed departures would a maintainer raise? Five decision designs over one
convention record, compared on the probe PRs' stage G candidates for ten rules. Calls no model.

The record, per rule: the guarded rule (`rules.json`), its positives (census asks filed under it by
reader A, comment and code) and its negatives (places the same blind pinpointer flags under it on a
seeded census sample where no maintainer asked in round 1), and a rate index. Every part of it comes
from census PRs, which are disjoint from the probe's.

usage (repo root):
  python3 <this file> mined <census release dir> <census bodies.json>   label the census sample's places, write the rates
  python3 <this file> folders <design> <census bodies.json> <scratch>   decider folders for a design, two halves
  python3 <this file> rate                                              design R, decided by the index alone
  python3 <this file> score                                             every design against the probe's asks
"""
import hashlib
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
CENSUS = Path("results/pr_review_v5/adjudications/conventions-census-v1")
EVENTS = Path("results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/events.jsonl")
FEEDBACK = {"val": Path("results/pr_review_v5/probes/model-gap-val-small12/feedback.json"),
            "post": Path("results/pr_review_v5/probes/postcutoff-2026-09-29/feedback.json")}
RELEASES = {"val": Path("inputs/pr_review_v4/releases/val-2025-06-2026-03-v1"),
            "post": Path("inputs/probes/probe-2026-07-08-v1")}
SEED = "stage-h-2026-10-06"
RULES = json.loads((HERE / "stage_h_rules.json").read_text())["rules"]
HALVES = [[30641, 29842, 41930, 32875, 42814], [30458, 28649, 42184, 43167, 34091]]
DESIGNS = ("judge", "examples", "examples_rate", "retrieve")
N_CENSUS = 973          # val1000's accepted PRs: the population the census asks were read on
rules = {r["id"]: r for r in json.loads((HERE / "rules.json").read_text())}
principle = {e["id"]: e["principle"] for e in json.loads((CENSUS / "reader_A/codebook.json").read_text())}
key = lambda *parts: hashlib.sha256("\0".join((SEED,) + tuple(map(str, parts))).encode()).hexdigest()


def names_in(text):
    return [n for n in re.findall(r"[A-Za-z_][\w.'!?₀-₉]*", text) if len(n) > 3]


def at_place(item, path, hunk):
    """The mechanical test of stage G: an ask with no code is at its place wherever its rule fires;
    otherwise the item names the ask's file and a declaration whose name occurs in the ask's code."""
    if not hunk or not path:
        return True
    return item["file"] == path and any(n in hunk or n.split(".")[-1] in hunk for n in names_in(item["declaration"]))


def hunks(diff):
    files, cur_file, cur = {}, None, None
    for line in diff.split("\n"):
        if line.startswith("diff --git "):
            cur_file, cur = line.split(" b/", 1)[-1], None
            files.setdefault(cur_file, [])
        elif line.startswith("@@") and cur_file is not None:
            cur = [line]
            files[cur_file].append(cur)
        elif cur is not None:
            cur.append(line)
    return {f: ["\n".join(h) for h in hs] for f, hs in files.items()}


def excerpt(diff, item, limit=1400):
    """The diff hunk around the item's declaration, as a reviewer would see it."""
    if item["file"] == "PR":
        return "(the PR's title or description)"
    keys = [n.split(".")[-1] for n in names_in(item["declaration"])]
    for h in hunks(diff).get(item["file"], []):
        found = [h.find(k) for k in keys if k in h]
        if found:
            start = max(0, min(found) - 400)
            return h[start:start + limit]
    hs = hunks(diff).get(item["file"], [])
    return hs[0][:limit] if hs else "(no hunk of this file names the declaration)"


def episodes(release):
    return {e["pr_number"]: e for e in map(json.loads, (Path(release) / "input/episodes.jsonl").read_text().splitlines())}


# ---------------------------------------------------------------- the probe side (fixed, from stage G)

def probe_candidates():
    """Stage G's candidates for the ten rules on the ten PRs, each with its code and whether it sits
    at a maintainer's in-census ask filed under the same rule (the score's truth; never shown)."""
    asks = json.loads((HERE / "briefs_exact.json").read_text())["asks"]
    fb = {r["cid"]: r for path in FEEDBACK.values() for r in json.loads(path.read_text())["rows"]}
    eps = {**episodes(RELEASES["val"]), **episodes(RELEASES["post"])}
    out = []
    for pr in HALVES[0] + HALVES[1]:
        prasks = [(c, a) for c, a in asks.items() if a["pr"] == pr and a["in_census"]]
        for n, it in enumerate(json.loads((HERE / f"pinpoints/pr{pr}.json").read_text())):
            if it["id"] not in RULES:
                continue
            hit = [c for c, a in prasks if it["id"] in set(a["r1"]) | set(a["r2"])
                   and at_place(it, fb[c].get("path"), fb[c].get("diff_hunk") or "")]
            out.append({"pr": pr, "n": n, **it, "code": excerpt(eps[pr]["diff"], it),
                        "title": eps[pr]["title"]["text"] if isinstance(eps[pr]["title"], dict) else eps[pr]["title"],
                        "asked": bool(hit), "asks": hit})
    for c in out:
        c["cid"] = "c" + key("cand", c["pr"], c["n"])[:6]
    return out


# ---------------------------------------------------------------- the record (census only)

def positives(bodies):
    body = {r["cid"]: r for r in json.loads(Path(bodies).read_text())["rows"] if r["set"] in ("val1000", "outside_years")}
    out = defaultdict(list)
    for f in sorted(CENSUS.glob("reader_A/labels_*.jsonl")):
        for l in map(json.loads, f.open(encoding="utf-8")):
            for p in (l["principle_id"], l.get("second_principle_id") or ""):
                if p in RULES and l["cid"] in body:
                    r = body[l["cid"]]
                    out[p].append({"id": "pos:" + l["cid"], "pr": r["pr"], "path": r["path"] or "PR",
                                   "comment": r["body"][:700], "code": (r["diff_hunk"] or "(a comment on the PR as a whole)")[-900:]})
    return out


def mined(release, bodies):
    sample = json.loads((HERE / "census_sample.json").read_text())
    prs = [p["pr"] for p in sample["prs"]]
    ev = {r["cid"]: r for r in map(json.loads, EVENTS.open(encoding="utf-8"))}
    body = {r["cid"]: r for r in json.loads(Path(bodies).read_text())["rows"] if r["set"] == "val1000"}
    labels = {l["cid"]: l for f in sorted(CENSUS.glob("reader_A/labels_b*.jsonl")) for l in map(json.loads, f.open())}
    eps = episodes(release)
    items, fires = [], Counter()
    for pr in prs:
        prasks = [c for c in labels if int(ev[c]["pr"]) == pr]
        for n, it in enumerate(json.loads((HERE / f"census_pinpoints/pr{pr}.json").read_text())):
            if it["id"] not in RULES:
                continue
            fires[it["id"]] += 1
            hit = [c for c in prasks if it["id"] in (labels[c]["principle_id"], labels[c].get("second_principle_id") or "")
                   and at_place(it, body[c].get("path"), body[c].get("diff_hunk") or "")]
            items.append({"id": f"{'pos' if hit else 'neg'}:{pr}:{n}", "pr": pr, "rule": it["id"], "status": it["status"],
                          "file": it["file"], "declaration": it["declaration"], "fact": it["fact"],
                          "code": excerpt(eps[pr]["diff"], it), "asked": bool(hit), "asks": hit})
    census_asks = Counter()
    for c, l in labels.items():
        for p in {l["principle_id"], l.get("second_principle_id") or ""}:
            if p in RULES:
                census_asks[p] += 1
    rates = {r: {"flagged_in_sample": fires[r], "asked_in_sample": sum(i["asked"] for i in items if i["rule"] == r),
                 "census_asks": census_asks[r],
                 "flagged_per_pr": round(fires[r] / len(prs), 2),
                 "index": round(census_asks[r] / (N_CENSUS * (fires[r] + 0.5) / len(prs)), 4)} for r in RULES}
    (HERE / "census_mined.json").write_text(json.dumps({"prs": prs, "items": items}, indent=1, ensure_ascii=False) + "\n")
    (HERE / "census_rates.json").write_text(json.dumps(rates, indent=1) + "\n")
    print(f"{len(items)} places for the ten rules on {len(prs)} census PRs; {sum(i['asked'] for i in items)} at an ask")
    for r in sorted(RULES, key=lambda r: -rates[r]["index"]):
        print(f"  {r}: flagged {rates[r]['flagged_in_sample']:3d} ({rates[r]['flagged_per_pr']}/PR), asked in sample "
              f"{rates[r]['asked_in_sample']}, census asks {rates[r]['census_asks']:3d}, index {rates[r]['index']}")


# ---------------------------------------------------------------- decider folders

LEAD = """# Would a maintainer raise this? (decider rubric, design `{design}`, fixed 2026-10-06 before any decision)

You are helping a study of Mathlib code review. A blind pass read each pull request in `candidates.md`
against conventions Mathlib's maintainers hold, and listed places where a convention's situation
occurs. Most such places are never raised in review: maintainers hold many conventions and ask for
a few of them. Your task is to say, for each candidate, whether a Mathlib maintainer reviewing that
pull request in its first round would ask for the change the convention calls for, **at that
place**.

Read only the files in your working directory. Do not look anything up and run nothing.
"""
DESIGN_TEXT = {
    "judge": """
Decide from the candidate, its code and the rule alone.
""",
    "examples": """
`examples.md` holds, for each rule, examples from other pull requests: **asked**, places where a
maintainer asked for it (their comment and the code), and **not asked**, places the same blind pass
flagged under the rule where no maintainer asked. Read the rule's examples before deciding its
candidates, and decide by which side a candidate resembles.
""",
    "examples_rate": """
`examples.md` holds, for each rule, examples from other pull requests: **asked**, places where a
maintainer asked for it (their comment and the code), and **not asked**, places the same blind pass
flagged under the rule where no maintainer asked. It also gives each rule's measured rate: how often
the pass flags the rule's situation, and how often maintainers asked under it, over the census of
pull requests. Read the rule's rate and examples before deciding its candidates. Use the rate as
the prior, and the examples to judge which side a candidate resembles.
""",
    "retrieve": """
`examples/` holds one file per rule: every example the study has from other pull requests, each
with an id, its file path and code: **asked** examples, where a maintainer asked for the rule
(with their comment), and **not asked** examples, places the same blind pass flagged under the rule
where no maintainer asked. For **each** candidate, before deciding, open its rule's file, find the
asked and not-asked examples most like the candidate (the same kind of declaration, the same area of
the library, the same shape of code), and decide by which side the most similar ones fall. Cite the
ids you relied on in `basis`.
""",
}
TAIL = """
## Output

Write `decisions.json` in your working directory: a JSON list with one object per candidate in
`candidates.md`, with exactly these keys:
- `cid`: the candidate's id;
- `raise`: `true` if a maintainer would ask for it at that place in the first round, else `false`;
- `p`: your probability, from 0 to 1, that a maintainer would;
- `basis`: at most 25 words.

Check that the file parses, has every cid of `candidates.md` exactly once, and that every `p` is
between 0 and 1. Then reply with one line: the number of candidates and how many you would raise.
"""
PROMPT = """You are a decider in a research study of Mathlib code review. Your working directory is `{dir}`.

Read `decider_rubric.md` in that directory and do what it says. Its inputs are in the same directory.

Rules, which the study depends on:
- Read only files inside your working directory. Do not open, list or search anything outside it, do not run git, and do not use web search or web fetch.
- Put any temporary file in `tmp/` inside your working directory.
- The decisions must be yours, made by reading each candidate. A script may check your JSON, but must not decide.

When done, reply with one line: the number of candidates and how many you would raise."""


def rule_block(r):
    x = rules[r]
    return (f"**Convention:** {principle[r]}\n- Trigger: {x['trigger']}\n- Preferred form: {x['required']}\n"
            f"- How to tell a departure (`{x['check_kind']}`): {x['check']}\n- Not when: {x['not_when'] or 'no exception recorded'}\n")


def example_text(e, asked):
    head = f"`{e['id']}` ({e.get('path') or e.get('file')})"
    if asked:
        return f"- **asked** {head}\n  The maintainer's comment: {' '.join(e['comment'].split())[:500]}\n```\n{e['code']}\n```\n"
    return (f"- **not asked** {head}, `{e['declaration']}`: {e['fact']}\n```\n{e['code']}\n```\n")


def folders(design, bodies, scratch):
    assert design in DESIGNS, design
    cands = probe_candidates()
    pos = positives(bodies)
    neg = defaultdict(list)
    for i in json.loads((HERE / "census_mined.json").read_text())["items"]:
        if not i["asked"]:              # an asked mined place is already among the census positives
            neg[i["rule"]].append(i)
    rates = json.loads((HERE / "census_rates.json").read_text())
    for h, prs in enumerate(HALVES, 1):
        d = Path(scratch) / design / f"half{h}"
        if d.exists():
            shutil.rmtree(d)
        (d / "tmp").mkdir(parents=True)
        mine = sorted((c for c in cands if c["pr"] in prs), key=lambda c: c["cid"])
        used = sorted({c["id"] for c in mine})
        parts = [f"# {len(mine)} candidates on {len(prs)} pull requests\n\n## The rules\n"]
        parts += [f"\n### {r}\n\n{rule_block(r)}" for r in used]
        parts.append("\n## The candidates\n")
        for c in mine:
            parts.append(f"\n### {c['cid']} (rule {c['id']})\n\nPull request: {c['title']}\n\n`{c['file']}`, `{c['declaration']}`: "
                         f"{c['fact']} ({'the pass judged by reading that the code departs' if c['status'] == 'departs' else 'the pass could not decide without a check'})\n```\n{c['code']}\n```\n")
        (d / "candidates.md").write_text("".join(parts))
        if design in ("examples", "examples_rate"):
            ex = [f"# Examples from other pull requests, by rule\n"]
            for r in used:
                p = sorted(pos[r], key=lambda e: key("pos", r, e["id"]))[:4]
                n = sorted(neg[r], key=lambda e: key("neg", r, e["id"]))[:4]
                ex.append(f"\n## {r}\n\n{principle[r]}\n")
                if design == "examples_rate":
                    x = rates[r]
                    ex.append(f"\n**Rate.** On a sample of 16 census pull requests the pass flagged this rule's situation at "
                              f"{x['flagged_in_sample']} places ({x['flagged_per_pr']} a pull request); maintainers asked under it "
                              f"{x['census_asks']} times over the 973 census pull requests, about one ask per "
                              f"{round(1 / max(x['index'], 1e-6)):d} flagged places.\n")
                ex.append(f"\n### Asked ({len(p)} of {len(pos[r])})\n\n" + "".join(example_text(e, True) for e in p))
                ex.append(f"\n### Not asked ({len(n)} of {len(neg[r])})\n\n" + "".join(example_text(e, False) for e in n))
            (d / "examples.md").write_text("".join(ex))
        if design == "retrieve":
            (d / "examples").mkdir()
            for r in used:
                p = sorted(pos[r], key=lambda e: key("pos", r, e["id"]))[:30]
                (d / "examples" / f"{r}.md").write_text(
                    f"# {r}: {principle[r]}\n\n## Asked ({len(p)} of {len(pos[r])})\n\n" + "".join(example_text(e, True) for e in p)
                    + f"\n## Not asked ({len(neg[r])})\n\n" + "".join(example_text(e, False) for e in neg[r]))
        (d / "decider_rubric.md").write_text(LEAD.format(design=design) + DESIGN_TEXT[design] + TAIL)
        print(json.dumps({"folder": str(d.resolve()), "description": f"Decider {design} half{h}",
                          "prompt": PROMPT.format(dir=d.resolve())}))


# ---------------------------------------------------------------- design R and the score

def rate_design():
    """Design R: no model. Per PR, raise the three candidates whose rule has the highest index
    (ties: decided-by-reading first, then the pass's order)."""
    cands = probe_candidates()
    index = {r: v["index"] for r, v in json.loads((HERE / "census_rates.json").read_text()).items()}
    out = []
    for pr in HALVES[0] + HALVES[1]:
        mine = sorted((c for c in cands if c["pr"] == pr), key=lambda c: (-index[c["id"]], c["status"] != "departs", c["n"]))
        out += [{"cid": c["cid"], "raise": k < 3, "p": index[c["id"]], "basis": "rule index"} for k, c in enumerate(mine)]
    (HERE / "stage_h_decisions").mkdir(exist_ok=True)
    (HERE / "stage_h_decisions/rate.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"design rate: raises {sum(d['raise'] for d in out)} of {len(out)}")


def score():
    cands = {c["cid"]: c for c in probe_candidates()}
    total, asked = len(cands), sum(c["asked"] for c in cands.values())
    asks = {a for c in cands.values() for a in c["asks"]}
    print(f"{total} candidates on 10 PRs, {asked} at an ask ({len(asks)} distinct asks); base precision {asked / total:.3f}")
    print(f"{'design':15} {'raised':>6} {'a PR':>5} {'at ask':>6} {'asks':>5} {'precision':>9} {'recall':>6}  reading")
    order = {}
    for pr in HALVES[0] + HALVES[1]:  # the pass's own order, departs first: what the pinpointer alone ranks
        mine = sorted((c for c in cands.values() if c["pr"] == pr), key=lambda c: (c["status"] != "departs", c["n"]))
        order.update({c["cid"]: k < 3 for k, c in enumerate(mine)})
    rows = [("all (stage G)", {c: True for c in cands}), ("exact (oracle)", {c: cands[c]["asked"] for c in cands}),
            ("order (base)", order)]
    for f in sorted((HERE / "stage_h_decisions").glob("*.json")):
        got = {d["cid"]: bool(d["raise"]) for d in json.loads(f.read_text())}
        missing = set(cands) - set(got)
        if missing:
            print(f"{f.stem}: {len(missing)} candidates undecided, read as not raised")
        rows.append((f.stem, {c: got.get(c, False) for c in cands}))
    for name, raised in rows:
        r = [c for c in cands if raised[c]]
        hit = [c for c in r if cands[c]["asked"]]
        covered = {a for c in hit for a in cands[c]["asks"]}
        prec, rec = (len(hit) / len(r) if r else 0.0), len(hit) / asked
        reading = ("strong" if rec >= 8 / 12 and prec >= 0.35 else "carry to sessions" if rec >= 6 / 12 and prec >= 0.25
                   else "below the bar") if name not in ("all (stage G)", "exact (oracle)", "order (base)") else ""
        print(f"{name:15} {len(r):6d} {len(r) / 10:5.1f} {len(hit):6d} {len(covered):5d} {prec:9.3f} {rec:6.3f}  {reading}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "mined":
        mined(sys.argv[2], sys.argv[3])
    elif cmd == "folders":
        folders(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "rate":
        rate_design()
    elif cmd == "score":
        score()
    elif cmd == "probe":
        cs = probe_candidates()
        print(len(cs), "candidates;", sum(c["asked"] for c in cs), "at an ask;", Counter(c["pr"] for c in cs))
        print("per half:", [sum(c["pr"] in h for c in cs) for h in HALVES])
        c = next(c for c in cs if c["asked"])
        print(json.dumps({k: (v[:300] if isinstance(v, str) else v) for k, v in c.items()}, ensure_ascii=False, indent=1))
