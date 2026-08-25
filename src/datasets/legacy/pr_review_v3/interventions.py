"""Phase A of the intervention-level benchmark redesign (docs/research/
intervention-benchmark-redesign.md §1): build `interventions_v1.jsonl` from the v2 annotated gold.

The gold unit changes from COMMENT to INTERVENTION — one maintainer judgment + the set of sites it
applies to + its outcome. Construction stages (LLM steps cached per content, mirrors the matcher):

  1. thread grouping (mechanical)       — replies in one review thread are one seed
  2. propagation attach (mechanical)    — "Same here"/"(and the other ones)" markers attach to the
                                          nearest preceding substantive seed by the same author
  3. cross-seed merge (LLM, per PR)     — seeds describing the SAME single ask are merged
                                          (e.g. 33098's six per-lemma golf comments = one judgment)
  4. enrichment (LLM, per intervention) — self-contained `canonical_ask` (thread context resolved,
                                          referents named), concern, judgeable flag, anchor set
                                          (source linked hunks + inferred sibling anchors)
  5. outcome labeling (LLM)             — adopted/partially_adopted/contested/dropped/unknown from
                                          the revision hunks overlapping the anchors + thread state

Output: inputs/pr_review_v3/interventions_v1.jsonl + interventions_review.md (the human-skim
digest — Phase-A gate is a hand review of that file).

  python -m src.datasets.pr_review_v3.interventions --records \
      inputs/pr_review_v2/mathlib_pr_review_v2_annotated_20260612.jsonl

Needs API for stages 3-5 on first run (~85-250 calls, then cached).
"""

import argparse
import asyncio
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

SCHEMA_VERSION = "i5"  # i5: + lint field, + correctness concern
ACTIONABLE = {"V1", "V2", "V3", "V4"}
OUT_DIR = PROJECT_ROOT / "inputs" / "pr_review_v3"
CACHE_ROOT = PROJECT_ROOT / "data" / "pr_review_v3" / "cache"
DEFAULT_RECORDS = PROJECT_ROOT / "inputs" / "pr_review_v2" / "mathlib_pr_review_v2_annotated_20260612.jsonl"

# v3 (2026-07-09, after the second human review): the v1/v2 failures were an information-
# presentation bug, not a prompt problem — delta_total holds removed_in_revision (code AS REVIEWED)
# and added_in_revision (code AFTER the author's response) pairs, and enrichment fed both unlabeled
# as "the reviewed state" (so `round_eq'` -> `round_eq_div` looked like round_eq_div already
# existing, and the 2->k generalization of two_mul_fract_... was invisible). v3 mechanically
# separates the evidence into REVIEWED / MAINTAINER-PROPOSED (suggestion blocks) / AUTHOR-ADOPTED
# (revision) sections and makes enrichment a diff-description task. Rationale becomes
# always-populated + rationale_source: stated|inferred (v2's stated-only rule nulled 36%).
# v4/v3 (2026-07-10, after the third review round — all four fixes are again evidence gaps, not
# prompts): (1) outcome now sees the FULL revision delta, not just anchor-overlapping hunks — 28/46
# "dropped" labels had non-anchor revisions the judge never saw (adoption-elsewhere false drops);
# (2) unanchored interventions get a δ0 (input.diff) excerpt filtered to the comment's identifiers
# as their reviewed-state evidence (was: zero code -> "the identifier named along the lines of...");
# (3) `meta` flag for PR-metadata asks (description/title), excluded from code metrics;
# (4) rationale_source "stated" tightened to: the REASON itself appears in the comments.
# outcome v4 (2026-07-10): v3's ELSEWHERE fix was defeated by TRUNCATION — adoption text sits at
# hunk ends (new lemmas are appended): `ciSup'` at char 2491 of a 3694-char hunk cut at 900, so
# adopted asks (33145 ciSup'/ciInf', 33048 mk_le_mk rename) were still labeled dropped despite the
# evidence being in delta_total. v4 adds ASK-AWARE evidence: a mechanical full-text identifier
# presence table (reviewed-side vs post-revision-side) + the matching lines, immune to truncation.
# enrich v5 (2026-07-10): + "correctness" concern (V1/policy asks like "remove the axiom" were
# unreachable — no category could carry them); + ask lint (degenerate renames like the 33400
# "rename contDiffAt to contDiffAt" artifact are flagged into the digest for review).
MERGE_PROMPT_VERSION = "v2"
ENRICH_PROMPT_VERSION = "v5"
OUTCOME_PROMPT_VERSION = "v4"
SUMMARY_PROMPT_VERSION = "v1"
CONCERNS = ["proof-golf", "generalization", "duplication", "naming", "docs", "style", "scope",
            "correctness", "other"]

