"""Phase B evaluator — tiered metrics over intervention gold (redesign spec §3).

The three separable capabilities, scored separately (the single fused number smeared them and
produced this week's confusions — apply-all "regression", priming "wins"):

  T1 identification — the system produced at least one finding co-located with the intervention
                      (any anchor, ±slack). Measures site/concern attempt, no content judgment.
  T2 instantiation  — given T1: issue-match rate and resolution-match rate (judge.py, two-level).
  T3 selection      — the system's top-k findings per PR (k≈3, maintainer volume): precision of
                      the selected findings and intervention-recall through them. This is where
                      a flood is punished and where selection ideas get measured.

Axes: stratum, outcome (headline = adopted + partially_adopted), plus PR-level bootstrap CIs —
the ±5-covered noise floor is reported, not folklore. Denominators are judgeable, non-meta
interventions. Every run writes an audit sample (10 accepted + 10 rejected pairs) for the standing
hand-verification gate.

  python -m src.datasets.pr_review_v3.evaluate_tiers \\
      inputs/pr_review_v3/interventions_v4.jsonl \\
      inputs/pr_review_v2/predictions/preds_instantiate_all_gpt_5.2_run1b.jsonl
"""

import argparse
import asyncio
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ape.utils.logging import create_logger

from src.datasets.pr_review_v2.evaluate_d2 import _norm_path, _pred_span
from .judge import judge_pairs

HEADLINE_OUTCOMES = {"adopted", "partially_adopted"}


# ---------------------------------------------------------------------------
# pairing
# ---------------------------------------------------------------------------

