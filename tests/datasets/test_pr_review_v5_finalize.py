"""Admission: what the system is allowed to say, and who is allowed to decide it.

The lead routes. It does not publish. These tests pin the two gates it cannot reach, plus
the property that makes the three-mode comparison fair — the deterministic arm is identical
in all of them because it involves no model call.

Both gates are *closed by default* on purpose. `generalist_findings` treats
`supported_candidate_ids=None` as "publish everything", so reaching that branch by omission
would silently convert a publication warrant into a rubber stamp for the 53% of the corpus
no collector can support.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.io import load_jsonl
from src.mathlib_review.schema import ReviewWorkUnit
from src.mathlib_review.review.finalize import finalize, ingest_responses

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")


@pytest.fixture(scope="module")
def unit():
    """A real work unit with at least one declaration target, so a claim can anchor."""

    units = load_jsonl(RELEASE / "derived/work_units.jsonl", ReviewWorkUnit)
    for candidate in units:
        change_id = candidate.change_ids[0]
        if candidate.primary_subjects_by_change.get(change_id) and \
                candidate.entity_ids_by_change.get(change_id):
            return candidate
    pytest.skip("no suitable work unit in the release")


def _candidate(unit, **overrides):
    change_id = unit.change_ids[0]
    payload = {
        "primary_change_id": change_id,
        "primary_entity_id": unit.entity_ids_by_change[change_id][0],
        "primary_subject": unit.primary_subjects_by_change[change_id],
        "change_ids": [change_id],
        "concern_family": "proof-golf",
        "issue_kind": "proof_simplification",
        "concern_label": "proof-golf",
        "severity": "advisory",
        "claim": f"The proof of {unit.primary_subjects_by_change[change_id]} can be shorter.",
        "requested_change": (
            f"Shorten the proof of {unit.primary_subjects_by_change[change_id]}."),
        "proposed_edit": {
            "path": unit.paths_by_change.get(change_id) or "Mathlib/A.lean",
            "declaration_name": "Foo.bar",
            "new_declaration": "theorem Foo.bar : True := trivial",
        },
    }
    payload.update(overrides)
    return payload


def _response(unit, arm_id, candidates, artifacts=(), spec_id=None):
    return {
        "invocation_id": f"{unit.work_unit_id}#{arm_id}",
        "arm_id": arm_id,
        "work_unit_id": unit.work_unit_id,
        "spec_id": spec_id,
        "pr_number": unit.pr_number,
        "status": "success",
        "candidates": list(candidates),
        "verification_artifacts": list(artifacts),
    }


def _artifact(unit, ordinal, success=True):
    return {
        "schema_version": "residual-candidate-verification1",
        "artifact_id": f"residual-candidate-verification:{ordinal:024d}",
        "work_unit_id": unit.work_unit_id,
        "candidate_ordinal": ordinal,
        "stage": "proposed_edit",
        "kind": "lean_compile",
        "success": success,
        "path": "Mathlib/A.lean",
        "content": "compiled",
        "snapshot_sha": "abc",
        "source_sha256": "d" * 64,
    }


def test_ingestion_splits_by_arm_and_takes_spec_from_the_invocation(unit):
    """A model is not trusted to say which agent it is: golf and idiom both declare
    `proof_simplification`, and the verifier keys its warrant on the spec."""

    generalist, specialist, evidence_specialist, artifacts, rejections = ingest_responses(
        [unit],
        [
            _response(unit, "generalist", [_candidate(unit)]),
            _response(unit, "proof_golf", [_candidate(unit)], [_artifact(unit, 0)],
                      spec_id="proof_golf"),
        ],
    )
    assert len(generalist) == 1 and generalist[0].spec_id is None
    assert len(specialist) == 1 and specialist[0].spec_id == "proof_golf"
    assert len(artifacts) == 1 and not rejections


def test_a_failed_job_contributes_nothing(unit):
    generalist, specialist, _evidence, _artifacts, _rejections = ingest_responses(
        [unit], [dict(_response(unit, "proof_golf", [_candidate(unit)]), status="failed")])
    assert not generalist and not specialist


def test_one_malformed_candidate_does_not_sink_the_batch(unit):
    """Raising would discard every other candidate and leave the drop rate unmeasurable,
    which makes the system look more precise than it is."""

    good, bad = _candidate(unit), _candidate(unit, change_ids=["change:nonexistent"])
    generalist, _spec, _evidence, _artifacts, rejections = ingest_responses(
        [unit], [_response(unit, "generalist", [good, bad])])
    assert len(generalist) == 1
    assert len(rejections) == 1


def test_generalist_claims_cannot_publish_without_evidence(unit, tmp_path):
    """The gate the lead cannot reach. Retained and counted, never published."""

    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "generalist", [_candidate(unit)])],
    )
    assert report["candidates_generalist"] == 1
    assert report["generalist_evidence_gate"] == "closed"
    issues = [json.loads(x) for x in
              (tmp_path / "run" / "issues.jsonl").read_text().splitlines() if x.strip()]
    assert issues, "the claim is retained"
    assert all(item["admission"] != "published" for item in issues)


def test_a_specialist_claim_without_a_verification_artifact_is_dropped(unit, tmp_path):
    """Dropped, not downgraded. Downgrading would smuggle an unverified claim into the one
    arm whose entire premise is that the compiler agreed."""

    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "proof_golf", [_candidate(unit)], spec_id="proof_golf")],
    )
    assert report["candidates_specialist"] == 1
    assert report["issues_total"] == 0


def test_a_specialist_claim_with_a_failed_artifact_is_dropped(unit, tmp_path):
    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "proof_golf", [_candidate(unit)],
                             [_artifact(unit, 0, success=False)], spec_id="proof_golf")],
    )
    assert report["issues_total"] == 0


def test_a_verified_specialist_claim_publishes(unit, tmp_path):
    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "proof_golf", [_candidate(unit)],
                             [_artifact(unit, 0)], spec_id="proof_golf")],
    )
    assert report["issues_published"] >= 1


def test_the_lead_assessment_changes_nothing(unit, tmp_path):
    """v1 records arbitration and applies none of it. `finalize` has no parameter through
    which an assessment could reach admission — this pins that absence."""

    import inspect

    assert "assessment" not in inspect.signature(finalize).parameters
    responses = [_response(unit, "proof_golf", [_candidate(unit)], [_artifact(unit, 0)],
                           spec_id="proof_golf")]
    first = finalize(tmp_path / "a", units=[unit], routing_mode="lead", responses=responses)
    second = finalize(tmp_path / "b", units=[unit], routing_mode="fanout", responses=responses)
    assert first["issues_sha256"] == second["issues_sha256"]


def test_routing_mode_does_not_change_the_assembler(unit, tmp_path):
    """Identical arm output must produce identical issues in every mode, or a comparison
    between modes is measuring two assemblers rather than two routers."""

    responses = [
        _response(unit, "generalist", [_candidate(unit)]),
        _response(unit, "proof_golf", [_candidate(unit)], [_artifact(unit, 0)],
                  spec_id="proof_golf"),
    ]
    digests = {
        mode: finalize(tmp_path / mode, units=[unit], routing_mode=mode,
                       responses=responses)["issues_sha256"]
        for mode in ("fanout", "rules", "lead")
    }
    assert len(set(digests.values())) == 1


def test_a_response_for_an_unknown_work_unit_is_skipped(unit, tmp_path):
    other = unit.model_copy(update={"work_unit_id": "wu:not-in-this-run"})
    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(other, "generalist", [_candidate(unit)])],
    )
    assert report["candidates_generalist"] == 0


def test_dropped_specialist_candidates_are_counted_not_just_dropped(unit, tmp_path):
    """`focused_findings` drops any specialist claim with no successful verification
    artifact — correctly, but silently. A run where every specialist claim evaporated then
    looks exactly like a run where the specialists found nothing, which is a very different
    fact about the system."""

    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "generality", [_candidate(unit)], spec_id="generality")],
    )
    assert report["candidates_specialist"] == 1
    assert report["candidates_specialist_dropped_unverified"] == 1
    assert report["dropped_unverified_by_concern"]
    assert report["issues_total"] == 0


def test_a_verified_specialist_candidate_is_not_counted_as_dropped(unit, tmp_path):
    report = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "proof_golf", [_candidate(unit)],
                             [_artifact(unit, 0)], spec_id="proof_golf")],
    )
    assert report["candidates_specialist_dropped_unverified"] == 0


# --- §4: the evidence chain, and the gate the lead still cannot reach -------------------

def test_the_gate_reports_which_regime_it_ran_under(unit, tmp_path):
    """`closed` and `evidence_chain` are different claims about a diagnostic finding.

    Under `closed`, nothing was asked to support anything, so `diagnostic` says only that no
    chain ran. Eight runs reported publication rates under that regime as if they were
    strictness results. The report has to name the regime or the number is unreadable.
    """

    summary = finalize(
        tmp_path / "closed", units=[unit], routing_mode="lead",
        responses=[_response(unit, "generalist", [_candidate(unit)])],
    )
    assert summary["generalist_evidence_gate"] == "closed"

    summary = finalize(
        tmp_path / "chained", units=[unit], routing_mode="lead",
        responses=[_response(unit, "generalist", [_candidate(unit)])],
        collect_supported=lambda candidates: set(),
    )
    assert summary["generalist_evidence_gate"] == "evidence_chain"


def test_the_chain_sees_the_candidates_whose_admission_depends_on_it(unit, tmp_path):
    """Generalist and non-compile specialists go to the chain; compile-gated ones do not.

    Putting the compile-gated arms through it would cost a baseline compile each and could
    not change their admission, which `focused_findings` decides from their artifacts.
    """

    seen = {}

    def collect(candidates):
        seen["families"] = sorted(item.concern_family for item in candidates)
        return set()

    finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[
            _response(unit, "generalist", [_candidate(unit, concern_family="documentation",
                                                      issue_kind="documentation_gap")]),
            _response(unit, "naming", [_candidate(unit, concern_family="naming",
                                                  issue_kind="naming_convention_violation")],
                      spec_id="naming"),
            _response(unit, "proof_golf", [_candidate(unit)],
                      artifacts=[_artifact(unit, 0)], spec_id="proof_golf"),
        ],
        collect_supported=collect,
    )
    assert seen["families"] == ["documentation", "naming"]


def test_a_supported_candidate_publishes_and_an_unsupported_one_stays_diagnostic(
    unit, tmp_path
):
    subject = unit.primary_subjects_by_change[unit.change_ids[0]]
    responses = [_response(unit, "generalist", [
        _candidate(unit, claim=f"{subject} A.", concern_family="documentation",
                   issue_kind="documentation_gap", requested_change=f"Document {subject}."),
        _candidate(unit, claim=f"{subject} B.", concern_family="style",
                   issue_kind="style_norm_violation", requested_change=f"Restyle {subject}."),
    ])]
    generalist, _s, _e, _a, _r = ingest_responses([unit], responses)
    supported = {generalist[0].candidate_id}

    summary = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead", responses=responses,
        collect_supported=lambda candidates: supported,
    )
    findings = [json.loads(line) for line in
                (tmp_path / "run" / "findings.jsonl").read_text().splitlines() if line.strip()]
    admissions = {item["claim"][-2]: item["admission"] for item in findings}
    assert admissions == {"A": "published", "B": "diagnostic"}


def test_an_assessment_cannot_promote_a_candidate_the_chain_did_not_support(unit, tmp_path):
    """The load-bearing test for §3 and §4 together.

    A lead that could talk a finding past the evidence chain would make every published
    finding mean less. `keep` is agreement, not a warrant.
    """

    responses = [_response(unit, "generalist", [_candidate(unit)])]
    summary = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead", responses=responses,
        candidate_assessments=[{
            "invocation_id": f"{unit.work_unit_id}#generalist",
            "candidate_ordinal": 0, "verdict": "keep", "severity": "blocking",
            "reason": "I am confident about this one.",
        }],
        collect_supported=lambda candidates: set(),
    )
    assert summary["issues_published"] == 0
    findings = [json.loads(line) for line in
                (tmp_path / "run" / "findings.jsonl").read_text().splitlines() if line.strip()]
    assert [item["admission"] for item in findings] == ["diagnostic"]


def test_an_assessment_cannot_attach_a_compile_warrant(unit, tmp_path):
    """A specialist claim with no successful artifact is dropped, and `keep` does not save it."""

    summary = finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "proof_golf", [_candidate(unit)],
                             artifacts=[_artifact(unit, 0, success=False)],
                             spec_id="proof_golf")],
        candidate_assessments=[{
            "invocation_id": f"{unit.work_unit_id}#proof_golf",
            "candidate_ordinal": 0, "verdict": "keep", "reason": "it is right anyway",
        }],
        collect_supported=lambda candidates: set(),
    )
    assert summary["candidates_specialist_dropped_unverified"] == 1
    assert summary["issues_published"] == 0


def test_a_dropped_candidate_never_reaches_the_chain(unit, tmp_path):
    """Synthesis is subtractive and runs first, so the expensive part is not spent
    adjudicating a claim nobody stands by."""

    seen = []
    finalize(
        tmp_path / "run", units=[unit], routing_mode="lead",
        responses=[_response(unit, "generalist", [
            _candidate(unit, claim=f"{unit.primary_subjects_by_change[unit.change_ids[0]]} A.",
                       requested_change="Do the first thing."),
            _candidate(unit, claim=f"{unit.primary_subjects_by_change[unit.change_ids[0]]} B.",
                       requested_change="Do the second thing."),
        ])],
        candidate_assessments=[{
            "invocation_id": f"{unit.work_unit_id}#generalist",
            "candidate_ordinal": 1, "verdict": "drop", "reason": "restates the first",
        }],
        collect_supported=lambda candidates: seen.extend(candidates) or set(),
    )
    assert len(seen) == 1
    assert seen[0].claim.endswith("A.")


def test_the_evidence_summary_reaches_the_written_report(unit, tmp_path):
    """It was attached to the returned dict after the file was written, so it never landed.

    `write_once` will not rewrite `finalization_report.json`, so anything a caller adds to
    the returned summary is invisible to every reader of the run.
    """

    out = tmp_path / "run"
    finalize(
        out, units=[unit], routing_mode="lead",
        responses=[_response(unit, "generalist", [_candidate(unit)])],
        collect_supported=lambda candidates: set(),
    )
    written = json.loads((out / "finalization_report.json").read_text())
    assert "evidence" in written


# --- Stage 0: the lead's removals survive as audit trail --------------------------------

def test_a_dropped_candidate_appears_as_a_diagnostic_finding(unit, tmp_path):
    """It must reach `findings.jsonl`, which is what the judge reads.

    On heldout11 rep2 seven of the twelve candidates that landed on a gold obligation's site
    were deleted here, so nobody could tell a good drop from a bad one.
    """

    out = tmp_path / "run"
    subject = unit.primary_subjects_by_change[unit.change_ids[0]]
    summary = finalize(
        out, units=[unit], routing_mode="lead", pr_numbers=[unit.pr_number],
        responses=[_response(unit, "generalist", [
            _candidate(unit, claim=f"{subject} A.", requested_change="Do the first thing."),
            _candidate(unit, claim=f"{subject} B.", requested_change="Do the second thing."),
        ])],
        candidate_assessments=[{
            "invocation_id": f"{unit.work_unit_id}#generalist",
            "candidate_ordinal": 1, "verdict": "drop", "reason": "a formatting nit",
        }],
        collect_supported=lambda candidates: set(),
    )
    findings = [json.loads(line) for line in
                (out / "findings.jsonl").read_text().splitlines() if line.strip()]
    assert len(findings) == 2
    dropped = [f for f in findings if f["claim"].endswith("B.")]
    assert len(dropped) == 1
    assert dropped[0]["admission"] == "diagnostic"
    assert "removed by the lead" in dropped[0]["admission_reason"]
    assert summary["lead_removed_findings"] == 1


def test_a_removed_finding_never_reaches_the_review(unit, tmp_path):
    """`issues.jsonl` is what a maintainer would see, and the lead's judgment governs it."""

    out = tmp_path / "run"
    subject = unit.primary_subjects_by_change[unit.change_ids[0]]
    finalize(
        out, units=[unit], routing_mode="lead", pr_numbers=[unit.pr_number],
        responses=[_response(unit, "generalist", [
            _candidate(unit, claim=f"{subject} A.", requested_change="Do the first thing."),
            _candidate(unit, claim=f"{subject} B.", requested_change="Do the second thing."),
        ])],
        candidate_assessments=[{
            "invocation_id": f"{unit.work_unit_id}#generalist",
            "candidate_ordinal": 1, "verdict": "drop", "reason": "noise",
        }],
        collect_supported=lambda candidates: set(),
    )
    issues = [json.loads(line) for line in
              (out / "issues.jsonl").read_text().splitlines() if line.strip()]
    assert not any(i["claim"].endswith("B.") for i in issues)


