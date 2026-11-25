"""Independent reviewer entry points and fresh readings of a saved submission."""

import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import pytest

from ape.orchestration.persistence import TaskStorage
from ape.tasks.lean_tasks.formal_math.review.whole_pr import SubmittedFinding
from src.mathlib_review.analysis import submissions
from src.mathlib_review.io import pretty_json_bytes, sha256_file
from src.mathlib_review.judge.ask_matching import render_matcher_prompt
from src.mathlib_review.review import cli, reviewers, runner

PROBE = Path("results/pr_review_v5/probes/named-episode-review-2026-11-25")
#: The orchestrator's own run and the environment preflight, kept before any test replaces them.
ORCHESTRATOR_RUN = runner.TaskOrchestrator.run
ENVIRONMENT_PREFLIGHT = runner.assert_ready


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pretty_json_bytes(value))


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    repo = Path.cwd()
    monkeypatch.chdir(tmp_path)
    for name in ("configs", "inputs"):
        Path(name).symlink_to(repo / name)
    return repo


def run_options(reviewer, alias, head="c5474cb4"):
    return ["run", "--reviewer", reviewer, "--case", f"42184@{head}", "--run-name", alias, "--execute"]


#: The specialist and historical stages. A named review ends at its accepted submission without them.
SPECIALIST_STAGES = ("load_release", "select_units_and_episodes", "agenda_for_release", "build_agenda",
                     "stamp_submission_directives", "_build_plan", "solo_responses", "finalize", "reconcile")


@pytest.fixture
def provider(checkout, monkeypatch):
    # Supply only the commit date. Prior reviews and expert requests are absent during generation.
    put(Path("data/pr_review_v2/cache/bundles/pr_42184.json"), {"commits": [{
        "sha": "c5474cb4a68a515228b49225b38a2507264f91f7", "commit": {"committer": {"date": "2026-07-30T00:00:00Z"}}}]})
    original_load = runner.load_run

    def load(*args):
        dataset, scaffold, overrides = original_load(*args)
        scaffold.runs_base_dir = Path.cwd() / ".ape/runs"
        if accept.release is not None:
            dataset.release = accept.release
        return dataset, scaffold, overrides

    monkeypatch.setattr(runner, "load_run", load)
    monkeypatch.setattr(runner, "assert_ready", lambda *a, **kw: None)
    for stage in SPECIALIST_STAGES:
        def refuse(*args, stage=stage, **kwargs):
            raise AssertionError(f"the named review invoked {stage}")
        monkeypatch.setattr(runner, stage, refuse)

    async def prebuilt(*args, **kwargs):
        return []

    monkeypatch.setattr(runner, "assert_workspaces_prebuilt", prebuilt)
    monkeypatch.setattr(runner, "assert_reviewed_workspaces_prebuilt", prebuilt)

    async def accept(self, tasks):
        task, = tasks
        task_dir = self.tasks_dir / task.data.global_index
        stored = await TaskStorage(task_dir, task.data.global_index).load_all_samples()
        if 0 in stored and stored[0].is_failed_on_errors(self.config.execution.task_max_retries):
            # As the orchestrator does: a sample whose retries are spent stays failed until requeued.
            return SimpleNamespace(task_results=[])
        plans = {path: submissions.read(path) for path in Path(".ape/reviews").glob("*/generation.json")}
        (plan_path, record), = [(path, run["episodes"]["42184"]) for path, plan in plans.items()
                                for run in plan["runs"].values() if run["run"] == self.orchestrator_id]
        alias = Path(plan_path).parent.name
        accept.sessions.append(alias)
        folder = task_dir / "samples/0"
        attempt = folder / "attempts/ok"
        cwd = str(attempt / "workspaces")
        put(attempt / "claude_code_session.json", {
            "init": {"model": record["model"], "claude_code_version": record["cli_version"], "cwd": cwd,
                     "tools": record["builtins"] + ["mcp__core__" + t for t in record["mcp"]],
                     "permissionMode": "dontAsk", "mcp_servers": [{"name": "core", "status": "connected"}]},
            "effort": record["effort"]})
        put(attempt / "containment_audit.json", {"clean": True, "usable": True, "transcripts": [{"by_tool": {}}]})
        message = Path(record["message"]).read_text().replace("{attempt_workspaces}", cwd)
        (attempt / "claude_code_conversation_1.jsonl").write_text(
            json.dumps({"type": "user", "message": {"content": message}}) + "\n")
        review = accept.reviews.get(alias, {})
        sample = {"sample_id": "s", "sample_index": 0, "task_global_index": task.data.global_index,
                  "created_at": "2026-11-25", "updated_at": "2026-11-25"}
        limits = {"max_turns": record["max_turns"], "cost_limit": record["cost_cap"], "token_limit": record["token_cap"]}
        if review in ("fail", "lost"):
            # "fail": the model stopped without calling the submission tool. "lost": every attempt
            # died on a system error until its retries ran out. Neither writes a task result.
            status, count = (("failed_model", 1) if review == "fail"
                             else ("failed_error", self.config.execution.task_max_retries + 1))
            put(folder / "sample.json", {**sample, "attempts": [
                {"attempt_id": n + 1, "path": str(attempt), "status": status, "created_at": "2026-11-25", **limits}
                for n in range(count)]})
            return SimpleNamespace(task_results=[])
        submitted = [SubmittedFinding(**finding) for finding in review.get("findings", [])]
        # The result the submission tool builds, through the task's own result class.
        raw = task.create_result(
            success=True, score=1.0, pr_number=task.data.pr_number,
            review_message=review.get("message", "No changes requested."),
            findings=[f.recorded() for f in submitted],
            submitted_findings=[f.model_dump(exclude_unset=True) for f in submitted]).model_dump(mode="json")
        put(folder / "sample.json", {**sample, "attempts": [
            {"attempt_id": 1, "path": str(attempt), "status": "success", "created_at": "2026-11-25",
             **limits, "result": raw}]})
        if review.get("then") == "kill before its result":
            raise InterruptedError("process killed after the session was accepted, before its task result")
        put(task_dir / "task_result.json", raw)
        if review.get("then") == "kill":
            raise InterruptedError("process killed after the session was accepted")
        return SimpleNamespace(task_results=[raw])

    accept.reviews, accept.sessions, accept.release = {}, [], None
    monkeypatch.setattr(runner.TaskOrchestrator, "run", accept)

    return accept


