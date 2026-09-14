"""The reviewed workspace for PR 33337, if this machine has built it.

The unit tests prove the builder on a miniature; this checks the real artifact the probe runs
verify in, structurally and cheaply (no Lean is compiled here -- a Mathlib file is tens of
seconds). It skips where the workspace is absent, which is every fresh clone: "Tests that need
a built Lean workspace under `data/code_execute/` fail on a fresh clone; expected", and a skip
is the honest form of that.

33337 is the PR the whole defect was diagnosed on: two changed files, `Positive.lean` importing
a lemma that `Projection/Submodule.lean` renames in the same PR. In the source-only overlay
that lemma was `Unknown constant` when `Positive.lean` was verified; in the reviewed workspace
`Submodule`'s `.olean` is the PR's.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest

from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.3.0")
PR = 33337


def _episode():
    for line in (RELEASE / "input/episodes.jsonl").read_text(encoding="utf-8").split("\n"):
        if line.strip():
            row = json.loads(line)
            if row["pr_number"] == PR:
                return row
    raise AssertionError(f"PR {PR} is not in {RELEASE}")


@pytest.fixture(scope="module")
def reviewed():
    episode = _episode()
    key = reviewed_workspace_key(episode["base_sha"], episode["diff"])
    root = LeanVerifyToolConfig().get_workspace_dir("mathlib4") / key
    if not (root / "Mathlib").is_dir():
        pytest.skip(f"reviewed workspace for PR {PR} is not built on this machine ({key})")
    return episode, key, root


def test_the_state_machine_says_it_is_usable(reviewed):
    from src.mathlib_review.analysis.runs import unbuilt_base_commits

    _episode, key, _root = reviewed
    assert asyncio.run(unbuilt_base_commits([key])) == []


def test_build_products_are_a_real_writable_copy_and_the_rest_is_shared(reviewed):
    """`.lake` is a real directory whose `build` is a real copy (Lean rewrote it) and whose
    `packages` is still the base's (never rewritten, 100k files not worth copying)."""

    _episode, _key, root = reviewed
    lake = root / ".lake"
    assert lake.is_dir() and not lake.is_symlink()
    assert (lake / "build").is_dir() and not (lake / "build").is_symlink()
    assert (lake / "packages").is_symlink()
    assert (root / "lakefile.lean").is_symlink() or (root / "lakefile.lean").is_file()


def test_changed_modules_were_rebuilt_from_the_prs_sources(reviewed):
    """Every changed module: its source is the PR's, and Lake rebuilt it -- the `.trace` (Lake's
    record of the inputs a build product came from) differs from the base's, and the `.olean` is
    a file of this workspace, not the base's inode. The `.olean` bytes need not differ: on
    33337 `Positive.lean` changes only a lemma name inside `simpa [...]` lists, and its rebuilt
    `.olean` is byte-identical to the base's -- the elaborated terms never used that lemma.
    `Submodule.olean`, where the rename is declared, must differ, and does."""

    episode, _key, root = reviewed
    base_root = root.parent / episode["base_sha"]
    olean_changed = []
    for rel in episode["changed_files"]:
        src = root / rel
        assert src.is_file() and not src.is_symlink(), f"{rel} must be a materialised copy"
        assert src.read_text() != (base_root / rel).read_text(), f"{rel} must carry the diff"
        stem = Path(".lake/build/lib/lean") / rel[: -len(".lean")]
        trace, olean = stem.with_suffix(".trace"), stem.with_suffix(".olean")
        assert (root / trace).is_file() and not (root / trace).is_symlink(), f"{trace} missing"
        assert (root / trace).read_bytes() != (base_root / trace).read_bytes(), (
            f"{trace} equals the base's: Lake did not rebuild {rel}")
        assert (root / olean).is_file() and not (root / olean).is_symlink()
        assert (root / olean).stat().st_ino != (base_root / olean).stat().st_ino, (
            f"{olean} is the base's inode: the build tree was not a real copy")
        olean_changed.append((root / olean).read_bytes() != (base_root / olean).read_bytes())
    assert any(olean_changed), "no changed module's .olean differs from the base's at all"


def test_the_workspace_is_finalised_read_only(reviewed):
    """Read-only like a restored base: the tools compile from a system temp file with the
    workspace as cwd, and nothing an attempt does may write into a shared artifact."""

    episode, _key, root = reviewed
    assert not os.access(root, os.W_OK)
    for rel in episode["changed_files"]:
        assert not os.access(root / rel, os.W_OK), rel


def test_the_task_resolves_it_and_links_target_to_it(reviewed, tmp_path):
    """What every v5 task does at setup: the reviewed key resolves through the restore manager
    to this root, `target/` becomes a link to it, and the returned `WorkspaceInfo` carries the
    reviewed key as its `commit_hash` -- which is how the verification note knows which world
    it is in."""

    from types import SimpleNamespace

    from ape.tasks.base import WorkspaceInfo
    from ape.tasks.lean_tasks.formal_math.pr_review.core import ReviewPRCoreTask
    from ape.toolkits.execute.lean.core.build_manager import is_reviewed_workspace_key

    episode, key, root = reviewed
    data = SimpleNamespace(
        pr_diff=episode["diff"], pr_number=PR,
        target_workspace=WorkspaceInfo(
            name="target", commit_hash=episode["base_sha"],
            repo_url="https://github.com/leanprover-community/mathlib4.git",
            default_target="Mathlib"))
    link = tmp_path / "target"

    resolved = asyncio.run(ReviewPRCoreTask._maybe_setup_reviewed_target_workspace(
        data, link, logger=None, progress_callback=None))

    assert resolved is not None, "the workspace exists, so the task must take it"
    assert resolved.commit_hash == key and is_reviewed_workspace_key(resolved.commit_hash)
    assert Path(resolved.path).resolve() == root.resolve()
    assert link.is_symlink() and link.resolve() == root.resolve()
