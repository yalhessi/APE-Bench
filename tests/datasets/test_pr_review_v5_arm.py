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

from ape.tasks.lean_tasks.formal_math.review.candidates import (
    CandidateSubmission,
    LeanPRReviewV4CandidateTask,
)
from ape.tasks.lean_tasks.formal_math.review.arm import (
    ARM_TASK_TYPE,
    ReviewArmData,
    ReviewArmTask,
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
    return ReviewArmData(**payload)


@pytest.fixture
def submit():
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = ReviewArmTask(_data(), ApeAgentConfig())
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

    owned = set(ReviewArmTask.__dict__)
    # The checks themselves. A second implementation of any of these drifts from the version
    # the v2 recall baseline was measured under.
    for method in ("_verify_candidate_submission", "_statement_gate_error"):
        assert method not in owned, (
            f"{method} is overridden in the v5 arm; the candidate contract must stay "
            "single-implementation"
        )
    # The hooks are the opposite: v4 declares them as what a subclass extends through, "rather
    # than reimplementing the rest and drifting from it". v5 used `_extra_candidate_error` to
    # keep a specialist inside its concern family and now uses `_annotate_candidate` to record
    # when it does not — a rule that decides what may be said, moved to one that records what
    # was said. Either is the sanctioned seam; reimplementing a check is not.
    assert "_annotate_candidate" in owned
    # The one legitimate override extends rather than replaces.
    import inspect

    source = inspect.getsource(ReviewArmTask.register_task_tools)
    assert "super().register_task_tools(mcp)" in source


def test_the_arm_is_a_v4_candidate_task():
    assert issubclass(ReviewArmTask, LeanPRReviewV4CandidateTask)
    assert ReviewArmTask.task_type == ARM_TASK_TYPE


def test_identity_comes_from_the_invocation_not_the_model():
    """Golf and idiom both declare `proof_simplification` but make different claims, and the
    verifier keys its warrant on the spec. A self-reported label would let a golf run inherit
    idiom's laxer rule."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = ReviewArmTask(_data(), ApeAgentConfig())
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

def test_a_specialist_claiming_outside_its_concern_is_recorded_not_refused(submit):
    """The rep2 failure and the fix that replaced the fix.

    The `generality` arm submitted four candidates in `style` and `naming`. Those families are
    not checkable, so no verification artifact was required at submission — and
    `focused_findings` then dropped all four at finalization for having no artifact, silently.
    Refusing the submission turned that silent deletion into a fixable error, which was an
    improvement and cost findings: 11 of the 19 gold obligations labelled `style` are `grind`
    simplifications and `encard_` renames, so an arm that finds one and labels it honestly was
    refused for guessing the evaluator's vocabulary wrong.

    Finalization now retains every drop as a `diagnostic` finding, so the deletion is not
    silent whether or not submission refuses. Refusing buys nothing and still costs that.
    """

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = ReviewArmTask(
        _data(arm_id="generality", spec_id="generality"),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    result = asyncio.run(mcp.tools["submit_candidates"](candidates=[_candidate(
        concern_family="style", issue_kind="style_norm_violation", concern_label="style")]))
    assert result["evaluation_result"].success is True


def test_claiming_outside_its_concern_leaves_a_trace():
    """Recorded, not merely permitted. Without the tag, "the generality arm wandered into
    style 40% of the time" stops being answerable, and that is the routing measurement the
    gate was standing in for."""

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = ReviewArmTask(
        _data(arm_id="generality", spec_id="generality"),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    off = {"concern_family": "style"}
    task._annotate_candidate(off)
    assert off["concern_tags"] == ["style", "off-concern:generality"]

    on = {"concern_family": "generalization"}
    task._annotate_candidate(on)
    assert on["concern_tags"] == ["generalization"]


def test_the_generalist_is_never_off_concern():
    """It has no expected set, so there is no such thing as wandering out of it."""

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = ReviewArmTask(
        _data(arm_id="generalist", spec_id=None),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    candidate = {"concern_family": "style"}
    task._annotate_candidate(candidate)
    assert candidate["concern_tags"] == ["style"]


def test_a_specialist_may_make_its_own_kind_of_claim(submit):
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = ReviewArmTask(
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

    from ape.tasks.lean_tasks.formal_math.review.arm import EXPECTED_CONCERN_BY_ARM

    assert EXPECTED_CONCERN_BY_ARM["proof_golf"] == EXPECTED_CONCERN_BY_ARM["proof_idiom"]
    assert EXPECTED_CONCERN_BY_ARM["proof_golf"] == {"proof-golf"}


def test_the_generalist_has_no_concern_filter(submit):
    """It is the control: same sites and tools as the specialists, covering the families no
    specialist exists for. A filter here would remove the thing it is for."""

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.arm import EXPECTED_CONCERN_BY_ARM

    assert "generalist" not in EXPECTED_CONCERN_BY_ARM
    task = ReviewArmTask(
        _data(arm_id="generalist", spec_id=None),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    result = asyncio.run(mcp.tools["submit_candidates"](candidates=[_candidate(
        concern_family="documentation", issue_kind="documentation_gap",
        concern_label="documentation")]))
    assert result["evaluation_result"].success is True


# --- the ask whose fix does not compile -----------------------------------------------------
#
# `verify_checkable_edits` refuses a candidate in a checkable concern family that carries no
# `proposed_edit`. Reading the held-out run's gold-site silences on 2026-09-21, that rule is
# what the largest group of in-remit silences ran into: the arm had the maintainer's answer
# and could not make it compile. `verify_edits_if_present` is the same policy with that one
# refusal lifted -- an edit that IS supplied is still compiled, and one that fails is still
# refused. The unverified ask lands as `diagnostic`, which `finalize` keeps out of `published`.


def _submit_under(policy):
    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = ReviewArmTask(_data(submission_verification_policy=policy), ApeAgentConfig())
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    return mcp.tools["submit_candidates"]


def test_a_checkable_claim_with_no_edit_is_refused_under_the_verifying_policy():
    """The rule as it stands, pinned so the relaxation cannot be mistaken for a bug fix."""

    submit = _submit_under("verify_checkable_edits")
    result = asyncio.run(submit(candidates=[_candidate(proposed_edit=None)]))
    assert result["evaluation_result"].success is False
    assert "require a structured proposed_edit" in _message(result)


def test_the_relaxed_policy_accepts_the_ask_without_the_edit():
    """And only that. The claim still has to name its subject, stay inside the work unit and
    say what transformation it wants -- every other rule in the contract is untouched."""

    submit = _submit_under("verify_edits_if_present")
    result = asyncio.run(submit(candidates=[_candidate(proposed_edit=None)]))
    assert result["evaluation_result"].success is True
    # No compile ran, so it carries no warrant, which is what makes it `diagnostic`
    # downstream rather than a verified finding.
    assert not result.get("verification_artifacts")

    outside = asyncio.run(submit(candidates=[
        _candidate(proposed_edit=None, change_ids=["change:z"], primary_change_id="change:z")]))
    assert outside["evaluation_result"].success is False
    assert "unknown change_ids" in _message(outside)


def test_the_relaxed_policy_is_not_a_request_for_findings():
    """An empty submission stays exactly as cheap as it was: the mute-abstention refusal is
    the one that asks for a reason, and it still asks for nothing else. This is the property
    that keeps the control PRs measurable, and the reason `forbid_abstention` -- which took
    control emission 1 -> 36 -- is a diagnostic and not a design."""

    submit = _submit_under("verify_edits_if_present")
    muted = asyncio.run(submit(candidates=[]))
    assert muted["evaluation_result"].success is False
    assert "NOT a request to find something" in _message(muted)

    labelled = asyncio.run(submit(candidates=[], abstention_reason="already_correct",
                                  abstention_detail="checked the three names against the corpus"))
    assert labelled["evaluation_result"].success is True


# --- a verdict on every target ----------------------------------------------------------------
#
# `target_verdicts` replaces the job-level abstention with one verdict per review target:
# `issue` (backed by a candidate), `no_issue` or `cannot_determine`, each with its reason. It is
# not forcing -- `no_issue` is legal -- and it lives entirely in the submission tool, so the
# default tool must stay exactly as it was for every run that does not ask for it.

from ape.tasks.lean_tasks.formal_math.review.candidates import (  # noqa: E402
    TargetVerdictSubmission, UNSTATED_VERDICT, VERDICTS_ABSTENTION_REASON,
)


def _verdict_task(**overrides):
    """A two-target job under the verdict contract, and the result it records."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    data = dict(
        target_verdicts=True, submission_verification_policy="verify_edits_if_present",
        change_ids=["change:a", "change:b"],
        entity_ids_by_change={"change:a": ["entity:1"], "change:b": []},
        primary_subjects_by_change={"change:a": "Foo.bar", "change:b": "Foo.baz"},
        paths_by_change={"change:a": "Mathlib/A.lean", "change:b": "Mathlib/A.lean"},
    )
    data.update(overrides)
    task = ReviewArmTask(_data(**data), ApeAgentConfig())
    recorded = []

    async def keep(result):
        recorded.append(result)

    task.termination_callback = keep
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    return mcp.tools["submit_candidates"], recorded


