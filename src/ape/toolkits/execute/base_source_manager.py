"""
Base Source Manager - Git repository and worktree management.

Provides common functionality for cloning repositories and creating worktrees.
Language-specific managers should inherit from this class.
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING

import git
import aiofiles.os

from .config import CodeExecuteToolConfig
from ape.utils.file_ops import file_lock, safe_remove_directory, normalize_repo_url
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging


class BaseSourceManager:
    """Base class for managing Git source repositories and worktrees.

    Provides:
    - Repository cloning with retry logic
    - Worktree creation and cleanup
    - Commit checkout operations

    Subclasses can extend for language-specific build processes.
    """

    def __init__(
        self,
        config: Optional[CodeExecuteToolConfig] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        repo_url: Optional[str] = None
    ):
        """Initialize source manager.

        Args:
            config: Configuration object
            logger: Logger instance
            repo_url: Repository URL (uses default if not provided)
        """
        self.config = config or CodeExecuteToolConfig()
        self.logger = logger or create_logger()
        self.repo_url = repo_url or self.config.default_repo_url

        if self.repo_url:
            self.repo_name = normalize_repo_url(self.repo_url)
        else:
            self.repo_name = None

        self._git_repo: Optional[git.Repo] = None

        self.logger.info(f"BaseSourceManager initialized: repo={self.repo_name}")

    @property
    def repo_path(self) -> Path:
        """Get the local path for the repository source."""
        if not self.repo_name:
            raise ValueError("Repository name not set")
        return self.config.get_repo_source_path(self.repo_name)

    @property
    def repo_lock_path(self) -> Path:
        """Get the lock path for Git operations that mutate the shared source repo."""
        if not self.repo_name:
            raise ValueError("Repository name not set")
        return self.config.get_repo_base_dir(self.repo_name) / "locks" / "source.lock"

    def _get_git_repo(self) -> git.Repo:
        """Get or create Git repository instance.

        Raises:
            RuntimeError: If repository doesn't exist and needs to be cloned first.
        """
        if self._git_repo is None:
            if not self.repo_path.exists():
                raise RuntimeError(
                    f"Repository not found at {self.repo_path}. "
                    f"Call ensure_repository_cloned() first."
                )
            self._git_repo = git.Repo(self.repo_path)
        return self._git_repo

    async def _ref_exists_locally(self, git_ref: str) -> bool:
        """Return True when the requested ref/commit already exists locally."""
        try:
            repo = self._get_git_repo()
            await asyncio.to_thread(repo.git.rev_parse, "--verify", f"{git_ref}^{{commit}}")
            return True
        except Exception:
            return False

    async def _ensure_repository_cloned_unlocked(self) -> bool:
        """Ensure repository is cloned without acquiring the repo mutation lock."""
        if await aiofiles.os.path.exists(self.repo_path):
            self.logger.info(f"Repository already exists: {self.repo_name}")
            return True

        self.logger.info(f"Cloning repository: {self.repo_url} -> {self.repo_path}")

        for attempt in range(self.config.max_retries):
            try:
                await aiofiles.os.makedirs(self.repo_path.parent, exist_ok=True)

                await asyncio.to_thread(
                    git.Repo.clone_from,
                    self.repo_url,
                    str(self.repo_path)
                )

                self.logger.info(f"Repository cloned successfully: {self.repo_name}")
                return True

            except Exception as e:
                self.logger.warning(f"Clone attempt {attempt + 1} failed: {e}")

                # Cleanup failed clone
                if await aiofiles.os.path.exists(self.repo_path):
                    try:
                        await safe_remove_directory(self.repo_path)
                    except Exception:
                        pass

                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_base_delay * (attempt + 1)
                    await asyncio.sleep(delay)

        self.logger.error(f"Failed to clone after {self.config.max_retries} attempts")
        return False

    async def ensure_repository_cloned(self) -> bool:
        """Ensure repository is cloned to source directory.

        Returns:
            True if successful, False otherwise.
        """
        async with file_lock(self.repo_lock_path, timeout=self.config.git_operation_timeout):
            return await self._ensure_repository_cloned_unlocked()

    async def _fetch_updates_unlocked(self) -> bool:
        """Fetch updates from the remote repository without acquiring the repo lock."""
        try:
            repo = self._get_git_repo()
            await asyncio.to_thread(repo.remotes.origin.fetch)
            self.logger.debug(f"Fetched updates for {self.repo_name}")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to fetch updates: {e}")
            return False

    async def fetch_updates(self) -> bool:
        """Fetch updates from remote repository.

        Returns:
            True if successful, False otherwise.
        """
        async with file_lock(self.repo_lock_path, timeout=self.config.git_operation_timeout):
            clone_success = await self._ensure_repository_cloned_unlocked()
            if not clone_success:
                return False
            return await self._fetch_updates_unlocked()

    async def create_worktree(
        self,
        commit_hash: str,
        target_dir: Path,
        force: bool = False
    ) -> Path:
        """Create a git worktree for a specific commit.

        Args:
            commit_hash: Target commit hash
            target_dir: Directory to create worktree in
            force: Force creation even if exists

        Returns:
            Path to the created worktree.

        Raises:
            RuntimeError: If worktree creation fails.
        """
        worktree_path = target_dir / f"{commit_hash}_{os.getpid()}_{uuid.uuid4().hex[:8]}"

        try:
            await aiofiles.os.makedirs(target_dir, exist_ok=True)
            async with file_lock(self.repo_lock_path, timeout=self.config.git_operation_timeout):
                clone_success = await self._ensure_repository_cloned_unlocked()
                if not clone_success:
                    raise RuntimeError(f"Failed to clone repository for {self.repo_name}")

                # Only fetch when the requested revision is not already available locally.
                if not await self._ref_exists_locally(commit_hash):
                    await self._fetch_updates_unlocked()

                repo = self._get_git_repo()

                # Create worktree while holding the repo mutation lock so
                # concurrent workers do not race on shared Git metadata.
                force_flag = '-f' if force else ''
                if force_flag:
                    await asyncio.to_thread(
                        repo.git.worktree,
                        'add', force_flag,
                        str(worktree_path),
                        commit_hash
                    )
                else:
                    await asyncio.to_thread(
                        repo.git.worktree,
                        'add',
                        str(worktree_path),
                        commit_hash
                    )

            self.logger.info(f"Created worktree: {worktree_path}")
            return worktree_path

        except Exception as e:
            # Cleanup on failure
            if await aiofiles.os.path.exists(worktree_path):
                await safe_remove_directory(worktree_path)
            raise RuntimeError(f"Failed to create worktree for {commit_hash}") from e

    async def create_plain_worktree(
        self,
        commit_hash: str,
        workspace_name: Optional[str] = None
    ) -> Path:
        """Create a plain worktree (no compilation) for a commit.

        This is the primary method for non-compiled workspace creation.

        Args:
            commit_hash: Target commit hash
            workspace_name: Optional custom name (defaults to commit_hash)

        Returns:
            Path to the created workspace.
        """
        workspace_dir = self.config.get_plain_workspace_dir(self.repo_name)
        workspace_name = workspace_name or commit_hash
        workspace_path = workspace_dir / workspace_name

        # Check if already exists
        if await aiofiles.os.path.exists(workspace_path):
            self.logger.info(f"Plain workspace already exists: {workspace_path}")
            return workspace_path

        # Create worktree
        temp_worktree = await self.create_worktree(
            commit_hash,
            workspace_dir.parent / "temp_worktrees"
        )

        try:
            # Move to final location
            await aiofiles.os.makedirs(workspace_dir, exist_ok=True)
            await asyncio.to_thread(os.rename, str(temp_worktree), str(workspace_path))

            self.logger.info(f"Plain workspace created: {workspace_path}")
            return workspace_path

        except Exception as e:
            # Cleanup
            if await aiofiles.os.path.exists(temp_worktree):
                await safe_remove_directory(temp_worktree)
            raise RuntimeError(f"Failed to create plain workspace for {commit_hash}") from e

    async def cleanup_worktree(self, worktree_path: Path) -> None:
        """Clean up a worktree and its git reference.

        Args:
            worktree_path: Path to the worktree to remove.
        """
        try:
            # Remove directory
            if await aiofiles.os.path.exists(worktree_path):
                await safe_remove_directory(worktree_path)

            # Remove git reference
            try:
                if await aiofiles.os.path.exists(self.repo_path):
                    async with file_lock(self.repo_lock_path, timeout=self.config.git_operation_timeout):
                        repo = self._get_git_repo()
                        await asyncio.to_thread(
                            repo.git.worktree,
                            'remove', '--force',
                            str(worktree_path)
                        )
            except git.GitCommandError:
                pass  # Already removed or doesn't exist

            self.logger.debug(f"Cleaned up worktree: {worktree_path}")

        except Exception as e:
            self.logger.warning(f"Failed to cleanup worktree {worktree_path}: {e}")

    async def list_commits(
        self,
        max_count: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[str]:
        """List commit hashes from the repository.

        Args:
            max_count: Maximum number of commits to return
            since: Only commits after this date (YYYY-MM-DD)
            until: Only commits before this date (YYYY-MM-DD)

        Returns:
            List of commit hashes.
        """
        await self.ensure_repository_cloned()
        repo = self._get_git_repo()

        kwargs = {}
        if max_count:
            kwargs['max_count'] = max_count
        if since:
            kwargs['since'] = since
        if until:
            kwargs['until'] = until

        commits = [commit.hexsha for commit in repo.iter_commits('HEAD', **kwargs)]
        return commits

    async def get_workspace(self, commit_hash: str) -> Path:
        """Get or create a plain workspace for a commit.

        Args:
            commit_hash: Target commit hash

        Returns:
            Path to the workspace directory.
        """
        workspace_dir = self.config.get_plain_workspace_dir(self.repo_name)
        workspace_path = workspace_dir / commit_hash

        # Check if exists
        if await aiofiles.os.path.exists(workspace_path):
            self.logger.debug(f"Workspace exists: {commit_hash}")
            return workspace_path

        # Create new workspace
        return await self.create_plain_worktree(commit_hash, commit_hash)
