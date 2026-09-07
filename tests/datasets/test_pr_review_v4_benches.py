"""A bench makes one arm answerable on its own.

Today an arm can only be measured by running the whole pipeline -- a lead, a nested
orchestrator, a full judge run -- and attributing findings backwards. That costs a paid run to
learn anything about one arm, which is why "investigate each arm separately" has never
happened and why a proposed replacement for `proof_golf` has no way to prove itself.

Building the fixtures turned up a defect that had made one arm unmeasurable from the day it
was added: every arm declares the concern family `documentation` and every gold judgment says
`docs`. Nothing joined the two, so `docs` had zero attributable obligations.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.datasets.pr_review_v4.benches import (
    CONCERN_ALIASES, build_all, build_bench, coverage_report,
)
from src.datasets.pr_review_v4.io import load_jsonl
from src.datasets.pr_review_v4.schema import JudgmentNode, ReviewWorkUnit

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.fixture(scope="module")
def benches():
    if not RELEASE.is_dir():
        pytest.skip("release not present")
    from src.datasets.pr_review_v5.arm_registry import ARM_DEFINITIONS
    roster = {d.arm_id: sorted(d.allowed_concerns) for d in ARM_DEFINITIONS}
    return build_all(RELEASE, roster)


def test_every_arm_has_something_to_be_measured_against(benches):
    """An arm with no positives cannot be improved by its bench, and that should be said out
    loud rather than discovered after a paid run."""

    report = coverage_report(benches)
    assert report["arms_with_no_positives"] == []
    assert report["total_positive_cases"] > 50


def test_the_docs_arm_is_measurable_at_all(benches):
    """It was not. `documentation` never matched `docs`, so no gold obligation could be
    attributed to it, and improving the arm could not have shown up anywhere."""

    assert len(benches["docs"].positives) == 4


def test_the_two_concern_vocabularies_are_bridged(benches):
    """Guards the alias table against quietly growing: any arm concern family that gold never
    uses, and that no alias maps, is an arm nothing can score."""

    import json

    from src.datasets.pr_review_v5.arm_registry import ARM_DEFINITIONS

    gold_labels = set()
    for line in (RELEASE / "gold/judgments.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            gold_labels.update(json.loads(line).get("concern_labels") or [])

    arm_families = {c for d in ARM_DEFINITIONS for c in d.allowed_concerns}
    unbridged = {
        family for family in arm_families
        if family not in gold_labels and CONCERN_ALIASES.get(family) not in gold_labels
    }
    assert unbridged == set(), (
        f"arm concern families gold cannot express: {sorted(unbridged)}. "
        "Either the arm declares a concern gold never uses, or CONCERN_ALIASES needs a row.")


def test_a_bench_carries_negatives_from_the_same_prs(benches):
    """An arm that reports something everywhere scores perfectly against positives alone. A
    negative drawn from a PR the arm never sees measures nothing, so they come from PRs gold
    does cover -- places a maintainer looked and asked for nothing of this kind."""

    for arm_id, bench in benches.items():
        assert bench.negatives, arm_id
        positive_prs = {case.pr_number for case in bench.positives}
        negative_prs = {case.pr_number for case in bench.negatives}
        assert positive_prs <= negative_prs | positive_prs, arm_id


def test_a_case_handed_to_an_arm_carries_no_gold():
    """The arm sees a work unit; the scorer sees the obligation afterwards. Putting gold in
    the payload is the contamination this project has already had once."""

    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    judgments = load_jsonl(RELEASE / "gold/judgments.jsonl", JudgmentNode)
    bench = build_bench("duplication", ["duplication"], units=units, judgments=judgments)

    case = bench.positives[0]
    # The fields an arm payload is built from.
    payload_fields = {"work_unit_id", "pr_number", "episode_id", "change_ids"}
    for name in payload_fields:
        assert getattr(case, name) is not None
    # Gold lives on the case for the scorer, and must be separately named so it cannot be
    # passed along by accident.
    assert case.expected_obligation_ids
    assert "expected" not in payload_fields


def test_the_fixture_is_hashed_so_a_score_names_what_it_measured(benches):
    first = benches["duplication"].identity()
    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    judgments = load_jsonl(RELEASE / "gold/judgments.jsonl", JudgmentNode)
    again = build_bench("duplication", ["duplication"],
                        units=units, judgments=judgments).identity()
    assert first == again
    assert first != benches["naming"].identity()


def test_restricting_to_a_pr_set_narrows_the_fixture():
    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    judgments = load_jsonl(RELEASE / "gold/judgments.jsonl", JudgmentNode)
    everything = build_bench("duplication", ["duplication"],
                             units=units, judgments=judgments)
    smoke4 = build_bench("duplication", ["duplication"], units=units, judgments=judgments,
                         pr_numbers=[33117, 33145, 33337, 33362])
    assert 0 < len(smoke4.cases) < len(everything.cases)
    assert {case.pr_number for case in smoke4.cases} <= {33117, 33145, 33337, 33362}


# --- scoring --------------------------------------------------------------------------------
#
# The bench's cheap signal: did the arm speak, and in the right place. Whether the claim is
# *correct* is the judge's question and needs a semantic run -- a bench hit is a necessary
# condition for a scored hit, never a sufficient one.


def _judgments():
    return load_jsonl(RELEASE / "gold/judgments.jsonl", JudgmentNode)


def test_a_perfect_run_locates_every_positive(benches):
    from src.datasets.pr_review_v4.benches import gold_anchor_index, score_bench

    bench = benches["duplication"]
    anchors = {case.work_unit_id: list(case.change_ids) for case in bench.positives}
    score = score_bench(bench, anchors,
                        gold_anchors_by_unit=gold_anchor_index(bench, _judgments()))

    assert score["located"] == score["positives"]
    assert score["location_rate"] == 1.0
    assert score["spoke_when_quiet"] == 0


def test_a_silent_run_locates_nothing_and_is_counted_as_abstaining(benches):
    """The failure mode the arms actually exhibit: 30 of 46 specialist runs on smoke4
    abstained, and an abstention has to be distinguishable from a wrong answer."""

    from src.datasets.pr_review_v4.benches import gold_anchor_index, score_bench

    bench = benches["duplication"]
    score = score_bench(bench, {},
                        gold_anchors_by_unit=gold_anchor_index(bench, _judgments()))

    assert score["located"] == 0
    assert score["abstained_on_positives"] == score["positives"]
    assert score["spoke_when_quiet"] == 0


def test_an_arm_that_reports_everywhere_is_penalised_on_negatives(benches):
    """Positives alone would score a maximally noisy arm perfectly."""

    from src.datasets.pr_review_v4.benches import gold_anchor_index, score_bench

    bench = benches["naming"]
    everywhere = {case.work_unit_id: list(case.change_ids) for case in bench.cases}
    score = score_bench(bench, everywhere,
                        gold_anchors_by_unit=gold_anchor_index(bench, _judgments()))

    assert score["spoke_when_quiet"] == score["negatives"] > 0
    assert score["false_alarm_rate"] == 1.0


def test_landing_in_the_right_unit_but_the_wrong_declaration_is_not_a_hit(benches):
    """Gold anchors are narrower than the work unit, so a candidate anywhere in a multi-target
    unit must not count as having found the obligation's site."""

    from src.datasets.pr_review_v4.benches import gold_anchor_index, score_bench

    bench = benches["duplication"]
    gold_anchors = gold_anchor_index(bench, _judgments())
    elsewhere = {
        case.work_unit_id: ["change:not-a-real-anchor"] for case in bench.positives
    }
    score = score_bench(bench, elsewhere, gold_anchors_by_unit=gold_anchors)

    assert score["located"] == 0
    assert score["candidates_total"] == len(bench.positives)   # it spoke, just wrongly


def test_the_score_names_the_fixture_it_measured(benches):
    from src.datasets.pr_review_v4.benches import score_bench

    bench = benches["duplication"]
    score = score_bench(bench, {})
    assert score["fixture_sha256"] == bench.identity()
    assert "necessary condition" in score["note"]


def test_an_arm_payload_carries_no_gold():
    """The run itself must be gold-free. The scorer joins gold afterwards, on this side."""

    from src.datasets.pr_review_v5.bench_cli import _payloads_for, roster
    from src.datasets.pr_review_v5.runner import load_release, load_run

    config = Path("configs/bases/v5_generation.yaml")
    if not config.is_file():
        pytest.skip("base config not present")
    dataset, _scaffold, _ = load_run(config)
    release = load_release(dataset)
    bench = build_all(dataset.release, roster(), pr_numbers=[33145])["duplication"]

    payloads = _payloads_for(bench, dataset, release)
    assert payloads
    for payload in payloads.values():
        for key in payload:
            assert not any(word in key.lower()
                           for word in ("obligation", "gold", "judgment", "expected")), key
