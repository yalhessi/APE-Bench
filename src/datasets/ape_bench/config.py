"""
APE Bench Configuration System

Generalized for any formal language project (Lean, Isabelle, Coq, etc.).
Uses plain git worktrees for file access (no compilation required).
"""

from typing import Dict, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field

from ape.toolkits.execute.config import CodeExecuteToolConfig
from ape.utils.project import PROJECT_ROOT


class ApeBenchConfig(BaseModel):
    """APE Bench configuration for formal language projects"""

    # Repository settings
    repo_url: str = Field(
        ...,
        description="Repository URL"
    )
    # Language settings
    language: str = Field(
        default="lean",
        description="Formal language: lean, isabelle, coq"
    )
    file_extension: str = Field(
        default=".lean",
        description="File extension for the language"
    )

    # Data collection settings
    dataset_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "datasets" / "ape_bench",
        description="Dataset output directory"
    )
    output_file: Optional[Path] = Field(
        default=None,
        description="Specific output file path"
    )

    # Diff size limits
    min_diff_lines: int = Field(default=10, description="Minimum diff lines")
    max_diff_lines: int = Field(default=300, description="Maximum diff lines")

    # Data limits
    latest_num_data: Optional[int] = Field(default=None, description="Number of latest data points")
    max_commits_scan: Optional[int] = Field(default=None, description="Maximum commits to scan")

    # Date filtering
    earliest_date: Optional[str] = Field(
        default="2023-08-01",
        description="Earliest date (YYYY-MM-DD)"
    )
    latest_date: Optional[str] = Field(
        default=None,
        description="Latest date (YYYY-MM-DD)"
    )

    # Content filtering
    min_edit_distance: int = Field(default=10, description="Minimum edit distance")
    min_absolute_added_lines: int = Field(default=10, description="Minimum added lines")
    max_more_removed_line_ratio: float = Field(default=0.5, description="Max removed line ratio")

    # Processing settings
    num_processes: int = Field(default=8, description="Parallel processes")
    max_retries: int = Field(default=3, description="Maximum retry attempts for failed tasks")
    scaffold_type: str = Field(default="ape_agent", description="Scaffold name")
    model: str = Field(default="gemini_3_pro", description="Model name")

    # Workspace settings (uses plain git worktrees, no compilation)
    workspace_config: CodeExecuteToolConfig = Field(
        default_factory=CodeExecuteToolConfig,
        description="Workspace configuration for plain git worktrees"
    )

    # Processing limits
    max_cpu_limit: int = Field(
        default=64,
        description="Maximum CPU cores for parallel processing"
    )

    # Lean verification settings (code execution verification during data collection)
    enable_verification: bool = Field(
        default=True,
        description="Whether to verify commits can compile successfully during data collection"
    )
    lean_verify_num_processes: int = Field(
        default=4,
        description="Number of parallel processes for Lean code compilation verification"
    )

    # Commit filtering
    allowed_commit_types: List[str] = Field(
        default=['chore', 'feat', 'refactor', 'fix'],
        description="Allowed commit types"
    )
    commit_typo_map: Dict[str, str] = Field(
        default={
            'faet': 'feat',
            'feature': 'feat',
            'featl': 'feat',
            'feeat': 'feat',
        },
        description="Commit type typo correction mapping"
    )

    # File filtering
    exclude_deleted_files: bool = Field(
        default=True,
        description="Whether to exclude deleted files"
    )

    # Content filtering
    non_repeating_threshold: float = Field(
        default=0.8,
        description="Threshold for non-repeating modifications check"
    )

    # Edit distance filtering
    edit_distance_scattered_threshold: int = Field(
        default=3,
        description="Threshold for scattered edits"
    )
    edit_distance_max_scattered_ratio: float = Field(
        default=0.5,
        description="Maximum scattered edit ratio"
    )

    # Train/Test split settings
    enable_split: bool = Field(
        default=True,
        description="Whether to enable train/test splitting"
    )
    test_size: Optional[int] = Field(
        default=None,
        description="Number of samples for test set. If None, no splitting is performed"
    )
    split_strategy: str = Field(
        default='balanced',
        description="Sampling strategy: 'balanced', 'proportional', or 'difficulty_focused'"
    )

    # Task validation settings (semantic validation of generated tasks)
    validate_generated_task: bool = Field(
        default=True,
        description="Whether to run semantic validation on generated PE task using ground truth solution"
    )
