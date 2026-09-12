"""A reviewed workspace: the base snapshot, the PR's diff, and its changed modules rebuilt.

The environment a PR is verified in has to be the one it was written in. The review overlay
applied the diff to source only and every compile resolved imports through the base commit's
build products, so a declaration the PR renames in a sibling file was an `Unknown constant`
whatever the PR's real state -- 41 of 321 arm sessions on the held-out run, 16 findings
asserting a build failure on PRs that all build.

These tests drive the builder with `lake` and the copy faked. What they pin is the part that
matters for a shared, read-only, 444-protected base: the state transitions, the atomic rename
into place, that nothing under the base path is ever opened for writing, and that a failed
build leaves neither a half-built workspace nor a BUILT state behind. The real build was
measured separately (33337: 67s, ten modules, base untouched, zero unknown constants).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from ape.toolkits.execute.lean.core.build_manager import (
    is_reviewed_workspace_key,
    lake_targets_for_changed_files,
    reviewed_workspace_key,
)

SHA = "a36c84ab8236a4869899268a42a44af07daa21ed"


# --- the key --------------------------------------------------------------------------------


def test_the_key_is_the_base_commit_plus_the_diffs_mark():
    key = reviewed_workspace_key(SHA, "--- a/x\n+++ b/x\n")
    assert key.startswith(SHA + "+") and len(key) == len(SHA) + 1 + 12
    assert is_reviewed_workspace_key(key) and not is_reviewed_workspace_key(SHA)


def test_the_key_is_deterministic_and_diff_sensitive():
    assert reviewed_workspace_key(SHA, "d1") == reviewed_workspace_key(SHA, "d1")
    assert reviewed_workspace_key(SHA, "d1") != reviewed_workspace_key(SHA, "d2")
    assert reviewed_workspace_key(SHA, "d1") != reviewed_workspace_key("b" * 40, "d1")


def test_the_key_uses_the_patch_markers_recipe():
    """Commit, NUL, diff -- the same bytes `ReviewPRCoreTask._patch_fingerprint` hashes, so
    the overlay's marker and the reviewed workspace agree on identity by construction."""

    import hashlib

    digest = hashlib.sha256(SHA.encode() + b"\0" + b"the diff").hexdigest()
    assert reviewed_workspace_key(SHA, "the diff") == f"{SHA}+{digest[:12]}"


# --- which modules to build -------------------------------------------------------------------


def test_targets_name_only_library_modules_that_still_exist(tmp_path):
    (tmp_path / "Mathlib.lean").write_text("")
    (tmp_path / "Mathlib/Analysis").mkdir(parents=True)
    (tmp_path / "Mathlib/Analysis/Positive.lean").write_text("")
    (tmp_path / "Mathlib/Analysis/Deleted.lean")  # not created: the PR deleted it
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/lint.lean").write_text("")   # no `scripts.lean` root: not a library
    (tmp_path / "docs.md").write_text("")

    targets = lake_targets_for_changed_files(
        ["Mathlib/Analysis/Positive.lean", "Mathlib/Analysis/Deleted.lean",
         "scripts/lint.lean", "docs.md", "Mathlib/Analysis/Positive.lean"], tmp_path)

    assert targets == ["+Mathlib.Analysis.Positive"]


def test_archive_and_counterexamples_are_libraries_too(tmp_path):
    for root in ("Archive", "Counterexamples"):
        (tmp_path / f"{root}.lean").write_text("")
        (tmp_path / root).mkdir()
        (tmp_path / root / "Thing.lean").write_text("")
    assert lake_targets_for_changed_files(
        ["Archive/Thing.lean", "Counterexamples/Thing.lean"], tmp_path
    ) == ["+Archive.Thing", "+Counterexamples.Thing"]


# --- the build, with Lake faked ---------------------------------------------------------------


class _State:
    def __init__(self, status=None):
        self.status = status
        self.file_count = 0


