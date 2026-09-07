"""The judge's unit of work and its verdict."""

from typing import Dict, List, Literal, Optional, get_args
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import StrictModel
from .runs import PairingTier


class SemanticPair(StrictModel):
    """One planned comparison, sealed before the judge is asked anything.

    Planning pairs as artifacts is what makes the verdict set checkable: the returned
    verdicts must reconcile exactly against these, so a pair that silently produced no
    verdict is a coverage failure rather than an invisible miss.
    """

    schema_version: Literal["semantic-pair1"] = "semantic-pair1"
    pair_id: str
    obligation_id: str
    obligation_source_sha256: str
    candidate_id: str
    candidate_source_sha256: str
    pr_number: int
    pairing_tier: PairingTier
    #: Why this tier applies — the shared change IDs, the relation ID, or the shared path.
    #: "Has a valid relation" is not a coherent requirement at the `file` tier.
    tier_justification: str
    gold_change_ids: List[str]
    candidate_change_ids: List[str]
    gold_code_sha256: str
    #: Absent at the `anchor` tier, where both sides point at the same code.
    candidate_code_sha256: Optional[str] = None
    prompt_sha256: str
    judge_identity: str
    #: `null` pairs calibrate how often the judge matches things that merely sit near each
    #: other. They are judged alongside the observed pairs and excluded from every recall.
    role: Literal["observed", "null"] = "observed"
    source_sha256: str


class SemanticMatch(StrictModel):
    schema_version: Literal["semantic-match1"] = "semantic-match1"
    match_id: str
    candidate_id: str
    obligation_id: str
    issue_match: bool
    resolution_match: bool
    reason: str
    judge_model: str
    judge_version: str
    candidate_source_sha256: str
    obligation_source_sha256: str
    #: Carried so a widened verdict can never be counted as an anchored one. Defaults keep
    #: verdicts written before tiered pairing loadable.
    pairing_tier: PairingTier = "anchor"
    role: Literal["observed", "null"] = "observed"
    abstain: bool = False
    pair_id: Optional[str] = None
    source_sha256: str
