"""Selector upper-bound: can a judge separate the on-target findings from the
off-target flood in an eager candidate pool?

The miss decomposition showed most misses are SELECTION gaps (the candidate sits at
the maintainer's exact line, wrong concern) — so the lever is a selector that keeps the
maintainer-worthy findings and drops the rest. This measures the *ceiling* of that lever:

  - LABEL each pooled prediction on-target (covers a gold finding) / off-target, using the
    frozen topical-judge cache (no new API for labels).
  - SCORE each prediction with an LLM selector that sees the PR (title/description/diff) and
    the finding only — NOT the gold, NOT the other findings — and estimates the probability a
    Mathlib maintainer would actually raise it. This is a *realizable* per-finding selector.
  - Measure separability: AUC of score vs on-target label, and the gold-recall / finding-
    precision frontier as the score threshold sweeps, against the no-selector baseline.

High AUC => the gold is separable from the off-target pile => a selector recovers precision at
~constant recall (the hoped Pareto win). AUC ~0.5 => maintainer selection is NOT predictable
from finding content + PR context => a deeper finding (the signal lives elsewhere).

Scores are cached (sidecar per pool/model/prompt), so re-runs are free and auditable.

Usage:
  python -m src.datasets.pr_review_v2.selector            # default: gpt_5.2 holistic pool
  python -m src.datasets.pr_review_v2.selector pool=grand_union selector_model=gpt_5.4
"""

import argparse
import asyncio
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ape.utils import parse_cli_args
from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT
from .evaluate_d2 import _gold_findings, _gold_line, norm_path, _pair_cache_key, pred_span

PRED_DIR = PROJECT_ROOT / "inputs" / "pr_review_v2" / "predictions"
GOLD = PROJECT_ROOT / "inputs" / "pr_review_v2" / "mathlib_pr_review_v2_actionable_20260618.jsonl"
TOPICAL_CACHE = PROJECT_ROOT / "data" / "pr_review_v2" / "cache" / "matcher"
SELECTOR_CACHE = PROJECT_ROOT / "data" / "pr_review_v2" / "cache" / "selector"
TOPICAL_MODEL = "gpt_5_mini"
LINE_SLACK = 10
DIFF_CAP = 12000

SELECTOR_PROMPT_VERSION = "v1"

SELECTOR_PROMPT = """You are estimating whether a Mathlib maintainer would actually RAISE a particular
review comment on a pull request.

Crucial context: Mathlib maintainers are highly SELECTIVE. On any PR there are many *valid*
improvements (a proof could be golfed, a lemma could be more general, a name could be tweaked) that a
maintainer will simply NOT comment on — they raise only the ones worth the author's time given this
PR's scope and the surrounding code. Your job is not "is this finding correct?" but "is this the kind
of specific issue a maintainer would bother to flag HERE?".

## Pull request
Title: {title}
{description}

## Diff
{diff}

## Candidate review finding
Location: {loc}
Severity (as labelled by the generator): {severity}
Claim: {claim}
Suggested fix: {fix}

Estimate the probability (0-100) that a Mathlib maintainer reviewing this PR would actually raise THIS
specific finding (same place, same concern). Be calibrated: most valid-but-minor findings score low;
reserve high scores for issues a maintainer would genuinely stop to request.

Answer with one JSON object: {{"score": <0-100 integer>, "reason": "<one short sentence>"}}"""


LISTWISE_PROMPT_VERSION = "v1"

SELECTOR_LISTWISE_PROMPT = """You are a Mathlib maintainer triaging a pull request. Below is the PR and a
LIST of candidate review findings (produced by automated reviewers). Maintainers are highly SELECTIVE:
on a typical PR they raise only a FEW comments and let many *valid* improvements pass. Your job is to
decide, COMPARATIVELY across this list, which findings you would actually raise on THIS PR — the ones
worth the author's time given the PR's scope and the surrounding code — vs the valid-but-not-worth-it
rest.

## Pull request
Title: {title}
{description}

## Diff
{diff}

## Candidate findings
{findings_block}

For EACH finding, give the probability (0-100) that you would actually raise it as a review comment.
Be selective and comparative: spread the scores, reserve high values for the few you would truly flag.

Answer with one JSON object mapping each finding id (as a string) to its integer score, e.g.
{{"1": 70, "2": 5, "3": 30, ...}}. Include every id."""


