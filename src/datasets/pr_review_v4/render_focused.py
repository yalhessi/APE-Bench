"""Render one prompt per focused invocation.

The four v2 system prompts are the asset this arm exists to reuse: they carry the review
instruction that measured 14% V2-stratum recall against the holistic arm's 4%, and rewording
them would break the comparison the whole arm is for. They are used **verbatim**, read from
`pr_shared.focused_prompts`.

What is *not* reused is v2's submission envelope. Those prompts end by describing v2 fields —
`path`, `severity`, `claim`, `suggested_fix` — and a v2 finding is not a v4 candidate: it
carries no `change_ids`, no `primary_change_id`, no `primary_subject`, no `issue_kind`. Sent
through `submit_candidates` unchanged, every finding would be rejected. So the v2 system text
is followed by the v4 contract, which explicitly supersedes the field list above it. The
anchoring this buys is the point of the exercise: candidates land on real change targets and
are comparable to the other two arms, instead of on line numbers nothing joins.

Only the invocation's **scheduled sites** are rendered as review targets, not the whole work
unit. A duplication agent scheduled on the two added declarations in a unit should not be
handed the six modified proofs as well: they are another spec's job, and the enumeration
that makes the arm gold-free is exactly the claim that each spec sees only what its rule
selected. Sites are always a subset of the unit's `change_ids`, so the existing submission
contract — `change_ids ⊆ unit` — keeps holding unchanged.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from ape.tasks.lean_tasks.formal_math.pr_shared.focused_prompts import FOCUSED_PROMPTS

from .focused_specs import FocusedAgentSpec, FocusedInvocation
from .io import canonical_json_bytes, sha256_bytes
from .render_prompts import FACET_CHECKLIST
from .schema import ChangeGraph, RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit

FOCUSED_RENDERER_VERSION = "focused-prompt/1"

#: The v4 submission envelope, appended after each spec's own instruction.
#:
#: `issue_kind` is fixed by the spec rather than chosen by the model. The spec *is* the
#: claim — a proof_golf invocation asserts proof simplification and nothing else — and a
#: model free to relabel its kind could route itself to a verifier whose warrant is laxer
#: than the one its own instruction was written against.
_SUBMISSION_CONTRACT = """

# Submission contract for this run

This supersedes any field list above: findings are submitted as *candidates* against the
review targets below, not as free-standing line-span findings.

Finish by calling submit_candidates exactly once, using:
{{"candidates": [{{"primary_change_id": "change:...", "primary_entity_id": "... or null",
"primary_subject": "copy exactly", "change_ids": ["change:..."],
"concern_family": "{concern_family}", "issue_kind": "{issue_kind}",
"concern_label": "short free-form description", "severity": "blocking|advisory",
"claim": "specific present problem", "requested_change": "concrete maintainer request",
"suggested_fix": "optional implementation detail or null", "proposed_edit": {{"path": "...",
"declaration_name": "...", "new_declaration": "complete replacement"}} or null,
"model_confidence": 0.0}}]}}. An empty candidates list is valid.

Every candidate must set concern_family to "{concern_family}" and issue_kind to
"{issue_kind}" — this run is the {spec_id} check and makes no other kind of claim. Each
candidate has exactly one primary target and subject; copy their IDs and subject exactly, and
name the primary declaration in the claim. Submit a candidate only for the review targets
listed below. Verify every edit with lean_verify_edit before submitting it."""


def _target_block(target) -> str:
    base = target.base_code if target.base_code is not None else "(not present)"
    reviewed = target.reviewed_code if target.reviewed_code is not None else "(not present)"
    return (
        f"## Review target\nChange ID (copy exactly): `{target.change_id}`\n"
        f"Path: {target.path}\nKind: {target.kind}\n"
        f"Primary subject (copy exactly): `{target.declaration_name or target.path}`\n"
        f"Primary entity IDs (copy one, or null if none): "
        f"{', '.join(target.reviewed_entity_ids + target.base_entity_ids) or '(none)'}\n"
        f"### Complete base region\n```lean\n{base}\n```\n"
        f"### Complete reviewed region\n```lean\n{reviewed}\n```\n"
        f"### Exact changed fragments\n```diff\n{''.join(target.diff_fragments)}\n```"
    )


def focused_system_prompt(spec: FocusedAgentSpec) -> str:
    """The spec's v2 instruction verbatim, followed by the v4 envelope."""

    _tools, system, _user = FOCUSED_PROMPTS[spec.spec_id]
    return system + _SUBMISSION_CONTRACT.format(
        concern_family=spec.concern_family,
        issue_kind=spec.issue_kind,
        spec_id=spec.spec_id,
    )


