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


# --- the grant must be usable: dontAsk refuses whatever is not pre-approved -----------------


def test_ape_tools_and_the_grant_are_pre_approved():
    """smoke2 (2026-10-01): under dontAsk with no approvals, 7 of 8 calls were refused --
    Read, lean_verify, declaration_search and all three submit_findings -- so the reviewer read
    nothing and its review could not land."""

    from types import SimpleNamespace

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.claude_code.scaffold import ClaudeCodeScaffold

    scaffold = object.__new__(ClaudeCodeScaffold)
    scaffold.task = SimpleNamespace(config=ClaudeCodeConfig(
        llm_config=LLMConfig(model_name="gpt_5.2"), tools=["Read", "Grep", "Glob", "TodoWrite"]))
    assert scaffold._pre_approved_tools() == ["mcp__core", "Read", "Grep", "Glob", "TodoWrite"]
    assert "allowed_tools=self._pre_approved_tools()" in inspect.getsource(
        ClaudeCodeScaffold._run_batch_mode)


def test_the_audit_reports_calls_the_cli_itself_refused(tmp_path):
    """Not a leak, but a session that could not act: an empty review from it is not the
    reviewer's. The wording is the bundled 2.1.139 CLI's, from smoke2's transcript."""

    import json

    from ape.scaffolds.claude_code.containment import audit_transcript, provisioned_roots

    workspaces, _base, _later, _gold = _review_layout(tmp_path)
    denied = ("Permission to use mcp__core__submit_findings has been denied because Claude Code "
              "is running in don't ask mode.")
    lines = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "s1", "name": "mcp__core__submit_findings",
             "input": {"findings": []}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "s1", "is_error": True, "content": denied}]}},
    ]
    transcript = tmp_path / "s.jsonl"
    transcript.write_text("".join(json.dumps(line) + "\n" for line in lines))

    report = audit_transcript(transcript, provisioned_roots(workspaces), str(workspaces))
    assert report["clean"] is True
    assert report["refused_by_cli"] == [{"id": "s1", "tool_name": "mcp__core__submit_findings"}]


# --- one relay per session: its address goes to its own CLI, never the process ---------------


def test_two_relays_in_one_process_stay_separate(monkeypatch):
    """probe_postcutoff_gpt52_G_claude_rep1 (2026-10-01): each relay wrote ANTHROPIC_BASE_URL
    into os.environ when it started, and tasks run as coroutines in one process, so the CLIs
    inherited whichever relay started last -- three of six relays saw no request, one saw 39
    from four sessions sharing its turn limit, budget and transcript record."""

    import os

    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.claude_code.relay import ClaudeCodeRelaySession

    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    first, second = (ClaudeCodeRelaySession(port=port, llm_config=LLMConfig(model_name="gpt_5.2"))
                     for port in (41001, 41002))
    first.configure_environment()
    second.configure_environment()

    assert "ANTHROPIC_BASE_URL" not in os.environ
    assert "ANTHROPIC_AUTH_TOKEN" not in os.environ, "it would outrank a subscription login too"
    assert first.client_environment()["ANTHROPIC_BASE_URL"].endswith(":41001")
    assert second.client_environment()["ANTHROPIC_BASE_URL"].endswith(":41002")


def test_each_cli_process_is_given_its_own_relay():
    from ape.scaffolds.claude_code.scaffold import ClaudeCodeScaffold

    assert "**self._relay_environment()" in inspect.getsource(ClaudeCodeScaffold._run_batch_mode)
    assert "**self._relay_environment()" in inspect.getsource(ClaudeCodeScaffold._run_cli_mode)


# --- the relayed prompt must keep a stable prefix, or the provider's cache never hits ----------


def _relayed_system_text(cch):
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.claude_code.relay import ClaudeCodeRelaySession

    relay = ClaudeCodeRelaySession(port=41004, llm_config=LLMConfig(model_name="gpt_5.2"))
    request = {"system": [
        {"type": "text", "text": f"x-anthropic-billing-header: cc_version=2.1.139.f8a; cc_entrypoint=sdk-py; cch={cch};"},
        {"type": "text", "text": "You are Claude Code, Anthropic's official CLI."}],
        "messages": [{"role": "user", "content": "Review PR 1."}]}
    session = relay._convert_anthropic_to_session(request, None)
    return [b.text for b in session.nodes[0].message.content]


