"""
Lean Judgment Task Module.

Provides task definitions for Lean code judgment, including
data models, task configuration, and evaluation logic with
three-dimensional assessment (semantic correctness, requirement alignment, scope control).
"""

import difflib
from typing import Dict, Any, Callable, Optional, List, TYPE_CHECKING, Literal, Tuple
import traceback
from pathlib import Path
from datetime import datetime
from pydantic import Field, BaseModel, ConfigDict, field_validator
from ape.tasks.base import BaseTaskConfig, register_task, BaseTaskData, BaseTaskResult, EvaluationResult
from ape.tasks.models import WorkspaceInfo
from ape.tasks.lean_tasks.base import BaseLeanTask
from ape.tasks.lean_tasks.formal_math.proof_engineering.task import SemanticValidationConfig
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class LeanJudgmentConfig(BaseTaskConfig):
    """Configuration for Lean code judgment tasks."""
    judge_mode: str = "with_ground_truth"
    format_display_mode: str = "line_spans"
    format_body_handling: str = "keep_all"
    format_context_lines: int = 10
    enabled_tools: Optional[List[str]] = [
        "bash_execute",
        "file_read",
        # "file_search",
        # "content_search",
        # "file_write",
        # "file_edit",
        # "file_multi_edit",
        "lean_retrieve",
        # "lean_verify",
        "get_lean_goal",
        "code_hover",
        "code_goto",
        "code_references",
    ]


class Judgment(BaseModel):
    """Judgment evaluation result structure with three dimensions."""

    semantic_correctness_assessment: str = Field(
        ..., description="Detailed assessment conclusion for semantic correctness with specific evidence"
    )
    semantic_correctness_rating: Literal['excellent', 'good', 'acceptable', 'poor', 'unacceptable'] = Field(
        ..., description="Rating of mathematical/logical correctness and semantic soundness"
    )

    requirement_alignment_assessment: str = Field(
        ..., description="Detailed assessment conclusion for requirement alignment with specific evidence"
    )
    requirement_alignment_rating: Literal['excellent', 'good', 'acceptable', 'poor', 'unacceptable'] = Field(
        ..., description="Rating of how well the solution fulfills task requirements"
    )

    scope_control_assessment: str = Field(
        ..., description="Detailed assessment conclusion for scope control with specific evidence"
    )
    scope_control_rating: Literal['excellent', 'good', 'acceptable', 'poor', 'unacceptable'] = Field(
        ..., description="Rating of how well the solution controls change scope and preserves unrelated code"
    )

    overall_judgment: Literal['accept', 'reject'] = Field(
        ..., description="Overall judgment: accept (solution is adequate) or reject (solution has critical issues)"
    )

    @field_validator('semantic_correctness_rating', 'requirement_alignment_rating', 'scope_control_rating')
    @classmethod
    def validate_rating_values(cls, v: str) -> str:
        """Validate rating value."""
        valid_values = ['excellent', 'good', 'acceptable', 'poor', 'unacceptable']
        if v not in valid_values:
            raise ValueError(f"Rating must be one of {valid_values}, got '{v}'")
        return v

    @field_validator('overall_judgment')
    @classmethod
    def validate_overall_judgment(cls, v: str) -> str:
        """Validate overall judgment value."""
        valid_values = ['accept', 'reject']
        if v not in valid_values:
            raise ValueError(f"Overall judgment must be one of {valid_values}, got '{v}'")
        return v


class LeanJudgmentData(BaseTaskData):
    """Data model for Lean code judgment tasks."""
    task_type: Literal["lean_judgment"] = Field(
        default="lean_judgment",
        description="Task type identifier"
    )
    target_code: str = Field(..., description="Target code to evaluate")
    original_code: Optional[str] = Field(default=None, description="Original code (None for new files)")
    task_description: str = Field(..., description="Task description")
    reference_implementation: Optional[str] = Field(default=None, description="Reference implementation")
    gold_diff: Optional[str] = Field(default=None, description="Reference diff")
    filename: Optional[Path] = Field(default=None, description="Filename")

    target_workspace: WorkspaceInfo = Field(
        ...,
        description="Target workspace specification"
    )
    reference_workspaces: Optional[List[WorkspaceInfo]] = Field(
        default=None,
        description="Optional reference workspaces"
    )

    judgement_ground_truth: Optional[bool] = Field(default=None, description="Ground truth for accuracy evaluation")


