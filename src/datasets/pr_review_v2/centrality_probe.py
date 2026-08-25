"""Cheap, no-API probe of the centrality hypothesis for selection.

Hypothesis (a follow-up to the selector upper-bound): a candidate finding is more
maintainer-worthy when its target declaration is *central* to the PR. Before building an
LLM/agentic centrality scorer, test whether crude offline proxies already separate
on-target from off-target findings — and, crucially, whether they do so WITHIN a PR (the
axis the selector must rank on) or only ACROSS PRs (a per-PR scrutiny signal).

Proxies (per candidate, from the gold record + the finding's claim):
  - in_titledesc : the claim's lead `identifier` appears in the PR title/description
  - ref_count    : occurrences of that identifier in the diff (depended-on within the PR)
  - on_added     : that identifier appears on an added (`+`) diff line
  - pr_diff_len  : PR diff size (smaller PR -> more per-finding scrutiny)

Reports global AUC, within-PR AUC, and the selector+centrality combined frontier. Reuses
the diff-only selector's cached scores; no new API.

    python -m src.datasets.pr_review_v2.centrality_probe [pool=grand_union]
"""

import json
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

from ape.utils import parse_cli_args
from .selector import (
    SELECTOR_CACHE, POOLS, _selector_key, auc, build_candidates, frontier, load_gold,
)

_IDENT_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*)`")


def _lead_ident(claim: str) -> Optional[str]:
    m = _IDENT_RE.search(claim or "")
    return m.group(1) if m else None


def attach_features(cands: List[Dict[str, Any]], gold: Dict[int, Dict[str, Any]], model: str) -> None:
    for c in cands:
        inp = gold[c["pr"]]["input"]
        title, desc, diff = inp.get("title", "") or "", inp.get("description", "") or "", inp.get("diff", "") or ""
        ident = _lead_ident(c["finding"].get("claim", ""))
        added = "\n".join(l for l in diff.splitlines() if l.startswith("+"))
        c["in_titledesc"] = 1.0 if (ident and (ident in title or ident in desc)) else 0.0
        c["ref_count"] = float(len(re.findall(re.escape(ident), diff))) if ident else 0.0
        c["on_added"] = 1.0 if (ident and ident in added) else 0.0
        c["pr_diff_len"] = float(len(diff))
        cf = SELECTOR_CACHE / f"{_selector_key(c['pr'], c['finding'], model)}.json"
        c["sel"] = json.loads(cf.read_text())["score"] if cf.exists() else 0.0
        # combined ranker: selector score + centrality nudge + tiny small-PR tiebreak
        c["combo"] = c["sel"] / 100.0 + 0.5 * c["in_titledesc"] - 1e-7 * c["pr_diff_len"]


def within_pr_auc(cands: List[Dict[str, Any]], feat: str) -> Optional[float]:
    by_pr: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for c in cands:
        by_pr[c["pr"]].append(c)
    wins = tot = 0.0
    for cs in by_pr.values():
        on = [c for c in cs if c["on_target"]]
        off = [c for c in cs if not c["on_target"]]
        for a in on:
            for b in off:
                tot += 1
                wins += 1 if a[feat] > b[feat] else 0.5 if a[feat] == b[feat] else 0
    return round(wins / tot, 3) if tot else None


def main() -> None:
    import sys
    cli = parse_cli_args(sys.argv[1:])
    pool = cli.get("pool", "grand_union")
    model = cli.get("selector_model", "gpt_5.4")
    gold = load_gold()
    cands, g2c, _ = build_candidates(gold, POOLS[pool])
    attach_features(cands, gold, model)

    on = [c for c in cands if c["on_target"]]
    off = [c for c in cands if not c["on_target"]]
    v2 = [c for c in cands if (not c["on_target"]) or ("V2" in c["hit_strata"])]
    v2on, v2off = [c for c in v2 if c["on_target"]], [c for c in v2 if not c["on_target"]]

    print(f"pool={pool} | {len(on)} on-target / {len(off)} off-target | V2 on-target={len(v2on)}\n")
    print(f"{'feature':<14}{'globalAUC(all)':>15}{'globalAUC(V2)':>15}{'withinPR_AUC(V2)':>18}")
    for feat in ["sel", "in_titledesc", "ref_count", "on_added", "pr_diff_len", "combo"]:
        ga = auc([c[feat] for c in on], [c[feat] for c in off])
        gv = auc([c[feat] for c in v2on], [c[feat] for c in v2off])
        wv = within_pr_auc(v2, feat)
        print(f"{feat:<14}{str(ga):>15}{str(gv):>15}{str(wv):>18}")

    print("\nframe: 'global' separates across all candidates (helps a global precision threshold); "
          "'withinPR' ranks a PR's own findings (the selection axis).\n")
    print(f"{'ranker':<8}{'overallAUC':>12}{'peak_prec':>11}{'90%gold_prec':>14}")
    for k in ["sel", "combo"]:
        for c in cands:
            c["score"] = c[k]
        fr = frontier(cands, g2c)
        peak = max(p["finding_precision"] or 0 for p in fr["sweep"])
        op = fr["op_retain_90pct_gold"]
        a = auc([c[k] for c in on], [c[k] for c in off])
        print(f"{k:<8}{str(a):>12}{round(peak, 3):>11}{(op['finding_precision'] or 0):>14}")


if __name__ == "__main__":
    main()
