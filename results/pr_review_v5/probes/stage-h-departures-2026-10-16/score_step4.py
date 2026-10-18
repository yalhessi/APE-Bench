"""Score step 4 (each rule's own check, run with tools) by PROTOCOL.md, written before most checks exist.

Reads checks/<PR>.jsonl (one row per place: item, rule, verdict departs|conforms|undecided, calls, evidence) and
the note-free readers S1, S2 of step 3. Reports, on the PRs checked so far, with the unchecked named:
  1. the share of reader-`conforms` open substantive places where the check finds `departs`, per reader and
     pooled, against the pre-registered lines (>= 30%: readers' conforms was largely not checking; <= 10%: it
     holds; between: mixed);
  2. the substantive departure share by the checks alone, and by rule, beside step 3's readers on the same places;
  3. calibration: the 7 asked places, the check should find each departure (at least 5 of 7);
  4. the layout places (read rules, measured), check against readers.
With audit.jsonl present (PROTOCOL.md, step 4 amendment), sections 1-3 are reported twice: the strict reading
(an audited `looser` departure counts as `conforms`) first, then the checker's verdicts as written; the
`looser` and `incomplete` rows are listed.

usage (repo root): ape/bin/python <this file>
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))
from src.mathlib_review.io import jsonl_rows  # noqa: E402

HERE = Path(__file__).resolve().parent
LAYOUT = {"P084", "P048"}
DECIDED = ("departs", "conforms")
READER_DECIDED = ("departs", "conforms", "excluded")


def frac(d: int, n: int) -> str:
    return f"{d}/{n}" + (f" = {d / n:.0%}" if n else "")


def load_checks() -> dict:
    checks = {}
    for path in sorted((HERE / "checks").glob("*.jsonl")):
        for row in jsonl_rows(path):
            checks[row["item"]] = row
    return checks


def strict(checks: dict, audit: dict) -> dict:
    """The strict reading: a departure the audit calls `looser` counts as `conforms`."""
    out = {}
    for i, c in checks.items():
        looser = c["verdict"] == "departs" and audit.get(i, {}).get("reading") == "looser"
        out[i] = {**c, "verdict": "conforms"} if looser else c
    return out


def main() -> int:
    checks = load_checks()
    audit_path = HERE / "audit.jsonl"
    audit = {row["item"]: row for row in jsonl_rows(audit_path)} if audit_path.is_file() else {}
    if not audit:
        return report(checks)
    print(f"audit: {len(audit)} of {len(checks)} rows; "
          f"looser {sorted(i for i, a in audit.items() if a['reading'] == 'looser')}; "
          f"incomplete {sorted(i for i, a in audit.items() if a['reading'] == 'incomplete')}; "
          f"rows not audited {sorted(i for i in checks if i not in audit)}")
    print("\n" + "=" * 30 + " STRICT READING (looser departures count as conforms) " + "=" * 30)
    report(strict(checks, audit))
    print("\n" + "=" * 30 + " CHECKER'S VERDICTS AS WRITTEN " + "=" * 30)
    report(checks)
    return 0


def report(checks: dict) -> int:
    key = {row["item"]: row for row in jsonl_rows(HERE / "step3_items.jsonl")}
    readers = {r: {row["item"]: row for row in jsonl_rows(HERE / "readings" / f"{r}.jsonl")} for r in ("S1", "S2")}
    by_pr = defaultdict(list)
    for i, k in key.items():
        by_pr[k["pr"]].append(i)
    done = sorted(p for p, ids in by_pr.items() if all(i in checks for i in ids))
    partial = sorted(p for p, ids in by_pr.items() if any(i in checks for i in ids) and p not in done)
    unchecked = sorted(p for p in by_pr if p not in done and p not in partial)
    stray = sorted(i for i in checks if i not in key)
    print(f"checked: {len(checks)} of {len(key)} places; PRs complete {len(done)} of {len(by_pr)}: {done}")
    if partial:
        print(f"PRs partly checked: {partial}")
    print(f"PRs not checked (named): {unchecked}")
    if stray:
        print(f"rows for items not in step3_items.jsonl (ignored): {stray}")
    verdicts = Counter(c["verdict"] for i, c in checks.items() if i in key)
    print(f"verdicts: {dict(verdicts)}")
    for i, c in sorted(checks.items()):
        if i in key and c["rule"] != key[i]["rule"]:
            print(f"  RULE MISMATCH {i}: check says {c['rule']}, key says {key[i]['rule']}")

    open_ids = [i for i, k in key.items() if k["role"] == "open" and i in checks]
    sub = [i for i in open_ids if key[i]["rule"] not in LAYOUT]
    lay = [i for i in open_ids if key[i]["rule"] in LAYOUT]

    print("\n1. reader-`conforms` open substantive places where the check finds `departs` (check undecided excluded)")
    pooled_d = pooled_n = 0
    for r, got in readers.items():
        conf = [i for i in sub if got.get(i, {}).get("label") == "conforms" and checks[i]["verdict"] in DECIDED]
        d = sum(1 for i in conf if checks[i]["verdict"] == "departs")
        pooled_d += d
        pooled_n += len(conf)
        print(f"  {r}: {frac(d, len(conf))}  {[i for i in conf if checks[i]['verdict'] == 'departs']}")
    if pooled_n:
        s = pooled_d / pooled_n
        verdict = ("readers' substantive conforms was largely not checking; the departure share is the check's"
                   if s >= 0.30 else "readers' conforms holds; the split stands as step 3 measured it"
                   if s <= 0.10 else "mixed")
        print(f"  pooled: {frac(pooled_d, pooled_n)} -> {verdict}")
    conf_rev = [(r, i) for r, got in readers.items() for i in sub
                if got.get(i, {}).get("label") == "departs" and checks[i]["verdict"] == "conforms"]
    print(f"  the other direction, reader `departs` where the check finds `conforms`: {len(conf_rev)} {conf_rev}")

    print("\n2. substantive departure share, open places")
    c = Counter(checks[i]["verdict"] for i in sub)
    print(f"  check:             {frac(c['departs'], c['departs'] + c['conforms'])}  (undecided {c['undecided']})")
    for r, got in readers.items():
        rc = Counter(got[i]["label"] for i in sub if i in got)
        print(f"  {r} (same places): {frac(rc['departs'], sum(rc[k] for k in READER_DECIDED))}")
    print("  by rule (check | S1 | S2):")
    for rule in sorted({key[i]["rule"] for i in sub}):
        ids = [i for i in sub if key[i]["rule"] == rule]
        cc = Counter(checks[i]["verdict"] for i in ids)
        parts = [frac(cc["departs"], cc["departs"] + cc["conforms"]) + (f" ({cc['undecided']} undecided)" if cc["undecided"] else "")]
        for r, got in readers.items():
            rc = Counter(got[i]["label"] for i in ids if i in got)
            parts.append(frac(rc["departs"], sum(rc[k] for k in READER_DECIDED)))
        print(f"    {rule} ({key[ids[0]]['check_kind']:7}) " + " | ".join(parts))

    print("\n3. calibration: asked places the check finds `departs` (bar: at least 5 of 7)")
    cal = [i for i, k in key.items() if k["role"] == "calibration"]
    got_cal = [i for i in cal if i in checks]
    hit = [i for i in got_cal if checks[i]["verdict"] == "departs"]
    print(f"  {len(hit)} of {len(got_cal)} checked (of {len(cal)}); misses "
          f"{[(i, key[i]['rule'], checks[i]['verdict']) for i in got_cal if i not in hit]}; "
          f"not yet checked {[i for i in cal if i not in checks]}")
    if len(got_cal) == len(cal):
        print(f"  -> {'passes' if len(hit) >= 5 else 'FAILS'}")

    print("\n4. layout places (read rules, measured): check against readers")
    lc = Counter(checks[i]["verdict"] for i in lay)
    print(f"  check: {frac(lc['departs'], lc['departs'] + lc['conforms'])}")
    for r, got in readers.items():
        same = sum(1 for i in lay if i in got and got[i]["label"] == checks[i]["verdict"])
        print(f"  {r} agrees with the check on {same} of {len(lay)}")
    calls = [checks[i].get("calls", 0) for i in checks if i in key]
    print(f"\ntool calls per place: total {sum(calls)}, max {max(calls) if calls else 0}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
