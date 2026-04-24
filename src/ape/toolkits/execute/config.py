"""
Code Execute Tool Configuration Base Class

Provides common path configuration and operational parameters for all
code execution toolkits (Lean, Isabelle, Coq, etc.)
"""

import os
import configparser
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from ape.utils.project import PROJECT_ROOT


def _optional_env(*names: str) -> Optional[str]:
    """Read environment variables in priority order and normalize empty strings to None."""
    for name in names:
        value = os.environ.get(name)
        if value is None:
            continue
        value = value.strip()
        if value:
            return value
    return None


def _read_aws_ini_section(path: Path, section: str) -> dict[str, str]:
    """Read a single AWS shared-config/credentials section if present."""
    expanded_path = path.expanduser()
    if not expanded_path.exists():
        return {}

    parser = configparser.RawConfigParser()
    try:
        parser.read(expanded_path, encoding="utf-8")
    except Exception:
        return {}

    if not parser.has_section(section):
        return {}

    return {
        key.strip(): value.strip()
        for key, value in parser.items(section)
        if value is not None and value.strip()
    }


def _load_aws_profile_settings(profile_name: Optional[str] = None) -> dict[str, str]:
    """Load AWS shared profile settings from ~/.aws/config and ~/.aws/credentials.

    Credentials files are traditionally for secrets only, but some S3-compatible
    providers document extra profile keys there as well. We support both files so
    users can rely on the conventions already present on their machines.
    """
    profile = (profile_name or _optional_env("AWS_PROFILE") or "default").strip() or "default"
    config_path = Path(_optional_env("AWS_CONFIG_FILE") or "~/.aws/config")
    credentials_path = Path(
        _optional_env("AWS_SHARED_CREDENTIALS_FILE") or "~/.aws/credentials"
    )

    credentials_settings = _read_aws_ini_section(credentials_path, profile)
    config_section = "default" if profile == "default" else f"profile {profile}"
    config_settings = _read_aws_ini_section(config_path, config_section)

    merged_settings = dict(credentials_settings)
    merged_settings.update(config_settings)
    return merged_settings


