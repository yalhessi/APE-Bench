"""The filing contract's bars, read from the three matched seals (README: "Bars", fixed 2026-10-12).

Each figure on each matcher separately:
1. Naming: the asks of the two cores (`cores.json`) that any of G1-G3 reached (All(G), the union).
2. Volume: G's filed findings on the three controls over the nine runs (`counts.py`), and asks reached
   per finding, G's sessions pooled against DX1's, on this seal.
3. The policy: the core asks a G session reached through a finding A(G) keeps, against All(G)'s.
Reported beside them: every session's reach on all asks; the anchors' drift from the table's own
matches of DX1 and AP1 (more than four asks is flagged); the table's three-rep DX and AP unions on the
cores; which of G's reaching findings were questions, and on what ground the reviewer would have left
each out; and the core asks on PRs where a self-lookup alone closes most conforming cells (amendment 2).

usage (repo root): ape/bin/python <this file>
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from counts import CONTROLS, cell_of, ledger_rows, withheld_by_policy  # noqa: E402
from smoke_check import self_lookup_only  # noqa: E402

D = Path("results/pr_review_v5/probes/filing-contract-2026-10-12")
TABLE = Path("results/pr_review_v5/probes/one-reviewer-table-2026-10-10")
#: core set key -> (this probe's seal, the G runs' set tag, the table's seal of the same asks)
SEALS = {"P14_val": ("G_P14_val", "val", "match_P14_val"), "P14_post": ("G_P14_post", "post", "match_P14_post"),
         "D12": ("G_D12", "dev", "match_D12b")}
G = ("G1", "G2", "G3")
MATCHERS = ("1", "2")


def load():
    """Per matcher: {(core id, session): (value, finding index, pr)}; and findings shown, by (pr, session)."""
    cells = {m: {} for m in MATCHERS}
    shown = {}
    for key, (name, _tag, _table) in SEALS.items():
        seal = json.loads((D / f"blinding_{name}_SEALED.json").read_text())
        for m in MATCHERS:
            for ask in json.loads((D / f"match_{name}" / f"matches.{m}.json").read_text())["asks"]:
                for label, session in seal[str(ask["pr"])].items():
                    cells[m][(f"{key}/{ask['ask_id']}", session)] = (ask.get(label), ask.get(f"{label}_finding"),
                                                                     int(ask["pr"]))
        for pr, by in json.loads((D / f"match_{name}" / "session_stats.json").read_text()).items():
            for session, stats in by.items():
                shown[(key, int(pr), session)] = stats["findings"]
    return cells, shown


def g_findings():
    """{(set key, G label, pr): [(withheld by A(G), disposition, would_clear_on), ...]} in filed order,
    the order `probe match-inputs` numbers them in; and self-lookup-heavy (set key, G label, pr)."""
    out, heavy = {}, set()
    for key, (_name, tag, _table) in SEALS.items():
        for n, label in enumerate(G, 1):
            for row in ledger_rows(f"filing_g_{tag}_rep{n}"):
                by_cell = cell_of(row)
                rows = []
                for finding in row.get("findings") or []:
                    cell = by_cell.get((finding.get("declaration"), finding.get("concern"))) or {}
                    rows.append((withheld_by_policy(finding, cell), cell.get("disposition"), cell.get("would_clear_on")))
                out[(key, row["pr_number"], label)] = rows
                conforming = [c for c in row.get("ledger") or [] if c.get("disposition") == "conforms"]
                if conforming and sum(map(self_lookup_only, conforming)) > len(conforming) / 2:
                    heavy.add((key, row["pr_number"], label))
    return out, heavy


def table_reached(m: str) -> dict:
    """The table's own matches: {session: set of core-style ask ids it reached}, over its three seals."""
    out = {}
    for key, (_name, _tag, table) in SEALS.items():
        for cid, row in json.loads((TABLE / table / "unblinded.json").read_text())[m]["table"].items():
            for session, value in row.items():
                if value == "reached":
                    out.setdefault(session, set()).add(f"{key}/{cid}")
    return out


