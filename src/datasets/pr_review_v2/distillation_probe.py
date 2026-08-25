"""Probe: does NL-distillation legibility separate maintainer-flagged findings?

Distills each PR (cached, one LLM call/PR via distillation.distill_prs), turns each
candidate finding into a legibility signal (obscurity of the proof it targets, 100 -
legibility), and measures whether that separates on- from off-target — globally and
WITHIN a PR (the selection axis) — for V2, the same way the centrality probe did. Also
reports the diff-only selector + legibility combination on the frontier.

Two artifact sources:
  - default: diff-only distillation (distill_prs, one cached LLM call/PR)
  - artifacts=<jsonl>: grounded distillation task output (distill_runner) — the fair test.

    python -m src.datasets.pr_review_v2.distillation_probe [pool=grand_union] [distill_model=gpt_5.4]
    python -m src.datasets.pr_review_v2.distillation_probe artifacts=inputs/pr_review_v2/predictions/distillations_grand_union_gpt_5.4.jsonl
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

from ape.utils import parse_cli_args
from ape.utils.logging import create_logger
from .centrality_probe import within_pr_auc
from .distillation import distill_prs, legibility_signal, load_distillations
from .selector import (
    PRED_DIR, POOLS, SELECTOR_CACHE, _selector_key, auc, build_candidates, frontier, load_gold,
)


def main() -> None:
    cli = parse_cli_args(sys.argv[1:])
    pool = cli.get("pool", "grand_union")
    distill_model = cli.get("distill_model", "gpt_5.4")
    sel_model = cli.get("selector_model", "gpt_5.4")
    artifacts_path = cli.get("artifacts")  # grounded task output; else diff-only distill
    concurrency = int(cli.get("concurrency", 8))
    logger = create_logger()

    gold = load_gold()
    cands, g2c, _ = build_candidates(gold, POOLS[pool])

    prs = sorted({c["pr"] for c in cands})
    if artifacts_path:
        source = f"grounded:{Path(artifacts_path).name}"
        arts = load_distillations(Path(artifacts_path))
    else:
        source = f"diff-only:{distill_model}"
        import asyncio
        arts = asyncio.run(distill_prs({pr: gold[pr]["input"] for pr in prs},
                                       distill_model, concurrency, logger))

    matched = 0
    for c in cands:
        art = arts.get(c["pr"])
        sig = legibility_signal(c["finding"], art)
        c["legib"] = sig
        if sig != 50.0:
            matched += 1
        cf = SELECTOR_CACHE / f"{_selector_key(c['pr'], c['finding'], sel_model)}.json"
        c["sel"] = json.loads(cf.read_text())["score"] if cf.exists() else 0.0
        c["combo"] = c["sel"] / 100.0 + 0.5 * (c["legib"] / 100.0)

    on = [c for c in cands if c["on_target"]]
    off = [c for c in cands if not c["on_target"]]
    v2 = [c for c in cands if (not c["on_target"]) or ("V2" in c["hit_strata"])]
    v2on, v2off = [c for c in v2 if c["on_target"]], [c for c in v2 if not c["on_target"]]
    n_decls = sum(len(a.declarations) for a in arts.values())
    legibs = [d.legibility for a in arts.values() for d in a.declarations]
    import statistics as st
    legib_spread = (f"min {min(legibs)} median {int(st.median(legibs))} mean {round(st.mean(legibs),1)}"
                    if legibs else "n/a")

    print(f"\npool={pool} source={source} | PRs distilled={len(arts)} (decls={n_decls}; "
          f"legibility {legib_spread}) | findings matched to a decl: {matched}/{len(cands)}\n")
    print(f"{'feature (V2)':<16}{'globalAUC':>11}{'withinPR_AUC':>14}")
    for feat in ["sel", "legib", "combo"]:
        gv = auc([c[feat] for c in v2on], [c[feat] for c in v2off])
        wv = within_pr_auc(v2, feat)
        print(f"{feat:<16}{str(gv):>11}{str(wv):>14}")

    print(f"\n{'ranker':<8}{'overallAUC':>12}{'peak_prec':>11}{'90%gold_prec':>14}")
    for k in ["sel", "combo"]:
        for c in cands:
            c["score"] = c[k]
        fr = frontier(cands, g2c)
        peak = max(p["finding_precision"] or 0 for p in fr["sweep"])
        op = fr["op_retain_90pct_gold"]
        a = auc([c[k] for c in on], [c[k] for c in off])
        print(f"{k:<8}{str(a):>12}{round(peak, 3):>11}{(op['finding_precision'] or 0):>14}")

    result = {
        "pool": pool, "source": source, "selector_model": sel_model,
        "prs_distilled": len(arts), "decls": n_decls, "findings_matched": matched,
        "legibility": legib_spread,
        "v2_auc": {f: auc([c[f] for c in v2on], [c[f] for c in v2off]) for f in ("sel", "legib", "combo")},
        "v2_within_pr_auc": {f: within_pr_auc(v2, f) for f in ("sel", "legib", "combo")},
    }
    tag = "grounded" if artifacts_path else f"diffonly_{distill_model}"
    out = PRED_DIR / f"distillation_probe_{pool}_{tag}.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
