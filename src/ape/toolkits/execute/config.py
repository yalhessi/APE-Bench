"""
Code Execute Tool Configuration Base Class

Provides common path configuration and operational parameters for all
code execution toolkits (Lean, Isabelle, Coq, etc.)
"""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from ape.utils.project import PROJECT_ROOT


class CodeExecuteToolConfig(BaseModel):
    """Base configuration for code execution tools.

    Provides unified path management and operational timeouts.
    Language-specific configs should inherit from this class.
    """
    model_config = ConfigDict(extra='forbid')

    # ==================== Path Configuration ====================
    # Base directory for all code execution data
    base_dir: Path = Field(
        default=PROJECT_ROOT / "data/code_execute",
        description="Base directory for code execution data"
    )

    # Global shared storage (CAS storage shared across all repos)
    storage_dir: Path = Field(
        default=PROJECT_ROOT / "data/code_execute/storage",
        description="Global shared content-addressable storage"
    )

    # Repository data directory (each repo has its own subdirectory)
    repos_dir: Path = Field(
        default=PROJECT_ROOT / "data/code_execute/repos",
        description="Base directory for all repository-specific data"
    )

    # ==================== Default Repository ====================
    default_repo_url: Optional[str] = Field(
        default=None,
        description="Default repository URL"
    )

    # ==================== Operation Timeouts ====================
    git_operation_timeout: float = Field(
        default=300.0,
        description="Git operation timeout (seconds)"
    )
    workspace_operation_timeout: float = Field(
        default=300.0,
        description="Workspace operation timeout (seconds)"
    )

    # ==================== Concurrency Configuration ====================
    max_concurrent_operations: int = Field(
        default=16,
        description="Maximum concurrent operations"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )
    retry_base_delay: float = Field(
        default=10.0,
        description="Base delay between retries (seconds)"
    )

    # ==================== Disk Space Configuration ====================
    disk_space_threshold_percent: float = Field(
        default=95.0,
        description="Disk usage threshold percentage"
    )

    # ==================== Path Helper Methods ====================

    def get_repo_base_dir(self, repo_name: str) -> Path:
        """Get base directory for a specific repository.

        Structure under this directory:
        - source/               # Git repository itself
        - snapshots/           # Snapshot index files
        - workspaces/ # Workspaces restored from snapshots (for repos that need compilation)
        - plain_workspaces/    # Workspaces created via git worktree (for repos without compilation)
        - build_workspaces/    # Temporary build directories
        """
        return self.repos_dir / repo_name

    def get_repo_source_path(self, repo_name: str) -> Path:
        """Get the git repository source path.

        This is the git repo itself, not a parent directory containing it.
        E.g., for mathlib4: repos/mathlib4/source/ is the mathlib4 git repo.
        """
        return self.get_repo_base_dir(repo_name) / "source"

    def get_snapshot_dir(self, repo_name: str) -> Path:
        """Get snapshot directory for a repository."""
        return self.get_repo_base_dir(repo_name) / "snapshots"

    def get_compiled_workspace_dir(self, repo_name: str) -> Path:
        """Get compiled workspace directory (restored from snapshots)."""
        return self.get_repo_base_dir(repo_name) / "workspaces"

    def get_plain_workspace_dir(self, repo_name: str) -> Path:
        """Get plain workspace directory (created via git worktree)."""
        return self.get_repo_base_dir(repo_name) / "plain_workspaces"

    def get_build_workspace_dir(self, repo_name: str) -> Path:
        """Get temporary build workspace directory."""
        return self.get_repo_base_dir(repo_name) / "build_workspaces"

    def get_cache_dir(self, repo_name: str) -> Path:
        """Get cache directory for a repository.

        Used for temporary cache operations like lake cache get.
        Structure: repos/repo_name/cache/commit_hash/attempt_{pid}_{timestamp}_{uuid}
        """
        return self.get_repo_base_dir(repo_name) / "cache"

    @model_validator(mode='after')
    def validate_and_create_directories(self):
        """Convert to absolute paths and create base directories."""
        self.base_dir = self.base_dir.resolve()
        self.storage_dir = self.storage_dir.resolve()
        self.repos_dir = self.repos_dir.resolve()

        # Create base directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.repos_dir.mkdir(parents=True, exist_ok=True)

        return self
