"""
Persistence and Progress Display.

Unified module containing:
- TaskStorage (file operations)
- ProgressManager (progress management)
- Progress display logic
- Statistics computation
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Callable, Any
from enum import Enum

import aiofiles
from ape.utils.file_ops import file_lock, read_json, write_json
from ape.tasks.base import BaseTaskResult, get_task_class

from .models import (
    Sample, OrchestratorProgress, SampleProgress,
    ExecutionStatus, OrchestratorResults, make_sample_id
)


# ============================================================================
# Task-level Storage
# ============================================================================

class TaskStorage:
    """Task-level storage manager."""

    def __init__(self, task_dir: Path, global_index: str):
        self.task_dir = task_dir
        self.global_index = global_index
        self.samples_dir = task_dir / "samples"

    def get_sample_file(self, sample_index: int) -> Path:
        return self.samples_dir / str(sample_index) / "sample.json"

    async def save_sample(self, sample: Sample):
        """Save Sample."""
        sample_file = self.get_sample_file(sample.sample_index)
        sample_file.parent.mkdir(parents=True, exist_ok=True)
        await write_json(sample_file, sample.model_dump(mode='json'))

    async def ensure_sample_placeholder(self, sample_index: int, task_type: Optional[str] = None) -> Sample:
        """Ensure sample.json exists and return corresponding Sample"""
        sample = await self.load_sample(sample_index, task_type)
        if sample:
            return sample

        now = datetime.now()
        sample = Sample(
            sample_id=make_sample_id(self.global_index, sample_index),
            sample_index=sample_index,
            task_global_index=self.global_index,
            attempts=[],
            created_at=now,
            updated_at=now
        )
        await self.save_sample(sample)
        return sample

    async def load_sample(self, sample_index: int, task_type: Optional[str] = None) -> Optional[Sample]:
        """Load Sample"""
        sample_file = self.get_sample_file(sample_index)
        data = await read_json(sample_file)
        if not data:
            return None
        
        sample = Sample.model_validate(data)
        return self._normalize_sample(sample, task_type)
    
    async def load_all_samples(self, task_type: Optional[str] = None) -> Dict[int, Sample]:
        """Load all samples"""
        samples = {}
        if not self.samples_dir.exists():
            return samples
        
        for sample_dir in self.samples_dir.iterdir():
            if sample_dir.is_dir() and sample_dir.name.isdigit():
                sample_index = int(sample_dir.name)
                sample = await self.load_sample(sample_index, task_type)
                if sample:
                    samples[sample_index] = sample
        return samples
    
    def get_attempt_path(self, sample_index: int, attempt_id: int) -> Path:
        """Get attempt workspace path"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        workspace_name = f"attempt_{attempt_id}_{timestamp}"
        return self.samples_dir / str(sample_index) / "attempts" / workspace_name
    
    async def save_task_result(self, result: BaseTaskResult):
        """Save BaseTaskResult"""
        result_file = self.task_dir / "task_result.json"
        await write_json(result_file, result.model_dump(mode='json'))
    
    async def load_task_result(self) -> Optional[Dict]:
        """Load BaseTaskResult"""
        result_file = self.task_dir / "task_result.json"
        return await read_json(result_file)
    
    @staticmethod
    def _normalize_sample(sample: Sample, task_type: Optional[str]) -> Sample:
        """Ensure attempt.result uses the specific BaseTaskResult type"""
        if not sample.sample_id:
            sample.sample_id = make_sample_id(sample.task_global_index, sample.sample_index)

        if not task_type:
            return sample

        task_class = get_task_class(task_type)

        task_result_cls = getattr(task_class, "task_result_class", BaseTaskResult)

        for attempt in sample.attempts:
            if attempt.result and isinstance(attempt.result, dict):
                # Try task-specific result class first, fall back to BaseTaskResult
                try:
                    attempt.result = task_result_cls.model_validate(attempt.result)
                except Exception:
                    # Fall back to BaseTaskResult if task-specific class fails
                    # This is normal when task failed/was cancelled
                    attempt.result = BaseTaskResult.model_validate(attempt.result)

        return sample


# ============================================================================
# Progress Management
# ============================================================================

