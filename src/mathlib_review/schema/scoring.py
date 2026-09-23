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


class SilenceLabel(StrictModel):
    """Why one specialist arm said nothing at one site a maintainer asked about.

    The companion to `AdjudicationLabel` on the other side of the ledger: that one labels a
    finding gold cannot judge, this one labels a *silence* gold can. Replay established that 41
    of 45 such silences reproduce from an identical prefix, so they are readings of a contract
    rather than sampling noise -- and a reading is a thing a person can name, but only by
    reading what the arm wrote. The reason enum will not do it: 17 of those 45 sessions produced
    a different `abstention_reason` under replay with the same outcome, `already_correct` and
    `could_not_establish` swapping freely. The label is made from `abstention_detail`.

    Eight labels, because the first pass over the 43 found eight mechanisms and collapsing them
    is what sent the first round of interventions at the wrong three:

    * `off_concern` -- the ask is outside this arm's remit, and the silence is correct. The
      majority (32 of 43 on the first read), and evidence about *routing*, not about the arm.
    * `fix_required` -- the arm has the maintainer's answer and no compiling edit, which the
      submission contract refuses (`candidates.py`, the checkable families).
    * `advisory_suppressed` -- the evidence supports an advisory ask and the arm withheld it.
    * `cross_unit` -- seen, real, and unanchorable in this work unit.
    * `evidence_gap` -- a tool could not produce what the arm needed; `evidence_gap_tool` names
      which, because "the tools are weak" is not an actionable finding and "`naming_norm`
      returned insufficient_evidence on a resolvable subject" is.
    * `knowledge_gap` -- the arm did not know the thing the maintainer knew.
    * `disagreement` -- the arm considered the ask and judged against it, on stated grounds.
    * `decision_noise` -- replay shows the same prefix files at least sometimes.

    **Not gold, and not a score.** Like `AdjudicationLabel` this orders work and explains a
    number; it never enters recall. A silence labelled `off_concern` is not a miss the arm
    committed, and a labelled corpus of silences is not a benchmark.
    """

    schema_version: Literal["silence-label1"] = "silence-label1"
    #: `<invocation_id>|<obligation_id>`. The invocation is `<work_unit_id>#<arm_id>` and work
    #: units are derived from the release, so this key survives into any rep built on the same
    #: release -- which is what makes labelling 43 cells worth the hour it takes.
    key: str
    invocation_id: str
    obligation_id: str
    pr_number: int
    arm_id: str
    label: Literal[
        "off_concern",
        "fix_required",
        "advisory_suppressed",
        "cross_unit",
        "evidence_gap",
        "knowledge_gap",
        "disagreement",
        "decision_noise",
    ]
    #: Required by `evidence_gap` and forbidden otherwise: the tool that could not answer.
    evidence_gap_tool: Optional[str] = None
    #: `human:<name>` or `task:<identity>`, ordered the way `AdjudicationLabel` orders them.
    labelled_by: str
    #: The generation run whose silence this is, and the replay whose stability was read
    #: alongside it. The replay is optional: a silence can be labelled without one, and the
    #: label then rests on one sample.
    from_run: str
    replay_run: Optional[str] = None
    written_at: str
    #: What in the arm's own words settled it. A label with no quotation is an opinion.
    note: str = ""

    @model_validator(mode="after")
    def _tool_named_exactly_when_relevant(self) -> "SilenceLabel":
        if self.label == "evidence_gap" and not self.evidence_gap_tool:
            raise ValueError(
                "evidence_gap needs `evidence_gap_tool`: which tool could not answer is the "
                "whole content of the label, and 'the tools are weak' funds nothing")
        if self.label != "evidence_gap" and self.evidence_gap_tool:
            raise ValueError(
                f"`evidence_gap_tool` is set on a {self.label!r} label, which does not mean a "
                "tool failed; say it in `note` instead")
        return self

    @model_validator(mode="after")
    def _key_is_its_parts(self) -> "SilenceLabel":
        expected = f"{self.invocation_id}|{self.obligation_id}"
        if self.key != expected:
            raise ValueError(f"key must be {expected!r}, not {self.key!r}")
        return self


def silence_key(invocation_id: str, obligation_id: str) -> str:
    """The one spelling of a silence's identity. Both readers and the writer call this."""

    return f"{invocation_id}|{obligation_id}"
