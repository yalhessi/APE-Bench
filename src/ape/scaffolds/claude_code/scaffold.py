"""
Claude Code Scaffold - Orchestration layer using MCPServerManager

Inherits from BaseScaffold and uses shared MCP management.
"""

import asyncio
import os
import shutil
import sys
import tempfile
import traceback
import warnings
from pathlib import Path
from typing import Optional, TYPE_CHECKING, List, Dict, Any

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from ape.scaffolds.base import BaseScaffold
from ape.toolkits.mcp_manager import MCPManager
from ape.utils.project import PROJECT_ROOT
from .config import ClaudeCodeConfig
from .conversation import ClaudeCodeConversationManager

if TYPE_CHECKING:
    from ape.llm_clients.models import TokenUsage
    from ape.scaffolds.config import BaseScaffoldConfig


class ClaudeCodeScaffold(BaseScaffold):
    """Claude Code Scaffold - orchestration using MCPManager"""

    config_class = ClaudeCodeConfig

    def __init__(self):
        super().__init__()
        self.conversation_manager: Optional[ClaudeCodeConversationManager] = None
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

        # Validate bash configuration with runtime type
        config = self.task.config

        # Resume not supported (conversation files moved to scratch/.claude)
        resume_session_id = None

        # 1. Create conversation manager
        # When model_name is None, relay will be skipped (use official Claude Code models)
        self.conversation_manager = ClaudeCodeConversationManager(
            config=self.task.config,
            task=self.task,
            cost_limit=self.cost_limit,
            logger=self.logger,
            is_cli_mode=self.is_cli_mode,
            resume_session_id=resume_session_id
        )

        # 2. Initialize conversation (start relay only if model_name is not None)
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
        self.logger.info(f"[ClaudeCodeScaffold] MCP HTTP server started: {self.mcp_manager.get_server_url()}")

    def _get_resume_session_id(self) -> Optional[str]:
        """Get resume session ID from latest hardlink"""
        return ClaudeCodeConversationManager.find_latest_hardlink(
            self.task.attempt_path
        )

    async def _run_batch_mode(self) -> None:
        """Run batch mode using Claude SDK"""
        config = self.task.config

        # Configure MCP servers
        mcp_servers = {
            "core": {
                "type": "http",
                "url": self.mcp_manager.get_server_url()
            }
        }

        # Workspace configuration
        # Use workspaces directory directly (like ape_agent)
        if not self.task.scratch_workspace or not self.task.attempt_path:
            raise RuntimeError("Task workspace not initialized for Claude scaffold")

        # Use workspaces directory directly
        cwd = self.task.workspaces_dir

        # No need for add_dirs since cwd is the workspaces directory
        add_dirs = []

        # Build disallowed_tools based on configuration
        disallowed_tools = ["Explore"]
        if config.use_native_tools:
            # Disallow SDK builtin file tools when using native MCP tools
            disallowed_tools.extend(["Read", "Write", "Edit", "MultiEdit", "LS", "Glob", "Grep"])
            self.logger.info("[ClaudeCodeScaffold] use_native_tools=True, disallowed SDK builtin file tools")

        # Get resume session ID
        resume_session_id = self.conversation_manager.resume_session_id

        # Build system prompt with absolute paths for Claude Code
        from ape.scaffolds.prompts import build_system_prompt
        system_prompt = await build_system_prompt(
            scratch_workspace=self.task.scratch_workspace,
            target_workspace=self.task.target_workspace,
            reference_workspaces=self.task.reference_workspaces,
            use_absolute_paths=True,
            logger=self.logger
        )

        # Add cwd information to system prompt
        system_prompt += f"\n\nIMPORTANT: Your current working directory is `{cwd}`. Use absolute paths like `{cwd}/scratch/`, `{cwd}/target/`. Never use relative paths.\n"

        # Configure HOME environment variable for SDK
        # Set HOME to workspaces/ directory so SDK creates session files there
        # This allows Claude to access HOME/.claude/ and write to workspaces/
        workspaces_dir = self.task.workspaces_dir
        claude_home = workspaces_dir

        # Build Claude Agent options
        # Note: system_prompt is not passed here, it will be merged into initial_prompt instead
        options = ClaudeAgentOptions(
            model=config.llm_config.model_name,
            max_turns=config.execution.max_turns,
            mcp_servers=mcp_servers,
            cwd=cwd,
            add_dirs=add_dirs,
            permission_mode=config.permission_mode,
            disallowed_tools=disallowed_tools,
            include_partial_messages=True,
            resume=resume_session_id,
            fork_session=True if resume_session_id else False,
            env={
                'HOME': str(claude_home.resolve()),
                'CLAUDE_CODE_DISABLE_COMMAND_INJECTION_CHECK': '1'
            }
        )

        self.logger.info("[ClaudeCodeScaffold] Starting batch conversation")

        # Create SDK client and run conversation
        async with ClaudeSDKClient(options) as client:
            # Get task user prompt
            task_user_prompt = await self.task.create_user_prompt()

            # Merge system prompt and user prompt
            # For Claude Code, we put system prompt as part of user prompt
            initial_prompt = f"{system_prompt}\n\n{'='*80}\n\n{task_user_prompt}"

            await self.conversation_manager.run_conversation(
                claude_client=client,
                initial_prompt=initial_prompt
            )
            self.logger.info("[ClaudeCodeScaffold] Conversation terminated (submit_result)")

    async def _run_cli_mode(self) -> None:
        """CLI mode execution - using claude command line tool"""
        if shutil.which("claude") is None:
            self.logger.error("Error: 'claude' CLI not found. Please install: npm install -g @anthropic-ai/claude-code")
            return

        config = self.task.config
        prompt = getattr(self.task, '_cli_prompt', None)
        extra_args = getattr(self.task, '_cli_extra_args', [])

        try:
            # Add MCP server to claude configuration
            await self._add_mcp_server_to_claude()

            # In CLI mode, use the workspace path directly (from --workspace or current directory)
            # No need to create scratch_workspace, use task.data.local_workspace_path
            cwd = self.task.data.local_workspace_path

            # Build claude command
            claude_args = [
                "claude",
                "--permission-mode", config.permission_mode
            ]

            # If there is an initial prompt, use print mode
            if prompt:
                claude_args.extend(["-p", prompt])

            # Add extra arguments
            if extra_args:
                claude_args.extend(extra_args)

            # Reuse conversation_manager's internal relay (started in _setup_components)
            # relay has been set environment variables through configure_environment()
            # external claude command will automatically use these environment variables

            # Run claude command
            # Note: In CLI mode, we don't set HOME
            # Claude will use the user's default HOME directory and execute in the workspace directory
            self.logger.info(f"Running: {' '.join(claude_args)}")
            self.logger.info(f"[ClaudeCodeScaffold] Workspace: {cwd}")

            proc = await asyncio.create_subprocess_exec(
                *claude_args,
                cwd=str(cwd),
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )

            # Wait for process to end
            await proc.wait()

        except Exception:
            self.logger.error(f"CLI mode execution failed:\n{traceback.format_exc()}")
        finally:
            # Clean up MCP server configuration
            self.logger.debug("Cleaning up MCP server configuration from claude CLI")
            await self._remove_mcp_server_from_claude()

    async def _add_mcp_server_to_claude(self):
        """Add MCP server to claude configuration"""
        try:
            cmd = [
                "claude", "mcp", "add",
                "--transport", "http",
                "lean-research",
                self.mcp_manager.get_server_url()
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            _, stderr = await proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                raise RuntimeError(f"Failed to add MCP server: {error_msg}")

        except Exception as e:
            self.logger.warning(f"Error adding MCP server to claude: {e}")
            raise

    async def _remove_mcp_server_from_claude(self):
        """Remove MCP server configuration: `claude mcp remove lean-research`"""
        try:
            cmd = ["claude", "mcp", "remove", "lean-research"]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await proc.communicate()

        except Exception as e:
            self.logger.warning(f"Error removing MCP server from claude (non-fatal): {e}")

    def _get_current_turns(self) -> int:
        """Get current turns"""
        return self.conversation_manager.get_current_turns()

    def _get_token_usage(self) -> Optional['TokenUsage']:
        """Get token usage"""
        return self.conversation_manager.get_token_usage()

    async def _interrupt_execution(self) -> None:
        """Interrupt execution"""
        await self.conversation_manager.request_stop()
        self.logger.info("[ClaudeCodeScaffold] Interrupt signal sent")

    async def _cleanup_components(self) -> None:
        """Cleanup components"""
        # 1. Cleanup conversation
        if self.conversation_manager:
            await self.conversation_manager.cleanup()

        # 2. Cleanup MCPManager (stops HTTP server and cleans up all tool instances)
        if self.mcp_manager:
            await self.mcp_manager.cleanup()

    @classmethod
    def get_required_resources(cls) -> list[tuple[Path, Optional[Path]]]:
        """Get resources required by Claude Code scaffold.

        Returns:
            List of (host_path, container_path) tuples for claude-code binary.
            Container path is specified to rename the binary to 'claude' without version markers.
        """
        resources = []

        # Add claude-code binary from /data/resources
        # Copy and rename to /root/lean_research/data/resources/claude in container
        claude_binary = PROJECT_ROOT / "data" / "resources" / "claude-2.0.37-linux-x64"
        if claude_binary.exists():
            container_path = Path("/root/lean_research/data/resources/claude")
            resources.append((claude_binary, container_path))

        return resources

    @classmethod
    def get_environment_config(cls, config: Optional['BaseScaffoldConfig'] = None) -> Dict[str, str]:
        """Get environment variables required for Claude Code scaffold in container.

        Returns:
            Environment variables for PATH configuration.
            $PATH will be expanded by runtime to container's actual PATH value.
        """
        return {
            "PATH": "/root/lean_research/data/resources:$PATH",
            "IS_SANDBOX": "1"
        }


# Automatic registration
from ape.scaffolds.registry import register_scaffold
register_scaffold("claude_code", ClaudeCodeScaffold)
