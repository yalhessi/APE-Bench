"""Digestion of site-level findings into maintainer-level issues.

The phase exists because the system's output unit did not match its evaluation unit. Gold
obligations are multi-site by construction — 8 of 43 on medium name more than one change
target, one names 19 — while every arm emits one finding per site. PR 33149 produced 19
findings against a single obligation, spending 19 of that PR's 20 publication slots.

The hard part is knowing when *not* to collapse. `repository_policy` and `baseline_failure`
emit textually identical templates varying only in the subject, but gold records the first as
one obligation of 19 change_ids and the second as separate obligations of one change_id each.
Five compile errors are five defects; nineteen axioms are one policy violation. No text rule
separates them, so the method declares it and the default is conservative.
"""

import pytest

from src.datasets.pr_review_v4.digest import (
    AGGREGATION_BY_METHOD,
    aggregation_for,
    digest_findings,
    mask_subject,
)
from src.datasets.pr_review_v4.merge import finding_from_opportunity
from src.datasets.pr_review_v4.schema import (
    ReviewOpportunity,
    WorthinessDecision,
    OpportunityTransformation,
)


def _decision(opportunity_id: str) -> WorthinessDecision:
    return WorthinessDecision(
        decision_id="decision:1", opportunity_id=opportunity_id,
        technical_assessment_id="assessment:1", evidence_artifact_ids=["artifact:1"],
        producer="policy", review_worthiness="request", request_force="advisory",
        rationale="x", source_sha256="0" * 64,
    )


def _finding(method_id, subject, change_id, *, pr_number=1, family="correctness",
             description=None, tier="lexical_rule"):
    opportunity = ReviewOpportunity(
        opportunity_id=f"opportunity:{subject}",
        investigation_id="investigation:1", method_id=method_id,
        episode_id="ep:1", pr_number=pr_number, primary_change_id=change_id,
        related_change_ids=[], observed_pattern=f"`{subject}` introduces a new `axiom`.",
        proposed_transformation=OpportunityTransformation(
            kind="remove_declaration",
            description=description or (
                f"Remove `{subject}` and derive the result instead, so the file "
                "introduces no `axiom`."
            ),
            symbols=[subject],
        ),
        source_artifact_ids=["artifact:1"], discovery_rank=1, source_sha256="0" * 64,
    )
    return finding_from_opportunity(
        opportunity, _decision(opportunity.opportunity_id),
        concern_family=family, evidence_tier=tier,
    )


def test_masking_respects_identifier_boundaries():
    """`card_foo` must not be masked inside `encard_foo`, or two renames become one issue."""

    text = "rename `card_foo` to `encard_foo`"
    masked = mask_subject(text, "card_foo")
    assert masked == "rename `<subject>` to `encard_foo`"
    # The full name and the leaf both mask, longest first.
    assert mask_subject("drop Set.card_foo", "Set.card_foo") == "drop <subject>"
    assert mask_subject("drop card_foo", "Set.card_foo") == "drop <subject>"


def test_masking_for_display_keeps_the_original_casing():
    """A grouping key wants case-folding; a maintainer-facing string does not."""

    text = "Remove `Foo` and derive the result"
    assert mask_subject(text, "Foo", normalize=False) == "Remove `<subject>` and derive the result"
    assert mask_subject(text, "Foo") == "remove `<subject>` and derive the result"


def test_a_policy_violation_collapses_to_one_issue():
    """19 axioms are one policy violation; gold records exactly that, with 19 change_ids."""

    findings = [
        _finding("repository_policy.v1", f"axiom_{index}", f"change:{index}")
        for index in range(19)
    ]
    issues, report = digest_findings(findings)
    assert len(issues) == 1
    issue = issues[0]
    assert issue.aggregation == "per_pattern"
    assert issue.site_count == 19
    assert sorted(issue.change_ids) == sorted(f"change:{i}" for i in range(19))
    assert len(issue.primary_subjects) == 19
    assert report["findings_absorbed"] == 19


def test_independent_defects_do_not_collapse():
    """The case a text rule gets wrong: same template, five separate obligations in gold."""

    findings = [
        _finding("baseline_failure.v1", f"lemma_{index}", f"change:{index}")
        for index in range(5)
    ]
    issues, _report = digest_findings(findings)
    assert len(issues) == 5, (
        "five compile errors are five defects; fixing one proves nothing about the others"
    )
    assert all(item.aggregation == "per_site" for item in issues)