def _verdict(change_id, verdict, reason="checked the statement against its neighbours"):
    return TargetVerdictSubmission(change_id=change_id, verdict=verdict, reason=reason)


def test_the_default_tool_is_unchanged_when_verdicts_are_off():
    """Every run that does not ask for verdicts must see the tool it has always seen: same
    parameters, same order, no verdict field. A schema change here would move what every arm
    in every comparison run was shown."""

    import inspect

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    task = ReviewArmTask(_data(), ApeAgentConfig())
    mcp = FakeMCP()
    asyncio.run(task.register_task_tools(mcp))
    params = list(inspect.signature(mcp.tools["submit_candidates"]).parameters)
    assert params == ["candidates", "abstention_reason", "abstention_detail"]

    verdict_submit, _ = _verdict_task()
    assert list(inspect.signature(verdict_submit).parameters) == ["target_verdicts", "candidates"]


def test_all_no_issue_is_a_legal_answer_and_says_why():
    """Not forcing: an arm that checked every target and found nothing submits no candidates,
    and the record keeps a reason per target instead of one sentence for the job."""

    submit, recorded = _verdict_task()
    result = asyncio.run(submit(target_verdicts=[
        _verdict("change:a", "no_issue"),
        _verdict("change:b", "cannot_determine", "needed the base file, which I could not read")]))
    assert result["evaluation_result"].success is True
    (row,) = recorded
    assert row.candidates == []
    assert [v["verdict"] for v in row.target_verdicts] == ["no_issue", "cannot_determine"]
    assert row.abstention["reason"] == VERDICTS_ABSTENTION_REASON
    assert "1 no_issue" in row.abstention["detail"] and "1 cannot_determine" in row.abstention["detail"]


