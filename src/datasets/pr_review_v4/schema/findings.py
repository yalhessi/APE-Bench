"""What a reviewer produces: a candidate claim, the finding it becomes, and the issue
published from it, plus the synthesis records that decide which survive.
"""

from typing import Dict, List, Literal, Optional, get_args
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import StrictModel
from .evidence import EvidenceTier
from .opportunities import CandidateOpportunityLink


ConcernFamily = Literal[
    "correctness",
    "proof-golf",
    "duplication",
    "naming",
    "generalization",
    "documentation",
    "style",
    "scope",
    "other",
]


#: What kind of issue a finding claims — the same vocabulary the deterministic arm and the
#: C0–C2 census already speak, so the two arms sit on one axis.
#:
#: `concern_family` is too coarse to verify: "naming" is not a check, so no evidence
#: collector could ever support a naming claim and every one of them stayed `inconclusive`.
#: An issue kind names something checkable, and each kind routes to the operator that can
#: check it — `naming_convention_violation` to the snapshot population scan,
#: `style_norm_violation` to the text-style linter, `duplicate_implementation` to canonical
#: retrieval. The operators already exist; what was missing was the routing key.
IssueKind = Literal[
    "broken_build",
    "correctness_policy",
    "documentation_gap",
    "duplicate_implementation",
    "generalization_available",
    "missed_canonical_api",
    "naming_convention_violation",
    "policy_violation",
    "proof_simplification",
    "scope_placement",
    "style_norm_violation",
]


class SynthesisAnchor(StrictModel):
    change_id: str
    source_candidate_ids: List[str] = Field(min_length=1)
    source_opportunity_ids: List[str] = Field(min_length=1)
    relation_ids: List[str] = Field(default_factory=list)


class SynthesizedFinding(StrictModel):
    """One publishable PR-level finding with complete many-to-one source lineage."""

    schema_version: Literal["synthesized-finding1"] = "synthesized-finding1"
    finding_id: str
    pr_number: int
    source_candidate_ids: List[str] = Field(min_length=1)
    source_opportunity_ids: List[str] = Field(min_length=1)
    investigation_ids: List[str] = Field(default_factory=list)
    change_ids: List[str] = Field(min_length=1)
    context_change_ids: List[str] = Field(default_factory=list)
    anchors: List[SynthesisAnchor] = Field(min_length=1)
    method_ids: List[str] = Field(min_length=1)
    action_key: str
    concern_family: ConcernFamily
    severity: Literal["blocking", "advisory"]
    claim: str
    requested_change: str
    evidence_artifact_ids: List[str] = Field(min_length=1)
    rank_key: str
    source_sha256: str

    @model_validator(mode="after")
    def anchors_must_equal_issue_changes(self):
        if {item.change_id for item in self.anchors} != set(self.change_ids):
            raise ValueError("synthesis anchors must account for every issue change ID exactly")
        if set(self.change_ids).intersection(self.context_change_ids):
            raise ValueError("issue and context-only change IDs must be disjoint")
        return self


class SynthesisDecision(StrictModel):
    schema_version: Literal["synthesis-decision1"] = "synthesis-decision1"
    synthesis_id: str
    pr_number: int
    action: Literal[
        "retain", "group", "suppress_duplicate", "suppress_dominated", "defer_conflict",
        "suppress_volume"
    ]
    opportunity_ids: List[str] = Field(min_length=1)
    candidate_ids: List[str] = Field(default_factory=list)
    finding_id: Optional[str] = None
    evidence_artifact_ids: List[str] = Field(default_factory=list)
    rationale: str
    source_sha256: str

    @model_validator(mode="after")
    def validate_finding_reference(self):
        if self.action in {"retain", "group", "suppress_duplicate"} and self.finding_id is None:
            raise ValueError(f"{self.action} decisions require a synthesized finding ID")
        if self.action in {"suppress_dominated", "defer_conflict", "suppress_volume"} and self.finding_id is not None:
            raise ValueError(f"{self.action} decisions cannot reference a published finding")
        return self


class SynthesisMatchProjection(StrictModel):
    """Gold-side projection used to measure whether synthesis retained an atomic match."""

    schema_version: Literal["synthesis-match-projection1"] = "synthesis-match-projection1"
    projection_id: str
    finding_id: str
    obligation_id: str
    source_candidate_ids: List[str] = Field(min_length=1)
    issue_match: bool
    resolution_match: bool
    source_match_ids: List[str] = Field(min_length=1)
    source_sha256: str


