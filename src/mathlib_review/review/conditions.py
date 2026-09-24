"""Run one ensemble condition end to end, producing the system's final findings.

Three conditions share this path, so a comparison between them differs only in which arms
contribute — not in how their output is assembled, merged, limited or serialized:

* `checker_only` — the deterministic arm alone. Judge-free and free of cost.
* `holistic_only` — the reviewer alone.
* `merged_ensemble` — both, merged.

The output is a `ReviewFinding` set, which is what gets judged. Scoring candidates *before*
the merge and projecting verdicts back through them credits a finding for wording the merge
discarded.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from src.mathlib_review.io import (
    jsonl_bytes, jsonl_rows, load_jsonl, pretty_json_bytes, sha256_bytes, write_once,
)
from src.mathlib_review.review.digest import digest_findings
from src.mathlib_review.review.merge import finding_from_candidate, finding_from_opportunity, merge_findings
from src.mathlib_review.paths import assert_repo_root
from src.mathlib_review.legacy_pipeline.phase7_adjudication import adjudicate, production_cases
from src.mathlib_review.schema import (
    FILE_COHERENCE_SPEC,
    CandidateClaim,
    EvidenceArtifact,
    EvidenceAssertion,
    EvidencePacket,
    ReviewFinding,
    ReviewOpportunity,
)
from src.mathlib_review.opportunities.select import select_findings

#: `merged_ensemble` is the locked two-arm baseline and keeps its meaning unchanged;
#: `merged_ensemble_v2` is the three-arm system. They are separate conditions rather than one
#: condition that grew an arm, because the baseline's `findings_sha256` is what every
#: focused-arm claim is measured against and it must stay reproducible.
#: `generalist_only` is the *control* — per-site, same tools as the specialists, covering the
#: families no specialist exists for. `file_generalist_only` is the *component* — one
#: invocation per changed file, restricted to claims that need the file view. They are
#: separate conditions because the whole point is to measure them apart.
CONDITIONS = ("checker_only", "generalist_only", "file_generalist_only", "focused_only",
              "merged_ensemble", "merged_ensemble_v2", "merged_ensemble_v3")

#: Method -> the concern family a maintainer would file the request under. The registries
#: speak in issue classes (`style_norm_violation`), candidates speak in concern families
#: (`style`); merging requires one vocabulary, and the candidate's is the one gold is
#: annotated against.
_CONCERN_BY_METHOD = {
    "baseline_failure.v1": "correctness",
    "canonical_api_search.v1": "duplication",
    "wrapper_composition.v1": "duplication",
    "naming_contrast.v1": "naming",
    "naming_norm.v1": "naming",
    "lint_norm.v1": "style",
    "repository_policy.v1": "correctness",
}

#: Method -> evidence strength, as an ordinal tier rather than an artifact count.
#:
#: `verified_compile` is claimed only where the operator actually ran a compiler:
#: `baseline_failure` compiles the reconstructed file, and the canonical-API and wrapper
#: operators gate on an applicability compile. The naming operators measure a snapshot
#: population — strong, but not execution. The lint and policy operators apply a published
#: textual rule.
_EVIDENCE_BY_METHOD = {
    "baseline_failure.v1": "verified_compile",
    "canonical_api_search.v1": "verified_compile",
    "wrapper_composition.v1": "verified_compile",
    "naming_contrast.v1": "repository_measurement",
    "naming_norm.v1": "repository_measurement",
    "lint_norm.v1": "lexical_rule",
    "repository_policy.v1": "lexical_rule",
}


#: Implementations that are subsumed by another and must not run in the same condition.
#:
#: `naming_contrast.encard_subject_prefix.v1` hardcodes the `Set.encard` subject;
#: `naming_norm.subject_prefix.v1` mines the subject from the conclusion and reaches
#: everything the former does. Running both makes each rename twice in different words
#: (`Metric.card_x` vs `card_x`), which the merge correctly refuses to collapse — canonical
#: equality is case and whitespace only, deliberately — and so reports as a conflict.
#:
#: They stay in the registry: Phase 9's frozen results were produced with the narrow one,
#: and removing it would invalidate that lineage. A *condition* declares which methods it
#: runs; the registry declares what exists.
#: Empty since registry `/4`, and kept as a name so the mechanism stays available.
#:
#: It previously listed `naming_contrast.v1` and read as though that operator were excluded.
#: It was not: `build_condition` defaults `exclude_methods` to `()` and the CLI to `[]`, so
#: nothing ever applied it. The three single-PR operators are now retired in the registry
#: itself (`method_registry.RETIRED_SINGLE_PR_METHODS`), which cannot be forgotten at a call
#: site the way a flag can.
SUBSUMED_METHODS: tuple = ()


def deterministic_findings(execution_release: Path,
                           exclude_methods: Iterable[str] = (),
                           pr_numbers: Optional[Iterable[int]] = None) -> List[ReviewFinding]:
    """Adjudicate every opportunity and project it into the common finding shape.

    Everything not adjudicated `request` becomes `diagnostic` rather than disappearing, so
    the arm's reach stays measurable without claiming it would have said anything to a
    maintainer. `defer` deliberately does not trigger LLM redundancy voting: those votes
    cost money and are non-deterministic, and would forfeit the arm's only two durable
    properties — byte-reproducibility and silence on control PRs.
    """

    opportunities = {
        item.opportunity_id: item for item in
        load_jsonl(execution_release / "derived/opportunities.jsonl", ReviewOpportunity)
    }
    excluded = set(exclude_methods)
    wanted = set(pr_numbers) if pr_numbers else None
    findings = []
    for case in production_cases(execution_release):
        opportunity = opportunities[case.opportunity_id]
        if opportunity.method_id in excluded:
            continue
        if wanted is not None and opportunity.pr_number not in wanted:
            continue
        for decision in adjudicate(case).worthiness_decisions:
            findings.append(finding_from_opportunity(
                opportunity, decision,
                concern_family=_CONCERN_BY_METHOD.get(opportunity.method_id, "other"),
                evidence_tier=_EVIDENCE_BY_METHOD.get(opportunity.method_id, "lexical_rule"),
            ))
    return findings


def generalist_findings(candidates_path: Path,
                      supported_candidate_ids: Optional[Iterable[str]] = None,
                      pr_numbers: Optional[Iterable[int]] = None,
                      evidence_tiers: Optional[Dict[str, str]] = None) -> List[ReviewFinding]:
    """Project reviewer candidates into the common shape.

    `supported_candidate_ids` are those whose evidence packet passes the publication gate
    (`select.select_findings`). Everything else is retained as `diagnostic`.

    The gate is deliberately not loosened here. `evidence.py` has no collector that can
    emit a claim-scoped `supports` for naming, documentation or scope, so the holistic
    published tier is structurally near-empty for 53% of the corpus. That is a result to
    report, not a gate to relax: loosening it turns a publication warrant into a rubber
    stamp and worsens exactly the silent-PR axis the deterministic arm wins on.
    """

    supported = set(supported_candidate_ids) if supported_candidate_ids is not None else None
    tiers = evidence_tiers or {}
    wanted = set(pr_numbers) if pr_numbers else None
    findings = []
    for candidate in load_jsonl(candidates_path, CandidateClaim):
        if wanted is not None and candidate.pr_number not in wanted:
            continue
        published = supported is None or candidate.candidate_id in supported
        # Only a published candidate can carry a warrant. A diagnostic one was not supported,
        # so there is nothing to tier it from, and letting a tier ride on an unsupported
        # claim would let it outrank a supported rival at the same anchor.
        tier = tiers.get(candidate.candidate_id) if published else None
        findings.append(finding_from_candidate(
            candidate,
            admission="published" if published else "diagnostic",
            admission_reason=(
                "evidence packet supports the claim" if published
                else "no collector can support this claim's concern family"
            ),
            **({"evidence_tier": tier} if tier else {}),
        ))
    return findings


def focused_findings(candidates_path: Path,
                     verification_artifacts_path: Optional[Path] = None,
                     pr_numbers: Optional[Iterable[int]] = None,
                     dropped: Optional[List[CandidateClaim]] = None) -> List[ReviewFinding]:
    """Project focused-agent candidates into the common shape.

    Every focused candidate that exists was already compile-verified: the submission handler
    refuses a focused finding without a structured edit and rejects the edit if recompiling
    the reviewed file fails. So the evidence tier is `verified_compile` — not because this
    function asserts it, but because a candidate could not have been recorded otherwise.

    What that tier does *not* mean is worth stating where the tier is assigned. The compile
    shows the replacement elaborates in context; with the statement gate it also shows the
    theorem is unchanged. It does not show the new proof closes the same goal. That is the
    strongest available proxy and it is a proxy.

    Artifacts join on `(invocation_id, ordinal)` -- on `(work_unit_id, ordinal)` only for runs
    whose artifacts predate the field -- which is why `CandidateClaim.ordinal` is recorded. A candidate whose artifact is missing is dropped rather than published at a
    tier nothing backs — `FindingSource` refuses a focused source with no evidence, and
    silently downgrading it to `model_assertion` would smuggle an unverified claim into the
    arm whose entire premise is verification.

    Pass `dropped` to collect those candidates rather than only counting them. Until this
    existed the drop was a line on stderr and nothing else: no artifact, nothing the judge
    could see, no way to tell a correct claim that lacked a warrant from a wrong one. That
    That mattered beyond bookkeeping: it was the precondition for retiring v5's concern gate,
    which refused an off-concern submission up front precisely because such a claim lands here
    and used to vanish. It is collected now, so the gate is gone.
    """

    wanted = set(pr_numbers) if pr_numbers else None
    # Keyed on the invocation when the artifacts carry it. `(work_unit_id, ordinal)` is kept only
    # for runs whose artifacts predate the field, so they finalize as they did -- it is not a key
    # in v5, where every arm's first candidate on a unit is ordinal 0, and it published an arm's
    # edit-less claim on another arm's compile (7 findings on the family-division run).
    artifacts_by_candidate: Dict[tuple, List[str]] = {}
    keyed_by_invocation = False
    if verification_artifacts_path and verification_artifacts_path.is_file():
        rows = [row for row in jsonl_rows(verification_artifacts_path)
                if row.get("stage") == "proposed_edit" and row.get("success")]
        keyed_by_invocation = any(row.get("invocation_id") for row in rows)
        for row in rows:
            key = ((row.get("invocation_id"), row.get("candidate_ordinal")) if keyed_by_invocation
                   else (row.get("work_unit_id"), row.get("candidate_ordinal")))
            artifacts_by_candidate.setdefault(key, []).append(row["artifact_id"])

    findings, unverified = [], 0
    for candidate in load_jsonl(candidates_path, CandidateClaim):
        if wanted is not None and candidate.pr_number not in wanted:
            continue
        if not candidate.spec_id or candidate.spec_id == FILE_COHERENCE_SPEC:
            raise ValueError(
                f"{candidate.candidate_id} carries no focused spec_id, so it is not a "
                "focused candidate; the focused condition must not silently absorb "
                "generalist or file-scoped output"
            )
        # A v5 invocation id is `<work unit>#<arm>`, and a focused candidate carries both halves.
        key = ((f"{candidate.work_unit_id}#{candidate.spec_id}", candidate.ordinal)
               if keyed_by_invocation else (candidate.work_unit_id, candidate.ordinal))
        artifact_ids = artifacts_by_candidate.get(key, [])
        if not artifact_ids:
            unverified += 1
            if dropped is not None:
                dropped.append(candidate)
            continue
        findings.append(finding_from_candidate(
            candidate,
            admission="published",
            admission_reason="the proposed edit recompiled the reviewed file",
            evidence_tier="verified_compile",
            evidence_artifact_ids=artifact_ids,
        ))
    if unverified:
        print(f"note: dropped {unverified} focused candidates with no successful "
              f"verification artifact", file=sys.stderr)
    return findings


def file_generalist_findings(candidates_path: Path,
                             pr_numbers: Optional[Iterable[int]] = None
                             ) -> List[ReviewFinding]:
    """Project file-scoped candidates into the common shape.

    Admitted at `model_assertion` like any prose claim: seeing a whole file is a better
    *vantage point*, not stronger evidence. The arm's discipline is in what it is allowed to
    claim — several targets, or `scope_placement` — enforced at submission, not here.
    """

    wanted = set(pr_numbers) if pr_numbers else None
    findings = []
    for candidate in load_jsonl(candidates_path, CandidateClaim):
        if wanted is not None and candidate.pr_number not in wanted:
            continue
        if candidate.spec_id != FILE_COHERENCE_SPEC:
            raise ValueError(
                f"{candidate.candidate_id} is not a file-scoped candidate "
                f"(spec_id={candidate.spec_id!r})"
            )
        findings.append(finding_from_candidate(
            candidate, admission="published",
            admission_reason="file-scoped claim spanning several targets",
        ))
    return findings


def supported_from_evidence(candidates_path: Path, evidence_dir: Path) -> List[str]:
    """Apply the real publication gate: `select.select_findings`.

    Read through `select` rather than reimplemented here, so the condition cannot drift
    from the gate it claims to apply. The gate is strict by design — no collector can emit
    a claim-scoped `supports` for naming, documentation or scope — and that strictness is
    not loosened to make the holistic arm look better: it is what keeps the arm's silent-PR
    behaviour meaningful.

    `tiers_from_evidence` reads the same pass for the warrant each survivor earned; the two
    are separate calls because publication and rank are separate questions, and only the
    first one is a gate.
    """

    candidates = load_jsonl(candidates_path, CandidateClaim)
    packets = load_jsonl(evidence_dir / "packets.jsonl", EvidencePacket)
    assertions = load_jsonl(evidence_dir / "assertions.jsonl", EvidenceAssertion)
    return [item.candidate_id for item in select_findings(candidates, packets, assertions)]


def tiers_from_evidence(candidates_path: Path, evidence_dir: Path) -> Dict[str, str]:
    """The warrant each supported candidate actually earned, keyed by candidate id.

    Read from the same `select_findings` pass that decides publication, so a candidate can
    never be published on one set of assertions and tiered on another.

    The rule is deliberately narrow, and it is keyed on *what produced the support*, never
    on the claim's text:

    * a `lean_compile` artifact supporting the `proposed_edit` -> `verified_compile`. The
      compiler accepted the replacement; that is the same warrant `focused_findings` states,
      established the same way.
    * otherwise an `issue_kind_verifier` artifact -> whatever
      `verifiers.WARRANT_BY_ISSUE_KIND` says that kind's operator earns, which today is
      `naming_norm` and `lint_policy` and nothing else.
    * otherwise the floor, `model_assertion`.

    `repository_search` is pointedly *not* in that list even though it supports 7 of the 11
    selected candidates on rep1. "Found 1 file(s) declaring a cited identifier" is a
    retrieval hit, not a measurement over the repository, and promoting it would hand the
    largest holistic family a tier it did not earn — which is the rubber stamp
    `generalist_findings` and `verifiers` both warn about in their own docstrings.

    Returns only the candidates that clear the gate. Everything else is absent, and an
    absent candidate keeps `finding_from_candidate`'s `model_assertion` default.
    """

    from src.mathlib_review.evidence.verifiers import WARRANT_BY_ISSUE_KIND

    packets_path = evidence_dir / "packets.jsonl"
    assertions_path = evidence_dir / "assertions.jsonl"
    artifacts_path = evidence_dir / "artifacts.jsonl"
    # A chain that did not run leaves no files, and "no chain" means "no warrant" — every
    # candidate keeps the `model_assertion` floor. Raising here instead would make a caller
    # that supplies its own `collect_supported` — every finalize test does — die on a file
    # the gate it stubbed never wrote.
    if not (packets_path.is_file() and assertions_path.is_file()):
        return {}

    candidates = load_jsonl(candidates_path, CandidateClaim)
    packets = load_jsonl(packets_path, EvidencePacket)
    assertions = load_jsonl(assertions_path, EvidenceAssertion)
    artifacts = ({item.artifact_id: item
                  for item in load_jsonl(artifacts_path, EvidenceArtifact)}
                 if artifacts_path.is_file() else {})

    by_id = {item.candidate_id: item for item in candidates}
    assertion_by_id = {item.assertion_id: item for item in assertions}
    packet_by_candidate = {item.candidate_id: item for item in packets}

    tiers: Dict[str, str] = {}
    for selected in select_findings(candidates, packets, assertions):
        candidate = by_id.get(selected.candidate_id)
        if candidate is None:
            continue
        packet = packet_by_candidate.get(selected.candidate_id)
        packet_assertions = [assertion_by_id[item] for item in (packet.assertion_ids if packet else [])
                             if item in assertion_by_id]
        # The compile has to be the one that vouched for the *edit*. A `lean_compile`
        # artifact also rides along on `local_context` baselines, and "the file compiled
        # before we touched it" is not a warrant for the claim.
        verified = any(
            item.assertion_scope == "proposed_edit" and item.polarity == "supports"
            and any(artifacts[ref].collector == "lean_compile"
                    for ref in item.artifact_ids if ref in artifacts)
            for item in packet_assertions
        )
        if verified:
            tiers[candidate.candidate_id] = "verified_compile"
            continue
        supporting = [assertion_by_id[item] for item in selected.evidence_assertion_ids
                      if item in assertion_by_id]
        by_verifier = any(
            artifacts[ref].collector == "issue_kind_verifier"
            for item in supporting for ref in item.artifact_ids if ref in artifacts
        )
        warrant = WARRANT_BY_ISSUE_KIND.get(candidate.issue_kind or "")
        if by_verifier and warrant:
            tiers[candidate.candidate_id] = warrant
    return tiers


def build_condition(
    condition: str,
    out: Path,
    *,
    execution_release: Optional[Path] = None,
    exclude_methods: Iterable[str] = (),
    pr_numbers: Optional[Iterable[int]] = None,
    candidates: Optional[Path] = None,
    supported_candidate_ids: Optional[Iterable[str]] = None,
    evidence_tiers: Optional[Dict[str, str]] = None,
    focused_candidates: Optional[Path] = None,
    file_candidates: Optional[Path] = None,
    focused_verification_artifacts: Optional[Path] = None,
    pr_finding_limit: int = 20,
) -> Dict:
    assert_repo_root()
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}; expected one of {CONDITIONS}")

    findings: List[ReviewFinding] = []
    if condition in ("checker_only", "merged_ensemble", "merged_ensemble_v2",
                     "merged_ensemble_v3"):
        if execution_release is None:
            raise ValueError(f"{condition} requires --execution-release")
        findings.extend(deterministic_findings(execution_release, exclude_methods, pr_numbers))
    if condition in ("generalist_only", "merged_ensemble", "merged_ensemble_v2",
                     "merged_ensemble_v3"):
        if candidates is None:
            raise ValueError(f"{condition} requires --candidates")
        findings.extend(generalist_findings(candidates, supported_candidate_ids, pr_numbers,
                                            evidence_tiers))
    if condition in ("file_generalist_only", "merged_ensemble_v3"):
        if file_candidates is None:
            raise ValueError(f"{condition} requires --file-candidates")
        findings.extend(file_generalist_findings(file_candidates, pr_numbers))
    if condition in ("focused_only", "merged_ensemble_v2", "merged_ensemble_v3"):
        if focused_candidates is None:
            raise ValueError(f"{condition} requires --focused-candidates")
        findings.extend(focused_findings(
            focused_candidates, focused_verification_artifacts, pr_numbers,
        ))

    # Merge without the limit, digest into issues, then limit the issues. Findings remain the
    # audit trail; issues are what the system says to a maintainer and what gold is paired
    # against, since `obligation.change_ids` is itself multi-site.
    merged, conflicts, report = merge_findings(findings, pr_finding_limit=None)
    issues, digest_report = digest_findings(merged, pr_finding_limit=pr_finding_limit)
    out.mkdir(parents=True, exist_ok=True)
    write_once(out / "findings.jsonl", jsonl_bytes(merged))
    write_once(out / "conflicts.jsonl", jsonl_bytes(conflicts))
    write_once(out / "issues.jsonl", jsonl_bytes(issues))
    published = [item for item in issues if item.admission == "published"]
    full = {
        **report,
        "condition": condition,
        "excluded_methods": sorted(exclude_methods),
        "scoped_pr_numbers": sorted(pr_numbers) if pr_numbers else None,
        "execution_release": str(execution_release) if execution_release else None,
        "candidates": str(candidates) if candidates else None,
        "focused_candidates": str(focused_candidates) if focused_candidates else None,
        "digest": digest_report,
        "findings_sha256": sha256_bytes(jsonl_bytes(merged)),
        "issues_sha256": sha256_bytes(jsonl_bytes(issues)),
        "published_prs": sorted({item.pr_number for item in published}),
        "published_by_concern": {
            family: sum(item.concern_family == family for item in published)
            for family in sorted({item.concern_family for item in published})
        },
    }
    write_once(out / "condition_report.json", pretty_json_bytes(full))
    return full


def main() -> None:
    parser = argparse.ArgumentParser(description="Build one ensemble condition's findings")
    parser.add_argument("--condition", required=True, choices=CONDITIONS)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--execution-release", type=Path)
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--file-candidates", type=Path,
                        help="candidates from the file-scoped generalist component")
    parser.add_argument("--focused-candidates", type=Path,
                        help="candidates from the focused arm; each must carry a spec_id")
    parser.add_argument("--focused-verification-artifacts", type=Path,
                        help="the focused run's verification artifacts; a focused finding "
                             "without one is dropped, never downgraded")
    parser.add_argument("--pr-finding-limit", type=int, default=20)
    parser.add_argument("--pr-numbers", nargs="*", type=int, default=[])
    parser.add_argument("--evidence-dir", type=Path,
                        help="apply the real publication gate; without it every holistic "
                             "candidate is admitted, which overstates the arm")
    parser.add_argument("--exclude-methods", nargs="*", default=[],
                        help=f"methods to leave out; subsumed today: {SUBSUMED_METHODS}")
    args = parser.parse_args()
    if args.condition in ("generalist_only", "merged_ensemble", "merged_ensemble_v2"):
        if args.evidence_dir is None:
            parser.error(
                f"{args.condition} requires --evidence-dir; omitting the publication gate "
                "would silently publish every generalist candidate"
            )
    print(json.dumps(build_condition(
        args.condition, args.out,
        execution_release=args.execution_release,
        candidates=args.candidates,
        focused_candidates=args.focused_candidates,
        file_candidates=args.file_candidates,
        focused_verification_artifacts=args.focused_verification_artifacts,
        pr_finding_limit=args.pr_finding_limit,
        exclude_methods=args.exclude_methods,
        pr_numbers=args.pr_numbers or None,
        supported_candidate_ids=(
            supported_from_evidence(args.candidates, args.evidence_dir)
            if args.evidence_dir and args.candidates else None
        ),
    ), indent=2))


if __name__ == "__main__":
    main()
