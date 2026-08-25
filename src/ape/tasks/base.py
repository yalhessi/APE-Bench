"""
Task Base Module.

This module provides the foundational classes for defining and executing tasks
in the APE framework:

- BaseTaskConfig: Configuration base class for task-specific settings
- BaseTaskData: Data model base class containing task input data
- EvaluationResult: Intermediate result from task evaluation
- BaseTaskResult: Final result model containing execution outcomes
- BaseTask: Base class that all task types must inherit from

The task system supports automatic attempt path management, environment setup,
and result aggregation for batch execution scenarios.
"""

import inspect
from typing import Dict, Any, List, TYPE_CHECKING, Optional, Callable, Awaitable
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid
import json
import hashlib
from ape.utils.logging import create_logger
from ape.utils import deep_merge

# Import data models
from ape.tasks.models import WorkspaceInfo

# Runtime import of TokenUsage to avoid Pydantic forward reference issues
from ape.llm_clients.models import TokenUsage

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class SemanticValidationConfig(BaseModel):
    """Configuration for semantic validation with judge-related settings."""

    enabled: bool = True
    judge_method: str = "agentic"  # "static" or "agentic"
    static_semantic_samples: int = 4
    agentic_semantic_samples: int = 3
    num_processes: int = 0  # Process count for judgment (0 = main process with async)
    max_concurrency: int = 3  # Maximum concurrent coroutines for judgment
    scaffold_type: str = "ape_agent"  # Scaffold used for judge tasks
    max_turns: int = 100
    judge_mode: str = "with_ground_truth"  # "generated_only" or "with_ground_truth"
    model: str = "gpt_5_mini"  # Model used for judge tasks
    runtime_type: str = "local"  # Runtime for judge tasks: "local" (default), "sandbox", "container"


class BaseTaskConfig(BaseModel):
    """Base class for task configuration - serves as a type marker.

    Note: Access control has been moved to WorkspaceInfo (ape.tasks.models.WorkspaceInfo).
    Tasks modify WorkspaceInfo's access control fields directly in setup().
    """
    model_config = ConfigDict(extra='forbid')
    # Tool configuration
    enabled_tools: Optional[List[str]] = None
    disabled_tools: Optional[List[str]] = None

    def apply_to_scaffold_config(self, scaffold_config: 'BaseScaffoldConfig') -> None:
        """Apply task configuration to scaffold configuration.

        Subclasses can override this method to apply task-level configuration
        (e.g., lean_verify) to scaffold's tools_config, ensuring the tool layer
        can use the task configuration.

        Args:
            scaffold_config: Scaffold configuration to modify (modified in-place).
        """
        pass  # Base class performs no modifications by default

class BaseTaskData(BaseModel):
    """Base class for task data models.

    All concrete task data models should inherit from this class.
    Provides automatic content-based hashing for deduplication.
    """
    task_type: str = Field(..., description="Task type identifier")
    task_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Task metadata")
    global_index: str = Field(default="", description="Content-based unique identifier")

    # Document databases for doc_retrieve tool
    document_databases: Optional[List[str]] = Field(
        default=None,
        description="Document database names for doc_retrieve"
    )

    def model_post_init(self, __context: Any) -> None:
        """Generate global_index after model initialization."""
        self.global_index = self.generate_global_index()

    def generate_global_index(self) -> str:
        """Generate a content-based unique identifier.

        Creates a SHA256 hash from stable content fields, excluding task_id,
        metadata, and global_index itself to ensure identical content produces
        identical hashes.

        Returns:
            A 64-character hexadecimal hash string.
        """
        data_for_hash = self.model_dump(mode='json', exclude={'task_id', 'metadata', 'global_index'})
        hash_content = json.dumps(data_for_hash, sort_keys=True, ensure_ascii=False)
        hash_obj = hashlib.sha256(hash_content.encode('utf-8'))
        return hash_obj.hexdigest()


class EvaluationResult(BaseModel):
    """Intermediate result from task evaluation.

Used by evaluators to return assessment results, which are then
converted to task-specific BaseTaskResult subclasses.
    """
    model_config = ConfigDict()

    success: bool = Field(..., description="Whether the evaluation completed successfully")
    score: float = Field(..., ge=0.0, le=1.0, description="Evaluation score (0.0-1.0)")
    message: Optional[str] = Field(None, description="Status message or feedback")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Quantitative metrics and evaluation data")
    nested_token_usage: Optional[TokenUsage] = Field(None, description="Token usage from nested task executions")


