"""Base classes for Lean-specific tasks.

This module provides BaseLeanTask and BaseLeanTaskData which handle
Lean workspace setup, repository management, and Lean-specific execution patterns.

Key Design:
- BaseLeanTaskData defines workspace specifications (commit_hash + repo_url)
- BaseLeanTask.setup_attempt() creates symlinks from attempt_path/workspaces/ to actual Lean repos
- Symlinks allow uniform path access (e.g., 'target/', 'reference/<name>/') regardless of where repos are stored
"""

import inspect
import json
import tempfile
import traceback
from typing import Optional, List, TYPE_CHECKING, Callable, Any
from pathlib import Path
from pydantic import Field

from ..base import BaseTask, BaseTaskData
from ..models import WorkspaceInfo

if TYPE_CHECKING:
    from ape.scaffolds.config import BaseScaffoldConfig
    import logging


class BaseLeanTaskData(BaseTaskData):
    """Base data model for all Lean tasks.

    All Lean tasks require a target_workspace and may optionally have reference_workspaces.
    Workspaces are specified by commit_hash + repo_url, not by local paths.
    """

    target_workspace: WorkspaceInfo = Field(
        ...,
        description="Target workspace specification (commit_hash, repo_url, default_target, toolchain)"
    )

    reference_workspaces: Optional[List[WorkspaceInfo]] = Field(
        default=None,
        description="Optional reference workspaces for semantic retrieval"
    )


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
    target_workspace: Optional[WorkspaceInfo] = None
    reference_workspaces: Optional[List[WorkspaceInfo]] = None

    async def setup(
        self,
        termination_callback,
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
    ) -> 'logging.LoggerAdapter':
        """Set up Lean task workspaces and auto-build CLI retrieval indices when needed."""
        logger = await super().setup(termination_callback, orchestrator_id, attempt_path)
        await self._ensure_cli_retrieve_indices_ready()
        return logger

    def _lean_retrieve_enabled(self) -> bool:
        """Return True when the task configuration enables the lean_retrieve tool."""
        task_config = getattr(self.config, "task_config", None)
        if task_config is None:
            return True

        enabled_tools = getattr(task_config, "enabled_tools", None)
        if enabled_tools is not None:
            return "lean_retrieve" in enabled_tools

        disabled_tools = set(getattr(task_config, "disabled_tools", None) or [])
        return "lean_retrieve" not in disabled_tools

    def _iter_retrieve_workspaces(self) -> List[WorkspaceInfo]:
        """Collect Git-backed workspaces relevant to lean_retrieve."""
        workspaces: List[WorkspaceInfo] = []
        if self.target_workspace and self.target_workspace.commit_hash and self.target_workspace.repo_url:
            workspaces.append(self.target_workspace)

        for workspace in self.reference_workspaces or []:
            if workspace and workspace.commit_hash and workspace.repo_url:
                workspaces.append(workspace)

        return workspaces

    def _retrieve_index_ready(self, workspace_spec: WorkspaceInfo) -> bool:
        """Check whether retrieval artifacts exist for a workspace commit."""
        retrieve_config = self.config.tools_config.lean_retrieve
        commit_index_file = (
            retrieve_config.get_commit_index_dir(workspace_spec.repo_url)
            / f"{workspace_spec.commit_hash}.jsonl"
        )
        annotated_ids_file = retrieve_config.get_annotated_ids_file(workspace_spec.repo_url)
        chroma_db_file = retrieve_config.get_storage_dir(workspace_spec.repo_url) / "chroma_db" / "chroma.sqlite3"
        return (
            commit_index_file.exists()
            and annotated_ids_file.exists()
            and chroma_db_file.exists()
        )

    def _missing_retrieve_workspaces(self) -> List[WorkspaceInfo]:
        """Return unique workspaces whose retrieval artifacts are missing."""
        missing: List[WorkspaceInfo] = []
        seen: set[tuple[str, str, Optional[str]]] = set()

        for workspace_spec in self._iter_retrieve_workspaces():
            key = (
                workspace_spec.repo_url,
                workspace_spec.commit_hash,
                workspace_spec.default_target,
            )
            if key in seen:
                continue
            seen.add(key)

            if not self._retrieve_index_ready(workspace_spec):
                missing.append(workspace_spec)

        return missing

    @staticmethod
    def _format_retrieve_workspace_label(workspace_spec: WorkspaceInfo) -> str:
        """Create a concise repo@commit label for user-facing messages."""
        from ape.utils.file_ops import normalize_repo_url

        repo_name = normalize_repo_url(workspace_spec.repo_url) if workspace_spec.repo_url else workspace_spec.name
        commit_prefix = workspace_spec.commit_hash[:8] if workspace_spec.commit_hash else "unknown"
        return f"{repo_name}@{commit_prefix}"

    @staticmethod
    def _format_retrieve_repo_spec(workspace_spec: WorkspaceInfo) -> str:
        """Format a workspace in the builder's repo_url@@commit@@target CLI syntax."""
        spec = f"{workspace_spec.repo_url}@@{workspace_spec.commit_hash}"
        if workspace_spec.default_target:
            spec = f"{spec}@@{workspace_spec.default_target}"
        return spec

    def _format_retrieve_build_command(self, missing_workspaces: List[WorkspaceInfo]) -> str:
        """Build a single manual builder command for the missing workspaces."""
        if not missing_workspaces:
            return "python -m ape.toolkits.retrieve.lean.build"

        command_parts = [
            "python -m ape.toolkits.retrieve.lean.build",
            f'--target_repo "{self._format_retrieve_repo_spec(missing_workspaces[0])}"',
        ]
        for workspace_spec in missing_workspaces[1:]:
            command_parts.append(
                f'--reference_repo "{self._format_retrieve_repo_spec(workspace_spec)}"'
            )
        return " ".join(command_parts)

    def _retrieve_build_num_processes(self) -> int:
        """Run on-demand CLI builds in the main process to avoid fork issues."""
        return 0

    async def _run_retrieve_build(self, missing_workspaces: List[WorkspaceInfo]) -> None:
        """Run the Lean retrieval builder for the missing workspace commits."""
        from ape.toolkits.retrieve.lean.build import main as build_retrieve_main

        temp_file_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                suffix=".jsonl",
                delete=False,
                encoding="utf-8",
            ) as handle:
                temp_file_path = Path(handle.name)
                for workspace_spec in missing_workspaces:
                    record = {
                        "target_workspace": {
                            "name": workspace_spec.name,
                            "commit_hash": workspace_spec.commit_hash,
                            "repo_url": workspace_spec.repo_url,
                            "default_target": workspace_spec.default_target,
                            "toolchain": workspace_spec.toolchain,
                        }
                    }
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")

            cli_overrides = {
                "scaffold_type": getattr(self.config, "scaffold_type", "ape_agent"),
                "num_processes": self._retrieve_build_num_processes(),
            }

            model_name = getattr(getattr(self.config, "llm_config", None), "model_name", None)
            if model_name:
                cli_overrides["model"] = model_name

            exit_code = await build_retrieve_main(
                input_file=temp_file_path,
                orchestrator_id=f"cli_retrieve_{self.data.global_index[:12]}",
                cli_overrides=cli_overrides,
                logger=self.logger,
                progress_callback=self.emit_progress,
            )
            if exit_code not in (0, None):
                raise RuntimeError(f"Builder exited with code {exit_code}")
        finally:
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()

    async def _ensure_cli_retrieve_indices_ready(self) -> None:
        """Auto-build missing retrieval indices for CLI Lean tasks before tool registration."""
        if not getattr(self, "is_cli_mode", False):
            return

        if not self._lean_retrieve_enabled():
            return

        missing_workspaces = self._missing_retrieve_workspaces()
        if not missing_workspaces:
            return

        workspace_summary = ", ".join(
            self._format_retrieve_workspace_label(workspace_spec)
            for workspace_spec in missing_workspaces
        )

        if self.logger:
            self.logger.info(
                "Missing Lean retrieval artifacts for %s; starting CLI auto-build",
                workspace_summary,
            )

        await self.emit_progress(
            "Lean retrieval index missing for "
            f"{workspace_summary}; building it now. This may take several minutes."
        )

        try:
            await self._run_retrieve_build(missing_workspaces)
        except Exception as exc:
            manual_command = self._format_retrieve_build_command(missing_workspaces)
            raise RuntimeError(
                "Failed to auto-build Lean retrieval index for "
                f"{workspace_summary}. Run `{manual_command}` manually or disable "
                "`lean_retrieve` for this CLI task."
            ) from exc

        remaining_missing = self._missing_retrieve_workspaces()
        if remaining_missing:
            remaining_summary = ", ".join(
                self._format_retrieve_workspace_label(workspace_spec)
                for workspace_spec in remaining_missing
            )
            manual_command = self._format_retrieve_build_command(remaining_missing)
            raise RuntimeError(
                "Lean retrieval auto-build completed, but artifacts are still missing for "
                f"{remaining_summary}. Run `{manual_command}` manually and retry."
            )

        if self.logger:
            self.logger.info(
                "Lean retrieval artifacts ready for %s after CLI auto-build",
                workspace_summary,
            )

        await self.emit_progress(f"Lean retrieval index ready for {workspace_summary}.")

    @classmethod
    async def setup_attempt(
        cls,
        data: 'BaseLeanTaskData',
        config: 'BaseScaffoldConfig',
        orchestrator_id: str,
        attempt_path: Optional[Path] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        progress_callback: Optional[Callable[[str], Any]] = None,
    ) -> tuple[Path, WorkspaceInfo, Optional[WorkspaceInfo], Optional[List[WorkspaceInfo]]]:
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
            data,
            config,
            orchestrator_id,
            attempt_path,
            logger,
            progress_callback,
        )

        # Calculate workspaces_dir (classmethod cannot access self)
        workspaces_dir = attempt_path / config.workspaces_dir_name

        # Setup target workspace symlink (required for Lean tasks)
        await cls._emit_progress(
            progress_callback,
            f"Resolving target Lean workspace {data.target_workspace.name}@{data.target_workspace.commit_hash[:8]}...",
        )
        target_workspace = await cls._setup_workspace_symlink(
            workspace_spec=data.target_workspace,
            link_path=workspaces_dir / "target",
            config=config,
            logger=logger,
            progress_callback=progress_callback,
        )

        # Setup reference workspace symlinks (optional)
        reference_workspaces = None
        if data.reference_workspaces:
            reference_workspaces = []
            ref_base_dir = workspaces_dir / "reference"
            ref_base_dir.mkdir(parents=True, exist_ok=True)

            for ref_ws in data.reference_workspaces:
                await cls._emit_progress(
                    progress_callback,
                    f"Resolving reference Lean workspace {ref_ws.name}@{ref_ws.commit_hash[:8]}...",
                )
                linked_ref = await cls._setup_workspace_symlink(
                    workspace_spec=ref_ws,
                    link_path=ref_base_dir / ref_ws.name,
                    config=config,
                    logger=logger,
                    progress_callback=progress_callback,
                )
                reference_workspaces.append(linked_ref)

        return attempt_path, scratch_workspace, target_workspace, reference_workspaces

    @classmethod
    async def _setup_workspace_symlink(
        cls,
        workspace_spec: WorkspaceInfo,
        link_path: Path,
        config: 'BaseScaffoldConfig',
        logger: Optional['logging.LoggerAdapter'] = None,
        progress_callback: Optional[Callable[[str], Any]] = None,
    ) -> WorkspaceInfo:
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
            logger=logger,
            progress_callback=progress_callback,
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
        logger: Optional['logging.LoggerAdapter'] = None,
        progress_callback: Optional[Callable[[str], Any]] = None,
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

            await cls._emit_progress(
                progress_callback,
                f"Checking cached Lean workspace for {repo_name}@{commit_hash[:8]}...",
            )

            restore_manager = RestoreManager(
                verify_config,
                logger,
                resolved_url,
                progress_callback=progress_callback,
            )
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

    @staticmethod
    async def _emit_progress(
        progress_callback: Optional[Callable[[str], Any]],
        message: str,
    ) -> None:
        """Emit a user-facing progress update when configured."""
        if not progress_callback:
            return

        result = progress_callback(message)
        if inspect.isawaitable(result):
            await result
