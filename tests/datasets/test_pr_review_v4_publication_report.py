"""Final-finding judgment and pre/post-publication reporting."""

from src.mathlib_review.judge.runner import (
    candidate_from_finding,
    publication_summary,
)
from src.mathlib_review.schema import FindingSource, ReviewFinding


def _finding(admission="diagnostic"):
    return ReviewFinding(
        finding_id="finding:1",
        pr_number=7,
        episode_id="episode:7",
        arm="generalist",
        admission=admission,
        admission_reason="test",
        change_ids=["change:1"],
        primary_change_id="change:1",
        concern_family="style",
        issue_kind="style_norm_violation",
        primary_subject="theorem x",
        severity="advisory",
        claim="final merged claim",
        requested_change="final merged request",
        evidence_tier="model_assertion",
        action_key="change:1:style",
        sources=[FindingSource(arm="generalist", candidate_id="candidate:old")],
        source_sha256="finding-sha",
    )


def _report(issue, resolution):
    return {
        "scored": True,
        "counts": {"obligations": 40},
        "obligation_status_counts": {
            "issue": {"hit": issue, "ambiguous": 0, "miss": 40 - issue},
            "resolution": {
                "hit": resolution,
                "ambiguous": 0,
                "miss": 40 - resolution,
            },
        },
    }


def test_final_finding_projection_judges_only_final_wording_and_identity():
    candidate = candidate_from_finding(_finding())
    assert candidate.candidate_id == "finding:1"
    assert candidate.source_sha256 == "finding-sha"
    assert candidate.claim == "final merged claim"
    assert candidate.requested_change == "final merged request"
    assert candidate.candidate_id != "candidate:old"


def test_publication_summary_exposes_the_four_requested_counts():
    report = publication_summary([_finding("published")], _report(12, 8), _report(5, 4))
    assert report["obligations"] == 40
    assert report["pre_publication"] == {"issue_hits": 12, "resolution_hits": 8}
    assert report["post_publication"] == {"issue_hits": 5, "resolution_hits": 4}
    assert report["findings"] == {"pre_publication": 1, "post_publication": 1}

