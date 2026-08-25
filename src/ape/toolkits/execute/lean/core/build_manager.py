"""
Lean Build Manager - Inherits from BaseSourceManager.

Adds Lean-specific build functionality (lake build, cache management).
"""

import os
import re
import asyncio
import inspect
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Callable, Any, Iterable
from datetime import datetime

import aiofiles.os

# Import base class
from ape.toolkits.execute.base_source_manager import BaseSourceManager
from ..config import LeanVerifyToolConfig
from ..models import BuildResult, WorkspaceStatus
from .blob_store import create_blob_store
from .bundle_manager import SnapshotBundleManager
from ..core.workspace_state import WorkspaceStateManager
from ..core.storage import ContentStore
from ..core.snapshot import SnapshotManager
from ..utils.process_ops import is_process_alive, run_command
from ape.utils.file_ops import safe_remove_directory, list_files_recursive, safe_unlink, file_lock
from ..utils.exceptions import AlreadyBuildingError, AlreadyRestoringError
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging


class BuildManager(BaseSourceManager):
    """Lean Build Manager - extends BaseSourceManager with Lean compilation.

    Inherits:
    - Repository cloning (from BaseSourceManager)
    - Worktree management (from BaseSourceManager)

    Adds:
    - Lake build execution
    - Cache management
    - Snapshot creation
    - Build state management
    """

    def __init__(
        self,
        config: Optional[LeanVerifyToolConfig] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        repo_url: Optional[str] = None
    ):
        """Initialize Lean build manager."""
        # Use LeanVerifyToolConfig as default
        actual_config = config or LeanVerifyToolConfig()
        super().__init__(actual_config, logger, repo_url)

        # Cast to specific config type for Lean-specific attributes
        self.config: LeanVerifyToolConfig = actual_config

        # Lean-specific components
        self.blob_store = create_blob_store(self.config, self.logger)
        self.state_manager = WorkspaceStateManager(self.config, self.logger, self.repo_name)
        self.content_store = ContentStore(self.config, self.logger, blob_store=self.blob_store)
        self.snapshot_manager = SnapshotManager(
            self.config,
            self.logger,
            self.repo_name,
            blob_store=self.blob_store,
        )
        self.bundle_manager = SnapshotBundleManager(
            self.config,
            self.logger,
            self.repo_name,
            blob_store=self.blob_store,
        )

        # Build workspace directory
        self.build_workspace_dir = self.config.get_build_workspace_dir(self.repo_name)

        self.logger.info(f"Lean BuildManager initialized [{self.repo_name}]")

    @staticmethod
    async def _emit_progress(progress_callback: Optional[Callable[[str], Any]], message: str) -> None:
        if progress_callback is None:
            return

        result = progress_callback(message)
        if inspect.isawaitable(result):
            await result

    @staticmethod
    def _cache_namespace(cache_repo_full_name: Optional[str], fallback_repo_name: str) -> str:
        """Build a filesystem-safe namespace for shared Lean cache downloads."""
        raw_namespace = str(cache_repo_full_name or fallback_repo_name or "default").strip()
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "__", raw_namespace)
        normalized = normalized.strip("._-")
        return normalized or "default"

    async def _cleanup_partial_cache_files(self, cache_dir: Path) -> int:
        """Remove stale partial downloads before reusing a shared cache directory."""
        try:
            partial_files = await asyncio.to_thread(
                lambda: [path for path in cache_dir.rglob("*.part") if path.is_file()]
            )
        except FileNotFoundError:
            return 0
        except Exception as exc:
            self.logger.debug("Unable to enumerate partial cache files in %s: %s", cache_dir, exc)
            return 0

        removed_count = 0
        for partial_file in partial_files:
            try:
                await safe_unlink(partial_file)
                removed_count += 1
            except Exception as exc:
                self.logger.debug("Failed to remove partial cache file %s: %s", partial_file, exc)

        return removed_count

    async def _wait_for_build_completion(self, commit_hash: str) -> BuildResult:
        """Wait for another process to finish building the same workspace."""
        actual_timeout = self.config.restore_queue_timeout
        poll_interval = self.config.workspace_restore_poll_interval
        start_time = datetime.now()
        last_progress_report = start_time

        self.logger.info(f"Wait for build completion: {commit_hash}")

        while (datetime.now() - start_time).total_seconds() < actual_timeout:
            state = await self.state_manager.read_state(commit_hash)

            if not state:
                raise RuntimeError(f"[{commit_hash}] State file disappeared during wait")

            if state.status in (
                WorkspaceStatus.BUILT,
                WorkspaceStatus.READY,
                WorkspaceStatus.RESTORING,
            ):
                self.logger.info(f"Build completed in another process: {commit_hash}")
                return BuildResult(
                    success=True,
                    commit_hash=commit_hash,
                    build_duration=0.0,
                    file_count=state.file_count,
                )

            if state.status == WorkspaceStatus.FAILED:
                raise RuntimeError(f"[{commit_hash}] Build failed: {state.error_message}")

            if state.status != WorkspaceStatus.BUILDING:
                raise RuntimeError(f"[{commit_hash}] State abnormal during wait: {state.status}")

            if state.build_pid and not is_process_alive(state.build_pid):
                raise RuntimeError(
                    f"[{commit_hash}] Waiting for build process to die (pid={state.build_pid})"
                )

            now = datetime.now()
            if (now - last_progress_report).total_seconds() >= 15:
                self.logger.info(
                    "Still waiting for workspace build to finish for %s@%s...",
                    self.repo_name,
                    commit_hash[:8],
                )
                last_progress_report = now

            await asyncio.sleep(poll_interval)

        raise TimeoutError(f"[{commit_hash}] Waiting for build completion timed out ({actual_timeout}s)")
    
    async def build_workspace(self, commit_hash: str, force_rebuild: bool = False) -> BuildResult:
        """Build workspace
        
        Args:
            commit_hash: Target commit hash
            force_rebuild: Whether to force rebuild
            
        Returns:
            BuildResult: Build result
            
        Raises:
            AlreadyBuildingError: Already building
            AlreadyRestoringError: Already restoring
            OtherException: Build process error
        """
        start_time = datetime.now()
        self.logger.info(f"Start building workspace: {commit_hash}")
        
        try:
            # 1. Atomic attempt to start build
            current_state = await self.state_manager.try_start_build(commit_hash, force_rebuild)
            
            # If already built, return directly
            if current_state.status in (WorkspaceStatus.BUILT, WorkspaceStatus.READY):
                self.logger.info(f"Workspace already built: {commit_hash}")
                return BuildResult(
                    success=True,
                    commit_hash=commit_hash,
                    build_duration=0.0,
                    file_count=current_state.file_count
                )
            
            # 2. Execute actual build
            self.logger.info(f"Execute build: {commit_hash}")
            file_count = await self._execute_build(commit_hash)
            
            # 3. Calculate build time and complete status update
            build_duration = (datetime.now() - start_time).total_seconds()
            await self.state_manager.complete_build(
                commit_hash, True, build_duration, file_count
            )
            
            self.logger.info(f"Build successful: {commit_hash}, time: {build_duration:.2f}s")
            return BuildResult(
                success=True,
                commit_hash=commit_hash,
                build_duration=build_duration,
                file_count=file_count
            )
                
        except (AlreadyBuildingError, AlreadyRestoringError):
            # These exceptions are directly rethrown, allowing the caller to decide how to handle them
            raise
            
        except Exception as e:
            # Other exceptions: try to update failed status and rethrow
            build_duration = (datetime.now() - start_time).total_seconds()
            error_message = str(e)
            
            self.logger.error(f"Build exception {commit_hash}: {error_message}")
            
            try:
                await self.state_manager.complete_build(
                    commit_hash, False, build_duration, 0, error_message, type(e).__name__
                )
            except Exception:
                # State update failure cannot prevent exception propagation
                pass
            
            # Rethrow original exception
            raise
    
    async def _execute_build(self, commit_hash: str) -> int:
        """Execute actual build process

        Returns:
            int: Number of files built

        Raises:
            RuntimeError: Build process error
            OSError: File system operation error
            TimeoutError: Build timeout
        """
        build_workspace_path = None

        try:
            # 1. Create build worktree (using inherited method)
            build_workspace_path = await self.create_worktree(
                commit_hash,
                self.build_workspace_dir
            )

            # 2. Run lake build (Lean-specific)
            await self._run_lake_build(build_workspace_path, commit_hash)

            # 3. Create snapshot (Lean-specific)
            file_count = await self._create_snapshot(commit_hash, build_workspace_path)

            return file_count

        finally:
            # Cleanup build workspace (using inherited method)
            if build_workspace_path:
                await self.cleanup_worktree(build_workspace_path)
    
    
    async def _run_lake_build(self, build_workspace_path: Path, commit_hash: str) -> None:
        """Run lake build
        
        Raises:
            RuntimeError: Lake build failed
            TimeoutError: Build timeout
        """
        try:
            # Delete possible .lake directory
            lake_dir = build_workspace_path / ".lake"
            if await aiofiles.os.path.exists(lake_dir):
                await safe_remove_directory(lake_dir)
            
            # Try to get cache
            cache_success = await self._get_cache_for_workspace(build_workspace_path, commit_hash)
            if cache_success:
                self.logger.info(f"Successfully get workspace cache: {commit_hash}")
            else:
                self.logger.warning("Get cache failed, continue build process")
            
            # Execute lake build
            stdout, stderr, returncode = await run_command(
                ["lake", "build"],
                cwd=build_workspace_path,
                timeout=self.config.build_timeout,
                print_output=True,
                operation_name=f"lake build {commit_hash}",
                logger=self.logger
            )
            
            if returncode == 0:
                self.logger.info(f"Lake build successful: {commit_hash}")
            elif returncode == -15:
                # Timeout exit
                raise TimeoutError(f"[{commit_hash}] Build timeout ({self.config.build_timeout}s)")
            else:
                error_message = f"Lake build failed: {stderr}"
                self.logger.error(f"Lake build failed {commit_hash}: {error_message}")
                raise RuntimeError(f"[{commit_hash}] {error_message}")
                
        except TimeoutError:
            # Rethrow timeout exception
            raise
        except RuntimeError:
            # Rethrow runtime exception
            raise
        except Exception as e:
            # Wrap other exceptions
            raise RuntimeError(f"[{commit_hash}] Build process exception") from e
    
    async def _get_cache_for_workspace(self, build_workspace_path: Path, commit_hash: str) -> bool:
        """Get workspace cache"""
        max_retries = 3
        
        for attempt in range(max_retries):
            if attempt > 0:
                self.logger.debug(f"Retry cache get ({attempt + 1}/{max_retries})")
                await asyncio.sleep(10)
            
            try:
                # Set cache directory environment - use repo-specific cache directory
                import uuid
                import time
                cache_base = self.config.get_cache_dir(self.repo_name)
                cache_dir = cache_base / commit_hash / f"attempt_{os.getpid()}_{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}"
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                env = os.environ.copy()
                env["XDG_CACHE_HOME"] = str(cache_dir)
                
                stdout, stderr, return_code = await run_command(
                    ["lake", "exe", "cache", "get"],
                    cwd=build_workspace_path,
                    timeout=self.config.cache_operation_timeout,
                    env=env,
                    print_output=True,
                    logger=self.logger,
                    operation_name=f"lake cache get {commit_hash}"
                )
                
                # Clean up cache directory
                await safe_remove_directory(cache_dir)
                
                if return_code == 0:
                    self.logger.debug("Cache get successful")
                    return True
                else:
                    self.logger.warning(f"Cache get failed: {stderr}")
                    if attempt >= max_retries - 1:
                        return False
                    await asyncio.sleep(10 * (attempt + 1))
                        
            except Exception as e:
                self.logger.warning(f"Execute cache get command error: {e}")
                if attempt >= max_retries - 1:
                    return False
        
        return False
    
    async def _create_snapshot(self, commit_hash: str, workspace_path: Path) -> int:
        """Create workspace snapshot
        
        Returns:
            int: Number of files in snapshot
            
        Raises:
            RuntimeError: Snapshot creation failed
        """
        self.logger.info(f"Create workspace snapshot: {commit_hash}")
        
        try:
            # 1. Collect all file paths and types
            file_list = await list_files_recursive(workspace_path)
            
            total_files = len(file_list)
            self.logger.info(f"Found {total_files} files, start parallel processing...")
            
            # 2. Parallel store files to content store
            file_mappings = {}
            semaphore = asyncio.Semaphore(os.cpu_count() // 2)  # Limit concurrency
            
            async def store_single_file(file_path: Path, file_type: str) -> None:
                async with semaphore:
                    relative_path = str(file_path.relative_to(workspace_path))
                    try:
                        # Store file, internal will calculate hash
                        content_hash = await self.content_store.store_file(file_path, file_type)
                        
                        file_mappings[relative_path] = {
                            "hash": content_hash,
                            "type": file_type
                        }
                        
                    except Exception as e:
                        self.logger.error(f"Store file failed {relative_path}: {e}")
            
            # Parallel store all files
            tasks = [store_single_file(file_path, file_type) for file_path, file_type in file_list]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            file_count = len(file_mappings)
            if file_count == 0:
                raise RuntimeError(f"[{commit_hash}] No files were successfully stored in the snapshot")
            
            self.logger.info(f"File storage completed, successfully processed {file_count}/{total_files} files")
            
            # 3. Store snapshot metadata
            await self.snapshot_manager.store_snapshot(commit_hash, file_mappings)
            try:
                await self.bundle_manager.store_snapshot_bundles(commit_hash, file_mappings)
            except Exception as exc:
                self.logger.warning(
                    "Failed to build snapshot bundle acceleration for %s: %s",
                    commit_hash,
                    exc,
                )
            self.logger.info(f"Create snapshot completed: {commit_hash}, file count: {file_count}")
            
            return file_count
            
        except Exception as e:
            raise RuntimeError(f"[{commit_hash}] Create snapshot failed") from e
    
    
    async def retry_failed_build(self, commit_hash: str) -> BuildResult:
        """Retry failed build"""
        self.logger.info(f"Retry build: {commit_hash}")
        return await self.build_workspace(commit_hash, force_rebuild=True)
    
    async def get_build_status(self, commit_hash: str) -> Optional[WorkspaceStatus]:
        """Get build status"""
        state = await self.state_manager.read_state(commit_hash)
        return state.status if state else None
