"""
Proof Engineering Task.

Provides task definitions for Lean proof engineering,
separating data models from task logic.
"""

from typing import Dict, Any, Callable, Optional, List, TYPE_CHECKING, Literal
import traceback
from datetime import datetime
from pathlib import Path
from pydantic import Field, BaseModel, ConfigDict

from ape.tasks.base import BaseTaskConfig, register_task, BaseTaskData, BaseTaskResult, EvaluationResult, SemanticValidationConfig
from ape.tasks.models import WorkspaceInfo
from ape.tasks.lean_tasks.base import BaseLeanTask

# Configuration components (LeanVerifyToolConfig is passed via scaffold config)

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class LeanProofEngineeringConfig(BaseTaskConfig):
    """Configuration for Lean proof engineering tasks."""

    lean_verify_print_axioms: bool = False  # Proof engineering doesn't need axiom checking

    semantic_validation: SemanticValidationConfig = SemanticValidationConfig(enabled=True)

    # APE-Bench specific configuration
    skip_syntax_validation: bool = False  # Skip syntax validation (for APE-Bench ground truth)

    # Code formatting configuration
    include_original_code_in_prompt: bool = False  # Include original code content in prompt
    format_body_handling: str = "keep_all"  # "keep_all" | "omit_all"
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
        """Apply task's lean_verify configuration to scaffold's tools_config."""
        scaffold_config.tools_config.lean_verify.print_axioms = self.lean_verify_print_axioms


class LeanProofEngineeringData(BaseTaskData):
    """Data model for Lean proof engineering tasks."""

    task_type: Literal["lean_proof_engineering"] = Field(
        default="lean_proof_engineering",
        description="Task type identifier"
    )

    task_description: str = Field(..., description="Task description")
    original_code: Optional[str] = Field(default=None, description="Original code (None for new file creation)")
    reference_implementation: Optional[str] = Field(default=None, description="Reference implementation")
    gold_diff: Optional[str] = Field(default=None, description="Reference diff")
    filename: Optional[Path] = Field(default=None, description="File name")

    target_workspace: WorkspaceInfo = Field(
        ...,
        description="Target workspace specification"
    )
    reference_workspaces: Optional[List[WorkspaceInfo]] = Field(
        default=None,
        description="List of reference workspaces"
    )


class LeanProofEngineeringResult(BaseTaskResult):
    """Result model for Lean proof engineering tasks."""

    model_config = ConfigDict()

    improved_code: str = Field(..., description="Improved code after engineering")


