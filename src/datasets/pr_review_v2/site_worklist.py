"""Site-first pipeline, step 1 — build the per-PR instantiation WORKLIST.

For every changed site (hunk) of every eval PR: retrieve its top-k corpus neighbors (dense, local),
classify each neighbor's maintainer comment into a concern type (mini model, per-comment cache),
and aggregate into a similarity-weighted concern profile per site. The worklist row for a PR lists
its sites, each with its top concerns and exemplar precedents OF THAT CONCERN — the input the
instantiation checker (`lean_pr_review_instantiate`) is required to decide item by item.

Design facts this rests on (site_discrimination + Stage-1): site enumeration is cheap (~2-4 sites/PR,
contains 100% of anchored gold); neighbors carry the gold concern type at ~83% of gold sites. The
open number is blind instantiation-match, which the checker run measures.

  python -m src.datasets.pr_review_v2.site_worklist            # all 57 gold-bearing PRs
  python -m src.datasets.pr_review_v2.site_worklist --prs 33048 33065

Needs API only for classifying UNCACHED neighbor comments (gpt_5_mini, ~1-2k one-shot calls first
time, then free). Retrieval/aggregation is local.
"""

import argparse
import asyncio
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

from .delta import parse_patch_hunks
from .precedent_bench import DEFAULT_CORPUS, hunk_code, load_corpus
from .precedent_prime import DEFAULT_RECORDS, FIRST20  # noqa: F401  (FIRST20 re-exported for configs)

WORKLIST_OUT = PROJECT_ROOT / "inputs" / "pr_review_v2" / "precedent_bench" / "worklist_by_pr.jsonl"
CACHE_DIR = PROJECT_ROOT / "data" / "pr_review_v2" / "cache" / "concern_classify"

CONCERNS = ["proof-golf", "generalization", "duplication", "naming", "docs", "style", "scope"]

# v2 FACET BATTERY (2026-07-10): the identify->issue failure analysis showed the neighbor-voted
# concern selection was the binding constraint — 24/33 failures had the intervention's concern
# ABSENT from the site's checklist, and the delivered mix was systematically biased (27% golf items
# vs 4% golf interventions; style/docs chronically under-delivered). Neighbors were wrong about
# WHICH concerns apply; they remain useful for exemplars. So: EVERY site gets EVERY facet; facets
# with neighbor support carry weight + typical_ask + precedents, the rest carry a canned hint.
FACETS = CONCERNS + ["correctness"]
FACET_HINTS = {
    "proof-golf": "Is any proof here longer or more manual than the canonical tactic/lemma allows?",
    "generalization": "Should any statement be stated more generally (weaker hypotheses, more "
                      "general typeclass, arbitrary constant instead of a fixed one)?",
    "duplication": "Does anything here restate or specialize material that already exists in "
                   "Mathlib (or elsewhere in this PR)?",
    "naming": "Does every new/renamed declaration follow the naming convention and match its "
              "siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?",
    "docs": "Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, "
            "references to renamed declarations, module-doc conventions)?",
    "style": "Any formatting/structure issue maintainers flag: line breaks, calc layout, binder "
             "style, attribute placement, explicit vs implicit arguments, redundant qualifiers?",
    "scope": "Is anything in the wrong place (file, namespace, section), unnecessary for this PR, "
             "or better split out / made private-or-public differently?",
    "correctness": "Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) "
                   "or contain a semantic error a maintainer would block on?",
}
CLASSIFY_PROMPT_VERSION = "v1"
CLASSIFY_PROMPT = """Classify this Mathlib review comment by the KIND of change the maintainer is asking for.

The comment was made on this code:
```
{code}
```
Maintainer said: "{body}"

Pick exactly one:
- "proof-golf": shorter/simpler/more idiomatic PROOF for the same statement (incl. use tactic X / lemma Y)
- "generalization": weaker hypotheses / more general statement or typeclass
- "duplication": this (or part of it) already exists in Mathlib / duplicates another declaration
- "naming": rename a declaration / wrong namespace
- "docs": docstring / comment content
- "style": formatting, attributes, syntax conventions (not proof content)
- "scope": move to a different file/PR, split the PR, delete dead code
- "none": no actionable ask (acknowledgement, question, discussion)

JSON only: {{"concern": "<one of the above>"}}"""

ASK_CACHE_DIR = PROJECT_ROOT / "data" / "pr_review_v2" / "cache" / "ask_distill"
ASK_PROMPT_VERSION = "v1"
ASK_PROMPT = """These are real Mathlib maintainer review comments, all raising the same KIND of concern
("{concern}") on code similar to a site under review:

{bodies}

Distill them into ONE concrete sentence describing the typical ask a maintainer makes in this
situation — specific enough that a reviewer knows what to look for (name the convention/tactic/
pattern involved, not just the category). JSON only: {{"ask": "<one sentence>"}}"""