# --------------------------------------------------------------------------- pools

RUNS: Dict[str, str] = {
    "gpt_5.4 holistic": "preds_gpt_5.4_workspace_20260618145045",
    "gpt_5.4 guidelines": "preds_gpt_5.4_workspace_20260618150029",
    "gpt_5.4 composed": "preds_gpt_5.4_composed_20260618164852",
    "gpt_5.2 holistic": "preds_gpt52_holistic",
    "gpt_5.2 guidelines": "preds_gpt52_guidelines",
    "gpt_5.2 composed": "preds_gpt52_composed",
}
POOLS: Dict[str, List[str]] = {
    "gpt52_holistic": ["gpt_5.2 holistic"],
    "gpt54_union": ["gpt_5.4 holistic", "gpt_5.4 composed"],
    "grand_union": list(RUNS.keys()),
}


def load_gold() -> Dict[int, Dict[str, Any]]:
    return {
        (r := json.loads(l))["pr_number"]: r
        for l in GOLD.read_text().splitlines() if l.strip()
    }


def topical_accept(gold: Dict[str, Any], pred: Dict[str, Any]) -> Optional[bool]:
    key = _pair_cache_key(gold, pred, TOPICAL_MODEL)
    f = TOPICAL_CACHE / f"{key}.json"
    if not f.exists():
        return None
    return bool(json.loads(f.read_text())["same_issue"])


def build_candidates(
    gold_records: Dict[int, Dict[str, Any]], pool_keys: List[str]
) -> Tuple[List[Dict[str, Any]], Dict[int, List[int]], int]:
    """Return (candidates, covered_gold->list of on-target cand indices, n_uncached_labels).

    Each candidate: {pr, finding, on_target, gold_hits:[gid]}. on_target via the frozen
    topical cache (located within slack AND same-concern).
    """
    # pool findings by PR
    by_pr: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for key in pool_keys:
        path = PRED_DIR / f"{RUNS[key]}.jsonl"
        for rec in (json.loads(l) for l in path.read_text().splitlines() if l.strip()):
            if not rec.get("parse_ok"):
                continue
            for f in rec.get("findings") or []:
                by_pr[rec["pr_number"]].append(f)

    candidates: List[Dict[str, Any]] = []
    gold_to_cands: Dict[int, List[int]] = defaultdict(list)
    gid_counter = 0
    uncached = 0

    for pr, record in gold_records.items():
        golds = []
        for g in _gold_findings(record):
            gp = norm_path((g.get("anchor") or {}).get("path"))
            gl = _gold_line(g)
            if gp and gl is not None:
                golds.append((gid_counter, g, gp, gl))
                gid_counter += 1

        for f in by_pr.get(pr, []):
            path, start, end = pred_span(f)
            np = norm_path(path)
            ci = len(candidates)
            cand = {"ci": ci, "pr": pr, "finding": f, "on_target": False,
                    "gold_hits": [], "hit_strata": []}
            if np and start is not None:
                for gid, g, gp, gl in golds:
                    if np == gp and start - LINE_SLACK <= gl <= (end or start) + LINE_SLACK:
                        acc = topical_accept(g, f)
                        if acc is None:
                            uncached += 1
                        elif acc:
                            cand["on_target"] = True
                            cand["gold_hits"].append(gid)
                            cand["hit_strata"].append(g["stratum"])
                            gold_to_cands[gid].append(ci)
            candidates.append(cand)

    return candidates, dict(gold_to_cands), uncached


# --------------------------------------------------------------------------- LLM selector

