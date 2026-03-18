"""Lean spec generation task for prompt-only HumanEval formalization."""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Literal

from pydantic import ConfigDict, Field

from ape.tasks.base import register_task
from ape.tasks.lean_tasks.program_synthesis.code_generation.task import (
    LeanCodeGenerationConfig,
    LeanCodeGenerationData,
    LeanCodeGenerationResult,
    LeanCodeGenerationTask,
)

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig


class LeanSpecGenerationConfig(LeanCodeGenerationConfig):
    """Configuration for prompt-only Lean formalization tasks."""


class LeanSpecGenerationData(LeanCodeGenerationData):
    """Data model for prompt-only Lean formalization tasks."""

    task_type: Literal["lean_spec_generation"] = Field(
        default="lean_spec_generation",
        description="Task type identifier"
    )
    source_code: str = Field(
        ...,
        description="Visible HumanEval prompt/program stub to formalize into Lean"
    )
    source_filename: Path = Field(
        default=Path("prompt.py"),
        description="Read-only prompt file written into scratch workspace"
    )
    target_filename: Path = Field(
        default=Path("formalization.lean"),
        description="Suggested output file path inside scratch workspace"
    )


class LeanSpecGenerationResult(LeanCodeGenerationResult):
    """Result model for prompt-only Lean formalization tasks."""

    model_config = ConfigDict()


class LeanSpecGenerationTask(LeanCodeGenerationTask):
    """Task implementation for formalizing HumanEval prompts into Lean."""

    task_type = "lean_spec_generation"
    data_class = LeanSpecGenerationData
    task_config_class = LeanSpecGenerationConfig
    task_result_class = LeanSpecGenerationResult

    def __init__(self, data: LeanSpecGenerationData, config: "BaseScaffoldConfig"):
        """Initialize the task."""
        super().__init__(data, config)

    async def create_user_prompt(self) -> str:
        """Create the user prompt for prompt-only formalization."""
        from ape.toolkits.code.python.provider import PythonCodeToolsProvider

        from .prompt import LEAN_SPEC_GENERATION_USER_PROMPT

        submit_tool_name = f"{self.config.mcp_server_name}submit_result"
        source_prompt = PythonCodeToolsProvider.display_content(
            content=self.data.source_code,
            add_line_numbers=False,
            display_mode="full",
            body_handling="keep_all",
        )

        benchmark_prefix = ""
        if self.data.benchmark_name and self.data.benchmark_task_id:
            benchmark_prefix = (
                f"This instance comes from {self.data.benchmark_name} task "
                f"`{self.data.benchmark_task_id}`.\n\n"
            )

        task_description = benchmark_prefix + self.data.task_description

        return LEAN_SPEC_GENERATION_USER_PROMPT.format(
            submit_tool_name=submit_tool_name,
            task_description=task_description,
            translation_contract=self.data.translation_contract,
            source_prompt=source_prompt,
            source_file=self.data.source_filename.as_posix(),
            target_file=self.data.target_filename.as_posix(),
            entry_point=self.data.entry_point,
        )


register_task("lean_spec_generation", LeanSpecGenerationTask)

