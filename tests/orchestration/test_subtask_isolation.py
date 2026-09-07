"""Every child gets its own workspace, and the guarantee is asserted rather than assumed.

`_ensure_patched_target_workspace` is destructive: it unlinks the snapshot symlink, builds a
symlink farm in its place, chmods it writable, copies changed files over it, and runs
`patch -p1`. Two tasks pointed at the same `target` would race on all five steps. The patch
marker written afterwards is not a lock -- it refuses a *different* patch, and only after the
fact.

Isolation holds today purely because `TaskStorage.get_attempt_path` returns a distinct path
per (task, sample, attempt) and the workspace hangs off it. That is a property of an unrelated
module, with no assertion, no lock and no test anywhere -- so a change to path derivation could
remove it silently, and the first symptom would be corrupted Lean workspaces under
concurrency.

These tests pin the derivation. They do not spawn anything: what is being checked is that two
children cannot be handed the same directory, which is a statement about paths.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ape.orchestration.persistence import TaskStorage


def _storage(tmp_path, task_id="gi1"):
    return TaskStorage(tmp_path / "tasks" / task_id, task_id)


def test_two_samples_of_one_task_get_different_attempt_paths(tmp_path):
    storage = _storage(tmp_path)
    assert storage.get_attempt_path(0, 1) != storage.get_attempt_path(1, 1)


def test_two_attempts_of_one_sample_get_different_paths(tmp_path):
    """A retry must not reuse its predecessor's workspace: the overlay it left behind carries
    a patch marker for a patch the retry may not be applying."""

    storage = _storage(tmp_path)
    assert storage.get_attempt_path(0, 1) != storage.get_attempt_path(0, 2)


def test_two_tasks_get_different_attempt_paths(tmp_path):
    first = _storage(tmp_path, "gi1").get_attempt_path(0, 1)
    second = _storage(tmp_path, "gi2").get_attempt_path(0, 1)
    assert first != second
    assert first.parent.parent.parent != second.parent.parent.parent


def test_an_attempt_path_is_under_its_own_task_directory(tmp_path):
    """The containment the trajectory reader and the evidence chain both rely on when they
    resolve a workspace back to the job that produced it."""

    storage = _storage(tmp_path, "gi1")
    attempt = storage.get_attempt_path(0, 1)
    assert storage.task_dir in attempt.parents


def test_the_workspace_hangs_off_the_attempt_path(tmp_path):
    """This is the whole isolation guarantee, in one line of `pr_review/core.py`. If the
    workspace were derived from the task or the orchestrator instead, every sibling arm would
    compile into one directory."""

    from ape.scaffolds.config import BaseScaffoldConfig

    name = BaseScaffoldConfig.model_fields["workspaces_dir_name"].default
    first = _storage(tmp_path, "gi1").get_attempt_path(0, 1) / name / "target"
    second = _storage(tmp_path, "gi2").get_attempt_path(0, 1) / name / "target"
    assert first != second
    # And the derivation itself, so a refactor that hangs the workspace off the task or the
    # orchestrator instead fails here rather than in a corrupted Lean build.
    source = Path(
        "src/ape/tasks/lean_tasks/formal_math/pr_review/core.py").read_text(encoding="utf-8")
    assert "attempt_path / config.workspaces_dir_name" in source


def test_the_patch_marker_is_not_a_lock(tmp_path):
    """Documented so nobody mistakes it for one. It records which patch an overlay carries and
    refuses a different one; it says nothing about a second writer applying the *same* patch
    concurrently, which is the race isolation actually prevents."""

    from ape.tasks.lean_tasks.formal_math.pr_review import core

    source = Path(core.__file__).read_text(encoding="utf-8")
    assert "_read_patch_marker" in source
    # The unlink-then-rebuild sequence that makes concurrent use unsafe.
    assert "target_path.unlink()" in source
    assert "_create_snapshot_overlay" in source


def test_nested_execution_does_not_inherit_a_process_pool(tmp_path):
    """A task already running inside a worker that spawns a nested orchestrator with
    `num_processes > 0` creates a process pool inside a pool. `_wave_config` sets it to 0, and
    that is load-bearing rather than incidental."""

    from ape.tasks.lean_tasks.formal_math.pr_review_v5 import delegation

    source = Path(delegation.__file__).read_text(encoding="utf-8")
    assert "num_processes = 0" in source or "num_processes=0" in source
