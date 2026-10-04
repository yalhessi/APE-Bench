"""`cli run --resume` continues an interrupted run, and only that.

`guard_run_name` refuses any run name with results or orchestrator state, because the name is the
orchestrator's resume key and a rerun after a code change would report cached attempts as new. That
left a run killed before it wrote anything with two options, discard it or pay for it again.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from src.mathlib_review.review import runner

LOGGER = logging.getLogger("test")


@pytest.fixture
def layout(tmp_path, monkeypatch):
    results, scratch = tmp_path / "results", tmp_path / "scratch"
    monkeypatch.setattr(runner, "run_dir", lambda name: results / name)
    return results, scratch, SimpleNamespace(runs_base_dir=scratch), SimpleNamespace(run_name="r")


def test_an_interrupted_run_resumes_with_a_warning(layout, caplog):
    results, scratch, scaffold, dataset = layout
    (scratch / "r").mkdir(parents=True)
    (results / "r").mkdir(parents=True)
    (results / "r" / "agenda.json").write_text("{}")  # written before execution, not an output
    with caplog.at_level(logging.WARNING):
        runner.guard_run_name(dataset, LOGGER, scaffold, resume=True)
    assert "resuming 'r'" in caplog.text


def test_without_resume_the_same_run_is_still_refused(layout):
    results, scratch, scaffold, dataset = layout
    (scratch / "r").mkdir(parents=True)
    with pytest.raises(RuntimeError, match="already been executed"):
        runner.guard_run_name(dataset, LOGGER, scaffold)


def test_a_finished_run_is_not_resumed(layout):
    results, scratch, scaffold, dataset = layout
    (scratch / "r").mkdir(parents=True)
    (results / "r").mkdir(parents=True)
    (results / "r" / "findings.jsonl").write_text("")
    with pytest.raises(RuntimeError, match="finished"):
        runner.guard_run_name(dataset, LOGGER, scaffold, resume=True)


def test_there_must_be_something_to_resume(layout):
    _results, _scratch, scaffold, dataset = layout
    with pytest.raises(RuntimeError, match="nothing to resume"):
        runner.guard_run_name(dataset, LOGGER, scaffold, resume=True)


def test_redo_and_resume_cannot_be_combined():
    from src.mathlib_review.review import cli

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["run", "--config", "x.yaml", "--run-name", "r", "--redo", "--resume"])
    assert excinfo.value.code == 2  # argparse's usage error, before any config is read
