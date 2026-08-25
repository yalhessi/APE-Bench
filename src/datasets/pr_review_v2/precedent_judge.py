"""Stage 1 judge — precedent-hit@k scorer (docs/research/precedent-retrieval-design.md §7).

Consumes a `retrieved_<design>.jsonl` from precedent_bench.py and, for each (query, candidate)
pair, asks an LLM whether the historical precedent would PREDICT the hidden maintainer comment:

  relation = "hit"          precedent raises the same KIND of concern AND applying its principle to
                            the new site's code yields (roughly) the hidden comment's ask
             "same_concern" same kind of concern, but its principle does NOT determine the hidden ask
                            (retrieval found the right neighbourhood but not a predictive precedent)
             "unrelated"    different concern / no transferable principle

The three-way split lets the report separate "no predictive precedent was retrieved" (miss) from
"a same-concern precedent exists but doesn't transfer" — the failure taxonomy the design asks for.

Mirrors evaluate_d2.py's matcher: async, per-pair file cache keyed on content + prompt version, so
re-running is free and a prompt change forces a clean re-judge. The judge sees the hidden comment on
purpose — it is the answer key for scoring, not part of the retrieval system under test.

  python -m src.datasets.pr_review_v2.precedent_judge --retrieved inputs/pr_review_v2/precedent_bench/retrieved_lexical.jsonl
  python -m src.datasets.pr_review_v2.precedent_judge --retrieved inputs/pr_review_v2/precedent_bench/retrieved_*.jsonl --model gpt_5.2
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

# Bump when JUDGE_PROMPT changes — it is part of the cache key.
# v2: added the actionable-principle gate (STEP 1) — a precedent that states no reusable instruction
# (bare "thanks"/"done"/LGTM, a question, a personal musing) can never be a hit, regardless of how
# well its topic aligns with the site. Kills the ~1-in-6 spurious V2 hits the audit found.
JUDGE_PROMPT_VERSION = "v2"
CACHE_DIR = PROJECT_ROOT / "data" / "pr_review_v2" / "cache" / "precedent_judge"

JUDGE_PROMPT = """You are auditing whether a HISTORICAL Mathlib maintainer review comment is a useful \
PRECEDENT for a NEW review situation — i.e. whether, if a reviewer had this precedent in hand, its \
principle would lead them to raise (roughly) the concern a maintainer actually raised on the new site.

