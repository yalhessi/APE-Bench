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


# ---------------------------------------------------------------------------------------
# The grep prefilter. It exists for speed, so the only thing worth testing is that speed
# bought nothing else: the same results, the same coverage numbers, and a full scan whenever
# grep cannot answer. Measured before it was written -- whole-tree `content_search` was 26-30%
# of all arm wall time on a 12-PR run, and its throughput was flat from concurrency 1 to 8
# because ~8,500 `asyncio.to_thread` dispatches per search saturate the 32-worker pool that
# `aiofiles` also writes through.


def _no_grep(*_args, **_kwargs):
    """Stand-in for grep declining: a bad pattern, a missing binary, a timeout."""

    return None


def test_the_prefilter_does_not_change_results_or_coverage(searcher, monkeypatch):
    """Same answer with and without it, fields included -- `files_available`/`files_scanned`
    are the census-vs-sample signal and must count the search space, not the survivors."""

    with_grep = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib"), max_results=20))
    monkeypatch.setattr("ape.toolkits.file_system.core.grep_candidate_files", _no_grep)
    without = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib"), max_results=20))
    assert with_grep == without, "the prefilter may only save I/O, never change the answer"
    assert with_grep["files_available"] == 3 and with_grep["files_scanned"] == 3


def test_a_declining_grep_falls_back_to_the_full_scan(searcher, monkeypatch):
    """`None` means "I did not answer", and must never be read as "nothing matched"."""

    monkeypatch.setattr("ape.toolkits.file_system.core.grep_candidate_files", _no_grep)
    result = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib"), max_results=20))
    assert result["files_with_matches"] == 2


def test_an_empty_candidate_set_is_not_a_declining_grep(searcher, monkeypatch):
    """The distinction the fallback rests on: `set()` is an answer, `None` is not."""

    monkeypatch.setattr("ape.toolkits.file_system.core.grep_candidate_files",
                        lambda *a, **k: set())
    result = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib"), max_results=20))
    assert result["files_with_matches"] == 0
    assert result["files_scanned"] == 3, "coverage is still the whole search space"


def test_the_prefilter_reaches_through_a_symlinked_overlay(tmp_path):
    """The reach regression this file exists for, now on the grep side: a review attempt's
    `target/` is a symlink farm, and a prefilter that missed the siblings would silently
    shrink every repository-wide search back to the PR's own neighbourhood."""

    from ape.toolkits.file_system.utils import grep_candidate_files

    ws, _base = _overlay(tmp_path)
    files = resolve_search_paths(Path("target/Mathlib"), ws, True, None)
    found = grep_candidate_files("toLinearMap", files)
    assert found is not None
    assert sorted(Path(p).name for p in found) == ["Far.lean", "Other.lean"]


def test_the_prefilter_never_drops_a_file_the_matcher_would_keep(tmp_path):
    """Soundness is one-sided and is the whole contract: extra files cost a wasted read, a
    missing one loses a result. Checked against the matcher itself over the real patterns'
    shapes -- alternation, escapes, anchors, character classes."""

    import re

    from ape.toolkits.file_system.utils import (
        grep_candidate_files, search_content_with_timeout)

    root = tmp_path / "corpus"
    root.mkdir()
    texts = {
        "a.lean": "theorem Nat.ceil_natCast_add : True := trivial\n@[simp] lemma foo : 1 = 1 := rfl\n",
        "b.lean": "-- #check Meromorphic\nset_option linter.style.commandStart false\n",
        "c.lean": "structure T3 where\n  x : Nat\n",
        "d.lean": "nothing of interest here\n",
    }
    for name, text in texts.items():
        (root / name).write_text(text)
    files = sorted(root.glob("*.lean"))

    for pattern in [r"ceil.*natCast.*add", r"#check|#print", r"set_option linter\.style\.commandStart",
                    r"^structure T3\b", r"\[simp\]", r"Meromorphic", r"[A-Z][a-z]+\.ceil"]:
        rx = re.compile(pattern, re.MULTILINE)
        expected = {
            str(path) for path in files
            if search_content_with_timeout(path.read_text(), pattern, True, 5.0)
        }
        candidates = grep_candidate_files(pattern, files)
        assert candidates is not None, f"grep declined {pattern!r}"
        assert expected <= candidates, (
            f"{pattern!r}: grep missed {expected - candidates}, which the matcher accepts")
