"""
Codex Scaffold - Main Entry Point.

Usage:
    python -m ape.scaffolds.codex.main <tasks_file> [options] [key=value ...]

Options:
    --config <yaml>              Path to YAML configuration file
    --orchestrator_id <id>       Orchestrator identifier
    --max_tasks <n>              Maximum number of tasks to run
    --task_modules <modules>     Task modules to import (e.g., examples.arithmetic.task)

Configuration examples (use Python literal syntax):
    llm_config.temperature=0.7
    llm_config.streaming=False
    llm_config.max_tokens=8000

Configuration priority: CLI overrides > YAML > Pydantic defaults
"""

import argparse
import asyncio
import importlib
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

from .config import CodexConfig
from ape.utils import load_yaml, parse_cli_args, deep_merge, create_logger
from ape.orchestration.orchestrator import run_orchestrator_from_file

if TYPE_CHECKING:
    import logging


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser with minimal arguments."""
    parser = argparse.ArgumentParser(
        description="Codex Scaffold",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('tasks_file', type=Path, help='Path to tasks JSONL file')
    parser.add_argument('--config', type=Path, default=None, help='Path to YAML configuration file')
    parser.add_argument('--orchestrator_id', type=str, default=None, help='Orchestrator ID')
    parser.add_argument('--max_tasks', type=int, default=None, help='Maximum number of tasks')
    parser.add_argument(
        '--task_modules',
        nargs='+',
        default=None,
        help='Task modules to import (e.g., examples.arithmetic.task my.tasks.foo)'
    )

    return parser


def main(
    tasks_file: Path,
    config_path: Optional[Path] = None,
    orchestrator_id: Optional[str] = None,
    max_tasks: Optional[int] = None,
    task_modules: Optional[list[str]] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
    logger: Optional['logging.LoggerAdapter'] = None
) -> None:
    """Codex Scaffold entry point.

    Args:
        tasks_file: Path to tasks JSONL file.
        config_path: Optional path to YAML configuration file.
        orchestrator_id: Optional orchestrator identifier.
        max_tasks: Optional maximum number of tasks to run.
        task_modules: Optional list of task modules to import.
        cli_overrides: Optional CLI configuration overrides.
        logger: Optional logger instance.
    """
    if logger is None:
        logger = create_logger()

    # Import task modules
    if task_modules:
        for module_path in task_modules:
            try:
                importlib.import_module(module_path)
                logger.info(f"Imported task module: {module_path}")
            except ImportError as e:
                logger.error(f"Failed to import task module '{module_path}': {e}")
                raise

    # Build configuration: YAML + CLI overrides
    config_dict = load_yaml(config_path) if config_path else {}
    if cli_overrides:
        config_dict = deep_merge(config_dict, cli_overrides)

    # Extract task_config overrides
    task_config_overrides = config_dict.pop('task_config', {})

    # Create scaffold configuration
    scaffold_config = CodexConfig.model_validate(config_dict)

    logger.info(f"Starting Codex scaffold | tasks: {tasks_file}")

    asyncio.run(run_orchestrator_from_file(
        tasks_file=tasks_file,
        config=scaffold_config,
        orchestrator_id=orchestrator_id,
        max_tasks=max_tasks,
        task_config_overrides=task_config_overrides,
        logger=logger
    ))


if __name__ == '__main__':
    console_logger = create_logger()
    parser = create_argument_parser()
    args, remaining_args = parser.parse_known_args()

    main(
        tasks_file=args.tasks_file,
        config_path=args.config,
        orchestrator_id=args.orchestrator_id,
        max_tasks=args.max_tasks,
        task_modules=args.task_modules,
        cli_overrides=parse_cli_args(remaining_args),
        logger=console_logger
    )