_RENAME_RE = re.compile(r"[Rr]ename[^`]{0,60}`([^`]+)`[^`]{0,80}?\bto\b[^`]{0,40}`([^`]+)`")


def lint_ask(ask: str, judgeable: bool) -> List[str]:
    """Mechanical sanity flags on a canonical ask, surfaced in the review digest."""
    warnings = []
    m = _RENAME_RE.search(ask or "")
    if m and m.group(1).strip() == m.group(2).strip():
        warnings.append(f"degenerate rename: source == target (`{m.group(1)}`)")
    if judgeable and not re.search(r"`[^`]+`", ask or ""):
        warnings.append("judgeable ask names no backticked identifier (weak referents)")
    return warnings

PR_SUMMARY_PROMPT = """Summarize what this Mathlib pull request DOES, for a reviewer who will judge
comments about it. 2-4 sentences: the mathematical/library goal, the main declarations it adds or
changes (name them), and anything unusual about its structure.

PR #{pr_number}: {title}

Description:
{description}

Changed hunks (path:line | first lines):
{menu}

JSON only: {{"pr_summary": "<2-4 sentences>"}}"""

# short bodies that only point at a previous comment
_PROP_RE = re.compile(
    r"^\s*\(?\s*(same( comment| here| below| as above)?|ditto|likewise|also here|and the other"
    r"( ones?)?|as above)\b[\s\S]{0,40}$", re.I)

MERGE_PROMPT = """These are review-comment CLUSTERS from ONE Mathlib pull request (each cluster is one
review thread, already grouped). Some clusters express the SAME single judgment applied at several
places, and should be merged into one intervention.

What the PR does: {pr_summary}

{clusters}

Merge when the clusters are one judgment voiced repeatedly — the typical patterns:
- the same transformation requested on each of several sibling declarations ("this and the next
  three lemmas can be proven with X", then per-lemma suggestion blocks implementing exactly that);
- the same systematic refactor applied across a family (e.g. dualize each `ciSup` lemma via
  `OrderDual`, or rename each new lemma to a common scheme);
- a comment plus later comments that only extend it to more targets ("Same comment: please also...").
Do NOT merge different asks that merely share a topic or a file. Reply JSON only:
{{"merges": [[<cluster indices that are one judgment>], ...]}}  (omit singletons)"""

