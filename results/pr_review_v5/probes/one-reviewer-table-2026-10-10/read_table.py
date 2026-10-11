"""The one reviewer table's reading, by the rule fixed in docs/plans/2026-10-10-one-reviewer-table.md.

Matcher scorer, per seal (`match_<seal>/unblinded.json` from `cli probe unblind`, and its
`session_stats.json`), per matcher, on all asks and on in-census asks:
- each row's per-session reach for every rep, the mean, the union and the stable count;
- findings a PR, and yield (asks reached per finding).

A row is a session label less its digits. The derived rows are DX_i u DX_j (the three pairs) and
AP_i u DX_i (paired by rep), `deployable-reviewer-review-2026-10.md` section 4's comparator.

Judge scorer on D12: issue hits of 23 per run, from each run's audit, with per-obligation hits mapped
to PRs through the release's gold judgments.

For each pre-stated comparison, the difference of means, a paired PR-cluster bootstrap (10,000 draws
over PRs, seeded) and the leave-one-PR-out range, on every matcher. An ordering is claimed only when
the two rows' rep ranges do not overlap and the bootstrap's 95% interval excludes 0 on every matcher;
otherwise the rows read as indistinguishable on that benchmark.

usage (repo root): python3 <this file> [--seal NAME=DIR ...] [--judge]
  default seals: P14 (match_P14_val + match_P14_post, pooled, and each), D12 (match_D12).
"""
import argparse
import json
import random
import statistics
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).parent
CEIL = HERE.parent / "conventions-ceiling-2026-10-04"
ASKS = {**json.loads((CEIL / "briefs_exact.json").read_text())["asks"],
        **json.loads((CEIL / "asks_dev_census.json").read_text())["asks"]}
ORDER = ["X", "T", "TA", "OP", "GPT", "DX", "AP", "DXuDX", "APuDX"]
COMPARE = [("DX", "GPT"), ("X", "DX"), ("T", "DX"), ("OP", "DX"), ("X", "OP"), ("X", "T"), ("AP", "DX"), ("AP", "DXuDX"),
           ("APuDX", "DXuDX"), ("TA", "T"), ("X", "AP"), ("T", "AP")]
DRAWS, SEED = 10_000, "one-reviewer-table-2026-10-10"


def condition(session):
    return session.rstrip("0123456789")


def load_seal(dirs):
    """Per matcher: {cid: {session: hit}}; and findings by (pr, session)."""
    tables, findings = {}, {}
    for d in dirs:
        u = json.loads((d / "unblinded.json").read_text())
        for m in ("1", "2"):
            for cid, row in u[m]["table"].items():
                tables.setdefault(m, {})[cid] = {s: v == "reached" for s, v in row.items()}
        for pr, per in json.loads((d / "session_stats.json").read_text()).items():
            for s, st in per.items():
                findings[(pr, s)] = st["findings"]
    return tables, findings


def rows_of(table):
    """Each row's reps as functions cid -> hit, the derived rows included."""
    sessions = sorted({s for row in table.values() for s in row})
    reps = {}
    for s in sessions:
        reps.setdefault(condition(s), []).append(lambda c, s=s: table[c].get(s, False))
    if "DX" in reps:
        dx = {s: (lambda c, s=s: table[c].get(s, False)) for s in sessions if condition(s) == "DX"}
        reps["DXuDX"] = [lambda c, a=a, b=b: dx[a](c) or dx[b](c) for a, b in combinations(sorted(dx), 2)]
        if "AP" in reps:
            reps["APuDX"] = [lambda c, n=n: table[c].get(f"AP{n}", False) or table[c].get(f"DX{n}", False)
                             for n in sorted(s[2:] for s in sessions if condition(s) == "AP")]
    return reps


def by_pr(cids):
    out = {}
    for c in cids:
        out.setdefault(str(ASKS[c]["pr"]), []).append(c)
    return out


