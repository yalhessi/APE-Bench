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


class AdjudicationLabel(StrictModel):
    """One human or model verdict on a finding that matched no maintainer obligation.

    Roughly 90% of what the system emits is off-gold, and nothing in the evaluation says
    whether any of it is useful. `gold_alignment_rate` is not precision -- gold is a lower
    bound, so a finding absent from it is *unaligned*, not wrong -- and the batching comparison
    moved alignment 0.069-0.091 to 0.181-0.202 while nobody could say whether the output had
    got better. That is the largest gap in the evaluation, and this is the record that closes
    it one claim at a time.

    Keyed by `review/merge.py::finding_key`, so a label survives the run it was made on: the
    site-and-kind key recurs 127 times across three reps where the full key recurs 0 times.
    Labelling amortises across repetitions for that reason and only that reason.

    Three labels, and the third is the one that matters. `valid_not_an_ask` is a finding that
    is true and that a maintainer would not have raised -- the category Tricorder's definition
    argues for keeping separate, and the one a two-way correct/wrong split silently forces into
    the wrong bucket.

    **Not gold.** Gold is what maintainers actually asked for, derived from what they wrote;
    these are judgements about what they did not ask for, and merging the two would destroy the
    revealed-preference property the whole benchmark rests on.
    """

    schema_version: Literal["adjudication-label1"] = "adjudication-label1"
    #: `finding_key(finding)`: pr number, primary change id, issue kind.
    key: str
    pr_number: int
    primary_change_id: str
    issue_kind: Optional[str] = None
    label: Literal["correct_ask", "wrong", "valid_not_an_ask"]
    #: The finding this label was made by reading. Later findings that reproduce the key
    #: inherit the label, and the exemplar is how a reader checks that inheritance is fair.
    exemplar_finding_id: str
    exemplar_action_key: str
    exemplar_source_sha256: str
    #: `human:<name>` or `task:<adjudicator identity>`. A human row outranks a model row on the
    #: same key, and the prefix is what says which is which.
    labelled_by: str
    adjudication_version: str
    #: The run whose findings were being read when this was labelled.
    from_run: str
    written_at: str
    note: str = ""