ENRICH_PROMPT = """You are preparing benchmark gold from Mathlib review comments. Below is ONE
maintainer INTERVENTION (one judgment, possibly voiced across several comments). Your job is to
state the TRANSFORMATION it asks for, by comparing the labeled evidence sections.

PR #{pr_number}: {title}
What the PR does: {pr_summary}

Maintainer comments (chronological; the intervention is what they jointly ask):
{comments}

### A. Code AS THE MAINTAINER REVIEWED IT (the state the comments are about):
{reviewed}

### B. Change the MAINTAINER PROPOSED (suggestion blocks from the comments, verbatim):
{proposed}

### C. The AUTHOR'S SUBSEQUENT REVISION of this code (after the review; where it matches the
comments, it is direct evidence of what the maintainer meant):
{adopted}

### Anchor menu (all changed hunks in the PR; [rev]=post-revision, [pre]=as-reviewed — pick every
hunk this ask applies to, including siblings covered by 'same here/below' phrasing):
{menu}

The canonical ask is the A -> B transformation (fall back to A -> C when there is no suggestion
block and the revision clearly implements the comments; if B and C conflict, follow the comments).
State it as one imperative: what in A changes, into what — e.g. "rename `round_eq'` to
`round_eq_div`" when A has round_eq' and B/C have round_eq_div; "generalize the fixed factor 2 in
`two_mul_fract_eq_one_iff_exists_int` to any `k` with hypothesis `1 < k`, renaming it
`mul_fract_eq_one_iff_exists_int`" when that is the A -> B delta. Describe the delta itself —
never write "match the suggestion". If the comments ask an open question that neither B nor C
resolves, record the precise decision target instead of inventing an answer.

Write JSON only:
{{"canonical_ask": "<the imperative transformation, per the rules above>",
 "rationale": "<the best account of WHY the maintainer asks this — quote/paraphrase when stated,
   otherwise your best reconstruction from the code and conventions>",
 "rationale_source": "stated" | "inferred",  // "stated" ONLY if the REASON ITSELF (not merely the
   // ask) appears in the comments; a reconstructed motive behind a bare ask is "inferred"
 "concern": "{concern_options}",
 "severity": "blocking" | "advisory",
 "judgeable": true | false,   // false if no concrete ask or decision target is recoverable
 "meta": true | false,        // true when the ask targets PR METADATA (description, title, commit
   // message, labels) rather than the code — excluded from code-review metrics
 "anchor_hunk_ids": ["<hunk ids from the menu this ask applies to>", ...]}}"""

OUTCOME_PROMPT = """Did the PR author ADOPT this maintainer intervention? Compare the code as
reviewed with the author's subsequent revision at the intervention's anchor sites.

Intervention: "{canonical_ask}"
Review-thread resolved flag(s): {resolved}
PR merged: {merged} | review rounds: {rounds}

### Code AS REVIEWED (at the intervention's anchors):
{reviewed}

### The author's SUBSEQUENT REVISION at the anchors:
{adopted}

### Revisions ELSEWHERE in the PR (the ask may have been adopted at a different site — a new lemma
added elsewhere, code moved to another file; check these before ruling "dropped"):
{elsewhere}

### IDENTIFIER EVIDENCE — mechanical full-text search over ALL revision hunks (the code excerpts
above are truncated; THIS is not — trust it over the excerpts):
{ident_table}

Reading the table: a rename OLD -> NEW is adopted iff OLD is only on the reviewed side and NEW
appears on the post-revision side. An addition is adopted iff the new identifier appears on the
post-revision side. A resolved review thread usually means the comment was addressed.

adopted = some revision (at the anchors or elsewhere) implements the ask; partially_adopted = some
of it; contested = the thread shows push-back and no revision implements it; dropped = no revision
anywhere implements it and no resolution; unknown = evidence insufficient. Reply JSON only:
{{"outcome": "adopted" | "partially_adopted" | "contested" | "dropped" | "unknown",
 "outcome_evidence": "<one sentence citing the concrete evidence>"}}"""


# ---------------------------------------------------------------------------
# mechanical stages
# ---------------------------------------------------------------------------

def is_propagation_marker(body: str) -> bool:
    return bool(_PROP_RE.match((body or "").strip()))


