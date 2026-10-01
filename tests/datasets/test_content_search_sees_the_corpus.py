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
    """A real provider, built the way the scaffold builds one.

    This used to hand-assemble the object through `__new__` and set the three attributes the
    tests happened to reach. That broke the moment the provider grew per-attempt state (the
    search-path cache), and it would break again for the next one -- so it now goes through
    `__init__` and only the task is a stand-in.
    """

    import types

    from ape.scaffolds.config import BaseScaffoldConfig
    from ape.toolkits.file_system.core import FileSystemProvider

    ws, _base = _overlay(tmp_path)
    return FileSystemProvider(
        task=types.SimpleNamespace(workspaces_dir=ws),
        config=BaseScaffoldConfig(scaffold_type="ape_agent"),
    )


def test_a_complete_search_reports_its_coverage(searcher):
    result = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib"), max_results=20))
    assert result["success"]
    assert result["truncated"] is False
    assert result["files_available"] == 3 and result["files_scanned"] == 3
    assert result["files_with_matches"] == 2
    assert "note" not in result


def test_a_bad_path_is_not_a_search_that_found_nothing(searcher):
    """Two negatives, told apart: a path with no files under it searched nothing (a bad request),
    while a real path with no match ran and found nothing. "No files found for path" read as the
    second; at least 13 calls on six gpt runs (2026-09-30) were the first."""

    bad = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib/NoSuchDir")))
    assert bad["success"] is False and bad["outcome"] == "invalid_request"
    assert "Nothing was searched" in bad["error"]
    empty = asyncio.run(searcher.content_search(
        content_pattern="noSuchIdentifierAnywhere", search_path=Path("target/Mathlib")))
    assert empty["success"] is True and empty["results"] == [] and "outcome" not in empty


def test_file_search_finds_a_file_by_its_name_through_the_overlay(searcher):
    """No test had ever called `file_search`. It matched the pattern against the workspace path
    only, so `Far.lean` -- a file name, as the tool's own examples suggest -- found nothing, as an
    ordinary empty result. It is granted to the contract condition, so it is exercised here."""

    by_name = asyncio.run(searcher.file_search(pattern="Far.lean", directory_path=Path("target")))
    assert by_name["success"] and [r["path"] for r in by_name["results"]] == [
        "target/Mathlib/Analysis/Far.lean"]
    assert by_name["truncated"] is False
    glob = asyncio.run(searcher.file_search(pattern="*.lean", directory_path=Path("target/Mathlib")))
    assert sorted(r["path"].rsplit("/", 1)[-1] for r in glob["results"]) == [
        "Edited.lean", "Far.lean", "Other.lean"]
    capped = asyncio.run(searcher.file_search(pattern="*.lean", directory_path=Path("target"),
                                              max_results=2))
    assert len(capped["results"]) == 2 and capped["truncated"] is True and "note" in capped
    missing = asyncio.run(searcher.file_search(pattern="*.lean", directory_path=Path("target/Nope")))
    assert missing["success"] is False and missing["outcome"] == "invalid_request"
    nothing = asyncio.run(searcher.file_search(pattern="NoSuch*.lean", directory_path=Path("target")))
    assert nothing["success"] is True and nothing["results"] == [] and "outcome" not in nothing


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


async def _no_grep(*_args, **_kwargs):
    """Stand-in for grep declining: a bad pattern, a missing binary, a timeout."""

    return None


async def _grep_finds_nothing(*_args, **_kwargs):
    """Stand-in for grep answering, with an empty answer."""

    return set()


def test_the_prefilter_does_not_change_results_or_coverage(searcher, monkeypatch):
    """Same answer with and without it, fields included -- `files_available`/`files_scanned`
    are the census-vs-sample signal and must count the search space, not the survivors."""

    with_grep = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib"), max_results=20))
    monkeypatch.setattr("ape.toolkits.file_system.core.grep_candidate_files_async", _no_grep)
    without = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib"), max_results=20))
    assert with_grep == without, "the prefilter may only save I/O, never change the answer"
    assert with_grep["files_available"] == 3 and with_grep["files_scanned"] == 3


def test_a_declining_grep_falls_back_to_the_full_scan(searcher, monkeypatch):
    """`None` means "I did not answer", and must never be read as "nothing matched"."""

    monkeypatch.setattr("ape.toolkits.file_system.core.grep_candidate_files_async", _no_grep)
    result = asyncio.run(searcher.content_search(
        content_pattern="toLinearMap", search_path=Path("target/Mathlib"), max_results=20))
    assert result["files_with_matches"] == 2


def test_an_empty_candidate_set_is_not_a_declining_grep(searcher, monkeypatch):
    """The distinction the fallback rests on: `set()` is an answer, `None` is not."""

    monkeypatch.setattr("ape.toolkits.file_system.core.grep_candidate_files_async",
                        _grep_finds_nothing)
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


# ---------------------------------------------------------------------------------------
# The search-path cache. The walk is the part of a search that cannot be made concurrent --
# it is Python holding the GIL -- and it was being redone on every call over a tree that
# does not change. Measured over Mathlib's 7,435 files, one walk per concurrent search:
# 0.16s at 1, 3.01s at 16, i.e. no speedup at all, while grep over the same files went
# 0.68s -> 2.15s. These tests pin the two halves of the contract: it is reused, and a write
# drops it.


def test_the_search_path_walk_happens_once(searcher, monkeypatch):
    walks = []
    real = resolve_search_paths

    def counted(*args, **kwargs):
        walks.append(args[0])
        return real(*args, **kwargs)

    monkeypatch.setattr("ape.toolkits.file_system.core.resolve_search_paths", counted)
    for _ in range(3):
        asyncio.run(searcher.content_search(
            content_pattern="toLinearMap", search_path=Path("target/Mathlib")))
    assert len(walks) == 1, f"the tree was re-walked {len(walks)} times for one search path"


def test_distinct_search_paths_are_cached_separately(searcher, monkeypatch):
    walks = []
    real = resolve_search_paths
    monkeypatch.setattr("ape.toolkits.file_system.core.resolve_search_paths",
                        lambda *a, **k: (walks.append(a[0]), real(*a, **k))[1])
    asyncio.run(searcher.content_search(content_pattern="x", search_path=Path("target/Mathlib")))
    asyncio.run(searcher.content_search(content_pattern="x", search_path=Path("target")))
    asyncio.run(searcher.content_search(content_pattern="x", search_path=Path("target/Mathlib")))
    assert len(walks) == 2, "a different search path is a different question"


def test_a_write_invalidates_the_cached_walk(searcher):
    """The one thing that can make the cache wrong: a file that did not exist when we walked.
    Without this the arm writes a file and then cannot find it."""

    before = asyncio.run(searcher.content_search(
        content_pattern="brand_new_lemma", search_path=Path("target/Mathlib")))
    assert before["files_with_matches"] == 0

    written = asyncio.run(searcher.file_write(
        file_path=Path("target/Mathlib/Touched/New.lean"),
        content="theorem brand_new_lemma : True := trivial\n", execute=False))
    assert written["success"], written

    after = asyncio.run(searcher.content_search(
        content_pattern="brand_new_lemma", search_path=Path("target/Mathlib")))
    assert after["files_with_matches"] == 1, "a search after a write must see the new file"
    assert after["files_available"] == before["files_available"] + 1
