"""
Natural-language distillation of a PR — a shared, reusable artifact.

Hypothesis under test (selector follow-up): a maintainer is more likely to flag a proof
when the *Lean* proof obscures or diverges from the *natural-language* mathematical
argument — i.e. the proof is hard to follow relative to the intended idea. Distilling each
changed declaration into (NL statement, NL proof sketch, a legibility score, divergence
notes) surfaces that, and the per-declaration legibility becomes a selection signal: a
finding on a LOW-legibility proof is more maintainer-worthy.

Design intent — this is a building block, not a one-off:
  - `PRDistillation` / `DeclDistillation` are the stable artifact schema. Anything that
    wants "what is this PR's math, and which proofs are opaque" reads this — the selector
    (now), and later the holistic review agent and the checkers.
  - `distill_prs` computes + caches the artifact per PR (one LLM call/PR). The cache is the
    shared resource: a second consumer hits it for free.
  - Evolution path: promote `distill_prs` into a registered `lean_pr_review_distill` task
    that subclasses BasePRReviewTask (so it can READ the workspace and even lean_verify
    instead of working from the diff alone) and emits this SAME `PRDistillation` via a
    submit tool — at which point the orchestrator composes it with the other review tasks.
    Keeping the schema/prompt/cache here means that promotion is a thin wrapper.

No task wiring yet — this is the small probe stage (see distillation_probe.py).
"""

import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ape.utils.project import PROJECT_ROOT

DISTILL_CACHE = PROJECT_ROOT / "data" / "pr_review_v2" / "cache" / "distillation"
DIFF_CAP = 14000
DISTILL_PROMPT_VERSION = "v1"


class DeclDistillation(BaseModel):
    name: str = ""
    nl_statement: str = ""          # what it asserts, in plain mathematical English
    nl_proof_sketch: str = ""       # the natural argument a mathematician would give
    legibility: int = 50            # 0-100: how directly the Lean proof follows the NL argument
    divergence: str = ""            # where/why the Lean proof obscures/departs from that argument


class PRDistillation(BaseModel):
    pr_number: int
    pr_summary: str = ""
    declarations: List[DeclDistillation] = Field(default_factory=list)
    prompt_version: str = DISTILL_PROMPT_VERSION
    parse_ok: bool = True


DISTILL_PROMPT = """You are reading a Mathlib pull request to understand the MATHEMATICS behind each
proof it adds or changes — the intended idea — independent of Lean syntax.

For each theorem/lemma/def the PR ADDS or MEANINGFULLY CHANGES that has a non-trivial proof, give:
- `name`: the declaration name.
- `nl_statement`: what it asserts, in plain mathematical English.
- `nl_proof_sketch`: the natural argument you'd give a colleague — the intended idea, a few sentences.
- `legibility` (0-100): how DIRECTLY the Lean proof follows that natural argument. 100 = the Lean
  proof transparently mirrors the math, step for step. Low = the Lean proof is convoluted, indirect,
  or obscures the idea relative to the clean argument (e.g. heavy bespoke `rw` chains, metavariable
  gymnastics, redundant case work, a clever-but-opaque tactic sequence, or a `calc` that hides why it
  works). Judge the PROOF's transparency, not whether the statement is interesting.
- `divergence`: one sentence on where/why the Lean proof departs from or obscures the natural
  argument — empty string if the proof is clean and follows the idea directly.

## Pull request
Title: {title}
{description}

## Diff
{diff}

Answer with ONE JSON object:
{{"pr_summary": "<one sentence on what the PR does>",
  "declarations": [{{"name": "...", "nl_statement": "...", "nl_proof_sketch": "...",
                     "legibility": <int>, "divergence": "..."}}, ...]}}
Include only declarations the PR adds or meaningfully changes; omit trivial one-liners."""


def _cache_key(pr_number: int, diff: str, model: str) -> str:
    payload = json.dumps([pr_number, hashlib.md5((diff or "").encode()).hexdigest(),
                          model, DISTILL_PROMPT_VERSION], sort_keys=True)
    return hashlib.md5(payload.encode()).hexdigest()