@pytest.fixture
def frozen_history(monkeypatch):
    """Stand in only for the embedding data. The runner still pins the index and grants the tool."""
    from src.mathlib_review.retrieval.precedent_index import PrecedentIndex

    def index(collection):
        directory = Path("frozen-index")
        put(directory / "manifest.json", {"corpus_sha256": collection.sha256})
        return directory

    monkeypatch.setattr(reviewers.ExcerptCollection, "index", index)
    monkeypatch.setattr(PrecedentIndex, "shared", lambda *a, **kw: None)


def episodes_only_release(checkout, *extra):
    """A release holding only the visible episodes: no work units, change graphs or feedback."""
    release = Path("episodes-only")
    (release / "input").mkdir(parents=True)
    source = checkout / "inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl"
    rows = [json.loads(line) for line in source.read_text().split("\n") if line.strip()]
    (release / "input/episodes.jsonl").write_text("".join(json.dumps(r) + "\n" for r in [*rows, *extra]))
    return release.resolve()


def test_an_interrupted_review_is_archived_from_its_accepted_session(checkout, provider, monkeypatch):
    alias = "guided-42184-a"
    out = submissions.review_directory(alias)
    opts = run_options("solo-v1", alias)
    provider.reviews[alias] = {**saved_42184_reviews(checkout)["guided"], "then": "kill"}
    with pytest.raises(InterruptedError, match="accepted"):
        cli.main(opts)
    assert provider.sessions == [alias] and not (out / "archive.json").exists()
    # The resumed run archives the accepted session that is already on disk.
    refuse_new_sessions(monkeypatch)
    assert cli.main([*opts, "--resume"]) == 0
    assert cli.main([*opts, "--resume"]) == 0
    assert provider.sessions == [alias]
    archived = submissions.read(out / "archive.json")["records"][0]
    raw = submissions.read(Path(archived["files"]["task_result.json"]["path"]))
    submitted = provider.reviews[alias]
    assert raw["review_message"] == submitted["message"]
    assert [(f["path"], f["line_start"], f["line_end"], f["claim"]) for f in raw["submitted_findings"]] == [
        (f["path"], f["line_start"], f["line_end"], f["claim"]) for f in submitted["findings"]]
    projected = submissions.read(out / f"submissions/{archived['run']}/findings.json")["42184"]
    assert [f["target"] for f in projected] == [
        f"{f['path']}:{f['line_start']}" for f in submitted["findings"]]
    with pytest.raises(SystemExit) as wrong_head:
        cli.main([*run_options("solo-v1", alias, "0000000"), "--resume"])
    assert wrong_head.value.code == 2
    second = "solo-42184-b"
    monkeypatch.setattr(runner.TaskOrchestrator, "run", provider)
    assert cli.main(run_options("solo-v1", second)) == 0
    copy_reference(checkout)
    score = ["score", "--of", alias, "--using"]
    for policy in ("round1-requests-v1", "round1-questions-v1", "round1-requests-v1"):
        assert cli.main([*score, policy]) == 0
    def plans():
        return [submissions.matching.load_plan(p.parent)
                for p in Path(".ape/review-comparisons").rglob(submissions.matching.PLAN_FILE)]
    before = plans()
    assert len(before) == 2 and before[0].packets == before[1].packets
    assert {p.expected_cells for p in before} == {2}
    paired = ["score", "--of", alias, second, "--using", "round1-requests-v1"]
    assert cli.main(paired) == 0
    reference = submissions.probes.load_probe_set(submissions.REFERENCE)
    asks = submissions.read(reference.asks_file)
    asks["asks"]["42184"].pop()
    put(reference.asks_file, asks)
    assert cli.main([*score, "round1-requests-v1"]) == 0
    assert cli.main(paired) == 0
    assert sorted(p.expected_cells for p in plans()) == [1, 2, 2, 2, 4]
    projection = out / f"submissions/{archived['run']}/findings.json"
    saved_projection = projection.read_bytes()
    projection.write_text(json.dumps({"42184": []}))
    with pytest.raises(ValueError, match="archived matcher input changed"):
        submissions.saved_reviews(out)
    projection.write_bytes(saved_projection)
    Path(archived["files"]["task_result.json"]["path"]).write_text("{}")
    with pytest.raises(ValueError, match="accepted task result changed"):
        submissions.saved_reviews(out)


