"""Pairing, coverage and metric-naming guarantees for the evaluator.

Each test here corresponds to a defect that reached a shipped run:

* pairing on exact `change_id` intersection left 16 of 22 obligations (73%) unjudged, with
  no trace anywhere in the report;
* a pair that produced no verdict was indistinguishable from one the judge answered "no",
  so judge failures silently became misses;
* `resolution_recall` ignored the ambiguity registry while `issue_recall` honoured it,
  making `resolution_recall > issue_recall` reachable;
* the precision denominator counted only candidates that had already been located onto an
  eligible obligation, so flooding was invisible.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.datasets.pr_review_v4.semantic_judge import (
    VerdictCoverageError,
    build_null_pairs,
    build_pairs,
    reconcile,
    seal_pair,
    semantic_report,
)
from src.datasets.pr_review_v4.schema import (
    CandidateClaim,
    ChangeTarget,
    InterventionView,
    JudgmentAction,
    JudgmentAnnotation,
    JudgmentNode,
    JudgmentObligation,
    SemanticMatch,
)

RULED = "obligation:a58d0d5ea6ca1dcb635a19a06e272cb7e73adefa96272448dca2e373aeb72a4b"


def _obligation(oid, change_ids=("change:1",)):
    return JudgmentObligation(
        obligation_id=oid, claim="c", status="proposed_atomic",
        change_ids=list(change_ids), source_sha256=f"h-{oid}",
    )


def _judgment(obligations, pr_number=1):
    return JudgmentNode(
        judgment_id="j1", source_intervention_id="i1", repo="r", pr_number=pr_number,
        episode_id="e1", action=JudgmentAction(kind="replace", object="x"),
        speech_act="request", blocking_force="advisory", concern_labels=["style"],
        scope_relations=[], obligations=obligations, source_event_ids=[],
        context_relations=[], outcome_observation_ids=[],
        annotation=JudgmentAnnotation(
            producer="t", source_schema="t1", status="migration_proposal",
            atomicity_status="presumed_atomic",
        ),
        source_sha256="h",
    )


def _view(obligation_ids):
    return InterventionView(
        view_id="v1", source_intervention_id="i1", judgment_ids=["j1"],
        obligation_ids=list(obligation_ids), aggregation_policy="all_required",
        evaluation_eligibility="included", source_sha256="h",
    )


def _candidate(cid="candidate:1", change_ids=("change:1",), pr_number=1):
    return CandidateClaim(
        candidate_id=cid, work_unit_id="w", episode_id="e1", pr_number=pr_number,
        change_ids=list(change_ids), concern_family="style", concern_label="style",
        severity="advisory", claim="c", evidence_requests=[], source_sha256=f"h-{cid}",
    )


def _target(change_id, path):
    return ChangeTarget(
        change_id=change_id, episode_id="e1", pr_number=1, kind="declaration", path=path,
        declaration_name=change_id, declaration_kind="theorem", changed_range_ids=[],
        diff_fragments=[], reviewed_code="theorem x : True := trivial",
        parse_status="semantic", source_sha256="t",
    )


def _match(oid, issue, resolution=False, cid="candidate:1", role="observed", pair_id=None,
           tier="anchor"):
    return SemanticMatch(
        match_id=f"m-{oid}-{cid}-{role}", candidate_id=cid, obligation_id=oid,
        issue_match=issue, resolution_match=resolution and issue, reason="r",
        judge_model="gpt_5_mini", judge_version="v9", candidate_source_sha256=f"h-{cid}",
        obligation_source_sha256=f"h-{oid}", role=role, pair_id=pair_id, pairing_tier=tier,
        source_sha256="h",
    )


# --- pairing -----------------------------------------------------------------------

def test_anchor_tier_alone_reproduces_the_original_rule():
    judgments = [_judgment([_obligation("obligation:a")])]
    views = [_view(["obligation:a"])]
    near = _candidate("candidate:near", change_ids=["change:2"])
    pairs = build_pairs(judgments, views, [_candidate(), near])
    assert [pair["candidate"].candidate_id for pair in pairs] == ["candidate:1"]
    assert pairs[0]["pairing_tier"] == "anchor"


def test_file_tier_reaches_an_obligation_anchor_pairing_cannot():
    """The 73% of obligations that never reached the judge at all."""

    judgments = [_judgment([_obligation("obligation:a")])]
    views = [_view(["obligation:a"])]
    near = _candidate("candidate:near", change_ids=["change:2"])
    targets = {"change:1": _target("change:1", "Mathlib/A.lean"),
               "change:2": _target("change:2", "Mathlib/A.lean")}

    assert not build_pairs(judgments, views, [near])
    widened = build_pairs(judgments, views, [near], tiers=("anchor", "file"),
                          targets_by_change_id=targets)
    assert len(widened) == 1
    assert widened[0]["pairing_tier"] == "file"
    assert "Mathlib/A.lean" in widened[0]["tier_justification"]


def test_a_pair_is_emitted_once_at_the_strictest_tier_that_applies():
    judgments = [_judgment([_obligation("obligation:a")])]
    views = [_view(["obligation:a"])]
    targets = {"change:1": _target("change:1", "Mathlib/A.lean")}
    pairs = build_pairs(judgments, views, [_candidate()], tiers=("anchor", "file"),
                        targets_by_change_id=targets)
    assert len(pairs) == 1, "the same comparison must not be counted at two strengths"
    assert pairs[0]["pairing_tier"] == "anchor"


def test_null_pairs_stay_within_the_pull_request():
    """A cross-PR null contradicts the rubric's own premise and is a trivial negative."""

    judgments = [_judgment([_obligation("obligation:a")])]
    views = [_view(["obligation:a"])]
    other_pr = _candidate("candidate:other", change_ids=["change:9"], pr_number=2)
    observed = build_pairs(judgments, views, [_candidate()])
    nulls = build_null_pairs(observed, [_candidate(), _candidate("candidate:z"), other_pr])
    assert nulls, "there should be an unpaired same-PR candidate to use"
    assert all(pair["candidate"].pr_number == 1 for pair in nulls)
    assert all(pair["role"] == "null" for pair in nulls)
    assert "candidate:other" not in {pair["candidate"].candidate_id for pair in nulls}


