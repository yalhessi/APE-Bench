"""One map per PR, and a small slice of it per job.

Measured on heldout11: 10 of 19 audited obligations cannot be concluded from the changed
declaration alone — 6 need the sibling family, 3 need a convention stated nowhere in the code,
1 needs the file's structure. Meanwhile an arm sees only its own targets plus the PR title
and description, and the 161 mandatory floor jobs are *injected* rather than requested, so
they receive no brief at all. The context those obligations need is not thin; for most of the
run it is absent.

**Slices, not a broadcast.** Handing every job the whole map would pay its token cost 161
times and dilute site reviews that need none of it. The map is built once; each job is given
only the part that bears on its own targets.

**Evidence is labelled, never flattened.** A component grouped by an exact relation is stated
as fact; one grouped by a shared name stem is stated as a suspicion to check. That
distinction is load-bearing — merging the two groupings once produced a fourteen-member
"family" spanning `Ordinal.add_*` and `Ordinal.deriv_*`, and a reviewer told those are one
API has been handed a premise about unrelated code.

**Nothing here is a finding.** The map states structure and asks questions. Admission remains
a property of evidence, and importance governs allocation only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .components import ReviewComponent

#: Target kinds that describe a file's shape rather than its contents. Their order and line
#: positions are the whole answer to a placement question — PR 33362 asks to move
#: declarations inside `namespace Complex`, which is visible only as the ordering of a
#: `namespace` marker against the declarations around it.
STRUCTURE_KINDS = ("module_doc", "namespace", "section", "command", "import")

#: How many structural entries a skeleton may carry before it is truncated. A skeleton is
#: orientation, not the file.
MAX_SKELETON_ROWS = 40


@dataclass(frozen=True)
class FileSkeleton:
    """Where the structural markers sit in one changed file, in line order."""

    path: str
    rows: Tuple[Tuple[int, str, str], ...]      # (line, kind, name)
    truncated: bool = False

    def render(self) -> str:
        lines = [f"### Structure of `{self.path}`"]
        for line, kind, name in self.rows:
            label = f" `{name}`" if name else ""
            lines.append(f"  line {line}: {kind}{label}")
        if self.truncated:
            lines.append("  … (truncated)")
        return "\n".join(lines)


@dataclass(frozen=True)
class ConventionQuestion:
    """A naming or structural norm the PR's own shape raises, and where to settle it.

    Deliberately a *question with a corpus to search*, not an answer. Measured: the code
    corpus argues against the maintainer on both naming conventions in this set —
    `toLinearMap_` appears 50 times against `coe_`'s 4,707, dot notation 2,359 against
    22,345 — because these are conventions Mathlib is moving toward, and frequency measures
    where it has been. The same norms are stated plainly in review: 224 comments discuss dot
    notation, and one says "we want to move away from primed names". So the retrieval target
    is the review corpus, and repository frequency is at most supporting evidence.
    """

    kind: str
    question: str
    query: str

    def render(self) -> str:
        return f"  - {self.question}\n    (search maintainer review comments for: {self.query!r})"


@dataclass(frozen=True)
class ContextSlice:
    """Everything one job is told beyond its own targets — and nothing more."""

    invocation_id: str
    families: Tuple[ReviewComponent, ...] = ()
    skeletons: Tuple[FileSkeleton, ...] = ()
    conventions: Tuple[ConventionQuestion, ...] = ()
    exposure: Tuple[Tuple[str, int], ...] = ()

    @property
    def empty(self) -> bool:
        return not (self.families or self.skeletons or self.conventions or self.exposure)

    def render(self) -> str:
        """The text an arm sees. Framed as context and questions, never as findings."""

        if self.empty:
            return ""
        out = [
            "\n\n---\n## What else is in this PR",
            "Context, not findings. None of this has been verified and none of it is a claim "
            "you should repeat — it is here so you are not reviewing one declaration as "
            "though the rest of the change did not exist. Establish anything you report.\n",
        ]
        for family in self.families:
            verb = "are" if family.evidence == "exact" else "may be"
            out.append(
                f"**Related declarations** ({family.evidence}): these {verb} one group — "
                + ", ".join(f"`{s}`" for s in family.subjects[:8])
                + (" …" if len(family.subjects) > 8 else "")
            )
            # The reason already carries the caveat for a hypothesis; repeating it here
            # made every such block say "check the statements" twice.
            out.append(f"  {family.reason}")
        for skeleton in self.skeletons:
            out.append(skeleton.render())
        if self.conventions:
            out.append("**Conventions this change touches** — settle these against review "
                       "history, not against how common a spelling is today:")
            out.extend(item.render() for item in self.conventions)
        if self.exposure:
            out.append("**Referenced elsewhere in the library** (how much depends on this):")
            out.extend(f"  - `{name}`: {reach} modules" for name, reach in self.exposure)
        return "\n".join(out)


def file_skeletons(graph: Any, paths: Optional[Set[str]] = None) -> List[FileSkeleton]:
    """Structural markers per changed file, in line order, from the change graph alone.

    No file is read: the graph already records `module_doc`, `namespace`, `section` and
    `command` targets with entity spans, which is exactly the ordering a placement question
    turns on.
    """

    entities = {item.entity_id: item for item in getattr(graph, "entities", [])}

    def first_line(target: Any) -> Optional[int]:
        spans = [entities[e].span.line_start
                 for e in (list(getattr(target, "reviewed_entity_ids", []))
                           + list(getattr(target, "base_entity_ids", [])))
                 if e in entities]
        return min(spans) if spans else None

    by_path: Dict[str, List[Tuple[int, str, str]]] = {}
    for target in getattr(graph, "targets", []):
        if paths is not None and target.path not in paths:
            continue
        line = first_line(target)
        if line is None:
            continue
        # Declarations are included so a marker's position is readable *relative to them*;
        # a namespace line means nothing without knowing what sits after it.
        if target.kind not in STRUCTURE_KINDS and target.kind != "declaration":
            continue
        by_path.setdefault(target.path, []).append(
            (line, target.kind, target.declaration_name or ""))

    out = []
    for path, rows in sorted(by_path.items()):
        # Deduplicated: a target can contribute the same (line, kind, name) through both its
        # base and reviewed entities, and a skeleton that lists `module_doc` twice at line 11
        # reads as though the file had two of them.
        ordered = sorted(set(rows))
        # A file with no structural marker at all answers no placement question, and listing
        # its declarations alone is the diff again.
        if not any(kind in STRUCTURE_KINDS for _line, kind, _name in ordered):
            continue
        out.append(FileSkeleton(
            path=path, rows=tuple(ordered[:MAX_SKELETON_ROWS]),
            truncated=len(ordered) > MAX_SKELETON_ROWS))
    return out


def convention_questions(components: Sequence[ReviewComponent],
                         subjects: Iterable[str]) -> List[ConventionQuestion]:
    """Norms this PR's shape raises, phrased as questions with a corpus to search.

    Derived from the change's own shape — a stated rename, a primed name being introduced, a
    coercion in a name — never from any answer key.
    """

    names = [s for s in subjects if s]
    questions: List[ConventionQuestion] = []
    grains = {c.grain for c in components}

    if "migration" in grains:
        questions.append(ConventionQuestion(
            kind="rename_form",
            question=("This PR renames or deprecates. Does the repository spell this family "
                      "of names with dot notation (`Foo.of_bar`) or flat (`foo_of_bar`), and "
                      "has that preference changed recently?"),
            query="dot notation naming convention rename"))
    if any(name.rstrip("'") != name for name in names):
        questions.append(ConventionQuestion(
            kind="primed_name",
            question=("A primed name is being added or kept. Is a primed variant acceptable "
                      "here, or is a descriptive suffix expected instead?"),
            query="primed name convention rename descriptive"))
    if any("coe" in name.rsplit(".", 1)[-1].lower() for name in names):
        questions.append(ConventionQuestion(
            kind="coercion_name",
            question=("A name mentions a coercion. What does the repository call lemmas about "
                      "this coercion — `coe_…`, or the name of the map it produces?"),
            query="coe naming convention coercion lemma name"))
    return questions


def build_slices(
    *,
    components_by_pr: Dict[int, Sequence[ReviewComponent]],
    graphs_by_episode: Dict[str, Any],
    jobs: Sequence[Tuple[str, int, str, Sequence[str]]],
    subjects_by_change: Dict[str, str],
    paths_by_change: Dict[str, str],
    exposure_by_change: Optional[Dict[str, int]] = None,
) -> Dict[str, ContextSlice]:
    """One slice per job, containing only what bears on that job's own targets.

    `jobs` is `(invocation_id, pr_number, episode_id, change_ids)`.
    """

    exposure_by_change = exposure_by_change or {}
    slices: Dict[str, ContextSlice] = {}
    for invocation_id, pr_number, episode_id, change_ids in jobs:
        mine = set(change_ids)
        components = components_by_pr.get(pr_number, [])
        families = tuple(
            c for c in components
            if c.grain == "family" and mine & set(c.change_ids) and set(c.change_ids) - mine
        )
        graph = graphs_by_episode.get(episode_id)
        paths = {paths_by_change.get(c, "") for c in mine}
        paths = {p for p in paths if p}
        skeletons = tuple(file_skeletons(graph, paths or None)) if graph is not None else ()
        names = [subjects_by_change.get(c, "") for c in mine]
        conventions = tuple(convention_questions(
            [c for c in components if mine & set(c.change_ids)], names))
        exposure = tuple(sorted(
            ((subjects_by_change.get(c, c), exposure_by_change[c])
             for c in mine if c in exposure_by_change),
            key=lambda item: -item[1]))
        slices[invocation_id] = ContextSlice(
            invocation_id=invocation_id, families=families, skeletons=skeletons,
            conventions=conventions, exposure=exposure)
    return slices


def slices_report(slices: Dict[str, ContextSlice]) -> Dict[str, Any]:
    """How much context actually reached jobs, and how much of it was nothing.

    A slice that is empty for most jobs is the honest outcome for a PR whose changes are all
    independent — and it is also what a broken join looks like, so it is counted rather than
    assumed.
    """

    values = list(slices.values())
    return {
        "jobs": len(values),
        "with_context": sum(1 for s in values if not s.empty),
        "with_family": sum(1 for s in values if s.families),
        "with_skeleton": sum(1 for s in values if s.skeletons),
        "with_conventions": sum(1 for s in values if s.conventions),
        "with_exposure": sum(1 for s in values if s.exposure),
        "median_rendered_chars": sorted(len(s.render()) for s in values)[len(values) // 2]
        if values else 0,
    }


def with_context(prompt: Any, context_text: str) -> Any:
    """A copy of a rendered prompt with a context slice appended, re-hashed.

    The generalist floor's prompt comes from the release's pre-rendered production prompts,
    not from the focused renderer, so it is the one path a slice could not reach — and the
    floor is 95 of the 161 mandatory jobs and the source of every candidate that has landed
    on a gold obligation so far. Leaving it uncontextualised would have improved the arms
    that produce least and left the one that produces most exactly as it was.

    A new prompt is constructed rather than the release's mutated: release artifacts are
    inputs. The hashes are recomputed so the sealed plan records the text actually sent —
    a prompt whose `prompt_sha256` no longer matches its body is worse than no hash.
    """

    from src.datasets.pr_review_v4.io import canonical_json_bytes, sha256_bytes

    if not context_text:
        return prompt
    user = prompt.user_prompt + context_text
    system = prompt.system_prompt
    return prompt.model_copy(update={
        "user_prompt": user,
        "user_sha256": sha256_bytes(user.encode()),
        "prompt_sha256": sha256_bytes(
            canonical_json_bytes({"system": system, "user": user})),
        "rendered_chars": len(system) + len(user),
        "estimated_tokens": (len(system.encode()) + len(user.encode()) + 3) // 4,
    })