class EvidenceRequest(StrictModel):
    collector: Literal[
        "local_context", "repository_search", "lean_compile", "policy", "precedent"
    ]
    query: str
    purpose: Literal["support", "counterevidence", "both"] = "both"


class ProposedEdit(StrictModel):
    path: str
    declaration_name: Optional[str] = None
    new_declaration: Optional[str] = None
    line_start: Optional[int] = Field(default=None, ge=1)
    line_end: Optional[int] = Field(default=None, ge=1)
    replacement: Optional[str] = None


class CandidateClaim(StrictModel):
    schema_version: Literal["c1"] = "c1"
    candidate_id: str
    producer: Literal["model", "deterministic"] = "model"
    investigation_id: Optional[str] = None
    opportunity_ids: List[str] = Field(default_factory=list)
    work_unit_id: str
    #: Position within its own submission. Already inside the identity payload that mints
    #: `candidate_id`, but never recorded — so a candidate could not be joined to the
    #: verification artifact that compiled it, which is keyed on
    #: `(work_unit_id, candidate_ordinal)`. Optional so frozen candidate files still load;
    #: adding it does not move any existing `candidate_id`.
    ordinal: Optional[int] = None
    episode_id: str
    pr_number: int
    change_ids: List[str]
    entity_ids: List[str] = Field(default_factory=list)
    primary_change_id: Optional[str] = None
    primary_entity_id: Optional[str] = None
    primary_subject: Optional[str] = None
    requested_change: Optional[str] = None
    concern_family: ConcernFamily = "other"
    #: Optional on the model, required at ingestion from renderer `candidate-prompt/12`
    #: onward. It has to stay optional here or the frozen 0.9.x candidate files — written
    #: before the field existed — would no longer load, and those carry Phase 9's lineage.
    issue_kind: Optional[IssueKind] = None
    #: Which focused agent produced this, when one did. `issue_kind` is not enough to tell
    #: them apart: proof golf and proof idiom both declare `proof_simplification`, and they
    #: make *different* claims — golf says the proof gets shorter, idiom says it gets more
    #: canonical and explicitly may not. A verifier keyed on the issue kind alone would hand
    #: idiom's laxer warrant to golf candidates and repeal golf's own rule.
    spec_id: Optional[str] = None
    #: Non-gating, multi-valued. `concern_family` is one word chosen from a closed list and is
    #: what routing and verification key on; tags are what the claim was additionally observed
    #: to be. `off-concern:<arm_id>` records that a specialist declared a family outside its
    #: expected set — the fact the concern gate used to refuse the submission over.
    #:
    #: Deliberately outside the identity payload that mints `candidate_id`: an annotation must
    #: not be able to move a candidate's identity, and frozen candidate files must still load.
    concern_tags: List[str] = Field(default_factory=list)
    concern_label: str
    severity: Literal["blocking", "advisory"]
    claim: str
    suggested_fix: Optional[str] = None
    proposed_edit: Optional[ProposedEdit] = None
    evidence_requests: List[EvidenceRequest]
    model_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    source_sha256: str

    @model_validator(mode="before")
    @classmethod
    def infer_legacy_concern_family(cls, data):
        if isinstance(data, dict) and "concern_family" not in data:
            label = data.get("concern_label")
            families = set(ConcernFamily.__args__)
            data = {**data, "concern_family": label if label in families else "other"}
        return data


class FindingSource(StrictModel):
    """Where one contribution to a finding came from.

    Replaces `CandidateOpportunityLink` for the arm-neutral path. Opportunity lineage is
    *optional*: a holistic finding has none, and the old link required one, which is why
    `synthesis.link_candidates` raised on every holistic candidate and made a unified merge
    impossible.
    """

    schema_version: Literal["finding-source1"] = "finding-source1"
    #: `holistic` is the retired spelling of `generalist`, kept loadable because 264 frozen
    #: findings carry it. New writes use `generalist`: the arm was never holistic — 162 of
    #: 225 medium work units hold a single change target, and its prompt never contained the
    #: PR diff. It is a generalist reviewer of the same sites, with the same seven tools as
    #: the focused arm, differing only in breadth of checklist.
    arm: Literal["deterministic", "holistic", "generalist", "file_generalist",
                 "focused_agent"]
    candidate_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    method_id: Optional[str] = None
    #: Which focused spec produced this, when the arm is `focused_agent`. Golf and idiom
    #: make different claims under one issue kind, so the finding must record which.
    spec_id: Optional[str] = None
    evidence_artifact_ids: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _deterministic_sources_carry_lineage(self):
        if self.arm == "deterministic" and not (self.opportunity_id and self.evidence_artifact_ids):
            raise ValueError(
                "a deterministic source must name its opportunity and evidence; that "
                "lineage is what makes the arm auditable"
            )
        if self.arm in ("holistic", "generalist", "file_generalist") and not self.candidate_id:
            raise ValueError(f"a {self.arm} source must name its candidate")
        if self.arm == "focused_agent":
            # A focused finding's whole warrant is "an agent constructed this replacement and
            # the compiler accepted it". Without the candidate it cannot be traced to the
            # invocation that made it, and without the verification artifact the compile is
            # an unevidenced assertion — which is precisely the `model_assertion` tier the
            # arm exists to beat. Neither is optional here, unlike for a holistic source.
            if not self.candidate_id:
                raise ValueError("a focused source must name its candidate")
            if not self.spec_id:
                raise ValueError("a focused source must name the spec that produced it")
            if not self.evidence_artifact_ids:
                raise ValueError(
                    "a focused source must name its verification artifacts; the arm's "
                    "warrant is a compile, and an unevidenced compile is an assertion"
                )
        return self


