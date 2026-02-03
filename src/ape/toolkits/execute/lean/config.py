"""
Lean Verify Tool Configuration

Inherits from CodeExecuteToolConfig and adds Lean-specific settings.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import Field, ConfigDict
from ape.utils.file_ops import normalize_repo_url

# Import base class
from ..config import CodeExecuteToolConfig


class LeanVerifyToolConfig(CodeExecuteToolConfig):
    """Lean verification service configuration.

    Inherits common path and operational configuration from CodeExecuteToolConfig.
    Adds Lean-specific verification and build settings.
    """
    model_config = ConfigDict(extra='forbid')

    # ==================== Lean-specific Options ====================
    lean_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Lean compiler options"
    )

    # ==================== Verification Limits ====================
    timeout: float = Field(default=300.0, description="Verification timeout (seconds)")
    max_memory_gb: float = Field(default=8.0, description="Maximum memory (GB)")
    num_processes: int = Field(default=4, description="Number of parallel processes")
    nproc: Optional[int] = Field(default=None, description="Lean nproc setting")

    # ==================== Verification Options ====================
    accepted_axioms: List[str] = Field(
        default_factory=lambda: ['propext', 'Classical.choice', 'Quot.sound'],
        description="Accepted axioms list"
    )
    allow_sorries: bool = Field(default=False, description="Allow sorry placeholders")
    print_axioms: bool = Field(default=False, description="Print axioms during verification")
    max_messages: int = Field(default=20, description="Maximum verification messages")

    # ==================== Default Lean Repository ====================
    default_repo_url: str = Field(
        default="https://github.com/leanprover-community/mathlib4.git",
        description="Default Lean repository URL"
    )
    default_commit_hash: str = Field(
        default="2df2f0150c275ad53cb3c90f7c98ec15a56a1a67",
        description="Default commit hash"
    )

    # ==================== Build Configuration ====================
    build_timeout: Optional[float] = Field(default=None, description="Build timeout (seconds)")
    toolchain_install_timeout: float = Field(default=600.0, description="Toolchain install timeout")
    cache_operation_timeout: float = Field(default=3600.0, description="Cache operation timeout")
    workspace_restore_timeout: float = Field(default=300.0, description="Workspace restore timeout")

    # ==================== Concurrency for Lean ====================
    max_concurrent_installs: int = Field(default=16, description="Max concurrent toolchain installs")
    max_concurrent_restores: int = Field(default=64, description="Max concurrent restores")
    restore_queue_timeout: float = Field(default=600.0, description="Restore queue timeout")
    restore_batch_size: int = Field(default=500, description="Files per restore batch")
    workspace_restore_poll_interval: float = Field(default=2.0, description="Restore poll interval")

    # ==================== Lean-Specific Path Methods ====================

    @property
    def default_repo_name(self) -> str:
        """Get normalized default repository name."""
        return normalize_repo_url(self.default_repo_url)

    def resolve_repo(self, repo_url: Optional[str] = None) -> tuple[str, str]:
        """Resolve repository name and URL with defaults."""
        url = repo_url or self.default_repo_url
        name = normalize_repo_url(url)
        return name, url

    def get_workspace_dir(self, repo_name: str) -> Path:
        """Get compiled workspace directory for Lean repos.

        Lean repos need compilation, so workspace always refers to workspaces.
        """
        return self.get_compiled_workspace_dir(repo_name)

    def get_repo_path(self, repo_name: str) -> Path:
        """Get git repository source path."""
        return self.get_repo_source_path(repo_name)
