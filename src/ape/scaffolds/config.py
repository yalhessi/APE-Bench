"""
Base Scaffold Configuration Module.

Provides Pydantic configuration models for all scaffold types.
"""

from typing import Any, Dict, Literal, Optional
from pathlib import Path
import importlib

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
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
from ape.scaffolds.skills import SkillsConfig


#: The key under which a serialized task config names its own class (see `BaseScaffoldConfig`).
TASK_CONFIG_CLASS_KEY = "__task_config_class__"


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

    @field_serializer("task_config")
    def _serialize_task_config(self, value: Optional[BaseTaskConfig], info):
        """A concrete task config crosses the worker boundary as itself, not as its base class.

        The field is annotated `BaseTaskConfig`, and pydantic serializes a field by its
        annotation: a `LeanJudgmentConfig(judge_mode=...)` dumped as two base fields, the worker
        validated those back into a bare `BaseTaskConfig`, and every subclass setting was gone
        with no warning. So the dump names its class, and the validator below restores it.
        Only explicitly set fields are written, so a field left at its default stays a default.
        """

        if value is None:
            return None
        cls = type(value)
        payload = value.model_dump(mode=info.mode, exclude_unset=True)
        return {TASK_CONFIG_CLASS_KEY: f"{cls.__module__}:{cls.__qualname__}", **payload}

    @field_validator("task_config", mode="before")
    @classmethod
    def _restore_task_config(cls, value: Any) -> Any:
        """The inverse of `_serialize_task_config`; an untagged dict validates as before."""

        if isinstance(value, dict) and TASK_CONFIG_CLASS_KEY in value:
            payload = dict(value)
            module_name, _, qualname = payload.pop(TASK_CONFIG_CLASS_KEY).partition(":")
            target: Any = importlib.import_module(module_name)
            for part in qualname.split("."):
                target = getattr(target, part)
            if not (isinstance(target, type) and issubclass(target, BaseTaskConfig)):
                raise ValueError(f"{module_name}:{qualname} is not a task config class")
            return target.model_validate(payload)
        return value

    # Managed agent skills
    skills: SkillsConfig = Field(default_factory=SkillsConfig)

    # LLM configuration
    llm_config: LLMConfig = Field(default_factory=LLMConfig)

    #: The preamble a batch session opens with (`ape.scaffolds.prompts.BATCH_PREAMBLES`).
    #: "standard" is what every run before 2026-10-01 saw; "plain" drops its imperatives (text
    #: "accomplishes NOTHING", batch every call, submit only when "COMPLETED and VALIDATED") for
    #: a task whose own contract says how to work. Part of the scaffold config, so of the plan.
    #: On the base, with `workspace_environment`, since 2026-10-01: every scaffold builds
    #: its first message from the same preamble (APE-Agent as its system message, Claude
    #: Code and Codex in their first user message), so a contract condition that sets
    #: them means the same text under each harness. The default stays "standard" although the
    #: best Claude results ran without it and gpt's recall did not move when it was dropped
    #: (dev, 2-3 of 23 either way): 127 of the 135 review configs inherit the default
    #: (2026-10-05) and have runs under their names, so flipping it would change what each
    #: of them means. A new review config sets "plain", or extends one that does.
    batch_preamble: Literal["standard", "plain"] = "standard"

    #: False drops the system prompt's `<environment>` section (scratch as a place for "rapid
    #: iteration and experimentation", target as the verification library) unless it carries
    #: blocked-path notes. True, the default, is every run before 2026-10-01.
    workspace_environment: bool = True

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