class ProgressManager:
    """
    Progress manager - incremental update progress.json
    
    Core improvements:
    - Full sample state maintenance
    - Incremental update (only update changed parts)
    - Remove Manager.dict, use file lock synchronization
    """
    
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.lock_file = Path(str(progress_file) + ".lock")
    
    async def update(self, updater: Callable[[OrchestratorProgress], None]):
        """Atomic update progress (with lock)"""
        async with file_lock(self.lock_file, shared=False):
            progress = await self.read() or OrchestratorProgress(
                last_updated=datetime.now(),
                total_tasks=0,
                total_samples=0
            )
            
            updater(progress)
            progress.last_updated = datetime.now()
            
            await write_json(self.progress_file, progress.model_dump(mode='json'))
    
    async def read(self) -> Optional[OrchestratorProgress]:
        """Read progress (no lock)"""
        data = await read_json(self.progress_file)
        return OrchestratorProgress.model_validate(data) if data else None

    async def replace(self, progress: OrchestratorProgress):
        """Overwrite write entire progress snapshot"""
        async with file_lock(self.lock_file, shared=False):
            progress.last_updated = datetime.now()
            await write_json(self.progress_file, progress.model_dump(mode='json'))


# ============================================================================
# Progress display (keep original format)
# ============================================================================