def test_claude_codes_per_request_billing_header_does_not_reach_the_backend():
    """2.1.139 opens its system prompt with an attribution line whose `cch` changes on every
    request. Forwarded, it put a different string at character 92 of every prompt: 0 cached
    tokens across three repetitions, $0.258 a session against about $0.089 cached."""

    first, second = _relayed_system_text("d726d"), _relayed_system_text("16be4")
    assert first == second == ["You are Claude Code, Anthropic's official CLI."]


def test_the_header_is_stripped_only_where_it_opens_a_block():
    from ape.scaffolds.claude_code.relay import strip_billing_header

    assert strip_billing_header("x-anthropic-billing-header: cch=1;\nYou are...") == "You are..."
    kept = "Quote: x-anthropic-billing-header: cch=1;"
    assert strip_billing_header(kept) == kept


# --- a streamed request gets a streamed reply, or the CLI asks for every turn twice ------------


def _replay(stream_text):
    """Rebuild a message from its events, the way a streaming client accumulates them."""

    import json

    message, blocks, partial = None, {}, {}
    for chunk in stream_text.strip().split("\n\n"):
        name_line, data_line = chunk.split("\n")
        assert name_line.startswith("event: ") and data_line.startswith("data: ")
        event = json.loads(data_line[len("data: "):])
        assert event["type"] == name_line[len("event: "):]
        if event["type"] == "message_start":
            message = event["message"]
        elif event["type"] == "content_block_start":
            blocks[event["index"]] = dict(event["content_block"])
        elif event["type"] == "content_block_delta":
            delta = event["delta"]
            if delta["type"] == "text_delta":
                blocks[event["index"]]["text"] += delta["text"]
            else:
                partial[event["index"]] = partial.get(event["index"], "") + delta["partial_json"]
        elif event["type"] == "message_delta":
            message["stop_reason"] = event["delta"]["stop_reason"]
            message["usage"]["output_tokens"] = event["usage"]["output_tokens"]
    for index, text in partial.items():
        blocks[index]["input"] = json.loads(text)
    message["content"] = [blocks[i] for i in sorted(blocks)]
    return message


def test_the_event_stream_rebuilds_the_message_it_replays():
    """Claude Code sends every turn with stream: true. Answered with JSON it discarded the reply
    and asked again without streaming: 128 main-model requests for 64 turns, each billed twice."""

    from ape.scaffolds.claude_code.relay import anthropic_event_stream

    message = {"id": "msg_1", "type": "message", "role": "assistant", "model": "gpt_5.2",
               "content": [{"type": "text", "text": "Reading the file."},
                           {"type": "tool_use", "id": "toolu_1", "name": "mcp__core__lean_verify",
                            "input": {"file_path": "target/Mathlib/A.lean", "max_messages": 20}}],
               "stop_reason": "tool_use", "stop_sequence": None,
               "usage": {"input_tokens": 16011, "output_tokens": 642}}
    assert _replay(anthropic_event_stream(message)) == message


def test_a_streamed_request_is_answered_as_a_stream():
    from ape.scaffolds.claude_code.relay import ClaudeCodeRelaySession

    source = inspect.getsource(ClaudeCodeRelaySession._handle_messages)
    assert 'anthropic_request.get("stream")' in source
    assert "anthropic_event_stream(anthropic_response)" in source
    assert 'media_type="text/event-stream"' in source


# --- carried reasoning must survive the round trip through the client ---------------------------


