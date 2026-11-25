"""Reopen named archives written by the pre-change code, using the current code, generation disabled."""
import os
import shutil
import sys
from pathlib import Path

from ape.orchestration import TaskOrchestrator
from src.mathlib_review.analysis import submissions
from src.mathlib_review.judge.ask_matching import render_matcher_prompt
from src.mathlib_review.review import cli, reviewers, runner


def refuse(*args, **kwargs):
    raise SystemExit("generation is disabled in this process")


TaskOrchestrator.run = runner.run = runner.review_episode = reviewers.run_reviewer = refuse

root = Path(sys.argv[1])
baseline = Path(sys.argv[2])
os.chdir(root)
for alias in ("ordinary", "guided"):
    out = submissions.review_directory(alias)
    generation, archive = submissions.saved_reviews(out)
    assert all("inputs" not in run for run in generation["runs"].values()), "expected a pre-change generation"
    for scorer in ("round1-requests-v1", "round1-questions-v1"):
        assert cli.main(["score", "--of", alias, "--using", scorer]) == 0
    for plan_file in Path(".ape/review-comparisons").rglob(submissions.matching.PLAN_FILE):
        plan = submissions.matching.load_plan(plan_file.parent)
        if set(plan.seal["42184"].values()) == {alias}:
            policy = plan.identity.question_policy
            text = render_matcher_prompt(plan.packets, policy)
            same = text == (baseline / f"matcher-{alias}-named-{policy}.txt").read_text()
            print(f"reopened {alias}: {archive['records'][0]['findings']} findings, {policy} matcher input "
                  f"{'matches' if same else 'DIFFERS FROM'} the pre-change bytes")
            assert same

# A pre-change generation interrupted before its archive: recovered through its run plan.
out = submissions.review_directory("guided")
before = (out / "archive.json").read_bytes()
(out / "archive.json").unlink()
shutil.rmtree(out / "submissions")
generation, archive = submissions.saved_reviews(out, recover=True)
run_name = generation["runs"]["pr-search-v1"]["run"]
assert Path("results/pr_review_v5/runs", run_name, "run_plan.json").is_file()
print("recovered guided from run_plan.json; archive bytes", "identical" if (out / "archive.json").read_bytes() == before
      else "differ")
