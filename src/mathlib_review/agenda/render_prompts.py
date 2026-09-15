"""Single production renderer for both prompt previews and task execution."""

import argparse
import difflib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, sha256_bytes, write_once
from src.mathlib_review.schema import ChangeGraph, PromptPrecedent, RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit


SYSTEM_PROMPT = """Act as a Mathlib maintainer reviewing complete change targets. Predict concrete
changes a maintainer would plausibly request, not general risks, questions, defenses of the code, or
notes that something is merely worth checking. Examine every target across all concern families:
proof-golf, generalization, duplication, naming, documentation, style, scope, and correctness. There
is no quota: submit only actionable requests supported by the reviewed code, and submit none when no
request is warranted.

Each candidate has exactly one primary target and subject. Copy their IDs and subject exactly. The
claim must assert a present problem and name the primary declaration when one is supplied. The
requested_change must be an imperative, concrete transformation that would resolve it. Related
change_ids may be included, but never attach a claim about a neighboring declaration to this target.
Evidence planning happens after generation; do not submit evidence requests.

Finish by calling submit_candidates exactly once, using:
{"candidates": [{"primary_change_id": "change:...", "primary_entity_id": "... or null",
"primary_subject": "copy exactly", "change_ids": ["change:..."],
"concern_family": "correctness|proof-golf|duplication|naming|generalization|documentation|style|scope|other",
"concern_label": "short free-form description", "severity": "blocking|advisory",
"claim": "specific present problem", "requested_change": "concrete maintainer request",
"suggested_fix": "optional implementation detail or null", "proposed_edit": {"path": "...",
"declaration_name": "...", "new_declaration": "complete replacement"} or null,
"model_confidence": 0.0}]}. An empty candidates list is valid."""


#: `candidate-prompt/12` adds one field to the submission contract: `issue_kind`.
#:
#: It is a separate constant rather than an edit to `SYSTEM_PROMPT` because that constant is
#: hashed into every frozen `rendered_prompts.jsonl`; editing it in place moved every
#: prompt hash in every release at once, which is precisely what a renderer version exists
#: to prevent. Runs at /9, /10 and /11 stay byte-identical.
SYSTEM_PROMPT_V12 = SYSTEM_PROMPT.replace(
    'Evidence planning happens after generation; do not submit evidence requests.',
    "Evidence planning happens after generation; do not submit evidence requests.\n"
    "State an issue_kind naming what kind of problem this is, so the claim can be checked "
    "against the repository itself. Choose the kind whose check would settle your claim: "
    "naming_convention_violation when the corpus's own naming population would show the name "
    "is wrong, style_norm_violation when Mathlib's style linters would flag it, "
    "documentation_gap when documentation is absent, duplicate_implementation when an "
    "existing declaration already does this. Choose the kind that matches what you actually "
    "claim, not the one most likely to be confirmed.",
).replace(
    '"concern_label": "short free-form description"',
    '"issue_kind": "broken_build|correctness_policy|documentation_gap|'
    'duplicate_implementation|generalization_available|missed_canonical_api|'
    'naming_convention_violation|policy_violation|proof_simplification|scope_placement|'
    'style_norm_violation", "concern_label": "short free-form description"',
)


def renderer_number(renderer_version: str) -> int:
    """The numeric part of `candidate-prompt/N`.

    String comparison is wrong here and quietly so: `"candidate-prompt/9" >
    "candidate-prompt/12"` is True lexicographically, which made every /9 work unit look
    newer than /12 and demanded a field its prompt never asked for.
    """

    try:
        return int(renderer_version.rsplit("/", 1)[-1])
    except (ValueError, IndexError):
        return 0


def system_prompt_for(renderer_version: str) -> str:
    """The submission contract for one renderer version."""

    return SYSTEM_PROMPT_V12 if renderer_number(renderer_version) >= 12 else SYSTEM_PROMPT


