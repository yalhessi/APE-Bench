"""
D2 evaluation: align predicted findings with gold maintainer comments and
report precision/recall (spec §4 D2; rubric docs/research/stratum-rubric.md).

Gold findings = comments with stratum V1-V4 (P/Q are non-findings and are
excluded — run `annotate` first). Two matching modes:

  anchor — geometric only: same file + line-window overlap for anchored pairs,
           unanchored-pred × unanchored-gold for PR-level pairs; greedy 1-1 by
           line distance. No LLM anywhere. Fast, conservative lower bound on
           recall (a correct claim anchored to a different-but-related line
           does not match).
  llm    — anchor-gated candidates plus same-file and PR-level cross pairs,
           judged for claim equivalence by a model; cached per pair. This is
           the matcher the researcher hand-validates (~50 pairs) and freezes.

Always writes a pairs file (one row per candidate with the decision) — that
file is the hand-validation sample source.

Usage:
  python -m src.datasets.pr_review_v2.evaluate_d2 <gold_annotated.jsonl> <preds.jsonl> [mode=anchor]
"""

import argparse
import asyncio
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from ape.utils import deep_merge, load_yaml, parse_cli_args
from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

FINDING_STRATA = {"V1", "V2", "V3", "V4"}

# Bump this whenever MATCH_PROMPT changes — it is part of the cache key, so a
# new version forces re-judging instead of returning stale cached decisions.
MATCHER_PROMPT_VERSION = "v6"

MATCH_PROMPT = """You are checking whether an automated reviewer (B) CAUGHT the issue a real Mathlib
maintainer (A) raised on a pull request — by comparing the KIND of issue each raises and whether B's
change accomplishes the SAME RESULT A wants.

Set same_issue = true only if ALL THREE hold:
  1. SAME TARGET: A and B concern the same declaration / overlapping lines. (Different declarations,
     or far-apart lines, → NOT the same target.)
  2. SAME KIND OF CONCERN: A and B object to the SAME CATEGORY of issue. Categories include: proof
     golf / simplification (the proof is too long or non-idiomatic), generalization (the STATEMENT
     should hold under weaker hypotheses / more general types), duplication (already exists, use the
     existing declaration), naming, documentation, style, scope. If B's STATED concern is a different
     category than A's, it is NOT a catch — even if B's edit incidentally also changes A's code.
     Example: A asks to GOLF a proof (`simp […]`); B's finding is about GENERALIZING the statement
     (and its whole-declaration rewrite happens to also shorten the proof) → DIFFERENT kind → false.
     Judge the kind from B's stated claim, not from side effects of its edit.
  3. SAME RESULT: B's actual change accomplishes what A asks for, on that code. A and B may write
     DIFFERENT edits within the same kind — that is fine when they achieve the SAME improvement (A
     suggests `simp_all`, B writes `simp [pow_zero]` — both golf the same proof → true). But if A asks
     for a specific improvement and B's change does NOT achieve it at A's spot, it is NOT a catch —
     e.g. A collapses the `n+1` proof to a one-line `grw`, but B keeps a multi-step `calc` there → false.

How to judge:
- When A gives a CONCRETE suggested change (shown under "A's proposed change"), compare B's actual
  edit against it: same kind of concern AND same kind of result at the same place. Textual difference
  is OK; a different category of concern, or failing to achieve A's result, is not.
- When A is PROSE-ONLY (no concrete suggestion), judge whether B's stated concern is A's kind and B's
  edit addresses A's problem at A's target.
- Do NOT match on shared topic alone, on co-location alone, or because B's whole-declaration edit
  happens to touch A's region. If A is too terse to identify its target (e.g. "Same here") and B does
  not clearly coincide, → false.

## A — maintainer comment ({gold_loc})
{gold_body}

## A's proposed change (extracted from A, if any)
{gold_change}

## B — model finding ({pred_loc}); approximate line gap from A: {line_gap}
{pred_claim}

## B's actual edit (the Lean change B makes)
{pred_edit}

Answer with one JSON object: {{"same_issue": true|false, "reason": "<one short sentence: same kind of concern and same result at the same target, or how they differ>"}}"""


