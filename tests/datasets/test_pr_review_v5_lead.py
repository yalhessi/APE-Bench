"""The lead's contract: it may route freely, but it must account for everything.

The lead is the only component in this pipeline whose decisions are not derived from a rule,
which makes its *ledger* the thing that keeps the run interpretable. A lead that could quietly
drop a proposal, run a pair twice, or invent a job outside the sealed pool would still finish
successfully — and the run would be measuring something nobody wrote down.

These tests spawn nothing. Delegation itself is covered in
`test_pr_review_v5_delegation.py`; what is checked here is the bookkeeping around it.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from ape.tasks.lean_tasks.formal_math.pr_review_v5.lead import (
    LEAD_TASK_TYPE,
    LeanPRReviewV5LeadData,
    LeanPRReviewV5LeadTask,
)


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **_kwargs):
        def decorate(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorate


def _proposal(work_unit_id, arm_id, *, mandatory=False, eligible=True):
    invocation_id = f"{work_unit_id}#{arm_id}"
    return {
        "schema_version": "v5-proposal1",
        "proposal_id": invocation_id, "invocation_id": invocation_id,
        "arm_id": arm_id, "work_unit_id": work_unit_id, "episode_id": "ep:1",
        "pr_number": 33098, "site_change_ids": ["change:a"],
        "eligible": eligible, "mandatory": mandatory,
        "prompt_sha256": "a" * 64, "cost_hint": 0.079, "rationale": "why this arm exists",
        "source_sha256": "b" * 64,
    }


#: What the lead now reads: one ranked row per work unit, not a page of (arm, unit) pairs.
CENSUS = [
    {
        "work_unit_id": "wu:1",
        "rank": 1,
        "subjects": ["Foo.bar"],
        "why": ["`Foo.bar` is a chain of 4 low-level tactic steps"],
        "suggested_arms": ["proof_golf", "proof_idiom"],
        "available_arms": {"proof_golf": "wu:1#proof_golf",
                           "duplication": "wu:1#duplication"},
    },
]

PROPOSALS = [
    _proposal("wu:1", "generalist", mandatory=True),
    _proposal("wu:1", "proof_golf"),
    _proposal("wu:1", "duplication", eligible=False),
]


def _pool_file(tmp_path):
    rows = []
    for proposal in PROPOSALS:
        rows.append({
            "invocation_id": proposal["invocation_id"],
            "arm_id": proposal["arm_id"],
            "work_unit_id": proposal["work_unit_id"],
            "spec_id": None if proposal["arm_id"] == "generalist" else proposal["arm_id"],
            "rendered_prompt_sha256": "a" * 64,
            "task_data": {"task_type": "lean_pr_review_v5_arm",
                          "task_id": "pr5_" + proposal["invocation_id"]},
        })
    path = tmp_path / "arm_pool.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    return path


@pytest.fixture
def lead(tmp_path):
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    data = LeanPRReviewV5LeadData(
        task_id="pr5lead_test", episode_id="ep:1", pr_number=33098,
        pr_title="t", pr_description="d", diff="--- a\n+++ b\n",
        changed_files=["Mathlib/A.lean"], proposals=list(PROPOSALS),
        census=list(CENSUS),
        arm_pool_path=str(_pool_file(tmp_path)),
        trace_path=str(tmp_path / "trace.jsonl"),
        target_workspace={"name": "target", "commit_hash": "c" * 40,
                          "repo_url": "https://example.invalid/m.git",
                          "default_target": "Mathlib"},
    )
    task = LeanPRReviewV5LeadTask(data, ApeAgentConfig())
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    return task, mcp.tools


def test_the_lead_task_is_registered():
    from ape.tasks.base import get_task_class

    assert get_task_class(LEAD_TASK_TYPE) is LeanPRReviewV5LeadTask


def test_the_agenda_is_ranked_work_units_not_a_hash_ordered_page(lead):
    """The change this replaced: a page of (arm, unit) pairs ordered by content hash, which
    let nine of eleven leads see 5 of 56 work units and route from that."""

    _task, tools = lead
    agenda = asyncio.run(tools["read_agenda"]())
    assert agenda["work_units_total"] == 1
    row = agenda["ranked_work_units"][0]
    assert row["rank"] == 1
    assert row["work_unit_id"] == "wu:1"


def test_each_row_says_why_it_ranked_there(lead):
    """A rank with no reason is just a different arbitrary order."""

    _task, tools = lead
    row = asyncio.run(tools["read_agenda"]())["ranked_work_units"][0]
    assert row["why"] and "tactic steps" in row["why"][0]
    assert row["suggested_arms"] == ["proof_golf", "proof_idiom"]


def test_each_row_carries_the_ids_delegate_needs(lead):
    """The lead routes straight from this; a row without proposal ids is unroutable."""

    _task, tools = lead
    row = asyncio.run(tools["read_agenda"]())["ranked_work_units"][0]
    assert row["available_arms"]["proof_golf"] == "wu:1#proof_golf"


def test_the_lead_is_told_how_much_it_has_not_seen(lead):
    """Truncation is fine; silent truncation is what caused the failure."""

    _task, tools = lead
    agenda = asyncio.run(tools["read_agenda"](top=1))
    assert agenda["remaining_below"] == 0
    assert agenda["showing"] == [1, 1]
    assert agenda["mandatory_generalist_jobs"] == 1


def test_task_data_without_a_census_still_serves_the_agenda(tmp_path):
    """Older runs carry no census; falling back beats returning nothing."""

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    data = LeanPRReviewV5LeadData(
        task_id="t", episode_id="ep:1", pr_number=33098, pr_title="t", pr_description="d",
        diff="d", changed_files=["A.lean"], proposals=list(PROPOSALS), census=[],
        arm_pool_path=str(_pool_file(tmp_path)),
        target_workspace={"name": "target", "commit_hash": "c" * 40,
                          "repo_url": "https://e.invalid/m.git", "default_target": "Mathlib"})
    task = LeanPRReviewV5LeadTask(
        data, ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    agenda = asyncio.run(mcp.tools["read_agenda"]())
    assert agenda["ranked"] is False
    assert agenda["total"] == 2


def test_a_job_outside_the_pool_is_refused(lead):
    """The pre-registration boundary: every runnable pair was rendered and hashed before the
    run, so a pair with no rendered prompt is one the plan cannot vouch for."""

    task, tools = lead
    task._state()["floor_done"] = True   # isolate job validation from the wave-1 injection
    task._state()["comprehension"] = {"summary": "s", "questions": []}
    result = asyncio.run(tools["delegate"](jobs=[
        {"arm_id": "proof_golf", "work_unit_id": "wu:does-not-exist"}]))
    assert result["success"] is False
    assert "no prompt was rendered" in result["rejected"][0]["reason"]


def test_a_job_naming_neither_a_proposal_nor_a_pair_is_refused(lead):
    task, tools = lead
    task._state()["floor_done"] = True
    task._state()["comprehension"] = {"summary": "s", "questions": []}
    result = asyncio.run(tools["delegate"](jobs=[{"budget_tier": "deep"}]))
    assert result["success"] is False
    assert "proposal_id" in result["rejected"][0]["reason"]


def test_unselected_proposals_are_pruned_automatically(lead):
    """The ledger guarantee is kept; the bookkeeping is the runner's job, not the model's.

    Requiring the lead to serialize a prune record for every proposal killed one: with 184
    proposals the largest agenda gave one lead ~46 to transcribe, and it spent four rejected
    `submit_routing` calls and its whole budget failing to, hitting `paused_cost_limit`
    having reviewed nothing.
    """

    task, tools = lead
    # The floor runs as wave 1 through `delegate`; simulate it having done so.
    task._state()["floor_done"] = True
    result = asyncio.run(tools["submit_routing"](pruned=[], candidate_assessments=[]))
    assert result["evaluation_result"].success is True

    records, _responses, _gaps = task._reconcile([])
    dispositions = {item["invocation_id"]: item["disposition"] for item in records}
    # Every non-mandatory proposal still ends with a disposition — nothing goes missing.
    assert dispositions["wu:1#proof_golf"] == "pruned"
    assert dispositions["wu:1#duplication"] == "pruned"
    assert all(item["reason"] for item in records if item["disposition"] == "pruned")


def test_an_auto_pruned_proposal_is_marked_as_such(lead):
    """A default reason must be distinguishable from one the lead actually gave, or the
    trace cannot tell a considered decision from an unmentioned one."""

    task, _tools = lead
    records, _responses, _gaps = task._reconcile([
        {"proposal_id": "wu:1#proof_golf", "reason": "no proof was modified here"}])
    by_id = {item["invocation_id"]: item for item in records}
    assert by_id["wu:1#proof_golf"]["reason_given"] is True
    assert by_id["wu:1#duplication"]["reason_given"] is False
    assert by_id["wu:1#duplication"]["reason"] == "not selected by the lead"


def test_pruning_everything_is_a_valid_review(lead):
    """A lead that runs no specialist has still made a decision, and the generalist floor
    ran regardless — so this must be recordable, not an error."""

    task, tools = lead
    task._state()["floor_done"] = True
    result = asyncio.run(tools["submit_routing"](
        pruned=[{"proposal_id": "wu:1#proof_golf", "reason": "no proof was modified here"},
                {"proposal_id": "wu:1#duplication", "reason": "not a new declaration"}],
        candidate_assessments=[], message="nothing worth a specialist"))
    assert result["evaluation_result"].success is True


def test_a_pruned_proposal_is_recorded_with_its_reason(lead):
    task, tools = lead
    asyncio.run(tools["submit_routing"](pruned=[
        {"proposal_id": "wu:1#proof_golf", "reason": "no proof was modified here"},
        {"proposal_id": "wu:1#duplication", "reason": "not a new declaration"}]))
    records, _responses, _gaps = task._reconcile([
        {"proposal_id": "wu:1#proof_golf", "reason": "no proof was modified here"},
        {"proposal_id": "wu:1#duplication", "reason": "not a new declaration"}])
    by_id = {item["invocation_id"]: item for item in records}
    assert by_id["wu:1#proof_golf"]["disposition"] == "pruned"
    assert by_id["wu:1#proof_golf"]["reason"] == "no proof was modified here"
    assert by_id["wu:1#proof_golf"]["status"] is None


def test_assessments_reach_the_result_and_are_applied_only_subtractively(lead):
    """The v1 contract was "recorded, never applied"; §3 replaced it with a narrower one.

    Assessments are now consumed by `finalize`, so the guarantee cannot be "nothing reads
    them" any more. It is the boundary instead: `synthesis.apply_assessments` returns
    subsets of the candidate lists it is given, so no assessment can introduce a candidate,
    and admission still belongs to the evidence chain.
    """

    task, tools = lead
    assessment = {"invocation_id": "wu:1#proof_golf", "candidate_ordinal": 0,
                  "verdict": "drop", "reason": "duplicates the generalist"}
    asyncio.run(tools["submit_routing"](
        pruned=[{"proposal_id": "wu:1#proof_golf", "reason": "r"},
                {"proposal_id": "wu:1#duplication", "reason": "r"}],
        candidate_assessments=[assessment]))

    import inspect

    from src.mathlib_review.review import finalize as finalize_module

    assert "candidate_assessments" in inspect.signature(
        finalize_module.finalize).parameters
    # Synthesis runs before the gate, never after it: a dropped candidate must not reach
    # the evidence chain, and a kept one must not skip it.
    source = inspect.getsource(finalize_module.finalize)
    assert source.index("= apply_assessments(") < source.index("= collect_supported(")


def test_the_lead_does_not_expose_a_findings_tool(lead):
    """It routes; it does not author. A `submit_findings` here would let it publish directly,
    bypassing every gate."""

    _task, tools = lead
    assert "submit_findings" not in tools
    assert set(tools) == {"lean_verify_edit", "read_agenda", "submit_comprehension",
                          "delegate", "submit_routing"}


# --------------------------------------------------------------------------------------
# the coverage floor, now the lead's own first wave
# --------------------------------------------------------------------------------------

def test_submission_is_refused_until_the_floor_has_run(lead):
    """Folding the floor into the lead must not make it skippable. Before this, the floor was
    a separate orchestrator the runner drove; now it is injected into the lead's first
    `delegate` call, and this is the guard that keeps "not the lead's to cut" true."""

    _task, tools = lead
    result = asyncio.run(tools["submit_routing"](pruned=[], candidate_assessments=[]))
    assert result["evaluation_result"].success is False
    message = result["evaluation_result"].message
    assert "has not run" in message
    # It must say how to fix it, not merely refuse.
    assert "delegate" in message and "empty" in message


def test_the_floor_does_not_spend_the_delegation_budget(lead):
    """Counting 22 mandatory generalist jobs against `max_delegations` would leave a budget
    of 30 with eight specialists on a 22-unit PR — a formality, not a routing decision."""

    task, _tools = lead
    from ape.tasks.lean_tasks.formal_math.pr_review_v5.delegation import JobSpec

    state = task._state()
    for disposition, invocation in (("mandatory", "wu:1#generalist"),
                                    ("proposed", "wu:1#proof_golf")):
        spec = JobSpec(invocation, invocation.split("#")[1], "wu:1", 1, {},
                       disposition=disposition)
        state["outcomes"][invocation] = (object(), spec)
    assert task._specialist_count(state) == 1


def test_the_lead_prompt_describes_the_floor_as_its_first_wave():
    from ape.tasks.lean_tasks.formal_math.pr_review_v5.prompts import LEAD_SYSTEM

    assert "first wave is a broad sweep you do not choose" in LEAD_SYSTEM
    assert "empty `jobs` list" in LEAD_SYSTEM
    assert "does not count against your delegation budget" in LEAD_SYSTEM


def test_the_runner_no_longer_drives_a_separate_floor():
    """One agent per PR delegating all of its own work is the shape the generation is named
    for; a floor orchestrator outside the lead was a departure from it."""

    import inspect

    from src.mathlib_review.review import runner

    assert not hasattr(runner, "_mandatory_arm_task_data")
    assert not hasattr(runner, "_floor_delegation_records")
    assert not hasattr(runner, "_floor_summary")
    # One top-level orchestrator, whatever the routing mode: the specialists and the floor
    # are both nested under the lead. (`mandatory_floor_cost` survives as a dry-run
    # projection, which is a cost estimate rather than an execution path.)
    source = inspect.getsource(runner.run)
    assert source.count("TaskOrchestrator(") == 1
    assert 'orchestrator_id=f"{dataset.run_name}_floor"' not in source


def test_the_per_pr_cost_cap_is_actually_enforced(lead):
    """It was a label for six runs. The per-job cap bounds one subagent and
    `max_delegations` bounds their number, but neither bounds the product — and the lead's
    own `sample_max_cost` never sees nested spend, because subagents run in their own
    orchestrator. At 22 work units that gap was affordable; at 203 it is not."""

    task, tools = lead
    state = task._state()
    state["floor_done"] = True
    state["comprehension"] = {"summary": "s", "questions": []}
    state["delegated_spend"] = task._task_config().per_pr_cost_cap + 0.01
    result = asyncio.run(tools["delegate"](jobs=[
        {"proposal_id": "wu:1#proof_golf", "budget_tier": "standard"}]))
    assert result["success"] is False
    assert "per-PR cost cap" in result["rejected"][0]["reason"]


def test_remaining_budget_is_reported_back(lead):
    """A lead that cannot see what it has left cannot ration it."""

    import inspect

    from ape.tasks.lean_tasks.formal_math.pr_review_v5 import lead as lead_module

    assert "spend_remaining" in inspect.getsource(lead_module)


def test_the_floor_does_not_consume_the_per_pr_cost_cap(lead):
    """The mirror of `test_the_floor_does_not_spend_the_delegation_budget`, and the defect
    that made the held-out run uninterpretable: PR 33149 had 108 work units, so its floor
    cost $10.05 against a $1.50 cap and every specialist request was refused. The cap bound
    hardest on the largest PR — the one where routing mattered most."""

    task, tools = lead
    state = task._state()
    state["floor_done"] = True
    state["comprehension"] = {"summary": "s", "questions": []}
    state["spend"] = 10.05          # a large floor
    state["delegated_spend"] = 0.0  # but nothing the lead chose
    # Stub the executor: what is under test is the admission decision, not the spawn.
    import ape.tasks.lean_tasks.formal_math.pr_review_v5.lead as lead_module

    async def _no_jobs(*_a, **_k):
        return []

    original = lead_module.run_jobs
    lead_module.run_jobs = _no_jobs
    try:
        result = asyncio.run(tools["delegate"](jobs=[
            {"proposal_id": "wu:1#proof_golf", "budget_tier": "standard"}]))
    finally:
        lead_module.run_jobs = original
    # Not refused on cost grounds: the floor is not a routing decision.
    assert not any("cost cap" in r["reason"] for r in result.get("rejected", []))


# --- comprehension precedes delegation --------------------------------------------------

def test_nothing_is_delegated_before_the_lead_has_read_the_pr(lead):
    """A lead that dispatches before saying what the change is doing is routing on the
    diff's surface. The gate sits on `delegate` rather than in an optional preamble because
    the coverage floor rides that same call."""

    _task, tools = lead
    result = asyncio.run(tools["delegate"](jobs=[]))
    assert result["success"] is False
    assert "submit_comprehension" in result["message"]


def test_comprehension_refuses_an_assertion_dressed_as_a_question(lead):
    """An arm handed a conclusion confirms it, and a confirmed conclusion is not evidence.
    The check is structural — there is nowhere here to put a severity or a fix, and an entry
    that does not ask something is rejected outright."""

    _task, tools = lead
    result = asyncio.run(tools["submit_comprehension"](
        summary="Deprecates the old spelling across the library.",
        questions=[{"kind": "convention",
                    "question": "`foo_bar` should be renamed to `foo_of_baz`."}]))
    assert result["success"] is False
    assert "not questions" in result["message"]


def test_comprehension_accepts_questions_and_opens_the_gate(lead):
    task, tools = lead
    ok = asyncio.run(tools["submit_comprehension"](
        summary="Adds a dualised API and deprecates the old spelling.",
        questions=[{"kind": "duality",
                    "question": "Does the infimum side reuse the supremum lemma, or "
                                "duplicate its argument?",
                    "arms": ["generality"]}]))
    assert ok["success"] is True and ok["questions_recorded"] == 1
    assert task._state()["comprehension"]["summary"].startswith("Adds a dualised")


def test_comprehension_requires_a_summary(lead):
    _task, tools = lead
    result = asyncio.run(tools["submit_comprehension"](summary="   ", questions=[]))
    assert result["success"] is False


def test_comprehension_is_submitted_once(lead):
    _task, tools = lead
    asyncio.run(tools["submit_comprehension"](summary="A rename.", questions=[]))
    again = asyncio.run(tools["submit_comprehension"](summary="Something else.", questions=[]))
    assert again["success"] is False


# --- coverage gaps ----------------------------------------------------------------------
#
# A mandatory job that RAN and failed used to be indistinguishable from one that ran and found
# nothing: `_reconcile` only asked whether the invocation was in `outcomes`, and a failed job
# is. On PR 33117 the family_design floor job exhausted its budget, was booked as
# `status=failed cost=0.0`, and satisfied the coverage check -- so the run reported
# `units_without_specialist: []`, which is the field used to green-light a specialist-only run.


def _record_outcome(task, invocation_id, *, disposition, status, error=None):
    """Put a finished job into the lead's state the way `delegate` would."""

    from types import SimpleNamespace

    outcome = SimpleNamespace(
        invocation_id=invocation_id, arm_id=invocation_id.split("#")[-1],
        work_unit_id=invocation_id.split("#")[0], pr_number=1,
        status=status, cost=0.0, nominal_cost=0.0, error=error,
        candidates=[], verification_artifacts=[], result_sha256=None,
        budget_tier="standard", budget_cap=0.3, wall_seconds=1.0,
        token_usage=None, delivered_prompt_sha256="x",
    )
    spec = SimpleNamespace(
        invocation_id=invocation_id, proposal_id=invocation_id,
        disposition=disposition, reason="", brief=None,
        payload={"rendered_prompt_sha256": "x"},
    )
    task._state()["outcomes"][invocation_id] = (outcome, spec)


