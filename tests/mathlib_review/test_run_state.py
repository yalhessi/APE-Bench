"""The run state machine, and the property it exists to hold.

Every transition here was already enforced somewhere -- `TaskExecutionStatus` in the
orchestrator, `completion_status` on the manifest, the judge's refusal to score an incomplete
run. What did not exist was a place that states the machine, so the guarantee had to be
assembled by reading three files and hoping they agreed.

These tests also pin the agreement, which is the part that would rot: the manifest's own
vocabulary is `complete` / `partial` / `failed`, and it is deliberately not renamed.
"""

from __future__ import annotations

import pytest

from src.mathlib_review.run_state import (
    SCOREABLE, TRANSITIONS, IllegalTransition, RunState, assert_transition, from_manifest,
)


def test_paused_is_not_partial():
    """The distinction that voided two September runs. `paused` stopped on a limit and can
    resume; `partial` is closed and cannot satisfy required coverage, so its recall is measured
    against a denominator including units nobody looked at."""

    assert RunState.PAUSED in TRANSITIONS[RunState.RUNNING]
    assert RunState.PARTIAL in TRANSITIONS[RunState.RUNNING]
    # Resumable.
    assert TRANSITIONS[RunState.PAUSED] == frozenset({RunState.RUNNING})
    # Closed.
    assert TRANSITIONS[RunState.PARTIAL] == frozenset()


def test_a_partial_run_never_enters_the_successful_chain():
    for target in (RunState.GENERATED, RunState.FINALIZED, RunState.JUDGED):
        with pytest.raises(IllegalTransition):
            assert_transition(RunState.PARTIAL, target)


def test_a_resume_goes_back_to_running_not_straight_to_a_verdict():
    """What closes a run is reconciliation, and that only happens after work stops."""

    assert_transition(RunState.PAUSED, RunState.RUNNING)
    with pytest.raises(IllegalTransition):
        assert_transition(RunState.PAUSED, RunState.GENERATED)


def test_only_a_closed_covered_run_is_scoreable():
    assert SCOREABLE == frozenset({RunState.GENERATED, RunState.FINALIZED})
    assert RunState.PARTIAL not in SCOREABLE
    assert RunState.PAUSED not in SCOREABLE


def test_the_error_says_what_the_legal_moves_are():
    """"Illegal transition" alone tells you nothing you can act on."""

    with pytest.raises(IllegalTransition) as excinfo:
        assert_transition(RunState.PLANNED, RunState.JUDGED)
    message = str(excinfo.value)
    assert "planned -> judged" in message
    assert "running" in message


def test_the_manifest_vocabulary_maps_on_without_being_renamed():
    """`complete` / `partial` / `failed` are in every manifest in the tree. Renaming them to
    say the same thing in different words would make old runs unreadable."""

    assert from_manifest("complete") is RunState.GENERATED
    assert from_manifest("partial") is RunState.PARTIAL
    assert from_manifest("failed") is RunState.FAILED
    # An unknown status is not silently optimistic.
    assert from_manifest("something-new") is RunState.FAILED


def test_the_manifest_states_and_the_machine_agree():
    """The manifest's `Literal` is the source of the strings; every one must map."""

    from src.mathlib_review.schema.runs import RunManifest

    declared = set(RunManifest.model_fields["completion_status"].annotation.__args__)
    for status in declared:
        assert isinstance(from_manifest(status), RunState), status


def test_every_state_is_reachable_from_planned():
    """A state nothing can reach is a state that does not exist, and would be a lie in the
    diagram."""

    seen, frontier = {RunState.PLANNED}, [RunState.PLANNED]
    while frontier:
        for nxt in TRANSITIONS.get(frontier.pop(), frozenset()):
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    assert seen == set(RunState)


def test_the_judge_asks_the_machine_rather_than_comparing_a_string():
    """The machine is only worth having if it is the thing consulted. A literal `== "complete"`
    in the judge would be a second place that has to agree with it, and nothing would check."""

    import inspect

    from src.mathlib_review.judge import runner

    # The refusal moved into `StageInput.at`, which is where every stage now asks it -- so the
    # judge asks the machine through one hop rather than restating the rule.
    from src.mathlib_review.run_state import StageInput

    assert "SCOREABLE" in inspect.getsource(StageInput.at)
    assert '== "complete"' not in inspect.getsource(runner)
    assert "StageInput" in inspect.getsource(runner.source_run)