FACET_CHECKLIST = """### Maintainer ask checklist for this target
Consider every item, but emit a candidate only for a concrete change you would actually request.
1. proof-golf: replace a longer/manual proof with a canonical lemma, tactic, or proof structure.
2. generalization: weaken hypotheses or state the declaration at the reusable level maintainers expect.
3. duplication: replace new code with an existing declaration or shared abstraction.
4. naming: rename declarations to match their meaning, type, and local sibling conventions.
5. documentation: correct or complete docstrings and module documentation.
6. style: request a specific formatting, binder, calc, case-split, attribute, or structural rewrite.
7. scope: move, split, expose, privatize, or remove code that is misplaced for this PR.
8. correctness: fix a present semantic, elaboration, build, policy, or API error.
Do not report that an item was checked, does not apply, or is merely worth investigating."""


#: The same checklist, addressed to every target at once instead of repeated under each.
#:
#: The per-target wording above is hashed into every frozen `rendered_prompts.jsonl`, so it is
#: never edited in place; a renderer version chooses between them.
FACET_CHECKLIST_ONCE = FACET_CHECKLIST.replace(
    "### Maintainer ask checklist for this target\n"
    "Consider every item, but emit a candidate only for a concrete change you would actually "
    "request.",
    "### Maintainer ask checklist\n"
    "Apply every item to every review target above, but emit a candidate only for a concrete "
    "change you would actually request.",
)


def _join_regions(chunks: Sequence[str], *, preserve_adjacency: bool) -> str:
    """Concatenate a declaration's parts the way the file has them.

    `"\n".join` inserts a separator unconditionally, and a region already ends with its own
    newline, so it fabricated a blank line that is not in the source. On PR 33321 that turned
    `… -/\n@[to_additive …` -- a doc-comment immediately followed by the attribute it belongs
    to, which is ordinary Lean -- into `… -/\n\n@[to_additive …`, two floating comments. The
    reviewer answered the artifact: it asked to remove "an extra adjacent doc comment" and the
    judge scored the obligation a miss on a run where the site was correctly located.

    `preserve_adjacency` is False only for `candidate-prompt/13`, whose release was built from
    the fabricated form and must still re-render to the prompts it froze.
    """

    parts = [chunk for chunk in chunks if chunk]
    if not preserve_adjacency:
        return "\n".join(parts)
    out = ""
    for chunk in parts:
        if out and not out.endswith("\n"):
            out += "\n"
        out += chunk
    return out


def target_diff_section(target: Any, attachments: Sequence[Any] = (),
                        *, preserve_adjacency: bool = True) -> str:
    """The `Exact changed fragments` body for one target, scoped to that target.

    `diff_fragments` holds the raw `@@` hunks covering the target's changed ranges, so a target
    in a single-hunk file inherits the whole file's diff. On PR 33149 that is one 17,303-char
    hunk shipped to all 120 jobs, each reviewing one declaration averaging 163 characters — a
    106:1 ratio of pasted diff to reviewed code — and across a 12-PR lead repetition the section
    is 43.6% of all rendered prompt characters with 95.5% of its volume a re-send of a block
    another job for the same PR already carries. Caching does not absorb it: the prompt diverges
    at the change-id line, which precedes this section.

    A target is by definition not a fragment, so the section is rendered from the target's own
    two complete regions instead — the choice `analysis/review_overlay._pretty_diff` already
    makes for the overlay, for the same stated reason.

    Import blocks are the one kind with nothing to diff: `base_code` and `reviewed_code` are
    built from semantic entities and an import block has none, so they keep the raw hunk, which
    is the only record of what changed there. Measured over `dev-medium-0.3.0` that exception is
    17 of 508 targets and 2,195 of 2,583,336 fragment characters. An empty diff falls back the
    same way, so a target can never be shown a blank change.
    """

    raw = f"```diff\n{''.join(target.diff_fragments)}\n```"
    # A declaration's doc-comment and attributes are separate targets but not separate code:
    # in Lean they precede what they qualify, so they are diffed as part of it. Severing them
    # cost two obligations on PR 33321 that every baseline repetition had found.
    ordered = [*attachments, target]
    base = _join_regions([item.base_code for item in ordered],
                         preserve_adjacency=preserve_adjacency)
    reviewed = _join_regions([item.reviewed_code for item in ordered],
                             preserve_adjacency=preserve_adjacency)
    if not base and not reviewed:
        return raw
    lines = list(difflib.unified_diff(
        base.splitlines(), reviewed.splitlines(), lineterm="", n=3))
    # `unified_diff` emits `--- ` / `+++ ` headers even with no file names given; the path is
    # already in the target block's own header.
    if lines[:1] and lines[0].startswith("---"):
        lines = lines[2:] if lines[1:] and lines[1].startswith("+++") else lines[1:]
    if not lines:
        return raw
    return "```diff\n" + "\n".join(lines) + "\n```"


