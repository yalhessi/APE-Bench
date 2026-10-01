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
from typing import Any, Dict, Iterable, List, Optional, Sequence

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


def provisioned_roots(workspaces_dir: Path, extra: Iterable[Path] = ()) -> List[str]:
    """The directories a session may touch: its workspace, and where the workspace's links lead.

    Each link directly in the workspace (`target`, `reference/<name>`) adds its resolved home,
    and each link directly in that home adds the directory it resolves into: for a reviewed
    workspace, the base checkout it is built on. Nothing else in the shared store is reachable.
    """

    workspaces_dir = Path(os.path.abspath(workspaces_dir))
    # The resolved spelling too: a process's working directory is resolved, so under a linked
    # `.ape/` (every worktree) Claude Code reports workspace files by their resolved paths.
    roots = {str(workspaces_dir), os.path.realpath(workspaces_dir)}
    roots.update(os.path.abspath(p) for p in extra)
    links = [p for p in workspaces_dir.iterdir() if p.is_symlink()]
    reference = workspaces_dir / "reference"
    if reference.is_dir() and not reference.is_symlink():
        links.extend(p for p in reference.iterdir() if p.is_symlink())
    for link in links:
        home = Path(os.path.realpath(link))
        if not home.is_dir():
            continue
        roots.add(str(home))
        for entry in home.iterdir():
            if entry.is_symlink():
                roots.add(os.path.dirname(os.path.realpath(entry)))
    return sorted(roots)


def _inside(path: str, roots: Sequence[str]) -> bool:
    return any(path == root or path.startswith(root.rstrip(os.sep) + os.sep) for root in roots)


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
        if not _inside(os.path.normpath(joined), roots):
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
    """

    calls: List[Dict[str, Any]] = []
    refused_ids = set()
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
                elif (block.get("type") == "tool_result" and block.get("is_error")
                      and REFUSAL_MARK in _result_text(block.get("content"))):
                    refused_ids.add(block.get("tool_use_id"))

    leaks, refused = [], []
    for call in calls:
        reason = violation(call["tool_name"], call["tool_input"], roots, cwd)
        if reason is None:
            continue
        entry = {**call, "reason": reason}
        (refused if call["id"] in refused_ids else leaks).append(entry)
    by_tool: Dict[str, int] = {}
    for call in calls:
        by_tool[call["tool_name"]] = by_tool.get(call["tool_name"], 0) + 1
    return {"transcript": str(transcript), "tool_calls": len(calls), "by_tool": by_tool,
            "refused": refused, "leaks": leaks, "clean": not leaks}