# --- coverage ----------------------------------------------------------------------

def _sealed(pair):
    return seal_pair(pair, judge_identity="jid", prompt="p", gold_code="code")


def test_a_pair_with_no_verdict_is_a_coverage_failure_not_a_miss():
    judgments = [_judgment([_obligation("obligation:a"), _obligation("obligation:b")])]
    views = [_view(["obligation:a", "obligation:b"])]
    pairs = [_sealed(pair) for pair in build_pairs(judgments, views, [_candidate()])]
    assert len(pairs) == 2
    with pytest.raises(VerdictCoverageError, match="missing"):
        reconcile(pairs, [_match("obligation:a", True, pair_id=pairs[0].pair_id)])


@pytest.mark.parametrize("problem", ["duplicated", "extra", "stale_source"])
def test_reconciliation_rejects_every_discrepancy(problem):
    judgments = [_judgment([_obligation("obligation:a")])]
    views = [_view(["obligation:a"])]
    pairs = [_sealed(pair) for pair in build_pairs(judgments, views, [_candidate()])]
    good = _match("obligation:a", True, pair_id=pairs[0].pair_id)
    if problem == "duplicated":
        matches = [good, good.model_copy(update={"match_id": "m2"})]
    elif problem == "extra":
        matches = [good, _match("obligation:a", True, cid="candidate:ghost", pair_id="nope")]
    else:
        matches = [good.model_copy(update={"candidate_source_sha256": "drifted"})]
    with pytest.raises(VerdictCoverageError, match=problem):
        reconcile(pairs, matches)


def test_an_incomplete_verdict_set_withholds_every_recall():
    judgments = [_judgment([_obligation("obligation:a"), _obligation("obligation:b")])]
    views = [_view(["obligation:a", "obligation:b"])]
    pairs = [_sealed(pair) for pair in build_pairs(judgments, views, [_candidate()])]
    report = semantic_report(
        judgments, views, [_candidate()],
        [_match("obligation:a", True, pair_id=pairs[0].pair_id)],
        planned_pairs=pairs,
    )
    assert report["scored"] is False
    assert report["coverage"]["complete"] is False
    assert "issue_recall" not in report


