"""Task Models Module providing workspace metadata structures."""

from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel, Field


class WorkspaceInfo(BaseModel):
    """Workspace information including path, version, and access control.

    Supports two workspace types:
    - Lean project workspace (target/reference): requires commit_hash, repo_url; default_target is optional
    - Scratch workspace: only requires name and path, Git fields are None

    Access Control:
        blocked_path_patterns: Paths completely blocked from access
        read_only_path_patterns: Paths that can be read but not written
        no_read_path_patterns: Paths that can be written but not read

    Path patterns support glob syntax relative to workspace root,
    or absolute paths for exact file matching.
    """
    name: str = Field(..., description="Workspace name")
    path: Optional[Path] = Field(default=None, description="Workspace root directory path (set during setup)")

    # Git information (required for Lean workspaces, None for scratch)
    commit_hash: Optional[str] = Field(default=None, description="Git commit hash")
    repo_url: Optional[str] = Field(default=None, description="Git repository URL")
    default_target: Optional[str] = Field(default=None, description="Optional target subdirectory filter (e.g., 'Mathlib'). If not set, uses entire repository.")
    toolchain: Optional[str] = Field(default=None, description="Lean toolchain version (e.g., 'leanprover/lean4:v4.22.0')")

    # Access control patterns
    blocked_path_patterns: List[str] = Field(
        default_factory=list,
        description="Paths completely blocked from access"
    )
    read_only_path_patterns: List[str] = Field(
        default_factory=list,
        description="Read-only paths (write blocked)"
    )
    no_read_path_patterns: List[str] = Field(
        default_factory=list,
        description="Write-only paths (read blocked)"
    )

    @property
    def target_path(self) -> Path:
        """Get effective target path (path / default_target if set)."""
        if not self.path:
            raise ValueError("Workspace path is not initialized")
        if self.default_target:
            return self.path / self.default_target
        return self.path
