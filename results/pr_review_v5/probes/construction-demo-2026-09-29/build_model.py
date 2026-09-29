"""Pass 0 of `docs/research/review-coordination-design-2026-09.md`: the PR model, built
deterministically for the demonstration's three PRs.

Reads the release's `input/episodes.jsonl` and `derived/{change_graphs,modification_inventory}.jsonl`
only -- never `gold/`, and no review text. Relations and families come from the pipeline's own
functions (`release.pr_relations.build_relations`, `agenda.components.build_components`). What the
design's pass 0 also holds and is not built (library candidates, the twin-pattern and area
censuses, open-PR overlap) is left out and said so in the rendered model.

Run from the repo root: `PYTHONPATH=$PWD:$PWD/src ape/bin/python <this file>`.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.mathlib_review.agenda.components import build_components
from src.mathlib_review.io import load_jsonl
from src.mathlib_review.release.pr_relations import build_relations
from src.mathlib_review.schema import ChangeGraph, ReviewEpisodeInput

RELEASE = Path("inputs/pr_review_v4/releases/val-2025-06-2026-03-v1")
PRS = (34091, 30458, 32875)
OUT = Path(__file__).parent

episodes = {e.pr_number: e for e in load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput)
            if e.pr_number in PRS}
graphs = [g for g in load_jsonl(RELEASE / "derived/change_graphs.jsonl", ChangeGraph)
          if g.pr_number in PRS]
inventory = {}
for line in (RELEASE / "derived/modification_inventory.jsonl").read_text().splitlines():
    row = json.loads(line)
    if row["pr_number"] in PRS:
        inventory[row["primary_change_id"]] = row
relations, _evidence = build_relations(graphs)
components = build_components(graphs, relations, episodes.values())


def text(value) -> str:
    return (getattr(value, "text", None) or "") if value is not None else ""


def short(change_id: str) -> str:
    return change_id.split(":", 1)[-1][:10]


for graph in graphs:
    pr = graph.pr_number
    episode = episodes[pr]
    name = {t.change_id: (t.declaration_name or f"{t.kind} in {t.path.split('/')[-1]}")
            for t in graph.targets}
    lines = [
        f"# The PR model for #{pr} (pass 0)",
        "",
        "Built deterministically from the diff and the change graph, with no review text. Every "
        "entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, "
        "not a premise. Not built, so not here: library candidates, the area's twin patterns "
        "and conventions, and other open PRs. Construct what you need of those with the tools.",
        "",
        "## The PR",
        "",
        f"- title: {text(episode.title)}",
        f"- description: {text(episode.description) or '(not recoverable at review start)'}",
        f"- changed files: {', '.join(episode.changed_files)}",
        "",
        "## Objects",
        "",
    ]
    removed = []
    for t in sorted(graph.targets, key=lambda t: (t.path, t.change_id)):
        inv = inventory.get(t.change_id, {})
        lifecycle = inv.get("lifecycle") or ("added" if not (t.base_code or "").strip()
                                             else "removed" if not (t.reviewed_code or "").strip()
                                             else "modified")
        changed = ", ".join(f"{d['component']}:{d['status']}" for d in inv.get("component_deltas", [])
                            if d.get("status") != "unchanged") or "-"
        kind = t.declaration_kind or t.kind
        lines.append(f"### `{name[t.change_id]}` ({kind}, {lifecycle}) [{short(t.change_id)}]")
        lines.append(f"- file: `{t.path}`; changed: {changed}")
        if lifecycle == "removed":
            removed.append(name[t.change_id])
        if t.kind in ("declaration",) or lifecycle != "unchanged_context":
            if (t.base_code or "").strip():
                lines += ["- before the PR:", "```lean", t.base_code.rstrip(), "```"]
            if (t.reviewed_code or "").strip():
                lines += ["- as the PR leaves it:", "```lean", t.reviewed_code.rstrip(), "```"]
        lines.append("")
    lines += ["## Removed or renamed", ""]
    lines += [f"- `{n}`" for n in removed] or ["- none"]
    lines += ["", "## Families (declarations that may be one decision)", ""]
    fams = [c for c in components if c.pr_number == pr and c.grain == "family"]
    for c in fams:
        lines.append(f"- [{c.evidence}] " + ", ".join(f"`{s}`" for s in c.subjects) + f" -- {c.reason}")
    if not fams:
        lines.append("- none found by the change graph")
    lines += ["", "## Relations between changed declarations", ""]
    rels = [r for r in relations if r.pr_number == pr]
    for r in sorted(rels, key=lambda r: (r.relation_kind, name[r.source_change_id])):
        related = ", ".join(f"`{name[c]}`" for c in r.related_change_ids if c in name)
        lines.append(f"- {r.relation_kind} [{r.confidence}]: `{name[r.source_change_id]}` -> {related}")
    if not rels:
        lines.append("- none")
    (OUT / f"model_pr{pr}.md").write_text("\n".join(lines) + "\n")
    print(pr, "objects", len(graph.targets), "families", len(fams), "relations", len(rels))
