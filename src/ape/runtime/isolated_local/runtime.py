"""Isolated Local Runtime - Full copy workspace isolation with permission control.

This runtime provides workspace isolation by creating FULL COPIES of workspaces
directly (not through symlinks). Key differences from standard setup:

1. Standard flow: RestoreManager -> hardlink files -> symlink to workspace
2. Isolated flow: RestoreManager -> COPY files directly (no hardlinks, no symlinks)

Design rationale:
- Containers provide the best isolation but introduce engineering complexity
- Hardlinks in data workspace save storage but prevent permission control
- This runtime copies workspace files directly, allowing full permission control
- No symlinks means no conflict between symlink/directory states
"""

import asyncio
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, TYPE_CHECKING
import traceback

from pydantic import Field

from ape.runtime.base import BaseRuntime, RuntimeConfig
from ape.runtime.utils import collect_blocked_paths, collect_readonly_paths

if TYPE_CHECKING:
    import logging
    from ape.scaffolds.base import ScaffoldTerminationResult
    from ape.scaffolds.config import BaseScaffoldConfig
    from ape.tasks.base import BaseTaskResult
    from ape.tasks.models import WorkspaceInfo


# =============================================================================
# Configuration
# =============================================================================

class IsolatedLocalRuntimeConfig(RuntimeConfig):
    """Configuration for isolated local runtime."""

    runtime_type: Literal['isolated_local'] = Field(
        default='isolated_local',
        description="Isolated local runtime type"
    )

    copy_timeout: int = Field(
        default=600,
        description="Timeout in seconds for copying workspace directory"
    )


# =============================================================================
# Workspace Copy Tracking
# =============================================================================

@dataclass
class WorkspaceCopyRecord:
    """Track information about a fully-copied workspace."""

    workspace_path: Path
    """Path to the copied workspace directory"""

    workspace_name: str
    """Workspace name for logging"""

    is_copied: bool = False
    """Whether the copy was successfully created"""


@dataclass
class IsolationContext:
    """Context for workspace isolation during a single task execution."""

    copy_records: List[WorkspaceCopyRecord] = field(default_factory=list)
    """Records of all workspaces that were fully copied"""

    permission_changes: Dict[Path, int] = field(default_factory=dict)
    """Original permissions for paths that were modified"""


# =============================================================================
# Isolated Local Runtime
# =============================================================================

