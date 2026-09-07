"""Provenance recorded, and drops retained -- the two things the concern gate stands in for.

`ALLOWED_CONCERN_BY_ARM` refuses a submission whose declared concern is outside the arm's set.
It exists for a good reason: an arm reporting an unexpected concern passes submission, produces
no verification artifact its declared concern can generate, and is dropped at finalization
"without a word" -- on the rep2 smoke run that was all four specialist candidates.

But the gate rejects correct findings. 11 of the 19 gold obligations labelled `style` are
`grind` simplifications and `encard_` renames, so an arm that finds one and labels it honestly
is refused for guessing the evaluator's vocabulary wrong.

Removing it safely needs two things first: every drop recorded so it can be scored, and
provenance that does not depend on the concern label.
"""

from __future__ import annotations

import pytest

from src.datasets.pr_review_v4.schema import ReviewFinding


def test_the_finding_model_records_which_arm_found_it():
    """`arm` is a coarse class several arms share -- `generalist` covers naming, docs, style
    and family_design -- so it cannot answer "which arm found this"."""

    fields = ReviewFinding.model_fields
    assert "origin_arm_id" in fields
    assert fields["origin_arm_id"].default is None


def test_concern_tags_are_plural_and_non_gating():
    """`concern_family` is one value and is gated on. Tags let a claim say what it is without
    the label deciding whether it may be said."""

    fields = ReviewFinding.model_fields
    assert "concern_tags" in fields
    assert fields["concern_tags"].default_factory is not None


@pytest.fixture
def unit_and_run(tmp_path):
    """One specialist claim with no verification artifact, finalized."""

    from src.datasets.pr_review_v4.io import load_jsonl
    from src.datasets.pr_review_v4.schema import ReviewWorkUnit
    from src.datasets.pr_review_v5.finalize import finalize
    from tests.datasets.test_pr_review_v5_finalize import RELEASE, _candidate, _response

    unit = next(
        (item for item in load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
         if item.primary_subjects_by_change.get(item.change_ids[0])
         and item.entity_ids_by_change.get(item.change_ids[0])),
        None,
    )
    if unit is None:
        pytest.skip("no suitable work unit in the release")
    finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "proof_golf", [_candidate(unit)], spec_id="proof_golf")],
    )
    return tmp_path / "run"


def _candidate(spec_id="duplication", concern="duplication", ordinal=0):
    from src.datasets.pr_review_v4.schema import CandidateClaim

    return CandidateClaim(
        candidate_id=f"candidate:{spec_id}{ordinal}", producer="model",
        work_unit_id="wu:1", episode_id="ep:1", pr_number=1,
        change_ids=["change:a"], primary_change_id="change:a",
        primary_subject="Foo.bar", requested_change="do the thing",
        concern_family=concern, spec_id=spec_id, concern_label=concern,
        severity="advisory", claim="a claim about Foo.bar", ordinal=ordinal,
        evidence_requests=[], source_sha256="a" * 64,
    )


def test_provenance_is_taken_from_the_candidate():
    from src.datasets.pr_review_v4.merge import finding_from_candidate

    finding = finding_from_candidate(
        _candidate(), admission="diagnostic", admission_reason="r", arm="generalist")
    assert finding.origin_arm_id == "duplication"
    assert finding.concern_tags == ["duplication"]


def test_merging_two_arms_records_both_concerns_and_no_single_origin():
    """Two arms finding the same thing is a fact about the finding. Keeping only the
    representative's provenance would report one arm's work as the whole of it."""

    from src.datasets.pr_review_v4.merge import finding_from_candidate, merge_findings

    first = finding_from_candidate(
        _candidate("duplication", "duplication", 0),
        admission="diagnostic", admission_reason="r", arm="generalist")
    second = finding_from_candidate(
        _candidate("family_design", "generalization", 1),
        admission="diagnostic", admission_reason="r", arm="generalist")
    # Same anchor and same requested change, so they fold together.
    merged, _conflicts, _report = merge_findings([first, second], pr_finding_limit=None)

    if len(merged) == 1:
        assert merged[0].origin_arm_id is None          # several arms, no single origin
        assert set(merged[0].concern_tags) >= {"duplication"}
    else:
        # They did not fold; each keeps its own provenance, which is the other correct answer.
        assert {item.origin_arm_id for item in merged} == {"duplication", "family_design"}