class AnsiCode(str, Enum):
    """ANSI color codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def colored(text: str, color: str = "", bold: bool = False) -> str:
    """Add color to text"""
    color_map = {
        'red': AnsiCode.RED,
        'green': AnsiCode.GREEN,
        'yellow': AnsiCode.YELLOW,
        'blue': AnsiCode.BLUE,
        'cyan': AnsiCode.CYAN,
    }
    
    prefix = AnsiCode.BOLD.value if bold else ""
    if color and color in color_map:
        prefix += color_map[color].value
    
    if prefix:
        return f"{prefix}{text}{AnsiCode.RESET.value}"
    return text


def get_performance_color(rate: float) -> str:
    """Get color based on performance metric"""
    if rate >= 0.7:
        return "green"
    elif rate >= 0.5:
        return "yellow"
    else:
        return "red"


def format_time_duration(seconds: float) -> str:
    """Format time"""
    if seconds <= 0:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h{minutes}m{secs}s"
    elif minutes > 0:
        return f"{minutes}m{secs}s"
    else:
        return f"{secs}s"


async def print_progress(
    progress: OrchestratorProgress,
    execution_mode: str,
    start_time: datetime,
    logger
):
    """
    Print real-time progress (keep original format)
    
    Improvements: directly read from progress object, no cross-process synchronization
    """
    status_counts = progress.get_status_counts()
    tracked_samples = len(progress.samples)
    pending_tracked = status_counts.get(ExecutionStatus.PENDING.value, 0)
    running_samples = status_counts.get(ExecutionStatus.RUNNING.value, 0)
    success_samples = status_counts.get(ExecutionStatus.SUCCESS.value, 0)
    resumable_samples = progress.get_resumable_count()
    retryable_samples = progress.get_retryable_count()
    failed_samples = progress.get_failed_count()
    
    pending_untracked = max(progress.total_samples - tracked_samples, 0)
    pending_samples = pending_tracked + pending_untracked
    
    samples_total = max(progress.total_samples, tracked_samples)
    samples_processed = max(tracked_samples - pending_tracked, 0)
    samples_success = success_samples
    samples_success_rate = samples_success / samples_processed if samples_processed > 0 else 0.0
    
    # Task statistics
    tasks_completed = progress.completed_tasks
    tasks_success = progress.successful_tasks
    tasks_pass = progress.passed_tasks
    
    tasks_success_rate = tasks_success / tasks_completed if tasks_completed > 0 else 0.0
    tasks_pass_rate_local = tasks_pass / tasks_completed if tasks_completed > 0 else 0.0
    tasks_pass_rate_global = tasks_pass / progress.total_tasks if progress.total_tasks > 0 else 0.0
    
    # Cost
    total_cost = progress.get_total_cost()
    total_cached_cost = progress.get_total_cached_cost()
    
    # Estimate final cost
    remaining_tasks = progress.total_tasks - tasks_completed
    if tasks_completed > 0 and remaining_tasks > 0:
        avg_cost = total_cost / tasks_completed
        avg_cached_cost = total_cached_cost / tasks_completed
        estimated_final_cost = total_cost + avg_cost * remaining_tasks
        estimated_final_cached_cost = total_cached_cost + avg_cached_cost * remaining_tasks
    else:
        estimated_final_cost = total_cost
        estimated_final_cached_cost = total_cached_cost
    
    # Time
    elapsed_seconds = (datetime.now() - start_time).total_seconds()
    elapsed_str = format_time_duration(elapsed_seconds)
    
    if tasks_completed > 0 and remaining_tasks > 0 and elapsed_seconds > 0:
        avg_time_per_task = elapsed_seconds / tasks_completed
        eta_seconds = avg_time_per_task * remaining_tasks
        eta_str = format_time_duration(eta_seconds)
    else:
        eta_str = "N/A"
    
    # Format output (keep original format)
    sample_color = get_performance_color(samples_success_rate)
    success_color = get_performance_color(tasks_success_rate)
    pass_local_color = get_performance_color(tasks_pass_rate_local)
    pass_global_color = get_performance_color(tasks_pass_rate_global)
    
    tasks_success_display = f"{tasks_success}/{tasks_completed}" if tasks_completed > 0 else f"{tasks_success}/-"
    tasks_pass_display = f"{tasks_pass}/{tasks_completed}" if tasks_completed > 0 else f"{tasks_pass}/-"

    progress_str = (
        f"{colored(f'[{execution_mode}]', 'cyan')} "
        f"{colored('[SAMPLES]', 'cyan')} "
        f"{colored(f'{samples_processed}/{samples_total}', bold=True)}, SUCCESS:"
        f"{colored(f'{samples_success} ({samples_success_rate*100:.1f}%)', sample_color)} "
        f"| {colored('[TASKS]', 'cyan')} "
        f"{colored(f'{tasks_completed}/{progress.total_tasks}', bold=True)}, SUCCESS:"
        f"{colored(f'{tasks_success_display} ({tasks_success_rate*100:.1f}%)', success_color)}, PASS:"
        f"{colored(f'{tasks_pass_display} ({tasks_pass_rate_local*100:.1f}%)', pass_local_color)}/"
        f"{colored(f'{tasks_pass}/{progress.total_tasks} ({tasks_pass_rate_global*100:.1f}%)', pass_global_color)}"
    )
    
    progress_str += (
        f" | {colored('[STATUS]', 'cyan')} "
        f"Pending:{colored(str(pending_samples), 'yellow')}, "
        f"Running:{colored(str(running_samples), 'yellow')}, "
        f"Retryable:{colored(str(retryable_samples), 'yellow')}, "
        f"Resumable:{colored(str(resumable_samples), 'yellow')}, "
        f"Failed:{colored(str(failed_samples), 'red')}"
    )

    # New: display custom metrics
    custom_metrics = progress.get_aggregated_custom_metrics()
    if custom_metrics:
        metrics_parts = []
        for key, value in sorted(custom_metrics.items()):
            metrics_parts.append(f"{key.upper()}:{value:.2f}")
        if metrics_parts:
            progress_str += f" | {colored('[METRICS]', 'cyan')} {', '.join(metrics_parts)}"

    progress_str += (
        f" | {colored('[COST]', 'cyan')} "
        f"Cost:{colored(f'${total_cost:.2f}→${estimated_final_cost:.2f}', 'yellow')}, "
        f"Cached:{colored(f'${total_cached_cost:.2f}→${estimated_final_cached_cost:.2f}', 'green')}, "
        f"ELAPSED:{colored(elapsed_str, 'yellow')}, ETA:{colored(eta_str, 'yellow')}"
    )
    
    logger.info(progress_str)


async def print_summary(results: OrchestratorResults, tasks_dir: Path, logger):
    """Print final summary"""
    
    # Load all samples statistics from disk
    total_cost = 0.0
    total_cached_cost = 0.0
    
    for task_dir in tasks_dir.iterdir():
        if not task_dir.is_dir():
            continue
        
        samples_dir = task_dir / "samples"
        if not samples_dir.exists():
            continue
        
        for sample_dir in samples_dir.iterdir():
            sample_file = sample_dir / "sample.json"
            if not sample_file.exists():
                continue
            
            data = await read_json(sample_file)
            for att in data.get("attempts", []):
                total_cost += att.get("cost", 0.0)
                total_cached_cost += att.get("cached_cost", 0.0)
    
    # Remove unused sample_execution_times calculation
    
    # Print summary
    separator = colored('─' * 70, 'cyan')
    
    lines = [
        "",
        colored('=' * 70, 'cyan', bold=True),
        colored('ORCHESTRATOR RESULTS SUMMARY', 'cyan', bold=True),
        colored('=' * 70, 'cyan', bold=True),
        f"{colored('Orchestrator ID:', bold=True)}  {colored(results.orchestrator_id, 'blue')}",
        f"{colored('Scaffold:', bold=True)}      {colored(results.scaffold_type, 'blue')}",
        separator,
        f"{colored('Tasks:', bold=True)}         "
        f"{colored(f'{results.completed_tasks}/{results.total_tasks}', 'green')} "
        f"({colored(f'{results.completion_rate*100:.1f}%', 'green')} completed)",
        f"{colored('Success:', bold=True)}       "
        f"{colored(f'{results.successful_tasks}/{results.completed_tasks}', 'green')} "
        f"({colored(f'{results.success_rate*100:.1f}%', 'green')} of completed)",
        f"{colored('Pass:', bold=True)}          "
        f"{colored(f'{results.passed_tasks}/{results.completed_tasks}', 'green')} "
        f"({colored(f'{results.pass_rate_local*100:.1f}%', 'green')} of completed), "
        f"{colored(f'{results.passed_tasks}/{results.total_tasks}', 'green')} "
        f"({colored(f'{results.pass_rate_global*100:.1f}%', 'green')} of total)",
        f"{colored('Avg Score:', bold=True)}     {colored(f'{results.average_score:.3f}', 'green')}",
        separator,
        f"{colored('Total Cost:', bold=True)}    "
        f"Cost: ${colored(f'{total_cost:.4f}', 'yellow')}, "
        f"Cached: ${colored(f'{total_cached_cost:.4f}', 'green')}",
        separator,
        f"{colored('Wall Time:', bold=True)}     {colored(format_time_duration(results.wall_clock_time), 'yellow')}",
        f"{colored('Workspace:', bold=True)}     {results.workspace_path}",
        colored('=' * 70, 'cyan', bold=True),
    ]
    
    logger.info('\n'.join(lines))


# ============================================================================
# Save configuration
# ============================================================================

async def save_orchestrator_config(
    config_file: Path,
    orchestrator_id: str,
    scaffold_type: str,
    task_type_stats: Dict[str, int],
    config: Any,
    input_file: Optional[Path] = None,
    num_processes: Optional[int] = None
):
    """Save Orchestrator configuration"""
    import os
    import git
    
    config_data = {
        'orchestrator_id': orchestrator_id,
        'scaffold_type': scaffold_type,
        'task_type_stats': task_type_stats,
        'config': config.model_dump(mode='json'),
        'created_at': datetime.now().isoformat(),
        'pid': os.getpid(),
        'num_processes': num_processes or config.execution.num_processes or 1
    }
    
    try:
        repo = git.Repo(search_parent_directories=True)
        config_data['commit'] = repo.head.commit.hexsha
    except Exception:
        pass
    
    if input_file:
        config_data['input_file'] = str(input_file)
    
    await write_json(config_file, config_data)


# ============================================================================
# JSONL file operations
# ============================================================================

async def append_to_jsonl(file_path: Path, data: dict):
    """Append a line to JSONL file"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(file_path, 'a', encoding='utf-8') as f:
        await f.write(json.dumps(data, ensure_ascii=False) + '\n')