class _StateManager:
    """Records the transitions the builder asks for."""

    def __init__(self):
        self.calls = []

    async def try_start_build(self, key, force_rebuild=False):
        self.calls.append(("start", key))
        return _State(status="building")

    async def complete_build(self, key, success, duration, file_count=0, **kw):
        self.calls.append(("complete", key, success, kw.get("error_type")))
        return _State(status="built" if success else "failed")


def _base(tmp_path):
    """A miniature base workspace laid out like a restored one: 444 files, 555 dirs."""

    base = tmp_path / "workspaces" / SHA
    (base / "Mathlib/A").mkdir(parents=True)
    (base / "Mathlib.lean").write_text("import Mathlib.A.B\n")
    (base / "Mathlib/A/B.lean").write_text("theorem old : True := trivial\n")
    (base / ".lake/build/lib/lean/Mathlib/A").mkdir(parents=True)
    (base / ".lake/build/lib/lean/Mathlib/A/B.olean").write_bytes(b"olean")
    (base / ".lake/packages/batteries").mkdir(parents=True)
    (base / ".lake/packages/batteries/x").write_text("dep")
    for p in base.rglob("*"):
        os.chmod(p, 0o555 if p.is_dir() else 0o444)
    os.chmod(base, 0o555)
    return base


def _manager(tmp_path, state_manager, run_command):
    """A BuildManager with only what the reviewed build touches."""

    from types import SimpleNamespace

    from ape.toolkits.execute.lean.core.build_manager import BuildManager

    manager = BuildManager.__new__(BuildManager)
    manager.workspace_dir = tmp_path / "workspaces"
    manager.build_workspace_dir = tmp_path / "build_workspaces"
    manager.state_manager = state_manager
    manager.config = SimpleNamespace(build_timeout=60)
    manager.logger = SimpleNamespace(info=lambda *a, **k: None, error=lambda *a, **k: None,
                                     warning=lambda *a, **k: None, debug=lambda *a, **k: None)
    import ape.toolkits.execute.lean.core.build_manager as module
    module.run_command = run_command
    return manager


async def _prepare(build_root: Path, base_root: Path) -> None:
    """The task layer's job, done minimally: symlink the base, patch one source file."""

    build_root.mkdir(parents=True)
    for child in base_root.iterdir():
        (build_root / child.name).symlink_to(child)
    # materialise Mathlib/A/B.lean as a patched real copy
    (build_root / "Mathlib").unlink()
    (build_root / "Mathlib/A").mkdir(parents=True)
    (build_root / "Mathlib/A/B.lean").write_text("theorem new : True := trivial\n")


def test_a_reviewed_workspace_is_built_beside_the_base_and_renamed_into_place(tmp_path):
    base = _base(tmp_path)
    states = _StateManager()
    seen = {}

    async def fake_lake(cmd, cwd, **kw):
        seen["cmd"] = cmd
        seen["cwd"] = Path(cwd)
        # Lean writes an artifact where the real one would go
        out = Path(cwd) / ".lake/build/lib/lean/Mathlib/A/B.olean"
        out.write_bytes(b"rebuilt")
        return "", "", 0

    manager = _manager(tmp_path, states, fake_lake)
    key = reviewed_workspace_key(SHA, "diff")
    result = asyncio.run(manager.build_reviewed_workspace(
        key, SHA, prepare_sources=_prepare, targets=["+Mathlib.A.B"]))

    assert result.success
    final = tmp_path / "workspaces" / key
    assert final.is_dir(), "renamed into place under workspaces/<key>"
    assert seen["cmd"] == ["lake", "build", "+Mathlib.A.B"]
    assert seen["cwd"] != final, "Lake ran in the temp build dir, not the final path"
    assert seen["cwd"].parent == final.parent, "same parent: the rename never rewrites `..`"
    assert not [p for p in final.parent.iterdir() if p.name.startswith(".")], "temp dir removed"
    assert oct(final.stat().st_mode & 0o777) == "0o555", "finalised before the rename"
    assert oct((final / "Mathlib/A/B.lean").stat().st_mode & 0o777) == "0o444"
    assert (final / ".lake/build/lib/lean/Mathlib/A/B.olean").read_bytes() == b"rebuilt"
    assert (final / "Mathlib/A/B.lean").read_text().startswith("theorem new")
    assert (final / ".lake/packages").is_symlink(), "dependency packages stay shared"
    assert states.calls == [("start", key), ("complete", key, True, None)]


