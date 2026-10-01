"""The mechanism table from both readers' labels.

Usage, from the repo root:
    python results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30/mechanisms.py

Reads labels/<split>.<reader>.jsonl (readers m1 and m2), joins each pair with the population file
for its set, class and family, and prints:
  1. per mechanism: pairs labelled by both readers, by one, and asks (distinct ask_ids) with the
     label from both readers -- the count the plan's ">= 5 asks" rule reads;
  2. the same split by reviewer family (Claude X1/X2 against gpt Grc1) and by set;
  3. reachable per ask, both readers;
  4. pair-level disagreement: pairs where the readers' label sets are disjoint.
Disagreement is reported, never averaged.
"""
import collections
import json
from pathlib import Path

HERE = Path(__file__).parent
POPULATION = Path("results/pr_review_v5/probes/phase0-carried-baseline-2026-09-30/phase1_population.json")
SPLIT_SET = {"post": "post", "val": "val", "dev_a": "dev", "dev_b": "dev"}
LABELS = ["never_attempted", "attempted_concluded_fine", "attempted_opposite", "verified_withheld", "filed_elsewhere",
          "try_it_not_tried", "knowledge_convention", "analogue_not_compared", "pr_level_or_history",
          "not_reachable_from_code", "ask_unclear"]


def load():
    pop = json.load(open(POPULATION))["sets"]
    rows = {}  # (split, ask, reviewer) -> {reader: row}
    for path in sorted((HERE / "labels").glob("*.jsonl")):
        split, reader = path.stem.split(".")
        for line in open(path):
            if not line.strip():
                continue
            r = json.loads(line)
            key = (split, r["ask_id"], r["reviewer"])
            rows.setdefault(key, {})[reader] = r
    out = []
    for (split, ask, reviewer), by in rows.items():
        meta = pop[SPLIT_SET[split]]["rows"][ask]
        out.append({"set": SPLIT_SET[split], "ask": ask, "reviewer": reviewer, "family": meta["family"],
                    "class": meta["class"], "by": by})
    return out


def table(pairs, title, keyfn=lambda p: True):
    sel = [p for p in pairs if keyfn(p)]
    print(f"\n### {title} ({len(sel)} pairs, {len({(p['set'], p['ask']) for p in sel})} asks)\n")
    print("| mechanism | pairs: both readers | one reader | asks: both readers | asks: either |")
    print("|---|---|---|---|---|")
    for lab in LABELS:
        both = one = 0; asks_both = set(); asks_either = set()
        for p in sel:
            has = [lab in (p["by"].get(m, {}).get("mechanisms") or []) for m in ("m1", "m2")]
            if all(has):
                both += 1; asks_both.add((p["set"], p["ask"]))
            elif any(has):
                one += 1
            if any(has):
                asks_either.add((p["set"], p["ask"]))
        print(f"| `{lab}` | {both} | {one} | {len(asks_both)} | {len(asks_either)} |")


def main():
    pairs = load()
    readers = {m for p in pairs for m in p["by"]}
    print(f"pairs {len(pairs)}, readers {sorted(readers)}, pairs with both readers {sum(len(p['by']) == 2 for p in pairs)}")
    table(pairs, "All pairs")
    table(pairs, "Claude pairs (X1, X2)", lambda p: p["reviewer"].startswith("X"))
    table(pairs, "gpt_5.2 carried pairs (Grc1)", lambda p: p["reviewer"] == "Grc1")
    table(pairs, "gpt on Claude-only asks", lambda p: p["class"] == "claude_only")
    for s in ("post", "val", "dev"):
        table(pairs, f"set {s}", lambda p, s=s: p["set"] == s)
    print("\n### Reachable, per ask (both readers agree / disagree)\n")
    reach = collections.Counter()
    for p in pairs:
        vals = {m: p["by"][m].get("reachable") for m in p["by"]}
        if len(vals) == 2:
            a, b = vals["m1"], vals["m2"]
            reach[(a if a == b else "disagree")] += 1
    print(dict(reach))
    print("\n### Pairs where the readers' label sets are disjoint\n")
    for p in pairs:
        if len(p["by"]) == 2:
            a = set(p["by"]["m1"].get("mechanisms") or []); b = set(p["by"]["m2"].get("mechanisms") or [])
            if a and b and not (a & b):
                print(f"- {p['set']} {p['ask']} {p['reviewer']}: m1 {sorted(a)} | m2 {sorted(b)}")


if __name__ == "__main__":
    main()