def test_a_failed_mandatory_job_is_a_coverage_gap_not_coverage(lead):
    task, _tools = lead
    _record_outcome(task, "wu:1#generalist", disposition="mandatory",
                    status="paused_cost", error="cost limit reached")

    _records, _responses, gaps = task._reconcile([])

    assert [g["invocation_id"] for g in gaps] == ["wu:1#generalist"]
    assert gaps[0]["status"] == "paused_cost"
    assert gaps[0]["reason"] == "cost limit reached"


def test_a_successful_mandatory_job_leaves_no_gap(lead):
    task, _tools = lead
    _record_outcome(task, "wu:1#generalist", disposition="mandatory", status="success")

    _records, _responses, gaps = task._reconcile([])
    assert gaps == []


def test_a_failed_discretionary_job_is_not_a_coverage_gap(lead):
    """Coverage is a promise about mandatory work. A specialist the lead chose to run and
    which failed is a routing outcome, not a hole in what the run guaranteed to look at."""

    task, _tools = lead
    _record_outcome(task, "wu:1#proof_golf", disposition="delegated",
                    status="failed", error="boom")

    _records, _responses, gaps = task._reconcile([])
    assert "wu:1#proof_golf" not in {g["invocation_id"] for g in gaps}
    # The fixture's own mandatory job was never dispatched, so it is a gap — which is the
    # other half of the rule and worth asserting here rather than assuming it away.
    assert {g["invocation_id"] for g in gaps} == {"wu:1#generalist"}
    assert gaps[0]["status"] == "never_ran"