def seed_clusters(rec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Stage 1+2: thread grouping, then attach propagation-marker seeds to the nearest
    preceding substantive seed by the same author."""
    comments = [c for c in (rec.get("gold", {}).get("comments") or [])
                if (c.get("stratum") or "") in ACTIONABLE]
    comments.sort(key=lambda c: c.get("submitted_at") or "")
    by_thread: Dict[Any, List[Dict[str, Any]]] = {}
    order: List[Any] = []
    for c in comments:
        tid = c.get("thread_id") or f"solo_{c.get('id')}"
        if tid not in by_thread:
            by_thread[tid] = []
            order.append(tid)
        by_thread[tid].append(c)
    seeds = [{"comments": by_thread[t]} for t in order]

    merged: List[Dict[str, Any]] = []
    for s in seeds:
        bodies = [c.get("body") or "" for c in s["comments"]]
        author = s["comments"][0].get("author")
        if merged and all(is_propagation_marker(b) for b in bodies):
            # attach to the nearest preceding seed by the same author
            for prev in reversed(merged):
                if prev["comments"][0].get("author") == author:
                    prev["comments"].extend(s["comments"])
                    break
            else:
                merged.append(s)
        else:
            merged.append(s)
    return merged


def _delta_index(rec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {h["hunk_id"]: h for h in (rec.get("gold", {}).get("delta_total") or []) if h.get("hunk_id")}


_SUGGESTION_RE = re.compile(r"```suggestion[^\n]*\n(.*?)```", re.S)
_FENCE_RE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.S)


def _suggestion_blocks(comments: List[Dict[str, Any]], cap: int = 3, max_chars: int = 1500) -> List[str]:
    """The maintainer's own proposed code, from ```suggestion``` (preferred) or fenced blocks."""
    out: List[str] = []
    for c in comments:
        body = c.get("body") or ""
        blocks = _SUGGESTION_RE.findall(body) or _FENCE_RE.findall(body)
        out.extend(b.strip()[:max_chars] for b in blocks if b.strip())
    return out[:cap]


_TICK_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_.']{2,})`")


def _delta0_excerpt(rec: Dict[str, Any], comments: List[Dict[str, Any]], max_chars: int = 3000) -> str:
    """Reviewed-state evidence for UNANCHORED comments: the PR's own diff (δ0, base -> reviewed),
    filtered to file blocks containing identifiers the comments mention (else the head)."""
    diff = (rec.get("input") or {}).get("diff") or ""
    if not diff.strip():
        return "(no PR diff available)"
    tokens = {t for c in comments for t in _TICK_RE.findall(c.get("body") or "")}
    blocks = re.split(r"(?=^diff --git )", diff, flags=re.M)
    hits = [b for b in blocks if any(t in b for t in tokens)] if tokens else []
    text = "\n".join(hits) if hits else diff
    return text[:max_chars]


def evidence_sections(rec: Dict[str, Any], comments: List[Dict[str, Any]],
                      hunk_ids: List[str], max_chars: int = 1600) -> Dict[str, str]:
    """Separate the intervention's evidence by TEMPORAL DIRECTION — the load-bearing fix of v3.

    delta hunks come in removed_in_revision (the code AS THE MAINTAINER REVIEWED IT) /
    added_in_revision (the code AFTER the author responded) pairs. Feeding them unlabeled made the
    post-adoption state look like the reviewed state (`round_eq_div` "already existing"). Returns:
      reviewed — removed hunks at the anchors (fallback note when the region is added-only);
      adopted  — added hunks (the author's subsequent revision; direct evidence of what was adopted);
      proposed — the maintainer's suggestion blocks from the comments.
    """
    didx = _delta_index(rec)
    removed, added = [], []
    for h in dict.fromkeys(hunk_ids):
        hd = didx.get(h)
        if not hd:
            continue
        patch = (hd.get("patch") or "")[:max_chars]
        loc = f"{hd.get('path')}:{hd.get('new_start')}"
        (removed if hd.get("op") == "removed_in_revision" else added).append(f"[{loc}]\n{patch}")
    reviewed = "\n\n".join(removed) if removed else (
        "(no pre-revision hunk at the anchors — the region below was added/changed only after "
        "review; its context lines existed at review time)\n\n" + "\n\n".join(added[:1])
        if added else
        "(comment not anchored to a changed hunk — excerpt of the PR's reviewed diff below)\n\n"
        + _delta0_excerpt(rec, comments))
    adopted = "\n\n".join(added) if added else "(the author did not revise this code after review)"
    proposed = "\n\n".join(_suggestion_blocks(comments)) or "(no suggestion block in the comments)"
    return {"reviewed": reviewed, "adopted": adopted, "proposed": proposed}


def _hunk_menu(rec: Dict[str, Any], max_head: int = 2) -> str:
    lines = []
    for h in (rec.get("gold", {}).get("delta_total") or []):
        head = "\n".join((h.get("patch") or "").splitlines()[1:1 + max_head])
        ns = h.get("new_start")
        tag = "pre" if h.get("op") == "removed_in_revision" else "rev"
        lines.append(f"- {h.get('hunk_id')} [{tag}] | {h.get('path')}:{ns} | {head[:120]}")
    return "\n".join(lines) or "(none)"


# ---------------------------------------------------------------------------
# LLM stages (each cached per content)
# ---------------------------------------------------------------------------

def _key(*parts: Any) -> str:
    return hashlib.md5(json.dumps(parts, ensure_ascii=False, default=str).encode()).hexdigest()


async def _call(client, prompt: str, max_tokens: int = 4000):
    from ape.llm_clients.models import ContentBlock, ConversationSession
    s = ConversationSession()
    s.add_user_message([ContentBlock.text_block(prompt)], cwd=str(PROJECT_ROOT))
    nodes, _u, _ = await client.call_api(s, max_tokens=max_tokens, thinking_budget_tokens=1024,
                                         meta_info={"task": "interventions_v3"})
    return "\n".join(b.text for n in nodes for b in n.message.content if b.type == "text" and b.text)


def _parse_json(text: str) -> Dict[str, Any]:
    from src.datasets.pr_review_v2.predictions import _extract_json_object
    try:
        return _extract_json_object(text)
    except ValueError:
        return {}


async def pr_summary_stage(pr: int, rec: Dict[str, Any], client, model: str) -> str:
    """Per-PR context: what the PR does (cached). Conditions merge + enrich; stored on rows."""
    inp = rec.get("input") or {}
    cache = CACHE_ROOT / "summary" / f"{_key(pr, inp.get('title'), model, SUMMARY_PROMPT_VERSION)}.json"
    if cache.exists():
        return json.loads(cache.read_text())["pr_summary"]
    out = _parse_json(await _call(client, PR_SUMMARY_PROMPT.format(
        pr_number=pr, title=inp.get("title") or "",
        description=(inp.get("description") or "")[:2500], menu=_hunk_menu(rec))))
    summary = str(out.get("pr_summary") or "").strip()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"pr_summary": summary}, ensure_ascii=False))
    return summary


