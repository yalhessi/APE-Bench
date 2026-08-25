"""Offline gates for the registered-task judge, before it is allowed to spend money.

R0 compares the task arm against verdicts the script arm already cached. That comparison
is only meaningful if the two arms ask the model the *same question* and identify pairs
the *same way*; otherwise R0 would be measuring a prompt rewrite rather than a migration.
These tests pin both, plus the vote aggregation that is the migration's actual payoff.
"""

import asyncio

import pytest

from src.datasets.pr_review_v4 import judge_protocol, semantic_judge
from src.datasets.pr_review_v4.judge_runner import pair_task_data, script_cache_key
from src.datasets.pr_review_v4.schema import (
    CandidateClaim,
    EvidenceRequest,
    JudgmentAction,
    JudgmentAnnotation,
    JudgmentNode,
    JudgmentObligation,
)

from ape.tasks.base import create_task_from_data, get_task_class, list_task_types
from ape.tasks.lean_tasks.formal_math.pr_review_v4 import judgment as judge_task


def _pair():
    obligation = JudgmentObligation(
        obligation_id="obligation:abc",
        claim="Rename the lemma with an `encard_` prefix.",
        resolution_criteria="The declaration is renamed and references updated.",
        status="proposed_atomic",
        change_ids=["change:1"],
        source_sha256="obl-hash",
    )
    node = JudgmentNode(
        judgment_id="j1",
        source_intervention_id="intervention:1",
        repo="leanprover-community/mathlib4",
        pr_number=33098,
        episode_id="episode:1",
        action=JudgmentAction(kind="rename", object="lemma"),
        speech_act="request",
        blocking_force="advisory",
        concern_labels=["style", "naming"],
        scope_relations=[],
        obligations=[obligation],
        source_event_ids=[],
        context_relations=[],
        outcome_observation_ids=[],
        annotation=JudgmentAnnotation(
            producer="test", source_schema="t1",
            status="migration_proposal", atomicity_status="presumed_atomic",
        ),
        source_sha256="judgment-hash",
    )
    candidate = CandidateClaim(
        candidate_id="candidate:xyz",
        work_unit_id="wu:1",
        episode_id="episode:1",
        pr_number=33098,
        change_ids=["change:1"],
        primary_subject="Metric.card_maximalSeparatedSet",
        requested_change="Rename to `Metric.encard_maximalSeparatedSet`.",
        concern_family="naming",
        concern_label="naming",
        severity="advisory",
        claim="The lemma uses a `card_` prefix although its subject is `Set.encard`.",
        suggested_fix="Rename and update references.",
        evidence_requests=[],
        source_sha256="cand-hash",
    )
    return {
        "judgment": node, "obligation": obligation,
        "candidate": candidate, "overlap_change_ids": ["change:1"],
    }


def test_judge_task_is_registered():
    assert "lean_pr_review_v4_semantic_judgment" in list_task_types()
    assert get_task_class("lean_pr_review_v4_semantic_judgment") is judge_task.LeanPRReviewV4JudgmentTask


def test_there_is_one_rubric_object_not_two_equal_ones():
    """Identity, not equality.

    The two arms used to hold byte-identical copies asserted equal by this test. Copies
    drift: the script arm's only caller never passed the change graph, so it rendered an
    empty `## REVIEWED CODE` section while stamping verdicts with the v8 version string.
    Both now import from `judge_protocol`, so `is` holds and drift is impossible.
    """

    assert judge_task.JUDGE_VERSION is semantic_judge.JUDGE_VERSION
    assert judge_task.JUDGE_PROMPT is judge_protocol.JUDGE_PROMPT
    assert semantic_judge.JUDGE_PROMPT is judge_protocol.JUDGE_PROMPT


