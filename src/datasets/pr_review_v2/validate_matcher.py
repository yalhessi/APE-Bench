"""
Score the hand-validated matcher sample (Step 4 freeze gate).

The researcher fills `human_same_issue` (true/false) in the blind sample file,
then this joins it back to the matcher's decisions and reports agreement.

Usage:
  python -m src.datasets.pr_review_v2.validate_matcher \
      inputs/pr_review_v2/annotations/matcher_validation_sample.jsonl \
      inputs/pr_review_v2/predictions/<preds>_d2_llm_pairs.jsonl
"""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Score matcher hand-validation sample")
    parser.add_argument("sample", type=Path)
    parser.add_argument("pairs", type=Path)
    args = parser.parse_args()

    sample = [json.loads(l) for l in args.sample.read_text().splitlines() if l.strip()]
    pairs = [json.loads(l) for l in args.pairs.read_text().splitlines() if l.strip()]
    matcher = {(p["pr_number"], p["gold_id"], p["pred_claim"]): p for p in pairs}

    unfilled = [s["idx"] for s in sample if s.get("human_same_issue") is None]
    if unfilled:
        print(f"{len(unfilled)} rows still unfilled (idx: {unfilled[:10]}…)")
        return

    tp = fp = fn = tn = 0
    disagreements = []
    for s in sample:
        pair = matcher[(s["pr_number"], s["gold_id"], s["pred_claim"])]
        human, model = bool(s["human_same_issue"]), bool(pair["accepted"])
        if human and model:
            tp += 1
        elif human and not model:
            fn += 1
        elif not human and model:
            fp += 1
        else:
            tn += 1
        if human != model:
            disagreements.append(
                {"idx": s["idx"], "pr": s["pr_number"], "human": human, "matcher": model,
                 "gold": s["gold_body"][:120], "pred": s["pred_claim"][:120],
                 "matcher_reason": pair.get("reason", "")[:120]}
            )

    n = len(sample)
    print(json.dumps({
        "pairs_scored": n,
        "agreement": round((tp + tn) / n, 3),
        "matcher_precision_vs_human": round(tp / (tp + fp), 3) if tp + fp else None,
        "matcher_recall_vs_human": round(tp / (tp + fn), 3) if tp + fn else None,
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }, indent=2))
    if disagreements:
        print("\nDisagreements (matcher vs you):")
        for d in disagreements:
            print(f"  [{d['idx']}] PR {d['pr']} human={d['human']} matcher={d['matcher']}")
            print(f"      GOLD: {d['gold']}")
            print(f"      PRED: {d['pred']}")
            print(f"      WHY : {d['matcher_reason']}")


if __name__ == "__main__":
    main()
