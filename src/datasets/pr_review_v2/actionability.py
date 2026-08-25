"""
Gold-quality re-audit: some maintainer comments labelled as findings (V1-V4) are
not actionable in-scope requests — they are approvals, indecision/deferrals, or
content-free pointers ("Same here") that slipped past the P/Q non-finding tags.
They inflate the recall denominator (no reviewer should "flag" them).

This pass re-classifies each V1-V4 comment as one of:
  ACTIONABLE  — requests/implies a concrete change. NOTE: flagging a *pre-existing*
                issue still counts as ACTIONABLE (kept in-scope by decision).
  APPROVAL    — approves/praises with no change requested ("I like this the best").
  INDECISION  — uncertainty / defers the decision ("not sure I prefer those, I'll
                wait for another opinion"); not a request.
  POINTER     — content-free reference to another comment ("Same here", "and the
                others") carrying no standalone, locatable concern.

The latter three are non-findings; `apply` rewrites their stratum to `P` (which the
evaluator already excludes), preserving the original stratum in the note. Same
sidecar contract as annotate.py: rows keyed by (pr_number, comment_id).

  # 1. classify (LLM, cached) -> sidecar
  python -m src.datasets.pr_review_v2.actionability classify <records.jsonl> <sidecar.jsonl>
  # 2. apply -> cleaned extract + report
  python -m src.datasets.pr_review_v2.actionability apply <records.jsonl> <sidecar.jsonl> -o <clean.jsonl>
"""

import argparse
import asyncio
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

FINDING_STRATA = {"V1", "V2", "V3", "V4"}
NON_ACTIONABLE = {"APPROVAL", "INDECISION", "POINTER"}
PROMPT_VERSION = "v1"

CLASSIFY_PROMPT = """You are auditing one comment a Mathlib maintainer left on a pull request, to decide
whether it is an ACTIONABLE review finding or a non-finding that should not be scored.

Classify the comment as exactly one of:
- ACTIONABLE: it requests or clearly implies a concrete change to the code (a fix, golf, rename,
  generalization, restatement, doc change, etc.). Flagging a PRE-EXISTING issue (code not added by
  this PR) still counts as ACTIONABLE.
- APPROVAL: it approves, praises, or agrees, with no change requested (e.g. "I like this the best",
  "looks good", "nice"). It may explain why the current code is fine.
- INDECISION: it expresses uncertainty or defers the decision rather than requesting a change
  (e.g. "I'm not sure I prefer those", "I'll wait for another opinion", "no strong preference").
  A tentative "maybe X?" that still proposes a concrete change is ACTIONABLE, not INDECISION.
- POINTER: a content-free reference to another comment with no standalone, locatable concern
  (e.g. "Same here", "and the others", "ditto"). If it adds its own concrete concern, it is ACTIONABLE.

## Maintainer comment (file {path}, line {line}, current stratum {stratum})
{body}

Answer with one JSON object: {{"verdict": "ACTIONABLE|APPROVAL|INDECISION|POINTER", "reason": "<one short sentence>"}}"""


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _cache_key(comment: Dict[str, Any], model: str) -> str:
    payload = json.dumps([comment.get("body"), comment.get("stratum"), model, PROMPT_VERSION],
                         ensure_ascii=False, sort_keys=True)
    return hashlib.md5(payload.encode()).hexdigest()


def _finding_comments(records: List[Dict[str, Any]]):
    for record in records:
        for comment in record["gold"]["comments"]:
            if comment.get("stratum") in FINDING_STRATA:
                yield record, comment


