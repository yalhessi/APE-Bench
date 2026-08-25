"""Stage 2 precompute — retrieve precedents for each eval PR's CHANGED sites (Mode A priming).

At generation time we do not know which sites a maintainer will flag, so — unlike the Stage-1
benchmark, which queried the gold site — we query EVERY changed hunk in the PR (`gold.delta_total`),
merge the retrieved precedents per PR (dedup by comment, keep the highest-scoring), and write a
precedents-by-PR file. The primed checker (BasePRReviewConfig.precedent_file) injects the top-k into
its prompt: "maintainers have said these things on similar code."

This runs fully offline (local corpus + local embedding model — no API, no cost):

  python -m src.datasets.pr_review_v2.precedent_prime            # first-20 eval PRs, dense_code
  python -m src.datasets.pr_review_v2.precedent_prime --design lexical --prs 33048 33065
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

from .precedent_bench import DEFAULT_CORPUS, RETRIEVERS, load_corpus

DEFAULT_RECORDS = PROJECT_ROOT / "inputs" / "pr_review_v2" / "mathlib_pr_review_v2_annotated_20260612.jsonl"
DEFAULT_OUT = PROJECT_ROOT / "inputs" / "pr_review_v2" / "precedent_bench" / "precedents_by_pr.jsonl"
FIRST20 = [33048, 33065, 33066, 33067, 33070, 33078, 33079, 33081, 33086, 33090,
           33092, 33098, 33101, 33104, 33111, 33117, 33127, 33137, 33141, 33145]


def _split_unified_diff(diff: str) -> List[Tuple[str, str]]:
    """Fallback site source: split a raw unified diff into per-file .lean hunks."""
    from .delta import parse_patch_hunks
    sites: List[Tuple[str, str]] = []
    path, body = None, []
    def flush():
        if path and path.endswith(".lean") and body:
            for h in parse_patch_hunks(path, "\n".join(body)):
                sites.append((path, h.patch_text))
    for line in (diff or "").splitlines():
        if line.startswith("diff --git"):
            flush(); path, body = None, []
        elif line.startswith("+++ b/"):
            path = line[6:].strip()
        elif path is not None:
            body.append(line)
    flush()
    return sites


def changed_sites(rec: Dict[str, Any]) -> List[Tuple[str, str]]:
    """(path, hunk-patch) for every changed hunk in the PR — the sites a reviewer would look at.
    Prefer the drift-proof `delta_total`; fall back to splitting the raw diff when it is empty."""
    sites = [(h.get("path"), h.get("patch") or "")
             for h in (rec.get("gold", {}).get("delta_total") or []) if h.get("patch")]
    if sites:
        return sites
    return _split_unified_diff((rec.get("input") or {}).get("diff") or "")


def build(prs, records_path, corpus_path, design, per_hunk_k, keep, out, logger) -> Path:
    recs = {json.loads(l)["pr_number"]: json.loads(l)
            for l in records_path.read_text().splitlines() if l.strip()}
    corpus = load_corpus(corpus_path)
    logger.info("Priming %d PRs against %d corpus situations (design=%s)", len(prs), len(corpus), design)
    retriever = RETRIEVERS[design](corpus, logger=logger)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for pr in prs:
            rec = recs.get(pr)
            if not rec:
                logger.warning("PR %d not in records — skipping", pr)
                continue
            sites = changed_sites(rec)
            merged: Dict[Any, Tuple[float, Dict[str, Any], str]] = {}
            for path, patch in sites:
                for idx, score in retriever.retrieve({"site_code": patch}, per_hunk_k):
                    c = corpus[idx]
                    cid = c.get("comment_id")
                    if cid not in merged or score > merged[cid][0]:
                        merged[cid] = (score, c, path)
            ranked = sorted(merged.values(), key=lambda x: -x[0])[:keep]
            precs = [{
                "comment_id": c.get("comment_id"), "pr_number": c.get("pr_number"),
                "path": c.get("path"), "score": round(float(s), 5),
                "precedent_body": c.get("body") or "", "precedent_code": c.get("diff_hunk") or "",
                "commenter": c.get("commenter"), "matched_site_path": mp,
            } for s, c, mp in ranked]
            fh.write(json.dumps({"pr_number": pr, "precedents": precs}, ensure_ascii=False) + "\n")
            logger.info("  PR %d: %d changed sites -> %d precedents (top score %.3f)",
                        pr, len(sites), len(precs), precs[0]["score"] if precs else 0.0)
    logger.info("Wrote precedents-by-PR -> %s", out)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 2: precompute per-PR precedents for Mode A priming")
    p.add_argument("--prs", type=int, nargs="*", default=FIRST20)
    p.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    p.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    p.add_argument("--design", default="dense_code", choices=sorted(RETRIEVERS))
    p.add_argument("--per-hunk-k", type=int, default=5, help="top-k precedents retrieved per changed hunk")
    p.add_argument("--keep", type=int, default=12, help="max precedents kept per PR (inject <= this)")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = p.parse_args()
    logger = create_logger()
    build(args.prs, args.records, args.corpus, args.design, args.per_hunk_k, args.keep, args.out, logger)


if __name__ == "__main__":
    main()
