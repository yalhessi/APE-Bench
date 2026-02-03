"""
APE Bench Data Models

Generalized for any formal language project.
"""

from typing import Literal, Optional
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class Exercise(BaseModel):
    """Exercise data structure for instruction generation.

    Contains both the task description (objectives) and the implementation approach
    (how the objectives are achieved through the modification).
    """

    title: str = Field(..., min_length=5, description="Exercise title (minimum 5 characters)")
    task_category: Literal['feature', 'bug fix', 'refactor', 'chore', 'testing', 'documentation', 'formatting'] = Field(
        ..., description="Task category"
    )
    formalization_aspect: Literal['new_content', 'proof_technique', 'abstraction', 'structural_design', 'technical_implementation'] = Field(
        ..., description="Type of formalization work"
    )
    difficulty: Literal['very easy', 'easy', 'medium', 'hard', 'very hard'] = Field(
        ..., description="Difficulty level"
    )
    task_nature: Literal['substantial', 'superficial'] = Field(
        ..., description="Task nature"
    )

    # Core content fields
    context: Optional[str] = Field(default=None, description="Background and current limitations")
    objectives: Optional[str] = Field(default=None, description="Specific goals to achieve")
    significance: Optional[str] = Field(default=None, description="Significance of achieving these objectives")

    # Implementation approach - how objectives are achieved
    implementation_approach: Optional[str] = Field(
        default=None,
        description="Detailed description of how the objectives are achieved: problem analysis, solution strategy, and implementation details"
    )

    # Rejection handling
    reject_reason: Optional[str] = Field(default=None, description="Reason for rejecting this task")

    # File context
    file_path: Path = Field(..., description="File path for this exercise")
    total_diff_lines: int = Field(default=0, description="Total diff lines in the modification")

    @field_validator('title')
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        """Ensure title is not empty after stripping whitespace"""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty after stripping whitespace")
        return stripped

    @field_validator('context', 'objectives', 'significance', 'implementation_approach')
    @classmethod
    def validate_content_fields(cls, v: Optional[str]) -> Optional[str]:
        """Validate content fields when provided"""
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty after stripping whitespace")
        return stripped
