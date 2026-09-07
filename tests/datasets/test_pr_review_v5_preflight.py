"""Refusing to start, and saying why.

Verification is the warrant behind every specialist claim, and its absence is silent: `lake
env lean` exits 127, emits no Lean diagnostics, and the arm gate then drops the unverified
finding. One held-out run failed **225 of 225** verifications this way — the shell that
launched it had no elan on `PATH` — and the artifacts read as "the specialists found nothing
on unseen PRs".

What is tested here is therefore not only that a missing prerequisite is detected, but the
three properties that make the check trustworthy: it never guesses at a toolchain, an
explicit declaration is validated rather than believed, and a machine missing two things is
told about both at once.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.datasets.pr_review_v5.preflight import (
    PreflightError,
    assert_ready,
    assert_workspaces_prebuilt,
)

LOGGER = logging.getLogger("preflight-test")


def scaffold(*, toolchain_bin=None, model_name="gpt-5", api_key="sk-test"):
    return SimpleNamespace(
        tools_config=SimpleNamespace(
            lean_verify=SimpleNamespace(lean_toolchain_bin=toolchain_bin)),
        llm_config=SimpleNamespace(
            model_name=model_name, api_key=api_key,
            provider_type=SimpleNamespace(value="openai")),
    )


@pytest.fixture
def bare_path(monkeypatch):
    """A machine with no Lean toolchain anywhere on `PATH`."""

    monkeypatch.setenv("PATH", "/nonexistent-for-tests")
    monkeypatch.delenv("ELAN_HOME", raising=False)


@pytest.fixture
def fake_toolchain(tmp_path):
    binv = tmp_path / "elan" / "bin"
    binv.mkdir(parents=True)
    (binv / "lake").write_text("#!/bin/sh\n")
    (binv / "lake").chmod(0o755)
    return binv


def test_a_missing_toolchain_stops_the_run_before_it_spends(bare_path):
    with pytest.raises(PreflightError) as caught:
        assert_ready(scaffold(), LOGGER)
    message = str(caught.value)
    assert "lean toolchain" in message
    # The consequence is named, because that is what stops the failure being misattributed.
    assert "found nothing" in message


def test_a_declared_directory_is_put_on_path_once(bare_path, fake_toolchain, monkeypatch):
    assert_ready(scaffold(toolchain_bin=fake_toolchain), LOGGER)
    assert str(fake_toolchain) in os.environ["PATH"]


def test_a_declaration_that_does_not_resolve_is_worse_than_none(bare_path, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(PreflightError) as caught:
        assert_ready(scaffold(toolchain_bin=empty), LOGGER)
    assert "no `lake` in it" in str(caught.value)


def test_nothing_is_guessed_when_a_toolchain_sits_in_a_standard_location(
    bare_path, tmp_path, monkeypatch
):
    """The property the reverted implementation violated.

    An earlier version searched `ELAN_HOME`, `~/.elan/bin` and friends, and patched `PATH`
    from whatever it found. A run that repairs its own environment cannot report which
    toolchain compiled its evidence — so a toolchain that is merely *findable* must still
    fail the check. It has to be on `PATH` or written down.
    """

    elan = tmp_path / ".elan" / "bin"
    elan.mkdir(parents=True)
    (elan / "lake").write_text("#!/bin/sh\n")
    monkeypatch.setenv("ELAN_HOME", str(tmp_path / ".elan"))
    monkeypatch.setenv("HOME", str(tmp_path))

    with pytest.raises(PreflightError):
        assert_ready(scaffold(), LOGGER)


def test_a_missing_credential_is_caught_before_the_plan_is_sealed(fake_toolchain):
    with pytest.raises(PreflightError) as caught:
        assert_ready(scaffold(toolchain_bin=fake_toolchain, api_key=None), LOGGER)
    assert "model credential" in str(caught.value)


def test_a_model_free_mode_needs_no_credential(fake_toolchain):
    assert_ready(
        scaffold(toolchain_bin=fake_toolchain, model_name=None, api_key=None), LOGGER)


def test_every_unmet_prerequisite_is_reported_together(bare_path):
    """One round trip to fix a machine, not one per fault."""

    with pytest.raises(PreflightError) as caught:
        assert_ready(scaffold(api_key=None), LOGGER)
    message = str(caught.value)
    assert "lean toolchain" in message and "model credential" in message
    assert "2 prerequisite(s)" in message


def test_unbuilt_workspaces_stop_the_run(monkeypatch):
    async def unbuilt(commits):
        return sorted(commits)

    monkeypatch.setattr("src.datasets.pr_review_v5.preflight.unbuilt_base_commits", unbuilt)
    data = [{"target_workspace": {"commit_hash": "abc123"}}]
    with pytest.raises(PreflightError) as caught:
        asyncio.run(assert_workspaces_prebuilt(data))
    assert "abc123" in str(caught.value)
    assert "prebuild" in str(caught.value)


def test_the_workspace_check_is_skippable_by_config(monkeypatch):
    async def explode(commits):  # pragma: no cover - must not run
        raise AssertionError("should not have been consulted")

    monkeypatch.setattr("src.datasets.pr_review_v5.preflight.unbuilt_base_commits", explode)
    asyncio.run(assert_workspaces_prebuilt(
        [{"target_workspace": {"commit_hash": "x"}}], required=False))


def test_a_dry_run_reports_but_does_not_block(bare_path, caplog):
    """A dry run spends nothing, so it validates a config on a machine that cannot run it.

    It still says exactly what would stop the real run — that is what the command is for.
    """

    with caplog.at_level(logging.WARNING):
        assert_ready(scaffold(api_key=None), LOGGER, enforce=False)
    assert "lean toolchain" in caplog.text and "model credential" in caplog.text
    assert "has not started" not in caplog.text
