"""Group a PR's changes into the units maintainers actually review.

Every arm we have reviews one declaration at a time, and that is measurably the wrong grain
for a large share of what maintainers ask for. On heldout11, nine of twenty reachable
obligations were *discovered* — a candidate landed on the right declaration — and still
missed, because the ask was about something larger than the declaration:

* **33145** wanted both `Dense.continuous_upperBounds` and `Dense.continuous_lowerBounds`
  renamed and the lower one reproved through `OrderDual`. That is one decision about a
  **family**, and a per-declaration arm can only ever produce half of it.
* **33294** wanted `Ordinal.IsNormal` deprecated for `Order.IsNormal` consistently across
  origin and call sites. That is a **migration**.
* **33362** wanted declarations moved inside `namespace Complex`. That is a property of the
  **file**, owned by no declaration in it.

A component is a set of change targets plus the reason they belong together. It is a lens
over the existing change graph, not a new decomposition of the PR: every component's
`change_ids` are change ids the graph already contains, so nothing here can invent a review
target that the sealed agenda does not know about.

Built from relations `pr_relations.build_relations` already computes and v5 has so far only
used for census weighting — `name_family`, `changed_siblings`, `declaration_dependency`,
`direct_use_of_changed_declaration`. No new graph analysis, and no second parser.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from src.mathlib_review.io import canonical_json_bytes, sha256_bytes
from src.mathlib_review.schema import ChangeGraph, PRRelation, ReviewEpisodeInput

#: Grains, coarsest last. A target usually belongs to several: a declaration is its own
#: `site`, may sit in a `family`, and always sits in a `file`.
GRAINS = ("site", "family", "file", "migration", "pr_intent")

#: Relations that make two declarations part of one design decision. Deliberately not
#: `declaration_dependency` — A using B in its statement makes B *important* (see
#: `centrality`), not part of the same family. Conflating them merged whole files into one
#: component on PRs where everything imports one core lemma.
_FAMILY_RELATIONS = ("name_family", "changed_siblings")

#: What a PR says it is doing, and the grain that ask implies. Shares its vocabulary with
#: `census._INTENT_KEYWORDS` on purpose: a PR that reads as a rename should rank its naming
#: work up *and* get a migration component, and those must not disagree about the words.
_INTENT_GRAIN = {
    "golf": ("pr_intent", ("proof_golf", "proof_idiom")),
    "simplif": ("pr_intent", ("proof_golf", "proof_idiom")),
    "rename": ("migration", ("naming",)),
    "deprecat": ("migration", ("naming", "api_reuse")),
    "migrat": ("migration", ("naming", "api_reuse")),
    "generalis": ("pr_intent", ("generality",)),
    "generaliz": ("pr_intent", ("generality",)),
    "dedup": ("pr_intent", ("duplication", "api_reuse")),
}


@dataclass(frozen=True)
class ReviewComponent:
    """One coherent thing to review, and why it is one thing."""

    component_id: str
    grain: str
    pr_number: int
    episode_id: str
    change_ids: Tuple[str, ...]
    subjects: Tuple[str, ...]
    #: Human-readable, and read by the lead. The grain alone does not say why *these*
    #: declarations; the reason does.
    reason: str
    #: Arms whose concern this grain implies. Advisory: importance decides how hard to look,
    #: this decides what looking would even mean.
    suggested_arms: Tuple[str, ...] = ()
    paths: Tuple[str, ...] = ()
    #: `exact` when the change graph relates these directly, `hypothesis` when they merely
    #: look related. A reviewer told "these are one API" acts on it; a reviewer told "these
    #: may be one API, check first" does not build on a premise nobody established.
    evidence: str = "exact"

    def render(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "grain": self.grain,
            "subjects": list(self.subjects),
            "change_ids": list(self.change_ids),
            "why": self.reason,
            "evidence": self.evidence,
            "suggested_arms": list(self.suggested_arms),
        }


def _seal(payload: Dict[str, Any]) -> str:
    return "component:" + sha256_bytes(canonical_json_bytes(payload))[:24]


def _component(grain: str, graph: ChangeGraph, change_ids: Sequence[str],
               subjects: Sequence[str], reason: str,
               suggested_arms: Sequence[str] = (), paths: Sequence[str] = (),
               evidence: str = "exact") -> ReviewComponent:
    ordered = tuple(sorted(set(change_ids)))
    payload = {"grain": grain, "episode_id": graph.episode_id, "change_ids": list(ordered)}
    return ReviewComponent(
        component_id=_seal(payload), grain=grain, pr_number=graph.pr_number,
        episode_id=graph.episode_id, change_ids=ordered,
        subjects=tuple(sorted(set(s for s in subjects if s))),
        reason=reason, suggested_arms=tuple(suggested_arms), paths=tuple(sorted(set(paths))),
        evidence=evidence,
    )


def _stem(name: str) -> Optional[Tuple[str, str]]:
    """`(namespace, leading name token)`, the coarse "same API" key.

    Deliberately looser than `pr_relations._name_tokens`, which requires a 7-character token
    and ignores a stop-list including `continuous`. That tuning is right for v4's precision-
    weighted census signal and wrong here: measured on PR 33145, every one of
    `Dense.continuous_{sup,sup',inf,inf',upperBounds,lowerBounds}` yielded *zero* tokens —
    `upper` and `Bounds` fall under the length floor and `continuous` is on the stop-list —
    so the six declarations the maintainer treated as one API looked unrelated. The gold
    there is two asks about that family and we produced neither.

    A shared leading token under a shared namespace is a weaker claim than v4's, and that is
    appropriate: this decides what to *look at together*, not what to assert.
    """

    if "." not in name:
        return None
    namespace, short = name.rsplit(".", 1)
    head = short.rstrip("'").split("_", 1)[0]
    return (namespace, head.lower()) if namespace and head else None


def _families(graph: ChangeGraph, relations: Sequence[PRRelation]
              ) -> List[Tuple[Set[str], str, str]]:
    """Groups of declarations that may be one design decision, each with its evidence.

    Returns `(members, evidence, reason)`. Two groupings are computed **separately and never
    unioned**, because merging them transitively is what produced the false families:

    * **exact** — `name_family` and `changed_siblings` from `pr_relations`, which are derived
      from shared name tokens under a shared namespace, or adjacency in the parser's change
      graph. These may be asserted.
    * **hypothesis** — shared namespace and leading name token (`_stem`). This is what makes
      `Dense.continuous_{sup,inf,upperBounds,lowerBounds,…}` one API when v4's stricter
      tokeniser yields nothing for any of them, and it is weaker evidence, so it is labelled
      as a suspicion rather than stated as a fact.

    Merging the two through one union-find made PR 33294 report a fourteen-member "family"
    spanning `Ordinal.add_*` and `Ordinal.deriv_*`: stem joined A to B, `changed_siblings`
    joined B to C, a stem joined C to D, and the transitive closure swallowed unrelated APIs.
    A component asserted on that premise hands a reviewer a claim about code that has nothing
    in common, which is worse than handing it nothing.

    Singletons are dropped: a family of one is a site.
    """

    changed = {target.change_id for target in graph.targets}

    def close(edges: Dict[str, Set[str]]) -> List[Set[str]]:
        parent: Dict[str, str] = {}

        def find(item: str) -> str:
            parent.setdefault(item, item)
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[min(ra, rb)] = parent[max(ra, rb)] = min(ra, rb)

        for source, targets in edges.items():
            for target in targets:
                union(source, target)
        groups: Dict[str, Set[str]] = {}
        for item in parent:
            groups.setdefault(find(item), set()).add(item)
        return [members for members in groups.values() if len(members) > 1]

    exact: Dict[str, Set[str]] = {}
    for relation in relations:
        if (relation.episode_id != graph.episode_id
                or relation.relation_kind not in _FAMILY_RELATIONS):
            continue
        for related in relation.related_change_ids:
            if relation.source_change_id in changed and related in changed:
                exact.setdefault(relation.source_change_id, set()).add(related)

    by_stem: Dict[Tuple[str, str], List[str]] = {}
    for target in graph.targets:
        if target.kind != "declaration":
            continue
        stem = _stem(target.declaration_name or "")
        if stem is not None:
            by_stem.setdefault(stem, []).append(target.change_id)
    stems: Dict[str, Set[str]] = {}
    for members in by_stem.values():
        for other in members[1:]:
            stems.setdefault(members[0], set()).add(other)

    out: List[Tuple[Set[str], str, str]] = []
    for members in close(exact):
        out.append((
            members, "exact",
            f"{len(members)} declarations the change graph relates directly — a shared name "
            "family, or adjacency as changed siblings",
        ))
    seen = {frozenset(m) for m, _e, _r in out}
    for members in close(stems):
        if frozenset(members) in seen:
            continue
        out.append((
            members, "hypothesis",
            f"{len(members)} declarations share a namespace and leading name token, so they "
            "MAY be one API — a rename, a dualisation or a missing counterpart would be one "
            "decision about all of them. This is a suspicion from their names, not an "
            "established relation: check the statements before relying on it",
        ))
    return out


def centrality(graph: ChangeGraph, relations: Sequence[PRRelation]) -> Dict[str, int]:
    """How many other changed declarations lean on each one, within this PR.

    In-degree over `declaration_dependency` and `direct_use_of_changed_declaration`: if the
    rest of the diff references it, it is what the PR is *about*, and reviewing it badly
    costs more than reviewing a leaf badly. This is the PR-local half of importance; the
    library-wide half is `exposure.py`.
    """

    incoming: Dict[str, int] = {target.change_id: 0 for target in graph.targets}
    for relation in relations:
        if relation.episode_id != graph.episode_id:
            continue
        if relation.relation_kind not in (
                "declaration_dependency", "direct_use_of_changed_declaration"):
            continue
        for related in relation.related_change_ids:
            if related in incoming:
                incoming[related] += 1
    return incoming


def _intent(episode: Optional[ReviewEpisodeInput]) -> List[Tuple[str, str, Tuple[str, ...]]]:
    """(keyword, grain, arms) for every intent the PR states about itself."""

    if episode is None:
        return []
    text = " ".join([
        getattr(getattr(episode, "title", None), "text", "") or "",
        getattr(getattr(episode, "description", None), "text", "") or "",
    ]).lower()
    seen: Set[Tuple[str, Tuple[str, ...]]] = set()
    out = []
    for keyword, (grain, arms) in _INTENT_GRAIN.items():
        if keyword in text and (grain, arms) not in seen:
            seen.add((grain, arms))
            out.append((keyword, grain, arms))
    return out


def build_components(
    graphs: Iterable[ChangeGraph],
    relations: Sequence[PRRelation],
    episodes: Iterable[ReviewEpisodeInput] = (),
) -> List[ReviewComponent]:
    """Every reviewable component of every PR, ordered deterministically.

    A change target appears in several components. That is the point: the same declaration
    is a site, a member of a family, and part of a file, and which lens matters depends on
    what the maintainer was going to ask for.
    """

    episode_by_id = {item.episode_id: item for item in episodes}
    components: List[ReviewComponent] = []

    for graph in sorted(graphs, key=lambda item: (item.pr_number, item.episode_id)):
        declarations = [t for t in graph.targets if t.kind == "declaration"]
        subject_of = {t.change_id: (t.declaration_name or "") for t in graph.targets}
        path_of = {t.change_id: t.path for t in graph.targets}

        # --- site: one changed target, the grain every arm already speaks ---------------
        #
        # Every target kind, not only `declaration`. PR 33305 is seven `module_doc` changes
        # and no declarations at all, so a declaration-only rule gave that PR *zero*
        # components — and its gold ask (wrap an over-long doc line) is site-local and
        # perfectly reviewable. A change with no declaration name is still a change.
        for target in sorted(graph.targets, key=lambda t: t.change_id):
            components.append(_component(
                "site", graph, [target.change_id], [subject_of.get(target.change_id, "")],
                f"a single changed {target.kind.replace('_', ' ')}", paths=[target.path],
                suggested_arms=("docs", "style") if target.kind == "module_doc" else (),
            ))

        # --- family: declarations that are one design decision --------------------------
        for members, evidence, reason in sorted(
                _families(graph, relations), key=lambda item: sorted(item[0])[0]):
            names = [subject_of.get(cid, "") for cid in members]
            components.append(_component(
                "family", graph, sorted(members), names, reason,
                suggested_arms=("naming", "generality", "duplication"),
                paths=[path_of.get(cid, "") for cid in members],
                evidence=evidence,
            ))

        # --- file: placement, namespacing, module docs ----------------------------------
        by_path: Dict[str, List[str]] = {}
        for target in graph.targets:
            by_path.setdefault(target.path, []).append(target.change_id)
        for path, change_ids in sorted(by_path.items()):
            if len(change_ids) < 2:
                continue
            components.append(_component(
                "file", graph, change_ids, [subject_of.get(c, "") for c in change_ids],
                f"{len(change_ids)} changes in {path}; namespace placement, section "
                "structure and the module docstring are properties of the file that no "
                "single declaration in it owns",
                suggested_arms=("style", "docs"), paths=[path],
            ))

        # --- what the PR says it is doing ------------------------------------------------
        stated = _intent(episode_by_id.get(graph.episode_id))
        for keyword, grain, arms in stated:
            change_ids = [t.change_id for t in graph.targets]
            if not change_ids:
                continue
            components.append(_component(
                grain, graph, change_ids, [subject_of.get(c, "") for c in change_ids],
                f"the PR describes itself as {keyword!r}, so every changed declaration is "
                f"in scope for {', '.join(arms)} whether or not any single site looks "
                "remarkable on its own",
                suggested_arms=arms, paths=sorted({path_of.get(c, "") for c in change_ids}),
            ))

    components.sort(key=lambda c: (c.pr_number, GRAINS.index(c.grain), c.component_id))

    # Two *structural* grains covering exactly the same changes are one review unit wearing
    # two labels — a file whose every change is one family, say. Keep the finer one and drop
    # the duplicate rather than routing the same work twice.
    #
    # `migration` and `pr_intent` are exempt. They routinely span the whole PR and so collide
    # with `file` on single-file PRs, but they are not restatements of it: they carry what the
    # PR says it is *doing* and route different arms for it. Deduping them away silently
    # deleted the golf routing on PR 33285, which is the case the intent grain exists for.
    structural = {"site", "family", "file"}
    seen: Set[Tuple[int, Tuple[str, ...]]] = set()
    deduped: List[ReviewComponent] = []
    for component in components:
        key = (component.pr_number, component.change_ids)
        if component.grain in structural:
            if component.grain != "site" and key in seen:
                continue
            seen.add(key)
        deduped.append(component)
    return deduped


def components_report(components: Sequence[ReviewComponent]) -> Dict[str, Any]:
    """What the decomposition found, before anything is routed against it."""

    by_grain: Dict[str, int] = {}
    by_pr: Dict[int, Dict[str, int]] = {}
    for component in components:
        by_grain[component.grain] = by_grain.get(component.grain, 0) + 1
        by_pr.setdefault(component.pr_number, {}).setdefault(component.grain, 0)
        by_pr[component.pr_number][component.grain] += 1
    return {
        "components": len(components),
        "by_grain": dict(sorted(by_grain.items())),
        "by_pr": {pr: dict(sorted(g.items())) for pr, g in sorted(by_pr.items())},
        # A PR with only `site` components is one this decomposition did nothing for, and
        # says so rather than looking like coverage.
        "site_only_prs": sorted(
            pr for pr, grains in by_pr.items() if set(grains) == {"site"}),
    }
