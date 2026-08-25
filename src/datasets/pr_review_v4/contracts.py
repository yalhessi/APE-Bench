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