def target_block(target: Any, fragments_section: Optional[str] = None) -> str:
    """One `## Review target` block, shared by the generalist and focused renderers.

    The two renderers emitted this byte-for-byte independently until the fragment scoping
    landed; it lives here because `render_focused` imports this module and not the reverse.
    """

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


def target_blocks(targets: Iterable[Any], *, scoped: bool,
                  preserve_adjacency: bool = True) -> List[str]:
    """One block per target, with each distinct fragments section printed exactly once.

    The first target to use a section prints it; a later target whose section is identical gets
    a pointer to that target's subject. Under `scoped` the sections are per-target diffs and
    rarely repeat, so the pointer is mostly inert there — it still fires for genuinely identical
    changes, and it is what collapses a shared hunk when a target falls back to the raw form.
    """

    targets = list(targets)
    # Attachments are rendered inside their owner's diff, so they point at it instead of
    # repeating it. The owner may appear after them in the unit, so the wording does not say
    # "above".
    present = {item.change_id: item for item in targets}
    attached_to_owner: Dict[str, List[Any]] = {}
    if scoped:
        for item in targets:
            owner_id = getattr(item, "attached_to", None)
            if owner_id and owner_id in present:
                attached_to_owner.setdefault(owner_id, []).append(item)
    owner_subject = {
        owner_id: (present[owner_id].declaration_name or present[owner_id].path)
        for owner_id in attached_to_owner
    }
    shown_with_owner = {
        item.change_id: owner_id
        for owner_id, items in attached_to_owner.items() for item in items
    }

    first_use: Dict[str, str] = {}
    blocks: List[str] = []
    for target in targets:
        if target.change_id in shown_with_owner:
            blocks.append(target_block(target, "Shown with the changed fragments for "
                                       f"`{owner_subject[shown_with_owner[target.change_id]]}`."))
            continue
        section = target_diff_section(
            target, attached_to_owner.get(target.change_id, ()),
            preserve_adjacency=preserve_adjacency) if scoped else (
            f"```diff\n{''.join(target.diff_fragments)}\n```")
        subject = target.declaration_name or target.path
        owner = first_use.get(section)
        if owner is None:
            first_use[section] = subject
            blocks.append(target_block(target, section))
        else:
            blocks.append(target_block(
                target, f"Identical to the fragments shown for `{owner}` above."))
    return blocks


GENERIC_MAINTAINER_EXEMPLARS = """# Synthetic maintainer-request exemplars
These examples teach specificity and register only. They are not evidence or patterns to copy unless
the reviewed target independently supports the same request.

## Existing API instead of manual proof
Weak observation: `Demo.image_insert` has several rewrites and may be brittle.
Maintainer request:
- claim: `Demo.image_insert` manually proves the behavior already provided by `Set.image_insert`.
- requested_change: Replace the proof of `Demo.image_insert` with a direct `simpa` using
  `Set.image_insert`; remove the superseded rewrite sequence.

## State the reusable theorem
Weak observation: `Demo.sum_nat` might be generalizable.
Maintainer request:
- claim: `Demo.sum_nat` unnecessarily fixes coefficients to `Nat`, although the proof uses only an
  additive commutative monoid.
- requested_change: Generalize `Demo.sum_nat` to `[AddCommMonoid R]` and retain the `Nat` statement
  as a specialization only if it is used by callers.

## Exact structural rewrite
Weak observation: the `calc` block in `Demo.bound` is hard to read.
Maintainer request:
- claim: `Demo.bound` starts its `calc` block with a bare expression, hiding the relation being proved.
- requested_change: Put the complete goal relation before `:= calc`, then align each subsequent
  relation step under it without changing the proof.

The strong forms identify the exact declaration and present defect, then request one checkable end
state. Do not emit the weak forms."""


