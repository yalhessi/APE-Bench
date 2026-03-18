"""Lean code generation task for Python-to-Lean translation."""

from pathlib import Path
import traceback
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

from ape.tasks.base import BaseTaskConfig, BaseTaskResult, EvaluationResult, register_task
from ape.tasks.lean_tasks.base import BaseLeanTask, BaseLeanTaskData

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class LeanCodeGenerationExample(BaseModel):
    """A hidden evaluation example rendered as Lean expressions."""

    args: List[str] = Field(
        default_factory=list,
        description="Positional arguments rendered as Lean expressions"
    )
    expected: str = Field(
        ...,
        description="Expected output rendered as a Lean expression"
    )


class LeanCodeGenerationConfig(BaseTaskConfig):
    """Configuration for Lean code generation tasks."""

    lean_verify_print_axioms: bool = False

    enabled_tools: Optional[List[str]] = [
        "bash_execute",
        "file_read",
        "file_write",
        "file_edit",
        "file_multi_edit",
        "lean_retrieve",
        "lean_verify",
        "code_hover",
        "code_goto",
        "code_references",
    ]

    def apply_to_scaffold_config(self, scaffold_config: "BaseScaffoldConfig") -> None:
        """Apply Lean verification settings to the scaffold config."""
        scaffold_config.tools_config.lean_verify.print_axioms = self.lean_verify_print_axioms


class LeanCodeGenerationData(BaseLeanTaskData):
    """Data model for Lean code generation tasks."""

    task_type: Literal["lean_code_generation"] = Field(
        default="lean_code_generation",
        description="Task type identifier"
    )

    task_description: str = Field(..., description="User-facing task description")
    source_language: Literal["python"] = Field(
        default="python",
        description="Source language for the translation task"
    )
    source_code: str = Field(..., description="Source program to translate")
    entry_point: str = Field(..., description="Required Lean declaration name")
    translation_contract: str = Field(..., description="Type and representation mapping contract")

    source_filename: Path = Field(
        default=Path("source.py"),
        description="Read-only source file written into scratch workspace"
    )
    target_filename: Path = Field(
        default=Path("translation.lean"),
        description="Suggested output file path inside scratch workspace"
    )

    benchmark_name: Optional[str] = Field(default=None, description="Benchmark family name")
    benchmark_task_id: Optional[str] = Field(default=None, description="Original benchmark task identifier")
    evaluation_examples: List[LeanCodeGenerationExample] = Field(
        default_factory=list,
        description="Hidden evaluation examples rendered as Lean expressions"
    )


class LeanCodeGenerationResult(BaseTaskResult):
    """Result model for Lean code generation tasks."""

    model_config = ConfigDict()

    translated_code: str = Field(..., description="Final Lean translation")
    verification_status: str = Field(default="", description="Verification summary")
    tests_passed: int = Field(default=0, description="Number of hidden checks passed")
    tests_total: int = Field(default=0, description="Total number of hidden checks")


