"""Producers: facts about a PR, computed before any reviewer reads it.

`docs/research/codebase-redesign-2026-10.md` §4.4. The record's lesson on how knowledge reaches a
reviewer is settled: rules in the prompt moved nothing twice (guideline injection, precedent
priming), while facts *about the PR* did (the counted rename, the long line the compile
reported). A producer states such facts -- deterministically, from the PR's own change graph -- and
they reach the reviewer as a section of its packet, the per-PR `context_file` channel the solo
task already reads (`solo.py::solo_context_block`). The plan this serves is
`docs/plans/2026-10-03-after-structure.md` §2, conventions as detectors.

A producer is measured alone before any reviewer reads it, under the static pass's protocol --
facts located at gold sites, read by hand, and emission on the control PRs -- by
`analysis/producer_bench.py`, which is the only gold-reading code a producer has. Nothing here
reads gold, and a test keeps it that way.

Adding a producer is one module in this package and one line in `PRODUCERS`. The line is explicit
rather than discovered, for the reason `DESIGNS` is: a capability that nothing names is
coverage that is not there.
"""

from __future__ import annotations

import importlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol, Tuple

from src.mathlib_review.io import jsonl_rows


@dataclass(frozen=True)
class Fact:
    """One thing a producer found, at one place in the PR's changed code."""

    producer: str
    #: The change target it was found in, so a bench can join it to gold without re-locating it.
    change_id: str
    path: str
    line: int
    declaration: str
    #: The sentence the reviewer reads. A fact about the code, never an instruction.
    text: str
    #: The census convention it states (`results/pr_review_v5/adjudications/
    #: conventions-census-v1/reader_A/codebook.json`), so a fact can be read beside the asks filed
    #: under the same entry.
    convention: str

    def row(self) -> Dict[str, Any]:
        return asdict(self)


class Producer(Protocol):
    name: str
    version: str
    #: The section heading the reviewer sees, and the paragraph above its facts.
    title: str
    lead: str

    def facts(self, graph: Dict[str, Any]) -> List[Fact]:
        """Every fact on one episode's change graph (`derived/change_graphs.jsonl` row)."""


#: name -> "module:attribute". Imported on use, so a producer's dependencies load only when it is
#: asked for.
PRODUCERS: Dict[str, str] = {
    "dot_notation": "src.mathlib_review.producers.dot_notation:DOT_NOTATION",
}


def producer(name: str) -> Producer:
    if name not in PRODUCERS:
        raise KeyError(f"unknown producer {name!r}; registered: {sorted(PRODUCERS)} "
                       "(src/mathlib_review/producers/__init__.py::PRODUCERS)")
    module, _, attribute = PRODUCERS[name].partition(":")
    return getattr(importlib.import_module(module), attribute)


def change_graphs(release: Path, prs: Iterable[int]) -> Dict[int, Dict[str, Any]]:
    """A release's change graphs for `prs`, by PR. Gold-free: built from the diff alone."""

    wanted = set(prs)
    return {row["pr_number"]: row
            for row in jsonl_rows(Path(release) / "derived/change_graphs.jsonl")
            if row["pr_number"] in wanted}


def declarations(graph: Dict[str, Any]) -> Iterable[Tuple[Dict[str, Any], Dict[str, Any], bool]]:
    """`(target, reviewed entity, introduced)` for each changed declaration with exactly one reviewed
    entity; `introduced` is whether the PR added or renamed it (its full name is not among the
    target's base names). The one iteration every detector shares."""

    entities = {e["entity_id"]: e for e in graph.get("entities") or []}
    for target in graph.get("targets") or []:
        reviewed = [entities[e] for e in target.get("reviewed_entity_ids") or [] if e in entities]
        if target.get("kind") != "declaration" or len(reviewed) != 1:
            continue
        base_names = {entities[e].get("fullname") for e in target.get("base_entity_ids") or []
                      if e in entities}
        name = reviewed[0].get("fullname")
        yield target, reviewed[0], bool(name) and name not in base_names


def declared_names(graph: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Every full name the graph declares, either side, to its entity (reviewed side preferred)."""

    out: Dict[str, Dict[str, Any]] = {}
    for entity in graph.get("entities") or []:
        name = entity.get("fullname")
        if name and (name not in out or entity.get("side") == "reviewed"):
            out[name] = entity
    return out


def added_lines(target: Dict[str, Any]) -> set:
    """The stripped text of every line the target's diff fragments add."""

    return {line[1:].strip() for fragment in target.get("diff_fragments") or []
            for line in fragment.split("\n") if line.startswith("+") and not line.startswith("+++")}


def section(item: Producer, facts: List[Fact]) -> Optional[Dict[str, str]]:
    """The packet section for one PR, or None when there is nothing to say: a clean PR gets no
    section, so the absence of one is itself the fact."""

    if not facts:
        return None
    lines = [f"- `{f.path}:{f.line}` ({f.declaration}): {f.text}"
             for f in sorted(facts, key=lambda f: (f.path, f.line, f.text))]
    return {"title": item.title, "text": item.lead.rstrip() + "\n\n" + "\n".join(lines)}


def context_rows(graphs: Iterable[Dict[str, Any]], names: List[str],
                 base_rows: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """The solo task's `context_file` rows: each PR's existing sections (a PR model, say), then one
    section per producer that found something there.

    `base_rows` are read, never rewritten: they are probe-produced data, and the result is a new
    file. A PR in `graphs` with no base row gets a row of its own.
    """

    items = [producer(name) for name in names]
    rows = {row["pr_number"]: {"pr_number": row["pr_number"], "sections": list(row["sections"])}
            for row in (base_rows or [])}
    for graph in graphs:
        pr = graph["pr_number"]
        row = rows.setdefault(pr, {"pr_number": pr, "sections": []})
        for item in items:
            held = section(item, item.facts(graph))
            if held:
                row["sections"].append(held)
    return [rows[pr] for pr in sorted(rows)]


def context_jsonl(rows: List[Dict[str, Any]]) -> str:
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
