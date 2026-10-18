"""Score step 2 by PROTOCOL.md, written before any label exists.

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
DECIDED = ("departs", "conforms", "excluded")
UNASKED = 199


def summary(label: str, rows) -> None:
    c = Counter(r["label"] for r in rows)
    decided = sum(c[k] for k in DECIDED)
    d = c["departs"] / decided if decided else None
    verdict = ("" if d is None else "  -> denominator mostly conforming or excluded" if d <= 0.25
               else "  -> mostly departures nobody asked about" if d >= 0.6 else "  -> mixed")
    rate = f"; ask rate per departure 6 / (6 + {d:.2f} x {UNASKED}) = {6 / (6 + d * UNASKED):.1%}" if d else ""
    print(f"  {label:22} departs {c['departs']:2} conforms {c['conforms']:2} excluded {c['excluded']:2} "
          f"needs_tools {c['needs_tools']:2} unclear {c['unclear']:2} | departs {c['departs']}/{decided}"
          + (f" = {d:.0%}" if d is not None else "") + verdict + rate)


def main() -> int:
    key = {row["item"]: row for row in jsonl_rows(HERE / "step2_items.jsonl")}
    readers = {}
    for r in ("R1", "R2"):
        path = HERE / "readings" / f"{r}.jsonl"
        readers[r] = {row["item"]: row for row in jsonl_rows(path)} if path.is_file() else {}
        print(f"{r}: {len(readers[r])} of {len(key)} labelled")
    cal = [i for i, k in key.items() if k["role"] == "calibration"]
    trusted = {}
    for r, got in readers.items():
        hit = sum(1 for i in cal if got.get(i, {}).get("label") == "departs")
        trusted[r] = hit >= 5
        print(f"calibration {r}: {hit} of {len(cal)} asked places labelled `departs` ({'passes' if trusted[r] else 'FAILS'} 5 of 6); "
              f"misses {[(i, key[i]['rule'], got.get(i, {}).get('label')) for i in cal if got.get(i, {}).get('label') != 'departs']}")
    both = [i for i in key if i in readers["R1"] and i in readers["R2"]]
    agree = [i for i in both if readers["R1"][i]["label"] == readers["R2"][i]["label"]]
    print(f"agreement: {len(agree)} of {len(both)}")
    open_ids = [i for i, k in key.items() if k["role"] == "open"]
    for r, got in readers.items():
        summary(r, [got[i] for i in open_ids if i in got])
    summary("both agree", [readers["R1"][i] for i in open_ids if i in agree])
    print("by check kind (both readers pooled):")
    for kind in ("compile", "lookup", "read"):
        summary(kind, [readers[r][i] for r in readers for i in open_ids if i in readers[r] and key[i]["check_kind"] == kind])
    print("by rule (both readers pooled):")
    for rule in sorted({k["rule"] for k in key.values()}):
        summary(rule, [readers[r][i] for r in readers for i in open_ids if i in readers[r] and key[i]["rule"] == rule])
    return 0


if __name__ == "__main__":
    sys.exit(main())
