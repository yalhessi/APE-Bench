"""`prebuild --reviewed`: build the workspaces a run will verify in, and only those.

The preflight (`test_pr_review_v5_reviewed_preflight.py`) says which episodes lack a reviewed
workspace; this is the command that makes them. It plans before it builds, builds only what
is missing, refuses an episode whose *base* is not built rather than failing twelve minutes
into a copy, and spends nothing without `--execute` -- a build is not money, but it is an hour
of NFS and a state-machine transition, and the house rule is that nothing irreversible runs
from a command that could have been a look.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.mathlib_review.release import prebuild
from src.mathlib_review.release.prebuild import (
    BASE_MISSING,
    MISSING,
    READY,
    ReviewedBuild,
    build_reviewed_workspaces,
    plan_reviewed_builds,
    prepare_sources_for,
)
from src.mathlib_review.review import preflight
from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key

SHA_A = "a" * 40
SHA_B = "b" * 40


def _episode(pr, base, diff="d", files=("Mathlib/X.lean",)):
    return SimpleNamespace(pr_number=pr, base_sha=base, diff=diff, changed_files=list(files),
                           episode_id=f"ep:{pr}")


def _patch_unbuilt(monkeypatch, unbuilt):
    async def fake(commits, repo_name="mathlib4"):
        return [c for c in commits if c in unbuilt]

    monkeypatch.setattr(preflight, "unbuilt_base_commits", fake)
    monkeypatch.setattr(prebuild, "unbuilt_base_commits", fake)


def test_plan_classifies_ready_missing_and_base_missing(monkeypatch):
    ready, missing, orphan = _episode(1, SHA_A, "d1"), _episode(2, SHA_A, "d2"), _episode(3, SHA_B)
    k_missing = reviewed_workspace_key(SHA_A, "d2")
    k_orphan = reviewed_workspace_key(SHA_B, "d")
    _patch_unbuilt(monkeypatch, {k_missing, k_orphan, SHA_B})

    plan = asyncio.run(plan_reviewed_builds([orphan, missing, ready]))

    assert [(b.episode.pr_number, b.status) for b in plan] == [
        (1, READY), (2, MISSING), (3, BASE_MISSING)], "sorted by PR, classified"
    assert plan[1].key == k_missing


def test_plan_skips_episodes_without_a_diff(monkeypatch):
    _patch_unbuilt(monkeypatch, set())
    plan = asyncio.run(plan_reviewed_builds([_episode(1, SHA_A, diff="  ")]))
    assert plan == []


class _Manager:
    def __init__(self, fail_on=()):
        self.calls = []
        self.fail_on = set(fail_on)

    async def build_reviewed_workspace(self, key, base_commit, *, prepare_sources, changed_files,
                                       force_rebuild=False):
        self.calls.append((key, base_commit, list(changed_files), force_rebuild))
        if key in self.fail_on:
            # What the real builder does: marks the state FAILED, then re-raises.
            raise RuntimeError(f"[{key}] lake build failed:\nlake said no")
        return SimpleNamespace(success=True, commit_hash=key, error_message=None,
                               build_duration=1.0)


def _log():
    lines = []
    return SimpleNamespace(
        info=lambda m, *a: lines.append(("info", m % a if a else m)),
        warning=lambda m, *a: lines.append(("warning", m % a if a else m)),
        error=lambda m, *a: lines.append(("error", m % a if a else m)),
        lines=lines)


def test_builds_only_what_is_missing_and_names_what_it_will_not_touch():
    plan = [
        ReviewedBuild("k1", _episode(1, SHA_A), READY),
        ReviewedBuild("k2", _episode(2, SHA_A, files=("Mathlib/Y.lean", "docs/z.md")), MISSING),
        ReviewedBuild("k3", _episode(3, SHA_B), BASE_MISSING),
    ]
    manager, log = _Manager(), _log()

    results = asyncio.run(build_reviewed_workspaces(plan, manager=manager, logger=log))

    assert [c[0] for c in manager.calls] == ["k2"], "ready is skipped, base-missing is refused"
    assert manager.calls[0][1] == SHA_A
    assert manager.calls[0][2] == ["Mathlib/Y.lean", "docs/z.md"], (
        "the toolkit decides which of these are modules, against the patched tree")
    assert set(results) == {"k2"} and results["k2"].success
    said = " ".join(m for _, m in log.lines)
    assert "k3" in said and SHA_B in said and "base" in said, "the refusal names the base to build"


def test_a_failed_build_is_reported_not_raised_so_the_rest_still_build():
    plan = [ReviewedBuild("k1", _episode(1, SHA_A), MISSING),
            ReviewedBuild("k2", _episode(2, SHA_A, "d2"), MISSING)]
    manager, log = _Manager(fail_on={"k1"}), _log()

    results = asyncio.run(build_reviewed_workspaces(plan, manager=manager, logger=log))

    assert [c[0] for c in manager.calls] == ["k1", "k2"]
    assert not results["k1"].success and results["k2"].success
    assert any(level == "error" and "lake said no" in m for level, m in log.lines)


def test_force_rebuild_is_passed_through_and_rebuilds_ready_ones_too():
    plan = [ReviewedBuild("k1", _episode(1, SHA_A), READY)]
    manager = _Manager()
    asyncio.run(build_reviewed_workspaces(plan, manager=manager, logger=_log(), force_rebuild=True))
    assert manager.calls == [("k1", SHA_A, ["Mathlib/X.lean"], True)]


def test_prepare_sources_is_the_task_layers_own_overlay_and_patch(monkeypatch):
    """The callable handed to the toolkit reaches `ReviewPRCoreTask.prepare_reviewed_sources`
    with this episode's diff and files -- the same function the per-attempt overlay uses, so
    the prebuilt workspace and the fallback overlay cannot lay down different sources."""

    from ape.tasks.lean_tasks.formal_math.pr_review.core import ReviewPRCoreTask

    seen = {}

    async def fake(cls, overlay_root, base_root, *, pr_diff, changed_files, logger=None,
                   progress_callback=None):
        seen.update(overlay_root=overlay_root, base_root=base_root, pr_diff=pr_diff,
                    changed_files=list(changed_files))

    monkeypatch.setattr(ReviewPRCoreTask, "prepare_reviewed_sources", classmethod(fake))
    episode = _episode(7, SHA_A, diff="--- a\n+++ b\n", files=("Mathlib/P.lean",))

    prepare = prepare_sources_for(episode, logger=_log())
    asyncio.run(prepare(Path("/build"), Path("/base")))

    assert seen == {"overlay_root": Path("/build"), "base_root": Path("/base"),
                    "pr_diff": "--- a\n+++ b\n", "changed_files": ["Mathlib/P.lean"]}


def test_without_execute_the_command_plans_and_builds_nothing(monkeypatch, capsys):
    plan = [ReviewedBuild("k1", _episode(1, SHA_A), READY),
            ReviewedBuild("k2", _episode(2, SHA_A, "d2"), MISSING),
            ReviewedBuild("k3", _episode(3, SHA_B), BASE_MISSING)]

    async def fake_plan(episodes):
        return plan

    def no_build(*a, **k):
        raise AssertionError("nothing may be built without --execute")

    monkeypatch.setattr(prebuild, "plan_reviewed_builds", fake_plan)
    monkeypatch.setattr(prebuild, "build_reviewed_workspaces", no_build)
    monkeypatch.setattr(prebuild, "_selected_episodes", lambda config, overrides: ([], None))

    prebuild.main(["--reviewed", "--config", "configs/pr_review_v5_medium_heldout.yaml"])

    out = capsys.readouterr().out
    assert "1 ready" in out and "1 to build" in out and "1 base not built" in out
    assert "--execute" in out, "says how to actually build"


def test_with_execute_the_command_checks_the_toolchain_then_builds(monkeypatch):
    plan = [ReviewedBuild("k2", _episode(2, SHA_A, "d2"), MISSING)]
    order = []

    async def fake_plan(episodes):
        return plan

    async def fake_build(plan_, *, manager, logger, force_rebuild=False):
        order.append(("build", [b.key for b in plan_], force_rebuild))
        return {}

    monkeypatch.setattr(prebuild, "plan_reviewed_builds", fake_plan)
    monkeypatch.setattr(prebuild, "build_reviewed_workspaces", fake_build)
    monkeypatch.setattr(prebuild, "_selected_episodes", lambda config, overrides: ([], object()))
    monkeypatch.setattr(prebuild, "assert_toolchain", lambda scaffold, logger: order.append(("toolchain",)))
    monkeypatch.setattr(prebuild, "_build_manager", lambda scaffold, logger: object())

    prebuild.main(["--reviewed", "--execute", "--force-rebuild",
                   "--config", "configs/pr_review_v5_medium_heldout.yaml"])

    assert order == [("toolchain",), ("build", ["k2"], True)]


def test_the_toolchain_is_checked_before_a_manager_exists(monkeypatch):
    """A missing `lake` must be found before anything is constructed or copied."""

    async def fake_plan(episodes):
        return [ReviewedBuild("k2", _episode(2, SHA_A, "d2"), MISSING)]

    monkeypatch.setattr(prebuild, "plan_reviewed_builds", fake_plan)
    monkeypatch.setattr(prebuild, "_selected_episodes", lambda config, overrides: ([], object()))

    def refuse(scaffold, logger):
        raise preflight.PreflightError("lean toolchain: no lake")

    monkeypatch.setattr(prebuild, "assert_toolchain", refuse)
    monkeypatch.setattr(prebuild, "_build_manager",
                        lambda scaffold, logger: (_ for _ in ()).throw(AssertionError("too early")))

    with pytest.raises(preflight.PreflightError, match="no lake"):
        prebuild.main(["--reviewed", "--execute",
                       "--config", "configs/pr_review_v5_medium_heldout.yaml"])