# --- budget reservations ------------------------------------------------------------------


def test_a_single_wave_cannot_overshoot_the_per_pr_cap(lead):
    """`delegated_spend` only updates once a wave has finished, so checking it at request time
    meant every job in a wave saw the same pre-wave figure. One `delegate` call with 25 `deep`
    jobs at a $0.30 standard cap could authorise $15 against a $1.50 cap, and the check passed
    25 times.

    Both jobs here are refused, so nothing is dispatched and no subtask is spawned.
    """

    task, tools = lead
    # `_task_config()` builds a fresh object on every call, so the caps have to be set where
    # it reads them from.
    task.config.task_config = task.task_config_class(
        per_pr_cost_cap=0.10, standard_budget_cap=0.30)   # cap < one standard job's ceiling

    state = task._state()
    state["floor_done"] = True
    state["comprehension"] = {"summary": "s", "questions": []}

    result = asyncio.run(tools["delegate"](jobs=[
        {"proposal_id": "wu:1#proof_golf"},
        {"proposal_id": "wu:1#duplication"},
    ]))

    assert result["success"] is False
    assert len(result["rejected"]) == 2
    for row in result["rejected"]:
        assert "cost cap would be exceeded" in row["reason"]
    # Nothing was dispatched, so nothing is held.
    assert state["reserved"] == 0.0 or state["reserved"] == pytest.approx(0.0)


def test_a_deep_job_reserves_more_than_a_standard_one(lead):
    """The reservation is the job's ceiling, so tier has to enter it — otherwise a wave of
    `deep` jobs is bounded as though it were cheap."""

    task, tools = lead
    # A deep job reserves 2x standard: $0.60. The cap is $0.45, so the deep job is refused
    # while a standard one at $0.30 would have been accepted.
    task.config.task_config = task.task_config_class(
        per_pr_cost_cap=0.45, standard_budget_cap=0.30)

    state = task._state()
    state["floor_done"] = True
    state["comprehension"] = {"summary": "s", "questions": []}

    result = asyncio.run(tools["delegate"](jobs=[
        {"proposal_id": "wu:1#proof_golf", "budget_tier": "deep"}]))

    assert result["success"] is False
    assert "0.60" in result["rejected"][0]["reason"]
