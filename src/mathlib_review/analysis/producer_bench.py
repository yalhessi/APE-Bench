"""Measure a producer alone, before any reviewer reads it.

The protocol of `results/pr_review_v5/probes/static-pass-2026-10-01/README.md`, for any producer
in `src/mathlib_review/producers/` and any probe set (`configs/probe_sets/`):

- **located**: an ask is located when a fact shares a change target with it. That is the judge's
  `location_hit` notion and it is not a hit: whether the fact *is* the maintainer's ask is read by
  hand, which is why every located pair is written out with the ask's own words beside the fact;
- **control emission**: facts on the set's control PRs, where maintainers asked for nothing -- what
  the section would tell a reviewer about a clean PR;
- **volume**: facts per PR.

This module reads the maintainers' asks, so it is evaluation code: producers never import it, and
nothing it computes reaches a packet.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.mathlib_review.analysis.probes import load_probe_set
from src.mathlib_review.producers import change_graphs, producer


def ask_targets(graph: Dict[str, Any], path: Optional[str], line: Optional[int]) -> Set[str]:
    """The change targets an ask at `path:line` sits in: a reviewed declaration whose span holds
    the line, or a changed range of the target whose reviewed span does. A PR-level ask (no path)
    sits in none."""

    if not path or line is None:
        return set()
    entities = {e["entity_id"]: e for e in graph.get("entities") or []}
    ranges = {r["range_id"]: r for r in graph.get("changed_ranges") or []}
    found = set()
    for target in graph.get("targets") or []:
        if target.get("path") != path:
            continue
        spans = [entities[e]["span"] for e in target.get("reviewed_entity_ids") or [] if e in entities]
        spans += [ranges[r]["reviewed_span"] for r in target.get("changed_range_ids") or []
                  if r in ranges and ranges[r].get("reviewed_span")]
        if any(span["line_start"] <= line <= span["line_end"] for span in spans):
            found.add(target["change_id"])
    return found


def bench(producer_name: str, set_path: Path) -> Dict[str, Any]:
    spec = load_probe_set(set_path)
    asks = json.loads(spec.asks_file.read_text(encoding="utf-8"))
    controls = sorted(int(pr) for pr in asks.get("controls") or [])
    rows_by_cid = {row["cid"]: row
                   for row in json.loads(spec.feedback_file.read_text(encoding="utf-8"))["rows"]}
    item = producer(producer_name)
    graphs = change_graphs(spec.release, spec.pr_numbers)

    facts: List[Dict[str, Any]] = []
    located: List[Dict[str, Any]] = []
    asks_total = 0
    for pr in spec.pr_numbers:
        graph = graphs.get(pr)
        if graph is None:
            continue
        cids = list((asks.get("asks") or {}).get(str(pr)) or [])
        asks_total += len(cids)
        targets = {cid: ask_targets(graph, rows_by_cid[cid].get("path"), rows_by_cid[cid].get("line"))
                   for cid in cids if cid in rows_by_cid}
        for fact in item.facts(graph):
            sharing = sorted(cid for cid, held in targets.items() if fact.change_id in held)
            facts.append({**fact.row(), "pr_number": pr, "control": pr in controls,
                          "located_asks": sharing})
            for cid in sharing:
                located.append({"pr_number": pr, "cid": cid, "fact": fact.text,
                                "at": f"{fact.path}:{fact.line}",
                                "ask_at": f"{rows_by_cid[cid].get('path')}:{rows_by_cid[cid].get('line')}",
                                "ask": (rows_by_cid[cid].get("body") or "")[:600]})
    per_pr = Counter(f["pr_number"] for f in facts)
    return {
        "producer": producer_name,
        "version": item.version,
        "set": spec.name,
        "prs": len(graphs),
        "asks": asks_total,
        "facts": len(facts),
        "facts_per_pr": {str(pr): per_pr.get(pr, 0) for pr in spec.pr_numbers if pr in graphs},
        "control_prs": controls,
        "control_facts": {str(pr): per_pr.get(pr, 0) for pr in controls},
        "asks_located": sorted({row["cid"] for row in located}),
        "located": located,
        "fact_rows": facts,
    }