def test_a_turns_carried_reasoning_returns_with_it():
    """Responses carry-over keeps a turn's encrypted reasoning items in its message `signature`.
    Claude Code holds the conversation in Anthropic's format, which has no slot for that, so the
    relay rebuilt every request without it and nothing was carried. The relay now keeps it and
    puts it back when the turn comes home, and the provider turns it into reasoning input."""

    import json

    from ape.llm_clients.adapters.message_formatter import MessageFormatter
    from ape.llm_clients.config import LLMConfig
    from ape.llm_clients.models import ContentBlock, ConversationSession
    from ape.llm_clients.providers.openai_provider import responses_input
    from ape.scaffolds.claude_code.relay import ClaudeCodeRelaySession

    relay = ClaudeCodeRelaySession(port=41005, llm_config=LLMConfig(model_name="gpt_5.2"))
    carried = json.dumps({"responses_output": [
        {"type": "reasoning", "id": "rs_1", "encrypted_content": "gAAAA-opaque", "summary": []},
        {"type": "function_call", "call_id": "call_1"}]})
    response = ConversationSession()
    node = response.add_assistant_message(
        [ContentBlock.tool_use_block("call_1", "mcp__core__declaration_search", {"identifier": "Foo"})], "/w")
    node.message.signature = carried
    relay._cache_turn_signatures([node])

    request = {"system": [{"type": "text", "text": "You are Claude Code."}], "messages": [
        {"role": "user", "content": "Review PR 1."},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "call_1",
                                           "name": "mcp__core__declaration_search",
                                           "input": {"identifier": "Foo"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_1", "content": "found"}]}]}
    session = relay._convert_anthropic_to_session(request, None)
    assistant = [n for n in session.nodes if n.type == "assistant"]
    assert [n.message.signature for n in assistant] == [carried]

    _instructions, items = responses_input(MessageFormatter().format_for_api(session), carryover=True)
    kinds = [i.get("type") for i in items]
    assert kinds.index("reasoning") == kinds.index("function_call") - 1
    assert next(i for i in items if i.get("type") == "reasoning")["encrypted_content"] == "gAAAA-opaque"


def test_a_turn_without_carried_reasoning_gains_none():
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.claude_code.relay import ClaudeCodeRelaySession

    relay = ClaudeCodeRelaySession(port=41006, llm_config=LLMConfig(model_name="gpt_5.2"))
    request = {"messages": [
        {"role": "user", "content": "Review PR 1."},
        {"role": "assistant", "content": [{"type": "text", "text": "Nothing to flag."}]}]}
    session = relay._convert_anthropic_to_session(request, None)
    assert all(n.message.signature is None for n in session.nodes if n.type == "assistant")


def test_a_call_to_a_tool_that_does_not_exist_ran_nothing(tmp_path):
    """H-claude rep 2 called `zulip_search` for `mcp__core__zulip_search`, and the CLI answered
    "No such tool available". Nothing ran, so it is not a leak; an unclassifiable call without
    that answer, naming that tool, still is."""

    import json

    from ape.scaffolds.claude_code.containment import audit_transcript, provisioned_roots

    workspaces, _base, _later, _gold = _review_layout(tmp_path)
    roots = provisioned_roots(workspaces)
    lines = []
    for call_id, name, answer in (
            ("a", "zulip_search", "<tool_use_error>Error: No such tool available: zulip_search"
                                  "</tool_use_error>"),
            ("b", "zulip_search", "some result"),
            ("c", "other_tool", "<tool_use_error>Error: No such tool available: zulip_search"
                                "</tool_use_error>")):
        lines.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": call_id, "name": name, "input": {"query": "q"}}]}})
        lines.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": call_id, "is_error": True, "content": answer}]}})
    transcript = tmp_path / "s.jsonl"
    transcript.write_text("".join(json.dumps(line) + "\n" for line in lines))

    report = audit_transcript(transcript, roots, str(workspaces))
    assert [c["id"] for c in report["nonexistent"]] == ["a"]
    assert [c["id"] for c in report["leaks"]] == ["b", "c"]


def test_a_write_may_land_in_scratch_and_nowhere_else(tmp_path):
    """The review configs refused Write and Edit outright while the first message called
    `scratch/` "your workspace (read-write) ... for creating and editing files" (2026-10-01).
    Granting them needs this rule: `target/` is a link into the shared reviewed-workspace
    store, so a write there edits the environment of every other session on the same PR."""

    check, workspaces, base, _later, _gold = _rules(tmp_path)
    assert check("Write", file_path="scratch/notes.md") is None
    assert check("Write", file_path=f"{workspaces}/scratch/notes.md") is None
    assert check("Edit", file_path="scratch/notes.md") is None
    for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        key = "notebook_path" if tool == "NotebookEdit" else "file_path"
        reason = check(tool, **{key: "target/Mathlib/Foo.lean"})
        assert reason and "writes outside scratch/" in reason, (tool, reason)
    assert "writes outside scratch/" in check("Edit", file_path=f"{base}/Mathlib/Foo.lean")
    assert "leaves this review's workspace" in check("Write", file_path="/etc/notes.md")
    assert check("Read", file_path="target/Mathlib/Foo.lean") is None     # reads are unchanged


def test_the_session_cwd_is_one_resolved_spelling(tmp_path):
    """Under a linked `.ape/` the first message named two roots for one attempt, the unresolved
    one as the working directory and the resolved one in `<WORKSPACE_PATHS>` (2026-10-01)."""

    from types import SimpleNamespace

    from ape.scaffolds.claude_code.scaffold import ClaudeCodeScaffold

    real = tmp_path / "real" / "workspaces"
    real.mkdir(parents=True)
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "real")
    scaffold = object.__new__(ClaudeCodeScaffold)
    scaffold.task = SimpleNamespace(workspaces_dir=link / "workspaces")
    assert scaffold._session_cwd() == real.resolve()
