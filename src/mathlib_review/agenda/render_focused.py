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

from typing import Dict, Iterable, List, Optional

from ape.tasks.lean_tasks.formal_math.review.focused_prompts import (
    FOCUSED_PROMPTS, procedure_supplement,
)

from src.mathlib_review.agenda.focused_specs import FocusedAgentSpec, FocusedInvocation
from src.mathlib_review.io import canonical_json_bytes, sha256_bytes
from src.mathlib_review.agenda.render_prompts import (
    FACET_CHECKLIST_ONCE,
    target_blocks,
)
from src.mathlib_review.schema import ChangeGraph, RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit

#: `/2` deduplicated the hunk and the checklist within a prompt; `/3` scopes each target's
#: diff to that target (`render_prompts.target_diff_section`). Every prompt this renderer
#: produces changed at each bump, so runs across one are not prompt-identical and must not be
#: compared as if they were.
FOCUSED_RENDERER_VERSION = "focused-prompt/3"

#: The v4 submission envelope, appended after each spec's own instruction.
#:
#: `issue_kind` is fixed by the spec rather than chosen by the model. The spec *is* the
#: claim — a proof_golf invocation asserts proof simplification and nothing else — and a
#: model free to relabel its kind could route itself to a verifier whose warrant is laxer
#: than the one its own instruction was written against.
SUBMISSION_CONTRACT = """

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

Submitting nothing is a correct and common outcome of this check, and nothing below asks you to
avoid it. It does have to say which outcome it was: when `candidates` is empty, set
`abstention_reason` — `nothing_of_this_kind_here`, `already_correct`, `below_my_bar`,
`could_not_establish`, or `belongs_to_another_concern` — and put one sentence in
`abstention_detail` naming what you considered. Never add a candidate you do not believe in to
avoid abstaining; a wrong finding costs this review far more than a silence does.

Every candidate must set concern_family to "{concern_family}" and issue_kind to
"{issue_kind}" — this run is the {spec_id} check and makes no other kind of claim. Each
candidate has exactly one primary target and subject; copy their IDs and subject exactly, and
name the primary declaration in the claim. Submit a candidate only for the review targets
listed below. Verify every edit with lean_verify_edit before submitting it.

## State the change, not the impression

`requested_change` must name the transformation a maintainer would perform, precisely enough
that someone could carry it out without asking you a follow-up question. "Rename `foo_aux'`
to `foo_of_isUnit`" is a request. "This name is unclear" is not. If you propose a rename, give
the new name. If you propose a generalisation, give the generalised statement. If you propose
a different proof, give it.

Where a local fix and a structural one both apply, ask for the structural one. The measured
failure of this system is under-reaching: landing on exactly the right declaration and
requesting a smaller change than the maintainer wanted — offering a docstring rewording where
they asked for the lemma to be renamed and reproved through `OrderDual`, or a tidier tactic
where they asked for the result to be generalised. A reviewer who notices the right site and
asks for the wrong size of change has not helped.

Say which field your claim is about. If what you have found is that something already exists
in the library, that is a duplication claim whatever check you are running, and saying so in
`concern_label` is what lets it be verified against the library rather than taken on trust."""


def renderer_version_for(procedure_variant: str = "baseline") -> str:
    """The renderer version a variant stamps on its prompts.

    The variant travels in the version string as well as in the prompt hash: the hash alone
    says two runs differed, and the name says how without reading the prompt. `baseline` is
    spelled as the bare version so every pre-existing artifact keeps its value.
    """

    if procedure_variant == "baseline":
        return FOCUSED_RENDERER_VERSION
    return f"{FOCUSED_RENDERER_VERSION}+{procedure_variant}"


def focused_system_prompt(spec: FocusedAgentSpec,
                          procedure_variant: str = "baseline") -> str:
    """The spec's v2 instruction verbatim, a procedure supplement, then the v4 envelope.

    The supplement sits between the check and the submission contract on purpose: it modifies
    how the arm conducts the check, and the contract is about what a valid submission is. An
    unknown variant raises rather than rendering the baseline under the treatment's name.
    """

    _tools, system, _user = FOCUSED_PROMPTS[spec.spec_id]
    return system + procedure_supplement(procedure_variant, spec.spec_id) + \
        SUBMISSION_CONTRACT.format(
            concern_family=spec.concern_family,
            issue_kind=spec.issue_kind,
            spec_id=spec.spec_id,
        )


def render_focused_invocation(
    spec: FocusedAgentSpec, invocation: FocusedInvocation, unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput, graph: ChangeGraph,
    context_text: str = "",
    procedure_variant: str = "baseline",
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
    # The checklist is identical for every target and was previously appended to each one: 530
    # copies across smoke4's 143 prompts, 13% of all prompt text. It is emitted once, after the
    # targets, so it still reads as applying to all of them.
    blocks = target_blocks(
        [targets[change_id] for change_id in invocation.site_change_ids], scoped=True)
    system = focused_system_prompt(spec, procedure_variant)
    user = (
        f"# PR #{episode.pr_number}: {episode.title.text or ''}\n"
        f"Round: {episode.round_index}\n"
        f"Description: {episode.description.text or '(unavailable)'}\n"
        f"Changed files: {', '.join(episode.changed_files)}\n\n"
        f"You are running the {spec.spec_id} check on the "
        f"{len(blocks)} review target(s) below.\n\n" + "\n\n".join(blocks)
        + f"\n\n{FACET_CHECKLIST_ONCE}"
        # Appended *after* the targets, and hashed with them: the slice is part of the
        # sealed prompt, so a run cannot silently differ from the plan it sealed.
        + (context_text or "")
    )
    return RenderedPrompt(
        work_unit_id=unit.work_unit_id,
        invocation_id=invocation.invocation_id,
        spec_id=spec.spec_id,
        renderer_version=renderer_version_for(procedure_variant),
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
    context_by_invocation: Optional[Dict[str, str]] = None,
    procedure_variant: str = "baseline",
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
            (context_by_invocation or {}).get(invocation.invocation_id, ""),
            procedure_variant,
        ))
    return rendered