def boot(a_reps, b_reps, groups):
    """Mean reach difference a - b, its PR bootstrap interval and leave-one-PR-out range."""
    prs = sorted(groups)
    a = {pr: statistics.mean(sum(f(c) for c in groups[pr]) for f in a_reps) for pr in prs}
    b = {pr: statistics.mean(sum(f(c) for c in groups[pr]) for f in b_reps) for pr in prs}
    n = {pr: len(groups[pr]) for pr in prs}
    stat = lambda sample: sum(a[p] - b[p] for p in sample) / sum(n[p] for p in sample)
    rng = random.Random(SEED)
    draws = sorted(stat([rng.choice(prs) for _ in prs]) for _ in range(DRAWS))
    loo = [stat([p for p in prs if p != q]) for q in prs] if len(prs) > 1 else []
    return stat(prs), (draws[int(0.025 * DRAWS)], draws[int(0.975 * DRAWS) - 1]), (min(loo), max(loo)) if loo else None


def read_matcher(name, dirs):
    tables, findings = load_seal(dirs)
    print(f"\n######## {name}: {', '.join(d.name for d in dirs)}")
    out = {}
    for scope, keep in (("all asks", lambda c: True), ("in-census asks", lambda c: ASKS[c]["in_census"])):
        cids = sorted(c for c in tables["1"] if keep(c))
        groups = by_pr(cids)
        print(f"\n== {scope}: {len(cids)} asks on {len(groups)} PRs; per-session reach, matcher 1 / 2 ==")
        reps = {m: rows_of(tables[m]) for m in tables}
        ranges = {}
        for row in [r for r in ORDER if r in reps["1"]]:
            vals = {m: [sum(f(c) for c in cids) / len(cids) for f in reps[m][row]] for m in reps}
            union = {m: sum(any(f(c) for f in reps[m][row]) for c in cids) for m in reps}
            stable = {m: sum(all(f(c) for f in reps[m][row]) for c in cids) for m in reps}
            ranges[row] = {m: (min(v), max(v)) for m, v in vals.items()}
            line = " / ".join(f"{statistics.mean(v):.2f} [{', '.join(f'{x:.2f}' for x in v)}]" for v in vals.values())
            extra = ""
            if not row.endswith("uDX"):
                sess = sorted({s for (pr, s) in findings if condition(s) == row})
                prs = sorted({pr for (pr, s) in findings})
                per_pr = statistics.mean(findings[(pr, s)] for pr in prs for s in sess if (pr, s) in findings) if sess else 0
                hits = sum(f(c) for f in reps["1"][row] for c in cids)
                total = sum(findings[(pr, s)] for pr in prs for s in sess if (pr, s) in findings)
                extra = f" | {per_pr:.1f} findings a PR, yield {hits / total:.2f}" if total and scope == "all asks" else f" | {per_pr:.1f} findings a PR" if scope == "all asks" else ""
            print(f"  {row:6} {line} | union {union['1']}/{union['2']}, stable {stable['1']}/{stable['2']} of {len(cids)}{extra}")
            out.setdefault(scope, {})[row] = {"reps": vals, "union": union, "stable": stable}
        print(f"-- comparisons ({scope}): mean difference, 95% PR-bootstrap interval, leave-one-PR-out range; verdict --")
        for a, b in COMPARE:
            if a not in reps["1"] or b not in reps["1"]:
                continue
            got = {m: boot(reps[m][a], reps[m][b], groups) for m in reps}
            apart = all(ranges[a][m][0] > ranges[b][m][1] or ranges[b][m][0] > ranges[a][m][1] for m in reps)
            excl = all(ci[0] > 0 or ci[1] < 0 for _d, ci, _l in got.values())
            verdict = ("ordered" if apart and excl else "indistinguishable"
                       + (" (reps apart, interval spans 0)" if apart else " (interval excludes 0, reps overlap)" if excl else ""))
            print(f"  {a:>6} - {b:<6} " + " | ".join(
                f"m{m} {d:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}] loo {loo[0]:+.3f}..{loo[1]:+.3f}" for m, (d, ci, loo) in got.items())
                  + f"  -> {verdict}")
            out.setdefault(f"{scope} comparisons", {})[f"{a}-{b}"] = {m: {"diff": d, "ci": ci, "loo": loo} for m, (d, ci, loo) in got.items()} | {"verdict": verdict}
    return out