def test_the_active_rubric_is_v9_and_earlier_rubrics_are_retired():
    from src.datasets.pr_review_v4.legacy.judge_v71 import (
        LEGACY_JUDGE_PROMPT,
        LEGACY_JUDGE_VERSION,
    )

    assert semantic_judge.JUDGE_VERSION == "v4-semantic-v3-v9-rubric"
    assert LEGACY_JUDGE_VERSION == "v4-semantic-v1-v7.1-rubric"
    # The retired text is preserved for provenance, not for use.
    assert LEGACY_JUDGE_PROMPT != semantic_judge.JUDGE_PROMPT
    assert not hasattr(semantic_judge, "JUDGE_PROMPT_V8")


def test_the_task_prompt_always_carries_the_reviewed_code(tmp_path):
    """The defect this whole protocol exists to prevent, asserted directly."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from src.datasets.pr_review_v4.schema import ChangeTarget

    pair = _pair()
    target = ChangeTarget(
        change_id="change:1", episode_id="episode:1", pr_number=33098, kind="declaration",
        path="Mathlib/Test.lean", declaration_kind="theorem",
        declaration_name="Metric.card_maximalSeparatedSet",
        changed_range_ids=[], diff_fragments=[],
        reviewed_code="lemma Metric.card_maximalSeparatedSet : True := trivial\n",
        parse_status="semantic", source_sha256="t",
    )
    targets = {"change:1": target}
    record = pair_task_data(pair, "gpt_5_mini", semantic_judge.JUDGE_VERSION, targets)
    scaffold = ApeAgentConfig.model_validate({"scaffold_type": "ape_agent"})
    task = create_task_from_data(record, scaffold)

    prompt = asyncio.run(task.create_user_prompt())
    assert "reviewed code unavailable" not in prompt
    assert "Metric.card_maximalSeparatedSet" in prompt
    # And it is the protocol's renderer that produced it, not a second local copy.
    assert prompt == judge_protocol.render_prompt(
        gold_code=record["target_code"],
        gold_concerns=record["gold_concerns"],
        gold_action=record["gold_action"],
        gold_claim=record["gold_claim"],
        resolution_criteria=record["resolution_criteria"],
        primary_subject=record["primary_subject"],
        candidate_family=record["candidate_family"],
        candidate_claim=record["candidate_claim"],
        requested_change=record["requested_change"],
        suggested_fix=record["suggested_fix"],
        proposed_edit=record["proposed_edit"],
    )


def test_the_rubric_keeps_the_clauses_v71_dropped_and_adds_abstain():
    """v8 restored three omissions; v9 keeps them and adds the abstain verdict."""

    from src.datasets.pr_review_v4.legacy.judge_v71 import LEGACY_JUDGE_PROMPT

    # Prompts are hard-wrapped, so compare on whitespace-normalized text.
    squash = lambda s: " ".join(s.split())
    v9 = squash(semantic_judge.JUDGE_PROMPT)
    v71 = squash(LEGACY_JUDGE_PROMPT)
    for clause in (
        "DIFFERENT aspect of the same code",          # the rename/proof-style example
        "issue_match only",                            # a vaguer fix is issue-only
        "Compare the CHANGES",                         # compare transformations
        "{gold_code}",                                 # the reviewed code itself
        "{proposed_edit}",                             # the candidate's edit
        "abstain",                                     # v9: the judge may decline
    ):
        assert clause in v9, f"the active rubric must contain {clause!r}"
        if clause.startswith("{"):
            continue
        assert clause not in v71, f"{clause!r} was supposed to be missing from v7.1"


def test_v8_record_renders_the_code_and_hashes_differently_from_its_v71_twin(tmp_path):
    """A v8 record must be a distinct unit of work, or resume would cross the rubrics."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from src.datasets.pr_review_v4.schema import ChangeTarget

    pair = _pair()
    target = ChangeTarget(
        change_id="change:1", episode_id="episode:1", pr_number=33098, kind="declaration",
        path="Mathlib/Test.lean", declaration_kind="theorem",
        declaration_name="Metric.card_maximalSeparatedSet",
        changed_range_ids=[], diff_fragments=[],
        reviewed_code="lemma Metric.card_maximalSeparatedSet : True := trivial\n",
        parse_status="semantic", source_sha256="t",
    )
    from src.datasets.pr_review_v4.legacy.judge_v71 import LEGACY_JUDGE_VERSION

    v71 = pair_task_data(pair, "gpt_5_mini", LEGACY_JUDGE_VERSION)
    v8 = pair_task_data(pair, "gpt_5_mini", semantic_judge.JUDGE_VERSION, {"change:1": target})

    assert "card_maximalSeparatedSet" in v8["target_code"]

    scaffold = ApeAgentConfig.model_validate({"scaffold_type": "ape_agent"})
    t71 = create_task_from_data(v71, scaffold)
    t8 = create_task_from_data(v8, scaffold)
    assert t71.data.global_index != t8.data.global_index, (
        "v7.1 and v8 records must hash differently or a v8 run would resume into v7.1 results"
    )
    prompt8 = asyncio.run(t8.create_user_prompt())
    assert "REVIEWED CODE" in prompt8 and "card_maximalSeparatedSet" in prompt8


