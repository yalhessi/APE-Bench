"""A review task verifies against the reviewed workspace when one exists, and says so when not.

The arms, the lead and the solo task all reach their workspace through
`review/base.py::setup_attempt`, not `pr_review/core.py`'s -- so that is where the reviewed
workspace has to be picked up, or the fix would apply to the v2 tasks and skip every v5 one.

The fallback is not silent. A source-only overlay of the base commit is exactly the environment
in which a renamed sibling reads as `Unknown constant` (41 of 321 arm sessions on the held-out
run), and a fallback that looked like the fix while behaving like the defect would be worse than
either.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from ape.tasks.lean_tasks.formal_math.pr_review.core import ReviewPRCoreTask
from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key

SHA = "a36c84ab8236a4869899268a42a44af07daa21ed"
DIFF = "--- a/Mathlib/A.lean\n+++ b/Mathlib/A.lean\n@@ -1 +1 @@\n-old\n+new\n"


def _data():
    from ape.tasks.models import WorkspaceInfo

    return SimpleNamespace(
        pr_number=33337, pr_diff=DIFF, diff=DIFF, changed_files=["Mathlib/A.lean"],
        target_workspace=WorkspaceInfo(name="target", commit_hash=SHA, repo_url="x",
                                       default_target="Mathlib"),
    )


def test_the_reviewed_workspace_is_linked_when_it_exists(tmp_path, monkeypatch):
    reviewed = tmp_path / "workspaces" / reviewed_workspace_key(SHA, DIFF)
    (reviewed / "Mathlib").mkdir(parents=True)
    resolved = {}

    async def fake_resolve(spec, logger=None, progress_callback=None):
        resolved["key"] = spec.commit_hash
        return reviewed

    monkeypatch.setattr(ReviewPRCoreTask, "_maybe_resolve_cached_workspace",
                        classmethod(lambda cls, spec, **kw: fake_resolve(spec, **kw)))
    link = tmp_path / "attempt" / "workspaces" / "target"
    link.parent.mkdir(parents=True)

    info = asyncio.run(ReviewPRCoreTask._maybe_setup_reviewed_target_workspace(_data(), link))

    assert info is not None
    assert resolved["key"] == reviewed_workspace_key(SHA, DIFF), "looked up by the reviewed key"
    assert info.commit_hash == reviewed_workspace_key(SHA, DIFF), (
        "the WorkspaceInfo carries the reviewed key, which is how the tools know their environment")
    assert link.is_symlink() and link.resolve() == reviewed.resolve()


def test_no_reviewed_workspace_falls_back_and_warns(tmp_path, monkeypatch, caplog):
    async def nothing(spec, logger=None, progress_callback=None):
        return None

    monkeypatch.setattr(ReviewPRCoreTask, "_maybe_resolve_cached_workspace",
                        classmethod(lambda cls, spec, **kw: nothing(spec, **kw)))
    logger = logging.getLogger("reviewed-target-test")
    link = tmp_path / "attempt" / "workspaces" / "target"
    link.parent.mkdir(parents=True)

    with caplog.at_level(logging.WARNING, logger="reviewed-target-test"):
        info = asyncio.run(ReviewPRCoreTask._maybe_setup_reviewed_target_workspace(
            _data(), link, logger=logger))

    assert info is None
    assert "no reviewed workspace" in caplog.text and "prebuild" in caplog.text
    assert not link.exists(), "nothing linked; the caller builds the overlay"


def test_a_pr_with_no_diff_needs_no_reviewed_workspace(tmp_path):
    data = _data()
    data.pr_diff = ""
    data.diff = ""
    assert asyncio.run(ReviewPRCoreTask._maybe_setup_reviewed_target_workspace(
        data, tmp_path / "target")) is None


def test_the_review_base_setup_prefers_the_reviewed_workspace_and_skips_patching():
    """`review/base.py` is the path v5 tasks take. It must consult the reviewed workspace
    first and, when one is linked, not call the overlay patcher -- the diff is already there,
    and patching a read-only prebuilt tree would fail or, worse, double-apply."""

    import inspect

    from ape.tasks.lean_tasks.formal_math.review import base as review_base

    source = inspect.getsource(review_base.BasePRReviewTask.setup_attempt)
    assert "_maybe_setup_reviewed_target_workspace" in source
    idx_reviewed = source.index("_maybe_setup_reviewed_target_workspace")
    idx_patch = source.index("_ensure_patched_target_workspace")
    assert idx_reviewed < idx_patch, "reviewed workspace is tried before the overlay"
    assert "if reviewed is not None:" in source and "else:" in source


def test_core_setup_tries_the_reviewed_workspace_between_head_fast_path_and_overlay():
    import inspect

    source = inspect.getsource(ReviewPRCoreTask.setup_attempt)
    head = source.index("_maybe_setup_head_target_workspace")
    reviewed = source.index("_maybe_setup_reviewed_target_workspace")
    overlay = source.index("_ensure_patched_target_workspace")
    assert head < reviewed < overlay


def test_the_overlay_patcher_and_the_prebuild_share_one_source_preparation():
    """`prepare_reviewed_sources` is the callable the toolkit builder receives. If the overlay
    path stopped using it, the two would drift and a prebuilt workspace could differ from the
    per-attempt overlay it replaces."""

    import inspect

    source = inspect.getsource(ReviewPRCoreTask._ensure_patched_target_workspace)
    assert "prepare_reviewed_sources(" in source
    assert "_materialize_overlay_path" not in source, "materialisation moved into the shared step"


def test_the_marker_and_the_key_share_one_fingerprint_recipe():
    """The overlay marker keeps the full digest and the workspace name keeps twelve hex; they
    must be the same digest or an overlay and the workspace built for the same diff would
    disagree about identity."""

    from ape.toolkits.execute.lean.core.build_manager import patch_fingerprint

    full = ReviewPRCoreTask._patch_fingerprint(_data())
    assert full == patch_fingerprint(SHA, DIFF)
    assert reviewed_workspace_key(SHA, DIFF) == f"{SHA}+{full[:12]}"


# --- the environment note follows the target -------------------------------------------------


def _task_with_target(tmp_path, commit_hash):
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.ape_agent.config import ApeAgentConfig
    from ape.tasks.lean_tasks.formal_math.review.arm import ReviewArmData, ReviewArmTask
    from ape.tasks.models import WorkspaceInfo

    root = tmp_path / "target"
    (root / "Mathlib").mkdir(parents=True)
    item = ReviewArmTask(
        ReviewArmData(
            task_id="t", invocation_id="wu:a#proof_golf", arm_id="proof_golf",
            spec_id="proof_golf", work_unit_id="wu:a", episode_id="ep:1", pr_number=1,
            diff="d", changed_files=["Mathlib/A.lean"], change_ids=["change:a"],
            entity_ids_by_change={"change:a": ["e"]},
            primary_subjects_by_change={"change:a": "Foo.bar"},
            paths_by_change={"change:a": "Mathlib/A.lean"},
            rendered_system_prompt="s", rendered_user_prompt="u",
            rendered_prompt_sha256="a" * 64,
            target_workspace={"name": "target", "commit_hash": SHA,
                              "repo_url": "https://e.invalid/m.git", "default_target": "Mathlib"}),
        ApeAgentConfig(llm_config=LLMConfig(model_name="gpt_5.2")))
    item.target_workspace = WorkspaceInfo(name="target", path=root, commit_hash=commit_hash)
    return item


def test_against_a_base_overlay_the_note_names_the_artifact(tmp_path):
    note = _task_with_target(tmp_path, SHA)._verification_environment_note()
    assert "base commit's build products" in note and "This PR compiles" in note


def test_against_a_reviewed_workspace_the_note_says_the_error_is_genuine(tmp_path):
    note = _task_with_target(tmp_path, reviewed_workspace_key(SHA, DIFF))._verification_environment_note()
    assert "reviewed workspace" in note and "genuine" in note
    assert "base commit's build products" not in note