async def merge_stage(pr: int, seeds: List[Dict[str, Any]], rec: Dict[str, Any], pr_summary: str,
                      client, model: str) -> List[List[int]]:
    """Stage 3: LLM-proposed cross-seed merges (cached). Returns merge groups (lists of seed idx)."""
    if len(seeds) < 2:
        return []
    payload = [[c.get("id") for c in s["comments"]] + [s["comments"][0].get("body")] for s in seeds]
    cache = CACHE_ROOT / "merge" / f"{_key(pr, payload, model, MERGE_PROMPT_VERSION)}.json"
    if cache.exists():
        return json.loads(cache.read_text())["merges"]
    didx = _delta_index(rec)
    desc = []
    for i, s in enumerate(seeds):
        c0 = s["comments"][0]
        anchor = (c0.get("anchor") or {})
        heads = []
        for c in s["comments"]:
            for h in (c.get("linked_hunks") or [])[:2]:
                if h in didx:
                    heads.append("\n".join((didx[h].get("patch") or "").splitlines()[1:3])[:110])
        body = " | ".join((c.get("body") or "")[:300] for c in s["comments"][:3])
        desc.append(f"[{i}] author={c0.get('author')} stratum={c0.get('stratum')} "
                    f"file={anchor.get('path')} anchored-code={' / '.join(heads[:2]) or '?'} :: {body}")
    out = _parse_json(await _call(client, MERGE_PROMPT.format(
        pr_summary=pr_summary or "(unavailable)", clusters="\n".join(desc))))
    merges = [g for g in (out.get("merges") or [])
              if isinstance(g, list) and len(g) > 1 and all(isinstance(i, int) and 0 <= i < len(seeds) for i in g)]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"merges": merges}))
    return merges


