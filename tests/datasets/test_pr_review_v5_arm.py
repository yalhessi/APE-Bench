"""The specialist arm inherits v4's candidate contract whole, and must keep inheriting it.

Subclassing rather than reimplementing is the whole design of this task: everything that
makes a candidate anchorable — `change_ids ⊆ unit`, `primary_subject` equality, the entity
check, the statement gate, edit confinement, the compile-backed gate — lives in
`submit_candidates`, and a second implementation would be a second thing to keep correct.

The risk a subclass introduces is *silent* divergence: an override that looks like a small
convenience but re-implements one of those checks slightly differently. So these tests pin
both that the checks still fire through the v5 class, and that v5 has not taken ownership of
the methods that implement them.
"""

from __future__ import annotations

import asyncio

import pytest

from ape.tasks.lean_tasks.formal_math.pr_review_v4.candidates import (
    CandidateSubmission,
    LeanPRReviewV4CandidateTask,
)
from ape.tasks.lean_tasks.formal_math.pr_review_v5.arm import (
    ARM_TASK_TYPE,
    LeanPRReviewV5ArmData,
    LeanPRReviewV5ArmTask,
)


class FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, **_kwargs):
        def decorate(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorate


def _data(**overrides):
    payload = dict(
        task_id="pr5_test",
        invocation_id="wu:abc#proof_golf",
        arm_id="proof_golf",
        spec_id="proof_golf",
        work_unit_id="wu:abc",
        episode_id="ep:abc",
        pr_number=33098,
        diff="--- a\n+++ b\n",
        changed_files=["Mathlib/A.lean", "Mathlib/B.lean"],
        change_ids=["change:a"],
        entity_ids_by_change={"change:a": ["entity:1"]},
        primary_subjects_by_change={"change:a": "Foo.bar"},
        paths_by_change={"change:a": "Mathlib/A.lean"},
        rendered_system_prompt="sys",
        rendered_user_prompt="usr",
        rendered_prompt_sha256="a" * 64,
        submission_verification_policy="none",
        context_tools=[],
        target_workspace={
            "name": "target", "commit_hash": "c" * 40,
            "repo_url": "https://example.invalid/mathlib4.git", "default_target": "Mathlib",
        },
    )
    payload.update(overrides)
    return LeanPRReviewV5ArmData(**payload)


@pytest.fixture
def submit():
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = LeanPRReviewV5ArmTask(_data(), ApeAgentConfig())
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    return mcp.tools["submit_candidates"]


def _candidate(**overrides):
    """Built as the submission model, because that is what FastMCP hands the tool."""

    payload = dict(
        primary_change_id="change:a",
        primary_entity_id="entity:1",
        primary_subject="Foo.bar",
        change_ids=["change:a"],
        concern_family="proof-golf",
        issue_kind="proof_simplification",
        concern_label="proof-golf",
        severity="advisory",
        claim="The proof of bar can be shorter.",
        requested_change="Replace the proof of bar with a one-liner.",
        proposed_edit={
            "path": "Mathlib/A.lean",
            "declaration_name": "Foo.bar",
            "new_declaration": "theorem Foo.bar : True := trivial",
        },
    )
    payload.update(overrides)
    return CandidateSubmission(**payload)


def _message(result):
    return result["evaluation_result"].message


def test_a_well_formed_candidate_is_accepted(submit):
    result = asyncio.run(submit(candidates=[_candidate()]))
    assert result["evaluation_result"].success is True


def test_a_claim_outside_the_work_unit_is_rejected(submit):
    result = asyncio.run(submit(candidates=[
        _candidate(change_ids=["change:z"], primary_change_id="change:z")]))
    assert result["evaluation_result"].success is False
    assert "unknown change_ids" in _message(result)


def test_a_mismatched_subject_is_rejected(submit):
    result = asyncio.run(submit(candidates=[_candidate(primary_subject="Foo.baz")]))
    assert result["evaluation_result"].success is False
    assert "primary_subject" in _message(result)


def test_a_wrong_entity_is_rejected(submit):
    result = asyncio.run(submit(candidates=[_candidate(primary_entity_id="entity:9")]))
    assert result["evaluation_result"].success is False
    assert "primary_entity_id" in _message(result)


def test_a_cross_file_edit_is_rejected(submit):
    """`Mathlib/B.lean` is one of the PR's changed files, so only per-target confinement
    catches this. Without it the verifier compiles B and awards the claim about A."""

    result = asyncio.run(submit(candidates=[_candidate(proposed_edit={
        "path": "Mathlib/B.lean",
        "declaration_name": "Foo.bar",
        "new_declaration": "theorem Foo.bar : True := trivial",
    })]))
    assert result["evaluation_result"].success is False
    assert "primary change target" in _message(result)


def test_an_ambiguous_edit_is_rejected(submit):
    """Both modes fully specified. Which one applies decides what gets compiled, so an edit
    that says both is not a preference to resolve — it is two different edits."""

    result = asyncio.run(submit(candidates=[_candidate(proposed_edit={
        "path": "Mathlib/A.lean",
        "declaration_name": "Foo.bar",
        "new_declaration": "theorem Foo.bar : True := trivial",
        "line_start": 1, "line_end": 2, "replacement": "x",
    })]))
    assert result["evaluation_result"].success is False
    assert "exactly one complete mode" in _message(result)


def test_an_edit_specifying_no_mode_is_rejected(submit):
    result = asyncio.run(submit(candidates=[
        _candidate(proposed_edit={"path": "Mathlib/A.lean"})]))
    assert result["evaluation_result"].success is False
    assert "exactly one complete mode" in _message(result)


def test_a_line_mode_edit_is_accepted(submit):
    """The other legitimate mode; the contract must not have quietly become decl-only."""

    result = asyncio.run(submit(candidates=[_candidate(proposed_edit={
        "path": "Mathlib/A.lean", "line_start": 1, "line_end": 2,
        "replacement": "theorem Foo.bar : True := trivial",
    })]))
    assert result["evaluation_result"].success is True


def test_v5_does_not_reimplement_any_part_of_the_contract():
    """The structural half. An override of any of these is a second implementation of a
    check that is measured, and would drift from the version the baseline was measured under.
    """

    owned = set(LeanPRReviewV5ArmTask.__dict__)
    # The checks themselves. A second implementation of any of these drifts from the version
    # the v2 recall baseline was measured under.
    for method in ("_verify_candidate_submission", "_statement_gate_error"):
        assert method not in owned, (
            f"{method} is overridden in the v5 arm; the candidate contract must stay "
            "single-implementation"
        )
    # `_extra_candidate_error` is the opposite: v4 declares it as the hook a subclass uses to
    # add its own *scope* rule — "rather than reimplementing the rest and drifting from it".
    # v5 uses it to keep a specialist inside its own concern family.
    assert "_extra_candidate_error" in owned
    # The one legitimate override extends rather than replaces.
    import inspect

    source = inspect.getsource(LeanPRReviewV5ArmTask.register_task_tools)
    assert "super().register_task_tools(mcp)" in source


def test_the_arm_is_a_v4_candidate_task():
    assert issubclass(LeanPRReviewV5ArmTask, LeanPRReviewV4CandidateTask)
    assert LeanPRReviewV5ArmTask.task_type == ARM_TASK_TYPE


def test_identity_comes_from_the_invocation_not_the_model():
    """Golf and idiom both declare `proof_simplification` but make different claims, and the
    verifier keys its warrant on the spec. A self-reported label would let a golf run inherit
    idiom's laxer rule."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = LeanPRReviewV5ArmTask(_data(), ApeAgentConfig())
    result = task.create_result(
        success=True, score=1.0, pr_number=33098, work_unit_id="wu:abc",
        rendered_prompt_sha256="a" * 64, candidates=[], verification_artifacts=[],
        findings=[], review_message="",
    )
    assert result.invocation_id == "wu:abc#proof_golf"
    assert result.arm_id == "proof_golf"
    assert result.spec_id == "proof_golf"


# --------------------------------------------------------------------------------------
# concern discipline
# --------------------------------------------------------------------------------------

def test_a_specialist_cannot_claim_outside_its_concern(submit):
    """The rep2 failure: the `generality` arm submitted four candidates in `style` and
    `naming`. Those families are not checkable, so no verification artifact was required at
    submission — and `focused_findings` then dropped all four at finalization for having no
    artifact, silently. Rejecting now is what turns a silent deletion into a fixable error."""

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = LeanPRReviewV5ArmTask(
        _data(arm_id="generality", spec_id="generality"),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    result = asyncio.run(mcp.tools["submit_candidates"](candidates=[_candidate(
        concern_family="style", issue_kind="style_norm_violation", concern_label="style")]))
    assert result["evaluation_result"].success is False
    message = _message(result)
    assert "generality check" in message and "generalization" in message
    # It must say what to do, not merely that the claim is wrong.
    assert "drop it" in message


def test_a_specialist_may_make_its_own_kind_of_claim(submit):
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = LeanPRReviewV5ArmTask(
        _data(arm_id="duplication", spec_id="duplication"),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    result = asyncio.run(mcp.tools["submit_candidates"](candidates=[_candidate(
        concern_family="duplication", issue_kind="duplicate_implementation",
        concern_label="duplication")]))
    assert result["evaluation_result"].success is True


def test_golf_and_idiom_share_a_family_but_stay_distinct():
    """They inspect the same proofs and make different claims; `spec_id` keeps them apart,
    not the concern family. Splitting them by family would repeal one arm's warrant."""

    from ape.tasks.lean_tasks.formal_math.pr_review_v5.arm import ALLOWED_CONCERN_BY_ARM

    assert ALLOWED_CONCERN_BY_ARM["proof_golf"] == ALLOWED_CONCERN_BY_ARM["proof_idiom"]
    assert ALLOWED_CONCERN_BY_ARM["proof_golf"] == {"proof-golf"}


def test_the_generalist_has_no_concern_filter(submit):
    """It is the control: same sites and tools as the specialists, covering the families no
    specialist exists for. A filter here would remove the thing it is for."""

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.pr_review_v5.arm import ALLOWED_CONCERN_BY_ARM

    assert "generalist" not in ALLOWED_CONCERN_BY_ARM
    task = LeanPRReviewV5ArmTask(
        _data(arm_id="generalist", spec_id=None),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    result = asyncio.run(mcp.tools["submit_candidates"](candidates=[_candidate(
        concern_family="documentation", issue_kind="documentation_gap",
        concern_label="documentation")]))
    assert result["evaluation_result"].success is True
