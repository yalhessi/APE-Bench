"""
Restore manager - simplified exception-driven version.
Use standard exceptions and a small set of business exceptions to fully solve error handling.
"""

import asyncio
import os
import stat
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from datetime import datetime

import aiofiles.os

from ..config import LeanVerifyToolConfig
from ..models import RestoreResult, WorkspaceStatus
from ..core.workspace_state import WorkspaceStateManager
from ..core.storage import ContentStore
from ..core.snapshot import SnapshotManager
from ..utils.process_ops import is_process_alive, run_command
from ape.utils.file_ops import check_disk_space_available, get_disk_usage
from ..utils.exceptions import (
    DiskSpaceError, AlreadyRestoringError, AlreadyBuildingError, 
    WorkspaceFailedError, BuildIncompleteError
)
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging


class RestoreManager:
    """Simplified restore manager - exception-driven design"""

    def __init__(
        self,
        config: Optional[LeanVerifyToolConfig] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        repo_url: Optional[str] = None
    ):
        """Initialize restore manager

        Args:
            config: Configuration object
            logger: Logger
            repo_url: Repository URL
        """
        self.config = config or LeanVerifyToolConfig()
        self.logger = logger or create_logger()
        self.repo_name, self.repo_url = self.config.resolve_repo(repo_url)
        self.workspace_dir = self.config.get_workspace_dir(self.repo_name)
        self.state_manager = WorkspaceStateManager(self.config, self.logger, self.repo_name)
        self.content_store = ContentStore(self.config, self.logger)
        self.snapshot_manager = SnapshotManager(self.config, self.logger, self.repo_name)
        self.logger.info(f"Restore manager initialized [{self.repo_name}]: {self.workspace_dir}")

    async def _requires_build_first(self, commit_hash: str) -> bool:
        """Return True when no built state exists for the requested commit.

        Restore can only operate on an already-built snapshot or an existing
        ready workspace. When neither exists, callers need to run the build
        pipeline first.
        """
        state = await self.state_manager.read_state(commit_hash)
        if state:
            return False

        workspace_path = self.workspace_dir / commit_hash
        if await aiofiles.os.path.exists(workspace_path) and await aiofiles.os.path.isdir(workspace_path):
            return False

        snapshot_path = self.snapshot_manager.snapshot_dir / f"{commit_hash}.snap"
        if await aiofiles.os.path.exists(snapshot_path):
            return False

        return True
    
    async def get_workspace(self, commit_hash: str, timeout: Optional[float] = None) -> Path:
        """Get an available workspace path - main external interface.
        
        Raises:
            Exception: Various error cases, caller needs to handle exceptions
        """
        # 1. Quick path: check if workspace is ready
        workspace_path = self.workspace_dir / commit_hash
        if await aiofiles.os.path.exists(workspace_path) and await aiofiles.os.path.isdir(workspace_path):
            state = await self.state_manager.read_state(commit_hash)
            if state and state.status == WorkspaceStatus.READY:
                self.logger.info(f"Workspace is ready: {commit_hash}")
                return workspace_path
        
        # 2. Need to restore workspace
        restore_result = await self.try_restore(commit_hash, timeout)
        if not restore_result.success:
            raise RuntimeError(f"[{commit_hash}] Restore failed but no exception was thrown: {restore_result.error_message}")

        return restore_result.workspace_path
    
    async def try_restore(self, commit_hash: str, timeout: Optional[float] = None) -> RestoreResult:
        """Try to restore workspace
        
        Raises:
            AlreadyRestoringError: Need to wait for restore completion
            AlreadyBuildingError: Need to wait for build completion
            FileNotFoundError, WorkspaceFailedError, BuildIncompleteError: Need to build first
            OtherException: Restore execution error
        """
        start_time = datetime.now()
        self.logger.info(f"Start trying to restore workspace: {commit_hash}")
        
        try:
            # 1. Atomic attempt to get restore permission
            current_state = await self.state_manager.try_start_restore(commit_hash)
            
            # 2. Execute actual restore
            self.logger.info(f"Get restore permission, start executing restore: {commit_hash}")
            workspace_path = await self._execute_restore(commit_hash)
            
            # 3. Calculate restore time and complete status update
            restore_duration = (datetime.now() - start_time).total_seconds()
            await self.state_manager.complete_restore(
                commit_hash, True, workspace_path, restore_duration
            )
            
            # 4. Return success result
            self.logger.info(f"Restore success: {commit_hash}, time: {restore_duration:.2f}s")
            return RestoreResult(
                success=True,
                commit_hash=commit_hash,
                workspace_path=workspace_path,
                restore_duration=restore_duration
            )
                    
        except AlreadyRestoringError as e:
            # Wait for other processes to complete restore operation
            return await self._wait_for_restore_completion(commit_hash, timeout)
        except TimeoutError as e:
            if await self._requires_build_first(commit_hash):
                raise FileNotFoundError(
                    f"[{commit_hash}] No state or snapshot found after lock timeout, need to build first"
                ) from e
            self.logger.warning(
                f"Get state lock timeout, wait for existing restore to end: {commit_hash} ({e})"
            )
            return await self._wait_for_restore_completion(commit_hash, timeout)

        except AlreadyBuildingError as e:
            # Wait for build completion, then retry restore
            await self._wait_for_build_completion(commit_hash, timeout)
            # Recursive retry restore
            return await self.try_restore(commit_hash, timeout)
        
        except (FileNotFoundError, WorkspaceFailedError, BuildIncompleteError):
            # These errors are directly re-thrown, caller needs to build first
            raise
        
        except Exception as e:
            # Other exceptions: try to update failed status and re-throw
            restore_duration = (datetime.now() - start_time).total_seconds()
            error_message = str(e)
            
            self.logger.error(f"Restore exception {commit_hash}: {error_message}")
            
            try:
                await self.state_manager.complete_restore(
                    commit_hash, False, None, restore_duration, error_message, type(e).__name__
                )
            except Exception:
                # Status update failure cannot prevent exception propagation
                pass
            
            # Re-throw original exception
            raise
    
    async def _wait_for_restore_completion(self, commit_hash: str, timeout: Optional[float]) -> RestoreResult:
        """Wait for other processes to complete restore operation
        
        Raises:
            TimeoutError: Wait timeout
            RuntimeError: Process dead or restore failed
        """
        actual_timeout = timeout or self.config.restore_queue_timeout
        poll_interval = self.config.workspace_restore_poll_interval
        start_time = datetime.now()
        
        self.logger.info(f"Wait for other processes to complete restore: {commit_hash}")
        
        while (datetime.now() - start_time).total_seconds() < actual_timeout:
            # Use lock-free read to avoid deadlocks
            state = await self.state_manager.read_state(commit_hash)
            
            if not state:
                if await self._requires_build_first(commit_hash):
                    raise FileNotFoundError(
                        f"[{commit_hash}] No state or snapshot found while waiting, need to build first"
                    )
                raise RuntimeError(f"[{commit_hash}] State file disappeared during wait")
            
            if state.status == WorkspaceStatus.READY:
                # Restore completed and successful
                workspace_path = self.workspace_dir / commit_hash
                if await aiofiles.os.path.exists(workspace_path) and await aiofiles.os.path.isdir(workspace_path):
                    self.logger.info(f"Wait completed, workspace is ready: {commit_hash}")
                    return RestoreResult(
                        success=True,
                        commit_hash=commit_hash,
                        workspace_path=workspace_path,
                        restore_duration=0.0  # Wait time, actual restore is completed by other processes
                    )
                else:
                    raise RuntimeError(f"[{commit_hash}] State shows READY but workspace directory does not exist")
            
            elif state.status == WorkspaceStatus.FAILED:
                raise RuntimeError(f"[{commit_hash}] Other processes restore failed: {state.error_message}")
            
            elif state.status != WorkspaceStatus.RESTORING:
                raise RuntimeError(f"[{commit_hash}] State abnormal during wait: {state.status}")
            
            # Additional check: restore process is still alive
            if state.restore_pid and not is_process_alive(state.restore_pid):
                raise RuntimeError(f"[{commit_hash}] Waiting for restore process to die (pid={state.restore_pid})")
            
            # Continue waiting
            await asyncio.sleep(poll_interval)
        
        # Timeout
        raise TimeoutError(f"[{commit_hash}] Waiting for restore completion timed out ({actual_timeout}s)")
    
    async def _wait_for_build_completion(self, commit_hash: str, timeout: Optional[float]) -> None:
        """Wait for build operation to complete
        
        Raises:
            TimeoutError: Wait timeout
            RuntimeError: Build process dead or build failed
        """
        actual_timeout = timeout or self.config.restore_queue_timeout  
        poll_interval = self.config.workspace_restore_poll_interval
        start_time = datetime.now()
        
        self.logger.info(f"Wait for build completion: {commit_hash}")
        
        while (datetime.now() - start_time).total_seconds() < actual_timeout:
            state = await self.state_manager.read_state(commit_hash)
            
            if not state:
                raise RuntimeError(f"[{commit_hash}] State file disappeared during wait")
            
            if state.status == WorkspaceStatus.BUILT:
                self.logger.info(f"Build completed: {commit_hash}")
                return  # Completed successfully
            
            elif state.status == WorkspaceStatus.FAILED:
                raise RuntimeError(f"[{commit_hash}] Build failed: {state.error_message}")
            
            elif state.status != WorkspaceStatus.BUILDING:
                raise RuntimeError(f"[{commit_hash}] State abnormal during wait: {state.status}")
            
            # Check if the build process is still alive
            if state.build_pid and not is_process_alive(state.build_pid):
                raise RuntimeError(f"[{commit_hash}] Waiting for build process to die (pid={state.build_pid})")
            
            await asyncio.sleep(poll_interval)
        
        # Timeout
        raise TimeoutError(f"[{commit_hash}] Waiting for build completion timed out ({actual_timeout}s)")
    
    async def _execute_restore(self, commit_hash: str) -> Path:
        """Execute actual restore process

        Raises:
            FileNotFoundError: Snapshot not found
            ValueError: Snapshot corrupted
            DiskSpaceError: Not enough disk space
            RuntimeError: Execution process error
        """
        # 0. If workspace already exists, use it directly (skip snapshot restore)
        workspace_path = self.workspace_dir / commit_hash
        if await aiofiles.os.path.exists(workspace_path) and await aiofiles.os.path.isdir(workspace_path):
            # Check if workspace has files (not empty)
            entries = await asyncio.to_thread(os.listdir, workspace_path)
            if entries:
                self.logger.info(f"Workspace already exists, using directly: {commit_hash}")
                return workspace_path

        # 1. Check if the snapshot exists
        snapshot_path = self.snapshot_manager.snapshot_dir / f"{commit_hash}.snap"
        if not await aiofiles.os.path.exists(snapshot_path):
            raise FileNotFoundError(f"[{commit_hash}] Snapshot file not found: {snapshot_path}")
        
        # 2. Load snapshot
        try:
            file_mappings = await self.snapshot_manager.load_snapshot(commit_hash)
            if not file_mappings:
                raise ValueError(f"[{commit_hash}] Snapshot is empty or invalid")
        except Exception as e:
            raise ValueError(f"[{commit_hash}] Snapshot file corrupted") from e
        
        # 3. Check disk space and create workspace directory  
        workspace_path = await self._ensure_workspace_directory(commit_hash)
        
        # 4. Batch restore files
        try:
            await self.content_store.batch_retrieve_files(
                file_mappings,
                workspace_path,
                max_workers=self.config.max_concurrent_restores
            )
        except Exception as e:
            raise RuntimeError(f"[{commit_hash}] Restore file failed") from e

        # 4.5. Remove .git file from workspace root (if exists)
        # Git worktree creates .git as a file pointing to main repo, which contains host-specific paths
        # This file is invalid in container environments, so we remove it
        git_file = workspace_path / '.git'
        if await aiofiles.os.path.exists(git_file):
            try:
                await aiofiles.os.remove(git_file)
                self.logger.debug(f"Removed .git file from workspace root: {commit_hash}")
            except Exception as e:
                # Log warning but don't fail the restore
                self.logger.warning(f"Failed to remove .git file: {e}")

        # 5. Set entire workspace to readonly (exclude .lake/ directory)
        try:
            await self._set_workspace_readonly(workspace_path)
            self.logger.info(f"Workspace set to readonly: {commit_hash}")
        except Exception as e:
            # Readonly setting failure does not affect restore success, record warning only
            self.logger.warning(f"Set workspace readonly failed: {e}")
        
        self.logger.info(f"Restore workspace success: {commit_hash}")
        return workspace_path
    
    async def _ensure_workspace_directory(self, workspace_id: str) -> Path:
        """Ensure workspace directory exists and has enough disk space

        Raises:
            DiskSpaceError: Disk space is not enough
            OSError: Directory creation failed
        """
        # Check disk space
        if not await check_disk_space_available(self.workspace_dir, self.config.disk_space_threshold_percent):
            disk_info = await get_disk_usage(self.workspace_dir)
            raise DiskSpaceError(
                f"[{workspace_id}] Disk space not enough: {disk_info['usage_percent']:.1f}% used, "
                f"exceeds threshold {self.config.disk_space_threshold_percent}%"
            )

        workspace_path = self.workspace_dir / workspace_id
        try:
            await aiofiles.os.makedirs(workspace_path, exist_ok=True)
            return workspace_path
        except Exception as e:
            raise OSError(f"[{workspace_id}] Create workspace directory failed") from e

    async def _set_workspace_readonly(self, workspace_path: Path) -> None:
        """Set entire workspace to readonly in parallel
        
        Rules:
        - All .lean files and regular files: 0o444 (r--r--r--)
        - All directories: 0o555 (r-xr-xr-x, need x permission to traverse)
        
        Args:
            workspace_path: workspace root directory
        """
        # 1. Collect all paths that need to set permissions
        def collect_paths(root: Path):
            """Collect all file and directory paths"""
            files = []
            dirs = []
            for item in root.rglob('*'):
                if item.is_dir():
                    dirs.append(item)
                elif item.is_file() or item.is_symlink():
                    files.append(item)
            return files, dirs
        
        files, dirs = await asyncio.to_thread(collect_paths, workspace_path)
        total_items = len(files) + len(dirs)
        self.logger.info(f"Start setting readonly permissions: {total_items} items ({len(files)} files, {len(dirs)} directories)")
        
        # 2. Set permissions in parallel
        semaphore = asyncio.Semaphore(100)  # Limit concurrency
        
        async def set_file_readonly(file_path: Path) -> bool:
            """Set file to readonly"""
            async with semaphore:
                try:
                    await asyncio.to_thread(os.chmod, str(file_path), 0o444)
                    return True
                except (OSError, PermissionError) as e:
                    self.logger.debug(f"Set file readonly failed {file_path}: {e}")
                    return False
        
        async def set_dir_readonly(dir_path: Path) -> bool:
            """Set directory to readonly"""
            async with semaphore:
                try:
                    await asyncio.to_thread(os.chmod, str(dir_path), 0o555)
                    return True
                except (OSError, PermissionError) as e:
                    self.logger.debug(f"Set directory readonly failed {dir_path}: {e}")
                    return False
        
        # 3. Process all files first, then process directories (with progress monitoring)
        file_tasks = [asyncio.create_task(set_file_readonly(f)) for f in files]
        
        # Process files and monitor progress
        completed_count = 0
        last_report_time = datetime.now()
        start_time = datetime.now()
        
        for coro in asyncio.as_completed(file_tasks):
            try:
                await coro
                completed_count += 1
            except Exception:
                completed_count += 1
            
            # Print progress every 10 seconds
            current_time = datetime.now()
            if (current_time - last_report_time).total_seconds() >= 10:
                progress = completed_count / total_items
                total_elapsed = (current_time - start_time).total_seconds()
                
                # Calculate ETA
                avg_time_per_item = total_elapsed / completed_count
                remaining_items = total_items - completed_count
                eta_seconds = avg_time_per_item * remaining_items
                eta_minutes = int(eta_seconds // 60)
                eta_secs = int(eta_seconds % 60)
                eta_str = f"{eta_minutes}m{eta_secs}s" if eta_minutes > 0 else f"{eta_secs}s"
                
                self.logger.info(
                    f"Readonly permission setting progress: {completed_count}/{total_items} ({progress*100:.1f}%) | "
                    f"Elapsed time: {int(total_elapsed)}s | ETA: {eta_str}"
                )
                last_report_time = current_time
        
        # 4. Process all directories (from deep to shallow, to avoid permission issues)
        sorted_dirs = sorted(dirs, key=lambda d: len(d.parts), reverse=True)
        dir_tasks = [asyncio.create_task(set_dir_readonly(d)) for d in sorted_dirs]
        
        for coro in asyncio.as_completed(dir_tasks):
            try:
                await coro
                completed_count += 1
            except Exception:
                completed_count += 1
            
            # Print progress every 10 seconds
            current_time = datetime.now()
            if (current_time - last_report_time).total_seconds() >= 10:
                progress = completed_count / total_items
                total_elapsed = (current_time - start_time).total_seconds()
                
                # Calculate ETA
                avg_time_per_item = total_elapsed / completed_count
                remaining_items = total_items - completed_count
                eta_seconds = avg_time_per_item * remaining_items
                eta_minutes = int(eta_seconds // 60)
                eta_secs = int(eta_seconds % 60)
                eta_str = f"{eta_minutes}m{eta_secs}s" if eta_minutes > 0 else f"{eta_secs}s"
                
                self.logger.info(
                    f"Readonly permission setting progress: {completed_count}/{total_items} ({progress*100:.1f}%) | "
                    f"Elapsed time: {int(total_elapsed)}s | ETA: {eta_str}"
                )
                last_report_time = current_time
        
        self.logger.info(f"Readonly permission setting completed: {completed_count}/{total_items} processed")
        
        # 6. Finally set root directory to readonly
        try:
            await asyncio.to_thread(os.chmod, str(workspace_path), 0o555)
        except (OSError, PermissionError) as e:
            self.logger.debug(f"Set root directory readonly failed: {e}")
