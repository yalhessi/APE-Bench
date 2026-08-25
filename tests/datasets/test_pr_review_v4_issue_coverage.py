"""Graded, two-directional coverage of obligations by issues.

The boolean this replaces — "does any prediction touch any of the obligation's targets" —
fails in two directions at once. It saturates, because every arm is scheduled over the whole
change graph and the scheduled sites already intersect 37 of 40 medium obligations, so an arm
emitting one claim per site scores ~0.93 with no review skill. And it flattens multi-site
obligations, calling "touched 1 of 19" and "touched 19 of 19" both `True`.

Both directions are reported because they fail differently: low `obligation_coverage` means
we saw part of the problem, low `issue_specificity` means we asked for more than was wanted —
and a recall-only view scores the second as success.

The finding view survives underneath because an issue is an aggregate. When an issue partly
covers an obligation the useful question is *which members landed*, and that is unanswerable
at issue granularity.
"""

import pytest

from src.datasets.pr_review_v4.issue_coverage import coverage_report, pair_issues


class _Obligation:
    def __init__(self, obligation_id, pr_number, change_ids):
        self.obligation_id = obligation_id
        self.pr_number = pr_number
        self.change_ids = list(change_ids)


class _Issue:
    def __init__(self, issue_id, pr_number, change_ids, finding_ids=(),
                 admission="published"):
        self.issue_id = issue_id
        self.pr_number = pr_number
        self.change_ids = list(change_ids)
        self.finding_ids = list(finding_ids)
        self.admission = admission


class _Finding:
    def __init__(self, finding_id, pr_number, change_ids):
        self.finding_id = finding_id
        self.pr_number = pr_number
        self.change_ids = list(change_ids)


def test_a_multi_site_obligation_fully_covered_scores_one():
    """The case digestion exists for: 19 sites asked, 19 sites reached."""

    sites = [f"change:{i}" for i in range(19)]
    obligation = _Obligation("obligation:1", 1, sites)
    issue = _Issue("issue:1", 1, sites, [f"finding:{i}" for i in range(19)])
    findings = [_Finding(f"finding:{i}", 1, [f"change:{i}"]) for i in range(19)]

    row = pair_issues([obligation], [issue], findings)[0]
    assert row.matched_sites == 19
    assert row.obligation_coverage == 1.0
    assert row.issue_specificity == 1.0
    assert row.is_full and not row.is_partial
    assert len(row.matched_finding_ids) == 19


def test_touching_one_of_nineteen_is_not_the_same_as_covering_them():
    """The flattening the boolean caused."""

    gold = [f"change:{i}" for i in range(19)]
    obligation = _Obligation("obligation:1", 1, gold)
    issue = _Issue("issue:1", 1, ["change:0"], ["finding:0"])
    row = pair_issues([obligation], [issue], [_Finding("finding:0", 1, ["change:0"])])[0]
    assert row.is_partial
    assert row.obligation_coverage == pytest.approx(1 / 19)
    # Both would have been reported as a single `True` before.
    report = coverage_report([obligation], [issue])
    assert report["obligations_touched"] == 1
    assert report["obligations_fully_covered"] == 0
    assert report["obligations_partially_covered"] == 1


def test_specificity_catches_an_issue_broader_than_the_ask():
    """Recall alone scores an over-broad issue as a success."""

    obligation = _Obligation("obligation:1", 1, ["change:0"])
    issue = _Issue("issue:1", 1, [f"change:{i}" for i in range(19)])
    row = pair_issues([obligation], [issue])[0]
    assert row.obligation_coverage == 1.0
    assert row.issue_specificity == pytest.approx(1 / 19)


def test_a_partial_match_names_which_findings_landed():
    """The reason the finding view is kept beneath the issue view."""

    obligation = _Obligation("obligation:1", 1, ["change:a", "change:b"])
    issue = _Issue("issue:1", 1, ["change:a", "change:z"], ["finding:a", "finding:z"])
    findings = [
        _Finding("finding:a", 1, ["change:a"]),
        _Finding("finding:z", 1, ["change:z"]),
    ]
    row = pair_issues([obligation], [issue], findings)[0]
    assert row.is_partial
    assert row.matched_finding_ids == ("finding:a",)
    assert row.unmatched_finding_ids == ("finding:z",)

    report = coverage_report([obligation], [issue], findings)
    partial = report["partial_matches"][0]
    assert partial["matched_sites"] == 1
    assert partial["coverage"] == 0.5
    assert partial["matched_findings"] == ["finding:a"]
    assert partial["unmatched_findings"] == ["finding:z"]


def test_several_issues_can_jointly_satisfy_one_obligation():
    """Scoring only the best single issue would understate a system that split the ask."""

    obligation = _Obligation("obligation:1", 1, ["change:a", "change:b"])
    issues = [
        _Issue("issue:1", 1, ["change:a"]),
        _Issue("issue:2", 1, ["change:b"]),
    ]
    report = coverage_report([obligation], issues)
    assert report["obligations_fully_covered"] == 1
    assert report["obligations_partially_covered"] == 0
    assert report["mean_obligation_coverage"] == 1.0


def test_issues_matching_nothing_are_counted():
    """An arm that publishes freely must not look better for publishing more."""

    obligation = _Obligation("obligation:1", 1, ["change:a"])
    issues = [
        _Issue("issue:1", 1, ["change:a"]),
        _Issue("issue:2", 1, ["change:x"]),
        _Issue("issue:3", 1, ["change:y"]),
    ]
    report = coverage_report([obligation], issues)
    assert report["issues_matching_no_obligation"] == 2
    assert report["issues_published"] == 3


def test_diagnostic_issues_are_excluded_by_default():
    """Only published output is system output; counting diagnostics would inflate recall."""

    obligation = _Obligation("obligation:1", 1, ["change:a"])
    diagnostic = _Issue("issue:1", 1, ["change:a"], admission="diagnostic")
    assert pair_issues([obligation], [diagnostic]) == []
    assert pair_issues([obligation], [diagnostic], published_only=False)
    report = coverage_report([obligation], [diagnostic])
    assert report["obligations_touched"] == 0


def test_issues_never_pair_across_prs():
    obligation = _Obligation("obligation:1", 1, ["change:a"])
    issue = _Issue("issue:1", 2, ["change:a"])
    assert pair_issues([obligation], [issue]) == []


def test_an_obligation_with_no_sites_is_skipped_not_counted_as_missed():
    """One medium obligation carries zero change_ids; it cannot be located by construction."""

    obligation = _Obligation("obligation:1", 1, [])
    issue = _Issue("issue:1", 1, ["change:a"])
    report = coverage_report([obligation], [issue])
    assert report["obligations"] == 0
    assert report["location_issue_recall"] is None


def test_the_report_keeps_the_boolean_for_comparison():
    """The graded view must be comparable to the number it replaces, not silently swapped."""

    obligation = _Obligation("obligation:1", 1, ["change:a", "change:b"])
    issue = _Issue("issue:1", 1, ["change:a"])
    report = coverage_report([obligation], [issue])
    assert report["location_issue_recall"] == 1.0, "boolean: the obligation was touched"
    assert report["full_site_coverage_rate"] == 0.0, "graded: it was not covered"
    assert "location measure" in report["warning"]
