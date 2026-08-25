"""Mode-B gate experiment — does precedent-neighbor similarity predict WHERE maintainers engage?

The site-first pipeline (enumerate all changed sites -> data-driven concern prior -> instantiate)
stands or falls on one question, answerable offline: within a PR, do the sites maintainers actually
flagged sit closer to the historical maintainer-comment corpus than the sites they left silent?

Setup: for each gold-bearing PR, enumerate every changed hunk (site). A site is FLAGGED if some
actionable gold comment links to it (`linked_hunks`), else SILENT. Score each site by its dense
similarity to the corpus of historical commented hunks (several designs). Then, within each PR,
ask how well the score separates flagged from silent.

Reported:
  - within-PR AUC (flagged vs silent), pooled and per PR
  - recall@m: if we only instantiated findings at the top-m sites per PR, what fraction of flagged
    sites (and of gold comments, per stratum) would be in scope — the pipeline's recall CEILING
  - a random-ranking baseline for both (permutation), since PRs where most sites are flagged make
    even random ranking look good.

Fully offline: local embedding model + corpus + gold. No API.

  python -m src.datasets.pr_review_v2.site_discrimination
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

from .precedent_bench import DEFAULT_CORPUS, hunk_code, load_corpus

DEFAULT_RECORDS = PROJECT_ROOT / "inputs" / "pr_review_v2" / "mathlib_pr_review_v2_annotated_20260612.jsonl"
OUT_DIR = PROJECT_ROOT / "inputs" / "pr_review_v2" / "precedent_bench"
ACTIONABLE_STRATA = {"V1", "V2", "V3", "V4"}


# ---------------------------------------------------------------------------
# sites + labels
# ---------------------------------------------------------------------------

def pr_sites(rec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Every changed hunk in the PR, labelled flagged/silent from the gold comments' linked hunks.
    Only actionable (V1-V4) comments count as flags; strata of the flags are kept for reporting."""
    gold = rec.get("gold") or {}
    flags: Dict[str, List[str]] = defaultdict(list)  # hunk_id -> [stratum, ...]
    for c in (gold.get("comments") or []):
        if (c.get("stratum") or "") not in ACTIONABLE_STRATA:
            continue
        for h in (c.get("linked_hunks") or []):
            flags[h].append(c.get("stratum"))
    sites = []
    for h in (gold.get("delta_total") or []):
        hid, patch = h.get("hunk_id"), h.get("patch") or ""
        if not hid or not patch.strip():
            continue
        sites.append({
            "hunk_id": hid,
            "path": h.get("path"),
            "code": hunk_code(patch),
            "flagged": hid in flags,
            "strata": flags.get(hid, []),
        })
    return sites


# ---------------------------------------------------------------------------
# scoring designs — similarity of a site to the historical commented corpus
# ---------------------------------------------------------------------------

def score_sites(all_sites: List[Dict[str, Any]], corpus, k: int, logger) -> None:
    """Attach neighbor-similarity scores (in place). One batched embed of all sites."""
    from sentence_transformers import SentenceTransformer
    import numpy as np

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    corpus_texts = [hunk_code(c.get("diff_hunk") or "") for c in corpus]
    logger.info("Embedding %d corpus hunks + %d sites", len(corpus_texts), len(all_sites))
    emb_c = model.encode(corpus_texts, normalize_embeddings=True, batch_size=256)
    emb_s = model.encode([s["code"] for s in all_sites], normalize_embeddings=True, batch_size=256)
    sims = emb_s @ emb_c.T  # (n_sites, n_corpus)
    top = np.sort(sims, axis=1)[:, -k:]  # ascending; last k are the top-k
    for i, s in enumerate(all_sites):
        s["score_top1"] = float(top[i, -1])
        s["score_meank"] = float(top[i].mean())


# ---------------------------------------------------------------------------
# within-PR evaluation
# ---------------------------------------------------------------------------

