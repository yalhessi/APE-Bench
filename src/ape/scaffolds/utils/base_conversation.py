"""
Base Conversation Manager - Abstract base class for conversation management

This module provides the abstract base for all conversation managers,
handling common conversation loop, cost checking, and intelligent stop detection.
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging
    from ape.tasks.base import BaseTask
    from ape.llm_clients.models import TokenUsage
    from .base_relay import BaseRelaySession


class BaseConversationManager(ABC):
    """
    Base Conversation Manager - Abstract conversation control

    Responsibilities (Common):
    1. Manage relay lifecycle
    2. Conversation loop control
    3. Cost limit checking
    4. Turn limit checking
    5. Intelligent stop detection
    6. Retry prompt generation

    Responsibilities (Subclass):
    1. Execute single turn (_execute_turn)
    2. Detect submission (_detect_submission)
    3. Handle interruption (_interrupt_internal)
    """

    def __init__(
        self,
        config,
        task: 'BaseTask',
        cost_limit: Optional[float] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        is_cli_mode: bool = False
    ):
        """
        Initialize base conversation manager

        Args:
            config: Scaffold configuration
            task: Task instance
            cost_limit: Cost limit
            logger: Logger instance
            is_cli_mode: Whether in CLI mode
        """
        self.config = config
        self.task = task
        self.cost_limit = cost_limit
        self.logger = logger or task.logger or create_logger()
        self.is_cli_mode = is_cli_mode

        # Internal relay (created during initialization, but not started)
        self._relay_session: Optional['BaseRelaySession'] = None
        self._relay_logger: Optional['logging.LoggerAdapter'] = None

        # Termination signal
        self._stop_event = asyncio.Event()

        # Relay monitoring (unified for all scaffolds)
        self._relay_error: Optional[Exception] = None
        self._relay_task_monitor: Optional[asyncio.Task] = None

        self.logger.debug(f"[{self.__class__.__name__}] Initialized (use_relay={config.llm_config.model_name is not None}, model_name={config.llm_config.model_name})")

    @abstractmethod
    async def _create_relay_session(
        self,
        port: int,
        conversations_dir: Path,
        cwd: str,
        logger: 'logging.LoggerAdapter',
        conversation_trees_path: Path,
    ) -> 'BaseRelaySession':
        """
        Create relay session - must be implemented by subclass

        Args:
            port: Port number
            conversations_dir: Conversation directory
            cwd: Working directory
            conversation_trees_path: JSONL file storing prefix trees

        Returns:
            BaseRelaySession instance
        """
        pass

    async def _monitor_relay_task(self) -> None:
        """
        Monitor relay task and propagate fatal errors to the conversation loop.

        When relay shuts down due to limits, this monitor detects it and
        propagates the error to stop the conversation immediately.

        Unified implementation for all scaffolds.
        """
        try:
            if self._relay_session and self._relay_session._server_task:
                # Wait for relay server task to complete
                await self._relay_session._server_task

                # Check if shutdown was due to limit error
                if self._relay_session.last_error:
                    self._relay_error = self._relay_session.last_error
                    self.logger.warning(
                        f"[{self.__class__.__name__}] Relay shutdown with error: "
                        f"{self._relay_error}"
                    )
                    # Set stop event to trigger conversation exit
                    self._stop_event.set()
        except asyncio.CancelledError:
            # Normal cancellation during cleanup
            pass
        except Exception as e:
            self.logger.error(f"[{self.__class__.__name__}] Relay monitor error: {e}")

    async def initialize(self) -> None:
        """Initialize and start internal relay (if model_name is not None)"""
        # Skip relay when model_name is None (use official models)
        if self.config.llm_config.model_name is None:
            self.logger.info(f"[{self.__class__.__name__}] Skipping relay initialization (model_name=None, using official models)")
            return

        from datetime import datetime
        from .common import allocate_port

        if not self.task.attempt_path or not self.task.scratch_workspace:
            raise RuntimeError("Task workspace information not initialized before conversation")

        conversations_dir = self.task.attempt_path / self.config.conversations_dir_name
        cwd = str(self.task.scratch_workspace.path)
        conversation_trees_path = (
            self.task.attempt_path / self.config.conversation_trees_file_name
        )
        conversation_trees_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a dedicated logger for relay
        logs_dir = self.task.attempt_path / self.config.logs_dir_name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        relay_log_file = logs_dir / f"relay_{timestamp}.log"
        self._relay_logger = create_logger(log_file=relay_log_file, to_console=False)

        # Create and start relay (subclass implements specific relay type)
        port = allocate_port()
        self._relay_session = await self._create_relay_session(
            port,
            conversations_dir,
            cwd,
            logger=self._relay_logger,
            conversation_trees_path=conversation_trees_path
        )
        self._relay_session.logger = self._relay_logger
        await self._relay_session.start()

        # Start relay monitor (unified for all scaffolds)
        if self._relay_session and self._relay_task_monitor is None:
            self._relay_task_monitor = asyncio.create_task(self._monitor_relay_task())
            self.logger.debug(f"[{self.__class__.__name__}] Relay monitor started")

        self.logger.info(f"[{self.__class__.__name__}] Relay initialized and started")

    async def cleanup(self) -> None:
        """Clean up resources"""
        # Cancel relay monitor
        if self._relay_task_monitor:
            self._relay_task_monitor.cancel()
            try:
                await self._relay_task_monitor
            except asyncio.CancelledError:
                pass
            self._relay_task_monitor = None
            self.logger.debug(f"[{self.__class__.__name__}] Relay monitor stopped")

        # Stop relay
        if self._relay_session:
            try:
                await self._relay_session.stop()
                self.logger.debug(f"[{self.__class__.__name__}] Relay stopped")
            except Exception as e:
                self.logger.warning(f"[{self.__class__.__name__}] Error stopping relay: {e}")
            finally:
                self._relay_session = None

        # Subclass cleanup
        await self._cleanup_internal()

    @abstractmethod
    async def _cleanup_internal(self) -> None:
        """
        Internal cleanup - must be implemented by subclass

        Example: Close SDK clients, terminate processes, etc.
        """
        pass

    @abstractmethod
    async def _execute_turn(self, *args, **kwargs) -> bool:
        """
        Execute single conversation turn - must be implemented by subclass

        Returns:
            bool: True if submission detected (task complete), False otherwise

        Raises:
            Exception: Any errors during turn execution
        """
        pass

    @abstractmethod
    def _create_retry_prompt(self) -> str:
        """
        Create retry/supplement prompt - must be implemented by subclass

        Returns:
            str: Retry prompt
        """
        pass

    async def run_conversation(self, *args, **kwargs) -> bool:
        """
        Main conversation loop - common implementation

        Flow (updated to work with relay-based limit enforcement):
        1. Check relay error (highest priority - relay shutdown)
        2. Check termination signal (submit_result)
        3. Execute single turn
        4. Check for submission
        5. Intelligent stop detection
        6. Send retry prompt if needed

        Note: Limit checks (turns/cost) are now done by relay, not here.
        When relay detects limit exceeded, it shuts down and monitor detects it.

        Returns:
            True: submit_result triggers termination
            False: limit reached or exception
        """
        # Intelligent stop counters
        retries = 0
        max_consecutive = self.config.consecutive_retries_threshold
        max_total = getattr(self.config, "total_retries_threshold", None)

        self.logger.info(
            f"[{self.__class__.__name__}] Starting conversation loop: "
            f"max_consecutive_retries={max_consecutive}, "
            f"max_total_retries={max_total}"
        )

        while True:
            # Check relay error FIRST (highest priority - relay shutdown due to limits)
            # When relay shuts down, monitor task sets _relay_error
            if self._relay_error:
                self.logger.warning(
                    f"[{self.__class__.__name__}] Relay shutdown detected: {self._relay_error}"
                )
                raise self._relay_error

            # Check external termination signal (submit_result)
            if self._stop_event.is_set():
                # If there's a relay error, it takes precedence
                if self._relay_error:
                    raise self._relay_error

                self.logger.info(
                    f"[{self.__class__.__name__}] Conversation terminated by external signal (submit_result)"
                )
                return True

            # Execute single turn (subclass implements specific execution)
            submission_detected = await self._execute_turn(*args, **kwargs)

            if submission_detected:
                self.logger.info(f"[{self.__class__.__name__}] Submission detected, conversation complete")
                return True

            # Intelligent stop detection
            retries += 1
            if max_total is not None and retries >= max_total:
                from ape.scaffolds.base import ConversationStoppedError
                self.logger.warning(
                    f"[{self.__class__.__name__}] Total retry limit reached ({retries}/{max_total})"
                )
                raise ConversationStoppedError(
                    f"Total retry limit reached ({retries}/{max_total}), "
                    f"no submission detected - stopping conversation"
                )

            if max_consecutive is not None and retries >= max_consecutive:
                from ape.scaffolds.base import ConversationStoppedError
                self.logger.warning(
                    f"[{self.__class__.__name__}] Consecutive retry limit reached ({retries}/{max_consecutive})"
                )
                raise ConversationStoppedError(
                    f"Consecutive retry limit reached ({retries}/{max_consecutive}), "
                    f"no submission detected - stopping conversation"
                )

            # Send retry prompt (subclass implements specific sending)
            retry_prompt = self._create_retry_prompt()
            self.logger.info(
                f"[{self.__class__.__name__}] No submission detected, "
                f"sending retry prompt ({retries}/"
                f"{max_consecutive if max_consecutive is not None else '∞'})"
            )
            await self._send_retry_prompt(retry_prompt)

    @abstractmethod
    async def _send_retry_prompt(self, prompt: str) -> None:
        """
        Send retry prompt - must be implemented by subclass

        Args:
            prompt: Retry prompt to send
        """
        pass

    def get_token_usage(self) -> 'TokenUsage':
        """Get usage (delegate to relay)"""
        from ape.llm_clients.models import TokenUsage

        if self._relay_session:
            return self._relay_session.get_token_usage()
        return TokenUsage()

    def get_current_turns(self) -> int:
        """Get turns (delegate to relay)"""
        if self._relay_session:
            return self._relay_session.get_current_turns()
        return 0

    async def request_stop(self) -> None:
        """
        Request termination - common implementation

        1. Call subclass interrupt
        2. Set stop event
        """
        # 1. Interrupt internal execution
        await self._interrupt_internal()

        # 2. Set stop event
        self._stop_event.set()
        self.logger.info(f"[{self.__class__.__name__}] Stop event set")

    @abstractmethod
    async def _interrupt_internal(self) -> None:
        """
        Interrupt internal execution - must be implemented by subclass

        Example: Interrupt SDK, terminate process, etc.
        """
        pass
