"""The ensemble's union: identical asks collapse, agreement is a label, nothing is suppressed.

Layer 2 of `docs/plans/2026-10-01-beyond-the-solo-baseline.md` unions K passes' findings and
keeps how many passes agreed as a label. The boundary it must not cross is selection
(`.claude/rules/mathlib-review.md`): `merge_findings`' suppression step demotes alternatives at
one anchor, resolves by warrant and truncates per PR, and each of those decides which findings
reach a maintainer. The union reuses the merge's grouping and none of that.
"""

from __future__ import annotations

import inspect
import json

import pytest

from src.mathlib_review.io import load_jsonl
from src.mathlib_review.review import cli
from src.mathlib_review.review.merge import (
    finding_from_candidate, merge_findings, union_findings, write_union_run,
)
from src.mathlib_review.schema import CandidateClaim, ReviewFinding


def _finding(cid, requested, *, change="change:1", family="naming",
             kind="naming_convention_violation", pr=1, channels=("review",)):
    candidate = CandidateClaim(
        candidate_id=cid, work_unit_id="w", episode_id="e1", pr_number=pr,
        change_ids=[change], primary_change_id=change, concern_family=family,
        concern_label=family, issue_kind=kind, severity="advisory", claim="c",
        requested_change=requested, evidence_requests=[], source_sha256=f"h-{cid}")
    finding = finding_from_candidate(
        candidate, admission="published", admission_reason="filed")
    return finding.model_copy(update={"channels": list(channels)})


def test_identical_asks_collapse_and_different_asks_at_one_anchor_both_survive():
    """Where `merge_findings` sees a conflict -- two asks at one anchor and family with equal
    warrant -- and demotes both, the union keeps both. Only the identical sentence folds."""

    a_same = _finding("candidate:a1", "Rename the lemma.")
    b_same = _finding("candidate:b1", "rename   the lemma.")      # case and whitespace only
    b_other = _finding("candidate:b2", "Move it to the `Foo` namespace.")
    findings, report = union_findings({"a": [a_same], "b": [b_same, b_other]})

    assert len(findings) == 2
    assert report["inputs"] == 3 and report["collapsed_identical_asks"] == 1
    folded = next(f for f in findings if f.requested_change == "Rename the lemma.")
    assert {s.candidate_id for s in folded.sources} == {"candidate:a1", "candidate:b1"}
    assert report["members"][folded.finding_id] == [
        {"run": "a", "finding_id": a_same.finding_id},
        {"run": "b", "finding_id": b_same.finding_id}]
    # Admission is carried from the source run's own merge, not recomputed.
    assert {f.admission for f in findings} == {"published"}

    merged, conflicts, _report = merge_findings([a_same, b_same, b_other])
    assert conflicts and {f.admission for f in merged} == {"diagnostic"}


def test_agreement_is_a_label_on_the_claim_identity():
    """`passes_agreeing` counts the runs that filed something of the same `finding_key` -- site
    and issue kind -- because the full action key recurs essentially never across runs
    (6 of 375 on the four Opus passes). Two different asks at one site and kind agree at 2;
    a finding alone agrees at 1. Nothing is cut on it."""

    findings, report = union_findings({
        "a": [_finding("candidate:a1", "Rename the lemma.")],
        "b": [_finding("candidate:b1", "Rename it `foo_bar`.")],
        "c": [_finding("candidate:c1", "Golf the proof.", change="change:2",
                       family="proof-golf", kind="proof_simplification")],
    })
    by_text = {f.requested_change: f for f in findings}
    assert by_text["Rename the lemma."].passes == ["a", "b"]
    assert by_text["Rename the lemma."].passes_agreeing == 2
    assert by_text["Rename it `foo_bar`."].passes == ["a", "b"]
    assert by_text["Golf the proof."].passes == ["c"]
    assert by_text["Golf the proof."].passes_agreeing == 1
    assert report["k_identical_ask"] == {"1": 3}
    assert report["k_site_and_kind"] == {"1": 1, "2": 2}
    assert report["k_site_and_kind_keys"] == {"1": 1, "2": 1}
    assert len(findings) == 3, "the label is a label: nothing was dropped on it"


def test_the_union_never_runs_the_suppression_step():
    """Structural: the suppression lives in `merge_findings`, and the union must not reach it.
    Every input finding is accounted for in `members`, so a quiet drop would show as a count."""

    source = inspect.getsource(union_findings) + inspect.getsource(write_union_run)
    assert "merge_findings(" not in source
    assert "pr_finding_limit" not in source and "suppressed" not in source

    runs = {"a": [_finding("candidate:a1", "x"), _finding("candidate:a2", "y", change="change:2")],
            "b": [_finding("candidate:b1", "x"), _finding("candidate:b2", "z")]}
    findings, report = union_findings(runs)
    assert sum(len(rows) for rows in report["members"].values()) == report["inputs"] == 4
    assert len(findings) == report["union"] == 3


def test_only_the_review_channel_is_unioned_and_the_rest_is_counted():
    findings, report = union_findings({
        "a": [_finding("candidate:a1", "x"), _finding("candidate:a2", "y", channels=())]})
    assert len(findings) == 1
    assert report["dropped_not_in_review_channel"] == 1
    assert report["findings_per_run"] == {"a": 2} and report["inputs"] == 1


