"""
Task Runner - Single task executor.

Complete separation of task execution and scaffold state management:
- BaseTaskResult: Pure task execution result without execution state information
- ScaffoldTerminationReason: Scaffold termination reason, handled by orchestrator layer

This module can be executed directly in Docker containers:
    python -m ape.scaffolds.runner <params_json>
"""

import asyncio
import json
import sys
import time
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING, Callable, Awaitable, Tuple
from pathlib import Path

from ape.scaffolds.config import BaseScaffoldConfig
from ape.tasks.base import BaseTaskResult, BaseTask
from ape.utils.logging import create_logger

# Import TokenUsage at runtime to avoid Pydantic forward reference issues
from ape.llm_clients.models import TokenUsage

if TYPE_CHECKING:
    import logging
    from ape.scaffolds.base import BaseScaffold, ScaffoldTerminationResult, ScaffoldTerminationReason


class TaskRunner:
    """Single task executor with pure execution responsibilities."""

    def __init__(self, config: BaseScaffoldConfig, logger: Optional['logging.LoggerAdapter'] = None):
        self.config = config
        if logger is None:
            logger = create_logger()
        self.logger = logger

    def _merge_token_usage(self, scaffold_usage: Optional['TokenUsage'], nested_usage: Optional['TokenUsage']) -> Optional['TokenUsage']:
        """Merge scaffold and nested token usage.

        Args:
            scaffold_usage: Token usage of the scaffold
            nested_usage: Token usage of the nested task
        """
        if not scaffold_usage and not nested_usage:
            return None
        if not scaffold_usage:
            return nested_usage
        if not nested_usage:
            return scaffold_usage

        # Both exist, add all fields
        def add(left: Optional[float], right: Optional[float]) -> float:
            return (left or 0.0) + (right or 0.0)

        return TokenUsage(
            input_tokens=scaffold_usage.input_tokens + nested_usage.input_tokens,
            output_tokens=scaffold_usage.output_tokens + nested_usage.output_tokens,
            total_tokens=add(scaffold_usage.total_tokens, nested_usage.total_tokens),
            reasoning_tokens=(
                add(scaffold_usage.reasoning_tokens, nested_usage.reasoning_tokens)
                if scaffold_usage.reasoning_tokens or nested_usage.reasoning_tokens
                else None
            ),
            cache_creation_input_tokens=(
                add(scaffold_usage.cache_creation_input_tokens, nested_usage.cache_creation_input_tokens)
                if scaffold_usage.cache_creation_input_tokens or nested_usage.cache_creation_input_tokens
                else None
            ),
            cache_read_input_tokens=(
                add(scaffold_usage.cache_read_input_tokens, nested_usage.cache_read_input_tokens)
                if scaffold_usage.cache_read_input_tokens or nested_usage.cache_read_input_tokens
                else None
            ),
            total_cost=add(scaffold_usage.total_cost, nested_usage.total_cost),
            cached_total_cost=add(scaffold_usage.cached_total_cost, nested_usage.cached_total_cost)
        )

    async def run_task(
        self,
        task: BaseTask,
        scaffold_type: str,
        orchestrator_id: Optional[str] = None,
        cost_limit: Optional[float] = None,
        attempt_path: Optional[Path] = None
    ) -> Tuple[BaseTaskResult, Optional['ScaffoldTerminationResult']]:
        """
        Execute a single task - purely execute, without processing business logic

        Args:
            task: BaseTask object to execute.
            scaffold_type: Name of scaffold implementation.
            orchestrator_id: Caller identifier.
            cost_limit: Optional cost ceiling.
            attempt_path: Preset workspace path for attempt.

        Returns:
            tuple[BaseTaskResult, Optional[ScaffoldTerminationResult]]:
                Task execution result and scaffold termination information (contains termination_reason and current_turns)
        """
        task_started_at = datetime.now()

        try:
            result, termination_info = await self._execute_with_timeout(
                task=task,
                scaffold_type=scaffold_type,
                orchestrator_id=orchestrator_id,
                started_at=task_started_at,
                cost_limit=cost_limit,
                attempt_path=attempt_path
            )

            # Record execution result
            result_message = '\033[92mTrue\033[0m' if result.success else '\033[91mFalse\033[0m'
            score_message = f"{result.score:.2f}" if result.score == 1.0 else f'\033[91m{result.score:.2f}\033[0m'
            cost = (result.token_usage.total_cost or 0.0) if result.token_usage else 0.0
            self.logger.info(
                f"Task {task.data.task_id} completed: success={result_message}, "
                f"score={score_message}, execution_time={result.execution_time:.2f}s, cost=${cost:.4f}"
            )
            return result, termination_info

        except Exception:
            self.logger.error(f"Task {task.data.task_id} failed: {traceback.format_exc()}")
            return self._build_result(
                task=task,
                success=False,
                score=0.0,
                error=traceback.format_exc(),
                started_at=task_started_at
            ), None

    async def _execute_with_timeout(
        self,
        task: BaseTask,
        scaffold_type: str,
        orchestrator_id: Optional[str],
        started_at: datetime,
        cost_limit: Optional[float] = None,
        attempt_path: Optional[Path] = None
    ) -> Tuple[BaseTaskResult, Optional['ScaffoldTerminationResult']]:
        """
        Execute task with termination callback support

        Note: Early stop is handled at orchestration layer, not here
        """
        # Delay import to avoid circular import
        from ape.scaffolds.factory import create_scaffold
        from ape.scaffolds.base import ScaffoldTerminationReason, ScaffoldTerminationResult

        scaffold = create_scaffold(scaffold_type)
        scaffold_task = None

        # Create a separate termination event for this task execution
        termination_event: asyncio.Event = asyncio.Event()
        termination_result: Optional[BaseTaskResult] = None

        async def termination_callback(result: BaseTaskResult) -> None:
            nonlocal termination_result
            termination_result = result
            termination_event.set()

        try:
            # Create scaffold execution task
            scaffold_task = asyncio.create_task(
                scaffold.solve(
                    task,
                    termination_callback,
                    orchestrator_id,
                    attempt_path,
                    cost_limit
                )
            )

            while True:
                # Create monitoring task collection
                wait_tasks = {
                    'scaffold': scaffold_task,
                    'termination': asyncio.create_task(termination_event.wait())
                }

                # Wait for any condition to be met (no timeout limit)
                done, pending = await asyncio.wait(
                    wait_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Clean up incomplete monitoring tasks
                for async_task in pending:
                    if async_task != scaffold_task:
                        async_task.cancel()
                        try:
                            await async_task
                        except asyncio.CancelledError:
                            pass

                # Identify completed task type
                completed_task = next(iter(done))

                # Process completed task type
                if completed_task == wait_tasks['termination']:
                    # termination callback triggered - task successfully completed
                    termination_info = await self._cleanup_scaffold(scaffold, scaffold_task)
                    elapsed = (datetime.now() - started_at).total_seconds()
                    self.logger.info(
                        f"Task {task.data.task_id} completed via termination callback "
                        f"(elapsed: {elapsed:.1f}s, success: {termination_result.success if termination_result else 'unknown'})"
                    )

                    if termination_result is not None:
                        # Use termination result, update time information
                        completed_at = datetime.now()
                        execution_time = (completed_at - started_at).total_seconds()

                        termination_result.execution_time = execution_time
                        termination_result.started_at = started_at
                        termination_result.completed_at = completed_at

                        # Merge token usage
                        merged_token_usage = self._merge_token_usage(
                            termination_info.token_usage if termination_info else None,
                            termination_result.nested_token_usage
                        )
                        termination_result.token_usage = merged_token_usage

                        return termination_result, termination_info
                    else:
                        # Exception: event triggered but result not set
                        self.logger.warning(f"Task {task.data.task_id} termination event fired but no result available")
                        return self._build_result(
                            task=task,
                            success=False,
                            score=0.0,
                            error="Termination event fired but no result available",
                            started_at=started_at
                        ), ScaffoldTerminationResult(
                            success=False,
                            termination_reason=ScaffoldTerminationReason.ERROR,
                            current_turns=0
                        )

                elif completed_task == scaffold_task:
                    # Scaffold completed (non-SUCCESS) - simplified processing
                    termination_info = await self._cleanup_scaffold(scaffold, scaffold_task)

                    # Directly return failure result and scaffold termination reason
                    result = self._build_result(
                        task=task,
                        success=False,
                        score=0.0,
                        token_usage=termination_info.token_usage if termination_info else None,
                        started_at=started_at
                    )

                    return result, termination_info

        except asyncio.CancelledError:
            self.logger.info(f"Task {task.data.task_id} was cancelled")
            termination_info = await self._cleanup_scaffold(scaffold, scaffold_task)
            # Keyboard interrupt: return INTERRUPTED reason, so that worker maintains RUNNING state to support resume
            actual_turns = termination_info.current_turns if termination_info else 0
            return self._build_result(
                task=task,
                success=False,
                score=0.0,
                error="Cancelled",
                started_at=started_at
            ), ScaffoldTerminationResult(
                success=False,
                termination_reason=ScaffoldTerminationReason.INTERRUPTED,
                current_turns=actual_turns
            )

        except Exception as e:
            self.logger.error(f"Execution error for task {task.data.task_id}: {e}")
            await self._cleanup_scaffold(scaffold, scaffold_task)
            raise

    def _build_result(
        self,
        task: BaseTask,
        success: bool,
        score: float,
        error: Optional[str] = None,
        token_usage: Optional['TokenUsage'] = None,
        started_at: Optional[datetime] = None
    ) -> BaseTaskResult:
        """Build task result - unified time processing

        Attempts to use task-specific result class, falls back to BaseTaskResult
        if task.create_result() fails (e.g., missing required fields).
        """
        if started_at is None:
            started_at = datetime.now()

        completed_at = datetime.now()
        execution_time = (completed_at - started_at).total_seconds()

        return BaseTaskResult(
                task_id=task.data.task_id,
                task_type=task.task_type,
                global_index=task.data.global_index,
                success=success,
                score=score,
                execution_time=execution_time,
                error=error,
                started_at=started_at,
                completed_at=completed_at,
                token_usage=token_usage
            )

    async def _cleanup_scaffold(self, scaffold: 'BaseScaffold', scaffold_task: Optional[asyncio.Task] = None):
        """
        Clean up scaffold resources - clean up in the correct order

        Cleanup process:
        1. Call terminate() to send interrupt signal
           - For ClaudeCode: call client.interrupt() and set stop_event
           - For ApeAgent: call conversation_manager.request_stop()
        2. Wait for scaffold_task to exit naturally
           - Interrupt signal will stop the message stream blocking
           - async with will automatically disconnect SDK
           - Usually completes within 5 seconds
        3. Call _cleanup() to clean up resources
           - Stop relay and MCP server
           - Clean up references and temporary files

        Note:
        - SDK's disconnect is handled automatically by async with
        - cleanup only handles other resources (relay, MCP, etc.)
        """
        termination_result = None

        # 1. Call terminate to send interrupt signal (will call _interrupt_execution)
        try:
            termination_result = await scaffold.terminate()
            if termination_result.token_usage:
                self.logger.debug(f"Scaffold token usage: {termination_result.token_usage}")
        except Exception as e:
            from ape.scaffolds.base import ScaffoldTerminationResult, ScaffoldTerminationReason
            self.logger.warning(f"Scaffold termination error: {e}")
            termination_result = ScaffoldTerminationResult(
                success=False,
                token_usage=None,
                termination_reason=ScaffoldTerminationReason.ERROR
            )

        # 2. Wait for scaffold_task to exit naturally (should complete quickly after interruption)
        if scaffold_task and not scaffold_task.done():
            try:
                # Wait up to 5 seconds for scaffold to exit naturally
                # Interrupt signal has been sent, SDK message stream should stop blocking, async with will automatically disconnect
                await asyncio.wait_for(scaffold_task, timeout=5.0)
            except asyncio.TimeoutError:
                scaffold_task.cancel()
                try:
                    await asyncio.wait_for(scaffold_task, timeout=2.0)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    pass
            except Exception as e:
                pass

        # 3. Call cleanup to clean up resources (SDK has disconnected, now clean up relay and other resources)
        try:
            await scaffold._cleanup()
        except asyncio.CancelledError:
            self.logger.warning(f"Scaffold cleanup cancelled")
        except Exception as e:
            self.logger.warning(f"Scaffold cleanup error: {e}")

        return termination_result


# ============================================================================
# Container entry point - execute TaskRunner from serialized parameters
# ============================================================================

async def main_from_params(params: Dict[str, Any]) -> Tuple['BaseTaskResult', Optional['ScaffoldTerminationResult']]:
    """
    Execute task from serialized parameters.

    Args:
        params: Serialized parameters containing:
            - task_data: dict
            - task_type: str
            - config: dict
            - scaffold_type: str
            - orchestrator_id: Optional[str]
            - cost_limit: Optional[float]
            - attempt_path: Optional[str]

    Returns:
        Tuple of (BaseTaskResult, Optional[ScaffoldTerminationResult])

    Note:
        - This function returns objects, not serialized dicts
        - Serialization should happen at process boundary (__main__)
        - Local runtime can use objects directly without dump/load overhead
    """
    from pathlib import Path
    from ape.tasks.base import create_task_from_data

    # Rebuild config
    from ape.scaffolds import get_scaffold_class
    scaffold_class = get_scaffold_class(params['scaffold_type'])
    config_class = getattr(scaffold_class, 'config_class', BaseScaffoldConfig)
    config = config_class.model_validate(params['config'])

    # Rebuild task (task_type is extracted from task_data['task_type'])
    task = create_task_from_data(
        params['task_data'],
        config,
        task_config_overrides=config.task_config_overrides
    )

    # Create runner and execute
    logger = create_logger(to_console=False)
    runner = TaskRunner(config, logger)

    attempt_path = params.get('attempt_path')
    if attempt_path:
        attempt_path = Path(attempt_path)

    result, termination = await runner.run_task(
        task=task,
        scaffold_type=params['scaffold_type'],
        orchestrator_id=params.get('orchestrator_id'),
        cost_limit=params.get('cost_limit'),
        attempt_path=attempt_path
    )

    return result, termination


if __name__ == '__main__':
    """Command-line entry point for Docker containers.

    Responsible for:
    1. Parsing JSON parameters from command line
    2. Executing task via main_from_params
    3. Serializing result objects to JSON (process boundary)
    4. Writing JSON to stdout for parent process
    5. Handling errors and ensuring valid JSON output
    """
    if len(sys.argv) != 2:
        print("Usage: python -m ape.scaffolds.runner <params_json>", file=sys.stderr)
        sys.exit(1)

    params_json = sys.argv[1]
    params = None

    try:
        params = json.loads(params_json)

        # Execute task (returns objects)
        result, termination = asyncio.run(main_from_params(params))

        # Serialize at process boundary (only here, not in main_from_params)
        result_data = {
            'task_result': result.model_dump(mode='json'),
            'termination': termination.model_dump(mode='json') if termination else None
        }

        # Write result to stdout (JSON)
        print(json.dumps(result_data))
        sys.exit(0)

    except Exception:
        # If execution fails, output a BaseTaskResult error
        # This ensures sandbox/container runtime can always parse valid JSON
        from ape.scaffolds.base import ScaffoldTerminationResult, ScaffoldTerminationReason

        # Extract task info if params was successfully parsed
        task_data = params.get('task_data', {}) if params else {}
        task_id = task_data.get('task_id', 'unknown')
        task_type = task_data.get('task_type', 'unknown')
        global_index = task_data.get('global_index', 'unknown')

        error_result = BaseTaskResult(
            task_id=task_id,
            task_type=task_type,
            global_index=global_index,
            success=False,
            score=0.0,
            error=traceback.format_exc(),
            execution_time=0.0,
            started_at=datetime.now(),
            completed_at=datetime.now()
        )

        error_termination = ScaffoldTerminationResult(
            success=False,
            termination_reason=ScaffoldTerminationReason.ERROR,
            current_turns=0
        )

        result_data = {
            'task_result': error_result.model_dump(mode='json'),
            'termination': error_termination.model_dump(mode='json')
        }

        print(json.dumps(result_data))
        sys.exit(1)