# --- StageInput: what a stage reads, and what it records having read -----------------------


import itertools
from pathlib import Path

from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, sha256_file
from src.mathlib_review.run_state import (
    AUDIT_ARTIFACTS, RUN_ARTIFACTS, MissingArtifact, StageInput, state_of,
)


_PROBE = itertools.count()


def _run(tmp_path, *, status="complete", findings=True, plan=True, agenda=True):
    """A run directory with exactly the artifacts named, and nothing else.

    A fresh directory per call: two runs in one test must not inherit each other's artifacts,
    which is the whole property `state_of` is being asked about.
    """

    directory = tmp_path / f"pr5_probe_rep{next(_PROBE)}"
    directory.mkdir(parents=True, exist_ok=True)
    if agenda:
        (directory / "agenda.json").write_bytes(canonical_json_bytes(
            {"release": "inputs/pr_review_v4/releases/dev-medium-0.3.0"}))
    if plan:
        (directory / "run_plan.json").write_bytes(canonical_json_bytes({"run_name": "probe"}))
    if status:
        (directory / "run_manifest.json").write_bytes(canonical_json_bytes(
            {"run_name": "pr5_probe_rep1", "completion_status": status}))
    if findings:
        (directory / "findings.jsonl").write_bytes(jsonl_bytes([{"finding_id": "finding:a"}]))
    (directory / "agenda_report.json").write_bytes(canonical_json_bytes({"pr_numbers": [1]}))
    return directory


def test_a_sealed_but_unclosed_run_is_running_not_planned(tmp_path):
    """A plan with no manifest is a run that started and did not close. `PAUSED` would be a
    claim about resumability that only the samples can support."""

    assert state_of(_run(tmp_path, status=None)) is RunState.RUNNING
    assert state_of(tmp_path / "nothing-here") is RunState.PLANNED


def test_finalized_is_generated_plus_findings(tmp_path):
    """`finalize` runs BEFORE `reconcile` writes the manifest, so a partial run has findings
    too -- which is why `FINALIZED` cannot be read off the manifest alone, and why it is
    reserved for a run that also covered what it promised."""

    assert state_of(_run(tmp_path, findings=False)) is RunState.GENERATED
    assert state_of(_run(tmp_path, findings=True)) is RunState.FINALIZED
    assert state_of(_run(tmp_path, status="partial", findings=True)) is RunState.PARTIAL


def test_judged_comes_from_a_ledger_row_not_from_an_audit_existing(tmp_path):
    """An audit directory can be written by hand, and `--allow-partial` writes one deliberately
    marked forensic. Only a non-forensic row from the judge stage means the run was scored."""

    directory = _run(tmp_path)
    (directory / "stages.jsonl").write_bytes(jsonl_bytes([
        {"stage": "judge", "forensic": True, "run_name": "pr5_probe_rep1"}]))
    assert state_of(directory) is RunState.FINALIZED
    with (directory / "stages.jsonl").open("ab") as handle:
        handle.write(canonical_json_bytes(
            {"stage": "judge", "forensic": False, "run_name": "pr5_probe_rep1"}) + b"\n")
    assert state_of(directory) is RunState.JUDGED


def test_a_partial_run_is_refused_unless_it_is_asked_for(tmp_path):
    directory = _run(tmp_path, status="partial")
    with pytest.raises(ValueError) as error:
        StageInput.at(directory)
    assert "partial" in str(error.value) and "forensic" in str(error.value)
    stage = StageInput.at(directory, allow_partial=True)
    assert stage.forensic is True


def test_only_the_required_artifacts_are_hashed(tmp_path):
    """`context_trace.jsonl` runs to tens of megabytes and one reader needs it. Hashing
    everything by default would make every stage pay for the most expensive reader."""

    directory = _run(tmp_path)
    stage = StageInput.at(directory, require=("findings", "agenda_report"))
    assert set(stage.consumed) == {"findings", "agenda_report"}
    assert stage.consumed["findings"] == sha256_file(directory / "findings.jsonl")


