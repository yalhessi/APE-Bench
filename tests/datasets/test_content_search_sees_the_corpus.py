"""`content_search` must see through a workspace overlay, and must say when it did not look.

Both halves are regressions from one measured failure. A review attempt's `target/` is a farm
of symlinks into a shared read-only workspace with only the PR's own subtree materialised.
`Path.rglob` does not descend a symlinked directory, so `content_search(path="target/Mathlib")`
reached 66 of Mathlib's 7,443 files -- and reported no total, no truncation, no error. The
naming arm asked repository-wide convention questions (39 of 109 calls scoped to
`target/Mathlib`, 60 of 109 with regex), was handed its own neighbourhood with the corpus's
authority, and correctly concluded there was no convention to cite.

The second half is the `limit` cap: even with full reach, a census would have come back at 20
files with nothing saying so. `analysis/evidence.py` already refuses to read a naming
population from a partial tree, calling it "a 2% sample that still clears MIN_SUPPORT"; the
search tool is where that sample was produced.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from ape.toolkits.file_system.utils import resolve_search_paths, walk_workspace_files


def _overlay(tmp_path: Path) -> tuple[Path, Path]:
    """A base tree and an overlay of symlinks into it, shaped like a review attempt."""

    base = tmp_path / "base"
    (base / "Mathlib" / "Analysis").mkdir(parents=True)
    (base / "Mathlib" / "Order").mkdir(parents=True)
    (base / "Mathlib" / "Analysis" / "Far.lean").write_text("theorem toLinearMap_far : True := trivial\n")
    (base / "Mathlib" / "Order" / "Other.lean").write_text("theorem toLinearMap_other : True := trivial\n")
    (base / ".lake" / "build" / "lib").mkdir(parents=True)
    for i in range(5):
        (base / ".lake" / "build" / "lib" / f"artifact{i}.lean").write_text("theorem toLinearMap_junk : True := trivial\n")

    ws = tmp_path / "ws"
    target = ws / "target"
    (target / "Mathlib").mkdir(parents=True)
    # The PR's own directory is real; every sibling is a symlink into the base.
    (target / "Mathlib" / "Touched").mkdir()
    (target / "Mathlib" / "Touched" / "Edited.lean").write_text("theorem coe_edited : True := trivial\n")
    (target / "Mathlib" / "Analysis").symlink_to(base / "Mathlib" / "Analysis")
    (target / "Mathlib" / "Order").symlink_to(base / "Mathlib" / "Order")
    (target / ".lake").symlink_to(base / ".lake")
    return ws, base


def test_a_directory_search_descends_symlinked_siblings(tmp_path):
    ws, _base = _overlay(tmp_path)
    found = resolve_search_paths(Path("target/Mathlib"), ws, True, None)
    names = sorted(p.name for p in found)
    assert names == ["Edited.lean", "Far.lean", "Other.lean"], (
        f"the symlinked siblings must be reachable, got {names}")


def test_hidden_directories_are_skipped_below_the_root(tmp_path):
    """`.lake` holds ~96k build artifacts on a real workspace: walking it cost 23 s and still
    missed Mathlib. `glob` already skips hidden names in the wildcard branch, so this also
    makes the two branches of the resolver agree."""

    ws, _base = _overlay(tmp_path)
    found = resolve_search_paths(Path("target"), ws, True, None)
    assert not [p for p in found if ".lake" in p.parts], "build artifacts must not be walked"
    assert sorted(p.name for p in found) == ["Edited.lean", "Far.lean", "Other.lean"]


def test_an_explicit_hidden_path_still_works(tmp_path):
    """Only descendants are pruned. An operator who names `.lake` means it."""

    ws, _base = _overlay(tmp_path)
    found = resolve_search_paths(Path("target/.lake/build/lib"), ws, True, None)
    assert len(found) == 5


def test_a_symlink_cycle_terminates(tmp_path):
    root = tmp_path / "root"
    (root / "a").mkdir(parents=True)
    (root / "a" / "f.lean").write_text("x")
    (root / "a" / "loop").symlink_to(root)
    assert [p.name for p in walk_workspace_files(root)] == ["f.lean"]


def test_non_recursive_is_one_level(tmp_path):
    ws, _base = _overlay(tmp_path)
    found = resolve_search_paths(Path("target/Mathlib"), ws, False, None)
    assert found == [], "no files sit directly in target/Mathlib; only directories do"


@pytest.fixture
def searcher(tmp_path):
    import logging

    from ape.toolkits.file_system.config import FileSystemToolConfig
    from ape.toolkits.file_system.core import FileSystemProvider

    ws, _base = _overlay(tmp_path)
    ops = FileSystemProvider.__new__(FileSystemProvider)
    ops.workspaces_dir = ws
    ops.fs_config = FileSystemToolConfig()
    ops.logger = logging.getLogger("test")
    return ops


def test_a_complete_search_reports_its_coverage(searcher):
    result = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib"), max_results=20))
    assert result["success"]
    assert result["truncated"] is False
    assert result["files_available"] == 3 and result["files_scanned"] == 3
    assert result["files_with_matches"] == 2
    assert "note" not in result


def test_a_truncated_search_says_it_is_a_sample(searcher):
    """The failure this exists to stop: a capped search reading as an absence, or as a count."""

    result = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib"), max_results=1))
    assert result["truncated"] is True
    assert result["files_with_matches"] == 1 and result["files_available"] == 3
    assert "SAMPLE, not a census" in result["note"]
