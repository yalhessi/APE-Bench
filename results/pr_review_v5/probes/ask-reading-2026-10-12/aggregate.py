"""Aggregate the per-ask readings (`readings/*.jsonl`) into the tables the design document reads from.

usage (worktree root): ape/bin/python results/pr_review_v5/probes/ask-reading-2026-10-12/aggregate.py
writes readings/aggregate.md and readings/aggregate.json. Counts are one reader's per batch, provisional.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "readings"
BEH = ["reached", "P", "E", "K", "V", "C", "O", "A"]
BEH_TEXT = {"reached": "reached", "P": "partial", "E": "filed, unmatched", "K": "right concern, dropped",
            "V": "checked, read as conforming", "C": "attended, concluded fine",
            "O": "attended, asked something else", "A": "not attended"}
KNOW = ["none", "demand", "mechanism", "direction", "api", "construction", "pr_context", "unclear"]


def setname(s):
    return "D12" if s == "D12" else "P14"


def main():
    rows = []
    for f in sorted(R.glob("*.jsonl")):
        if f.name.startswith("aggregate"):
            continue
        for line in open(f):
            if line.strip():
                r = json.loads(line); r["batch"] = f.stem; rows.append(r)
    out = ["# Aggregate of the per-ask readings\n",
           f"{len(rows)} rows from {sorted({r['batch'] for r in rows})}; "
           f"{len({(r['set'], r['ask']) for r in rows})} asks. One reader per batch; provisional.\n"]
    # 1. behaviour per condition x set
    out.append("## 1. Behaviour at the place, per session row (condition x set)\n")
    out.append("| condition | set | rows | " + " | ".join(BEH_TEXT[b] for b in BEH) + " |")
    out.append("|---|---|---|" + "---|" * len(BEH))
    agg = {}
    for cond in ("DX", "AP"):
        for st in ("D12", "P14", "all"):
            sel = [r for r in rows if r["condition"] == cond and (st == "all" or setname(r["set"]) == st)]
            c = Counter(r["behaviour"] for r in sel)
            agg[(cond, st)] = c
            out.append(f"| {cond} | {st} | {len(sel)} | " + " | ".join(str(c.get(b, 0)) for b in BEH) + " |")
    out.append("")
    # 2. knowledge per ask (one code per ask per condition: take the modal code over its rows)
    out.append("## 2. Knowledge the miss needed, per ask (modal code over the condition's rows; reached-only asks excluded)\n")
    know = {}
    for (st, ask, cond), grp in groupby(rows, lambda r: (r["set"], r["ask"], r["condition"])).items():
        if all(r["behaviour"] == "reached" for r in grp):
            continue
        codes = Counter(r.get("knowledge") or "none" for r in grp if r["behaviour"] != "reached")
        know[(st, ask, cond)] = (codes.most_common(1)[0][0], [r.get("knowledge_detail") for r in grp if r.get("knowledge_detail")][:1])
    out.append("| condition | set | asks with a miss | " + " | ".join(KNOW) + " |")
    out.append("|---|---|---|" + "---|" * len(KNOW))
    for cond in ("DX", "AP"):
        for st in ("D12", "P14", "all"):
            sel = {k: v for k, v in know.items() if k[2] == cond and (st == "all" or setname(k[0]) == st)}
            c = Counter(v[0] for v in sel.values())
            out.append(f"| {cond} | {st} | {len(sel)} | " + " | ".join(str(c.get(k, 0)) for k in KNOW) + " |")
    out.append("\n### 2a. The asks by knowledge code (DX), with the reader's detail\n")
    byk = defaultdict(list)
    for (st, ask, cond), (code, det) in know.items():
        if cond == "DX":
            byk[code].append(f"{ask} ({st}){': ' + det[0][:140] if det else ''}")
    for k in KNOW:
        if byk.get(k):
            out.append(f"- **{k}** ({len(byk[k])}): " + "; ".join(sorted(byk[k])))
    out.append("")
    # 3. AP: held / use
    out.append("## 3. The applicable-conventions section: held, and what the session did\n")
    ap = [r for r in rows if r["condition"] == "AP"]
    held = Counter(r.get("ap") for r in ap)
    out.append(f"AP rows {len(ap)}: held {held.get('held', 0)}, absent {held.get('absent', 0)}, n/a {held.get('n/a', 0)}.\n")
    use = Counter((r.get("ap_use") or "null", r["behaviour"]) for r in ap if r.get("ap") == "held")
    out.append("| held and … | reached | partial | K dropped | V | C | O | E |")
    out.append("|---|---|---|---|---|---|---|---|")
    for u in ("used", "considered_dropped", "ignored", "null"):
        out.append(f"| {u} | " + " | ".join(str(use.get((u, b), 0)) for b in ("reached", "P", "K", "V", "C", "O", "E")) + " |")
    # per ask: DX hits vs AP hits where held
    out.append("\n### 3a. Per ask where the section held the convention: DX hits -> AP hits (of 3), AP use\n")
    per = defaultdict(lambda: {"DX": 0, "AP": 0, "use": Counter(), "set": None})
    for r in rows:
        k = (r["set"], r["ask"]); per[k]["set"] = r["set"]
        if r["behaviour"] == "reached":
            per[k][r["condition"]] += 1
        if r["condition"] == "AP" and r.get("ap") == "held":
            per[k]["use"][r.get("ap_use") or "null"] += 1
            per[k]["held"] = True
    gained = lost = same = 0
    for (st, ask), v in sorted(per.items()):
        if not v.get("held"):
            continue
        d = v["AP"] - v["DX"]
        gained += d > 0; lost += d < 0; same += d == 0
        out.append(f"- {ask} ({st}): DX {v['DX']} -> AP {v['AP']}; " + ", ".join(f"{u} {n}" for u, n in v["use"].items()))
    out.append(f"\nHeld asks: AP > DX at {gained}, AP < DX at {lost}, equal at {same}.\n")
    # 4. the grounds for dropping (K) and the checks (V)
    out.append("## 4. The grounds on which a named concern was dropped (K rows), verbatim\n")
    for r in rows:
        if r["behaviour"] == "K":
            out.append(f"- {r['ask']} {r['session']}: \"{(r.get('quote') or '').strip()[:200]}\"")
    out.append("\n## 5. Checks read as conforming (V rows), verbatim\n")
    for r in rows:
        if r["behaviour"] == "V":
            out.append(f"- {r['ask']} {r['session']}: \"{(r.get('quote') or '').strip()[:200]}\"")
    # 6. per family
    out.append("\n## 6. Reach by family (asks, sessions reached of 3) per condition\n")
    fam = defaultdict(lambda: Counter())
    for (st, ask), v in per.items():
        f = next((r["family"] for r in rows if r["set"] == st and r["ask"] == ask), "?")
        fam[f]["asks"] += 1; fam[f]["DX"] += v["DX"]; fam[f]["AP"] += v["AP"]
    out.append("| family | asks | DX hits (of 3n) | AP hits |")
    out.append("|---|---|---|---|")
    for f, c in sorted(fam.items()):
        out.append(f"| {f} | {c['asks']} | {c['DX']} | {c['AP']} |")
    (R / "aggregate.md").write_text("\n".join(out) + "\n")
    (R / "aggregate.json").write_text(json.dumps({
        "behaviour": {f"{k[0]}/{k[1]}": dict(v) for k, v in agg.items()},
        "knowledge": {f"{k[0]}/{k[1]}/{k[2]}": v[0] for k, v in know.items()},
        "held": {f"{st}/{ask}": {"DX": v["DX"], "AP": v["AP"], "use": dict(v["use"])} for (st, ask), v in per.items() if v.get("held")},
    }, indent=1))
    print("\n".join(out[:16]))


def groupby(rows, key):
    d = defaultdict(list)
    for r in rows:
        d[key(r)].append(r)
    return d


if __name__ == "__main__":
    main()
