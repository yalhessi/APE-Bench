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


# --- the refusal and the audit (`containment.py`) -----------------------------------------


def _review_layout(tmp_path):
    """The real shape, small: `workspaces/target` links to a reviewed workspace in a shared
    store, whose entries link into the base checkout; the store also holds a later commit's
    workspace, and the repository beside it holds gold."""

    store = tmp_path / "store"
    base = store / "base"
    (base / "Mathlib").mkdir(parents=True)
    (base / "Mathlib" / "Foo.lean").write_text("theorem foo : True := trivial\n")
    reviewed = store / "base+pr"
    reviewed.mkdir()
    (reviewed / "Mathlib").symlink_to(base / "Mathlib")
    later = store / "later"
    later.mkdir()
    (later / "Merged.lean").write_text("the merged form of the PR under review\n")
    gold = tmp_path / "repo" / "inputs" / "gold.json"
    gold.parent.mkdir(parents=True)
    gold.write_text("{}")
    workspaces = tmp_path / "attempt" / "workspaces"
    (workspaces / "scratch").mkdir(parents=True)
    (workspaces / "target").symlink_to(reviewed)
    return workspaces, base, later, gold


def _rules(tmp_path):
    from ape.scaffolds.claude_code.containment import provisioned_roots, violation

    workspaces, base, later, gold = _review_layout(tmp_path)
    roots = provisioned_roots(workspaces)
    cwd = str(workspaces)
    return (lambda name, **tool_input: violation(name, tool_input, roots, cwd)), workspaces, base, later, gold


def test_the_workspace_and_its_provisioned_links_are_reachable(tmp_path):
    check, workspaces, base, _later, _gold = _rules(tmp_path)
    assert check("Read", file_path=f"{workspaces}/target/Mathlib/Foo.lean") is None
    assert check("Read", file_path="target/Mathlib/Foo.lean") is None
    # A tool may report a file by its resolved path; the base checkout is provisioned.
    assert check("Read", file_path=f"{base}/Mathlib/Foo.lean") is None
    assert check("Grep", pattern="theorem") is None          # defaults to cwd
    assert check("Glob", pattern="**/*.lean") is None
    assert check("Glob", pattern="*.lean", path="target/Mathlib") is None
    assert check("TodoWrite", todos=[]) is None
    assert check("mcp__core__file_read", path="/anywhere") is None  # scoped by APE


def test_planted_lures_outside_the_workspace_are_refused(tmp_path):
    check, workspaces, _base, later, gold = _rules(tmp_path)
    assert check("Read", file_path=str(gold))                         # this repository's gold
    assert check("Read", file_path=f"{later}/Merged.lean")            # a later commit's workspace
    assert check("Read", file_path=f"{workspaces}/../../repo/inputs/gold.json")
    assert check("Grep", pattern="obligation", path=str(gold.parent))
    assert check("Glob", pattern=f"{gold.parent}/*.json")             # absolute pattern
    assert check("Glob", pattern="../../repo/**/*.json")              # escaping pattern
    assert check("Bash", command="git show HEAD:inputs/gold.json")    # never granted


def test_the_hook_denies_with_a_marked_reason_and_records_it(tmp_path):
    import asyncio

    from ape.scaffolds.claude_code.containment import (
        REFUSAL_MARK, pre_tool_use_hook, provisioned_roots)

    workspaces, _base, _later, gold = _review_layout(tmp_path)
    refusals = []
    hook = pre_tool_use_hook(provisioned_roots(workspaces), str(workspaces), refusals)

    out = asyncio.run(hook({"tool_name": "Read", "tool_input": {"file_path": str(gold)}}, "t1", None))
    decision = out["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert decision["permissionDecisionReason"].startswith(REFUSAL_MARK)
    assert [r["tool_use_id"] for r in refusals] == ["t1"]

    inside = {"tool_name": "Read", "tool_input": {"file_path": f"{workspaces}/target/Mathlib/Foo.lean"}}
    assert asyncio.run(hook(inside, "t2", None)) == {}   # no decision: dontAsk still applies
    assert len(refusals) == 1


def _transcript(path, calls, refused=()):
    """A session transcript in Claude Code's own JSONL shape."""

    import json

    from ape.scaffolds.claude_code.containment import REFUSAL_MARK

    lines = []
    for call_id, name, tool_input in calls:
        lines.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": call_id, "name": name, "input": tool_input}]}})
        text = f"{REFUSAL_MARK} refused" if call_id in refused else "ok"
        lines.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": call_id, "is_error": call_id in refused,
             "content": text}]}})
    path.write_text("".join(json.dumps(line) + "\n" for line in lines))
    return path


