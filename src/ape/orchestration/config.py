"""
Execution Configuration.

Configuration models for task execution.
"""

from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ConfigDict


class EarlyStopMode(str, Enum):
    """Early stop mode for sample generation.

    - DISABLED: Generate all samples (majority voting)
    - ON_SUCCESS: Stop after any successful execution (retry until success)
    - ON_BEST: Stop only when best result (score=1.0) is found (aggressive optimization)
    """
    DISABLED = "disabled"
    ON_SUCCESS = "on_success"
    ON_BEST = "on_best"


class ExecutionConfig(BaseModel):
    """Task execution configuration."""

    model_config = ConfigDict(extra='forbid')
    max_turns: int = 100  # Maximum conversation turns
    sample_count: int = 1  # Number of samples (1 = no multi-sampling)
    early_stop_mode: EarlyStopMode = EarlyStopMode.DISABLED  # Early stop mode
    progress_filename: str = "progress.json"  # Progress snapshot filename
    tasks_dirname: str = "tasks"  # Individual task persistence directory name
    aggregated_results_filename: str = "aggregated_results.jsonl"  # Aggregated results filename
    config_filename: str = "config.json"  # Execution config snapshot filename

    # Sample-level multi-processing configuration
    num_processes: Optional[int] = 0  # Worker process count (None = auto: min(cpu_count, 8), 0 = main process)
    max_concurrency: int = 1  # Async coroutine concurrency per worker process

    # Task ordering optimization configuration
    optimize_task_order: bool = True  # Optimize task order by commit_hash

    # Unified error retry configuration
    task_retry_delay: float = 30.0  # Base retry delay (seconds)
    task_retry_jitter: float = 10.0  # Retry delay jitter range (seconds)
    task_max_retries: int = 3  # Maximum task retry attempts
    worker_idle_timeout: float = 60.0  # Worker idle timeout before exit (seconds)

    # Sample cost control
    sample_max_cost: Optional[float] = None  # Max cost per sample (can resume after increase)

    # Sample queue randomization configuration
    shuffle_seed: Optional[int] = 42  # Random seed (None = random each time)

    def model_post_init(self, __context) -> None:
        """Validate configuration consistency after initialization."""
        if self.sample_count == 1 and self.early_stop_mode != EarlyStopMode.DISABLED:
            raise ValueError(
                f"Early stop mode '{self.early_stop_mode.value}' is meaningless when sample_count=1. "
                f"Early stop is designed to stop generating new samples after success/best result, "
                f"but with sample_count=1, there are no additional samples to stop. "
                f"Please either set sample_count > 1 or set early_stop_mode=EarlyStopMode.DISABLED."
            )

    def get_progress_path(self, workspace: Path) -> Path:
        """Get full path to progress.json."""
        return workspace / self.progress_filename

    def get_tasks_path(self, workspace: Path) -> Path:
        """Get tasks directory path."""
        return workspace / self.tasks_dirname

    def get_aggregated_results_path(self, workspace: Path) -> Path:
        """Get aggregated results file path."""
        return workspace / self.aggregated_results_filename

    def get_config_path(self, workspace: Path) -> Path:
        """Get configuration snapshot file path."""
        return workspace / self.config_filename
