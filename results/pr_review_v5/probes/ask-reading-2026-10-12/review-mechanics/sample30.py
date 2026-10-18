"""Draw the seeded, stratified 30-row sample for the inter-reader re-code (seed 2026; strata K, C, V, O).

Allocation: K 10, C 8, V 6, O 6 -- proportional would give K 11, C 10, V 3, O 6; V is oversampled
to 6 (at C's expense) because the V-vs-K boundary is one of the three the review was asked to probe.
usage: ape/bin/python review-mechanics/sample30.py  -> writes review-mechanics/sample30.jsonl
"""
import json
import random
from pathlib import Path

from load import rows

HERE = Path(__file__).resolve().parent
ALLOC = {"K": 10, "C": 8, "V": 6, "O": 6}


def main():
    rs = rows()
    rng = random.Random(2026)
    out = []
    for code, n in ALLOC.items():
        pool = sorted((r for r in rs if r["behaviour"] == code),
                      key=lambda r: (r["batch"], r["set"], r["pr"], r["ask"], r["session"]))
        out.extend(rng.sample(pool, n))
    with open(HERE / "sample30.jsonl", "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for r in out:
        print(f"{r['behaviour']} {r['batch']:9} {r['set']:8} {r['pr']} {r['ask']} {r['session']} l.{r['line']}  {r['quote'][:70]}")


if __name__ == "__main__":
    main()
