"""A workspace-relative path must reach the Lean LSP as an absolute one.

The three LSP-backed tools -- `get_lean_goal`, `code_hover`, `code_goto` -- hand the provider
exactly what the agent typed, e.g. `target/Mathlib/Topology/MetricSpace/CoveringNumbers.lean`.
`find_project_path` then walked *up from that relative path*, so it looked for
`target/lean-toolchain` beneath the process working directory rather than beneath the task's
workspace, found nothing, and raised "Cannot find Lean project".

Measured across every rung of the oracle ladder: **122 `get_lean_goal` calls, 122 failures**.
No arm ever inspected a goal state, and rung 3a -- whose entire hypothesis was "inspect the goal
before proposing" -- could not have passed whatever the model did.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ape.toolkits.code.lean.provider import LeanCodeToolsProvider
from ape.toolkits.code.lean.utils import find_project_path


def _provider(workspace: Path) -> LeanCodeToolsProvider:
    """The provider's path logic, without constructing an LSP client."""

    provider = LeanCodeToolsProvider.__new__(LeanCodeToolsProvider)
    provider._workspace_root = workspace
    return provider


@pytest.fixture()
def workspace(tmp_path):
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.27.0-rc1\n", encoding="utf-8")
    target = tmp_path / "target" / "Mathlib" / "Topology"
    target.mkdir(parents=True)
    (target / "Thing.lean").write_text("theorem foo : True := by trivial\n", encoding="utf-8")
    return tmp_path


def test_the_bug_a_relative_path_finds_no_project(workspace):
    """Pinned so the failure mode cannot come back silently: this is what the arms hit 122
    times, and it surfaced as a tool error rather than as a missing capability."""

    assert find_project_path(Path("target/Mathlib/Topology/Thing.lean")) is None


def test_a_resolved_path_finds_the_project(workspace):
    resolved = _provider(workspace)._resolve_in_workspace(
        Path("target/Mathlib/Topology/Thing.lean"))
    assert resolved.is_file()
    assert find_project_path(resolved) == workspace.resolve()


def test_an_absolute_path_is_left_alone(workspace):
    """Callers that resolve for themselves keep working."""

    absolute = (workspace / "target/Mathlib/Topology/Thing.lean").resolve()
    assert _provider(workspace)._resolve_in_workspace(absolute) == absolute


def test_traversal_is_refused(workspace):
    """Same rule as `file_system.core._resolve_path`, which these tools should never have
    diverged from."""

    with pytest.raises(ValueError) as excinfo:
        _provider(workspace)._resolve_in_workspace(Path("../../etc/passwd"))
    assert "Parent directory references" in str(excinfo.value)


def test_every_lsp_entry_point_resolves_before_finding_the_project():
    """hover, goto, diagnostics and get_goal all took the raw path; a fix to one is not a fix."""

    import inspect

    source = inspect.getsource(LeanCodeToolsProvider)
    assert source.count("self._resolve_in_workspace(file_path)") == 4