class BaseTaskResult(BaseModel):
    """Base class for task execution results.

    Provides standard fields for all task types. Concrete task types
    can inherit from this class and add task-specific fields.
    """
    model_config = ConfigDict()

    # Identity fields
    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Task type name")
    global_index: str = Field(..., description="Content-based unique identifier")

    # Core results
    success: bool = Field(..., description="Whether the task completed successfully")
    score: float = Field(..., ge=0.0, le=1.0, description="Task completion score (0.0-1.0)")

    # Execution statistics (populated by runner)
    execution_time: Optional[float] = Field(None, ge=0.0, description="Execution time in seconds")
    error: Optional[str] = Field(None, description="Error details if task failed")
    started_at: Optional[datetime] = Field(None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")

    # Extensible metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Task-specific metadata")

    # Token usage statistics
    token_usage: Optional[TokenUsage] = Field(None, description="LLM token usage statistics")
    nested_token_usage: Optional[TokenUsage] = Field(None, description="Token usage from nested tasks")

    # Custom metrics for task-specific statistics
    custom_metrics: Optional[Dict[str, float]] = Field(None, description="Task-specific metrics")


class BaseTask:
    """Base class for all task types.

    Subclasses must define the following class variables:
        task_type: Unique string identifier for the task type
        data_class: TaskData subclass for input data
        task_config_class: TaskConfig subclass for configuration
        task_result_class: BaseTaskResult subclass for output

    Attributes:
        data: Task input data
        config: Scaffold configuration
        attempt_path: Workspace attempt path (set during setup)
        workspaces_dir: Workspaces directory path (set during setup)
        scratch_workspace: Scratch workspace reference
        target_workspace: Target workspace (optional)
        reference_workspaces: Reference workspaces (optional)
        logger: Logger instance (set during setup)
    """

    # Class variables to be defined by subclasses
    task_type: str = None
    data_class: type[BaseTaskData] = None
    task_config_class: type['BaseTaskConfig'] = None
    task_result_class: type['BaseTaskResult'] = BaseTaskResult

    def __init__(self, data: BaseTaskData, config: 'BaseScaffoldConfig'):
        """Initialize task instance.

        Args:
            data: Task input data.
            config: Scaffold configuration.
        """
        self.data = data
        self.config = config
        self.attempt_path: Optional[Path] = None
        self.workspaces_dir: Optional[Path] = None
        self.scratch_workspace: Optional[WorkspaceInfo] = None
        self.target_workspace: Optional[WorkspaceInfo] = None
        self.reference_workspaces: Optional[List[WorkspaceInfo]] = None
        self.logger: Optional['logging.LoggerAdapter'] = None
        self.termination_callback: Optional[Callable[['BaseTaskResult'], Awaitable[None]]] = None
        self.progress_callback: Optional[Callable[[str], Any]] = None

        if self.data.task_type != self.task_type:
            raise ValueError(
                f"Task data type '{self.data.task_type}' does not match task class type '{self.task_type}'"
            )

    async def emit_progress(self, message: str) -> None:
        """Emit a user-facing progress message when a callback is available."""
        if not self.progress_callback:
            return

        result = self.progress_callback(message)
        if inspect.isawaitable(result):
            await result

    async def setup(
        self,
        termination_callback,
        orchestrator_id: str,
        attempt_path: Optional[Path] = None
    ) -> 'logging.LoggerAdapter':
        """Set up task workspaces and logging (template method).

        Args:
            termination_callback: Callback function for task termination.
            orchestrator_id: Orchestrator ID for path control ("cli" for CLI mode).
            attempt_path: Orchestrator-provided attempt path (if any).

        Returns:
            Logger instance for the scaffold to use.
        """
        try:
            self.is_cli_mode = (orchestrator_id == "cli")
            await self.emit_progress(f"Preparing task workspace for {self.task_type}...")

            # Ensure attempt_path exists (unified handling for both orchestrator and CLI modes)
            attempt_path = await self.__class__._ensure_attempt_path(
                config=self.config,
                orchestrator_id=orchestrator_id,
                attempt_path=attempt_path,
                data=self.data,
                task_type=self.task_type if hasattr(self, 'task_type') else None
            )

            # Create logger BEFORE setup_attempt so all components (RestoreManager, etc.) receive proper logger
            # This prevents workspace logs from being printed to stdout
            logs_dir = attempt_path / self.config.logs_dir_name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = logs_dir / f"scaffold_{timestamp}.log"
            self.logger = create_logger(log_file=log_file, to_console=False)

            # Setup attempt directory and workspaces (scratch, target, reference)
            # Call class method and unpack results (attempt_path already exists, so this is idempotent)
            attempt_path, scratch_workspace, target_workspace, reference_workspaces = await self.__class__.setup_attempt(
                data=self.data,
                config=self.config,
                orchestrator_id=orchestrator_id,
                attempt_path=attempt_path,
                logger=self.logger,
                progress_callback=self.progress_callback,
            )

            # Set instance variables
            self.attempt_path = attempt_path
            self.workspaces_dir = attempt_path / self.config.workspaces_dir_name
            self.scratch_workspace = scratch_workspace
            self.target_workspace = target_workspace
            self.reference_workspaces = reference_workspaces
            self.termination_callback = termination_callback

            self.logger.info(
                f"Workspace ready for task {self.data.task_id} "
                f"(global_index: {self.data.global_index}) at {attempt_path}"
            )

            return self.logger

        except Exception as e:
            raise RuntimeError(
                f"Failed to create workspace for task {self.data.task_id}: {e}"
            ) from e
    
    @classmethod
    async def setup_attempt(
        cls,
        data: 'BaseTaskData',
        config: 'BaseScaffoldConfig',
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        progress_callback: Optional[Callable[[str], Any]] = None,
    ) -> tuple[Path, WorkspaceInfo, Optional[WorkspaceInfo], Optional[List[WorkspaceInfo]]]:
        """Setup attempt directory structure (class method).

        Creates the basic attempt structure:
        - logs/ directory
        - conversations/ directory
        - workspaces/scratch/ directory

        Subclasses (e.g., BaseLeanTask) override this to add additional setup.

        Args:
            data: Task data
            config: Scaffold configuration
            orchestrator_id: Orchestrator ID or 'cli' for CLI mode.
            attempt_path: Optional pre-created attempt path.
            logger: Optional logger

        Returns:
            Tuple of (attempt_path, scratch_workspace, target_workspace, reference_workspaces)
        """
        attempt_path = await cls._ensure_attempt_path(
            config,
            orchestrator_id,
            attempt_path,
            data,
            cls.task_type if hasattr(cls, 'task_type') else None
        )

        # Create workspaces directory structure
        workspaces_dir = attempt_path / config.workspaces_dir_name
        workspaces_dir.mkdir(parents=True, exist_ok=True)

        # Create scratch workspace (actual directory)
        scratch_path = workspaces_dir / "scratch"
        scratch_path.mkdir(parents=True, exist_ok=True)

        scratch_workspace = WorkspaceInfo(
            name="scratch",
            path=scratch_path,
            target_path=scratch_path,
            commit_hash=None,
            repo_url=None,
            default_target=None
        )

        return attempt_path, scratch_workspace, None, None

    @classmethod
    async def _ensure_attempt_path(
        cls,
        config: 'BaseScaffoldConfig',
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
        data: Optional['BaseTaskData'] = None,
        task_type: Optional[str] = None
    ) -> Path:
        """Ensure attempt directories exist and return their paths."""
        if attempt_path:
            attempt_path.mkdir(parents=True, exist_ok=True)
        else:
            attempt_path = await cls._create_attempt_path(config, orchestrator_id, data, task_type)

        (attempt_path / config.logs_dir_name).mkdir(parents=True, exist_ok=True)
        (attempt_path / config.conversations_dir_name).mkdir(parents=True, exist_ok=True)

        return attempt_path

    async def signal_termination(self, result: 'BaseTaskResult') -> None:
        """Invoke termination callback if available."""
        if self.termination_callback:
            await self.termination_callback(result)

    @classmethod
    async def _create_attempt_path(
        cls,
        config: 'BaseScaffoldConfig',
        orchestrator_id: str,
        data: Optional['BaseTaskData'] = None,
        task_type: Optional[str] = None
    ) -> Path:
        """Create attempt directory structure.

        Args:
            config: Scaffold configuration
            orchestrator_id: Orchestrator ID or 'cli' for CLI mode.
            data: Optional task data for metadata
            task_type: Optional task type for metadata

        Returns:
            attempt_path.
        """
        runs_base = config.runs_base_dir
        base_path = runs_base / orchestrator_id
        base_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        uuid_str = str(uuid.uuid4())[:8]
        instance_id = f"agent_{timestamp}_{uuid_str}"

        attempt_path = base_path / instance_id
        attempt_path.mkdir(parents=True, exist_ok=True)

        if data:
            metadata = {
                "task_id": data.task_id,
                "task_type": task_type or "unknown",
                "global_index": data.global_index,
                "orchestrator_id": orchestrator_id,
                "created_at": datetime.now().isoformat(),
                "instance_id": instance_id,
                "workspaces_dir": "workspaces",
                "task_data": data.model_dump(mode='json'),
                "task_config": config.task_config.model_dump(mode='json') if config.task_config else {}
            }

            metadata_file = attempt_path / "metadata.json"
            import aiofiles
            async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(metadata, ensure_ascii=False, indent=2))

        return attempt_path

    @classmethod
    def create_data_from_dict(cls, data: Dict[str, Any]) -> BaseTaskData:
        """Create task data instance from dictionary.

        Subclasses may override for custom data creation logic.

        Args:
            data: Dictionary containing task data fields.

        Returns:
            BaseTaskData instance.
        """
        if cls.data_class is None:
            raise ValueError(f"Task class {cls.__name__} must define data_class")

        return cls.data_class.model_validate(data)

    @classmethod
    def from_data(cls, data: Dict[str, Any], config: 'BaseScaffoldConfig') -> 'BaseTask':
        """Create task instance from data dictionary and configuration."""
        task_data = cls.create_data_from_dict(data)
        return cls(task_data, config)

    async def register_task_tools(self, mcp) -> None:
        """Register task-specific tools. Override in subclasses."""
        pass

    async def create_user_prompt(self) -> str:
        """Create user prompt for the task. Default returns empty string."""
        return ""

    def create_result(self, **kwargs) -> BaseTaskResult:
        """Create task result using the configured task_result_class."""
        if self.task_result_class is None:
            raise ValueError(f"Task class {self.__class__.__name__} must define task_result_class")
        identity_fields = {
            "task_id": self.data.task_id,
            "task_type": self.task_type or self.data.task_type,
            "global_index": self.data.global_index,
        }
        identity_fields.update(kwargs)
        return self.task_result_class(**identity_fields)

    def should_terminate(self, evaluation_result: EvaluationResult = None) -> bool:
        """Determine if execution should terminate.

        Default implementation terminates when score reaches 1.0.
        Subclasses may override for custom termination logic.

        Args:
            evaluation_result: Evaluation result to check.

        Returns:
            True if execution should terminate.
        """
        if evaluation_result is None:
            return False
        return evaluation_result.score == 1.0
    
    @classmethod
    def _aggregate_resources(cls, results: List[BaseTaskResult]) -> dict:
        """Aggregate resource consumption statistics from multiple results."""
        valid_usages = [r.token_usage for r in results if r.token_usage]
        aggregated_usage = valid_usages[0] if valid_usages else None

        return {
            "execution_time": sum(r.execution_time for r in results if r.execution_time),
            "started_at": min((r.started_at for r in results if r.started_at), default=None),
            "completed_at": max((r.completed_at for r in results if r.completed_at), default=None),
            "token_usage": aggregated_usage
        }

    @classmethod
    def aggregate_results(cls, results: List[BaseTaskResult]) -> BaseTaskResult:
        """Aggregate multiple task results. Default: select highest score."""
        if not results:
            raise ValueError("No results to aggregate")

        best_result = max(results, key=lambda r: r.score)
        resources = cls._aggregate_resources(results)

        return best_result.model_copy(update=resources)

    @classmethod
    def is_best_result(cls, result: BaseTaskResult) -> bool:
        """Check if result is optimal (for early termination).

        Args:
            result: Task result to check.

        Returns:
            True if result is optimal (default: score == 1.0).
        """
        return result.success and result.score == 1.0

    @classmethod
    def aggregate_custom_metrics(cls, results: List[BaseTaskResult]) -> Optional[Dict[str, float]]:
        """Aggregate custom metrics across multiple task results.

        Default implementation computes macro-average of numeric metrics.
        Subclasses may override for custom aggregation (e.g., confusion matrix).

        Args:
            results: List of task results (each already aggregated).

        Returns:
            Aggregated metrics dictionary, or None if no metrics.
        """
        from collections import defaultdict

        if not results:
            return None

        metrics_by_key = defaultdict(list)

        for result in results:
            if result.success and result.custom_metrics:
                for key, value in result.custom_metrics.items():
                    if isinstance(value, (int, float)):
                        metrics_by_key[key].append(float(value))

        aggregated = {}
        for key, values in metrics_by_key.items():
            if values:
                aggregated[key] = sum(values) / len(values)

        return aggregated if aggregated else None

