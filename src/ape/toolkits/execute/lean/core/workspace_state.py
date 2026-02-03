"""
Simplified workspace state manager - exception-driven version
Use standard exceptions and few business exceptions, completely solve the problem of error handling
"""

import os
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from ..config import LeanVerifyToolConfig
from ..models import WorkspaceState, WorkspaceStatus
from ..utils.process_ops import is_process_alive
from ape.utils.file_ops import file_lock, read_json, write_json
from ..utils.exceptions import (
    AlreadyBuildingError, AlreadyRestoringError, 
    BuildIncompleteError, WorkspaceFailedError
)
import aiofiles.os
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging

class WorkspaceStateManager:
    """Workspace state manager - exception-driven design"""

    def __init__(self, config: Optional[LeanVerifyToolConfig] = None, logger: Optional['logging.LoggerAdapter'] = None, repo_name: str = "mathlib4"):
        """Initialize workspace state manager

        Args:
            config: Configuration object
            logger: Logger
            repo_name: Repository name, default is mathlib4 (backward compatibility)
        """
        self.config = config or LeanVerifyToolConfig()
        self.logger = logger or create_logger()
        self.repo_name = repo_name
        # State files are stored in the snapshot directory
        self.state_dir = self.config.get_snapshot_dir(repo_name)
        self.lock_timeout = 5.0  # Unified state lock timeout
        self.logger.info(f"Workspace state manager initialized [{repo_name}]: {self.state_dir}")
    
    def get_state_path(self, workspace_id: str) -> Path:
        return self.state_dir / f"{workspace_id}.state"
    
    def get_lock_path(self, workspace_id: str) -> Path:
        """Get state lock file path"""
        return self.get_state_path(workspace_id).with_suffix(".lock")

    async def read_state(self, workspace_id: str) -> Optional[WorkspaceState]:
        """Read workspace state without lock"""
        state_path = self.get_state_path(workspace_id)
        
        try:
            state_data = await read_json(state_path)
            if state_data:
                return WorkspaceState.model_validate(state_data)
            return None
        except Exception as e:
            self.logger.debug(f"Read workspace state failed {workspace_id}: {e}")
            return None
    
    async def try_start_restore(self, workspace_id: str) -> WorkspaceState:
        """Try to start restore operation
        
        Raises:
            FileNotFoundError: State file does not exist
            ValueError: State file corrupted or invalid state conversion
            TimeoutError: Unable to get state lock
            AlreadyRestoringError: Already restoring
            AlreadyBuildingError: Still building  
            BuildIncompleteError: Build incomplete
            WorkspaceFailedError: Workspace failed state
        """
        state_path = self.get_state_path(workspace_id)
        await aiofiles.os.makedirs(self.state_dir, exist_ok=True)
        # Pre-read state, quickly check concurrency conflicts (only throw exception when process is alive, dead processes allow takeover)
        pre_state = await self.read_state(workspace_id)
        if pre_state:
            if pre_state.status == WorkspaceStatus.RESTORING:
                if pre_state.restore_pid and is_process_alive(pre_state.restore_pid):
                    raise AlreadyRestoringError(
                        f"[{workspace_id}] Workspace is already restoring (process {pre_state.restore_pid})"
                    )
                # Process is dead, record log but continue execution, allow lock inner logic to takeover
                if pre_state.restore_pid:
                    self.logger.warning(f"Pre-read detected dead restore process, preparing to takeover: {workspace_id} (pid={pre_state.restore_pid})")
            elif pre_state.status == WorkspaceStatus.BUILDING:
                if pre_state.build_pid and is_process_alive(pre_state.build_pid):
                    raise AlreadyBuildingError(
                        f"[{workspace_id}] Workspace is still building (process {pre_state.build_pid})"
                    )
                # Build process is dead, restore should not continue, need to rebuild
                if pre_state.build_pid:
                    self.logger.warning(f"Pre-read detected dead build process: {workspace_id} (pid={pre_state.build_pid}), BuildIncompleteError will be thrown inside the lock")
        
        try:
            lock_path = self.get_lock_path(workspace_id)
            async with file_lock(lock_path, timeout=self.lock_timeout):
                # 1. Read current state
                state_data = await read_json(state_path)
                if not state_data:
                    # Check if workspace directory exists
                    workspace_dir = self.config.get_workspace_dir(self.repo_name)
                    workspace_path = workspace_dir / workspace_id
                    if await aiofiles.os.path.exists(workspace_path) and await aiofiles.os.path.isdir(workspace_path):
                        # Workspace exists but state file missing - create READY state
                        self.logger.warning(f"State file missing but workspace exists, creating READY state: {workspace_id}")
                        current_state = WorkspaceState(
                            status=WorkspaceStatus.READY,
                            commit_hash=workspace_id,
                            workspace_path=workspace_path
                        )
                        # Save the newly created state
                        await write_json(state_path, current_state.model_dump(mode='json'))
                    else:
                        raise FileNotFoundError(f"[{workspace_id}] State file does not exist, need to build first")
                else:
                    try:
                        current_state = WorkspaceState.model_validate(state_data)
                    except Exception as e:
                        raise ValueError(f"[{workspace_id}] State file corrupted") from e
                
                # 2. Check state conversion conditions
                if current_state.status == WorkspaceStatus.RESTORING:
                    if current_state.restore_pid and is_process_alive(current_state.restore_pid):
                        raise AlreadyRestoringError(f"[{workspace_id}] Workspace is already restoring (process {current_state.restore_pid})")
                    self.logger.warning(f"Detected dead restore process, allowing takeover: {workspace_id} (pid={current_state.restore_pid})")
                
                elif current_state.status == WorkspaceStatus.BUILDING:
                    if current_state.build_pid and is_process_alive(current_state.build_pid):
                        raise AlreadyBuildingError(f"[{workspace_id}] Workspace is still building (process {current_state.build_pid})")
                    raise BuildIncompleteError(f"[{workspace_id}] Build process terminated abnormally, need to rebuild (dead process {current_state.build_pid})")
                
                elif current_state.status == WorkspaceStatus.FAILED:
                    error_detail = f": {current_state.error_message}" if current_state.error_message else ""
                    raise WorkspaceFailedError(f"[{workspace_id}] Workspace is in failed state, need to rebuild{error_detail}")
                
                elif current_state.status not in [WorkspaceStatus.BUILT, WorkspaceStatus.READY]:
                    raise ValueError(f"[{workspace_id}] Unable to perform restore operation from state '{current_state.status.value}'")
                
                # 3. Update state to RESTORING
                now = datetime.now().isoformat()
                current_state.status = WorkspaceStatus.RESTORING
                current_state.restore_started_at = now
                current_state.restore_pid = os.getpid()
                current_state.updated_at = now
                current_state.last_active_at = now
                
                # 4. Write state file
                await write_json(state_path, current_state.model_dump(mode='json'))
                
                self.logger.info(f"Restore operation started successfully: {workspace_id}")
                return current_state
                    
        except (TimeoutError, OSError) as e:
            state = await self.read_state(workspace_id)
            if state:
                if state.status == WorkspaceStatus.RESTORING and state.restore_pid:
                    if is_process_alive(state.restore_pid):
                        raise AlreadyRestoringError(
                            f"[{workspace_id}] Workspace is already restoring (process {state.restore_pid})"
                        ) from e
                if state.status == WorkspaceStatus.BUILDING and state.build_pid:
                    if is_process_alive(state.build_pid):
                        raise AlreadyBuildingError(
                            f"[{workspace_id}] Workspace is still building (process {state.build_pid})"
                        ) from e
            hint = ""
            if state and state.restore_pid:
                hint = f", current restore process: {state.restore_pid}"
            raise TimeoutError(
                f"[{workspace_id}] Unable to get state lock, timeout {self.lock_timeout:.1f}s{hint}"
            ) from e
    
    async def complete_restore(self, workspace_id: str, success: bool, 
                             workspace_path: Optional[Path] = None,
                             restore_duration: Optional[float] = None,
                             error_message: Optional[str] = None,
                             error_type: Optional[str] = None) -> WorkspaceState:
        """Complete restore operation
        
        Raises:
            FileNotFoundError: State file does not exist
            ValueError: State file corrupted or write failed
            TimeoutError: Unable to get state lock
        """
        state_path = self.get_state_path(workspace_id)
        
        try:
            lock_path = self.get_lock_path(workspace_id)
            async with file_lock(lock_path, timeout=self.lock_timeout):
                state_data = await read_json(state_path)
                if not state_data:
                    raise FileNotFoundError(f"[{workspace_id}] State file does not exist when completing restore")
                
                try:
                    current_state = WorkspaceState.model_validate(state_data)
                except Exception as e:
                    raise ValueError(f"[{workspace_id}] State file corrupted") from e
                
                # Update completed status
                now = datetime.now().isoformat()
                current_state.status = WorkspaceStatus.READY if success else WorkspaceStatus.FAILED
                current_state.restore_completed_at = now
                current_state.restore_duration = restore_duration
                current_state.restore_pid = None
                current_state.updated_at = now
                current_state.last_active_at = now
                
                if success and workspace_path:
                    current_state.workspace_path = workspace_path
                    current_state.error_message = None
                    current_state.error_type = None
                else:
                    current_state.error_message = error_message
                    current_state.error_type = error_type
                
                await write_json(state_path, current_state.model_dump(mode='json'))
                
                self.logger.info(f"Restore operation completed: {workspace_id}, success: {success}")
                return current_state
                
        except (TimeoutError, OSError) as e:
            state = await self.read_state(workspace_id)
            hint = ""
            if state and state.restore_pid:
                hint = f", current restore process: {state.restore_pid}"
            raise TimeoutError(
                f"[{workspace_id}] Unable to get state lock, timeout {self.lock_timeout:.1f}s{hint}"
            ) from e
    
    # ==================== Build related operations ====================
    
    async def try_start_build(self, workspace_id: str, force_rebuild: bool = False) -> WorkspaceState:
        """Try to start build operation"""
        state_path = self.get_state_path(workspace_id)
        await aiofiles.os.makedirs(self.state_dir, exist_ok=True)
        # Pre-read state, quickly check if build can be skipped or detect conflicts
        pre_state = await self.read_state(workspace_id)
        if pre_state:
            # If build is complete (including RESTORING state, indicating snapshot exists), return directly
            if pre_state.status in (WorkspaceStatus.BUILT, WorkspaceStatus.RESTORING, WorkspaceStatus.READY):
                if not force_rebuild:
                    return pre_state  # Snapshot exists, no need to rebuild

            # Detect concurrency conflicts: other processes are building
            if pre_state.status == WorkspaceStatus.BUILDING and pre_state.build_pid:
                if is_process_alive(pre_state.build_pid):
                    raise AlreadyBuildingError(
                        f"[{workspace_id}] Workspace is already building (process {pre_state.build_pid})"
                    )
                # Process is dead, record log but continue execution, allow lock inner logic to takeover
                self.logger.warning(f"Pre-read detected dead build process, preparing to takeover: {workspace_id} (pid={pre_state.build_pid})")
        
        try:
            lock_path = self.get_lock_path(workspace_id)
            async with file_lock(lock_path, timeout=self.lock_timeout):
                state_data = await read_json(state_path)
                
                if state_data:
                    try:
                        current_state = WorkspaceState.model_validate(state_data)
                    except Exception as e:
                        raise ValueError(f"[{workspace_id}] State file corrupted") from e
                    
                    # Check if build can be started
                    # RESTORING state indicates snapshot exists, for build it is equivalent to completed
                    if current_state.status in (WorkspaceStatus.BUILT, WorkspaceStatus.RESTORING, WorkspaceStatus.READY):
                        if not force_rebuild:
                            return current_state  # Build is complete (snapshot exists)

                    if current_state.status == WorkspaceStatus.BUILDING:
                        if current_state.build_pid and is_process_alive(current_state.build_pid):
                            raise AlreadyBuildingError(f"[{workspace_id}] Workspace is already building (process {current_state.build_pid})")
                        self.logger.warning(f"Pre-read detected dead build process, preparing to takeover: {workspace_id} (pid={current_state.build_pid})")
                
                else:
                    # Create new state
                    current_state = WorkspaceState(
                        status=WorkspaceStatus.BUILDING,
                        commit_hash=workspace_id
                    )
                
                # Update state to BUILDING
                now = datetime.now().isoformat()
                current_state.status = WorkspaceStatus.BUILDING
                current_state.build_started_at = now
                current_state.build_pid = os.getpid()
                current_state.error_message = None
                current_state.error_type = None
                current_state.updated_at = now
                current_state.last_active_at = now
                
                await write_json(state_path, current_state.model_dump(mode='json'))
                
                return current_state
                
        except (TimeoutError, OSError) as e:
            state = await self.read_state(workspace_id)
            # When lock timeout, check state again and give more precise error hint
            if state and state.status == WorkspaceStatus.BUILDING and state.build_pid:
                if is_process_alive(state.build_pid):
                    raise AlreadyBuildingError(
                        f"[{workspace_id}] Workspace is already building (process {state.build_pid})"
                    ) from e
            # Note: RESTORING state is no longer considered an error, it should not be thrown here
            # If really due to RESTORING causing lock timeout, should return success (snapshot exists)
            if state and state.status in (WorkspaceStatus.BUILT, WorkspaceStatus.RESTORING, WorkspaceStatus.READY):
                if not force_rebuild:
                    self.logger.info(f"Lock timeout but detected snapshot exists, returning success: {workspace_id}")
                    return state

            hint = ""
            if state and state.build_pid:
                hint = f", current build process: {state.build_pid}"
            raise TimeoutError(
                f"[{workspace_id}] Unable to get state lock, timeout {self.lock_timeout:.1f}s{hint}"
            ) from e
    
    async def complete_build(self, workspace_id: str, success: bool, 
                           build_duration: float, file_count: int = 0,
                           error_message: Optional[str] = None, 
                           error_type: Optional[str] = None) -> WorkspaceState:
        """Complete build operation"""
        state_path = self.get_state_path(workspace_id)
        
        try:
            lock_path = self.get_lock_path(workspace_id)
            async with file_lock(lock_path, timeout=self.lock_timeout):
                state_data = await read_json(state_path)
                if not state_data:
                    raise FileNotFoundError(f"[{workspace_id}] State file does not exist when completing build")
                
                try:
                    current_state = WorkspaceState.model_validate(state_data)
                except Exception as e:
                    raise ValueError(f"[{workspace_id}] State file corrupted") from e
                
                # Update build completed status
                now = datetime.now().isoformat()
                current_state.status = WorkspaceStatus.BUILT if success else WorkspaceStatus.FAILED
                current_state.build_completed_at = now
                current_state.build_duration = build_duration
                current_state.file_count = file_count
                current_state.build_pid = None
                current_state.updated_at = now
                current_state.last_active_at = now
                
                if success:
                    current_state.error_message = None
                    current_state.error_type = None
                else:
                    current_state.error_message = error_message
                    current_state.error_type = error_type
                
                await write_json(state_path, current_state.model_dump(mode='json'))
                
                self.logger.info(f"Build operation completed: {workspace_id}, success: {success}")
                return current_state
                
        except (TimeoutError, OSError) as e:
            state = await self.read_state(workspace_id)
            hint = ""
            if state and state.build_pid:
                hint = f", current build process: {state.build_pid}"
            raise TimeoutError(
                f"[{workspace_id}] Unable to get state lock, timeout {self.lock_timeout:.1f}s{hint}"
            ) from e
