"""A whole-PR review, from submitted findings to the file the judge scores.

`plan` proves the front half of a solo run -- agenda, budget, cutoffs, sealing. This is the
back half, which nothing else exercises: `_solo_responses` anchors the free-form findings, then
`finalize` ingests them, merges, assigns channels, digests and writes `findings.jsonl`.

Every piece has unit tests. The seam between them does not, and it is where a solo run differs
most from the arms: these candidates arrive without a rendered work-unit prompt behind them,
without a verification artifact, and from an arm the merge and the digest have never seen. A
run is expensive and a judge run is expensive again, so the chain is proven here for nothing
first.

Real release data on purpose. A fixture graph would prove the code paths connect while saying
nothing about whether an agent's file-and-line lands on a change target that is actually in a
work unit, which is the part that can fail quietly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.io import jsonl_rows, load_jsonl
from src.mathlib_review.review.runner import SOLO_ARM_ID, _solo_responses
from src.mathlib_review.review.finalize import finalize
from src.mathlib_review.schema import ChangeGraph, ReviewWorkUnit

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
pytestmark = pytest.mark.skipif(
    not (RELEASE / "derived/change_graphs.jsonl").is_file(),
    reason="needs the dev-medium release on disk")


class _Results:
    def __init__(self, rows):
        self.task_results = rows


@pytest.fixture(scope="module")
def episode():
    """A real episode whose graph has a declaration target inside a work unit, with a
    reviewed-side line an agent could plausibly cite."""

    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    graphs = [ChangeGraph.model_validate(row)
              for row in jsonl_rows(RELEASE / "derived/change_graphs.jsonl")]
    by_episode = {}
    for unit in units:
        by_episode.setdefault(unit.episode_id, []).append(unit)

    for graph in graphs:
        episode_units = by_episode.get(graph.episode_id) or []
        owned = {cid for unit in episode_units for cid in unit.change_ids}
        ranges = {item.range_id: item for item in graph.changed_ranges}
        for target in graph.targets:
            if target.change_id not in owned or target.kind != "declaration":
                continue
            for range_id in target.changed_range_ids:
                span = ranges[range_id].reviewed_span
                if span:
                    return graph, episode_units, target, span.line_start
    pytest.skip("no anchorable declaration target in the release")


def _submission(graph, path, line, **overrides):
    finding = {
        "anchor": {"path": path, "line_start": line, "line_end": line},
        "severity": "advisory",
        "claim": "This declaration duplicates an existing one.",
        "suggested_fix": "Reuse the existing declaration.",
        "concern_family": "duplication",
        "issue_kind": "duplicate_implementation",
    }
    finding.update(overrides)
    return {"success": True, "episode_id": graph.episode_id, "pr_number": graph.pr_number,
            "findings": [finding]}


def test_a_submitted_finding_becomes_a_scorable_finding_on_disk(episode, tmp_path):
    """The whole chain. What the judge reads is `findings.jsonl`, and a run that produces an
    empty one is scored as a reviewer that found nothing -- so "it did not crash" is not the
    property worth asserting here. The property is that a real change target comes out the far
    end, attributed to the right arm."""

    graph, units, target, line = episode
    responses, anchor_rows = _solo_responses(
        _Results([_submission(graph, target.path, line)]), [graph], units)

    assert responses, "the anchoring produced no response to finalize"
    assert anchor_rows[0]["failure"] is None, anchor_rows[0]

    report = finalize(tmp_path / "run", units=list(units), routing_mode="solo",
                      responses=responses)

    findings = [json.loads(line) for line
                in (tmp_path / "run" / "findings.jsonl").read_text().split("\n") if line.strip()]
    assert findings, f"nothing reached findings.jsonl; report={report}"
    assert all(item["arm"] == SOLO_ARM_ID for item in findings), \
        [item["arm"] for item in findings]
    assert target.change_id in findings[0]["change_ids"]
    assert findings[0]["primary_change_id"] == target.change_id


def test_it_is_filed_under_its_own_arm_and_not_the_generalists(episode, tmp_path):
    """`solo_agent` and `generalist` are the control and the treatment of the comparison this
    condition exists for. Sharing a value would make them indistinguishable in every `by_arm`
    breakdown, and the comparison would silently have one arm."""

    graph, units, target, line = episode
    responses, _rows = _solo_responses(
        _Results([_submission(graph, target.path, line)]), [graph], units)
    finalize(tmp_path / "run", units=list(units), routing_mode="solo", responses=responses)

    findings = [json.loads(line) for line
                in (tmp_path / "run" / "findings.jsonl").read_text().split("\n") if line.strip()]
    assert "generalist" not in {item["arm"] for item in findings}


def test_it_lands_in_the_review_channel_though_the_evidence_gate_stays_shut(episode, tmp_path):
    """The gate is closed for this arm as it is for the generalist -- no collector can support
    a duplication claim -- so `published` recall would measure the gate rather than either
    reviewer. `channels` is what separates the two, and the comparison is read on `review`."""

    graph, units, target, line = episode
    responses, _rows = _solo_responses(
        _Results([_submission(graph, target.path, line)]), [graph], units)
    finalize(tmp_path / "run", units=list(units), routing_mode="solo", responses=responses)

    findings = [json.loads(line) for line
                in (tmp_path / "run" / "findings.jsonl").read_text().split("\n") if line.strip()]
    assert any("review" in (item.get("channels") or []) for item in findings)
    assert all(item["admission"] != "published" for item in findings)


def test_a_finding_with_no_issue_kind_is_refused_rather_than_mislabelled(episode, tmp_path):
    """Every work unit in this release is `candidate-prompt/12`, which requires it. The
    refusal must be visible: a rejected candidate is recorded, not dropped, or the condition
    reads as silent for a reason nobody can see."""

    graph, units, target, line = episode
    responses, _rows = _solo_responses(
        _Results([_submission(graph, target.path, line, issue_kind=None)]), [graph], units)
    report = finalize(tmp_path / "run", units=list(units), routing_mode="solo",
                      responses=responses)

    rejections = (tmp_path / "run" / "candidate_rejections.jsonl")
    assert rejections.is_file() and rejections.read_text().strip(), report
    assert "issue_kind" in rejections.read_text()


def test_an_unanchorable_finding_reaches_no_work_unit_and_is_counted(episode, tmp_path):
    """A whole-PR reviewer comments on unchanged context lines. Those resolve to nothing, and
    the loss has to be counted rather than deleted -- dropping them would hand the condition a
    free precision gain on the control PR plus a recall penalty, and hide its own loss rate."""

    graph, units, _target, _line = episode
    responses, rows = _solo_responses(
        _Results([_submission(graph, "Mathlib/NotInThisPR.lean", 5)]), [graph], units)

    assert responses == []
    assert len(rows) == 1 and rows[0]["failure"] == "unknown_path"