def render_precedent_block(precedents: Iterable[PromptPrecedent]) -> str:
    precedents = list(precedents)
    if not precedents:
        return ""
    blocks = [
        "# Temporally prior maintainer asks\n"
        "These line-review comments predate this review and come from other PRs. They illustrate "
        "maintainer idioms and request forms, but they are not evidence that the current target has "
        "the same problem. Transfer an ask only when the current code independently supports the "
        "exact claim and requested transformation."
    ]
    grouped = {}
    for item in precedents:
        grouped.setdefault(item.source_event_id, []).append(item)
    for items in grouped.values():
        item = items[0]
        target_ids = ", ".join(f"`{value.primary_change_id}`" for value in items)
        matched_terms = sorted({term for value in items for term in value.matched_terms})
        body = "\n".join(f"> {line}" if line else ">" for line in item.body.splitlines())
        blocks.append(
            f"## Prior ask retrieved for {target_ids}\n"
            f"Source: PR #{item.source_pr_number}, before the current review cutoff\n"
            f"Problem-shape overlap: {', '.join(matched_terms)}\n"
            f"### Historical reviewed context ({item.context_path})\n"
            f"```diff\n{item.context}\n```\n"
            f"### Historical maintainer ask\n{body}"
        )
    return "\n\n".join(blocks)


def _index(items: Iterable, attr: str) -> Dict[str, object]:
    return {getattr(item, attr): item for item in items}


def generalist_features(renderer_version: str) -> Dict[str, bool]:
    """Which prompt changes a generalist renderer version selects, one flag each.

    They arrived together at `candidate-prompt/13` and should not have. On
    `pr5_A_lead_heldout12_rel040_rep1` the generalist's candidates per job fell from 1.24 and
    1.30 across the two 0.3.0 repetitions to 0.71 -- a 45% drop in the arm that produces most of
    this system's matched output -- while the focused arms, which none of these three changes
    touched, held at 0.14/0.20 -> 0.21. Three simultaneous prompt changes and one moved number
    says nothing about which.

    `/14` therefore keeps the two with measurement behind them and restores the contract, which
    had the least. It was dropped on the argument that the focused arms do not carry it and
    review normally -- but the arms emit 0.2 candidates per job against the generalist's 1.3, so
    they were never the reference class for an instruction whose job is to make the model speak.

    Each flag is separate so a later version can move exactly one and be read.
    """

    number = renderer_number(renderer_version)
    return {
        #: Each target's diff is its own change, not the `@@` hunk it happens to sit in.
        "scoped_diffs": number >= 13,
        #: The checklist once below the targets instead of under every one.
        "checklist_once": number >= 13,
        #: The contract repeated in the user message, where the model may weight it more than
        #: the identical system prompt. Dropped at /13, restored at /14, and the difference
        #: between those two releases is the measurement of whether it was load-bearing.
        "contract_in_user_message": number < 13 or number >= 14,
        #: Join a declaration's parts the way the file has them. False only for /13, whose
        #: release was built from a join that fabricated a blank line.
        "preserve_adjacency": number >= 14,
    }


