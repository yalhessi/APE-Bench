"""Resume a named run recorded before the change, accepted but not yet archived, with the current code.

Usage: resume_pre_change.py <folder of a pre-change named test run> <alias> <checkout that started it>

The generation record hashes the scaffold, whose tool paths resolve from the checkout's configs, so
the resume reads the configs of the checkout the run was started from, as a researcher's would.

The folder is one of the test directories written at 067749d3 (see README). Its archive is removed
first, which leaves the state of a run interrupted after acceptance. A new session raises in this process,
no credential is needed, and the resume must archive the accepted session again, unchanged apart from the inputs it now records.
"""
import json
import shutil
import sys
from pathlib import Path

from ape.orchestration import TaskOrchestrator
from src.mathlib_review.analysis import submissions
from src.mathlib_review.io import sha256_file
from src.mathlib_review.review import cli, runner


async def refuse(*args, **kwargs):
    raise SystemExit("generation is disabled in this process")


root, alias, repo = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3])
for name in ("configs", "inputs"):
    link = root / name
    link.unlink()
    link.symlink_to(repo / name)
original_load = runner.load_run


def load(*args):
    # The pre-change test kept its orchestrator state under its own folder.
    dataset, scaffold, overrides = original_load(*args)
    scaffold.runs_base_dir = root / ".ape/runs"
    return dataset, scaffold, overrides


runner.load_run = load
TaskOrchestrator._execute_jobs = refuse  # the orchestrator may reconcile, never start a session

import os

os.chdir(root)
out = submissions.review_directory(alias)
before = (out / "archive.json").read_bytes()
generation = (out / "generation.json").read_bytes()
shutil.copytree(out, root / f"{alias}.saved")
(out / "archive.json").unlink()
shutil.rmtree(out / "submissions")
reviewer = next(iter(submissions.read(out / "generation.json")["runs"]))
try:
    assert cli.main(["run", "--reviewer", reviewer, "--case", "42184@c5474cb4", "--run-name", alias,
                     "--execute", "--resume"]) == 0
except BaseException:
    shutil.rmtree(out)
    shutil.copytree(root / f"{alias}.saved", out)
    raise
assert (out / "generation.json").read_bytes() == generation, "the pre-change generation record was rewritten"
# The resume records the run's inputs before it could dispatch a reviewer, so the archive gains their
# digest. Everything else, every archived file included, must be what the pre-change code archived.
rebuilt, original = submissions.read(out / "archive.json"), json.loads(before)
assert rebuilt.pop("inputs_sha256") == sha256_file(out / submissions.INPUTS_FILE)
assert rebuilt == original, "the resumed archive differs from the pre-change one"
for record in original["records"]:
    for kept in record["files"].values():
        assert sha256_file(Path(kept["path"])) == kept["sha256"], kept["path"]
(name,) = (run["run"] for run in submissions.read(out / "generation.json")["runs"].values())
sealed = json.loads((Path("results/pr_review_v5/runs") / name / "run_plan.json").read_bytes())
assert submissions.read(out / submissions.INPUTS_FILE)[name]["design"] == sealed["evaluation_settings"]["design"]
print(f"resumed {alias}: archive identical apart from the added inputs digest; inputs agree with its run plan")