def test_the_audit_fires_on_a_planted_lure_that_was_not_refused(tmp_path):
    """The condition the solo_claude configs' headers set before any number is read."""

    from ape.scaffolds.claude_code.containment import audit_transcript, provisioned_roots

    workspaces, _base, later, gold = _review_layout(tmp_path)
    roots = provisioned_roots(workspaces)
    transcript = _transcript(tmp_path / "s.jsonl", [
        ("a", "Read", {"file_path": f"{workspaces}/target/Mathlib/Foo.lean"}),
        ("b", "Read", {"file_path": str(gold)}),
        ("c", "Read", {"file_path": f"{later}/Merged.lean"}),
        ("d", "mcp__core__submit_findings", {"findings": []}),
    ], refused={"b"})

    report = audit_transcript(transcript, roots, str(workspaces))
    assert report["tool_calls"] == 4
    assert [r["id"] for r in report["refused"]] == ["b"]
    assert [r["id"] for r in report["leaks"]] == ["c"]
    assert report["clean"] is False


def test_the_audit_passes_a_contained_session(tmp_path):
    from ape.scaffolds.claude_code.containment import audit_transcript, provisioned_roots

    workspaces, _base, _later, gold = _review_layout(tmp_path)
    transcript = _transcript(tmp_path / "s.jsonl", [
        ("a", "Grep", {"pattern": "theorem", "path": "target"}),
        ("b", "Read", {"file_path": str(gold)}),
    ], refused={"b"})
    report = audit_transcript(transcript, provisioned_roots(workspaces), str(workspaces))
    assert report["clean"] is True and not report["leaks"]
    assert report["by_tool"] == {"Grep": 1, "Read": 1}


def test_contain_to_workspace_reaches_the_sdk_options():
    import dataclasses

    from claude_agent_sdk import ClaudeAgentOptions

    from ape.scaffolds.claude_code.scaffold import ClaudeCodeScaffold

    assert "hooks" in {f.name for f in dataclasses.fields(ClaudeAgentOptions)}
    assert ClaudeCodeConfig().contain_to_workspace is False
    source = inspect.getsource(ClaudeCodeScaffold._run_batch_mode)
    assert "config.contain_to_workspace" in source
    assert 'optional_containment["hooks"]' in source
    assert "_write_containment_audit()" in inspect.getsource(ClaudeCodeScaffold._cleanup_components)


def test_a_workspace_under_a_linked_run_root_is_reachable_by_either_spelling(tmp_path):
    """In a worktree `.ape/` is a link to the main checkout's store, and a process's working
    directory is resolved, so the same file arrives under two spellings."""

    from ape.scaffolds.claude_code.containment import provisioned_roots, violation

    workspaces, _base, _later, gold = _review_layout(tmp_path)
    linked = tmp_path / "linked_attempt"
    linked.symlink_to(workspaces.parent)
    roots = provisioned_roots(linked / "workspaces")
    cwd = str(linked / "workspaces")
    assert violation("Read", {"file_path": f"{workspaces}/scratch/notes.md"}, roots, cwd) is None
    assert violation("Read", {"file_path": f"{cwd}/scratch/notes.md"}, roots, cwd) is None
    assert violation("Read", {"file_path": str(gold)}, roots, cwd)


# --- the transcript must reach the attempt, or nothing can audit it ------------------------


@pytest.mark.parametrize("user_id,headers,expected", [
    # 2.1.x, as captured from the bundled CLI (2.1.139) on 2026-10-01: a header, and JSON user_id
    ('{"device_id":"d","account_uuid":"","session_id":"10f86fe9-9fb0-41a4-91bc-66d07775aa84"}',
     {"x-claude-code-session-id": "10f86fe9-9fb0-41a4-91bc-66d07775aa84"},
     "10f86fe9-9fb0-41a4-91bc-66d07775aa84"),
    ('{"device_id":"d","account_uuid":"","session_id":"10f86fe9-9fb0-41a4-91bc-66d07775aa84"}',
     None, "10f86fe9-9fb0-41a4-91bc-66d07775aa84"),
    # 2.0.x
    ("user_abc_account_1234__session_7e2f-aa01", None, "7e2f-aa01"),
    (None, None, None),
])
def test_the_relay_reads_the_session_id_of_either_cli_generation(user_id, headers, expected):
    """Read only the 2.0.x way, every request under the bundled 2.1.139 CLI failed building its
    session before any model call (the first smoke run, 2026-10-01: 12 of 12)."""

    from ape.scaffolds.claude_code.relay import ClaudeCodeRelaySession

    assert ClaudeCodeRelaySession._extract_session_id(user_id, headers) == expected


def test_the_session_file_is_found_by_name_not_by_a_rederived_directory(tmp_path):
    """The CLI names its project directory after its cwd with every non-alphanumeric character
    turned to `-` (`probe_cwd` -> `probe-cwd`); the old lookup re-derived it from `scratch/`."""

    from ape.scaffolds.claude_code.conversation import ClaudeCodeConversationManager

    project = tmp_path / ".claude" / "projects" / "-tmp-attempt-1-workspaces"
    project.mkdir(parents=True)
    session = project / "10f86fe9.jsonl"
    session.write_text("{}\n")

    find = ClaudeCodeConversationManager.find_session_file
    assert find(tmp_path, "10f86fe9") == session
    assert find(tmp_path, "absent") is None
