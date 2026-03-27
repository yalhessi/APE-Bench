"""
Base Scaffold Configuration Module.

Provides Pydantic configuration models for all scaffold types.
"""

from typing import Any, Optional, Dict
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, field_validator
from ape.orchestration.config import ExecutionConfig
from ape.tasks.base import BaseTaskConfig
from ape.llm_clients.config import LLMConfig
from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
from ape.toolkits.execute.bash.config import BashExecuteToolConfig
from ape.toolkits.retrieve.lean.config import LeanRetrieveToolConfig
from ape.toolkits.file_system.config import FileSystemToolConfig
from ape.runtime.local.runtime import LocalRuntimeConfig
from ape.runtime.base import RuntimeConfig
from ape.utils.project import PROJECT_ROOT


class BaseToolsConfig(BaseModel):
    """Base tools configuration shared by all scaffolds."""
    model_config = ConfigDict(extra='forbid')

    lean_verify: LeanVerifyToolConfig = Field(default_factory=LeanVerifyToolConfig)
    lean_retrieve: LeanRetrieveToolConfig = Field(default_factory=LeanRetrieveToolConfig)
    bash_execute: BashExecuteToolConfig = Field(default_factory=BashExecuteToolConfig)
    file_system: FileSystemToolConfig = Field(default_factory=FileSystemToolConfig)


class BaseScaffoldConfig(BaseModel):
    """Base scaffold configuration class.

    Uses runs directory for all execution results management.
    All paths are relative to PROJECT_ROOT to ensure consistency across different runtimes.
    """
    model_config = ConfigDict(extra='forbid')

    # Scaffold type identifier (must be overridden in subclasses)
    scaffold_type: str = Field(..., description="Scaffold type identifier")

    # System version
    version: str = "1.0.0"

    # Workspace configuration
    # IMPORTANT: This must be relative to PROJECT_ROOT for Docker runtime transparency
    runs_base_dir: Path = PROJECT_ROOT / ".ape" / "runs"
    target_workspace: Optional[Path] = None

    # Workspace structure
    workspaces_dir_name: str = "workspaces"  # Contains scratch/, target/, reference/

    # Agent workspace artifacts
    logs_dir_name: str = "logs"
    conversations_dir_name: str = "conversations"
    conversation_trees_file_name: str = "conversation_trees.jsonl"

    # MCP server configuration
    mcp_server_name: str = ""  # MCP server name prefix for tool name generation (e.g., "mcp__core__", "lean-research__"), empty means no prefix

    # Execution configuration
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)

    # Task configuration
    task_config: Optional[BaseTaskConfig] = None
    # Task config overrides passed from CLI/YAML (persisted for runtime task rebuild)
    task_config_overrides: Optional[Dict[str, Any]] = None

    # LLM configuration
    llm_config: LLMConfig = Field(default_factory=LLMConfig)

    # Tools configuration
    tools_config: BaseToolsConfig = Field(default_factory=BaseToolsConfig)

    # Runtime configuration (supports any RuntimeConfig subclass)
    # Uses Any to preserve actual type during serialization/deserialization
    runtime_config: Any = Field(
        default_factory=LocalRuntimeConfig,
        description="Runtime configuration (defaults to LocalRuntimeConfig)"
    )

    @field_validator('runtime_config', mode='before')
    @classmethod
    def validate_runtime_config(cls, v: Any) -> RuntimeConfig:
        """Convert dict to appropriate RuntimeConfig subclass.

        When runtime_config is serialized and deserialized (e.g., in multiprocessing),
        it becomes a dict. This validator converts it back to the correct RuntimeConfig
        subclass based on the 'runtime_type' field.

        RuntimeConfig instances are passed through unchanged, preserving their actual type.
        """
        # Ensure all runtime modules are imported and registered
        # This is critical for Docker runtime where field_validator runs in container
        import ape.runtime  # noqa: F401

        # RuntimeConfig instances (including subclasses) are preserved as-is
        if isinstance(v, RuntimeConfig):
            return v

        # Dict inputs are converted to the appropriate RuntimeConfig subclass
        if isinstance(v, dict):
            from ape.runtime.factory import create_runtime_config_for_type
            return create_runtime_config_for_type(**v)

        raise ValueError(
            f"runtime_config must be a RuntimeConfig instance or dict, got {type(v)}"
        )

    # Intelligent stop detection configuration
    # - consecutive_retries_threshold: stop after N consecutive "no submission" turns; None disables
    # - total_retries_threshold: stop after N total retries; None disables
    # NOTE: Not every scaffold uses distinct semantics; for some scaffolds total == consecutive.
    consecutive_retries_threshold: Optional[int] = None
    total_retries_threshold: Optional[int] = None

    # VS Code integration
    open_in_vscode: bool = False
