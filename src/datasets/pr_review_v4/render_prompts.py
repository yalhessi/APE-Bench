"""Single production renderer for both prompt previews and task execution."""

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

from .io import canonical_json_bytes, jsonl_bytes, sha256_bytes, write_once
from .schema import ChangeGraph, PromptPrecedent, RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit


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


def render_work_unit(
    unit: ReviewWorkUnit, episode: ReviewEpisodeInput, graph: ChangeGraph,
    precedents: Iterable[PromptPrecedent] = (),
) -> RenderedPrompt:
    targets = _index(graph.targets, "change_id")
    blocks = []
    for change_id in unit.change_ids:
        target = targets[change_id]
        base = target.base_code if target.base_code is not None else "(not present)"
        reviewed = target.reviewed_code if target.reviewed_code is not None else "(not present)"
        blocks.append(
            f"## Review target\nChange ID (copy exactly): `{change_id}`\n"
            f"Path: {target.path}\nKind: {target.kind}\n"
            f"Primary subject (copy exactly): `{target.declaration_name or target.path}`\n"
            f"Primary entity IDs (copy one, or null if none): "
            f"{', '.join(target.reviewed_entity_ids + target.base_entity_ids) or '(none)'}\n"
            f"### Complete base region\n```lean\n{base}\n```\n"
            f"### Complete reviewed region\n```lean\n{reviewed}\n```\n"
            f"### Exact changed fragments\n```diff\n{''.join(target.diff_fragments)}\n```"
            f"\n{FACET_CHECKLIST}"
        )
    treatment = ""
    if unit.renderer_version == "candidate-prompt/9":
        treatment = f"{GENERIC_MAINTAINER_EXEMPLARS}\n\n"
    elif unit.renderer_version == "candidate-prompt/10":
        rendered_precedents = render_precedent_block(precedents)
        treatment = f"{rendered_precedents}\n\n" if rendered_precedents else ""
    user = (
        "# Review contract\n"
        f"{system_prompt_for(unit.renderer_version)}\n\n"
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