def within_pr_auc(sites: List[Dict[str, Any]], key: str) -> float:
    """AUC of `key` separating flagged from silent within one PR (needs both classes)."""
    pos = [s[key] for s in sites if s["flagged"]]
    neg = [s[key] for s in sites if not s["flagged"]]
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def recall_at_m(by_pr: Dict[int, List[Dict[str, Any]]], key: str, m: int) -> float:
    """Fraction of flagged sites that fall in each PR's top-m sites by `key`."""
    hit = tot = 0
    for sites in by_pr.values():
        ranked = sorted(sites, key=lambda s: -s[key])
        top = set(id(s) for s in ranked[:m])
        for s in sites:
            if s["flagged"]:
                tot += 1
                hit += id(s) in top
    return hit / tot if tot else float("nan")


def random_recall_at_m(by_pr: Dict[int, List[Dict[str, Any]]], m: int, iters: int = 200) -> float:
    rng = random.Random(0)
    acc = []
    for _ in range(iters):
        hit = tot = 0
        for sites in by_pr.values():
            order = list(sites)
            rng.shuffle(order)
            top = set(id(s) for s in order[:m])
            for s in sites:
                if s["flagged"]:
                    tot += 1
                    hit += id(s) in top
        acc.append(hit / tot if tot else 0.0)
    return sum(acc) / len(acc)


def main() -> None:
    p = argparse.ArgumentParser(description="Site-level discrimination test (Mode-B gate)")
    p.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    p.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    p.add_argument("--k", type=int, default=10, help="neighbors per site for the mean-k score")
    p.add_argument("--ms", type=int, nargs="*", default=[1, 2, 3, 5])
    args = p.parse_args()
    logger = create_logger()

    recs = [json.loads(l) for l in args.records.read_text().splitlines() if l.strip()]
    by_pr: Dict[int, List[Dict[str, Any]]] = {}
    for r in recs:
        sites = pr_sites(r)
        if sites and any(s["flagged"] for s in sites):
            by_pr[r["pr_number"]] = sites
    all_sites = [s for sites in by_pr.values() for s in sites]
    n_flag = sum(s["flagged"] for s in all_sites)
    logger.info("PRs with >=1 flagged site: %d | sites: %d (%d flagged, %d silent)",
                len(by_pr), len(all_sites), n_flag, len(all_sites) - n_flag)

    corpus = load_corpus(args.corpus)
    score_sites(all_sites, corpus, args.k, logger)

    report: Dict[str, Any] = {"n_prs": len(by_pr), "n_sites": len(all_sites), "n_flagged": n_flag}
    for key in ("score_top1", "score_meank"):
        aucs = [a for sites in by_pr.values() if (a := within_pr_auc(sites, key)) == a]  # drop NaN
        report[key] = {
            "mean_within_pr_auc": round(sum(aucs) / len(aucs), 3) if aucs else None,
            "prs_with_both_classes": len(aucs),
            "recall_at_m": {m: round(recall_at_m(by_pr, key, m), 3) for m in args.ms},
        }
        logger.info("[%s] mean within-PR AUC=%.3f over %d PRs | recall@m: %s",
                    key, report[key]["mean_within_pr_auc"] or float("nan"), len(aucs),
                    report[key]["recall_at_m"])
    report["random_baseline_recall_at_m"] = {m: round(random_recall_at_m(by_pr, m), 3) for m in args.ms}
    logger.info("[random] recall@m: %s", report["random_baseline_recall_at_m"])

    # per-stratum recall@m for the better design (meank), counting each flag stratum instance
    key = "score_meank"
    strat_hit: Dict[str, List[int]] = defaultdict(list)
    for m in args.ms:
        for sites in by_pr.values():
            ranked = sorted(sites, key=lambda s: -s[key])
            top = set(id(s) for s in ranked[:m])
            for s in sites:
                for st in s["strata"]:
                    strat_hit[f"{st}@{m}"].append(id(s) in top)
    report["per_stratum_recall_meank"] = {
        k2: f"{sum(v)}/{len(v)} ({100*sum(v)/len(v):.0f}%)" for k2, v in sorted(strat_hit.items())
    }
    for k2, v in sorted(report["per_stratum_recall_meank"].items()):
        logger.info("  %s: %s", k2, v)

    out = OUT_DIR / "site_discrimination_report.json"
    out.write_text(json.dumps(report, indent=2))
    logger.info("Report -> %s", out)


if __name__ == "__main__":
    main()