@pytest.mark.parametrize("tamper, reason", [
    ("containment_audit.json", "archived containment_audit.json changed"),
    ("claude_code_session.json", "archived claude_code_session.json changed"),
    ("transcript", "archived claude_code_conversation_1.jsonl changed"),
    ("sample.json", "archived sample.json changed"),
    ("first-message.txt", "archived first message changed"),
    ("episode_id", "different run or episode"),
    ("other accepted result", "accepted attempt's submission"),
    ("records", "cover PRs []"),
    ("evidence list", "lacks ['claude_code_session.json', 'containment_audit.json', 'task_result.json', "
                      "'sample.json', 'claude_code_conversation_*.jsonl']")])
def test_scoring_refuses_an_altered_archive(checkout, provider, capsys, tamper, reason):
    alias = "guided-42184"
    provider.reviews[alias] = saved_42184_reviews(checkout)["guided"]
    assert cli.main(run_options("solo-v1", alias)) == 0
    copy_reference(checkout)
    out = submissions.review_directory(alias)
    path = out / "archive.json"
    archive = submissions.read(path)
    if tamper == "first-message.txt":
        (out / tamper).write_text("A different first message.")
    elif tamper == "episode_id":
        archive["records"][0]["episode_id"] = "another reviewed head"
        put(path, archive)
    elif tamper == "other accepted result":
        sample_file = archive["records"][0]["files"]["sample.json"]
        target = Path(sample_file["path"])
        sample = submissions.read(target)
        sample["attempts"][0]["result"]["submitted_findings"] = []
        put(target, sample)
        sample_file["sha256"] = sha256_file(target)
        put(path, archive)
    elif tamper == "records":
        archive["records"] = []
        put(path, archive)
    elif tamper == "evidence list":
        archive["records"][0].update(files={}, run_files={})
        put(path, archive)
    else:
        files = archive["records"][0]["files"]
        name = next(n for n in files if n.startswith("claude_code_conversation")) if tamper == "transcript" else tamper
        target = Path(files[name]["path"])
        target.write_text(json.dumps({"clean": False, "usable": False}) if tamper == "containment_audit.json"
                          else target.read_text() + " ")
    capsys.readouterr()
    with pytest.raises(SystemExit) as refused:
        cli.main(["score", "--of", alias, "--using", "round1-requests-v1"])
    assert refused.value.code == 2 and reason in capsys.readouterr().err
    assert not Path(".ape/review-comparisons").exists()


@pytest.mark.parametrize("swapped", ["record", "files", "projection"])
def test_scoring_refuses_another_samples_evidence(checkout, provider, swapped):
    # Same reviewer and head, independently accepted submissions with one and two findings.
    provider.reviews.update(saved_42184_reviews(checkout))
    for alias in ("ordinary", "guided"):
        assert cli.main(run_options("solo-v1", alias)) == 0
    copy_reference(checkout)
    path = submissions.review_directory("ordinary") / "archive.json"
    ordinary = submissions.read(path)
    guided = submissions.read(submissions.review_directory("guided") / "archive.json")
    if swapped == "record":
        ordinary["records"] = guided["records"]
    elif swapped == "files":
        ordinary["records"][0]["files"] = guided["records"][0]["files"]
    else:
        ordinary["sources"] = guided["sources"]
        ordinary["projection_sha256"] = guided["projection_sha256"]
    put(path, ordinary)
    with pytest.raises(SystemExit) as refused:
        cli.main(["score", "--of", "ordinary", "--using", "round1-requests-v1"])
    assert refused.value.code == 2
    assert not Path(".ape/review-comparisons").exists()