def filter_evaluable(interventions: List[Dict[str, Any]],
                     preds_by_pr: Dict[int, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Restrict gold to PRs the system actually reviewed. The intervention gold covers every
    comment-bearing PR in the records, but a prediction set covers only its run's PR list —
    interventions on unreviewed PRs are unreachable by construction and must not deflate
    denominators (they silently cost ~6 T1 points in the first allv2 reports)."""
    inrun = [iv for iv in interventions if iv["pr_number"] in preds_by_pr]
    excluded = [iv for iv in interventions if iv["pr_number"] not in preds_by_pr]
    return inrun, excluded


def co_located(iv: Dict[str, Any], finding: Dict[str, Any], slack: int) -> Tuple[bool, str]:
    """Does the finding overlap ANY anchor of the intervention (±slack)? Unanchored interventions
    accept any finding on the PR (PR-level asks). Returns (hit, line_gap_desc)."""
    anchors = iv.get("anchors") or []
    path, ls, le = _pred_span(finding)
    if not anchors:
        return True, "n/a (unanchored intervention — PR-level pairing)"
    if not (path and ls):
        return False, ""
    best: Optional[int] = None
    for a in anchors:
        if _norm_path(a.get("path") or "") != _norm_path(path):
            continue
        gap = max(int(a["line_start"]) - (le or ls), ls - int(a["line_end"]), 0)
        best = gap if best is None else min(best, gap)
    return (best is not None and best <= slack), (str(best) if best is not None else "different file")


def build_pairs(interventions: List[Dict[str, Any]], preds_by_pr: Dict[int, Dict[str, Any]],
                slack: int) -> List[Dict[str, Any]]:
    pairs = []
    for iv in interventions:
        p = preds_by_pr.get(iv["pr_number"])
        for f in ((p or {}).get("findings") or []):
            hit, gap = co_located(iv, f, slack)
            if not hit:
                continue
            path, ls, _le = _pred_span(f)
            pairs.append({"iv": iv, "pred": f,
                          "pred_loc": f"{path}:{ls}" if path else "PR-level",
                          "line_gap": gap})
    return pairs


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------

def _select_top_k(findings: List[Dict[str, Any]], k: int) -> List[int]:
    """Indices of the PR's top-k findings: confidence desc (None last), stable order."""
    order = sorted(range(len(findings)),
                   key=lambda i: (-(findings[i].get("confidence") if findings[i].get("confidence")
                                    is not None else -1.0), i))
    return order[:k]


def tier_metrics(interventions: List[Dict[str, Any]], preds_by_pr: Dict[int, Dict[str, Any]],
                 pairs: List[Dict[str, Any]], k: int) -> Dict[str, Any]:
    by_iv: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in pairs:
        by_iv[p["iv"]["intervention_id"]].append(p)

    # per-PR top-k membership (by identity of the finding dicts)
    topk_ids: Dict[int, set] = {}
    for pr, p in preds_by_pr.items():
        fs = p.get("findings") or []
        topk_ids[pr] = {id(fs[i]) for i in _select_top_k(fs, k)}

    per_iv = []
    for iv in interventions:
        ps = by_iv.get(iv["intervention_id"], [])
        t1 = bool(ps)
        issue = any(x.get("issue_match") for x in ps)
        resolution = any(x.get("resolution_match") for x in ps)
        sel = topk_ids.get(iv["pr_number"], set())
        issue_at_k = any(x.get("issue_match") and id(x["pred"]) in sel for x in ps)
        per_iv.append({"iv": iv, "t1": t1, "issue": issue, "resolution": resolution,
                       "issue_at_k": issue_at_k})

    def rates(sel: List[Dict[str, Any]]) -> Dict[str, Any]:
        n = len(sel)
        if not n:
            return {"n": 0}
        t1 = sum(x["t1"] for x in sel)
        iss = sum(x["issue"] for x in sel)
        res = sum(x["resolution"] for x in sel)
        isk = sum(x["issue_at_k"] for x in sel)
        return {"n": n,
                "T1_identified": f"{t1}/{n} ({100*t1/n:.0f}%)",
                "T2_issue": f"{iss}/{n} ({100*iss/n:.0f}%)",
                "T2_issue_given_T1": f"{iss}/{t1} ({100*iss/max(t1,1):.0f}%)",
                "T2_resolution": f"{res}/{n} ({100*res/n:.0f}%)",
                "T3_issue_at_top%d" % k: f"{isk}/{n} ({100*isk/n:.0f}%)"}

    report: Dict[str, Any] = {"overall": rates(per_iv)}
    report["headline_adopted"] = rates([x for x in per_iv
                                        if x["iv"]["outcome"] in HEADLINE_OUTCOMES])
    for strat in sorted({x["iv"]["stratum"] for x in per_iv}):
        report.setdefault("by_stratum", {})[strat] = rates(
            [x for x in per_iv if x["iv"]["stratum"] == strat])
    for oc in sorted({x["iv"]["outcome"] for x in per_iv}):
        report.setdefault("by_outcome", {})[oc] = rates(
            [x for x in per_iv if x["iv"]["outcome"] == oc])

    # T3 precision: of the selected top-k findings (PRs with >=1 intervention), how many
    # issue-match some intervention?
    sel_total = sel_hit = 0
    iv_prs = {iv["pr_number"] for iv in interventions}
    hit_ids = {id(x["pred"]) for x in pairs if x.get("issue_match")}
    for pr in iv_prs:
        for fid in topk_ids.get(pr, set()):
            sel_total += 1
            sel_hit += fid in hit_ids
    report["T3_precision_at_top%d" % k] = f"{sel_hit}/{sel_total} ({100*sel_hit/max(sel_total,1):.0f}%)"

    report["_per_iv"] = [{"intervention_id": x["iv"]["intervention_id"], "t1": x["t1"],
                          "issue": x["issue"], "resolution": x["resolution"],
                          "issue_at_k": x["issue_at_k"]} for x in per_iv]
    return report


def bootstrap_ci(per_iv: List[Dict[str, Any]], key: str, iters: int = 1000,
                 seed: int = 0) -> Tuple[float, float, float]:
    """PR-level bootstrap 95% CI on an intervention-coverage rate."""
    by_pr: Dict[int, List[bool]] = defaultdict(list)
    for x in per_iv:
        by_pr[x["iv"]["pr_number"] if isinstance(x["iv"], dict) else x["iv"]].append(bool(x[key]))
    prs = list(by_pr)
    rng = random.Random(seed)
    stats = []
    for _ in range(iters):
        sample = [rng.choice(prs) for _ in prs]
        vals = [v for pr in sample for v in by_pr[pr]]
        stats.append(sum(vals) / len(vals) if vals else 0.0)
    stats.sort()
    point = sum(v for vs in by_pr.values() for v in vs) / max(sum(len(vs) for vs in by_pr.values()), 1)
    return point, stats[int(0.025 * iters)], stats[int(0.975 * iters)]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Tiered evaluation against intervention gold (i1)")
    ap.add_argument("interventions", type=Path)
    ap.add_argument("predictions", type=Path)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--slack", type=int, default=10)
    ap.add_argument("--model", default="gpt_5_mini")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--audit", type=int, default=10, help="pairs per verdict class in the audit sample")
    args = ap.parse_args()
    logger = create_logger()

    all_iv = [json.loads(l) for l in args.interventions.read_text().splitlines() if l.strip()]
    interventions = [iv for iv in all_iv if iv.get("judgeable") and not iv.get("meta")]
    preds_by_pr = {r["pr_number"]: r for r in
                   (json.loads(l) for l in args.predictions.read_text().splitlines() if l.strip())}
    interventions, out_of_run = filter_evaluable(interventions, preds_by_pr)
    logger.info("Interventions: %d total | %d judgeable non-meta | %d evaluable (%d on PRs outside "
                "this run's prediction set — excluded from denominators)",
                len(all_iv), len(interventions) + len(out_of_run), len(interventions),
                len(out_of_run))

    pairs = build_pairs(interventions, preds_by_pr, args.slack)
    logger.info("Co-located pairs: %d", len(pairs))
    asyncio.run(judge_pairs(pairs, model=args.model, concurrency=args.concurrency, logger=logger))

    report = tier_metrics(interventions, preds_by_pr, pairs, args.k)
    # provenance — the v4/v5 gold-version confound went unnoticed because reports carried none
    from datetime import datetime, timezone
    from .judge import JUDGE_PROMPT_VERSION
    report["_provenance"] = {
        "gold_file": str(args.interventions),
        "gold_schema": (all_iv[0].get("schema_version") if all_iv else None),
        "judge_version": JUDGE_PROMPT_VERSION,
        "judge_model": args.model,
        "predictions_file": str(args.predictions),
        "k": args.k, "slack": args.slack,
        "evaluable_interventions": len(interventions),
        "excluded_out_of_run": len(out_of_run),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    per_iv_full = [{"iv": next(i for i in interventions if i["intervention_id"] == x["intervention_id"]),
                    **x} for x in report["_per_iv"]]
    for key in ("issue", "resolution"):
        pt, lo, hi = bootstrap_ci(per_iv_full, key)
        report[f"ci95_{key}"] = f"{100*pt:.0f}% [{100*lo:.0f}%, {100*hi:.0f}%]"

    stem = args.predictions.stem
    out = args.predictions.parent / f"{stem}_i1_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    # standing audit sample (spec gate: hand-verify before using the numbers)
    rng = random.Random(1)
    acc = [p for p in pairs if p.get("issue_match")]
    rej = [p for p in pairs if not p.get("issue_match")]
    sample = rng.sample(acc, min(args.audit, len(acc))) + rng.sample(rej, min(args.audit, len(rej)))
    audit_file = args.predictions.parent / f"{stem}_i1_audit.jsonl"
    with audit_file.open("w") as fh:
        for p in sample:
            fh.write(json.dumps({
                "intervention_id": p["iv"]["intervention_id"], "ask": p["iv"]["canonical_ask"],
                "claim": p["pred"].get("claim"), "fix": p["pred"].get("suggested_fix"),
                "issue_match": p.get("issue_match"), "resolution_match": p.get("resolution_match"),
                "reason": p.get("reason")}, ensure_ascii=False) + "\n")

    summary = {k2: v for k2, v in report.items() if k2 not in ("_per_iv",)}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    logger.info("Report: %s | audit sample: %s", out, audit_file)


if __name__ == "__main__":
    main()