def test_the_default_is_per_site():
    """A method absent from the table must not aggregate by accident."""

    assert "baseline_failure.v1" not in AGGREGATION_BY_METHOD
    unknown = _finding("some_new_method.v1", "foo", "change:1")
    assert aggregation_for(unknown) == "per_site"
    findings = [
        _finding("some_new_method.v1", f"foo_{i}", f"change:{i}") for i in range(3)
    ]
    issues, _r = digest_findings(findings)
    assert len(issues) == 3


def test_a_pattern_issue_publishes_the_masked_ask_not_one_arbitrary_subject():
    """Otherwise the headline names `axiom_0` while standing for nineteen."""

    findings = [
        _finding("repository_policy.v1", f"axiom_{index}", f"change:{index}")
        for index in range(19)
    ]
    issues, _report = digest_findings(findings)
    issue = issues[0]
    assert "<subject>" in issue.requested_change
    assert not any(f"axiom_{i}`" in issue.requested_change for i in range(19))
    # The subjects are not lost — they move to the field that can hold all of them.
    assert len(issue.primary_subjects) == 19


def test_different_asks_stay_separate_even_under_one_method():
    """Aggregation is per pattern, not per method: two policies are two issues."""

    findings = [
        _finding("repository_policy.v1", "a", "change:1"),
        _finding("repository_policy.v1", "b", "change:2"),
        _finding("repository_policy.v1", "c", "change:3",
                 description="Remove the `sorry` in `c` and finish the proof."),
    ]
    issues, _report = digest_findings(findings)
    assert len(issues) == 2
    assert sorted(item.site_count for item in issues) == [1, 2]


def test_findings_in_different_prs_never_digest_together():
    findings = [
        _finding("repository_policy.v1", "a", "change:1", pr_number=1),
        _finding("repository_policy.v1", "b", "change:2", pr_number=2),
    ]
    issues, _report = digest_findings(findings)
    assert len(issues) == 2


def test_the_publication_limit_applies_to_issues_not_findings():
    """The whole point: one 19-site pattern must cost one slot, not nineteen."""

    findings = [
        _finding("repository_policy.v1", f"axiom_{index}", f"change:{index}")
        for index in range(19)
    ]
    findings += [
        _finding("baseline_failure.v1", f"broken_{index}", f"change:b{index}")
        for index in range(4)
    ]
    issues, report = digest_findings(findings, pr_finding_limit=5)
    published = [item for item in issues if item.admission == "published"]
    assert len(published) == 5
    assert report["suppressed_by_limit"] == 0, (
        "23 findings became 5 issues, so nothing should hit the limit"
    )
    # Without digestion those 19 findings alone would have exhausted a limit of 5.
    assert any(item.site_count == 19 for item in published)


def test_the_issue_key_names_no_arm():
    """Cross-arm unification is the reason this phase exists rather than living in an arm."""

    import ast
    import inspect

    from src.datasets.pr_review_v4 import digest

    source = inspect.getsource(digest._issue_key)
    tree = ast.parse(source.strip())
    attributes = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    assert "arm" not in attributes, "the grouping key must not read the arm"


def test_a_mixed_source_finding_stays_per_site():
    """A pattern method merged with an independent-defect method must not aggregate.

    Otherwise a real compile failure disappears inside a policy issue.
    """

    finding = _finding("repository_policy.v1", "a", "change:1")
    mixed = finding.model_copy(update={
        "sources": [
            finding.sources[0],
            finding.sources[0].model_copy(update={"method_id": "baseline_failure.v1"}),
        ]
    })
    assert aggregation_for(mixed) == "per_site"


def test_the_report_counts_what_collapsed():
    findings = [
        _finding("repository_policy.v1", f"axiom_{index}", f"change:{index}")
        for index in range(19)
    ] + [_finding("baseline_failure.v1", "broken", "change:x")]
    _issues, report = digest_findings(findings)
    assert report["findings_in"] == 20
    assert report["issues_out"] == 2
    assert report["issues_collapsing_several_findings"] == 1
    assert report["by_aggregation"] == {"per_site": 1, "per_pattern": 1}
    assert report["largest_issue_sites"] == 19
