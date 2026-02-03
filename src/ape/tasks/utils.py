from ape.tasks.base import create_task_from_data, BaseTask
from ape.utils.logging import create_logger
from pathlib import Path
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import json

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
    """Load tasks from a JSONL file.

    Args:
        file_path: Path to JSONL file.
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

    with file_path.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            data = json.loads(line)

            if not isinstance(data, dict):
                raise TypeError(f"Line {line_num}: Expected dict, got {type(data).__name__}")

            # Ensure task_id exists
            if not data.get('task_id'):
                data['task_id'] = f"line_{line_num}"

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