class CodeExecuteToolConfig(BaseModel):
    """Base configuration for code execution tools.

    Provides unified path management and operational timeouts.
    Language-specific configs should inherit from this class.
    """
    model_config = ConfigDict(extra='forbid')

    # ==================== Path Configuration ====================
    # Base directory for all code execution data
    base_dir: Path = Field(
        default=PROJECT_ROOT / "data/code_execute",
        description="Base directory for code execution data"
    )

    # Global shared storage (CAS storage shared across all repos)
    storage_dir: Path = Field(
        default=PROJECT_ROOT / "data/code_execute/storage",
        description="Global shared content-addressable storage"
    )

    # Repository data directory (each repo has its own subdirectory)
    repos_dir: Path = Field(
        default=PROJECT_ROOT / "data/code_execute/repos",
        description="Base directory for all repository-specific data"
    )

    # Optional remote backing store for immutable artifacts and snapshots.
    s3_bucket: Optional[str] = Field(
        default_factory=lambda: _optional_env("APE_CODE_EXECUTE_S3_BUCKET"),
        description="Optional S3 bucket used as a backing store for immutable execute artifacts"
    )
    s3_prefix: str = Field(
        default_factory=lambda: os.environ.get("APE_CODE_EXECUTE_S3_PREFIX", "").strip(),
        description="Optional S3 key prefix under the backing-store bucket"
    )
    s3_endpoint_url: Optional[str] = Field(
        default_factory=lambda: _optional_env(
            "APE_CODE_EXECUTE_S3_ENDPOINT_URL",
            "AWS_ENDPOINT_URL",
        ),
        description="Optional custom S3 endpoint URL"
    )
    s3_region: Optional[str] = Field(
        default_factory=lambda: _optional_env(
            "APE_CODE_EXECUTE_S3_REGION",
            "AWS_REGION",
            "AWS_DEFAULT_REGION",
        ),
        description="Optional S3 region name"
    )
    s3_profile: Optional[str] = Field(
        default_factory=lambda: _optional_env(
            "APE_CODE_EXECUTE_S3_PROFILE",
            "AWS_PROFILE",
        ),
        description="Optional AWS profile name for the S3 client"
    )
    s3_request_checksum_calculation: Optional[str] = Field(
        default_factory=lambda: _optional_env(
            "APE_CODE_EXECUTE_S3_REQUEST_CHECKSUM_CALCULATION",
            "AWS_REQUEST_CHECKSUM_CALCULATION",
        ),
        description="Optional botocore request checksum calculation policy"
    )
    s3_response_checksum_validation: Optional[str] = Field(
        default_factory=lambda: _optional_env(
            "APE_CODE_EXECUTE_S3_RESPONSE_CHECKSUM_VALIDATION",
            "AWS_RESPONSE_CHECKSUM_VALIDATION",
        ),
        description="Optional botocore response checksum validation policy"
    )

    # ==================== Default Repository ====================
    default_repo_url: Optional[str] = Field(
        default=None,
        description="Default repository URL"
    )

    # ==================== Operation Timeouts ====================
    git_operation_timeout: float = Field(
        default=300.0,
        description="Git operation timeout (seconds)"
    )
    workspace_operation_timeout: float = Field(
        default=300.0,
        description="Workspace operation timeout (seconds)"
    )

    # ==================== Concurrency Configuration ====================
    max_concurrent_operations: int = Field(
        default=16,
        description="Maximum concurrent operations"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )
    retry_base_delay: float = Field(
        default=10.0,
        description="Base delay between retries (seconds)"
    )

    # ==================== Disk Space Configuration ====================
    disk_space_threshold_percent: float = Field(
        default=95.0,
        description="Disk usage threshold percentage"
    )

    # ==================== Path Helper Methods ====================

    def get_repo_base_dir(self, repo_name: str) -> Path:
        """Get base directory for a specific repository.

        Structure under this directory:
        - source/               # Git repository itself
        - snapshots/           # Snapshot index files
        - workspaces/ # Workspaces restored from snapshots (for repos that need compilation)
        - plain_workspaces/    # Workspaces created via git worktree (for repos without compilation)
        - build_workspaces/    # Temporary build directories
        """
        return self.repos_dir / repo_name

    def get_repo_source_path(self, repo_name: str) -> Path:
        """Get the git repository source path.

        This is the git repo itself, not a parent directory containing it.
        E.g., for mathlib4: repos/mathlib4/source/ is the mathlib4 git repo.
        """
        return self.get_repo_base_dir(repo_name) / "source"

    def get_snapshot_dir(self, repo_name: str) -> Path:
        """Get snapshot directory for a repository."""
        return self.get_repo_base_dir(repo_name) / "snapshots"

    def get_compiled_workspace_dir(self, repo_name: str) -> Path:
        """Get compiled workspace directory (restored from snapshots)."""
        return self.get_repo_base_dir(repo_name) / "workspaces"

    def get_plain_workspace_dir(self, repo_name: str) -> Path:
        """Get plain workspace directory (created via git worktree)."""
        return self.get_repo_base_dir(repo_name) / "plain_workspaces"

    def get_build_workspace_dir(self, repo_name: str) -> Path:
        """Get temporary build workspace directory."""
        return self.get_repo_base_dir(repo_name) / "build_workspaces"

    def get_cache_dir(self, repo_name: str) -> Path:
        """Get cache directory for a repository.

        Used for temporary cache operations like lake cache get.
        Structure: repos/repo_name/cache/commit_hash/attempt_{pid}_{timestamp}_{uuid}
        """
        return self.get_repo_base_dir(repo_name) / "cache"

    @model_validator(mode='after')
    def validate_and_create_directories(self):
        """Convert to absolute paths, hydrate optional AWS settings, and create base directories."""
        aws_profile_settings = _load_aws_profile_settings(self.s3_profile)

        if self.s3_bucket is None:
            self.s3_bucket = (
                aws_profile_settings.get("ape_code_execute_s3_bucket")
                or aws_profile_settings.get("s3_bucket")
            )
        if not self.s3_prefix:
            self.s3_prefix = (
                aws_profile_settings.get("ape_code_execute_s3_prefix")
                or aws_profile_settings.get("s3_prefix")
                or self.s3_prefix
            )
        if self.s3_endpoint_url is None:
            self.s3_endpoint_url = aws_profile_settings.get("endpoint_url")
        if self.s3_region is None:
            self.s3_region = aws_profile_settings.get("region")
        if self.s3_request_checksum_calculation is None:
            self.s3_request_checksum_calculation = aws_profile_settings.get(
                "request_checksum_calculation"
            )
        if self.s3_response_checksum_validation is None:
            self.s3_response_checksum_validation = aws_profile_settings.get(
                "response_checksum_validation"
            )

        self.base_dir = self.base_dir.resolve()
        self.storage_dir = self.storage_dir.resolve()
        self.repos_dir = self.repos_dir.resolve()

        # Create base directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.repos_dir.mkdir(parents=True, exist_ok=True)

        return self
