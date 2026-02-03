"""
File operation helpers - simplified version.
Uses straightforward synchronous locks instead of over-engineered async locks.
"""

import os
import json
import fcntl
import errno
import shutil
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union, List
from contextlib import contextmanager

import aiofiles
import aiofiles.os


# ==================== Async file locks (reader/writer mode) ====================

from contextlib import asynccontextmanager
import asyncio

def _sync_acquire_lock(file_path: Path, timeout: float, shared: bool, blocking: bool = True):
    """Synchronously acquire a file lock (internal helper).

    Returns:
        File descriptor.
    Raises:
        TimeoutError: Blocking mode timed out.
        BlockingIOError: Non-blocking mode encountered a held lock.
    """
    import time
    import random
    
    # Ensure the parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create an empty file if needed
    if not file_path.exists():
        file_path.touch()
    
    # Open the file
    flags = os.O_RDONLY if shared else (os.O_RDWR | os.O_CREAT)
    fd = os.open(file_path, flags, 0o644)
    
    # Choose the lock type
    lock_type = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
    
    if not blocking:
        # Non-blocking mode
        try:
            fcntl.flock(fd, lock_type | fcntl.LOCK_NB)
            return fd
        except OSError as e:
            os.close(fd)
            if e.errno in (errno.EAGAIN, errno.EACCES):
                raise BlockingIOError(f"Lock is already held: {file_path}")
            raise
    
    # Blocking mode with timeout retries and random backoff
    start_time = time.time()
    attempt = 0
    
    while True:
        try:
            fcntl.flock(fd, lock_type | fcntl.LOCK_NB)
            return fd
        except OSError as e:
            if e.errno in (errno.EAGAIN, errno.EACCES):
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    os.close(fd)
                    lock_name = "shared lock" if shared else "exclusive lock"
                    raise TimeoutError(f"Failed to acquire {lock_name} within {timeout}s: {file_path}")
                
                # Exponential backoff with random jitter to avoid thundering herd issues
                # base: 0.05s -> 0.1s -> 0.2s -> 0.4s -> 0.8s -> 1.6s -> 3.2s
                base_wait = min(0.05 * (2 ** attempt), 3.0)
                
                # Add ±50% jitter so processes do not retry in sync
                jitter = random.uniform(base_wait * 0.5, base_wait * 1.5)
                
                # Ensure we do not exceed the remaining time
                remaining = timeout - elapsed
                actual_wait = min(jitter, remaining)
                
                if actual_wait > 0:
                    time.sleep(actual_wait)
                
                attempt += 1
            else:
                os.close(fd)
                raise


def _sync_release_lock(fd: int):
    """Synchronously release the lock (internal helper)."""
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    except Exception:
        pass


@asynccontextmanager
async def file_lock(file_path: Path, timeout: float = 120.0, shared: bool = False):
    """Async file-lock context manager (automatically releases)."""
    fd = await asyncio.to_thread(_sync_acquire_lock, file_path, timeout, shared, blocking=True)
    try:
        yield
    finally:
        await asyncio.to_thread(_sync_release_lock, fd)


async def acquire_shared_lock(file_path: Path, timeout: float = 120.0) -> int:
    """Acquire a shared lock without auto release; caller or OS must release it.

    Use this when verification needs to keep a shared lock to prevent GC cleanup.

    Returns:
        File descriptor (released automatically when the process exits or via release_lock()).
    """
    return await asyncio.to_thread(_sync_acquire_lock, file_path, timeout, shared=True, blocking=True)


async def try_acquire_exclusive_lock(file_path: Path) -> Optional[int]:
    """Try to acquire an exclusive lock in non-blocking mode.

    Useful for GC to check whether a workspace is in use.

    Returns:
        File descriptor on success, None if another process holds the lock.
    """
    try:
        return await asyncio.to_thread(_sync_acquire_lock, file_path, 0, shared=False, blocking=False)
    except BlockingIOError:
        return None


async def release_lock(fd: int) -> None:
    """Release the lock and close the file descriptor."""
    await asyncio.to_thread(_sync_release_lock, fd)


# ==================== JSON file operations ====================