JUDGE_RUNS = {"X": ["probe-dev-claude-X1.elm", "probe-dev-claude-X2.elm"],
              "OP": ["probe-dev-opus55-contract2-claude-sub-rep1.elm", "probe-dev-opus55-contract2-claude-sub-rep2.elm"],
              "GPT": [f"probe-dev-elmgpt55-contract2-rep{n}" for n in (1, 2, 3)],
              "DX": [f"iter-ds41-conv-dev-base-rep{n}" for n in (1, 2, 3)],
              "AP": [f"iter-ds41-conv-dev-apt-rep{n}" for n in (1, 2, 3)],
              "T": ["probe-dev-claude-T1"], "TA": ["probe-dev-claude-TA1"]}


def read_judge():
    gold = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0/gold/judgments.jsonl")
    pr_of = {}
    for line in gold.read_text(encoding="utf-8").split("\n"):
        if line:
            r = json.loads(line)
            for ob in r["obligations"]:
                pr_of[ob["obligation_id"]] = str(r["pr_number"])
    print("\n######## D12 judge v9 (elm_gpt_5_mini): issue hits of 23 per run")
    hits, out = {}, {}
    for row, slugs in JUDGE_RUNS.items():
        got = []
        for slug in slugs:
            f = Path("results/pr_review_v5/audits") / slug / "semantic_report.json"
            if not f.exists():
                got.append(None)
                continue
            d = json.loads(f.read_text())
            got.append({o["obligation_id"]: o["issue_status"] == "hit" for o in d["per_obligation"]})
        done = [g for g in got if g is not None]
        hits[row] = done
        vals = [sum(g.values()) for g in done]
        union = sum(any(g[o] for g in done) for o in done[0]) if done else None
        print(f"  {row:4} {vals} of 23 (missing {got.count(None)}); union {union}")
        out[row] = vals
    groups = {}
    for o in next(iter(g for v in hits.values() for g in v)):
        groups.setdefault(pr_of[o], []).append(o)
    print("-- comparisons (judge): mean difference in obligations, 95% PR-bootstrap interval, leave-one-PR-out --")
    for a, b in COMPARE:
        if not hits.get(a) or not hits.get(b):
            continue
        d, ci, loo = boot([g.get for g in hits[a]], [g.get for g in hits[b]], groups)
        apart = min(out[a]) > max(out[b]) or min(out[b]) > max(out[a])
        excl = ci[0] > 0 or ci[1] < 0
        print(f"  {a:>4} - {b:<4} {23 * d:+.2f} [{23 * ci[0]:+.2f}, {23 * ci[1]:+.2f}] loo {23 * loo[0]:+.2f}..{23 * loo[1]:+.2f}"
              f"  -> {'ordered' if apart and excl else 'indistinguishable'}")
    return out


ap = argparse.ArgumentParser()
ap.add_argument("--seal", action="append", default=[], help="NAME=DIR[,DIR...]")
ap.add_argument("--judge", action="store_true")
args = ap.parse_args()
seals = [(s.split("=", 1)[0], [Path(p) for p in s.split("=", 1)[1].split(",")]) for s in args.seal] or [
    ("P14 pooled", [HERE / "match_P14_val", HERE / "match_P14_post"]), ("P14 validation", [HERE / "match_P14_val"]),
    ("P14 post-cutoff", [HERE / "match_P14_post"]), ("D12 matcher", [HERE / "match_D12"])]
result = {name: read_matcher(name, dirs) for name, dirs in seals if all((d / "unblinded.json").exists() for d in dirs)}
if args.judge:
    result["D12 judge"] = read_judge()
if not args.seal:
    (HERE / "table.json").write_text(json.dumps(result, indent=1) + "\n")
