"""
Scaffold Base Module.

Provides abstract base class for scaffold implementations with
common setup, execution, and cleanup workflows.
"""

import asyncio
import inspect
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING, Optional, Callable, Type
from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path

from ape.llm_clients.models import TokenUsage
from ape.llm_clients.config import MalformedResponseError

if TYPE_CHECKING:
    from ape.tasks.base import BaseTask
    from ape.scaffolds.config import BaseScaffoldConfig


class ScaffoldTerminationReason(str, Enum):
    """Scaffold termination reason enumeration."""
    SUCCESS = "success"
    MAX_TURNS_REACHED = "max_turns_reached"
    COST_EXHAUSTED = "cost_exhausted"
    CONVERSATION_STOPPED = "conversation_stopped"
    EARLY_STOPPED = "early_stopped"
    INTERRUPTED = "interrupted"
    ERROR = "error"


class MaxTurnsReachedError(Exception):
    """Raised when conversation reaches max_turns limit."""
    pass


class ConversationStoppedError(Exception):
    """Raised when conversation is stopped by intelligent stop mechanism."""
    pass


class ConversationInterruptedError(Exception):
    """Raised when conversation is interrupted by user."""
    pass


class ScaffoldTerminationResult(BaseModel):
    """Scaffold termination result."""
    success: bool = Field(..., description="Whether scaffold terminated successfully")
    token_usage: Optional[TokenUsage] = Field(None, description="Token usage statistics")
    current_turns: int = Field(0, description="Current conversation turns")
    termination_reason: Optional[ScaffoldTerminationReason] = Field(None, description="Termination reason")


