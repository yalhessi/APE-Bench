"""
Codex Conversation Manager - HTTP-based conversation coordination

Uses CodexBridge as HTTP API to communicate with Codex SDK.
Similar to ClaudeCode design but adapted for HTTP protocol.

Prerequisites:
- CodexBridge is configured as a git submodule at: src/ape/scaffolds/codex/codexbridge/
- Repository: https://github.com/begonia599/CodexBridge
- Pinned to commit: dea9bd729a379882119754a6d50a2c02951b582b
- Initialize submodules: git submodule update --init --recursive

Core responsibilities (aligned with ClaudeCode):
1. Manage CodexBridge Node.js service lifecycle
2. Manage internal relay lifecycle
3. HTTP-based communication with CodexBridge
4. Intelligent stop detection and prompt supplement
5. Cost limit checking
"""

import asyncio
import shutil
import uuid
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ape.scaffolds.utils.base_conversation import BaseConversationManager

if TYPE_CHECKING:
    import logging
    from .relay import CodexRelaySession


class CodexConversationManager(BaseConversationManager):
    """
    Codex conversation manager - HTTP-based coordination

    Specific responsibilities:
    1. Manage CodexBridge Node.js service
    2. Send HTTP requests to CodexBridge
    3. Detect submission from response
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # CodexBridge service
        self._codexbridge_process: Optional[asyncio.subprocess.Process] = None
        self._codexbridge_port: Optional[int] = None
        self._codexbridge_url: Optional[str] = None
        self._session_id = f"ape-{uuid.uuid4()}"

        # Initial prompt (sent on first turn)
        self._initial_prompt: Optional[str] = None
        self._first_turn = True
        # Pending user prompt for next turn (avoid empty messages)
        self._pending_prompt: Optional[str] = None

    async def _create_relay_session(
        self,
        port: int,
        conversations_dir: Path,
        cwd: str,
        logger: 'logging.LoggerAdapter',
        conversation_trees_path: Path
    ) -> 'CodexRelaySession':
        """Create Codex relay session"""
        from .relay import CodexRelaySession

        return CodexRelaySession(
            port=port,
            llm_config=self.config.llm_config,
            conversations_dir=conversations_dir,
            cwd=cwd,
            logger=logger,
            conversation_trees_path=conversation_trees_path,
            max_turns=self.config.execution.max_turns,  # Pass max_turns to relay
            cost_limit=self.cost_limit  # Pass cost_limit to relay
        )

    async def _start_codexbridge(self) -> None:
        """Start CodexBridge Node.js service"""
        from ape.scaffolds.utils.common import allocate_port

        # Check dependencies
        if not shutil.which("node"):
            raise RuntimeError("Node.js not found. Please install Node.js 18+")
        if not shutil.which("npm"):
            raise RuntimeError("npm not found. Please install npm")

        codexbridge_dir = Path(__file__).parent / "codexbridge"

        # Install dependencies if needed
        await self._ensure_npm_dependencies(codexbridge_dir)

        # Allocate port and start service
        self._codexbridge_port = allocate_port()
        self._codexbridge_url = f"http://localhost:{self._codexbridge_port}"

        self.logger.info(f"[CodexConversationManager] Starting CodexBridge on port {self._codexbridge_port}")

        # Get workspace path (aligned with ClaudeCode)
        import os
        # CRITICAL: Use absolute paths! CodexBridge runs from its own directory,
        # so relative paths won't work
        if not self.task.scratch_workspace or not self.task.attempt_path:
            raise RuntimeError("Task workspace is not initialized for Codex conversation")

        # CRITICAL: Set CODEX_WORKDIR to workspaces/ (not scratch/) to allow access to all subdirectories
        # Codex needs to access scratch/, target/, and reference/ directories
        workspaces_dir = self.task.workspaces_dir
        workspace_path = str(workspaces_dir.resolve())  # Use workspaces/ as working directory
        sandbox_home = str(workspaces_dir.resolve())
        codex_home = str((workspaces_dir / ".codex").resolve())

        if self.config.llm_config.model_name is None:
            raise RuntimeError("Codex scaffold requires llm_config.model_name (official Codex models are not supported)")

        env = {
            **os.environ.copy(),
            "HOME": sandbox_home,  # HOME points to workspaces/ directory
            "PORT": str(self._codexbridge_port),
            "CODEX_BRIDGE_API_KEY": "ape-scaffold-key",
            "CODEX_SKIP_GIT_CHECK": "true",
            "CODEX_WORKDIR": workspace_path,  # Force Codex to run in workspaces/ directory (absolute path)
            "CODEX_HOME": codex_home,  # CRITICAL: Point to config.toml location (absolute path)
            "CODEX_SANDBOX_MODE": self.config.sandbox_mode,
            "CODEX_NETWORK_ACCESS": "true" if self.config.network_access else "false",
            "CODEX_WEB_SEARCH": "true" if self.config.web_search else "false",
            "CODEX_APPROVAL_POLICY": self.config.approval_policy,
            "CODEX_REQUIRE_SESSION_ID": "true",
            "CODEX_LOG_REQUESTS": "false",
            "CODEX_MODEL": self.config.llm_config.model_name,
            "RUST_BACKTRACE": "1"
        }

        self.logger.debug(f"[CodexConversationManager] CODEX_HOME={codex_home}")
        self.logger.debug(f"[CodexConversationManager] CODEX_WORKDIR={workspace_path}")

        self._codexbridge_process = await asyncio.create_subprocess_exec(
            "node",
            "server.js",
            cwd=str(codexbridge_dir),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Create dedicated log files for CodexBridge
        # Use the same log directory as the main scaffold logs (at attempt_path level)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get log directory - should be at attempt_path/logs (same level as conversations)
        log_dir = self.task.attempt_path / self.config.logs_dir_name
        log_dir.mkdir(parents=True, exist_ok=True)

        codexbridge_stdout_log = log_dir / f"codexbridge_stdout_{timestamp}.log"
        codexbridge_stderr_log = log_dir / f"codexbridge_stderr_{timestamp}.log"

        # Start background tasks to read stdout/stderr (prevent pipe blocking)
        asyncio.create_task(self._log_codexbridge_output(
            self._codexbridge_process.stdout, "stdout", codexbridge_stdout_log
        ))
        asyncio.create_task(self._log_codexbridge_output(
            self._codexbridge_process.stderr, "stderr", codexbridge_stderr_log
        ))

        self.logger.info(f"[CodexConversationManager] CodexBridge logs: {codexbridge_stdout_log}, {codexbridge_stderr_log}")

        # Wait for server to be ready
        await self._wait_for_codexbridge_ready()

        self.logger.info(f"[CodexConversationManager] CodexBridge started: {self._codexbridge_url}")

    async def _log_codexbridge_output(self, stream, stream_name: str, log_file: Path) -> None:
        """Read and log CodexBridge output to prevent pipe blocking"""
        try:
            # Open log file for writing
            with open(log_file, 'a', encoding='utf-8') as f:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode('utf-8', errors='ignore').rstrip()
                    if decoded:
                        # Write to dedicated log file
                        f.write(f"{decoded}\n")
                        f.flush()  # Ensure immediate write
        except Exception as e:
            self.logger.debug(f"[CodexConversationManager] Error reading {stream_name}: {e}")

    async def _ensure_npm_dependencies(self, codexbridge_dir: Path) -> None:
        """Install npm dependencies if needed"""
        node_modules = codexbridge_dir / "node_modules"

        if node_modules.exists():
            self.logger.debug("[CodexConversationManager] npm dependencies already installed")
            return

        self.logger.info("[CodexConversationManager] Installing npm dependencies...")

        proc = await asyncio.create_subprocess_exec(
            "npm",
            "install",
            cwd=str(codexbridge_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
            raise RuntimeError(f"Failed to install npm dependencies: {error_msg}")

        self.logger.info("[CodexConversationManager] npm dependencies installed")

    async def _wait_for_codexbridge_ready(self, timeout: float = 30.0) -> None:
        """Wait for CodexBridge to be ready"""
        import httpx

        start_time = asyncio.get_event_loop().time()
        health_url = f"{self._codexbridge_url}/health"
        last_error = None

        while True:
            # Check if process died
            if self._codexbridge_process and self._codexbridge_process.returncode is not None:
                returncode = self._codexbridge_process.returncode
                raise RuntimeError(
                    f"CodexBridge process terminated unexpectedly with code {returncode}. "
                    f"Check logs for error details. Last error: {last_error}"
                )

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                # Provide detailed error message
                error_msg = f"CodexBridge failed to start within {timeout}s. "
                if self._codexbridge_process:
                    error_msg += f"Process is still running (PID: {self._codexbridge_process.pid}). "
                error_msg += f"Health check URL: {health_url}. "
                if last_error:
                    error_msg += f"Last connection error: {last_error}"
                raise RuntimeError(error_msg)

            # Try health check
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(health_url, timeout=2.0)
                    if resp.status_code == 200:
                        self.logger.debug("[CodexConversationManager] CodexBridge health check passed")
                        return
                    else:
                        last_error = f"HTTP {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                # Log first few attempts for debugging
                if elapsed < 5:
                    self.logger.debug(f"[CodexConversationManager] Health check failed (will retry): {e}")

            await asyncio.sleep(0.5)

    async def _stop_codexbridge(self) -> None:
        """Stop CodexBridge service"""
        if not self._codexbridge_process:
            return

        self.logger.info("[CodexConversationManager] Stopping CodexBridge")

        try:
            self._codexbridge_process.terminate()
            try:
                await asyncio.wait_for(self._codexbridge_process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._codexbridge_process.kill()
                await self._codexbridge_process.wait()
        except Exception as e:
            self.logger.warning(f"[CodexConversationManager] Error stopping CodexBridge: {e}")
        finally:
            self._codexbridge_process = None

        self.logger.debug("[CodexConversationManager] CodexBridge stopped")

    async def _cleanup_internal(self) -> None:
        """Clean up CodexBridge"""
        await self._stop_codexbridge()

    async def initialize(self):
        """
        Initialize conversation manager

        Start relay and CodexBridge (batch mode only)
        """
        # Call base initialization (starts relay and monitor)
        await super().initialize()

        # Start CodexBridge only in batch mode
        # CLI mode directly calls `codex` command, no need for CodexBridge
        if not self.is_cli_mode:
            await self._start_codexbridge()
            self.logger.info("[CodexConversationManager] Batch mode: CodexBridge started")
        else:
            self.logger.info("[CodexConversationManager] CLI mode: Skipping CodexBridge (will use codex command directly)")

    async def run_conversation(self, initial_prompt: str) -> bool:
        """
        Run conversation with CodexBridge via HTTP

        Design (aligned with ClaudeCode):
        1. Relay enforces turn/cost limits via shutdown
        2. Submission detected via stop_event (set by submit_result tool)
        3. Base class handles retry loop and limit checking

        Args:
            initial_prompt: Initial prompt

        Returns:
            True if submission detected, False otherwise
        """
        # Store initial prompt and prime next turn
        self._initial_prompt = initial_prompt
        self._pending_prompt = initial_prompt

        # Call base conversation loop (handles retry logic, limit checks, etc.)
        return await super().run_conversation()

    async def _execute_turn(self) -> bool:
        """
        Execute single turn by calling CodexBridge HTTP API

        Design (aligned with ClaudeCode):
        - Send HTTP request to CodexBridge
        - If relay shuts down during request, connection will fail
        - But we don't handle that here - monitor task detects relay shutdown
        - Next loop iteration in run_conversation() will check _relay_error

        Returns:
            True if submission detected, False otherwise
        """
        import httpx

        # Build messages for this turn (one user prompt per turn)
        messages = []
        if self._pending_prompt:
            messages.append({"role": "user", "content": self._pending_prompt})
            self._pending_prompt = None
            self._first_turn = False
        else:
            self.logger.warning("[CodexConversationManager] No pending prompt for this turn; skipping request")
            return False

        # Build request payload (OpenAI compatible)
        payload = {
            "session_id": self._session_id,
            "messages": messages,
            "stream": False
        }

        # Make HTTP request to CodexBridge
        # Note: If relay shuts down, this will fail with connection error
        # Monitor task will set _relay_error, and next loop iteration will detect it
        url = f"{self._codexbridge_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer ape-scaffold-key"
        }

        async with httpx.AsyncClient() as client:
            # No timeout - Codex may take a long time for complex tasks
            resp = await client.post(url, json=payload, headers=headers, timeout=None)

            if resp.status_code != 200:
                error_text = resp.text
                self.logger.error(f"[CodexConversationManager] Request failed: {error_text}")
                # Don't raise - let monitor detect relay shutdown
                return False

            # Response successful
            _ = resp.json()

            # Log turn statistics
            current_turns = self.get_current_turns()
            self.logger.debug(
                f"[CodexConversationManager] Turn completed, "
                f"total LLM calls: {current_turns}"
            )

        # Check if submission was detected (stop_event set by submit_result tool)
        # This check happens AFTER successful response, aligned with ClaudeCode
        if self._stop_event.is_set():
            self.logger.info(
                "[CodexConversationManager] Submission detected via stop_event "
                "(submit_result tool called)"
            )
            return True

        return False

    async def _send_retry_prompt(self, prompt: str) -> None:
        """Queue retry prompt for next turn"""
        self._pending_prompt = prompt
        self.logger.debug("[CodexConversationManager] Retry prompt queued for next turn")

    def _create_retry_prompt(self) -> str:
        """Create retry prompt for Codex"""
        # Get submit tool name from config (mcp_server_name already includes trailing __)
        submit_tool_name = f"{self.config.mcp_server_name}submit_result"

        return (
            f"Continue. You must submit your final result using the `{submit_tool_name}` tool "
            "when you have completed the task. "
            "Leverage all available tools to thoroughly complete the task. "
            "Analyze, create, modify, verify, and iterate as needed. "
            f"When the task is fully completed, use `{submit_tool_name}`."
        )

    async def _interrupt_internal(self) -> None:
        """Interrupt execution - stop CodexBridge"""
        await self._stop_codexbridge()