async def distill_prs(
    pr_inputs: Dict[int, Dict[str, Any]], model: str, concurrency: int, logger,
) -> Dict[int, PRDistillation]:
    """Distill each PR (cached). `pr_inputs[pr]` is the gold record's `input` dict
    (title/description/diff). Returns pr -> PRDistillation."""
    from ape.llm_clients.client import LLMClient
    from ape.llm_clients.config import LLMConfig
    from ape.llm_clients.models import ContentBlock, ConversationSession
    from src.mathlib_review.model_output import extract_json_object

    DISTILL_CACHE.mkdir(parents=True, exist_ok=True)
    out: Dict[int, PRDistillation] = {}
    pending = []
    for pr, inp in pr_inputs.items():
        cf = DISTILL_CACHE / f"{_cache_key(pr, inp.get('diff', ''), model)}.json"
        if cf.exists():
            out[pr] = PRDistillation.model_validate(json.loads(cf.read_text()))
        else:
            pending.append((pr, inp, cf))
    logger.info("Distillation: %d cached, %d to distill", len(out), len(pending))
    if not pending:
        return out

    sem = asyncio.Semaphore(concurrency)

    async def one(pr: int, inp: Dict[str, Any], cf: Path, client) -> None:
        prompt = DISTILL_PROMPT.format(
            title=inp.get("title", ""), description=(inp.get("description") or "")[:1500],
            diff=(inp.get("diff") or "")[:DIFF_CAP])
        async with sem:
            s = ConversationSession()
            s.add_user_message([ContentBlock.text_block(prompt)], cwd=str(PROJECT_ROOT))
            nodes, _u, _ = await client.call_api(
                s, max_tokens=4000, thinking_budget_tokens=1500,
                meta_info={"task": "pr_review_v2_distill"})
            text = "\n".join(b.text for n in nodes for b in n.message.content
                             if b.type == "text" and b.text)
        try:
            v = extract_json_object(text)
            decls = [DeclDistillation.model_validate(d) for d in (v.get("declarations") or [])
                     if isinstance(d, dict)]
            art = PRDistillation(pr_number=pr, pr_summary=str(v.get("pr_summary") or ""),
                                 declarations=decls)
        except (ValueError, TypeError) as exc:
            art = PRDistillation(pr_number=pr, parse_ok=False, pr_summary=f"parse_error: {exc}")
        cf.write_text(art.model_dump_json(indent=2))
        out[pr] = art

    cfg = LLMConfig(model_name=model, max_tokens=4000, thinking_budget_tokens=1500)
    async with LLMClient(cfg, logger=logger) as client:
        await asyncio.gather(*(one(pr, inp, cf, client) for pr, inp, cf in pending))
    return out


def load_distillations(path: Path) -> Dict[int, PRDistillation]:
    """Load PRDistillation artifacts from a JSONL (one per line) — e.g. the grounded
    distillation task's output. The shared way any consumer reads distillations."""
    out: Dict[int, PRDistillation] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        art = PRDistillation.model_validate_json(line)
        out[art.pr_number] = art
    return out


_IDENT_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*)`")


def _finding_ident(finding: Dict[str, Any]) -> Optional[str]:
    """Best guess at the declaration a finding targets: the lead backtick identifier in
    the claim, falling back to the suggested_fix."""
    for field in ("claim", "suggested_fix"):
        m = _IDENT_RE.search(str(finding.get(field) or ""))
        if m:
            return m.group(1)
    return None


def legibility_signal(
    finding: Dict[str, Any], artifact: Optional[PRDistillation], *, default: float = 50.0,
) -> float:
    """Selection signal = obscurity (100 - legibility) of the declaration the finding targets.
    Higher => the proof obscures the natural argument => more maintainer-worthy. Returns
    `default` (neutral) when the artifact is missing or the declaration can't be matched."""
    if artifact is None or not artifact.parse_ok or not artifact.declarations:
        return default
    ident = _finding_ident(finding)
    if not ident:
        return default
    # exact name match, else substring either direction (handles namespacing / partial names)
    decl = next((d for d in artifact.declarations if d.name == ident), None)
    if decl is None:
        decl = next((d for d in artifact.declarations
                     if d.name and (d.name in ident or ident in d.name)), None)
    if decl is None:
        return default
    return float(100 - max(0, min(100, decl.legibility)))
