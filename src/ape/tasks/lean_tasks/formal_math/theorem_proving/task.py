"""
Lean Theorem Proving Task Module.

Provides task definitions for Lean theorem proving, including
data models, task configuration, and evaluation logic.
"""

from typing import Dict, Any, Callable, Optional, List, TYPE_CHECKING, Literal
import traceback
from pydantic import Field, BaseModel, ConfigDict
from ape.tasks.base import BaseTaskConfig, register_task
from ape.tasks.base import BaseTaskResult, EvaluationResult
from ape.tasks.lean_tasks.base import BaseLeanTask, BaseLeanTaskData
from ape.toolkits.code.lean.provider import LeanCodeToolsProvider

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig


class LeanTheoremProvingConfig(BaseTaskConfig):
    """Configuration for Lean theorem proving tasks."""
    lean_verify_print_axioms: bool = True
    check_theorem_statement: bool = True
    enabled_tools: Optional[List[str]] = [
        "bash_execute",
        "file_read",
        # "file_search",
        # "content_search",
        "file_write",
        "file_edit",
        "file_multi_edit",
        "lean_retrieve",
        "lean_verify",
        "get_lean_goal",
        "code_hover",
        "code_goto",
        "code_references",
    ]

    def apply_to_scaffold_config(self, scaffold_config: 'BaseScaffoldConfig') -> None:
        """Apply lean_verify configuration to scaffold."""
        scaffold_config.tools_config.lean_verify.print_axioms = self.lean_verify_print_axioms


class LeanTheoremProvingData(BaseLeanTaskData):
    """Data model for Lean theorem proving tasks."""

    task_type: Literal["lean_theorem_proving"] = Field(
        default="lean_theorem_proving",
        description="Task type identifier"
    )
    theorem_statement: str = Field(..., description="Theorem statement to prove")


class LeanTheoremProvingResult(BaseTaskResult):
    """Result model for Lean theorem proving tasks."""
    model_config = ConfigDict()

    theorem_statement: str = Field(..., description="Theorem statement")
    proof_code: str = Field(..., description="Proof code")
    verification_status: str = Field(default="", description="Verification status")