def test_the_prompt_is_part_of_the_pair_identity():
    """A pair whose prompt lost its code section is a different comparison."""

    pair = build_pairs([_judgment([_obligation("obligation:a")])],
                       [_view(["obligation:a"])], [_candidate()])[0]
    with_code = seal_pair(pair, judge_identity="jid", prompt="full", gold_code="code")
    without = seal_pair(pair, judge_identity="jid", prompt="empty", gold_code="")
    assert with_code.pair_id != without.pair_id


# --- metrics -----------------------------------------------------------------------

def test_resolution_recall_can_never_exceed_issue_recall():
    """Definitionally impossible, and it was reachable: ambiguity demoted issue hits out of
    the numerator while resolution ignored the registry entirely."""

    judgments = [_judgment([_obligation(RULED)])]
    views = [_view([RULED])]
    report = semantic_report(judgments, views, [_candidate()], [_match(RULED, True, True)])
    assert report["resolution_recall"] <= report["issue_recall"]


def test_ambiguity_applies_to_resolution_as_well_as_issue():
    judgments = [_judgment([_obligation(RULED)])]
    views = [_view([RULED])]
    report = semantic_report(judgments, views, [_candidate()], [_match(RULED, True, True)])
    assert report["obligation_status_counts"]["issue"]["ambiguous"] == 1
    assert report["obligation_status_counts"]["resolution"]["ambiguous"] == 1


def test_gold_alignment_is_not_called_precision_and_counts_every_candidate():
    """Gold is a lower bound on legitimate findings, so an unaligned candidate is not wrong.

    The old denominator was candidates already located onto an eligible obligation, which
    made flooding invisible: 100 off-target candidates plus one hit scored 1.0.
    """

    judgments = [_judgment([_obligation("obligation:a")])]
    views = [_view(["obligation:a"])]
    flood = [_candidate()] + [_candidate(f"candidate:{i}", change_ids=["change:9"])
                              for i in range(9)]
    report = semantic_report(judgments, views, flood, [_match("obligation:a", True)])
    assert "paired_candidate_issue_precision" not in report
    assert report["gold_alignment_rate"] == pytest.approx(1 / 10)
    assert report["gold_alignment_within_paired"] == 1.0


def test_null_verdicts_are_excluded_from_recall_and_reported_as_candidate_negatives():
    judgments = [_judgment([_obligation("obligation:a")])]
    views = [_view(["obligation:a"])]
    matches = [
        _match("obligation:a", False),
        _match("obligation:a", True, cid="candidate:null", role="null"),
    ]
    report = semantic_report(judgments, views, [_candidate()], matches)
    assert report["issue_recall"] == 0.0, "a null match must never satisfy an obligation"
    assert report["null_pair_diagnostics"]["candidate_negative_issue_match_rate"] == 1.0
    assert "false_positive" not in json.dumps(report)


def test_silent_pr_emission_is_counted_without_calling_it_invented():
    judgments = [_judgment([_obligation("obligation:a")])]
    views = [_view(["obligation:a"])]
    control = _candidate("candidate:ctl", change_ids=["change:9"], pr_number=7)
    report = semantic_report(
        judgments, views, [_candidate(), control], [_match("obligation:a", True)],
        control_pr_numbers=[7],
    )
    assert report["silent_pr_emission"]["candidates"] == 1
    assert report["silent_pr_emission"]["candidates_per_control_pr"] == 1.0


def test_a_report_reads_its_judge_version_off_the_verdicts():
    """The shipped v8 reports are stamped with the retired v7.1 version string."""

    judgments = [_judgment([_obligation("obligation:a")])]
    views = [_view(["obligation:a"])]
    report = semantic_report(judgments, views, [_candidate()], [_match("obligation:a", True)])
    assert report["judge_version"] == "v9"

    mixed = [_match("obligation:a", True),
             _match("obligation:a", True, cid="candidate:2").model_copy(
                 update={"judge_version": "v8"})]
    with pytest.raises(ValueError, match="mixes judge_version"):
        semantic_report(judgments, views, [_candidate()], mixed)


