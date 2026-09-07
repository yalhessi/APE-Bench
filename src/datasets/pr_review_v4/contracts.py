"""Seal the generation and evaluation contracts — separately, and in that order.

One pre-registration covering both would make the reviewer's contract depend on gold. The
reviewer never sees gold; that isolation is the single structural defence against the leak
that once produced a meaningless 99% location score, and a contract that hashes gold into
the generation plan quietly reintroduces the coupling.

So there are four artifacts, sealed at the three moments where something becomes knowable:

1. `GenerationPlanV2` — before generation. Gold-free, enforced by `assert_gold_free`.
2. `GenerationRunReceipt` — after each repetition. Repetitions are separate deployed
   systems; each gets its own receipt bound to the shared parent plan.
3. `EvaluationProtocol` + `PairManifest` — after generation, before judging. Policy and
   metric names are fixed here so the headline cannot be chosen after seeing verdicts.
4. `EvaluationReceipt` — after judging. Carries what was *observed* (the provider's actual
   model revision), which is not knowable when the plan is written.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from .io import canonical_json_bytes, sealed_model, sha256_bytes
from .schema import (
    EvaluationProtocol,
    EvaluationReceipt,
    GenerationPlanV2,
    GenerationRunReceipt,
    PairManifest,
)


CONTRACTS_VERSION = "split-contracts/1"

#: Anything whose presence in a generation plan would mean gold reached the reviewer's
#: contract. Checked against the serialized plan, so a nested or renamed field cannot slip
#: past by not being one of the names we thought to look for.
_GOLD_MARKERS = (
    "obligation", "judgment", "gold", "intervention_view", "ambiguous", "semantic_match",
    "resolution_criteria", "maintainer_comment",
)


class GoldLeakError(ValueError):
    """A generation-side artifact referenced gold."""


def assert_gold_free(plan: GenerationPlanV2) -> None:
    """Refuse to seal a generation plan that mentions gold.

    A structural check, not a naming convention: the plan is serialized and swept, so a
    field added later cannot bypass it by being called something else.
    """

    text = canonical_json_bytes(plan.model_dump(mode="json")).decode().lower()
    found = sorted({marker for marker in _GOLD_MARKERS if marker in text})
    if found:
        raise GoldLeakError(
            f"generation plan references gold ({', '.join(found)}); gold belongs to the "
            "evaluation protocol, never the reviewer's contract"
        )


#: Tokens too common to distinguish a leak from ordinary English or ordinary Lean. A gold
#: string that reduces to only these carries no information a reviewer could exploit.
_UNDISTINGUISHING = frozenset({
    "the", "a", "an", "to", "of", "and", "or", "in", "is", "it", "this", "that", "for",
    "be", "as", "with", "on", "by", "from", "not", "should", "use", "using", "add", "set",
    "rename", "replace", "lemma", "theorem", "proof", "name", "file", "line", "type",
})

#: How long a shared verbatim run has to be before it is a leak rather than a coincidence.
#: Seven words is well above what two independent descriptions of the same code share.
_MIN_LEAK_RUN = 7

#: Language and tactic names that legitimately appear in review instructions and happen to
#: also occur inside a gold claim. Deliberately tiny, and the standard is strict: a token
#: belongs here only if it names a *tactic or language feature*, never a declaration the gold
#: asks to add, rename or remove. Anything else on this list is a leak being waved through.
_GENERIC_LEAN_VOCABULARY = frozenset({
    "fun_prop", "to_fun", "simp_rw", "simp_all", "norm_num", "aesop", "omega",
    "gcongr", "linarith", "positivity", "gcongr_discharger", "gcongr_forward",
})


def _words(text: str) -> List[str]:
    return [w for w in re.findall(r"[A-Za-z0-9_.'\u2019]+", (text or "").lower()) if w]


#: A Lean identifier, for leak purposes: long, and carrying a `.` or `_`. Length alone is
#: not enough — an early version matched any word of eight characters and would have flagged
#: "Complete" and "Generalize" in every prompt that contains ordinary English.
#: Requires a `_`, or a `.` with a letter after it — so `Dense.upperBounds_image` and
#: `round_eq_div` match while an ordinary word ending a sentence ("statement.") does not.
_IDENTIFIER = re.compile(
    r"[A-Za-z_][A-Za-z0-9_']*(?:[._][A-Za-z0-9_'][A-Za-z0-9_.']*)+")

#: Source-file suffixes. A path is not an identifier: gold names the file it is about, and a
#: reviewer is *given* that file — `Inverses.lean` appearing in both is the review working,
#: not the answer leaking. Without this the check fires on any prompt that names a changed
#: file, which is every prompt with a file skeleton in it.
_FILE_SUFFIXES = (".lean", ".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt")


def _informative(text: str) -> List[str]:
    return [w for w in _words(text) if w not in _UNDISTINGUISHING]


def prompt_leaks(prompt_text: str, gold_strings: Iterable[str]) -> List[str]:
    """Gold phrasings that appear verbatim in a prompt.

    Two shapes are caught, because the leaks measured had both:

    * a **declaration name** the gold asks for — `round_eq_div` was written into the
      submission contract as an illustration of a good rename request, and it is the exact
      new name PR 33421's maintainer asked for. Identifiers are extracted from *within* gold
      claims, since a claim is a sentence and the leak is one token inside it.
    * a **run of prose** copied from a gold claim — a docstring sentence lifted verbatim from
      PR 33321 into the documentation arm's instructions.

    Both sides are filtered identically before comparison. Filtering stop-words out of gold
    but not out of the prompt is why the first version of this check reported the codebase
    clean while three leaks were sitting in it.
    """

    haystack = (prompt_text or "")
    lowered = haystack.lower()
    prompt_runs = set()
    prompt_words = _informative(haystack)
    for i in range(max(0, len(prompt_words) - _MIN_LEAK_RUN + 1)):
        prompt_runs.add(tuple(prompt_words[i:i + _MIN_LEAK_RUN]))

    found: List[str] = []
    for gold in gold_strings:
        if not gold:
            continue
        text = str(gold)
        for identifier in _IDENTIFIER.findall(text):
            if len(identifier) < 8 or identifier.lower() in _GENERIC_LEAN_VOCABULARY:
                continue
            if identifier.lower().endswith(_FILE_SUFFIXES):
                continue
            # Whole-identifier, not substring. `Finset.sum` occurs inside `Finset.sum_comm`,
            # and a prompt naming the latter has not quoted the former — matching by
            # substring reported that as a leak and would do so for any shared namespace.
            boundary = re.compile(
                r"(?<![A-Za-z0-9_.'])" + re.escape(identifier) + r"(?![A-Za-z0-9_.'])",
                re.IGNORECASE)
            if boundary.search(haystack):
                found.append(identifier)
        gold_words = _informative(text)
        for i in range(max(0, len(gold_words) - _MIN_LEAK_RUN + 1)):
            run = tuple(gold_words[i:i + _MIN_LEAK_RUN])
            if run in prompt_runs:
                found.append(" ".join(run))
                break
    return sorted(set(found))


def assert_prompts_gold_free(prompts: Iterable[str], gold_strings: Iterable[str]) -> None:
    """Refuse a run whose prompts quote the answers.

    `assert_gold_free` sweeps the sealed *agenda*, and the agenda carries prompt **hashes**
    only — so prompt text has always been outside that check by construction. Three exact
    heldout answers reached the arms' instructions that way: two written as illustrations
    while editing an arm prompt and a submission contract, one inherited. An illustration is
    exactly how this happens, because a real example is the most natural thing to reach for
    and the evaluation set is the code you have been reading.
    """

    gold = list(gold_strings)
    leaks = {}
    for index, prompt in enumerate(prompts):
        found = prompt_leaks(prompt, gold)
        if found:
            leaks[index] = found
    if leaks:
        detail = "; ".join(f"prompt {i}: {', '.join(v)}" for i, v in sorted(leaks.items()))
        raise GoldLeakError(
            f"{len(leaks)} rendered prompt(s) quote gold verbatim — {detail}. A reviewer that "
            "has been handed the answer is not measuring discovery."
        )


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _seal(model, prefix: str, **values):
    draft = sealed_model(model, **{f"{prefix}_id": "", **values})
    return draft.model_copy(update={f"{prefix}_id": f"{prefix}:{draft.source_sha256[:24]}"})


def seal_generation_plan(**values) -> GenerationPlanV2:
    values.setdefault("created_at", _now())
    plan = _seal(GenerationPlanV2, "plan", **values)
    assert_gold_free(plan)
    return plan


def seal_generation_receipt(plan: GenerationPlanV2, **values) -> GenerationRunReceipt:
    values.setdefault("completed_at", _now())
    return _seal(
        GenerationRunReceipt, "receipt",
        plan_id=plan.plan_id, plan_sha256=plan.source_sha256, **values,
    )


def seal_evaluation_protocol(**values) -> EvaluationProtocol:
    values.setdefault("created_at", _now())
    return _seal(EvaluationProtocol, "protocol", **values)


def seal_pair_manifest(protocol: EvaluationProtocol, **values) -> PairManifest:
    values.setdefault("created_at", _now())
    return _seal(
        PairManifest, "manifest",
        protocol_id=protocol.protocol_id, protocol_sha256=protocol.source_sha256, **values,
    )


def seal_evaluation_receipt(manifest: PairManifest, **values) -> EvaluationReceipt:
    values.setdefault("completed_at", _now())
    return _seal(
        EvaluationReceipt, "receipt",
        manifest_id=manifest.manifest_id, manifest_sha256=manifest.source_sha256, **values,
    )


def verify_chain(
    plan: GenerationPlanV2,
    receipts: Sequence[GenerationRunReceipt],
    protocol: EvaluationProtocol,
    manifest: PairManifest,
    evaluation: EvaluationReceipt,
) -> Dict:
    """Check that every artifact binds to the one it claims to descend from.

    Each link is a hash, not a name, so a plan cannot be edited and re-pointed at silently:
    the child's recorded parent hash stops matching.
    """

    problems = []
    for receipt in receipts:
        if receipt.plan_sha256 != plan.source_sha256:
            problems.append(f"receipt {receipt.receipt_id} descends from a different plan")
    if manifest.protocol_sha256 != protocol.source_sha256:
        problems.append("pair manifest descends from a different evaluation protocol")
    if evaluation.manifest_sha256 != manifest.source_sha256:
        problems.append("evaluation receipt descends from a different pair manifest")
    covered = {item.receipt_id for item in receipts}
    missing = sorted(set(manifest.generation_receipt_ids) - covered)
    if missing:
        problems.append(f"pair manifest cites unknown generation receipts: {missing}")
    if plan.repetitions != len(receipts):
        problems.append(
            f"plan declares {plan.repetitions} repetitions but {len(receipts)} receipts exist"
        )
    if problems:
        raise ValueError("contract chain is broken: " + "; ".join(problems))
    return {
        "contracts_version": CONTRACTS_VERSION,
        "plan_id": plan.plan_id,
        "protocol_id": protocol.protocol_id,
        "repetitions": len(receipts),
        "scored": evaluation.scored,
        "coverage_complete": evaluation.coverage_complete,
        "complete": True,
    }
