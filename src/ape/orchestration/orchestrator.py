"""Task orchestrator: prepares sample jobs, runs workers, aggregates results."""

import asyncio
import hashlib
import inspect
import json
import multiprocessing as mp
import random
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import ValidationError

from ape.scaffolds.config import BaseScaffoldConfig
from ape.tasks.base import BaseTaskResult, BaseTask, get_task_class
from ape.utils.logging import create_logger
from ape.llm_clients import TokenUsage

from .config import EarlyStopMode
from .models import ExecutionStatus, OrchestratorProgress, OrchestratorResults
from .persistence import (
    ProgressManager,
    TaskStorage,
    load_jsonl,
    print_progress,
    print_summary,
    save_orchestrator_config,
    check_orchestrator_lock,
)
from .worker import sample_worker_main, SampleWorker


class TaskOrchestrator:
    """Coordinates sample execution for a batch of tasks."""

    def __init__(
        self,
        config: BaseScaffoldConfig,
        orchestrator_id: Optional[str] = None,
        logger=None,
        input_file: Optional[Path] = None,
        progress_callback=None,
    ):
        self.config = config
        self.logger = logger or create_logger()
        self.input_file = input_file
        self.progress_callback = progress_callback

        # Generate or use provided orchestrator_id
        if orchestrator_id:
            self.orchestrator_id = orchestrator_id
        else:
            config_str = json.dumps(config.model_dump(mode="json"), ensure_ascii=False)
            config_hash = hashlib.md5(f"{config.scaffold_type}_{config_str}".encode()).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.orchestrator_id = f"orchestrator_{timestamp}_{config_hash}"

        # Create workspace
        self.workspace_path = config.runs_base_dir / self.orchestrator_id
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        # Determine concurrency mode
        exec_config = config.execution
        if exec_config.num_processes is None:
            self.num_processes = min(mp.cpu_count(), 8)
        else:
            self.num_processes = exec_config.num_processes

        self.samples_per_task = max(exec_config.sample_count or 1, 1)

        # Execution mode description
        if self.num_processes == 0:
            self.execution_mode = f"sample-async(concurrency={exec_config.max_concurrency}, samples={self.samples_per_task})"
        else:
            self.execution_mode = f"sample-mp(procs={self.num_processes}, concurrency={exec_config.max_concurrency}, samples={self.samples_per_task})"

        # Initialize paths
        self.progress_manager = ProgressManager(exec_config.get_progress_path(self.workspace_path))
        self.tasks_dir = exec_config.get_tasks_path(self.workspace_path)
        self.tasks_dir.mkdir(exist_ok=True)
        self.aggregated_results_file = exec_config.get_aggregated_results_path(self.workspace_path)
        self.config_file = exec_config.get_config_path(self.workspace_path)

        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    async def _emit_progress(self, progress: OrchestratorProgress) -> None:
        """Forward progress snapshots to an optional callback."""
        if not self.progress_callback:
            return

        result = self.progress_callback(progress)
        if inspect.isawaitable(result):
            await result

    async def run(self, tasks: List[BaseTask]) -> OrchestratorResults:
        """Execute all tasks"""
        if not tasks:
            raise ValueError("No tasks to execute")

        await check_orchestrator_lock(self.workspace_path, self.logger)

        self.start_time = datetime.now()
        self.logger.info(
            "Starting orchestrator %s | tasks=%d | mode=%s | sample_count=%s | sample_max_cost=%s | early_stop=%s",
            self.orchestrator_id,
            len(tasks),
            self.execution_mode,
            self.config.execution.sample_count,
            self.config.execution.sample_max_cost,
            self.config.execution.early_stop_mode.value,
        )

        # Save configuration
        task_type_stats = {}
        for task in tasks:
            task_type_stats[task.task_type] = task_type_stats.get(task.task_type, 0) + 1
        await save_orchestrator_config(
            self.config_file,
            self.orchestrator_id,
            self.config.scaffold_type,
            task_type_stats,
            self.config,
            self.input_file,
            num_processes=self.num_processes,
        )

        # Prepare sample jobs and progress snapshot
        sample_jobs, progress_snapshot, early_stop_ready = await self._prepare_jobs(tasks)

        await self.progress_manager.replace(progress_snapshot)

        # Execute sample jobs
        if sample_jobs:
            await print_progress(progress_snapshot, self.execution_mode, self.start_time, self.logger)
            await self._emit_progress(progress_snapshot)
            await self._execute_jobs(sample_jobs, tasks, early_stop_ready)
        else:
            self.logger.info("No pending samples to execute")
            await print_progress(progress_snapshot, self.execution_mode, self.start_time, self.logger)
            await self._emit_progress(progress_snapshot)

        # Aggregate final results
        self.end_time = datetime.now()
        results = await self._aggregate_final_results(tasks)
        await print_summary(results, self.tasks_dir, self.logger)
        return results

    async def _prepare_jobs(
        self, tasks: List[BaseTask]
    ) -> tuple[List[Dict[str, Any]], OrchestratorProgress, Set[str]]:
        """Prepare sample jobs and progress snapshot"""
        progress = OrchestratorProgress(
            last_updated=datetime.now(),
            total_tasks=len(tasks),
            total_samples=0,
        )
        sample_jobs = []
        early_stop_ready = set()
        enable_early_stop = self.config.execution.early_stop_mode != EarlyStopMode.DISABLED

        for task in tasks:
            task_id = task.data.global_index
            storage = TaskStorage(self.tasks_dir / task_id, task_id)

            # Load existing samples and task result
            existing_samples = await storage.load_all_samples(task.task_type)
            task_result = await storage.load_task_result()

            # Update progress snapshot
            for sample in existing_samples.values():
                progress.samples[sample.sample_id] = sample.to_progress(
                    self.config.execution.task_max_retries,
                    self.config.execution.max_turns,
                    self.config.execution.sample_max_cost,
                )

            # Skip tasks that were already completed and update progress
            if task_result:
                self.logger.info("Task %s already aggregated, skipping new samples", task_id)
                if task_id not in progress.completed_task_indices:
                    progress.completed_tasks += 1
                    if task_result.get("success"):
                        progress.successful_tasks += 1
                        if task_result.get("score") == 1.0:
                            progress.passed_tasks += 1
                    progress.completed_task_indices.append(task_id)
                    if task_result.get("custom_metrics"):
                        progress.task_custom_metrics[task_id] = task_result["custom_metrics"]

                # Check early stop condition
                if enable_early_stop and existing_samples and self._check_early_stop(existing_samples.values(), task.task_type):
                    early_stop_ready.add(task_id)
                continue

            # Determine whether to stop generating new samples
            stop_new_samples = False
            if enable_early_stop and existing_samples and self._check_early_stop(existing_samples.values(), task.task_type):
                early_stop_ready.add(task_id)
                stop_new_samples = True

            # Create a job for each sample slot
            for sample_idx in range(self.samples_per_task):
                sample = existing_samples.get(sample_idx)

                # Create or load the sample
                if sample is None:
                    if stop_new_samples:
                        continue
                    sample = await storage.ensure_sample_placeholder(sample_idx, task.task_type)
                    existing_samples[sample_idx] = sample

                # Update progress
                progress.samples[sample.sample_id] = sample.to_progress(
                    self.config.execution.task_max_retries,
                    self.config.execution.max_turns,
                    self.config.execution.sample_max_cost,
                )

                # Check if the sample can be executed
                if not sample.can_execute(
                    self.config.execution.task_max_retries,
                    self.config.execution.max_turns,
                    self.config.execution.sample_max_cost,
                ):
                    continue

                # Create job entry
                sample_jobs.append({
                    "task_global_index": task_id,
                    "task_type": task.task_type,
                    "task_data": task.data.model_dump(mode="json"),
                    "sample_index": sample_idx,
                    "early_stop_mode": self.config.execution.early_stop_mode.value,
                })

        progress.total_samples = len(progress.samples)

        # Shuffle jobs
        if sample_jobs:
            shuffle_seed = self.config.execution.shuffle_seed
            if shuffle_seed is None:
                random.shuffle(sample_jobs)
                self.logger.info("Shuffled %d samples randomly", len(sample_jobs))
            else:
                random.Random(shuffle_seed).shuffle(sample_jobs)
                self.logger.info("Shuffled %d samples with seed=%s", len(sample_jobs), shuffle_seed)

        return sample_jobs, progress, early_stop_ready

    def _check_early_stop(self, samples, task_type: str) -> bool:
        """Check if early stop should be triggered based on existing sample results.

        This is used during job preparation to determine if a task already has
        a successful sample and should not generate new samples.

        Note: This only checks existing samples. The actual early stop event
        is set by workers after runtime execution completes successfully.
        """
        mode = self.config.execution.early_stop_mode
        if mode == EarlyStopMode.DISABLED:
            return False

        success_samples = [s for s in samples if s.status == ExecutionStatus.SUCCESS]
        if not success_samples:
            return False

        if mode == EarlyStopMode.ON_SUCCESS:
            return True

        if mode == EarlyStopMode.ON_BEST:
            task_class = get_task_class(task_type)
            for sample in success_samples:
                if sample.current_attempt and sample.current_attempt.result:
                    if task_class.is_best_result(sample.current_attempt.result):
                        return True

        return False

    async def _execute_jobs(
        self,
        sample_jobs: List[Dict[str, Any]],
        tasks: List[BaseTask],
        early_stop_ready: Set[str],
    ) -> None:
        """Execute all sample jobs (either main process or multiprocess)."""
        enable_early_stop = self.config.execution.early_stop_mode != EarlyStopMode.DISABLED

        if self.num_processes == 0:
            # Main-process mode
            await self._execute_in_main_process(sample_jobs, tasks, enable_early_stop, early_stop_ready)
        else:
            # Multiprocess mode
            await self._execute_in_worker_processes(sample_jobs, tasks, enable_early_stop, early_stop_ready)

    async def _execute_in_main_process(
        self,
        sample_jobs: List[Dict[str, Any]],
        tasks: List[BaseTask],
        enable_early_stop: bool,
        early_stop_ready: Set[str],
    ) -> None:
        """Execute in main process using coroutine concurrency.

        Early Stop Architecture:
        - early_stop_events are asyncio.Event objects shared across all workers
        - Workers check event.is_set() BEFORE calling runtime.run_task()
        - Workers call event.set() AFTER successful task completion
        - Runtime and runner layers are completely unaware of early stop
        """
        self.logger.info("Running in main process with %d coroutines", self.config.execution.max_concurrency)

        # Create asyncio Queue
        queue = asyncio.Queue()
        for job in sample_jobs:
            await queue.put(job)

        # Create early stop events (orchestration layer only)
        early_stop_events = {}
        if enable_early_stop:
            for task in tasks:
                event = asyncio.Event()
                if task.data.global_index in early_stop_ready:
                    event.set()
                early_stop_events[task.data.global_index] = event

        # Create worker (using asyncio.Queue)
        # Note: Worker does NOT receive a shared runtime - each task creates its own
        worker = SampleWorker(
            config=self.config,
            scaffold_type=self.config.scaffold_type,
            orchestrator_dir=self.workspace_path,
            worker_id=0,
            early_stop_events=early_stop_events,
            aggregation_lock=threading.Lock(),
            execution_mode_name=self.execution_mode,
            orchestrator_start_time=self.start_time,
            sample_queue=queue,
            logger=self.logger,
            progress_callback=self._emit_progress,
        )

        # Run worker
        await worker.run()
        self.logger.info("All samples completed in main process")

    async def _execute_in_worker_processes(
        self,
        sample_jobs: List[Dict[str, Any]],
        tasks: List[BaseTask],
        enable_early_stop: bool,
        early_stop_ready: Set[str],
    ) -> None:
        """Execute in multiple worker processes.

        Early Stop Architecture:
        - early_stop_events are mp.Event objects shared across all worker processes
        - Workers check event.is_set() BEFORE calling runtime.run_task()
        - Workers call event.set() AFTER successful task completion
        - Runtime and runner layers are completely unaware of early stop
        """
        # Use fork where available to avoid heavy module re-import on spawn
        start_method = "fork" if sys.platform != "win32" else "spawn"
        ctx = mp.get_context(start_method)
        queue = ctx.Queue()

        try:
            # Enqueue all jobs
            for job in sample_jobs:
                queue.put(job)
            self.logger.info("Enqueued %d samples for execution", len(sample_jobs))

            # Create shared primitives
            aggregation_lock = ctx.Lock()

            # Create early stop events (shared across processes)
            early_stop_events = {}
            if enable_early_stop:
                for task in tasks:
                    event = ctx.Event()
                    if task.data.global_index in early_stop_ready:
                        event.set()
                    early_stop_events[task.data.global_index] = event

            # Get logs directory from log file path
            base_logger = getattr(self.logger, "logger", None)
            log_file = getattr(base_logger, "_ape_logger_log_file", None) if base_logger else None
            logs_dir = str(Path(log_file).parent) if log_file else None

            # Start worker processes
            processes = []
            for worker_id in range(self.num_processes):
                proc = ctx.Process(
                    target=sample_worker_main,
                    args=(
                        queue,
                        self.config.model_dump(mode="json"),
                        self.config.scaffold_type,
                        str(self.workspace_path),
                        worker_id,
                        early_stop_events,
                        aggregation_lock,
                        self.execution_mode,
                        logs_dir,
                        self.start_time.isoformat() if self.start_time else None,
                    ),
                )
                proc.start()
                processes.append(proc)
                runtime_type = self.config.runtime_config.runtime_type
                self.logger.info("Started worker %d (PID: %s, runtime: %s)", worker_id, proc.pid, runtime_type)

            # Wait for all processes to complete
            for idx, proc in enumerate(processes):
                proc.join()
                self.logger.info("Worker %d (PID: %s) completed", idx, proc.pid)

            self.logger.info("All workers completed")
        finally:
            queue.close()
            try:
                queue.join_thread()
            except Exception:
                pass

    async def _aggregate_final_results(self, tasks: List[BaseTask]) -> OrchestratorResults:
        """Aggregate final results for all tasks."""
        # Load every task result
        results_data = await load_jsonl(self.aggregated_results_file)
        tasks_by_index = {task.data.global_index: task for task in tasks}

        results_by_index: Dict[str, BaseTaskResult] = {}
        duplicate_records = 0
        for data in results_data:
            task_type = data.get("task_type")
            global_index = data.get("global_index")

            task_cls = get_task_class(task_type)

            task = tasks_by_index.get(global_index)
            if not task:
                self.logger.warning(
                    "Task %s found in aggregated_results.jsonl but not in current tasks list; skipping",
                    global_index,
                )
                continue

            # Deserialize result
            task_result_cls = task_cls.task_result_class or BaseTaskResult
            result_target_cls = task_result_cls if data.get("success") else BaseTaskResult

            try:
                result_obj = result_target_cls.model_validate(data)
            except ValidationError:
                # Try loading from storage if validation fails
                storage = TaskStorage(self.tasks_dir / global_index, global_index)
                result_data = await storage.load_task_result()
                if result_data:
                    result_obj = result_target_cls.model_validate(result_data)
                else:
                    raise

            if global_index in results_by_index:
                duplicate_records += 1
            results_by_index[global_index] = result_obj

        if duplicate_records:
            self.logger.warning(
                "Detected %d duplicate aggregated result records; keeping latest per task",
                duplicate_records,
            )

        task_results: List[BaseTaskResult] = []
        for task in tasks:
            global_index = task.data.global_index
            result = results_by_index.get(global_index)
            if result:
                task_results.append(result)

        self.logger.info(
            "Loaded %d aggregated records (%d unique task results)",
            len(results_data),
            len(results_by_index),
        )

        # Compute statistics
        completed = len(task_results)
        successful = sum(1 for r in task_results if r.success)
        passed = sum(1 for r in task_results if r.success and r.score == 1.0)

        completion_rate = completed / len(tasks) if tasks else 0.0
        success_rate = successful / completed if completed else 0.0
        pass_rate_local = passed / completed if completed else 0.0
        pass_rate_global = passed / len(tasks) if tasks else 0.0

        successful_scores = [r.score for r in task_results if r.success]
        average_score = sum(successful_scores) / len(successful_scores) if successful_scores else 0.0

        wall_clock_time = (self.end_time - self.start_time).total_seconds() if self.end_time else 0.0
        cumulative_execution_time = sum(r.execution_time for r in task_results if r.execution_time)
        average_task_time = cumulative_execution_time / completed if completed else 0.0

        # Aggregate token usage
        valid_usages = [r.token_usage for r in task_results if r.token_usage]
        total_token_usage = None
        if valid_usages:
            total_token_usage = TokenUsage(
                input_tokens=sum(u.input_tokens for u in valid_usages),
                output_tokens=sum(u.output_tokens for u in valid_usages),
                total_tokens=sum((u.total_tokens or 0) for u in valid_usages),
                reasoning_tokens=sum((u.reasoning_tokens or 0) for u in valid_usages) or None,
                cache_creation_input_tokens=sum((u.cache_creation_input_tokens or 0) for u in valid_usages) or None,
                cache_read_input_tokens=sum((u.cache_read_input_tokens or 0) for u in valid_usages) or None,
                total_cost=sum((u.total_cost or 0) for u in valid_usages),
                cached_total_cost=sum((u.cached_total_cost or 0) for u in valid_usages),
            )

        # Pull sample statistics from progress
        progress = await self.progress_manager.read()
        total_cost = progress.get_total_cost() if progress else 0.0
        total_cached_cost = progress.get_total_cached_cost() if progress else 0.0
        total_samples = len(progress.samples) if progress else 0
        status_counts = progress.get_status_counts() if progress else {}
        successful_samples = status_counts.get(ExecutionStatus.SUCCESS.value, 0)

        return OrchestratorResults(
            orchestrator_id=self.orchestrator_id,
            scaffold_type=self.config.scaffold_type,
            task_results=task_results,
            total_tasks=len(tasks),
            completed_tasks=completed,
            successful_tasks=successful,
            passed_tasks=passed,
            completion_rate=completion_rate,
            success_rate=success_rate,
            pass_rate_local=pass_rate_local,
            pass_rate_global=pass_rate_global,
            average_score=average_score,
            wall_clock_time=wall_clock_time,
            cumulative_execution_time=cumulative_execution_time,
            average_task_time=average_task_time,
            started_at=self.start_time,
            completed_at=self.end_time,
            config_snapshot=self.config.model_dump(mode="json"),
            total_token_usage=total_token_usage,
            workspace_path=self.workspace_path,
            total_samples=total_samples,
            successful_samples=successful_samples,
            total_cost=total_cost,
            total_cached_cost=total_cached_cost,
        )


async def run_orchestrator_from_file(
    tasks_file: Path,
    config: BaseScaffoldConfig,
    max_tasks: Optional[int] = None,
    orchestrator_id: Optional[str] = None,
    task_config_overrides: Optional[Dict[str, Any]] = None,
    logger=None,
) -> OrchestratorResults:
    """Load tasks from a file and run the orchestrator."""
    from ape.tasks.utils import load_tasks_from_file

    logger = logger or create_logger()

    orchestrator = TaskOrchestrator(
        config=config,
        orchestrator_id=orchestrator_id,
        logger=logger,
        input_file=tasks_file,
    )

    tasks = load_tasks_from_file(
        tasks_file,
        config=config,
        max_tasks=max_tasks,
        task_config_overrides=task_config_overrides,
        logger=logger,
    )

    return await orchestrator.run(tasks)
