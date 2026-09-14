"""From a whole-PR review to scorable findings, and the two ways that silently returns zero.

Both failure modes here produce an empty `findings.jsonl` and a run that closes cleanly, which
the judge then scores as "the baseline found nothing". That is a statement about the plumbing
presented as a statement about the agent, and it is the single most likely way this experiment
produces a confident wrong answer:

1. `candidates_from_response` refuses a candidate with no `issue_kind` on any release rendered
   at `candidate-prompt/12` or later -- which is every work unit of dev-medium-0.3.0. A solo
   finding that does not carry one is rejected at ingestion.
2. A solo task that never submitted -- the likeliest cause being the billed cost cap, after
   which the relay refuses the next request and an external CLI usually dies -- leaves no
   response at all. `solo` schedules no mandatory jobs, so nothing else would notice.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.review.runner import (
    SOLO_ARM_ID, _solo_candidate, _solo_coverage_gaps, _solo_responses,
)


class _Unit:
    def __init__(self):
        self.work_unit_id = "wu:1"
        self.episode_id = "ep:1"
        self.primary_subjects_by_change = {"change:a": "Foo.bar"}
        self.entity_ids_by_change = {"change:a": ["entity:1"], "change:b": []}


class _Result(dict):
    """A task result as the orchestrator hands it over."""


class _Results:
    def __init__(self, rows):
        self.task_results = rows


def _finding(**overrides):
    row = {"primary_change_id": "change:a", "change_ids": ["change:a"],
           "claim": "`Foo.bar` duplicates `Bar.foo`", "suggested_fix": "reuse `Bar.foo`",
           "severity": "blocking", "concern_family": "duplication",
           "issue_kind": "duplicate_implementation"}
    row.update(overrides)
    return row


def test_a_candidate_carries_the_issue_kind_ingestion_requires():
    """Trap 1. Without this every finding is rejected and the condition reads as silent."""

    candidate = _solo_candidate(_finding(), _Unit())
    assert candidate["issue_kind"] == "duplicate_implementation"
    assert candidate["concern_family"] == "duplication"


def test_an_unlabelled_finding_still_produces_a_usable_candidate():
    """A model that omits the labels should cost that finding its routing, not its existence.
    `concern_family` falls back to the closed list's own escape hatch rather than to a guess;
    `issue_kind` stays absent, so ingestion refuses it loudly instead of silently mislabelling
    it as something a verifier would then check under the wrong rule."""

    candidate = _solo_candidate(_finding(concern_family=None, issue_kind=None), _Unit())
    assert candidate["concern_family"] == "other"
    assert candidate["issue_kind"] is None


def test_the_subject_comes_from_the_work_unit_not_the_model():
    """It was never told the subject, so requiring it to name one would require it to guess the
    decomposition's vocabulary -- which is the thing being withheld."""

    candidate = _solo_candidate(_finding(), _Unit())
    assert candidate["primary_subject"] == "Foo.bar"
    assert candidate["primary_entity_id"] == "entity:1"


def test_a_target_with_no_entities_gets_none_rather_than_a_guess():
    candidate = _solo_candidate(
        _finding(primary_change_id="change:b", change_ids=["change:b"]), _Unit())
    assert candidate["primary_entity_id"] is None


def test_an_episode_that_never_submitted_is_a_coverage_gap():
    """Trap 2, and the reason the run must not close `complete`. `assert_source_run_is_complete`
    then refuses to score it without `allow_partial`, which is the point: a budget result must
    not be reportable as a capability result."""

    data = [{"episode_id": "ep:1", "pr_number": 1},
            {"episode_id": "ep:2", "pr_number": 2}]
    results = _Results([_Result(success=True, episode_id="ep:1", pr_number=1)])

    gaps = _solo_coverage_gaps(results, data)
    assert [row["episode_id"] for row in gaps] == ["ep:2"]
    assert gaps[0]["arm_id"] == SOLO_ARM_ID


