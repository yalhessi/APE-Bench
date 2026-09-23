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
#: diff to that target (`render_prompts.target_diff_section`); `/4` tells the arms a compile
#: can settle that `patch_set` exists, in the contract rather than in one arm's own prose.
#: Every prompt this renderer produces changed at each bump, so runs across one are not
#: prompt-identical and must not be compared as if they were -- except at `/4`, where the
#: seven granted arms' prompts change and the other three are byte-identical, which is
#: asserted rather than assumed (`test_pr_review_v4_focused_task.py`).
#:
#: The two contract knobs do not bump this constant; they suffix it (`renderer_version_for`).
#: With both off the text is byte-identical to `/4`, so a sealed control agenda keeps its
#: version and every prompt hash, and a run that renders the extra text says which text by name.
FOCUSED_RENDERER_VERSION = "focused-prompt/4"

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
{patch_set_field}"model_confidence": 0.0}}]}}. An empty candidates list is valid.

{abstention_paragraph}

Every candidate must set concern_family to "{concern_family}" and issue_kind to
"{issue_kind}" — this run is the {spec_id} check and makes no other kind of claim. Each
candidate has exactly one primary target and subject; copy their IDs and subject exactly, and
name the primary declaration in the claim. Submit a candidate only for the review targets
listed below. Verify every edit with lean_verify_edit before submitting it.{ask_without_fix_clause}{target_sections}

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
`concern_label` is what lets it be verified against the library rather than taken on trust.{patch_set_clause}"""

#: What a granted arm is told about coordinated fixes, in the contract that supersedes the
#: prompt above it. `family_design` alone carried this, in its own prompt, 2,400 characters
#: above a template that did not list the field -- so the one arm that could submit one was
#: told about it by the text the contract overrides. The instruction is the same instruction;
#: what changes is that it is now where the arm reads its field list, and that every arm whose
#: fix a compile settles reads it.
PATCH_SET_FIELD = ('"patch_set": [{"path": "...", "change_id": "change:...",\n'
                   '"declaration_name": "...", "new_declaration": "complete replacement"}] '
                   'or null,\n')

PATCH_SET_CLAUSE = """

## Coordinated fixes

Where the fix genuinely spans several declarations, submit it as `patch_set` — a list of edits
applied and compiled TOGETHER, instead of `proposed_edit`. Use it when the halves are
individually wrong: deleting a generated lemma without adding the attribute that regenerates
it does not compile, and neither does adding a dual before the lemma it is derived from
exists. An empty `new_declaration` deletes the declaration.

Every edit names the `change_id` it is about, and that target must be one your candidate
claims in `change_ids` — an edit may not rewrite a declaration you are not asking about. The
whole candidate is refused if any edit escapes its target, if two edits overlap, or if any
touched file fails to compile, so verify with lean_verify_edit as you go. Where one edit
suffices, use `proposed_edit` as usual."""


#: The abstention paragraph every arm has read since `/1`, verbatim. Rendered whenever the run
#: does not ask for per-target verdicts, so v4's arm and every control stay byte-identical.
LEGACY_ABSTENTION_PARAGRAPH = """Submitting nothing is a correct and common outcome of this check, and nothing below asks you to
avoid it. It does have to say which outcome it was: when `candidates` is empty, set
`abstention_reason` — `nothing_of_this_kind_here`, `already_correct`, `below_my_bar`,
`could_not_establish`, or `belongs_to_another_concern` — and put one sentence in
`abstention_detail` naming what you considered. Never add a candidate you do not believe in to
avoid abstaining; a wrong finding costs this review far more than a silence does."""

#: The same paragraph for an arm that answers every target. It does not name `abstention_reason`:
#: the verdict tool has no such argument, and the unchanged `/4` paragraph told the arms to set it
#: on the one paid run that used the verdict tool. What it no longer says is also the point: "a
#: wrong finding costs this review far more than a silence does" is a price on speech that no
#: measurement here supports, and it was the last sentence an arm read before deciding.
VERDICTS_ABSTENTION_PARAGRAPH = """Submitting no candidate is a correct and common outcome of this check. Under this run's contract
you record it target by target, in `target_verdicts` -- see "Account for every target" below --
rather than with one reason for the submission as a whole."""

#: What an arm under `verify_edits_if_present` is told, where it reads its field list.
#:
#: The tool had been relaxed and the arm had not been told: the arm supplements say "Report only
#: golfs you have VERIFIED compile" and "If nothing you attempted compiled, submit nothing". About 9
#: of 43 gold-site abstention texts on the held-out run name that rule, including PR 33149, where
#: the arm found the library lemma answering "use the existing Parseval identity" and could not say
#: so without a patch the maintainer never supplied either. From `configs/v5_replay_ask_without_fix.yaml`.
ASK_WITHOUT_FIX_CLAUSE = """

## When the fix does not compile

A candidate may be submitted with `proposed_edit: null` when you have identified a change a
maintainer would want and could not produce an edit that compiles. This overrides any
instruction above to report only verified edits, or to submit nothing when no edit you
attempted compiled. Put the transformation in `requested_change`, precisely enough to carry
out, and in `suggested_fix` say what you attempted and what the compiler said. Such a candidate
is recorded as unverified: it is not published as a verified finding, and it is not held
against you that it carries no edit. An edit you do supply is still compiled, and one that fails
to compile is refused.