def test_a_folded_candidate_does_not_resurrect_the_conflict(unit, tmp_path):
    """The load-bearing exclusion.

    `merge_findings` demotes *both* sides of an equal-warrant clash at one anchor, so
    re-entering a folded finding into the merge would undo exactly what `duplicate_of` was
    built to fix. It is appended after the merge, never into it.
    """

    out = tmp_path / "run"
    subject = unit.primary_subjects_by_change[unit.change_ids[0]]
    summary = finalize(
        out, units=[unit], routing_mode="lead", pr_numbers=[unit.pr_number],
        responses=[_response(unit, "generalist", [
            _candidate(unit, claim=f"{subject} rename it.", concern_family="naming",
                       issue_kind="naming_convention_violation",
                       requested_change=f"Rename {subject}."),
            _candidate(unit, claim=f"{subject} fix its docstring.", concern_family="naming",
                       issue_kind="naming_convention_violation",
                       requested_change=f"Document {subject}."),
        ])],
        candidate_assessments=[{
            "invocation_id": f"{unit.work_unit_id}#generalist",
            "candidate_ordinal": 1, "verdict": "duplicate_of",
            "duplicate_of": f"{unit.work_unit_id}#generalist#0",
        }],
        collect_supported=lambda candidates: set(),
    )
    assert summary["conflicts"] == 0
    assert summary["lead_removed_findings"] == 1


