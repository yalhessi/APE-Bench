"""
Semantic annotation task (per file)

Minimal task using only read-only tools (file_read, file_search, content_search, file_diff) and a submit_result tool.
Terminates when all provided declaration ids have been annotated.
"""

import traceback
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING, Literal
from pydantic import BaseModel, Field
from pathlib import Path

from ape.tasks.base import BaseTaskConfig, register_task, BaseTaskResult, EvaluationResult
from ape.tasks.lean_tasks.base import BaseLeanTask, BaseLeanTaskData
from ape.toolkits.code.lean.provider import LeanCodeToolsProvider

from .prompt import ANNOTATION_USER_PROMPT
from .models import DeclarationInfo
from .utils import generate_task_id

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig


class Annotation(BaseModel):
    """Semantic annotation for a declaration"""
    semantic_statement: str = Field(..., description="Single sentence mathematical statement in natural language")
    keywords: str = Field(..., description="Comma-separated mathematical keywords (3-7 items)")


class AnnotationTaskData(BaseLeanTaskData):
    filename: Path = Field(..., description="Repo-root relative file path")
    task_type: Literal["lean_semantic_annotation"] = Field(
        default="lean_semantic_annotation",
        description="Task type identifier"
    )
    declarations: List[DeclarationInfo] = Field(default_factory=list)


class AnnotationTaskConfig(BaseTaskConfig):
    # Explicit tool allowlist for annotation tasks
    disabled_tools: List[str] = [
        "file_write", "file_edit"
    ]
    enabled_tools: Optional[List[str]] = [
        "bash_execute",
        "file_read", 
        # "file_search", "content_search", "file_diff",
        "file_multi_edit",
        # "lean_retrieve",
        # "lean_verify",
    ]
    
    # Code formatting configuration for LeanCodeToolsProvider.display_content
    format_display_mode: str = "line_spans"  # "full" | "line_spans"
    format_body_handling: str = "omit_outside_spans"  # "keep_all" | "omit_all" | "omit_outside_spans"
    format_context_lines: int = 10


class AnnotationTaskResult(BaseTaskResult):
    model_config = {"arbitrary_types_allowed": True}
    filename: Path = Field(...)
    annotations: Dict[str, Annotation] = Field(default_factory=dict)