This is not a request to find something, and you should not add a candidate you do not believe
in. It removes one specific reason for silence: that the fix would not compile, when you were
confident about the ask itself."""

#: What an arm under `target_verdicts` is told. The tool enforces the first section; the second is
#: the contract's only definition of `severity` beyond the JSON literal "blocking|advisory". Gold
#: marks 19 of 24 held-out judgments advisory, and on 33337 the naming arm wrote "emerging (21 vs 7)
#: ... so I'm not requesting a rename" -- then, forced, produced the maintainer's rename.
TARGET_SECTIONS = """

## Account for every target

Each review target below ends with exactly one entry in `target_verdicts`:
{"change_id": "change:...", "reason": "one sentence naming what you checked here and what you
found", "verdict": "issue" | "no_issue" | "cannot_determine"} -- the reason first, then the
verdict. A target you are asking something of is `issue`, and is covered by a candidate whose
`primary_change_id` is that target; a candidate's primary target is always an `issue`. `no_issue`
means you checked it and it is fine under this check; `cannot_determine` means your tools could
not settle it, and its reason names the evidence you needed. Both are correct and common
outcomes; this records them and does not ask you to avoid them. Never add a candidate you do not
believe in to fill a slot.

## Two strengths of ask

Maintainers here ask at advisory strength far more often than at blocking strength, and
`severity` has a word for each. `blocking` is a change a maintainer would hold the PR for.
`advisory` is a change you believe a maintainer would ask for and would merge without: a
convention the repository is adopting but has not settled, or an improvement the author could
reasonably decline. A claim you hold at advisory strength is one you believe in: file it as
advisory rather than withholding it. Withhold a claim when you lack evidence for it, not because
the evidence you have makes it advisory rather than blocking."""


def renderer_version_for(procedure_variant: str = "baseline", *,
                         submission_verification_policy: Optional[str] = None,
                         target_verdicts: bool = False) -> str:
    """The renderer version a prompt is stamped with: the base, plus what else rendered.

    The variant travels in the version string as well as in the prompt hash: the hash alone
    says two runs differed, and the name says how without reading the prompt. `baseline` with
    both contract knobs off is spelled as the bare version so every pre-existing artifact keeps
    its value. The knobs come before the variant, in the order their text appears.
    """

    parts = [FOCUSED_RENDERER_VERSION]
    if submission_verification_policy == "verify_edits_if_present":
        parts.append("ask_without_fix")
    if target_verdicts:
        parts.append("target_verdicts")
    if procedure_variant != "baseline":
        parts.append(procedure_variant)
    return "+".join(parts)


def focused_system_prompt(spec: FocusedAgentSpec,
                          procedure_variant: str = "baseline",
                          submission_verification_policy: Optional[str] = None,
                          target_verdicts: bool = False) -> str:
    """The spec's v2 instruction verbatim, a procedure supplement, then the v4 envelope.

    The supplement sits between the check and the submission contract on purpose: it modifies
    how the arm conducts the check, and the contract is about what a valid submission is. An
    unknown variant raises rather than rendering the baseline under the treatment's name.

    The two knobs are the ones the task enforces, and the contract says what each allows, so an
    arm is never told one rule and refused by another. With both off this is `/4`'s text.
    """

    from src.mathlib_review.agenda.registry import patch_set_arms

    coordinated = spec.spec_id in patch_set_arms()
    _tools, system, _user = FOCUSED_PROMPTS[spec.spec_id]
    return system + procedure_supplement(procedure_variant, spec.spec_id) + \
        SUBMISSION_CONTRACT.format(
            concern_family=spec.concern_family,
            issue_kind=spec.issue_kind,
            spec_id=spec.spec_id,
            patch_set_field=PATCH_SET_FIELD if coordinated else "",
            patch_set_clause=PATCH_SET_CLAUSE if coordinated else "",
            abstention_paragraph=(
                VERDICTS_ABSTENTION_PARAGRAPH if target_verdicts
                else LEGACY_ABSTENTION_PARAGRAPH),
            ask_without_fix_clause=(
                ASK_WITHOUT_FIX_CLAUSE
                if submission_verification_policy == "verify_edits_if_present" else ""),
            target_sections=TARGET_SECTIONS if target_verdicts else "",
        )


def render_focused_invocation(
    spec: FocusedAgentSpec, invocation: FocusedInvocation, unit: ReviewWorkUnit,
    episode: ReviewEpisodeInput, graph: ChangeGraph,
    context_text: str = "",
    procedure_variant: str = "baseline",
    submission_verification_policy: Optional[str] = None,
    target_verdicts: bool = False,
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
    system = focused_system_prompt(spec, procedure_variant, submission_verification_policy,
                                   target_verdicts)
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
        renderer_version=renderer_version_for(
            procedure_variant, submission_verification_policy=submission_verification_policy,
            target_verdicts=target_verdicts),
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
        # `None` is "the run did not say", and a specialist's edit is settled by compiling it.
        submission_verification_policy=submission_verification_policy or "verify_checkable_edits",
    )


def render_focused_all(
    specs: Iterable[FocusedAgentSpec], invocations: Iterable[FocusedInvocation],
    units: Iterable[ReviewWorkUnit], episodes: Iterable[ReviewEpisodeInput],
    graphs: Iterable[ChangeGraph],
    context_by_invocation: Optional[Dict[str, str]] = None,
    procedure_variant: str = "baseline",
    submission_verification_policy: Optional[str] = None,
    target_verdicts: bool = False,
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
            submission_verification_policy,
            target_verdicts,
        ))
    return rendered
