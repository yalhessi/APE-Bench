"""Recompute the draft's section 5 and 1.5 counts from the readings, and list the knowledge-column
disagreements (within a condition across rows; between DX and AP) and the K-with-partial rows."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from load import PROBE, rows

HERE = Path(__file__).resolve().parent


def main():
    rs = rows()
    by_ask = defaultdict(list)
    for r in rs:
        by_ask[(r["set"], r["ask"])].append(r)
    fam = {k: v[0]["family"] for k, v in by_ask.items()}
    # never-reached (any column 0 in asks_all.tsv)
    tsv = list(csv.DictReader(open(PROBE / "asks_all.tsv"), delimiter="\t"))
    cols = ["DX", "AP", "X", "T", "TA", "OP", "GPT"]
    never = {(r["set"], r["ask"]) for r in tsv if all(int(r[c]) == 0 for c in cols)}
    print(f"never-reached (asks_all.tsv, 7 columns, m1 reached): {len(never)}")
    # 1.5: knowledge of the never-reached (DX modal), family, behaviour
    know_dx = {}
    for k, grp in by_ask.items():
        dx = [r for r in grp if r["condition"] == "DX" and r["behaviour"] != "reached"]
        if dx:
            know_dx[k] = Counter(r.get("knowledge") or "none" for r in dx).most_common(1)[0][0]
    print("  by knowledge (DX modal):", Counter(know_dx.get(k, "n/a") for k in never))
    print("  by family:", Counter(fam[k] for k in never))
    beh = Counter(r["behaviour"] for k in never for r in by_ask[k])
    print("  behaviour rows at those asks:", dict(beh), "total", sum(beh.values()))
    # 5: K rows
    K = [r for r in rs if r["behaviour"] == "K"]
    V = [r for r in rs if r["behaviour"] == "V"]
    C = [r for r in rs if r["behaviour"] == "C"]
    O = [r for r in rs if r["behaviour"] == "O"]
    print(f"\nK rows {len(K)} on {len({(r['set'], r['ask']) for r in K})} asks; V {len(V)}; C {len(C)}; O {len(O)}")
    reached_asks = {k for k, grp in by_ask.items() if any(r["behaviour"] == "reached" for r in grp)}
    m1_reached_asks = {(r["set"], r["ask"]) for r in tsv if any(int(r[c]) > 0 for c in cols)}
    print(f"  K rows on asks some DX/AP session reached (behaviour): {sum(1 for r in K if (r['set'], r['ask']) in reached_asks)}")
    print(f"  K rows on asks some session of any row reached (m1): {sum(1 for r in K if (r['set'], r['ask']) in m1_reached_asks)}")
    print(f"  K rows on never-reached asks: {sum(1 for r in K if (r['set'], r['ask']) in never)}")
    print(f"  K rows per condition: {Counter(r['condition'] for r in K)}; per batch: {Counter(r['batch'] for r in K)}")
    print(f"  K rows where m1/m2 not both 'no': {[(r['set'], r['ask'], r['session'], r['m1'], r['m2']) for r in K if (r['m1'], r['m2']) != ('no', 'no')]}")
    print(f"  C rows by family: {Counter(fam[(r['set'], r['ask'])] for r in C)}")
    print(f"  O rows by family: {Counter(fam[(r['set'], r['ask'])] for r in O)}")
    ap = [r for r in rs if r["condition"] == "AP"]
    print(f"  AP held rows: {sum(1 for r in ap if r.get('ap') == 'held')}; ignored: {sum(1 for r in ap if r.get('ap') == 'held' and r.get('ap_use') == 'ignored')}; "
          f"considered_dropped: {sum(1 for r in ap if r.get('ap_use') == 'considered_dropped')}; used: {sum(1 for r in ap if r.get('ap_use') == 'used')}")
    print(f"  held & ignored by behaviour: {Counter(r['behaviour'] for r in ap if r.get('ap') == 'held' and r.get('ap_use') == 'ignored')}")
    print(f"  held & considered_dropped by behaviour: {Counter(r['behaviour'] for r in ap if r.get('ap_use') == 'considered_dropped')}")
    # family tallies for 1.4: F2 and F6 and F8 by condition hits
    for f in ("F2", "F6", "F8"):
        asks = [k for k in by_ask if fam[k] == f]
        dx = sum(1 for k in asks for r in by_ask[k] if r["condition"] == "DX" and r["behaviour"] == "reached")
        apn = sum(1 for k in asks for r in by_ask[k] if r["condition"] == "AP" and r["behaviour"] == "reached")
        held = [k for k in asks if any(r.get("ap") == "held" for r in by_ask[k])]
        ign = sum(1 for k in asks for r in by_ask[k] if r.get("ap") == "held" and r.get("ap_use") == "ignored")
        print(f"  {f}: asks {len(asks)} DX {dx} AP {apn} of {3*len(asks)}; held asks {len(held)}; held-ignored rows {ign}")
    # knowledge disagreements
    print("\n## knowledge column disagreements")
    dis = []
    for k, grp in sorted(by_ask.items()):
        codes = {c: Counter(r.get("knowledge") or "none" for r in grp if r["condition"] == c and r["behaviour"] != "reached") for c in ("DX", "AP")}
        within = {c: v for c, v in codes.items() if len(v) > 1}
        modal = {c: (v.most_common(1)[0][0] if v else None) for c, v in codes.items()}
        between = modal["DX"] and modal["AP"] and modal["DX"] != modal["AP"]
        if within or between:
            dis.append((k, dict(codes["DX"]), dict(codes["AP"]), "within" if within else "", "between" if between else ""))
    for d in dis:
        print("  ", d)
    print(f"  asks with any disagreement: {len(dis)} of {len(by_ask)}")
    # modal ties
    ties = []
    for k, grp in sorted(by_ask.items()):
        for c in ("DX", "AP"):
            v = Counter(r.get("knowledge") or "none" for r in grp if r["condition"] == c and r["behaviour"] != "reached")
            mc = v.most_common()
            if len(mc) > 1 and mc[0][1] == mc[1][1]:
                ties.append((k, c, dict(v)))
    print(f"  modal ties (aggregate.py breaks by first-seen row order): {ties}")
    # demand vs none: K-row knowledge codes
    print("\n## knowledge code on K rows (concern named and dropped):", Counter(r.get('knowledge') for r in K))
    print("## knowledge code on C rows:", Counter(r.get('knowledge') for r in C))
    print("## knowledge code on V rows:", Counter(r.get('knowledge') for r in V))
    # per batch: knowledge distribution of non-reached rows (reader style)
    print("\n## per batch, non-reached rows' knowledge codes")
    for b in sorted({r["batch"] for r in rs}):
        print("  ", b, dict(Counter(r.get("knowledge") for r in rs if r["batch"] == b and r["behaviour"] != "reached")))
    print("\n## per batch, behaviour codes of non-reached rows (share)")
    for b in sorted({r["batch"] for r in rs}):
        nr = [r for r in rs if r["batch"] == b and r["behaviour"] != "reached"]
        c = Counter(r["behaviour"] for r in nr)
        print("  ", b, len(nr), {k: f"{v} ({v/len(nr):.0%})" for k, v in sorted(c.items())})


if __name__ == "__main__":
    main()
