"""Digest site-level findings into the issues a maintainer would actually receive.

Every arm reviews *sites* — one change target at a time — because that is what makes
scheduling enumerable and gold-free. Maintainers do not write per-site comments. Measured on
medium, 8 of 43 gold obligations name more than one change target, and PR 33149's names
**19**: *"remove the newly introduced axioms ... so the file adds no new axioms."* Against
that single ask the deterministic arm emitted 19 separate findings, one per axiom.

That mismatch is not cosmetic. It costs three measurable things:

* **Budget** — 19 of that PR's 20 publication slots restating one issue.
* **Alignment** — 19 published items scored against 1 maintainer ask.
* **Displacement** — a per-PR limit sorted by evidence tier lets one over-emitting method
  crowd out every other arm's output on that PR.

This phase runs *after* the merge and *before* the publication limit, so the limit applies to
issues rather than to findings. It is arm-blind by construction: the grouping key names no
arm, so two arms that produced instances of one pattern digest together. Solving it here is
the point — an arm that aggregated privately would be re-deriving cross-site structure for
itself and leaving the cross-*arm* case unsolved.

## Why aggregation is declared per method rather than inferred from text

The tempting rule is "same requested change modulo the subject". It over-collapses. Measured
against gold:

* PR 33149 — 19 `repository_policy` findings, gold obligation of 19 change_ids. Collapsing is
  **right**: one policy is violated, and one fix satisfies it.
* PR 33294 — 5 `baseline_failure` findings, gold has **two obligations of one change_id
  each**. Collapsing would be **wrong**: five compile errors are five independent defects
  needing five independent fixes.

Both look identical to a text rule — a fixed template varying only in the subject. What
separates them is whether the fix is *one action or N*, which is a property of what the
method checks, not of how it words its output. So the method declares it, the default is the
conservative `per_site`, and a method opts in with a stated reason.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from src.mathlib_review.io import sealed_model
from src.mathlib_review.schema import ARMS, ReviewFinding, ReviewIssue, evidence_rank

DIGEST_VERSION = "site-to-issue-digest/1"

#: Method -> how its findings aggregate. Absent means `per_site`, the conservative default.
#:
#: `repository_policy.v1` is the only opt-in today, and the gold obligation it matches carries
#: exactly the 19 change_ids it fires on. A policy is a property of the file — "this file
#: introduces axioms" — so its instances are one violation with many sites, and one remedy
#: discharges all of them.
#:
#: `baseline_failure.v1` deliberately stays `per_site` despite an equally templated message:
#: gold records PR 33294's compile errors as separate obligations, because fixing one proves
#: nothing about the others.
AGGREGATION_BY_METHOD: Dict[str, str] = {
    "repository_policy.v1": "per_pattern",
}


def _identifier_boundary(term: str) -> re.Pattern:
    """Match `term` only as a whole identifier.

    Without the boundaries, masking the subject `card_foo` inside "rename `card_foo` to
    `encard_foo`" also rewrites the *target* name, and two findings proposing different
    renames collapse into one. The same boundary rule `evidence.declares_identifier` uses.
    """

    return re.compile(
        r"(?<![A-Za-z0-9_'])" + re.escape(term) + r"(?![A-Za-z0-9_'])"
    )


def mask_subject(text: str, subject: Optional[str], *, normalize: bool = True) -> str:
    """Replace a finding's own subject with a placeholder, so instances compare equal.

    Both the full name and its leaf are masked, longest first — a claim may cite either
    `Set.encard_foo` or `encard_foo`, and masking the leaf first would leave `Set.<subject>`
    unequal to `<subject>`.

    `normalize=True` also case-folds and collapses whitespace, which is right for a grouping
    key and wrong for anything a maintainer reads. `normalize=False` returns the masked text
    with its original casing, for publishing a pattern issue.
    """

    if not text:
        return ""
    if subject:
        terms = sorted({subject, subject.rsplit(".", 1)[-1]}, key=len, reverse=True)
        for term in terms:
            if term:
                text = _identifier_boundary(term).sub("<subject>", text)
    if not normalize:
        return text.strip()
    return re.sub(r"\s+", " ", text.strip().lower())


def _methods(finding: ReviewFinding) -> List[str]:
    return sorted({
        source.method_id for source in finding.sources if source.method_id
    })


def aggregation_for(finding: ReviewFinding) -> str:
    """How this finding aggregates, from the method that produced it.

    A finding merged from several sources aggregates per pattern only if *every* method
    behind it says so: mixing an independent defect into a pattern issue would hide it.
    Model arms carry no method and take the conservative default.
    """

    methods = _methods(finding)
    if not methods:
        return "per_site"
    modes = {AGGREGATION_BY_METHOD.get(item, "per_site") for item in methods}
    return "per_pattern" if modes == {"per_pattern"} else "per_site"


def _issue_key(finding: ReviewFinding) -> Tuple:
    """The identity of the issue a finding belongs to.

    Contains no arm and no `change_id`: findings from different arms at different sites are
    exactly what this phase exists to unify. `per_site` findings key on their own finding ID,
    so they pass through as singleton issues rather than being grouped with anything.
    """

    if aggregation_for(finding) != "per_pattern":
        return (finding.pr_number, "per_site", finding.finding_id)
    return (
        finding.pr_number,
        "per_pattern",
        finding.concern_family,
        finding.issue_kind,
        mask_subject(finding.requested_change, finding.primary_subject),
    )


def _representative(group: Sequence[ReviewFinding]) -> ReviewFinding:
    """The member whose wording survives.

    Strongest evidence first, then the stable finding ID. Never `model_confidence`, which has
    been falsified three times as a ranking signal. The text is *chosen*, never synthesised:
    a digest that rewrote the ask would publish words no arm actually produced and no
    evidence backs.
    """

    return max(group, key=lambda item: (evidence_rank(item.evidence_tier), item.finding_id))


def _issue_from_group(group: Sequence[ReviewFinding]) -> ReviewIssue:
    best = _representative(group)
    aggregation = aggregation_for(best) if len(group) > 1 else "per_site"
    change_ids = sorted({cid for item in group for cid in item.change_ids})
    subjects = sorted({item.primary_subject for item in group if item.primary_subject})
    published = any(item.admission == "published" for item in group)
    claim, requested = best.claim, best.requested_change
    if len(group) > 1 and aggregation == "per_pattern":
        # The representative names one of N subjects; published unchanged it would read as a
        # request about `cMoser` alone while standing for nineteen. Masking is not a
        # synthesis — it is the members' own shared wording with the varying part removed,
        # and `primary_subjects` carries every subject the issue covers.
        claim = mask_subject(claim, best.primary_subject, normalize=False)
        requested = mask_subject(requested, best.primary_subject, normalize=False)
        reason = (
            f"{len(group)} findings are instances of one {best.concern_family} pattern; "
            f"published as a single issue covering {len(change_ids)} targets"
        )
    elif len(group) > 1:
        reason = (
            f"{len(group)} findings merged at one anchor; "
            f"covering {len(change_ids)} targets"
        )
    else:
        reason = best.admission_reason
    draft = sealed_model(
        ReviewIssue,
        issue_id="",
        pr_number=best.pr_number,
        episode_id=best.episode_id,
        concern_family=best.concern_family,
        issue_kind=best.issue_kind,
        change_ids=change_ids,
        primary_change_id=best.primary_change_id,
        primary_subjects=subjects,
        severity=("blocking" if any(item.severity == "blocking" for item in group)
                  else "advisory"),
        claim=claim,
        requested_change=requested,
        proposed_edit=best.proposed_edit,
        evidence_tier=best.evidence_tier,
        admission="published" if published else "diagnostic",
        admission_reason=reason,
        finding_ids=sorted(item.finding_id for item in group),
        arms=sorted({item.arm for item in group}),
        aggregation=aggregation,
        site_count=len(change_ids),
    )
    return draft.model_copy(update={"issue_id": f"issue:{draft.source_sha256[:24]}"})


def digest_findings(
    findings: Iterable[ReviewFinding],
    *,
    pr_finding_limit: Optional[int] = None,
) -> Tuple[List[ReviewIssue], Dict]:
    """Group findings into issues, then apply the publication limit to *issues*.

    The limit belongs here rather than in the merge, because a limit applied to findings
    counts one pattern nineteen times against a budget of twenty.
    """

    findings = list(findings)
    grouped: Dict[Tuple, List[ReviewFinding]] = defaultdict(list)
    for finding in findings:
        grouped[_issue_key(finding)].append(finding)
    issues = sorted(
        (_issue_from_group(group) for _key, group in sorted(grouped.items())),
        key=lambda item: (
            item.pr_number,
            -evidence_rank(item.evidence_tier),
            0 if item.severity == "blocking" else 1,
            item.issue_id,
        ),
    )

    published_before = sum(item.admission == "published" for item in issues)
    if pr_finding_limit is not None:
        per_pr: Dict[int, int] = defaultdict(int)
        limited = []
        for issue in issues:
            if issue.admission == "published":
                if per_pr[issue.pr_number] >= pr_finding_limit:
                    issue = issue.model_copy(update={
                        "admission": "diagnostic",
                        "admission_reason": (
                            f"per-PR publication limit of {pr_finding_limit} reached"
                        ),
                    })
                else:
                    per_pr[issue.pr_number] += 1
            limited.append(issue)
        issues = limited
    published_after = sum(item.admission == "published" for item in issues)

    collapsed = [item for item in issues if item.site_count > 1 and len(item.finding_ids) > 1]
    report = {
        "digest_version": DIGEST_VERSION,
        "findings_in": len(findings),
        "issues_out": len(issues),
        "issues_collapsing_several_findings": len(collapsed),
        "findings_absorbed": sum(len(item.finding_ids) for item in collapsed),
        "published_before_limit": published_before,
        "published_after_limit": published_after,
        "suppressed_by_limit": published_before - published_after,
        "pr_finding_limit": pr_finding_limit,
        "by_aggregation": {
            mode: sum(item.aggregation == mode for item in issues)
            for mode in ("per_site", "per_pattern")
        },
        "by_arm": {
            arm: sum(arm in item.arms for item in issues) for arm in ARMS
        },
        "largest_issue_sites": max((item.site_count for item in issues), default=0),
    }
    return issues, report