class LeanTheoremProvingTask(BaseLeanTask):
    """Lean theorem proving task with syntax verification."""

    task_type = "lean_theorem_proving"
    data_class = LeanTheoremProvingData
    task_config_class = LeanTheoremProvingConfig
    task_result_class = LeanTheoremProvingResult

    def __init__(self, data: LeanTheoremProvingData, config: 'BaseScaffoldConfig'):
        """Initialize theorem proving task."""
        super().__init__(data, config)

    async def create_user_prompt(self) -> str:
        """Create user prompt for theorem proving task."""
        from .prompt import LEAN_THEOREM_PROVING_USER_PROMPT

        # Get submit tool name from config (mcp_server_name already includes trailing __)
        submit_tool_name = f"{self.config.mcp_server_name}submit_result"

        return LEAN_THEOREM_PROVING_USER_PROMPT.format(
            theorem_statement=self.data.theorem_statement,
            submit_tool_name=submit_tool_name
        )

    async def register_task_tools(self, mcp) -> None:
        """Register task-specific tools for theorem proving."""
        from typing import Annotated
        from pydantic import Field

        @mcp.tool(
            description=(
                "Submit your final solution for theorem proving tasks. Provide either code content directly "
                "or file path to your solution. This will trigger evaluation and may end the conversation.\n\n"
                "**CRITICAL: You MUST use this tool to submit your result. Providing results only in text response is INVALID and will NOT be accepted.**"
            )
        )
        async def submit_result(
            final_code_content: Annotated[Optional[str], Field(
                description="The final Lean proof code content, complete and ready for verification"
            )] = None,
            final_code_file_path: Annotated[Optional[str], Field(
                description="File path with workspace prefix. Example: 'scratch/solution.lean'"
            )] = None,
            message: Annotated[str, Field(
                description="Optional message describing your proof approach (optional).",
                default=""
            )] = ""
        ) -> Dict[str, Any]:
            """Submit final result for theorem proving evaluation and potential termination."""
            # EvaluationResult already imported above

            self.logger.info("Tool submit_result: execution started")
            try:
                from ape.tasks.lean_tasks.utils import validate_final_code_params

                success, final_code, error_result = await validate_final_code_params(
                    final_code_content, final_code_file_path,
                    self.workspaces_dir
                )

                if not success:
                    return {
                        "evaluation_result": error_result,
                        "message": "Evaluation failed or not ready"
                    }

                if final_code_file_path and final_code_file_path.startswith("target/"):
                    file_path_str = final_code_file_path.replace("target/", "")
                    error_result = EvaluationResult(
                        success=False,
                        score=0.0,
                        message=f"Cannot submit target workspace file: {file_path_str}. Target workspace is read-only. You must submit files from scratch workspace."
                    )
                    return {
                        "evaluation_result": error_result,
                        "message": "Evaluation failed or not ready"
                    }

                evaluation_result = await self._evaluate_lean_theorem(final_code)

                should_terminate = self.should_terminate(evaluation_result)

                if should_terminate and self.termination_callback:
                    try:
                        task_result = self.create_result(
                            success=evaluation_result.success,
                            score=evaluation_result.score,
                            proof_code=final_code,
                            verification_status="Evaluation completed"
                        )

                        await self.termination_callback(task_result)
                    except Exception as e:
                        self.logger.warning(f"Failed to trigger termination: {traceback.format_exc()}")

                self.logger.info(f"Tool submit_result: execution completed successfully (success={evaluation_result.success}, score={evaluation_result.score})")
                return {
                    "evaluation_result": evaluation_result,
                    "message": "Result submitted and evaluated"
                }

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Lean theorem proving evaluation failed: {traceback.format_exc()}")
                evaluation_result = EvaluationResult(
                    success=False,
                    score=0.0,
                    message=traceback.format_exc()
                )
                return {
                    "evaluation_result": evaluation_result,
                    "message": "Evaluation failed or not ready"
                }

    async def _evaluate_lean_theorem(self, final_code: str) -> EvaluationResult:
        """Evaluate Lean theorem proof."""
        import time
        import re
        start_time = time.time()

        try:
            task_config: LeanTheoremProvingConfig = self.config.task_config

            # Check theorem statement presence
            if task_config.check_theorem_statement and self.data.theorem_statement:
                if not self._contains_theorem_statement(final_code, self.data.theorem_statement):
                    theorem_preview = self.data.theorem_statement
                    if ":=" in theorem_preview:
                        theorem_preview = theorem_preview[:theorem_preview.find(":=")].strip()

                    return EvaluationResult(
                        success=True,
                        score=0.0,
                        message=f"Code does not contain the required theorem statement. Expected theorem signature:\n\n{theorem_preview}"
                    )

            # Verify Lean code
            from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider
            lean_tool = LeanVerifyToolsProvider(
                task=self,
                config=self.config,
                logger=self.logger
            )

            verification_result = await lean_tool.execute(code=final_code)

            if verification_result.get("success", False):
                return EvaluationResult(
                    success=True,
                    score=1.0,
                    message="Theorem proving evaluation completed successfully"
                )
            else:
                error_messages = [err["data"] for err in verification_result.get("errors", [])]
                warning_messages = [warn["data"] for warn in verification_result.get("warnings", [])]

                message_parts = ["Lean verification failed."]
                if error_messages:
                    message_parts.append(f"\nErrors:\n" + "\n".join(f"- {msg}" for msg in error_messages))
                if warning_messages:
                    message_parts.append(f"\nWarnings:\n" + "\n".join(f"- {msg}" for msg in warning_messages))

                return EvaluationResult(
                    success=True,
                    score=0.0,
                    message="\n".join(message_parts),
                    metrics=None
                )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Lean theorem proving execution failed: {traceback.format_exc()}")
            return EvaluationResult(
                success=False,
                score=0.0,
                message=traceback.format_exc()
            )

    def _contains_theorem_statement(self, code: str, theorem_statement: str) -> bool:
        """Check if code contains the required theorem statement."""
        import re

        normalized_code = re.sub(r'\s+', '', LeanCodeToolsProvider.remove_comments(code))
        theorem_no_comments = LeanCodeToolsProvider.remove_comments(theorem_statement)

        for statement in re.split(r'\n\n\s*', theorem_no_comments):
            snippet = statement.strip()
            if not snippet:
                continue

            if ':=' in snippet:
                snippet = snippet.split(':=', 1)[0]

            normalized_theorem = re.sub(r'\s+', '', snippet)
            if not normalized_theorem:
                continue

            if normalized_theorem not in normalized_code:
                return False

        return True

    def create_result(
        self,
        success: bool,
        score: float,
        proof_code: str,
        verification_status: str = "",
        **kwargs
    ) -> LeanTheoremProvingResult:
        """Create theorem proving task result."""
        return LeanTheoremProvingResult(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=success,
            score=score,
            theorem_statement=self.data.theorem_statement,
            proof_code=proof_code,
            verification_status=verification_status,
            **kwargs
        )

    @classmethod
    def is_best_result(cls, result: 'BaseTaskResult') -> bool:
        """Check if result is optimal (verification passed)."""
        return result.success and result.score == 1.0


register_task("lean_theorem_proving", LeanTheoremProvingTask)