def test_a_missing_artifact_names_the_stage_that_writes_it(tmp_path):
    """"No such file" three frames into a join is how an unlinked arm pool read as an empty
    run. The refusal says whose output it is, and carries the hint where there is one."""

    directory = _run(tmp_path)
    with pytest.raises(MissingArtifact) as error:
        StageInput.at(directory).path("arm_pool")
    message = str(error.value)
    assert "written by the `run` stage" in message
    assert "gitignored" in message and "worktree" in message


def test_the_release_comes_from_the_runs_own_agenda(tmp_path):
    """Not from a config: the config that produced a run is not recoverable from the run, and
    the sealed agenda is. That is the same reason `judge --of` derives its paths."""

    stage = StageInput.at(_run(tmp_path))
    assert stage.release == Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
    assert StageInput.at(_run(tmp_path, agenda=False)).release is None


def test_an_audit_is_read_by_the_node_that_wrote_it(tmp_path):
    """A run may carry several judgements -- a widened pairing tier, a different rubric. Each
    gets its own directory, so they cannot resume into each other, and either can be read."""

    directory = _run(tmp_path)
    audit = tmp_path / "audit"
    audit.mkdir()
    (audit / "semantic_report.json").write_bytes(canonical_json_bytes({"issue_recall": 0.2}))
    stage = StageInput.at(directory, audit_dir=audit)
    assert set(stage.consumed_audit) == {"semantic_report"}
    assert stage.audit_path("semantic_report").is_file()
    with pytest.raises(MissingArtifact):
        stage.audit_path("semantic_matches")
    with pytest.raises(MissingArtifact) as error:
        StageInput.at(directory).audit_path("semantic_report")
    assert "judge the run first" in str(error.value)


def test_derive_from_run_keeps_its_default_paths_and_names_other_nodes(tmp_path):
    from src.mathlib_review.judge.runner import derive_from_run
    from src.mathlib_review.paths import AUDITS

    default = derive_from_run("pr5_A_lead_heldout12_v2_rep1")
    assert default["out_dir"] == AUDITS / "pr5-A-lead-heldout12-v2-rep1"
    assert default["run_name"] == "pr_review_v5_judge_pr5_A_lead_heldout12_v2_rep1"
    widened = derive_from_run("pr5_A_lead_heldout12_v2_rep1", "judge_relation")
    assert widened["out_dir"] != default["out_dir"]
    assert widened["run_name"] != default["run_name"]
    assert widened["candidates"] == default["candidates"]


def test_the_audit_root_is_spelled_once():
    """It was spelled twice -- `judge.runner.JUDGE_AUDIT_ROOT` and
    `analysis.denominators._AUDIT_ROOT` -- and a run's identity written in two places is the
    class of mistake `judge --of` exists to remove."""

    import re

    from src.mathlib_review import paths

    definitions = [
        str(path) for path in Path("src").rglob("*.py")
        if "__pycache__" not in path.parts
        and re.search(r'^\s*\w*AUDIT_ROOT\s*=\s*Path\(', path.read_text(encoding="utf-8"), re.M)
    ]
    assert definitions == [], definitions
    assert paths.AUDITS == paths.RESULTS / "audits"


def test_the_judge_reads_its_source_run_through_stage_input():
    """The hand-off is only worth naming if it is the thing used. A stage that rebuilds a
    sibling path by hand is the defect `judge --of` fixed once and nothing generalised."""

    import inspect

    from src.mathlib_review.judge import runner as judge_runner

    assert "StageInput" in inspect.getsource(judge_runner.source_run)
    # And the two siblings it used to rebuild are resolved through the artifact table.
    assert 'parent / "run_manifest.json"' not in inspect.getsource(judge_runner)


def test_a_run_with_no_manifest_is_unchecked_rather_than_refused(tmp_path):
    """v4 runs never wrote a manifest and a hand-assembled candidates file has no run at all.
    Refusing those would be a new rule wearing a refactor's clothes: what is refused is a run
    that CLOSED and said it did not cover what it promised."""

    directory = _run(tmp_path, status=None, findings=True)
    stage = StageInput.at(directory)
    assert stage.unchecked is True and stage.forensic is False