# Global task registry
_tasks: Dict[str, type['BaseTask']] = {}


def register_task(task_type: str, task_class: type['BaseTask']) -> None:
    """Register a task type in the global registry."""
    _tasks[task_type] = task_class


def get_task_class(task_type: str) -> type['BaseTask']:
    """Get task class from registry.

    Args:
        task_type: Task type identifier

    Returns:
        Task class

    Raises:
        ValueError: If task type is not registered
    """
    if task_type not in _tasks:
        raise ValueError(
            f"Unknown task type: {task_type}. "
            f"Registered types: {list(_tasks.keys())}"
        )
    return _tasks[task_type]


def result_counts_as_pass(result: BaseTaskResult) -> bool:
    """Check whether a task result counts as a pass in orchestration summaries."""
    task_class = get_task_class(result.task_type)
    return task_class.is_best_result(result)


def create_task_from_data(
    data: Dict[str, Any],
    config: 'BaseScaffoldConfig',
    task_config_overrides: Optional[Dict[str, Any]] = None
) -> 'BaseTask':
    """Create a task instance from data dictionary.

    Args:
        data: Task data dictionary (must include 'task_type' field).
        config: Base scaffold configuration.
        task_config_overrides: Optional overrides for task configuration.

    Returns:
        Task instance.

    Raises:
        ValueError: If task_type is missing or not registered.
    """
    task_type = data.get('task_type')
    if not isinstance(task_type, str) or not task_type.strip():
        raise ValueError(
            f"task_data must contain 'task_type' field. Got: {list(data.keys())}"
        )

    task_class = get_task_class(task_type)
    if task_class.task_type != task_type:
        raise ValueError(
            f"Task class {task_class.__name__} has task_type={task_class.task_type}, "
            f"but requested {task_type}"
        )

    record_task_config_overrides = data.get("task_config_overrides")
    if not isinstance(record_task_config_overrides, dict):
        record_task_config_overrides = {}

    overrides = deep_merge(record_task_config_overrides, task_config_overrides or {})
    valid_overrides = {
        k: v for k, v in overrides.items()
        if k in task_class.task_config_class.model_fields
    }
    task_config = task_class.task_config_class(**valid_overrides)

    task_specific_config = config.model_copy(update={'task_config': task_config}, deep=True)
    task_config.apply_to_scaffold_config(task_specific_config)

    return task_class.from_data(data, task_specific_config)


def create_task_config_for_type(task_type: str, **overrides) -> 'BaseTaskConfig':
    """Create task configuration for a specific task type.

    Args:
        task_type: Task type identifier.
        **overrides: Configuration parameters to override.

    Returns:
        BaseTaskConfig instance for the specified task type.

    Raises:
        ValueError: If task_type is not registered.
    """
    task_class = get_task_class(task_type)
    return task_class.task_config_class.model_validate(overrides)


def list_task_types() -> List[str]:
    """Return registered task types in sorted order."""
    return sorted(_tasks.keys())
