"""Score step 3 (the note-free re-read) by PROTOCOL.md, written before any label exists.

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
LAYOUT = {"P084", "P048"}


def share(rows):
    c = Counter(r["label"] for r in rows)
    decided = sum(c[k] for k in DECIDED)
    return c["departs"], decided, (c["departs"] / decided if decided else None)


def fmt(rows) -> str:
    d, n, s = share(rows)
    return f"{d}/{n}" + (f" = {s:.0%}" if s is not None else "")


def main() -> int:
    key = {row["item"]: row for row in jsonl_rows(HERE / "step3_items.jsonl")}
    by_old = {k["step2_item"]: i for i, k in key.items()}
    new = {}
    for r in ("S1", "S2"):
        path = HERE / "readings" / f"{r}.jsonl"
        new[r] = {row["item"]: row for row in jsonl_rows(path)} if path.is_file() else {}
        print(f"{r}: {len(new[r])} of {len(key)} labelled")
    old = {}
    for r in ("R1", "R2"):
        old[r] = {by_old[row["item"]]: row for row in jsonl_rows(HERE / "readings" / f"{r}.jsonl")}
    cal = [i for i, k in key.items() if k["role"] == "calibration"]
    for r, got in new.items():
        hits = {t: sum(1 for i in cal if key[i]["note"] == t and got.get(i, {}).get("label") == "departs") for t in ("names_fix", "neutral")}
        tot = sum(hits.values())
        print(f"calibration {r}: {tot} of {len(cal)} asked places `departs` ({'passes' if tot >= 5 else 'FAILS'} 5 of 7); "
              f"names_fix {hits['names_fix']}/4, neutral {hits['neutral']}/3")
    both = [i for i in key if i in new["S1"] and i in new["S2"]]
    agree = [i for i in both if new["S1"][i]["label"] == new["S2"][i]["label"]]
    print(f"agreement: {len(agree)} of {len(both)}")
    open_ids = [i for i, k in key.items() if k["role"] == "open"]
    print("\n1. departs by note type, open places (with note: step 2, R1+R2 pooled | without: step 3, S1+S2 pooled | step 3 both agree)")
    for t in ("names_fix", "hedged", "neutral"):
        ids = [i for i in open_ids if key[i]["note"] == t]
        with_note = [old[r][i] for r in old for i in ids]
        without = [new[r][i] for r in new for i in ids if i in new[r]]
        agreed = [new["S1"][i] for i in ids if i in agree]
        print(f"  {t:10} n={len(ids):2}  with note {fmt(with_note):>12}  without {fmt(without):>12}  agreed {fmt(agreed):>10}")
    d, n, s = share([new[r][i] for r in new for i in open_ids if key[i]["note"] == "neutral" and i in new[r]])
    d2, n2, s2 = share([new[r][i] for r in new for i in open_ids if key[i]["note"] == "names_fix" and i in new[r]])
    if s is not None and s2 is not None:
        verdict = ("notes suppressed departures where silent" if s >= 0.2 else
                   "readers find the pinpointer's departures unaided; the note was informative" if s <= 0.05 and s2 >= 0.5 else
                   "neither line")
        print(f"  -> neutral {s:.0%}, names_fix {s2:.0%}: {verdict}")
    print("\n2. the rule-kind split (open places, both readers pooled)")
    for label, rows_of in (("with note (step 2)", lambda i: [old[r][i] for r in old]),
                           ("without (step 3)", lambda i: [new[r][i] for r in new if i in new[r]])):
        lay = [x for i in open_ids if key[i]["rule"] in LAYOUT for x in rows_of(i)]
        sub = [x for i in open_ids if key[i]["rule"] not in LAYOUT for x in rows_of(i)]
        _, _, sl = share(lay); _, _, ss = share(sub)
        gap = (sl - ss) * 100 if sl is not None and ss is not None else None
        verdict = "" if gap is None else ("survives" if gap >= 30 else "collapses" if gap <= 15 else "between")
        print(f"  {label:20} layout {fmt(lay):>12}  substantive {fmt(sub):>12}  gap {gap:.0f} points -> {verdict}" if gap is not None else f"  {label}: n/a")
    print("\nper rule, without the note (S1+S2 pooled):")
    for rule in sorted({k["rule"] for k in key.values()}):
        print(f"  {rule}  {fmt([new[r][i] for r in new for i in open_ids if key[i]['rule'] == rule and i in new[r]])}")
    flips = Counter((old["R1"][i]["label"], new["S1"][i]["label"]) for i in open_ids if i in new["S1"])
    print("\nreader-1 label, with note -> without:", dict(flips.most_common(10)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