class ReviewFinding(StrictModel):
    """One thing the system says about the PR, from either arm, in one shape.

    This is what gets judged. Scoring candidates *before* the merge and projecting verdicts
    back through them credits a finding for wording it no longer has — the merge keeps only
    the representative's text.
    """

    schema_version: Literal["review-finding1"] = "review-finding1"
    finding_id: str
    pr_number: int
    episode_id: str
    arm: Literal["deterministic", "holistic", "generalist", "file_generalist",
                 "focused_agent", "merged"]
    #: `published` is what the system would show a maintainer; `diagnostic` is retained and
    #: judged but never counted as system output. Keeping both is what lets the detection
    #: ceiling and the publishable result be reported without conflating them.
    admission: Literal["published", "diagnostic"]
    admission_reason: str
    #: Which output channels this finding belongs to.
    #:
    #: `admission` answers one question with one field and so conflates two: whether the
    #: system would say this, and whether it proved it. That conflation is what makes the
    #: publication ceiling read as a reviewer failure -- 27 of 43 gold obligations carry a
    #: concern no deterministic warrant can settle, so a correct finding about any of them can
    #: never be `published` however good it is.
    #:
    #: * `review`   -- a maintainer-facing finding. What the system would say.
    #: * `verified` -- the subset carrying claim-scoped deterministic support and no
    #:                 contradiction. What it proved.
    #:
    #: A finding in `review` but not `verified` is not a worse finding; it is one whose
    #: concern has no warrant yet. Reporting recall against both is what separates reviewer
    #: performance from mechanism coverage.
    channels: List[Literal["review", "verified"]] = Field(default_factory=list)
    #: The arm that produced this, recorded immutably rather than inferred.
    #:
    #: `arm` is a coarse *class* -- `generalist`, `focused_agent`, `merged` -- and several arms
    #: file under one value, so it cannot answer "which arm found this". `sources[].spec_id`
    #: carries it today, which works and is easy to lose in a merge.
    origin_arm_id: Optional[str] = None
    #: Concerns this finding touches, as the arm saw them. Non-gating and possibly several.
    #:
    #: `concern_family` is one value, chosen from a closed list, and routing and verification
    #: key on it. It used to gate submission too -- an arm could declare only concerns in its
    #: own set -- and that rejected correct findings: 11 of the 19 gold obligations labelled
    #: `style` are `grind` simplifications and `encard_` renames, so an arm that found one and
    #: labelled it honestly was refused for guessing the evaluator's vocabulary wrong. Tags let
    #: a claim say what it is without the label deciding whether it may be said at all, which
    #: is what let the gate go.
    concern_tags: List[str] = Field(default_factory=list)
    #: Set when evidence actively contradicted the claim. The finding stays in `review` with
    #: this attached rather than vanishing: a contradiction is a fact about the claim that a
    #: maintainer would want, and deleting it destroys the evidence that the collector ran.
    contradiction: Optional[str] = None
    change_ids: List[str]
    primary_change_id: str
    concern_family: str
    issue_kind: Optional[IssueKind] = None
    primary_subject: Optional[str] = None
    severity: Literal["blocking", "advisory"]
    claim: str
    requested_change: str
    #: Resolution judging compares transformations, so the edit has to survive the merge.
    proposed_edit: Optional[ProposedEdit] = None
    evidence_tier: EvidenceTier
    action_key: str
    sources: List[FindingSource]
    source_sha256: str