class IsolatedLocalRuntime(BaseRuntime):
    """Local runtime with workspace isolation via FULL file copying.

    Key difference from standard setup:
    - Standard: Creates symlinks to data workspace (which uses hardlinks)
    - Isolated: Copies all files directly to workspace path (no symlinks, no hardlinks)

    This allows:
    1. Full permission control on workspace files
    2. No risk of modifying shared content store
    3. Clean workspace state (no symlink/directory conflicts)

    Workflow:
    1. Setup Phase: Copy workspace files directly (using ContentStore with force copy)
    2. Permission Phase: Apply blocked/readonly permissions
    3. Execution Phase: Run task
    4. Cleanup Phase: Remove copied workspaces
    """

    config_class = IsolatedLocalRuntimeConfig

    def __init__(
        self,
        config: IsolatedLocalRuntimeConfig,
        logger: Optional['logging.LoggerAdapter'] = None
    ):
        super().__init__(config, logger)
        self.config: IsolatedLocalRuntimeConfig = config

    async def run_task(
        self,
        task_data: dict,
        config: 'BaseScaffoldConfig',
        scaffold_type: str,
        orchestrator_id: str,
        attempt_path: Path,
        cost_limit: Optional[float] = None,
    ) -> Tuple['BaseTaskResult', Optional['ScaffoldTerminationResult']]:
        """Execute task with fully-copied isolated workspaces.

        Workflow:
        1. Setup: Create workspaces with full file copies (no hardlinks)
        2. Permission: Apply access control
        3. Execute: Run task
        4. Cleanup: Remove copied workspaces
        """
        from ape.scaffolds.runner import main_from_params
        from ape.tasks.base import get_task_class
        from ape.utils.logging import create_logger

        task_type = task_data.get('task_type')
        if not task_type:
            raise ValueError("task_data must contain 'task_type' field")

        task_id = task_data.get('task_id', 'unknown')

        # Setup runtime-specific logger
        logs_dir = attempt_path / config.logs_dir_name
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        runtime_log_file = logs_dir / f"runtime_{timestamp}.log"

        original_logger = self.logger
        self.logger = create_logger(log_file=runtime_log_file, to_console=False)

        # Initialize isolation context
        isolation_ctx = IsolationContext()

        try:
            self.logger.info(
                f"[IsolatedLocalRuntime] Starting task {task_id} "
                f"type={task_type} (isolated local execution)"
            )

            # Phase 1: Setup workspaces with FULL COPIES (no symlinks, no hardlinks)
            task_class = get_task_class(task_type)
            task_data_obj = task_class.create_data_from_dict(task_data)

            # Create attempt directory structure
            attempt_path, scratch_workspace, target_workspace, reference_workspaces = \
                await self._setup_isolated_workspaces(
                    isolation_ctx=isolation_ctx,
                    task_class=task_class,
                    task_data=task_data_obj,
                    config=config,
                    orchestrator_id=orchestrator_id,
                    attempt_path=attempt_path
                )

            # Phase 2: Apply access control permissions
            await self._apply_access_control(
                isolation_ctx=isolation_ctx,
                scratch_workspace=scratch_workspace,
                target_workspace=target_workspace,
                reference_workspaces=reference_workspaces
            )

            # Phase 3: Execute task
            self.logger.info(f"[IsolatedLocalRuntime] Executing task {task_id}")

            params = {
                'task_data': task_data,
                'config': config.model_dump(mode='json'),
                'scaffold_type': scaffold_type,
                'orchestrator_id': orchestrator_id,
                'cost_limit': cost_limit,
                'attempt_path': str(attempt_path),
            }

            task_result, termination = await main_from_params(params)

            self.logger.info(
                f"[IsolatedLocalRuntime] Task completed "
                f"success={task_result.success} score={task_result.score:.3f}"
            )

            return task_result, termination

        finally:
            # Phase 4: Cleanup copied workspaces
            await self._cleanup_workspaces(isolation_ctx)

            # Cleanup logger
            try:
                if self.logger:
                    for handler in self.logger.logger.handlers[:]:
                        try:
                            handler.close()
                            self.logger.logger.removeHandler(handler)
                        except Exception:
                            pass
            finally:
                self.logger = original_logger

    # =========================================================================
    # Workspace Setup: Full Copy (No Symlinks)
    # =========================================================================

    async def _setup_isolated_workspaces(
        self,
        isolation_ctx: IsolationContext,
        task_class,
        task_data,
        config: 'BaseScaffoldConfig',
        orchestrator_id: str,
        attempt_path: Path
    ) -> Tuple[Path, 'WorkspaceInfo', Optional['WorkspaceInfo'], Optional[List['WorkspaceInfo']]]:
        """Setup workspaces with full file copies (no symlinks, no hardlinks).

        This replaces the standard setup_attempt flow for Lean tasks.
        Instead of creating symlinks to data workspace, we:
        1. Get the snapshot from RestoreManager
        2. Copy all files directly to workspace path (force copy, no hardlinks)
        """
        from ape.tasks.base import BaseTask
        from ape.tasks.models import WorkspaceInfo

        # Create basic directory structure (logs, conversations, workspaces)
        attempt_path = await BaseTask._ensure_attempt_path(
            config, orchestrator_id, attempt_path, task_data,
            task_class.task_type if hasattr(task_class, 'task_type') else None
        )

        workspaces_dir = attempt_path / config.workspaces_dir_name
        workspaces_dir.mkdir(parents=True, exist_ok=True)

        # Create scratch workspace (actual directory)
        scratch_path = workspaces_dir / "scratch"
        scratch_path.mkdir(parents=True, exist_ok=True)

        scratch_workspace = WorkspaceInfo(
            name="scratch",
            path=scratch_path,
            commit_hash=None,
            repo_url=None,
            default_target=None
        )

        # Setup target workspace with FULL COPY
        target_workspace = None
        if hasattr(task_data, 'target_workspace') and task_data.target_workspace:
            target_path = workspaces_dir / "target"
            target_workspace = await self._setup_workspace_full_copy(
                isolation_ctx=isolation_ctx,
                workspace_spec=task_data.target_workspace,
                output_path=target_path,
                workspace_name="target",
                config=config
            )

        # Setup reference workspaces with FULL COPY
        reference_workspaces = None
        if hasattr(task_data, 'reference_workspaces') and task_data.reference_workspaces:
            reference_workspaces = []
            ref_base_dir = workspaces_dir / "reference"
            ref_base_dir.mkdir(parents=True, exist_ok=True)

            for ref_ws in task_data.reference_workspaces:
                ref_path = ref_base_dir / ref_ws.name
                linked_ref = await self._setup_workspace_full_copy(
                    isolation_ctx=isolation_ctx,
                    workspace_spec=ref_ws,
                    output_path=ref_path,
                    workspace_name=f"reference/{ref_ws.name}",
                    config=config
                )
                reference_workspaces.append(linked_ref)

        return attempt_path, scratch_workspace, target_workspace, reference_workspaces

    async def _setup_workspace_full_copy(
        self,
        isolation_ctx: IsolationContext,
        workspace_spec: 'WorkspaceInfo',
        output_path: Path,
        workspace_name: str,
        config: 'BaseScaffoldConfig'
    ) -> 'WorkspaceInfo':
        """Setup a workspace by copying the entire directory (no symlinks, no hardlinks)."""
        from ape.toolkits.execute.lean.core.restore_manager import RestoreManager
        from ape.toolkits.execute.lean.config import LeanVerifyToolConfig

        if not workspace_spec.commit_hash:
            raise ValueError(
                f"Workspace '{workspace_spec.name}' must have commit_hash. "
                f"Got: {workspace_spec.model_dump()}"
            )

        commit_hash = workspace_spec.commit_hash
        repo_url = workspace_spec.repo_url

        self.logger.info(
            f"[IsolatedLocalRuntime] Setting up isolated workspace {workspace_name}: "
            f"{commit_hash}"
        )

        # Get config and resolve repo
        verify_config = LeanVerifyToolConfig()
        repo_name, resolved_url = verify_config.resolve_repo(repo_url)

        # Get the data workspace path via RestoreManager
        restore_manager = RestoreManager(verify_config, self.logger, resolved_url)
        data_workspace_path = await restore_manager.get_workspace(commit_hash)

        if not data_workspace_path or not data_workspace_path.exists():
            raise RuntimeError(
                f"Failed to get data workspace for {repo_name}@{commit_hash}"
            )

        # Track this workspace for cleanup
        record = WorkspaceCopyRecord(
            workspace_path=output_path,
            workspace_name=workspace_name,
            is_copied=False
        )
        isolation_ctx.copy_records.append(record)

        # Copy entire directory
        await self._copy_workspace_directory(
            source_path=data_workspace_path,
            output_path=output_path
        )

        record.is_copied = True

        self.logger.info(
            f"[IsolatedLocalRuntime] Workspace {workspace_name} copied successfully"
        )

        # Return WorkspaceInfo with the copied path
        read_only_patterns = workspace_spec.read_only_path_patterns or ["**/*"]

        return workspace_spec.model_copy(update={
            "path": output_path,
            "read_only_path_patterns": read_only_patterns
        })

    async def _copy_workspace_directory(
        self,
        source_path: Path,
        output_path: Path
    ) -> None:
        """Copy entire workspace directory using shutil.copytree.

        Uses copy2 to ensure full file copies (no hardlinks).
        """
        from ape.utils.file_ops import safe_remove_directory

        start_time = datetime.now()

        self.logger.info(
            f"[IsolatedLocalRuntime] Copying workspace: {source_path} -> {output_path}"
        )

        # Remove output_path if it exists (using safe removal to handle readonly files)
        if output_path.exists():
            await safe_remove_directory(output_path)

        def copy_tree_sync():
            # Copy entire directory tree with full file copies
            shutil.copytree(
                src=source_path,
                dst=output_path,
                symlinks=True,  # Preserve symlinks
                copy_function=shutil.copy2,  # Full copy, not hardlink
                dirs_exist_ok=False
            )

        try:
            await asyncio.wait_for(
                asyncio.to_thread(copy_tree_sync),
                timeout=self.config.copy_timeout
            )
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"Workspace copy timed out after {self.config.copy_timeout}s"
            )

        elapsed = (datetime.now() - start_time).total_seconds()
        self.logger.info(
            f"[IsolatedLocalRuntime] Copy completed in {elapsed:.2f}s"
        )

    # =========================================================================
    # Access Control: Permission Phase
    # =========================================================================

    async def _apply_access_control(
        self,
        isolation_ctx: IsolationContext,
        scratch_workspace: Optional['WorkspaceInfo'],
        target_workspace: Optional['WorkspaceInfo'],
        reference_workspaces: Optional[List['WorkspaceInfo']]
    ) -> None:
        """Apply file permission-based access control."""
        all_blocked: List[Path] = []
        all_readonly: List[Path] = []

        for ws in [scratch_workspace, target_workspace]:
            if ws:
                all_blocked.extend(collect_blocked_paths(ws, self.logger))
                all_readonly.extend(collect_readonly_paths(ws, self.logger))

        if reference_workspaces:
            for ref_ws in reference_workspaces:
                if ref_ws:
                    all_blocked.extend(collect_blocked_paths(ref_ws, self.logger))
                    all_readonly.extend(collect_readonly_paths(ref_ws, self.logger))

        # Apply readonly first, then blocked (to prevent readonly from overwriting blocked)
        # Since readonly uses find to recursively chmod, it would overwrite any previously blocked files
        if all_readonly:
            await self._apply_readonly_permissions(isolation_ctx, all_readonly)

        if all_blocked:
            await self._apply_blocked_permissions(isolation_ctx, all_blocked)

    async def _apply_blocked_permissions(
        self,
        isolation_ctx: IsolationContext,
        blocked_paths: List[Path]
    ) -> None:
        """Make paths completely inaccessible (chmod 000).

        Uses shell commands for batch processing to improve performance.
        Note: No need to save original permissions since isolated runtime
        will delete the entire workspace during cleanup.
        """
        if not blocked_paths:
            return

        # Filter existing paths
        existing_paths = [p for p in blocked_paths if p.exists()]

        if not existing_paths:
            return

        self.logger.info(f"[IsolatedLocalRuntime] Blocking {len(existing_paths)} paths")

        # Use shell command for batch chmod
        def chmod_batch():
            # Process in batches to avoid command line length limits
            batch_size = 100
            for i in range(0, len(existing_paths), batch_size):
                batch = existing_paths[i:i + batch_size]
                # Build chmod command with all paths
                cmd = ['chmod', '000'] + [str(p) for p in batch]
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    self.logger.warning(
                        f"[IsolatedLocalRuntime] chmod batch failed (batch {i//batch_size + 1}): {e.stderr.decode()}"
                    )

        try:
            await asyncio.to_thread(chmod_batch)
            self.logger.debug(f"[IsolatedLocalRuntime] Successfully blocked {len(existing_paths)} paths")
        except Exception as e:
            self.logger.warning(f"[IsolatedLocalRuntime] Failed to apply blocked permissions: {e}")

    async def _apply_readonly_permissions(
        self,
        isolation_ctx: IsolationContext,
        readonly_paths: List[Path]
    ) -> None:
        """Make paths read-only."""
        for path in readonly_paths:
            if not path.exists():
                continue

            try:
                await self._set_readonly_recursive(isolation_ctx, path)
                self.logger.debug(f"[IsolatedLocalRuntime] Set readonly: {path}")
            except Exception as e:
                self.logger.warning(f"[IsolatedLocalRuntime] Failed to set readonly {path}: {e}")

    async def _set_readonly_recursive(
        self,
        isolation_ctx: IsolationContext,
        path: Path
    ) -> None:
        """Recursively set path and all contents to readonly.

        Uses shell commands (find + chmod) for batch processing to improve performance.
        Note: No need to save original permissions since isolated runtime
        will delete the entire workspace during cleanup.
        """
        def set_readonly_sync():
            if path.is_file():
                # Single file: just chmod
                os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            elif path.is_dir():
                # Directory: use find + chmod for batch processing
                # Files: chmod 444 (r--r--r--)
                cmd_files = [
                    'find', str(path), '-type', 'f',
                    '-exec', 'chmod', '444', '{}', '+'
                ]
                try:
                    subprocess.run(cmd_files, check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    self.logger.warning(
                        f"[IsolatedLocalRuntime] Failed to chmod files in {path}: {e.stderr.decode()}"
                    )

                # Directories: chmod 555 (r-xr-xr-x)
                cmd_dirs = [
                    'find', str(path), '-type', 'd',
                    '-exec', 'chmod', '555', '{}', '+'
                ]
                try:
                    subprocess.run(cmd_dirs, check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    self.logger.warning(
                        f"[IsolatedLocalRuntime] Failed to chmod dirs in {path}: {e.stderr.decode()}"
                    )

        await asyncio.to_thread(set_readonly_sync)

    # =========================================================================
    # Cleanup Phase
    # =========================================================================

    async def _cleanup_workspaces(
        self,
        isolation_ctx: IsolationContext
    ) -> None:
        """Clean up copied workspaces after execution.

        Since we created full copies (not symlinks), we just need to delete them.
        No symlink restoration needed.
        """
        if not isolation_ctx.copy_records:
            return

        self.logger.info(
            f"[IsolatedLocalRuntime] Cleaning up {len(isolation_ctx.copy_records)} workspace(s)"
        )

        for record in isolation_ctx.copy_records:
            try:
                await self._cleanup_single_workspace(record)
            except Exception as e:
                self.logger.error(
                    f"[IsolatedLocalRuntime] Failed to cleanup workspace "
                    f"{record.workspace_name}: {e}"
                )

    async def _cleanup_single_workspace(
        self,
        record: WorkspaceCopyRecord
    ) -> None:
        """Clean up a single copied workspace."""
        try:
            from ape.utils.file_ops import safe_remove_directory

            workspace_path = record.workspace_path

            if not workspace_path.exists():
                return

            self.logger.info(
                f"[IsolatedLocalRuntime] Removing copied workspace: {record.workspace_name}"
            )

            # Use safe_remove_directory which handles readonly files
            await safe_remove_directory(workspace_path)

            self.logger.info(
                f"[IsolatedLocalRuntime] Successfully removed workspace {record.workspace_name}"
            )
        except Exception as e:
            self.logger.error(
                f"[IsolatedLocalRuntime] Failed to remove workspace {record.workspace_name}: {traceback.format_exc()}"
            )


# =============================================================================
# Registration
# =============================================================================

from ape.runtime.registry import register_runtime

register_runtime('isolated_local', IsolatedLocalRuntime)