async def load_jsonl(file_path: Path) -> List[dict]:
    """Load all lines from JSONL file"""
    if not file_path.exists():
        return []
    
    results = []
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        async for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results

async def check_orchestrator_lock(workspace_path: Path, logger=None) -> Optional[int]:
    """Check if another process is executing this orchestrator"""
    try:
        from ape.toolkits.execute.lean.utils.process_ops import is_process_alive
    except ImportError:
        try:
            import psutil
            def is_process_alive(pid):
                if pid is None or pid <= 0:
                    return False
                try:
                    return psutil.pid_exists(pid)
                except Exception:
                    return False
        except ImportError:
            if logger:
                logger.warning("Cannot import psutil, skipping PID lock check")
            return None
    
    config_files = list(workspace_path.glob("config*.json"))
    if not config_files:
        return None
    
    latest_config = max(config_files, key=lambda p: p.stat().st_mtime)
    
    try:
        async with aiofiles.open(latest_config, 'r') as f:
            content = await f.read()
            config_data = json.loads(content)
        
        existing_pid = config_data.get('pid')
        if existing_pid and is_process_alive(existing_pid):
            import os
            current_pid = os.getpid()
            if existing_pid != current_pid:
                error_msg = (
                    f"Another process (PID={existing_pid}) is executing the same orchestrator_id.\n"
                    f"Workspace: {workspace_path}\n"
                    f"Config file: {latest_config}\n"
                    f"If you confirm that the process has ended, please manually delete the config file and try again."
                )
                if logger:
                    logger.error(error_msg)
                raise RuntimeError(error_msg)
            else:
                if logger:
                    logger.debug(f"Current process PID={current_pid}, continuing")
                return None
    
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        if logger:
            logger.warning(f"Failed to read config file {latest_config}: {e}")
    
    return None
