"""Finalization, replayed over a real run's recorded arm responses.

Every unit test in `test_pr_review_v5_finalize.py` builds its own candidates. This one takes
the 51 arm responses `pr_review_v5_specialist4_rep1` actually produced and puts them through
the current chain, because everything in the admission path changed this session -- drops
retained as diagnostics, the concern gate retired in favour of provenance, dual channels
assigned after the merge -- and a chain that assembles on fabricated input can still fall over
on the shapes a real arm emits.

It costs nothing: the responses are committed, and no model is called.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.datasets.pr_review_v4.io import load_jsonl
from src.datasets.pr_review_v4.schema import ReviewFinding, ReviewWorkUnit

RUN = Path("results/pr_review_v5/runs/pr_review_v5_specialist4_rep1")
RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
PRS = [33117, 33145, 33337, 33362]


@pytest.fixture(scope="module")
def replay(tmp_path_factory):
    if not (RUN / "arm_responses.jsonl").is_file():
        pytest.skip(f"{RUN} is not in this tree")

    from src.mathlib_review.review.finalize import finalize

    responses = [
        json.loads(line)
        for line in (RUN / "arm_responses.jsonl").read_text().splitlines() if line.strip()
    ]
    wanted = {row.get("work_unit_id") for row in responses}
    units = [
        unit for unit in load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
        if unit.work_unit_id in wanted
    ]
    out = tmp_path_factory.mktemp("replay") / "run"
    report = finalize(out, units=units, routing_mode="lead", responses=responses,
                      pr_numbers=PRS)
    return out, report


def test_the_chain_assembles_on_real_arm_output(replay):
    _out, report = replay
    assert report["candidates_specialist"] > 0
    assert report["issues_total"] > 0


def test_every_finding_names_the_arm_that_produced_it(replay):
    """`arm` is a coarse class several arms share. On this run five distinct specialists are
    named, which is what the routing analysis needs and what `arm` alone cannot give."""

    out, _report = replay
    findings = load_jsonl(out / "findings.jsonl", ReviewFinding)
    assert findings
    assert all(item.origin_arm_id for item in findings)
    assert len({item.origin_arm_id for item in findings}) >= 3


def test_every_finding_carries_its_concern_tags(replay):
    out, _report = replay
    findings = load_jsonl(out / "findings.jsonl", ReviewFinding)
    assert all(item.concern_tags for item in findings)


def test_channels_take_only_the_two_shapes_they_can(replay):
    """`review` is what the system would say; `verified` is the subset it proved. A finding in
    `verified` and not `review` would mean it proved something it does not say."""

    out, _report = replay
    findings = load_jsonl(out / "findings.jsonl", ReviewFinding)
    shapes = {tuple(item.channels) for item in findings}
    assert shapes <= {("review",), ("review", "verified"), ()}
    assert ("review",) in shapes, "some finding should be said and not proved"


def test_the_two_channels_are_substantively_different(replay):
    """If they matched, the split would be reporting one number twice."""

    _out, report = replay
    channels = report["channels"]
    assert channels["review"] > channels["verified"] > 0
    assert channels["review_only"] == channels["review"] - channels["verified"]


def test_the_judges_own_model_parses_what_finalization_wrote(replay):
    """The fields added this session travel through `findings.jsonl`, which is the file the
    judge reads. A schema change that finalization accepts and the judge refuses would only
    surface after a paid generation run."""

    out, _report = replay
    findings = load_jsonl(out / "findings.jsonl", ReviewFinding)
    assert len(findings) == len(
        [line for line in (out / "findings.jsonl").read_text().splitlines() if line.strip()])
