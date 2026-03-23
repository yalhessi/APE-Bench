"""
APE Bench Instruction Generation Task

Generalized for any formal language project.
Uses plain source workspaces instead of compiled workspaces.
"""

from pathlib import Path, PurePosixPath
from typing import Dict, Any, Optional, TYPE_CHECKING, List, Tuple, Union, Literal
import traceback
import asyncio
from pydantic import Field, ValidationError, field_validator

from ape.tasks.base import BaseTask, BaseTaskData, BaseTaskConfig, register_task, BaseTaskResult, EvaluationResult, SemanticValidationConfig
from ape.tasks.models import WorkspaceInfo, parse_workspace_info
from ape.tasks.workspace_sources import resolve_plain_source_workspace
from .models import Exercise

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class InstructionGenerationData(BaseTaskData):
    """Task data for instruction generation.

    Does NOT inherit from BaseLeanTaskData - uses plain source workspaces.
    """
    task_type: Literal["instruction_generation"] = Field(
        default="instruction_generation",
        description="Task type identifier"
    )

    # Workspace specification (for plain git worktree, not compiled)
    target_workspace: WorkspaceInfo = Field(
        ...,
        description="Target workspace specification"
    )

    # File information
    file_path_before: Optional[Path] = None
    file_path_after: Optional[Path] = None
    content_before: Optional[str] = None
    content_after: Optional[str] = None
    gold_diff: str

    # Additional metadata
    parent_commit_hash: Optional[str] = None
    author: Optional[str] = None
    message: Optional[str] = None
    date: Optional[str] = None

    # Language
    language: str = Field(default="lean", description="Formal language")

    # Statistics
    diff_lines: int = 0
    change_type: str = "modified"

    @field_validator("target_workspace", mode="before")
    @classmethod
    def validate_target_workspace(cls, value: Any) -> WorkspaceInfo:
        """Preserve language-specific workspace metadata during parsing."""
        return parse_workspace_info(value)


class InstructionGenerationConfig(BaseTaskConfig):
    """Task configuration with read-only tools only."""

    # Task validation settings (semantic validation of generated tasks)
    validate_generated_task: bool = Field(
        default=False,
        description="Whether to run semantic validation on generated PE task using ground truth solution"
    )

    # Tool configuration - only read-only tools
    disabled_tools: list[str] = [
        "file_write", "file_edit", "file_multi_edit",
        "python_run_code", "lean_verify", "isabelle_verify",
        "lean_retrieve"
    ]

    enabled_tools: Optional[list[str]] = [
        "file_read", "file_search", "content_search",
        "file_diff"
    ]

    # Code formatting configuration
    format_display_mode: str = "line_spans"  # "full" | "line_spans"
    format_context_lines: int = 10

    # Semantic validation configuration (for validate_generated_task)
    semantic_validation: SemanticValidationConfig = Field(
        default_factory=lambda: SemanticValidationConfig(
            enabled=True,
            judge_method="static",
            static_semantic_samples=1,
            agentic_semantic_samples=1,
            scaffold_type="ape_agent",
            max_turns=10,
            judge_mode="generated_only"
        ),
        description="Semantic validation configuration for PE task verification"
    )


class InstructionGenerationTaskResult(BaseTaskResult):
    """Task result with generated exercise data."""

    # Generated exercise data
    exercise_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Generated exercise data including objectives and implementation_approach"
    )

def _build_task_description(exercise: Exercise) -> str:
    """Build task description for downstream dataset consumption."""
    if exercise.objectives:
        return f"{exercise.title}:\n\n{exercise.objectives}"
    return exercise.title


