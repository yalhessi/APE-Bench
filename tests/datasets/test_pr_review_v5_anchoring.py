"""Projecting a whole-PR review onto change targets, and measuring what the projection costs.

The `solo` condition is never given the change-id vocabulary -- that is the treatment. But
everything downstream keys on it: `ingest_responses` resolves a response through
`unit_by_id[work_unit_id]` and skips an unknown one with a `logger.warning` only, and the judge
pairs findings to obligations on shared `change_ids`. So a free-form finding has to be resolved
onto a change target and a work unit, and the resolution has to be measured -- an unmeasured
projection applied to one arm of a comparison is the shape of a retracted result
(`docs/dead-ends.md:128`: "a path-normalisation bug plus claim-strictness; the whole first
decomposition effort chased a metric artifact").

The resolver is not new. `GraphIndex.line_targets` was written to migrate curated maintainer
review-comment anchors onto change targets, which is the same provenance as a baseline finding.
`test_the_resolver_reproduces_every_curated_maintainer_anchor` is the validation that matters,
and it runs against frozen human-labelled gold.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from src.mathlib_review.io import jsonl_rows
from src.mathlib_review.review.candidates import (
    ANCHOR_FAILURES, anchor_submitted_findings, anchoring_report,
)
from src.mathlib_review.schema import ChangeGraph, ReviewWorkUnit

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
pytestmark = pytest.mark.skipif(
    not (RELEASE / "derived/change_graphs.jsonl").is_file(),
    reason="needs the dev-medium release on disk")


def _graphs():
    return {graph.graph_id: graph for graph in (
        ChangeGraph.model_validate(row)
        for row in jsonl_rows(RELEASE / "derived/change_graphs.jsonl"))}


def _units():
    return [ReviewWorkUnit.model_validate(row)
            for row in jsonl_rows(RELEASE / "derived/work_units.jsonl")]


def test_the_resolver_reproduces_every_curated_maintainer_anchor():
    """The validation the free-form design rests on.

    `gold/intervention_scope_migrations.jsonl` is frozen and curator-reviewed. Its
    `source_comment` resolutions are maintainer GitHub review comments at a reviewed-side line,
    each with the change targets a human accepted. If the resolver cannot reproduce those, it
    cannot be trusted on an agent's findings either -- and the baseline's recall would be a
    measurement of this function.
    """

    from src.mathlib_review.legacy_pipeline.migrate_interventions import GraphIndex

    indexes = {gid: GraphIndex(graph) for gid, graph in _graphs().items()}
    stats, replayed, misses = Counter(), 0, []
    for row in jsonl_rows(RELEASE / "gold/intervention_scope_migrations.jsonl"):
        index = indexes.get(row["graph_id"])
        if index is None:
            continue
        for res in row.get("resolutions") or []:
            if res.get("source_kind") != "source_comment":
                continue
            if res.get("line_start") is None or not res.get("path"):
                continue
            replayed += 1
            got, method = index.line_targets(
                res["path"], res["line_start"], res.get("side") or "RIGHT")
            stats[method] += 1
            if set(got) == set(res.get("change_ids") or []):
                stats["exact_set"] += 1
            else:
                misses.append((res["path"], res["line_start"], sorted(got)))

    assert replayed == 41, replayed
    assert stats["exact_set"] == 41, misses
    # Every one at the strictest tier: no changed-range fallback, no nearest-within-3.
    assert stats["review_line_entity"] == 41, dict(stats)


def test_every_change_target_sits_in_exactly_one_work_unit():
    """Hop two is total and unique, so it cannot silently drop a finding hop one resolved. If a
    release ever packs a target into two units this fails, and `anchor_submitted_findings`
    would start attributing one finding to whichever unit it happened to see first."""

    counts = Counter()
    for unit in _units():
        for change_id in unit.change_ids:
            counts[change_id] += 1
    targets = {t.change_id for graph in _graphs().values() for t in graph.targets}

    assert not [cid for cid, n in counts.items() if n > 1], "a target is in two work units"
    assert not (targets - set(counts)), "a change target belongs to no work unit"


def _one_graph_with_units():
    units = _units()
    by_graph = {}
    for unit in units:
        by_graph.setdefault(unit.graph_id, []).append(unit)
    graphs = _graphs()
    for graph_id, graph_units in sorted(by_graph.items()):
        graph = graphs.get(graph_id)
        if graph and graph.targets:
            return graph, graph_units
    pytest.skip("no graph with both targets and units")


def _finding(path, line, claim="c"):
    return {"anchor": {"path": path, "line_start": line, "line_end": line},
            "claim": claim, "severity": "advisory"}


def test_a_located_finding_reaches_a_work_unit_with_real_change_ids():
    graph, units = _one_graph_with_units()
    target = next(t for t in graph.targets
                  if any(t.change_id in u.change_ids for u in units))
    span = next((r for r in graph.changed_ranges
                 if r.range_id in target.changed_range_ids and r.reviewed_span), None)
    if span is None:
        pytest.skip("target has no reviewed-side span")

    by_unit, rows = anchor_submitted_findings(
        [_finding(target.path, span.reviewed_span.line_start)], graph=graph, units=units)

    assert rows[0]["failure"] is None, rows[0]
    assert rows[0]["work_unit_id"] and rows[0]["change_ids"]
    landed = next(iter(by_unit.values()))[0]
    assert landed["primary_change_id"] in landed["change_ids"]
    assert landed["claim"] == "c"


def test_the_workspace_prefix_a_free_form_agent_emits_is_normalised():
    """The agent works in `workspaces/target/`, so it writes `target/Mathlib/...`. Without
    normalisation every finding it files would miss on path and read as a silent recall of
    zero -- which is indistinguishable from an agent that found nothing."""

    graph, units = _one_graph_with_units()
    target = next(t for t in graph.targets
                  if any(t.change_id in u.change_ids for u in units))
    span = next((r for r in graph.changed_ranges
                 if r.range_id in target.changed_range_ids and r.reviewed_span), None)
    if span is None:
        pytest.skip("target has no reviewed-side span")
    line = span.reviewed_span.line_start

    plain, _ = anchor_submitted_findings([_finding(target.path, line)],
                                         graph=graph, units=units)
    prefixed, _ = anchor_submitted_findings([_finding(f"target/{target.path}", line)],
                                            graph=graph, units=units)
    assert prefixed == plain and plain


@pytest.mark.parametrize("finding,failure", [
    ({"claim": "no location at all"}, "no_location"),
    (_finding("Mathlib/DoesNotExist.lean", 10), "unknown_path"),
])
def test_an_unanchorable_finding_is_kept_and_its_failure_named(finding, failure):
    """Never dropped. A whole-PR reviewer comments on unchanged context lines, and deleting
    those would hand the condition a free precision gain -- fewer emissions on a control PR --
    plus a recall penalty, while making its own loss rate invisible."""

    graph, units = _one_graph_with_units()
    by_unit, rows = anchor_submitted_findings([finding], graph=graph, units=units)

    assert by_unit == {}
    assert len(rows) == 1 and rows[0]["failure"] == failure
    assert failure in ANCHOR_FAILURES


def test_the_report_states_the_loss_rather_than_leaving_it_to_be_divided():
    graph, units = _one_graph_with_units()
    _by_unit, rows = anchor_submitted_findings(
        [_finding("Mathlib/DoesNotExist.lean", 10), {"claim": "x"}], graph=graph, units=units)
    report = anchoring_report(rows)

    assert report["findings_in"] == 2
    assert report["anchored"] == 0 and report["unanchored"] == 2
    assert report["unanchored_rate"] == 1.0
    assert report["by_failure"] == {"no_location": 1, "unknown_path": 1}