class LeanCodeGenerationTask(BaseLeanTask):
    """Task implementation for translating Python programs into Lean."""

    task_type = "lean_code_generation"
    data_class = LeanCodeGenerationData
    task_config_class = LeanCodeGenerationConfig
    task_result_class = LeanCodeGenerationResult

    def __init__(self, data: LeanCodeGenerationData, config: "BaseScaffoldConfig"):
        """Initialize the task."""
        super().__init__(data, config)
        self.source_file_path: Optional[Path] = None
        self.target_file_path: Optional[Path] = None

    async def setup(
        self,
        termination_callback,
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
    ) -> "logging.LoggerAdapter":
        """Set up scratch files for the translation task."""
        logger = await super().setup(termination_callback, orchestrator_id, attempt_path)
        if not self.scratch_workspace:
            raise RuntimeError("Scratch workspace not initialized for Lean code generation task")

        self.source_file_path = self.scratch_workspace.path / self.data.source_filename
        self.target_file_path = self.scratch_workspace.path / self.data.target_filename

        self.source_file_path.parent.mkdir(parents=True, exist_ok=True)

        import aiofiles

        async with aiofiles.open(self.source_file_path, "w", encoding="utf-8") as handle:
            await handle.write(self.data.source_code)

        patterns = list(self.scratch_workspace.read_only_path_patterns or [])
        patterns.append(str(self.source_file_path.resolve()))
        self.scratch_workspace.read_only_path_patterns = patterns

        self.logger.info(
            "Source program written to: %s (read-only)",
            self.source_file_path.relative_to(self.scratch_workspace.path),
        )
        return logger

    async def create_user_prompt(self) -> str:
        """Create the user prompt for translation."""
        from ape.toolkits.code.python.provider import PythonCodeToolsProvider

        from .prompt import LEAN_CODE_GENERATION_USER_PROMPT

        submit_tool_name = f"{self.config.mcp_server_name}submit_result"
        source_program = PythonCodeToolsProvider.display_content(
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

        return LEAN_CODE_GENERATION_USER_PROMPT.format(
            submit_tool_name=submit_tool_name,
            task_description=task_description,
            translation_contract=self.data.translation_contract,
            source_program=source_program,
            source_file=self.data.source_filename.as_posix(),
            target_file=self.data.target_filename.as_posix(),
            entry_point=self.data.entry_point,
        )

    async def register_task_tools(self, mcp) -> None:
        """Register the submit tool for translation tasks."""
        from typing import Annotated
        from pydantic import Field

        @mcp.tool(
            description=(
                "Submit your final Lean translation. Provide either the code directly or a file path in "
                "the scratch workspace. This runs compilation and hidden HumanEval-derived checks.\n\n"
                "**CRITICAL: You MUST use this tool to submit your result. Providing results only in text response is INVALID and will NOT be accepted.**"
            )
        )
        async def submit_result(
            final_code_content: Annotated[Optional[str], Field(
                description="The final Lean translation as code content"
            )] = None,
            final_code_file_path: Annotated[Optional[str], Field(
                description="File path with workspace prefix. Example: 'scratch/translation.lean'"
            )] = None,
            message: Annotated[str, Field(
                description="Optional note about the translation approach.",
                default=""
            )] = "",
        ) -> Dict[str, Any]:
            """Submit the translation for evaluation."""
            self.logger.info("Tool submit_result: execution started")
            try:
                from ape.tasks.lean_tasks.utils import validate_final_code_params

                success, final_code, error_result = await validate_final_code_params(
                    final_code_content,
                    final_code_file_path,
                    self.workspaces_dir,
                )

                if not success:
                    return {
                        "evaluation_result": error_result,
                        "message": "Evaluation failed or not ready",
                    }

                if final_code_file_path and final_code_file_path.startswith("target/"):
                    error_result = EvaluationResult(
                        success=False,
                        score=0.0,
                        message=(
                            "Cannot submit a file from the target workspace. "
                            "Target workspaces are read-only; submit a file from scratch instead."
                        ),
                    )
                    return {
                        "evaluation_result": error_result,
                        "message": "Evaluation failed or not ready",
                    }

                evaluation_result = await self._evaluate_translation(final_code)
                should_terminate = self.should_terminate(evaluation_result)

                if should_terminate and self.termination_callback:
                    try:
                        task_result = self.create_result(
                            success=evaluation_result.success,
                            score=evaluation_result.score,
                            translated_code=final_code,
                            verification_status=evaluation_result.message or "",
                            tests_passed=(
                                len(self.data.evaluation_examples) if evaluation_result.score == 1.0 else 0
                            ),
                            tests_total=len(self.data.evaluation_examples),
                        )
                        await self.termination_callback(task_result)
                    except Exception:
                        self.logger.warning(
                            "Failed to trigger termination: %s",
                            traceback.format_exc(),
                        )

                self.logger.info(
                    "Tool submit_result: execution completed successfully (success=%s, score=%s)",
                    evaluation_result.success,
                    evaluation_result.score,
                )
                return {
                    "evaluation_result": evaluation_result,
                    "message": "Result submitted and evaluated",
                }

            except Exception:
                if self.logger:
                    self.logger.error(
                        "Lean code generation evaluation failed: %s",
                        traceback.format_exc(),
                    )
                evaluation_result = EvaluationResult(
                    success=False,
                    score=0.0,
                    message=traceback.format_exc(),
                )
                return {
                    "evaluation_result": evaluation_result,
                    "message": "Evaluation failed or not ready",
                }

    async def _evaluate_translation(self, final_code: str) -> EvaluationResult:
        """Compile the submission and run hidden behavior checks."""
        from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider

        if not self.data.evaluation_examples:
            return EvaluationResult(
                success=False,
                score=0.0,
                message="No hidden evaluation examples are configured for this task.",
            )

        lean_tool = LeanVerifyToolsProvider(
            task=self,
            config=self.config,
            logger=self.logger,
        )

        compile_result = await lean_tool.execute(code=final_code)
        if not compile_result.get("success", False):
            return EvaluationResult(
                success=False,
                score=0.0,
                message=self._format_compile_failure(compile_result),
                metrics={
                    "compile_passed": 0.0,
                    "hidden_examples": float(len(self.data.evaluation_examples)),
                },
            )

        hidden_check_code = self._build_hidden_check_code(final_code)
        hidden_check_result = await lean_tool.execute(code=hidden_check_code)

        if hidden_check_result.get("success", False):
            total = len(self.data.evaluation_examples)
            return EvaluationResult(
                success=True,
                score=1.0,
                message=(
                    "Translation compiled successfully and passed the hidden "
                    "HumanEval-derived behavior checks."
                ),
                metrics={
                    "compile_passed": 1.0,
                    "hidden_examples": float(total),
                },
            )

        self.logger.info(
            "Hidden HumanEval-derived checks failed for task %s",
            self.data.task_id,
        )
        self.logger.debug("Hidden check result: %s", hidden_check_result)
        return EvaluationResult(
            success=False,
            score=0.0,
            message=(
                "The translation compiles, but it does not satisfy the hidden "
                "HumanEval-derived behavior checks."
            ),
            metrics={
                "compile_passed": 1.0,
                "hidden_examples": float(len(self.data.evaluation_examples)),
            },
        )

    @staticmethod
    def _needs_parentheses(expr: str) -> bool:
        """Return whether a Lean expression should be parenthesized in application position."""
        stripped = expr.strip()
        if not stripped:
            return False
        if stripped[0] in "([{\"'":
            return False
        if stripped in {"true", "false", "none", "()"}:
            return False
        return " " in stripped or "\n" in stripped or stripped.startswith("-")

    @classmethod
    def _wrap_expression(cls, expr: str) -> str:
        """Wrap a Lean expression with parentheses when helpful."""
        stripped = expr.strip()
        if cls._needs_parentheses(stripped):
            return f"({stripped})"
        return stripped

    def _build_hidden_check_code(self, final_code: str) -> str:
        """Append hidden example checks to the submitted code."""
        hidden_examples: List[str] = []

        for example in self.data.evaluation_examples:
            call_args = " ".join(self._wrap_expression(arg) for arg in example.args)
            if call_args:
                call_expr = f"{self.data.entry_point} {call_args}"
            else:
                call_expr = self.data.entry_point

            # Use BEq-based checks so Float-valued tasks do not rely on missing DecidableEq instances.
            hidden_examples.append(
                "example : "
                f"({call_expr} == {self._wrap_expression(example.expected)}) = true := by\n"
                "  native_decide"
            )

        return final_code.rstrip() + "\n\n" + "\n\n".join(hidden_examples) + "\n"

    @staticmethod
    def _format_compile_failure(compile_result: Dict[str, Any]) -> str:
        """Convert Lean verification output into a user-visible compile failure message."""
        error_messages = [err["data"] for err in compile_result.get("errors", [])]
        warning_messages = [warn["data"] for warn in compile_result.get("warnings", [])]

        message_parts = ["Lean compilation failed."]
        if error_messages:
            message_parts.append("\nErrors:\n" + "\n".join(f"- {msg}" for msg in error_messages))
        if warning_messages:
            message_parts.append("\nWarnings:\n" + "\n".join(f"- {msg}" for msg in warning_messages))

        return "\n".join(message_parts)

    def create_result(
        self,
        success: bool,
        score: float,
        translated_code: str,
        verification_status: str = "",
        tests_passed: int = 0,
        tests_total: int = 0,
        **kwargs,
    ) -> BaseTaskResult:
        """Create a task result for code generation."""
        return self.task_result_class(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=success,
            score=score,
            translated_code=translated_code,
            verification_status=verification_status,
            tests_passed=tests_passed,
            tests_total=tests_total,
            **kwargs,
        )

    @classmethod
    def is_best_result(cls, result: BaseTaskResult) -> bool:
        """The optimal result is a fully verified translation."""
        return result.success and result.score == 1.0


register_task("lean_code_generation", LeanCodeGenerationTask)
