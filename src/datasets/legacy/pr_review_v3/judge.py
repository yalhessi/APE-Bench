"""Phase B judge — two-level matching against intervention gold (redesign spec §2).

Replaces the v6 matcher's single fused criterion (which wobbled exactly on its seam: 30-40%
generous accepts, near-miss rejects, one same-site accept/reject inconsistency) with two levels,
both judged against the enriched `canonical_ask` (never the raw indexical comment):

  issue_match      — the prediction identifies the SAME PROBLEM: same site, same specific aspect
                     of the code (not merely the same concern category). It may propose a
                     different fix. "Make this helper public" and "document why it is private"
                     BOTH issue-match an intervention about the helper's private status.
  resolution_match — implies issue_match: the prediction's concrete change achieves the ask's
                     resolution (the strict, headline-quality level).

Versioned v7 (continuing the matcher's v6 line — the old judge and its caches stay frozen for
historical comparability). Per-pair content-keyed cache; resolution⇒issue enforced in code.
"""

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ape.utils.project import PROJECT_ROOT

# v7.1: audit of v7 (17/20 agreement) found one systematic leniency — findings that examine the
# right code but conclude "no change needed" were credited as issue-matches. Defending the code is
# not identifying the problem; the no-change clause below excludes them.
JUDGE_PROMPT_VERSION = "v7.1"
CACHE_DIR = PROJECT_ROOT / "data" / "pr_review_v3" / "cache" / "judge"

JUDGE_PROMPT = """You are scoring one CANDIDATE REVIEW FINDING against one gold MAINTAINER
INTERVENTION on the same Mathlib pull request. Judge two levels.

PR context: {pr_summary}

## GOLD INTERVENTION (reconstructed from the maintainer's comments; the reference)
Concern: {concern} | anchors: {anchor_desc}
Ask: {canonical_ask}
Why ({rationale_source}): {rationale}

## CANDIDATE FINDING (location {pred_loc}; line distance from nearest anchor: {line_gap})
Claim: {claim}
Proposed fix: {suggested_fix}
Verified edit (if any): {evidence}

Levels:
1. "issue_match": the finding identifies the SAME PROBLEM — the same declaration/code aspect the
   intervention is about (the thing that would have to change), not merely the same category of
   concern near the same lines. A different proposed fix for the same problem still issue-matches.
   A finding about a DIFFERENT aspect of the same lines (e.g. proof style when the ask is a
   rename) does NOT. A finding that examines the same code but concludes NO CHANGE IS NEEDED
   (defends the current code, says the concern does not apply, or reports the ask as already
   satisfied) does NOT issue-match — identifying the problem means asserting it exists.
2. "resolution_match" (only possible when issue_match): the finding's concrete change achieves the
   intervention's ask — compare the CHANGES (the ask's transformation vs the finding's fix/edit),
   allowing different wording but the same result. A vaguer fix that would not by itself produce
   the asked transformation is issue_match only.

Reply JSON only:
{{"issue_match": true|false, "resolution_match": true|false, "reason": "<one sentence>"}}"""


def pair_key(iv: Dict[str, Any], pred_finding: Dict[str, Any], model: str) -> str:
    payload = json.dumps([
        iv.get("intervention_id"), iv.get("canonical_ask"),
        pred_finding.get("claim"), pred_finding.get("suggested_fix"), pred_finding.get("evidence"),
        model, JUDGE_PROMPT_VERSION,
    ], ensure_ascii=False)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def parse_verdict(text: str) -> Tuple[bool, bool, str]:
    """(issue_match, resolution_match, reason); resolution ⇒ issue enforced here."""
    from src.mathlib_review.model_output import extract_json_object
    try:
        v = extract_json_object(text)
    except ValueError:
        return False, False, f"judge_unparseable: {text[:100]}"
    issue = bool(v.get("issue_match"))
    resolution = bool(v.get("resolution_match")) and issue
    return issue, resolution, str(v.get("reason") or "")


async def judge_pairs(pairs: List[Dict[str, Any]], *, model: str, concurrency: int, logger,
                      cache_dir: Path = CACHE_DIR) -> None:
    """Fill pair['issue_match'] / pair['resolution_match'] / pair['reason'] (cached per content).

    Each pair: {"iv": <intervention row>, "pred": <prediction finding>, "pred_loc": str,
    "line_gap": str}. Failed calls stay uncached (re-run retries them); one failure does not
    tear down the batch.
    """
    from ape.llm_clients.client import LLMClient
    from ape.llm_clients.config import LLMConfig
    from ape.llm_clients.models import ContentBlock, ConversationSession

    cache_dir.mkdir(parents=True, exist_ok=True)
    pending = []
    for p in pairs:
        f = cache_dir / f"{pair_key(p['iv'], p['pred'], model)}.json"
        if f.exists():
            c = json.loads(f.read_text())
            p["issue_match"], p["resolution_match"], p["reason"] = (
                c["issue_match"], c["resolution_match"], c.get("reason", ""))
        else:
            pending.append((p, f))
    logger.info("Judge v7: %d pairs, %d to judge (rest cached)", len(pairs), len(pending))
    if not pending:
        return
    sem = asyncio.Semaphore(concurrency)

    async def one(p, f, client):
        iv, pred = p["iv"], p["pred"]
        anchor_desc = ", ".join(f"{a['path'].split('/')[-1]}:{a['line_start']}-{a['line_end']}"
                                for a in (iv.get("anchors") or [])[:4]) or "(unanchored)"
        prompt = JUDGE_PROMPT.format(
            pr_summary=(iv.get("pr_summary") or "")[:600],
            concern=iv.get("concern"), anchor_desc=anchor_desc,
            canonical_ask=(iv.get("canonical_ask") or "")[:1200],
            rationale_source=iv.get("rationale_source") or "?",
            rationale=(iv.get("rationale") or "")[:400],
            pred_loc=p.get("pred_loc") or "?", line_gap=p.get("line_gap") or "?",
            claim=(pred.get("claim") or "")[:1200],
            suggested_fix=(pred.get("suggested_fix") or "(none)")[:800],
            evidence=(pred.get("evidence") or "(none)")[:900],
        )
        async with sem:
            s = ConversationSession()
            s.add_user_message([ContentBlock.text_block(prompt)], cwd=str(PROJECT_ROOT))
            nodes, _u, _ = await client.call_api(s, max_tokens=2000, thinking_budget_tokens=1024,
                                                 meta_info={"task": "judge_v7"})
            text = "\n".join(b.text for n in nodes for b in n.message.content
                             if b.type == "text" and b.text)
        issue, resolution, reason = parse_verdict(text)
        p["issue_match"], p["resolution_match"], p["reason"] = issue, resolution, reason
        f.write_text(json.dumps({"issue_match": issue, "resolution_match": resolution,
                                 "reason": reason}, ensure_ascii=False))

    cfg = LLMConfig(model_name=model, max_tokens=2000, thinking_budget_tokens=1024)
    async with LLMClient(cfg, logger=logger) as client:
        results = await asyncio.gather(*(one(p, f, client) for p, f in pending),
                                       return_exceptions=True)
    failures = [e for e in results if isinstance(e, Exception)]
    if failures:
        raise RuntimeError(f"{len(failures)}/{len(pending)} judge calls failed "
                           f"(first: {str(failures[0])[:150]}); re-run to resume from cache.")
