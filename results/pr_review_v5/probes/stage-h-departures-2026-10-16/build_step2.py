"""Build step 2's items and packets (PROTOCOL.md, step 2). Packets go to scratch: they quote census asks.

usage (repo root): ape/bin/python <this file> <bodies.json> <scratch packet dir>
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))
from src.mathlib_review.io import jsonl_rows  # noqa: E402

HERE = Path(__file__).resolve().parent
C = Path("results/pr_review_v5/probes/conventions-ceiling-2026-10-04")
CENSUS = Path("results/pr_review_v5/adjudications/conventions-census-v1")
DRAW = Path("inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1/draw.json")
SEED, CAP, N = 20261018, 8, 60


def main() -> int:
    bodies = json.loads(Path(sys.argv[1]).read_text())
    bodies = {r["cid"]: r for r in (bodies if isinstance(bodies, list) else bodies["rows"]) if r["set"] == "val1000"}
    out_dir = Path(sys.argv[2]); out_dir.mkdir(parents=True, exist_ok=True)
    mined = json.loads((C / "census_mined.json").read_text())
    follow = {(r["pr"], r["file"], r["declaration"], r["rule"]): r for r in jsonl_rows(HERE / "follow.jsonl") if r["kind"] == "place"}
    rules = {r["id"]: r for r in json.loads((C / "rules.json").read_text())}
    book = {e["id"]: e for e in json.loads((CENSUS / "reader_A/codebook.json").read_text())}
    labels = [json.loads(l) for f in sorted(CENSUS.glob("reader_A/labels_b*.jsonl")) for l in f.open()]
    base = {a["pr_number"]: a["base_sha"] for a in json.loads(DRAW.read_text())["accepted"]}
    sixteen = {str(p) for p in mined["prs"]}
    rng = random.Random(SEED)
    examples = {}
    for rule in rules:
        pool = sorted(l["cid"] for l in labels if rule in (l["principle_id"], l.get("second_principle_id") or "")
                      and bodies.get(l["cid"], {}).get("pr") not in sixteen)
        examples[rule] = rng.sample(pool, min(2, len(pool)))
    located = [i for i in mined["items"] if not i["asked"]
               and follow.get((i["pr"], i["file"], i["declaration"], i["rule"]), {}).get("outcome") in ("unchanged", "changed", "gone")]
    by_rule = defaultdict(list)
    for i in located:
        by_rule[i["rule"]].append(i)
    pool = []
    for rule, items in sorted(by_rule.items()):
        pool += rng.sample(items, min(CAP, len(items)))
    sample = rng.sample(pool, min(N, len(pool)))
    chosen = [("open", i) for i in sample] + [("calibration", i) for i in mined["items"] if i["asked"]]
    rng.shuffle(chosen)
    key = []
    for n, (role, i) in enumerate(chosen, 1):
        item = f"H{n:03d}"
        r, e = rules[i["rule"]], book[i["rule"]]
        asks = "\n\n".join(f"> {bodies[c]['body'].strip()[:700]}" for c in examples[i["rule"]])
        packet = (f"# Item {item}\n\n**The rule ({i['rule']}).** {e['principle']}\n\n"
                  f"- Trigger: {r.get('trigger')}\n- Check: {r.get('check')}\n- Exception: {r.get('exception') or 'none stated'}\n\n"
                  f"**How maintainers state it (two asks under this rule, from other PRs):**\n\n{asks}\n\n"
                  f"**The place.** `{i['file']}`, `{i['declaration']}`. Library before the PR: base commit `{base[i['pr']]}`.\n\n"
                  f"**What the blind pass noted here:** {i['fact']}\n\n"
                  f"**The PR's code at review time, around the place:**\n\n```\n{i.get('code') or '(no excerpt)'}\n```\n")
        (out_dir / f"{item}.md").write_text(packet)
        key.append({"item": item, "role": role, "pr": i["pr"], "rule": i["rule"], "status": i["status"],
                    "file": i["file"], "declaration": i["declaration"],
                    "check_kind": r.get("check_kind"), "examples": examples[i["rule"]]})
    (HERE / "step2_items.jsonl").write_text("".join(json.dumps(k, ensure_ascii=False) + "\n" for k in key))
    print(len(key), "items;", sum(k["role"] == "calibration" for k in key), "calibration;",
          dict(sorted((r, sum(1 for k in key if k["rule"] == r and k["role"] == "open")) for r in rules if r in by_rule)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