async def enrich_stage(pr: int, rec: Dict[str, Any], comments: List[Dict[str, Any]],
                       pr_summary: str, client, model: str) -> Dict[str, Any]:
    """Stage 4: canonical_ask + concern + judgeable + anchor set (cached)."""
    ids = [c.get("id") for c in comments]
    cache = CACHE_ROOT / "enrich" / f"{_key(pr, ids, [c.get('body') for c in comments], model, ENRICH_PROMPT_VERSION)}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    didx = _delta_index(rec)
    linked = [h for c in comments for h in (c.get("linked_hunks") or []) if h in didx]
    sections = evidence_sections(rec, comments, linked)
    ctext = "\n".join(f"- [{c.get('author')} @ {c.get('submitted_at')}] {(c.get('body') or '')[:2000]}"
                      for c in comments)
    out = _parse_json(await _call(client, ENRICH_PROMPT.format(
        pr_number=pr, title=(rec.get("input") or {}).get("title") or "",
        pr_summary=pr_summary or "(unavailable)",
        comments=ctext, reviewed=sections["reviewed"], proposed=sections["proposed"],
        adopted=sections["adopted"], menu=_hunk_menu(rec),
        concern_options='" | "'.join(CONCERNS))))
    result = {
        "canonical_ask": str(out.get("canonical_ask") or "").strip(),
        "rationale": str(out.get("rationale") or "").strip(),
        "rationale_source": out.get("rationale_source") if out.get("rationale_source") in ("stated", "inferred") else "inferred",
        "concern": out.get("concern") if out.get("concern") in CONCERNS else "other",
        "severity": out.get("severity") if out.get("severity") in ("blocking", "advisory") else "advisory",
        "judgeable": bool(out.get("judgeable")) and bool(str(out.get("canonical_ask") or "").strip()),
        "meta": bool(out.get("meta")),
        "anchor_hunk_ids": [h for h in (out.get("anchor_hunk_ids") or []) if h in didx],
        "linked_hunk_ids": list(dict.fromkeys(linked)),
    }
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result, ensure_ascii=False))
    return result


def _ident_evidence(ask: str, rec: Dict[str, Any], max_idents: int = 8) -> str:
    """Mechanical, truncation-immune adoption evidence: for each backticked identifier in the
    canonical ask, full-text presence on the reviewed side vs the post-revision side of the WHOLE
    delta, with the first matching lines quoted verbatim."""
    didx = _delta_index(rec)
    idents = list(dict.fromkeys(_TICK_RE.findall(ask)))[:max_idents]
    if not idents:
        return "(the ask names no backticked identifiers — judge from the code sections above)"
    out = []
    for t in idents:
        pre_lines, post_lines = [], []
        for h in didx.values():
            for line in (h.get("patch") or "").splitlines():
                if t in line:
                    (pre_lines if h.get("op") == "removed_in_revision" else post_lines).append(line.strip()[:140])
        out.append(f"- `{t}` | reviewed side: {'YES' if pre_lines else 'no'} | "
                   f"post-revision side: {'YES' if post_lines else 'no'}")
        for tag, ls in (("reviewed", pre_lines), ("post-rev", post_lines)):
            for l in ls[:2]:
                out.append(f"     [{tag}] {l}")
    return "\n".join(out)