class AnnotationTask(BaseLeanTask):
    task_type = "lean_semantic_annotation"
    data_class = AnnotationTaskData
    evaluator_class = None
    task_config_class = AnnotationTaskConfig
    task_result_class = AnnotationTaskResult

    def __init__(self, data: AnnotationTaskData, config: 'BaseScaffoldConfig'):
        super().__init__(data, config)
        self._annotations: Dict[str, Annotation] = {}  # item_id -> Annotation
        
    
    def _get_line_spans_from_declarations(self) -> List[Tuple[int, int]]:
        """Get line spans from declarations (span is already line numbers)"""
        line_spans = []
        for decl in self.data.declarations:
            start_line, end_line = decl.span  # span is already line numbers
            line_spans.append((start_line, end_line))
        
        # Merge overlapping spans and sort
        if not line_spans:
            return []
        
        line_spans.sort(key=lambda x: x[0])
        merged = [line_spans[0]]
        
        for start, end in line_spans[1:]:
            last_start, last_end = merged[-1]
            if start <= last_end + 1:  # Adjacent or overlapping
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))
        
        return merged

    @classmethod
    def create_data_from_dict(cls, data: Dict[str, Any]) -> AnnotationTaskData:
        """Create task data from data dictionary."""
        # Generate task ID if not provided
        if 'task_id' not in data:
            workspace_spec = data.get('target_workspace') or {}
            commit_hash = workspace_spec.get('commit_hash') or data.get('commit_hash') or 'unknown'
            filename = data.get('filename', 'unknown')
            data['task_id'] = generate_task_id(commit_hash, filename)
        
        # Set default metadata if not provided
        if 'metadata' not in data:
            data['metadata'] = {}
    
        
        # Use model_validate directly with the data
        return AnnotationTaskData.model_validate(data)

    async def create_user_prompt(self) -> str:
        import json

        def one_decl_line(idx: int, d: DeclarationInfo) -> str:
            nm = d.name or ""
            line_start, line_end = d.span  # span is already line numbers

            return json.dumps({
                "declaration_index": idx,
                "name": nm,
                "kind": d.kind,
                "line_start": line_start,
                "line_end": line_end
            }, ensure_ascii=False)

        declarations_list = "\n".join(one_decl_line(i, d) for i, d in enumerate(self.data.declarations))

        return ANNOTATION_USER_PROMPT.format(
            declarations_list=declarations_list,
            file_content_section=await self._get_file_content_section()
        )

    async def _get_file_content_section(self) -> str:
        """
        Get the file content section for the prompt, showing only declaration-related content.
        
        Returns:
            Formatted file content section
        
        Raises:
            RuntimeError: If environment or file is not available
        """
        if self.target_workspace is None:
            raise RuntimeError("Workspace not initialized - cannot read file content")

        # filename is repo-root relative; use workspace root directly
        target_workspace_path = self.target_workspace.path
        file_path = target_workspace_path / self.data.filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        import aiofiles
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Get line spans from declarations (already line numbers)
        line_spans = self._get_line_spans_from_declarations()
        
        # Get task config
        task_config: AnnotationTaskConfig = self.config.task_config
        
        # Apply LeanCodeToolsProvider.display_content with line spans (CPU-intensive operation, move to thread pool)
        import asyncio
        try:
            processed_content = await asyncio.to_thread(
                LeanCodeToolsProvider.display_content,
                content=content,
                display_mode=task_config.format_display_mode,
                body_handling=task_config.format_body_handling,
                line_spans=line_spans,
                context_lines=task_config.format_context_lines
            )
        except Exception as e:
            self.logger.warning(f"Failed to format content from {self.data.filename}: {traceback.format_exc()}")
            # Fallback: show complete file
            processed_content = await asyncio.to_thread(
                LeanCodeToolsProvider.display_content,
                content=content,
                display_mode="full",
                body_handling="keep_all"
            )
        
        # Add note about display mode
        display_note = ""
        if task_config.format_display_mode == "line_spans":
            display_note = f"\n\nNote: File content is displayed in line-spans mode, showing only declaration-related lines with {task_config.format_context_lines} lines of context. Use file reading tools if you need additional context."
        
        return f"\n\n<FILE_CONTENT filename=\"{self.data.filename}\">{display_note}\n{processed_content}\n</FILE_CONTENT>"
    
    def should_terminate(self, evaluation_result: EvaluationResult) -> bool:
        # Terminate when all declarations have been annotated
        target_item_ids = {d.item_id for d in self.data.declarations}
        return len(self._annotations) >= len(self.data.declarations) and target_item_ids.issubset(self._annotations.keys())

    async def register_task_tools(self, mcp) -> None:
        from typing import Annotated
        from pydantic import Field

        @mcp.tool(
            description=(
                "Submit a complete mathematical annotation for a declaration (use declaration index 0, 1, 2, etc.).\n\n"
                "**CRITICAL: You MUST use this tool to submit your annotation. Providing annotation only in text response is INVALID and will NOT be accepted.**"
            )
        )
        async def submit_result(
            declaration_index: Annotated[int, Field(description="Target declaration index (0, 1, 2, etc.)", ge=0)],
            label: Annotated[str, Field(description="Short descriptive title (3-8 words) - captures the main mathematical concept using standard terminology")],
            semantic_statement: Annotated[str, Field(description="Self-contained mathematical explanation - complete meaning in natural language without Lean syntax")],
            keywords: Annotated[str, Field(description="3-7 searchable mathematical terms separated by commas - include concepts at different abstraction levels")]
        ) -> Dict[str, Any]:
            if not label or not semantic_statement or not keywords or \
            not label.strip() or not semantic_statement.strip() or not keywords.strip():
                missing_fields = []
                if not label or not label.strip(): missing_fields.append("label")
                if not semantic_statement or not semantic_statement.strip(): missing_fields.append("semantic_statement")
                if not keywords or not keywords.strip(): missing_fields.append("keywords")
                
                return {
                    "success": False, 
                    "error": f"Missing: {', '.join(missing_fields)}",
                    "guidance": "Provide: declaration_index (0,1,2...), label (3-8 words), semantic_statement (math explanation), keywords (3-7 terms)",
                    "message": "Evaluation failed or not ready"
                }

            # Validate declaration index
            if declaration_index >= len(self.data.declarations):
                return {
                    "success": False, 
                    "error": f"Invalid index: {declaration_index}",
                    "guidance": f"Use index 0 to {len(self.data.declarations) - 1}",
                    "message": "Evaluation failed or not ready"
                }
            
            # Get target declaration and item_id
            target_declaration = self.data.declarations[declaration_index]
            item_id = target_declaration.item_id

            # Validate annotation format using Pydantic
            try:
                annotation = Annotation(
                    semantic_statement=(label.strip() + " | " + semantic_statement.strip()),
                    keywords=keywords.strip()
                )
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Invalid annotation format: {traceback.format_exc()}")
                return {
                    "success": False, 
                    "error": f"Invalid format: {str(e)}",
                    "guidance": "Format: label (concept title), semantic_statement (math meaning), keywords (searchable terms)",
                    "message": "Evaluation failed or not ready"
                }

            # Record the annotation using original item_id
            self._annotations[item_id] = annotation

            # Check if should terminate after adding this annotation
            should_terminate = self.should_terminate(evaluation_result=EvaluationResult(success=True, score=1.0))
            
            # Trigger termination if complete
            if should_terminate and self.termination_callback:
                result = self.create_result(success=True, score=1.0, annotations=self._annotations)
                await self.termination_callback(result)

            return {
                "success": True, 
                "pending": len(self.data.declarations) - len(self._annotations), 
                "annotated_index": declaration_index,
                "message": "Annotation submitted successfully"
            }

    def create_result(self, **kwargs) -> AnnotationTaskResult:
        """Create annotation task result - only contains business data"""
        return AnnotationTaskResult(
            task_id=self.data.task_id,
            task_type=self.task_type,
            global_index=self.data.global_index,
            success=kwargs["success"],
            score=kwargs["score"],
            filename=self.data.filename,
            annotations=kwargs["annotations"]
        )


register_task("lean_semantic_annotation", AnnotationTask)
