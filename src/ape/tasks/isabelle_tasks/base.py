"""Base classes for Isabelle-specific tasks.

Isabelle tasks use plain source workspaces and session-aware workspace metadata.
"""

from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

from pydantic import Field, field_validator

from ..base import BaseTask, BaseTaskData
from ..models import WorkspaceInfo, IsabelleWorkspaceInfo, parse_workspace_info
from ..workspace_sources import resolve_plain_source_workspace

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class BaseIsabelleTaskData(BaseTaskData):
    """Base data model for Isabelle tasks."""

    target_workspace: IsabelleWorkspaceInfo = Field(
        ...,
        description="Target Isabelle workspace specification"
    )

    @field_validator("target_workspace", mode="before")
    @classmethod
    def validate_target_workspace(cls, value: Any) -> IsabelleWorkspaceInfo:
        """Preserve explicit Isabelle workspace metadata during parsing."""
        workspace = parse_workspace_info(value)
        if isinstance(workspace, IsabelleWorkspaceInfo):
            return workspace
        return IsabelleWorkspaceInfo.model_validate(workspace.model_dump())


class BaseIsabelleTask(BaseTask):
    """Base class for Isabelle tasks using plain worktrees."""

    target_workspace: Optional[IsabelleWorkspaceInfo] = None

    @classmethod
    async def setup_attempt(
        cls,
        data: "BaseIsabelleTaskData",
        config: "BaseScaffoldConfig",
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
        logger: Optional["logging.LoggerAdapter"] = None,
    ) -> tuple[Path, WorkspaceInfo, Optional[IsabelleWorkspaceInfo], None]:
        """Set up scratch and target workspaces for Isabelle tasks."""
        attempt_path, scratch_workspace, _, _ = await super().setup_attempt(
            data, config, orchestrator_id, attempt_path, logger
        )

        workspaces_dir = attempt_path / config.workspaces_dir_name
        target_workspace = await cls._setup_plain_workspace_symlink(
            workspace_spec=data.target_workspace,
            link_path=workspaces_dir / "target",
            config=config,
            logger=logger,
        )

        return attempt_path, scratch_workspace, target_workspace, None

    @classmethod
    async def _setup_plain_workspace_symlink(
        cls,
        workspace_spec: IsabelleWorkspaceInfo,
        link_path: Path,
        config: "BaseScaffoldConfig",
        logger: Optional["logging.LoggerAdapter"] = None,
    ) -> IsabelleWorkspaceInfo:
        """Resolve the workspace and expose it under the task workspaces directory."""
        if link_path.exists() and link_path.is_dir() and not link_path.is_symlink():
            if logger:
                logger.info(
                    f"Workspace {workspace_spec.name} already exists as directory at {link_path}, "
                    f"using existing (IsolatedLocalRuntime mode)"
                )
            read_only_patterns = workspace_spec.read_only_path_patterns or ["**/*"]
            return workspace_spec.model_copy(update={
                "path": link_path,
                "read_only_path_patterns": read_only_patterns,
            })

        del config  # Plain workspace resolution only depends on workspace source spec.
        actual_workspace_path = await resolve_plain_source_workspace(
            workspace_spec=workspace_spec,
            logger=logger,
        )

        if link_path.is_symlink():
            link_path.unlink()
        elif link_path.exists():
            link_path.unlink()
        link_path.symlink_to(actual_workspace_path, target_is_directory=True)

        read_only_patterns = workspace_spec.read_only_path_patterns or ["**/*"]
        return workspace_spec.model_copy(update={
            "path": link_path,
            "read_only_path_patterns": read_only_patterns,
        })
