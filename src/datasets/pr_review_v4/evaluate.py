"""Transparent v4 funnel metrics over stable change and obligation IDs."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Optional

from .io import pretty_json_bytes, write_once
from .schema import (
    CandidateClaim,
    EvidenceAssertion,
    EvidencePacket,
    InterventionView,
    JudgmentNode,
    PilotCase,
    SelectedFinding,
    SemanticMatch,
    ReviewWorkUnit,
)
from .issue_coverage import coverage_report
from .semantic_judge import semantic_report


def _covered(obligation, predictions) -> bool:
    gold = set(obligation.change_ids)
    return bool(gold) and any(gold.intersection(item.change_ids) for item in predictions)


def evaluate_funnel(judgments: Iterable[JudgmentNode], views: Iterable[InterventionView],
                    candidates: Iterable[CandidateClaim], findings: Iterable[SelectedFinding],
                    pilot_cases: Iterable[PilotCase],
                    pr_numbers: Optional[Iterable[int]] = None,
                    scoped_change_ids: Optional[Iterable[str]] = None,
                    issues: Optional[Iterable] = None,
                    merged_findings: Optional[Iterable] = None) -> Dict:
    judgments, views = list(judgments), list(views)
    candidates, findings, cases = list(candidates), list(findings), list(pilot_cases)
    scoped_prs = set(pr_numbers) if pr_numbers is not None else None
    if scoped_prs is not None:
        judgments = [item for item in judgments if item.pr_number in scoped_prs]
        judgment_ids = {item.judgment_id for item in judgments}
        views = [item for item in views if set(item.judgment_ids) <= judgment_ids]
        candidates = [item for item in candidates if item.pr_number in scoped_prs]
        findings = [item for item in findings if item.pr_number in scoped_prs]
        cases = [item for item in cases if item.pr_number in scoped_prs]
    eligible_views = [v for v in views if v.evaluation_eligibility == "included"]
    eligible_obligation_ids = {
        obligation_id for view in eligible_views for obligation_id in view.obligation_ids
    }
    obligations = [
        obligation for judgment in judgments for obligation in judgment.obligations
        if obligation.status == "proposed_atomic"
        and obligation.obligation_id in eligible_obligation_ids
    ]
    change_scope = set(scoped_change_ids) if scoped_change_ids is not None else None
    if change_scope is not None:
        obligations = [
            item for item in obligations if set(item.change_ids).intersection(change_scope)
        ]
    scoped_obligation_ids = {item.obligation_id for item in obligations}
    eligible_views = [
        item for item in eligible_views
        if set(item.obligation_ids).intersection(scoped_obligation_ids)
    ]
    issues = [item for item in (issues or [])
              if scoped_prs is None or item.pr_number in scoped_prs]
    merged_findings = [item for item in (merged_findings or [])
                       if scoped_prs is None or item.pr_number in scoped_prs]
    candidate_hits = {o.obligation_id: _covered(o, candidates) for o in obligations}
    finding_hits = {o.obligation_id: _covered(o, findings) for o in obligations}
    full_candidate = {v.view_id: all(
        candidate_hits[item] for item in v.obligation_ids if item in scoped_obligation_ids
    )
                      for v in eligible_views}
    full_selected = {v.view_id: all(
        finding_hits[item] for item in v.obligation_ids if item in scoped_obligation_ids
    )
                     for v in eligible_views}
    by_pr = defaultdict(list)
    for finding in findings:
        by_pr[finding.pr_number].append(finding)
    controls = [case for case in cases if case.case_kind == "control"]
    positives = [case for case in cases if case.case_kind == "intervention"]
    return {
        "schema_version": "v4-evaluation1",
        "evaluated_pr_numbers": sorted(scoped_prs) if scoped_prs is not None else None,
        "scoped_change_ids": sorted(change_scope) if change_scope is not None else None,
        "warning": "Change-scope hits measure location recall, not semantic issue/resolution correctness.",
        "counts": {"obligations": len(obligations), "eligible_interventions": len(eligible_views),
                   "candidates": len(candidates), "selected_findings": len(findings),
                   "intervention_prs": len(positives), "control_prs": len(controls)},
        "location_candidate_recall": sum(candidate_hits.values()) / len(candidate_hits) if candidate_hits else None,
        "location_selected_recall": sum(finding_hits.values()) / len(finding_hits) if finding_hits else None,
        "full_intervention_candidate_recall": sum(full_candidate.values()) / len(full_candidate) if full_candidate else None,
        "full_intervention_selected_recall": sum(full_selected.values()) / len(full_selected) if full_selected else None,
        "control_false_finding_rate": sum(bool(by_pr[c.pr_number]) for c in controls) / len(controls) if controls else None,
        "findings_per_control_pr": sum(len(by_pr[c.pr_number]) for c in controls) / len(controls) if controls else None,
        "abstention": {
            "intervention_prs": sum(not by_pr[c.pr_number] for c in positives) / len(positives) if positives else None,
            "control_prs": sum(not by_pr[c.pr_number] for c in controls) / len(controls) if controls else None,
        },
        # The unit the system actually publishes, and the unit gold is written in:
        # `obligation.change_ids` is multi-site, so an issue is directly comparable while a
        # per-site finding is not. The finding view is retained beneath it, not replaced —
        # a partially covered issue is only explicable in terms of which members landed.
        "issue_coverage": (
            coverage_report(obligations, issues, merged_findings) if issues else None
        ),
        "semantic_scoring_status": "not_attached",
        "evidence_support_precision_status": "human_audit_required",
    }


def attach_scored_views(
    report: Dict,
    judgments: Iterable[JudgmentNode],
    views: Iterable[InterventionView],
    candidates: Iterable[CandidateClaim],
    findings: Iterable[SelectedFinding],
    matches: Iterable[SemanticMatch],
    packets: Iterable[EvidencePacket],
    assertions: Iterable[EvidenceAssertion],
    scoped_change_ids: Optional[Iterable[str]] = None,
) -> Dict:
    """Attach semantic and evidence dispositions without conflating their metrics."""
    judgments, views = list(judgments), list(views)
    candidates, findings, matches = list(candidates), list(findings), list(matches)
    packets, assertions = list(packets), list(assertions)
    semantic = semantic_report(judgments, views, candidates, matches, scoped_change_ids)
    finding_candidate_ids = {item.candidate_id for item in findings}
    selected_matches = [item for item in matches if item.candidate_id in finding_candidate_ids]
    selected_paired = {item.candidate_id for item in selected_matches}
    selected_issue = {item.candidate_id for item in selected_matches if item.issue_match}
    packet_statuses = defaultdict(int)
    for packet in packets:
        packet_statuses[packet.status] += 1
    assertion_polarities = defaultdict(int)
    for assertion in assertions:
        assertion_polarities[assertion.polarity] += 1
    return {
        **report,
        "semantic_scoring_status": "attached",
        "semantic": semantic,
        "selected_paired_issue_precision": (
            len(selected_issue) / len(selected_paired) if selected_paired else None
        ),
        "evidence": {
            "packets": len(packets),
            "packet_status": dict(sorted(packet_statuses.items())),
            "assertions": len(assertions),
            "assertion_polarity": dict(sorted(assertion_polarities.items())),
            "complete_packet_rate": (
                sum(item.status != "incomplete" for item in packets) / len(packets)
                if packets else None
            ),
            "support_precision_status": "human_audit_required",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--views", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--pilot-cases", type=Path, required=True)
    parser.add_argument("--issues", type=Path,
                        help="the condition's issues.jsonl — the unit the system publishes "
                             "and the unit gold is written in, since obligation.change_ids "
                             "is multi-site")
    parser.add_argument("--merged-findings", type=Path,
                        help="the condition's findings.jsonl, kept as the view beneath "
                             "issues so a partial match can name which members landed")
    parser.add_argument("--pr-numbers", type=int, nargs="*",
                        help="Restrict gold and predictions to an explicitly executed smoke subset")
    parser.add_argument("--semantic-matches", type=Path)
    parser.add_argument("--packets", type=Path)
    parser.add_argument("--assertions", type=Path)
    parser.add_argument("--work-units", type=Path)
    parser.add_argument("--work-unit-ids", nargs="*")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    def load(path, cls):
        return [cls.model_validate_json(x) for x in path.read_text().splitlines() if x]
    judgments = load(args.judgments, JudgmentNode)
    views = load(args.views, InterventionView)
    candidates = load(args.candidates, CandidateClaim)
    findings = load(args.findings, SelectedFinding)
    scoped_change_ids = None
    if args.work_unit_ids:
        if args.work_units is None:
            raise ValueError("--work-unit-ids requires --work-units")
        wanted_units = set(args.work_unit_ids)
        units = [
            item for item in load(args.work_units, ReviewWorkUnit)
            if item.work_unit_id in wanted_units
        ]
        missing_units = wanted_units - {item.work_unit_id for item in units}
        if missing_units:
            raise ValueError(f"unknown work-unit IDs: {sorted(missing_units)}")
        scoped_change_ids = {change_id for item in units for change_id in item.change_ids}
    from .schema import ReviewFinding, ReviewIssue

    issues = load(args.issues, ReviewIssue) if args.issues else None
    merged_findings = (
        load(args.merged_findings, ReviewFinding) if args.merged_findings else None
    )
    if issues and merged_findings is None:
        # Not fatal, but a partial match would then be unattributable to its members, which
        # is the reason the finding view is kept at all.
        print("note: --issues without --merged-findings; partial matches will not name "
              "which member findings landed", file=sys.stderr)
    report = evaluate_funnel(
        judgments, views, candidates, findings, load(args.pilot_cases, PilotCase),
        args.pr_numbers, scoped_change_ids, issues=issues, merged_findings=merged_findings,
    )
    scored_paths = (args.semantic_matches, args.packets, args.assertions)
    if any(scored_paths) and not all(scored_paths):
        raise ValueError("semantic matches, packets, and assertions must be supplied together")
    if all(scored_paths):
        if args.pr_numbers:
            wanted = set(args.pr_numbers)
            judgments = [item for item in judgments if item.pr_number in wanted]
            judgment_ids = {item.judgment_id for item in judgments}
            views = [item for item in views if set(item.judgment_ids) <= judgment_ids]
            candidates = [item for item in candidates if item.pr_number in wanted]
            findings = [item for item in findings if item.pr_number in wanted]
        report = attach_scored_views(
            report, judgments, views, candidates, findings,
            load(args.semantic_matches, SemanticMatch),
            load(args.packets, EvidencePacket),
            load(args.assertions, EvidenceAssertion),
            scoped_change_ids,
        )
    write_once(args.out, pretty_json_bytes(report))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
