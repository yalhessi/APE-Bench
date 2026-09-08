"""Recall has two denominators, and reporting one of them alone conflates two claims.

Both September runs published only through the compile gate; the evidence chain returned zero
supported verdicts across 18 packets. Only 16 of the release's 43 gold obligations carry a
concern a compile can settle, so 27 were unpublishable by construction — and every run was
reported against 43.

A figure against 43 measures the reviewer and the publication mechanism together. A figure
against 16 measures the reviewer alone, given what the mechanism can express. Both are worth
having; only reporting both makes either readable.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.analysis.reachability import (
    AWAITING_A_WARRANT,
    VERIFIABLE_BY_COMPILE,
    annotate_recall,
    mechanism_identity,
    reachability_report,
    reachable_concerns,
)

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


def _gold_concerns():
    path = RELEASE / "gold/judgments.jsonl"
    if not path.is_file():
        pytest.skip("release not present")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        judgment = json.loads(line)
        for _obligation in judgment.get("obligations") or []:
            rows.append(judgment.get("concern_labels") or [])
    return rows


def test_the_release_ceiling_is_37_percent():
    """The measured figure this module exists to make visible."""

    report = reachability_report(_gold_concerns())
    assert report["obligations_total"] == 43
    assert report["obligations_reachable"] == 16
    assert report["reachable_share"] == pytest.approx(0.3721, abs=1e-3)


def test_style_is_the_largest_unreachable_block():
    """19 of 43 -- and only ~2 of those are linter-shaped, so the block is not one fix."""

    report = reachability_report(_gold_concerns())
    assert report["by_concern"]["style"]["total"] == 19
    assert report["by_concern"]["style"]["reachable"] == 0


def test_reachability_is_predeclared_not_observed():
    """Deriving it from what published would let a run that published nothing declare nothing
    reachable and score 100%. The mapping is a constant, and its hash is recorded."""

    empty = reachability_report([])
    populated = reachability_report([["style"], ["duplication"]])
    assert empty["mechanism_sha256"] == populated["mechanism_sha256"]
    assert populated["obligations_reachable"] == 1


def test_the_evidence_chain_is_not_counted_until_it_admits_something():
    """Counting a channel that has never returned `supported` would inflate the denominator
    with obligations nothing can publish."""

    assert reachable_concerns() == VERIFIABLE_BY_COMPILE
    widened = reachable_concerns(evidence_chain_admits=True)
    assert AWAITING_A_WARRANT <= widened
    assert mechanism_identity() != mechanism_identity(evidence_chain_admits=True)


def test_both_spellings_of_the_documentation_concern_are_covered():
    """Gold labels it `docs`; findings label it `documentation`. Carrying one spelling would
    silently exclude the other the day the evidence chain starts admitting."""

    widened = reachable_concerns(evidence_chain_admits=True)
    assert {"docs", "documentation"} <= widened


def test_an_obligation_is_reachable_if_any_of_its_concerns_is():
    """The generous reading, so the ceiling is not overstated."""

    report = reachability_report([["style", "duplication"]])
    assert report["obligations_reachable"] == 1


def test_recall_is_annotated_with_the_reachable_denominator():
    """This test asserted `issue_recall_reachable == 2.0` and passed.

    A recall rate of 2.0 is not a number that can be right, and the assertion was written to
    match what the code produced rather than to say what the metric means. It took a real run
    reporting 3.0 to notice. Both halves now describe the same obligations.
    """

    # Four obligations, one of which a compile can settle -- and it was hit.
    concerns = {"o1": ["style"], "o2": ["naming"], "o3": ["duplication"], "o4": ["docs"]}
    judge_report = {"per_obligation": [
        {"obligation_id": "o1", "issue_status": "hit", "resolution_status": "miss"},
        {"obligation_id": "o2", "issue_status": "miss", "resolution_status": "miss"},
        {"obligation_id": "o3", "issue_status": "hit", "resolution_status": "hit"},
        {"obligation_id": "o4", "issue_status": "miss", "resolution_status": "miss"},
    ]}
    out = annotate_recall(judge_report, concerns)

    assert out["reachability"]["obligations_reachable"] == 1
    assert out["issue_recall_reachable"] == pytest.approx(1.0)
    assert out["resolution_recall_reachable"] == pytest.approx(1.0)
    # The style hit is real and unpublishable, and is reported rather than folded in.
    assert out["issue_hits_unreachable"] == 1


def test_annotation_handles_a_zero_reachable_denominator():
    out = annotate_recall(
        {"per_obligation": [{"obligation_id": "o1", "issue_status": "miss"}]},
        {"o1": ["style"]})
    assert out["issue_recall_reachable"] is None


# --- the numerator and the denominator must describe the same obligations --------------------


def test_reachable_recall_cannot_exceed_one():
    """`pr5_smoke4_rep9` reported `issue_recall_reachable: 3.0` -- six hits over two reachable
    obligations. The numerator was the total hit count across every obligation; the denominator
    counted only the reachable ones.

    A rate above 1 is the visible symptom. The real error is that the halves were about
    different sets, and about different questions: a hit is *identification*, reachable is
    *publication*. Fourteen of that run's obligations are `style`, which no mechanism can
    settle, and several were correctly identified.
    """

    from src.mathlib_review.analysis.reachability import annotate_recall

    concerns = {
        "o1": ["proof-golf"],   # reachable: a compile settles it
        "o2": ["duplication"],  # reachable
        "o3": ["style"],        # not reachable
        "o4": ["style"],
        "o5": ["docs"],
    }
    report = {"per_obligation": [
        {"obligation_id": "o1", "issue_status": "hit", "resolution_status": "hit"},
        {"obligation_id": "o2", "issue_status": "miss", "resolution_status": "miss"},
        {"obligation_id": "o3", "issue_status": "hit", "resolution_status": "miss"},
        {"obligation_id": "o4", "issue_status": "hit", "resolution_status": "miss"},
        {"obligation_id": "o5", "issue_status": "hit", "resolution_status": "miss"},
    ]}
    out = annotate_recall(report, concerns)
    assert out["reachability"]["obligations_reachable"] == 2
    # 1 of the 2 reachable obligations was hit. Four hits total, three of them unreachable.
    assert out["issue_recall_reachable"] == 0.5
    assert out["issue_hits_reachable"] == 1
    assert out["issue_hits_unreachable"] == 3
    assert 0.0 <= out["issue_recall_reachable"] <= 1.0


def test_both_halves_are_reported_not_only_the_ratio():
    """A reader should be able to see the two sets rather than infer them. "Correctly
    identified and unpublishable" is the interesting number here and a ratio hides it."""

    from src.mathlib_review.analysis.reachability import annotate_recall

    out = annotate_recall(
        {"per_obligation": [{"obligation_id": "o1", "issue_status": "hit"}]},
        {"o1": ["style"]})
    assert out["issue_hits_unreachable"] == 1
    assert out["issue_recall_reachable"] is None   # nothing reachable to divide by


def test_the_report_and_the_recall_split_agree_on_what_is_reachable():
    """They each decided it themselves, and disagreeing about exactly that is how the rate
    came out at 3.0."""

    from src.mathlib_review.analysis.reachability import (
        _is_reachable, annotate_recall, reachability_report,
    )

    concerns = {"a": ["proof-golf"], "b": ["style"], "c": ["duplication"]}
    out = annotate_recall({"per_obligation": []}, concerns)
    assert out["reachability"]["obligations_reachable"] == sum(
        _is_reachable(v) for v in concerns.values())
    assert reachability_report(concerns.values())["obligations_reachable"] == 2