ALL_57 = [33048, 33065, 33066, 33067, 33070, 33078, 33079, 33081, 33086, 33090,
          33092, 33098, 33101, 33104, 33111, 33117, 33127, 33137, 33141, 33145,
          33146, 33149, 33150, 33153, 33154, 33169, 33183, 33190, 33201, 33203,
          33207, 33208, 33232, 33267, 33268, 33283, 33285, 33287, 33294, 33310,
          33316, 33321, 33332, 33333, 33337, 33343, 33345, 33349, 33356, 33362,
          33373, 33376, 33395, 33400, 33401, 33419, 33421]


# ---------------------------------------------------------------------------
# sites (with line spans, for anchoring the instantiated findings)
# ---------------------------------------------------------------------------

def pr_sites_with_spans(rec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Changed sites with reviewed-state line spans, built EXCLUSIVELY from `input.diff` —
    the base->reviewed diff, the only thing a real reviewer sees.

    LEAK POSTMORTEM (2026-07-11): this function previously preferred `gold.delta_total`, the
    POST-REVIEW revision delta. That (a) showed the system the author's eventual corrected code
    (106/202 hunks were added_in_revision — for adopted asks the checklist could contain the
    answer), and (b) shrank the search space ~2x toward gold-concentrated regions (374 real sites
    vs 202 delta sites across the 57 PRs; PR 33294: 51 vs 6), inflating T1 and plausibly T2/T3.
    Every result produced from delta-derived worklists is an oracle-site diagnostic, not a
    deployable measurement. Sites must never be derived from any `gold.*` field; the invariant is
    enforced by test_worklist_is_gold_independent."""
    sites: List[Dict[str, Any]] = []
    diff = (rec.get("input") or {}).get("diff") or ""
    path, body = None, []
    def flush():
        if path and path.endswith(".lean") and body:
            for ph in parse_patch_hunks(path, "\n".join(body)):
                sites.append({"path": path, "patch": ph.patch_text,
                              "line_start": ph.new_start,
                              "line_end": ph.new_start + max(ph.new_lines - 1, 0)})
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            flush(); path, body = None, []
        elif line.startswith("+++ b/"):
            path = line[6:].strip()
        elif path is not None:
            body.append(line)
    flush()
    return sites


# ---------------------------------------------------------------------------
# neighbor-comment concern classification (cached; mirrors precedent_judge)
# ---------------------------------------------------------------------------

def _cache_key(comment: Dict[str, Any], model: str) -> str:
    payload = json.dumps([comment.get("comment_id"), comment.get("body"),
                          model, CLASSIFY_PROMPT_VERSION], ensure_ascii=False)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def parse_concern(text: str) -> str:
    from .predictions import _extract_json_object
    try:
        c = str(_extract_json_object(text).get("concern") or "none").strip().lower()
    except ValueError:
        return "none"
    return c if c in set(CONCERNS) | {"none"} else "none"


async def classify_comments(comments: List[Dict[str, Any]], *, model: str, concurrency: int,
                            logger) -> Dict[Any, str]:
    """comment_id -> concern, classifying only uncached ones."""
    from ape.llm_clients.client import LLMClient
    from ape.llm_clients.config import LLMConfig
    from ape.llm_clients.models import ContentBlock, ConversationSession

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out: Dict[Any, str] = {}
    pending = []
    for c in comments:
        f = CACHE_DIR / f"{_cache_key(c, model)}.json"
        if f.exists():
            out[c["comment_id"]] = json.loads(f.read_text())["concern"]
        else:
            pending.append((c, f))
    logger.info("Concern classify: %d comments, %d uncached", len(comments), len(pending))
    if not pending:
        return out
    sem = asyncio.Semaphore(concurrency)

    async def one(c, f, client):
        # Token budget mirrors precedent_judge: gpt_5_mini is a reasoning model — with a tiny
        # max_tokens and no thinking budget it spends everything reasoning and returns EMPTY
        # content (finish_reason=length), which killed the first run.
        prompt = CLASSIFY_PROMPT.format(code=hunk_code(c.get("diff_hunk") or "")[:1500],
                                        body=str(c.get("body") or "")[:1200])
        async with sem:
            s = ConversationSession()
            s.add_user_message([ContentBlock.text_block(prompt)], cwd=str(PROJECT_ROOT))
            nodes, _u, _ = await client.call_api(s, max_tokens=2000, thinking_budget_tokens=1024,
                                                 meta_info={"task": "concern_classify"})
            text = "\n".join(b.text for n in nodes for b in n.message.content
                             if b.type == "text" and b.text)
        concern = parse_concern(text)
        out[c["comment_id"]] = concern
        f.write_text(json.dumps({"concern": concern}))

    cfg = LLMConfig(model_name=model, max_tokens=2000, thinking_budget_tokens=1024)
    async with LLMClient(cfg, logger=logger) as client:
        # Failure-tolerant: a failed comment stays UNCACHED (never cached as "none"), so a rerun
        # retries exactly the failures. One bad call must not tear down the other in-flight calls.
        results = await asyncio.gather(*(one(c, f, client) for c, f in pending),
                                       return_exceptions=True)
    failures = [e for e in results if isinstance(e, Exception)]
    if failures:
        logger.warning("Concern classify: %d/%d failed (first: %s). They remain uncached — "
                       "re-run the command to retry just those.", len(failures), len(pending),
                       str(failures[0])[:200])
        raise RuntimeError(f"{len(failures)} comment classifications failed; re-run to resume "
                           f"(cache holds the {len(pending) - len(failures)} that succeeded).")
    return out


# ---------------------------------------------------------------------------
# per-item "typical ask" distillation (cached) — a bare concern word under-specifies the ask
# (spot-read: agents given `scope` checked "is it private?" while the ask was namespace placement)
# ---------------------------------------------------------------------------

def _ask_key(concern: str, bodies: List[str], model: str) -> str:
    payload = json.dumps([concern, bodies, model, ASK_PROMPT_VERSION], ensure_ascii=False)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


async def distill_asks(items: List[Dict[str, Any]], *, model: str, concurrency: int, logger) -> None:
    """Attach item['typical_ask'] (in place) for every worklist item; cached per content."""
    from ape.llm_clients.client import LLMClient
    from ape.llm_clients.config import LLMConfig
    from ape.llm_clients.models import ContentBlock, ConversationSession
    from .predictions import _extract_json_object

    ASK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    pending = []
    for it in items:
        bodies = [p.get("body") or "" for p in (it.get("precedents") or [])][:3]
        if not any(b.strip() for b in bodies):
            continue  # hint-only battery facet: canned typical_ask already set, nothing to distill
        f = ASK_CACHE_DIR / f"{_ask_key(it['concern'], bodies, model)}.json"
        if f.exists():
            it["typical_ask"] = json.loads(f.read_text())["ask"]
        else:
            pending.append((it, bodies, f))
    logger.info("Ask distill: %d items, %d uncached", len(items), len(pending))
    if not pending:
        return
    sem = asyncio.Semaphore(concurrency)

    async def one(it, bodies, f, client):
        prompt = ASK_PROMPT.format(concern=it["concern"],
                                   bodies="\n".join(f'- "{b[:350]}"' for b in bodies if b.strip()))
        async with sem:
            s = ConversationSession()
            s.add_user_message([ContentBlock.text_block(prompt)], cwd=str(PROJECT_ROOT))
            nodes, _u, _ = await client.call_api(s, max_tokens=2000, thinking_budget_tokens=1024,
                                                 meta_info={"task": "ask_distill"})
            text = "\n".join(b.text for n in nodes for b in n.message.content
                             if b.type == "text" and b.text)
        try:
            ask = str(_extract_json_object(text).get("ask") or "").strip()
        except ValueError:
            ask = ""
        it["typical_ask"] = ask
        f.write_text(json.dumps({"ask": ask}))

    cfg = LLMConfig(model_name=model, max_tokens=2000, thinking_budget_tokens=1024)
    async with LLMClient(cfg, logger=logger) as client:
        results = await asyncio.gather(*(one(it, b, f, client) for it, b, f in pending),
                                       return_exceptions=True)
    failures = [e for e in results if isinstance(e, Exception)]
    if failures:
        raise RuntimeError(f"{len(failures)} ask distillations failed; re-run to resume.")


# ---------------------------------------------------------------------------
# worklist assembly
# ---------------------------------------------------------------------------

def build_worklist(prs: List[int], *, records_path: Path, corpus_path: Path, k: int,
                   max_concerns: int, exemplars: int, min_weight: float,
                   model: str, concurrency: int, out: Path, logger,
                   no_retrieval: bool = False) -> Path:
    recs = {json.loads(l)["pr_number"]: json.loads(l)
            for l in records_path.read_text().splitlines() if l.strip()}

    # 1. enumerate sites (from input.diff ONLY — see pr_sites_with_spans leak postmortem)
    sites_by_pr: Dict[int, List[Dict[str, Any]]] = {}
    flat: List[Dict[str, Any]] = []
    for pr in prs:
        rec = recs.get(pr)
        if not rec:
            logger.warning("PR %d not in records — skipped", pr)
            continue
        ss = pr_sites_with_spans(rec)
        sites_by_pr[pr] = ss
        flat.extend(ss)

    if no_retrieval:
        # ablation / offline mode: full facet battery with canned hints, no precedent exemplars.
        logger.info("Worklist (NO retrieval): %d PRs, %d sites", len(sites_by_pr), len(flat))
        corpus = []
        for s in flat:
            s["neighbors"] = []
        concern_of: Dict[Any, str] = {}
    else:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        corpus = load_corpus(corpus_path)
        by_id = {c["comment_id"]: c for c in corpus}
        logger.info("Worklist: %d PRs, %d sites, corpus %d", len(sites_by_pr), len(flat), len(corpus))
        modelE = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        emb_c = modelE.encode([hunk_code(c.get("diff_hunk") or "") for c in corpus],
                              normalize_embeddings=True, batch_size=256)
        emb_s = modelE.encode([hunk_code(s["patch"]) for s in flat],
                              normalize_embeddings=True, batch_size=256)
        sims = emb_s @ emb_c.T
        for i, s in enumerate(flat):
            idx = np.argsort(-sims[i])[:k]
            s["neighbors"] = [(int(j), float(sims[i][j])) for j in idx]

        # 2. classify every retrieved neighbor comment (cached)
        needed_ids = {corpus[j]["comment_id"] for s in flat for j, _ in s["neighbors"]}
        concern_of = asyncio.run(classify_comments([by_id[i] for i in sorted(needed_ids)],
                                                   model=model, concurrency=concurrency, logger=logger))

    # 3. per-site concern profile -> worklist items
    pr_rows: List[Tuple[int, List[Dict[str, Any]]]] = []
    all_items: List[Dict[str, Any]] = []
    for pr, ss in sites_by_pr.items():
        rows = []
        for s in ss:
            wt: Dict[str, float] = defaultdict(float)
            ex: Dict[str, List[Tuple[float, Dict[str, Any]]]] = defaultdict(list)
            for j, sim in s["neighbors"]:
                c = corpus[j]
                concern = concern_of.get(c["comment_id"], "none")
                if concern == "none":
                    continue
                wt[concern] += sim
                ex[concern].append((sim, c))
            total = sum(wt.values()) or 1.0
            # v2 battery: EVERY facet is an item. Facets with neighbor support (top `max_concerns`
            # by weight) carry full precedent exemplars; the rest carry the canned hint only —
            # neighbors no longer gate which concerns the checker may consider.
            supported = {c for c, _ in sorted(wt.items(), key=lambda kv: -kv[1])[:max_concerns]}
            items = []
            for facet in FACETS:
                w = wt.get(facet, 0.0)
                item = {"concern": facet, "weight": round(w / total, 3) if w else 0.0,
                        "precedents": []}
                if facet in supported and ex.get(facet):
                    item["precedents"] = [{
                        "body": (c.get("body") or "")[:400],
                        "code": (c.get("diff_hunk") or "")[:500],
                        "path": c.get("path"),
                    } for _sim, c in sorted(ex[facet], key=lambda t: -t[0])[:exemplars]]
                else:
                    item["typical_ask"] = FACET_HINTS[facet]
                items.append(item)
            all_items.extend(items)
            rows.append({"path": s["path"], "line_start": s["line_start"],
                         "line_end": s["line_end"], "site_code": hunk_code(s["patch"])[:1800],
                         "items": items})
        pr_rows.append((pr, rows))

    # 4. distill each item's concern into a concrete one-line ask (cached)
    if not no_retrieval:
        asyncio.run(distill_asks(all_items, model=model, concurrency=concurrency, logger=logger))

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for pr, rows in pr_rows:
            fh.write(json.dumps({"pr_number": pr, "sites": rows}, ensure_ascii=False) + "\n")
    logger.info("Worklist -> %s (%d PRs, %d instantiation items)", out, len(pr_rows), len(all_items))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Build the per-PR site x concern instantiation worklist")
    p.add_argument("--prs", type=int, nargs="*", default=ALL_57)
    p.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    p.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    p.add_argument("--k", type=int, default=10, help="neighbors per site")
    p.add_argument("--max-concerns", type=int, default=2, help="max concerns kept per site")
    p.add_argument("--exemplars", type=int, default=3, help="precedent exemplars per concern")
    p.add_argument("--min-weight", type=float, default=0.2, help="min relative concern weight")
    p.add_argument("--model", default="gpt_5_mini")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--no-retrieval", action="store_true",
                   help="battery with canned hints only, no precedent exemplars (fully offline; "
                        "also the retrieval-contribution ablation arm)")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    out = args.out or WORKLIST_OUT.with_name(
        "worklist_v3_raw_nr_by_pr.jsonl" if args.no_retrieval else "worklist_v3_raw_by_pr.jsonl")
    logger = create_logger()
    build_worklist(args.prs, records_path=args.records, corpus_path=args.corpus, k=args.k,
                   max_concerns=args.max_concerns, exemplars=args.exemplars,
                   min_weight=args.min_weight, model=args.model, concurrency=args.concurrency,
                   out=out, logger=logger, no_retrieval=args.no_retrieval)


if __name__ == "__main__":
    main()
