"""The files a run config hands a reviewer, resolved to the bytes a session will read, before any runs.

A solo-family task reads two optional files at execution time: `system_prompt_file`, a brief in place
of the built-in system prompt, and `context_file`, per-PR sections appended to the user prompt. Until
2026-10-22 only their *paths* reached the run's identity, inside `scaffold_config_sha256`, which a
resume may change; so a brief edited at the same path was read by every later session of a resumed
run and nothing refused it, and "what did this reviewer see" meant finding which revision of the file
was on disk when each session started.

Now, one resolver, used by the run and by `cli report inputs`:

- `resolve_input_files` reads each named file's bytes and digest;
- the run plan seals the digests (`evaluation_settings["input_files"]`, which a resume may not change),
  so an edited brief refuses a resume rather than becoming part of it;
- `snapshot_input_files` copies the bytes into the run directory (`inputs/`), so what a session read
  stays readable after the file moves on;
- `pin_overrides` hands each task the digest, and the task refuses bytes that do not match it, so an
  edit between two sessions of one attempt cannot slip in either.

A path is a locator: the same bytes at another path are the same input.

A context file derived from session outputs (`analysis/sessions.derive_context`) carries
`<file>.lineage.json`. The resolver recomputes the file from it, so a missing or changed upstream
output is refused before any session, and records the lineage beside the digest; the plan still
seals the bytes alone, because the same bytes are the same input whatever produced them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from src.mathlib_review.io import sha256_bytes, write_once

#: Task-config fields naming a file whose bytes a session reads, and the field that pins each.
INPUT_FILE_FIELDS = {"system_prompt_file": "system_prompt_sha256",
                     "context_file": "context_file_sha256"}
SNAPSHOT_DIR = "inputs"


def resolve_input_files(task_overrides: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    """{field: {"path", "sha256"}} for every input file the overrides name."""

    resolved: Dict[str, Dict[str, str]] = {}
    for field in INPUT_FILE_FIELDS:
        value = (task_overrides or {}).get(field)
        if value in (None, "", "None"):
            continue
        path = Path(value)
        if not path.is_file():
            raise FileNotFoundError(f"{field} {str(path)!r} is not a file")
        resolved[field] = {"path": str(path), "sha256": sha256_bytes(path.read_bytes())}
        if field == "context_file":
            from src.mathlib_review.analysis.sessions import context_lineage_path, verify_context

            lineage = verify_context(path)
            if lineage is not None:
                resolved[field]["lineage"] = str(context_lineage_path(path))
                resolved[field]["lineage_sha256"] = lineage.source_sha256
    return resolved


def sealed_digests(resolved: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """What the plan seals: the digest of each input, never its path."""

    return {field: item["sha256"] for field, item in sorted(resolved.items())}


def pin_overrides(resolved: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """The task-config overrides that make each task verify the bytes it reads."""

    return {INPUT_FILE_FIELDS[field]: item["sha256"] for field, item in resolved.items()}


def snapshot_input_files(resolved: Dict[str, Dict[str, str]], run_dir: Path) -> Dict[str, Dict[str, str]]:
    """Copy each input's bytes into `<run_dir>/inputs/`, named by content; returns `resolved` with
    each item's `snapshot` path. A second run of the same bytes writes nothing new."""

    out: Dict[str, Dict[str, str]] = {}
    for field, item in resolved.items():
        source = Path(item["path"])
        data = source.read_bytes()
        if sha256_bytes(data) != item["sha256"]:
            raise ValueError(f"{field} {source} changed between resolving and snapshotting it")
        target = Path(run_dir) / SNAPSHOT_DIR / f"{field}-{item['sha256'][:16]}{source.suffix}"
        write_once(target, data)
        out[field] = {**item, "snapshot": str(target)}
        if item.get("lineage"):
            lineage = Path(item["lineage"]).read_bytes()
            kept = target.with_name(target.name + ".lineage.json")
            write_once(kept, lineage)
            out[field]["lineage_snapshot"] = str(kept)
    return out


def verified_text(path: Path, expected_sha256: Optional[str], field: str) -> str:
    """A file's text, refused when its bytes are not the ones the run sealed."""

    data = Path(path).read_bytes()
    if expected_sha256 and sha256_bytes(data) != expected_sha256:
        raise ValueError(
            f"{field} {path} is not the file this run sealed (sha256 {expected_sha256[:12]}...); it "
            "was edited after the plan was sealed. A session must not read other bytes than its "
            "run's: use a new run name for the edited file.")
    return data.decode("utf-8")


async def mcp_signatures(task):
    import logging
    from fastmcp import FastMCP
    from ape.toolkits.mcp_manager import MCPManager

    # Use the same tool binding as MCPManager.setup_http_mode, entirely in memory.
    manager = MCPManager(task, logging.getLogger(__name__), task.config, use_native_tools=task.config.use_native_tools)
    manager.mcp_server = FastMCP("inspect")
    manager._bind_tools_to_server(manager.calculate_enabled_tools())
    await task.register_task_tools(manager.mcp_server)
    return {tool.name: (tool.description, tool.parameters) for tool in await manager.mcp_server.list_tools()}


async def first_message(task, cwd, target):
    import logging
    from ape.scaffolds.claude_code.scaffold import ClaudeCodeScaffold
    from ape.tasks.models import WorkspaceInfo

    task.workspaces_dir = cwd
    task.scratch_workspace = WorkspaceInfo(name="scratch", path=cwd / "scratch")
    task.target_workspace = WorkspaceInfo(name="target", path=target, read_only_path_patterns=["**/*"])
    scaffold = ClaudeCodeScaffold()
    scaffold.task, scaffold.logger = task, logging.getLogger(__name__)
    return await scaffold._initial_prompt(scaffold._session_cwd())
