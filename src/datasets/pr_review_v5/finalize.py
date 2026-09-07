"""Turn what the arms returned into the review the system actually says.

Nothing new is invented here. The chain is v4's, in v4's order — ingest, evidence-gate,
project to findings, merge, digest — and v5 supplies it with arm responses instead of a
single arm's response file. That is the whole point: if v5 assembled its output its own way,
a comparison against v4's conditions would be measuring two assemblers, not two routers.

Two admission rules survive from v4 unchanged, and both are gates the lead cannot reach:

* **A specialist candidate is published only if a successful `proposed_edit` verification
  artifact joins to it** on `(work_unit_id, ordinal)`. A candidate whose artifact is missing
  is dropped rather than downgraded, because downgrading would smuggle an unverified claim
  into the one arm whose entire premise is that the compiler agreed.
* **A generalist candidate is published only if its evidence packet supports it.** When no
  evidence chain has been run there is no support, so the candidates are admitted
  `diagnostic` — retained, counted, never published. The gate is deliberately not defaulted
  open: `generalist_findings` treats `supported_candidate_ids=None` as "publish everything",
  and reaching that branch by omission would turn a publication warrant into a rubber stamp.

`issues.jsonl` is the deployable output — merged, digested, per-PR limited. Findings remain
the audit trail beneath it. Gold is paired against issues because `obligation.change_ids` is
itself multi-site, so scoring the pre-merge candidates would credit wording the merge threw
away.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from src.datasets.pr_review_v4.candidates import candidates_from_response
from src.datasets.pr_review_v4.conditions import (
    deterministic_findings,
    focused_findings,
    generalist_findings,
)
from src.datasets.pr_review_v4.digest import digest_findings
from src.datasets.pr_review_v4.io import (
    jsonl_bytes,
    pretty_json_bytes,
    sha256_bytes,
    write_once,
)
from src.datasets.pr_review_v4.merge import merge_findings
from src.datasets.pr_review_v4.schema import ReviewWorkUnit

from .arms import CHECKABLE_ARMS, GENERALIST_ARM_ID
from .synthesis import apply_assessments


def ingest_responses(
    units: Sequence[ReviewWorkUnit],
    responses: Iterable[Dict[str, Any]],
    logger=None,
) -> Tuple[List[Any], List[Any], List[Any], List[Dict[str, Any]], List[Any]]:
    """Validate arm responses into candidates, split by arm kind.

    `spec_id` is taken from the *invocation*, never from the model's self-report. Golf and
    idiom both declare `proof_simplification` while making different claims, and the verifier
    keys its warrant on the spec — a golf agent that reported itself as idiom would inherit
    idiom's laxer rule and repeal its own.

    Ingestion is non-strict: one malformed candidate is a bad item among good ones, while
    raising would discard every other candidate in the batch and leave the drop rate
    unmeasurable — which makes the system look more precise than it is.
    """

    unit_by_id = {item.work_unit_id: item for item in units}
    generalist: List[Any] = []
    specialist: List[Any] = []
    #: Per-site specialists whose concern is not settled by compiling — naming, docs, style.
    #: Kept apart from both: they are not the broad generalist, and they cannot satisfy the
    #: `focused_agent` invariant that a focused source must name a verification artifact.
    evidence_specialist: List[Any] = []
    artifacts: List[Dict[str, Any]] = []
    rejections: List[Any] = []

    for response in responses:
        work_unit_id = response.get("work_unit_id")
        unit = unit_by_id.get(work_unit_id)
        if unit is None:
            if logger:
                logger.warning("response for unknown work unit %s — skipped", work_unit_id)
            continue
        if response.get("status") != "success":
            continue
        spec_id = response.get("spec_id")
        accepted, rejected = candidates_from_response(
            unit, response, strict=False, spec_id=spec_id,
        )
        rejections.extend(rejected)
        # Split by whether the arm's concern is settled by *compiling* something, not by
        # whether it is the generalist. A naming or docstring claim cannot carry a compile
        # artifact — renaming a declaration breaks its call sites, and a typo fix proves
        # nothing by elaborating — so routing those arms to the verification gate would drop
        # every finding they ever make for lacking a warrant their concern cannot produce.
        # They go through the evidence chain instead, exactly like the generalist.
        arm_id = response.get("arm_id")
        if arm_id == GENERALIST_ARM_ID:
            generalist.extend(accepted)
        elif arm_id in CHECKABLE_ARMS:
            specialist.extend(accepted)
        else:
            evidence_specialist.extend(accepted)
        artifacts.extend(response.get("verification_artifacts") or [])
    return generalist, specialist, evidence_specialist, artifacts, rejections


def _evidence_specialist_findings(candidates, supported_candidate_ids, pr_numbers):
    """Project the non-compile specialists.

    Not via `generalist_findings`, which derives the arm from `spec_id` and would land on
    `focused_agent` — whose invariant is that a focused source names a verification artifact,
    because its warrant is a compile. These arms have no compile to point at, so they are
    filed as `generalist` (same sites, evidence-warranted, narrower checklist) with
    `source.spec_id` still naming the specialist that produced them.
    """

    from src.datasets.pr_review_v4.merge import finding_from_candidate

    supported = set(supported_candidate_ids) if supported_candidate_ids is not None else None
    wanted = set(pr_numbers) if pr_numbers else None
    findings = []
    for candidate in candidates:
        if wanted is not None and candidate.pr_number not in wanted:
            continue
        published = supported is not None and candidate.candidate_id in supported
        findings.append(finding_from_candidate(
            candidate,
            admission="published" if published else "diagnostic",
            admission_reason=(
                "evidence packet supports the claim" if published
                else "no collector can support this claim's concern family"
            ),
            arm="generalist",
        ))
    return findings


def _lead_removed_findings(removed: Sequence[Tuple[Any, str]], pr_numbers):
    """Project the candidates the lead dropped or folded, as `diagnostic` findings.

    Filed under `generalist` for the same reason `_evidence_specialist_findings` is: these
    carry no verification artifact, and `focused_agent` holds a hard invariant that a focused
    source names one. `source.spec_id` still records which arm produced the claim, so the
    per-arm attribution the routing analysis depends on survives.

    `evidence_tier` stays `model_assertion` and `admission` stays `diagnostic`: this restores
    the record of a claim, never its standing. A finding here was never evidence-checked,
    because synthesis runs before the chain.
    """

    from src.datasets.pr_review_v4.merge import finding_from_candidate

    wanted = set(pr_numbers) if pr_numbers else None
    findings = []
    for candidate, reason in removed:
        if wanted is not None and candidate.pr_number not in wanted:
            continue
        findings.append(finding_from_candidate(
            candidate,
            admission="diagnostic",
            admission_reason=f"removed by the lead before the gate: {reason}",
            arm="generalist",
        ))
    return findings


def finalize(
    out: Path,
    *,
    units: Sequence[ReviewWorkUnit],
    responses: Iterable[Dict[str, Any]],
    routing_mode: str,
    execution_release: Optional[Path] = None,
    exclude_methods: Iterable[str] = (),
    pr_numbers: Optional[Iterable[int]] = None,
    supported_candidate_ids: Optional[Iterable[str]] = None,
    collect_supported: Optional[Callable[[Sequence[Any]], Set[str]]] = None,
    candidate_assessments: Iterable[Dict[str, Any]] = (),
    pr_finding_limit: int = 20,
    logger=None,
) -> Dict[str, Any]:
    """Ingest, synthesise, gate, merge, digest, and write everything the run is judged on.

    `collect_supported` runs the evidence chain over the candidates that need one and
    returns the ids the gate admits. It is a callable rather than four more parameters
    because resolving workspaces is the runner's job, not finalization's — and because a
    caller that passes nothing must get the closed gate, not an open one.

    `candidate_assessments` is the lead's read on what came back. It can only subtract; see
    `synthesis.apply_assessments`.
    """

    responses = list(responses)
    generalist, specialist, evidence_specialist, artifacts, rejections = ingest_responses(
        units, responses, logger)
    out.mkdir(parents=True, exist_ok=True)

    # Every candidate any arm submitted, before synthesis touches anything. The immutable
    # discovery record: what the system *found* is a different question from what it chose
    # to say, and conflating them is what made the lead's drops unevaluable.
    write_once(out / "candidates_discovered.jsonl",
               jsonl_bytes([*generalist, *specialist, *evidence_specialist]))

    # Synthesis first: a candidate the lead dropped should never reach the evidence chain,
    # which is the expensive part and would be spent adjudicating a claim nobody stands by.
    (generalist, specialist, evidence_specialist,
     lead_removed, synthesis) = apply_assessments(
        generalist=generalist, specialist=specialist,
        evidence_specialist=evidence_specialist, responses=responses,
        assessments=candidate_assessments, logger=logger,
    )

    generalist_path = out / "candidates_generalist.jsonl"
    specialist_path = out / "candidates_specialist.jsonl"
    artifacts_path = out / "verification_artifacts.jsonl"
    write_once(generalist_path, jsonl_bytes(generalist))
    write_once(specialist_path, jsonl_bytes(specialist))
    write_once(artifacts_path, jsonl_bytes(artifacts))
    write_once(out / "candidate_rejections.jsonl", jsonl_bytes(rejections))

    # `focused_findings` drops any specialist candidate with no successful verification
    # artifact — correctly, since the arm's whole premise is that the compiler agreed. But
    # it drops them silently, so a run where every specialist claim evaporated looks exactly
    # like a run where the specialists found nothing. Count them here.
    verified_keys = {
        (item.get("work_unit_id"), item.get("candidate_ordinal"))
        for item in artifacts
        if item.get("stage") == "proposed_edit" and item.get("success")
    }
    unverified_specialist = [
        item for item in specialist
        if (item.work_unit_id, item.ordinal) not in verified_keys
    ]

    # The compile-gated specialists are settled by `focused_findings` against their
    # verification artifacts, so they are not put through the chain: it would cost a
    # baseline compile each and could not change their admission.
    evidence_summary: Dict[str, Any] = {}
    if collect_supported is not None:
        supported_candidate_ids = collect_supported([*generalist, *evidence_specialist])
        # Read back here, not in the runner: `finalization_report.json` is written below
        # and `write_once` will not rewrite it, so a summary attached to the returned dict
        # afterwards is silently lost — which is exactly what happened on heldout11 rep2.
        from .evidence_chain import evidence_report

        evidence_summary = evidence_report(out)

    findings = []
    if execution_release is not None:
        # The deterministic arm is identical in every routing mode — it involves no model
        # call. It is included so the three modes differ only in the model-driven half.
        findings.extend(deterministic_findings(execution_release, exclude_methods, pr_numbers))
    if generalist:
        findings.extend(generalist_findings(
            generalist_path,
            # Never `None` by omission: that branch publishes every claim unsupported.
            supported_candidate_ids if supported_candidate_ids is not None else set(),
            pr_numbers,
        ))
    if specialist:
        findings.extend(focused_findings(specialist_path, artifacts_path, pr_numbers))
    if evidence_specialist:
        findings.extend(_evidence_specialist_findings(
            evidence_specialist, supported_candidate_ids, pr_numbers))

    merged, conflicts, report = merge_findings(findings, pr_finding_limit=None)
    issues, digest_report = digest_findings(merged, pr_finding_limit=pr_finding_limit)

    # The lead's removals, projected only now — after the merge and after the digest.
    #
    # Both exclusions are deliberate. Re-entering the merge would resurrect the conflicts
    # `duplicate_of` exists to resolve, because `merge_findings` demotes *both* sides of an
    # equal-warrant clash at one anchor. Re-entering the digest would put them in the
    # maintainer-facing review, which is the one thing the lead's judgment should govern.
    # They land in `findings.jsonl` alone: the audit trail the judge reads, so a drop can
    # finally be scored instead of vanishing.
    removed_findings = _lead_removed_findings(lead_removed, pr_numbers)
    write_once(out / "findings.jsonl", jsonl_bytes([*merged, *removed_findings]))
    write_once(out / "conflicts.jsonl", jsonl_bytes(conflicts))
    write_once(out / "issues.jsonl", jsonl_bytes(issues))

    published = [item for item in issues if item.admission == "published"]
    full = {
        **report,
        "routing_mode": routing_mode,
        "scoped_pr_numbers": sorted(pr_numbers) if pr_numbers else None,
        "execution_release": str(execution_release) if execution_release else None,
        "candidates_generalist": len(generalist),
        "candidates_specialist": len(specialist),
        "candidates_evidence_specialist": len(evidence_specialist),
        "candidates_specialist_dropped_unverified": len(unverified_specialist),
        "dropped_unverified_by_concern": {
            family: sum(item.concern_family == family for item in unverified_specialist)
            for family in sorted({item.concern_family for item in unverified_specialist})
        },
        "candidate_rejections": len(rejections),
        "lead_synthesis": synthesis,
        # Restored to `findings.jsonl` but kept out of the merge and the review. Counted
        # separately so "what the lead removed" is readable without re-deriving it.
        "lead_removed_findings": len(removed_findings),
        "evidence": evidence_summary,
        "verification_artifacts": len(artifacts),
        "generalist_evidence_gate": (
            "evidence_chain" if supported_candidate_ids is not None else "closed"
        ),
        "digest": digest_report,
        "findings_sha256": sha256_bytes(jsonl_bytes(merged)),
        "issues_sha256": sha256_bytes(jsonl_bytes(issues)),
        "issues_total": len(issues),
        "issues_published": len(published),
        "published_prs": sorted({item.pr_number for item in published}),
        "published_by_concern": {
            family: sum(item.concern_family == family for item in published)
            for family in sorted({item.concern_family for item in published})
        },
    }
    write_once(out / "finalization_report.json", pretty_json_bytes(full))
    if logger:
        logger.info(
            "finalized: %d candidates -> %d findings -> %d issues (%d published)",
            len(generalist) + len(specialist) + len(evidence_specialist),
            len(merged), len(issues), len(published),
        )
        if unverified_specialist:
            logger.warning(
                "%d specialist candidate(s) were dropped for carrying no successful "
                "verification artifact (by concern: %s). A specialist claim is published "
                "only if the compiler agreed.",
                len(unverified_specialist),
                dict(full["dropped_unverified_by_concern"]),
            )
    return full
