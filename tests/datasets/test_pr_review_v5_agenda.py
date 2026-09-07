"""The agenda: what may run, and the properties a routing comparison depends on.

Three failure modes are guarded here, and each one would corrupt a result rather than break
a run — which is why they are tests and not assertions in a docstring.

* A **non-deterministic agenda** makes two runs of the "same" configuration incomparable.
* A **leaky agenda** activates an arm because gold says an issue occurred there, which is
  the leak the episode split exists to prevent, arriving through the back door of "we only
  run the checker where it is needed".
* **Mode-dependent prompts** would mean a difference between `fanout`, `rules` and `lead` is
  a difference in the text the arms were sent, not in the routing being measured.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.datasets.pr_review_v4.contracts import assert_gold_free
from src.datasets.pr_review_v4.io import canonical_json_bytes, load_jsonl
from src.datasets.pr_review_v4.schema import (
    ChangeGraph,
    ModificationRecord,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)
from src.mathlib_review.agenda.agenda import agenda_report, build_agenda, initial_jobs
from src.mathlib_review.agenda.arms import GENERALIST_ARM_ID, default_arms, specs_by_arm_id

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
INVENTORY = Path(
    "inputs/pr_review_v4/treatments/systematic-opportunities-v3-medium/derived/"
    "modification_inventory.jsonl"
)
SMOKE_PRS = [33057, 33066, 33098, 33438]


@pytest.fixture(scope="module")
def release():
    return {
        "units": load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit),
        "episodes": load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput),
        "graphs": load_jsonl(RELEASE / "derived/change_graphs.jsonl", ChangeGraph),
        "release_prompts": load_jsonl(RELEASE / "derived/rendered_prompts.jsonl", RenderedPrompt),
        "modifications": load_jsonl(INVENTORY, ModificationRecord),
    }


def _build(release, mode="lead", prs=SMOKE_PRS):
    return build_agenda(
        run_name="test", routing_mode=mode, release=RELEASE,
        modification_inventory=INVENTORY, pr_numbers=prs, **release,
    )


@pytest.fixture(scope="module")
def agenda(release):
    return _build(release)[0]


def test_the_agenda_is_byte_identical_across_builds(release):
    first, _ = _build(release)
    second, _ = _build(release)
    assert canonical_json_bytes(first.model_dump(mode="json")) == canonical_json_bytes(
        second.model_dump(mode="json")
    )


def test_the_agenda_mentions_no_gold(agenda):
    """`assert_gold_free` substring-sweeps the serialization, so a field added later cannot
    bypass the check by being named something innocuous."""

    assert_gold_free(agenda)


def test_prompt_text_never_reaches_the_agenda(agenda):
    """Only hashes. The focused prompts contain phrases like "would a maintainer say", which
    would trip the gold sweep on prose that is not a leak — and a plan carrying prompt text
    is vouching for something other than an identity."""

    text = canonical_json_bytes(agenda.model_dump(mode="json")).decode()
    assert "maintainer" not in text.lower()
    for proposal in agenda.proposals:
        assert len(proposal.prompt_sha256) == 64


def test_every_work_unit_gets_a_mandatory_generalist(agenda):
    """The coverage floor. R1 measured coverage, not selection, as the dominant wall for a
    single pass, so a lead free to prune everything could win on cost by not looking."""

    units = {item.work_unit_id for item in agenda.proposals}
    generalists = {
        item.work_unit_id for item in agenda.proposals
        if item.arm_id == GENERALIST_ARM_ID
    }
    assert generalists == units
    assert all(
        item.mandatory for item in agenda.proposals if item.arm_id == GENERALIST_ARM_ID
    )
    # A specialist may be mandatory now — the coverage contract requires work the PR itself
    # asks for — but only ever through `routing_priority`, so there is one enforcement
    # mechanism rather than two and every mandate carries a reason the lead can read.
    for item in agenda.proposals:
        if item.arm_id == GENERALIST_ARM_ID:
            continue
        assert item.mandatory == (item.routing_priority == "required")
        if item.mandatory:
            assert item.routing_reason


def test_eligibility_is_the_v4_rule_and_not_a_second_copy(release, agenda):
    """Eligible pairs must be exactly what `schedule_focused` selects — no more, no fewer.

    The relaxed site set exists so that ineligible pairs are still *renderable*; it must
    never promote one to eligible, which would silently widen the deterministic arm.
    """

    from src.datasets.pr_review_v4.focused_specs import schedule_focused

    units = [u for u in release["units"] if u.pr_number in set(SMOKE_PRS)]
    scheduled = {
        item.invocation_id for item in schedule_focused(
            list(specs_by_arm_id().values()), release["modifications"], units, SMOKE_PRS)
    }
    eligible = {
        item.invocation_id for item in agenda.proposals
        if item.eligible and item.arm_id != GENERALIST_ARM_ID
    }
    assert eligible == scheduled


def test_eligible_specialist_sites_match_the_scheduler_exactly(release, agenda):
    from src.datasets.pr_review_v4.focused_specs import schedule_focused

    units = [u for u in release["units"] if u.pr_number in set(SMOKE_PRS)]
    by_id = {
        item.invocation_id: sorted(item.site_change_ids)
        for item in schedule_focused(
            list(specs_by_arm_id().values()), release["modifications"], units, SMOKE_PRS)
    }
    for proposal in agenda.proposals:
        if proposal.eligible and proposal.arm_id != GENERALIST_ARM_ID:
            assert sorted(proposal.site_change_ids) == by_id[proposal.invocation_id]


def test_specialists_are_never_offered_a_non_declaration_target(release, agenda):
    """The relaxed set drops the lifecycle and component filters but keeps subject kind.

    Offering a proof-golf arm a target that is not a declaration renders a prompt with
    nothing in it, which costs a model call to discover.
    """

    kinds = {
        item.primary_change_id: item.subject_kind for item in release["modifications"]
    }
    specs = specs_by_arm_id()
    for proposal in agenda.proposals:
        if proposal.arm_id == GENERALIST_ARM_ID:
            continue
        allowed = specs[proposal.arm_id].subject_kinds
        for change_id in proposal.site_change_ids:
            if change_id in kinds:
                assert kinds[change_id] in allowed


def test_no_pair_is_enumerated_twice(agenda):
    ids = [item.invocation_id for item in agenda.proposals]
    assert len(ids) == len(set(ids))


def test_every_routing_mode_sends_identical_prompts(release):
    """The property the whole three-way comparison rests on."""

    _, fanout = _build(release, "fanout")
    _, rules = _build(release, "rules")
    _, lead = _build(release, "lead")
    assert set(fanout) == set(rules) == set(lead)
    for key in fanout:
        assert (fanout[key]["rendered_prompt_sha256"]
                == rules[key]["rendered_prompt_sha256"]
                == lead[key]["rendered_prompt_sha256"])
        assert fanout[key]["rendered_user_prompt"] == lead[key]["rendered_user_prompt"]


def test_static_modes_select_the_sets_they_claim(release):
    fanout_agenda, _ = _build(release, "fanout")
    rules_agenda, _ = _build(release, "rules")
    assert len(initial_jobs(fanout_agenda)) == len(fanout_agenda.proposals)
    rules_jobs = initial_jobs(rules_agenda)
    assert all(job.mandatory or job.eligible for job in rules_jobs)
    # `rules` is a strict subset here only because this release has ineligible pairs at all;
    # if it ever stops being one, the two conditions have silently merged.
    assert len(rules_jobs) < len(fanout_agenda.proposals)


def test_lead_mode_refuses_to_decide_its_jobs_statically(release):
    """`lead` has no static job set; asking for one is a caller bug, not an empty list."""

    lead_agenda, _ = _build(release, "lead")
    with pytest.raises(ValueError, match="run time"):
        initial_jobs(lead_agenda)


def test_the_pool_carries_a_runnable_payload_for_every_proposal(release):
    agenda, pool = _build(release)
    assert set(pool) == {item.invocation_id for item in agenda.proposals}
    for invocation_id, payload in pool.items():
        assert payload["task_type"] == "lean_pr_review_v5_arm"
        assert payload["invocation_id"] == invocation_id
        assert payload["change_ids"], "an arm with no targets has nothing to be asked"


def test_specialist_payloads_demand_verification(release):
    """A specialist claim is settled by compiling the replacement; the policy is what makes
    `submit_candidates` enforce that rather than accept prose."""

    _, pool = _build(release)
    for payload in pool.values():
        if payload["arm_id"] != GENERALIST_ARM_ID:
            assert payload["submission_verification_policy"] == "verify_checkable_edits"


def test_specialist_scope_is_narrowed_to_its_own_sites(release):
    """The prompt shows only the sites the arm was scheduled on, and the contract must
    accept only those — otherwise an arm can claim about a target it was never shown, and
    the gold-free enumeration the arm rests on stops being exact."""

    agenda, pool = _build(release)
    by_id = {item.invocation_id: item for item in agenda.proposals}
    for invocation_id, payload in pool.items():
        if payload["arm_id"] == GENERALIST_ARM_ID:
            continue
        assert sorted(payload["change_ids"]) == sorted(by_id[invocation_id].site_change_ids)


def test_the_report_costs_the_floor_and_both_static_modes(agenda):
    report = agenda_report(agenda)
    assert report["proposals_enumerated"] == len(agenda.proposals)
    assert 0 < report["mandatory_floor_cost"] <= report["projected_cost_rules"]
    assert report["projected_cost_rules"] <= report["projected_cost_fanout"]


def test_arm_registry_speaks_the_merge_vocabulary():
    """A concern family the merge does not know silently defaults to the weakest tier and
    loses every tie it takes part in."""

    from typing import get_args

    from src.datasets.pr_review_v4.schema import ConcernFamily, IssueKind

    families, kinds = set(get_args(ConcernFamily)), set(get_args(IssueKind))
    for arm in default_arms("candidate-prompt/12"):
        assert arm.concern_family in families
        if arm.issue_kind is not None:
            assert arm.issue_kind in kinds


# --- the specialist-only run ------------------------------------------------------------


def test_the_floor_can_be_turned_off_for_a_specialist_only_run(release):
    """smoke4 said the generalist's lead in gold-reaching candidates is volume, not quality:
    per candidate the two are indistinguishable (0.08 against 0.09), and its 4x lead per
    invocation is 2.0 candidates per run against the specialists' 0.5. The only way to ask
    whether that is right is to run without it."""

    agenda, pool = build_agenda(
        run_name="test", routing_mode="lead", release=RELEASE,
        modification_inventory=INVENTORY, pr_numbers=SMOKE_PRS,
        generalist_floor=False, **release,
    )
    assert not [p for p in agenda.proposals if p.arm_id == GENERALIST_ARM_ID]
    assert not [k for k in pool if k.endswith(f"#{GENERALIST_ARM_ID}")]
    assert agenda.proposals, "turning off the floor must not empty the agenda"


def test_the_floor_is_on_unless_asked_otherwise(release):
    """Every measurement so far was taken with it running."""

    agenda, _ = _build(release)
    assert [p for p in agenda.proposals if p.arm_id == GENERALIST_ARM_ID]


def test_a_specialist_only_agenda_reports_what_it_would_leave_unreviewed(release):
    """The number that separates "the specialists are worse" from "nobody looked".

    Without the floor, a work unit no specialist is eligible on is simply not reviewed, and a
    recall drop from that is a coverage artifact rather than a result about the arms.
    """

    agenda, _ = build_agenda(
        run_name="test", routing_mode="lead", release=RELEASE,
        modification_inventory=INVENTORY, pr_numbers=SMOKE_PRS,
        generalist_floor=False, **release,
    )
    report = agenda_report(agenda)
    assert "units_without_specialist" in report
    assert isinstance(report["units_without_specialist"], list)
