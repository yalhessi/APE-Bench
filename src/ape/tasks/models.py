"""Task Models Module providing workspace metadata structures."""

from pathlib import Path
from typing import Any, List, Optional, Literal

from pydantic import BaseModel, Field, model_validator


class WorkspaceSource(BaseModel):
    """Base class for workspace source descriptors."""

    kind: str = Field(..., description="Workspace source kind discriminator")


class GitWorkspaceSource(WorkspaceSource):
    """Workspace source backed by a Git repository checkout."""

    kind: Literal["git"] = Field(default="git", description="Git-backed workspace source")
    commit_hash: str = Field(..., description="Git commit hash")
    repo_url: Optional[str] = Field(default=None, description="Git repository URL")


class LocalWorkspaceSource(WorkspaceSource):
    """Workspace source backed by a local directory on disk."""

    kind: Literal["local"] = Field(default="local", description="Local-directory-backed workspace source")
    path: Path = Field(..., description="Local directory path")


class WorkspaceInfo(BaseModel):
    """Generic workspace information including path, version, and access control.

    Supports three common workspace shapes:
    - Repository-backed target/reference workspaces: source={kind='git', ...}
    - Local-directory-backed target/reference workspaces: source={kind='local', ...}
    - Scratch workspace: only requires name and runtime path

    Access Control:
        blocked_path_patterns: Paths completely blocked from access
        read_only_path_patterns: Paths that can be read but not written
        no_read_path_patterns: Paths that can be written but not read

    Path patterns support glob syntax relative to workspace root,
    or absolute paths for exact file matching.
    """
    name: str = Field(..., description="Workspace name")
    path: Optional[Path] = Field(default=None, description="Workspace root directory path (set during setup)")

    # Source information
    source: Optional[GitWorkspaceSource | LocalWorkspaceSource] = Field(
        default=None,
        discriminator="kind",
        description="Workspace source descriptor (git repository or local directory)"
    )

    # Language-specific workspace metadata
    default_target: Optional[str] = Field(default=None, description="Optional target subdirectory filter (e.g., 'Mathlib'). If not set, uses entire repository.")
    toolchain: Optional[str] = Field(default=None, description="Lean toolchain version (e.g., 'leanprover/lean4:v4.22.0')")

    # Access control patterns
    blocked_path_patterns: List[str] = Field(
        default_factory=list,
        description="Paths completely blocked from access"
    )
    read_only_path_patterns: List[str] = Field(
        default_factory=list,
        description="Read-only paths (write blocked)"
    )
    no_read_path_patterns: List[str] = Field(
        default_factory=list,
        description="Write-only paths (read blocked)"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_source_fields(cls, value: Any) -> Any:
        """Normalize legacy flat source fields into the canonical nested source form."""
        if not isinstance(value, dict):
            return value

        normalized = dict(value)
        source = cls._normalize_source_dict(normalized.get("source"))

        if source is None:
            source = cls._build_source_from_legacy_fields(normalized)
        elif isinstance(source, dict):
            if source.get("kind") == "git":
                if source.get("commit_hash") is None and normalized.get("commit_hash") is not None:
                    source["commit_hash"] = normalized.get("commit_hash")
                if source.get("repo_url") is None and normalized.get("repo_url") is not None:
                    source["repo_url"] = normalized.get("repo_url")
            elif source.get("kind") == "local":
                if source.get("path") is None:
                    legacy_path = normalized.get("source_path") or normalized.get("path")
                    if legacy_path is not None:
                        source["path"] = legacy_path

        if source is not None:
            normalized["source"] = source
        else:
            normalized.pop("source", None)

        normalized.pop("source_type", None)
        normalized.pop("source_path", None)
        normalized.pop("commit_hash", None)
        normalized.pop("repo_url", None)
        return normalized

    @staticmethod
    def _normalize_source_dict(value: Any) -> Any:
        """Normalize source dictionaries into the canonical field names."""
        if not isinstance(value, dict):
            return value

        normalized = dict(value)
        legacy_kind = normalized.pop("source_type", None)
        if legacy_kind is not None and "kind" not in normalized:
            normalized["kind"] = legacy_kind

        legacy_path = normalized.pop("source_path", None)
        if legacy_path is not None and "path" not in normalized:
            normalized["path"] = legacy_path

        return normalized

    @classmethod
    def _build_source_from_legacy_fields(cls, value: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Build a nested source object from legacy flat workspace fields."""
        source_type = value.get("source_type")
        source_path = value.get("source_path")
        commit_hash = value.get("commit_hash")
        repo_url = value.get("repo_url")

        if source_type == "local" or source_path is not None:
            local_path = source_path or value.get("path")
            if local_path is None:
                raise ValueError("Local workspace source requires a path")
            return {
                "kind": "local",
                "path": local_path,
            }

        if source_type == "git" or commit_hash is not None or repo_url is not None:
            if commit_hash is None:
                raise ValueError("Git workspace source requires a commit_hash")
            return {
                "kind": "git",
                "commit_hash": commit_hash,
                "repo_url": repo_url,
            }

        return None

    @property
    def target_path(self) -> Path:
        """Get effective target path (path / default_target if set)."""
        if not self.path:
            raise ValueError("Workspace path is not initialized")
        if self.default_target:
            return self.path / self.default_target
        return self.path

    @property
    def git_source(self) -> Optional[GitWorkspaceSource]:
        """Return the git source descriptor when present."""
        if isinstance(self.source, GitWorkspaceSource):
            return self.source
        return None

    @property
    def local_source(self) -> Optional[LocalWorkspaceSource]:
        """Return the local-directory source descriptor when present."""
        if isinstance(self.source, LocalWorkspaceSource):
            return self.source
        return None

    @property
    def commit_hash(self) -> Optional[str]:
        """Backward-compatible access to the git commit hash."""
        git_source = self.git_source
        return git_source.commit_hash if git_source else None

    @property
    def repo_url(self) -> Optional[str]:
        """Backward-compatible access to the git repository URL."""
        git_source = self.git_source
        return git_source.repo_url if git_source else None

    @property
    def source_type(self) -> Optional[str]:
        """Backward-compatible access to the source kind."""
        return self.resolved_source_type

    @property
    def source_path(self) -> Optional[Path]:
        """Backward-compatible access to the local source path."""
        local_source = self.local_source
        if local_source:
            return local_source.path
        if self.source is None and self.path is not None:
            return self.path
        return None

    @property
    def resolved_source_type(self) -> Optional[str]:
        """Infer the effective source type when not explicitly provided."""
        if self.source is not None:
            return self.source.kind
        if self.path is not None:
            return "local"
        return None

    @property
    def is_git_source(self) -> bool:
        """Return whether this workspace is backed by a git repository."""
        return self.resolved_source_type == "git"

    @property
    def is_local_source(self) -> bool:
        """Return whether this workspace is backed by a local directory."""
        return self.resolved_source_type == "local"

    @property
    def resolved_source_path(self) -> Path:
        """Get the local source directory for local-directory-backed workspaces."""
        local_source = self.local_source
        if local_source is not None:
            return local_source.path.resolve()
        if self.source is None and self.path is not None:
            return self.path.resolve()
        raise ValueError("Workspace local source path is not initialized")


class LeanWorkspaceInfo(WorkspaceInfo):
    """Workspace metadata for Lean projects.

    Keeps Lean-specific repository metadata explicit while remaining compatible
    with the generic workspace surface.
    """

    default_target: Optional[str] = Field(
        default=None,
        description="Optional Lean target subdirectory filter (e.g., 'Mathlib')"
    )
    toolchain: Optional[str] = Field(
        default=None,
        description="Lean toolchain version (e.g., 'leanprover/lean4:v4.22.0')"
    )


class IsabelleWorkspaceInfo(WorkspaceInfo):
    """Workspace metadata for Isabelle projects.

    Extends the generic workspace information with the session metadata
    required for `isabelle process` based verification.
    """

    session_name: str = Field(..., description="Isabelle session name used for verification")
    working_directory: Optional[Path] = Field(
        default=None,
        description="Optional Isabelle session directory, relative to workspace root or absolute"
    )

    @property
    def effective_working_directory(self) -> Path:
        """Get the directory that should be passed to `isabelle process -d`."""
        if not self.path:
            raise ValueError("Workspace path is not initialized")
        if self.working_directory is None:
            return self.path
        if self.working_directory.is_absolute():
            return self.working_directory
        return self.path / self.working_directory


def _has_lean_workspace_metadata(value: Any) -> bool:
    """Return whether raw workspace data should be parsed as Lean metadata."""
    if not isinstance(value, dict):
        return False

    return (
        value.get("default_target") is not None
        or value.get("toolchain") is not None
    )


def _has_isabelle_workspace_metadata(value: Any) -> bool:
    """Return whether raw workspace data should be parsed as Isabelle metadata."""
    if not isinstance(value, dict):
        return False

    return (
        value.get("session_name") is not None
        or value.get("working_directory") is not None
    )


def parse_workspace_info(value: Any) -> WorkspaceInfo:
    """Parse workspace metadata into the appropriate concrete workspace model."""
    if isinstance(value, WorkspaceInfo):
        return value
    if _has_isabelle_workspace_metadata(value):
        return IsabelleWorkspaceInfo.model_validate(value)
    if _has_lean_workspace_metadata(value):
        return LeanWorkspaceInfo.model_validate(value)
    return WorkspaceInfo.model_validate(value)


def parse_workspace_info_list(value: Any) -> Optional[List[WorkspaceInfo]]:
    """Parse a list of workspace metadata dictionaries into concrete models."""
    if value is None:
        return None
    return [parse_workspace_info(item) for item in value]
