"""Score step 4 (what maintainers say when they decline) by PROTOCOL.md, written before any label exists.

usage (repo root): ape/bin/python <this file>
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
GROUNDS = ("place", "economy", "indifference", "scope", "authority", "none")


def main() -> int:
    key = {json.loads(l)["item"]: json.loads(l) for l in open(HERE / "declines_key.jsonl")}
    path = HERE / "declines_labels.jsonl"
    lab = {json.loads(l)["item"]: json.loads(l) for l in open(path)} if path.is_file() else {}
    print(f"labelled {len(lab)} of {len(key)}")
    cal = [i for i, k in key.items() if k["source"] == "calibration_ask"]
    ok = sum(1 for i in cal if lab.get(i, {}).get("decline") == "no")
    print(f"calibration: {ok} of {len(cal)} census asks marked decline: no ({'passes' if ok >= 8 else 'FAILS'} 8 of 10)")
    dec = [lab[i] for i, k in key.items() if k["source"] == "decline" and i in lab]
    yes = [r for r in dec if r["decline"] == "yes"]
    print(f"phrase matches read as declines: {len(yes)} of {len(dec)}")
    print("object:", dict(Counter(r["object"] for r in yes)))
    for obj in ("convention", "content", "process", "unclear"):
        sub = [r for r in yes if r["object"] == obj]
        if sub:
            c = Counter(r["ground"] for r in sub)
            print(f"  {obj:10} n={len(sub):2}  " + "  ".join(f"{g} {c[g]}" for g in GROUNDS))
    conv = [r for r in yes if r["object"] == "convention"]
    if conv and ok >= 8:
        c = Counter(r["ground"] for r in conv)
        place, econ = c["place"] / len(conv), (c["economy"] + c["indifference"]) / len(conv)
        verdict = ("maintainers state evidence at the place when they decline" if place >= 1 / 3 else
                   "the negative half in their words is economy and indifference" if econ >= 2 / 3 else "mixed")
        print(f"declines of a convention: place {place:.0%}, economy+indifference {econ:.0%} -> {verdict}")
    elif ok < 8:
        print("not read: calibration failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
