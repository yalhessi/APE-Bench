"""Base classes for Lean-specific tasks.

This module provides BaseLeanTask and BaseLeanTaskData which handle
Lean workspace setup, repository management, and Lean-specific execution patterns.

Key Design:
- BaseLeanTaskData defines workspace specifications (commit_hash + repo_url)
- BaseLeanTask.setup_attempt() creates symlinks from attempt_path/workspaces/ to actual Lean repos
- Symlinks allow uniform path access (e.g., 'target/', 'reference/<name>/') regardless of where repos are stored
"""

import traceback
from typing import Any, Optional, List, TYPE_CHECKING
from pathlib import Path
from pydantic import Field, field_validator

from ..base import BaseTask, BaseTaskData
from ..models import WorkspaceInfo, LeanWorkspaceInfo, parse_workspace_info, parse_workspace_info_list

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class BaseLeanTaskData(BaseTaskData):
    """Base data model for all Lean tasks.

    All Lean tasks require a target_workspace and may optionally have reference_workspaces.
    Workspaces are specified by commit_hash + repo_url, not by local paths.
    """

    target_workspace: LeanWorkspaceInfo = Field(
        ...,
        description="Target workspace specification (commit_hash, repo_url, default_target, toolchain)"
    )

    reference_workspaces: Optional[List[LeanWorkspaceInfo]] = Field(
        default=None,
        description="Optional reference workspaces for semantic retrieval"
    )

    @field_validator("target_workspace", mode="before")
    @classmethod
    def validate_target_workspace(cls, value: Any) -> LeanWorkspaceInfo:
        """Preserve explicit Lean workspace metadata during parsing."""
        workspace = parse_workspace_info(value)
        if isinstance(workspace, LeanWorkspaceInfo):
            return workspace
        return LeanWorkspaceInfo.model_validate(workspace.model_dump())

    @field_validator("reference_workspaces", mode="before")
    @classmethod
    def validate_reference_workspaces(cls, value: Any) -> Optional[List[LeanWorkspaceInfo]]:
        """Preserve explicit Lean workspace metadata during parsing."""
        workspaces = parse_workspace_info_list(value)
        if workspaces is None:
            return None
        return [
            workspace
            if isinstance(workspace, LeanWorkspaceInfo)
            else LeanWorkspaceInfo.model_validate(workspace.model_dump())
            for workspace in workspaces
        ]


