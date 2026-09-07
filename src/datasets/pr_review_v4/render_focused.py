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

from typing import Any, Dict, Iterable, List, Optional, Sequence

from ape.tasks.lean_tasks.formal_math.pr_shared.focused_prompts import FOCUSED_PROMPTS

from .focused_specs import FocusedAgentSpec, FocusedInvocation
from .io import canonical_json_bytes, sha256_bytes
from .render_prompts import FACET_CHECKLIST
from .schema import ChangeGraph, RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit

#: Bumped for the hunk/checklist deduplication: every prompt this renderer produces changed,
#: so runs before and after are not prompt-identical and must not be compared as if they were.
FOCUSED_RENDERER_VERSION = "focused-prompt/2"

#: The same checklist, emitted once for the whole prompt instead of once per target.
#:
#: `render_prompts.FACET_CHECKLIST` keeps its per-target wording and is deliberately left alone:
#: it is hashed into every frozen `rendered_prompts.jsonl`, so editing it moves every prompt
#: hash in every release at once. The generalist path therefore still carries the repetition
#: until a release is re-rendered; only the arms this renderer serves are deduplicated here.
FOCUSED_FACET_CHECKLIST = FACET_CHECKLIST.replace(
    "### Maintainer ask checklist for this target\n"
    "Consider every item, but emit a candidate only for a concrete change you would actually "
    "request.",
    "### Maintainer ask checklist\n"
    "Apply every item to every review target above, but emit a candidate only for a concrete "
    "change you would actually request.",
)

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


def _target_block(target, fragments_section: Optional[str] = None) -> str:
    base = target.base_code if target.base_code is not None else "(not present)"
    reviewed = target.reviewed_code if target.reviewed_code is not None else "(not present)"
    if fragments_section is None:
        fragments_section = f"```diff\n{''.join(target.diff_fragments)}\n```"
    return (
        f"## Review target\nChange ID (copy exactly): `{target.change_id}`\n"
        f"Path: {target.path}\nKind: {target.kind}\n"
        f"Primary subject (copy exactly): `{target.declaration_name or target.path}`\n"
        f"Primary entity IDs (copy one, or null if none): "
        f"{', '.join(target.reviewed_entity_ids + target.base_entity_ids) or '(none)'}\n"
        f"### Complete base region\n```lean\n{base}\n```\n"
        f"### Complete reviewed region\n```lean\n{reviewed}\n```\n"
        f"### Exact changed fragments\n{fragments_section}"
    )


def _target_blocks(targets: Sequence[Any]) -> List[str]:
    """One block per target, with each distinct diff hunk printed exactly once.

    A work unit is a group of related changes in one file, so its targets usually share a hunk:
    measured across smoke4's 143 prompts, the mean was 1.8 distinct hunks against 3.4 targets,
    and 32% of all prompt text was a hunk verbatim repeated within the same prompt. One
    `api_reuse` job carried six targets, one unique hunk, and 16,710 duplicate characters out of
    33,174. Re-reading the same diff five times is paid for on every invocation and crowds out
    the context the arm was given the slice for.

    The first target to use a hunk prints it; later targets naming the same hunk get a pointer
    to that target's subject. Nothing else about a target block changes, so the per-target
    identity fields the submission contract keys on are untouched.
    """

    first_use: Dict[str, str] = {}
    blocks: List[str] = []
    for target in targets:
        fragments = "".join(target.diff_fragments)
        subject = target.declaration_name or target.path
        owner = first_use.get(fragments)
        if owner is None:
            first_use[fragments] = subject
            blocks.append(_target_block(target))
        else:
            blocks.append(_target_block(
                target,
                f"Identical to the fragments shown for `{owner}` above.",
            ))
    return blocks


def focused_system_prompt(spec: FocusedAgentSpec) -> str:
    """The spec's v2 instruction verbatim, followed by the v4 envelope."""

    _tools, system, _user = FOCUSED_PROMPTS[spec.spec_id]
    return system + SUBMISSION_CONTRACT.format(
        concern_family=spec.concern_family,
        issue_kind=spec.issue_kind,
        spec_id=spec.spec_id,
    )


def render_focused_invocation(
    spec: FocusedAgentSpec, invocation: FocusedInvocation, unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput, graph: ChangeGraph,
    context_text: str = "",
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
    blocks = _target_blocks([targets[change_id] for change_id in invocation.site_change_ids])
    system = focused_system_prompt(spec)
    user = (
        f"# PR #{episode.pr_number}: {episode.title.text or ''}\n"
        f"Round: {episode.round_index}\n"
        f"Description: {episode.description.text or '(unavailable)'}\n"
        f"Changed files: {', '.join(episode.changed_files)}\n\n"
        f"You are running the {spec.spec_id} check on the "
        f"{len(blocks)} review target(s) below.\n\n" + "\n\n".join(blocks)
        + f"\n\n{FOCUSED_FACET_CHECKLIST}"
        # Appended *after* the targets, and hashed with them: the slice is part of the
        # sealed prompt, so a run cannot silently differ from the plan it sealed.
        + (context_text or "")
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
    context_by_invocation: Optional[Dict[str, str]] = None,
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
        ))
    return rendered