STEP 1 — the precedent's PRINCIPLE, judged FROM THE PRECEDENT ALONE (do NOT look at the new site or
the answer key yet). State the concrete, transferable instruction the precedent gives — the reusable
rule a reviewer could carry to other code. Examples of a real principle: "replace a verbose calc proof
with `simpa using <lemma>`", "rename lemmas to match the surrounding namespace", "state this hypothesis
in the lemma rather than only in the proof", "use the existing lemma X instead of re-proving it". A
concrete ```suggestion``` code block counts as a principle (the rewrite it demonstrates).
If the precedent gives NO reusable instruction — it is only an acknowledgement ("thanks", "done",
"LGTM", "nice"), a bare question, a personal musing ("I'm sure there's a better way but I couldn't
find it"), or social chatter — then it has NO principle: set "precedent_principle" to "NONE".

STEP 2 — TRANSFER, only if there is a principle. Would applying that principle to the NEW SITE's code
produce approximately the hidden maintainer comment's ask?

NEW SITE — the changed code a reviewer is about to look at (the real maintainer comment is HIDDEN):
Path: {q_path}
```
{site_code}
```

The HIDDEN maintainer comment on the new site (the ANSWER KEY — what we want a precedent to predict):
"{hidden_body}"

CANDIDATE PRECEDENT — a real past maintainer comment and the code it was made on:
Path: {p_path}
```
{prec_code}
```
Maintainer said: "{prec_body}"

Classify "relation":
- "not_actionable": the precedent has no reusable principle (precedent_principle is NONE). This wins
  over every other label — a precedent with no principle cannot be a hit however well its topic matches.
- "hit": there IS a principle, it is the SAME KIND of concern (proof-golf/simplification |
  generalization | duplication | naming | docs | style | scope), AND applying it to the new site's code
  would produce approximately the hidden comment's ask.
- "same_concern": same KIND of concern, but the principle would not by itself yield the hidden ask.
- "unrelated": different concern, or the principle does not transfer to this site.

Judge the transfer of the PRINCIPLE, not surface word overlap. Reply with JSON only:
{{"precedent_principle": "<the reusable instruction, or NONE>", \
"relation": "not_actionable" | "hit" | "same_concern" | "unrelated", "reason": "<one sentence>"}}"""


def parse_verdict(text: str):
    """(relation, principle, reason) from the judge's JSON, with the actionable-principle gate
    enforced in code: an empty/NONE principle forces relation=not_actionable regardless of label."""
    from .predictions import _extract_json_object
    try:
        verdict = _extract_json_object(text)
    except ValueError:
        return "unrelated", "", f"judge_unparseable: {text[:100]}"
    relation = str(verdict.get("relation") or "unrelated")
    if relation not in {"not_actionable", "hit", "same_concern", "unrelated"}:
        relation = "unrelated"
    principle = str(verdict.get("precedent_principle") or "")
    if not principle.strip() or principle.strip().upper() == "NONE":
        relation = "not_actionable"
    return relation, principle, str(verdict.get("reason") or "")


def _cache_key(query_id: Any, cand: Dict[str, Any], hidden_body: str, model: str) -> str:
    payload = json.dumps([
        query_id, cand.get("comment_id"), cand.get("precedent_body"), cand.get("precedent_code"),
        hidden_body, model, JUDGE_PROMPT_VERSION,
    ], ensure_ascii=False, sort_keys=True)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


async def judge_file(retrieved_path: Path, out: Path, *, model: str, concurrency: int,
                     judge_k: int, logger) -> Path:
    from ape.llm_clients.client import LLMClient
    from ape.llm_clients.config import LLMConfig
    from ape.llm_clients.models import ContentBlock, ConversationSession

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    queries = [json.loads(l) for l in retrieved_path.read_text().splitlines() if l.strip()]

    # Flatten to (query, candidate) work items, honoring cache.
    pending = []
    for q in queries:
        for cand in q.get("candidates", [])[:judge_k]:
            key = _cache_key(q["query_id"], cand, q.get("hidden_body", ""), model)
            cache_file = CACHE_DIR / f"{key}.json"
            if cache_file.exists():
                cached = json.loads(cache_file.read_text())
                cand["hit"] = cached["relation"] == "hit"
                cand["relation"] = cached["relation"]
                cand["judge_reason"] = cached.get("reason", "")
                cand["precedent_principle"] = cached.get("precedent_principle", "")
            else:
                pending.append((q, cand, cache_file))
    logger.info("[%s] %d pairs, %d to judge (rest cached)", retrieved_path.name,
                sum(len(q.get("candidates", [])[:judge_k]) for q in queries), len(pending))

    if pending:
        semaphore = asyncio.Semaphore(concurrency)

        async def one(q: Dict[str, Any], cand: Dict[str, Any], cache_file: Path, client) -> None:
            prompt = JUDGE_PROMPT.format(
                q_path=q.get("path"), site_code=str(q.get("site_code", ""))[:2500],
                hidden_body=str(q.get("hidden_body", ""))[:1200],
                p_path=cand.get("path"), prec_code=str(cand.get("precedent_code", ""))[:2000],
                prec_body=str(cand.get("precedent_body", ""))[:1500],
            )
            async with semaphore:
                session = ConversationSession()
                session.add_user_message([ContentBlock.text_block(prompt)], cwd=str(PROJECT_ROOT))
                nodes, _usage, _ = await client.call_api(
                    session, max_tokens=1500, thinking_budget_tokens=1024,
                    meta_info={"task": "precedent_judge"},
                )
                text = "\n".join(b.text for n in nodes for b in n.message.content
                                 if b.type == "text" and b.text)
            relation, principle, reason = parse_verdict(text)
            cand["relation"] = relation
            cand["hit"] = relation == "hit"
            cand["precedent_principle"] = principle
            cand["judge_reason"] = reason
            cache_file.write_text(json.dumps(
                {"relation": relation, "reason": reason, "precedent_principle": principle}))

        llm_config = LLMConfig(model_name=model, max_tokens=1500, thinking_budget_tokens=1024)
        async with LLMClient(llm_config, logger=logger) as client:
            await asyncio.gather(*(one(q, cand, cf, client) for q, cand, cf in pending))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(q, ensure_ascii=False) for q in queries) + "\n")
    n_hit = sum(1 for q in queries if any(c.get("hit") for c in q.get("candidates", [])[:judge_k]))
    logger.info("[%s] judged -> %s | queries with >=1 hit@%d: %d/%d",
                retrieved_path.name, out, judge_k, n_hit, len(queries))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 1 precedent-hit@k LLM judge")
    p.add_argument("--retrieved", type=Path, nargs="+", required=True,
                   help="one or more retrieved_<design>.jsonl from precedent_bench")
    p.add_argument("--model", default="gpt_5_mini", help="judge model (default gpt_5_mini)")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--judge-k", type=int, default=10, help="judge only the top-k candidates per query")
    args = p.parse_args()
    logger = create_logger()
    for rp in args.retrieved:
        out = rp.parent / rp.name.replace("retrieved_", "judged_")
        if out == rp:
            out = rp.parent / f"judged_{rp.stem}.jsonl"
        asyncio.run(judge_file(rp, out, model=args.model, concurrency=args.concurrency,
                               judge_k=args.judge_k, logger=logger))


if __name__ == "__main__":
    main()
