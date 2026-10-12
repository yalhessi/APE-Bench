"""Hand classification of the 105 K rows' grounds (the row numbers are k_rows.tsv's), and the tally
against the draft's keyword counts. Codebook (mine; several per row allowed, first is primary):
  worth      worth / minor / marginal / taste / noise / "fine" as a bare preference / Meh / not worth
  guess      a negative estimate that maintainers would not ask (wouldn't reject; not sure a maintainer
             would ask; probability 0.35; don't think a maintainer would demand; maintainers accept these)
  siblings   consistency with the file's or the PR's own siblings or namespace
  plurality  corpus prevalence, a counter-precedent in the corpus, a tool's count or 'unresolved' verdict
  brief      the brief's form rules (not questions; concrete requests; about the reviewed code)
  framing    the PR's own framing (its focus, its docstring, its profile / speed)
  budget     finding count or triage ("strongest ask", "focus and be strategic", "already at 7")
  technical  a technical justification that the code is right or the change impossible / undesirable,
             stated without a check (wrong in hindsight)
  refutation a correct technical argument that the ask's change does not work (v0105)
  satisfied  a convention (the ask's or a neighbour's) judged satisfied at the place, no check run
  unstated   the concern named, no ground given (trails off, "Hmm", moves on)
  norule     searched for a rule and found none
  speculative dropped as too speculative / limited basis (self-assessed evidence)
Inadmissible per the draft's section 3.2: guess, worth, siblings, plurality, brief, framing, budget.
"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
INADMISSIBLE = {"guess", "worth", "siblings", "plurality", "brief", "framing", "budget"}
CODES = {
    1: ["siblings"], 2: ["siblings", "guess"], 3: ["technical"], 4: ["norule"], 5: ["worth"],
    6: ["unstated"], 7: ["plurality"], 8: ["budget"], 9: ["unstated"], 10: ["plurality"], 11: ["budget"],
    12: ["unstated"], 13: ["plurality"], 14: ["budget"], 15: ["unstated"], 16: ["plurality"], 17: ["budget"],
    18: ["siblings"], 19: ["speculative"], 20: ["technical"], 21: ["siblings"], 22: ["speculative"], 23: ["technical"],
    24: ["siblings"], 25: ["siblings"], 26: ["plurality"], 27: ["siblings"], 28: ["technical"], 29: ["worth"],
    30: ["unstated"], 31: ["worth"], 32: ["satisfied"], 33: ["worth"], 34: ["worth", "budget"], 35: ["unstated"],
    36: ["plurality"], 37: ["plurality"], 38: ["brief"], 39: ["worth"], 40: ["unstated"], 41: ["worth"],
    42: ["satisfied", "speculative"], 43: ["plurality", "worth"], 44: ["plurality"], 45: ["unstated"], 46: ["unstated"],
    47: ["framing"], 48: ["satisfied", "guess"], 49: ["budget"], 50: ["guess", "budget", "plurality"],
    51: ["technical"], 52: ["technical"], 53: ["technical"], 54: ["technical", "worth"], 55: ["framing"],
    56: ["speculative"], 57: ["worth"], 58: ["unstated"], 59: ["technical"], 60: ["framing"], 61: ["worth"],
    62: ["worth"], 63: ["worth"], 64: ["worth"], 65: ["worth"], 66: ["worth"], 67: ["worth"], 68: ["worth"],
    69: ["technical", "worth"], 70: ["worth"], 71: ["technical", "worth"], 72: ["worth"], 73: ["technical", "worth"],
    74: ["unstated"], 75: ["refutation"], 76: ["refutation"], 77: ["refutation"], 78: ["refutation"],
    79: ["refutation"], 80: ["refutation"], 81: ["brief"], 82: ["brief"], 83: ["satisfied"], 84: ["brief"],
    85: ["brief"], 86: ["satisfied"], 87: ["worth"], 88: ["guess", "worth"], 89: ["worth"], 90: ["technical"],
    91: ["satisfied"], 92: ["guess", "worth"], 93: ["worth"], 94: ["technical"], 95: ["satisfied"], 96: ["worth"],
    97: ["worth"], 98: ["guess", "technical"], 99: ["worth"], 100: ["worth"], 101: ["worth"], 102: ["unstated"],
    103: ["unstated"], 104: ["satisfied"], 105: ["technical"],
}
# rows whose named concern is adjacent to the ask's (K doubtful: C or O under a strict reading)
ADJACENT = {19, 20, 22, 23, 83, 86, 91, 95}
DRAFT_K = {"worth": 27, "guess": 22, "plurality": 14, "siblings": 9, "failed check": 6, "brief": 4, "outside authority": 1, "framing": 2}


def main():
    rows = list(csv.DictReader(open(HERE / "k_rows.tsv"), delimiter="\t"))
    assert len(rows) == 105 == len(CODES)
    out = []
    for r in rows:
        n = int(r["n"]); codes = CODES[n]
        out.append({**r, "grounds": codes, "primary": codes[0], "inadmissible": bool(set(codes) & INADMISSIBLE),
                    "adjacent_concern": n in ADJACENT,
                    "mentions_maintainer": bool(re.search(r"maintainer", r["quote"], re.I))})
    with open(HERE / "k_grounds.jsonl", "w") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    prim = Counter(o["primary"] for o in out)
    anyc = Counter(c for o in out for c in set(o["grounds"]))
    print("primary ground:", dict(prim.most_common()))
    print("any ground   :", dict(anyc.most_common()))
    inad = [o for o in out if o["inadmissible"]]
    print(f"rows with an inadmissible ground (draft's list): {len(inad)} of 105, on {len({(o['set'], o['ask']) for o in inad})} asks  (draft: 63 on 32)")
    strict = [o for o in inad if o["primary"] in INADMISSIBLE]
    print(f"  primary ground inadmissible: {len(strict)} on {len({(o['set'], o['ask']) for o in strict})} asks")
    print(f"  of these, adjacent-concern rows (K doubtful): {sum(1 for o in inad if o['adjacent_concern'])}")
    rest = Counter(o["primary"] for o in out if not o["inadmissible"])
    print(f"rows with no inadmissible ground: {105 - len(inad)}: {dict(rest)}")
    # the 'maintainer' keyword as a proxy for the draft's 'guess about maintainers' regex
    mm = [o for o in out if o["mentions_maintainer"]]
    print(f"\nquotes containing 'maintainer': {len(mm)} (draft's 'guess about maintainers' = 22)")
    print("  of which my code is guess:", sum(1 for o in mm if "guess" in o["grounds"]),
          "; the rest name the ask as a prediction and drop it on:", dict(Counter(o["primary"] for o in mm if "guess" not in o["grounds"])))
    for o in mm:
        print(f"   {o['n']:>3} {o['ask']} {o['session']} [{'/'.join(o['grounds'])}] {o['quote'][:150]}")
    print("\nper batch, primary grounds:")
    for b in sorted({o["batch"] for o in out}):
        print("  ", b, dict(Counter(o["primary"] for o in out if o["batch"] == b)))
    print("\nper condition, inadmissible share:", {c: f"{sum(1 for o in inad if o['session'].startswith(c))}/{sum(1 for o in out if o['session'].startswith(c))}" for c in ("DX", "AP")})
    # asks: inadmissible-ground asks that are never reached (the draft's 32 vs 24 overlap)
    tsv = list(csv.DictReader(open(HERE.parent / "asks_all.tsv"), delimiter="\t"))
    never = {(r["set"], r["ask"]) for r in tsv if all(int(r[c]) == 0 for c in ("DX", "AP", "X", "T", "TA", "OP", "GPT"))}
    ia = {(o["set"], o["ask"]) for o in inad}
    print(f"\ninadmissible-ground asks: {len(ia)}; of them never reached (24-set): {len(ia & never)}; reached by someone: {len(ia - never)}")


if __name__ == "__main__":
    main()
