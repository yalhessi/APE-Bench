"""The run refuses, or knowingly accepts, the environment it will verify in.

A reviewed workspace is the base snapshot plus the PR's diff plus its changed modules rebuilt.
Whether one exists is a property of the run decided before the first model call, so it is a
preflight fact: reported by `plan` always, refused by `run` when required. The alternative --
discovering it in the findings as `broken_build` claims on PRs that build -- is how 16 such
findings reached the held-out results, 4 of them published.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from src.mathlib_review.review import preflight
from src.mathlib_review.review.preflight import (
    PreflightError,
    assert_reviewed_workspaces_prebuilt,
    reviewed_workspace_keys,
    unbuilt_reviewed_workspaces,
)
from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key

SHA_A = "a" * 40
SHA_B = "b" * 40


def _episode(pr, base, diff="--- a\n+++ b\n"):
    return SimpleNamespace(pr_number=pr, base_sha=base, diff=diff, episode_id=f"ep:{pr}")


def test_keys_are_per_episode_and_skip_episodes_with_no_diff():
    episodes = [_episode(1, SHA_A), _episode(2, SHA_B), _episode(3, SHA_A, diff="   ")]
    keys = asyncio.run(reviewed_workspace_keys(episodes))
    assert set(keys) == {reviewed_workspace_key(SHA_A, "--- a\n+++ b\n"),
                         reviewed_workspace_key(SHA_B, "--- a\n+++ b\n")}
    assert all(k.startswith(("a" * 40, "b" * 40)) and "+" in k for k in keys)


def test_two_prs_on_one_base_with_different_diffs_need_two_workspaces():
    """The key is (base, diff), not base: sharing a base commit is the common case on a release
    and a workspace built for one PR's diff is the wrong environment for another's."""

    episodes = [_episode(1, SHA_A, "d1"), _episode(2, SHA_A, "d2")]
    keys = asyncio.run(reviewed_workspace_keys(episodes))
    assert len(keys) == 2


def _patch_unbuilt(monkeypatch, missing_keys):
    async def fake(commits, repo_name="mathlib4"):
        return [c for c in commits if c in missing_keys]

    monkeypatch.setattr(preflight, "unbuilt_base_commits", fake)


def test_missing_workspaces_are_reported_by_episode(monkeypatch):
    episodes = [_episode(1, SHA_A, "d1"), _episode(2, SHA_A, "d2")]
    k2 = reviewed_workspace_key(SHA_A, "d2")
    _patch_unbuilt(monkeypatch, {k2})

    missing = asyncio.run(unbuilt_reviewed_workspaces(episodes))
    assert list(missing) == [k2] and missing[k2].pr_number == 2


def test_required_and_missing_refuses_with_the_prebuild_command(monkeypatch):
    episodes = [_episode(33337, SHA_A, "d")]
    _patch_unbuilt(monkeypatch, {reviewed_workspace_key(SHA_A, "d")})

    with pytest.raises(PreflightError) as excinfo:
        asyncio.run(assert_reviewed_workspaces_prebuilt(episodes, required=True))
    message = str(excinfo.value)
    assert "33337" in message
    assert "prebuild --reviewed" in message
    assert "require_reviewed_workspaces: false" in message, "the knowing opt-out is named"


def test_not_required_still_reports_but_does_not_refuse(monkeypatch):
    """A run may accept the degraded environment on purpose; it may not do so unknowingly."""

    class Log:
        def __init__(self):
            self.warnings = []

        def warning(self, msg, *args):
            self.warnings.append(msg % args if args else msg)

    episodes = [_episode(33337, SHA_A, "d")]
    _patch_unbuilt(monkeypatch, {reviewed_workspace_key(SHA_A, "d")})
    log = Log()

    missing = asyncio.run(assert_reviewed_workspaces_prebuilt(episodes, required=False, logger=log))
    assert len(missing) == 1
    assert log.warnings and "base commit's build products" in log.warnings[0]


def test_nothing_missing_is_quiet(monkeypatch):
    _patch_unbuilt(monkeypatch, set())
    assert asyncio.run(assert_reviewed_workspaces_prebuilt(
        [_episode(1, SHA_A, "d")], required=True)) == {}


def test_the_runner_asks_before_spending_and_the_dry_run_reports():
    """Both paths: `run` calls the guard beside the base-workspace guard, and `plan` reports the
    count so a dry run can say what environment the real run would verify in."""

    import inspect

    from src.mathlib_review.review import runner

    source = inspect.getsource(runner.run)
    assert source.count("assert_reviewed_workspaces_prebuilt(") == 2, (
        "once in the dry-run branch, once before the orchestrator")
    assert "reviewed workspaces: %d of %d episode(s) prebuilt" in source
    assert "require_reviewed_workspaces" in inspect.getsource(runner.V5DatasetConfig)


def test_the_knob_defaults_off_and_the_base_config_says_why():
    from pathlib import Path

    from src.mathlib_review.review.runner import V5DatasetConfig

    assert V5DatasetConfig.model_fields["require_reviewed_workspaces"].default is False
    text = Path("configs/bases/v5_generation.yaml").read_text()
    assert "require_reviewed_workspaces: false" in text
    assert "prebuild --reviewed" in text