async def classify(records, sidecar_path: Path, model: str, cache_dir: Path, concurrency: int, logger):
    from ape.llm_clients.client import LLMClient
    from ape.llm_clients.config import LLMConfig
    from ape.llm_clients.models import ContentBlock, ConversationSession
    from .predictions import _extract_json_object

    cache_dir.mkdir(parents=True, exist_ok=True)
    rows: Dict[tuple, Dict[str, Any]] = {}
    pending = []
    for record, comment in _finding_comments(records):
        key = (record["pr_number"], comment["id"])
        cache_file = cache_dir / f"{_cache_key(comment, model)}.json"
        if cache_file.exists():
            v = json.loads(cache_file.read_text())
            rows[key] = {"pr_number": key[0], "comment_id": key[1], **v}
        else:
            pending.append((record, comment, key, cache_file))
    logger.info("Actionability: %d cached, %d to classify", len(rows), len(pending))

    if pending:
        semaphore = asyncio.Semaphore(concurrency)

        async def run(record, comment, key, cache_file, client):
            anchor = comment.get("anchor") or {}
            prompt = CLASSIFY_PROMPT.format(
                path=anchor.get("path") or "(PR-level)", line=anchor.get("line") or "-",
                stratum=comment.get("stratum"), body=(comment.get("body") or "")[:2000])
            async with semaphore:
                session = ConversationSession()
                session.add_user_message([ContentBlock.text_block(prompt)], cwd=str(PROJECT_ROOT))
                nodes, _u, _ = await client.call_api(
                    session, max_tokens=1500, thinking_budget_tokens=1024,
                    meta_info={"task": "pr_review_v2_actionability"})
                text = "\n".join(b.text for n in nodes for b in n.message.content
                                 if b.type == "text" and b.text)
            try:
                verdict = _extract_json_object(text)
                v = {"verdict": str(verdict.get("verdict", "")).upper().strip(),
                     "reason": str(verdict.get("reason") or "")}
                if v["verdict"] not in (NON_ACTIONABLE | {"ACTIONABLE"}):
                    v = {"verdict": "ACTIONABLE", "reason": f"unparseable verdict: {text[:80]}"}
            except ValueError:
                v = {"verdict": "ACTIONABLE", "reason": f"unparseable: {text[:80]}"}
            cache_file.write_text(json.dumps(v))
            rows[key] = {"pr_number": key[0], "comment_id": key[1], **v}

        llm_config = LLMConfig(model_name=model, max_tokens=1500, thinking_budget_tokens=1024)
        async with LLMClient(llm_config, logger=logger) as client:
            await asyncio.gather(*(run(r, c, k, cf, client) for r, c, k, cf in pending))

    with sidecar_path.open("w") as fh:
        for key in sorted(rows):
            fh.write(json.dumps(rows[key], ensure_ascii=False) + "\n")
    tally = Counter(r["verdict"] for r in rows.values())
    logger.info("Verdicts: %s -> sidecar %s", dict(tally), sidecar_path)
    return dict(tally)


def apply_actionability(records, sidecar) -> Dict[str, Any]:
    """Rewrite non-actionable finding-comments to stratum 'P' (preserving the original)."""
    index = {(s["pr_number"], s["comment_id"]): s for s in sidecar}
    reclassified = Counter()
    seen = 0
    for record in records:
        for comment in record["gold"]["comments"]:
            if comment.get("stratum") not in FINDING_STRATA:
                continue
            seen += 1
            s = index.get((record["pr_number"], comment["id"]))
            if s and s["verdict"] in NON_ACTIONABLE:
                comment["orig_stratum"] = comment["stratum"]
                comment["stratum"] = "P"
                comment["actionability"] = s["verdict"]
                comment["actionability_reason"] = s.get("reason", "")
                reclassified[s["verdict"]] += 1
    return {"finding_comments_seen": seen,
            "reclassified_to_P": sum(reclassified.values()),
            "by_category": dict(reclassified),
            "remaining_findings": seen - sum(reclassified.values())}


def main() -> None:
    parser = argparse.ArgumentParser(description="Gold-quality actionability re-audit of V1-V4 comments")
    sub = parser.add_subparsers(dest="cmd", required=True)
    pc = sub.add_parser("classify")
    pc.add_argument("records", type=Path)
    pc.add_argument("sidecar", type=Path)
    pc.add_argument("--model", default="gpt_5_mini")
    pc.add_argument("--concurrency", type=int, default=8)
    pa = sub.add_parser("apply")
    pa.add_argument("records", type=Path)
    pa.add_argument("sidecar", type=Path)
    pa.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    logger = create_logger()

    records = load_jsonl(args.records)
    if args.cmd == "classify":
        cache_dir = PROJECT_ROOT / "data" / "pr_review_v2" / "cache" / "actionability"
        tally = asyncio.run(classify(records, args.sidecar, args.model, cache_dir, args.concurrency, logger))
        print(json.dumps(tally, indent=2))
    else:
        stats = apply_actionability(records, load_jsonl(args.sidecar))
        if args.output:
            with args.output.open("w") as fh:
                for record in records:
                    fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
