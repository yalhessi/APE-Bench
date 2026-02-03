"""
Claude Code Conversation Manager - SDK coordination layer

Inherits from BaseConversationManager and implements Claude SDK specific:
1. SDK client management
2. Message stream processing
"""

import asyncio
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ape.scaffolds.utils.base_conversation import BaseConversationManager
from ape.scaffolds.utils.common import open_file_in_vscode

if TYPE_CHECKING:
    import logging
    from claude_agent_sdk import ClaudeSDKClient
    from .relay import ClaudeCodeRelaySession


class ClaudeCodeConversationManager(BaseConversationManager):
    """
    Claude Code conversation manager - SDK coordination

    Specific responsibilities:
    1. Manage Claude SDK client lifecycle
    2. Process SDK message stream
    3. Create hardlinks for SDK conversation files
    """

    def __init__(self, *args, resume_session_id: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)

        # Claude SDK specific
        self._claude_client: Optional['ClaudeSDKClient'] = None
        self.resume_session_id = resume_session_id

        # Hardlink creation status
        self._hardlink_created = bool(resume_session_id)

        if resume_session_id:
            self.logger.debug(f"[ClaudeCodeConversationManager] Resume mode: {resume_session_id}")

    async def _create_relay_session(
        self,
        port: int,
        conversations_dir: Path,
        cwd: str,
        logger: 'logging.LoggerAdapter',
        conversation_trees_path: Path
    ) -> 'ClaudeCodeRelaySession':
        """Create Claude Code relay session"""
        from .relay import ClaudeCodeRelaySession

        return ClaudeCodeRelaySession(
            port=port,
            llm_config=self.config.llm_config,
            fast_llm_config=self.config.fast_llm_config,
            conversations_dir=conversations_dir,
            cwd=cwd,
            logger=logger,
            conversation_trees_path=conversation_trees_path,
            max_turns=self.config.execution.max_turns,  # Pass max_turns to relay
            cost_limit=self.cost_limit  # Pass cost_limit to relay
        )

    async def _cleanup_internal(self) -> None:
        """Clean up SDK client reference"""
        if self._claude_client:
            self._claude_client = None
            self.logger.debug("[ClaudeCodeConversationManager] SDK client reference cleared")

    async def run_conversation(
        self,
        claude_client: 'ClaudeSDKClient',
        initial_prompt: Optional[str] = None
    ) -> bool:
        """
        Run conversation with Claude SDK

        Args:
            claude_client: ClaudeSDK client instance
            initial_prompt: Initial prompt (optional)

        Returns:
            True if submission detected, False otherwise
        """
        # Save client reference
        self._claude_client = claude_client

        # Send initial prompt if provided
        if initial_prompt:
            await claude_client.query(initial_prompt)
            self.logger.info("[ClaudeCodeConversationManager] Sent initial query")

        # Call base conversation loop (monitor is started in base class)
        return await super().run_conversation()

    async def _execute_turn(self) -> bool:
        """
        Execute single turn using Claude SDK

        Key difference from receive_messages():
        - receive_response() automatically returns after receiving ResultMessage
        - This ensures one complete turn (request -> response -> tool execution -> result)
        - Without this, receive_messages() would wait indefinitely for new messages

        Returns:
            True if submission detected, False otherwise
        """
        async for _ in self._claude_client.receive_response():
            # Check termination
            if self._stop_event.is_set():
                self.logger.debug("[ClaudeCodeConversationManager] Termination detected during stream")
                break

            # Try to create hardlink
            await self._try_create_hardlink()

        # Check if submission was detected (stop event was set by termination callback)
        if self._stop_event.is_set():
            self.logger.info("[ClaudeCodeConversationManager] Submission detected via termination callback")
            return True

        # No submission detected in this turn
        return False

    async def _send_retry_prompt(self, prompt: str) -> None:
        """Send retry prompt to SDK"""
        await self._claude_client.query(prompt)

    def _create_retry_prompt(self) -> str:
        """Create retry prompt for Claude SDK"""
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
        """Interrupt SDK message stream"""
        if self._claude_client:
            try:
                await self._claude_client.interrupt()
                self.logger.info("[ClaudeCodeConversationManager] SDK interrupt signal sent")
            except Exception as e:
                self.logger.warning(f"[ClaudeCodeConversationManager] Error sending interrupt: {e}")

    def get_claude_code_session_id(self) -> Optional[str]:
        """Get Claude Code session ID from relay"""
        if self._relay_session:
            return self._relay_session.claude_code_session_id
        return None

    @staticmethod
    def find_latest_hardlink(attempt_path: Path) -> Optional[str]:
        """
        Find latest hardlink file and extract session ID

        Args:
            attempt_path: Agent workspace path

        Returns:
            Session ID or None
        """
        if not attempt_path.exists():
            return None

        hardlink_files = list(attempt_path.glob("claude_code_conversation_*__*.jsonl"))
        if not hardlink_files:
            return None

        hardlink_files.sort(key=lambda f: f.name)
        latest_file = hardlink_files[-1]

        filename = latest_file.stem
        if "__" in filename:
            return filename.split("__")[-1]

        return None

    async def _try_create_hardlink(self) -> None:
        """
        Try to create hardlink for SDK conversation file (only once)

        SDK automatically creates {session_id}.jsonl in ~/.claude/projects/{encoded_cwd}/
        Since HOME is set to workspaces/, the actual path is:
        workspaces/.claude/projects/{encoded_cwd}/
        """
        if self._hardlink_created:
            return

        session_id = self.get_claude_code_session_id()
        if not session_id:
            return

        try:
            if not self.task.scratch_workspace or not self.task.attempt_path:
                raise RuntimeError("Task workspace not initialized for Claude conversation")
            # Encode cwd as project directory name
            cwd = str(self.task.scratch_workspace.path.resolve())
            encoded_cwd = cwd.replace("/", "-").replace(".", "-").replace("_", "-")

            # SDK session file path (using HOME=workspaces/)
            # HOME is now workspaces/, so ~/.claude/ is workspaces/.claude/
            workspaces_dir = self.task.workspaces_dir
            claude_home = workspaces_dir / ".claude"
            claude_projects_dir = claude_home / "projects"
            project_dir = claude_projects_dir / encoded_cwd
            sdk_session_file = project_dir / f"{session_id}.jsonl"

            if not sdk_session_file.exists():
                return

            # Create hardlink
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            attempt_path = self.task.attempt_path
            hardlink_path = attempt_path / f"claude_code_conversation_{timestamp}__{session_id}.jsonl"

            if hardlink_path.exists():
                hardlink_path.unlink()

            hardlink_path.hardlink_to(sdk_session_file)

            self._hardlink_created = True
            self.logger.info(f"[ClaudeCodeConversationManager] Created hardlink: {hardlink_path.name}")

            # Optionally open in VS Code (only in CLI mode)
            if self.is_cli_mode:
                open_file_in_vscode(hardlink_path, enabled=self.config.open_in_vscode, logger=self.logger)

        except Exception as e:
            self.logger.debug(f"[ClaudeCodeConversationManager] Failed to create hardlink: {e}")
