"""Workspace source resolution helpers for plain-source tasks."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ape.tasks.models import WorkspaceInfo

if TYPE_CHECKING:
    import logging


def describe_workspace_source(workspace_spec: WorkspaceInfo) -> str:
    """Return a readable description of a workspace source."""
    if workspace_spec.is_local_source:
        return f"local:{workspace_spec.resolved_source_path}"

    git_source = workspace_spec.git_source
    if git_source is not None:
        repo_url = git_source.repo_url or "<default-repo>"
        return f"git:{repo_url}@{git_source.commit_hash}"

    return f"workspace:{workspace_spec.name}"


async def resolve_plain_source_workspace(
    workspace_spec: WorkspaceInfo,
    logger: Optional["logging.LoggerAdapter"] = None,
) -> Path:
    """Resolve a plain-source workspace from either a local directory or git source."""
    if workspace_spec.is_local_source:
        source_path = workspace_spec.resolved_source_path
        if not source_path.exists():
            raise FileNotFoundError(
                f"Local workspace source does not exist: {source_path}"
            )
        if not source_path.is_dir():
            raise NotADirectoryError(
                f"Local workspace source is not a directory: {source_path}"
            )
        if logger:
            logger.info(
                f"Using local workspace source for {workspace_spec.name}: {source_path}"
            )
        return source_path

    git_source = workspace_spec.git_source
    if git_source is None:
        raise ValueError(
            f"Workspace '{workspace_spec.name}' must declare either a local source or a git source. "
            f"Got: {workspace_spec.model_dump()}"
        )

    try:
        from ape.toolkits.execute.base_source_manager import BaseSourceManager
        from ape.toolkits.execute.config import CodeExecuteToolConfig

        source_config = CodeExecuteToolConfig()

        if logger:
            logger.info(
                f"Getting plain workspace for {git_source.commit_hash[:8]} "
                f"from {git_source.repo_url or '<default-repo>'}"
            )

        source_manager = BaseSourceManager(
            config=source_config,
            logger=logger,
            repo_url=git_source.repo_url,
        )

        workspace_path = await source_manager.get_workspace(git_source.commit_hash)
        if not workspace_path:
            raise RuntimeError(
                f"Failed to get workspace for {git_source.commit_hash}"
            )

        return workspace_path

    except Exception as exc:
        if logger:
            logger.error(
                f"Failed to get workspace from {describe_workspace_source(workspace_spec)}: "
                f"{traceback.format_exc()}"
            )
        raise RuntimeError(
            f"Cannot get workspace from {describe_workspace_source(workspace_spec)}: {exc}"
        ) from exc
