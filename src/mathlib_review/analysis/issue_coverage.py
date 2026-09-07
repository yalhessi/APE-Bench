"""Pair issues to obligations at site granularity, keeping the finding view underneath.

The evaluation used to ask a boolean question — does any prediction touch any of this
obligation's change targets? Two things make that the wrong question now.

**It saturates by enumeration.** Every arm is scheduled over the whole change graph, so the
scheduled sites already intersect 37 of 40 medium obligations. An arm that emitted one
non-empty claim per scheduled site would score ~0.93 "location recall" with no review skill
at all. A boolean cannot distinguish that from understanding.

**Obligations are multi-site.** 8 of 43 name more than one change target and one names 19.
Against a 19-target ask, touching one target and touching all nineteen are very different
outcomes, and a boolean calls them both `True`.

So coverage is graded, and reported from both directions, because they fail differently:

* `obligation_coverage` — the share of the ask's targets the issue reached. Low means we saw
  part of the problem.
* `issue_specificity` — the share of the issue's targets the ask actually named. Low means we
  asked for more than was wanted, which a recall-only view scores as success.

Neither replaces semantic judging. Both are still *location* measures: they say an issue
landed on the right targets, never that it asked for the right thing. `semantic.issue_match`
remains the headline.

The finding view is kept because an issue is an aggregate: when an issue partially covers an
obligation, the useful question is *which of its member findings* landed and which did not,
and that is only answerable below the issue.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

COVERAGE_VERSION = "issue-coverage/1"


@dataclass(frozen=True)
class IssueCoverage:
    """How one issue relates to one obligation, at site granularity."""

    obligation_id: str
    issue_id: str
    pr_number: int
    obligation_sites: int
    issue_sites: int
    matched_sites: int
    #: Share of the obligation's targets this issue reached.
    obligation_coverage: float
    #: Share of this issue's targets the obligation actually named.
    issue_specificity: float
    #: The finding view of a partial match: which members landed, which did not.
    matched_finding_ids: Tuple[str, ...] = ()
    unmatched_finding_ids: Tuple[str, ...] = ()

    @property
    def is_full(self) -> bool:
        return self.matched_sites == self.obligation_sites and self.obligation_sites > 0

    @property
    def is_partial(self) -> bool:
        return 0 < self.matched_sites < self.obligation_sites


def _finding_sites(issue, findings_by_id) -> Dict[str, set]:
    """change_ids per member finding, so a partial match can be attributed."""

    sites = {}
    for finding_id in issue.finding_ids:
        finding = findings_by_id.get(finding_id)
        sites[finding_id] = set(finding.change_ids) if finding is not None else set()
    return sites


def pair_issues(
    obligations: Sequence,
    issues: Sequence,
    findings: Iterable = (),
    *,
    published_only: bool = True,
) -> List[IssueCoverage]:
    """Every (obligation, issue) pair that shares at least one change target.

    Deliberately many-to-many. One issue may cover several obligations and one obligation may
    need several issues; forcing a single best pair would hide exactly the partial structure
    this exists to expose.
    """

    findings_by_id = {item.finding_id: item for item in findings}
    scoped = [
        item for item in issues
        if not published_only or item.admission == "published"
    ]
    by_pr = defaultdict(list)
    for issue in scoped:
        by_pr[issue.pr_number].append(issue)

    rows: List[IssueCoverage] = []
    for obligation in obligations:
        gold = set(obligation.change_ids or [])
        if not gold:
            continue
        for issue in by_pr.get(getattr(obligation, "pr_number", None) or 0, []) or []:
            predicted = set(issue.change_ids)
            matched = gold & predicted
            if not matched:
                continue
            sites = _finding_sites(issue, findings_by_id)
            rows.append(IssueCoverage(
                obligation_id=obligation.obligation_id,
                issue_id=issue.issue_id,
                pr_number=issue.pr_number,
                obligation_sites=len(gold),
                issue_sites=len(predicted),
                matched_sites=len(matched),
                obligation_coverage=len(matched) / len(gold),
                issue_specificity=len(matched) / len(predicted) if predicted else 0.0,
                matched_finding_ids=tuple(sorted(
                    fid for fid, s in sites.items() if s & gold
                )),
                unmatched_finding_ids=tuple(sorted(
                    fid for fid, s in sites.items() if s and not (s & gold)
                )),
            ))
    return rows


def coverage_report(
    obligations: Sequence,
    issues: Sequence,
    findings: Iterable = (),
    *,
    published_only: bool = True,
) -> Dict:
    """Graded coverage from both directions, with the partial matches enumerated."""

    findings = list(findings)
    rows = pair_issues(obligations, issues, findings, published_only=published_only)
    published = [
        item for item in issues
        if not published_only or item.admission == "published"
    ]

    best: Dict[str, IssueCoverage] = {}
    union_matched: Dict[str, set] = defaultdict(set)
    obligation_sites = {}
    for obligation in obligations:
        gold = set(obligation.change_ids or [])
        if gold:
            obligation_sites[obligation.obligation_id] = gold
    for row in rows:
        current = best.get(row.obligation_id)
        if current is None or row.obligation_coverage > current.obligation_coverage:
            best[row.obligation_id] = row

    # Union coverage: several issues may jointly satisfy one multi-site obligation, and
    # scoring only the best single issue would understate a system that split the ask.
    issue_by_id = {item.issue_id: item for item in published}
    for row in rows:
        issue = issue_by_id.get(row.issue_id)
        if issue is not None:
            union_matched[row.obligation_id] |= (
                obligation_sites[row.obligation_id] & set(issue.change_ids)
            )

    total = len(obligation_sites)
    full = sum(
        1 for oid, gold in obligation_sites.items()
        if len(union_matched.get(oid, set())) == len(gold)
    )
    partial = sum(
        1 for oid, gold in obligation_sites.items()
        if 0 < len(union_matched.get(oid, set())) < len(gold)
    )
    touched = full + partial
    matched_issue_ids = {row.issue_id for row in rows}
    spurious = [item for item in published if item.issue_id not in matched_issue_ids]

    mean_coverage = (
        sum(len(union_matched.get(oid, set())) / len(gold)
            for oid, gold in obligation_sites.items()) / total
        if total else None
    )
    specificities = [row.issue_specificity for row in rows]
    return {
        "coverage_version": COVERAGE_VERSION,
        "warning": (
            "Site coverage is a location measure. An issue landing on the right targets is "
            "not an issue asking for the right thing; semantic.issue_match remains the "
            "headline."
        ),
        "obligations": total,
        "issues_published": len(published),
        # The boolean the old metric reported, kept so the graded view can be compared to it.
        "obligations_touched": touched,
        "location_issue_recall": touched / total if total else None,
        "obligations_fully_covered": full,
        "obligations_partially_covered": partial,
        "obligations_uncovered": total - touched,
        "full_site_coverage_rate": full / total if total else None,
        "mean_obligation_coverage": mean_coverage,
        "mean_issue_specificity": (
            sum(specificities) / len(specificities) if specificities else None
        ),
        "issues_matching_no_obligation": len(spurious),
        "issue_pairs": len(rows),
        "partial_matches": [
            {
                "obligation_id": oid,
                "obligation_sites": len(gold),
                "matched_sites": len(union_matched.get(oid, set())),
                "coverage": len(union_matched.get(oid, set())) / len(gold),
                "issues": sorted(
                    row.issue_id for row in rows if row.obligation_id == oid
                ),
                "matched_findings": sorted({
                    fid for row in rows if row.obligation_id == oid
                    for fid in row.matched_finding_ids
                }),
                "unmatched_findings": sorted({
                    fid for row in rows if row.obligation_id == oid
                    for fid in row.unmatched_finding_ids
                }),
            }
            for oid, gold in sorted(obligation_sites.items())
            if 0 < len(union_matched.get(oid, set())) < len(gold)
        ],
    }
