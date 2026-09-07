"""The focused arm's task, prompt and ingestion contract.

Three properties carry the arm's claims, and each has a way of failing silently:

* **The v2 instruction is reused verbatim.** The arm's justification is that these prompts
  measured 14% V2-stratum recall against the holistic arm's 4%. A reworded prompt is a
  different treatment and the comparison stops meaning anything, so the reuse is asserted on
  the text rather than trusted.
* **Identity is per invocation, not per work unit.** Four specs run against one unit. Keyed
  on the unit, four terminal responses read as four duplicates of one and ingestion raises;
  four identical candidates collide on `candidate_id` and one silently replaces the others.
* **The spec comes from the invocation.** Golf and idiom both declare `proof_simplification`
  while making different claims, and `verify_proof_simplification` keys its warrant on the
  spec. A model trusted to report its own spec could take idiom's laxer rule for a golf
  claim, which is exactly the repeal the spec-keyed verifier was built to stop.
"""

from pathlib import Path

import pytest

from src.mathlib_review.review.candidates import (
    candidates_from_response,
    ingest_responses,
    invocation_work_unit,
)
from src.mathlib_review.agenda.focused_specs import default_specs, schedule_focused
from src.mathlib_review.io import load_jsonl
from src.mathlib_review.agenda.render_focused import (
    render_focused_all,
    render_focused_invocation,
)
from src.mathlib_review.schema import (
    ChangeGraph,
    ModificationRecord,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)
from src.mathlib_review.review.task_adapter import build_focused_task_data

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
INVENTORY = Path(
    "inputs/pr_review_v4/treatments/systematic-opportunities-v2-medium/"
    "derived/modification_inventory.jsonl"
)


@pytest.fixture(scope="module")
def scheduled():
    if not RELEASE.is_dir() or not INVENTORY.is_file():
        pytest.skip("the medium release or its modification inventory is not present")
    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    episodes = load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput)
    graphs = load_jsonl(RELEASE / "derived/change_graphs.jsonl", ChangeGraph)
    modifications = load_jsonl(INVENTORY, ModificationRecord)
    specs = default_specs()
    invocations = schedule_focused(specs, modifications, units)
    prompts = render_focused_all(specs, invocations, units, episodes, graphs)
    return {
        "specs": {item.spec_id: item for item in specs},
        "invocations": invocations,
        "prompts": prompts,
        "units": {item.work_unit_id: item for item in units},
        "episodes": {item.episode_id: item for item in episodes},
        "graphs": {item.graph_id: item for item in graphs},
    }


def test_the_v2_instruction_is_reused_verbatim(scheduled):
    from ape.tasks.lean_tasks.formal_math.pr_shared.focused_prompts import FOCUSED_PROMPTS

    for prompt in scheduled["prompts"]:
        _tools, system, _user = FOCUSED_PROMPTS[prompt.spec_id]
        assert prompt.system_prompt.startswith(system), (
            f"{prompt.spec_id} no longer opens with its v2 instruction verbatim"
        )


def test_the_v4_submission_contract_supersedes_the_v2_field_list(scheduled):
    """v2 findings are not v4 candidates; without this every submission would be rejected."""

    for prompt in scheduled["prompts"]:
        system = prompt.system_prompt
        # Positional, but on the thing that actually matters: the v4 contract must come
        # *after* the v2 instruction it supersedes. Asserting it lands in the back half was
        # a proxy that broke the moment the contract grew, which says nothing about order.
        contract_at = system.index("# Submission contract for this run")
        assert system.index("submit_candidates exactly once") > contract_at
        assert system.index("primary_change_id") > contract_at
        spec = scheduled["specs"][prompt.spec_id]
        assert system.index(f'"{spec.issue_kind}"') > contract_at


def test_sites_are_a_subset_of_the_work_unit(scheduled):
    """The submission contract is `change_ids ⊆ unit`; sites must not widen it."""

    for prompt in scheduled["prompts"]:
        unit = scheduled["units"][prompt.work_unit_id]
        assert set(prompt.included_change_ids) <= set(unit.change_ids)
        assert prompt.included_change_ids, "an invocation with no site should not exist"