def test_null_coverage_is_reported_when_widening_exhausts_the_pool():
    """Widening can leave no unpaired same-PR candidate to draw a near negative from.

    Measured on the 0.9.0 pilot: at `anchor` there are 12 nulls available, at
    `anchor+file` there are 0, because every same-PR candidate is now compared to an
    obligation. That is reduced calibration coverage, and it has to be visible — the
    alternative, a cross-PR null, contradicts the rubric's "same pull request" premise.
    """

    judgments = [_judgment([_obligation("obligation:a")])]
    views = [_view(["obligation:a"])]
    report = semantic_report(
        judgments, views, [_candidate()], [_match("obligation:a", True)],
        null_pairs_requested=2,
    )
    assert report["null_pair_diagnostics"]["requested"] == 2
    assert report["null_pair_diagnostics"]["pairs"] == 0
    assert report["null_pair_diagnostics"]["coverage"] == 0.0


# --- context ablations --------------------------------------------------------------

def test_each_context_block_is_an_independent_ablation_with_its_own_identity():
    """Adding context changes what the judge is asked, so it must change what it *is*.

    Otherwise an ablation run could resume into, or collide with, verdicts produced under
    different context — and the comparison would be meaningless.
    """

    from src.datasets.pr_review_v4.judge_protocol import ContextProfile, judge_identity

    base = dict(
        model="gpt_5_mini", sample_count=3, max_tokens=4000, thinking_budget_tokens=3000,
        temperature=None, aggregation_policy="majority",
    )
    identities = {
        profile.as_key(): judge_identity(**base, context_profile=profile)
        for profile in (
            ContextProfile(),
            ContextProfile(maintainer_comment=True),
            ContextProfile(sibling_obligations=True),
            ContextProfile(maintainer_comment=True, sibling_obligations=True),
        )
    }
    assert len(set(identities.values())) == 4, "each ablation must be a distinct judge"


def test_optional_blocks_are_omitted_not_stubbed():
    """A block rendered "(not recorded)" is still a different prompt from one that never
    mentions the field, which would make the base condition unreproducible."""

    from src.datasets.pr_review_v4.judge_protocol import render_prompt

    base = dict(
        gold_code="code", gold_concerns="naming", gold_action="rename lemma",
        gold_claim="c", resolution_criteria="r", primary_subject="s",
        candidate_family="naming", candidate_claim="cc", requested_change="rc",
        suggested_fix="sf", proposed_edit="(none)",
    )
    plain = render_prompt(**base)
    assert "WHAT THE MAINTAINER WROTE" not in plain
    assert "OTHER ASKS" not in plain

    with_comment = render_prompt(**base, maintainer_comment="please rename it")
    assert "WHAT THE MAINTAINER WROTE" in with_comment
    assert "OTHER ASKS" not in with_comment


def test_sibling_context_carries_claims_only_and_says_not_to_score_them():
    """Sibling *candidates* are never shown: that would let the judge credit this
    obligation using another candidate's content."""

    from src.datasets.pr_review_v4.judge_protocol import render_prompt

    prompt = render_prompt(
        gold_code="code", gold_concerns="naming", gold_action="rename lemma",
        gold_claim="c", resolution_criteria="r", primary_subject="s",
        candidate_family="naming", candidate_claim="cc", requested_change="rc",
        suggested_fix="sf", proposed_edit="(none)",
        sibling_claims=("Same below for `bar`.",),
    )
    assert "Same below for `bar`." in prompt
    assert "do not score these" in prompt


def test_the_context_sidecar_covers_every_included_obligation():
    """Built from the frozen raw bundles, because the release's events file is an index:
    it names the bundle and key a comment lives at, not the comment text."""

    from src.datasets.pr_review_v4.obligation_context import load_context

    context = load_context()
    assert len(context) == 40
    assert all(row["maintainer_comment"] for row in context.values())
    assert all(row["provenance"] in {"obligation_event", "judgment_event"}
               for row in context.values())