def test_an_issue_is_a_candidate_and_a_candidate_is_an_issue():
    submit, recorded = _verdict_task()
    ok = asyncio.run(submit(
        target_verdicts=[_verdict("change:a", "issue"), _verdict("change:b", "no_issue")],
        candidates=[_candidate(proposed_edit=None)]))
    assert ok["evaluation_result"].success is True
    assert recorded[0].abstention is None
    assert recorded[0].target_verdicts[0] == {
        "change_id": "change:a", "verdict": "issue",
        "reason": "checked the statement against its neighbours"}

    submit, _ = _verdict_task()
    unbacked = asyncio.run(submit(
        target_verdicts=[_verdict("change:a", "issue"), _verdict("change:b", "no_issue")]))
    assert unbacked["evaluation_result"].success is False
    assert "no candidate names it" in _message(unbacked)

    submit, _ = _verdict_task()
    contradicted = asyncio.run(submit(
        target_verdicts=[_verdict("change:a", "no_issue"), _verdict("change:b", "no_issue")],
        candidates=[_candidate(proposed_edit=None)]))
    assert contradicted["evaluation_result"].success is False
    assert "whose verdict is 'no_issue'" in _message(contradicted)


def test_a_verdict_outside_the_job_or_without_a_reason_is_refused():
    submit, _ = _verdict_task()
    stray = asyncio.run(submit(target_verdicts=[
        _verdict("change:a", "no_issue"), _verdict("change:b", "no_issue"),
        _verdict("change:z", "no_issue")]))
    assert "not one of this job's review targets" in _message(stray)

    submit, _ = _verdict_task()
    mute = asyncio.run(submit(target_verdicts=[
        _verdict("change:a", "no_issue", reason="  "), _verdict("change:b", "no_issue")]))
    assert "empty reason" in _message(mute)


def test_a_missing_target_is_pressed_then_recorded_as_unstated_never_as_no_issue():
    """Bounded, so an arm that answers most targets cannot be turned into a failed job -- a
    coverage gap -- by one it keeps leaving out; and recorded under a system value so
    "never answered" is not mistaken for "checked and fine"."""

    submit, recorded = _verdict_task()
    partial = [_verdict("change:a", "no_issue")]
    for _ in range(3):
        refused = asyncio.run(submit(target_verdicts=partial))
        assert refused["evaluation_result"].success is False
        assert "Missing: change:b" in _message(refused)
    accepted = asyncio.run(submit(target_verdicts=partial))
    assert accepted["evaluation_result"].success is True
    assert recorded[0].target_verdicts[1] == {
        "change_id": "change:b", "verdict": UNSTATED_VERDICT, "reason": ""}


def test_verdicts_do_not_bring_back_the_abstention_refusals():
    """Under verdicts there is no job-level abstention to label and nothing to press for: the
    mute-abstention and forced paths belong to the default contract only."""

    submit, recorded = _verdict_task(forbid_abstention=True)
    result = asyncio.run(submit(target_verdicts=[
        _verdict("change:a", "no_issue"), _verdict("change:b", "no_issue")]))
    assert result["evaluation_result"].success is True
    assert recorded[0].candidates == []