def test_the_discovery_record_holds_every_candidate_any_arm_submitted(unit, tmp_path):
    """Immutable, and written before synthesis touches anything."""

    out = tmp_path / "run"
    subject = unit.primary_subjects_by_change[unit.change_ids[0]]
    finalize(
        out, units=[unit], routing_mode="lead", pr_numbers=[unit.pr_number],
        responses=[_response(unit, "generalist", [
            _candidate(unit, claim=f"{subject} A.", requested_change="First."),
            _candidate(unit, claim=f"{subject} B.", requested_change="Second."),
        ])],
        candidate_assessments=[{
            "invocation_id": f"{unit.work_unit_id}#generalist",
            "candidate_ordinal": 0, "verdict": "drop", "reason": "noise",
        }],
        collect_supported=lambda candidates: set(),
    )
    discovered = [json.loads(line) for line in
                  (out / "candidates_discovered.jsonl").read_text().splitlines() if line.strip()]
    assert len(discovered) == 2


def test_a_dropped_candidate_still_never_reaches_the_evidence_chain(unit, tmp_path):
    """Restoring the record must not restore the spend: the chain is the expensive part."""

    seen = []
    subject = unit.primary_subjects_by_change[unit.change_ids[0]]
    finalize(
        tmp_path / "run", units=[unit], routing_mode="lead", pr_numbers=[unit.pr_number],
        responses=[_response(unit, "generalist", [
            _candidate(unit, claim=f"{subject} A.", requested_change="First."),
            _candidate(unit, claim=f"{subject} B.", requested_change="Second."),
        ])],
        candidate_assessments=[{
            "invocation_id": f"{unit.work_unit_id}#generalist",
            "candidate_ordinal": 1, "verdict": "drop", "reason": "noise",
        }],
        collect_supported=lambda candidates: seen.extend(candidates) or set(),
    )
    assert len(seen) == 1
    assert seen[0].claim.endswith("A.")


