"""Lineage-preserving PR-level synthesis for accepted review opportunities."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
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
from src.mathlib_review.schema import (
    CandidateClaim,
    CandidateOpportunityLink,
    ChangeGraph,
    AdjudicationConsensus,
    InvestigationTask,
    OpportunityAdjudication,
    OracleOpportunity,
    PRRelation,
    ResidualReviewPass,
    ReviewOpportunity,
    SemanticMatch,
    SynthesisAnchor,
    SynthesisDecision,
    SynthesisMatchProjection,
    SynthesizedFinding,
    WorthinessDecision,
)


SYNTHESIS_VERSION = "phase8-pr-synthesis/1"
DEFAULT_PHASE2 = Path("inputs/pr_review_v4/treatments/systematic-opportunities-v1")
DEFAULT_ORACLE_RELEASE = Path("inputs/pr_review_v4/treatments/oracle-evidence-probe-0.2.0")
DEFAULT_ORACLE_RUN = Path("results/pr_review_v4/runs/oracle-evidence-probe-0.2.0")
DEFAULT_PHASE7_GATE = Path("results/pr_review_v4/audits/phase7-adjudication-gate-0.1.1")
DEFAULT_PHASE7_CANONICAL = Path(
    "results/pr_review_v4/runs/phase7-canonical-redundancy-smoke-0.1.1"
)
DEFAULT_CANONICAL_RELEASE = Path(
    "inputs/pr_review_v4/releases/dev-pilot-0.9.1-canonical-smoke"
)
DEFAULT_CANONICAL_RUN = Path(
    "results/pr_review_v4/runs/dev-pilot-0.9.1-canonical-smoke-rep1"
)
DEFAULT_OUT = Path("results/pr_review_v4/audits/phase8-synthesis-gate-0.1.0")


def _digest(payload) -> str:
    return sha256_bytes(canonical_json_bytes(payload))


def _record_id(prefix: str, payload) -> tuple[str, str]:
    digest = _digest(payload)
    return f"{prefix}:{digest[:24]}", digest


def accepted_opportunity_ids(
    decisions: Iterable[WorthinessDecision],
    consensus: Iterable = (),
) -> set[str]:
    accepted = {
        item.opportunity_id for item in decisions if item.review_worthiness == "request"
    }
    for item in consensus:
        if item.status == "agreement" and item.final_worthiness == "request":
            accepted.add(item.opportunity_id)
        else:
            accepted.discard(item.opportunity_id)
    return accepted


def _method_family(method: str) -> str:
    return method.removesuffix(".v1")


def _method_matches_candidate(method: str, candidate: CandidateClaim) -> bool:
    family = _method_family(method)
    if candidate.concern_family == "naming":
        return family == "naming_contrast"
    if candidate.concern_family == "proof-golf":
        return family == "proof_compression"
    if candidate.concern_family == "style":
        return family in {
            "canonical_api_search", "wrapper_composition", "intra_pr_composition",
            "proof_compression", "repository_pattern",
        }
    return True


def _text_symbols(value: str | None) -> list[str]:
    if not value:
        return []
    return sorted({
        token for token in re.findall(r"`([^`]+)`", value)
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_'.]*(?:\.[A-Za-z_][A-Za-z0-9_']*)*", token)
    })


def link_candidates(
    candidates: Iterable[CandidateClaim],
    production_opportunities: Iterable[ReviewOpportunity] = (),
    oracle_opportunities: Iterable[OracleOpportunity] = (),
    investigation_tasks: Iterable[InvestigationTask] = (),
    relations: Iterable[PRRelation] = (),
) -> list[CandidateOpportunityLink]:
    candidates = list(candidates)
    production = list(production_opportunities)
    oracle = list(oracle_opportunities)
    task_by_investigation = {item.investigation_id: item for item in investigation_tasks}
    relations = list(relations)
    links = []
    for candidate in candidates:
        explicit = set(candidate.opportunity_ids)
        options = []
        for item in production:
            task = task_by_investigation.get(item.investigation_id)
            if (
                (item.opportunity_id in explicit)
                or (
                    task is not None
                    and task.work_unit_id == candidate.work_unit_id
                    and item.primary_change_id == candidate.primary_change_id
                )
            ):
                options.append((item, item.method_id, item.source_artifact_ids))
        for item in oracle:
            if (
                (item.opportunity_id in explicit)
                or (
                    item.work_unit_id == candidate.work_unit_id
                    and item.primary_change_id == candidate.primary_change_id
                )
            ):
                options.append((item, item.method, [evidence.evidence_id for evidence in item.evidence]))
        narrowed = [item for item in options if _method_matches_candidate(item[1], candidate)]
        if narrowed:
            options = narrowed
        if len(options) != 1:
            raise ValueError(
                f"candidate {candidate.candidate_id} maps to {len(options)} opportunities"
            )
        opportunity, method, evidence_ids = options[0]
        context_changes = list(opportunity.related_change_ids)
        relation_ids = sorted({
            relation.relation_id for relation in relations
            if relation.pr_number == candidate.pr_number
            and relation.source_change_id == candidate.primary_change_id
            and set(relation.related_change_ids).intersection(context_changes)
            and relation.confidence in {"exact", "high"}
        })
        if isinstance(opportunity, ReviewOpportunity):
            transformation = opportunity.proposed_transformation
            action_kind = transformation.kind if transformation else _method_family(method)
            symbols = list(transformation.symbols) if transformation else []
            investigation_id = opportunity.investigation_id
        else:
            action_kind = _method_family(method)
            symbols = _text_symbols(opportunity.proposed_alternative)
            investigation_id = None
        payload = {
            "candidate_id": candidate.candidate_id,
            "opportunity_id": opportunity.opportunity_id,
            "investigation_id": investigation_id,
            "pr_number": candidate.pr_number,
            "method_id": method,
            "primary_change_id": candidate.primary_change_id,
            "context_change_ids": context_changes,
            "relation_ids": relation_ids,
            "action_kind": action_kind,
            "action_symbols": symbols,
            "evidence_artifact_ids": list(evidence_ids),
        }
        link_id, digest = _record_id("candidate-opportunity-link", payload)
        links.append(CandidateOpportunityLink(link_id=link_id, source_sha256=digest, **payload))
    return links


def _action_key(candidate: CandidateClaim, link: CandidateOpportunityLink) -> str:
    if link.action_symbols:
        identity = {"kind": link.action_kind, "symbols": sorted(link.action_symbols)}
    else:
        normalized = re.sub(r"\W+", " ", candidate.requested_change.lower()).strip()
        identity = {"kind": link.action_kind, "request": normalized}
    return f"action:{_digest(identity)[:24]}"


def _decision(
    action: str,
    pr_number: int,
    rows: Sequence[tuple[CandidateClaim, CandidateOpportunityLink]],
    finding_id: str | None,
    rationale: str,
) -> SynthesisDecision:
    payload = {
        "pr_number": pr_number,
        "action": action,
        "opportunity_ids": sorted({link.opportunity_id for _candidate, link in rows}),
        "candidate_ids": sorted({candidate.candidate_id for candidate, _link in rows}),
        "finding_id": finding_id,
        "evidence_artifact_ids": sorted({
            evidence_id for _candidate, link in rows for evidence_id in link.evidence_artifact_ids
        }),
        "rationale": rationale,
    }
    synthesis_id, digest = _record_id("synthesis-decision", payload)
    return SynthesisDecision(synthesis_id=synthesis_id, source_sha256=digest, **payload)


def _relation_connects(
    left: Sequence[tuple[CandidateClaim, CandidateOpportunityLink]],
    right: Sequence[tuple[CandidateClaim, CandidateOpportunityLink]],
    relations: Sequence[PRRelation],
) -> bool:
    left_ids = {candidate.primary_change_id for candidate, _link in left}
    right_ids = {candidate.primary_change_id for candidate, _link in right}
    return any(
        relation.confidence in {"exact", "high"}
        and relation.relation_kind in {
            "changed_siblings", "name_family", "direct_use_of_changed_declaration"
        }
        and (
            relation.source_change_id in left_ids
            and bool(set(relation.related_change_ids).intersection(right_ids))
            or relation.source_change_id in right_ids
            and bool(set(relation.related_change_ids).intersection(left_ids))
        )
        for relation in relations
    )


def synthesize_findings(
    candidates: Iterable[CandidateClaim],
    links: Iterable[CandidateOpportunityLink],
    accepted_opportunities: set[str],
    relations: Iterable[PRRelation] = (),
    support_scores: dict[str, float] | None = None,
    volume_limit: int = 20,
) -> tuple[list[SynthesizedFinding], list[SynthesisDecision]]:
    candidates = list(candidates)
    links = list(links)
    relations = list(relations)
    support_scores = support_scores or {}
    candidate_by_id = {item.candidate_id: item for item in candidates}
    link_by_candidate = {}
    for link in links:
        if link.candidate_id in link_by_candidate:
            raise ValueError(f"candidate {link.candidate_id} has multiple synthesis links")
        if link.candidate_id not in candidate_by_id:
            raise ValueError(f"link references unknown candidate {link.candidate_id}")
        link_by_candidate[link.candidate_id] = link
    missing = {item.candidate_id for item in candidates} - set(link_by_candidate)
    if missing:
        raise ValueError(f"candidates lack opportunity links: {sorted(missing)}")
    rows = [
        (candidate, link_by_candidate[candidate.candidate_id])
        for candidate in candidates
        if link_by_candidate[candidate.candidate_id].opportunity_id in accepted_opportunities
    ]

    by_issue = defaultdict(list)
    for candidate, link in rows:
        by_issue[(candidate.pr_number, _method_family(link.method_id), link.primary_change_id)].append(
            (candidate, link)
        )
    decisions: list[SynthesisDecision] = []
    issue_clusters = []
    for issue_key, issue_rows in sorted(by_issue.items()):
        by_action = defaultdict(list)
        for row in issue_rows:
            by_action[_action_key(*row)].append(row)
        if len(by_action) == 1:
            action_key, winning_rows = next(iter(by_action.items()))
            issue_clusters.append((action_key, winning_rows))
            continue
        action_scores = {
            action: max(support_scores.get(link.opportunity_id, 0.0) for _candidate, link in group)
            for action, group in by_action.items()
        }
        top = max(action_scores.values())
        winners = [action for action, score in action_scores.items() if score == top]
        if len(winners) != 1:
            decisions.append(_decision(
                "defer_conflict", issue_key[0], issue_rows, None,
                "Competing transformations have equal evidence support; synthesis defers.",
            ))
            continue
        winner = winners[0]
        issue_clusters.append((winner, by_action[winner]))
        for action, group in by_action.items():
            if action != winner:
                decisions.append(_decision(
                    "suppress_dominated", issue_key[0], group, None,
                    "A competing transformation has strictly stronger evidence support.",
                ))

    # Merge only same-action clusters joined by a validated PR relation.
    merged: list[tuple[str, list[tuple[CandidateClaim, CandidateOpportunityLink]]]] = []
    for action_key, cluster in issue_clusters:
        matches = [
            index for index, (other_action, other_cluster) in enumerate(merged)
            if action_key == other_action and _relation_connects(cluster, other_cluster, relations)
        ]
        if not matches:
            merged.append((action_key, list(cluster)))
            continue
        target = matches[0]
        merged[target][1].extend(cluster)
        for index in reversed(matches[1:]):
            merged[target][1].extend(merged.pop(index)[1])

    ordered_clusters = sorted(merged, key=lambda item: (
        0 if any(candidate.severity == "blocking" for candidate, _link in item[1]) else 1,
        min(candidate.candidate_id for candidate, _link in item[1]),
    ))
    findings = []
    for rank, (action_key, cluster) in enumerate(ordered_clusters):
        representative, _rep_link = max(cluster, key=lambda row: (
            support_scores.get(row[1].opportunity_id, 0.0),
            row[0].model_confidence if row[0].model_confidence is not None else 0.0,
            row[0].candidate_id,
        ))
        candidate_ids = sorted({candidate.candidate_id for candidate, _link in cluster})
        opportunity_ids = sorted({link.opportunity_id for _candidate, link in cluster})
        issue_changes = sorted({change_id for candidate, _link in cluster for change_id in candidate.change_ids})
        context_changes = sorted({
            change_id for _candidate, link in cluster for change_id in link.context_change_ids
            if change_id not in issue_changes
        })
        anchors = []
        for change_id in issue_changes:
            anchor_rows = [row for row in cluster if change_id in row[0].change_ids]
            anchors.append(SynthesisAnchor(
                change_id=change_id,
                source_candidate_ids=sorted({row[0].candidate_id for row in anchor_rows}),
                source_opportunity_ids=sorted({row[1].opportunity_id for row in anchor_rows}),
                relation_ids=sorted({relation_id for row in anchor_rows for relation_id in row[1].relation_ids}),
            ))
        multi_anchor = len(issue_changes) > 1
        subjects = sorted({candidate.primary_subject for candidate, _link in cluster if candidate.primary_subject})
        claim = representative.claim
        requested_change = representative.requested_change or "Apply the supported transformation."
        if multi_anchor:
            claim += " The same supported concern applies across: " + ", ".join(subjects) + "."
            requested_change += " Apply the same transformation consistently at all listed anchors."
        payload = {
            "pr_number": representative.pr_number,
            "source_candidate_ids": candidate_ids,
            "source_opportunity_ids": opportunity_ids,
            "investigation_ids": sorted({
                link.investigation_id for _candidate, link in cluster if link.investigation_id
            }),
            "change_ids": issue_changes,
            "context_change_ids": context_changes,
            "anchors": [item.model_dump(mode="json") for item in anchors],
            "method_ids": sorted({link.method_id for _candidate, link in cluster}),
            "action_key": action_key,
            "concern_family": representative.concern_family,
            "severity": (
                "blocking" if any(candidate.severity == "blocking" for candidate, _link in cluster)
                else "advisory"
            ),
            "claim": claim,
            "requested_change": requested_change,
            "evidence_artifact_ids": sorted({
                evidence_id for _candidate, link in cluster for evidence_id in link.evidence_artifact_ids
            }),
            "rank_key": f"{rank:08d}:{action_key}",
        }
        finding_id, digest = _record_id("synthesized-finding", payload)
        finding = SynthesizedFinding(finding_id=finding_id, source_sha256=digest, **payload)
        if len(findings) >= volume_limit:
            decisions.append(_decision(
                "suppress_volume", representative.pr_number, cluster, None,
                f"The explicit PR finding budget of {volume_limit} was exhausted.",
            ))
            continue
        findings.append(finding)
        decisions.append(_decision(
            "group" if len(candidate_ids) > 1 or multi_anchor else "retain",
            representative.pr_number, cluster, finding.finding_id,
            "Same-action sources were merged with complete candidate and opportunity lineage."
            if len(candidate_ids) > 1 or multi_anchor
            else "The accepted opportunity is retained as one supported PR-level finding.",
        ))
        by_anchor_action = defaultdict(list)
        for row in cluster:
            by_anchor_action[(row[0].primary_change_id, _action_key(*row))].append(row)
        for duplicate_rows in by_anchor_action.values():
            if len(duplicate_rows) > 1:
                decisions.append(_decision(
                    "suppress_duplicate", representative.pr_number, duplicate_rows[1:],
                    finding.finding_id,
                    "Equivalent candidate variants are represented by the grouped finding.",
                ))
    return findings, decisions


def project_semantic_matches(
    findings: Iterable[SynthesizedFinding], matches: Iterable[SemanticMatch]
) -> list[SynthesisMatchProjection]:
    matches = list(matches)
    by_candidate = defaultdict(list)
    for match in matches:
        by_candidate[match.candidate_id].append(match)
    projections = []
    for finding in findings:
        by_obligation = defaultdict(list)
        for candidate_id in finding.source_candidate_ids:
            for match in by_candidate.get(candidate_id, []):
                by_obligation[match.obligation_id].append(match)
        for obligation_id, source_matches in sorted(by_obligation.items()):
            payload = {
                "finding_id": finding.finding_id,
                "obligation_id": obligation_id,
                "source_candidate_ids": sorted({item.candidate_id for item in source_matches}),
                "issue_match": any(item.issue_match for item in source_matches),
                "resolution_match": any(item.resolution_match for item in source_matches),
                "source_match_ids": sorted({item.match_id for item in source_matches}),
            }
            projection_id, digest = _record_id("synthesis-match-projection", payload)
            projections.append(SynthesisMatchProjection(
                projection_id=projection_id, source_sha256=digest, **payload
            ))
    return projections


def schedule_residual_reviews(
    graphs: Iterable[ChangeGraph],
    opportunities: Iterable[OracleOpportunity | ReviewOpportunity],
    findings: Iterable[SynthesizedFinding],
) -> list[ResidualReviewPass]:
    graphs = list(graphs)
    opportunities = list(opportunities)
    findings = list(findings)
    output = []
    for graph in sorted(graphs, key=lambda item: item.pr_number):
        pr_opportunities = [item for item in opportunities if item.pr_number == graph.pr_number]
        pr_findings = [item for item in findings if item.pr_number == graph.pr_number]
        covered = sorted({item.primary_change_id for item in pr_opportunities})
        all_changes = {item.change_id for item in graph.targets}
        payload = {
            "episode_id": graph.episode_id,
            "pr_number": graph.pr_number,
            "status": "scheduled",
            "covered_method_ids": sorted({
                item.method if isinstance(item, OracleOpportunity) else item.method_id
                for item in pr_opportunities
            }),
            "structured_finding_ids": sorted(item.finding_id for item in pr_findings),
            "covered_change_ids": covered,
            "uncovered_change_ids": sorted(all_changes - set(covered)),
            "candidate_ids": [],
            "terminal_reason": None,
        }
        residual_id, digest = _record_id("residual-review", payload)
        output.append(ResidualReviewPass(residual_id=residual_id, source_sha256=digest, **payload))
    return output


def build_gate_artifacts() -> tuple[dict[str, list], dict]:
    oracle_opportunities = load_jsonl(
        DEFAULT_ORACLE_RELEASE / "derived/oracle_opportunities.jsonl", OracleOpportunity
    )
    graphs = load_jsonl(DEFAULT_ORACLE_RELEASE / "derived/change_graphs.jsonl", ChangeGraph)
    candidates = load_jsonl(DEFAULT_ORACLE_RUN / "candidates.jsonl", CandidateClaim)
    candidates.extend(load_jsonl(DEFAULT_CANONICAL_RUN / "candidates.jsonl", CandidateClaim))
    matches = load_jsonl(DEFAULT_ORACLE_RUN / "semantic-judge-v1/matches.jsonl", SemanticMatch)
    matches.extend(load_jsonl(
        DEFAULT_CANONICAL_RUN / "semantic-judge-v1/matches.jsonl", SemanticMatch
    ))
    decisions = load_jsonl(DEFAULT_PHASE7_GATE / "worthiness_decisions.jsonl", WorthinessDecision)
    consensus = load_jsonl(
        DEFAULT_PHASE7_CANONICAL / "adjudication_consensuses.jsonl", AdjudicationConsensus
    )
    production_opportunities = load_jsonl(
        DEFAULT_CANONICAL_RELEASE / "derived/opportunities.jsonl", ReviewOpportunity
    )
    investigation_tasks = load_jsonl(
        DEFAULT_CANONICAL_RELEASE / "derived/investigation_tasks.jsonl", InvestigationTask
    )
    relations = load_jsonl(DEFAULT_PHASE2 / "derived/pr_relations.jsonl", PRRelation)
    links = link_candidates(
        candidates,
        production_opportunities=production_opportunities,
        oracle_opportunities=oracle_opportunities,
        investigation_tasks=investigation_tasks,
        relations=relations,
    )
    accepted = accepted_opportunity_ids(decisions, consensus)
    scores = {
        item.opportunity_id: (
            10.0 if item.request_force == "blocking" else 5.0
        ) + len(item.evidence_artifact_ids) / 100.0
        for item in decisions if item.review_worthiness == "request"
    }
    scores.update({item.opportunity_id: 10.0 for item in consensus if item.final_worthiness == "request"})
    findings, synthesis_decisions = synthesize_findings(
        candidates, links, accepted, relations, scores
    )
    projections = project_semantic_matches(findings, matches)
    residual = schedule_residual_reviews(graphs, oracle_opportunities, findings)
    accepted_candidates = {
        link.candidate_id for link in links if link.opportunity_id in accepted
    }
    before_issue = {
        item.obligation_id for item in matches
        if item.candidate_id in accepted_candidates and item.issue_match
    }
    after_issue = {item.obligation_id for item in projections if item.issue_match}
    control_prs = {
        item.pr_number for item in oracle_opportunities if item.selection_provenance == "matched_control"
    }
    action_sites = [(item.pr_number, item.action_key, tuple(item.change_ids)) for item in findings]
    report = {
        "schema_version": "phase8-synthesis-gate-report1",
        "synthesis_version": SYNTHESIS_VERSION,
        "counts": {
            "candidates": len(candidates),
            "accepted_candidates": len(accepted_candidates),
            "links": len(links),
            "findings": len(findings),
            "synthesis_decisions": len(synthesis_decisions),
            "match_projections": len(projections),
            "residual_passes": len(residual),
        },
        "gates": {
            "supported_issue_matches_retained": before_issue == after_issue,
            "exact_duplicate_findings": len(action_sites) == len(set(action_sites)),
            "control_findings": sum(item.pr_number in control_prs for item in findings),
            "all_findings_have_complete_lineage": all(
                item.source_candidate_ids and item.source_opportunity_ids
                and item.evidence_artifact_ids and item.anchors
                for item in findings
            ),
            "residual_pass_scheduled_for_both_prs": len(residual) == 2,
        },
        "issue_matched_obligations_before": sorted(before_issue),
        "issue_matched_obligations_after": sorted(after_issue),
        "finding_ids": [item.finding_id for item in findings],
    }
    report["complete"] = (
        report["gates"]["supported_issue_matches_retained"]
        and report["gates"]["exact_duplicate_findings"]
        and report["gates"]["control_findings"] == 0
        and report["gates"]["all_findings_have_complete_lineage"]
        and report["gates"]["residual_pass_scheduled_for_both_prs"]
    )
    return {
        "candidate_opportunity_links": links,
        "synthesized_findings": findings,
        "synthesis_decisions": synthesis_decisions,
        "match_projections": projections,
        "residual_review_passes": residual,
    }, report


def write_gate(out: Path = DEFAULT_OUT) -> dict:
    first, report = build_gate_artifacts()
    second, second_report = build_gate_artifacts()
    byte_stable = all(jsonl_bytes(first[key]) == jsonl_bytes(second[key]) for key in first)
    report["gates"]["byte_stable_replay"] = byte_stable and report == second_report
    report["complete"] = report["complete"] and report["gates"]["byte_stable_replay"]
    for name, rows in first.items():
        write_once(out / f"{name}.jsonl", jsonl_bytes(rows))
    write_once(out / "report.json", pretty_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(write_gate(args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
