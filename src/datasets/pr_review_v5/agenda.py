"""Enumerate every (arm, work unit) pair that could run, and mark which the rule selects.

The central decision here is that the agenda enumerates the **full pool**, not just the
eligible pairs, and renders a prompt for every entry in it up front.

The alternative — render eligible pairs now, render an agent-added pair on demand — looks
cheaper and is wrong twice. It would let a lead-added job run against a prompt no plan ever
vouched for, defeating the pre-registration; and it would let `fanout`, `rules` and `lead`
send *different text* for the same (arm, unit) pair, so a difference between modes could be
a difference in prompts rather than in routing. Sharing one pre-rendered pool is what makes
the three-mode comparison mean what it claims.

Eligibility is still the deterministic rule, unchanged: `schedule_focused` enumerates from
the modification inventory, which is built from change graphs alone. An arm is never marked
eligible because gold says an issue of that kind occurred there — that is the leak the
episode split exists to prevent, reintroduced through the back door of "we only run the
checker where it is needed".

Pairs the rule rejects are still *renderable*, and that is a weaker relaxation than it
sounds: the lifecycle and component filters are dropped, but the subject-kind filter is
kept, so a golf arm is never offered a target that is not a declaration. A pair with no
renderable site is not enumerated at all — there is nothing to ask about.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from src.datasets.pr_review_v4.focused_specs import (
    SCHEDULER_VERSION,
    FocusedAgentSpec,
    FocusedInvocation,
    schedule_focused,
)
from src.datasets.pr_review_v4.io import canonical_json_bytes, sealed_model, sha256_bytes
from src.datasets.pr_review_v4.render_focused import FOCUSED_RENDERER_VERSION, render_focused_all
from src.datasets.pr_review_v4.schema import (
    ChangeGraph,
    ModificationRecord,
    RenderedPrompt,
    ReviewEpisodeInput,
    ReviewWorkUnit,
)
from src.datasets.pr_review_v4.task_adapter import (
    build_candidate_task_data,
    build_focused_task_data,
)

from .arms import ARM_TASK_TYPE, GENERALIST_ARM_ID, default_arms, specs_by_arm_id
from .schema import AgendaProposal, ReviewAgenda, ReviewArm

AGENDA_VERSION = "v5-agenda/1"


def _renderable_sites(
    spec: FocusedAgentSpec,
    unit: ReviewWorkUnit,
    modifications_by_change: Dict[str, ModificationRecord],
) -> List[str]:
    """Sites this spec could speak about if its lifecycle/component filter were relaxed.

    Used only for pairs the rule did *not* select, so that the lead has something to add and
    `fanout` has something to run. The subject-kind filter stays: offering a proof-golf arm
    a target that is not a declaration produces a prompt with nothing in it.
    """

    sites = []
    for change_id in unit.change_ids:
        modification = modifications_by_change.get(change_id)
        if modification is None:
            continue
        if modification.subject_kind in spec.subject_kinds:
            sites.append(change_id)
    return sorted(sites)


def _invocation(spec_id: str, unit: ReviewWorkUnit, sites: Sequence[str],
                eligible: bool) -> FocusedInvocation:
    payload = {
        "scheduler_version": SCHEDULER_VERSION,
        "agenda_version": AGENDA_VERSION,
        "spec_id": spec_id,
        "work_unit_id": unit.work_unit_id,
        "site_change_ids": sorted(sites),
        "eligible": eligible,
    }
    return FocusedInvocation(
        invocation_id=f"{unit.work_unit_id}#{spec_id}",
        spec_id=spec_id,
        work_unit_id=unit.work_unit_id,
        episode_id=unit.episode_id,
        pr_number=unit.pr_number,
        site_change_ids=tuple(sorted(sites)),
        source_sha256=sha256_bytes(canonical_json_bytes(payload)),
    )


def enumerate_invocations(
    units: Sequence[ReviewWorkUnit],
    modifications: Sequence[ModificationRecord],
    pr_numbers: Optional[Iterable[int]] = None,
) -> Tuple[List[FocusedInvocation], Dict[str, bool]]:
    """Every renderable (specialist, unit) pair, plus which ones the rule selected.

    Returns the invocations and an `invocation_id -> eligible` map. The eligible ones keep
    the sites `schedule_focused` chose; the rest get the relaxed site set.
    """

    specs = specs_by_arm_id()
    scheduled = schedule_focused(list(specs.values()), modifications, units, pr_numbers)
    scheduled_by_id = {item.invocation_id: item for item in scheduled}
    modifications_by_change = {
        item.primary_change_id: item for item in modifications
    }
    wanted = set(pr_numbers) if pr_numbers else None
    selected_units = [
        unit for unit in units if wanted is None or unit.pr_number in wanted
    ]

    invocations: List[FocusedInvocation] = []
    eligibility: Dict[str, bool] = {}
    for unit in sorted(selected_units, key=lambda item: item.work_unit_id):
        for spec_id in sorted(specs):
            invocation_id = f"{unit.work_unit_id}#{spec_id}"
            hit = scheduled_by_id.get(invocation_id)
            if hit is not None:
                invocations.append(_invocation(
                    spec_id, unit, hit.site_change_ids, eligible=True))
                eligibility[invocation_id] = True
                continue
            sites = _renderable_sites(specs[spec_id], unit, modifications_by_change)
            if not sites:
                continue
            invocations.append(_invocation(spec_id, unit, sites, eligible=False))
            eligibility[invocation_id] = False
    return invocations, eligibility


def _arm_payload(base_payload: Dict[str, Any], *, arm: ReviewArm, invocation_id: str,
                 spec_id: Optional[str]) -> Dict[str, Any]:
    """Turn a v4 task-data payload into a v5 arm payload.

    Built by dumping v4's own builders rather than assembling the fields here, so the
    per-target maps the submission contract checks against — `change_ids`,
    `primary_subjects_by_change`, `entity_ids_by_change`, `paths_by_change` — are exactly
    the ones v4 would have produced. Rebuilding them by hand is how edit confinement quietly
    stops confining anything.
    """

    payload = dict(base_payload)
    payload.pop("task_type", None)
    payload["task_type"] = ARM_TASK_TYPE
    payload["invocation_id"] = invocation_id
    payload["arm_id"] = arm.arm_id
    payload["spec_id"] = spec_id
    payload["context_tools"] = list(arm.context_tools)
    payload["task_id"] = "pr5_" + invocation_id.replace(":", "_").replace("#", "__")
    return payload


def build_agenda(
    *,
    run_name: str,
    routing_mode: str,
    release: Path,
    modification_inventory: Optional[Path],
    units: Sequence[ReviewWorkUnit],
    episodes: Sequence[ReviewEpisodeInput],
    graphs: Sequence[ChangeGraph],
    release_prompts: Sequence[RenderedPrompt],
    modifications: Sequence[ModificationRecord],
    pr_numbers: Optional[Iterable[int]] = None,
) -> Tuple[ReviewAgenda, Dict[str, Dict[str, Any]]]:
    """The sealed agenda, and the pool of arm task payloads keyed by `proposal_id`.

    The agenda carries hashes; the pool carries prompt text. They are separate because
    `contracts.assert_gold_free` substring-sweeps the serialized agenda, and the focused
    prompts are full of phrases like "would a maintainer say" — shipping the text would trip
    a leak check on prose that is not a leak.
    """

    if not release_prompts:
        raise ValueError("release carries no rendered prompts; cannot schedule a generalist")
    renderer_version = release_prompts[0].renderer_version
    arms = default_arms(renderer_version)
    arms_by_id = {arm.arm_id: arm for arm in arms}
    specs = specs_by_arm_id()

    wanted = set(pr_numbers) if pr_numbers else None
    selected_units = [unit for unit in units if wanted is None or unit.pr_number in wanted]
    unit_by_id = {item.work_unit_id: item for item in selected_units}
    episode_by_id = {item.episode_id: item for item in episodes}
    release_prompt_by_unit = {item.work_unit_id: item for item in release_prompts}

    proposals: List[AgendaProposal] = []
    pool: Dict[str, Dict[str, Any]] = {}

    # --- the mandatory generalist, one per unit ---------------------------------------
    generalist = arms_by_id[GENERALIST_ARM_ID]
    for unit in sorted(selected_units, key=lambda item: item.work_unit_id):
        prompt = release_prompt_by_unit.get(unit.work_unit_id)
        if prompt is None:
            raise ValueError(
                f"work unit {unit.work_unit_id} has no rendered production prompt in the "
                "release; the generalist floor cannot be scheduled without one"
            )
        invocation_id = f"{unit.work_unit_id}#{GENERALIST_ARM_ID}"
        data = build_candidate_task_data(unit, episode_by_id[unit.episode_id], prompt)
        pool[invocation_id] = _arm_payload(
            data.model_dump(mode="json"), arm=generalist,
            invocation_id=invocation_id, spec_id=None,
        )
        proposals.append(sealed_model(
            AgendaProposal,
            proposal_id=invocation_id,
            invocation_id=invocation_id,
            arm_id=GENERALIST_ARM_ID,
            work_unit_id=unit.work_unit_id,
            episode_id=unit.episode_id,
            pr_number=unit.pr_number,
            site_change_ids=list(unit.change_ids),
            eligible=True,
            mandatory=True,
            prompt_sha256=prompt.prompt_sha256,
            cost_hint=generalist.cost_hint,
            rationale=generalist.rationale,
        ))

    # --- specialists, eligible and merely renderable -----------------------------------
    invocations, eligibility = enumerate_invocations(
        selected_units, modifications, pr_numbers
    )
    rendered = render_focused_all(
        list(specs.values()), invocations, selected_units, episodes, graphs
    )
    rendered_by_id = {item.invocation_id: item for item in rendered}
    for invocation in invocations:
        prompt = rendered_by_id[invocation.invocation_id]
        unit = unit_by_id[invocation.work_unit_id]
        arm = arms_by_id[invocation.spec_id]
        data = build_focused_task_data(unit, episode_by_id[unit.episode_id], prompt)
        pool[invocation.invocation_id] = _arm_payload(
            data.model_dump(mode="json"), arm=arm,
            invocation_id=invocation.invocation_id, spec_id=invocation.spec_id,
        )
        proposals.append(sealed_model(
            AgendaProposal,
            proposal_id=invocation.invocation_id,
            invocation_id=invocation.invocation_id,
            arm_id=arm.arm_id,
            work_unit_id=unit.work_unit_id,
            episode_id=unit.episode_id,
            pr_number=unit.pr_number,
            site_change_ids=list(invocation.site_change_ids),
            eligible=eligibility[invocation.invocation_id],
            mandatory=False,
            prompt_sha256=prompt.prompt_sha256,
            cost_hint=arm.cost_hint,
            rationale=arm.rationale,
        ))

    proposals.sort(key=lambda item: item.proposal_id)
    agenda = sealed_model(
        ReviewAgenda,
        agenda_id=f"agenda:{run_name}",
        run_name=run_name,
        routing_mode=routing_mode,
        release=str(release),
        modification_inventory=(
            str(modification_inventory) if modification_inventory else None
        ),
        arms=arms,
        proposals=proposals,
        scheduler_version=SCHEDULER_VERSION,
        renderer_version=f"{renderer_version}+{FOCUSED_RENDERER_VERSION}",
    )
    return agenda, pool


def initial_jobs(agenda: ReviewAgenda) -> List[AgendaProposal]:
    """The proposals a non-`lead` mode runs, with no model call involved.

    `fanout` takes the whole pool; `rules` takes the mandatory floor plus whatever the
    deterministic scheduler marked eligible. `lead` is absent here on purpose — it is the
    only mode where the set is not knowable before a model call.
    """

    if agenda.routing_mode == "fanout":
        return list(agenda.proposals)
    if agenda.routing_mode == "rules":
        return [item for item in agenda.proposals if item.mandatory or item.eligible]
    raise ValueError(
        f"routing_mode {agenda.routing_mode!r} decides its jobs at run time, not statically"
    )


def agenda_report(agenda: ReviewAgenda) -> Dict[str, Any]:
    """What the agenda would cost and where it would speak — before anything is spent."""

    by_arm: Dict[str, Dict[str, Any]] = {}
    for proposal in agenda.proposals:
        row = by_arm.setdefault(
            proposal.arm_id, {"enumerated": 0, "eligible": 0, "sites": 0, "cost_hint": 0.0}
        )
        row["enumerated"] += 1
        row["eligible"] += int(proposal.eligible)
        row["sites"] += len(proposal.site_change_ids)
        row["cost_hint"] += proposal.cost_hint
    eligible = [item for item in agenda.proposals if item.mandatory or item.eligible]
    return {
        "agenda_version": AGENDA_VERSION,
        "scheduler_version": agenda.scheduler_version,
        "renderer_version": agenda.renderer_version,
        "routing_mode": agenda.routing_mode,
        "work_units": len({item.work_unit_id for item in agenda.proposals}),
        "pr_numbers": sorted({item.pr_number for item in agenda.proposals}),
        "proposals_enumerated": len(agenda.proposals),
        "proposals_eligible": len(eligible),
        "by_arm": by_arm,
        "projected_cost_fanout": round(
            sum(item.cost_hint for item in agenda.proposals), 4),
        "projected_cost_rules": round(sum(item.cost_hint for item in eligible), 4),
        "mandatory_floor_cost": round(
            sum(item.cost_hint for item in agenda.proposals if item.mandatory), 4),
    }