def render_focused_invocation(
    spec: FocusedAgentSpec, invocation: FocusedInvocation, unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput, graph: ChangeGraph,
) -> RenderedPrompt:
    if invocation.spec_id != spec.spec_id:
        raise ValueError(
            f"invocation {invocation.invocation_id} is not a {spec.spec_id} invocation"
        )
    if not set(invocation.site_change_ids) <= set(unit.change_ids):
        raise ValueError(
            f"invocation {invocation.invocation_id} names sites outside its work unit"
        )
    targets = {item.change_id: item for item in graph.targets}
    blocks = [
        f"{_target_block(targets[change_id])}\n{FACET_CHECKLIST}"
        for change_id in invocation.site_change_ids
    ]
    system = focused_system_prompt(spec)
    user = (
        f"# PR #{episode.pr_number}: {episode.title.text or ''}\n"
        f"Round: {episode.round_index}\n"
        f"Description: {episode.description.text or '(unavailable)'}\n"
        f"Changed files: {', '.join(episode.changed_files)}\n\n"
        f"You are running the {spec.spec_id} check on the "
        f"{len(blocks)} review target(s) below.\n\n" + "\n\n".join(blocks)
    )
    return RenderedPrompt(
        work_unit_id=unit.work_unit_id,
        invocation_id=invocation.invocation_id,
        spec_id=spec.spec_id,
        renderer_version=FOCUSED_RENDERER_VERSION,
        system_prompt=system, user_prompt=user,
        system_sha256=sha256_bytes(system.encode()),
        user_sha256=sha256_bytes(user.encode()),
        prompt_sha256=sha256_bytes(canonical_json_bytes({"system": system, "user": user})),
        rendered_chars=len(system) + len(user),
        estimated_tokens=(len(system.encode()) + len(user.encode()) + 3) // 4,
        included_change_ids=list(invocation.site_change_ids),
        # Sites, not the unit, are this invocation's scope; the unit's other targets are
        # another spec's business and are recorded as omitted rather than silently dropped.
        omitted_change_ids=[
            change_id for change_id in unit.change_ids
            if change_id not in set(invocation.site_change_ids)
        ],
        submission_verification_policy="verify_checkable_edits",
    )


def render_focused_all(
    specs: Iterable[FocusedAgentSpec], invocations: Iterable[FocusedInvocation],
    units: Iterable[ReviewWorkUnit], episodes: Iterable[ReviewEpisodeInput],
    graphs: Iterable[ChangeGraph],
) -> List[RenderedPrompt]:
    spec_by_id: Dict[str, FocusedAgentSpec] = {item.spec_id: item for item in specs}
    unit_by_id = {item.work_unit_id: item for item in units}
    episode_by_id = {item.episode_id: item for item in episodes}
    graph_by_id = {item.graph_id: item for item in graphs}
    rendered = []
    for invocation in invocations:
        unit = unit_by_id[invocation.work_unit_id]
        rendered.append(render_focused_invocation(
            spec_by_id[invocation.spec_id], invocation, unit,
            episode_by_id[unit.episode_id], graph_by_id[unit.graph_id],
        ))
    return rendered
