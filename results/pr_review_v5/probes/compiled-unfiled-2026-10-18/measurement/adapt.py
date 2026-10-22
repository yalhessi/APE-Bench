"""The compiled-unfiled probe's matching on the shared path: a thin adapter, no model.

The task/dataflow refactor's implementation review follow-up (2026-10-22, closure item 2) asked
that the demonstrated-change consumer's saved findings and asks pass through the shared matching,
report and trace, and that its study reading consume the common report. `match.py inputs` built
matcher folders by hand and `match.py read` unblinded the matchers' files itself; here the probe's
own renderer and readers are reused (imported from `match.py`, not copied) and only the way a
verdict is looked up changes: from the shared report's per-replicate tables.

From the repository root (`<probe>` defaults to this directory's parent):

    ape/bin/python <this dir>/adapt.py inputs [<probe>]
    ape/bin/python -m src.mathlib_review.review.cli probe match-plan \
        --set configs/probe_sets/dev_medium_0_3_0.yaml --name compiled_unfiled --out <this dir> \
        --seal <this dir>/seal.json --sources <this dir>/sources.json \
        --ask-packets <this dir>/ask_packets.json --version 1-session --question-form --replicates 2
    ape/bin/python -m src.mathlib_review.review.cli probe match-import \
        --set configs/probe_sets/dev_medium_0_3_0.yaml --plan <this dir> --name compiled_unfiled \
        --matches <probe>/match/matches.1.json <probe>/match/matches.2.json
    ape/bin/python <this dir>/adapt.py read [<probe>]     # prints what reading.txt holds

`--set` is required by the CLI and unused when the asks and findings are given.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

HERE = Path(__file__).resolve().parent
PRODUCER = "import-compiled_unfiled"


def _probe(root: Path):
    """The probe's own `match.py`, as a module: its renderer, readers and constants."""
    spec = importlib.util.spec_from_file_location("compiled_unfiled_match", root / "match.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = root
    module.ASK_READING = root.parent / "ask-reading-2026-10-12"
    return module


def inputs(root: Path) -> None:
    """The three sessions' findings files, the ask packets and the sources, as `match.py inputs`
    would have written the matcher folders: the same seal, the same `_finding`, the same order."""
    m = _probe(root)
    seal = json.loads((root / "blinding_SEALED.json").read_text())
    added = [r for r in m._rows("added_findings.jsonl") if r["ask_pr"]]
    packets = m._packets()
    prs = sorted(int(pr) for pr in seal)
    (HERE / "seal.json").write_text((root / "blinding_SEALED.json").read_text())
    asks = {str(pr): [a["matcher_text"] for a in packets[pr][1]["asks"]] for pr in prs}
    (HERE / "ask_packets.json").write_text(json.dumps(asks, indent=1, ensure_ascii=False) + "\n")
    sources = {}
    for session in m.SESSIONS:
        found = {str(pr): [{**m._finding(r), "key": r["key"]}
                           for r in sorted(added, key=lambda r: (r["order"], r["key"]))
                           if r["pr"] == pr and r["session"] == session]
                 for pr in prs}
        path = HERE / f"findings_{session}.json"
        path.write_text(json.dumps(found, indent=1, ensure_ascii=False) + "\n")
        sources[session] = {"kind": "findings_file", "path": str(path.relative_to(Path.cwd()))}
    (HERE / "sources.json").write_text(json.dumps(sources, indent=1) + "\n")
    print(f"{len(prs)} PRs, {len(added)} added findings, {sum(len(v) for v in asks.values())} asks")


def read(root: Path) -> None:
    """`match.py read`'s lines, each verdict read from the shared report's replicate tables."""
    from src.mathlib_review.analysis.matching import report_matching

    m = _probe(root)
    report = report_matching(HERE, write=False, producers=[PRODUCER])
    if report["measurement"]["forensic"]:
        raise SystemExit("the stored matching does not cover its plan; nothing is read from it")
    tables = [report[f"{PRODUCER}:{n}"]["table"] for n in (1, 2)]
    asks_tsv = {r["ask"]: r for r in csv.DictReader(open(m.ASK_READING / "asks_all.tsv"), delimiter="\t")}
    packets = m._packets()
    added = m._rows("added_findings.jsonl")
    ask_added = [r for r in added if r["ask_pr"]]

    before = {}
    for pr, (_s, packet) in packets.items():
        for a in packet["asks"]:
            for session in m.SESSIONS:
                o = a["outcomes"].get(session) or {}
                before[(session, a["id"])] = "reached" in (o.get("m1"), o.get("m2"))

    def outcome(n, ask, session):
        return (tables[n].get(ask) or {}).get(session, "no")

    def count(rows, label):
        prs = sorted({r["pr"] for r in rows})
        new, partial, already, new_m1 = (defaultdict(set) for _ in range(4))
        for pr in prs:
            _s, packet = packets[pr]
            sessions_with = {r["session"] for r in rows if r["pr"] == pr}
            for a in packet["asks"]:
                for session in sessions_with:
                    o1, o2 = outcome(0, a["id"], session), outcome(1, a["id"], session)
                    if o1 == "reached" and o2 == "reached":
                        (already if before[(session, a["id"])] else new)[a["id"]].add(session)
                    elif "partial" in (o1, o2) or "reached" in (o1, o2):
                        partial[a["id"]].add(session)
                    if o1 == "reached" and not before[(session, a["id"])]:
                        new_m1[a["id"]].add(session)
        n_added = len(rows)
        ask_sessions = sum(len(v) for v in new.values())
        distinct = sorted(new)
        solo_union66 = {a for a, r in asks_tsv.items() if r["family"] in m.CODE_FAMILIES and int(r["DX"]) > 0}
        solo_union93 = {a for a, r in asks_tsv.items() if int(r["DX"]) > 0}
        print(f"\n== {label}: {n_added} added findings on the ask PRs ({n_added / 78:.2f} a session)")
        print(f"   newly reached, both matchers: {len(distinct)} distinct asks, {ask_sessions} ask-sessions: "
              + ", ".join(f"{a} ({'/'.join(sorted(v))}, {asks_tsv[a]['family']})" for a, v in sorted(new.items())))
        print(f"   yield (newly reached ask-sessions per added finding): {ask_sessions / max(n_added, 1):.3f}")
        print(f"   reached on both, already reached by the session's filed findings: "
              + (", ".join(f"{a} ({'/'.join(sorted(v))})" for a, v in sorted(already.items())) or "none"))
        print(f"   partial or split between matchers: "
              + (", ".join(f"{a} ({'/'.join(sorted(v))})" for a, v in sorted(partial.items())) or "none"))
        print(f"   matcher 1 union on the 66: {len(solo_union66)} -> {len(solo_union66 | {a for a in new_m1 if asks_tsv[a]['family'] in m.CODE_FAMILIES})}; "
              f"on the 93: {len(solo_union93)} -> {len(solo_union93 | set(new_m1))}")
        if len(distinct) >= 4 and n_added <= 30:
            verdict = "BUILD"
        elif len(distinct) <= 1:
            verdict = "NOT WORTH A BUILD"
        else:
            controls = sum(1 for r in added if r["pr"] in m.DEV_CONTROLS and (label == "primary" or r["last_at_place"])) / 9
            ok = ask_sessions / max(n_added, 1) >= 0.10 and controls <= 0.5
            verdict = f"BETWEEN -> {'build' if ok else 'do not build'} (yield {ask_sessions / max(n_added, 1):.3f}, dev controls {controls:.2f} a session)"
        print(f"   line: {verdict}")

    count(ask_added, "primary")
    count([r for r in ask_added if r["last_at_place"]], "last change per place")
    noask = [r for r in added if not r["ask_pr"]]
    print(f"\nno-ask sessions: {len(noask)} added over 30 ({len(noask) / 30:.2f} a session); dev controls "
          f"{sum(1 for r in noask if r['pr'] in m.DEV_CONTROLS)} over 9")


if __name__ == "__main__":
    root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else HERE.parent
    {"inputs": inputs, "read": read}[sys.argv[1]](root)