def test_every_invocation_has_its_own_prompt_and_task_id(scheduled):
    prompts = scheduled["prompts"]
    assert len({item.prompt_sha256 for item in prompts}) == len(prompts)
    assert len({item.invocation_id for item in prompts}) == len(prompts)

    datas = []
    for prompt in prompts[:40]:
        unit = scheduled["units"][prompt.work_unit_id]
        datas.append(build_focused_task_data(
            unit, scheduled["episodes"][unit.episode_id], prompt
        ))
    assert len({item.task_id for item in datas}) == len(datas), (
        "colliding task ids mean four runs sharing one workspace"
    )


def test_invocation_work_unit_round_trips(scheduled):
    for invocation in scheduled["invocations"]:
        assert invocation_work_unit(invocation.invocation_id) == invocation.work_unit_id
    # A plain work-unit id is its own invocation id: that is every holistic run.
    assert invocation_work_unit("wu:abc") == "wu:abc"


def _multi_spec_unit(scheduled):
    counts = {}
    for invocation in scheduled["invocations"]:
        counts.setdefault(invocation.work_unit_id, []).append(invocation)
    for work_unit_id, group in counts.items():
        if len(group) >= 2:
            return scheduled["units"][work_unit_id], group
    pytest.skip("no work unit carries more than one scheduled spec")


def test_several_specs_on_one_unit_ingest_without_tripping_the_one_response_rule(scheduled):
    unit, group = _multi_spec_unit(scheduled)
    rows = [
        {"invocation_id": item.invocation_id, "work_unit_id": item.work_unit_id,
         "spec_id": item.spec_id, "success": True, "response": {"candidates": []}}
        for item in group
    ]
    assert ingest_responses(
        [unit], rows, expected_invocations=[item.invocation_id for item in group]
    ) == []


def test_identical_candidates_from_two_specs_do_not_collide(scheduled):
    """Without `spec_id` in the identity payload one would silently replace the other."""

    unit, group = _multi_spec_unit(scheduled)
    change_id = group[0].site_change_ids[0]
    subject = unit.primary_subjects_by_change[change_id]
    entities = unit.entity_ids_by_change.get(change_id) or []
    leaf = subject.rsplit(".", 1)[-1]
    raw = {
        "change_ids": [change_id], "primary_change_id": change_id,
        "primary_subject": subject,
        "primary_entity_id": entities[0] if entities else None,
        "issue_kind": "duplicate_implementation", "concern_family": "duplication",
        "concern_label": "x", "severity": "advisory",
        "claim": f"{leaf} duplicates an existing lemma",
        "requested_change": f"replace {leaf} with the existing declaration",
    }
    first = candidates_from_response(unit, {"candidates": [raw]}, spec_id="duplication")
    second = candidates_from_response(unit, {"candidates": [raw]}, spec_id="generality")
    assert first[0].spec_id == "duplication" and second[0].spec_id == "generality"
    assert first[0].candidate_id != second[0].candidate_id


def test_a_model_may_not_relabel_its_own_spec(scheduled):
    """The whole point of keying the proof verifier on the spec rather than the kind."""

    unit, group = _multi_spec_unit(scheduled)
    change_id = group[0].site_change_ids[0]
    subject = unit.primary_subjects_by_change[change_id]
    entities = unit.entity_ids_by_change.get(change_id) or []
    leaf = subject.rsplit(".", 1)[-1]
    raw = {
        "change_ids": [change_id], "primary_change_id": change_id,
        "primary_subject": subject,
        "primary_entity_id": entities[0] if entities else None,
        "issue_kind": "proof_simplification", "concern_family": "proof-golf",
        "concern_label": "x", "severity": "advisory",
        "spec_id": "proof_idiom",
        "claim": f"{leaf} can be shortened",
        "requested_change": f"rewrite {leaf} with grind",
    }
    with pytest.raises(ValueError, match="reports spec_id"):
        candidates_from_response(unit, {"candidates": [raw]}, spec_id="proof_golf")


def test_a_focused_prompt_missing_its_identity_is_rejected(scheduled):
    """Task data must never take the spec from anywhere but the prompt."""

    prompt = scheduled["prompts"][0]
    unit = scheduled["units"][prompt.work_unit_id]
    episode = scheduled["episodes"][unit.episode_id]
    stripped = prompt.model_copy(update={"spec_id": None, "invocation_id": None})
    with pytest.raises(ValueError, match="invocation_id and spec_id"):
        build_focused_task_data(unit, episode, stripped)


