"""
Lean Build Manager - Inherits from BaseSourceManager.

Adds Lean-specific build functionality (lake build, cache management).
"""

import os
import re
import asyncio
import uuid
import shutil
import hashlib
import inspect
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Optional, Sequence, TYPE_CHECKING
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



# --- reviewed workspaces ---------------------------------------------------------------------
#
# A compiled snapshot of one commit is the wrong environment to verify a pull request in. The
# review overlay applies the PR's diff to *source* only, so every compile resolves imports
# through the base commit's build products: a declaration the PR adds or renames in one file is
# an `Unknown constant` when any other file is verified. Measured on the 12-PR held-out run,
# 41 of 321 arm sessions received such an error and 16 findings asserted a build failure on PRs
# that all build. A reviewed workspace is the base snapshot plus the diff plus a targeted
# rebuild of the changed modules -- the environment the PR was actually written in.
#
# It is built IN PLACE, not through the content-store snapshot path. `list_files_recursive`
# does not descend symlinked directories, and a reviewed workspace is mostly symlinks into its
# base; storing it would mean expanding every directory of Mathlib and its packages first.
# `RestoreManager._execute_restore` already treats an existing non-empty `workspaces/<id>` as
# restored, so an in-place build needs no snapshot: `complete_build` marks it BUILT and the
# first `get_workspace` flips it READY.
#
# What was measured before choosing a real copy of `.lake/build` (33337, 2 changed files):
#   * hardlink tree (`cp -al`, 31s): Lean creates `.olean` fresh but opens `.ilean` in place --
#     EACCES on the 444 shared inode. Mixed write semantics make hardlinks unusable for
#     anything Lean rewrites, and the rewrite set spans every module on an import path between
#     two changed files. The base's 444 mode turned every wrong guess into a loud failure and
#     never a corruption, which is the property this design keeps.
#   * reflink: the store is NFSv3; `cp --reflink` is not supported.
#   * real copy (2.7 GB): ~10.5 min on this NFS, then `lake build` 67s for a ten-module chain,
#     140 files written, base untouched, `Positive.lean` verifies with zero unknown constants.
# Once per episode, not per attempt: a held-out run materialises 12 overlays per PR.


def patch_fingerprint(base_commit: str, pr_diff: str) -> str:
    """The identity of "this diff applied to this commit": sha256 of commit, NUL, diff.

    One definition. The review overlay's `.ape_pr_review_patch.json` marker records the full
    digest; a reviewed workspace's name carries its first twelve hex characters. Both call
    this, so they agree by construction rather than by two functions happening to match.
    """

    digest = hashlib.sha256()
    digest.update((base_commit or "").encode("utf-8"))
    digest.update(b"\0")
    digest.update((pr_diff or "").encode("utf-8"))
    return digest.hexdigest()


def reviewed_workspace_key(base_commit: str, pr_diff: str) -> str:
    """`<base sha>+<12 hex>`: one reviewed workspace per (base commit, diff) pair. Twelve hex
    characters after the commit it was built from is enough to read and to keep distinct."""

    return f"{base_commit}+{patch_fingerprint(base_commit, pr_diff)[:12]}"


def is_reviewed_workspace_key(workspace_id: str) -> bool:
    """A base commit is forty hex characters; a reviewed key carries the diff's mark after `+`."""

    return "+" in str(workspace_id or "")


def lake_targets_for_changed_files(changed_files: Sequence[str], root: Path) -> list[str]:
    """`+Mathlib.A.B` for every changed `.lean` that still exists and lives in a Lake library.

    A library is recognised by its root aggregator (`Mathlib.lean`, `Archive.lean`,
    `Counterexamples.lean`) sitting beside it. Files the PR deletes, non-Lean files and files
    outside any library are left out; Lake would refuse them, and a targeted build that names
    only real modules is what keeps its rebuild set to the changed modules and the import
    paths between them.
    """

    targets: list[str] = []
    for rel in changed_files or ():
        rel = str(rel).strip().replace("\\", "/")
        if not rel.endswith(".lean"):
            continue
        parts = rel[:-len(".lean")].split("/")
        if len(parts) < 2 or not (root / f"{parts[0]}.lean").is_file():
            continue
        if not (root / rel).is_file():
            continue
        target = "+" + ".".join(parts)
        if target not in targets:
            targets.append(target)
    return targets