def test_unknown_rubric_version_is_rejected_rather_than_silently_defaulted():
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    record = pair_task_data(_pair(), "gpt_5_mini", semantic_judge.JUDGE_VERSION)
    record["judge_version"] = "v4-semantic-vX-made-up"
    scaffold = ApeAgentConfig.model_validate({"scaffold_type": "ape_agent"})
    task = create_task_from_data(record, scaffold)
    with pytest.raises(ValueError, match="unknown judge rubric"):
        asyncio.run(task.create_user_prompt())


def test_judge_config_pins_a_budget_adequate_for_the_tool_call_protocol():
    """Decode parameters must be pinned, and sized for THIS arm's submission protocol.

    Two R0 rounds taught two different halves of this:

    * Round 1 left the budget unset, so the task arm inherited the framework defaults
      (32000/30000) and deliberated 3-5x longer than the script — a different judge.
    * Round 2 copied the script's 1200/512, and 4 of 18 pairs failed outright without
      ever reaching `submit_result`. The script returns plain-text JSON; this task must
      emit a tool call, which costs extra tokens on top of the same reasoning. The
      failures were the borderline pairs, so the surviving agreement was a selection
      effect.

    So the requirement is not parity with the script's numbers — it is an explicit budget
    that clears the observed reasoning ceiling (2752 tokens) with headroom.
    """

    from pathlib import Path

    from ape.utils import load_yaml

    config = load_yaml(Path("configs/pr_review_v4_judge.yaml"))["llm_config"]
    for key in ("max_tokens", "thinking_budget_tokens"):
        assert key in config, (
            f"judge config must pin {key}; leaving it unset inherits the framework "
            "defaults and silently changes the judge"
        )
    observed_ceiling = 2752  # max reasoning tokens measured across R0 round 1
    assert config["thinking_budget_tokens"] > observed_ceiling, (
        "thinking budget must exceed the observed reasoning ceiling, or hard pairs fail "
        "to produce a verdict at all"
    )
    assert config["max_tokens"] > config["thinking_budget_tokens"], (
        "max_tokens must leave room for the submit_result tool call after reasoning"
    )


def test_judge_identity_covers_everything_that_can_change_a_verdict():
    """Model and rubric are not enough to identify a judge.

    R0 measured the two arms disagreeing on 4 of 18 pairs purely because their decode
    budgets differed, with every disagreeing pair unanimous *within* its arm. Sampling and
    the aggregation policy decide what a set of samples means, and the context profile
    decides what the judge was shown, so all of them are part of its identity.
    """

    base = dict(
        model="gpt_5_mini", sample_count=3, max_tokens=4000, thinking_budget_tokens=3000,
        temperature=None, aggregation_policy="majority",
        context_profile=judge_protocol.ContextProfile(),
    )
    identity = judge_protocol.judge_identity(**base)
    for field, value in (
        ("model", "gpt_5.2"),
        ("sample_count", 5),
        ("max_tokens", 1200),
        ("thinking_budget_tokens", 512),
        ("temperature", 0.7),
        ("aggregation_policy", "unanimous"),
        ("context_profile", judge_protocol.ContextProfile(maintainer_comment=True)),
    ):
        assert judge_protocol.judge_identity(**{**base, field: value}) != identity, (
            f"changing {field} must change the judge's identity"
        )
    # And the retired rubric can never join to the active one.
    from src.datasets.pr_review_v4.legacy.judge_v71 import LEGACY_JUDGE_VERSION

    assert judge_protocol.judge_identity(**base, judge_version=LEGACY_JUDGE_VERSION) != identity


