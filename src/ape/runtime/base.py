"""Runtime Core - Base classes and configuration.

This module defines the core abstractions for the runtime layer:
- BaseRuntime: Abstract runtime interface for task execution
- RuntimeConfig: Base configuration for all runtimes
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    import logging
    from ape.tasks.base import BaseTaskResult
    from ape.scaffolds.base import ScaffoldTerminationResult
    from ape.scaffolds.config import BaseScaffoldConfig


class RuntimeConfig(BaseModel):
    """Base runtime configuration.

    Each runtime implementation should define its own config subclass
    with a Literal runtime_type field to identify the runtime type.
    """

    model_config = ConfigDict(extra='forbid')


class BaseRuntime(ABC):
    """Abstract runtime interface.

    Responsibilities:
    1. Decide WHERE tasks execute (sandbox, container, etc.)
    2. Manage execution environment lifecycle
    3. Execute tasks and return results

    Each subclass must define:
    - config_class: Points to its configuration class (e.g., SandboxRuntimeConfig)
    """

    config_class: type = None

    def __init__(self, config: RuntimeConfig, logger: Optional['logging.LoggerAdapter'] = None):
        """Initialize runtime.

        Args:
            config: Runtime configuration instance
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

    @abstractmethod
    async def run_task(
        self,
        task_data: dict,
        config: 'BaseScaffoldConfig',
        scaffold_type: str,
        orchestrator_id: str,
        attempt_path: Path,
        cost_limit: Optional[float] = None,
        ) -> Tuple['BaseTaskResult', Optional['ScaffoldTerminationResult']]:
        """Execute a task.

        This is the main entry point for task execution.

        Args:
            task_data: Serialized task data (must include 'task_type' field)
            config: Scaffold configuration
            scaffold_type: Name of scaffold to use
            orchestrator_id: Orchestrator identifier (must match orchestrator workspace id)
            attempt_path: Attempt workspace path
            cost_limit: Maximum cost limit

        Returns:
            Tuple of (BaseTaskResult, ScaffoldTerminationResult)
        """
        pass
