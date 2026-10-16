"""Score the survivors' reading by PROTOCOL.md amendment 2, written before any label exists.

Joins `readings/{A,B}_{1,2}.jsonl` to the key in `reading_items.jsonl`; reports each reader's
calibration (fixed departures labelled `departure`, bar 9 of 13), agreement, and the construct error
((excluded + invalid) over labelled, `unclear` out, `contested` apart) on the 77 open survivors, per
convention and pooled, per reader and on the items both agree on; and the grounds named.

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
ERROR = {"excluded", "invalid"}


def labels(reader: str) -> dict:
    out = {}
    for part in (1, 2):
        path = HERE / "readings" / f"{reader}_{part}.jsonl"
        if path.is_file():
            out.update({row["item"]: row for row in jsonl_rows(path)})
    return out


def share(rows) -> str:
    c = Counter(r["label"] for r in rows)
    labelled = sum(v for k, v in c.items() if k not in ("unclear", "contested"))
    err = sum(c[k] for k in ERROR)
    rate = f"{err / labelled:.0%}" if labelled else "-"
    verdict = ("" if not labelled else "  -> denominator mostly ours" if err / labelled >= 0.5
               else "  -> enforcement where noticed" if err / labelled <= 0.2 else "  -> mixed")
    return (f"departure {c['departure']:2} excluded {c['excluded']:2} invalid {c['invalid']:2} contested {c['contested']:2} "
            f"unclear {c['unclear']:2} | construct error {err}/{labelled} = {rate}{verdict}")


def main() -> int:
    key = {row["item"]: row for row in jsonl_rows(HERE / "reading_items.jsonl")}
    readers = {r: labels(r) for r in ("A", "B")}
    for r, got in readers.items():
        missing = sorted(set(key) - set(got))
        print(f"reader {r}: {len(got)} of {len(key)} labelled; missing {missing[:8]}")
    calibration = [i for i, k in key.items() if k["role"] == "calibration"]
    trusted = {}
    for r, got in readers.items():
        hit = sum(1 for i in calibration if got.get(i, {}).get("label") == "departure")
        trusted[r] = hit >= 9
        print(f"calibration, reader {r}: {hit} of {len(calibration)} fixed departures labelled `departure` "
              f"({'passes' if trusted[r] else 'FAILS'} the 9-of-13 bar)")
    both = [i for i in key if i in readers["A"] and i in readers["B"]]
    agree = [i for i in both if readers["A"][i]["label"] == readers["B"][i]["label"]]
    print(f"agreement: {len(agree)} of {len(both)} items")
    open_items = [i for i, k in key.items() if k["role"] == "open"]
    for conv in ("P057", "P108", "P113", None):
        ids = [i for i in open_items if conv is None or key[i]["convention"] == conv]
        print(f"\n== {conv or 'pooled'} (n={len(ids)})")
        for r, got in readers.items():
            print(f"  reader {r}:   {share([got[i] for i in ids if i in got])}")
        agreed = [readers["A"][i] for i in ids if i in agree]
        print(f"  both agree: {share(agreed)}  (on {len(agreed)} items)")
    grounds = Counter(row.get("ground") for got in readers.values() for i, row in got.items()
                      if key[i]["role"] == "open" and row["label"] == "excluded")
    print("\ngrounds named for `excluded` (both readers):", dict(grounds.most_common()))
    print("\ncontrol PRs only (open items on PRs with no asks at all):")
    for r, got in readers.items():
        print(f"  reader {r}: {share([got[i] for i in open_items if key[i]['control'] and i in got])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