#: Every arm a finding can carry, read off the model rather than restated.
#:
#: Reports that enumerate arms must derive them from here. A hand-written list does not fail
#: when an arm is added — it reports nothing for it, so a whole arm's output silently reads
#: as zero, which is indistinguishable from that arm having found nothing.
ARMS = get_args(ReviewFinding.model_fields["arm"].annotation)


#: The arms that actually produce findings; `merged` is what the merge makes of them.
PRODUCING_ARMS = tuple(arm for arm in ARMS if arm != "merged")


#: The file-scoped generalist. Separate from `generalist` rather than a mode of it, because
#: the two are deliberately run as different things and must be counted apart: the per-site
#: generalist is the *control* — same sites and tools as the specialists, covering the concern
#: families no specialist exists for — while this one is a *component* whose distinguishing
#: input is the whole file's changes at once.
FILE_GENERALIST_ARM = "file_generalist"


#: The `spec_id` a file-scoped candidate carries. It is a spec in the plumbing sense — it
#: identifies which scheduled reviewer produced the candidate — but it is not a focused
#: agent, and reading "has a spec_id" as "is focused" would file this arm's output under the
#: arm it is meant to be compared with.
FILE_COHERENCE_SPEC = "file_coherence"


#: The arm a model candidate without a focused spec belongs to. Named once so writers cannot
#: reintroduce the retired spelling by habit.
GENERALIST_ARM = "generalist"


RETIRED_ARM_SPELLINGS = {"holistic": GENERALIST_ARM}


class ReviewIssue(StrictModel):
    """One thing the system says to a maintainer, after site-level results are digested.

    A finding is anchored to one change target; a maintainer's ask often is not. Measured on
    medium, 8 of 43 gold obligations name more than one change target, and one names 19 —
    *"remove the newly introduced axioms ... so the file adds no new axioms"*. The
    deterministic arm emitted 19 separate findings there, one per axiom, so the system was
    structurally mismatched with the unit it is evaluated against: 19 published items scored
    against a single maintainer ask, occupying 19 of that PR's 20 publication slots.

    An issue is the unit that gets published and paired with gold. `change_ids` is the union
    over its member findings, which makes it directly comparable to `obligation.change_ids`.
    """

    schema_version: Literal["review-issue1"] = "review-issue1"
    issue_id: str
    pr_number: int
    episode_id: str
    concern_family: ConcernFamily
    issue_kind: Optional[IssueKind] = None
    #: Union over member findings, comparable to `obligation.change_ids`.
    change_ids: List[str]
    primary_change_id: str
    #: Every subject the members named, so a pattern issue can list what it covers.
    primary_subjects: List[str] = Field(default_factory=list)
    severity: Literal["blocking", "advisory"]
    claim: str
    requested_change: str
    proposed_edit: Optional[ProposedEdit] = None
    evidence_tier: EvidenceTier
    admission: Literal["published", "diagnostic"]
    admission_reason: str
    #: The findings this issue speaks for, and the arms they came from.
    finding_ids: List[str]
    arms: List[str]
    #: `per_site` — one finding, published as itself. `per_pattern` — several findings that
    #: the producing method declares are instances of one violation.
    aggregation: Literal["per_site", "per_pattern"]
    site_count: int = Field(ge=1)
    source_sha256: str


class ConflictRecord(StrictModel):
    """Two findings on the same anchor asking for incompatible transformations.

    Emitted instead of picking a winner when neither side has strictly stronger evidence.
    A merge that silently resolves a genuine disagreement reports more confidence than the
    system has.
    """

    schema_version: Literal["conflict-record1"] = "conflict-record1"
    conflict_id: str
    pr_number: int
    primary_change_id: str
    concern_family: str
    finding_ids: List[str]
    action_keys: List[str]
    evidence_tiers: List[str]
    rationale: str
    source_sha256: str


class CandidateRejection(StrictModel):
    """One candidate that failed validation, kept as a record rather than aborting the batch.

    Ingestion used to `raise` on the first malformed candidate, discarding every other
    candidate in the run and leaving no artifact — so drop rates were unmeasurable. A
    rejected *candidate* is distinct from a failed *response*: the latter means the model
    produced nothing usable and is a coverage failure, the former is one bad item among
    good ones.
    """

    schema_version: Literal["candidate-rejection1"] = "candidate-rejection1"
    work_unit_id: str
    pr_number: int
    ordinal: int
    reason_code: str
    detail: str
    raw_sha256: str
    source_sha256: str