def test_context_profile_names_only_the_blocks_that_are_on():
    assert judge_protocol.ContextProfile().as_key() == "base"
    assert judge_protocol.ContextProfile(maintainer_comment=True).as_key() == "maintainer_comment"
    both = judge_protocol.ContextProfile(maintainer_comment=True, sibling_obligations=True)
    assert both.as_key() == "maintainer_comment+sibling_obligations"


def test_verdict_parsing_reports_status_and_never_scores_garbage_as_a_negative():
    """An unparseable reply is an error, not a "no".

    Scoring garbage as a negative verdict silently converts judge failures into misses.
    """

    parsed = semantic_judge.parse_verdict(
        '{"issue_match": true, "resolution_match": true, "reason": "same rename"}'
    )
    assert (parsed.issue_match, parsed.resolution_match, parsed.status) == (True, True, "parsed")

    fenced = semantic_judge.parse_verdict(
        '```json\n{"issue_match": false, "resolution_match": false, "reason": "no"}\n```'
    )
    assert fenced.status == "parsed"

    garbage = semantic_judge.parse_verdict("unparseable")
    assert garbage.status == "unparseable"
    assert (garbage.issue_match, garbage.resolution_match) == (False, False)


def test_stringified_booleans_are_not_truthy():
    """`bool("false")` is `True`; a stringified boolean must not invert the verdict."""

    assert judge_protocol.as_bool("false") is False
    assert judge_protocol.as_bool("true") is True
    assert judge_protocol.as_bool(False) is False


def test_resolution_implies_issue_is_enforced():
    verdict = semantic_judge.parse_verdict(
        '{"issue_match": false, "resolution_match": true, "reason": "x"}'
    )
    assert (verdict.issue_match, verdict.resolution_match) == (False, False)


def _result(issue, resolution=False):
    return judge_task.LeanPRReviewV4JudgmentResult(
        task_id="t", task_type="lean_pr_review_v4_semantic_judgment", global_index="g",
        success=True, score=1.0, issue_match=issue, resolution_match=resolution,
    )


def test_majority_vote_resolves_a_split_and_records_the_disagreement():
    """The migration's payoff: a 2-of-3 flip becomes a measured, voted outcome."""

    aggregated = judge_task.LeanPRReviewV4JudgmentTask.aggregate_results(
        [_result(True), _result(True), _result(False)]
    )
    assert aggregated.issue_match is True
    assert aggregated.custom_metrics["issue_votes"] == 2
    assert aggregated.custom_metrics["samples_succeeded"] == 3
    assert aggregated.custom_metrics["issue_unanimous"] is False

    unanimous = judge_task.LeanPRReviewV4JudgmentTask.aggregate_results(
        [_result(False), _result(False), _result(False)]
    )
    assert unanimous.issue_match is False
    assert unanimous.custom_metrics["issue_unanimous"] is True


