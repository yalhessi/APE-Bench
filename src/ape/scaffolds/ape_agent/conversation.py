"""
APE Agent Conversation Manager Module.

Provides conversation management for the APE Agent scaffold with:
- Intelligent stop detection
- Session management with resume support
- Core conversation flow control
- Tool execution handling
"""

import asyncio
import aiofiles
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List, Tuple, TYPE_CHECKING
from fastmcp import FastMCP, Client
from fastmcp.exceptions import ToolError
import uuid

from ape.utils.logging import create_logger
from ape.llm_clients.models import ContentBlock

if TYPE_CHECKING:
    import logging
    from ape.llm_clients import LLMClient
    from ape.llm_clients.models import TokenUsage, ConversationSession, ConversationNode
    from ape.tasks.base import BaseTask

from .config import ApeAgentConfig


from ape.scaffolds.base import ConversationStoppedError, ConversationInterruptedError

def should_stop_conversation(session: 'ConversationSession',
                           consecutive_retries_threshold: Optional[int] = 3,
                           total_retries_threshold: Optional[int] = None) -> Tuple[bool, str]:
    """Check if conversation should stop using dual-layer detection.

    Args:
        session: Conversation session.
        consecutive_retries_threshold: Consecutive retry threshold (None to disable).
        total_retries_threshold: Total retry threshold (None to disable).

    Returns:
        Tuple of (should_stop, reason).
    """
    consecutive_retries = 0
    total_retries = 0

    for node in session.nodes:
        if node.type == "user" and node.message.role == "user":
            has_tool_result = any(
                block.type == "tool_result"
                for block in node.message.content
            )

            if has_tool_result:
                consecutive_retries = 0
            else:
                is_retry = any(
                    block.type == "text" and block.is_retry_prompt
                    for block in node.message.content
                )

                if is_retry:
                    total_retries += 1
                    consecutive_retries += 1

                    if consecutive_retries_threshold is not None and consecutive_retries >= consecutive_retries_threshold:
                        return True, f"Consecutive retry threshold reached ({consecutive_retries} retries)"

                    if total_retries_threshold is not None and total_retries >= total_retries_threshold:
                        return True, f"Total retry threshold reached ({total_retries} retries)"
                else:
                    consecutive_retries = 0

    return False, ""


