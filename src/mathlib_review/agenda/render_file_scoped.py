"""Schedule and render the file-scoped generalist: one invocation per changed file.

Two generalist arms exist on purpose, and they answer different questions.

The **control** (`generalist`) reviews one work unit at a time — the same sites, the same
seven tools as the focused arm — and its job is the concern families no specialist covers
yet. Measured on medium gold those are `docs` (3 of 33 judgments) and `scope` (1). It is the
comparison that shows what specialisation buys.

This is the **component**. Its distinguishing input is every change the PR made to one file,
seen together. What that buys is measured, not assumed:

* **0 of 43** gold obligations cross a file boundary, so the file — not the PR — is the
  widest scope with anything to find. PR-level context would cost tokens for nothing.
* **8 of 43** span more than one work unit *within* a file, and all 8 live in the 12 files
  that have more than one work unit. Those are invisible whole to any per-site arm.
* **73 of 85** files hold exactly one work unit, where this view is identical to the control's
  — no regression, and no duplicated effort worth worrying about.

## What it must not do

Re-emit per-site findings. Cross-site *unification* is `digest`'s job now, solved once for
every arm; an arm that re-derived it privately would leave the cross-arm case unsolved and
flood the merge with duplicates. So the submission contract restricts this arm to claims that
actually need the file view:

* the claim spans **more than one change target**, or
* its `issue_kind` is `scope_placement`, which is inherently about a declaration's position
  relative to its neighbours — the one kind `verify_scope_placement` abstains on today
  precisely because "placement needs file-level adjacency, which hunk-level change targets do
  not record".

Everything else belongs to a specialist or to the control, and is rejected at submission
rather than left to prompt discipline.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from src.mathlib_review.io import canonical_json_bytes, sha256_bytes
from src.mathlib_review.agenda.render_prompts import system_prompt_for
from src.mathlib_review.schema import ChangeGraph, RenderedPrompt, ReviewEpisodeInput, ReviewWorkUnit

FILE_RENDERER_VERSION = "file-prompt/1"

#: Issue kinds a file-scoped claim may carry without spanning several targets.
SINGLE_TARGET_KINDS_ALLOWED = frozenset({"scope_placement"})

_FILE_INSTRUCTION = """

# This run: file-level coherence

You are reviewing **every change this PR made to one file, together**. Other reviewers see
these declarations one at a time; you are the only one who sees them as a set. Report only
what that view reveals:

- declarations that duplicate, overlap or should be derived from one another;
- a defect repeated across several of these declarations, reported once, naming every target
  it applies to in `change_ids`;
- ordering, sectioning and placement — a declaration in the wrong section, a `variable` or
  `open` in the wrong place, blank-line and section structure between declarations;
- changes that do not hang together: a new declaration nothing uses, an inconsistent naming
  or argument convention *across* these declarations, a missing counterpart.

Do **not** report what is visible from a single declaration alone — a proof that could be
shorter, one name that breaks a convention, one missing docstring. Other reviewers cover
those, and duplicating them here adds noise without adding information.