class BaseLeanTask(BaseTask):
    """Base class for all Lean-specific tasks.

    Responsibilities:
    1. Resolve commit_hash -> actual workspace path via RestoreManager
    2. Create symlinks in attempt_path/workspaces/ pointing to resolved paths
    3. Set read-only patterns for target and reference workspaces

    Workspace Structure:
        attempt_path/
            workspaces/
                scratch/           (actual directory, writable)
                target/            (symlink -> ~/.ape/lean_verify/repos/.../workspaces/{commit_hash}/, read-only)
                reference/
                    {name}/        (symlink -> workspace, read-only)
    """

    # Workspace info after setup (with resolved paths and symlinks)
    target_workspace: Optional[LeanWorkspaceInfo] = None
    reference_workspaces: Optional[List[LeanWorkspaceInfo]] = None

    @classmethod
    async def setup_attempt(
        cls,
        data: 'BaseLeanTaskData',
        config: 'BaseScaffoldConfig',
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
        logger: Optional['logging.LoggerAdapter'] = None
    ) -> tuple[Path, WorkspaceInfo, Optional[LeanWorkspaceInfo], Optional[List[LeanWorkspaceInfo]]]:
        """Setup attempt with Lean workspaces (class method).

        Overrides BaseTask.setup_attempt to add Lean workspace setup:
        1. Call parent to create scratch workspace
        2. Resolve and symlink target workspace
        3. Resolve and symlink reference workspaces (if any)

        Args:
            data: Task data
            config: Scaffold configuration
            orchestrator_id: Orchestrator ID or 'cli' for CLI mode.
            attempt_path: Optional pre-created attempt path.
            logger: Optional logger

        Returns:
            Tuple of (attempt_path, scratch_workspace, target_workspace, reference_workspaces)
        """
        # Call parent setup to create basic structure (logs/, conversations/, workspaces/scratch/)
        attempt_path, scratch_workspace, _, _ = await super().setup_attempt(
            data, config, orchestrator_id, attempt_path, logger
        )

        # Calculate workspaces_dir (classmethod cannot access self)
        workspaces_dir = attempt_path / config.workspaces_dir_name

        # Setup target workspace symlink (required for Lean tasks)
        target_workspace = await cls._setup_workspace_symlink(
            workspace_spec=data.target_workspace,
            link_path=workspaces_dir / "target",
            config=config,
            logger=logger
        )

        # Setup reference workspace symlinks (optional)
        reference_workspaces = None
        if data.reference_workspaces:
            reference_workspaces = []
            ref_base_dir = workspaces_dir / "reference"
            ref_base_dir.mkdir(parents=True, exist_ok=True)

            for ref_ws in data.reference_workspaces:
                linked_ref = await cls._setup_workspace_symlink(
                    workspace_spec=ref_ws,
                    link_path=ref_base_dir / ref_ws.name,
                    config=config,
                    logger=logger
                )
                reference_workspaces.append(linked_ref)

        return attempt_path, scratch_workspace, target_workspace, reference_workspaces

    @classmethod
    async def _setup_workspace_symlink(
        cls,
        workspace_spec: LeanWorkspaceInfo,
        link_path: Path,
        config: 'BaseScaffoldConfig',
        logger: Optional['logging.LoggerAdapter'] = None
    ) -> LeanWorkspaceInfo:
        """Setup a workspace symlink (class method).

        Args:
            workspace_spec: Workspace specification (must have commit_hash + repo_url)
            link_path: Path where symlink will be created
            config: Scaffold configuration
            logger: Optional logger

        Returns:
            WorkspaceInfo with updated path (pointing to symlink) and read-only patterns

        Workflow:
            1. Resolve commit_hash -> actual workspace path via RestoreManager
            2. Create symlink: link_path -> actual workspace path
            3. Return updated WorkspaceInfo with symlink path and read-only patterns set
        """
        if not workspace_spec.commit_hash:
            raise ValueError(
                f"Workspace '{workspace_spec.name}' must have commit_hash for Lean tasks. "
                f"Got: {workspace_spec.model_dump()}"
            )

        # Resolve commit_hash to actual workspace path
        # Check if link_path already exists as a directory (not symlink)
        # This happens when IsolatedLocalRuntime creates full copies
        # In this case, skip symlink creation and use the existing directory
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

        actual_workspace_path = await cls._resolve_lean_workspace(
            commit_hash=workspace_spec.commit_hash,
            repo_url=workspace_spec.repo_url,
            config=config,
            logger=logger
        )

        # Create symlink (remove existing symlink or file if present)
        if link_path.is_symlink():
            link_path.unlink()
        elif link_path.exists():
            # This is a file (not directory, not symlink) - remove it
            link_path.unlink()
        link_path.symlink_to(actual_workspace_path, target_is_directory=True)

        read_only_patterns = workspace_spec.read_only_path_patterns or ["**/*"]
        return workspace_spec.model_copy(update={
            "path": link_path,
            "read_only_path_patterns": read_only_patterns
        })

    @classmethod
    async def _resolve_lean_workspace(
        cls,
        commit_hash: str,
        repo_url: Optional[str] = None,
        config: Optional['BaseScaffoldConfig'] = None,
        logger: Optional['logging.LoggerAdapter'] = None
    ) -> Path:
        """Resolve commit_hash to actual Lean workspace path via RestoreManager (class method).

        Args:
            commit_hash: Git commit hash
            repo_url: Repository URL (None for default mathlib4)
            config: Scaffold configuration
            logger: Optional logger

        Returns:
            Path to the workspace directory

        Raises:
            RuntimeError: If workspace cannot be resolved or prepared
        """
        try:
            from ape.toolkits.execute.lean.core.restore_manager import RestoreManager
            from ape.toolkits.execute.lean.config import LeanVerifyToolConfig

            verify_config = LeanVerifyToolConfig()
            repo_name, resolved_url = verify_config.resolve_repo(repo_url)

            if logger:
                logger.info(f"Resolving Lean workspace: {repo_name}@{commit_hash}")

            restore_manager = RestoreManager(verify_config, logger, resolved_url)
            workspace_path = await restore_manager.get_workspace(commit_hash)

            if not workspace_path:
                raise RuntimeError(
                    f"RestoreManager returned None for {repo_name}@{commit_hash}"
                )

            return workspace_path

        except Exception as e:
            if logger:
                logger.error(
                    f"Failed to resolve workspace for {commit_hash}: {traceback.format_exc()}"
                )
            raise RuntimeError(
                f"Cannot resolve Lean workspace for commit {commit_hash}: {e}"
            ) from e