class InstructionGenerationTask(BaseTask):
    """Instruction generation task for formal language projects.

    Uses BaseSourceManager for plain git worktrees (no compilation required).
    """

    task_type = "instruction_generation"
    data_class = InstructionGenerationData
    task_config_class = InstructionGenerationConfig
    task_result_class = InstructionGenerationTaskResult

    def __init__(self, data: InstructionGenerationData, config: 'BaseScaffoldConfig'):
        """Initialize instruction generation task"""
        super().__init__(data, config)

    @classmethod
    async def setup_attempt(
        cls,
        data: 'InstructionGenerationData',
        config: 'BaseScaffoldConfig',
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
        logger: Optional['logging.LoggerAdapter'] = None
    ) -> tuple[Path, WorkspaceInfo, Optional[WorkspaceInfo], Optional[List[WorkspaceInfo]]]:
        """Setup attempt with a plain source workspace (no compilation).

        Uses BaseSourceManager.get_workspace() instead of RestoreManager.
        """
        # Call parent to create basic structure
        attempt_path, scratch_workspace, _, _ = await super(InstructionGenerationTask, cls).setup_attempt(
            data, config, orchestrator_id, attempt_path, logger
        )

        workspaces_dir = attempt_path / config.workspaces_dir_name

        # Setup target workspace using BaseSourceManager (plain worktree)
        target_workspace = await cls._setup_plain_workspace_symlink(
            workspace_spec=data.target_workspace,
            link_path=workspaces_dir / "target",
            config=config,
            logger=logger
        )

        return attempt_path, scratch_workspace, target_workspace, None

    @classmethod
    async def _setup_plain_workspace_symlink(
        cls,
        workspace_spec: WorkspaceInfo,
        link_path: Path,
        config: 'BaseScaffoldConfig',
        logger: Optional['logging.LoggerAdapter'] = None
    ) -> WorkspaceInfo:
        """Setup workspace symlink using a plain source workspace."""
        if link_path.exists() and link_path.is_dir() and not link_path.is_symlink():
            if logger:
                logger.info(
                    f"Workspace {workspace_spec.name} already exists as directory at {link_path}, "
                    f"using existing (IsolatedLocalRuntime mode)"
                )
            read_only_patterns = workspace_spec.read_only_path_patterns or ["**/*"]
            return workspace_spec.model_copy(update={
                "path": link_path,
                "read_only_path_patterns": read_only_patterns
            })

        del config  # Plain source resolution only depends on workspace source spec.
        actual_workspace_path = await resolve_plain_source_workspace(
            workspace_spec=workspace_spec,
            logger=logger,
        )

        # Create symlink
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        link_path.symlink_to(actual_workspace_path, target_is_directory=True)

        # Return WorkspaceInfo with symlink path and read-only patterns
        read_only_patterns = workspace_spec.read_only_path_patterns or ["**/*"]

        return workspace_spec.model_copy(update={
            "path": link_path,
            "read_only_path_patterns": read_only_patterns
        })

    def _convert_diff_to_line_spans(self, diff_text: str) -> List[Tuple[int, int]]:
        """Convert git diff to line spans."""
        if not diff_text:
            return []

        import re
        ranges = []
        hunk_pattern = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@', re.MULTILINE)

        for match in hunk_pattern.finditer(diff_text):
            start_old = int(match.group(1))
            length_old = int(match.group(2)) if match.group(2) else 1
            end_old = start_old + length_old - 1
            ranges.append((start_old, end_old))

        return ranges

    def _get_language_handler(self, file_path: Optional[Path]):
        """Get formatter for file based on extension."""
        if not file_path:
            return None

        from ape.toolkits.code.base_provider import LANGUAGE_PROVIDER_REGISTRY

        # Get extension from file path
        ext = file_path.suffix if isinstance(file_path, Path) else Path(file_path).suffix
        if not ext:
            return None

        provider_class = LANGUAGE_PROVIDER_REGISTRY.get(ext)
        if provider_class:
            # All providers are now classes with static methods, no need to instantiate
            return provider_class
        return None

    @classmethod
    def create_data_from_dict(cls, data: Dict[str, Any]) -> InstructionGenerationData:
        """Create task data from data dictionary."""
        if 'target_workspace' not in data:
            raise ValueError("InstructionGenerationData requires 'target_workspace'")

        if 'task_id' not in data:
            workspace_spec = data['target_workspace']
            commit_hash = parse_workspace_info(workspace_spec).commit_hash
            if not commit_hash:
                raise ValueError("A git-backed target_workspace source is required for task_id generation")
            file_path = data.get('file_path_after') or data.get('file_path_before', 'unknown')
            data['task_id'] = f"instruction_{commit_hash[:8]}_{Path(file_path).stem if isinstance(file_path, (Path, str)) else 'unknown'}"

        return InstructionGenerationData.model_validate(data)

    async def create_user_prompt(self) -> str:
        """Create user prompt."""
        from .prompt import INSTRUCTION_GENERATION_USER_PROMPT

        task_config: InstructionGenerationConfig = self.config.task_config

        # Prepare file content section
        line_spans = None
        if task_config.format_display_mode == "line_spans":
            line_spans = self._convert_diff_to_line_spans(self.data.gold_diff)

        file_content_section = ""
        if task_config.format_display_mode == "line_spans":
            file_content_section = f"\nNote: File content is displayed in line-spans mode, showing only diff-related lines with {task_config.format_context_lines} lines of context.\n"
        else:
            file_content_section = "\nNote: File content is displayed in full mode.\n"

        if self.data.content_before:
            # Use formatter if available
            formatter = self._get_language_handler(self.data.file_path_after)
            if formatter:
                # All formatters now support unified display_content interface
                formatter_kwargs = {
                    "content": self.data.content_before,
                    "add_line_numbers": True,
                    "display_mode": task_config.format_display_mode,
                    "context_lines": task_config.format_context_lines
                }

                if task_config.format_display_mode == "line_spans" and line_spans:
                    formatter_kwargs["line_spans"] = line_spans

                # For Lean files, add body_handling (omit proofs outside spans)
                if self.data.file_path_before and self.data.file_path_before.suffix == '.lean':
                    formatter_kwargs["body_handling"] = "omit_outside_spans"

                content_display = await asyncio.to_thread(
                    formatter.display_content,
                    **formatter_kwargs
                )
            else:
                # No formatter - show complete content with line numbers
                lines = self.data.content_before.splitlines()
                content_display = "\n".join(f"{i+1:6d}|{line}" for i, line in enumerate(lines))

            file_content_section += f"\n<original_file name=\"{self.data.file_path_before}\">\n{content_display}\n</original_file>\n"
        else:
            file_content_section += f"\n<original_file>\nEmpty file (new file creation)\n</original_file>\n"

        assert self.data.gold_diff, "gold_diff is required"
        file_content_section += f"<diff>\n{self.data.gold_diff}\n</diff>\n"

        return INSTRUCTION_GENERATION_USER_PROMPT.format(
            file_content_section=file_content_section
        )

    def should_terminate(self, evaluation_result: EvaluationResult = None) -> bool:
        """Terminate when result is successfully submitted."""
        if evaluation_result is None:
            return False
        return evaluation_result.score == 1.0

    async def register_task_tools(self, mcp) -> None:
        """Register submission tool."""
        from typing import Annotated

        @mcp.tool(
            description="""Submit a comprehensive formalization task for the file modification.

First assess if this modification is substantial enough for a task:
- If difficulty is "very easy" AND task_nature is "superficial", provide only: title, difficulty, task_nature, reject_reason
- Otherwise provide all fields to create a substantial task

For substantial tasks:
- title: Task title (5-20 words describing what to do)
- task_category: One of [feature, bug fix, refactor, chore, testing, documentation, formatting]
- formalization_aspect: One of [new_content, proof_technique, abstraction, structural_design, technical_implementation]
- difficulty: One of [very easy, easy, medium, hard, very hard]
- task_nature: One of [substantial, superficial]
- context: Background explaining current state and limitations
- objectives: Specific, concrete goals to achieve
- implementation_approach: Detailed description of how objectives are achieved (problem analysis, solution strategy, implementation details)
- significance: Why achieving these objectives is beneficial

For rejected tasks (very easy + superficial):
- title: Brief description of what was changed
- difficulty: "very easy"
- task_nature: "superficial"
- reject_reason: Brief explanation of why this is too trivial

**CRITICAL: You MUST use this tool to submit your task. Text-only responses are NOT accepted.**"""
        )
        async def submit_result(
            title: Annotated[str, Field(description="Task title or brief change description")],
            difficulty: Annotated[str, Field(description="One of: very easy, easy, medium, hard, very hard")],
            task_nature: Annotated[str, Field(description="One of: substantial, superficial")],
            reject_reason: Annotated[Optional[str], Field(default=None, description="Required if difficulty=very easy AND task_nature=superficial")] = None,
            task_category: Annotated[Optional[str], Field(default=None, description="One of: feature, bug fix, refactor, chore, testing, documentation, formatting")] = None,
            formalization_aspect: Annotated[Optional[str], Field(default=None, description="One of: new_content, proof_technique, abstraction, structural_design, technical_implementation")] = None,
            context: Annotated[Optional[str], Field(default=None, description="Background explaining current state and limitations")] = None,
            objectives: Annotated[Optional[str], Field(default=None, description="Specific, concrete goals to achieve")] = None,
            implementation_approach: Annotated[Optional[str], Field(default=None, description="Detailed description of how objectives are achieved: problem analysis, solution strategy, and implementation details")] = None,
            significance: Annotated[Optional[str], Field(default=None, description="Why achieving these objectives is beneficial")] = None
        ) -> Dict[str, Any]:
            """Submit exercise with validation."""

            self.logger.info("Tool submit_result: execution started")
            try:
                # Check if this is a rejection case
                is_rejected = (difficulty == "very easy" and task_nature == "superficial")

                if is_rejected:
                    if not reject_reason:
                        return {
                            "success": False,
                            "error": "reject_reason is required when difficulty=very easy AND task_nature=superficial",
                            "guidance": "Please provide a brief explanation of why this modification is too trivial.",
                            "message": "Evaluation failed or not ready"
                        }

                    self.logger.info(f"Task rejected: {reject_reason}")

                    task_result = self.create_result(
                        success=True,
                        score=0.0,
                        exercise_data={"rejected": True, "reject_reason": reject_reason, "title": title}
                    )

                    await self.signal_termination(task_result)

                    return {
                        "success": True,
                        "message": f"Task rejected: {reject_reason}"
                    }

                # For substantial tasks, validate and create exercise
                try:
                    exercise = Exercise(
                        title=title,
                        task_category=task_category,
                        formalization_aspect=formalization_aspect,
                        difficulty=difficulty,
                        task_nature=task_nature,
                        context=context,
                        objectives=objectives,
                        implementation_approach=implementation_approach,
                        significance=significance,
                        file_path=self.data.file_path_after or self.data.file_path_before,
                        total_diff_lines=self.data.diff_lines
                    )
                except ValidationError as e:
                    errors = [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                              for err in e.errors()]
                    return {
                        "success": False,
                        "error": "Exercise validation failed:\n" + "\n".join(errors),
                        "guidance": "Please ensure all required fields are provided with valid values.",
                        "message": "Evaluation failed or not ready"
                    }

                # Build exercise data for result
                # Use path as-is (relative to repo root, including default_target prefix if present)
                file_path = self.data.file_path_after or self.data.file_path_before
                file_path_str = str(file_path) if file_path else None

                target_workspace_data = (
                    self.data.target_workspace.model_dump(mode="json", exclude={"path"})
                    if self.data.target_workspace
                    else {"name": "target"}
                )
                if not target_workspace_data.get("read_only_path_patterns"):
                    target_workspace_data["read_only_path_patterns"] = ["**/*"]

                exercise_data = {
                    "title": exercise.title,
                    "task_category": exercise.task_category,
                    "formalization_aspect": exercise.formalization_aspect,
                    "difficulty": exercise.difficulty,
                    "task_nature": exercise.task_nature,
                    "context": exercise.context,
                    "objectives": exercise.objectives,
                    "implementation_approach": exercise.implementation_approach,
                    "significance": exercise.significance,
                    "file_path": file_path_str,
                    "total_diff_lines": exercise.total_diff_lines,
                    # Include original data for SFT
                    "original_code": self.data.content_before,
                    "modified_code": self.data.content_after,
                    "gold_diff": self.data.gold_diff,
                    "target_workspace": target_workspace_data,
                    "language": self.data.language,
                    "commit_message": self.data.message,
                    "commit_author": self.data.author,
                    "commit_date": self.data.date
                }
                exercise_data["task_description"] = _build_task_description(exercise)

                self.logger.info("Task validated successfully")

                # Check if generated task validation is requested
                task_config = self.config.task_config
                if not isinstance(task_config, InstructionGenerationConfig):
                    raise TypeError(f"Expected InstructionGenerationConfig, got {type(task_config)}")

                if task_config.validate_generated_task:
                    self.logger.info("Task validation requested, running semantic validation...")
                    # Run semantic validation on generated task data
                    validation_result = await self._run_task_validation(exercise, exercise_data)

                    if not validation_result['success']:
                        return {
                            "success": False,
                            "error": validation_result.get('error', 'Validation failed'),
                            "guidance": validation_result.get('guidance', 'Please revise the task description.'),
                            "message": "Evaluation failed or not ready"
                        }

                task_result = self.create_result(
                    success=True,
                    score=1.0,
                    exercise_data=exercise_data
                )

                await self.signal_termination(task_result)

                self.logger.info("Tool submit_result: execution completed successfully")
                return {
                    "success": True,
                    "message": "Task created successfully!"
                }

            except Exception as e:
                self.logger.error(f"Failed to process submission: {traceback.format_exc()}")
                return {
                    "success": False,
                    "error": str(e),
                    "guidance": "An unexpected error occurred. Please try again.",
                    "message": "Evaluation failed or not ready"
                }

    async def _run_task_validation(self, exercise: Exercise, exercise_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run semantic validation on generated task data.

        Validates that the generated task description aligns with the ground truth solution
        using semantic evaluation (LLM-based judgment).

        Returns:
            Dict with 'success' and optional 'error', 'guidance'
        """
        try:
            # Get executor for the language
            from ape.toolkits.registry import get_executor_class

            ext_map = {
                'lean': '.lean',
                'isabelle': '.thy',
                'coq': '.v'
            }
            ext = ext_map.get(self.data.language)
            if not ext:
                return {
                    "success": False,
                    "error": f"Unsupported language for semantic validation: {self.data.language}",
                    "guidance": "Semantic validation is only supported for lean, isabelle, and coq."
                }

            executor_class = get_executor_class(ext)
            if not executor_class:
                self.logger.warning(f"No executor found for {self.data.language}, skipping semantic validation")
                return {"success": True}  # Skip validation if no executor

            # For Lean, use semantic evaluation with LLM judgment
            # For other languages, semantic validation is not yet implemented
            if self.data.language == 'lean':
                from ape.tasks.lean_tasks.formal_math.judgment.task import lean_semantic_evaluation

                # Get semantic validation config from task config
                task_config: InstructionGenerationConfig = self.config.task_config
                semantic_config = task_config.semantic_validation

                # Run semantic evaluation
                task_description = _build_task_description(exercise)
                semantic_result = await lean_semantic_evaluation(
                    final_code=self.data.content_after,
                    original_code=self.data.content_before,
                    task_description=task_description,
                    semantic_config=semantic_config,
                    base_config=self.config,
                    reference_implementation=self.data.content_after,
                    filename=Path(exercise_data.get('file_path', 'unknown.lean')),
                    target_workspace=self.data.target_workspace,
                    gold_diff=self.data.gold_diff,
                    logger=self.logger,
                    parent_attempt_path=self.attempt_path
                )

                if not semantic_result['success']:
                    return {
                        "success": False,
                        "error": f"Semantic validation failed: {semantic_result['message']}",
                        "guidance": "The ground truth code does not pass semantic validation. Please check the task description."
                    }

                judgment_conclusion = semantic_result.get('judgment_conclusion')
                if judgment_conclusion != 'positive':
                    metrics = semantic_result.get('aggregated_evaluations', {})
                    guidance_parts = ["Task doesn't align with ground truth solution."]

                    semantic_rating = metrics.get('semantic_correctness_rating', '')
                    requirement_rating = metrics.get('requirement_alignment_rating', '')

                    if semantic_rating in ['poor', 'unacceptable']:
                        assessment = metrics.get('semantic_correctness_assessment', '')
                        if assessment:
                            guidance_parts.append(f"Semantic Issue: {assessment[:200]}...")

                    if requirement_rating in ['poor', 'unacceptable']:
                        assessment = metrics.get('requirement_alignment_assessment', '')
                        if assessment:
                            guidance_parts.append(f"Requirement Issue: {assessment[:200]}...")

                    if len(guidance_parts) == 1:
                        guidance_parts.append("Review the diff and ensure task description captures all contributions.")

                    return {
                        "success": False,
                        "error": "Task description does not match ground truth",
                        "guidance": " ".join(guidance_parts)
                    }
            else:
                # For non-Lean languages, semantic validation is not yet implemented
                self.logger.info(f"Semantic validation for {self.data.language} not fully implemented, skipping")

            return {"success": True}

        except Exception as e:
            self.logger.error(f"Semantic validation error: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Semantic validation system error: {str(e)}",
                "guidance": "An unexpected error occurred during semantic validation."
            }

    def create_result(
        self,
        success: bool,
        score: float,
        exercise_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> InstructionGenerationTaskResult:
        """Create task result."""
        return InstructionGenerationTaskResult(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=success,
            score=score,
            exercise_data=exercise_data,
            error=error
        )


# Register task
register_task("instruction_generation", InstructionGenerationTask)
