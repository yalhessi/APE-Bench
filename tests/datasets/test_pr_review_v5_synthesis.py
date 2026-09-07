"""The lead may remove or combine. It may never admit.

This is the file to read hardest. §3 gives a model authority over the finding set for the
first time, and the only thing keeping that safe is that the authority is subtractive: an
assessment can delete a candidate or fold it into another, and nothing else. If an
assessment could add a candidate, raise a severity, or attach a warrant, then a published
finding would no longer mean "the evidence chain supported this" — it would mean "the
evidence chain supported this, or a model said so", which is not a claim worth publishing.

So most of what follows tests things the code must *refuse* to do.
"""

from __future__ import annotations

from types import SimpleNamespace

from src.mathlib_review.review.lead_synthesis import apply_assessments


def candidate(cid, *, work_unit_id="wu:1", spec_id=None, ordinal=0):
    return SimpleNamespace(candidate_id=cid, work_unit_id=work_unit_id,
                           spec_id=spec_id, ordinal=ordinal)


def response(invocation_id, *, work_unit_id="wu:1", spec_id=None):
    return {"invocation_id": invocation_id, "work_unit_id": work_unit_id, "spec_id": spec_id}


def assess(invocation_id, ordinal, verdict, **extra):
    return {"invocation_id": invocation_id, "candidate_ordinal": ordinal,
            "verdict": verdict, **extra}


def run(generalist=(), specialist=(), evidence_specialist=(), responses=(), assessments=()):
    """Returns (kept_generalist, kept_specialist, kept_evidence, report).

    The removed candidates are checked through `removed()` below, so the existing tests keep
    reading as statements about what survives.
    """

    gen, spec, ev, _removed, report = apply_assessments(
        generalist=list(generalist), specialist=list(specialist),
        evidence_specialist=list(evidence_specialist),
        responses=list(responses), assessments=list(assessments),
    )
    return gen, spec, ev, report


def removed(**kwargs):
    """The candidates synthesis took out, paired with why."""

    return apply_assessments(
        generalist=list(kwargs.get("generalist", ())),
        specialist=list(kwargs.get("specialist", ())),
        evidence_specialist=list(kwargs.get("evidence_specialist", ())),
        responses=list(kwargs.get("responses", ())),
        assessments=list(kwargs.get("assessments", ())),
    )[3]


# --- what the lead may do -------------------------------------------------------------

def test_drop_removes_the_candidate_before_projection():
    kept, _s, _e, report = run(
        generalist=[candidate("candidate:a"), candidate("candidate:b", ordinal=1)],
        responses=[response("wu:1#generalist")],
        assessments=[assess("wu:1#generalist", 0, "drop", reason="already covered")],
    )
    assert [item.candidate_id for item in kept] == ["candidate:b"]
    assert report["candidates_dropped"] == 1


def test_duplicate_of_folds_one_candidate_into_another():
    """The probe's actual failure: two findings at one anchor, both suppressed as a conflict.

    Folding the restatement leaves a single finding at the anchor, so the merge has nothing
    to arbitrate and the surviving claim keeps whatever admission it earned.
    """

    kept, _s, _e, report = run(
        generalist=[candidate("candidate:a"), candidate("candidate:b", ordinal=1)],
        responses=[response("wu:1#generalist")],
        assessments=[assess("wu:1#generalist", 1, "duplicate_of",
                            duplicate_of="wu:1#generalist#0")],
    )
    assert [item.candidate_id for item in kept] == ["candidate:a"]
    assert report["candidates_absorbed"] == 1
    assert report["removed_by_candidate"]["candidate:b"] == "folded into candidate:a"


def test_keep_and_needs_sibling_change_nothing():
    kept, _s, _e, report = run(
        generalist=[candidate("candidate:a"), candidate("candidate:b", ordinal=1)],
        responses=[response("wu:1#generalist")],
        assessments=[assess("wu:1#generalist", 0, "keep"),
                     assess("wu:1#generalist", 1, "needs_sibling")],
    )
    assert len(kept) == 2
    assert report["by_verdict"] == {"keep": 1, "needs_sibling": 1}


def test_a_candidate_is_addressable_across_arms_on_the_same_work_unit():
    """Two arms on one work unit both start at ordinal 0, so the arm must disambiguate."""

    kept, _s, evidence, _report = run(
        generalist=[candidate("candidate:g", spec_id=None)],
        evidence_specialist=[candidate("candidate:n", spec_id="naming")],
        responses=[response("wu:1#generalist"),
                   response("wu:1#naming", spec_id="naming")],
        assessments=[assess("wu:1#naming", 0, "drop")],
    )
    assert [item.candidate_id for item in kept] == ["candidate:g"]
    assert evidence == []


# --- what the lead may not do ---------------------------------------------------------

def test_synthesis_can_only_ever_return_a_subset():
    """The invariant the whole design rests on, stated directly."""

    everything = [candidate("candidate:a"), candidate("candidate:b", ordinal=1)]
    for verdict in ("keep", "drop", "duplicate_of", "needs_sibling"):
        kept, _s, _e, report = run(
            generalist=everything,
            responses=[response("wu:1#generalist")],
            assessments=[assess("wu:1#generalist", 0, verdict,
                                duplicate_of="wu:1#generalist#1")],
        )
        assert {item.candidate_id for item in kept} <= {"candidate:a", "candidate:b"}
        assert report["candidates_out"] <= report["candidates_in"]


