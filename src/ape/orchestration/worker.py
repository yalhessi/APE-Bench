"""Worker process that executes samples, handles retries, and aggregates tasks."""

import asyncio
import contextvars
import inspect
import multiprocessing as mp
import random
import threading
import traceback
from datetime import datetime
from pathlib import Path
from queue import Empty
from typing import Any, Dict, Optional, Union, Tuple

from ape.scaffolds.base import ScaffoldTerminationReason, ScaffoldTerminationResult
from ape.scaffolds.config import BaseScaffoldConfig
from ape.tasks.base import BaseTaskResult, get_task_class
from ape.utils.logging import create_logger

from .config import EarlyStopMode
from .models import Attempt, ExecutionStatus, OrchestratorProgress, Sample, make_sample_id
from .persistence import ProgressManager, TaskStorage, append_to_jsonl, print_progress


class SampleWorker:
    """Worker for executing sample tasks, handles complete execution workflow."""

    def __init__(
        self,
        config: BaseScaffoldConfig,
        scaffold_type: str,
        orchestrator_dir: Path,
        worker_id: int,
        early_stop_events: Union[Dict[str, mp.Event], Dict[str, asyncio.Event]],
        aggregation_lock: Union[mp.Lock, threading.Lock],
        execution_mode_name: str,
        orchestrator_start_time: datetime,
        sample_queue: Optional[Union[mp.Queue, asyncio.Queue]] = None,
        logger=None,
        progress_callback=None,
    ):
        self.config = config
        self.scaffold_type = scaffold_type
        self.orchestrator_dir = orchestrator_dir
        self.worker_id = worker_id
        self.early_stop_events = early_stop_events
        self.aggregation_lock = aggregation_lock
        self.execution_mode_name = execution_mode_name
        self.orchestrator_start_time = orchestrator_start_time
        self.sample_queue = sample_queue
        self.logger = logger or create_logger()
        self.progress_callback = progress_callback

        self.progress_manager = ProgressManager(config.execution.get_progress_path(orchestrator_dir))
        self.tasks_dir = config.execution.get_tasks_path(orchestrator_dir)
        self._worker_context = contextvars.ContextVar(
            f"ape_worker_context_{id(self)}",
            default=None,
        )
        self._worker_marker = object()

    async def execute_sample(self, job: Dict[str, Any]) -> Optional[float]:
        """Execute complete workflow for a single sample.

        Returns:
            Optional[float]: Retry delay in seconds if retry needed, None otherwise.
        """

        task_id = job["task_global_index"]
        task_type = job["task_type"]
        task_data = job["task_data"]
        if not isinstance(task_data, dict):
            raise TypeError(f"Expected job['task_data'] to be dict, got {type(task_data).__name__}")
        sample_idx = job["sample_index"]
        storage = TaskStorage(self.tasks_dir / task_id, task_id)

        # === 1. Load or create sample ===
        sample = await storage.load_sample(sample_idx, task_type)
        if not sample:
            now = datetime.now()
            sample = Sample(
                sample_id=make_sample_id(task_id, sample_idx),
                sample_index=sample_idx,
                task_global_index=task_id,
                attempts=[],
                created_at=now,
                updated_at=now,
            )
            await storage.save_sample(sample)

        # === 2. Prepare attempt ===
        current_attempt = sample.current_attempt
        if not current_attempt or current_attempt.status.is_terminal() or current_attempt.status.is_system_error():
            # Need to create new attempt
            attempt = Attempt(
                attempt_id=len(sample.attempts) + 1,
                path=storage.get_attempt_path(sample_idx, len(sample.attempts) + 1),
                status=ExecutionStatus.PENDING,
                created_at=datetime.now(),
                max_turns=self.config.execution.max_turns,
                cost_limit=self.config.execution.sample_max_cost,
            )
            sample.attempts.append(attempt)
        else:
            # Resume existing attempt
            attempt = current_attempt
            if not attempt.path.exists():
                attempt.status = ExecutionStatus.FAILED_ERROR
                attempt.error_message = f"Workspace missing: {attempt.path}"
                attempt.completed_at = datetime.now()
                sample.updated_at = datetime.now()
                await storage.save_sample(sample)
                await self._update_progress(sample)
                return

        attempt.status = ExecutionStatus.RUNNING
        attempt.started_at = attempt.started_at or datetime.now()
        sample.updated_at = datetime.now()
        await storage.save_sample(sample)
        await self._update_progress(sample)

        self.logger.info("Sample %s: starting attempt #%d", sample.sample_id, attempt.attempt_id)

        # === 3. Check early stop before running task ===
        # Early stop is handled entirely at orchestration layer
        early_stop_event = None
        if job["early_stop_mode"] != EarlyStopMode.DISABLED.value:
            early_stop_event = self.early_stop_events.get(task_id)

        # Check if early stop is already triggered before execution
        if early_stop_event and early_stop_event.is_set():
            self.logger.info("Sample %s: early stop already triggered, skipping execution", sample.sample_id)

            # Create early stopped result (never actually executed)
            result = BaseTaskResult(
                task_id=task_data.get('task_id', 'unknown'),
                global_index=task_data.get('global_index', 'unknown'),
                task_type=task_type,
                success=False,
                score=0.0,
                error="Early stopped before execution (another sample already succeeded)"
            )
            termination = ScaffoldTerminationResult(
                success=False,
                termination_reason=ScaffoldTerminationReason.EARLY_STOPPED,
                current_turns=0
            )
        else:
            # Execute task with early stop monitoring
            # Early stop is handled by concurrent monitoring at orchestration layer
            try:
                # Execute with monitoring - can be cancelled if early stop is triggered
                result, termination = await self._execute_with_early_stop_monitoring(
                    task_id=task_id,
                    task_data=task_data,
                    attempt_path=attempt.path,
                    early_stop_event=early_stop_event
                )

            except asyncio.CancelledError:
                # Task was cancelled due to early stop
                self.logger.info("Sample %s: cancelled due to early stop", sample.sample_id)
                result = BaseTaskResult(
                    task_id=task_data.get('task_id', 'unknown'),
                    global_index=task_data.get('global_index', 'unknown'),
                    task_type=task_type,
                    success=False,
                    score=0.0,
                    error="Cancelled: another sample succeeded (early stop)"
                )
                termination = ScaffoldTerminationResult(
                    success=False,
                    termination_reason=ScaffoldTerminationReason.EARLY_STOPPED,
                    current_turns=0
                )
                # Don't re-raise, continue to save state

            except Exception as exc:
                attempt.status = ExecutionStatus.FAILED_ERROR
                attempt.error_message = f"Exception: {exc}\n{traceback.format_exc()}"
                attempt.completed_at = datetime.now()
                sample.updated_at = datetime.now()
                await storage.save_sample(sample)
                self.logger.error("Sample %s: execution failed: %s", sample.sample_id, traceback.format_exc())
                result = None
                termination = None

        # === 4. Determine final status ===
        if result and result.success:
            attempt.status = ExecutionStatus.SUCCESS
        elif termination:
            # Special handling: INTERRUPTED maintains RUNNING status to support resume
            if termination.termination_reason == ScaffoldTerminationReason.INTERRUPTED:
                attempt.status = ExecutionStatus.RUNNING
            else:
                attempt.status = self._map_status(termination.termination_reason)
        else:
            attempt.status = ExecutionStatus.FAILED_ERROR

        # Set completed_at based on status
        # RUNNING status (interrupted) should not set completed_at as task is not truly complete
        if attempt.status != ExecutionStatus.RUNNING:
            attempt.completed_at = datetime.now()

        attempt.result = result if result and result.success else None
        attempt.error_message = result.error if result else None

        if result and result.token_usage:
            attempt.cost = float(result.token_usage.total_cost or 0.0)
            attempt.cached_cost = float(result.token_usage.cached_total_cost or 0.0)
        else:
            attempt.cost = 0.0
            attempt.cached_cost = 0.0

        if termination:
            attempt.turns = termination.current_turns

        sample.updated_at = datetime.now()
        await storage.save_sample(sample)

        self.logger.info(
            "Sample %s: completed with %s (cost=$%.4f, turns=%s)",
            sample.sample_id,
            attempt.status.value,
            attempt.cost,
            attempt.turns,
        )

        # === 5. Update progress ===
        await self._update_progress(sample)

        # === 5. Early stop ===
        if result and attempt.status == ExecutionStatus.SUCCESS:
            await self._check_early_stop(job, sample)

        # === 6. Aggregation check ===
        await self._try_aggregate(job, storage, task_data, task_type)

        # === 7. Return retry signal ===
        if attempt.status.is_system_error() and sample.is_retryable(self.config.execution.task_max_retries):
            error_count = sample.get_error_count()
            retry_delay = self.config.execution.task_retry_delay
            retry_jitter = self.config.execution.task_retry_jitter
            delay = retry_delay + random.uniform(-retry_jitter, retry_jitter)
            delay = max(0, delay)

            self.logger.info(
                "Sample %s: will retry after %.1fs (retry #%d, error: %s)",
                sample.sample_id,
                delay,
                error_count,
                attempt.error_message[:100] if attempt.error_message else "unknown",
            )
            return delay

        return None

    async def run(self) -> None:
        """Main work loop - fetch and execute tasks until all work completed.

        Design notes:
        - We spawn max_concurrency coroutines, each independently fetches and executes tasks.
        - No semaphore needed: the number of coroutines IS the concurrency limit.
        - Exit condition: queue empty (timeout on get()).
        - Retry handling: The coroutine that needs to retry puts the job back and continues,
          ensuring retried tasks are always processed even if other coroutines exit.
        - Short timeout (0.1s) for quick exit detection while avoiding busy wait.
        - asyncio.to_thread avoids thread pool queuing (each call gets its own thread).
        """
        if self.sample_queue is None:
            raise ValueError("sample_queue is required for worker.run()")

        token = self._worker_context.set(self._worker_marker)
        try:
            max_concurrency = self.config.execution.max_concurrency
            is_async_queue = isinstance(self.sample_queue, asyncio.Queue)

            async def fetch_and_execute():
                """Loop to fetch and execute tasks until queue is empty."""
                while True:
                    try:
                        if is_async_queue:
                            job = await asyncio.wait_for(self.sample_queue.get(), timeout=0.1)
                        else:
                            # Use to_thread to avoid thread pool queuing issues
                            job = await asyncio.to_thread(self.sample_queue.get, timeout=0.1)
                    except (Empty, asyncio.TimeoutError):
                        # Queue empty - exit immediately
                        # If any task needs retry, the coroutine executing it will handle it
                        self.logger.debug("Worker %d: queue empty, exiting", self.worker_id)
                        break

                    if job is None:
                        # Termination signal
                        self.logger.info("Worker %d: received termination signal", self.worker_id)
                        break

                    try:
                        retry_delay = await self.execute_sample(job)

                        # Handle retry: put job back and continue (this coroutine will process it)
                        if retry_delay:
                            await asyncio.sleep(retry_delay)
                            if is_async_queue:
                                await self.sample_queue.put(job)
                            else:
                                await asyncio.to_thread(self.sample_queue.put, job)
                    except Exception:
                        self.logger.error(
                            "Worker %d: failed to execute sample: %s",
                            self.worker_id,
                            traceback.format_exc(),
                        )

            # Launch coroutines for concurrent execution
            await asyncio.gather(*[fetch_and_execute() for _ in range(max_concurrency)])
            self.logger.info("Worker %d: all coroutines completed", self.worker_id)
            await self._cancel_pending_tasks()
        finally:
            self._worker_context.reset(token)

    async def _cancel_pending_tasks(self) -> None:
        pending = []
        current_task = asyncio.current_task()
        for task in asyncio.all_tasks():
            if task is current_task or task.done():
                continue
            get_context = getattr(task, "get_context", None)
            if get_context is None:
                continue
            try:
                task_context = get_context()
            except Exception:
                continue
            if task_context.get(self._worker_context) is not self._worker_marker:
                continue
            pending.append(task)
        if not pending:
            return

        task_summaries = []
        for task in pending[:5]:
            coro = task.get_coro()
            coro_name = getattr(coro, "__qualname__", repr(coro))
            task_summaries.append(f"{task.get_name()}:{coro_name}")
        suffix = "" if len(pending) <= 5 else f" (+{len(pending) - 5} more)"
        self.logger.warning(
            "Worker %d: cancelling %d worker task(s): %s%s",
            self.worker_id,
            len(pending),
            ", ".join(task_summaries),
            suffix,
        )

        for task in pending:
            task.cancel()

        try:
            await asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=5.0)
        except asyncio.TimeoutError:
            self.logger.warning(
                "Worker %d: pending task cancellation timed out",
                self.worker_id,
            )

    def _map_status(self, reason: ScaffoldTerminationReason) -> ExecutionStatus:
        """Map termination reason to execution status."""
        return {
            ScaffoldTerminationReason.MAX_TURNS_REACHED: ExecutionStatus.PAUSED_MAX_TURNS,
            ScaffoldTerminationReason.COST_EXHAUSTED: ExecutionStatus.PAUSED_COST_LIMIT,
            ScaffoldTerminationReason.CONVERSATION_STOPPED: ExecutionStatus.FAILED_MODEL,
            ScaffoldTerminationReason.EARLY_STOPPED: ExecutionStatus.FAILED_EARLY_STOP,
        }.get(reason, ExecutionStatus.FAILED_ERROR)

    async def _update_progress(self, sample: Sample) -> None:
        """Update progress state."""
        def updater(progress: OrchestratorProgress) -> None:
            progress.samples[sample.sample_id] = sample.to_progress(
                self.config.execution.task_max_retries,
                self.config.execution.max_turns,
                self.config.execution.sample_max_cost,
            )
            progress.total_samples = len(progress.samples)

        await self.progress_manager.update(updater)

    async def _execute_with_early_stop_monitoring(
        self,
        task_id: str,
        task_data: dict,
        attempt_path: Path,
        early_stop_event: Optional[Union[asyncio.Event, mp.Event]]
    ) -> Tuple[BaseTaskResult, Optional['ScaffoldTerminationResult']]:
        """Execute runtime task with concurrent early stop monitoring.

        This method runs two concurrent tasks:
        1. runtime.run_task() - actual execution
        2. _monitor_early_stop() - monitors event for cancellation

        If the monitor detects early stop, it cancels the execution task.

        Each task creates its own independent runtime instance (sandbox/container).
        """
        attempt_path.mkdir(parents=True, exist_ok=True)

        # Create independent runtime for this task
        from ape.runtime.factory import create_runtime
        runtime = create_runtime(config=self.config.runtime_config, logger=self.logger)
        
        exec_task = asyncio.create_task(
            runtime.run_task(
                task_data=task_data,
                config=self.config,
                scaffold_type=self.scaffold_type,
                orchestrator_id=self.orchestrator_dir.name,
                attempt_path=attempt_path,
                cost_limit=self.config.execution.sample_max_cost
            )
        )

        # Create monitor task if early stop is enabled
        if early_stop_event:
            monitor_task = asyncio.create_task(
                self._monitor_early_stop(task_id, early_stop_event)
            )
            tasks = [exec_task, monitor_task]
        else:
            monitor_task = None
            tasks = [exec_task]

        try:
            # Wait for any task to complete
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Check which task completed
            if exec_task in done:
                # Execution completed normally
                return await exec_task
            else:
                # Monitor triggered early stop - cancel execution
                self.logger.info(f"Task {task_id}: early stop monitor triggered")
                if not exec_task.done():
                    exec_task.cancel()
                    try:
                        await exec_task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        self.logger.warning(f"Exception during task cancellation: {e}")

                raise asyncio.CancelledError("Early stop triggered by another sample")

        except asyncio.CancelledError:
            # Task was cancelled - ensure execution task is cancelled
            if not exec_task.done():
                exec_task.cancel()
                try:
                    await exec_task
                except:
                    pass
            raise

        except Exception:
            # Unexpected exception - cancel execution task
            if not exec_task.done():
                exec_task.cancel()
                try:
                    await exec_task
                except:
                    pass
            raise


    async def _monitor_early_stop(
        self,
        task_id: str,
        event: Union[asyncio.Event, mp.Event]
    ) -> None:
        """Monitor early stop event and return when triggered.

        This coroutine waits for the early stop event to be set.
        When it returns, the caller should cancel the execution task.
        """
        if isinstance(event, asyncio.Event):
            # Async event - direct await
            await event.wait()
        else:
            # mp.Event - need to poll
            while not event.is_set():
                await asyncio.sleep(0.05)  # Poll every 50ms

        self.logger.debug(f"Task {task_id}: early stop event detected")

    async def _check_early_stop(self, job: Dict[str, Any], sample: Sample) -> None:
        """Check and trigger early stop if conditions met.

        This method operates entirely at the orchestration layer by setting
        an in-memory event (asyncio.Event or mp.Event) that is shared across
        all workers. This event is checked before task execution in execute_sample().

        The runtime and runner layers are completely unaware of early stop.
        """
        if job["early_stop_mode"] == EarlyStopMode.DISABLED.value:
            return

        event = self.early_stop_events.get(job["task_global_index"])
        if not event or event.is_set():
            return

        mode = EarlyStopMode(job["early_stop_mode"])
        task_class = get_task_class(job["task_type"])

        should_stop = False
        if mode == EarlyStopMode.ON_SUCCESS:
            should_stop = True
        elif mode == EarlyStopMode.ON_BEST:
            attempt = sample.current_attempt
            if attempt and attempt.result and task_class.is_best_result(attempt.result):
                should_stop = True

        if should_stop:
            # Set in-memory event (shared across all workers in orchestration layer)
            # This will cause other workers to skip execution when they check this event
            event.set()

            self.logger.info(
                "Task %s: early stop triggered by sample %d (mode=%s)",
                job["task_global_index"],
                sample.sample_index,
                mode.value,
            )

    async def _try_aggregate(
        self,
        job: Dict[str, Any],
        storage: TaskStorage,
        task_data: Dict[str, Any],
        task_type: str,
    ) -> None:
        """Try to aggregate task results if all samples completed.

        Fixed: Minimize critical section - only hold lock for atomic checks and writes.
        """
        # Quick check without lock
        if (storage.task_dir / "task_result.json").exists():
            return

        # Load samples outside of lock
        samples = await storage.load_all_samples(job["task_type"])
        if not samples:
            return

        # Check completion status outside of lock
        for sample in samples.values():
            if sample.status in {ExecutionStatus.PENDING, ExecutionStatus.RUNNING}:
                return
            if sample.can_execute(
                self.config.execution.task_max_retries,
                self.config.execution.max_turns,
                self.config.execution.sample_max_cost,
            ):
                return

        # Now acquire lock for the aggregation
        with self.aggregation_lock:
            # Double-check after acquiring lock
            if (storage.task_dir / "task_result.json").exists():
                return

            # Aggregate results
            task_class = get_task_class(task_type)
            successful = [
                s.current_attempt.result
                for s in samples.values()
                if s.current_attempt and s.current_attempt.result and s.status == ExecutionStatus.SUCCESS
            ]

            if successful:
                task_result = task_class.aggregate_results(successful)
            else:
                # All samples failed
                total_time = sum(
                    (a.completed_at - a.started_at).total_seconds()
                    for s in samples.values()
                    for a in s.attempts
                    if a.started_at and a.completed_at
                )
                result_task_id = task_data["task_id"] if "task_id" in task_data else job["task_global_index"]
                task_result = BaseTaskResult(
                    task_id=result_task_id,
                    task_type=task_type,
                    global_index=job["task_global_index"],
                    success=False,
                    score=0.0,
                    error=f"All samples failed: {[s.status.value for s in samples.values()]}",
                    execution_time=total_time,
                )

        # Save results outside of lock
        await storage.save_task_result(task_result)
        aggregated_path = self.config.execution.get_aggregated_results_path(self.orchestrator_dir)
        await append_to_jsonl(aggregated_path, task_result.model_dump(mode="json"))

        # Update progress outside of lock
        def updater(progress: OrchestratorProgress) -> None:
            if task_result.global_index not in progress.completed_task_indices:
                progress.completed_tasks += 1
                if task_result.success:
                    progress.successful_tasks += 1
                    if task_result.score == 1.0:
                        progress.passed_tasks += 1
                progress.completed_task_indices.append(task_result.global_index)
                if task_result.custom_metrics:
                    progress.task_custom_metrics[task_result.global_index] = task_result.custom_metrics

        await self.progress_manager.update(updater)

        self.logger.info(
            "Task %s: aggregated (success=%s, score=%.2f, samples=%d/%d)",
            job["task_global_index"],
            task_result.success,
            task_result.score,
            len(successful),
            len(samples),
        )

        # Print progress
        progress = await self.progress_manager.read()
        if progress:
            await print_progress(progress, self.execution_mode_name, self.orchestrator_start_time, self.logger)
            if self.progress_callback:
                result = self.progress_callback(progress)
                if inspect.isawaitable(result):
                    await result