async def read_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Read a JSON file."""
    if not await aiofiles.os.path.exists(file_path):
        return None
    
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            if not content.strip():
                return None
            return json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        # JSON parse error; the file may be corrupted
        raise ValueError(f"Invalid JSON format: {file_path}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to read JSON file: {file_path}") from e


async def write_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Write JSON with atomic semantics to avoid read races.

    Even when invoked inside a file lock we still need atomic writes because:
    1. read_state performs unlocked reads.
    2. fcntl.flock does not block unlocked IO.
    3. Opening with 'w' truncates the file first, causing read races.
    """
    try:
        json_content = json.dumps(data, indent=2, ensure_ascii=False)
        await atomic_write(file_path, json_content, encoding='utf-8')
    except Exception as e:
        raise RuntimeError(f"Failed to write JSON file: {file_path}") from e


# ==================== Atomic file operations ====================

async def atomic_write(file_path: Path, content: Union[str, bytes], 
                      encoding: Optional[str] = 'utf-8') -> None:
    """Atomically write a file by using a temp file plus rename."""
    await aiofiles.os.makedirs(file_path.parent, exist_ok=True)
    
    # Create the temp file in the same directory
    import uuid
    temp_name = f".{file_path.name}.tmp.{uuid.uuid4().hex[:8]}"
    temp_path = file_path.parent / temp_name
    
    try:
        # Write to the temporary file
        if isinstance(content, str):
            if encoding is None:
                raise ValueError("Encoding must be provided for string content")
            async with aiofiles.open(temp_path, 'w', encoding=encoding) as f:
                await f.write(content)
        else:
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(content)
        
        # Atomic replacement via rename
        await aiofiles.os.replace(temp_path, file_path)
        
    except Exception as e:
        # Clean up the temporary file
        if await aiofiles.os.path.exists(temp_path):
            try:
                await aiofiles.os.unlink(temp_path)
            except Exception:
                pass
        raise RuntimeError(f"Atomic write failed: {file_path}") from e


# ==================== File system operations ====================

async def compute_file_hash(file_path: Path, algorithm: str = "sha256", file_type: str = None) -> str:
    """Compute a file hash."""
    import hashlib
    import asyncio
    
    if not await aiofiles.os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Detect file type
    if file_type is None:
        is_symlink = await aiofiles.os.path.islink(file_path)
    else:
        is_symlink = (file_type == "symlink")
    
    if is_symlink:
        # Symbolic link: hash the target path
        target = await aiofiles.os.readlink(file_path)
        hasher = hashlib.new(algorithm)
        hasher.update(target.encode('utf-8'))
        return hasher.hexdigest()
    else:
        # Regular file: compute hash in a thread pool
        def sync_hash():
            hasher = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                while chunk := f.read(65536):  # 64KB chunks
                    hasher.update(chunk)
            return hasher.hexdigest()
        
        return await asyncio.to_thread(sync_hash)


async def list_files_recursive(directory: Path) -> List[Tuple[Path, str]]:
    """List all files in a directory recursively."""
    import asyncio
    
    def sync_list():
        result = []
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                file_type = 'symlink' if file_path.is_symlink() else 'regular'
                result.append((file_path, file_type))
        return result
    
    return await asyncio.to_thread(sync_list)


async def safe_unlink(file_path: Path, max_retries: int = 3) -> None:
    """Safely delete a file while handling read-only attributes."""
    import asyncio
    import stat
    
    if not await aiofiles.os.path.exists(file_path):
        return
    
    def sync_unlink():
        """Delete synchronously while fixing read-only permissions."""
        if file_path.exists():
            try:
                os.unlink(str(file_path))
            except PermissionError:
                # Make the file writable if deletion failed due to read-only bits
                os.chmod(str(file_path), stat.S_IWRITE | stat.S_IREAD)
                os.unlink(str(file_path))
    
    for attempt in range(max_retries):
        try:
            await asyncio.to_thread(sync_unlink)
            return
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(0.1 * (attempt + 1))
            else:
                raise RuntimeError(f"Failed to delete file: {file_path}: {traceback.format_exc()}") from e


