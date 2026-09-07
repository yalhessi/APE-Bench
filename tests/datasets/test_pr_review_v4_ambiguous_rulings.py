"""Ambiguous obligations are a third category, not a silent match or miss.

Some maintainer asks are not decided by the rubric — e.g. a candidate requesting a
prerequisite rename that the maintainer's proof rewrite presupposes. Forcing those into
`hit` overstates the system; forcing them into `miss` understates it. They are ruled by a
human in `inputs/pr_review_v4/curation/ambiguous_pairs_v2.json` and reported separately,
while staying in the denominator so recall cannot be inflated by dropping hard cases.

v2 keys rulings by (obligation, candidate, level): the documented ambiguity is a property
of a *relationship*, and applying it at obligation granularity over-applied it to every
other candidate reaching the same obligation. It also applies to resolution, which v1
ignored entirely — the omission that made `resolution_recall > issue_recall` reachable.
"""

import json
from pathlib import Path

from src.mathlib_review.io import jsonl_bytes
from src.mathlib_review.judge.semantic_judge import (
    AMBIGUOUS_REGISTRY,
    load_ambiguous_rulings,
    semantic_report,
)
from src.mathlib_review.schema import (
    CandidateClaim,
    InterventionView,
    JudgmentAction,
    JudgmentAnnotation,
    JudgmentNode,
    JudgmentObligation,
    SemanticMatch,
)

RULED = "obligation:a58d0d5ea6ca1dcb635a19a06e272cb7e73adefa96272448dca2e373aeb72a4b"


def _obligation(oid):
    return JudgmentObligation(
        obligation_id=oid, claim="c", status="proposed_atomic",
        change_ids=["change:1"], source_sha256="h",
    )


def _judgment(obligations):
    return JudgmentNode(
        judgment_id="j1", source_intervention_id="i1", repo="r", pr_number=1,
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
        obligation_ids=obligation_ids, aggregation_policy="all_required",
        evaluation_eligibility="included", source_sha256="h",
    )


def _match(oid, issue, resolution=False):
    return SemanticMatch(
        match_id="m", candidate_id="candidate:1", obligation_id=oid,
        issue_match=issue, resolution_match=resolution and issue, reason="r",
        judge_model="m", judge_version="v", candidate_source_sha256="c",
        obligation_source_sha256="o", source_sha256="h",
    )


def _candidate():
    return CandidateClaim(
        candidate_id="candidate:1", work_unit_id="w", episode_id="e1", pr_number=1,
        change_ids=["change:1"], concern_family="style", concern_label="style",
        severity="advisory", claim="c", evidence_requests=[], source_sha256="h",
    )


def test_the_shipped_registry_rules_the_prerequisite_rename_case():
    rulings = load_ambiguous_rulings()["rulings"]
    key = (RULED, "*", "issue")
    assert key in rulings, "the human ruling on the prerequisite-rename pair must be recorded"
    assert rulings[key]["ruling"] == "ambiguous"
    assert rulings[key]["rationale"], "a ruling without a rationale is not auditable"


def test_a_missing_registry_raises_rather_than_scoring_without_it():
    """It used to fail open: `{}` from any cwd but the repo root, silently two-way."""

    import pytest

    with pytest.raises(FileNotFoundError):
        load_ambiguous_rulings(Path("inputs/pr_review_v4/curation/does-not-exist.json"))


def test_registry_is_wellformed_and_rulings_are_distinguished_from_open_questions():
    payload = json.loads(AMBIGUOUS_REGISTRY.read_text())
    assert payload["schema_version"] == "pr4-ambiguous-pairs2"
    ruled = {r["obligation_id"] for r in payload["rulings"]}
    open_cases = {r["obligation_id"] for r in payload.get("candidates_for_ruling", [])}
    assert not (ruled & open_cases), (
        "an obligation cannot be both ruled and awaiting a ruling"
    )
    for row in payload["rulings"]:
        assert row["ruled_by"] and row["ruled_at"] and row["rationale"]


def test_ambiguous_match_is_reported_separately_and_stays_in_the_denominator(tmp_path):
    ruled, plain, missed = RULED, "obligation:plain", "obligation:missed"
    judgments = [_judgment([_obligation(x) for x in (ruled, plain, missed)])]
    views = [_view([ruled, plain, missed])]
    matches = [_match(ruled, True), _match(plain, True, True)]  # `missed` has none

    report = semantic_report(judgments, views, [_candidate()], matches)

    assert report["obligation_status_counts"]["issue"] == {"hit": 1, "ambiguous": 1, "miss": 1}
    # The denominator is unchanged: ambiguity does not shrink the problem.
    assert report["counts"]["obligations"] == 3
    assert report["issue_recall"] == 1 / 3
    assert report["issue_recall_including_ambiguous"] == 2 / 3
    assert report["ambiguous_rate"] == 1 / 3
    statuses = {r["obligation_id"]: r["issue_status"] for r in report["per_obligation"]}
    assert statuses == {ruled: "ambiguous", plain: "hit", missed: "miss"}


def test_a_ruled_obligation_with_no_match_is_still_a_miss():
    """The ruling governs how a match is counted, not whether one occurred."""

    judgments = [_judgment([_obligation(RULED)])]
    views = [_view([RULED])]
    report = semantic_report(judgments, views, [_candidate()], [_match(RULED, False)])

    assert report["obligation_status_counts"]["issue"] == {"hit": 0, "ambiguous": 0, "miss": 1}
    assert report["issue_recall"] == 0.0
    assert report["issue_recall_including_ambiguous"] == 0.0


def test_an_empty_registry_leaves_the_two_way_behaviour_unchanged(tmp_path):
    empty = tmp_path / "none.json"
    empty.write_text(json.dumps({"schema_version": "pr4-ambiguous-pairs2", "rulings": []}))
    judgments = [_judgment([_obligation(RULED)])]
    views = [_view([RULED])]
    report = semantic_report(
        judgments, views, [_candidate()], [_match(RULED, True)], ambiguous_registry=empty,
    )
    assert report["obligation_status_counts"]["issue"] == {"hit": 1, "ambiguous": 0, "miss": 0}
    assert report["issue_recall"] == 1.0