def test_a_failed_submission_is_a_gap_not_an_empty_success():
    """`success=False` with findings attached is still a gap: the task did not reach a terminal
    submission, so whatever it accumulated is not a review it stands behind."""

    data = [{"episode_id": "ep:1", "pr_number": 1}]
    results = _Results([_Result(success=False, episode_id="ep:1", pr_number=1,
                                findings=[{"claim": "half-finished"}])])

    assert len(_solo_coverage_gaps(results, data)) == 1


def test_a_review_is_filed_under_its_own_arm_and_never_the_generalists():
    """`solo_agent` and `generalist` are the control and the treatment of this comparison. A
    shared value would make them indistinguishable in every `by_arm` breakdown -- the "an arm's
    whole output silently reads as zero" failure the derived `ARMS` exists to prevent."""

    from src.mathlib_review.schema import ARMS

    assert SOLO_ARM_ID == "solo_agent" and SOLO_ARM_ID in ARMS
    assert SOLO_ARM_ID != "generalist"


def test_a_solo_finding_projects_under_solo_agent_not_generalist():
    """The bucket it shares with the evidence specialists files everything as `generalist`
    unless the producer is read off the candidate."""

    import inspect

    from src.mathlib_review.review import finalize

    source = inspect.getsource(finalize._evidence_specialist_findings)
    assert 'candidate.spec_id == "solo_agent"' in source


def test_a_validation_option_survives_the_non_strict_re_entry():
    """`candidates_from_response` re-enters itself per candidate when `strict=False`, and any
    option not threaded through that call is silently reset to its default. `finalize` only
    ever ingests non-strict, so an unthreaded option is one that never takes effect for any
    real caller while its unit test passes -- which is how `require_subject_in_claim` appeared
    to work and rejected every solo finding anyway.
    """

    import inspect

    from src.mathlib_review.review import candidates as module

    source = inspect.getsource(module.candidates_from_response)
    recursive = source.split("strict=True, spec_id=spec_id", 1)[1][:400]
    for option in ("require_subject_in_claim",):
        assert option in recursive, f"{option} is not threaded through the re-entry"


def test_a_solo_candidate_carries_every_field_the_claim_model_requires():
    """Constructed against the real model rather than a fixture: `concern_label` is required
    and was missing, which rejected the candidate under a generic `other` code that named a
    pydantic error rather than anything about reviewing."""

    from src.mathlib_review.schema import CandidateClaim

    candidate = _solo_candidate(_finding(), _Unit())
    required = {name for name, field in CandidateClaim.model_fields.items()
                if field.is_required()}
    supplied = set(candidate) | {
        # Filled by the validator from the invocation, not by the producer.
        "candidate_id", "source_sha256", "work_unit_id", "episode_id", "pr_number",
        "producer", "entity_ids", "evidence_requests",
    }
    assert not (required - supplied), sorted(required - supplied)


# --- closing a solo run's ledger ------------------------------------------------------------


def _solo_agenda(work_unit_ids=("wu:1",)):
    from src.mathlib_review.io import sealed_model
    from src.mathlib_review.schema.review import AgendaProposal, ReviewAgenda

    proposals = [
        sealed_model(
            AgendaProposal, proposal_id=f"{wu}#generalist", invocation_id=f"{wu}#generalist",
            arm_id="generalist", work_unit_id=wu, episode_id="ep:1", pr_number=1,
            site_change_ids=["change:a"], eligible=True, mandatory=True,
            prompt_sha256="a" * 64, cost_hint=0.079, rationale="r",
        )
        for wu in work_unit_ids
    ]
    return sealed_model(
        ReviewAgenda, agenda_id="agenda:t", run_name="t", routing_mode="solo",
        release="rel", arms=[], proposals=proposals,
        scheduler_version="s", renderer_version="r")


def _pruned_delegations(agenda):
    return [{"schema_version": "v5-delegation1", "invocation_id": item.invocation_id,
             "proposal_id": item.proposal_id, "arm_id": item.arm_id,
             "work_unit_id": item.work_unit_id, "pr_number": item.pr_number,
             "disposition": "pruned", "reason": "solo mode schedules no work-unit job",
             "budget_tier": None, "context_calls": []}
            for item in agenda.proposals]


