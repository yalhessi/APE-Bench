from pathlib import Path
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from ape.tasks.base import create_task_from_data, BaseTask
from ape.tasks.task_variants import load_task_records_from_path
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging

def load_tasks_from_file(
    file_path: Path,
    config: 'BaseScaffoldConfig',
    max_tasks: Optional[int] = None,
    task_config_overrides: Optional[Dict[str, Any]] = None,
    logger: Optional['logging.LoggerAdapter'] = None
) -> List[BaseTask]:
    """Load tasks from a task file.

    Args:
        file_path: Path to a JSONL task file, JSON task file, or task-variant manifest.
        config: Base scaffold configuration.
        max_tasks: Maximum number of tasks to load.
        task_config_overrides: Task configuration overrides (applied to all tasks).
        logger: Optional logger instance.

    Returns:
        List of Task objects (may contain heterogeneous task types).

    Raises:
        FileNotFoundError: If task file does not exist.
        TypeError: If a line is not a dictionary.
        ValueError: If task_type is missing or empty.
    """
    if logger is None:
        logger = create_logger()

    if not file_path.exists():
        raise FileNotFoundError(f"Task file not found: {file_path}")

    tasks = []
    task_type_counts = {}

    records = load_task_records_from_path(file_path)
    for record_index, data in enumerate(records, 1):
        if not isinstance(data, dict):
            raise TypeError(f"Record {record_index}: Expected dict, got {type(data).__name__}")

        # Ensure task_id exists
        if not data.get('task_id'):
            data['task_id'] = f"record_{record_index}"

        # Create task (validates task_type internally)
        task = create_task_from_data(data, config, task_config_overrides)
        tasks.append(task)

        # Track task types for summary
        task_type = task.task_type
        task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1

        if max_tasks and len(tasks) >= max_tasks:
            break

    type_summary = ', '.join(f"{t}: {c}" for t, c in sorted(task_type_counts.items()))
    logger.info(f"Loaded {len(tasks)} tasks ({type_summary})")

    return tasks