class LeanJudgmentResult(BaseTaskResult):
    """Result model for Lean code judgment tasks."""
    model_config = ConfigDict()

    judgment_conclusion: str = Field(..., description="Judgment conclusion: positive, negative, neutral")
    judgment_data: Dict[str, Any] = Field(..., description="Detailed judgment evaluation data")

    def model_post_init(self, __context) -> None:
        """Post-initialization: deserialize nested judge_results if they are dicts."""
        super().model_post_init(__context)

        # Handle deserialization of nested judge_results
        if 'judge_results' in self.judgment_data:
            judge_results = self.judgment_data['judge_results']
            if judge_results and isinstance(judge_results, list):
                deserialized_results = []
                for item in judge_results:
                    if isinstance(item, dict):
                        # Deserialize dict back to LeanJudgmentResult
                        try:
                            deserialized_results.append(LeanJudgmentResult.model_validate(item))
                        except Exception:
                            # If deserialization fails, keep as dict
                            deserialized_results.append(item)
                    else:
                        # Already an object, keep as is
                        deserialized_results.append(item)
                self.judgment_data['judge_results'] = deserialized_results


class LeanJudgmentTask(BaseLeanTask):
    """Lean code judgment task."""

    task_type = "lean_judgment"
    data_class = LeanJudgmentData
    task_config_class = LeanJudgmentConfig
    task_result_class = LeanJudgmentResult

    def __init__(self, data: LeanJudgmentData, config: 'BaseScaffoldConfig'):
        """Initialize judgment task."""
        super().__init__(data, config)
        self.scratch_target_path: Optional[Path] = None
        self.target_workspace_expected_file_path: Optional[Path] = None
    
    def _convert_diff_to_line_spans(self, diff_text: str) -> List[Tuple[int, int]]:
        """Convert git diff to line spans for LeanCodeToolsProvider.display_content"""
        if not diff_text:
            return []
        
        import re
        ranges = []
        hunk_pattern = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@', re.MULTILINE)
        
        for match in hunk_pattern.finditer(diff_text):
            start_old = int(match.group(1))
            length_old = int(match.group(2)) if match.group(2) else 1
            
            # Calculate the end line (inclusive)
            end_old = start_old + length_old - 1
            ranges.append((start_old, end_old))
        
        return ranges
    
    def _compute_diff(self, original: str, modified: str, filename: str = "file") -> str:
        """Compute unified diff between two files."""
        original_lines = original.splitlines(keepends=False)
        modified_lines = modified.splitlines(keepends=False)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        )

        return '\n'.join(diff)

    def _compute_diff_stats(self, diff_text: str) -> Dict[str, int]:
        """Compute diff statistics: additions and deletions."""
        if not diff_text:
            return {'additions': 0, 'deletions': 0}

        additions = 0
        deletions = 0

        for line in diff_text.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                additions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1

        return {'additions': additions, 'deletions': deletions}

    async def create_user_prompt(self) -> str:
        """Create user prompt for judgment task."""
        import asyncio
        from .prompt import LEAN_JUDGMENT_USER_PROMPT
        from ape.toolkits.code.lean.provider import LeanCodeToolsProvider

        judgment_config: LeanJudgmentConfig = self.config.task_config
        has_ground_truth = (judgment_config.judge_mode == "with_ground_truth")

        is_new_file = not self.data.original_code or not self.data.original_code.strip()

        target_filename = self.scratch_target_path.name

        if is_new_file:
            agent_solution = self.data.target_code
            original_content = "# Empty file (new file creation)"
            display_mode_note = ""
        else:
            agent_solution = self._compute_diff(
                self.data.original_code,
                self.data.target_code,
                self.data.filename or "file.lean"
            )
            
            line_spans = None
            if judgment_config.format_display_mode == "line_spans":
                line_spans = self._convert_diff_to_line_spans(agent_solution)

            original_content = await asyncio.to_thread(
                LeanCodeToolsProvider.display_content,
                content=self.data.original_code,
                display_mode=judgment_config.format_display_mode,
                body_handling=judgment_config.format_body_handling,
                line_spans=line_spans,
                context_lines=judgment_config.format_context_lines
            )
            
            if judgment_config.format_display_mode == "line_spans":
                display_mode_note = f"\n\nNote: Original file content is displayed in line-spans mode, showing only modification-related lines with {judgment_config.format_context_lines} lines of context before/after each change."
            elif judgment_config.format_display_mode == "full":
                display_mode_note = "\n\nNote: Original file content is displayed in full mode, showing the complete file."

        diff_stats_section = ""
        if not is_new_file:
            agent_stats = self._compute_diff_stats(agent_solution)

            if has_ground_truth and self.data.gold_diff:
                expert_stats = self._compute_diff_stats(self.data.gold_diff)
                diff_stats_section = f"""
<diff_statistics>
Agent solution: +{agent_stats['additions']} -{agent_stats['deletions']} lines
Expert reference: +{expert_stats['additions']} -{expert_stats['deletions']} lines

Note: Large discrepancies in change magnitude may indicate scope violations.
Use this as a reference point when evaluating scope control.
</diff_statistics>
"""
            else:
                diff_stats_section = f"""
<diff_statistics>
Agent solution: +{agent_stats['additions']} -{agent_stats['deletions']} lines

Note: Evaluate whether the change magnitude is appropriate for the task requirements.
</diff_statistics>
"""

        if has_ground_truth:
            resource_list = "\n- **Expert reference**: Mathlib maintainers' solution (in target workspace)"

            expert_section = f"\n<expert_diff>\n{self.data.gold_diff or '# No expert reference diff available'}\n</expert_diff>"

            expert_note = "\n- **Expert comparison**: Use as benchmark but recognize valid alternatives\n- **Fairness**: Different but equally correct approaches deserve equal ratings"
            expert_pitfalls = """
- Don't penalize valid alternatives differing from expert
- Don't focus on superficial differences (style/naming) vs substantive ones (correctness)
- Expert shows ONE correct way, not the ONLY way"""
        else:
            resource_list = "\n- **No ground truth reference available** (evaluate on merit alone)"

            expert_section = ""
            expert_note = ""
            expert_pitfalls = ""

        # Get submit tool name from config (mcp_server_name already includes trailing __)
        submit_tool_name = f"{self.config.mcp_server_name}submit_result"

        return LEAN_JUDGMENT_USER_PROMPT.format(
            task_description=self.data.task_description,
            target_filename=target_filename,
            original_content=original_content + display_mode_note,
            agent_solution=agent_solution,
            diff_stats_section=diff_stats_section,
            resource_list=resource_list,
            expert_section=expert_section,
            expert_note=expert_note,
            expert_pitfalls=expert_pitfalls,
            submit_tool_name=submit_tool_name
        )
    
    async def setup(
        self,
        termination_callback,
        orchestrator_id: str,
        attempt_path: Optional[Path] = None
    ) -> 'logging.LoggerAdapter':
        """Set up judgment task environment.

        Args:
            termination_callback: Termination callback function.
            orchestrator_id: Orchestrator ID.
            attempt_path: Preset workspace path if orchestrator created one.

        Returns:
            Logger instance for scaffold use.
        """
        logger = await super().setup(termination_callback, orchestrator_id, attempt_path)
        if not self.scratch_workspace:
            raise RuntimeError("Scratch workspace not initialized for judgment task")

        if self.data.original_code is not None and self.data.original_code.strip():
            if self.data.target_code.strip() == self.data.original_code.strip():
                raise ValueError(
                    "No modifications detected in judgment task - agent did not make any changes. "
                    "This indicates either no code changes were made or the agent submitted identical code."
                )

        if self.data.filename:
            base_name = Path(self.data.filename).stem
            target_file_path = self.scratch_workspace.path / f"{base_name}__AGENT.lean"
        else:
            target_file_path = self.scratch_workspace.path / f"target__AGENT.lean"
        self.scratch_target_path = target_file_path

        import aiofiles
        async with aiofiles.open(target_file_path, 'w', encoding='utf-8') as f:
            await f.write(self.data.target_code)

        if self.data.filename:
            if not self.target_workspace:
                raise RuntimeError("Target workspace not initialized for judgment task")
            # filename is relative to repo root (e.g., "Mathlib/Topology/Subpath.lean")
            self.target_workspace_expected_file_path = self.target_workspace.path / self.data.filename

        # if self.data.reference_implementation:
        #     await self._validate_reference_implementation()

        if self.scratch_target_path:
            self.scratch_workspace.read_only_path_patterns = [
                str(self.scratch_target_path.resolve())
            ]
            self.logger.debug(f"Set scratch target file as read-only: {self.scratch_target_path}")

        return logger
    
    async def _validate_reference_implementation(self) -> None:
        """Validate reference implementation consistency with target workspace."""
        if not self.data.reference_implementation or not self.data.filename:
            return
        try:
            if not self.target_workspace:
                raise RuntimeError("Target workspace not initialized for judgment task")
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

    async def register_task_tools(self, mcp) -> None:
        """Register task-specific tools for judgment."""
        from typing import Annotated
        from pydantic import Field
        
        @mcp.tool(
            description=(
                "Submit your final judgment evaluation for the Lean code.\n\n"
                "For each dimension (semantic_correctness, requirement_alignment, scope_control):\n"
                "1. Assessment (string): Detailed evaluation citing specific evidence\n"
                "   - Reference code elements, mathematical properties, constraints\n"
                "   - Use `backticks` for code, \\\\( \\\\) for inline math, \\\\[ \\\\] for block math\n"
                "   - Be thorough but focused\n"
                "2. Rating (string): excellent | good | acceptable | poor | unacceptable\n\n"
                "Then provide:\n"
                "3. Overall judgment (string): accept | reject\n"
                "   - accept: semantically correct, fulfills requirements, and properly scoped\n"
                "   - reject: has critical issues in semantics, requirements, or scope\n\n"
                "This will trigger evaluation and may end the conversation.\n\n"
                "**CRITICAL: You MUST use this tool to submit your judgment. Providing judgment only in text response is INVALID and will NOT be accepted.**"
            )
        )
        async def submit_result(
            # Semantic Correctness - assessment first, rating second
            semantic_correctness_assessment: Annotated[str, Field(
                description="Assessment conclusion for semantic correctness with evidence"
            )],
            semantic_correctness_rating: Annotated[str, Field(
                description="Rating: excellent, good, acceptable, poor, or unacceptable"
            )],
            # Requirement Alignment - assessment first, rating second
            requirement_alignment_assessment: Annotated[str, Field(
                description="Assessment conclusion for requirement alignment with evidence"
            )],
            requirement_alignment_rating: Annotated[str, Field(
                description="Rating: excellent, good, acceptable, poor, or unacceptable"
            )],
            # Scope Control - assessment first, rating second
            scope_control_assessment: Annotated[str, Field(
                description="Assessment conclusion for scope control with evidence"
            )],
            scope_control_rating: Annotated[str, Field(
                description="Rating: excellent, good, acceptable, poor, or unacceptable"
            )],
            # Overall Judgment
            overall_judgment: Annotated[str, Field(
                description="Overall judgment: accept or reject"
            )]
        ) -> Dict[str, Any]:
            """Submit final judgment for evaluation and potential termination."""
            from pydantic import ValidationError

            self.logger.info("Tool submit_result: execution started")
            try:
                judgment = Judgment(
                    semantic_correctness_assessment=semantic_correctness_assessment,
                    semantic_correctness_rating=semantic_correctness_rating,
                    requirement_alignment_assessment=requirement_alignment_assessment,
                    requirement_alignment_rating=requirement_alignment_rating,
                    scope_control_assessment=scope_control_assessment,
                    scope_control_rating=scope_control_rating,
                    overall_judgment=overall_judgment
                )
                
                if overall_judgment not in ["accept", "reject"]:
                    return {
                        "success": False,
                        "error": f"Invalid overall_judgment: '{overall_judgment}'. Must be either 'accept' or 'reject'.",
                        "message": "Evaluation failed or not ready"
                    }

                judgment_conclusion = "positive" if overall_judgment == "accept" else "negative"

                accuracy_score = 1.0
                custom_metrics = None

                if self.data.judgement_ground_truth is not None:
                    predicted_positive = judgment_conclusion == "positive"
                    is_correct = predicted_positive == self.data.judgement_ground_truth
                    accuracy_score = 1.0 if is_correct else 0.0

                    tp = 1.0 if predicted_positive and self.data.judgement_ground_truth else 0.0
                    tn = 1.0 if not predicted_positive and not self.data.judgement_ground_truth else 0.0
                    fp = 1.0 if predicted_positive and not self.data.judgement_ground_truth else 0.0
                    fn = 1.0 if not predicted_positive and self.data.judgement_ground_truth else 0.0

                    custom_metrics = {
                        "tp": tp,
                        "tn": tn,
                        "fp": fp,
                        "fn": fn
                    }

                evaluation_result = EvaluationResult(
                    success=True,
                    score=accuracy_score,
                    message="Judgment submitted successfully"
                )

                should_terminate = self.should_terminate(evaluation_result)

                judgment_data = {
                    "semantic_correctness_assessment": semantic_correctness_assessment,
                    "semantic_correctness_rating": semantic_correctness_rating,
                    "requirement_alignment_assessment": requirement_alignment_assessment,
                    "requirement_alignment_rating": requirement_alignment_rating,
                    "scope_control_assessment": scope_control_assessment,
                    "scope_control_rating": scope_control_rating,
                    "overall_judgment": overall_judgment,
                    "ground_truth": self.data.judgement_ground_truth
                }

                if should_terminate and self.termination_callback:
                    try:
                        task_result = self.create_result(
                            success=True,
                            score=accuracy_score,
                            judgment_conclusion=judgment_conclusion,
                            judgment_data=judgment_data,
                            custom_metrics=custom_metrics
                        )

                        await self.termination_callback(task_result)
                    except Exception as e:
                        self.logger.warning(f"Failed to trigger termination: {traceback.format_exc()}")

                self.logger.info(f"Tool submit_result: execution completed successfully (judgment_conclusion={judgment_conclusion}, accuracy_score={accuracy_score})")
                return {
                    "success": True,
                    "message": "Judgment submitted and evaluated successfully",
                    "judgment_conclusion": judgment_conclusion,
                    "judgment": judgment_data,
                    "accuracy_score": accuracy_score
                }
            
            except ValidationError as e:
                errors = []
                for err in e.errors():
                    field = '.'.join(str(loc) for loc in err['loc'])
                    msg = err['msg']
                    if 'rating' in field:
                        errors.append(f"{field}: Must be one of [excellent, good, acceptable, poor, unacceptable], got '{err.get('input', 'unknown')}'")
                    elif 'overall_judgment' in field:
                        errors.append(f"{field}: Must be either 'accept' or 'reject', got '{err.get('input', 'unknown')}'")
                    else:
                        errors.append(f"{field}: {msg}")

                return {
                    "success": False,
                    "error": "Judgment validation failed. Please check your field values:\n" + "\n".join(errors),
                    "message": "Evaluation failed or not ready"
                }
            except Exception as e:
                self.logger.error(f"Unexpected error in submit_result: {traceback.format_exc()}")
                return {
                    "success": False,
                    "error": f"Unexpected system error occurred:\n{traceback.format_exc()}",
                    "message": "Evaluation failed or not ready"
                }
    
    def create_result(
        self,
        success: bool,
        score: float,
        judgment_conclusion: str,
        judgment_data: Dict[str, Any],
        **kwargs
    ) -> LeanJudgmentResult:
        """Create judgment task result."""
        return LeanJudgmentResult(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=success,
            score=score,
            judgment_conclusion=judgment_conclusion,
            judgment_data=judgment_data,
            **kwargs
        )

    def should_terminate(self, evaluation_result: EvaluationResult = None) -> bool:
        """Terminate when judgment is successfully submitted."""
        if evaluation_result is None:
            return False
        return evaluation_result.success

    @classmethod
    def is_best_result(cls, result: 'BaseTaskResult') -> bool:
        """Judgment tasks do not support early termination."""
        return False

    @classmethod
    def aggregate_custom_metrics(cls, results: List['BaseTaskResult']) -> Optional[Dict[str, float]]:
        """Aggregate custom metrics across judgment tasks (micro-average)."""
        if not results:
            return None

        total_tp = 0.0
        total_tn = 0.0
        total_fp = 0.0
        total_fn = 0.0

        for result in results:
            if result.custom_metrics:
                total_tp += result.custom_metrics.get('tp', 0.0)
                total_tn += result.custom_metrics.get('tn', 0.0)
                total_fp += result.custom_metrics.get('fp', 0.0)
                total_fn += result.custom_metrics.get('fn', 0.0)
        
        if total_tp + total_tn + total_fp + total_fn == 0:
            return None

        aggregated = {
            "tp": total_tp,
            "tn": total_tn,
            "fp": total_fp,
            "fn": total_fn
        }

        total = total_tp + total_tn + total_fp + total_fn
        aggregated['accuracy'] = (total_tp + total_tn) / total if total > 0 else 0.0

        if (total_tp + total_fn) > 0:
            aggregated['tpr'] = total_tp / (total_tp + total_fn)  # True Positive Rate
        if (total_tn + total_fp) > 0:
            aggregated['tnr'] = total_tn / (total_tn + total_fp)  # True Negative Rate
        if (total_fp + total_tn) > 0:
            aggregated['fpr'] = total_fp / (total_fp + total_tn)  # False Positive Rate
        if (total_fn + total_tp) > 0:
            aggregated['fnr'] = total_fn / (total_fn + total_tp)  # False Negative Rate
        
        return aggregated
    
    @classmethod
    def aggregate_results(cls, results: List['BaseTaskResult']) -> 'BaseTaskResult':
        """Aggregate judgment results using majority voting."""
        if not results:
            raise ValueError("No results to aggregate")

        resources = cls._aggregate_resources(results)
        first = results[0]

        successful_results = [r for r in results if r.success]

        if not successful_results:
            return LeanJudgmentResult(
                task_id=first.task_id,
                task_type=first.task_type,
                global_index=first.global_index,
                success=False,
                score=0.0,
                judgment_conclusion="failed",
                **resources,
                judgment_data={
                    "judge_results": results,
                    "overall_result": "all_failed"
                },
                error="All samples failed"
            )
        
        judgment_conclusions = [r.judgment_conclusion for r in successful_results]

        positive_count = judgment_conclusions.count('positive')
        negative_count = judgment_conclusions.count('negative')

        overall_conclusion = "positive" if positive_count > negative_count else "negative"

        ground_truth = None
        for r in successful_results:
            if r.judgment_data and "ground_truth" in r.judgment_data:
                ground_truth = r.judgment_data["ground_truth"]
                break

        custom_metrics = None
        if ground_truth is not None:
            aggregated_predicted_positive = overall_conclusion == "positive"
            aggregated_accuracy_score = 1.0 if aggregated_predicted_positive == ground_truth else 0.0

            tp = 1.0 if aggregated_predicted_positive and ground_truth else 0.0
            tn = 1.0 if not aggregated_predicted_positive and not ground_truth else 0.0
            fp = 1.0 if aggregated_predicted_positive and not ground_truth else 0.0
            fn = 1.0 if not aggregated_predicted_positive and ground_truth else 0.0

            custom_metrics = {
                "tp": tp,
                "tn": tn,
                "fp": fp,
                "fn": fn
            }
        else:
            aggregated_accuracy_score = 1.0

        return LeanJudgmentResult(
            task_id=first.task_id,
            task_type=first.task_type,
            global_index=first.global_index,
            success=True,
            score=aggregated_accuracy_score,
            judgment_conclusion=overall_conclusion,
            **resources,
            judgment_data={
                "aggregation_method": "majority_voting",
                "total_judges": len(judgment_conclusions),
                "positive_votes": positive_count,
                "negative_votes": negative_count,
                "individual_conclusions": judgment_conclusions,
                "judge_results": results,  # Full raw data
                "overall_result": overall_conclusion
            },
            custom_metrics=custom_metrics
        )