def test_empty_mixed_and_failed_reviews_have_distinct_outcomes(checkout, provider, capsys):
    guided = saved_42184_reviews(checkout)["guided"]
    question = {"claim": "The description does not say why the NeBot instance was needed.",
                "suggested_fix": "Could you say in the description whether any caller relies on it?"}
    provider.reviews.update({
        "empty": {"findings": [], "message": "I would merge this as it is."},
        "mixed": {"findings": [*guided["findings"], question], "message": guided["message"]},
        "failed": "fail"})
    for alias in ("empty", "mixed"):
        assert cli.main(run_options("solo-v1", alias)) == 0
    saved = {}
    for alias in ("empty", "mixed"):
        _, archive = submissions.saved_reviews(submissions.review_directory(alias))
        record, = archive["records"]
        raw = submissions.read(Path(record["files"]["task_result.json"]["path"]))
        projected = submissions.read(Path(archive["sources"]["solo-v1"]["path"]))["42184"]
        saved[alias] = (record["findings"], raw["review_message"], projected)
        assert raw["review_message"] == provider.reviews[alias]["message"]
    assert saved["empty"][0] == 0 and saved["empty"][2] == []
    count, _, projected = saved["mixed"]
    assert count == 3
    assert projected == [
        *({"target": f"{f['path']}:{f['line_start']}", "claim": f["claim"], "requested_change": f["suggested_fix"]}
          for f in guided["findings"]),
        {"target": submissions.probes.PR_LEVEL_TARGET, "claim": question["claim"],
         "requested_change": question["suggested_fix"]}]
    assert cli.main(run_options("solo-v1", "failed")) == 1
    assert "NO SUBMITTED REVIEW" in capsys.readouterr().err
    failed = submissions.review_directory("failed")
    assert (failed / "generation.json").is_file() and not (failed / "archive.json").exists()
    with pytest.raises(SystemExit) as refused:
        cli.main(["score", "--of", "failed", "--using", "round1-requests-v1"])
    assert refused.value.code == 2
    assert provider.sessions == ["empty", "mixed", "failed"]


def test_a_pre_change_run_interrupted_before_its_run_plan_resumes_and_archives(checkout, provider, monkeypatch):
    alias = "early-42184"
    out = submissions.review_directory(alias)

    async def lost(self, tasks):
        raise InterruptedError("killed before the first attempt")

    monkeypatch.setattr(runner.TaskOrchestrator, "run", lost)
    with pytest.raises(InterruptedError):
        cli.main(run_options("solo-v1", alias))
    # The record the earlier code left: its generation alone, before it sealed a run plan.
    generation = submissions.read(out / "generation.json")
    for run in generation["runs"].values():
        assert not Path("results/pr_review_v5/runs", run["run"], "run_plan.json").exists()
    (out / submissions.INPUTS_FILE).unlink()
    monkeypatch.setattr(runner.TaskOrchestrator, "run", provider)
    assert cli.main([*run_options("solo-v1", alias), "--resume"]) == 0
    assert provider.sessions == [alias]
    _, archive = submissions.saved_reviews(out)
    assert archive["records"][0]["findings"] == 0


def test_a_run_records_the_profile_its_plan_previewed(checkout, provider, capsys):
    assert cli.main(["plan", "--reviewer", "solo-v1", "--case", "42184@c5474cb4"]) == 0
    printed = capsys.readouterr().out
    previewed = json.loads(printed[printed.rindex("\n{\n") + 1:])
    assert cli.main(run_options("solo-v1", "profiled-42184")) == 0
    recorded = submissions.read(submissions.review_directory("profiled-42184") / "generation.json")
    assert recorded["profile_sha256"] == previewed["profile_sha256"]


def test_a_resume_must_name_the_review_its_name_holds(checkout, provider, frozen_history, capsys):
    alias = "held-42184"
    assert cli.main(run_options("pr-search-v1", alias)) == 0
    archive = (submissions.review_directory(alias) / "archive.json").read_bytes()
    with pytest.raises(SystemExit) as refused:
        cli.main([*run_options("solo-v1", alias), "--resume"])
    assert refused.value.code == 2 and "different review" in capsys.readouterr().err
    assert (submissions.review_directory(alias) / "archive.json").read_bytes() == archive
    assert cli.main([*run_options("pr-search-v1", alias), "--resume"]) == 0


def test_a_refused_resume_of_an_earlier_run_writes_nothing(checkout, provider, frozen_history, monkeypatch, capsys):
    alias = "early-search-42184"
    out = submissions.review_directory(alias)

    async def lost(self, tasks):
        raise InterruptedError("killed before the first attempt")

    monkeypatch.setattr(runner.TaskOrchestrator, "run", lost)
    with pytest.raises(InterruptedError):
        cli.main(run_options("pr-search-v1", alias))
    (out / submissions.INPUTS_FILE).unlink()  # as the earlier code left it, before its run plan
    with pytest.raises(SystemExit) as refused:
        cli.main([*run_options("solo-v1", alias), "--resume"])
    assert refused.value.code == 2 and "different review" in capsys.readouterr().err
    assert not (out / submissions.INPUTS_FILE).exists()
    monkeypatch.setattr(runner.TaskOrchestrator, "run", provider)
    assert cli.main([*run_options("pr-search-v1", alias), "--resume"]) == 0
    assert provider.sessions == [alias]


