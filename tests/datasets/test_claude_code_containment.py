"""The Claude Code scaffold's containment, which for a long time was a docstring and nothing else.

`claude_code/__init__.py` claimed "Disables Bash commands". The scaffold refused exactly one
tool -- `Explore` -- and defaulted `permission_mode` to `bypassPermissions`, so Bash, WebFetch,
WebSearch, Task, Write and Edit were live and auto-approved. Nothing checked the claim.

It becomes load-bearing the moment this scaffold is pointed at the Mathlib review task, because
that task's whole validity rests on the reviewer not seeing the future. The scheduled arms get
that from a gold-free retrieval cutoff verified at 0 leaks on all 16 medium episodes; an
off-the-shelf agent has no such discipline and must be denied the capability instead.

These tests pin the containment knobs and the reachability facts that motivate them. They do
not assert a posture on the scaffold's defaults: the defaults stay permissive so existing
callers keep working, and a review run states its posture in its own config. What must never
regress is that the knobs exist and reach `ClaudeAgentOptions`.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from ape.scaffolds.claude_code.config import ClaudeCodeConfig

REPO = Path(__file__).resolve().parents[2]


def test_the_containment_knobs_exist():
    fields = ClaudeCodeConfig.model_fields
    for name in ("tools", "disallowed_tools", "setting_sources", "strict_mcp_config"):
        assert name in fields, name


def test_the_sdk_still_accepts_every_knob_we_pass():
    """The SDK is a vendored dependency on its own release cadence. If it renames one of these,
    the option is dropped and the run is uncontained -- silently, because an unknown keyword
    would have raised but a removed feature would not."""

    import dataclasses

    from claude_agent_sdk import ClaudeAgentOptions

    names = {f.name for f in dataclasses.fields(ClaudeAgentOptions)}
    for name in ("tools", "disallowed_tools", "setting_sources", "strict_mcp_config",
                 "permission_mode", "cwd", "add_dirs", "env"):
        assert name in names, name


def test_dontAsk_is_a_real_permission_mode():
    """The recommended review posture. `bypassPermissions` auto-approves everything; `dontAsk`
    denies anything not pre-approved, which is the difference between a cwd that is advisory
    and one that binds."""

    import typing

    import claude_agent_sdk.types as sdk_types

    assert "dontAsk" in typing.get_args(sdk_types.PermissionMode)


def test_configured_disallowed_tools_reach_the_sdk_options():
    """Additive, not replacing: the scaffold's own `Explore` entry and the native-tools
    exclusions must survive alongside whatever a config adds."""

    from ape.scaffolds.claude_code.scaffold import ClaudeCodeScaffold

    source = inspect.getsource(ClaudeCodeScaffold._run_batch_mode)
    assert "config.disallowed_tools" in source
    assert 'disallowed_tools = ["Explore"]' in source
    assert "disallowed_tools=disallowed_tools" in source


def test_an_empty_setting_sources_is_distinguished_from_an_unset_one():
    """They mean opposite things to the SDK -- none versus all -- so treating `[]` as absent
    would load this repository's own CLAUDE.md and .claude/rules/ into the experiment while
    reading as if it had been locked down."""

    from ape.scaffolds.claude_code.scaffold import ClaudeCodeScaffold

    source = inspect.getsource(ClaudeCodeScaffold._run_batch_mode)
    assert "config.setting_sources is not None" in source
    assert ClaudeCodeConfig().setting_sources is None


def test_the_docstring_no_longer_claims_a_containment_it_does_not_have():
    """The specific regression: a comment asserting a contract nothing enforces, which stops
    the next person checking."""

    import ape.scaffolds.claude_code as package

    # Checked against the numbered feature list only. The docstring still *quotes* the old
    # claim, in the past tense, to record why the containment knobs exist -- an accurate
    # account of a removed contract is the opposite of the defect.
    claims = [line.strip() for line in (package.__doc__ or "").splitlines()
              if line.strip()[:1].isdigit()]
    assert not [line for line in claims if "Disables Bash" in line], claims


# --- the reachability facts that motivate the posture --------------------------------------


def test_a_review_workspace_resolves_git_upward_into_this_repository():
    """Channel 1, and the reason `Bash` cannot be granted. The per-workspace `.git` is deleted,
    but run artifacts live under `.ape/` *inside* the repository, so git resolves upward from
    the agent's cwd to a work tree that contains `inputs/pr_review_v4/releases/*/gold/` -- the
    obligations the run is scored against. `git show HEAD:<path>` does not even need the file
    to be checked out.

    If this ever fails because the run root moved outside the repository, that is the fix
    landing, not a broken test -- relocate the assertion, do not delete it.

    The tree git resolves to is not always this one: in a worktree `.ape/` is a symlink to the
    main checkout's store (`.claude/worktree-setup.sh`), so git resolves into *that* checkout.
    The hazard is unchanged -- what matters is that the tree reached holds gold, not which tree
    it is -- so that is what is asserted.
    """

    import subprocess

    runs_root = REPO / ".ape"
    if not runs_root.is_dir():
        pytest.skip(".ape/ not present in this checkout")
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=runs_root,
        capture_output=True, text=True, check=False)
    if top.returncode != 0:
        pytest.skip("git unavailable")

    resolved = Path(top.stdout.strip())
    assert resolved in (REPO, Path(runs_root.resolve()).parent), (
        f"`.ape/` resolved to an unrelated work tree: {resolved}")
    assert (resolved / "inputs/pr_review_v4/releases").is_dir(), (
        "the upward work tree is the one holding gold")
