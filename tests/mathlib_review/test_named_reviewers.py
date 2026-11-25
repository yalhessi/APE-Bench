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

from ape.tasks.lean_tasks.formal_math.review.whole_pr import SubmittedFinding
from src.mathlib_review.analysis import submissions
from src.mathlib_review.io import pretty_json_bytes
from src.mathlib_review.judge.ask_matching import render_matcher_prompt
from src.mathlib_review.review import cli, reviewers, runner

PROBE = Path("results/pr_review_v5/probes/named-episode-review-2026-11-25")


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


@pytest.fixture
def provider(checkout, monkeypatch):
    # Supply only the commit date. Prior reviews and expert requests are absent during generation.
    put(Path("data/pr_review_v2/cache/bundles/pr_42184.json"), {"commits": [{
        "sha": "c5474cb4a68a515228b49225b38a2507264f91f7", "commit": {"committer": {"date": "2026-07-30T00:00:00Z"}}}]})
    original_load = runner.load_run

    def load(*args):
        dataset, scaffold, overrides = original_load(*args)
        scaffold.runs_base_dir = Path.cwd() / ".ape/runs"
        return dataset, scaffold, overrides

    monkeypatch.setattr(runner, "load_run", load)
    monkeypatch.setattr(runner, "assert_ready", lambda *a, **kw: None)

    async def prebuilt(*args, **kwargs):
        return []

    monkeypatch.setattr(runner, "assert_workspaces_prebuilt", prebuilt)
    monkeypatch.setattr(runner, "assert_reviewed_workspaces_prebuilt", prebuilt)

    async def accept(self, tasks):
        task, = tasks
        task_dir = self.tasks_dir / task.data.global_index
        plans = {path: submissions.read(path) for path in Path(".ape/reviews").glob("*/generation.json")}
        (plan_path, record), = [(path, run["episodes"]["42184"]) for path, plan in plans.items()
                                for run in plan["runs"].values() if run["run"] == self.orchestrator_id]
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
        review = reviews.get(Path(plan_path).parent.name, {})
        submitted = [SubmittedFinding(**finding) for finding in review.get("findings", [])]
        raw = {"pr_number": task.data.pr_number, "episode_id": task.data.episode_id, "success": True,
               "submitted_findings": [f.model_dump(exclude_unset=True) for f in submitted],
               "findings": [f.recorded() for f in submitted],
               "review_message": review.get("message", "No changes requested.")}
        put(folder / "sample.json", {"sample_id": "s", "sample_index": 0,
            "task_global_index": task.data.global_index, "created_at": "2026-11-25", "updated_at": "2026-11-25",
            "attempts": [{"attempt_id": 1, "path": str(attempt), "status": "success", "created_at": "2026-11-25",
                          "max_turns": record["max_turns"], "cost_limit": record["cost_cap"],
                          "token_limit": record["token_cap"], "result": raw}]})
        put(task_dir / "task_result.json", raw)
        return SimpleNamespace(task_results=[raw])

    reviews = {}
    accept.reviews = reviews
    monkeypatch.setattr(runner.TaskOrchestrator, "run", accept)

    return accept


def test_cli_accepts_empty_review_before_downstream_failure_and_can_read_it_again(checkout, provider, monkeypatch):
    alias = "solo-42184-a"
    out = submissions.review_directory(alias)
    opts = run_options("solo-v1", alias)

    def interrupt(*args):
        raise InterruptedError("post-processing interrupted")

    original_responses = runner.solo_responses
    monkeypatch.setattr(runner, "solo_responses", interrupt)
    with pytest.raises(InterruptedError, match="post-processing"):
        cli.main(opts)
    archived = submissions.read(out / "archive.json")["records"][0]
    assert archived["findings"] == 0
    raw_path = Path(archived["files"]["task_result.json"]["path"])
    assert submissions.read(raw_path)["review_message"] == "No changes requested."
    # A resume uses the accepted archive even though downstream reporting was interrupted.
    assert cli.main([*opts, "--resume"]) == 0
    with pytest.raises(SystemExit) as wrong_head:
        cli.main([*run_options("solo-v1", alias, "0000000"), "--resume"])
    assert wrong_head.value.code == 2
    monkeypatch.setattr(runner, "solo_responses", original_responses)
    second = "solo-42184-b"
    assert cli.main(run_options("solo-v1", second)) == 0
    monkeypatch.setattr(runner, "run", lambda *a, **kw: pytest.fail("scoring invoked reviewer"))
    reference = submissions.probes.load_probe_set(submissions.REFERENCE)
    reference.probe_dir.mkdir(parents=True)
    for path in (reference.asks_file, reference.feedback_file):
        shutil.copy(checkout / path, path)
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
    asks = submissions.read(reference.asks_file)
    asks["asks"]["42184"].pop()
    put(reference.asks_file, asks)
    assert cli.main([*score, "round1-requests-v1"]) == 0
    assert cli.main(paired) == 0
    assert sorted(p.expected_cells for p in plans()) == [1, 2, 2, 2, 4]
    raw_path.write_text("{}")
    with pytest.raises(ValueError, match="accepted task result changed"):
        submissions.saved_reviews(submissions.review_directory(alias))


def test_overlapping_reviewers_can_finish_and_resume_independently(provider, monkeypatch):
    from src.mathlib_review.retrieval.precedent_index import PrecedentIndex

    # Stand in only for the embedding data. The native runner seals the index and grants the tool.
    def index(collection):
        directory = Path("frozen-index")
        put(directory / "manifest.json", {"corpus_sha256": collection.sha256})
        return directory

    monkeypatch.setattr(reviewers.ExcerptCollection, "index", index)
    monkeypatch.setattr(PrecedentIndex, "shared", lambda *a, **kw: None)
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
    assert cli.main([*solo, "--resume"]) == 0
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

TaskOrchestrator.run = runner.run = reviewers.run_reviewer = refuse
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


def test_named_reading_reproduces_the_pre_change_matcher_input(checkout, provider, monkeypatch):
    from src.mathlib_review.retrieval.precedent_index import PrecedentIndex

    def index(collection):
        directory = Path("frozen-index")
        put(directory / "manifest.json", {"corpus_sha256": collection.sha256})
        return directory

    monkeypatch.setattr(reviewers.ExcerptCollection, "index", index)
    monkeypatch.setattr(PrecedentIndex, "shared", lambda *a, **kw: None)
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