@pytest.mark.parametrize("reviewer", ["solo-v1", "pr-search-v1"])
def test_an_accepted_run_recorded_with_inline_inputs_resumes(provider, frozen_history, monkeypatch, reviewer):
    alias = "inline-42184"
    out = submissions.review_directory(alias)
    options = run_options(reviewer, alias)
    provider.reviews[alias] = {"findings": [], "message": "No changes requested.", "then": "kill"}
    with pytest.raises(InterruptedError, match="accepted"):
        cli.main(options)
    # The shape 968c285e..86bb0f88 recorded: the inputs inside the generation record itself.
    recorded = submissions.read(out / submissions.INPUTS_FILE)
    generation = submissions.read(out / "generation.json")
    run = generation["runs"][reviewer]
    run["inputs"] = recorded[run["run"]]
    if reviewer == "pr-search-v1":
        # Recorded in the real 86bb0f88 search preview, alongside the granted precedent index.
        index = run["inputs"]["context_index_sha256"]
        index["zulip_corpus"] = "b0d013afb6bf9661ea9cdcbbc97ed4ca71348640fae45a50ee3af6aa10a9f8bd"
    saved = out / "generation.json"
    put(saved, generation)
    before = saved.read_bytes()
    (out / submissions.INPUTS_FILE).unlink()
    refuse_new_sessions(monkeypatch)
    if reviewer == "pr-search-v1":
        index["precedent_manifest"] = "0" * 64
        put(saved, generation)
        with pytest.raises(SystemExit) as refused:
            cli.main([*options, "--resume"])
        assert refused.value.code == 2 and not (out / "archive.json").exists()
        saved.write_bytes(before)
    assert cli.main([*options, "--resume"]) == 0
    assert saved.read_bytes() == before and provider.sessions == [alias]
    assert not (out / submissions.INPUTS_FILE).exists()
    _, archive = submissions.saved_reviews(out)
    assert archive["records"][0]["findings"] == 0


def no_login(*args, **kwargs):
    raise RuntimeError("1 prerequisite(s) are not met on this machine: [Claude login]")


async def no_reviewed_workspace(*args, **kwargs):
    raise RuntimeError("reviewed workspace for 42184 is not prebuilt")


@pytest.mark.parametrize("check, refusal", [("assert_ready", no_login),
                                            ("assert_reviewed_workspaces_prebuilt", no_reviewed_workspace)])
def test_a_run_refused_by_the_environment_can_start_again(checkout, provider, monkeypatch, check, refusal):
    alias = "refused-42184"
    present = getattr(runner, check)
    monkeypatch.setattr(runner, check, refusal)
    with pytest.raises(RuntimeError, match="Claude login|not prebuilt"):
        cli.main(run_options("solo-v1", alias))
    assert not any(submissions.review_directory(alias).glob("*.json"))
    monkeypatch.setattr(runner, check, present)
    assert cli.main(run_options("solo-v1", alias)) == 0
    assert provider.sessions == [alias]


def test_resuming_an_archived_review_from_before_the_inputs_record_changes_nothing(checkout, provider):
    alias = "archived-42184"
    out = submissions.review_directory(alias)
    assert cli.main(run_options("solo-v1", alias)) == 0
    # The earlier format archived its run plan and had no separate inputs record.
    (out / submissions.INPUTS_FILE).unlink()
    archive = submissions.read(out / "archive.json")
    archive.pop("inputs_sha256")
    record, = archive["records"]
    plan = out / "submissions" / record["run"] / "run_plan.json"
    put(plan, {"run_name": record["run"], "evaluation_settings": {"design": "whole_pr"}})
    record["run_files"][plan.name] = {"path": str(plan), "sha256": sha256_file(plan)}
    put(out / "archive.json", archive)
    before = sorted((p.relative_to(out), p.read_bytes()) for p in out.rglob("*") if p.is_file())
    assert cli.main([*run_options("solo-v1", alias), "--resume"]) == 0
    assert sorted((p.relative_to(out), p.read_bytes()) for p in out.rglob("*") if p.is_file()) == before
    assert provider.sessions == [alias]


@pytest.mark.parametrize("stop", ["kill", "kill before its result"])
def test_recovering_an_accepted_review_needs_no_generation_resources(checkout, provider, frozen_history,
                                                                     monkeypatch, stop):
    from src.datasets.zulip.config import ZulipConfig

    alias = "search-42184"
    opts = run_options("pr-search-v1", alias)
    monkeypatch.setattr(ZulipConfig, "sqlite_path", property(lambda self: Path("absent/zulip.sqlite3")))
    provider.reviews[alias] = {**saved_42184_reviews(checkout)["guided"], "then": stop}
    with pytest.raises(InterruptedError, match="accepted"):
        cli.main(opts)
    run = submissions.read(submissions.review_directory(alias) / "generation.json")["runs"]["pr-search-v1"]["run"]
    trace = runner.run_dir(run) / "context_trace.jsonl"
    trace.parent.mkdir(parents=True, exist_ok=True)
    trace.write_text(json.dumps({"tool": "declaration_search"}) + "\n")
    # A Zulip index the reviewer was never granted appears, and the session credential is gone.
    Path("zulip.sqlite3").write_text("")
    monkeypatch.setattr(ZulipConfig, "sqlite_path", property(lambda self: Path("zulip.sqlite3").resolve()))
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    monkeypatch.setattr(runner, "assert_ready", ENVIRONMENT_PREFLIGHT)
    refuse_new_sessions(monkeypatch)
    assert cli.main([*opts, "--resume"]) == 0
    assert provider.sessions == [alias]
    out = submissions.review_directory(alias)
    _, archive = submissions.saved_reviews(out)
    assert archive["records"][0]["findings"] == 2
    del archive["records"][0]["run_files"]["context_trace.jsonl"]
    put(out / "archive.json", archive)
    copy_reference(checkout)
    with pytest.raises(SystemExit) as refused:
        cli.main(["score", "--of", alias, "--using", "round1-requests-v1"])
    assert refused.value.code == 2


