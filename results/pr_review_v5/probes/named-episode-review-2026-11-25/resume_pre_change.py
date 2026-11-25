"""Resume a named run recorded before the change, accepted but not yet archived, with the current code.

Usage: resume_pre_change.py <folder of a pre-change named test run> <alias> <checkout that started it>

The generation record hashes the scaffold, whose tool paths resolve from the checkout's configs, so
the resume reads the configs of the checkout the run was started from, as a researcher's would.

The folder is one of the test directories written at 067749d3 (see README). Its archive is removed
first, which leaves the state of a run interrupted after acceptance. A new session raises in this process,
no credential is needed, and the resume must archive the accepted session again, byte for byte.
"""
import shutil
import sys
from pathlib import Path

from ape.orchestration import TaskOrchestrator
from src.mathlib_review.analysis import submissions
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
    assert (out / "generation.json").read_bytes() == generation, "the pre-change generation record was rewritten"
    # The run sealed its inputs in its run plan, so the resume records no other copy of them.
    assert not (out / submissions.INPUTS_FILE).exists(), "the resume recorded inputs the run plan already sealed"
    assert (out / "archive.json").read_bytes() == before, "the resumed archive differs from the pre-change one"
finally:
    # Put the pre-change folder back, so the check can be run again.
    shutil.rmtree(out)
    shutil.move(root / f"{alias}.saved", out)
print(f"resumed {alias}: archive bytes identical")