def _solo_response(work_unit_id):
    return {"invocation_id": f"{work_unit_id}#{SOLO_ARM_ID}", "arm_id": SOLO_ARM_ID,
            "work_unit_id": work_unit_id, "spec_id": SOLO_ARM_ID, "pr_number": 1,
            "status": "success", "candidates": [], "verification_artifacts": []}


def _plan():
    from src.mathlib_review.io import canonical_json_bytes, sha256_bytes
    from src.mathlib_review.schema.review import V5RunPlan

    plan = V5RunPlan(
        run_id="v5run:t", run_name="t", routing_mode="solo", agenda_sha256="a" * 64,
        release="rel", prompt_sha256_by_invocation={}, arm_sha256_by_id={},
        model_name="m", scaffold_config_sha256="b" * 64,
        lead_cost_cap=1.0, standard_budget_cap=0.25, per_pr_cost_cap=4.0, source_sha256="")
    return plan.model_copy(update={"source_sha256": sha256_bytes(canonical_json_bytes(
        plan.model_dump(mode="json", exclude={"source_sha256"})))})


class _Usage:
    task_results = []
    total_cost = 0.0
    total_cached_cost = 0.0


def test_a_solo_run_closes_though_no_response_maps_to_a_delegation():
    """The two standing rules are mutually exclusive for anything that is not an `(arm, unit)`
    pair: a response must map to a delegation, and a delegation must be an enumerated
    proposal. A whole-PR review is not one, so the first real run raised
    `1 response(s) map to no recorded job` after finalizing successfully -- the ledger refused
    a run whose output was already on disk."""

    from src.mathlib_review.review.trace import reconcile

    agenda = _solo_agenda()
    manifest = reconcile(
        agenda=agenda, delegations=_pruned_delegations(agenda),
        responses=[_solo_response("wu:1")], plan=_plan(), results=_Usage(), issues_total=2)

    assert manifest.routing_mode == "solo"


def test_a_response_anchored_outside_the_sealed_scope_is_still_refused():
    """Where the teeth are in this mode. A solo response's work unit comes from the anchoring
    pass rather than from the plan, so it is the one place an unplanned unit can enter -- and
    it would otherwise reach the judge as ordinary output."""

    from src.mathlib_review.review.trace import ReconciliationError, reconcile

    agenda = _solo_agenda()
    with pytest.raises(ReconciliationError, match="never enumerated"):
        reconcile(agenda=agenda, delegations=_pruned_delegations(agenda),
                  responses=[_solo_response("wu:not-in-the-agenda")],
                  plan=_plan(), results=_Usage(), issues_total=0)


def test_retrieval_calls_are_counted_from_the_trace_not_the_empty_ledger():
    """`context_calls_total` is summed over delegation rows. A solo run's delegations are all
    `pruned` with empty call lists, so the manifest reported 0 while `context_trace.jsonl` held
    real retrievals -- and 0 there is indistinguishable from an agent that chose not to
    retrieve, which is a claim this experiment would otherwise have made by accident.
    """

    from src.mathlib_review.review.trace import reconcile

    agenda = _solo_agenda()
    manifest = reconcile(
        agenda=agenda, delegations=_pruned_delegations(agenda),
        responses=[_solo_response("wu:1")], plan=_plan(), results=_Usage(),
        issues_total=2, context_calls_total=2)

    assert manifest.context_calls_total == 2


def test_the_ledger_still_supplies_the_count_when_nothing_overrides_it():
    """The override must not become the only path: every other mode's count comes from the
    delegation rows, and reading it from a trace file they do not write would zero them."""

    from src.mathlib_review.review.trace import reconcile

    agenda = _solo_agenda()
    delegations = _pruned_delegations(agenda)
    delegations[0]["context_calls"] = [{"tool": "declaration_search"}]
    manifest = reconcile(agenda=agenda, delegations=delegations,
                         responses=[_solo_response("wu:1")], plan=_plan(),
                         results=_Usage(), issues_total=0)

    assert manifest.context_calls_total == 1