def refuse_new_sessions(monkeypatch):
    """Resume through the orchestrator itself, with any new session refused."""
    async def no_session(self, *args, **kwargs):
        raise AssertionError("recovery scheduled a review session")

    monkeypatch.setattr(runner.TaskOrchestrator, "run", ORCHESTRATOR_RUN)
    monkeypatch.setattr(runner.TaskOrchestrator, "_execute_jobs", no_session)


def test_recovery_completes_the_outcome_record_an_interrupted_worker_left(checkout, provider, monkeypatch):
    alias = "outcome-42184"
    out = submissions.review_directory(alias)
    opts = run_options("solo-v1", alias)
    # Killed between writing the accepted task result and its outcome record.
    provider.reviews[alias] = {"findings": [], "message": "No changes requested.", "then": "kill"}
    with pytest.raises(InterruptedError, match="accepted"):
        cli.main(opts)
    tasks = Path(submissions.read(out / "generation.json")["runs"]["solo-v1"]["tasks_dir"])
    (task_dir,) = [p for p in tasks.iterdir() if p.is_dir()]
    assert (task_dir / "task_result.json").is_file() and not (task_dir / "task_outcome.json").exists()

    refuse_new_sessions(monkeypatch)
    assert cli.main([*opts, "--resume"]) == 0
    outcome = submissions.read(task_dir / "task_outcome.json")
    assert outcome["has_result"] is True
    assert provider.sessions == [alias]
    submissions.saved_reviews(out)


def test_a_session_lost_to_system_errors_runs_again_on_resume(checkout, provider, capsys):
    alias = "lost-42184"
    provider.reviews[alias] = "lost"
    assert cli.main(run_options("solo-v1", alias)) == 1
    assert "failed_error" in capsys.readouterr().err
    provider.reviews[alias] = {"findings": [], "message": "No changes requested."}
    assert cli.main([*run_options("solo-v1", alias), "--resume"]) == 0
    assert provider.sessions == [alias, alias]
    _, archive = submissions.saved_reviews(submissions.review_directory(alias))
    assert archive["records"][0]["findings"] == 0


def test_the_review_runs_from_a_release_holding_only_its_episodes(checkout, provider, frozen_history, capsys):
    generated = {}
    for label, release in (("profile", None), ("episodes", episodes_only_release(checkout))):
        provider.release = release
        for reviewer in ("solo-v1", "pr-search-v1"):
            assert cli.main(["plan", "--reviewer", reviewer, "--case", "42184@c5474cb4"]) == 0
            capsys.readouterr()
            alias = f"{reviewer}-{label}"
            assert cli.main(run_options(reviewer, alias)) == 0
            out = submissions.review_directory(alias)
            plan, archive = submissions.saved_reviews(out)
            assert archive["records"][0]["findings"] == 0
            run = plan["runs"][reviewer]
            recorded = submissions.read(out / submissions.INPUTS_FILE)[run["run"]]
            assert recorded["design"] == "whole_pr"
            assert ("context_index_sha256" in recorded) == (reviewer == "pr-search-v1")
            assert not Path(".ape/runs", run["run"], "run_plan.json").exists()
            generated[label, reviewer] = ((out / "first-message.txt").read_text(), run["episodes"]["42184"])
    keys = ("message_sha256", "mcp", "mcp_schema_sha256", "builtins", "model", "effort", "cutoff",
            "max_turns", "token_cap", "cost_cap", "reviewed_head_sha", "base_sha", "episode_id")
    for reviewer in ("solo-v1", "pr-search-v1"):
        (message, record), (again, other) = generated["profile", reviewer], generated["episodes", reviewer]
        assert message == again and {k: record[k] for k in keys} == {k: other[k] for k in keys}
    solo, search = generated["episodes", "solo-v1"][1], generated["episodes", "pr-search-v1"][1]
    assert solo["message_sha256"] == search["message_sha256"]
    assert set(search["mcp"]) - set(solo["mcp"]) == {"precedent_search"} and set(solo["mcp"]) < set(search["mcp"])