async def safe_remove_directory(directory: Path, max_retries: int = 3) -> None:
    """Safely remove a directory that may contain read-only entries.

    Strategy:
    1. Recursively add write permissions to the entire tree.
    2. Delete the directory.
    """
    import asyncio
    import stat
    
    if not await aiofiles.os.path.exists(directory):
        return
    
    def make_writable_and_remove():
        """Make the directory tree writable and then remove it."""
        if not directory.exists():
            return
        
        # Step 1: make every entry writable
        for root, dirs, files in os.walk(directory, topdown=False):
            # Ensure files are writable
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    os.chmod(file_path, stat.S_IWUSR | stat.S_IRUSR)
                except (OSError, PermissionError):
                    pass  # Ignore entries we cannot modify
            
            # Ensure directories are writable/executable
            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    os.chmod(dir_path, stat.S_IRWXU)
                except (OSError, PermissionError):
                    pass  # Ignore entries we cannot modify
            
            # Update the current directory
            try:
                os.chmod(root, stat.S_IRWXU)
            except (OSError, PermissionError):
                pass
        
        # Step 2: remove the tree
        shutil.rmtree(str(directory))
    
    # Retry loop
    for attempt in range(max_retries):
        try:
            await asyncio.to_thread(make_writable_and_remove)
            return
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
            else:
                raise RuntimeError(f"Failed to delete directory: {directory}: {traceback.format_exc()}") from e


async def copy_file_with_metadata(src: Path, dst: Path) -> None:
    """Copy a file while preserving metadata."""
    import asyncio
    
    await aiofiles.os.makedirs(dst.parent, exist_ok=True)
    
    def sync_copy():
        if src.is_symlink():
            # Handle symbolic links
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            dst.symlink_to(src.readlink())
        else:
            # Handle regular files
            shutil.copy2(str(src), str(dst))
    
    await asyncio.to_thread(sync_copy)


# ==================== Disk usage helpers ====================

async def get_disk_usage(path: Path) -> Dict[str, Any]:
    """Get disk usage statistics."""
    import asyncio
    
    def sync_disk_usage():
        check_path = path
        while not check_path.exists() and check_path != check_path.parent:
            check_path = check_path.parent
        
        total, used, free = shutil.disk_usage(check_path)
        usage_percent = (used / total) * 100 if total > 0 else 0
        return {
            'total': total,
            'used': used,
            'free': free,
            'usage_percent': usage_percent
        }
    
    return await asyncio.to_thread(sync_disk_usage)


async def check_disk_space_available(path: Path, threshold_percent: float = 90.0) -> bool:
    """Check whether enough disk space is available."""
    try:
        disk_info = await get_disk_usage(path)
        return disk_info['usage_percent'] < threshold_percent
    except Exception:
        # If the check failed, assume there is sufficient space
        return True


# ==================== Repository helper functions ====================

def normalize_repo_url(repo_url: str) -> str:
    """
    Extract a normalized repo name from a repository URL and use it as a directory name.

    Examples:
        >>> normalize_repo_url("https://github.com/leanprover-community/mathlib4")
        'mathlib4'
        >>> normalize_repo_url("https://github.com/leanprover/lean4-cli")
        'lean4-cli'
        >>> normalize_repo_url("git@github.com:user/repo.git")
        'repo'

    Args:
        repo_url: Repository URL or local path.

    Returns:
        Repository name suitable for directory naming.
    """
    from urllib.parse import urlparse

    if not repo_url:
        raise ValueError("repo_url cannot be empty")

    # Handle local paths
    if repo_url.startswith('/') or repo_url.startswith('.'):
        return Path(repo_url).name

    # Handle git@ style URLs
    if repo_url.startswith('git@'):
        # git@github.com:user/repo.git -> user/repo.git
        if ':' in repo_url:
            path_part = repo_url.split(':', 1)[1]
        else:
            path_part = repo_url
    else:
        # Handle standard URLs
        parsed = urlparse(repo_url)
        path_part = parsed.path

    # Remove leading slashes and a trailing .git
    path_part = path_part.strip('/')
    if path_part.endswith('.git'):
        path_part = path_part[:-4]

    # Use the final right-most segment as the repo name
    if '/' in path_part:
        repo_name = path_part.split('/')[-1]
    else:
        repo_name = path_part

    if not repo_name:
        raise ValueError(f"Cannot extract repo name from URL: {repo_url}")

    return repo_name
