"""Step 2 (Q1, PROTOCOL.md): is each rule the maintainers' own practice? Departure rate per opportunity in round-1
code by active reviewers, by other human authors and by AI-flagged PRs (`opportunities.jsonl`); in suggestion blocks
typed in review by anyone but the PR's author, any round (bodies read from the PR store, never written out); and in
the base version of each touched file (each path once). Reads no merge commit and no census ask.

usage (repo root): ape/bin/python <this file>
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import detect  # noqa: E402

HERE = Path(__file__).resolve().parent
DRAW = Path("inputs/pull_requests/evaluation/val1000-2025-06-2026-03-v1/draw.json")
BOTS = re.compile(r"bot|github-actions", re.I)
RULES = ("P084J", "P097", "P341", "P012", "P240", "P392")
FRAG = "lemma _frag : True := by"
#: rules a suggestion fragment cannot show: P341's docstring sits above the suggested lines and P012's
#: neighbours sit outside them, so a fragment would report false departures or false conformance
FRAGMENT_BLIND = ("P341", "P012")


def rate_of(opp: dict, dep: dict, rule: str):
    if rule == "P097":
        return opp.get("P097_proofs_departing", 0), opp.get("P097_proofs", 0)
    return dep.get(rule, 0), opp.get(rule, 0)


def suggestion_counts(classes):
    """Opportunities and departures in suggestion blocks typed by reviewers (fragments without a header get a
    neutral `lemma` header so that proof lines are read as a body; that header is never itself counted)."""
    opp_t, dep_t = Counter(), Counter()
    draw = json.loads(DRAW.read_text())["accepted"]
    n_blocks = 0
    for a in draw:
        d = Path(f"data/pull_requests/pr/{a['pr_number']}")
        if not (d / "pr.json").is_file():
            continue
        author = json.load(open(d / "pr.json"))["user"]["login"]
        for line in open(d / "review_comments.jsonl"):
            r = json.loads(line)
            u = (r.get("user") or {}).get("login") or ""
            if u == author or BOTS.search(u) or not (r.get("path") or "").startswith("Mathlib/"):
                continue
            for block in re.findall(r"```suggestion[^\n]*\n(.*?)```", r.get("body") or "", re.S):
                lines = block.rstrip("\n").splitlines()
                if not lines:
                    continue
                n_blocks += 1
                if not any(detect.HEADER.match(x) for x in lines) and all(x.startswith((" ", "\t")) or not x.strip() for x in lines):
                    lines = [FRAG] + lines
                opp, dep = detect.detect(lines, set(range(1, len(lines) + 1)), classes)
                for k, v in opp.items():
                    opp_t[k] += v
                for x in dep:
                    if x["decl"] != "_frag" or x["rule"] == "P097":
                        dep_t[x["rule"]] += 1
    return opp_t, dep_t, n_blocks


def main() -> int:
    classes = frozenset(l.strip() for l in open(HERE / "classes_unambiguous.txt") if l.strip())
    rows = [json.loads(l) for l in open(HERE / "opportunities.jsonl")]
    by_group = defaultdict(lambda: (Counter(), Counter()))
    base_seen = set()
    base_opp, base_dep = Counter(), Counter()
    for r in rows:
        o, d = by_group[r["group"]]
        o.update(r["opp"])
        d.update(r["dep"])
        if r["path"] not in base_seen and r["base_opp"]:
            base_seen.add(r["path"])
            base_opp.update(r["base_opp"])
            base_dep.update(r["base_dep"])
    s_opp, s_dep, n_blocks = suggestion_counts(classes)
    places = [json.loads(l) for l in open(HERE / "places.jsonl")]
    out = {"suggestion_blocks": n_blocks, "rules": {}}
    print(f"suggestion blocks read: {n_blocks}")
    print(f"{'rule':6} {'reviewers':>16} {'other humans':>16} {'AI-flagged':>14} {'suggestions':>14} {'base files':>16}  reading")
    for rule in RULES:
        cells = {}
        for g in ("reviewer", "other", "ai"):
            o, d = by_group[g]
            cells[g] = rate_of(o, d, rule)
        cells["suggestions"] = rate_of(s_opp, s_dep, rule)
        cells["base"] = rate_of(base_opp, base_dep, rule)
        (rd, rn), (od, on) = cells["reviewer"], cells["other"]
        r = rd / rn if rn else None
        o_ = od / on if on else None
        if r is None or o_ is None:
            reading = "too few"
        elif r >= 0.20 and r >= 2 / 3 * o_:
            reading = "not their practice"
        elif r <= 0.05 or r <= o_ / 3:
            reading = "their practice"
        else:
            reading = "mixed"
        sd, sn = cells["suggestions"]
        if rule in FRAGMENT_BLIND:
            cells["suggestions"] = (0, 0)
        elif sn >= 20 and r is not None:
            s = sd / sn
            if (r >= 0.20 and s <= 0.05) or (r <= 0.05 and s >= 0.20):
                reading += " (contested by suggestions)"
        fmt = lambda c: f"{c[0]}/{c[1]}" + (f" {c[0] / c[1]:.0%}" if c[1] else "")
        print(f"{rule:6} {fmt(cells['reviewer']):>16} {fmt(cells['other']):>16} {fmt(cells['ai']):>14} "
              f"{fmt(cells['suggestions']):>14} {fmt(cells['base']):>16}  {reading}")
        out["rules"][rule] = {**{k: list(v) for k, v in cells.items()}, "reading": reading}
    p341 = [p for p in places if p["rule"] == "P341"]
    exempt = sum(1 for p in p341 if p["decl_in_base_file"] or p["moved"])
    print(f"\nP341 departures in a declaration already in the base file or moved (the rule's own exception): "
          f"{exempt} of {len(p341)}")
    print("P097 in suggestions is counted per fragment-proof (one neutral header per headerless block).")
    (HERE / "practice.json").write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