# --- the lead's judgment can be recorded without being applied -------------------------------
#
# `pr5_smoke4_rep9` was the first run to apply it: 54 candidates became 27 issues, and of the
# six obligations the run hit, **two are hit only by a candidate the lead removed**. Four of
# the five gold-matching removals were `duplicate_of` folds into a representative that did not
# itself match, so folding -- which is meant to be lossless -- was not. rep6 and rep7 recorded
# assessments and applied none, and scored 6 and 7 issue hits against rep9's 6.


def _assessment(unit, ordinal=0, verdict="drop"):
    return {"schema_version": "v5-assessment1",
            "invocation_id": f"{unit.work_unit_id}#proof_golf",
            "candidate_ordinal": ordinal, "verdict": verdict, "reason": "not worth it"}


def test_synthesis_can_be_recorded_without_being_applied(unit, tmp_path):
    responses = [_response(unit, "proof_golf", [_candidate(unit)], [_artifact(unit, 0)],
                           spec_id="proof_golf")]
    assessments = [_assessment(unit)]

    applied = finalize(tmp_path / "on", units=[unit], routing_mode="lead",
                       responses=responses, candidate_assessments=assessments,
                       apply_lead_synthesis=True)
    recorded = finalize(tmp_path / "off", units=[unit], routing_mode="lead",
                        responses=responses, candidate_assessments=assessments,
                        apply_lead_synthesis=False)

    assert applied["lead_removed_findings"] == 1
    assert recorded["lead_removed_findings"] == 0
    assert recorded["issues_total"] > applied["issues_total"]