def main() -> int:
    cores = json.loads((D / "cores.json").read_text())
    k37, n32 = set(cores["inadmissible_K"]), set(cores["never_reached"])
    cells, shown = load()
    filed, heavy = g_findings()
    asks = sorted({cid for cid, _s in cells["1"]})
    print(f"{len(asks)} asks on {len({(c.split('/')[0], v[2]) for (c, _s), v in cells['1'].items()})} PRs; "
          f"cores: {len(k37)} inadmissible-dropped, {len(n32)} never reached")
    for m in MATCHERS:
        c = cells[m]
        reached = {s: {cid for (cid, s2), v in c.items() if s2 == s and v[0] == "reached"} for s in G + ("DX1", "AP1")}
        partial = {s: {cid for (cid, s2), v in c.items() if s2 == s and v[0] == "partial"} for s in G}
        all_g = set().union(*(reached[s] for s in G))
        part_g = set().union(*(partial[s] for s in G)) - all_g
        kept = set()
        for (cid, s), (value, index, pr) in c.items():
            if s in G and value == "reached":
                rows = filed.get((cid.split("/")[0], pr, s)) or []
                if index is None or index >= len(rows) or not rows[index][0]:
                    kept.add(cid)
        table = table_reached(m)
        print(f"\n=== matcher {m} ===")
        k, n = len(all_g & k37), len(all_g & n32)
        verdict = "PASS" if k >= 24 and n >= 8 else ("DEAD END (below 16 of 37)" if k < 16 else "below the bar")
        print(f"Bar 1  All(G) reaches {k} of 37 and {n} of 32 (bars 24 and 8): {verdict}; "
              f"partial only: {len(part_g & k37)} of 37, {len(part_g & n32)} of 32")
        for cond in ("DX", "AP"):
            union = set().union(*(table.get(f"{cond}{r}", set()) for r in (1, 2, 3)))
            print(f"       beside it, the table's {cond}1-3 union on its own seals: {len(union & k37)} of 37, "
                  f"{len(union & n32)} of 32")
        g_hits = sum(len(reached[s]) for s in G)
        g_findings_shown = sum(v for (key, pr, s), v in shown.items() if s in G)
        dx_findings_shown = sum(v for (key, pr, s), v in shown.items() if s == "DX1")
        g_yield, dx_yield = g_hits / max(g_findings_shown, 1), len(reached["DX1"]) / max(dx_findings_shown, 1)
        print(f"Bar 2  asks reached per finding: G {g_yield:.3f} ({g_hits} over {g_findings_shown} findings, three "
              f"sessions), DX1 {dx_yield:.3f} ({len(reached['DX1'])} over {dx_findings_shown}): "
              f"{'met' if g_yield >= dx_yield else 'NOT met'}")
        share = len(kept & k37) / max(len(all_g & k37), 1)
        print(f"Bar 3  A(G) reaches {len(kept & k37)} of All(G)'s {len(all_g & k37)} on the 37 ({share:.0%}; bar 80%)")
        print("Reach on all asks, per session: " + ", ".join(
            f"{s} {len(reached[s])}/{len(asks)}" for s in G + ("DX1", "AP1")))
        everyone = set(asks)
        print("  beside them, the table's sessions on its own seals: " + ", ".join(
            f"{s} {len(table.get(s, set()) & everyone)}/{len(asks)}" for c in ("DX", "AP") for s in (f"{c}1", f"{c}2", f"{c}3")))
        for cond, union in (("G", all_g), ("DX", set().union(*(table.get(f"DX{r}", set()) for r in (1, 2, 3)))),
                            ("AP", set().union(*(table.get(f"AP{r}", set()) for r in (1, 2, 3))))):
            print(f"  union of three reps, {cond}: {len(union & everyone)}/{len(asks)}"
                  + (f"; reached by G and by no DX or AP session: {len(all_g - set().union(*table.values()))}"
                     if cond == "G" else ""))
        for s in ("DX1", "AP1"):
            drift = len(reached[s] ^ table.get(s, set()))
            print(f"  anchor {s}: {len(reached[s])} here, {len(table.get(s, set()))} on the table's seals, "
                  f"{drift} asks differ{'  ** DRIFT over 4 **' if drift > 4 else ''}")
        grounds, questions = Counter(), 0
        for (cid, s), (value, index, pr) in c.items():
            if s in G and value == "reached" and cid in k37 | n32 and index is not None:
                rows = filed.get((cid.split("/")[0], pr, s)) or []
                if index < len(rows):
                    questions += rows[index][1] == "ask_author"
                    grounds[rows[index][2] or "no cell"] += 1
        print(f"G's reaching findings on the cores: {questions} questions; would_clear_on {dict(grounds.most_common())}")
        on_heavy = sorted(cid for (cid, s), v in c.items() if s in G and cid in k37 | n32
                          and (cid.split("/")[0], v[2], s) in heavy)
        print(f"Core asks on a PR where a self-lookup alone closes most conforming cells (in that rep): "
              f"{sorted(set(on_heavy)) or 'none'}")
    print("\nControls' volume (bar 2): ape/bin/python results/pr_review_v5/probes/filing-contract-2026-10-12/counts.py "
          "filing_g_{val,post,dev}_rep{1,2,3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
