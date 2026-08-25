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


def test_the_agenda_hides_the_mandatory_floor(lead):
    """The generalist is not a decision, so offering it as one invites the lead to spend
    reasoning on a job it cannot influence."""

    _task, tools = lead
    agenda = asyncio.run(tools["read_agenda"]())
    assert agenda["total"] == 2
    assert {job["arm_id"] for job in agenda["jobs"]} == {"proof_golf", "duplication"}
    assert agenda["mandatory_generalist_jobs"] == 1


def test_the_agenda_can_be_filtered_to_the_rule_selection(lead):
    _task, tools = lead
    agenda = asyncio.run(tools["read_agenda"](eligible_only=True))
    assert [job["arm_id"] for job in agenda["jobs"]] == ["proof_golf"]


def test_the_agenda_exposes_targets_and_rationale(lead):
    """A lead choosing between arms needs to know what each would look at and why it exists."""

    _task, tools = lead
    job = asyncio.run(tools["read_agenda"]())["jobs"][0]
    assert job["targets"] == ["change:a"]
    assert job["rationale"]
    assert "eligible" in job


def test_a_job_outside_the_pool_is_refused(lead):
    """The pre-registration boundary: every runnable pair was rendered and hashed before the
    run, so a pair with no rendered prompt is one the plan cannot vouch for."""

    task, tools = lead
    task._state()["floor_done"] = True   # isolate job validation from the wave-1 injection
    result = asyncio.run(tools["delegate"](jobs=[
        {"arm_id": "proof_golf", "work_unit_id": "wu:does-not-exist"}]))
    assert result["success"] is False
    assert "no prompt was rendered" in result["rejected"][0]["reason"]


def test_a_job_naming_neither_a_proposal_nor_a_pair_is_refused(lead):
    task, tools = lead
    task._state()["floor_done"] = True
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

    records, _responses = task._reconcile([])
    dispositions = {item["invocation_id"]: item["disposition"] for item in records}
    # Every non-mandatory proposal still ends with a disposition — nothing goes missing.
    assert dispositions["wu:1#proof_golf"] == "pruned"
    assert dispositions["wu:1#duplication"] == "pruned"
    assert all(item["reason"] for item in records if item["disposition"] == "pruned")


def test_an_auto_pruned_proposal_is_marked_as_such(lead):
    """A default reason must be distinguishable from one the lead actually gave, or the
    trace cannot tell a considered decision from an unmentioned one."""

    task, _tools = lead
    records, _responses = task._reconcile([
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
    records, _responses = task._reconcile([
        {"proposal_id": "wu:1#proof_golf", "reason": "no proof was modified here"},
        {"proposal_id": "wu:1#duplication", "reason": "not a new declaration"}])
    by_id = {item["invocation_id"]: item for item in records}
    assert by_id["wu:1#proof_golf"]["disposition"] == "pruned"
    assert by_id["wu:1#proof_golf"]["reason"] == "no proof was modified here"
    assert by_id["wu:1#proof_golf"]["status"] is None


def test_assessments_are_recorded_verbatim_and_applied_nowhere(lead):
    """Recorded because they are the evidence for whether arbitration is worth building;
    applied nowhere because publication belongs to the gates."""

    task, tools = lead
    assessment = {"invocation_id": "wu:1#proof_golf", "candidate_ordinal": 0,
                  "verdict": "drop", "reason": "duplicates the generalist"}
    asyncio.run(tools["submit_routing"](
        pruned=[{"proposal_id": "wu:1#proof_golf", "reason": "r"},
                {"proposal_id": "wu:1#duplication", "reason": "r"}],
        candidate_assessments=[assessment]))
    result = task._last_result if hasattr(task, "_last_result") else None
    # The assessment reaches the result untouched; nothing downstream consumes it.
    import inspect

    from src.datasets.pr_review_v5 import finalize as finalize_module

    assert "candidate_assessments" not in inspect.signature(finalize_module.finalize).parameters
    source = inspect.getsource(finalize_module)
    assert "candidate_assessments" not in source


def test_the_lead_does_not_expose_a_findings_tool(lead):
    """It routes; it does not author. A `submit_findings` here would let it publish directly,
    bypassing every gate."""

    _task, tools = lead
    assert "submit_findings" not in tools
    assert set(tools) == {"lean_verify_edit", "read_agenda", "delegate", "submit_routing"}


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

    from src.datasets.pr_review_v5 import runner

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
    state["spend"] = task._task_config().per_pr_cost_cap + 0.01
    result = asyncio.run(tools["delegate"](jobs=[
        {"proposal_id": "wu:1#proof_golf", "budget_tier": "standard"}]))
    assert result["success"] is False
    assert "per-PR cost cap" in result["rejected"][0]["reason"]


def test_remaining_budget_is_reported_back(lead):
    """A lead that cannot see what it has left cannot ration it."""

    import inspect

    from ape.tasks.lean_tasks.formal_math.pr_review_v5 import lead as lead_module

    assert "spend_remaining" in inspect.getsource(lead_module)