def _selector_key(pr: int, finding: Dict[str, Any], model: str) -> str:
    payload = json.dumps(
        [pr, finding.get("claim"), finding.get("suggested_fix"), finding.get("anchor") or {},
         model, SELECTOR_PROMPT_VERSION],
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.md5(payload.encode()).hexdigest()


async def score_candidates(
    candidates: List[Dict[str, Any]], gold_records: Dict[int, Dict[str, Any]],
    model: str, concurrency: int, logger,
) -> int:
    from ape.llm_clients.client import LLMClient
    from ape.llm_clients.config import LLMConfig
    from ape.llm_clients.models import ContentBlock, ConversationSession
    from src.mathlib_review.model_output import extract_json_object

    SELECTOR_CACHE.mkdir(parents=True, exist_ok=True)
    pending = []
    for c in candidates:
        key = _selector_key(c["pr"], c["finding"], model)
        cf = SELECTOR_CACHE / f"{key}.json"
        if cf.exists():
            c["score"] = json.loads(cf.read_text())["score"]
        else:
            pending.append((c, cf))
    logger.info("Selector: %d cached, %d to score", len(candidates) - len(pending), len(pending))
    if not pending:
        return 0

    sem = asyncio.Semaphore(concurrency)

    async def one(c: Dict[str, Any], cf: Path, client) -> None:
        rec = gold_records[c["pr"]]
        inp = rec["input"]
        f = c["finding"]
        path, start, end = pred_span(f)
        prompt = SELECTOR_PROMPT.format(
            title=inp.get("title", ""),
            description=(inp.get("description") or "")[:1500],
            diff=inp["diff"][:DIFF_CAP],
            loc=f"{path}:{start}" if path else "PR-level",
            severity=f.get("severity", "?"),
            claim=f.get("claim", "")[:1200],
            fix=(f.get("suggested_fix") or "—")[:800],
        )
        async with sem:
            s = ConversationSession()
            s.add_user_message([ContentBlock.text_block(prompt)], cwd=str(PROJECT_ROOT))
            nodes, _u, _ = await client.call_api(
                s, max_tokens=1500, thinking_budget_tokens=512,
                meta_info={"task": "pr_review_v2_selector"},
            )
            text = "\n".join(b.text for n in nodes for b in n.message.content
                             if b.type == "text" and b.text)
        try:
            v = extract_json_object(text)
            score = float(v.get("score"))
            reason = str(v.get("reason") or "")
        except (ValueError, TypeError):
            score, reason = 0.0, f"unparseable: {text[:80]}"
        c["score"] = score
        cf.write_text(json.dumps({"score": score, "reason": reason}))

    cfg = LLMConfig(model_name=model, max_tokens=1500, thinking_budget_tokens=512)
    async with LLMClient(cfg, logger=logger) as client:
        await asyncio.gather(*(one(c, cf, client) for c, cf in pending))
    return len(pending)


def _finding_hash(finding: Dict[str, Any]) -> str:
    payload = json.dumps([finding.get("claim"), finding.get("suggested_fix"),
                          finding.get("anchor") or {}], sort_keys=True, ensure_ascii=False)
    return hashlib.md5(payload.encode()).hexdigest()[:12]


def _listwise_key(pr: int, findings: List[Dict[str, Any]], model: str) -> str:
    payload = json.dumps([pr, sorted(_finding_hash(f) for f in findings), model,
                          LISTWISE_PROMPT_VERSION], sort_keys=True, ensure_ascii=False)
    return hashlib.md5(payload.encode()).hexdigest()


async def score_candidates_listwise(
    candidates: List[Dict[str, Any]], gold_records: Dict[int, Dict[str, Any]],
    model: str, concurrency: int, logger,
) -> int:
    """One call PER PR: show all of a PR's candidate findings together, score each
    comparatively (maintainer triage). Cached per (pr, finding-set, model)."""
    from ape.llm_clients.client import LLMClient
    from ape.llm_clients.config import LLMConfig
    from ape.llm_clients.models import ContentBlock, ConversationSession
    from src.mathlib_review.model_output import extract_json_object

    SELECTOR_CACHE.mkdir(parents=True, exist_ok=True)
    by_pr: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for c in candidates:
        by_pr[c["pr"]].append(c)

    pending = []  # (pr, cands, cache_file)
    for pr, cands in by_pr.items():
        cf = SELECTOR_CACHE / f"lw_{_listwise_key(pr, [c['finding'] for c in cands], model)}.json"
        if cf.exists():
            scores = json.loads(cf.read_text())["scores"]  # finding_hash -> score
            for c in cands:
                c["score"] = scores.get(_finding_hash(c["finding"]), 0.0)
        else:
            pending.append((pr, cands, cf))
    logger.info("Listwise selector: %d PRs cached, %d to score", len(by_pr) - len(pending), len(pending))
    if not pending:
        return 0

    sem = asyncio.Semaphore(concurrency)

    async def one_pr(pr: int, cands: List[Dict[str, Any]], cf: Path, client) -> None:
        rec = gold_records[pr]
        inp = rec["input"]
        lines = []
        for i, c in enumerate(cands, 1):
            f = c["finding"]
            path, start, _ = pred_span(f)
            lines.append(f"[{i}] ({path}:{start}; {f.get('severity','?')}) {f.get('claim','')[:400]}"
                         + (f"  Fix: {f['suggested_fix'][:200]}" if f.get("suggested_fix") else ""))
        prompt = SELECTOR_LISTWISE_PROMPT.format(
            title=inp.get("title", ""), description=(inp.get("description") or "")[:1500],
            diff=inp["diff"][:DIFF_CAP], findings_block="\n".join(lines),
        )
        async with sem:
            s = ConversationSession()
            s.add_user_message([ContentBlock.text_block(prompt)], cwd=str(PROJECT_ROOT))
            nodes, _u, _ = await client.call_api(
                s, max_tokens=2000, thinking_budget_tokens=1024,
                meta_info={"task": "pr_review_v2_selector_listwise"})
            text = "\n".join(b.text for n in nodes for b in n.message.content
                             if b.type == "text" and b.text)
        try:
            verdict = extract_json_object(text)
        except ValueError:
            verdict = {}
        scores_by_hash: Dict[str, float] = {}
        for i, c in enumerate(cands, 1):
            try:
                sc = float(verdict.get(str(i)))
            except (ValueError, TypeError):
                sc = 0.0
            c["score"] = sc
            scores_by_hash[_finding_hash(c["finding"])] = sc
        cf.write_text(json.dumps({"scores": scores_by_hash}))

    cfg = LLMConfig(model_name=model, max_tokens=2000, thinking_budget_tokens=1024)
    async with LLMClient(cfg, logger=logger) as client:
        await asyncio.gather(*(one_pr(pr, cands, cf, client) for pr, cands, cf in pending))
    return len(pending)


# --------------------------------------------------------------------------- metrics

def auc(scores_pos: List[float], scores_neg: List[float]) -> Optional[float]:
    """ROC-AUC via Mann-Whitney U (P(pos ranks above neg)), ties at 0.5."""
    if not scores_pos or not scores_neg:
        return None
    wins = 0.0
    for p in scores_pos:
        for n in scores_neg:
            wins += 1.0 if p > n else 0.5 if p == n else 0.0
    return round(wins / (len(scores_pos) * len(scores_neg)), 3)


def frontier(
    candidates: List[Dict[str, Any]], gold_to_cands: Dict[int, List[int]],
) -> Dict[str, Any]:
    """Sweep the score threshold; report gold-recall retained vs finding-precision."""
    n_covered = len(gold_to_cands)
    total = len(candidates)
    base_on_target = sum(1 for c in candidates if c["on_target"])
    score_of = {c["ci"]: c.get("score", 0.0) for c in candidates}

    # candidate cut points = the distinct scores (keep score >= t)
    thresholds = sorted({c.get("score", 0.0) for c in candidates})
    points = []
    for t in thresholds:
        kept = [c for c in candidates if c.get("score", 0.0) >= t]
        kept_on = sum(1 for c in kept if c["on_target"])
        covered_kept = sum(
            1 for gid, cis in gold_to_cands.items()
            if any(score_of[ci] >= t for ci in cis)
        )
        points.append({
            "threshold": t,
            "kept": len(kept),
            "kept_frac": round(len(kept) / total, 3) if total else None,
            "finding_precision": round(kept_on / len(kept), 3) if kept else None,
            "gold_recall_retained": round(covered_kept / n_covered, 3) if n_covered else None,
            "covered_gold_kept": covered_kept,
        })
    # baseline (keep all)
    baseline = {
        "kept": total, "finding_precision": round(base_on_target / total, 3) if total else None,
        "gold_recall_retained": 1.0, "covered_gold_kept": n_covered,
    }
    # operating point: highest threshold that retains >=90% of covered gold
    op90 = None
    for p in points:
        if (p["gold_recall_retained"] or 0) >= 0.90:
            op90 = p
    return {"baseline_keep_all": baseline, "op_retain_90pct_gold": op90, "sweep": points}


def compute_result(
    candidates: List[Dict[str, Any]], gold_to_cands: Dict[int, List[int]],
    *, pool_name: str, model: str, mode: str, prompt_version: str,
    uncached_labels: int = 0, n_scored: int = 0,
) -> Dict[str, Any]:
    """Assemble the standard selector report (AUC, per-stratum AUC, frontier) from
    scored candidates. Shared by the diff-only selector and the agentic selector so
    every variant is reported on identical metrics."""
    pos = [c["score"] for c in candidates if c["on_target"]]
    neg = [c["score"] for c in candidates if not c["on_target"]]
    # decisive cut: separability of on-target findings BY the stratum they hit (vs all off-target)
    auc_by_stratum, mean_by_stratum = {}, {}
    for s in ("V1", "V2", "V3", "V4"):
        s_pos = [c["score"] for c in candidates if c["on_target"] and s in c["hit_strata"]]
        if s_pos:
            auc_by_stratum[s] = auc(s_pos, neg)
            mean_by_stratum[s] = round(sum(s_pos) / len(s_pos), 1)
    # free baseline: the agent's own severity flag
    sev_pos = [1.0 if c["finding"].get("severity") == "blocking" else 0.0
               for c in candidates if c["on_target"]]
    sev_neg = [1.0 if c["finding"].get("severity") == "blocking" else 0.0
               for c in candidates if not c["on_target"]]
    return {
        "pool": pool_name,
        "mode": mode,
        "selector_model": model,
        "selector_prompt_version": prompt_version,
        "line_slack": LINE_SLACK,
        "n_candidates": len(candidates),
        "n_on_target": len(pos),
        "n_off_target": len(neg),
        "n_covered_gold": len(gold_to_cands),
        "uncached_labels": uncached_labels,
        "n_newly_scored": n_scored,
        "auc_selector": auc(pos, neg),
        "auc_severity_baseline": auc(sev_pos, sev_neg),
        "auc_by_hit_stratum": auc_by_stratum,
        "mean_score_on_target": round(sum(pos) / len(pos), 1) if pos else None,
        "mean_score_off_target": round(sum(neg) / len(neg), 1) if neg else None,
        "mean_score_by_hit_stratum": mean_by_stratum,
        "frontier": frontier(candidates, gold_to_cands),
    }


def print_summary(result: Dict[str, Any], out: Path) -> None:
    b = result["frontier"]["baseline_keep_all"]
    op = result["frontier"]["op_retain_90pct_gold"]
    print(json.dumps({k: v for k, v in result.items() if k != "frontier"}, indent=2))
    print("\nbaseline keep-all: precision %.3f at gold-recall 1.00 (%d findings)"
          % (b["finding_precision"], b["kept"]))
    if op:
        print("retain 90%% gold:   precision %.3f at gold-recall %.2f (%d findings, %.0f%% of pool)"
              % (op["finding_precision"], op["gold_recall_retained"], op["kept"], 100 * op["kept_frac"]))
    print(f"\nwrote {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    args, remaining = parser.parse_known_args()
    cli = parse_cli_args(remaining)
    pool_name = cli.get("pool", "gpt52_holistic")
    model = cli.get("selector_model", "gpt_5.4")
    mode = cli.get("mode", "pointwise")  # pointwise | listwise
    concurrency = int(cli.get("concurrency", 8))
    logger = create_logger()

    gold_records = load_gold()
    candidates, gold_to_cands, uncached_labels = build_candidates(gold_records, POOLS[pool_name])
    logger.info("Pool %s [%s]: %d candidates, %d covered gold, %d on-target, %d uncached labels",
                pool_name, mode, len(candidates), len(gold_to_cands),
                sum(1 for c in candidates if c["on_target"]), uncached_labels)

    scorer = score_candidates_listwise if mode == "listwise" else score_candidates
    n_scored = asyncio.run(scorer(candidates, gold_records, model, concurrency, logger))

    prompt_version = LISTWISE_PROMPT_VERSION if mode == "listwise" else SELECTOR_PROMPT_VERSION
    result = compute_result(candidates, gold_to_cands, pool_name=pool_name, model=model,
                            mode=mode, prompt_version=prompt_version,
                            uncached_labels=uncached_labels, n_scored=n_scored)
    tag = f"_{mode}" if mode != "pointwise" else ""
    out = PRED_DIR / f"selector_{pool_name}_{model}{tag}.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print_summary(result, out)


if __name__ == "__main__":
    main()
