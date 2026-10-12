"""Join checks on prepare.py's packets and the readings.

1. behaviour=='reached' in the readings vs the packet's m1/m2 for the same (ask, session).
2. For every DX/AP session: the packet's findings_as_matched (R_pr<pr>.json, what the matcher saw)
   against the transcript's own submit_findings call -- same count, same texts?
3. The AP section: identical across AP1/AP2/AP3 of a PR? how many conventions does it hold?
4. P14_val AP sessions: the sources list two runs (ap, apt); which one holds the PR, and does the
   matched finding list agree with that transcript?
5. Finding index base: m1_finding index against the input list and the transcript.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from load import PROBE, ROOT, packets, rows, sessions

LABELS = ("DX1", "DX2", "DX3", "AP1", "AP2", "AP3")


def submission(transcript):
    for line in open(transcript):
        if not line.strip():
            continue
        e = json.loads(line)
        for c in (e.get("message") or {}).get("content") or []:
            if c.get("type") == "tool_use" and c.get("name") == "submit_findings":
                return c.get("input")
    return None


def norm(s):
    return " ".join((s or "").split())


def main():
    rs = rows()
    pk = packets()
    # 1. reached vs m1/m2
    mism = []
    for r in rs:
        st, pr, ask, ses = r["set"], int(r["pr"]), r["ask"], r["session"]
        a = next(x for x in pk[(st, pr)]["asks"] if x["id"] == ask)
        o = a["outcomes"].get(ses, {})
        m1, m2 = o.get("m1"), o.get("m2")
        if (r["m1"], r["m2"]) != (m1, m2):
            mism.append((st, pr, ask, ses, "row m1/m2", r["m1"], r["m2"], "packet", m1, m2))
        beh = r["behaviour"]
        if beh == "reached" and not (m1 == "reached" and m2 == "reached"):
            mism.append((st, pr, ask, ses, "beh=reached but", m1, m2))
        if beh != "reached" and (m1 == "reached" and m2 == "reached"):
            mism.append((st, pr, ask, ses, f"beh={beh} but both matchers reached"))
        if beh == "P" and not (m1 == "partial" or m2 == "partial"):
            mism.append((st, pr, ask, ses, f"beh=P but", m1, m2))
    print("## 1. behaviour vs matcher outcome")
    print(f"rows {len(rs)}; mismatches {len(mism)}")
    for m in mism:
        print("  ", m)
    both = Counter()
    for r in rs:
        both[(r["behaviour"], r["m1"], r["m2"])] += 1
    print("  (behaviour, m1, m2) counts:")
    for k, v in sorted(both.items(), key=lambda kv: -kv[1]):
        print("   ", k, v)
    # 2. findings_as_matched vs transcript submission
    print("\n## 2. matched findings vs the transcript's submission (DX/AP)")
    bad = 0; n = 0; missing = 0
    for (st, pr), d in sorted(pk.items()):
        for lab in LABELS:
            e = d["sessions"].get(lab) or {}
            tr = e.get("transcript"); fm = e.get("findings_as_matched")
            if not tr:
                missing += 1; print(f"  {st} {pr} {lab}: no transcript"); continue
            sub = submission(tr)
            if sub is None:
                print(f"  {st} {pr} {lab}: no submit_findings in transcript"); bad += 1; continue
            subf = sub.get("findings") or []
            n += 1
            # compare counts and texts
            def key(f):
                if isinstance(f, dict):
                    return norm(f.get("title") or f.get("summary") or f.get("description") or json.dumps(f, sort_keys=True))[:80]
                return norm(str(f))[:80]
            if fm is None:
                print(f"  {st} {pr} {lab}: findings_as_matched is None; transcript has {len(subf)}"); bad += 1; continue
            if len(fm) != len(subf):
                print(f"  {st} {pr} {lab}: count differs: matched {len(fm)} vs transcript {len(subf)} (run {e.get('run')})"); bad += 1
                for f in subf[len(fm):]:
                    print("      unmatched extra finding:", norm(json.dumps(f, ensure_ascii=False))[:300])
                continue
            # text overlap
            km = [key(f) for f in fm]; ks = [key(f) for f in subf]
            same = sum(1 for a, b in zip(km, ks) if a == b)
            if same != len(km):
                print(f"  {st} {pr} {lab}: {same}/{len(km)} finding keys identical in order")
                for i, (a, b) in enumerate(zip(km, ks)):
                    if a != b:
                        print(f"      [{i}] matched   : {a!r}\n      [{i}] transcript: {b!r}")
                bad += 1
    print(f"sessions checked {n}; disagreements {bad}; missing transcripts {missing}")
    # 3. AP section identical across AP1-3; convention count
    print("\n## 3. AP section per PR: identical across the three AP sessions? conventions held")
    import os
    os.chdir(ROOT); sys.path.insert(0, str(PROBE))
    from prepare import ap_section  # noqa
    for (st, pr), d in sorted(pk.items()):
        secs = {}
        for lab in ("AP1", "AP2", "AP3"):
            tr = (d["sessions"].get(lab) or {}).get("transcript")
            secs[lab] = ap_section(tr) if tr else None
        vals = [norm(s) if s else None for s in secs.values()]
        ident = len(set(vals)) == 1
        s0 = secs["AP1"] or ""
        nconv = sum(1 for ln in s0.splitlines() if ln.startswith("- ") or ln[:2].rstrip(".").isdigit() or ln.startswith("### "))
        print(f"  {st} {pr}: identical={ident} AP1 len {len(s0)} chars; bullet/heading lines {nconv}; "
              f"starts {s0[:60]!r}; ends {s0[-80:]!r}")
    # 4. P14_val AP run ambiguity
    print("\n## 4. P14_val AP: which run holds the PR")
    from prepare import session_file  # noqa
    src = json.load(open(ROOT / "results/pr_review_v5/probes/one-reviewer-table-2026-10-10/sources_P14_val.json"))
    for (st, pr), d in sorted(pk.items()):
        if st != "P14_val":
            continue
        for lab in ("AP1", "AP2", "AP3"):
            runs = src[lab]["run"]
            have = {run: session_file(run, pr) for run in runs}
            print(f"  {pr} {lab}: " + "; ".join(f"{run}: {'yes' if v else 'no'}" for run, v in have.items()) + f" -> used {d['sessions'][lab].get('run')}")
    # 5. finding index base
    print("\n## 5. finding index: m1_finding vs text")
    cnt = Counter()
    for (st, pr), d in sorted(pk.items()):
        for a in d["asks"]:
            for lab, o in a["outcomes"].items():
                for m in ("m1", "m2"):
                    fi = o.get(f"{m}_finding")
                    if fi is None:
                        continue
                    lst = d["sessions"].get(lab, {}).get("findings_as_matched") or []
                    cnt["in_range" if 0 <= fi < len(lst) else "out_of_range"] += 1
                    if fi == len(lst):
                        cnt["== len (1-based?)"] += 1
                    if fi == 0:
                        cnt["zero"] += 1
    print("  ", dict(cnt))


if __name__ == "__main__":
    main()
