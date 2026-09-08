"""Miss decomposition: of the gold maintainer findings a run/pool does NOT cover,
how many are a SELECTION gap vs a COVERAGE gap?

For each anchored gold finding, against a pool of predicted findings:

  COVERED       — a same-file, within-slack prediction also passes the topical gate
                  (MATCH_PROMPT judge says SAME concern). This is the recall hit.
  LOCATED-MISS  — at least one prediction lands at the gold location (same file,
                  within slack) but NONE passes the topical gate. The generator
                  *reached the spot* and said something else / framed it differently.
                  Recoverable by a better concern lens or selection — not a coverage hole.
  UNTOUCHED     — no prediction lands anywhere near the gold location. The pool never
                  surfaced a candidate there at all: a genuine COVERAGE gap, the regime
                  where better generation (retrieval, exhaustive enumeration) is needed.

Decision this informs: lots of UNTOUCHED => invest in generation (retrieval / inventory);
lots of LOCATED-MISS => invest in concern-targeting / a selector (the calibration lever).

Reuses the frozen topical-judge cache (no new API calls if the pooled pairs were already
judged by each run's `evaluate_d2 mode=target topical_gate=True`). Pairs with no cached
verdict are reported as `uncached` so the result is known to be complete (or not).

Usage:
  python -m src.datasets.pr_review_v2.miss_decompose
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ape.utils.project import PROJECT_ROOT
from .evaluate_d2 import (
    _gold_findings,
    _gold_line,
    norm_path,
    _pair_cache_key,
    pred_span,
)

PRED_DIR = PROJECT_ROOT / "inputs" / "pr_review_v2" / "predictions"
GOLD = PROJECT_ROOT / "inputs" / "pr_review_v2" / "mathlib_pr_review_v2_actionable_20260618.jsonl"
CACHE_DIR = PROJECT_ROOT / "data" / "pr_review_v2" / "cache" / "matcher"
MATCHER_MODEL = "gpt_5_mini"
LINE_SLACK = 10

# Canonical runs (model, approach) -> prediction stem.
RUNS: Dict[Tuple[str, str], str] = {
    ("gpt_5.4", "holistic"): "preds_gpt_5.4_workspace_20260618145045",
    ("gpt_5.4", "guidelines"): "preds_gpt_5.4_workspace_20260618150029",
    ("gpt_5.4", "composed"): "preds_gpt_5.4_composed_20260618164852",
    ("gpt_5.2", "holistic"): "preds_gpt52_holistic",
    ("gpt_5.2", "guidelines"): "preds_gpt52_guidelines",
    ("gpt_5.2", "composed"): "preds_gpt52_composed",
}

# Pools to decompose: name -> list of (model, approach) keys to union.
POOLS: Dict[str, List[Tuple[str, str]]] = {
    "gpt_5.4 holistic": [("gpt_5.4", "holistic")],
    "gpt_5.2 holistic": [("gpt_5.2", "holistic")],
    "gpt_5.4 composed": [("gpt_5.4", "composed")],
    "gpt_5.2 composed": [("gpt_5.2", "composed")],
    "gpt_5.4 union (hol+comp)": [("gpt_5.4", "holistic"), ("gpt_5.4", "composed")],
    "gpt_5.2 union (hol+comp)": [("gpt_5.2", "holistic"), ("gpt_5.2", "composed")],
    "grand union (all runs)": list(RUNS.keys()),
}


def load_predictions(stem: str) -> List[Dict[str, Any]]:
    path = PRED_DIR / f"{stem}.jsonl"
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def lookup_cached(gold: Dict[str, Any], pred: Dict[str, Any]) -> Optional[bool]:
    """Frozen topical verdict for one (gold, pred) pair, or None if not cached."""
    key = _pair_cache_key(gold, pred, MATCHER_MODEL)
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None
    return bool(json.loads(cache_file.read_text())["same_issue"])


def decompose_pool(
    gold_records: Dict[int, Dict[str, Any]],
    pool_keys: List[Tuple[str, str]],
) -> Dict[str, Any]:
    # Pool predicted findings by PR across all runs in the pool.
    preds_by_pr: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for key in pool_keys:
        for rec in load_predictions(RUNS[key]):
            if not rec.get("parse_ok"):
                continue
            for f in rec.get("findings") or []:
                preds_by_pr[rec["pr_number"]].append(f)

    by_stratum = lambda: {"covered": 0, "located_miss": 0, "untouched": 0, "gold": 0}
    strata: Dict[str, Dict[str, int]] = defaultdict(by_stratum)
    totals = Counter()
    uncached = 0
    examples: Dict[str, List[Dict[str, Any]]] = {"located_miss": [], "untouched": []}

    for pr, record in gold_records.items():
        local_preds: List[Tuple[str, int, int, Dict[str, Any]]] = []
        for f in preds_by_pr.get(pr, []):
            path, start, end = pred_span(f)
            np = norm_path(path)
            if np and start is not None:
                local_preds.append((np, start, end or start, f))

        for g in _gold_findings(record):
            gp = norm_path((g.get("anchor") or {}).get("path"))
            gl = _gold_line(g)
            if not gp or gl is None:
                continue  # PR-level / unanchored gold is not locatable
            stratum = g["stratum"]
            strata[stratum]["gold"] += 1
            totals["gold"] += 1

            located = [
                pf for (pp, ps, pe, pf) in local_preds
                if pp == gp and ps - LINE_SLACK <= gl <= pe + LINE_SLACK
            ]
            if not located:
                strata[stratum]["untouched"] += 1
                totals["untouched"] += 1
                if len(examples["untouched"]) < 12:
                    examples["untouched"].append({
                        "pr": pr, "stratum": stratum,
                        "loc": f"{gp}:{gl}", "gold": g["body"][:160],
                    })
                continue

            verdicts = [lookup_cached(g, pf) for pf in located]
            uncached += sum(1 for v in verdicts if v is None)
            if any(v for v in verdicts):
                strata[stratum]["covered"] += 1
                totals["covered"] += 1
            else:
                strata[stratum]["located_miss"] += 1
                totals["located_miss"] += 1
                if len(examples["located_miss"]) < 12:
                    examples["located_miss"].append({
                        "pr": pr, "stratum": stratum, "loc": f"{gp}:{gl}",
                        "gold": g["body"][:160],
                        "nearby_preds": [pf["claim"][:120] for pf in located[:3]],
                    })

    def rate(part: int, whole: int) -> Optional[float]:
        return round(part / whole, 3) if whole else None

    g = totals["gold"]
    return {
        "anchored_gold": g,
        "covered": totals["covered"],
        "located_miss": totals["located_miss"],
        "untouched": totals["untouched"],
        "recall": rate(totals["covered"], g),
        "located_miss_rate": rate(totals["located_miss"], g),
        "untouched_rate": rate(totals["untouched"], g),
        # of the MISSES, how many are selection (located) vs coverage (untouched)?
        "miss_total": totals["located_miss"] + totals["untouched"],
        "selection_share_of_miss": rate(
            totals["located_miss"], totals["located_miss"] + totals["untouched"]
        ),
        "coverage_share_of_miss": rate(
            totals["untouched"], totals["located_miss"] + totals["untouched"]
        ),
        "by_stratum": {
            s: {
                **strata[s],
                "located_miss_rate": rate(strata[s]["located_miss"], strata[s]["gold"]),
                "untouched_rate": rate(strata[s]["untouched"], strata[s]["gold"]),
            }
            for s in sorted(strata)
        },
        "uncached_pairs": uncached,
        "examples": examples,
    }


def main() -> None:
    gold_records = {
        (row := json.loads(line))["pr_number"]: row
        for line in GOLD.read_text().splitlines() if line.strip()
    }
    result = {
        "gold_file": str(GOLD.relative_to(PROJECT_ROOT)),
        "line_slack": LINE_SLACK,
        "matcher_model": MATCHER_MODEL,
        "definitions": {
            "covered": "located prediction passes topical gate (recall hit)",
            "located_miss": "prediction at the gold location but topical gate rejects all "
                            "(SELECTION gap: generator reached the spot, wrong concern)",
            "untouched": "no prediction near the gold location (COVERAGE gap)",
        },
        "pools": {name: decompose_pool(gold_records, keys) for name, keys in POOLS.items()},
    }
    out = PRED_DIR / "miss_decomposition.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"wrote {out}")

    # console summary table
    print(f"\n{'pool':<28}{'gold':>5}{'cov':>5}{'loc':>5}{'unt':>5}"
          f"{'recall':>8}{'sel/miss':>9}{'cov/miss':>9}{'uncached':>9}")
    for name, r in result["pools"].items():
        print(f"{name:<28}{r['anchored_gold']:>5}{r['covered']:>5}{r['located_miss']:>5}"
              f"{r['untouched']:>5}{(r['recall'] or 0):>8.3f}"
              f"{(r['selection_share_of_miss'] or 0):>9.3f}"
              f"{(r['coverage_share_of_miss'] or 0):>9.3f}{r['uncached_pairs']:>9}")


if __name__ == "__main__":
    main()
