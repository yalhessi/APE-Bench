"""
Codex Scaffold - Orchestration layer using MCPServerManager

Inherits from BaseScaffold and uses shared MCP management.
"""

import asyncio
import shutil
import sys
import tempfile
import traceback
import warnings
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Dict

from ape.cli.task_session import is_internal_cli_task, merge_task_prompt
from ape.scaffolds.base import BaseScaffold
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

    def _setup_asyncio_exception_handler(self) -> None:
        """Configure asyncio exception handler"""
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn")
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(lambda loop, ctx: self.logger.debug(f"Asyncio exception: {ctx}"))

    async def _setup_components(self) -> None:
        """Setup components using shared utilities"""
        self._setup_asyncio_exception_handler()

        # 1. Create conversation manager
        # When model_name is None, relay will be skipped (use official Codex models)
        self.conversation_manager = CodexConversationManager(
            config=self.task.config,
            task=self.task,
            cost_limit=self.cost_limit,
            logger=self.logger,
            is_cli_mode=self.is_cli_mode
        )

        # 2. Initialize conversation (start relay and CodexBridge only if model_name is not None)
        # Note: CodexBridge must be installed at src/ape/scaffolds/codex/codexbridge/
        # Install from: https://github.com/begonia599/CodexBridge
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
        """
        Write Codex config.toml to scratch workspace

        This creates workspaces/.codex/config.toml with MCP configuration.
        If model_name is not None, also configure relay for custom model routing.
        """
        try:
            import tomli_w

            # Get scratch workspace path
            if not self.task.scratch_workspace:
                raise RuntimeError("Scratch workspace not initialized for Codex scaffold")

            # Build config with MCP server
            config = {
                "mcp_servers": {
                    "lean-research": {
                        "url": mcp_url,
                        "enabled": True,
                        "startup_timeout_sec": 3600,
                        "tool_timeout_sec": 3600
                    }
                }
            }

            # Add relay configuration only if model_name is not None
            if self.task.config.llm_config.model_name is not None:
                if not self.conversation_manager._relay_session:
                    raise RuntimeError("Relay session not initialized but model_name is not None")

                relay_base_url = self.conversation_manager._relay_session.base_url
                relay_model = self.task.config.llm_config.model_name

                config["model_provider"] = "relay"
                config["model"] = relay_model
                config["model_providers"] = {
                    "relay": {
                        "name": "Relay",
                        "base_url": relay_base_url
                    }
                }

            # Write to workspaces/.codex/config.toml
            # So that when HOME=workspaces/, Codex finds ~/.codex/config.toml
            workspaces_dir = self.task.workspaces_dir
            config_path = workspaces_dir / ".codex" / "config.toml"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'wb') as f:
                tomli_w.dump(config, f)

            if self.task.config.llm_config.model_name is not None:
                relay_base_url = self.conversation_manager._relay_session.base_url
                relay_model = self.task.config.llm_config.model_name
                self.logger.info(
                    f"[CodexScaffold] Configured {config_path}:\n"
                    f"  - Model provider: relay @ {relay_base_url} (model={relay_model})\n"
                    f"  - MCP server: lean-research @ {mcp_url}"
                )
            else:
                self.logger.info(
                    f"[CodexScaffold] Configured {config_path}:\n"
                    f"  - Model provider: official Codex models (no relay)\n"
                    f"  - MCP server: lean-research @ {mcp_url}"
                )

        except Exception as e:
            self.logger.warning(f"[CodexScaffold] Failed to configure Codex TOML: {e}")

    async def _run_batch_mode(self) -> None:
        """Run batch mode using subprocess"""
        # Use workspaces directory directly (like ape_agent)
        if not self.task.scratch_workspace:
            raise RuntimeError("Scratch workspace not initialized for Codex scaffold")

        # Use workspaces directory directly
        cwd = str(self.task.workspaces_dir)
        task_user_prompt = await self.task.create_user_prompt()

        # Build system prompt with absolute paths and merge into first user prompt (Claude Code style)
        from ape.scaffolds.prompts import build_system_prompt
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
        initial_prompt = f"{system_prompt}\n\n{'='*80}\n\n{task_user_prompt}"

        self.logger.info(f"[CodexScaffold] Starting batch conversation (cwd: {cwd})")

        await self.conversation_manager.run_conversation(
            initial_prompt=initial_prompt
        )

        self.logger.info("[CodexScaffold] Conversation terminated (submit_result)")

    async def _run_cli_mode(self) -> None:
        """
        CLI mode execution - using codex command line tool

        Key differences from batch mode:
        - No CodexBridge (direct codex command)
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
                cwd = str(cwd_path)

                from ape.scaffolds.prompts import build_system_prompt

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
                task_user_prompt = await self.task.create_user_prompt()
                task_prompt = f"{system_prompt}\n\n{'=' * 80}\n\n{task_user_prompt}"
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

            # Run codex command (interactive mode)
            proc = await asyncio.create_subprocess_exec(
                *codex_args,
                cwd=str(cwd),
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


# Automatic registration
from ape.scaffolds.registry import register_scaffold
register_scaffold("codex", CodexScaffold)