def test_the_assessments_are_still_counted_when_not_applied(unit, tmp_path):
    """The question under investigation is whether the lead's judgment is good, and answering
    that needs the judgments whether or not they are acted on."""

    report = finalize(tmp_path / "r", units=[unit], routing_mode="lead",
                      responses=[_response(unit, "proof_golf", [_candidate(unit)],
                                           [_artifact(unit, 0)], spec_id="proof_golf")],
                      candidate_assessments=[_assessment(unit)],
                      apply_lead_synthesis=False)
    synthesis = report["lead_synthesis"]
    assert synthesis["applied"] is False
    assert synthesis["assessments"] == 1
    assert synthesis["by_verdict"] == {"drop": 1}


def test_the_setting_is_sealed_in_the_run_plan():
    """It changes what reaches the maintainer-facing review, so two runs that differ on it are
    not comparable -- which is exactly what `evaluation_settings` is for."""

    import inspect

    from src.mathlib_review.review import runner

    source = inspect.getsource(runner._build_plan)
    assert '"apply_lead_synthesis": dataset.apply_lead_synthesis' in source


def test_it_is_off_by_default_while_under_investigation():
    from src.mathlib_review.review.runner import V5DatasetConfig

    assert V5DatasetConfig.model_fields["apply_lead_synthesis"].default is False