def episode_rows(checkout):
    source = checkout / "inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl"
    return {row["pr_number"]: row for row in (json.loads(line) for line in source.read_text().split("\n")
                                              if line.strip())}


@pytest.mark.parametrize("patch, problem", [("another PR", "patch hash mismatch"), ("empty", "patch hash mismatch"),
                                            ("file index", "changed-files index mismatch")])
def test_an_episode_whose_patch_disagrees_with_its_digest_is_refused(checkout, provider, capsys, patch, problem):
    rows = episode_rows(checkout)
    episode, other = rows[42184], rows[41930]
    swapped = {"empty": {**episode, "diff": "", "changed_files": []},
               "file index": {**episode, "changed_files": other["changed_files"]},
               "another PR": {**episode, "base_sha": other["base_sha"], "diff": other["diff"],
                              "changed_files": other["changed_files"]}}[patch]
    release = Path("swapped")
    (release / "input").mkdir(parents=True)
    (release / "input/episodes.jsonl").write_text(json.dumps(swapped) + "\n")
    provider.release = release.resolve()
    for command in (["plan", "--reviewer", "solo-v1", "--case", "42184@c5474cb4"],
                    run_options("solo-v1", "swapped")):
        with pytest.raises(SystemExit) as refused:
            cli.main(command)
        assert refused.value.code == 2 and problem in capsys.readouterr().err
    assert provider.sessions == [] and not (submissions.review_directory("swapped") / "generation.json").exists()


def test_a_release_manifest_refuses_an_episode_rewritten_with_another_prs_patch(checkout, provider, capsys):
    rows = episode_rows(checkout)
    other = rows[41930]
    # Consistent with itself: 41930's base, patch, file index and digest under 42184's head.
    swapped = {**rows[42184], **{k: other[k] for k in ("base_sha", "diff", "changed_files", "patch_sha256")}}
    release = Path("released")
    (release / "input").mkdir(parents=True)
    shutil.copy(checkout / "inputs/probes/probe-2026-07-08-v1/manifest.json", release / "manifest.json")
    (release / "input/episodes.jsonl").write_text(
        "".join(json.dumps(swapped if pr == 42184 else row) + "\n" for pr, row in rows.items()))
    provider.release = release.resolve()
    with pytest.raises(SystemExit) as refused:
        cli.main(["plan", "--reviewer", "solo-v1", "--case", "42184@c5474cb4"])
    assert refused.value.code == 2 and "input/episodes.jsonl" in capsys.readouterr().err


def test_the_manifest_must_hash_the_episode_file_the_reviewer_reads(checkout, provider, capsys):
    source = checkout / "inputs/probes/probe-2026-07-08-v1"
    release = Path("renamed")
    (release / "input").mkdir(parents=True)
    shutil.copy(source / "input/episodes.jsonl", release / "input/renamed.jsonl")
    manifest = json.loads((source / "manifest.json").read_text())
    for artifact in manifest["input_artifacts"]:
        if artifact["path"] == "input/episodes.jsonl":
            artifact["path"] = "input/renamed.jsonl"
    (release / "manifest.json").write_text(json.dumps(manifest))
    rows = episode_rows(checkout)
    edited = {**rows[42184], "title": {**rows[42184]["title"], "text": "A title the author never wrote"}}
    (release / "input/episodes.jsonl").write_text(
        "".join(json.dumps(edited if pr == 42184 else row) + "\n" for pr, row in rows.items()))
    provider.release = release.resolve()
    with pytest.raises(SystemExit) as refused:
        cli.main(["plan", "--reviewer", "solo-v1", "--case", "42184@c5474cb4"])
    assert refused.value.code == 2 and "input/episodes.jsonl" in capsys.readouterr().err


def test_a_case_names_exactly_one_reviewed_episode(checkout, provider, capsys):
    source = checkout / "inputs/probes/probe-2026-07-08-v1/input/episodes.jsonl"
    (episode,) = [json.loads(line) for line in source.read_text().split("\n")
                  if line.strip() and json.loads(line)["pr_number"] == 42184]
    later = {**episode, "reviewed_head_sha": "c5474cb4" + "f" * 32,
             "episode_id": episode["episode_id"].replace("round1", "round2")}
    provider.release = episodes_only_release(checkout, later)
    for head, problem in (("c5474cb4", "names 2 reviewed episodes"), ("0000000", "no reviewed episode")):
        with pytest.raises(SystemExit) as refused:
            cli.main(["plan", "--reviewer", "solo-v1", "--case", f"42184@{head}"])
        assert refused.value.code == 2 and problem in capsys.readouterr().err
    assert cli.main(["plan", "--reviewer", "solo-v1", "--case", "42184@c5474cb4a"]) == 0
    assert episode["reviewed_head_sha"] in capsys.readouterr().out
    assert provider.sessions == []