# Maintainer comments often carry their concrete proposed change as a fenced code block
# (GitHub ```suggestion, or ```lean). Surfacing it lets the judge compare changes, not prose.
_CODE_BLOCK_RE = re.compile(r"```[a-zA-Z]*\s*\n(.*?)```", re.S)


def _extract_change(text: str) -> str:
    blocks = [b.strip() for b in _CODE_BLOCK_RE.findall(text or "") if b.strip()]
    return "\n--- or ---\n".join(blocks)[:1200] if blocks else "(no concrete suggested change — prose only)"


class MatcherConfig(BaseModel):
    gold: Path
    predictions: Path
    mode: str = Field(default="anchor", description="anchor | llm | target")
    line_slack: int = 10
    verified_only: bool = Field(
        default=False,
        description="target mode: count only verified=True predictions (verifiable strata).",
    )
    topical_gate: bool = Field(
        default=False,
        description="target mode: a location-co-located prediction only counts as covering a gold "
        "finding if it also addresses the SAME concern (MATCH_PROMPT judge), rejecting coincidental "
        "co-location. Reuses the llm-matcher cache. Off => pure-location coverage.",
    )
    output_dir: Optional[Path] = None
    # llm mode
    matcher_model: str = "gpt_5_mini"
    matcher_cache_dir: Path = Field(default=PROJECT_ROOT / "data" / "pr_review_v2" / "cache" / "matcher")
    concurrency: int = 8


# ---------------------------------------------------------------------------
# pair construction
# ---------------------------------------------------------------------------

# Predicted findings carry workspace-relative paths (the agent reads `target/Mathlib/…`),
# often inconsistently; gold paths are repo-relative (`Mathlib/…`). Normalize both before
# any path comparison — without this the location gate silently fails on every prefixed
# path and recall is badly undercounted.
_PATH_PREFIX_RE = re.compile(r"^(?:target/|reference/[^/]+/|scratch/|a/|b/|\./|/)+")


def _norm_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return path
    return _PATH_PREFIX_RE.sub("", str(path).strip())