async def outcome_stage(pr: int, rec: Dict[str, Any], enriched: Dict[str, Any],
                        comments: List[Dict[str, Any]], client, model: str) -> Dict[str, Any]:
    """Stage 5: adoption label from revision hunks at the anchors (cached)."""
    cache = CACHE_ROOT / "outcome" / f"{_key(pr, enriched.get('canonical_ask'), model, OUTCOME_PROMPT_VERSION)}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    anchors = list(dict.fromkeys((enriched.get("linked_hunk_ids") or [])
                                 + (enriched.get("anchor_hunk_ids") or [])))
    sections = evidence_sections(rec, comments, anchors, max_chars=900)
    # adoption may happen AWAY from the anchors (new lemma added elsewhere, code moved): show the
    # rest of the revision delta too — 28/46 v3 "dropped" labels never saw these hunks.
    didx = _delta_index(rec)
    others = [h for hid, h in didx.items() if hid not in set(anchors)]
    elsewhere = "\n\n".join(
        f"[{h.get('op')} @ {h.get('path')}:{h.get('new_start')}]\n{(h.get('patch') or '')[:600]}"
        for h in others[:12]) or "(none)"
    outc = (rec.get("gold") or {}).get("outcome") or {}
    out = _parse_json(await _call(client, OUTCOME_PROMPT.format(
        canonical_ask=enriched.get("canonical_ask") or "",
        resolved=[c.get("thread_resolved") for c in comments],
        merged=outc.get("merged"), rounds=outc.get("rounds"),
        reviewed=sections["reviewed"], adopted=sections["adopted"], elsewhere=elsewhere,
        ident_table=_ident_evidence(enriched.get("canonical_ask") or "", rec))))
    label = out.get("outcome")
    if label not in ("adopted", "partially_adopted", "contested", "dropped", "unknown"):
        label = "unknown"
    result = {"outcome": label, "outcome_evidence": str(out.get("outcome_evidence") or "")[:400]}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(result, ensure_ascii=False))
    return result


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def _apply_merges(seeds: List[Dict[str, Any]], merges: List[List[int]]) -> List[Dict[str, Any]]:
    taken = set()
    out = []
    groups = {min(g): sorted(set(g)) for g in merges}
    for i, s in enumerate(seeds):
        if i in taken:
            continue
        if i in groups:
            cs = [c for j in groups[i] for c in seeds[j]["comments"]]
            taken.update(groups[i])
            out.append({"comments": sorted(cs, key=lambda c: c.get("submitted_at") or "")})
        else:
            out.append(s)
    return out


def _stratum_of(comments: List[Dict[str, Any]]) -> str:
    order = {"V1": 0, "V2": 1, "V3": 2, "V4": 3}
    return sorted((c.get("stratum") for c in comments if c.get("stratum") in ACTIONABLE),
                  key=lambda s: order[s])[0]


async def build(records_path: Path, out_path: Path, model: str, concurrency: int, logger) -> Path:
    from ape.llm_clients.client import LLMClient
    from ape.llm_clients.config import LLMConfig

    recs = [json.loads(l) for l in records_path.read_text().splitlines() if l.strip()]
    recs = [r for r in recs if any((c.get("stratum") or "") in ACTIONABLE
                                   for c in (r.get("gold", {}).get("comments") or []))]
    logger.info("Building interventions from %d PRs with actionable comments", len(recs))

    sem = asyncio.Semaphore(concurrency)
    interventions: List[Dict[str, Any]] = []

    cfg = LLMConfig(model_name=model, max_tokens=4000, thinking_budget_tokens=1024)
    async with LLMClient(cfg, logger=logger) as client:
        async def one_pr(rec):
            pr = rec["pr_number"]
            async with sem:
                seeds = seed_clusters(rec)
                pr_summary = await pr_summary_stage(pr, rec, client, model)
                merges = await merge_stage(pr, seeds, rec, pr_summary, client, model)
                clusters = _apply_merges(seeds, merges)
                didx = _delta_index(rec)
                rows = []
                for n, cl in enumerate(clusters, 1):
                    enriched = await enrich_stage(pr, rec, cl["comments"], pr_summary, client, model)
                    outcome = await outcome_stage(pr, rec, enriched, cl["comments"], client, model)
                    anchor_ids = list(dict.fromkeys(
                        (enriched.get("linked_hunk_ids") or []) + (enriched.get("anchor_hunk_ids") or [])))
                    anchors, seen_span = [], set()
                    for h in anchor_ids:
                        hd = didx.get(h)
                        if not hd:
                            continue
                        ns, nl = int(hd.get("new_start") or 1), int(hd.get("new_lines") or 1)
                        span = (hd.get("path"), ns, ns + max(nl - 1, 0))
                        if span in seen_span:  # added/removed revision pairs share a location
                            continue
                        seen_span.add(span)
                        anchors.append({"hunk_id": h, "path": hd.get("path"), "line_start": ns,
                                        "line_end": ns + max(nl - 1, 0),
                                        "inferred": h not in (enriched.get("linked_hunk_ids") or [])})
                    rows.append({
                        "schema_version": SCHEMA_VERSION,
                        "intervention_id": f"pr{pr}_i{n:02d}",
                        "pr_number": pr,
                        "pr_summary": pr_summary,
                        "stratum": _stratum_of(cl["comments"]),
                        "concern": enriched["concern"],
                        "canonical_ask": enriched["canonical_ask"],
                        "rationale": enriched["rationale"],
                        "rationale_source": enriched.get("rationale_source", "inferred"),
                        "severity": enriched["severity"],
                        "judgeable": enriched["judgeable"],
                        "meta": enriched.get("meta", False),
                        "lint": lint_ask(enriched["canonical_ask"], enriched["judgeable"]),
                        "anchors": anchors,
                        "source_comments": [{"id": c.get("id"), "author": c.get("author"),
                                             "submitted_at": c.get("submitted_at"),
                                             "stratum": c.get("stratum"),
                                             "body": c.get("body")} for c in cl["comments"]],
                        "outcome": outcome["outcome"],
                        "outcome_evidence": outcome["outcome_evidence"],
                    })
                return rows

        results = await asyncio.gather(*(one_pr(r) for r in recs), return_exceptions=True)
    failures = [e for e in results if isinstance(e, Exception)]
    for rows in results:
        if not isinstance(rows, Exception):
            interventions.extend(rows)
    if failures:
        logger.warning("%d PRs failed (uncached stages remain retryable): %s",
                       len(failures), str(failures[0])[:200])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for iv in interventions:
            fh.write(json.dumps(iv, ensure_ascii=False) + "\n")
    _write_digest(interventions, out_path.with_name(out_path.stem + "_review.md"))
    sizes = Counter(len(iv["source_comments"]) for iv in interventions)
    logger.info("Wrote %d interventions -> %s | cluster sizes: %s | judgeable: %d | outcomes: %s",
                len(interventions), out_path, dict(sorted(sizes.items())),
                sum(iv["judgeable"] for iv in interventions),
                dict(Counter(iv["outcome"] for iv in interventions)))
    if failures:
        raise RuntimeError(f"{len(failures)} PRs failed; re-run to resume from cache.")
    return out_path


