"""Inspection 3 (2026-10-11): how concentrated each benchmark's asks are (effective PRs and authors),
and each row's reach raw, weighting each (PR, author, family) group as one ask, and as a mean of
per-PR reach. Post hoc: the plan headlines raw per-session reach.

usage (repo root): python3 <this file>
"""
import json, sys, yaml
from pathlib import Path
from collections import defaultdict, Counter
P = Path("results/pr_review_v5/probes/conventions-ceiling-2026-10-04")
T = Path("results/pr_review_v5/probes/one-reviewer-table-2026-10-10")
ASKS = {**json.loads((P / "briefs_exact.json").read_text())["asks"], **json.loads((P / "asks_dev_census.json").read_text())["asks"]}
rows = {}
for y in ("val_small12", "postcutoff_2026_07_08_v1", "dev_medium_0_3_0"):
    spec = yaml.safe_load(open(f"configs/probe_sets/{y}.yaml"))
    fb = json.loads((Path(spec["probe_dir"]) / "feedback.json").read_text())
    rows.update({r["cid"]: r for r in fb["rows"]})
def load(dirs, m):
    tab = {}
    for d in dirs:
        tab.update(json.loads((T / d / "unblinded.json").read_text())[m]["table"])
    return tab
for name, dirs in (("P14", ["match_P14_val", "match_P14_post"]), ("P14val", ["match_P14_val"]), ("P14post", ["match_P14_post"]), ("D12", ["match_D12"])):
    tab = load(dirs, "1")
    cids = sorted(tab)
    auth = Counter(rows[c]["author"] for c in cids)
    prs = Counter(ASKS[c]["pr"] for c in cids)
    grp = Counter((ASKS[c]["pr"], rows[c]["author"], ASKS[c]["family"]) for c in cids)
    top = auth.most_common(2)
    # effective PR count (inverse Simpson)
    n = len(cids)
    eff_pr = n * n / sum(v * v for v in prs.values())
    eff_auth = n * n / sum(v * v for v in auth.values())
    print(f"{name}: {n} asks, {len(prs)} PRs (eff {eff_pr:.1f}), {len(auth)} authors (eff {eff_auth:.1f}); top authors {top}; top PRs {prs.most_common(3)}; (pr,author,family) groups {len(grp)}, of size>1: {sum(1 for v in grp.values() if v>1)} holding {sum(v for v in grp.values() if v>1)} asks")
    sessions = sorted({s for r in tab.values() for s in r})
    conds = sorted({s.rstrip('0123456789') for s in sessions})
    out = []
    for cnd in conds:
        ss = [s for s in sessions if s.rstrip('0123456789') == cnd]
        raw = sum(tab[c][s] == "reached" for c in cids for s in ss) / len(ss) / n
        # group-weighted: each (pr,author,family) group weighs 1 total
        w = sum(sum(tab[c][s] == "reached" for s in ss) / len(ss) / grp[(ASKS[c]["pr"], rows[c]["author"], ASKS[c]["family"])] for c in cids) / len(grp)
        # PR-macro: mean over PRs of per-PR reach
        byp = defaultdict(list)
        for c in cids: byp[ASKS[c]["pr"]].append(c)
        macro = sum(sum(tab[c][s] == "reached" for c in cs for s in ss) / len(ss) / len(cs) for cs in byp.values()) / len(byp)
        out.append(f"{cnd} {raw:.2f}/{w:.2f}/{macro:.2f}")
    print("   raw/group-weighted/PR-macro: " + "  ".join(out))