def test_merging_one_arm_with_itself_keeps_the_origin():
    from src.datasets.pr_review_v4.merge import finding_from_candidate, merge_findings

    findings = [
        finding_from_candidate(_candidate("duplication", "duplication", index),
                               admission="diagnostic", admission_reason="r",
                               arm="generalist")
        for index in range(2)
    ]
    merged, _c, _r = merge_findings(findings, pr_finding_limit=None)
    assert all(item.origin_arm_id == "duplication" for item in merged)


# --- drops are retained, not counted ------------------------------------------------------


def test_a_candidate_with_no_artifact_is_collected_rather_than_lost(tmp_path):
    """It was counted to stderr and discarded, which made a correct claim lacking a warrant
    indistinguishable from a wrong one."""

    import json

    from src.datasets.pr_review_v4.conditions import focused_findings

    path = tmp_path / "candidates.jsonl"
    path.write_text(
        json.dumps(_candidate().model_dump(mode="json")) + "\n", encoding="utf-8")

    dropped = []
    findings = focused_findings(path, None, None, dropped=dropped)
    assert findings == []
    assert len(dropped) == 1
    assert dropped[0].spec_id == "duplication"


def test_collecting_drops_is_optional_so_existing_callers_are_unchanged(tmp_path):
    import json

    from src.datasets.pr_review_v4.conditions import focused_findings

    path = tmp_path / "candidates.jsonl"
    path.write_text(
        json.dumps(_candidate().model_dump(mode="json")) + "\n", encoding="utf-8")
    assert focused_findings(path, None) == []


def test_a_dropped_candidate_becomes_a_diagnostic_finding():
    """So the judge can score it, and a claim that was right but unwarranted can be told apart
    from one that was wrong."""

    from src.datasets.pr_review_v5.finalize import _unwarranted_findings

    findings = _unwarranted_findings([_candidate()], pr_numbers=None)
    assert len(findings) == 1
    assert findings[0].admission == "diagnostic"
    assert "no verification artifact" in findings[0].admission_reason
    assert findings[0].origin_arm_id == "duplication"


def test_an_unwarranted_claim_reaches_the_judge_but_not_the_review(unit_and_run):
    """The two halves of "reported, not silently dropped".

    `findings.jsonl` is the audit trail the judge reads, so the claim has to be there or it
    cannot be scored. `issues.jsonl` is the maintainer-facing review, and it must not be
    there: downgrading a claim whose whole premise is that the compiler agreed, into a review
    where no compile backs it, is the thing `focused_findings` refuses to do directly.
    """

    import json

    run = unit_and_run
    findings = [json.loads(line) for line in
                (run / "findings.jsonl").read_text().splitlines() if line.strip()]
    issues = [json.loads(line) for line in
              (run / "issues.jsonl").read_text().splitlines() if line.strip()]

    assert len(findings) == 1
    assert findings[0]["admission"] == "diagnostic"
    assert findings[0]["origin_arm_id"] == "proof_golf"
    assert issues == []


def test_an_unwarranted_claim_is_in_neither_channel(unit_and_run):
    """It is an audit record, not something the system said. Counting it under `review` would
    claim credit for a claim that was withheld."""

    import json

    findings = [json.loads(line) for line in
                (unit_and_run / "findings.jsonl").read_text().splitlines() if line.strip()]
    assert findings[0]["channels"] == []


def test_the_drop_count_comes_from_the_function_that_drops(tmp_path):
    """It was re-derived here by reimplementing the artifact join. The copy did not apply
    `pr_numbers`, so a candidate that was never in scope was reported as one that lost its
    warrant."""

    import inspect

    from src.datasets.pr_review_v5 import finalize as module

    source = inspect.getsource(module.finalize)
    assert "verified_keys" not in source, "the drop rule is re-derived a second time"
    assert "dropped=unwarranted" in source
