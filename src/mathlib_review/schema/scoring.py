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


# --- Measurement identity and the raw-ask matcher's records (2026-10-22) -----------------------
#
# The registered judge scores one finding against one atomic gold obligation; the raw-ask matcher
# scores a maintainer's first-round ask against every finding of each anonymous reviewer at once.
# They answer different questions and their numbers are never pooled. What they share is that
# every number carries the identity below: which instrument, against which references, of which
# subjects through which output channel, under which seal, with how many replicates. Until this
# record the matcher's inputs were written to a scratch directory outside the repository and only
# its verdicts were kept (`docs/research/task-dataflow-refactor-implementation-2026-10-22.md`).

AskMatchValue = Literal["reached", "partial", "no"]


class SubjectBinding(StrictModel):
    """Whose findings a session label stands for, and through which output channel.

    `packet`: a probe session's `findings.json`; `solo`: a run's submitted task findings
    (channel `submitted`, before finalization); `lead`: a run's `findings.jsonl` (channel
    `finalized`, with the published ones marked); `findings_file`: findings written to a file
    per PR and session by the study itself (channel `declared`); `run`: a run the registered judge
    scored, its finalized findings or its pre-merge candidates.
    """

    session: str
    source: Literal["packet", "solo", "lead", "findings_file", "run"]
    channel: Literal["packet", "submitted", "finalized", "declared", "candidates"]
    runs: List[str] = Field(default_factory=list)
    path: Optional[str] = None


class MeasurementIdentity(StrictModel):
    """What a measurement means, fixed before any verdict exists."""

    schema_version: Literal["measurement-identity1"] = "measurement-identity1"
    instrument: str
    instrument_version: str
    #: SHA-256 of the exact rubric text the instrument presents.
    rubric_sha256: str
    question_policy: Literal["request_only", "questions"] = "request_only"
    reference_kind: Literal["raw_ask", "atomic_obligation"]
    reference_source: str
    reference_sha256: str
    reference_count: int
    population_prs: List[int]
    seal_path: Optional[str] = None
    seal_sha256: Optional[str] = None
    subjects: List[SubjectBinding] = Field(default_factory=list)
    #: The blind projection: fields kept, redaction, and any cut, as the matcher saw them.
    projection: Dict[str, object] = Field(default_factory=dict)
    replicates: int
    aggregation: str
    denominator: str
    missingness: str
    source_sha256: str


class BlindAsk(StrictModel):
    """One maintainer ask as a matcher sees it."""

    ask_id: str
    path: Optional[str] = None
    code_at_comment: Optional[str] = None
    comment: str
    replies_to: Optional[str] = None


class BlindFinding(StrictModel):
    """One finding as a matcher sees it: its index and the four kept fields, redacted."""

    i: int
    target: Optional[str] = None
    claim: Optional[str] = None
    requested_change: Optional[str] = None
    severity: Optional[str] = None


class BlindPacket(StrictModel):
    """Everything a matcher sees of one PR: its asks and each label's findings."""

    pr: int
    asks: List[BlindAsk]
    reviewers: Dict[str, List[BlindFinding]]


class MatchBatch(StrictModel):
    batch_id: str
    prs: List[int]


class MatchingPlan(StrictModel):
    """A raw-ask matching, sealed before any matcher runs. Holds the exact blind inputs."""

    schema_version: Literal["matching-plan1"] = "matching-plan1"
    plan_id: str
    identity: MeasurementIdentity
    identity_sha256: str
    seal: Dict[str, Dict[str, str]]
    batches: List[MatchBatch]
    packets: List[BlindPacket]
    #: Per PR and session: findings count, compiles, a cut or a cap, as `session_stats.json` held.
    session_stats: Dict[str, Dict[str, Dict[str, object]]] = Field(default_factory=dict)
    expected_cells: int
    created_at: str
    source_sha256: str


class MatchVerdict(StrictModel):
    """One matcher replicate's verdicts on one batch, from a task sample or an external import.

    `asks` keeps the historical `matches.json` row shape (`"R1": value, "R1_finding": index`) so
    the reading arithmetic is the one every earlier seal was read with.
    """

    schema_version: Literal["match-verdict1"] = "match-verdict1"
    plan_id: str
    batch_id: str
    #: The execution or import this observation came from: `task-<run name>` or `import-<name>`.
    #: An observation is `(producer, replicate)`; two runs of one plan both number their samples
    #: from 1, and without the producer their rows merged into one supposed replicate
    #: (implementation review, 2026-10-22, finding 2).
    producer: str
    replicate: str
    origin: Literal["task", "external_import"]
    #: Where the verdict's bytes are: a task directory, sample and attempt; or a file and digest.
    locator: Dict[str, str]
    #: What executed it, where known; an unknown is written as "unknown", never guessed.
    executor: Dict[str, str]
    asks: List[Dict[str, object]]
    unmatched: Dict[str, Dict[str, int]] = Field(default_factory=dict)