#: How long a second builder waits for a reviewed build another process owns. The base
#: build's bound is `restore_queue_timeout` (600 s), sized for a restore; a reviewed build
#: is a 2.8 GB copy plus a Lake rebuild and two of the first twelve took 776 s and 997 s, so
#: a waiter on that bound reported the key FAILED while the first builder was fine.
REVIEWED_BUILD_WAIT_SECONDS = 3600.0


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

    async def _wait_for_build_completion(
        self, commit_hash: str, timeout: Optional[float] = None,
    ) -> BuildResult:
        """Wait for another process to finish building the same workspace."""
        actual_timeout = timeout if timeout is not None else self.config.restore_queue_timeout
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
            if current_state.status in (
                WorkspaceStatus.BUILT,
                WorkspaceStatus.READY,
                WorkspaceStatus.RESTORING,
            ):
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
                
        except AlreadyBuildingError:
            self.logger.info(
                "Another process is already building %s; waiting for it to finish",
                commit_hash,
            )
            return await self._wait_for_build_completion(commit_hash)

        except AlreadyRestoringError:
            self.logger.info(
                "Workspace %s is already being restored; waiting for the compiled snapshot to be ready",
                commit_hash,
            )
            return await self._wait_for_build_completion(commit_hash)
            
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

    async def build_reviewed_workspace(
        self,
        key: str,
        base_commit: str,
        *,
        prepare_sources: Callable[[Path, Path], Awaitable[None]],
        changed_files: Sequence[str],
        force_rebuild: bool = False,
    ) -> BuildResult:
        """Build `workspaces/<key>`: the base snapshot, the PR's diff, and its changed modules rebuilt.

        `prepare_sources(build_root, base_root)` lays down the source overlay -- symlinks to
        the base and the PR's changed files as patched real copies. It is a callable because
        overlay creation and patching belong to the task layer that owns them, and the toolkit
        must not import it. This method owns the Lean half: replacing the `.lake` symlink with
        a real directory whose `build` is a writable copy, the targeted `lake build`, the
        read-only finalisation, the atomic rename into place, and the state machine.

        The Lake targets are derived from `changed_files` *after* the sources are prepared,
        against the patched tree: a module the PR adds is absent at base and one it deletes is
        present there, so the base tree gives the wrong answer in both directions and the
        patched tree exists only inside this call.

        Locking, waiting and dead-builder takeover are the base build's, unchanged: the key is
        just a workspace id to `try_start_build`.
        """

        start_time = datetime.now()
        self.logger.info("Start building reviewed workspace: %s (base %s)", key, base_commit)
        try:
            current_state = await self.state_manager.try_start_build(key, force_rebuild)
            if current_state.status in (
                WorkspaceStatus.BUILT, WorkspaceStatus.READY, WorkspaceStatus.RESTORING,
            ):
                self.logger.info("Reviewed workspace already built: %s", key)
                return BuildResult(success=True, commit_hash=key, build_duration=0.0,
                                   file_count=current_state.file_count)
            file_count = await self._execute_reviewed_build(
                key, base_commit, prepare_sources=prepare_sources,
                changed_files=list(changed_files), force_rebuild=force_rebuild)
            build_duration = (datetime.now() - start_time).total_seconds()
            await self.state_manager.complete_build(key, True, build_duration, file_count)
            self.logger.info("Reviewed workspace built: %s in %.1fs", key, build_duration)
            return BuildResult(success=True, commit_hash=key,
                               build_duration=build_duration, file_count=file_count)
        except AlreadyBuildingError:
            self.logger.info("Another process is building %s; waiting", key)
            return await self._wait_for_build_completion(key, timeout=REVIEWED_BUILD_WAIT_SECONDS)
        except AlreadyRestoringError:
            return await self._wait_for_build_completion(key, timeout=REVIEWED_BUILD_WAIT_SECONDS)
        except Exception as exc:
            build_duration = (datetime.now() - start_time).total_seconds()
            self.logger.error("Reviewed workspace build failed %s: %s", key, exc)
            try:
                await self.state_manager.complete_build(
                    key, False, build_duration, 0,
                    error_message=str(exc), error_type=type(exc).__name__)
            except Exception:  # noqa: BLE001
                pass
            raise

    async def _execute_reviewed_build(
        self,
        key: str,
        base_commit: str,
        *,
        prepare_sources: Callable[[Path, Path], Awaitable[None]],
        changed_files: list[str],
        force_rebuild: bool = False,
    ) -> int:
        from .restore_manager import set_workspace_readonly

        # The restored-workspace root, the same one `RestoreManager.get_workspace` links
        # `target/` to. It is asked of the config each time rather than cached on the manager
        # because this manager builds into `build_workspaces/` everywhere else and has no
        # attribute for it -- the first real run failed on exactly that assumption.
        workspace_dir = self.config.get_workspace_dir(self.repo_name)
        base_root = workspace_dir / base_commit
        if not (base_root / "Mathlib").is_dir():
            raise RuntimeError(
                f"[{key}] base workspace {base_commit} is not built at {base_root}; "
                "build the base commit first")

        final_root = workspace_dir / key
        # A hidden sibling of its final name, not the manager's scratch area. `rename()` of a
        # directory across parents must rewrite its `..` entry, which needs write permission on
        # the directory being moved -- and it has just been finalised to 0o555. Same-parent, the
        # rename touches only the parent's write bit, and `workspaces/<key>` exists only once it
        # is complete and read-only. A crash leaves a dotted name nothing looks up by.
        build_root = workspace_dir / f".{key}.{os.getpid()}.{uuid.uuid4().hex[:8]}"
        await aiofiles.os.makedirs(workspace_dir, exist_ok=True)
        # A builder that died hard (SIGKILL, OOM, node loss) skips its `finally` and leaves a
        # dotted tree of up to 2.8 GB that nothing else enumerates. The pid is in the name.
        for stale in self._dead_build_roots(workspace_dir, key):
            self.logger.warning("Removing orphaned reviewed build tree %s: its builder is gone",
                                stale.name)
            await asyncio.to_thread(self._make_tree_removable, stale)
            await safe_remove_directory(stale)
        try:
            await prepare_sources(build_root, base_root)
            targets = lake_targets_for_changed_files(changed_files, build_root)
            if not targets:
                # Before the copy: it is the expensive step, and a workspace with nothing
                # rebuilt in it would be the base overlay under a name that promises more.
                raise RuntimeError(
                    f"[{key}] no Lake targets: nothing in the diff is a library module")
            await asyncio.to_thread(self._materialize_build_tree, build_root, base_root)

            stdout, stderr, code = await run_command(
                ["lake", "build", *targets],
                cwd=build_root, timeout=self.config.build_timeout, print_output=False,
                operation_name=f"lake build {key}", logger=self.logger,
            )
            if code == -15:
                raise TimeoutError(f"[{key}] reviewed build timed out ({self.config.build_timeout}s)")
            if code != 0:
                tail = "\n".join((stderr or stdout or "").splitlines()[-25:])
                raise RuntimeError(f"[{key}] lake build {' '.join(targets)} failed:\n{tail}")

            await set_workspace_readonly(build_root, self.logger)
            replaced: Optional[Path] = None
            if force_rebuild and await aiofiles.os.path.isdir(final_root):
                # Move the tree being replaced aside first. `rename` refuses a non-empty
                # target, and the OSError branch below would read that refusal as "another
                # builder won" -- keeping the old tree, discarding the new one, and
                # recording success. Same parent, so the rename needs no write bit on the
                # 0o555 tree itself.
                replaced = workspace_dir / f".{key}.replaced.{os.getpid()}.{uuid.uuid4().hex[:8]}"
                await asyncio.to_thread(os.rename, final_root, replaced)
            try:
                await asyncio.to_thread(os.rename, build_root, final_root)
            except OSError:
                if final_root.is_dir() and os.listdir(final_root):
                    # Another builder finished first; ours is redundant, not wrong.
                    self.logger.info("Reviewed workspace %s appeared while building; using it", key)
                else:
                    raise
            if replaced is not None:
                await asyncio.to_thread(self._make_tree_removable, replaced)
                await safe_remove_directory(replaced)
            files = await list_files_recursive(final_root)
            return len(files)
        finally:
            if await aiofiles.os.path.exists(build_root):
                await asyncio.to_thread(self._make_tree_removable, build_root)
                await safe_remove_directory(build_root)

    @staticmethod
    def _dead_build_roots(workspace_dir: Path, key: str) -> list[Path]:
        """Hidden build trees for `key` whose builder pid is no longer alive.

        Names are `.<key>.<pid>.<hex>` and `.<key>.replaced.<pid>.<hex>`; the key itself has
        no dots. A live pid means another builder owns that tree and it is left alone.
        """

        stale = []
        for path in sorted(workspace_dir.glob(f".{key}.*")):
            if not path.is_dir() or path.is_symlink():
                continue
            pid = next((int(part) for part in path.name.split(".") if part.isdigit()), None)
            if pid is None or not is_process_alive(pid):
                stale.append(path)
        return stale

    @staticmethod
    def _materialize_build_tree(build_root: Path, base_root: Path) -> None:
        """Replace the overlay's `.lake` symlink with a real `.lake` whose `build` is writable.

        Every other child of `.lake` (the dependency packages) stays a symlink into the base:
        a Mathlib diff never rebuilds them. `build` is a real copy because Lean rewrites some
        artifacts in place, which rules out hardlinks (see the module comment), and the set it
        rewrites is not knowable before the build runs.

        Only the copy is made writable. Symlinks are never chmod'd -- chmod follows them, and
        the target is the base's 444 inode.
        """

        lake = build_root / ".lake"
        base_lake = base_root / ".lake"
        if lake.is_symlink():
            lake.unlink()
        lake.mkdir(exist_ok=True)
        for child in base_lake.iterdir():
            dest = lake / child.name
            if child.name == "build":
                continue
            if not dest.exists() and not dest.is_symlink():
                dest.symlink_to(child)
        build = lake / "build"
        if not build.exists():
            shutil.copytree(base_lake / "build", build, symlinks=True)
        for dirpath, dirnames, filenames in os.walk(build):
            os.chmod(dirpath, 0o755)
            for name in filenames:
                path = Path(dirpath) / name
                if not path.is_symlink():
                    os.chmod(path, 0o644)

    @staticmethod
    def _make_tree_removable(root: Path) -> None:
        """Undo read-only finalisation on a build dir we are about to delete, symlinks excluded."""

        for dirpath, dirnames, filenames in os.walk(root):
            try:
                os.chmod(dirpath, 0o755)
            except OSError:
                pass
            for name in filenames:
                path = Path(dirpath) / name
                if not path.is_symlink():
                    try:
                        os.chmod(path, 0o644)
                    except OSError:
                        pass

    async def build_workspace_from_ref(
        self,
        commit_hash: str,
        *,
        fetch_repo_url: Optional[str],
        fetch_ref: Optional[str],
        cache_repo_full_name: Optional[str] = None,
        force_rebuild: bool = False,
    ) -> BuildResult:
        """Build a workspace, fetching the requested revision when needed.

        This is primarily used for PR head commits that may only exist in a fork.
        The build still lands in the standard compiled-workspace snapshot store.
        """
        start_time = datetime.now()
        self.logger.info(
            "Start building workspace from ref: %s (fetch_repo_url=%s, fetch_ref=%s)",
            commit_hash,
            fetch_repo_url,
            fetch_ref,
        )

        try:
            current_state = await self.state_manager.try_start_build(commit_hash, force_rebuild)

            if current_state.status in (
                WorkspaceStatus.BUILT,
                WorkspaceStatus.READY,
                WorkspaceStatus.RESTORING,
            ):
                self.logger.info(f"Workspace already built: {commit_hash}")
                return BuildResult(
                    success=True,
                    commit_hash=commit_hash,
                    build_duration=0.0,
                    file_count=current_state.file_count,
                )

            self.logger.info(f"Execute build from ref: {commit_hash}")
            file_count = await self._execute_build(
                commit_hash,
                fetch_repo_url=fetch_repo_url,
                fetch_ref=fetch_ref,
                cache_repo_full_name=cache_repo_full_name,
            )

            build_duration = (datetime.now() - start_time).total_seconds()
            await self.state_manager.complete_build(
                commit_hash, True, build_duration, file_count
            )

            self.logger.info(f"Build from ref successful: {commit_hash}, time: {build_duration:.2f}s")
            return BuildResult(
                success=True,
                commit_hash=commit_hash,
                build_duration=build_duration,
                file_count=file_count,
            )

        except AlreadyBuildingError:
            self.logger.info(
                "Another process is already building %s; waiting for it to finish",
                commit_hash,
            )
            return await self._wait_for_build_completion(commit_hash)

        except AlreadyRestoringError:
            self.logger.info(
                "Workspace %s is already being restored; waiting for the compiled snapshot to be ready",
                commit_hash,
            )
            return await self._wait_for_build_completion(commit_hash)

        except Exception as e:
            build_duration = (datetime.now() - start_time).total_seconds()
            error_message = str(e)

            self.logger.error(f"Build-from-ref exception {commit_hash}: {error_message}")

            try:
                await self.state_manager.complete_build(
                    commit_hash, False, build_duration, 0, error_message, type(e).__name__
                )
            except Exception:
                pass

            raise

    async def prepare_workspace_from_ref_with_cache_probe(
        self,
        commit_hash: str,
        *,
        fetch_repo_url: Optional[str],
        fetch_ref: Optional[str],
        cache_repo_full_name: Optional[str] = None,
        verify_targets: Optional[Iterable[str]] = None,
        progress_callback: Optional[Callable[[str], Any]] = None,
        force_rebuild: bool = False,
    ) -> BuildResult:
        """Try to prepare a compiled workspace using bounded cache-only steps."""
        start_time = datetime.now()
        self.logger.info(
            "Start cache-only workspace preparation from ref: %s (fetch_repo_url=%s, fetch_ref=%s)",
            commit_hash,
            fetch_repo_url,
            fetch_ref,
        )

        try:
            current_state = await self.state_manager.try_start_build(commit_hash, force_rebuild)

            if current_state.status in (
                WorkspaceStatus.BUILT,
                WorkspaceStatus.READY,
                WorkspaceStatus.RESTORING,
            ):
                self.logger.info(f"Workspace already built: {commit_hash}")
                return BuildResult(
                    success=True,
                    commit_hash=commit_hash,
                    build_duration=0.0,
                    file_count=current_state.file_count,
                )

            self.logger.info(f"Execute cache-only preparation from ref: {commit_hash}")
            file_count = await self._execute_cache_probe_prepare(
                commit_hash,
                fetch_repo_url=fetch_repo_url,
                fetch_ref=fetch_ref,
                cache_repo_full_name=cache_repo_full_name,
                verify_targets=verify_targets,
                progress_callback=progress_callback,
            )

            build_duration = (datetime.now() - start_time).total_seconds()
            await self.state_manager.complete_build(
                commit_hash, True, build_duration, file_count
            )

            self.logger.info(
                "Cache-only workspace preparation from ref successful: %s, time: %.2fs",
                commit_hash,
                build_duration,
            )
            return BuildResult(
                success=True,
                commit_hash=commit_hash,
                build_duration=build_duration,
                file_count=file_count,
            )

        except AlreadyBuildingError:
            self.logger.info(
                "Another process is already building %s; waiting for it to finish",
                commit_hash,
            )
            return await self._wait_for_build_completion(commit_hash)

        except AlreadyRestoringError:
            self.logger.info(
                "Workspace %s is already being restored; waiting for the compiled snapshot to be ready",
                commit_hash,
            )
            return await self._wait_for_build_completion(commit_hash)

        except Exception as e:
            build_duration = (datetime.now() - start_time).total_seconds()
            error_message = str(e)

            self.logger.info(f"Cache-only workspace preparation miss {commit_hash}: {error_message}")

            try:
                await self.state_manager.complete_build(
                    commit_hash, False, build_duration, 0, error_message, type(e).__name__
                )
            except Exception:
                pass

            raise

    async def _commit_exists_locally(self, commit_hash: str) -> bool:
        """Return True if the commit object already exists in the local repo."""
        try:
            repo = self._get_git_repo()
            await asyncio.to_thread(repo.git.rev_parse, "--verify", f"{commit_hash}^{{commit}}")
            return True
        except Exception:
            return False

    async def _prepare_build_revision(
        self,
        commit_hash: str,
        *,
        fetch_repo_url: Optional[str] = None,
        fetch_ref: Optional[str] = None,
    ) -> Optional[str]:
        """Ensure the requested commit is available locally and return a temp ref if created."""
        async with file_lock(self.repo_lock_path, timeout=self.config.git_operation_timeout):
            clone_success = await self._ensure_repository_cloned_unlocked()
            if not clone_success:
                raise RuntimeError(f"Failed to clone repository for {self.repo_name}")

            if await self._commit_exists_locally(commit_hash):
                return None

            await self._fetch_updates_unlocked()

            if await self._commit_exists_locally(commit_hash):
                return None

            normalized_fetch_repo_url = str(fetch_repo_url or "").strip()
            normalized_fetch_ref = str(fetch_ref or "").strip()
            if not normalized_fetch_repo_url or not normalized_fetch_ref:
                raise RuntimeError(
                    f"Commit {commit_hash} is not available locally and no fetch repo/ref were provided"
                )

            repo = self._get_git_repo()
            local_ref = f"refs/ape/pr-review/{commit_hash}"
            fetch_specs: list[str] = []
            if normalized_fetch_ref.startswith("refs/"):
                fetch_specs.append(f"+{normalized_fetch_ref}:{local_ref}")
            else:
                fetch_specs.append(f"+refs/heads/{normalized_fetch_ref}:{local_ref}")
                fetch_specs.append(f"+{normalized_fetch_ref}:{local_ref}")
            fetch_specs.append(f"+{commit_hash}:{local_ref}")

            seen_specs: set[str] = set()
            deduped_fetch_specs: list[str] = []
            for spec in fetch_specs:
                if spec in seen_specs:
                    continue
                seen_specs.add(spec)
                deduped_fetch_specs.append(spec)

            last_error: Optional[Exception] = None
            for fetch_spec in deduped_fetch_specs:
                try:
                    self.logger.info(
                        "Fetching commit %s from %s via %s",
                        commit_hash,
                        normalized_fetch_repo_url,
                        fetch_spec,
                    )
                    await asyncio.to_thread(
                        repo.git.fetch,
                        normalized_fetch_repo_url,
                        fetch_spec,
                    )
                    if await self._commit_exists_locally(commit_hash):
                        return local_ref
                except Exception as exc:
                    last_error = exc
                    self.logger.warning(
                        "Failed to fetch %s from %s via %s: %s",
                        commit_hash,
                        normalized_fetch_repo_url,
                        fetch_spec,
                        exc,
                    )

            if await self._commit_exists_locally(commit_hash):
                return local_ref

            raise RuntimeError(
                f"Unable to fetch commit {commit_hash} from {normalized_fetch_repo_url} (ref={normalized_fetch_ref})"
            ) from last_error

    async def _delete_local_ref(self, local_ref: str) -> None:
        """Delete a temporary local ref created for a PR-head build."""
        try:
            async with file_lock(self.repo_lock_path, timeout=self.config.git_operation_timeout):
                repo = self._get_git_repo()
                await asyncio.to_thread(repo.git.update_ref, "-d", local_ref)
        except Exception as exc:
            self.logger.debug(f"Failed to delete temporary ref {local_ref}: {exc}")

    async def _execute_build(
        self,
        commit_hash: str,
        *,
        fetch_repo_url: Optional[str] = None,
        fetch_ref: Optional[str] = None,
        cache_repo_full_name: Optional[str] = None,
    ) -> int:
        """Execute actual build process

        Returns:
            int: Number of files built

        Raises:
            RuntimeError: Build process error
            OSError: File system operation error
            TimeoutError: Build timeout
        """
        build_workspace_path = None
        temporary_local_ref = None

        try:
            if fetch_repo_url or fetch_ref:
                temporary_local_ref = await self._prepare_build_revision(
                    commit_hash,
                    fetch_repo_url=fetch_repo_url,
                    fetch_ref=fetch_ref,
                )

            # 1. Create build worktree (using inherited method)
            build_workspace_path = await self.create_worktree(
                commit_hash,
                self.build_workspace_dir
            )

            # 2. Run lake build (Lean-specific)
            await self._run_lake_build(
                build_workspace_path,
                commit_hash,
                cache_repo_full_name=cache_repo_full_name,
            )

            # 3. Create snapshot (Lean-specific)
            file_count = await self._create_snapshot(commit_hash, build_workspace_path)

            return file_count

        finally:
            # Cleanup build workspace (using inherited method)
            if build_workspace_path:
                await self.cleanup_worktree(build_workspace_path)
            if temporary_local_ref:
                await self._delete_local_ref(temporary_local_ref)

    async def _execute_cache_probe_prepare(
        self,
        commit_hash: str,
        *,
        fetch_repo_url: Optional[str] = None,
        fetch_ref: Optional[str] = None,
        cache_repo_full_name: Optional[str] = None,
        verify_targets: Optional[Iterable[str]] = None,
        progress_callback: Optional[Callable[[str], Any]] = None,
    ) -> int:
        build_workspace_path = None
        temporary_local_ref = None

        try:
            if fetch_repo_url or fetch_ref:
                await self._emit_progress(
                    progress_callback,
                    f"Fetching PR-head commit {commit_hash[:8]} into the local mathlib repository...",
                )
                temporary_local_ref = await self._prepare_build_revision(
                    commit_hash,
                    fetch_repo_url=fetch_repo_url,
                    fetch_ref=fetch_ref,
                )

            build_workspace_path = await self.create_worktree(
                commit_hash,
                self.build_workspace_dir,
            )

            await self._prepare_cached_workspace(
                build_workspace_path,
                commit_hash,
                cache_repo_full_name=cache_repo_full_name,
                verify_targets=verify_targets,
                progress_callback=progress_callback,
            )

            await self._emit_progress(
                progress_callback,
                f"Snapshotting the cache-prepared PR-head workspace for {commit_hash[:8]}...",
            )
            return await self._create_snapshot(commit_hash, build_workspace_path)

        finally:
            if build_workspace_path:
                await self.cleanup_worktree(build_workspace_path)
            if temporary_local_ref:
                await self._delete_local_ref(temporary_local_ref)

    
    async def _run_lake_build(
        self,
        build_workspace_path: Path,
        commit_hash: str,
        *,
        cache_repo_full_name: Optional[str] = None,
    ) -> None:
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
            cache_success = await self._get_cache_for_workspace(
                build_workspace_path,
                commit_hash,
                cache_repo_full_name=cache_repo_full_name,
            )
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

    async def _prepare_cached_workspace(
        self,
        build_workspace_path: Path,
        commit_hash: str,
        *,
        cache_repo_full_name: Optional[str] = None,
        verify_targets: Optional[Iterable[str]] = None,
        progress_callback: Optional[Callable[[str], Any]] = None,
    ) -> None:
        lake_dir = build_workspace_path / ".lake"
        if await aiofiles.os.path.exists(lake_dir):
            await safe_remove_directory(lake_dir)

        probe_target = "Mathlib/Init.lean"
        probe_module = "Mathlib.Init"

        await self._emit_progress(
            progress_callback,
            f"Probing the remote Mathlib cache for {commit_hash[:8]} with {probe_module}...",
        )
        probe_success = await self._get_cache_for_workspace(
            build_workspace_path,
            commit_hash,
            cache_repo_full_name=cache_repo_full_name,
            cache_args=[probe_target],
            timeout=self.config.pr_head_cache_probe_timeout,
        )
        if not probe_success:
            raise RuntimeError(f"[{commit_hash}] PR-head cache probe did not find {probe_module}")

        await self._emit_progress(
            progress_callback,
            f"Verifying the initial PR-head cache probe for {commit_hash[:8]} without compiling...",
        )
        await self._run_lake_no_build(
            build_workspace_path,
            commit_hash,
            targets=[probe_module],
            timeout=self.config.pr_head_cache_verify_timeout,
        )

        await self._emit_progress(
            progress_callback,
            f"Fetching the remaining cached artifacts for PR-head {commit_hash[:8]}...",
        )
        full_fetch_success = await self._get_cache_for_workspace(
            build_workspace_path,
            commit_hash,
            cache_repo_full_name=cache_repo_full_name,
            timeout=self.config.pr_head_cache_fetch_timeout,
        )
        if not full_fetch_success:
            raise RuntimeError(f"[{commit_hash}] PR-head cache fetch did not complete within the fast-path budget")

        normalized_targets = self._normalize_verify_targets(verify_targets)
        await self._emit_progress(
            progress_callback,
            f"Verifying cached modules for PR-head {commit_hash[:8]} without compiling...",
        )
        await self._run_lake_no_build(
            build_workspace_path,
            commit_hash,
            targets=normalized_targets,
            timeout=self.config.pr_head_cache_verify_timeout,
        )

    def _normalize_verify_targets(self, verify_targets: Optional[Iterable[str]]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        limit = max(int(self.config.pr_head_cache_verify_target_limit), 1)
        for target in verify_targets or []:
            normalized_target = str(target or "").strip()
            if not normalized_target or normalized_target in seen:
                continue
            seen.add(normalized_target)
            normalized.append(normalized_target)
            if len(normalized) >= limit:
                break

        return normalized or ["Mathlib"]

    async def _run_lake_no_build(
        self,
        build_workspace_path: Path,
        commit_hash: str,
        *,
        targets: Iterable[str],
        timeout: Optional[float],
    ) -> None:
        normalized_targets = [str(target).strip() for target in targets if str(target).strip()]
        if not normalized_targets:
            normalized_targets = ["Mathlib"]

        stdout, stderr, returncode = await run_command(
            ["lake", "build", "--no-build", "-v", *normalized_targets],
            cwd=build_workspace_path,
            timeout=timeout,
            print_output=True,
            operation_name=f"lake build --no-build {commit_hash}",
            logger=self.logger,
        )

        if returncode == 0:
            return
        if returncode == -15:
            raise TimeoutError(
                f"[{commit_hash}] No-build verification timed out after {timeout}s for {', '.join(normalized_targets)}"
            )

        error_message = stderr or stdout or "unknown no-build verification failure"
        raise RuntimeError(f"[{commit_hash}] No-build verification failed: {error_message}")

    async def _get_cache_for_workspace(
        self,
        build_workspace_path: Path,
        commit_hash: str,
        *,
        cache_repo_full_name: Optional[str] = None,
        cache_args: Optional[Iterable[str]] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Get workspace cache"""
        max_retries = 3
        
        for attempt in range(max_retries):
            if attempt > 0:
                self.logger.debug(f"Retry cache get ({attempt + 1}/{max_retries})")
                await asyncio.sleep(10)
            
            try:
                # Use a stable per-repo namespace so remote-cache downloads can be
                # reused across repeated builds instead of being discarded each time.
                cache_base = self.config.get_cache_dir(self.repo_name)
                cache_namespace = self._cache_namespace(cache_repo_full_name, self.repo_name)
                cache_dir = cache_base / "xdg" / cache_namespace
                cache_dir.mkdir(parents=True, exist_ok=True)

                lock_path = cache_base / "locks" / f"{cache_namespace}.lock"
                command_timeout = timeout if timeout is not None else self.config.cache_operation_timeout
                self.logger.info(
                    "Waiting for shared Lean cache lock %s for %s",
                    cache_namespace,
                    commit_hash,
                )
                async with file_lock(lock_path, timeout=command_timeout):
                    removed_partial_count = await self._cleanup_partial_cache_files(cache_dir)
                    if removed_partial_count:
                        self.logger.info(
                            "Removed %s stale partial cache files from %s before cache fetch",
                            removed_partial_count,
                            cache_dir,
                        )

                    env = os.environ.copy()
                    env["XDG_CACHE_HOME"] = str(cache_dir)

                    cache_command = ["lake", "exe", "cache"]
                    if cache_repo_full_name:
                        cache_command.append(f"--repo={cache_repo_full_name}")
                    cache_command.append("get")
                    normalized_cache_args = [str(arg).strip() for arg in (cache_args or []) if str(arg).strip()]
                    cache_command.extend(normalized_cache_args)

                    stdout, stderr, return_code = await run_command(
                        cache_command,
                        cwd=build_workspace_path,
                        timeout=command_timeout,
                        env=env,
                        print_output=True,
                        logger=self.logger,
                        operation_name=f"lake cache get {commit_hash}"
                    )

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
