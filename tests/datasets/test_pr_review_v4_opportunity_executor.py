"""Contract tests for generic terminal execution accounting."""

from src.datasets.pr_review_v4.implementation_registry import assess_capabilities, default_implementations
from src.datasets.pr_review_v4.opportunity_executor import (
    RunnerOutcome,
    _operator_run,
    _opportunity,
    _unavailable,
    execute_treatment,
)
from src.datasets.pr_review_v4.schema import ReviewEpisodeInput, VisibleText

from tests.datasets.test_pr_review_v4_implementation_registry import (
    NAMING_POSITIVE,
    _graph,
    _target,
    _task,
)


def _episode():
    return ReviewEpisodeInput(
        episode_id="episode:test",
        repo="leanprover-community/mathlib4",
        pr_number=100,
        round_index=1,
        title=VisibleText(text="test", provenance="review_time_verified"),
        description=VisibleText(text=None, provenance="absent"),
        base_sha="base-test",
        reviewed_head_sha="head-test",
        diff="",
        changed_files=["Mathlib/Test.lean"],
        patch_sha256="patch-test",
        source_projection_sha256="projection-test",
    )


def test_executor_records_supported_noop_and_unsupported_tasks_separately(tmp_path):
    graph = _graph([
        _target("change:naming", NAMING_POSITIVE),
        _target("change:canonical", "theorem no_match : True := by trivial\n"),
    ])
    tasks = [
        _task("investigation:naming", "naming_contrast.v1", "change:naming"),
        _task("investigation:canonical", "canonical_api_search.v1", "change:canonical"),
    ]
    assessments = assess_capabilities(tasks, [graph], default_implementations())

    def naming_noop(task, _graph, _episode, _workspace, _cache):
        run = _operator_run(task, "naming_probe", "completed", [], 0)
        return RunnerOutcome(
            operator_runs=[run],
            disposition="checked_no_opportunity",
            basis="The supported naming implementation checked the target without an opportunity.",
        )

    output = execute_treatment(
        tasks,
        [graph],
        [_episode()],
        assessments,
        tmp_path / "workspaces",
        runners={"naming_contrast.encard_subject_prefix.v1": naming_noop},
    )
    records = {item.investigation_id: item for item in output["records"]}
    assert len(records) == len(tasks)
    assert records["investigation:naming"].disposition == "checked_no_opportunity"
    assert records["investigation:canonical"].disposition == "not_applicable"
    ledger = {item["investigation_id"]: item for item in output["ledger"]}
    assert ledger["investigation:naming"]["terminal_stage"] == "operator_completed"
    assert ledger["investigation:canonical"]["terminal_stage"] == "capability_assessed"
    assert len(output["operator_runs"]) == 1


def test_executor_preserves_unavailable_operator_as_needs_followup(tmp_path):
    graph = _graph([_target("change:naming", NAMING_POSITIVE)])
    task = _task("investigation:naming", "naming_contrast.v1", "change:naming")
    assessments = assess_capabilities([task], [graph], default_implementations())

    def unavailable_runner(task, _graph, _episode, _workspace, _cache):
        return _unavailable(task, "naming_probe", "required snapshot index is unavailable")

    output = execute_treatment(
        [task],
        [graph],
        [_episode()],
        assessments,
        tmp_path / "workspaces",
        runners={"naming_contrast.encard_subject_prefix.v1": unavailable_runner},
    )
    record = output["records"][0]
    assert record.disposition == "needs_followup"
    assert record.followup_ids
    assert output["ledger"][0]["terminal_stage"] == "operator_unavailable"


def test_executor_enforces_implementation_opportunity_limit(tmp_path):
    graph = _graph([_target("change:naming", NAMING_POSITIVE)])
    task = _task("investigation:naming", "naming_contrast.v1", "change:naming")
    assessments = assess_capabilities([task], [graph], default_implementations())

    def overproducing_runner(task, _graph, _episode, _workspace, _cache):
        run = _operator_run(task, "naming_probe", "completed", ["artifact:test"], 2)
        return RunnerOutcome(
            operator_runs=[run],
            opportunities=[
                _opportunity(task, "first", ["artifact:first"], None, 1.0),
                _opportunity(task, "second", ["artifact:second"], None, 1.0),
            ],
            disposition="opportunities",
        )

    output = execute_treatment(
        [task],
        [graph],
        [_episode()],
        assessments,
        tmp_path / "workspaces",
        runners={"naming_contrast.encard_subject_prefix.v1": overproducing_runner},
        implementation_limits={"naming_contrast.encard_subject_prefix.v1": 1},
    )
    assert len(output["opportunities"]) == 1
    assert output["records"][0].disposition == "opportunities"