# ============================================================================
# Worker process entry point
# ============================================================================


def sample_worker_main(
    sample_queue: mp.Queue,
    config_dict: dict,
    scaffold_type: str,
    orchestrator_dir: str,
    worker_id: int,
    early_stop_events: dict,
    aggregation_lock: mp.Lock,
    execution_mode_name: str,
    logs_dir: Optional[str],
    orchestrator_start_time: str,
) -> None:
    """Worker process entry point.

    Note: Each task creates its own independent runtime (sandbox/container).
    Worker does NOT create a shared runtime.
    """
    from ape.scaffolds import get_scaffold_class

    # Load configuration
    scaffold_class = get_scaffold_class(scaffold_type)
    if not scaffold_class:
        raise ValueError(f"Unknown scaffold: {scaffold_type}")

    config_model = getattr(scaffold_class, "config_class", None) or BaseScaffoldConfig
    config = config_model.model_validate(config_dict)

    # Initialize logger
    if logs_dir:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = Path(logs_dir) / f"worker_{worker_id}_{timestamp}.log"
        logger = create_logger(log_file=log_file, to_console=False)
    else:
        logger = create_logger()
    start_time = datetime.fromisoformat(orchestrator_start_time) if orchestrator_start_time else datetime.now()

    # Create worker (no shared runtime)
    orchestrator_path = Path(orchestrator_dir)
    worker = SampleWorker(
        config=config,
        scaffold_type=scaffold_type,
        orchestrator_dir=orchestrator_path,
        worker_id=worker_id,
        early_stop_events=early_stop_events,
        aggregation_lock=aggregation_lock,
        execution_mode_name=execution_mode_name,
        orchestrator_start_time=start_time,
        sample_queue=sample_queue,
        logger=logger,
    )

    logger.info("Worker %d started", worker_id)

    # Execute tasks
    asyncio.run(worker.run())

    logger.info("Worker %d exiting", worker_id)
