"""Local Runtime - Direct in-process execution without sandboxing.

This runtime executes tasks directly in the same process without any isolation.
Use only for testing and debugging.
"""

from pathlib import Path
from typing import Optional, Tuple, TYPE_CHECKING

from pydantic import Field

from ape.runtime.base import BaseRuntime, RuntimeConfig

if TYPE_CHECKING:
    from ape.scaffolds.base import ScaffoldTerminationResult
    from ape.scaffolds.config import BaseScaffoldConfig
    from ape.tasks.base import BaseTaskResult


class LocalRuntimeConfig(RuntimeConfig):
    """Configuration for local runtime (no sandboxing)."""

    runtime_type: str = Field(default="local", frozen=True)


class LocalRuntime(BaseRuntime):
    """Local runtime - direct in-process execution without sandboxing."""

    config_class = LocalRuntimeConfig

    async def run_task(
        self,
        task_data: dict,
        config: 'BaseScaffoldConfig',
        scaffold_type: str,
        orchestrator_id: str,
        attempt_path: Path,
        cost_limit: Optional[float] = None,
    ) -> Tuple['BaseTaskResult', Optional['ScaffoldTerminationResult']]:
        """Execute task directly in the same process."""
        from ape.scaffolds.runner import main_from_params
        from ape.utils.logging import create_logger
        from datetime import datetime

        task_type = task_data.get('task_type')
        if not task_type:
            raise ValueError("task_data must contain 'task_type' field")

        task_id = task_data.get('task_id', 'unknown')

        # Setup runtime-specific logger (redirect to file in attempt's logs directory)
        logs_dir = attempt_path / config.logs_dir_name
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        runtime_log_file = logs_dir / f"runtime_{timestamp}.log"

        # Create runtime logger (no console output to avoid pollution)
        original_logger = self.logger
        self.logger = create_logger(log_file=runtime_log_file, to_console=False)

        self.logger.info(f"[LocalRuntime] Executing task_id={task_id} type={task_type} (direct in-process)")

        # Prepare runner parameters
        params = {
            'task_data': task_data,
            'config': config.model_dump(mode='json'),
            'scaffold_type': scaffold_type,
            'orchestrator_id': orchestrator_id,
            'cost_limit': cost_limit,
            'attempt_path': str(attempt_path),
        }

        # Execute directly in the same process
        # main_from_params now returns objects directly, no need for dump/load
        task_result, termination = await main_from_params(params)

        self.logger.info(
            f"[LocalRuntime] Task completed success={task_result.success} score={task_result.score:.3f}"
        )

        # Clean up runtime logger and restore original logger
        try:
            if self.logger:
                # Close all handlers to release file locks
                for handler in self.logger.logger.handlers[:]:
                    try:
                        handler.close()
                        self.logger.logger.removeHandler(handler)
                    except Exception:
                        pass
        finally:
            # Restore original logger
            self.logger = original_logger

        return task_result, termination


# =============================================================================
# Registration
# =============================================================================

from ape.runtime.registry import register_runtime

register_runtime('local', LocalRuntime)
