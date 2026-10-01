"""Containment for a Claude Code session: built-in tools may touch only the attempt's workspace.

The review configs grant Read, Grep, Glob and TodoWrite under `permission_mode: dontAsk`, and
refuse Bash and the web. What that grant reaches was never shown: Read takes any absolute path,
and from a review workspace an absolute path reaches this repository's gold, the mathlib clone
whose HEAD is months past every episode, and every other PR's reviewed workspace. So two checks
are added, sharing one rule, `violation`:

- **a refusal**, `pre_tool_use_hook`: a PreToolUse hook that denies a built-in tool call whose
  path leaves the workspace, before Claude Code's own permission logic runs;
- **an audit**, `audit_transcript`: every tool call in the session transcript, checked
  afterwards, so a run carries evidence of the containment it had rather than a claim. A call
  that left the workspace and was not refused is a leak, whatever the hook believed.

Paths are compared **lexically**, not resolved. `workspaces/target` is a symlink into the shared
reviewed-workspace store, and that tree is itself links into the base checkout: those links are
the provisioned environment. What is refused is a path the agent writes that leaves the tree --
absolute, or through `..`. The resolved homes of the provisioned links are allowed too
(`provisioned_roots`), since a tool may report a file by its resolved path; the store's other
workspaces, some of them later commits, are not.

APE's own MCP tools (`mcp__*`) are not checked here: they are scoped by APE, the same tools
`ape_agent` runs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ape.utils.file_ops import provisioned_roots, within_roots

#: Built-in tool -> the input keys that name a filesystem location.
PATH_KEYS: Dict[str, tuple] = {
    "Read": ("file_path",),
    "Write": ("file_path",),
    "Edit": ("file_path",),
    "MultiEdit": ("file_path",),
    "NotebookRead": ("notebook_path",),
    "NotebookEdit": ("notebook_path",),
    "Grep": ("path",),
    "Glob": ("path", "pattern"),
    "LS": ("path",),
}

#: Built-in tools with no filesystem reach.
NO_PATH = frozenset({"TodoWrite"})

#: Opens every refusal, so the audit can tell a refused call from one that ran.
REFUSAL_MARK = "[ape containment]"

#: How Claude Code words a refusal by its own permission mode ("Permission to use Read has been
#: denied because Claude Code is running in don't ask mode", 2.1.139).
CLI_REFUSAL_MARKS = ("Permission to use", "has been denied")

#: How Claude Code answers a call to a tool that does not exist, by that tool's name (2.1.285:
#: "<tool_use_error>Error: No such tool available: zulip_search</tool_use_error>").
NO_SUCH_TOOL = "No such tool available: {name}"


def violation(tool_name: str, tool_input: Dict[str, Any], roots: Sequence[str],
              cwd: str) -> Optional[str]:
    """Why this call leaves the workspace, or None when it stays inside."""

    if tool_name.startswith("mcp__") or tool_name in NO_PATH:
        return None
    keys = PATH_KEYS.get(tool_name)
    if keys is None:
        # A tool the grant did not name reached the hook: refuse it rather than guess its reach.
        return f"{tool_name} is not a tool this containment can check"
    base = os.path.join(cwd, tool_input.get("path") or "")
    for key in keys:
        value = tool_input.get(key)
        if value in (None, ""):
            continue  # Grep and Glob default to the working directory
        if not isinstance(value, str):
            return f"{tool_name}.{key} is not a path"
        # A Glob pattern is joined to its base; normpath collapses `..` lexically, wildcards and all.
        joined = os.path.join(base if key == "pattern" else cwd, value)
        if not within_roots(os.path.normpath(joined), roots):
            return f"{tool_name}.{key} leaves this review's workspace: {value}"
    return None


def pre_tool_use_hook(roots: Sequence[str], cwd: str, refusals: List[Dict[str, Any]],
                      logger=None):
    """A PreToolUse hook refusing any built-in call `violation` objects to.

    Refusals are appended to `refusals` so the scaffold can report them beside the audit. A call
    it does not object to gets no decision, so Claude Code's own permission mode still applies.
    """

    async def hook(input_data, tool_use_id, context):
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input") or {}
        reason = violation(tool_name, tool_input, roots, cwd)
        if reason is None:
            return {}
        refusals.append({"tool_use_id": tool_use_id, "tool_name": tool_name,
                         "tool_input": tool_input, "reason": reason})
        if logger is not None:
            logger.warning("[containment] refused %s: %s", tool_name, reason)
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"{REFUSAL_MARK} {reason}. Use paths under {cwd}.",
        }}

    return hook


def _result_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


def audit_transcript(transcript: Path, roots: Sequence[str], cwd: str) -> Dict[str, Any]:
    """Every tool call in a Claude Code session transcript, checked against `violation`.

    `leaks` are calls that left the workspace and were not refused; `refused` are those the
    hook stopped. A run with any leak is not readable, and nor is one whose transcript is gone.
    `refused_by_cli` are calls Claude Code's own permission mode turned down, which leak nothing
    but mean the session could not do what it was granted.
    """

    calls: List[Dict[str, Any]] = []
    refused_ids = set()
    cli_refused_ids = set()
    error_texts: Dict[str, str] = {}
    with open(transcript, encoding="utf-8") as fh:
        for line in fh:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = record.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    calls.append({"id": block.get("id"), "tool_name": block.get("name", ""),
                                  "tool_input": block.get("input") or {}})
                elif block.get("type") == "tool_result" and block.get("is_error"):
                    text = _result_text(block.get("content"))
                    error_texts[block.get("tool_use_id")] = text
                    if REFUSAL_MARK in text:
                        refused_ids.add(block.get("tool_use_id"))
                    elif all(mark in text for mark in CLI_REFUSAL_MARKS):
                        cli_refused_ids.add(block.get("tool_use_id"))

    # A call to a tool that does not exist ran nothing: the CLI answered it with its own error,
    # naming that tool. H-claude rep 2 (2026-10-01) called `zulip_search` for
    # `mcp__core__zulip_search` once; read as a leak, it made a session unreadable.
    nonexistent_ids = {c["id"] for c in calls if NO_SUCH_TOOL.format(name=c["tool_name"])
                       in error_texts.get(c["id"], "")}
    leaks, refused = [], []
    for call in calls:
        if call["id"] in nonexistent_ids:
            continue
        reason = violation(call["tool_name"], call["tool_input"], roots, cwd)
        if reason is None:
            continue
        entry = {**call, "reason": reason}
        (refused if call["id"] in refused_ids else leaks).append(entry)
    by_tool: Dict[str, int] = {}
    for call in calls:
        by_tool[call["tool_name"]] = by_tool.get(call["tool_name"], 0) + 1
    # Refused by Claude Code itself: not a leak, but a session that could not act, whose empty
    # review would otherwise read as the reviewer's (smoke2: 7 of 8 calls).
    refused_by_cli = [{"id": c["id"], "tool_name": c["tool_name"]}
                      for c in calls if c["id"] in cli_refused_ids]
    nonexistent = [{"id": c["id"], "tool_name": c["tool_name"]}
                   for c in calls if c["id"] in nonexistent_ids]
    return {"transcript": str(transcript), "tool_calls": len(calls), "by_tool": by_tool,
            "refused": refused, "leaks": leaks, "clean": not leaks,
            "refused_by_cli": refused_by_cli, "nonexistent": nonexistent}