def _gold_findings(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [c for c in record["gold"]["comments"] if c.get("stratum") in FINDING_STRATA]


def _gold_line(comment: Dict[str, Any]) -> Optional[int]:
    anchor = comment.get("anchor") or {}
    return anchor.get("line") or anchor.get("original_line")


def _pred_span(finding: Dict[str, Any]) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    anchor = finding.get("anchor")
    if not anchor:
        return None, None, None
    start = anchor.get("line_start")
    end = anchor.get("line_end") or start
    return anchor.get("path"), start, end


def candidate_pairs(
    gold_findings: List[Dict[str, Any]],
    pred_findings: List[Dict[str, Any]],
    *,
    line_slack: int,
    include_loose: bool,
) -> List[Dict[str, Any]]:
    """Pairs with tier: 'anchor' (path+line window), 'file' (same path), 'pr_level'."""
    pairs = []
    for gi, gold in enumerate(gold_findings):
        gold_path = _norm_path((gold.get("anchor") or {}).get("path"))
        gold_line = _gold_line(gold)
        for pi, pred in enumerate(pred_findings):
            pred_path_raw, start, end = _pred_span(pred)
            pred_path = _norm_path(pred_path_raw)
            if gold_path and pred_path and gold_path == pred_path:
                if gold_line is not None and start is not None:
                    distance = max(start - line_slack - gold_line, gold_line - (end + line_slack), 0)
                    if distance == 0:
                        pairs.append({"gold_idx": gi, "pred_idx": pi, "tier": "anchor",
                                      "distance": abs(((start + end) // 2) - gold_line)})
                        continue
                if include_loose:
                    pairs.append({"gold_idx": gi, "pred_idx": pi, "tier": "file", "distance": 10_000})
            elif gold_path is None and pred_path is None:
                pairs.append({"gold_idx": gi, "pred_idx": pi, "tier": "pr_level", "distance": 5_000})
            elif include_loose and gold_path is None and pred_path is not None:
                # review bodies / issue comments often discuss a specific file
                pairs.append({"gold_idx": gi, "pred_idx": pi, "tier": "cross", "distance": 20_000})
    return pairs


def greedy_match(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """1-1 matching, best (lowest distance) first. Pairs must carry accept=True."""
    used_gold, used_pred, matched = set(), set(), []
    for pair in sorted(pairs, key=lambda p: p["distance"]):
        if not pair.get("accept"):
            continue
        if pair["gold_idx"] in used_gold or pair["pred_idx"] in used_pred:
            continue
        used_gold.add(pair["gold_idx"])
        used_pred.add(pair["pred_idx"])
        matched.append(pair)
    return matched


# ---------------------------------------------------------------------------
# llm claim equivalence (optional mode)
# ---------------------------------------------------------------------------

def _pair_cache_key(gold: Dict[str, Any], pred: Dict[str, Any], model: str) -> str:
    # `evidence` (the actual verified edit) is part of the key because the judge now uses it —
    # two findings with the same claim but different edits must be judged separately.
    payload = json.dumps(
        [gold.get("id"), gold.get("body"), pred.get("claim"), (pred.get("anchor") or {}),
         pred.get("evidence"), model, MATCHER_PROMPT_VERSION],
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.md5(payload.encode()).hexdigest()


async def judge_pairs_llm(
    work: List[Dict[str, Any]], config: MatcherConfig, logger
) -> None:
    """Fill pair['accept'] / pair['reason'] via claim-equivalence judgments (cached)."""
    from ape.llm_clients.client import LLMClient
    from ape.llm_clients.config import LLMConfig
    from ape.llm_clients.models import ContentBlock, ConversationSession
    from src.mathlib_review.model_output import extract_json_object

    config.matcher_cache_dir.mkdir(parents=True, exist_ok=True)
    pending = []
    for item in work:
        cache_file = config.matcher_cache_dir / f"{item['cache_key']}.json"
        if cache_file.exists():
            cached = json.loads(cache_file.read_text())
            item["pair"]["accept"] = cached["same_issue"]
            item["pair"]["reason"] = cached.get("reason", "")
        else:
            pending.append((item, cache_file))
    logger.info("Matcher: %d cached, %d to judge", len(work) - len(pending), len(pending))
    if not pending:
        return

    semaphore = asyncio.Semaphore(config.concurrency)

    async def judge(item: Dict[str, Any], cache_file: Path, client) -> None:
        gold, pred = item["gold"], item["pred"]
        gold_anchor = gold.get("anchor") or {}
        gold_line = _gold_line(gold)
        gold_loc = (
            f"{gold_anchor['path']}:{gold_line}" if gold_anchor.get("path")
            else f"PR-level {gold.get('kind', 'comment')}, no line anchor"
        )
        pred_path, start, end = _pred_span(pred)
        pred_loc = f"{pred_path}:{start}" if pred_path else "PR-level, no line anchor"
        if gold_anchor.get("path") and pred_path == gold_anchor["path"] and gold_line and start:
            line_gap = str(max(start - gold_line, gold_line - (end or start), 0))
        elif gold_anchor.get("path") and pred_path and pred_path != gold_anchor["path"]:
            line_gap = "different file"
        else:
            line_gap = "n/a (one side is PR-level)"
        # Compare the two CHANGES, not just the prose: A's concrete suggested change (from the
        # maintainer comment) vs B's actual verified edit (decl-mode: the whole rewritten
        # declaration; line-mode: the replacement). Same target + same result, allowing different
        # text — this is what stops a whole-declaration rewrite being credited for a change it does
        # not actually make.
        edit = pred.get("evidence") or pred.get("suggested_fix") or ""
        pred_edit = str(edit)[:1800] if str(edit).strip() else "(no explicit code edit provided — claim only)"
        prompt = MATCH_PROMPT.format(
            gold_loc=gold_loc, gold_body=gold["body"][:2000], gold_change=_extract_change(gold["body"]),
            pred_loc=pred_loc, line_gap=line_gap,
            pred_claim=(pred["claim"] + (
                f"\nSuggested fix: {pred['suggested_fix'][:500]}" if pred.get("suggested_fix") else "")),
            pred_edit=pred_edit,
        )
        async with semaphore:
            session = ConversationSession()
            session.add_user_message([ContentBlock.text_block(prompt)], cwd=str(PROJECT_ROOT))
            nodes, _usage, _ = await client.call_api(
                session, max_tokens=2000, thinking_budget_tokens=1024,
                meta_info={"task": "pr_review_v2_matcher"},
            )
            text = "\n".join(
                b.text for n in nodes for b in n.message.content if b.type == "text" and b.text
            )
        try:
            verdict = extract_json_object(text)
            same = bool(verdict.get("same_issue"))
            reason = str(verdict.get("reason") or "")
        except ValueError:
            same, reason = False, f"matcher_unparseable: {text[:100]}"
        item["pair"]["accept"] = same
        item["pair"]["reason"] = reason
        cache_file.write_text(json.dumps({"same_issue": same, "reason": reason}))

    llm_config = LLMConfig(model_name=config.matcher_model, max_tokens=2000, thinking_budget_tokens=1024)
    async with LLMClient(llm_config, logger=logger) as client:
        await asyncio.gather(*(judge(item, cache_file, client) for item, cache_file in pending))


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------

def evaluate(
    gold_records: Dict[int, Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    config: MatcherConfig,
    logger,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    pairs_dump: List[Dict[str, Any]] = []
    per_pr: List[Dict[str, Any]] = []
    llm_work: List[Dict[str, Any]] = []

    joined = []
    for pred in predictions:
        record = gold_records.get(pred["pr_number"])
        if record is None or not pred["parse_ok"]:
            continue
        gold_findings = _gold_findings(record)
        pairs = candidate_pairs(
            gold_findings, pred["findings"],
            line_slack=config.line_slack, include_loose=(config.mode == "llm"),
        )
        if config.mode == "anchor":
            for pair in pairs:
                pair["accept"] = pair["tier"] in ("anchor", "pr_level")
                pair["reason"] = f"tier={pair['tier']}"
        else:
            for pair in pairs:
                item = {
                    "pair": pair,
                    "gold": gold_findings[pair["gold_idx"]],
                    "pred": pred["findings"][pair["pred_idx"]],
                }
                item["cache_key"] = _pair_cache_key(item["gold"], item["pred"], config.matcher_model)
                llm_work.append(item)
        joined.append((pred, record, gold_findings, pairs))

    if config.mode == "llm" and llm_work:
        asyncio.run(judge_pairs_llm(llm_work, config, logger))

    totals = Counter()
    stratum_gold = Counter()
    stratum_matched = Counter()
    control_findings = []

    for pred, record, gold_findings, pairs in joined:
        matched = greedy_match(pairs)
        matched_gold = {p["gold_idx"] for p in matched}
        matched_pred = {p["pred_idx"] for p in matched}

        n_gold, n_pred = len(gold_findings), len(pred["findings"])
        totals["gold"] += n_gold
        totals["pred"] += n_pred
        totals["matched"] += len(matched)
        for gi, gold in enumerate(gold_findings):
            stratum_gold[gold["stratum"]] += 1
            if gi in matched_gold:
                stratum_matched[gold["stratum"]] += 1
            if gold.get("severity") == "blocking":
                totals["gold_blocking"] += 1
                if gi in matched_gold:
                    totals["matched_blocking"] += 1
        if n_gold == 0:  # approval-control PR: every finding is a false positive
            control_findings.append(n_pred)

        gold_verdict_approved = record["gold"]["verdict"] == "APPROVED"
        if pred.get("merge_ready_as_is") is not None:
            totals["d1_total"] += 1
            if pred["merge_ready_as_is"] == gold_verdict_approved:
                totals["d1_correct"] += 1

        per_pr.append({
            "pr_number": pred["pr_number"], "gold": n_gold, "pred": n_pred,
            "matched": len(matched), "verdict": record["gold"]["verdict"],
            "merge_ready_pred": pred.get("merge_ready_as_is"),
        })
        for pair in pairs:
            gold = gold_findings[pair["gold_idx"]]
            pf = pred["findings"][pair["pred_idx"]]
            gold_anchor = gold.get("anchor") or {}
            pred_path, pred_start, pred_end = _pred_span(pf)
            pairs_dump.append({
                "pr_number": pred["pr_number"],
                "gold_id": gold["id"], "gold_stratum": gold["stratum"],
                "gold_loc": (
                    f"{gold_anchor['path']}:{_gold_line(gold)}"
                    if gold_anchor.get("path") else f"PR_LEVEL/{gold['kind']}"
                ),
                "gold_body": gold["body"][:300],
                "pred_loc": (
                    "PR_LEVEL" if not pred_path
                    else f"{pred_path}:{pred_start}-{pred_end}" if pred_start is not None
                    else pred_path
                ),
                "pred_claim": pf["claim"][:300],
                "tier": pair["tier"], "accepted": bool(pair.get("accept")),
                "matched_1to1": pair in greedy_match(pairs),
                "reason": pair.get("reason", ""),
            })

    precision = totals["matched"] / totals["pred"] if totals["pred"] else 0.0
    recall = totals["matched"] / totals["gold"] if totals["gold"] else 0.0
    report = {
        "mode": config.mode,
        "prs_evaluated": len(per_pr),
        "gold_findings": totals["gold"],
        "predicted_findings": totals["pred"],
        "matched": totals["matched"],
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "blocking_recall": round(
            totals["matched_blocking"] / totals["gold_blocking"], 3
        ) if totals["gold_blocking"] else None,
        "recall_by_stratum": {
            s: {"gold": stratum_gold[s], "matched": stratum_matched[s],
                "recall": round(stratum_matched[s] / stratum_gold[s], 3)}
            for s in sorted(stratum_gold)
        },
        "control_prs": {
            "n": len(control_findings),
            "findings_per_control_pr": round(
                sum(control_findings) / len(control_findings), 2
            ) if control_findings else None,
        },
        "d1_verdict_accuracy": round(
            totals["d1_correct"] / totals["d1_total"], 3
        ) if totals["d1_total"] else None,
        "per_pr": per_pr,
    }
    return report, pairs_dump


def evaluate_target(
    gold_records: Dict[int, Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    config: MatcherConfig,
    logger,
) -> Dict[str, Any]:
    """TARGET coverage: did the reviewer flag the same place the maintainer flagged?

    A gold finding (anchored) is COVERED if a predicted finding sits in the same (normalized)
    file within line_slack of the gold line. Pure location is the honest recall floor for the
    verifiable strata (the reviewer's golf/dup/general statement legitimately differs from the
    maintainer's, so claim-matching understates it) — but pure location also OVER-counts via
    coincidental co-location (a golf finding landing near an unrelated doc/scope comment). With
    `topical_gate=True` a co-located prediction only counts if it also addresses the SAME concern
    (MATCH_PROMPT judge, shared with llm mode's cache), rejecting coincidence. The truth is
    between pure-location and strict-claim; the gate picks it.

    Also reports off-target predictions: findings NOT on any maintainer target — the
    valid-but-unflagged extras that define the selectivity problem.
    """
    slack = config.line_slack
    gold_items: List[Dict[str, Any]] = []   # {gid, pr, stratum}
    pred_items: List[Dict[str, Any]] = []   # {pid, pr}
    pairs: List[Dict[str, Any]] = []        # {gid, pid, accept}
    work: List[Dict[str, Any]] = []         # MATCH_PROMPT judge inputs (topical gate)
    verified_n = 0

    for pred in predictions:
        record = gold_records.get(pred["pr_number"])
        if record is None or not pred.get("parse_ok"):
            continue
        pr = pred["pr_number"]
        gold = _gold_findings(record)
        preds = pred.get("findings") or []
        if config.verified_only:
            preds = [p for p in preds if p.get("verified")]
        verified_n += sum(1 for p in preds if p.get("verified"))

        local_preds = []  # (pid, norm_path, start, end, finding)
        for p in preds:
            path, start, end = _pred_span(p)
            np = _norm_path(path)
            if np and start is not None:
                pid = len(pred_items)
                pred_items.append({"pid": pid, "pr": pr})
                local_preds.append((pid, np, start, end or start, p))

        for g in gold:
            gp = _norm_path((g.get("anchor") or {}).get("path"))
            gl = _gold_line(g)
            if not gp or gl is None:  # PR-level / unanchored gold can't be located
                continue
            gid = len(gold_items)
            gold_items.append({"gid": gid, "pr": pr, "stratum": g["stratum"]})
            for pid, pp, ps, pe, pf in local_preds:
                if pp == gp and ps - slack <= gl <= pe + slack:
                    pair = {"gid": gid, "pid": pid, "accept": not config.topical_gate}
                    pairs.append(pair)
                    if config.topical_gate:
                        work.append({"pair": pair, "gold": g, "pred": pf,
                                     "cache_key": _pair_cache_key(g, pf, config.matcher_model)})

    if config.topical_gate and work:
        asyncio.run(judge_pairs_llm(work, config, logger))

    covered = {p["gid"] for p in pairs if p["accept"]}
    on_target_pids = {p["pid"] for p in pairs if p["accept"]}

    stratum_gold = Counter()
    stratum_cov = Counter()
    pr_gold, pr_cov, pr_pred, pr_on = Counter(), Counter(), Counter(), Counter()
    for gi in gold_items:
        stratum_gold[gi["stratum"]] += 1
        pr_gold[gi["pr"]] += 1
        if gi["gid"] in covered:
            stratum_cov[gi["stratum"]] += 1
            pr_cov[gi["pr"]] += 1
    for pi in pred_items:
        pr_pred[pi["pr"]] += 1
        if pi["pid"] in on_target_pids:
            pr_on[pi["pr"]] += 1

    total_gold, total_cov = len(gold_items), len(covered)
    total_pred, on_target = len(pred_items), len(on_target_pids)
    prs = sorted({gi["pr"] for gi in gold_items} | {pi["pr"] for pi in pred_items})
    per_pr = [{
        "pr_number": pr, "gold_anchored": pr_gold[pr], "covered": pr_cov[pr],
        "anchored_pred": pr_pred[pr], "on_target": pr_on[pr],
        "off_target": pr_pred[pr] - pr_on[pr],
    } for pr in prs]

    return {
        "mode": "target",
        "topical_gate": config.topical_gate,
        "line_slack": slack,
        "verified_only": config.verified_only,
        "prs_evaluated": len(per_pr),
        "anchored_gold": total_gold,
        "gold_covered": total_cov,
        "target_recall": round(total_cov / total_gold, 3) if total_gold else None,
        "recall_by_stratum": {
            s: {"gold": stratum_gold[s], "covered": stratum_cov[s],
                "recall": round(stratum_cov[s] / stratum_gold[s], 3)}
            for s in sorted(stratum_gold)
        },
        "anchored_predictions": total_pred,
        "verified_predictions": verified_n,
        "on_target_predictions": on_target,
        "off_target_predictions": total_pred - on_target,  # selectivity candidates
        "on_target_rate": round(on_target / total_pred, 3) if total_pred else None,
        "per_pr": per_pr,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="D2 matcher + evaluation for v2 predictions")
    parser.add_argument("gold", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--config", type=Path, default=None)
    args, remaining = parser.parse_known_args()
    logger = create_logger()

    config_dict: Dict[str, Any] = load_yaml(args.config) if args.config else {}
    config_dict = deep_merge(config_dict, parse_cli_args(remaining))
    config_dict.update({"gold": args.gold, "predictions": args.predictions})
    config = MatcherConfig.model_validate(config_dict)

    gold_records = {
        (row := json.loads(line))["pr_number"]: row
        for line in args.gold.read_text().splitlines() if line.strip()
    }
    predictions = [json.loads(line) for line in args.predictions.read_text().splitlines() if line.strip()]

    if config.mode == "target":
        report, pairs = evaluate_target(gold_records, predictions, config, logger), []
    else:
        report, pairs = evaluate(gold_records, predictions, config, logger)

    out_dir = config.output_dir or args.predictions.parent
    stem = f"{args.predictions.stem}_d2_{config.mode}"
    report_file = out_dir / f"{stem}_report.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    if pairs:
        pairs_file = out_dir / f"{stem}_pairs.jsonl"
        with pairs_file.open("w") as fh:
            for row in pairs:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        logger.info("Pairs (hand-validation source): %s", pairs_file)

    summary = {k: v for k, v in report.items() if k != "per_pr"}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    logger.info("Report: %s", report_file)


if __name__ == "__main__":
    main()
