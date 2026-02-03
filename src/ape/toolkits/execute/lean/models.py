"""
Simplified data models - keep necessary exception classes for external integration
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator
from pathlib import Path

from ape.utils.file_ops import normalize_repo_url

# ==================== Core enumeration types ====================

class WorkspaceStatus(Enum):
    """Workspace status enumeration"""
    BUILDING = "building"       # Building
    BUILT = "built"            # Built
    RESTORING = "restoring"     # Restoring
    READY = "ready"            # Ready
    FAILED = "failed"          # Failed

class ErrorType(Enum):
    """Error type enumeration"""
    BUILD_FAILED = "build_failed"
    BUILD_TIMEOUT = "build_timeout"
    BUILD_OOM = "build_oom"
    RESTORE_FAILED = "restore_failed"
    WORKSPACE_CORRUPTED = "workspace_corrupted"
    PROCESS_DIED = "process_died"
    SNAPSHOT_MISSING = "snapshot_missing"
    DISK_FULL = "disk_full"

# ==================== Data classes ====================

class LeanMessage(BaseModel):
    """Lean verification output message"""
    severity: str  # 'error', 'warning', 'info'
    data: str
    code_line: Optional[str] = None
    pos: Optional[Dict[str, Any]] = None
    end_pos: Optional[Dict[str, Any]] = None

class VerificationResult(BaseModel):
    """Verification operation result - simplified design, only use success field"""
    success: bool
    messages: List[LeanMessage]
    errors: List[LeanMessage]
    warnings: List[LeanMessage]
    infos: List[LeanMessage]
    axioms: List[str]
    raw_output: str
    raw_stderr: str
    return_code: int
    execution_time: Optional[float] = None

class BuildResult(BaseModel):
    """Workspace build result"""
    success: bool
    commit_hash: str
    build_duration: Optional[float] = None
    file_count: Optional[int] = None
    error_message: Optional[str] = None
    error_type: Optional[ErrorType] = None
    workspace_path: Optional[Path] = None

class RestoreResult(BaseModel):
    """Workspace restore result"""
    success: bool
    commit_hash: str
    workspace_path: Optional[Path] = None
    restore_duration: Optional[float] = None
    error_message: Optional[str] = None
    error_type: Optional[ErrorType] = None

# ==================== Pydantic models ====================

class RepositoryInfo(BaseModel):
    """Repository information - used to identify different Lean libraries"""
    model_config = ConfigDict(frozen=True)  # Immutable, can be used as dictionary key

    repo_url: str = Field(..., description="Repository URL (optional, if empty use default mathlib4)")
    repo_name: str = Field(..., description="Normalized repository name (used as directory name)")

    @model_validator(mode='before')
    @classmethod
    def normalize_repo_info(cls, data: Any) -> Any:
        """Automatically normalize repo information"""
        if isinstance(data, dict):
            repo_url = data.get('repo_url', '')
            if repo_url and 'repo_name' not in data:
                # Automatically extract repo_name from URL
                data['repo_name'] = normalize_repo_url(repo_url)
        return data

    @classmethod
    def from_url(cls, repo_url: str) -> 'RepositoryInfo':
        """Create RepositoryInfo from repo URL"""
        return cls(repo_url=repo_url, repo_name=normalize_repo_url(repo_url))

    @classmethod
    def default_mathlib(cls) -> 'RepositoryInfo':
        """Return default mathlib4 configuration"""
        return cls(
            repo_url="https://github.com/leanprover-community/mathlib4",
            repo_name="mathlib4"
        )


class WorkspaceState(BaseModel):
    """Workspace state data"""
    model_config = ConfigDict(validate_assignment=True)

    # Basic information
    status: WorkspaceStatus
    commit_hash: str
    workspace_path: Optional[Path] = None
    
    # Build information
    build_started_at: Optional[str] = None
    build_pid: Optional[int] = None
    build_completed_at: Optional[str] = None
    build_duration: Optional[float] = None
    
    # Restore information
    restore_started_at: Optional[str] = None
    restore_pid: Optional[int] = None
    restore_completed_at: Optional[str] = None
    restore_duration: Optional[float] = None
    
    # Statistics information
    file_count: int = 0
    
    # Error information
    error_message: Optional[str] = None
    error_type: Optional[ErrorType] = None
    
    # Timestamp
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_active_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