class BaseScaffold(ABC):
    """Abstract base class for scaffolds.

    Subclasses must:
    - Set config_class class variable
    - Implement _setup_components()
    - Implement _run_batch_mode()
    - Implement _run_cli_mode()
    - Implement _get_token_usage()
    - Implement _get_current_turns()
    - Implement _interrupt_execution()
    - Optionally override _cleanup_components()
    """

    config_class: Type['BaseScaffoldConfig'] = None

    def __init__(self):
        """Initialize base scaffold."""
        self.logger = None
        self.task: Optional['BaseTask'] = None
        self.is_cli_mode: bool = False
        self.cost_limit: Optional[float] = None
        self._termination_reason: Optional[ScaffoldTerminationReason] = None
        self.progress_callback: Optional[Callable[[str], Any]] = None

    async def _emit_progress(self, message: str) -> None:
        """Emit a user-facing setup progress message when configured."""
        if not self.progress_callback:
            return

        result = self.progress_callback(message)
        if inspect.isawaitable(result):
            await result
        
    
    async def solve(
        self,
        task: 'BaseTask',
        termination_callback: Callable,
        orchestrator_id: str,
        attempt_path: Optional[Path],
        cost_limit: Optional[float] = None
    ) -> None:
        """Execute scaffold workflow: setup -> execute -> cleanup.

        Args:
            task: Task instance.
            termination_callback: Termination callback function.
            orchestrator_id: Orchestrator ID ('cli' for CLI mode).
            attempt_path: Attempt workspace path (if orchestrator pre-created one).
            cost_limit: Cost limit (sample_max_cost).
        """
        self.task = task
        self.is_cli_mode = (orchestrator_id == "cli")
        self.cost_limit = cost_limit

        try:
            await self._setup(termination_callback, orchestrator_id, attempt_path)

            if self.is_cli_mode:
                await self._run_cli_mode()
            else:
                await self._run_batch_mode()

        except asyncio.CancelledError:
            if self.logger:
                self.logger.debug("Task execution cancelled (this is normal during cleanup)")
            raise
        except Exception as e:
            from ape.llm_clients.config import CostExhaustedError, ContextLengthExceededError

            if isinstance(e, (MalformedResponseError, ConversationStoppedError, ContextLengthExceededError)):
                self._termination_reason = ScaffoldTerminationReason.CONVERSATION_STOPPED
                if self.logger:
                    self.logger.warning(
                        f"Model capability error, marking as CONVERSATION_STOPPED (will not retry):\n"
                        f"{traceback.format_exc()}"
                    )
            elif isinstance(e, CostExhaustedError):
                self._termination_reason = ScaffoldTerminationReason.COST_EXHAUSTED
                if self.logger:
                    self.logger.warning(
                        f"Cost exhausted, marking as COST_EXHAUSTED (will not retry):\n"
                        f"{traceback.format_exc()}"
                    )
            elif isinstance(e, MaxTurnsReachedError):
                self._termination_reason = ScaffoldTerminationReason.MAX_TURNS_REACHED
                if self.logger:
                    self.logger.warning(
                        f"Max turns reached, marking as MAX_TURNS_REACHED (resumable):\n"
                        f"{traceback.format_exc()}"
                    )
            else:
                self._termination_reason = ScaffoldTerminationReason.ERROR
                if self.logger:
                    self.logger.error(
                        f"System error execution:\n"
                        f"{traceback.format_exc()}"
                    )
    
    async def _setup(
        self,
        termination_callback: Callable,
        orchestrator_id: str,
        attempt_path: Optional[Path]
    ) -> None:
        """Common setup workflow.

        Args:
            termination_callback: Termination callback function.
            orchestrator_id: Orchestrator ID.
            attempt_path: Preset workspace path for attempt.
        """
        try:
            if self.task is not None:
                self.task.progress_callback = self.progress_callback

            # 1. Task setup (creates workspaces and logging)
            await self._emit_progress("Starting session setup...")
            self.logger = await self.task.setup(
                termination_callback,
                orchestrator_id,
                attempt_path
            )

            mode = 'CLI' if self.is_cli_mode else 'batch'
            cost_str = f"${self.cost_limit:.4f}" if self.cost_limit is not None else "N/A"
            self.logger.info(
                f"{self.__class__.__name__} starting {mode} mode - "
                f"task: {self.task.data.task_id}, "
                f"task_type: {self.task.task_type}, "
                f"cost_limit: {cost_str}"
            )

            # 2. Scaffold components setup
            await self._emit_progress("Initializing agent runtime...")
            await self._setup_components()
            await self._emit_progress("Setup complete. Starting session...")
            self.logger.debug(f"{self.__class__.__name__} components setup completed")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to setup {self.__class__.__name__}: {e}")
            raise ComponentSetupError(f"Failed to setup {self.__class__.__name__}: {e}") from e

    @abstractmethod
    async def _setup_components(self) -> None:
        """Set up scaffold-specific components. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def _run_batch_mode(self) -> None:
        """Execute batch mode logic. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def _run_cli_mode(self) -> None:
        """Execute CLI mode logic. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def _get_token_usage(self) -> Optional[Any]:
        """Get token usage statistics. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def _get_current_turns(self) -> int:
        """Get current conversation turns. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def _interrupt_execution(self) -> None:
        """Interrupt internal execution. Must be implemented by subclasses."""
        pass

    async def terminate(self) -> ScaffoldTerminationResult:
        """Terminate scaffold execution.

        Sets termination reason, interrupts execution, collects statistics.
        Subclasses typically do not need to override this method.

        Returns:
            ScaffoldTerminationResult with termination status.
        """
        try:
            if self._termination_reason is None:
                self._termination_reason = ScaffoldTerminationReason.SUCCESS

            if self.logger:
                self.logger.info(f"{self.__class__.__name__} terminate() called - interrupting execution")

            await self._interrupt_execution()

            token_usage = self._get_token_usage()
            current_turns = self._get_current_turns()

            if self.logger:
                token_summary = f"(tokens: {token_usage.total_tokens}, cost: ${token_usage.total_cost:.4f})" if token_usage else "(no token usage)"
                self.logger.info(
                    f"{self.__class__.__name__} termination completed - "
                    f"reason: {self._termination_reason}, turns: {current_turns}, "
                    f"{token_summary}"
                )

            return ScaffoldTerminationResult(
                success=True,
                token_usage=token_usage,
                current_turns=current_turns,
                termination_reason=self._termination_reason
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during termination: {traceback.format_exc()}")

            return ScaffoldTerminationResult(
                success=False,
                token_usage=None,
                termination_reason=self._termination_reason or ScaffoldTerminationReason.ERROR
            )

    async def _cleanup(self) -> None:
        """Common cleanup workflow."""
        try:
            if self.logger:
                self.logger.debug(f"[{self.__class__.__name__}] Starting cleanup")

            # 1. Cleanup scaffold components
            await self._cleanup_components()

            # 2. Clear references
            self.task = None

            if self.logger:
                self.logger.debug(f"[{self.__class__.__name__}] Cleanup completed")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during cleanup: {traceback.format_exc()}")
        finally:
            pass

    async def _cleanup_components(self) -> None:
        """Clean up scaffold-specific components. Override in subclasses."""
        pass

    @classmethod
    def get_required_resources(cls) -> list[tuple[Path, Optional[Path]]]:
        """Get resources required by this scaffold (e.g., binaries).

        Returns:
            List of (host_path, container_path) tuples.
            container_path=None means use default PROJECT_ROOT-based mapping.

        Override in subclasses that need specific resources (e.g., claude-code binary).
        """
        return []

    @classmethod
    def get_environment_config(cls, config: Optional[Any] = None) -> Dict[str, str]:
        """Get environment variables required by this scaffold in container.

        Args:
            config: Scaffold configuration

        Returns:
            Environment variables for scaffold execution.
            Values containing $VAR will be expanded by runtime using container's actual values.

        Override in subclasses that need specific environment variables.
        """
        return {}


class ScaffoldExecutionError(Exception):
    """Scaffold execution error."""
    pass


class ComponentSetupError(ScaffoldExecutionError):
    """Component setup error."""
    pass


class ConversationError(ScaffoldExecutionError):
    """Conversation execution error."""
    pass


class ResourceCleanupError(ScaffoldExecutionError):
    """Resource cleanup error."""
    pass