def test_the_base_is_never_written(tmp_path):
    """The whole design constraint. The base's 444 files turned every wrong guess into a loud
    failure during measurement; the builder must not rely on that -- it must not try."""

    base = _base(tmp_path)
    before = {p: p.stat().st_mtime_ns for p in base.rglob("*") if p.is_file()}
    olean = base / ".lake/build/lib/lean/Mathlib/A/B.olean"
    before_inode = olean.stat().st_ino

    async def fake_lake(cmd, cwd, **kw):
        (Path(cwd) / ".lake/build/lib/lean/Mathlib/A/B.olean").write_bytes(b"rebuilt")
        return "", "", 0

    manager = _manager(tmp_path, _StateManager(), fake_lake)
    asyncio.run(manager.build_reviewed_workspace(
        reviewed_workspace_key(SHA, "diff"), SHA, prepare_sources=_prepare, targets=["+M"]))

    after = {p: p.stat().st_mtime_ns for p in base.rglob("*") if p.is_file()}
    assert after == before
    assert olean.read_bytes() == b"olean" and olean.stat().st_ino == before_inode
    assert oct(olean.stat().st_mode & 0o777) == "0o444"


def test_a_failed_build_leaves_no_workspace_and_marks_failed(tmp_path):
    _base(tmp_path)
    states = _StateManager()

    async def failing_lake(cmd, cwd, **kw):
        return "", "error: Lean exited with code 1", 1

    manager = _manager(tmp_path, states, failing_lake)
    key = reviewed_workspace_key(SHA, "diff")
    with pytest.raises(RuntimeError, match="lake build"):
        asyncio.run(manager.build_reviewed_workspace(
            key, SHA, prepare_sources=_prepare, targets=["+M"]))

    assert not (tmp_path / "workspaces" / key).exists(), "nothing half-built left in place"
    assert not [p for p in (tmp_path / "workspaces").iterdir() if p.name.startswith(".")], \
        "temp dir removed"
    assert states.calls[-1][:3] == ("complete", key, False)


def test_an_already_built_key_is_not_rebuilt(tmp_path):
    class Built(_StateManager):
        async def try_start_build(self, key, force_rebuild=False):
            self.calls.append(("start", key))
            return _State(status=__import__("ape.toolkits.execute.lean.models",
                                            fromlist=["WorkspaceStatus"]).WorkspaceStatus.BUILT)

    ran = []

    async def lake(cmd, cwd, **kw):
        ran.append(cmd)
        return "", "", 0

    manager = _manager(tmp_path, Built(), lake)
    result = asyncio.run(manager.build_reviewed_workspace(
        reviewed_workspace_key(SHA, "d"), SHA, prepare_sources=_prepare, targets=["+M"]))
    assert result.success and result.build_duration == 0.0 and ran == []


def test_no_targets_is_refused_before_anything_is_copied(tmp_path):
    _base(tmp_path)

    async def lake(cmd, cwd, **kw):
        raise AssertionError("lake must not run")

    manager = _manager(tmp_path, _StateManager(), lake)
    with pytest.raises(RuntimeError, match="no Lake targets"):
        asyncio.run(manager.build_reviewed_workspace(
            reviewed_workspace_key(SHA, "d"), SHA, prepare_sources=_prepare, targets=[]))