class ApeAgentConversationManager:
    """Conversation manager for APE Agent scaffold.

    Responsibilities:
    - run_conversation: Main loop and flow control
    - _call_llm_api: LLM API calls
    - _handle_llm_response: Response handling and intelligent stop detection
    - _execute_tool_calls: Tool execution
    """
    
    def __init__(self, config: ApeAgentConfig,
                 task: Optional['BaseTask'] = None, cost_limit: Optional[float] = None,
                 logger: Optional['logging.LoggerAdapter'] = None,
                 interrupt_event: Optional[asyncio.Event] = None,
                 is_cli_mode: bool = False):
        self.config = config
        self.task = task
        self.cost_limit = cost_limit
        self.logger = logger or create_logger()
        self.is_cli_mode = is_cli_mode

        # Core components
        self.llm_client: Optional['LLMClient'] = None
        self.conversation_session: Optional['ConversationSession'] = None
        self._conversation_usage: List['TokenUsage'] = []
        self._stop_event = asyncio.Event()
        self.tools: List[Dict[str, Any]] = []

        # Session file management (aligned with Claude Code relay)
        self._session_file: Optional[Path] = None  # Full multi-turn conversation file (attempt_path/ape_agent_session_*.jsonl)
        self._session_created_at: Optional[str] = None
        self._persisted_node_count: int = 0  # Number of nodes already written to the session file

        # Interrupt handling
        self.interrupt_event = interrupt_event

        # Working directory support for standalone mode (no environment)
        self._temp_workspace: Optional[Path] = None

        self.logger.info("ConversationManager initialized")

    # ========================================================================
    # Session management helpers
    # ========================================================================

    def _get_conversations_dir(self) -> Path:
        """Return the directory used to persist conversation files."""
        if self.task and self.task.attempt_path:
            return self.task.attempt_path / self.config.conversations_dir_name

        # Standalone/test mode: use a temp directory
        if self._temp_workspace is None:
            import tempfile
            self._temp_workspace = Path(tempfile.mkdtemp(prefix="ape_conversations_"))
        return self._temp_workspace / self.config.conversations_dir_name

    def _get_session_context(self) -> str:
        """Get session context info (cwd)."""
        if self.task and self.task.scratch_workspace:
            return str(self.task.scratch_workspace.path)

        # Standalone mode: use current working directory
        import os
        return os.getcwd()
    
    def _ensure_session_file(self, attempt_path: Path, session_id: str) -> Path:
        """
        Ensure the session has a stable multi-turn log file (mirrors Claude Code hard-link behavior).

        Location: attempt_path/ape_agent_session_{timestamp}__{session_id}.jsonl
        Purpose: Resume mode loads the full conversational history.

        Args:
            attempt_path: Agent workspace path.
            session_id: Session identifier.

        Returns:
            Path to the multi-turn session file.
        """
        if self._session_created_at is None:
            self._session_created_at = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self._session_file is None:
            self._session_file = attempt_path / f"ape_agent_session_{self._session_created_at}__{session_id}.jsonl"
        return self._session_file
    
    async def _save_session(self, session: 'ConversationSession', incremental: bool = False):
        """
        Persist the full session to disk (used for resume functionality).

        Location: attempt_path/ape_agent_session_{timestamp}__{session_id}.jsonl
        Aligns with the Claude Code hard-link design.

        Args:
            session: Conversation session object.
            incremental: Append mode flag.
                - False: Rewrite entire file.
                - True: Append new nodes only.

        Design highlights:
        - One file per session to support resume.
        - Incremental mode appends based on persisted node count.
        """
        if not self.task or not self.task.attempt_path:
            return  # Standalone mode skips persisting session files

        attempt_path = self.task.attempt_path

        try:
            attempt_path.mkdir(parents=True, exist_ok=True)
            session_file = self._ensure_session_file(attempt_path, session.session_id)

            if incremental:
                existing_count = self._persisted_node_count
                if not session_file.exists() or existing_count > len(session.nodes):
                    incremental = False
                else:
                    new_nodes = session.nodes[existing_count:]
                    if not new_nodes:
                        return
                    async with aiofiles.open(session_file, 'a', encoding='utf-8') as f:
                        for node in new_nodes:
                            line = json.dumps(node.model_dump(mode='json'), ensure_ascii=False, default=str) + '\n'
                            await f.write(line)
                    self._persisted_node_count = len(session.nodes)
                    return

            async with aiofiles.open(session_file, 'w', encoding='utf-8') as f:
                for node in session.nodes:
                    line = json.dumps(node.model_dump(mode='json'), ensure_ascii=False, default=str) + '\n'
                    await f.write(line)
            self._persisted_node_count = len(session.nodes)
        except asyncio.CancelledError:
            self.logger.debug("Session save cancelled (normal during task completion)")
            raise
        except Exception as e:
            self.logger.debug(f"Failed to save session: {e}")
    
    async def record_turn(
        self,
        session: 'ConversationSession',
        new_nodes: List['ConversationNode'],
        usage: 'TokenUsage',
        turn_number: int,
        raw_response: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a single conversation turn (aligned with Claude Code relay's record_turn).

        Three files are saved:
        1. conversations/{timestamp}__turn_{n}.jsonl - turn snapshot containing all nodes up to that round.
        2. conversations/{timestamp}__turn_{n}_raw.jsonl - raw LLM response (for RL training).
        3. attempt_path/ape_agent_session_*.jsonl - full multi-turn session (append-only).

        Args:
            session: Conversation session.
            new_nodes: Nodes added in this turn.
            usage: Token usage stats.
            turn_number: Turn index.
            raw_response: Raw LLM API response (contains raw_output_ids, etc.)
        """
        if not new_nodes:
            return

        conversations_dir = self._get_conversations_dir()

        try:
            conversations_dir.mkdir(parents=True, exist_ok=True)

            # 1. Save a turn snapshot under conversations/ (full context)
            now = datetime.now()
            timestamp_str = now.strftime("%Y%m%d_%H%M%S_%f")[:-3]
            file_uid = str(uuid.uuid4())[:8]
            filename = f"{timestamp_str}__turn_{turn_number}__{file_uid}.jsonl"
            filepath = conversations_dir / filename

            # Write every node from the beginning through the current turn
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                for node in session.nodes:
                    line = json.dumps(
                        node.model_dump(mode='json'),
                        ensure_ascii=False,
                        default=str
                    ) + '\n'
                    await f.write(line)

            self.logger.debug(f"Recorded turn {turn_number}: {filename}, cost=${usage.total_cost:.6f}")

            # 2. Save raw response (for RL training)
            if raw_response:
                raw_filename = f"{timestamp_str}__turn_{turn_number}__{file_uid}_raw.jsonl"
                raw_filepath = conversations_dir / raw_filename

                async with aiofiles.open(raw_filepath, 'w', encoding='utf-8') as f:
                    line = json.dumps(
                        raw_response,
                        ensure_ascii=False,
                        default=str
                    ) + '\n'
                    await f.write(line)

                self.logger.debug(f"Recorded raw response: {raw_filename}")

            # 3. Update the full session file (append mode)
            await self._save_session(session, incremental=True)

        except Exception as e:
            self.logger.error(f"Failed to record turn: {e}")

    async def _add_nodes_to_session(self, session: 'ConversationSession', nodes: List['ConversationNode']):
        """Append nodes to the session (persistence handled later by record_turn)."""
        for node in nodes:
            node.sessionId = session.session_id
            session.nodes.append(node)

        self.logger.debug(f"Added {len(nodes)} nodes to session")
    
    async def _add_prompt_to_session(self, session: 'ConversationSession', message: str, is_retry_prompt: bool = False):
        """
        Append an auxiliary prompt message to the session.

        Note: this only updates the session file and skips per-turn snapshots.
        """
        cwd = self._get_session_context()
        session.add_user_message(
            content_blocks=[ContentBlock.text_block(message, is_retry_prompt=is_retry_prompt)],
            cwd=cwd
        )
        # Only update the session file
        await self._save_session(session, incremental=True)
    
    @staticmethod
    def find_latest_session_path(attempt_path: Path) -> Optional[Path]:
        """
        Locate the latest session file (mirrors Claude Code's find_latest_hardlink).

        Filename pattern: ape_agent_session_{timestamp}__{session_id}.jsonl
        Location: attempt_path/

        Args:
            attempt_path: Agent workspace path.

        Returns:
            Path to the latest session file, or None if absent.
        """
        if not attempt_path.exists():
            return None

        session_files = list(attempt_path.glob("ape_agent_session_*__*.jsonl"))
        if not session_files:
            return None

        # Sort by filename (includes timestamp)
        session_files.sort(key=lambda f: f.name)
        return session_files[-1]
    
    @classmethod  
    async def _load_session(cls, log_file: Path) -> Optional['ConversationSession']:
        """Load a session from a jsonl file asynchronously to avoid blocking."""
        from ape.llm_clients.models import ConversationSession, ConversationNode
        
        if not log_file.exists():
            return None
        
        nodes = []
        session_id = None
        
        try:
            async with aiofiles.open(log_file, 'r', encoding='utf-8') as f:
                async for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            node = ConversationNode.model_validate(data)
                            nodes.append(node)
                            if session_id is None:
                                session_id = node.sessionId
                        except Exception:
                            continue
            
            if not nodes or not session_id:
                return None
            return ConversationSession(session_id=session_id, nodes=nodes)
        except Exception:
            return None
    
    async def resume_or_create_session(self, max_turns: int = None, tools: Optional[List[Dict[str, Any]]] = None) -> 'ConversationSession':
        """Resume an existing session or create a new one (aligned with Claude Code).

        Resume workflow:
        1. Find the most recent session file (attempt_path/ape_agent_session_*__*.jsonl).
        2. Load session nodes and token usage.
        3. Clean up unfinished assistant messages (ensure tool results are complete).
        4. Return the session while preserving the session_id to reuse prompt caches.

        Alignment:
        - Claude Code reads from hard-linked files.
        - APE Agent reads from session jsonl files.

        Args:
            max_turns: Conversation turn limit.
            tools: Tool list.

        Returns:
            ConversationSession that was resumed or newly created.
        """
        if max_turns is None:
            max_turns = self.config.execution.max_turns

        # Find the latest session file under attempt_path/
        if self.task and self.task.attempt_path:
            attempt_path = self.task.attempt_path
            latest_session_file = self.find_latest_session_path(attempt_path)

            if latest_session_file:
                existing_session = await self._load_session(latest_session_file)
                if existing_session:
                    # Extract timestamp and session_id
                    filename = latest_session_file.stem
                    if "__" in filename:
                        parts = filename.split("__")
                        if len(parts) >= 2:
                            self._session_created_at = parts[0].replace("ape_agent_session_", "")

                    self._session_file = latest_session_file
                    self._persisted_node_count = len(existing_session.nodes)

                    resumed_session = await self._create_session_from_existing(existing_session)

                    # Restore token usage information
                    self._restore_conversation_usage(resumed_session)

                    total_cost = sum(u.total_cost for u in self._conversation_usage)
                    self.logger.info(
                        f"Resumed session {resumed_session.session_id} via {latest_session_file.name} "
                        f"with {len(resumed_session.nodes)} nodes, "
                        f"restored {len(self._conversation_usage)} usage records "
                        f"(total cost: ${total_cost:.6f})"
                    )
                    return resumed_session
                else:
                    self.logger.warning(
                        f"Failed to load session file {latest_session_file.name}, will create a new session"
                    )

        return await self.create_conversation_session(max_turns, tools)
    
    async def _create_session_from_existing(self, existing_session: 'ConversationSession') -> 'ConversationSession':
        """
        Create a new session from an existing one while cleaning incomplete messages.

        Design guidelines:
        - Exit via MAX_TURNS/COST_LIMIT: last turn is complete (message + tool saved) → keep it.
        - Crash/interruption: may contain unfinished tool executions → remove incomplete data.

        Validation steps:
        1. If the last node is an assistant with tool calls.
        2. Verify that subsequent nodes contain all corresponding tool results.
        3. Remove the assistant message and trailing nodes if results are missing.
        """
        import copy

        new_session = copy.deepcopy(existing_session)
        
        # Ensure the final assistant message is complete
        if new_session.nodes and len(new_session.nodes) > 0:
            # Locate the last assistant node
            last_assistant_idx = None
            for i in range(len(new_session.nodes) - 1, -1, -1):
                if new_session.nodes[i].type == "assistant":
                    last_assistant_idx = i
                    break
            
            if last_assistant_idx is not None:
                assistant_node = new_session.nodes[last_assistant_idx]
                
                # Determine whether the assistant issued tool calls
                has_tool_calls = False
                tool_call_ids = set()
                for block in assistant_node.message.content:
                    if block.type == "tool_use":
                        has_tool_calls = True
                        tool_call_ids.add(block.id)
                
                if has_tool_calls:
                    # Gather subsequent tool results
                    tool_result_ids = set()
                    for i in range(last_assistant_idx + 1, len(new_session.nodes)):
                        node = new_session.nodes[i]
                        if node.type == "user":
                            for block in node.message.content:
                                if block.type == "tool_result":
                                    tool_result_ids.add(block.tool_use_id)
                    
                    # Verify each tool call has a matching tool result
                    missing_results = tool_call_ids - tool_result_ids
                    
                    if missing_results:
                        # Incomplete: remove the assistant message and everything after it
                        new_session.nodes = new_session.nodes[:last_assistant_idx]
                        self.logger.info(
                            f"Removed incomplete assistant message and subsequent nodes "
                            f"(missing {len(missing_results)} tool results) - likely due to crash/interruption"
                        )
        
        # Preserve original session ID for prompt cache reuse
        # Resume relies on reusing the same session_id so Claude can reuse the prompt cache
        for node in new_session.nodes:
            node.sessionId = new_session.session_id
        
        self.logger.info(
            f"Resumed session with preserved session_id={new_session.session_id} "
            f"for prompt cache reuse"
        )
        
        self.conversation_session = new_session
        await self._save_session(new_session)
        return new_session
    
    def _restore_conversation_usage(self, session: 'ConversationSession'):
        """Restore token usage information from the session (critical for resume).

        Key goals:
        - Rebuild self._conversation_usage.
        - Ensure cost-limit checks are based on historical totals.

        Data flow:
        1. session.jsonl → ConversationSession.nodes
        2. Extract assistant usage → rebuild _conversation_usage
        3. run_conversation uses sum(u.total_cost for u in self._conversation_usage)

        Example:
        - Initial run (3 turns): usage [u1, u2, u3], total $0.15
        - Saved to session.jsonl
        - Resume: load session → restore [u1, u2, u3] → append [u4, u5]
        - Final: usage [u1, u2, u3, u4, u5], total $0.23

        Args:
            session: Conversation loaded from jsonl.
        """
        self._conversation_usage.clear()
        
        for node in session.nodes:
            # Only assistant messages carry usage data
            if node.type == "assistant" and node.message.usage:
                self._conversation_usage.append(node.message.usage)
        
        if self._conversation_usage:
            total_cost = sum(u.total_cost for u in self._conversation_usage)
            self.logger.debug(
                f"Restored {len(self._conversation_usage)} usage records from session, "
                f"total cost: ${total_cost:.6f}"
            )
    
    async def _task_system_prompt(self) -> Optional[str]:
        """The task's own system-level contract, when it defines one.

        Optional by design: most tasks put everything in the user prompt, and `BaseTask` does
        not declare this method at all. A task that raises or returns nothing is treated as
        having no contract rather than failing the run — a missing prompt should degrade the
        review, not abort it.
        """

        builder = getattr(self.task, "create_system_prompt", None)
        if builder is None:
            return None
        try:
            text = await builder()
        except NotImplementedError:
            return None
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("task system prompt unavailable: %s", exc)
            return None
        return (text or "").strip() or None

    async def create_conversation_session(self, max_turns: int = None, tools: Optional[List[Dict[str, Any]]] = None) -> 'ConversationSession':
        """Create a new conversation session."""
        from ape.llm_clients.models import ConversationSession
        from ape.scaffolds.prompts import build_system_prompt
        from ape.scaffolds.skills import get_task_managed_skills

        if max_turns is None:
            max_turns = self.config.execution.max_turns

        session = ConversationSession()

        cwd = self._get_session_context()
        self._session_created_at = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._persisted_node_count = 0

        # Initialize the session file path (used once nodes are added)
        if self.task and self.task.attempt_path:
            attempt_path = self.task.attempt_path
            self._session_file = self._ensure_session_file(attempt_path, session.session_id)

        # Only attach a system prompt when a task exists with workspace info
        if self.task and self.task.scratch_workspace:
            managed_skills = get_task_managed_skills(self.task)
            # Use environment-style variables so MCP tools can parse them
            system_prompt = await build_system_prompt(
                scratch_workspace=self.task.scratch_workspace,
                target_workspace=self.task.target_workspace,
                reference_workspaces=self.task.reference_workspaces,
                is_cli_mode=self.is_cli_mode,
                managed_skills=None if managed_skills is None else managed_skills.skills,
                logger=self.logger
            )
            # A task may contribute its own system-level contract on top of the workspace
            # preamble. Nothing used to call `create_system_prompt()`: it is defined on seven
            # task classes across v2, v4 and v5 and was invoked by no scaffold, so every
            # task-level system prompt in this project — the focused checkers' contracts, the
            # v4 candidate prompts, the v5 lead's routing policy — was silently discarded and
            # only the user prompt reached the model. Appending rather than replacing keeps
            # the workspace/tool preamble the harness depends on.
            task_system_prompt = await self._task_system_prompt()
            if task_system_prompt:
                system_prompt = f"{system_prompt}\n\n{'=' * 80}\n\n{task_system_prompt}"
            session.add_system_message(
                content_blocks=[ContentBlock.text_block(system_prompt)],
                cwd=cwd
            )

            # Record tool definitions separately
            if tools:
                session.add_tool_definitions(
                    tools=tools,
                    cwd=cwd
                )

        self.conversation_session = session
        await self._save_session(session)
        return session
    
    async def initialize(self):
        """Initialize the LLM client."""
        from ape.llm_clients import LLMClient

        # Directly use llm_config from the configuration
        self.llm_client = LLMClient(self.config.llm_config, logger=self.logger)
        await self.llm_client.__aenter__()
        self.logger.debug(f"LLM client initialized for provider: {self.config.llm_config.provider_type}")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.llm_client:
            await self.llm_client.__aexit__(None, None, None)

        # Remove temporary workspace if present
        if self._temp_workspace is not None and self._temp_workspace.exists():
            import shutil
            try:
                shutil.rmtree(self._temp_workspace)
                self.logger.debug(f"Removed temporary workspace: {self._temp_workspace}")
            except Exception as e:
                self.logger.warning(f"Failed to remove temporary workspace: {e}")

        self.llm_client = None
        self.conversation_session = None
        self._conversation_usage.clear()
        self._session_file = None
        self._session_created_at = None
        self._persisted_node_count = 0
        self._temp_workspace = None
        self.logger.debug("ConversationManager cleanup completed")
    
    # ========================================================================
    # Core conversation flow
    # ========================================================================
    
    async def run_conversation(self,
                            prompt: str = None,
                            session: Optional['ConversationSession'] = None,
                            mcp_instance: Client = None,
                            force_tool_use: bool = True,
                            streaming: Optional[bool] = None,
                            streaming_callback: Optional[Callable[[str, str], None]] = None,
                            user_input_callback: Optional[Callable[[], Any]] = None) -> bool:
        """Main conversation loop (supports resume and CLI interaction).

        Responsibilities:
        1. Manage the conversation loop: call the LLM, execute tools, persist state.
        2. Enforce limits by checking turns and cost before each round.
        3. Persist session/usage incrementally.
        4. Resume support: automatically restore historical usage totals.
        5. CLI interaction: block on user input via user_input_callback when provided.

        CLI interaction flow:
        - When user_input_callback is provided, CLI mode is enabled.
        - After an LLM response without tool calls, invoke the callback to wait for input.
        - User input is appended to the session and the loop continues until exit/limits.

        Resume behavior:
        - resume_or_create_session() restores previous usage.
        - Each round checks current turns and total cost.
        - Execution pattern: call_api() → append usage → save nodes.

        Args:
            prompt: Initial user prompt (only for new sessions).
            session: Existing session to reuse (optional).
            mcp_instance: MCP client instance.
            force_tool_use: Require tool calls (True for batch, False for CLI).
            streaming: Whether to enable streaming output.
            streaming_callback: Callback invoked with streaming chunks.
            user_input_callback: CLI callback returning user input; None indicates exit.

        Returns:
            True if submit_result triggered termination.
            False if max_turns was hit or the user exited.

        Raises:
            CostExhaustedError when cost limit is exceeded.
            ConversationStoppedError when intelligent stop triggers.
        """
        if not self.llm_client:
            await self.initialize()

        # Fetch available tools so we can record them in the session
        tools_list = await self._get_available_tools(mcp_instance) if mcp_instance else []
        self.tools = tools_list

        # Initialize or resume the session
        if session is None:
            session = await self.resume_or_create_session(tools=tools_list)

        # Add the initial prompt only when the session has no user messages yet
        has_user_message = any(
            node.type == "user"
            for node in session.nodes
        )

        if prompt and not has_user_message:
            cwd = self._get_session_context()

            session.add_user_message(
                content_blocks=[ContentBlock.text_block(prompt)],
                cwd=cwd
            )
            self.logger.debug(f"Added initial user prompt to new session")
        elif prompt and has_user_message:
            self.logger.debug(f"Skipping prompt addition in resume scenario (session has {len(session.nodes)} nodes)")
        
        # ====================================================================
        # Resume logging
        # ====================================================================
        is_resume = len(session.nodes) > 0
        
        if is_resume:
            # Log the restored state for visibility.
            # The orchestrator already enforces limits; this is informational only.
            current_turns = session.get_assistant_count()
            current_cost = sum(u.total_cost for u in self._conversation_usage)
            max_turns = self.config.execution.max_turns
            cost_str = f"${self.cost_limit:.6f}" if self.cost_limit else "N/A"
            
            self.logger.info(
                f"Resuming conversation from saved state:"
                f"\n  - Current turns: {current_turns}/{max_turns}"
                f"\n  - Already spent: ${current_cost:.6f}"
                f"\n  - Cost limit: {cost_str}"
            )
        
        # ====================================================================
        # Main loop with unified limit checks
        # ====================================================================
        max_turns = self.config.execution.max_turns
        
        while True:
            # ================================================================
            # Unified checkpoint: evaluate limits and interrupts before each turn
            # ================================================================
            # Goals:
            # 1. Check before starting a turn so we never exceed limits.
            # 2. Once checks pass, we execute a complete turn (message + tool persistence).
            # 3. Cost may grow each turn, so re-check every iteration.
            # 4. This is the single enforcement point; runners do not duplicate it.
            # ================================================================

            # External termination signal (highest priority, triggered by submit_result via terminate())
            if self._stop_event.is_set():
                self.logger.info("Conversation terminated by external signal (submit_result via terminate())")
                return True  # external termination counts as success

            # User interrupt (ESC key)
            if self.interrupt_event and self.interrupt_event.is_set():
                self.logger.info("Conversation interrupted by user (ESC key)")
                raise ConversationInterruptedError("User interrupted conversation with ESC key")

            current_turns = session.get_assistant_count()
            current_cost = sum(u.total_cost for u in self._conversation_usage)
            
            # Enforce turn limit
            if current_turns >= max_turns:
                from ape.scaffolds.base import MaxTurnsReachedError
                self.logger.info(
                    f"Max turns limit reached: {current_turns}/{max_turns} - "
                    f"last turn's message and tools are saved for potential resume"
                )
                raise MaxTurnsReachedError(
                    f"Max turns limit reached: {current_turns}/{max_turns}"
                )
            
            # Enforce cost limit
            # current_cost always reflects restored history + newly appended usage
            # cost_limit is provided by the orchestrator (sample_max_cost)
            if self.cost_limit is not None:
                if current_cost >= self.cost_limit:
                    from ape.llm_clients.config import CostExhaustedError
                    self.logger.warning(
                        f"Cost limit exceeded: current_cost=${current_cost:.6f} >= limit=${self.cost_limit:.6f} - "
                        f"last turn's message and tools are saved for potential resume"
                    )
                    raise CostExhaustedError(
                        f"Cost limit exceeded: ${current_cost:.6f} >= ${self.cost_limit:.6f}"
                    )
            
            # Log state on the first turn or at regular checkpoints
            if current_turns == 0:
                cost_str = f"limit ${self.cost_limit:.6f}" if self.cost_limit else "N/A"
                self.logger.info(
                    f"Starting conversation - turns: {current_turns}/{max_turns}, current_cost: ${current_cost:.6f}, {cost_str}"
                )
            
            # ================================================================
            # Execute a full turn: API call → save messages → run tools → save results
            # Guarantees:
            # 1. No interruption mid-turn unless system/user aborts.
            # 2. Messages and tool results are persisted.
            # 3. Token usage is appended to _conversation_usage.
            # 4. Next loop iteration re-checks the new cost.
            # ================================================================
            try:
                # Execute one turn (termination is handled externally via terminate())
                await self._single_turn(
                    session=session,
                    mcp_instance=mcp_instance,
                    force_tool_use=force_tool_use,
                    streaming=streaming,
                    streaming_callback=streaming_callback,
                    user_input_callback=user_input_callback
                )

                # Loop continues; external termination will be seen at the top

            except ConversationInterruptedError as e:
                # User interruption (ESC). In CLI mode we keep the session alive
                # and wait for the next user input instead of terminating.
                self.logger.info(f"Turn interrupted by user: {e}")

                # Clear the interrupt flag for the next interaction
                if self.interrupt_event:
                    self.interrupt_event.clear()

                # Notify streaming callback that the stream ended
                if streaming_callback:
                    try:
                        streaming_callback("", 'stream_end')
                    except:
                        pass

                # Wait for the next CLI user input, if a callback is available
                if user_input_callback:
                    # Prompt the user immediately
                    user_message = await user_input_callback()

                    if user_message is None:
                        # User chose to exit
                        self.logger.info("User chose to exit after interrupt")
                        return False

                    # Fetch session context
                    cwd = self._get_session_context()

                    # Append the user message to the session
                    session.add_user_message(
                        content_blocks=[ContentBlock.text_block(user_message)],
                        cwd=cwd
                    )
                    await self._save_session(session, incremental=True)
                    self.logger.debug(f"Added user message after interrupt: {user_message[:50]}...")

                    # Continue the loop with the new message
                    continue
                else:
                    # In batch mode the interrupt stops the conversation
                    raise
    
    async def _single_turn(self, session: 'ConversationSession',
                          mcp_instance: Client, force_tool_use: bool = True,
                          streaming: Optional[bool] = None,
                          streaming_callback: Optional[Callable[[str, str], None]] = None,
                          user_input_callback: Optional[Callable[[], Any]] = None) -> None:
        """
        Execute a single turn in three steps:

        1. Call the LLM API.
        2. Handle the response (tool calls, intelligent stop, fallback prompts).
        3. Execute tools if needed.

        Note: does not return should_terminate; external termination is handled via _stop_event.

        Raises:
            ConversationInterruptedError: User interruption handled by the caller.
        """
        from ape.llm_clients.adapters.streaming_processor import StreamingInterruptedError

        try:
            # Step 1: call the LLM API
            nodes, usage = await self._call_llm_api(session, streaming, streaming_callback)

            # Step 2: handle the response
            await self._handle_llm_response(
                session=session,
                nodes=nodes,
                usage=usage,
                mcp_instance=mcp_instance,
                force_tool_use=force_tool_use,
                streaming=streaming,
                streaming_callback=streaming_callback,
                user_input_callback=user_input_callback
            )

        except StreamingInterruptedError as e:
            # Convert streaming interruption to a unified interruption error
            self.logger.info(f"Streaming interrupted: {e}")
            raise ConversationInterruptedError(f"User interrupted during streaming: {e}") from e
    
    async def _call_llm_api(self, session: 'ConversationSession',
                           streaming: bool, streaming_callback: Optional[Callable]) -> Tuple[List['ConversationNode'], 'TokenUsage']:
        """
        Call the LLM API and persist the response.

        Resume-friendly design:
        1. Call the API to fetch the response (even if cost growth might exceed limits next round).
        2. Immediately persist nodes to the session so resume always has a complete message.
        3. Immediately record usage for the next loop's cost check.
        4. Do not enforce cost limits here; run_conversation handles that centrally.

        Resume guarantee:
        - Even if the next loop stops due to cost, the current message is saved.
        - Increasing cost limits later lets us continue from this consistent state.
        """
        from ape.llm_clients.config import MalformedResponseError
        
        try:
            self.logger.debug(f"Calling LLM API - session: {session.session_id}, nodes: {len(session.nodes)}")

            # Determine the actual streaming behavior:
            # - streaming=None → defer to config default.
            # - streaming=True without callback → keep True (server streams, client ignores).
            # - streaming=False → explicitly disable streaming.
            actual_streaming = streaming
            if streaming is True and streaming_callback is None:
                # Server still streams even if we do not consume it
                actual_streaming = True
            elif streaming is False:
                # Explicitly disabled
                actual_streaming = False
            # else: streaming is None; pass None to use the configured default

            nodes, usage, raw_response = await self.llm_client.call_api(
                session=session,
                tools=self.tools,
                max_tokens=self.config.llm_config.max_tokens,
                thinking_budget_tokens=self.config.llm_config.thinking_budget_tokens,
                temperature=self.config.llm_config.temperature,
                streaming=actual_streaming,
                streaming_callback=streaming_callback,
                interrupt_event=self.interrupt_event
            )

            # Persist nodes into the session
            if nodes:
                await self._add_nodes_to_session(session, nodes)
                self.logger.debug(f"Added {len(nodes)} nodes to session")

            # Track usage
            self._conversation_usage.append(usage)

            # Record the turn (aligned with relay's record_turn)
            if nodes:
                turn_number = session.get_assistant_count()
                await self.record_turn(session, nodes, usage, turn_number, raw_response)

            return nodes, usage
            
        except MalformedResponseError as e:
            # Empty/malformed response. Check intelligent stop, otherwise add a retry prompt.
            self.logger.warning(f"MalformedResponseError: {str(e)}")
            
            should_stop, stop_reason = should_stop_conversation(
                session,
                consecutive_retries_threshold=self.config.consecutive_retries_threshold,
                total_retries_threshold=self.config.total_retries_threshold
            )
            
            if should_stop:
                raise ConversationStoppedError(
                    f"{stop_reason} (triggered by: {str(e)})"
                ) from e
            
            # Add fallback prompt for empty response
            prompt = self._create_empty_response_prompt()
            await self._add_prompt_to_session(session, prompt, is_retry_prompt=True)
            self.logger.info(f'Added empty response prompt: {str(e)}')
            
            # Return empty nodes so callers continue the loop
            return [], usage if 'usage' in locals() else None
    
    async def _handle_llm_response(self, session: 'ConversationSession',
                                   nodes: List['ConversationNode'],
                                   usage: Optional['TokenUsage'],
                                   mcp_instance: Client,
                                   force_tool_use: bool,
                                   streaming: bool,
                                   streaming_callback: Optional[Callable],
                                   user_input_callback: Optional[Callable[[], Any]] = None) -> None:
        """
        Process the LLM response - nodes are already saved by _call_llm_api.

        Note: this no longer returns should_terminate; external termination is detected by _stop_event.
        """
        # Empty response (prompt already appended)
        if not nodes:
            return

        # Check for tool calls
        has_tool_calls = self.llm_client.message_formatter.check_has_tool_calls(nodes)

        if has_tool_calls:
            # Execute tool calls
            tool_calls = self.llm_client.message_formatter.extract_tool_calls_from_nodes(nodes)
            self.logger.info(f"Response contains {len(tool_calls)} tool calls")
            await self._execute_tool_calls(
                session, nodes, mcp_instance, streaming, streaming_callback
            )
            return

        # No tool calls
        if not force_tool_use:
            # In CLI mode, wait for user input when a callback is available
            if user_input_callback:
                self.logger.debug("CLI mode - waiting for user input")
                try:
                    user_input = await user_input_callback()

                    if user_input is None:
                        # User exited
                        self.logger.info("User requested exit")
                        self._stop_event.set()
                        return

                    # Append input to the session
                    cwd = self._get_session_context()

                    session.add_user_message(
                        content_blocks=[ContentBlock.text_block(user_input)],
                        cwd=cwd
                    )
                    await self._save_session(session, incremental=True)

                    # Continue the loop with the new message
                    return

                except Exception as e:
                    self.logger.error(f"Error getting user input: {e}")
                    self._stop_event.set()
                    return
            else:
                # CLI mode without a callback (should not happen) – accept response
                self.logger.debug("CLI mode - accepting response without tool calls (no callback)")
                self._stop_event.set()
                return

        # Batch mode: check intelligent stop
        should_stop, stop_reason = should_stop_conversation(
            session,
            consecutive_retries_threshold=self.config.consecutive_retries_threshold,
            total_retries_threshold=self.config.total_retries_threshold
        )

        if should_stop:
            self.logger.warning(f"Intelligent stop (no tool calls): {stop_reason}")
            raise ConversationStoppedError(stop_reason)

        # Add supplemental prompt to enforce tool usage
        prompt = self._create_no_tool_call_prompt()
        await self._add_prompt_to_session(session, prompt, is_retry_prompt=True)
        self.logger.info('Added no tool call prompt')
    
    # ========================================================================
    # Tool execution
    # ========================================================================
    
    async def _execute_tool_calls(self, session: 'ConversationSession',
                                  nodes: List['ConversationNode'],
                                  mcp_instance: Client,
                                  streaming: Optional[bool] = None,
                                  streaming_callback: Optional[Callable[[Any, str], None]] = None) -> None:
        """
        Execute tool calls sequentially.

        Note: does not return should_terminate; termination comes from submit_result → terminate().
        """
        if not nodes:
            return

        tool_calls = self.llm_client.message_formatter.extract_tool_calls_from_nodes(nodes)
        if not tool_calls:
            return
        
        # Display tool calls in CLI mode
        if streaming and streaming_callback:
            for tool_call in tool_calls:
                streaming_callback({
                    "name": tool_call.get("name"),
                    "arguments": tool_call.get("arguments", {})
                }, 'tool_call')
        
        # Execute sequentially; some tools depend on previous ones
        results = []
        for tool_call in tool_calls:
            # Allow user interrupts between calls
            if self.interrupt_event and self.interrupt_event.is_set():
                self.logger.info("Tool execution interrupted by user (ESC key)")
                raise ConversationInterruptedError("User interrupted tool execution with ESC key")

            try:
                result = await self._execute_single_tool_call(session, tool_call, mcp_instance, streaming, streaming_callback)
                results.append(result)
            except Exception as e:
                # Propagate system-level exceptions immediately
                # 1. KeyboardInterrupt / EOFError: user requested exit
                if isinstance(e, (KeyboardInterrupt, EOFError)):
                    raise

                # 2. UserDeclinedConfirmation: user declined confirmation, return to input
                from ..ape_agent.cli.ui.confirmation import UserDeclinedConfirmation
                if isinstance(e, UserDeclinedConfirmation):
                    self.logger.info("Tool execution declined by user (selected 'No')")
                    raise ConversationInterruptedError("User declined confirmation")

                # Other exceptions are recorded and execution continues
                results.append(e)

        # Track success/failure counts (termination already handled elsewhere)
        success_count = 0
        failure_count = 0

        for result in results:
            if isinstance(result, Exception):
                failure_count += 1
            else:
                tool_result = result
                if tool_result.get("success", True):
                    success_count += 1
                else:
                    failure_count += 1
    
    async def _execute_single_tool_call(self, session: 'ConversationSession',
                                       tool_call: Dict[str, Any],
                                       mcp_instance: Client,
                                       streaming: bool,
                                       streaming_callback: Optional[Callable]) -> Dict[str, Any]:
        """
        Execute a single tool call.

        Note: this does not return a terminate flag; submit_result handles termination externally.
        """
        cwd = self._get_session_context()

        try:
            # Remove parameters not defined by the tool schema
            tool_name = tool_call.get("name")
            arguments = tool_call.get("arguments", {})
            filtered_arguments = self._filter_tool_arguments(tool_name, arguments)

            tool_response = await mcp_instance.call_tool(
                tool_name,
                filtered_arguments
            )
            
            tool_result = tool_response.data
            if not isinstance(tool_result, dict):
                if isinstance(tool_result, str):
                    tool_result = json.loads(tool_result)
                else:
                    raise NotImplementedError(f"Unsupported tool data type: {type(tool_result)}")

            # Display tool result in CLI mode
            if streaming and streaming_callback:
                streaming_callback({
                    "tool_name": tool_call.get("name"),
                    "tool_use_id": tool_call.get("tool_use_id"),
                    "result": tool_result,
                    "success": True
                }, 'tool_result')

            # Persist result to the session (session file only)
            session.add_tool_result(
                tool_use_id=tool_call.get("tool_use_id"),
                content=tool_result,
                cwd=cwd,
                tool_name=tool_call.get("name")
            )
            await self._save_session(session, incremental=True)

            return tool_result
            
        except Exception as e:
            # Propagate system-level exceptions immediately
            # 1. KeyboardInterrupt / EOFError: user exit
            if isinstance(e, (KeyboardInterrupt, EOFError)):
                raise

            # 2. UserDeclinedConfirmation: user declined confirmation
            from ..ape_agent.cli.ui.confirmation import UserDeclinedConfirmation
            if isinstance(e, UserDeclinedConfirmation):
                raise

            # Format and enrich the error message
            tool_name = tool_call.get('name', '')

            if isinstance(e, ToolError):
                error_message = ' '.join(e.args)

                # Detect system-level exceptions wrapped inside ToolError
                if "User declined the operation" in error_message:
                    from ..ape_agent.cli.ui.confirmation import UserDeclinedConfirmation
                    raise UserDeclinedConfirmation(error_message)
                elif "KeyboardInterrupt" in error_message or "EOFError" in error_message:
                    if "KeyboardInterrupt" in error_message:
                        raise KeyboardInterrupt()
                    else:
                        raise EOFError()

                # Improve messaging for unknown tool errors
                if "unknown tool" in error_message.lower() or not tool_name.strip():
                    tool_names = [tool['function']['name'] for tool in self.tools]
                    error_message = (
                        f"Unknown tool: '{tool_name}'\n\n"
                        f"Tool name is missing or invalid. The 'name' field must be present and match an available tool name.\n\n"
                        f"Available tools: {', '.join(tool_names)}"
                    )
                # Provide hints for validation errors
                elif "validation error" in error_message.lower():
                    error_message = (
                        f"{error_message}\n\n"
                        f"Please review the tool definition and check parameter types carefully. "
                        f"Common issues: passing JSON strings instead of actual lists/dicts, "
                        f"incorrect parameter types, or missing required parameters."
                    )

                self.logger.warning(f"Tool '{tool_name}' failed: {error_message}")
            else:
                error_message = traceback.format_exc()
                self.logger.error(f"Tool '{tool_name}' exception:\n{error_message}")

            error_result = {"error": error_message, "success": False}
            
            # Display error in CLI mode
            if streaming and streaming_callback:
                streaming_callback({
                    "tool_name": tool_call.get("name"),
                    "tool_use_id": tool_call.get("tool_use_id"),
                    "result": error_result,
                    "success": False
                }, 'tool_result')
            
            # Persist the error back into the session
            session.add_tool_result(
                tool_use_id=tool_call.get("tool_use_id"),
                content=error_result,
                cwd=cwd,
                tool_name=tool_call.get("name")
            )
            await self._save_session(session, incremental=True)

            return error_result
    
    # ========================================================================
    # ========================================================================
    # Helper methods
    # ========================================================================
    
    def _create_no_tool_call_prompt(self) -> str:
        """Create a prompt reminding the model to call tools."""
        tool_names = [tool['function']['name'] for tool in self.tools]
        
        message = ("No tool call detected! You must use tools to make progress on this task. "
                  "Leverage all available tools to thoroughly complete the task. "
                  "Analyze, create, modify, verify, and iterate as needed. "
                    "When the task is fully completed, use `submit_result`.")
        
        message += f"\n\nAvailable tools: {', '.join(tool_names)}"
        return message
    
    def _create_empty_response_prompt(self) -> str:
        """Create a prompt for empty responses."""
        tool_names = [tool['function']['name'] for tool in self.tools]
        
        message = ("No response detected! Leverage all available tools to thoroughly complete the task. "
                    "Analyze, create, modify, verify, and iterate as needed. "
                    "When the task is fully completed, use `submit_result`.")
        
        message += f"\n\nAvailable tools: {', '.join(tool_names)}"
        return message
    
    async def _get_available_tools(self, mcp_instance: Client) -> List[Dict[str, Any]]:
        """Fetch the list of available tools."""
        available_tools = await mcp_instance.list_tools()

        tools = []

        for tool in available_tools:
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or '',
                    "parameters": tool.inputSchema
                }
            }
            tools.append(tool_schema)

        self.logger.debug(f"Available tools: {[t['function']['name'] for t in tools]}")
        return tools

    def _filter_tool_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter tool arguments and drop parameters not defined in the schema.

        Args:
            tool_name: Tool name.
            arguments: Raw parameter dictionary.

        Returns:
            Filtered parameter dictionary.
        """
        if not self.tools or not arguments:
            return arguments

        # Locate the matching tool schema
        tool_schema = None
        for tool in self.tools:
            if tool.get("function", {}).get("name") == tool_name:
                tool_schema = tool.get("function", {}).get("parameters", {})
                break

        if not tool_schema:
            self.logger.warning(f"Tool schema not found for '{tool_name}', using original arguments")
            return arguments

        # Collect defined parameter names
        defined_params = set(tool_schema.get("properties", {}).keys())

        # Filter incoming arguments
        filtered_arguments = {}
        removed_params = []

        for key, value in arguments.items():
            if key in defined_params:
                filtered_arguments[key] = value
            else:
                removed_params.append(key)

        # Log removed parameters
        if removed_params:
            self.logger.warning(
                f"Removed undefined parameters from tool '{tool_name}': {removed_params}"
            )

        return filtered_arguments

    # ========================================================================
    # Limit checks handled in run_conversation
    # ========================================================================
    
    def get_current_turns(self) -> int:
        """Return the number of assistant turns so far."""
        if self.conversation_session:
            return self.conversation_session.get_assistant_count()
        return 0
    
    def get_total_usage(self) -> 'TokenUsage':
        """Aggregate cumulative token usage and cost for the orchestration layer.

        Responsibilities:
        - Sum every assistant response's token usage.
        - Return the aggregated TokenUsage so the orchestrator can store it on the attempt.

        Aggregation rules:
        - Sum input/output/reasoning tokens.
        - Sum cache tokens.
        - Sum total_cost/cached_total_cost.

        Resume scenario:
        - Initial run: _conversation_usage = [u1, u2, u3] → total_cost = $0.15.
        - Resume run: restore [u1, u2, u3] + append [u4, u5] → total_cost = $0.23.
        - Returned TokenUsage always contains cumulative values.

        Returns:
            TokenUsage with cumulative statistics.

        Note:
            - The orchestration layer uses total_cost directly (no extra summation).
            - Resume overwrites the attempt cost with the cumulative value.
        """
        from ape.llm_clients.models import TokenUsage
        try:
            total_input = sum(u.input_tokens for u in self._conversation_usage)
            total_output = sum(u.output_tokens for u in self._conversation_usage)
            total_reasoning = sum(u.reasoning_tokens or 0 for u in self._conversation_usage)
            total_cache_creation = sum(u.cache_creation_input_tokens or 0 for u in self._conversation_usage)
            total_cache_read = sum(u.cache_read_input_tokens or 0 for u in self._conversation_usage)
            total_cost = sum(u.total_cost for u in self._conversation_usage)
            cached_total_cost = sum(u.cached_total_cost for u in self._conversation_usage)
            return TokenUsage(
                input_tokens=total_input,
                output_tokens=total_output,
                reasoning_tokens=total_reasoning if total_reasoning > 0 else None,
                cache_creation_input_tokens=total_cache_creation if total_cache_creation > 0 else None,
                cache_read_input_tokens=total_cache_read if total_cache_read > 0 else None,
                total_cost=total_cost,
                cached_total_cost=cached_total_cost
            )
        except Exception as e:
            self.logger.error(f"Error getting total usage: {e}")
            return TokenUsage()
    
    def get_token_usage(self) -> 'TokenUsage':
        """Compatibility method to fetch token usage."""
        return self.get_total_usage()
    
    def request_stop(self) -> None:
        """Request a cooperative termination."""
        self._stop_event.set()
