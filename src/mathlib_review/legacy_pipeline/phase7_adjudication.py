"""Deterministic three-axis adjudication and selective redundancy for Phase 7."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from src.mathlib_review.io import (
    canonical_json_bytes,
    jsonl_bytes,
    load_jsonl,
    pretty_json_bytes,
    sha256_bytes,
    write_once,
)
from src.mathlib_review.analysis.runs import load_candidate_responses
from src.mathlib_review.schema import (
    AdjudicationBundle,
    AdjudicationConsensus,
    AdjudicationVerificationArtifact,
    AdjudicationVote,
    CitedAdjudicationClaim,
    NormAssessment,
    NormRecord,
    NormScope,
    OpportunityEvidenceArtifact,
    OracleOpportunity,
    RedundancyRequest,
    ReviewOpportunity,
    TechnicalAssessment,
    WorthinessDecision,
)


#: /2 adds branches for `naming_norm`, `lint_norm` and `repository_policy` — methods added
#: after /1 was frozen, which reached the `unresolved` fallback and deferred by construction —
#: and teaches the `baseline_failure` branch the generic executor's `exit_code=` vocabulary
#: for a failed compile. Every /1 branch is unchanged; see
#: `tests/datasets/test_pr_review_v4_adjudication_policy.py`, which pins that.
POLICY_VERSION = "phase7-adjudication-policy/2"
DEFAULT_PRODUCTION_RELEASES = (
    Path("inputs/pr_review_v4/releases/dev-pilot-0.9.1-canonical-smoke"),
    Path("inputs/pr_review_v4/releases/dev-pilot-0.9.2-naming-smoke"),
    Path("inputs/pr_review_v4/releases/dev-pilot-0.9.3-wrapper-smoke"),
)
DEFAULT_ORACLE_RELEASE = Path("inputs/pr_review_v4/treatments/oracle-evidence-probe-0.2.0")
DEFAULT_OUT = Path("results/pr_review_v4/audits/phase7-adjudication-gate-0.1.1")


@dataclass(frozen=True)
class EvidenceView:
    evidence_id: str
    kind: str
    content: str
    snapshot_sha: str


@dataclass(frozen=True)
class OpportunityView:
    opportunity_id: str
    method: str
    pr_number: int
    primary_change_id: str
    proposed_alternative: str | None
    evidence: tuple[EvidenceView, ...]
    provenance: str


@dataclass
class AdjudicationArtifacts:
    technical_assessments: list[TechnicalAssessment] = field(default_factory=list)
    norm_records: list[NormRecord] = field(default_factory=list)
    norm_assessments: list[NormAssessment] = field(default_factory=list)
    worthiness_decisions: list[WorthinessDecision] = field(default_factory=list)
    cited_claims: list[CitedAdjudicationClaim] = field(default_factory=list)
    bundles: list[AdjudicationBundle] = field(default_factory=list)
    redundancy_requests: list[RedundancyRequest] = field(default_factory=list)

    def extend(self, other: "AdjudicationArtifacts") -> None:
        for name in self.__dataclass_fields__:
            getattr(self, name).extend(getattr(other, name))


@dataclass(frozen=True)
class _Outcome:
    policy_id: str
    technical_status: str
    compiled: bool | None
    norm_status: str
    norm_kind: str | None
    norm_strength: str | None
    worthiness: str
    request_force: str | None
    technical_evidence: tuple[str, ...]
    norm_evidence: tuple[str, ...]
    worthiness_evidence: tuple[str, ...]
    technical_claim: str
    norm_claim: str
    redundancy_reason: str | None = None
    disputed_axes: tuple[str, ...] = ()


def _digest(payload) -> str:
    return sha256_bytes(canonical_json_bytes(payload))


def _record_id(prefix: str, payload) -> tuple[str, str]:
    digest = _digest(payload)
    return f"{prefix}:{digest[:24]}", digest


def production_cases(release: Path) -> list[OpportunityView]:
    opportunities = load_jsonl(release / "derived/opportunities.jsonl", ReviewOpportunity)
    evidence = load_jsonl(release / "derived/opportunity_evidence.jsonl", OpportunityEvidenceArtifact)
    evidence_by_id = {item.artifact_id: item for item in evidence}
    cases = []
    for opportunity in opportunities:
        missing = set(opportunity.source_artifact_ids) - set(evidence_by_id)
        if missing:
            raise ValueError(
                f"opportunity {opportunity.opportunity_id} has missing evidence: {sorted(missing)}"
            )
        rows = tuple(evidence_by_id[item] for item in opportunity.source_artifact_ids)
        if any(
            item.investigation_id != opportunity.investigation_id
            or item.episode_id != opportunity.episode_id
            or item.pr_number != opportunity.pr_number
            for item in rows
        ):
            raise ValueError(f"opportunity {opportunity.opportunity_id} crosses evidence lineage")
        cases.append(OpportunityView(
            opportunity_id=opportunity.opportunity_id,
            method=opportunity.method_id,
            pr_number=opportunity.pr_number,
            primary_change_id=opportunity.primary_change_id,
            proposed_alternative=(
                opportunity.proposed_transformation.description
                if opportunity.proposed_transformation else None
            ),
            evidence=tuple(EvidenceView(
                item.artifact_id, item.kind, item.content, item.snapshot_sha
            ) for item in rows),
            provenance="production",
        ))
    return cases


def oracle_cases(release: Path) -> list[OpportunityView]:
    rows = load_jsonl(release / "derived/oracle_opportunities.jsonl", OracleOpportunity)
    return [OpportunityView(
        opportunity_id=item.opportunity_id,
        method=item.method,
        pr_number=item.pr_number,
        primary_change_id=item.primary_change_id,
        proposed_alternative=item.proposed_alternative,
        evidence=tuple(EvidenceView(
            evidence.evidence_id, evidence.kind, evidence.content, evidence.snapshot_sha
        ) for evidence in item.evidence),
        provenance=item.selection_provenance,
    ) for item in rows]


def _ids(case: OpportunityView, *, kinds: Iterable[str] = (), patterns: Iterable[str] = ()) -> tuple[str, ...]:
    kinds = set(kinds)
    patterns = tuple(pattern.lower() for pattern in patterns)
    matches = [
        item.evidence_id for item in case.evidence
        if (not kinds or item.kind in kinds)
        and (not patterns or any(pattern in item.content.lower() for pattern in patterns))
    ]
    return tuple(matches)


def _fallback(case: OpportunityView, ids: Sequence[str]) -> tuple[str, ...]:
    return tuple(ids) or (case.evidence[0].evidence_id,)


_EXIT_CODE_RE = re.compile(r"^exit_code=(-?\d+)", re.MULTILINE)


def _nonzero_exit_ids(case: OpportunityView) -> tuple[str, ...]:
    """Evidence reporting a non-zero process exit — the executor's way of saying a build failed.

    Parsed rather than substring-matched: `"exit_code=1" in content` would miss exit code 2
    and match exit code 10.
    """

    matches = []
    for item in case.evidence:
        found = _EXIT_CODE_RE.search(item.content)
        if found and int(found.group(1)) != 0:
            matches.append(item.evidence_id)
    return tuple(matches)


def _classify(case: OpportunityView) -> _Outcome:
    if not case.evidence:
        raise ValueError(f"opportunity {case.opportunity_id} has no evidence")
    method = case.method.removesuffix(".v1")
    all_text = "\n".join(item.content.lower() for item in case.evidence)
    all_ids = tuple(item.evidence_id for item in case.evidence)
    mechanical = _ids(case, kinds={"mechanical_check", "applicability_check"})
    compiled = _ids(case, patterns={"compiled=true"})
    # The three phrases are the frozen phase3/4/5 collectors' wording. The generic executor
    # writes a different vocabulary for the same fact — `exit_code=1\n<compiled-target>:…:
    # error: …` — so without `_nonzero_exit_ids` every file-level build failure it finds
    # falls through to `defer`: 12 of them at medium, which are the most objectively
    # actionable findings in the corpus.
    failed_compile = _ids(
        case, patterns={"compiled=false", "fails to compile", "compile failure"}
    ) + _nonzero_exit_ids(case)
    unavailable = _ids(case, patterns={"lake` is unavailable", "must verify the edit with lean"})
    negative = _ids(case, kinds={"negative_control", "counterexample"})
    conflict = bool(compiled and failed_compile) or ("collision=true" in all_text and "collision=false" in all_text)

    if conflict:
        return _Outcome(
            f"{POLICY_VERSION}:conflict", "uncertain", None, "unknown", None, None,
            "defer", None, _fallback(case, (*compiled, *failed_compile)), _fallback(case, all_ids),
            _fallback(case, all_ids), "The evidence contains conflicting technical results.",
            "The evidence does not support one unambiguous norm application.",
            "conflicting_evidence", ("technical", "norm", "worthiness"),
        )

    if method == "baseline_failure":
        cited = _fallback(case, failed_compile)
        if not failed_compile:
            return _Outcome(
                f"{POLICY_VERSION}:baseline-failure", "uncertain", None, "unknown", None, None,
                "defer", None, cited, cited, cited,
                "No cited artifact establishes the reported direct failure.",
                "The blocking-failure policy cannot be applied without a verified failure.",
                "low_confidence", ("technical",),
            )
        return _Outcome(
            f"{POLICY_VERSION}:baseline-failure", "valid", None, "applicable", "policy",
            "canonical", "request", "blocking", cited, cited, cited,
            "A deterministic check reports a failure in the reviewed state.",
            "Verified failures are governed by the blocking-correctness policy.",
        )

    if method == "canonical_api_search":
        norm = _fallback(case, _ids(case, kinds={"repository_declaration", "retrieval_trace", "quantitative_pattern"}))
        if case.proposed_alternative is None or "more direct matching declaration found=0" in all_text:
            cited = _fallback(case, (*negative, *norm))
            return _Outcome(
                f"{POLICY_VERSION}:canonical-api", "invalid", None, "contradicted", None, None,
                "no_request", None, cited, cited, cited,
                "No missing canonical replacement is identified by the supplied evidence.",
                "The current target is not shown to violate a canonical API expectation.",
            )
        if unavailable or not compiled:
            tech = _fallback(case, (*unavailable, *mechanical))
            return _Outcome(
                f"{POLICY_VERSION}:canonical-api", "uncertain", None, "applicable",
                "canonical_api", "canonical", "defer", None, tech, norm,
                tuple(dict.fromkeys((*tech, *norm))),
                "A source-derived canonical replacement exists but has no successful frozen check.",
                "The repository declaration supports a canonical API expectation.",
                "low_confidence", ("technical", "worthiness"),
            )
        return _Outcome(
            f"{POLICY_VERSION}:canonical-api", "valid", True, "applicable", "canonical_api",
            "canonical", "request", "advisory", compiled, norm,
            tuple(dict.fromkeys((*compiled, *norm))),
            "The proposed canonical replacement has a successful mechanical check.",
            "The replacement uses an exact repository declaration for the reconstructed operation.",
        )

    if method in {"wrapper_composition", "intra_pr_composition"}:
        norm = _fallback(case, _ids(case, kinds={
            "repository_declaration", "composition_plan", "dependency_reduction", "intra_pr_relation"
        }))
        if case.proposed_alternative is None or "no composition plan was produced" in all_text:
            cited = _fallback(case, (*negative, *norm))
            return _Outcome(
                f"{POLICY_VERSION}:wrapper-composition", "invalid", None, "contradicted", None,
                None, "no_request", None, cited, cited, cited,
                "No supported wrapper composition is identified by the supplied evidence.",
                "Parallel structure alone does not establish an abstraction expectation.",
            )
        if unavailable or not compiled:
            tech = _fallback(case, (*unavailable, *mechanical))
            return _Outcome(
                f"{POLICY_VERSION}:wrapper-composition", "uncertain", None, "applicable",
                "local_family", "strong_convention", "defer", None, tech, norm,
                tuple(dict.fromkeys((*tech, *norm))),
                "A source-derived wrapper composition exists but has no successful frozen check.",
                "The cited wrapper chain supports an abstraction-boundary expectation.",
                "low_confidence", ("technical", "worthiness"),
            )
        return _Outcome(
            f"{POLICY_VERSION}:wrapper-composition", "valid", True, "applicable", "local_family",
            "strong_convention", "request", "advisory", compiled, norm,
            tuple(dict.fromkeys((*compiled, *norm))),
            "The proposed wrapper composition has a successful mechanical check.",
            "The cited API chain removes direct reasoning through lower-level implementation details.",
        )

    if method == "naming_contrast":
        norm = _fallback(case, _ids(case, kinds={
            "naming_population", "semantic_subject", "name_collision", "quantitative_pattern",
            "repository_pattern", "counterexample",
        }))
        no_discrepancy = (
            case.proposed_alternative is None
            or "contradicting local examples found=0" in all_text
            or "no conflicting prefix" in all_text
        )
        if no_discrepancy:
            return _Outcome(
                f"{POLICY_VERSION}:strong-naming", "invalid", None, "contradicted", None, None,
                "no_request", None, norm, norm, norm,
                "No collision-free naming discrepancy is identified by the supplied evidence.",
                "The current name is not shown to violate the scoped naming population.",
            )
        collision = _ids(case, patterns={"collision=false"})
        tech = _fallback(case, collision or norm)
        return _Outcome(
            f"{POLICY_VERSION}:strong-naming", "valid", None, "applicable", "naming_pattern",
            "strong_convention", "request", "advisory", tech, norm,
            tuple(dict.fromkeys((*tech, *norm))),
            "The proposed rename is collision-free or otherwise mechanically well-formed.",
            "The scoped naming population strongly favors the proposed semantic-subject form.",
        )

    # --- methods added after the policy was first frozen -------------------------------
    # Without these, `lint_norm`, `naming_norm` and `repository_policy` reach the
    # `unresolved` fallback and defer by construction: 25 of 42 medium opportunities (60%),
    # leaving the deterministic arm with no published finding outside the development PR.
    # Each branch keeps the shape of its nearest frozen sibling; no existing branch moves.

    if method == "naming_norm":
        # Same evidence shape as `naming_contrast`, but the subject is mined from the
        # conclusion rather than fixed, so the population artifact carries the warrant.
        norm = _fallback(case, _ids(case, kinds={
            "naming_population", "semantic_subject", "name_collision",
        }))
        if case.proposed_alternative is None or "is_strong\": false" in all_text:
            return _Outcome(
                f"{POLICY_VERSION}:subject-naming", "invalid", None, "contradicted", None, None,
                "no_request", None, norm, norm, norm,
                "No collision-free rename is identified by the supplied evidence.",
                "The snapshot population does not establish a norm the current name violates.",
            )
        collision = _ids(case, patterns={"collision=false"})
        tech = _fallback(case, collision or norm)
        return _Outcome(
            f"{POLICY_VERSION}:subject-naming", "valid", None, "applicable", "naming_pattern",
            "strong_convention", "request", "advisory", tech, norm,
            tuple(dict.fromkeys((*tech, *norm))),
            "The proposed rename is collision-free against the snapshot and the current PR.",
            "The measured subject population strongly favors the proposed prefix.",
        )

    if method == "lint_norm":
        # Mathlib publishes these rules and enforces them in CI, so a violation is a policy
        # fact rather than a judgement call — but the linters are style rules, so the request
        # is advisory rather than blocking.
        report = _fallback(case, _ids(case, kinds={"lint_report"}))
        if not _ids(case, kinds={"lint_report"}):
            return _Outcome(
                f"{POLICY_VERSION}:lint-norm", "uncertain", None, "unknown", None, None,
                "defer", None, report, report, report,
                "No cited artifact reports a style-lint violation.",
                "The lint policy cannot be applied without a violation report.",
                "low_confidence", ("technical",),
            )
        return _Outcome(
            f"{POLICY_VERSION}:lint-norm", "valid", None, "applicable", "policy",
            "canonical", "request", "advisory", report, report, report,
            "A published Mathlib text-style lint reports a violation on reviewed lines.",
            "Style lints are explicit repository policy, not a scoped preference.",
        )

    if method == "repository_policy":
        # An introduced `axiom` or `sorry` adds an unproved assumption to the library. That
        # is the one norm in the registry with no legitimate counterexample, so unlike the
        # style lints it is blocking.
        report = _fallback(case, _ids(case, kinds={"policy_report"}))
        if not _ids(case, kinds={"policy_report"}):
            return _Outcome(
                f"{POLICY_VERSION}:repository-policy", "uncertain", None, "unknown", None, None,
                "defer", None, report, report, report,
                "No cited artifact reports an introduced forbidden construct.",
                "The repository policy cannot be applied without a construct report.",
                "low_confidence", ("technical",),
            )
        return _Outcome(
            f"{POLICY_VERSION}:repository-policy", "valid", None, "applicable", "policy",
            "canonical", "request", "blocking", report, report, report,
            "The reviewed state introduces a construct the repository forbids.",
            "Adding an unproved assumption is governed by explicit repository policy.",
        )

    if method == "proof_compression":
        tech = _fallback(case, compiled or mechanical)
        if "semantic steps removed=0" in all_text:
            return _Outcome(
                f"{POLICY_VERSION}:proof-compression", "valid", True, "unknown", None, None,
                "no_request", None, tech, tech, tech,
                "The alternative compiles but removes no semantic step.",
                "No repository expectation favors the syntax-only alternative.",
            )
        return _Outcome(
            f"{POLICY_VERSION}:proof-compression", "valid" if compiled else "uncertain",
            True if compiled else None, "unknown", None, None, "advisory_option", None,
            tech, tech, tech,
            "The alternative is mechanically supported as a proof simplification.",
            "No historical selection evidence establishes the simplification as a review norm.",
        )

    if method == "repository_pattern":
        tech = _fallback(case, compiled or mechanical)
        norm = _fallback(case, _ids(case, kinds={"quantitative_pattern", "repository_pattern"}))
        return _Outcome(
            f"{POLICY_VERSION}:repository-pattern", "valid" if compiled else "uncertain",
            True if compiled else None, "weak_prior", "adopted_transformation", "weak_prior",
            "advisory_option", None, tech, norm, tuple(dict.fromkeys((*tech, *norm))),
            "The proposed local rewrite has a successful mechanical check.",
            "Repository prevalence supports only a weak prior because both forms occur.",
        )

    if method == "family_consistency" and (
        "inconsistent facets=0" in all_text or case.proposed_alternative is None
    ):
        cited = _fallback(case, _ids(case, kinds={"quantitative_pattern", "reviewed_code"}))
        return _Outcome(
            f"{POLICY_VERSION}:family-consistency", "invalid", None, "contradicted", None, None,
            "no_request", None, cited, cited, cited,
            "The family comparison identifies no inconsistent facet or shared replacement.",
            "The supplied family evidence does not establish a consistency request.",
        )

    cited = _fallback(case, all_ids)
    return _Outcome(
        f"{POLICY_VERSION}:unresolved", "uncertain", None, "unknown", None, None, "defer",
        None, cited, cited, cited, "The deterministic policy cannot establish technical validity.",
        "The deterministic policy cannot establish norm applicability.",
        "low_confidence", ("technical", "norm", "worthiness"),
    )


def _claim(case: OpportunityView, text: str, evidence_ids: Sequence[str]) -> CitedAdjudicationClaim:
    payload = {
        "opportunity_id": case.opportunity_id,
        "text": text,
        "evidence_artifact_ids": list(dict.fromkeys(evidence_ids)),
    }
    claim_id, digest = _record_id("adjudication-claim", payload)
    return CitedAdjudicationClaim(claim_id=claim_id, source_sha256=digest, **payload)


def _norm_record(case: OpportunityView, outcome: _Outcome) -> NormRecord | None:
    if outcome.norm_kind is None or outcome.norm_strength is None:
        return None
    snapshots = sorted({item.snapshot_sha for item in case.evidence if item.evidence_id in outcome.norm_evidence})
    snapshot = snapshots[0] if snapshots else case.evidence[0].snapshot_sha
    payload = {
        "norm_kind": outcome.norm_kind,
        "trigger_predicate": f"policy={outcome.policy_id}; method={case.method}",
        "recommended_action": case.proposed_alternative or "Apply the verified policy action.",
        "scope": NormScope(snapshot_sha=snapshot).model_dump(mode="json"),
        "effective_before": f"snapshot:{snapshot}",
        "source_artifact_ids": list(outcome.norm_evidence),
        "strength": outcome.norm_strength,
    }
    norm_id, digest = _record_id("norm", payload)
    return NormRecord(norm_id=norm_id, source_sha256=digest, **payload)


def adjudicate(case: OpportunityView) -> AdjudicationArtifacts:
    outcome = _classify(case)
    norm = _norm_record(case, outcome)
    claims = [
        _claim(case, outcome.technical_claim, outcome.technical_evidence),
        _claim(case, outcome.norm_claim, outcome.norm_evidence),
    ]
    norm_ids = [norm.norm_id] if norm else []

    technical_payload = {
        "opportunity_id": case.opportunity_id,
        "status": outcome.technical_status,
        "evidence_artifact_ids": list(outcome.technical_evidence),
        "proposed_edit_compiled": outcome.compiled,
        "rationale": "The frozen policy result follows from the cited technical premise.",
        "producer": "policy",
    }
    technical_id, technical_digest = _record_id("technical-assessment", technical_payload)
    technical = TechnicalAssessment(
        assessment_id=technical_id, source_sha256=technical_digest, **technical_payload
    )

    norm_payload = {
        "opportunity_id": case.opportunity_id,
        "status": outcome.norm_status,
        "norm_ids": norm_ids,
        "evidence_artifact_ids": list(outcome.norm_evidence),
        "rationale": "The frozen policy result follows from the cited norm premise.",
        "producer": "policy",
    }
    norm_assessment_id, norm_assessment_digest = _record_id("norm-assessment", norm_payload)
    norm_assessment = NormAssessment(
        assessment_id=norm_assessment_id,
        source_sha256=norm_assessment_digest,
        **norm_payload,
    )

    decision_payload = {
        "opportunity_id": case.opportunity_id,
        "technical_assessment_id": technical.assessment_id,
        "norm_assessment_id": norm_assessment.assessment_id,
        "norm_ids": norm_ids,
        "review_worthiness": outcome.worthiness,
        "request_force": outcome.request_force,
        "evidence_artifact_ids": list(outcome.worthiness_evidence),
        "rationale": "The frozen policy maps the separate technical and norm results to this disposition.",
        "producer": "policy",
    }
    decision_id, decision_digest = _record_id("worthiness-decision", decision_payload)
    decision = WorthinessDecision(
        decision_id=decision_id, source_sha256=decision_digest, **decision_payload
    )

    redundancy = None
    if outcome.redundancy_reason:
        redundancy_payload = {
            "opportunity_id": case.opportunity_id,
            "reason": outcome.redundancy_reason,
            "disputed_axes": list(outcome.disputed_axes),
            # A follow-up judge needs the complete immutable opportunity packet, not only
            # the subset cited by the initial policy conclusion.
            "evidence_artifact_ids": [item.evidence_id for item in case.evidence],
            "required_votes": 2,
        }
        request_id, request_digest = _record_id("redundancy-request", redundancy_payload)
        redundancy = RedundancyRequest(
            request_id=request_id, source_sha256=request_digest, **redundancy_payload
        )

    bundle_payload = {
        "opportunity_id": case.opportunity_id,
        "policy_id": outcome.policy_id,
        "technical_assessment_id": technical.assessment_id,
        "norm_assessment_id": norm_assessment.assessment_id,
        "worthiness_decision_id": decision.decision_id,
        "cited_claim_ids": [item.claim_id for item in claims],
        "route": "redundant_adjudication" if redundancy else "deterministic",
        "redundancy_request_id": redundancy.request_id if redundancy else None,
    }
    bundle_id, bundle_digest = _record_id("adjudication-bundle", bundle_payload)
    bundle = AdjudicationBundle(bundle_id=bundle_id, source_sha256=bundle_digest, **bundle_payload)

    result = AdjudicationArtifacts(
        technical_assessments=[technical],
        norm_records=[norm] if norm else [],
        norm_assessments=[norm_assessment],
        worthiness_decisions=[decision],
        cited_claims=claims,
        bundles=[bundle],
        redundancy_requests=[redundancy] if redundancy else [],
    )
    validate_bundle(case, result)
    return result


def validate_bundle(case: OpportunityView, artifacts: AdjudicationArtifacts) -> None:
    """Reject uncited, foreign, or disconnected adjudication evidence."""
    if not (
        len(artifacts.technical_assessments)
        == len(artifacts.norm_assessments)
        == len(artifacts.worthiness_decisions)
        == len(artifacts.bundles)
        == 1
    ):
        raise ValueError("one opportunity must produce exactly one linked three-axis bundle")
    available = {item.evidence_id for item in case.evidence}
    claims = {item.claim_id: item for item in artifacts.cited_claims}
    bundle = artifacts.bundles[0]
    if set(bundle.cited_claim_ids) != set(claims):
        raise ValueError("bundle must reference every factual adjudication claim")
    cited_evidence = set()
    for claim in claims.values():
        if claim.opportunity_id != case.opportunity_id:
            raise ValueError("cited claim references a different opportunity")
        if not set(claim.evidence_artifact_ids) <= available:
            raise ValueError("cited claim references evidence outside the opportunity")
        cited_evidence.update(claim.evidence_artifact_ids)
    referenced = set()
    for item in (
        artifacts.technical_assessments[0],
        artifacts.norm_assessments[0],
        artifacts.worthiness_decisions[0],
        *artifacts.norm_records,
    ):
        evidence_ids = getattr(item, "evidence_artifact_ids", None)
        if evidence_ids is None:
            evidence_ids = getattr(item, "source_artifact_ids", [])
        if not set(evidence_ids) <= available:
            raise ValueError("adjudication record references evidence outside the opportunity")
        referenced.update(evidence_ids)
    if not referenced <= cited_evidence:
        raise ValueError("every factual adjudication premise must have a structured citation")
    if any(
        not set(item.evidence_artifact_ids) <= available
        for item in artifacts.redundancy_requests
    ):
        raise ValueError("redundancy request references evidence outside the opportunity")


def resolve_redundancy(
    request: RedundancyRequest,
    votes: Sequence[AdjudicationVote],
    verification_artifacts: Sequence[AdjudicationVerificationArtifact] = (),
) -> AdjudicationConsensus:
    if len(votes) != request.required_votes:
        raise ValueError(f"redundancy request requires exactly {request.required_votes} votes")
    if len({item.assessor_id for item in votes}) != len(votes):
        raise ValueError("redundant adjudication requires distinct assessors")
    if any(item.request_id != request.request_id or item.opportunity_id != request.opportunity_id for item in votes):
        raise ValueError("vote does not belong to the redundancy request")
    verification_by_id = {item.artifact_id: item for item in verification_artifacts}
    if any(
        item.opportunity_id != request.opportunity_id
        or not set(item.source_evidence_artifact_ids) <= set(request.evidence_artifact_ids)
        for item in verification_artifacts
    ):
        raise ValueError("verification artifact does not belong to the redundancy request")
    allowed_evidence = set(request.evidence_artifact_ids) | set(verification_by_id)
    if any(not set(item.evidence_artifact_ids) <= allowed_evidence for item in votes):
        raise ValueError("vote cites evidence outside the redundancy request")
    signatures = {
        (item.technical_status, item.norm_status, item.review_worthiness) for item in votes
    }
    agreement = len(signatures) == 1
    payload = {
        "request_id": request.request_id,
        "opportunity_id": request.opportunity_id,
        "vote_ids": [item.vote_id for item in votes],
        "status": "agreement" if agreement else "disagreement",
        "final_worthiness": votes[0].review_worthiness if agreement else "defer",
    }
    consensus_id, digest = _record_id("adjudication-consensus", payload)
    return AdjudicationConsensus(
        consensus_id=consensus_id, source_sha256=digest, **payload
    )


def _verification_artifact_from_raw(raw: dict) -> tuple[AdjudicationVerificationArtifact, bool]:
    """Repair the brief Phase 7 alias bug only when the original digest proves the fix."""
    artifact_id = raw.get("artifact_id")
    source_ids = list(raw.get("source_evidence_artifact_ids") or [])
    if artifact_id not in source_ids:
        return AdjudicationVerificationArtifact.model_validate(raw), False
    corrected = dict(raw)
    corrected["source_evidence_artifact_ids"] = [
        item for item in source_ids if item != artifact_id
    ]
    identity = {
        key: corrected[key]
        for key in (
            "opportunity_id",
            "kind",
            "success",
            "source_evidence_artifact_ids",
            "edit_sha256",
            "content",
            "snapshot_sha",
        )
    }
    digest = _digest(identity)
    if corrected.get("source_sha256") != digest or artifact_id != f"adjudication-verification:{digest[:24]}":
        raise ValueError("self-referential verification artifact cannot be hash-verified")
    return AdjudicationVerificationArtifact.model_validate(corrected), True


def _vote_from_response(
    request: RedundancyRequest,
    response_path: Path,
    row: dict,
) -> tuple[AdjudicationVote, list[AdjudicationVerificationArtifact], int]:
    response = row.get("response") or {}
    decisions = [
        item for item in response.get("adjudications") or []
        if item.get("opportunity_id") == request.opportunity_id
    ]
    if len(decisions) != 1:
        raise ValueError(
            f"{response_path} must contain exactly one adjudication for {request.opportunity_id}"
        )
    raw = decisions[0]
    parsed_artifacts = [
        _verification_artifact_from_raw(item)
        for item in response.get("verification_artifacts") or []
        if item.get("opportunity_id") == request.opportunity_id
    ]
    artifacts = [item for item, _migrated in parsed_artifacts]
    repaired_aliases = sum(migrated for _item, migrated in parsed_artifacts)
    evidence_ids = list(dict.fromkeys(raw.get("evidence_ids") or []))
    if raw.get("validity") == "valid" and raw.get("disposition") == "request" and not artifacts:
        raise ValueError(
            f"{response_path} requests a technically valid edit without a persisted verification artifact"
        )
    norm_status = {
        "required": "applicable",
        "canonical": "applicable",
        "conventional": "applicable",
        "common": "applicable",
        "preference": "weak_prior",
        "unsupported": "contradicted",
        "uncertain": "unknown",
    }[raw["norm_strength"]]
    worthiness = {
        "request": "request",
        "no_request": "no_request",
        "inconclusive": "defer",
    }[raw["disposition"]]
    payload = {
        "request_id": request.request_id,
        "opportunity_id": request.opportunity_id,
        "assessor_id": response_path.parent.name,
        "technical_status": raw["validity"],
        "norm_status": norm_status,
        "review_worthiness": worthiness,
        "evidence_artifact_ids": evidence_ids,
        "producer": "model",
    }
    vote_id, digest = _record_id("adjudication-vote", payload)
    return (
        AdjudicationVote(vote_id=vote_id, source_sha256=digest, **payload),
        artifacts,
        repaired_aliases,
    )


def ingest_redundancy_runs(
    gate_dir: Path,
    response_paths: Sequence[Path],
    out: Path,
) -> dict:
    requests = load_jsonl(gate_dir / "redundancy_requests.jsonl", RedundancyRequest)
    request_by_opportunity = {item.opportunity_id: item for item in requests}
    votes_by_request: dict[str, list[AdjudicationVote]] = {}
    artifacts_by_request: dict[str, list[AdjudicationVerificationArtifact]] = {}
    repaired_aliases = 0
    for response_path in response_paths:
        rows = load_candidate_responses(response_path)
        matched = []
        for row in rows:
            if not row.get("success"):
                continue
            opportunity_ids = {
                item.get("opportunity_id")
                for item in (row.get("response") or {}).get("adjudications") or []
            }
            for opportunity_id in opportunity_ids & set(request_by_opportunity):
                matched.append((request_by_opportunity[opportunity_id], row))
        if len(matched) != 1:
            raise ValueError(
                f"{response_path} must contain exactly one selected redundancy adjudication; "
                f"found {len(matched)}"
            )
        request, row = matched[0]
        vote, verification, repaired = _vote_from_response(request, response_path, row)
        repaired_aliases += repaired
        votes_by_request.setdefault(request.request_id, []).append(vote)
        artifacts_by_request.setdefault(request.request_id, []).extend(verification)

    selected = [item for item in requests if item.request_id in votes_by_request]
    consensuses = []
    for request in selected:
        consensuses.append(resolve_redundancy(
            request,
            votes_by_request[request.request_id],
            artifacts_by_request.get(request.request_id, []),
        ))
    votes = [item for request in selected for item in votes_by_request[request.request_id]]
    verification = [
        item for request in selected for item in artifacts_by_request.get(request.request_id, [])
    ]
    report = {
        "schema_version": "phase7-redundancy-ingest-report1",
        "complete": len(consensuses) == len(selected) and bool(selected),
        "counts": {
            "requests": len(selected),
            "votes": len(votes),
            "verification_artifacts": len(verification),
            "repaired_legacy_aliases": repaired_aliases,
            "consensuses": len(consensuses),
        },
        "outcomes": {
            item.opportunity_id: {
                "status": item.status,
                "final_worthiness": item.final_worthiness,
            }
            for item in consensuses
        },
    }
    write_once(out / "adjudication_votes.jsonl", jsonl_bytes(votes))
    write_once(out / "verification_artifacts.jsonl", jsonl_bytes(verification))
    write_once(out / "adjudication_consensuses.jsonl", jsonl_bytes(consensuses))
    write_once(out / "report.json", pretty_json_bytes(report))
    return report


def build_gate_artifacts(
    production_releases: Sequence[Path] = DEFAULT_PRODUCTION_RELEASES,
    oracle_release: Path = DEFAULT_ORACLE_RELEASE,
) -> tuple[AdjudicationArtifacts, dict]:
    cases = [case for release in production_releases for case in production_cases(release)]
    cases.extend(oracle_cases(oracle_release))
    artifacts = AdjudicationArtifacts()
    for case in cases:
        artifacts.extend(adjudicate(case))
    decisions = {
        item.opportunity_id: item for item in artifacts.worthiness_decisions
    }
    oracle = [case for case in cases if case.provenance != "production"]
    controls = [case for case in oracle if case.provenance == "matched_control"]
    targeted = [case for case in oracle if case.provenance == "oracle_gold_targeted"]
    oracle_requests = [case for case in oracle if decisions[case.opportunity_id].review_worthiness == "request"]
    minor_proofs = [case for case in oracle if case.method == "proof_compression"]
    production = [case for case in cases if case.provenance == "production"]
    production_requests = [
        case for case in production if decisions[case.opportunity_id].review_worthiness == "request"
    ]
    report = {
        "schema_version": "phase7-adjudication-gate-report1",
        "policy_version": POLICY_VERSION,
        "counts": {
            "opportunities": len(cases),
            "production_opportunities": len(production),
            "oracle_opportunities": len(oracle),
            "oracle_controls": len(controls),
            "oracle_targeted": len(targeted),
            "requests": sum(
                item.review_worthiness == "request"
                for item in artifacts.worthiness_decisions
            ),
            "redundancy_requests": len(artifacts.redundancy_requests),
        },
        "gates": {
            "oracle_controls_no_request": all(
                decisions[item.opportunity_id].review_worthiness == "no_request"
                for item in controls
            ),
            "minor_proofs_not_published": all(
                decisions[item.opportunity_id].review_worthiness != "request"
                for item in minor_proofs
            ),
            "oracle_request_precision": (
                sum(item.provenance == "oracle_gold_targeted" for item in oracle_requests)
                / len(oracle_requests) if oracle_requests else None
            ),
            "production_request_precision": (
                sum(item.proposed_alternative is not None for item in production_requests)
                / len(production_requests) if production_requests else None
            ),
            "all_records_citation_validated": True,
        },
        "oracle_requests": [item.opportunity_id for item in oracle_requests],
        "production_requests": [item.opportunity_id for item in production_requests],
        "deferred_opportunities": [
            item.opportunity_id for item in cases
            if decisions[item.opportunity_id].review_worthiness == "defer"
        ],
    }
    report["gates"]["candidate_issue_precision_no_decline"] = (
        report["gates"]["oracle_request_precision"] == 1.0
        and report["gates"]["production_request_precision"] == 1.0
    )
    return artifacts, report


def _artifact_bytes(artifacts: AdjudicationArtifacts) -> dict[str, bytes]:
    return {
        "technical_assessments.jsonl": jsonl_bytes(artifacts.technical_assessments),
        "norm_records.jsonl": jsonl_bytes(artifacts.norm_records),
        "norm_assessments.jsonl": jsonl_bytes(artifacts.norm_assessments),
        "worthiness_decisions.jsonl": jsonl_bytes(artifacts.worthiness_decisions),
        "cited_claims.jsonl": jsonl_bytes(artifacts.cited_claims),
        "adjudication_bundles.jsonl": jsonl_bytes(artifacts.bundles),
        "redundancy_requests.jsonl": jsonl_bytes(artifacts.redundancy_requests),
    }


def write_gate(out: Path = DEFAULT_OUT) -> dict:
    first, report = build_gate_artifacts()
    second, second_report = build_gate_artifacts()
    first_bytes = _artifact_bytes(first)
    report["gates"]["byte_stable_replay"] = (
        first_bytes == _artifact_bytes(second) and report == second_report
    )
    report["complete"] = all(
        value is True or (key.endswith("precision") and value == 1.0)
        for key, value in report["gates"].items()
    )
    for name, content in first_bytes.items():
        write_once(out / name, content)
    write_once(out / "report.json", pretty_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--gate-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--responses", type=Path, nargs="+")
    args = parser.parse_args()
    report = (
        ingest_redundancy_runs(args.gate_dir, args.responses, args.out)
        if args.responses else write_gate(args.out)
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