class LeanProofEngineeringTask(BaseLeanTask):
    """Lean proof engineering task implementation."""

    task_type = "lean_proof_engineering"
    data_class = LeanProofEngineeringData
    task_config_class = LeanProofEngineeringConfig
    task_result_class = LeanProofEngineeringResult

    def __init__(self, data: LeanProofEngineeringData, config: 'BaseScaffoldConfig'):
        """Initialize proof engineering task."""
        super().__init__(data, config)

        # Instance variables (set during setup)
        self.scratch_original_path: Optional[Path] = None
        self.scratch_file_path: Optional[Path] = None
        self.target_workspace_expected_file_path: Optional[Path] = None
    
    async def setup(
        self,
        termination_callback,
        orchestrator_id: str,
        attempt_path: Optional[Path] = None
    ) -> 'logging.LoggerAdapter':
        """Set up proof engineering task environment.

        Extends base class setup with:
        1. Writing original_code to scratch workspace (if provided)
        2. Validating reference_implementation consistency (if provided)
        3. Setting scratch workspace access control (original file as read-only)

        Args:
            termination_callback: Termination callback function.
            orchestrator_id: Task orchestrator ID.
            attempt_path: Preset workspace path (when provided by orchestrator/runtime).

        Returns:
            Scaffold logger instance.
        """
        logger = await super().setup(termination_callback, orchestrator_id, attempt_path)
        if not self.scratch_workspace:
            raise RuntimeError("Scratch workspace not initialized for proof engineering task")

        # Set file paths and write original_code if provided
        if self.data.filename:
            # Create corresponding full path in scratch workspace
            # filename is relative to repo root (e.g., "Mathlib/Topology/Subpath.lean")
            self.scratch_file_path = self.scratch_workspace.path / self.data.filename
            if not self.target_workspace:
                raise RuntimeError("Target workspace not initialized for proof engineering task")
            # Use workspace root path (not target_path) since filename includes full path
            self.target_workspace_expected_file_path = self.target_workspace.path / self.data.filename

            # If original_code exists, use filename with _ORIGINAL suffix
            if self.data.original_code:
                # Add _ORIGINAL suffix to distinguish (e.g., Basic.lean -> Basic_ORIGINAL.lean)
                original_filename = Path(self.data.filename)
                original_with_suffix = original_filename.parent / f"{original_filename.stem}_ORIGINAL{original_filename.suffix}"
                self.scratch_original_path = self.scratch_workspace.path / original_with_suffix

                # Create directory structure and write original file
                self.scratch_original_path.parent.mkdir(parents=True, exist_ok=True)
                import aiofiles
                async with aiofiles.open(self.scratch_original_path, 'w', encoding='utf-8') as f:
                    await f.write(self.data.original_code)

                self.logger.info(f"Original code written to: {self.scratch_original_path.relative_to(self.scratch_workspace.path)} (read-only)")
            else:
                self.scratch_original_path = None
                self.logger.info("No original code provided (new file creation task)")
        else:
            # No filename: write original_code to root directory
            self.scratch_file_path = None
            self.target_workspace_expected_file_path = None

            if self.data.original_code:
                self.scratch_original_path = self.scratch_workspace.path / "original.lean"
                self.scratch_original_path.parent.mkdir(parents=True, exist_ok=True)
                import aiofiles
                async with aiofiles.open(self.scratch_original_path, 'w', encoding='utf-8') as f:
                    await f.write(self.data.original_code)
                self.logger.info(f"Original code written to: {self.scratch_original_path.relative_to(self.scratch_workspace.path)} (read-only)")
            else:
                self.scratch_original_path = None
                self.logger.info("No original code provided (new file creation task)")

        # Validate reference_implementation consistency if provided
        # if self.data.reference_implementation:
        #     await self._validate_reference_implementation()

        # Set scratch workspace access control (original file as read-only)
        if self.scratch_original_path:
            self.scratch_workspace.read_only_path_patterns = [
                str(self.scratch_original_path.resolve())
            ]
            self.logger.debug(f"Set scratch original file as read-only: {self.scratch_original_path}")

        return logger
    
    async def _validate_reference_implementation(self) -> None:
        """Validate reference_implementation consistency with target workspace."""
        if not self.data.reference_implementation or not self.data.filename:
            return
        try:
            if not self.target_workspace:
                raise RuntimeError("Target workspace not initialized for proof engineering task")
            # filename is relative to repo root (includes full path like "Mathlib/...")
            target_file_path = self.target_workspace.path / self.data.filename

            if not target_file_path.exists():
                raise ValueError(
                    f"Reference file not found in target workspace: {self.data.filename}. "
                    f"This indicates a dataset construction error."
                )

            import aiofiles
            async with aiofiles.open(target_file_path, 'r', encoding='utf-8') as f:
                actual_content = await f.read()

            if actual_content.strip() != self.data.reference_implementation.strip():
                raise ValueError(
                    f"Reference implementation mismatch for file {self.data.filename}. "
                    f"Expected content in target workspace does not match reference_implementation. "
                    f"This indicates a dataset construction error."
                )

            self.logger.info(f"Reference implementation validation passed for {self.data.filename}")

        except Exception as e:
            self.logger.error(f"Reference implementation validation failed: {e}")
            raise

    async def create_user_prompt(self) -> str:
        """Create user prompt for proof engineering task."""
        import asyncio
        from .prompt import LEAN_PROOF_ENGINEERING_USER_PROMPT
        from ape.toolkits.code.lean.provider import LeanCodeToolsProvider

        is_new_file = not self.data.original_code or not self.data.original_code.strip()
        task_config: LeanProofEngineeringConfig = self.config.task_config
        original_code_section = ""

        if is_new_file:
            base_strategy = """This is a new file creation task. No original implementation is provided.

**Independent Implementation Requirement:**
- Implement all required functionality from scratch
- Do NOT attempt to use or depend on files in target workspace that may be blocked/inaccessible
- If certain library files cannot be accessed, implement the necessary functionality independently
- Blocked files are intentionally inaccessible - they are often reference implementations you must NOT use"""
        else:
            original_path = self.scratch_original_path.relative_to(self.scratch_workspace.path)

            if task_config.include_original_code_in_prompt:
                # Format and include original code content (CPU-intensive, offload to thread pool)
                formatted_code = await asyncio.to_thread(
                    LeanCodeToolsProvider.display_content,
                    content=self.data.original_code,
                    display_mode="full",
                    body_handling=task_config.format_body_handling
                )

                original_code_section = f"""
<original_implementation>
{formatted_code}
</original_implementation>
"""

                base_strategy = f"""This is a file modification task. **IMPORTANT: The original implementation shown above is an OLD VERSION of the file that requires refactoring/improvement according to the task description.**

**Critical Requirements:**
- The original implementation is provided COMPLETE above and corresponds to a read-only file at `scratch/{original_path}`
- This is an OLD VERSION - you MUST perform the refactoring/improvements specified in the task description
- Dependencies and code patterns used in the original may be OUTDATED - you MUST update them to current standards and fix any deprecated imports, types, or APIs
- Your submission is ONLY valid if:
  1. You have completed ALL the refactoring requirements specified in the task description
  2. The code passes all verification (syntax and semantic validation)
  3. All outdated dependencies and code patterns have been updated
- **IMPORTANT**: Make INCREMENTAL changes targeting only the parts that need modification. Avoid rewriting the entire file unless most of the content needs to change. This prevents duplicating large amounts of unchanged content.

**Independent Implementation Requirement:**
- Do NOT attempt to use or depend on files in target workspace that may be blocked/inaccessible
- If certain library files cannot be accessed during verification, implement the necessary functionality independently within your solution
- Blocked files are intentionally inaccessible - they are often reference implementations you must NOT use
- Your implementation should be self-contained and not rely on accessing blocked dependencies"""
            else:
                base_strategy = f"""This is a file modification task. **IMPORTANT: The original file is an OLD VERSION that requires refactoring/improvement according to the task description.**

**Critical Requirements:**
- The original file is available at `scratch/{original_path}` (read-only, cannot be modified in-place)
- This is an OLD VERSION - you MUST perform the refactoring/improvements specified in the task description
- Dependencies and code patterns used in the original may be OUTDATED - you MUST update them to current standards and fix any deprecated imports, types, or APIs
- Your submission is ONLY valid if:
  1. You have completed ALL the refactoring requirements specified in the task description
  2. The code passes all verification (syntax and semantic validation)
  3. All outdated dependencies and code patterns have been updated
- **IMPORTANT**: Make INCREMENTAL changes targeting only the parts that need modification. Avoid rewriting the entire file unless most of the content needs to change. This prevents duplicating large amounts of unchanged content.

**Independent Implementation Requirement:**
- Do NOT attempt to use or depend on files in target workspace that may be blocked/inaccessible
- If certain library files cannot be accessed during verification, implement the necessary functionality independently within your solution
- Blocked files are intentionally inaccessible - they are often reference implementations you must NOT use
- Your implementation should be self-contained and not rely on accessing blocked dependencies"""

        # Build file locations
        if is_new_file:
            if self.data.filename:
                file_locations = f"**Create:** `scratch/{self.data.filename}`"
            else:
                file_locations = "**Create:** Your solution in `scratch/` (choose appropriate filename)"
        else:
            original_path = self.scratch_original_path.relative_to(self.scratch_workspace.path)
            if self.data.filename:
                file_locations = f"**Input:** `scratch/{original_path}` (read-only)\n**Output:** Create improved version at `scratch/{self.data.filename}`"
            else:
                file_locations = f"**Input:** `scratch/{original_path}` (read-only)\n**Output:** Create improved version in `scratch/` (choose filename)"

        # Get submit tool name from config (mcp_server_name already includes trailing __)
        submit_tool_name = f"{self.config.mcp_server_name}submit_result"

        return LEAN_PROOF_ENGINEERING_USER_PROMPT.format(
            task_description=self.data.task_description,
            original_code_section=original_code_section,
            implementation_strategy_content=base_strategy,
            file_locations=file_locations,
            submit_tool_name=submit_tool_name
        )
    
    async def register_task_tools(self, mcp) -> None:
        """Register proof engineering task-specific tools."""
        from typing import Annotated
        from pydantic import Field
        
        @mcp.tool(
            description=(
                "Submit your final solution for proof engineering tasks. Provide either code content directly "
                "or file path to your solution. This will trigger evaluation and may end the conversation.\n\n"
                "**CRITICAL: You MUST use this tool to submit your result. Providing results only in text response is INVALID and will NOT be accepted.**"
            )
        )
        async def submit_result(
            final_code_content: Annotated[Optional[str], Field(
                description="The final refactored/improved Lean code content"
            )] = None,
            final_code_file_path: Annotated[Optional[str], Field(
                description="File path with workspace prefix. Example: 'scratch/solution.lean'"
            )] = None,
            message: Annotated[str, Field(
                description="Optional message describing your solution approach (optional).",
                default=""
            )] = ""
        ) -> Dict[str, Any]:
            """Submit final result for proof engineering evaluation and potential termination."""
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

                # Check if submitted file is read-only
                if final_code_file_path:
                    file_path_str = final_code_file_path.replace("scratch/", "").replace("target/", "")

                    if self.scratch_original_path:
                        submitted_path = self.scratch_workspace.path / file_path_str
                        if submitted_path.resolve() == self.scratch_original_path.resolve():
                            error_result = EvaluationResult(
                                success=False,
                                score=0.0,
                                message=f"Cannot submit read-only original file: {file_path_str}. You must create or modify a different file."
                            )
                            return {
                                "evaluation_result": error_result,
                                "message": "Evaluation failed or not ready"
                            }

                    # Check if attempting to submit target workspace file
                    if final_code_file_path.startswith("target/"):
                        error_result = EvaluationResult(
                            success=False,
                            score=0.0,
                            message=f"Cannot submit target workspace file: {file_path_str}. Target workspace is read-only. You must submit files from scratch workspace."
                        )
                        return {
                            "evaluation_result": error_result,
                            "message": "Evaluation failed or not ready"
                        }
                
                evaluation_result = await self._evaluate_proof_engineering(final_code)
                should_terminate = self.should_terminate(evaluation_result)

                if should_terminate and self.termination_callback:
                    try:
                        task_result = self.create_result(
                            success=evaluation_result.success,
                            score=evaluation_result.score,
                            improved_code=final_code,
                            evaluation_result=evaluation_result
                        )
                        await self.termination_callback(task_result)
                    except Exception as e:
                        self.logger.warning(f"Warning: Failed to trigger termination: {e}")
                
                self.logger.info(f"Tool submit_result: execution completed successfully (success={evaluation_result.success}, score={evaluation_result.score})")
                return {
                    "evaluation_result": evaluation_result,
                    "message": "Result submitted and evaluated"
                }
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Lean proof engineering evaluation failed: {traceback.format_exc()}")
                evaluation_result = EvaluationResult(
                    success=False,
                    score=0.0,
                    message=traceback.format_exc()
                )
                return {
                    "evaluation_result": evaluation_result,
                    "message": "Evaluation failed or not ready"
                }
    
    async def _evaluate_proof_engineering(self, final_code: str) -> EvaluationResult:
        """Evaluate proof engineering submission."""
        from ape.tasks.lean_tasks.formal_math.judgment.task import lean_semantic_evaluation
        import time

        try:
            pe_config: LeanProofEngineeringConfig = self.config.task_config
            syntax_result = None

            # Syntax validation (optional based on config)
            if not pe_config.skip_syntax_validation:
                from ape.toolkits.execute.lean.tools import LeanVerifyToolsProvider
                if not self.target_workspace or not self.scratch_workspace:
                    raise RuntimeError("Workspaces not initialized for Lean verification")
                lean_tool = LeanVerifyToolsProvider(
                    task=self,
                    config=self.config,
                    logger=self.logger
                )

                syntax_result = await lean_tool.execute(code=final_code)

                if not syntax_result["success"]:
                    error_messages = []
                    for err in syntax_result.get("errors", []):
                        error_messages.append(err["data"])

                    warning_messages = []
                    for warn in syntax_result.get("warnings", []):
                        warning_messages.append(warn["data"])

                    message_parts = ["Lean verification failed."]
                    if error_messages:
                        message_parts.append(f"\nErrors:\n" + "\n".join(f"- {msg}" for msg in error_messages))
                    if warning_messages:
                        message_parts.append(f"\nWarnings:\n" + "\n".join(f"- {msg}" for msg in warning_messages))

                    return EvaluationResult(
                        success=False,
                        score=0.0,
                        message="\n".join(message_parts),
                        metrics=None
                    )
            else:
                syntax_result = {"success": True, "message": "Syntax validation skipped"}

            # Semantic validation (if enabled)
            semantic_result = None
            if pe_config.semantic_validation.enabled:
                
                from ape.tasks.lean_tasks.formal_math.judgment.task import lean_semantic_evaluation
                semantic_result = await lean_semantic_evaluation(
                    final_code=final_code,
                    original_code=self.data.original_code,
                    task_description=self.data.task_description,
                    semantic_config=pe_config.semantic_validation,
                    base_config=self.config,
                    reference_implementation=self.data.reference_implementation,
                    filename=self.data.filename,
                    target_workspace=self.data.target_workspace,
                    gold_diff=self.data.gold_diff,
                    logger=self.logger,
                    parent_attempt_path=self.attempt_path
                )

            # Compute final result
            if semantic_result:
                if not semantic_result['success']:
                    return EvaluationResult(
                        success=False,
                        score=0.0,
                        message=f"Semantic validation system failed: {semantic_result['message']}"
                    )

                judgment_conclusion = semantic_result['judgment_conclusion']
                semantic_positive = judgment_conclusion == "positive"

                if not semantic_positive:
                    # Extract negative assessments (poor/unacceptable dimensions)
                    aggregated_evals = semantic_result.get('aggregated_evaluations', {})
                    judge_results = aggregated_evals.get('judge_results', [])
                    negative_feedback = []

                    for judge_result in judge_results:
                        if not judge_result.success:
                            continue

                        judgment_data = judge_result.judgment_data
                        dimensions = [
                            ('semantic_correctness', 'Semantic Correctness'),
                            ('requirement_alignment', 'Requirement Alignment'),
                            ('scope_control', 'Scope Control')
                        ]

                        for dim_key, dim_name in dimensions:
                            rating = judgment_data.get(f'{dim_key}_rating', '')
                            if rating in ['poor', 'unacceptable']:
                                assessment = judgment_data.get(f'{dim_key}_assessment', '')
                                negative_feedback.append(f"**{dim_name}** ({rating}):\n{assessment}")

                    if negative_feedback:
                        unique_feedback = list(dict.fromkeys(negative_feedback))
                        message = "Semantic validation failed. Issues identified:\n\n" + "\n\n".join(unique_feedback)
                    else:
                        message = f"Semantic validation failed: judgment was '{judgment_conclusion}' but no critical issues (poor/unacceptable) were identified."

                    return EvaluationResult(
                        success=True,
                        score=0.0,
                        message=message,
                        metrics=None,
                        nested_token_usage=semantic_result.get('nested_token_usage')
                    )
                else:
                    return EvaluationResult(
                        success=True,
                        score=1.0,
                        message="Proof engineering evaluation completed successfully",
                        metrics=None,
                        nested_token_usage=semantic_result.get('nested_token_usage')
                    )
            else:
                return EvaluationResult(
                    success=True,
                    score=1.0,
                    message="Proof engineering evaluation completed successfully (syntax only)" if not pe_config.skip_syntax_validation else "Proof engineering evaluation completed successfully (no validation)",
                    metrics=None
                )
            
        except Exception:
            if self.logger:
                self.logger.error(f"Lean proof engineering execution failed: {traceback.format_exc()}")
            return EvaluationResult(
                success=False,
                score=0.0,
                message=traceback.format_exc()
            )

    def create_result(
        self,
        success: bool,
        score: float,
        improved_code: str,
        evaluation_result: Optional['EvaluationResult'] = None,
        **kwargs
    ) -> LeanProofEngineeringResult:
        """Create Lean proof engineering task result with business data only."""
        if "nested_token_usage" not in kwargs and evaluation_result:
            kwargs["nested_token_usage"] = evaluation_result.nested_token_usage
        return LeanProofEngineeringResult(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=success,
            score=score,
            improved_code=improved_code,
            **kwargs
        )

    @classmethod
    def is_best_result(cls, result: 'BaseTaskResult') -> bool:
        """Proof engineering task: syntax validation success is best result."""
        return result.success and result.score == 1.0


register_task("lean_proof_engineering", LeanProofEngineeringTask)