def test_overlapping_reviewers_can_finish_and_resume_independently(provider, frozen_history, monkeypatch):
    entered, release = Event(), Event()
    solo = run_options("solo-v1", "first")
    search = run_options("pr-search-v1", "second")

    async def interrupted_solo(self, tasks):
        if "precedent_search" in tasks[0].data.context_tools:
            return await provider(self, tasks)
        entered.set()
        assert release.wait(45)
        raise InterruptedError("lost solo session")

    monkeypatch.setattr(runner.TaskOrchestrator, "run", interrupted_solo)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(cli.main, solo)
        try:
            assert entered.wait(45)
            with pytest.raises(SystemExit) as duplicate:
                cli.main(solo)
            assert duplicate.value.code == 2
            assert cli.main(search) == 0
            _, archive = submissions.saved_reviews(submissions.review_directory("second"))
            assert archive["records"][0]["search_calls"] == 0
        finally:
            release.set()
        with pytest.raises(InterruptedError, match="lost solo session"):
            first.result()
    monkeypatch.setattr(runner.TaskOrchestrator, "run", provider)
    # The solo session was lost before acceptance, so its resume generates once.
    assert provider.sessions == ["second"]
    assert cli.main([*solo, "--resume"]) == 0
    assert provider.sessions == ["second", "first"]
    solo_plan, _ = submissions.saved_reviews(submissions.review_directory("first"))
    search_plan, _ = submissions.saved_reviews(submissions.review_directory("second"))
    ordinary = solo_plan["runs"]["solo-v1"]
    history = search_plan["runs"]["pr-search-v1"]
    assert ordinary["tasks_dir"] != history["tasks_dir"]
    a, b = ordinary["episodes"]["42184"], history["episodes"]["42184"]
    assert a["message_sha256"] == b["message_sha256"]
    assert set(b["mcp"]) - set(a["mcp"]) == {"precedent_search"}


def saved_42184_reviews(repo):
    """The two accepted 42184 submissions recorded by the historical route, as their author filed them."""
    saved = json.loads((repo / PROBE.parent / "convention-scope-2026-11-24/full_tool_reviews.json").read_text())
    reviews = {}
    for review in saved:
        sample = {"ordinary": "ordinary", "comparison": "guided"}[review["arm"]]
        reviews[sample] = {"message": review["review_message"], "findings": [
            {"claim": f["claim"], "suggested_fix": f["requested_change"], "path": f["anchor"]["path"],
             "line_start": f["anchor"]["line_start"], "line_end": f["anchor"]["line_end"]}
            for f in sorted(review["findings"], key=lambda f: f["submitted_rank"])]}
    return reviews


DISABLED_GENERATION = """
import sys
from ape.orchestration import TaskOrchestrator
from src.mathlib_review.review import cli, reviewers, runner

def refuse(*args, **kwargs):
    raise SystemExit("generation is disabled in this process")

TaskOrchestrator.run = runner.run = runner.review_episode = reviewers.run_reviewer = refuse
sys.exit(cli.main(sys.argv[1:]))
"""


def score_without_generation(repo, *args):
    env = {**os.environ, "PYTHONPATH": f"{repo / 'src'}{os.pathsep}{repo}"}
    done = subprocess.run([sys.executable, "-c", DISABLED_GENERATION, "score", *args],
                          env=env, capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stdout + done.stderr
    return done.stdout


def copy_reference(repo):
    reference = submissions.probes.load_probe_set(submissions.REFERENCE)
    reference.probe_dir.mkdir(parents=True, exist_ok=True)
    for path in (reference.asks_file, reference.feedback_file):
        shutil.copy(repo / path, path)


def matcher_messages(alias):
    """Each final matcher message prepared for one saved review, by question policy."""
    out = {}
    for path in Path(".ape/review-comparisons").rglob(submissions.matching.PLAN_FILE):
        plan = submissions.matching.load_plan(path.parent)
        if set(plan.seal["42184"].values()) == {alias}:
            policy = plan.identity.question_policy
            out[policy] = render_matcher_prompt(plan.packets, policy)
    return out


def test_named_reading_reproduces_the_pre_change_matcher_input(checkout, provider, frozen_history):
    saved = saved_42184_reviews(checkout)
    assert [len(saved[s]["findings"]) for s in ("ordinary", "guided")] == [1, 2]
    assert saved["guided"]["findings"][0]["line_start"] == 239
    for sample, reviewer in (("ordinary", "solo-v1"), ("guided", "pr-search-v1")):
        provider.reviews[sample] = saved[sample]
        assert cli.main(run_options(reviewer, sample)) == 0
    copy_reference(checkout)
    for sample in ("ordinary", "guided"):
        for scorer in ("round1-requests-v1", "round1-questions-v1"):
            score_without_generation(checkout, "--of", sample, "--using", scorer)
        rendered = matcher_messages(sample)
        assert set(rendered) == {"request_only", "questions"}
        for policy, text in rendered.items():
            baseline = checkout / PROBE / "before" / f"matcher-{sample}-named-{policy}.txt"
            assert text == baseline.read_text(), (sample, policy)
