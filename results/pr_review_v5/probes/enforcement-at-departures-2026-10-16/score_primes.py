"""Score the primes re-read by PROTOCOL.md amendment 3, written before any label exists.

Joins `readings/{C,D}_primes.jsonl` to `reading_items_primes.jsonl`; reports each reader's calibration
(fixed primes labelled `departure`, bar 5 of 6), agreement, the construct error on the 25 open primes
((excluded + invalid) over labelled; `unclear` out, `contested` apart), the grounds, and how each item
moved from the first reading (`readings/{A,B}_{1,2}.jsonl`).

usage (repo root): ape/bin/python <this file>
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))
from src.mathlib_review.io import jsonl_rows  # noqa: E402

HERE = Path(__file__).resolve().parent


def share(rows) -> str:
    c = Counter(r["label"] for r in rows)
    labelled = sum(v for k, v in c.items() if k not in ("unclear", "contested"))
    err = c["excluded"] + c["invalid"]
    rate = err / labelled if labelled else None
    verdict = ("" if rate is None else "  -> denominator mostly ours" if rate >= 0.5
               else "  -> enforcement where noticed" if rate <= 0.2 else "  -> mixed")
    return (f"departure {c['departure']:2} excluded {c['excluded']:2} invalid {c['invalid']:2} contested {c['contested']:2} "
            f"unclear {c['unclear']:2} | construct error {err}/{labelled}" + (f" = {rate:.0%}" if rate is not None else "") + verdict)


def main() -> int:
    key = {row["item"]: row for row in jsonl_rows(HERE / "reading_items_primes.jsonl")}
    readers = {}
    for r in ("C", "D"):
        path = HERE / "readings" / f"{r}_primes.jsonl"
        readers[r] = {row["item"]: row for row in jsonl_rows(path)} if path.is_file() else {}
        print(f"reader {r}: {len(readers[r])} of {len(key)} labelled")
    cal = [i for i, k in key.items() if k["role"] == "calibration"]
    for r, got in readers.items():
        hit = sum(1 for i in cal if got.get(i, {}).get("label") == "departure")
        print(f"calibration, reader {r}: {hit} of {len(cal)} fixed primes labelled `departure` "
              f"({'passes' if hit >= 5 else 'FAILS'} the 5-of-6 bar); misses: "
              f"{[(i, got.get(i, {}).get('label'), got.get(i, {}).get('ground')) for i in cal if got.get(i, {}).get('label') != 'departure']}")
    both = [i for i in key if i in readers["C"] and i in readers["D"]]
    agree = [i for i in both if readers["C"][i]["label"] == readers["D"][i]["label"]]
    print(f"agreement: {len(agree)} of {len(both)}")
    open_ids = [i for i, k in key.items() if k["role"] == "open"]
    for r, got in readers.items():
        print(f"  reader {r}:   {share([got[i] for i in open_ids if i in got])}")
    print(f"  both agree: {share([readers['C'][i] for i in open_ids if i in agree])}")
    print("grounds for `excluded`:", dict(Counter(row.get("ground") for got in readers.values() for i, row in got.items()
                                                  if key.get(i, {}).get("role") == "open" and row["label"] == "excluded")))
    first = {}
    for r in ("A", "B"):
        for part in (1, 2):
            for row in jsonl_rows(HERE / "readings" / f"{r}_{part}.jsonl"):
                first.setdefault(row["item"], []).append(row["label"])
    moved = Counter()
    for i in open_ids:
        before = "departure" if first[key[i]["first_reading_item"]].count("departure") == 2 else "not"
        after = "departure" if [readers[r].get(i, {}).get("label") for r in readers].count("departure") == 2 else "not"
        moved[(before, after)] += 1
    print("open primes, both readers' departure call, first reading -> re-read:", dict(moved))
    return 0


if __name__ == "__main__":
    sys.exit(main())
