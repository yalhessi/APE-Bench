"""
APE Bench Main Entry Point

Aligned with semantic annotation design using --target_repo format.
"""

import argparse
import asyncio
import json
import hashlib
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Tuple
import pandas as pd

from .config import ApeBenchConfig
from .collector import DataCollector
from .task import InstructionGenerationTask, InstructionGenerationTaskResult

from ape.utils.logging import create_logger
from ape.utils import parse_cli_args
from ape.orchestration.orchestrator import TaskOrchestrator, OrchestratorResults
from ape.tasks.models import parse_workspace_info
from ..taxonomy.lean_task_taxonomy import annotate_record_metadata

if TYPE_CHECKING:
    import logging


class ApeBenchPipeline:
    """APE Bench data generation pipeline."""

    def __init__(self, config: ApeBenchConfig, logger: Optional['logging.LoggerAdapter'] = None,
                 orchestrator_id: Optional[str] = None):
        """Initialize pipeline with configuration"""
        self.config = config
        self.orchestrator_id = orchestrator_id
        if logger is None:
            logger = create_logger()
        self.logger = logger

        # Fixed output_file path
        if self.config.output_file:
            self.output_file = self.config.output_file
        else:
            output_dir = self.config.dataset_dir
            datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
            self.output_file = output_dir / f"proof_engineering_tasks_{datetime_str}.jsonl"

        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup scaffold configuration
        from ape.scaffolds.factory import create_scaffold_config_for_type
        from ape.tasks.base import create_task_config_for_type
        from ape.scaffolds.config import BaseScaffoldConfig
        from ape.orchestration.config import ExecutionConfig

        task_config = create_task_config_for_type(
            "instruction_generation",
        )

        # Pass validate_generated_task from ApeBenchConfig to InstructionGenerationConfig
        from .task import InstructionGenerationConfig
        if isinstance(task_config, InstructionGenerationConfig):
            task_config.validate_generated_task = config.validate_generated_task

        execution_config = ExecutionConfig(
            num_processes=config.num_processes,
            task_max_retries=config.max_retries
        )

        base_config = BaseScaffoldConfig(
            scaffold_type=config.scaffold_type,
            task_config=task_config,
            execution=execution_config
        )

        from ape.llm_clients.config import LLMConfig
        self.scaffold_config = create_scaffold_config_for_type(
            scaffold_type=config.scaffold_type,
            base_config=base_config,
            llm_config=LLMConfig(model_name=config.model)
        )

    def _compute_config_hash(self) -> str:
        """Compute deterministic config hash from business config.

        Excludes performance/efficiency-only parameters that don't affect data results.
        """
        exclude_fields = {
            # Performance parameters (don't affect data results)
            'num_processes',
            'max_retries',
            'max_cpu_limit',
            'lean_verify_num_processes',  # Only affects verification speed

            # Configuration objects and paths
            'lean_verify_config',
            'workspace_config',
            'dataset_dir',
            'output_file',
        }
        config_dict = self.config.model_dump(mode='json', exclude=exclude_fields)
        payload = json.dumps(config_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(payload.encode('utf-8')).hexdigest()[:16]

    def _compute_orchestrator_id(self) -> str:
        """Compute orchestrator ID from config hash."""
        config_hash = self._compute_config_hash()
        return f"ape_bench_{config_hash}"

    async def run(self) -> str:
        """Run the complete data generation pipeline with resume support."""
        self.logger.info("Starting APE Bench pipeline with resume support")
        self.logger.info(f"Output file: {self.output_file}")
        start_time = time.time()

        try:
            orchestrator_id = self.orchestrator_id or self._compute_orchestrator_id()
            self.logger.info(f"Using orchestrator ID: {orchestrator_id}")

            config_hash = self._compute_config_hash()
            data_collector = DataCollector(self.config, config_hash, self.logger)

            # Phase 1: Data Collection
            self.logger.info("=== Phase 1: Data Collection ===")
            data_df = await data_collector.collect_and_process_data()

            if data_df.empty:
                raise ValueError("No data collected")

            self.logger.info(f"Collected {len(data_df)} records")

            # Phase 2: Task Generation with Resume
            self.logger.info("=== Phase 2: Task Generation with Resume ===")
            await self._generate_proof_engineering_tasks(data_df, orchestrator_id)

            total_time = time.time() - start_time
            self.logger.info(f"Pipeline completed in {total_time:.2f} seconds")
            self.logger.info(f"Output: {self.output_file}")

            return str(self.output_file)

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise

    async def _generate_proof_engineering_tasks(self, data_df: pd.DataFrame, orchestrator_id: str) -> None:
        """Generate proof engineering tasks using orchestrator."""
        total_records = len(data_df)
        self.logger.info(f"Creating tasks for {total_records} records")

        tasks = []
        for _, row in data_df.iterrows():
            def _clean_value(value: Any) -> Any:
                return None if pd.isna(value) else value

            commit_hash = _clean_value(row.get("commit_hash"))
            repo_url = _clean_value(row.get("repo_url"))
            target_workspace = {
                "name": "target",
                "default_target": _clean_value(row.get("default_target")),
                "toolchain": _clean_value(row.get("toolchain")),
                "read_only_path_patterns": ["**/*"],
            }
            if commit_hash is not None or repo_url is not None:
                target_workspace["source"] = {
                    "kind": "git",
                    "commit_hash": commit_hash,
                    "repo_url": repo_url,
                }

            session_name = _clean_value(row.get("session_name"))
            if session_name is not None:
                target_workspace["session_name"] = session_name

            working_directory = _clean_value(row.get("working_directory"))
            if working_directory is not None:
                target_workspace["working_directory"] = working_directory

            task_data = {
                "target_workspace": target_workspace,
                "file_path_before": _clean_value(row.get("file_path_before")),
                "file_path_after": _clean_value(row.get("file_path_after")),
                "content_before": _clean_value(row.get("content_before")),
                "content_after": _clean_value(row.get("content_after")),
                "gold_diff": _clean_value(row.get("gold_diff")),
                "parent_commit_hash": _clean_value(row.get("parent_commit_hash")),
                "author": _clean_value(row.get("author")),
                "message": _clean_value(row.get("message")),
                "date": _clean_value(row.get("date")),
                "language": _clean_value(row.get("language")),
                "diff_lines": _clean_value(row.get("diff_lines")) or 0,
                "change_type": _clean_value(row.get("change_type")) or "modified",
            }
            task = InstructionGenerationTask.from_data(task_data, self.scaffold_config)
            tasks.append(task)

        if not tasks:
            self.logger.warning("No tasks created")
            return

        self.logger.info(f"Running {len(tasks)} tasks with orchestrator ID: {orchestrator_id}")

        orchestrator = TaskOrchestrator(
            config=self.scaffold_config,
            orchestrator_id=orchestrator_id,
            logger=self.logger
        )

        results = await orchestrator.run(tasks)

        await self._save_all_results(results)

        total_accepted = sum(1 for r in results.task_results if
                             r.success and isinstance(r, InstructionGenerationTaskResult) and
                             r.exercise_data and not r.exercise_data.get('rejected', False))
        total_rejected = sum(1 for r in results.task_results if
                             r.success and isinstance(r, InstructionGenerationTaskResult) and
                             r.exercise_data and r.exercise_data.get('rejected', False))
        total_failed = sum(1 for r in results.task_results if not r.success)

        self.logger.info(
            f"\nTask generation completed:\n"
            f"  - Total orchestrator results: {len(results.task_results)}\n"
            f"  - Content accepted: {total_accepted}\n"
            f"  - Content rejected (quality): {total_rejected}\n"
            f"  - Failed: {total_failed}"
        )

    async def _save_all_results(self, results: OrchestratorResults) -> None:
        """Save ALL successful results to output file(s) with optional train/test split."""
        records_to_save = []

        for result in results.task_results:
            if result.success and isinstance(result, InstructionGenerationTaskResult) and result.exercise_data:
                data = result.exercise_data

                # Check if this is a rejected task
                if data.get('rejected', False):
                    # Skip rejected tasks
                    continue

                task_description = data.get('task_description')
                if not task_description:
                    self.logger.warning(
                        "Missing task_description in exercise data; skipping record to avoid reconstruction."
                    )
                    continue

                target_workspace = data.get('target_workspace') or {}
                # Generate task_id from commit_hash and file_path
                commit_hash = parse_workspace_info(target_workspace).commit_hash or 'unknown'
                file_path = data.get('file_path', 'unknown')
                task_id = f"pe_{commit_hash[:8]}_{Path(file_path).stem if file_path != 'unknown' else 'unknown'}"

                # Build metadata dict
                metadata = {
                    'task_category': data.get('task_category'),
                    'formalization_aspect': data.get('formalization_aspect'),
                    'difficulty': data.get('difficulty'),
                    'task_nature': data.get('task_nature'),
                    'total_diff_lines': data.get('total_diff_lines'),
                    'commit_message': data.get('commit_message'),
                    'commit_author': data.get('commit_author'),
                    'commit_date': data.get('commit_date'),
                    'language': data.get('language')
                }

                # For PE tasks, block the target file (relative path, will be expanded during task setup)
                filename = str(data.get('file_path', ''))
                blocked_patterns = [filename] if filename else []

                record = {
                    'task_id': task_id,
                    'task_type': 'lean_proof_engineering',
                    'original_code': data.get('original_code'),
                    'task_description': task_description,
                    'reference_implementation': data.get('modified_code'),
                    'gold_diff': data.get('gold_diff'),
                    'filename': filename,
                    'target_workspace': {
                        **target_workspace,
                        'read_only_path_patterns': (
                            target_workspace.get('read_only_path_patterns') or ['**/*']
                        ),
                        'blocked_path_patterns': blocked_patterns
                    },
                    'metadata': metadata
                }
                annotate_record_metadata(record)
                records_to_save.append(record)

        if not records_to_save:
            self.logger.warning("No records to save")
            return

        # Perform train/test split if enabled
        if self.config.enable_split and self.config.test_size is not None:
            from .split import split_dataset

            self.logger.info(f"Splitting dataset: test_size={self.config.test_size}, strategy={self.config.split_strategy}")
            test_records, train_records = split_dataset(
                records_to_save,
                test_size=self.config.test_size,
                strategy=self.config.split_strategy
            )

            # Add split metadata
            for record in test_records:
                if record['metadata'] is None:
                    record['metadata'] = {}
                record['metadata']['split'] = 'test'

            for record in train_records:
                if record['metadata'] is None:
                    record['metadata'] = {}
                record['metadata']['split'] = 'train'

            # Save split files
            base_path = self.output_file.parent / self.output_file.stem
            test_file = base_path.parent / f"{base_path.name}_test.jsonl"
            train_file = base_path.parent / f"{base_path.name}_train.jsonl"
            all_file = base_path.parent / f"{base_path.name}_all.jsonl"

            with open(test_file, 'w', encoding='utf-8') as f:
                for record in test_records:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')

            with open(train_file, 'w', encoding='utf-8') as f:
                for record in train_records:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')

            with open(all_file, 'w', encoding='utf-8') as f:
                for record in test_records + train_records:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')

            self.logger.info(f"Saved {len(test_records)} test records to {test_file}")
            self.logger.info(f"Saved {len(train_records)} train records to {train_file}")
            self.logger.info(f"Saved {len(test_records) + len(train_records)} total records to {all_file}")
        else:
            # Save all records to single file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                for record in records_to_save:
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')

            self.logger.info(f"Saved {len(records_to_save)} records to {self.output_file}")


async def main(
        target_repo: str = None,
        dataset_dir: Path = None,
        output_file: Path = None,
        min_diff_lines: int = None,
        max_diff_lines: int = None,
        num_processes: int = None,
        latest_num_data: int = None,
        max_commits_scan: int = None,
        scaffold_type: str = None,
        earliest_date: str = None,
        latest_date: str = None,
        orchestrator_id: str = None,
        enable_split: bool = None,
        test_size: int = None,
        split_strategy: str = None,
        config_overrides: Dict[str, Any] = None,
        logger: Optional['logging.LoggerAdapter'] = None
) -> int:
    """Main entry point."""
    if logger is None:
        logger = create_logger()

    # Parse target_repo
    if target_repo:
        repo_url = target_repo
    else:
        repo_url = None

    # Prepare configuration
    config_dict = config_overrides.copy() if config_overrides else {}

    # Map parameters
    param_mapping = {
        'repo_url': repo_url,
        'dataset_dir': dataset_dir,
        'output_file': output_file,
        'min_diff_lines': min_diff_lines,
        'max_diff_lines': max_diff_lines,
        'latest_num_data': latest_num_data,
        'max_commits_scan': max_commits_scan,
        'num_processes': num_processes,
        'scaffold_type': scaffold_type,
        'earliest_date': earliest_date,
        'latest_date': latest_date,
        'enable_split': enable_split,
        'test_size': test_size,
        'split_strategy': split_strategy
    }

    for key, value in param_mapping.items():
        if value is not None:
            config_dict[key] = value
    config_dict.pop('default_target', None)

    # Create configuration
    config = ApeBenchConfig.model_validate(config_dict)

    logger.info("Starting APE Bench with resume support")

    # Run pipeline
    pipeline = ApeBenchPipeline(config, logger, orchestrator_id)
    await pipeline.run()

    return 0


def run_single_task(task_params: Dict[str, Any]) -> Tuple[int, str]:
    """Run a single task in a separate process."""
    import asyncio

    logger = create_logger()
    task_id = task_params.get('task_id', 'unknown')

    try:
        logger.info(f"Starting task {task_id}")

        result = asyncio.run(main(
            target_repo=task_params.get('target_repo'),
            dataset_dir=Path(task_params['dataset_dir']) if task_params.get('dataset_dir') else None,
            output_file=Path(task_params['output_file']) if task_params.get('output_file') else None,
            min_diff_lines=task_params.get('min_diff_lines'),
            max_diff_lines=task_params.get('max_diff_lines'),
            num_processes=task_params.get('num_processes'),
            latest_num_data=task_params.get('latest_num_data'),
            max_commits_scan=task_params.get('max_commits_scan'),
            scaffold_type=task_params.get('scaffold_type'),
            earliest_date=task_params.get('earliest_date'),
            latest_date=task_params.get('latest_date'),
            orchestrator_id=task_params.get('orchestrator_id'),
            enable_split=task_params.get('enable_split'),
            test_size=task_params.get('test_size'),
            split_strategy=task_params.get('split_strategy'),
            config_overrides=task_params.get('config_overrides', {}),
            logger=logger
        ))

        logger.info(f"Task {task_id} completed successfully")
        return result, f"Task {task_id} completed"

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        return 1, f"Task {task_id} failed: {e}"


def run_batch(batch_file: Path, num_workers: int = 4) -> int:
    """Run multiple tasks from a JSONL batch file in parallel.

    Args:
        batch_file: Path to JSONL file where each line contains task parameters
        num_workers: Number of parallel worker processes

    Returns:
        Exit code (0 for success)
    """
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from tqdm import tqdm

    logger = create_logger()
    logger.info(f"Loading batch file: {batch_file}")

    # Load tasks from JSONL
    tasks = []
    with open(batch_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.strip():
                task_params = json.loads(line)
                # Add task_id if not present
                if 'task_id' not in task_params:
                    task_params['task_id'] = f"task_{i}"
                tasks.append(task_params)

    if not tasks:
        logger.error("No tasks found in batch file")
        return 1

    logger.info(f"Loaded {len(tasks)} tasks, running with {num_workers} workers")

    # Run tasks in parallel
    results = []
    failed_tasks = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(run_single_task, task): task for task in tasks}

        for future in tqdm(as_completed(futures), total=len(tasks), desc="Processing tasks"):
            task = futures[future]
            task_id = task.get('task_id', 'unknown')

            try:
                exit_code, message = future.result()
                results.append((task_id, exit_code, message))

                if exit_code != 0:
                    failed_tasks.append(task_id)

            except Exception as e:
                logger.error(f"Task {task_id} raised exception: {e}")
                failed_tasks.append(task_id)
                results.append((task_id, 1, str(e)))

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Batch processing completed:")
    logger.info(f"  Total tasks: {len(tasks)}")
    logger.info(f"  Successful: {len(tasks) - len(failed_tasks)}")
    logger.info(f"  Failed: {len(failed_tasks)}")

    if failed_tasks:
        logger.error(f"  Failed task IDs: {', '.join(failed_tasks)}")

    logger.info(f"{'='*60}\n")

    return 0 if not failed_tasks else 1


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="APE Bench - Proof Engineering Benchmark Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Batch mode
    parser.add_argument("--batch", type=str,
                        help="JSONL file with batch task parameters (one task per line)")
    parser.add_argument("--num_workers", type=int, default=4,
                        help="Number of parallel workers for batch mode")

    # Single task mode
    parser.add_argument("--target_repo", type=str,
                        default="https://github.com/leanprover-community/mathlib4.git",
                        help="Target repository URL (default target inferred from lakefile)")
    parser.add_argument("--dataset_dir", type=str, help="Output directory")
    parser.add_argument("--output_file", type=str, help="Output file path")
    parser.add_argument("--min_diff_lines", type=int, help="Minimum diff lines")
    parser.add_argument("--max_diff_lines", type=int, help="Maximum diff lines")
    parser.add_argument("--latest_num_data", type=int, help="Number of latest data points")
    parser.add_argument("--max_commits_scan", type=int, help="Maximum commits to scan")
    parser.add_argument("--num_processes", type=int, help="Parallel processes")
    parser.add_argument("--scaffold_type", type=str, help="Scaffold name")
    parser.add_argument("--earliest_date", type=str, help="Earliest date (YYYY-MM-DD)")
    parser.add_argument("--latest_date", type=str, help="Latest date (YYYY-MM-DD)")
    parser.add_argument("--orchestrator_id", type=str,
                        help="Orchestrator ID for resume (auto-generated if not provided)")
    parser.add_argument("--enable_split", type=bool, help="Enable train/test split")
    parser.add_argument("--test_size", type=int, help="Number of samples for test set")
    parser.add_argument("--split_strategy", type=str, help="Sampling strategy for test set")

    return parser


if __name__ == "__main__":
    console_logger = create_logger()

    parser = create_argument_parser()
    args, remaining_args = parser.parse_known_args()

    # Check if batch mode
    if args.batch:
        batch_file = Path(args.batch)
        if not batch_file.exists():
            console_logger.error(f"Batch file not found: {batch_file}")
            sys.exit(1)

        sys.exit(run_batch(batch_file, args.num_workers))
    else:
        # Single task mode
        if not args.target_repo:
            console_logger.error("--target_repo is required in single task mode")
            sys.exit(1)

        config_overrides = parse_cli_args(remaining_args)

        sys.exit(asyncio.run(main(
            target_repo=args.target_repo,
            dataset_dir=Path(args.dataset_dir) if args.dataset_dir else None,
            output_file=Path(args.output_file) if args.output_file else None,
            min_diff_lines=args.min_diff_lines,
            max_diff_lines=args.max_diff_lines,
            num_processes=args.num_processes,
            latest_num_data=args.latest_num_data,
            max_commits_scan=args.max_commits_scan,
            scaffold_type=args.scaffold_type,
            earliest_date=args.earliest_date,
            latest_date=args.latest_date,
            orchestrator_id=args.orchestrator_id,
            enable_split=args.enable_split,
            test_size=args.test_size,
            split_strategy=args.split_strategy,
            config_overrides=config_overrides,
            logger=console_logger
        )))