def test_a_holistic_prompt_may_still_not_omit_targets(scheduled):
    """Relaxing the completeness check for focused prompts must not relax it for holistic."""

    from src.mathlib_review.review.task_adapter import build_candidate_task_data

    prompt = scheduled["prompts"][0]
    unit = scheduled["units"][prompt.work_unit_id]
    episode = scheduled["episodes"][unit.episode_id]
    if not prompt.omitted_change_ids:
        pytest.skip("this invocation covers its whole unit")
    holistic = prompt.model_copy(update={"spec_id": None})
    with pytest.raises(ValueError, match="incomplete production prompt"):
        build_candidate_task_data(unit, episode, holistic)


def test_a_spec_may_not_render_another_specs_invocation(scheduled):
    invocation = scheduled["invocations"][0]
    unit = scheduled["units"][invocation.work_unit_id]
    other = next(
        item for item in scheduled["specs"].values()
        if item.spec_id != invocation.spec_id
    )
    with pytest.raises(ValueError, match="is not a"):
        render_focused_invocation(
            other, invocation, unit, scheduled["episodes"][unit.episode_id],
            scheduled["graphs"][unit.graph_id],
        )


def test_the_result_carries_the_invocation_not_just_the_unit(scheduled):
    """Ingestion keys on `invocation_id`; a result without it cannot be attributed."""

    from ape.tasks.lean_tasks import (
        LeanPRReviewV4FocusedConfig,
        LeanPRReviewV4FocusedTask,
    )

    prompt = next(item for item in scheduled["prompts"] if item.spec_id == "proof_golf")
    unit = scheduled["units"][prompt.work_unit_id]
    data = build_focused_task_data(unit, scheduled["episodes"][unit.episode_id], prompt)
    task = LeanPRReviewV4FocusedTask(data, LeanPRReviewV4FocusedConfig())
    result = task.create_result(
        success=True, score=1.0, pr_number=data.pr_number,
        work_unit_id=data.work_unit_id,
        rendered_prompt_sha256=data.rendered_prompt_sha256,
        candidates=[], verification_artifacts=[], findings=[], review_message="",
    )
    assert result.invocation_id == prompt.invocation_id
    assert result.spec_id == "proof_golf"
    assert result.work_unit_id == unit.work_unit_id


def test_a_claim_only_focused_candidate_is_refused(scheduled):
    """v2's all-or-nothing verification gate is kept: no focused finding without an edit.

    Asserted through the real handler because this is the arm's precision floor — a focused
    candidate that never constructs a replacement is the ungrounded 'might already exist'
    the v2 prompts explicitly refuse, and it would enter the merge at `model_assertion`.
    """

    import asyncio

    from ape.tasks.lean_tasks import (
        LeanPRReviewV4FocusedConfig,
        LeanPRReviewV4FocusedTask,
    )
    from ape.tasks.lean_tasks.formal_math.pr_review_v4.candidates import (
        CandidateSubmission,
    )

    class _RecordingMCP:
        def __init__(self):
            self.tools = {}

        def tool(self, *_args, **_kwargs):
            def decorator(function):
                self.tools[function.__name__] = function
                return function
            return decorator

    prompt = next(item for item in scheduled["prompts"] if item.spec_id == "duplication")
    unit = scheduled["units"][prompt.work_unit_id]
    data = build_focused_task_data(unit, scheduled["episodes"][unit.episode_id], prompt)
    task = LeanPRReviewV4FocusedTask(data, LeanPRReviewV4FocusedConfig())
    mcp = _RecordingMCP()
    asyncio.run(task.register_task_tools(mcp))

    change_id = prompt.included_change_ids[0]
    subject = unit.primary_subjects_by_change[change_id]
    entities = unit.entity_ids_by_change.get(change_id) or []
    leaf = subject.rsplit(".", 1)[-1]
    submission = CandidateSubmission(
        change_ids=[change_id], primary_change_id=change_id, primary_subject=subject,
        primary_entity_id=entities[0] if entities else None,
        issue_kind="duplicate_implementation", concern_family="duplication",
        concern_label="duplicate", severity="advisory",
        claim=f"{leaf} duplicates an existing lemma",
        requested_change=f"replace {leaf} with the existing declaration",
    )
    result = asyncio.run(mcp.tools["submit_candidates"](candidates=[submission]))
    evaluation = result["evaluation_result"]
    assert not evaluation.success
    assert "proposed_edit" in evaluation.message
