"""Combine both review arms into one final finding set — the system's actual output.

The two arms previously ended in incompatible record types with no shared consumer, and
`synthesis.link_candidates` raised unless a candidate mapped to exactly one opportunity, so
a holistic finding (which has no opportunity) could not pass through it at all. This is the
arm-neutral replacement. `synthesis.py` is left untouched: it carries the frozen Phase 9
lineage, and bending holistic findings into its opportunity-shaped records would mean
fabricating opportunity IDs.

Two things this module deliberately does not do:

* **It does not rank by model confidence.** Self-confidence has been falsified as a ranking
  signal three times (precision flat 9% -> 12%), alongside five failed selector designs.
* **It does not resolve genuine disagreements.** Two findings asking for incompatible
  transformations on the same anchor, with no evidence-strength difference between them,
  produce a `ConflictRecord` — reporting a winner would claim confidence the system has not
  earned.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from src.mathlib_review.io import sealed_model
from src.mathlib_review.schema import (
    ARMS,
    FILE_COHERENCE_SPEC,
    FILE_GENERALIST_ARM,
    GENERALIST_ARM,
    CandidateClaim,
    ConflictRecord,
    EVIDENCE_TIERS,
    FindingSource,
    ReviewFinding,
    ReviewOpportunity,
    WorthinessDecision,
    evidence_rank,
)


MERGE_VERSION = "arm-neutral-merge/1"

#: Applied per PR, after every other step. The previous limit was checked against a flat
#: list spanning all PRs while its own message said "PR finding budget" — harmless at two
#: PRs, silently truncating at sixteen, and cutting in sha256 order.
DEFAULT_PR_FINDING_LIMIT = 20

_WHITESPACE = re.compile(r"\s+")


def canonical_action(concern_family: str, requested_change: str) -> str:
    """A normalized key for "asks for the same thing".

    Deliberately conservative: case and whitespace only. Anything cleverer — stemming,
    synonyms, embeddings — would merge findings we cannot prove equivalent, and a merge is
    lossy: only the representative's wording survives to be judged.
    """

    return f"{concern_family}:{_WHITESPACE.sub(' ', requested_change.strip().lower())}"


def _seal(model, prefix: str, payload: Dict):
    """Seal a record, deriving its ID from its own content hash.

    Built on `io.sealed_model` so nested models (sources, proposed edits) serialize through
    pydantic rather than being handed raw to the JSON encoder. The ID is derived here rather
    than supplied, so two identical findings from different runs collide by construction.
    """

    draft = sealed_model(model, **{f"{prefix}_id": "", **payload})
    return draft.model_copy(
        update={f"{prefix}_id": f"{prefix}:{draft.source_sha256[:24]}"}
    )


def finding_from_candidate(
    candidate: CandidateClaim,
    *,
    admission: str,
    admission_reason: str,
    evidence_tier: str = "model_assertion",
    evidence_artifact_ids: Sequence[str] = (),
    arm: Optional[str] = None,
) -> ReviewFinding:
    """Project a model candidate into the common shape, under the arm that produced it.

    The arm is read from `spec_id`, not passed in: a candidate carrying a spec came from a
    scheduled focused invocation, and that is the only thing that distinguishes it from a
    holistic one — `producer` is `model` for both. Hard-coding `holistic` here filed every
    focused finding under the arm it is supposed to be measured against.

    `arm` overrides that derivation, for the one case it does not cover: a per-site
    specialist whose concern is *not settled by compiling*. `focused_agent` carries a hard
    invariant — a focused source must name a verification artifact, because the arm's whole
    warrant is "the compiler accepted this replacement". A naming or docstring specialist
    cannot produce one (renaming breaks call sites; a typo fix proves nothing by elaborating),
    so deriving `focused_agent` for it makes the finding unconstructible. Such an arm is a
    `generalist` in this vocabulary — same sites, evidence-warranted, narrower checklist — and
    `source.spec_id` still records which specialist produced it, so attribution is not lost.
    """

    if arm is None:
        if candidate.spec_id == FILE_COHERENCE_SPEC:
            arm = FILE_GENERALIST_ARM
        elif candidate.spec_id:
            arm = "focused_agent"
        else:
            arm = GENERALIST_ARM
    source = FindingSource(
        arm=arm,
        candidate_id=candidate.candidate_id,
        spec_id=candidate.spec_id,
        evidence_artifact_ids=list(evidence_artifact_ids),
    )
    payload = {
        "pr_number": candidate.pr_number,
        "episode_id": candidate.episode_id,
        "arm": arm,
        "admission": admission,
        "admission_reason": admission_reason,
        "change_ids": sorted(candidate.change_ids),
        "primary_change_id": candidate.primary_change_id or sorted(candidate.change_ids)[0],
        "concern_family": candidate.concern_family,
        "issue_kind": candidate.issue_kind,
        "primary_subject": candidate.primary_subject,
        "severity": candidate.severity,
        "claim": candidate.claim,
        "requested_change": candidate.requested_change or candidate.suggested_fix or "",
        "proposed_edit": candidate.proposed_edit,
        "evidence_tier": evidence_tier,
        "action_key": canonical_action(
            candidate.concern_family,
            candidate.requested_change or candidate.suggested_fix or "",
        ),
        # Provenance, recorded rather than inferred. `arm` is a coarse class that several arms
        # share, so it cannot say which arm found this; `spec_id` can, and is easy to lose in
        # a merge.
        "origin_arm_id": candidate.spec_id,
        # What the claim is about, as the arm saw it. Non-gating, unlike `concern_family`.
        # The candidate's own tags carry anything the arm layer observed and declined to
        # refuse — `off-concern:<arm_id>` above all, which is what the concern gate used to
        # reject a submission over.
        "concern_tags": sorted(
            set(candidate.concern_tags or [])
            | ({candidate.concern_family} if candidate.concern_family else set())
        ),
        "sources": [source],
    }
    return _seal(ReviewFinding, "finding", payload)


def finding_from_opportunity(
    opportunity: ReviewOpportunity,
    decision: WorthinessDecision,
    *,
    concern_family: str,
    evidence_tier: str,
    issue_kind: Optional[str] = None,
) -> ReviewFinding:
    """Project a deterministic opportunity and its adjudication into the common shape.

    Only `request` is published. Everything else — `no_request`, `advisory_option`, and
    `defer` — is retained as `diagnostic`, so the arm's reach stays measurable without
    claiming it would have said anything to a maintainer.
    """

    published = decision.review_worthiness == "request"
    transformation = opportunity.proposed_transformation
    requested = transformation.description if transformation else opportunity.observed_pattern
    payload = {
        "pr_number": opportunity.pr_number,
        "episode_id": opportunity.episode_id,
        "arm": "deterministic",
        "admission": "published" if published else "diagnostic",
        "admission_reason": f"adjudicated {decision.review_worthiness}",
        "change_ids": sorted({opportunity.primary_change_id, *opportunity.related_change_ids}),
        "primary_change_id": opportunity.primary_change_id,
        "concern_family": concern_family,
        "issue_kind": issue_kind,
        "primary_subject": (transformation.symbols[0] if transformation and transformation.symbols
                            else None),
        "severity": "blocking" if decision.request_force == "blocking" else "advisory",
        "claim": opportunity.observed_pattern,
        "requested_change": requested,
        "proposed_edit": None,
        "evidence_tier": evidence_tier,
        "action_key": canonical_action(concern_family, requested),
        "sources": [FindingSource(
            arm="deterministic",
            opportunity_id=opportunity.opportunity_id,
            method_id=opportunity.method_id,
            evidence_artifact_ids=list(opportunity.source_artifact_ids),
        )],
    }
    return _seal(ReviewFinding, "finding", payload)


def _merge_group(findings: Sequence[ReviewFinding]) -> ReviewFinding:
    """Fold findings that ask for the same thing at the same place into one.

    The representative is the strongest-evidence member, so a verified deterministic finding
    supplies the surviving wording when a model assertion agrees with it — the merged text
    is the one with the best warrant behind it, not the first by hash.
    """

    if len(findings) == 1:
        return findings[0]
    best = max(findings, key=lambda item: (evidence_rank(item.evidence_tier), item.finding_id))
    payload = best.model_dump(mode="json", exclude={"finding_id", "source_sha256", "sources",
                                                    "arm", "schema_version"})
    payload["arm"] = "merged" if len({item.arm for item in findings}) > 1 else best.arm
    payload["severity"] = (
        "blocking" if any(item.severity == "blocking" for item in findings) else "advisory"
    )
    payload["sources"] = [
        source.model_dump(mode="json")
        for item in sorted(findings, key=lambda row: row.finding_id)
        for source in item.sources
    ]
    # Provenance combines rather than inheriting the representative's. Two arms finding the
    # same thing is a fact about the finding, and keeping only the winner's would report one
    # arm's work as the whole of it.
    origins = {item.origin_arm_id for item in findings if item.origin_arm_id}
    payload["origin_arm_id"] = origins.pop() if len(origins) == 1 else None
    payload["concern_tags"] = sorted({
        tag for item in findings for tag in (item.concern_tags or [])
    })
    return _seal(ReviewFinding, "finding", payload)


def _is_verified_proposal(finding: ReviewFinding) -> bool:
    """A finding that carries an edit the compiler accepted.

    This is what separates an *alternative* from a *contradiction*. A verified edit proves
    its own achievability, so two of them at one target are competing implementations. Two
    unverified prose claims that disagree are genuinely undecidable, and stay a conflict.
    """

    return finding.evidence_tier == "verified_compile" and finding.proposed_edit is not None


def _edit_size(finding: ReviewFinding) -> int:
    edit = finding.proposed_edit
    if edit is None:
        return 0
    return len((edit.new_declaration or edit.replacement or "").strip())


def _select_alternative(group: Sequence[ReviewFinding]) -> ReviewFinding:
    """Pick one verified edit from several at the same target.

    Smallest edit first: the more conservative ask, and for a proof rewrite it is the
    criterion the golf checker states for itself. Ties break on the stable finding ID, never
    on `model_confidence` — falsified three times as a ranking signal.
    """

    return min(group, key=lambda item: (_edit_size(item), item.finding_id))


def merge_findings(
    findings: Iterable[ReviewFinding],
    *,
    pr_finding_limit: Optional[int] = DEFAULT_PR_FINDING_LIMIT,
) -> Tuple[List[ReviewFinding], List[ConflictRecord], Dict]:
    """Merge, detect conflicts, then apply the per-PR publication limit.

    Returns `(findings, conflicts, report)`. The report carries pre- and post-limit counts,
    because a truncated finding set that reports only its post-limit size hides the fact
    that it was truncated at all.
    """

    findings = list(findings)
    grouped: Dict[Tuple, List[ReviewFinding]] = defaultdict(list)
    for finding in findings:
        # Merge only on identical anchors, family and canonical action. Nothing weaker:
        # an uncertain paraphrase stays a separate finding, because recall is not improved
        # by collapsing things we cannot prove equivalent.
        grouped[(finding.pr_number, tuple(finding.change_ids), finding.concern_family,
                 finding.action_key)].append(finding)

    merged = [_merge_group(group) for _key, group in sorted(grouped.items())]

    conflicts: List[ConflictRecord] = []
    by_anchor: Dict[Tuple, List[ReviewFinding]] = defaultdict(list)
    for finding in merged:
        by_anchor[(finding.pr_number, finding.primary_change_id, finding.concern_family)].append(
            finding
        )
    # finding_id -> why it was demoted. Three causes that used to share one message:
    # a stronger warrant elsewhere, an unresolved conflict, and an unselected alternative.
    suppressed: Dict[str, str] = {}
    alternatives = 0
    for (pr_number, change_id, family), group in sorted(by_anchor.items()):
        if len(group) < 2:
            continue
        ranks = {evidence_rank(item.evidence_tier) for item in group}
        if len(ranks) > 1:
            # A strictly stronger warrant resolves it; the weaker sides become diagnostic
            # rather than vanishing.
            best = max(ranks)
            for item in group:
                if evidence_rank(item.evidence_tier) < best:
                    suppressed[item.finding_id] = (
                        "a better-warranted finding covers this target"
                    )
            continue
        if all(_is_verified_proposal(item) for item in group):
            # Alternatives, not contradictions. Two verified edits at one target are two
            # ways of doing the achievable thing — each compiles, so each proves itself.
            # Treating them as a contradiction and demoting both makes the system publish
            # *less* the more of its checkers succeed, which is backwards.
            winner = _select_alternative(group)
            alternatives += len(group) - 1
            for item in group:
                if item.finding_id != winner.finding_id:
                    suppressed[item.finding_id] = (
                        f"an alternative verified edit was selected ({winner.finding_id})"
                    )
            continue
        conflicts.append(_seal(ConflictRecord, "conflict", {
            "pr_number": pr_number,
            "primary_change_id": change_id,
            "concern_family": family,
            "finding_ids": sorted(item.finding_id for item in group),
            "action_keys": sorted(item.action_key for item in group),
            "evidence_tiers": sorted({item.evidence_tier for item in group}),
            "rationale": (
                "Findings on the same target ask for different transformations with equal "
                "evidence strength and no verified edit to choose between them; no side is "
                "preferred."
            ),
        }))
        for item in group:
            suppressed[item.finding_id] = "in an unresolved conflict at this anchor"

    resolved = [
        item if item.finding_id not in suppressed
        else item.model_copy(update={
            "admission": "diagnostic",
            "admission_reason": suppressed[item.finding_id],
        })
        for item in merged
    ]

    # Publication limit: per PR, applied last, ordered by warrant — never by confidence.
    published_before = sum(item.admission == "published" for item in resolved)
    kept: List[ReviewFinding] = []
    per_pr: Dict[int, int] = defaultdict(int)
    for finding in sorted(
        resolved,
        key=lambda item: (
            item.pr_number,
            -evidence_rank(item.evidence_tier),
            0 if item.severity == "blocking" else 1,
            item.finding_id,
        ),
    ):
        if finding.admission == "published":
            # `None` defers the limit to the digest phase, where it applies to *issues*. A
            # limit applied here counts one 19-site pattern nineteen times against a budget
            # of twenty and crowds out every other arm on that PR.
            if pr_finding_limit is not None and per_pr[finding.pr_number] >= pr_finding_limit:
                finding = finding.model_copy(update={
                    "admission": "diagnostic",
                    "admission_reason": f"per-PR publication limit of {pr_finding_limit} reached",
                })
            else:
                per_pr[finding.pr_number] += 1
        kept.append(finding)

    published_after = sum(item.admission == "published" for item in kept)
    report = {
        "merge_version": MERGE_VERSION,
        "inputs": len(findings),
        "after_merge": len(merged),
        "conflicts": len(conflicts),
        "alternatives_not_selected": alternatives,
        "published_before_limit": published_before,
        "published_after_limit": published_after,
        "suppressed_by_limit": published_before - published_after,
        "pr_finding_limit": pr_finding_limit,
        "by_admission": {
            tier: sum(item.admission == tier for item in kept)
            for tier in ("published", "diagnostic")
        },
        # Derived from the schema, not listed here. A literal list does not fail when an arm
        # is added — it silently reports nothing for it, so a new arm's entire output reads
        # as zero in every report that consumes this.
        "by_arm": {
            arm: sum(item.arm == arm for item in kept) for arm in ARMS
        },
        "by_evidence_tier": {
            tier: sum(item.evidence_tier == tier for item in kept) for tier in EVIDENCE_TIERS
        },
    }
    return kept, conflicts, report