def test_match_projection_reads_source_hashes_from_the_pair_not_the_result():
    """Regression: the verdict result carries no content hashes; the pair supplies them.

    The first live run crashed here — `_match_from_result` looked for
    `candidate_source_sha256` on the task result, where it does not exist. Keeping the
    hashes on the record is deliberate (a result must not be able to disagree with the
    record about what was judged), so the projection has to join.
    """

    from src.datasets.pr_review_v4.judge_runner import _match_from_result

    pair = _pair()
    raw = {
        "candidate_id": pair["candidate"].candidate_id,
        "obligation_id": pair["obligation"].obligation_id,
        "issue_match": True, "resolution_match": True, "reason": "same ask",
    }
    hashes = {
        (pair["candidate"].candidate_id, pair["obligation"].obligation_id): (
            pair["candidate"].source_sha256, pair["obligation"].source_sha256,
            "semantic-pair:abc", "anchor", "observed",
        )
    }
    match = _match_from_result(raw, "gpt_5_mini", hashes)
    assert match.candidate_source_sha256 == pair["candidate"].source_sha256
    assert match.obligation_source_sha256 == pair["obligation"].source_sha256
    assert (match.issue_match, match.resolution_match) == (True, True)
    # The pair also supplies the identity the verdict must reconcile against, and the tier
    # it was compared at — so a widened verdict can never be counted as an anchored one.
    assert (match.pair_id, match.pairing_tier, match.role) == (
        "semantic-pair:abc", "anchor", "observed")

    # resolution stays subordinate to issue even if a result claims otherwise
    clamped = _match_from_result({**raw, "issue_match": False}, "gpt_5_mini", hashes)
    assert (clamped.issue_match, clamped.resolution_match) == (False, False)


def test_vote_metrics_survive_the_float_coercion_of_custom_metrics():
    """`custom_metrics` is a float map, so `unanimous` arrives as 1.0/0.0, not a bool."""

    aggregated = judge_task.LeanPRReviewV4JudgmentTask.aggregate_results(
        [_result(True), _result(True), _result(False)]
    )
    metrics = aggregated.custom_metrics
    # What judge_runner normalizes back into the votes artifact.
    assert int(metrics["issue_votes"]) == 2
    assert int(metrics["samples_succeeded"]) == 3
    assert bool(metrics["issue_unanimous"]) is False


def test_majority_vote_keeps_resolution_subordinate_to_issue():
    aggregated = judge_task.LeanPRReviewV4JudgmentTask.aggregate_results(
        [_result(False, True), _result(False, True), _result(False, False)]
    )
    assert (aggregated.issue_match, aggregated.resolution_match) == (False, False)


def test_resolution_votes_are_counted_only_among_issue_matching_samples():
    """A sample that said `issue=False` has `resolution_match=False` by clamp, not judgement.

    Counting those in the resolution majority lets samples that never considered the
    question decide it. Here 1 of 2 issue-matching samples said resolution — not a majority —
    where the old rule computed 1 of 3 and reached the same answer for the wrong reason.
    """

    aggregated = judge_task.LeanPRReviewV4JudgmentTask.aggregate_results(
        [_result(True, True), _result(False), _result(True)]
    )
    metrics = aggregated.custom_metrics
    assert metrics["resolution_denominator"] == 2
    assert metrics["resolution_votes"] == 1
    assert aggregated.resolution_match is False
    assert metrics["resolution_unanimous"] is False


def test_resolution_unanimity_is_reported_separately_from_issue():
    """v8 traded issue splits for resolution splits; only issue was ever reported."""

    aggregated = judge_task.LeanPRReviewV4JudgmentTask.aggregate_results(
        [_result(True, True), _result(True, True), _result(True, False)]
    )
    assert aggregated.custom_metrics["issue_unanimous"] is True
    assert aggregated.custom_metrics["resolution_unanimous"] is False


def test_too_few_successful_samples_is_a_coverage_gap_not_a_verdict():
    """One survivor of three must not decide, and must not be reported unanimous."""

    failed = judge_task.LeanPRReviewV4JudgmentResult(
        task_id="t", task_type="lean_pr_review_v4_semantic_judgment", global_index="g",
        success=False, score=0.0,
    )
    assert judge_task.LeanPRReviewV4JudgmentTask.aggregate_results(
        [_result(True, True), failed, failed]
    ) is None
    survived = judge_task.LeanPRReviewV4JudgmentTask.aggregate_results(
        [_result(True, True), _result(True, True), failed]
    )
    assert survived is not None
    assert survived.custom_metrics["samples_requested"] == 3
    assert survived.custom_metrics["samples_succeeded"] == 2