def test_control_pr_findings_are_counted_per_run_and_in_the_union():
    """The price of a union adds up on the PRs where maintainers asked for nothing; the report
    says it per pass and after the fold, which is the number the reading rule reads."""

    _findings, report = union_findings({
        "a": [_finding("candidate:a1", "x", pr=33304)],
        "b": [_finding("candidate:b1", "x", pr=33304), _finding("candidate:b2", "y", pr=33315)],
    }, control_pr_numbers=[33304, 33315])
    assert report["control_findings"] == {"33304": 1, "33315": 1}
    assert report["control_findings_per_run"] == {
        "a": {"33304": 1, "33315": 0}, "b": {"33304": 1, "33315": 1}}


# --- the derived run -------------------------------------------------------------------------


def _source_run(root, name, findings, status="complete"):
    out = root / name
    out.mkdir()
    (out / "findings.jsonl").write_text(
        "".join(json.dumps(f.model_dump(mode="json")) + "\n" for f in findings), encoding="utf-8")
    (out / "run_manifest.json").write_text(
        json.dumps({"run_name": name, "completion_status": status, "coverage_gaps": []}),
        encoding="utf-8")
    return out


def test_write_union_run_writes_a_derived_run_the_judge_reads_as_unchecked(tmp_path, monkeypatch):
    """No manifest and no agenda, because nothing ran: the judge's `StageInput` reads such a run
    as unchecked rather than refusing it. What it does have is a `union` row naming every source
    digest, and a report. Regenerating from the same sources is a no-op, with no second row."""

    from src.mathlib_review import paths
    from src.mathlib_review.run_state import StageInput, ledger

    monkeypatch.setattr(paths, "RUNS", tmp_path)
    _source_run(tmp_path, "rep1", [_finding("candidate:a1", "x")])
    _source_run(tmp_path, "rep2", [_finding("candidate:b1", "x"), _finding("candidate:b2", "y")])

    out = write_union_run(["rep1", "rep2"], "union_v1", control_pr_numbers=[7])
    assert out["written"] is True and out["union"] == 2 and "members" not in out

    derived = tmp_path / "union_v1"
    findings = load_jsonl(derived / "findings.jsonl", ReviewFinding)
    assert [f.passes_agreeing for f in findings] == [2, 2]
    report = json.loads((derived / "union_report.json").read_text(encoding="utf-8"))
    assert report["derived_run"] == "union_v1"
    assert report["sources"]["rep1"]["completion_status"] == "complete"
    assert set(report["members"]) == {f.finding_id for f in findings}

    rows = ledger(derived)
    assert [row["stage"] for row in rows] == ["union"]
    assert set(rows[0]["consumed"]) == {"rep1/findings", "rep2/findings"}
    assert rows[0]["identity"]["source_runs"] == ["rep1", "rep2"]
    assert any(path.endswith("findings.jsonl") for path in rows[0]["produced"])

    stage = StageInput.at(derived, require=("findings",))
    assert stage.unchecked and not stage.forensic

    again = write_union_run(["rep1", "rep2"], "union_v1", control_pr_numbers=[7])
    assert again["written"] is False
    assert [row["stage"] for row in ledger(derived)] == ["union"]


def test_a_derived_name_is_bound_to_its_sources(tmp_path, monkeypatch):
    """The same name from different passes is refused, not quietly rebuilt: every knob that
    changes what a run holds goes into the run name."""

    from src.mathlib_review import paths

    monkeypatch.setattr(paths, "RUNS", tmp_path)
    _source_run(tmp_path, "rep1", [_finding("candidate:a1", "x")])
    _source_run(tmp_path, "rep2", [_finding("candidate:b1", "y")])
    _source_run(tmp_path, "rep3", [_finding("candidate:c1", "z")])
    write_union_run(["rep1", "rep2"], "union_v1")
    with pytest.raises(FileExistsError):
        write_union_run(["rep1", "rep3"], "union_v1")


def test_a_partial_pass_is_refused(tmp_path, monkeypatch):
    """A pass that did not cover what it promised would union in its silences."""

    from src.mathlib_review import paths

    monkeypatch.setattr(paths, "RUNS", tmp_path)
    _source_run(tmp_path, "rep1", [_finding("candidate:a1", "x")])
    _source_run(tmp_path, "rep2", [_finding("candidate:b1", "y")], status="partial")
    with pytest.raises(ValueError, match="closed as 'partial'"):
        write_union_run(["rep1", "rep2"], "union_v1")
    with pytest.raises(ValueError, match="two or more distinct"):
        write_union_run(["rep1", "rep1"], "union_v2")
    with pytest.raises(ValueError, match="its own sources"):
        write_union_run(["rep1", "rep2"], "rep1")


def test_report_union_is_reachable_and_calls_no_model():
    args = cli.build_parser().parse_args(
        ["report", "union", "--runs", "a,b", "--as", "u", "--control-pr", "33304"])
    assert args.report_command == "union"
    assert args.runs == "a,b" and args.derived == "u" and args.control_pr_numbers == [33304]
    assert "report" not in cli.SPENDS