async def lean_semantic_evaluation(
    final_code: str,
    original_code: Optional[str],
    task_description: str,
    semantic_config: SemanticValidationConfig,
    base_config: 'BaseScaffoldConfig',
    reference_implementation: Optional[str] = None,
    filename: Optional[str] = None,
    target_workspace: Optional[WorkspaceInfo] = None,
    gold_diff: Optional[str] = None,
    logger: Optional['logging.LoggerAdapter'] = None,
    parent_attempt_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Execute Lean semantic evaluation using unified BoN mechanism.

    Args:
        final_code: Code to evaluate.
        original_code: Original code (None for new files).
        task_description: Task description.
        semantic_config: Semantic validation configuration.
        base_config: Base configuration object.
        reference_implementation: Optional reference implementation.
        filename: Optional filename.
        target_workspace: Target workspace specification.
        gold_diff: Optional reference diff.
        logger: Optional logger instance.
        parent_attempt_path: Optional parent workspace path.

    Returns:
        Evaluation result dictionary with success, message, and aggregated_evaluations.
    """
    if logger is None:
        logger = create_logger()

    if original_code is not None and original_code.strip():
        if final_code.strip() == original_code.strip():
            logger.warning("No actual modifications detected between original_code and final_code, skipping semantic validation")
            return {
                "success": False,
                "message": "No modifications detected - agent did not make any changes to the original code",
                "judgment_conclusion": "negative",
                "nested_token_usage": None
            }
    
    try:
        num_judges = (semantic_config.static_semantic_samples
                     if semantic_config.judge_method == 'static'
                     else semantic_config.agentic_semantic_samples)

        logger.info(f"Starting semantic validation with {num_judges} judges using unified BoN mechanism...")

        from ape.orchestration.config import ExecutionConfig
        from ape.scaffolds.factory import create_scaffold_config_for_type
        from ape.orchestration.orchestrator import TaskOrchestrator
        from ape.tasks.lean_tasks.formal_math.judgment.task import LeanJudgmentTask, LeanJudgmentData

        if target_workspace is None:
            raise ValueError("target_workspace specification is required for semantic evaluation")

        judge_data = LeanJudgmentData(
            task_id="semantic_judge",
            target_code=final_code,
            original_code=original_code,
            task_description=task_description,
            reference_implementation=reference_implementation,
            gold_diff=gold_diff,
            filename=filename,
            target_workspace=target_workspace,
            metadata={}
        )

        judge_mode = semantic_config.judge_mode

        judgment_task_config = LeanJudgmentConfig(
            judge_mode=judge_mode
        )

        from ape.llm_clients.config import LLMConfig
        from ape.runtime.factory import create_runtime_config_for_type

        # Create runtime config for judge tasks based on semantic_config
        judge_runtime_config = create_runtime_config_for_type(semantic_config.runtime_type)

        judge_config = create_scaffold_config_for_type(
            scaffold_type=semantic_config.scaffold_type,
            base_config=base_config,
            execution=ExecutionConfig(
                num_processes=semantic_config.num_processes,
                max_concurrency=semantic_config.max_concurrency,
                max_turns=semantic_config.max_turns,
                sample_count=num_judges
            ),
            task_config=judgment_task_config,
            llm_config=LLMConfig(model_name=semantic_config.model),
            runtime_config=judge_runtime_config  # Use semantic_config's runtime
        )

        if parent_attempt_path:
            subtasks_dir = parent_attempt_path / "subtasks"
            subtasks_dir.mkdir(parents=True, exist_ok=True)
            judge_config.runs_base_dir = subtasks_dir

        judge_task = LeanJudgmentTask(judge_data, judge_config)

        judge_runner = TaskOrchestrator(
            config=judge_config,
            logger=logger
        )
        
        logger.info(f"Executing semantic validation with unified BoN ({num_judges} samples)...")
        judge_results = await judge_runner.run([judge_task])

        if judge_results.workspace_path:
            logger.info(f"Semantic judgment execution completed. Judge results saved to: {judge_results.workspace_path}")

        if not judge_results.task_results:
            return {
                "success": False,
                "message": "No judge results received, please retry"
            }

        aggregated_result = judge_results.task_results[0]

        if not isinstance(aggregated_result, LeanJudgmentResult):
            logger.error(f"Judgment task failed during setup or execution: {aggregated_result.error or 'Unknown error'}")
            return {
                "success": False,
                "message": f"Judgment task failed: {aggregated_result.error or 'No error details available'}",
                "judgment_conclusion": "negative",
                "nested_token_usage": judge_results.total_token_usage
            }
        
        logger.info(f"🏁 Unified BoN semantic validation result: {aggregated_result.judgment_conclusion.upper()}")
        
        return {
            "success": aggregated_result.success,
            "message": f"Semantic validation completed with {num_judges} judges",
            "judgment_conclusion": aggregated_result.judgment_conclusion,
            "aggregated_evaluations": aggregated_result.judgment_data,
            "nested_token_usage": judge_results.total_token_usage
        }
        
    except Exception as e:
        logger.error(f"Semantic validation failed: {traceback.format_exc()}")
        return {
            "success": False,
            "message": f"Unified BoN semantic validation failed, please retry: {traceback.format_exc()}",
            "error": traceback.format_exc(),
            "nested_token_usage": None
        }

register_task("lean_judgment", LeanJudgmentTask)