Every candidate must therefore either list more than one entry in `change_ids`, or use
`issue_kind: "scope_placement"`. A candidate that does neither is rejected."""


@dataclass(frozen=True)
class FileInvocation:
    """One scheduled file review: an episode, a path, and the targets changed in it."""

    invocation_id: str
    episode_id: str
    pr_number: int
    path: str
    change_ids: Tuple[str, ...]
    work_unit_ids: Tuple[str, ...]
    source_sha256: str


def schedule_files(
    graphs: Iterable[ChangeGraph],
    work_units: Iterable[ReviewWorkUnit],
    pr_numbers: Optional[Iterable[int]] = None,
) -> List[FileInvocation]:
    """One invocation per changed file, from the change graph alone.

    Gold-free by construction: the only inputs are the graph's targets and the work units
    they belong to. Nothing here consults what a maintainer said.
    """

    wanted = set(pr_numbers) if pr_numbers else None
    unit_by_change = {
        change_id: unit.work_unit_id
        for unit in work_units
        for change_id in unit.change_ids
    }
    grouped: Dict[Tuple[str, str], List] = defaultdict(list)
    meta: Dict[Tuple[str, str], Tuple[int]] = {}
    for graph in graphs:
        if wanted is not None and graph.pr_number not in wanted:
            continue
        for target in graph.targets:
            if not target.path.endswith(".lean"):
                continue
            key = (graph.episode_id, target.path)
            grouped[key].append(target)
            meta[key] = (graph.pr_number,)

    invocations = []
    for (episode_id, path), targets in sorted(grouped.items()):
        change_ids = tuple(sorted(item.change_id for item in targets))
        units = tuple(sorted({
            unit_by_change[cid] for cid in change_ids if cid in unit_by_change
        }))
        if not units:
            # A file whose targets belong to no scheduled work unit is out of scope: the
            # other arms will not review it either, and reviewing it here would make the
            # arms incomparable.
            continue
        identity = {
            "version": FILE_RENDERER_VERSION,
            "episode_id": episode_id,
            "path": path,
            "change_ids": list(change_ids),
        }
        digest = sha256_bytes(canonical_json_bytes(identity))
        invocations.append(FileInvocation(
            invocation_id=f"file:{digest[:24]}",
            episode_id=episode_id,
            pr_number=meta[(episode_id, path)][0],
            path=path,
            change_ids=change_ids,
            work_unit_ids=units,
            source_sha256=digest,
        ))
    return invocations


def _target_block(target) -> str:
    base = target.base_code if target.base_code is not None else "(not present)"
    reviewed = target.reviewed_code if target.reviewed_code is not None else "(not present)"
    return (
        f"## Change target\nChange ID (copy exactly): `{target.change_id}`\n"
        f"Kind: {target.kind}\n"
        f"Primary subject (copy exactly): `{target.declaration_name or target.path}`\n"
        f"Primary entity IDs (copy one, or null if none): "
        f"{', '.join(target.reviewed_entity_ids + target.base_entity_ids) or '(none)'}\n"
        f"### Base\n```lean\n{base}\n```\n"
        f"### Reviewed\n```lean\n{reviewed}\n```"
    )


def render_file_invocation(
    invocation: FileInvocation, episode: ReviewEpisodeInput, graph: ChangeGraph,
) -> RenderedPrompt:
    targets = {item.change_id: item for item in graph.targets}
    blocks = [_target_block(targets[cid]) for cid in invocation.change_ids]
    # The file's diff once, not once per target. Change targets replicate it — measured, all
    # 108 targets in one medium file carry the identical 17.3k-character blob — so
    # concatenating per target would ship 1.87M characters for a single file.
    fragments = []
    for cid in invocation.change_ids:
        blob = "".join(targets[cid].diff_fragments)
        if blob and blob not in fragments:
            fragments.append(blob)
    system = system_prompt_for("candidate-prompt/12") + _FILE_INSTRUCTION
    user = (
        f"# PR #{episode.pr_number}: {episode.title.text or ''}\n"
        f"Round: {episode.round_index}\n"
        f"Description: {episode.description.text or '(unavailable)'}\n\n"
        f"# File under review: {invocation.path}\n"
        f"{len(blocks)} change targets in this file.\n\n"
        + "\n\n".join(blocks)
        + "\n\n## Diff for this file\n```diff\n" + "\n".join(fragments) + "\n```"
    )
    return RenderedPrompt(
        work_unit_id=invocation.work_unit_ids[0],
        invocation_id=invocation.invocation_id,
        spec_id="file_coherence",
        renderer_version=FILE_RENDERER_VERSION,
        system_prompt=system, user_prompt=user,
        system_sha256=sha256_bytes(system.encode()),
        user_sha256=sha256_bytes(user.encode()),
        prompt_sha256=sha256_bytes(canonical_json_bytes({"system": system, "user": user})),
        rendered_chars=len(system) + len(user),
        estimated_tokens=(len(system.encode()) + len(user.encode()) + 3) // 4,
        included_change_ids=list(invocation.change_ids),
        omitted_change_ids=[],
        submission_verification_policy="none",
    )


def render_file_all(
    invocations: Iterable[FileInvocation],
    episodes: Iterable[ReviewEpisodeInput],
    graphs: Iterable[ChangeGraph],
) -> List[RenderedPrompt]:
    episode_by_id = {item.episode_id: item for item in episodes}
    graph_by_episode = {item.episode_id: item for item in graphs}
    return [
        render_file_invocation(
            item, episode_by_id[item.episode_id], graph_by_episode[item.episode_id]
        )
        for item in invocations
    ]


def file_claim_error(change_ids: Sequence[str], issue_kind: Optional[str]) -> Optional[str]:
    """Why a file-scoped candidate is not a file-scoped claim, if it is not one."""

    if len(set(change_ids)) > 1:
        return None
    if issue_kind in SINGLE_TARGET_KINDS_ALLOWED:
        return None
    return (
        "a file-scoped finding must span more than one change target, or be a "
        "scope_placement claim. Anything visible from one declaration alone belongs to "
        "another reviewer and would only duplicate its output."
    )


def schedule_report(invocations: Sequence[FileInvocation]) -> Dict:
    by_size = defaultdict(int)
    for item in invocations:
        by_size[len(item.change_ids)] += 1
    return {
        "renderer_version": FILE_RENDERER_VERSION,
        "invocations": len(invocations),
        "pr_numbers": sorted({item.pr_number for item in invocations}),
        "files_with_one_target": by_size.get(1, 0),
        "files_with_several_targets": sum(
            count for size, count in by_size.items() if size > 1
        ),
        "largest_file_targets": max((len(item.change_ids) for item in invocations), default=0),
    }
