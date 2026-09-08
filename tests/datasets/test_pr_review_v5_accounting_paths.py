"""Two one-line defects that were invisible because neither raised where anyone looked.

`_patch_set_workspace` used `Path` in a module that never imported it, so the only arm allowed
to submit a coordinated patch (`family_design`, the sole member of `PATCH_SET_ARMS`) would have
received a raw traceback instead of a rejection message and burned turns on it.

`_sample_cost` read `sample.json` three directories above the result, which resolves to the
orchestrator root and never exists. It returned `(None, None, None)` every time, so the
trajectory sidecar reported the no-cache counterfactual as if it were spend.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_the_patch_set_workspace_resolves_instead_of_raising():
    """`Path` is imported. Before, any patch_set submission raised NameError."""

    from ape.tasks.lean_tasks.formal_math.review.candidates import (
        LeanPRReviewV4CandidateTask,
    )

    task = LeanPRReviewV4CandidateTask.__new__(LeanPRReviewV4CandidateTask)
    task.target_workspace = "/tmp/reviewed/workspace"
    assert LeanPRReviewV4CandidateTask._patch_set_workspace(task) == Path(
        "/tmp/reviewed/workspace")

    task.target_workspace = None
    assert LeanPRReviewV4CandidateTask._patch_set_workspace(task) is None


def _write_sample(task_dir: Path, attempts):
    sample_dir = task_dir / "samples" / "0"
    sample_dir.mkdir(parents=True, exist_ok=True)
    (sample_dir / "sample.json").write_text(
        json.dumps({"status": "success", "attempts": attempts}), encoding="utf-8")
    result = task_dir / "task_result.json"
    result.write_text(json.dumps({"task_id": "t"}), encoding="utf-8")
    return result


def test_sample_cost_finds_the_sample_beside_the_result(tmp_path):
    from src.mathlib_review.analysis.trajectory import _sample_cost

    result = _write_sample(
        tmp_path / "tasks" / "gi",
        [{"cost": 0.30, "cached_cost": 0.12, "status": "success"}],
    )
    cost, cached, status = _sample_cost(result)
    assert cost == pytest.approx(0.30)
    assert cached == pytest.approx(0.12)
    assert status == "success"


def test_sample_cost_accumulates_across_attempts(tmp_path):
    """A sample that paused and resumed spent the sum; reading the last attempt understates."""

    from src.mathlib_review.analysis.trajectory import _sample_cost

    result = _write_sample(
        tmp_path / "tasks" / "gi",
        [
            {"cost": 0.40, "cached_cost": 0.18, "status": "paused_cost_limit"},
            {"cost": 0.20, "cached_cost": 0.09, "status": "success"},
        ],
    )
    cost, cached, status = _sample_cost(result)
    assert cost == pytest.approx(0.60)
    assert cached == pytest.approx(0.27)
    assert status == "success"


def test_sample_cost_falls_back_to_nominal_when_no_billed_figure(tmp_path):
    from src.mathlib_review.analysis.trajectory import _sample_cost

    result = _write_sample(
        tmp_path / "tasks" / "gi", [{"cost": 0.25, "status": "success"}])
    cost, cached, _ = _sample_cost(result)
    assert cost == pytest.approx(0.25)
    assert cached == pytest.approx(0.25)