def test_an_assessment_naming_no_candidate_creates_nothing():
    """It is recorded as unmatched, loudly, because it means the lead was addressing claims
    it could not see — a routing bug, not a synthesis one."""

    kept, _s, _e, report = run(
        generalist=[candidate("candidate:a")],
        responses=[response("wu:1#generalist")],
        assessments=[assess("wu:9#ghost", 4, "keep"),
                     assess("wu:9#ghost", 5, "drop")],
    )
    assert [item.candidate_id for item in kept] == ["candidate:a"]
    assert len(report["unmatched"]) == 2


def test_a_duplicate_pointing_nowhere_does_not_delete_the_claim():
    """A duplicate of nothing is not a duplicate.

    Dropping it would delete a claim on the strength of a pointer that resolves to nothing —
    the one way `duplicate_of` could destroy a finding rather than combine two.
    """

    kept, _s, _e, report = run(
        generalist=[candidate("candidate:a")],
        responses=[response("wu:1#generalist")],
        assessments=[assess("wu:1#generalist", 0, "duplicate_of",
                            duplicate_of="wu:1#generalist#7")],
    )
    assert [item.candidate_id for item in kept] == ["candidate:a"]
    assert report["candidates_absorbed"] == 0
    assert report["unmatched"][0]["reason"].startswith("duplicate_of names no other candidate")


def test_mutual_duplicates_lose_one_side_not_both():
    """A cycle must not annihilate the anchor it describes."""

    kept, _s, _e, report = run(
        generalist=[candidate("candidate:a"), candidate("candidate:b", ordinal=1)],
        responses=[response("wu:1#generalist")],
        assessments=[
            assess("wu:1#generalist", 0, "duplicate_of", duplicate_of="wu:1#generalist#1"),
            assess("wu:1#generalist", 1, "duplicate_of", duplicate_of="wu:1#generalist#0"),
        ],
    )
    assert len(kept) == 1
    assert report["duplicate_cycles_broken"] >= 1


def test_a_severity_override_is_recorded_and_not_applied():
    """Re-grading is neither removing nor combining, and `blocking` orders the per-PR limit.

    A lead that could promote its own claims to blocking would control publication order.
    """

    kept, _s, _e, report = run(
        generalist=[candidate("candidate:a")],
        responses=[response("wu:1#generalist")],
        assessments=[assess("wu:1#generalist", 0, "keep", severity="blocking")],
    )
    assert kept[0] is not None
    assert not hasattr(kept[0], "severity")
    assert report["severity_overrides_recorded_not_applied"] == 1


def test_no_assessments_is_exactly_the_old_behaviour():
    """Every run before §3 must still be reproducible."""

    generalist = [candidate("candidate:a"), candidate("candidate:b", ordinal=1)]
    kept, _s, _e, report = run(generalist=generalist, responses=[response("wu:1#generalist")])
    assert kept == generalist
    assert report["candidates_out"] == report["candidates_in"] == 2


# --- removal is recorded, never destructive ---------------------------------------------

def test_a_removed_candidate_is_returned_not_destroyed():
    """The measured defect: seven of twelve gold-reaching candidates vanished here.

    Because they never reached `findings.jsonl`, the judge never saw them and nobody could
    say whether the lead's drops were right. Synthesis now hands them back so `finalize` can
    file them as `diagnostic`.
    """

    gone = removed(
        generalist=[candidate("candidate:a"), candidate("candidate:b", ordinal=1)],
        responses=[response("wu:1#generalist")],
        assessments=[assess("wu:1#generalist", 0, "drop", reason="a formatting nit")],
    )
    assert [c.candidate_id for c, _reason in gone] == ["candidate:a"]
    assert "a formatting nit" in gone[0][1] or "dropped" in gone[0][1]


def test_a_folded_candidate_is_returned_too():
    gone = removed(
        generalist=[candidate("candidate:a"), candidate("candidate:b", ordinal=1)],
        responses=[response("wu:1#generalist")],
        assessments=[assess("wu:1#generalist", 1, "duplicate_of",
                            duplicate_of="wu:1#generalist#0")],
    )
    assert [c.candidate_id for c, _r in gone] == ["candidate:b"]
    assert "folded into candidate:a" in gone[0][1]


def test_kept_and_removed_together_are_exactly_what_came_in():
    """Nothing is invented and nothing is silently lost — the whole point of the split."""

    everything = [candidate("candidate:a"), candidate("candidate:b", ordinal=1),
                  candidate("candidate:c", ordinal=2)]
    gen, _s, _e, gone, _report = apply_assessments(
        generalist=everything, specialist=[], evidence_specialist=[],
        responses=[response("wu:1#generalist")],
        assessments=[assess("wu:1#generalist", 0, "drop"),
                     assess("wu:1#generalist", 2, "duplicate_of",
                            duplicate_of="wu:1#generalist#1")],
    )
    assert {c.candidate_id for c in gen} | {c.candidate_id for c, _r in gone} == {
        "candidate:a", "candidate:b", "candidate:c"}
    assert len(gen) + len(gone) == 3


def test_removals_are_ordered_stably():
    """The audit trail has to be byte-stable across runs to be diffable."""

    args = dict(
        generalist=[candidate("candidate:z"), candidate("candidate:a", ordinal=1)],
        responses=[response("wu:1#generalist")],
        assessments=[assess("wu:1#generalist", 0, "drop"),
                     assess("wu:1#generalist", 1, "drop")],
    )
    assert [c.candidate_id for c, _r in removed(**args)] == ["candidate:a", "candidate:z"]
