"""
Codex Scaffold - Orchestration layer using MCPServerManager

Inherits from BaseScaffold and uses shared MCP management.
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
import traceback
import warnings
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Dict

from ape.cli.task_session import is_internal_cli_task, merge_task_prompt
from ape.scaffolds.base import BaseScaffold
from ape.scaffolds.skills import (
    CODEX_REPO_SKILL_DIR,
    materialize_task_skills,
    mirror_materialized_skills,
)
from ape.toolkits.mcp_manager import MCPManager
from ape.utils.project import PROJECT_ROOT
from .config import CodexConfig
from .conversation import CodexConversationManager

if TYPE_CHECKING:
    from ape.llm_clients.models import TokenUsage
    from ape.scaffolds.config import BaseScaffoldConfig


class CodexScaffold(BaseScaffold):
    """Codex Scaffold - orchestration using MCPManager"""

    config_class = CodexConfig

    def __init__(self):
        super().__init__()
        self.conversation_manager: Optional[CodexConversationManager] = None
        self.mcp_manager: Optional[MCPManager] = None
        self.managed_skills = None

    def _setup_asyncio_exception_handler(self) -> None:
        """Configure asyncio exception handler"""
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn")
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(lambda loop, ctx: self.logger.debug(f"Asyncio exception: {ctx}"))

    async def _setup_components(self) -> None:
        """Setup components using shared utilities"""
        self._setup_asyncio_exception_handler()

        self.managed_skills = materialize_task_skills(
            self.task,
            self.logger,
            repo_skill_dirs=(CODEX_REPO_SKILL_DIR,),
        )
        self._prepare_repo_scoped_skills()

        # 1. Create conversation manager
        # When model_name is None, relay will be skipped (use official Codex models)
        self.conversation_manager = CodexConversationManager(
            config=self.task.config,
            task=self.task,
            cost_limit=self.cost_limit,
            logger=self.logger,
            is_cli_mode=self.is_cli_mode,
            token_limit=self.token_limit
        )

        # 2. Initialize conversation (starts the relay)
        await self.conversation_manager.initialize()

        # 3. Start MCP server using MCPManager (HTTP mode)
        self.mcp_manager = MCPManager(
            task=self.task,
            logger=self.logger,
            config=self.task.config,
            confirmation_bridge=None,
            is_cli_mode=self.is_cli_mode,
            use_native_tools=self.task.config.use_native_tools,
        )
        await self.mcp_manager.setup_http_mode()
        mcp_url = self.mcp_manager.get_server_url()
        self.logger.info(f"[CodexScaffold] MCP HTTP server started: {mcp_url}")

        # 4. Configure ~/.codex/config.toml (MCP server and relay if model_name is not None)
        await self._configure_codex_toml(mcp_url)

    async def _configure_codex_toml(self, mcp_url: str) -> None:
        """Write the attempt's `workspaces/.codex/config.toml` (and model catalog), which the CLI
        reads with `CODEX_HOME` pointed there. A failure raises: without this file the CLI would
        not reach the relay."""
        import tomli_w

        config = self.task.config
        if config.llm_config.model_name is None:
            raise RuntimeError("Codex scaffold requires llm_config.model_name: it runs through the relay")
        relay = self.conversation_manager._relay_session
        if relay is None:
            raise RuntimeError("Relay session not initialized")
        codex_home = self.task.workspaces_dir / ".codex"
        codex_home.mkdir(parents=True, exist_ok=True)
        model = codex_model_name(config)
        catalog = (await write_model_catalog(codex_home, model, self.logger)
                   if config.list_mcp_tools_upfront else None)
        settings = codex_config(config, model, relay.base_url, mcp_url, catalog)
        (codex_home / "config.toml").write_bytes(tomli_w.dumps(settings).encode())
        self.logger.info(
            f"[CodexScaffold] {codex_home / 'config.toml'}: model {model} via relay {relay.base_url}, "
            f"MCP core @ {mcp_url}, disabled features {config.disabled_features}, "
            f"catalog {'upfront MCP tools' if catalog else 'bundled'}")

    async def _initial_prompt(self, cwd) -> str:
        """The first message: the workspace preamble, the task's own contract, then the task.

        Codex keeps its own system prompt, so APE's preamble goes in the first user message with
        the task's contract after it, as in `claude_code`. Batch and CLI modes send the same text.
        """
        from ape.scaffolds.prompts import build_system_prompt, with_task_system_prompt

        system_prompt = await build_system_prompt(
            scratch_workspace=self.task.scratch_workspace,
            target_workspace=self.task.target_workspace,
            reference_workspaces=self.task.reference_workspaces,
            use_absolute_paths=True,
            logger=self.logger
        )
        system_prompt += (
            f"\n\nIMPORTANT: Your current working directory is `{cwd}`. "
            f"Use absolute paths like `{cwd}/scratch/`, `{cwd}/target/`. Never use relative paths.\n"
        )
        # About shell commands, so only where Codex has a shell: a review condition disables it.
        if "shell_tool" not in self.task.config.disabled_features:
            system_prompt += (
            f"\n"
            f"CRITICAL - Shell Command Requirements:\n"
            f"When using shell/bash tools, you MUST use absolute paths for ALL commands:\n"
            f"  - Correct: /bin/ls, /bin/cat, /bin/grep, /usr/bin/git, /bin/sh\n"
            f"  - Wrong: ls, cat, grep, git, sh\n"
            f"Common command paths:\n"
            f"  - /bin/ls, /bin/cat, /bin/grep, /bin/sed, /bin/awk, /bin/rm, /bin/cp, /bin/mv\n"
            f"  - /bin/bash, /bin/sh, /usr/bin/find, /usr/bin/git, /usr/bin/python\n"
            f"This is required because PATH environment variable is not available in the shell environment.\n"
            )
        system_prompt = await with_task_system_prompt(system_prompt, self.task, self.logger)
        task_user_prompt = await self.task.create_user_prompt()
        return f"{system_prompt}\n\n{'=' * 80}\n\n{task_user_prompt}"

    async def _run_batch_mode(self) -> None:
        """Run batch mode using subprocess"""
        # Use workspaces directory directly (like ape_agent)
        if not self.task.scratch_workspace:
            raise RuntimeError("Scratch workspace not initialized for Codex scaffold")

        # Use workspaces directory directly
        cwd = str(self.task.workspaces_dir)
        initial_prompt = await self._initial_prompt(cwd)

        self.logger.info(f"[CodexScaffold] Starting batch conversation (cwd: {cwd})")

        await self.conversation_manager.run_conversation(
            initial_prompt=initial_prompt
        )

        self.logger.info("[CodexScaffold] Conversation terminated (submit_result)")

    def _prepare_repo_scoped_skills(self) -> tuple[Path, ...]:
        """Mirror managed skills into attempt-local repo scope for batch and registered-task runs."""
        if not self.managed_skills or not self.managed_skills.skills:
            return tuple()
        if self.is_cli_mode and is_internal_cli_task(self.task):
            return tuple()
        if not self.task.workspaces_dir:
            raise RuntimeError("Task workspaces are not initialized for Codex managed skills")

        managed_repo_root = self.task.workspaces_dir / ".agents" / "skills"
        mirrored = mirror_materialized_skills(
            self.managed_skills,
            managed_repo_root,
        )
        self.logger.info(
            "[CodexScaffold] Mirrored %s managed skills into %s",
            len(mirrored),
            managed_repo_root,
        )
        return mirrored

    def _build_cli_environment(self) -> Optional[Dict[str, str]]:
        """Create a per-session HOME/CODEX_HOME overlay when extra-root skills are configured."""
        if not is_internal_cli_task(self.task):
            return None
        if not self.managed_skills:
            return None

        extra_root_skills = self.managed_skills.select(source_kinds={"extra_root"})
        if not extra_root_skills:
            return None
        if not self.task.attempt_path or not self.task.workspaces_dir:
            raise RuntimeError("Task workspace is not initialized for Codex CLI overlay")

        overlay_home = self.task.attempt_path / "codex_home_overlay"
        if overlay_home.exists():
            shutil.rmtree(overlay_home)
        overlay_home.mkdir(parents=True, exist_ok=True)

        overlay_codex_home = overlay_home / ".codex"
        overlay_codex_home.mkdir(parents=True, exist_ok=True)

        user_codex_home = Path(
            os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
        ).expanduser()
        if user_codex_home.is_dir():
            shutil.copytree(user_codex_home, overlay_codex_home, dirs_exist_ok=True)

        generated_codex_home = self.task.workspaces_dir / ".codex"
        if generated_codex_home.is_dir():
            shutil.copytree(generated_codex_home, overlay_codex_home, dirs_exist_ok=True)

        mirror_materialized_skills(
            self.managed_skills,
            overlay_home / ".agents" / "skills",
            source_kinds={"extra_root"},
        )

        env = os.environ.copy()
        env["HOME"] = str(overlay_home.resolve())
        env["CODEX_HOME"] = str(overlay_codex_home.resolve())
        self.logger.info(
            "[CodexScaffold] Using HOME/CODEX_HOME overlay for %s managed extra-root skills",
            len(extra_root_skills),
        )
        return env

    async def _run_cli_mode(self) -> None:
        """
        CLI mode execution - using codex command line tool

        Key differences from batch mode:
        - Direct codex command, interactive
        - TOML already configured (relay + MCP)
        - All UI handled by codex CLI

        Codex CLI Parameters (from --help):
        - -C, --cd <DIR>: Working directory
        - -s, --sandbox <SANDBOX_MODE>: read-only / workspace-write / danger-full-access
        - -a, --ask-for-approval <APPROVAL_POLICY>: untrusted / on-failure / on-request / never
        - --search: Enable web search
        - -m, --model <MODEL>: Model selection (but we use TOML config instead)
        - Positional [PROMPT]: Initial prompt
        """
        if shutil.which("codex") is None:
            self.logger.error("Error: 'codex' CLI not found. Please install: npm install -g @openai/codex")
            return

        prompt = getattr(self.task, '_cli_prompt', None)
        extra_args = getattr(self.task, '_cli_extra_args', [])

        try:
            if is_internal_cli_task(self.task):
                cwd_path = self.task.data.local_workspace_path
                initial_prompt = prompt
            else:
                if not self.task.workspaces_dir:
                    raise RuntimeError("Task workspaces are not initialized for Codex CLI mode")

                cwd_path = self.task.workspaces_dir
                task_prompt = await self._initial_prompt(cwd_path)
                initial_prompt = merge_task_prompt(task_prompt, prompt)

            cwd = str(cwd_path)

            # Build codex command with correct parameters
            codex_args = ["codex"]

            # Set sandbox mode (-s, --sandbox)
            codex_args.extend(["-s", self.task.config.sandbox_mode])

            # Set approval policy (-a, --ask-for-approval)
            codex_args.extend(["-a", self.task.config.approval_policy])

            # Enable web search if configured (--search)
            if self.task.config.web_search:
                codex_args.append("--search")

            # Add prompt as positional argument if provided
            if initial_prompt:
                codex_args.append(initial_prompt)

            # Add extra arguments
            if extra_args:
                codex_args.extend(extra_args)

            # Note: In CLI mode, we don't set HOME or CODEX_HOME
            # Codex will use the user's default configuration directory

            self.logger.info(f"[CodexScaffold] Running codex command: {' '.join(codex_args)}")
            self.logger.info(f"[CodexScaffold] Workspace: {cwd}")
            self.logger.info(f"[CodexScaffold] Sandbox mode: {self.task.config.sandbox_mode}")
            self.logger.info(f"[CodexScaffold] Approval policy: {self.task.config.approval_policy}")

            codex_env = self._build_cli_environment()

            # Run codex command (interactive mode)
            proc = await asyncio.create_subprocess_exec(
                *codex_args,
                cwd=str(cwd),
                env=codex_env,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )

            # Wait for process to end
            await proc.wait()

        except Exception:
            self.logger.error(f"[CodexScaffold] CLI mode execution failed:\n{traceback.format_exc()}")

    def _get_current_turns(self) -> int:
        """Get current turns"""
        return self.conversation_manager.get_current_turns()

    def _get_token_usage(self) -> Optional['TokenUsage']:
        """Get token usage"""
        return self.conversation_manager.get_token_usage()

    async def _interrupt_execution(self) -> None:
        """Interrupt execution"""
        await self.conversation_manager.request_stop()
        self.logger.info("[CodexScaffold] Interrupt signal sent")

    async def _cleanup_components(self) -> None:
        """Cleanup components"""
        # The audit first, so every attempt carries one whatever happens after.
        if self.task.attempt_path and not self.is_cli_mode:
            try:
                events = self.task.attempt_path / "codex_events.jsonl"
                report = audit_events(events, self.task.config)
                (self.task.attempt_path / "containment_audit.json").write_text(json.dumps(report, indent=2))
                log = self.logger.info if report["clean"] and report["usable"] else self.logger.error
                log(f"[CodexScaffold] containment audit: clean={report['clean']} usable={report['usable']} "
                    f"{report['by_kind']}")
            except Exception:
                self.logger.error(f"containment audit failed:\n{traceback.format_exc()}")

        # 1. Cleanup conversation
        if self.conversation_manager:
            await self.conversation_manager.cleanup()

        # 2. Cleanup MCPManager (stops HTTP server and cleans up all tool instances)
        if self.mcp_manager:
            await self.mcp_manager.cleanup()

        # Note: No need to cleanup TOML config as it's in scratch workspace
        # which will be cleaned up automatically

    @classmethod
    def get_required_resources(cls) -> list[tuple[Path, Optional[Path]]]:
        """Get resources required by Codex scaffold.

        Returns:
            List of (host_path, container_path) tuples for codex binary and Node.js.
            Container path is specified to rename the binary to 'codex' without version markers.
        """
        resources = []

        # Add codex binary from /data/resources
        # Copy and rename to /root/lean_research/data/resources/codex in container
        codex_binary = PROJECT_ROOT / "data" / "resources" / "codex-x86_64-unknown-linux-musl"
        if codex_binary.exists():
            container_path = Path("/root/lean_research/data/resources/codex")
            resources.append((codex_binary, container_path))

        # Add Node.js directory (required by Codex: Node.js 18+)
        # Copy entire node directory to container
        # node_dir = PROJECT_ROOT / "data" / "resources" / "node-v18.20.1-linux-x64"
        # if node_dir.exists():
        #     container_node_path = Path("/root/lean_research/data/resources/node-v18.20.1-linux-x64")
        #     resources.append((node_dir, container_node_path))

        return resources

    @classmethod
    def get_environment_config(cls, config: Optional['BaseScaffoldConfig'] = None) -> Dict[str, str]:
        """Get environment variables required for Codex scaffold in container.

        Returns:
            Environment variables for PATH configuration.
            $PATH will be expanded by runtime to container's actual PATH value.
            Includes both codex binary and Node.js bin directory.
        """
        return {
            "PATH": "/root/lean_research/data/resources/node-v18.20.1-linux-x64/bin:/root/lean_research/data/resources:$PATH"
        }


#: Event items that show the CLI acting outside APE's tools. With the shell, edits and the web
#: disabled none should appear; one that does is a leak, whatever it did.
_OUTSIDE_APE = frozenset({"command_execution", "file_change", "web_search"})


def audit_events(events: Path, config) -> dict:
    """Every item a `codex exec` session reported, checked against its grant.

    `leaks`: an item that ran outside APE's tools (a shell command, a file change, a web search),
    or an MCP call to a server other than `core`. `refused`: an MCP call the CLI cancelled, which
    leaks nothing but means the grant was not usable ("user cancelled MCP tool call" is what the
    approval prompt does in exec mode). A missing log is unauditable, recorded as such.
    """
    by_kind: Dict[str, int] = {}
    leaks, refused = [], []
    if not events.exists():
        return {"events": str(events), "by_kind": {}, "leaks": [], "refused": [], "clean": False,
                "usable": False, "error": "no codex_events.jsonl; nothing was audited"}
    for line in events.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") != "item.completed":
            continue
        item = event.get("item") or {}
        kind = item.get("type") or "?"
        by_kind[kind] = by_kind.get(kind, 0) + 1
        if kind in _OUTSIDE_APE:
            leaks.append({"kind": kind, "item": {k: item.get(k) for k in ("command", "changes", "query")}})
        elif kind == "mcp_tool_call":
            if item.get("server") != "core":
                leaks.append({"kind": kind, "server": item.get("server"), "tool": item.get("tool")})
            elif "cancelled" in str((item.get("error") or {}).get("message", "")):
                refused.append({"tool": item.get("tool"), "error": item["error"]["message"]})
    return {"events": str(events), "by_kind": by_kind, "leaks": leaks, "refused": refused,
            "clean": not leaks, "usable": not refused}


def codex_model_name(config) -> str:
    """The model name Codex is told: `codex_model`, or `llm_config.model_name` as OpenAI spells it."""
    return config.codex_model or config.llm_config.model_name.replace("_", "-")


def codex_config(config, model: str, relay_base_url: str, mcp_url: str,
                 catalog: Optional[Path]) -> dict:
    """The attempt's config.toml as a dict: the relay as the only provider, the MCP server as
    `core` with its tools pre-approved, and the configured sandbox, features and web search.

    `default_tools_approval_mode = "approve"`: in `codex exec`, a call that would ask for approval
    is cancelled ("user cancelled MCP tool call"), so without it no APE tool runs. Captured
    2026-10-01 against a local server. `project_doc_max_bytes = 0`: the workspace sits inside
    this repository, and an AGENTS.md above it would reach the reviewer as CLAUDE.md once did.
    """
    settings = {
        "model": model,
        "model_provider": "relay",
        "approval_policy": config.approval_policy,
        "sandbox_mode": config.sandbox_mode,
        "web_search": "live" if config.web_search else "disabled",
        "project_doc_max_bytes": 0,
        "model_providers": {"relay": {"name": "relay", "base_url": relay_base_url,
                                      "wire_api": "responses"}},
        "mcp_servers": {"core": {"url": mcp_url, "enabled": True,
                                 "default_tools_approval_mode": "approve",
                                 "startup_timeout_sec": 3600, "tool_timeout_sec": 3600}},
    }
    if config.disabled_features:
        settings["features"] = {name: False for name in config.disabled_features}
    if config.sandbox_mode == "workspace-write":
        settings["sandbox_workspace_write"] = {"network_access": config.network_access}
    if catalog is not None:
        settings["model_catalog_json"] = str(catalog)
    return settings


async def write_model_catalog(codex_home: Path, model: str, logger) -> Optional[Path]:
    """Codex's own catalog entry for `model`, with `supports_search_tool` off, so the MCP tools
    are listed in each request rather than found through `tool_search`. `None`, leaving Codex's
    bundled catalog, if this CLI has no entry for the model."""
    proc = await asyncio.create_subprocess_exec(
        "codex", "debug", "models", "--bundled",
        env={**os.environ, "HOME": str(codex_home.parent), "CODEX_HOME": str(codex_home)},
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    out, _ = await proc.communicate()
    try:
        models = json.loads(out)["models"]
    except (ValueError, KeyError, TypeError):
        raise RuntimeError("`codex debug models --bundled` gave no catalog")
    entry = next((m for m in models if m.get("slug") == model), None)
    if entry is None:
        logger.warning(f"[CodexScaffold] no catalog entry for {model}; Codex uses its fallback metadata")
        return None
    path = codex_home / "model_catalog.json"
    path.write_text(json.dumps({"models": [{**entry, "supports_search_tool": False}]}))
    return path


# Automatic registration
from ape.scaffolds.registry import register_scaffold
register_scaffold("codex", CodexScaffold)