def render_work_unit(
    unit: ReviewWorkUnit, episode: ReviewEpisodeInput, graph: ChangeGraph,
    precedents: Iterable[PromptPrecedent] = (),
) -> RenderedPrompt:
    targets = _index(graph.targets, "change_id")
    unit_targets = [targets[change_id] for change_id in unit.change_ids]
    features = generalist_features(unit.renderer_version)
    if features["scoped_diffs"]:
        blocks = target_blocks(
            unit_targets, scoped=True,
            preserve_adjacency=features["preserve_adjacency"])
    else:
        blocks = [target_block(target) for target in unit_targets]
    if features["checklist_once"]:
        blocks = blocks + [FACET_CHECKLIST_ONCE]
    else:
        blocks = [f"{block}\n{FACET_CHECKLIST}" for block in blocks]
    treatment = ""
    if unit.renderer_version == "candidate-prompt/9":
        treatment = f"{GENERIC_MAINTAINER_EXEMPLARS}\n\n"
    elif unit.renderer_version == "candidate-prompt/10":
        rendered_precedents = render_precedent_block(precedents)
        treatment = f"{rendered_precedents}\n\n" if rendered_precedents else ""
    # The contract is the system prompt. Sending it again under `# Review contract` in the user
    # message put the identical 2,482 characters in front of the model twice on every call —
    # 203 of 203 generalist prompts in `pr5_A_lead_heldout12_fp3_rep1`, 503,846 characters,
    # 12.5% of that run's generalist user text — and the copy is the expensive one: user text is
    # billed at roughly 4.7x a token inside the cached prefix. The focused arms never carried it
    # (0 of 1,206 in the same run) and review normally, which is the evidence that it is
    # redundant rather than load-bearing.
    contract = (
        f"# Review contract\n{system_prompt_for(unit.renderer_version)}\n\n"
        if features["contract_in_user_message"] else "")
    user = (
        f"{contract}"
        f"{treatment}"
        f"# PR #{episode.pr_number}: {episode.title.text or ''}\n"
        f"Round: {episode.round_index}\nDescription: {episode.description.text or '(unavailable)'}\n"
        f"Changed files: {', '.join(episode.changed_files)}\n\n" + "\n\n".join(blocks)
    )
    system = system_prompt_for(unit.renderer_version)
    system_hash = sha256_bytes(system.encode())
    user_hash = sha256_bytes(user.encode())
    prompt_hash = sha256_bytes(canonical_json_bytes({"system": system, "user": user}))
    return RenderedPrompt(
        work_unit_id=unit.work_unit_id, renderer_version=unit.renderer_version,
        system_prompt=system, user_prompt=user, system_sha256=system_hash,
        user_sha256=user_hash, prompt_sha256=prompt_hash,
        rendered_chars=len(SYSTEM_PROMPT) + len(user),
        estimated_tokens=(len(system.encode()) + len(user.encode()) + 3) // 4,
        included_change_ids=list(unit.change_ids), omitted_change_ids=[],
    )


def render_all(units, episodes, graphs, precedents=()) -> List[RenderedPrompt]:
    episode_by_id = _index(episodes, "episode_id")
    graph_by_id = _index(graphs, "graph_id")
    precedents_by_unit: Dict[str, List[PromptPrecedent]] = {}
    for precedent in precedents:
        precedents_by_unit.setdefault(precedent.work_unit_id, []).append(precedent)
    return [render_work_unit(
                unit, episode_by_id[unit.episode_id], graph_by_id[unit.graph_id],
                precedents_by_unit.get(unit.work_unit_id, []),
            )
            for unit in units]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-units", type=Path, required=True)
    parser.add_argument("--episodes", type=Path, required=True)
    parser.add_argument("--graphs", type=Path, required=True)
    parser.add_argument("--precedents", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    units = [ReviewWorkUnit.model_validate_json(x) for x in args.work_units.read_text().splitlines() if x]
    episodes = [ReviewEpisodeInput.model_validate_json(x) for x in args.episodes.read_text().splitlines() if x]
    graphs = [ChangeGraph.model_validate_json(x) for x in args.graphs.read_text().splitlines() if x]
    precedents = ([PromptPrecedent.model_validate_json(x) for x in
                   args.precedents.read_text().splitlines() if x] if args.precedents else [])
    prompts = render_all(units, episodes, graphs, precedents)
    write_once(args.out, jsonl_bytes(prompts))
    print(json.dumps({"prompts": len(prompts), "max_estimated_tokens": max(p.estimated_tokens for p in prompts)}, indent=2))


if __name__ == "__main__":
    main()