def _write_digest(interventions: List[Dict[str, Any]], path: Path) -> None:
    """The human-skim file: one block per intervention, gold text next to the canonical ask."""
    lines = ["# Interventions review digest", "",
             f"{len(interventions)} interventions | "
             f"judgeable {sum(i['judgeable'] for i in interventions)} | "
             f"outcomes {dict(Counter(i['outcome'] for i in interventions))}", ""]
    for iv in interventions:
        lines.append(f"## {iv['intervention_id']}  [{iv['stratum']}/{iv['concern']}/"
                     f"{iv['outcome']}{'' if iv['judgeable'] else ' | NOT JUDGEABLE'}"
                     f"{' | META' if iv.get('meta') else ''}]")
        lines.append(f"**ask**: {iv['canonical_ask']}")
        for w in (iv.get("lint") or []):
            lines.append(f"**⚠ LINT**: {w}")
        if iv.get("rationale"):
            lines.append(f"**why** ({iv.get('rationale_source', '?')}): {iv['rationale']}")
        lines.append(f"**anchors**: " + ", ".join(
            f"{a['path'].split('/')[-1]}:{a['line_start']}{'*' if a['inferred'] else ''}"
            for a in iv["anchors"]) + "  (* = inferred)")
        for c in iv["source_comments"]:
            lines.append(f"> [{c['stratum']}] {(c['body'] or '')[:250]}".replace("\n", " "))
        lines.append("")
    path.write_text("\n".join(lines))


def main() -> None:
    p = argparse.ArgumentParser(description="Build the intervention-level gold (dataset v3, Phase A)")
    p.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    p.add_argument("--out", type=Path, default=OUT_DIR / "interventions_v5.jsonl")
    p.add_argument("--model", default="gpt_5.2")
    p.add_argument("--concurrency", type=int, default=8)
    args = p.parse_args()
    logger = create_logger()
    asyncio.run(build(args.records, args.out, args.model, args.concurrency, logger))


if __name__ == "__main__":
    main()
