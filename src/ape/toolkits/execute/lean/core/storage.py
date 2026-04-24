"""
Simplified content-addressable storage - optimized version
"""

import os
import asyncio
import uuid
import random
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING, List, Tuple
from datetime import datetime

import aiofiles
import aiofiles.os
from ..config import LeanVerifyToolConfig
from .blob_store import BlobStore, create_blob_store
from ape.utils.file_ops import copy_file_with_metadata, atomic_write
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging

class ContentStore:
    """Simplified content-addressable storage manager"""
    
    def __init__(
        self,
        config: Optional[LeanVerifyToolConfig] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        blob_store: Optional[BlobStore] = None,
    ):
        """Initialize content storage"""
        self.config = config or LeanVerifyToolConfig()
        self.logger = logger or create_logger()
        
        self.storage_dir = self.config.storage_dir
        self.blob_store = blob_store or create_blob_store(self.config, self.logger)
        # Note: Do not create directory during initialization, create asynchronously when needed
        
        self.logger.info(f"Content storage initialized: {self.storage_dir}")
    
    def _get_object_path(self, content_hash: str) -> Path:
        """Get storage path for content hash - two-level directory structure"""
        if len(content_hash) < 4:
            raise ValueError(f"Invalid hash length: {content_hash}")
        
        level1 = content_hash[:2]
        level2 = content_hash[2:4]
        object_dir = self.storage_dir / level1 / level2
        
        return object_dir / content_hash

    def _blob_key(self, content_hash: str) -> str:
        """Build the remote blob-store key for a CAS object."""
        return f"storage/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}"

    async def _mirror_object_if_configured(self, content_hash: str, object_path: Path) -> None:
        """Best-effort upload of a local CAS object to the configured blob store."""
        if not self.blob_store.enabled:
            return

        try:
            await self.blob_store.upload_file_if_missing(
                object_path,
                self._blob_key(content_hash),
            )
        except Exception as exc:
            self.logger.warning(
                "Failed to mirror content object %s to the remote blob store: %s",
                content_hash[:12],
                exc,
            )

    async def _ensure_object_available_locally(self, content_hash: str) -> bool:
        """Return True when the requested object exists locally, hydrating it remotely if needed."""
        object_path = self._get_object_path(content_hash)
        if await aiofiles.os.path.exists(object_path):
            return True

        if not self.blob_store.enabled:
            return False

        try:
            restored = await self.blob_store.download_file_if_present(
                self._blob_key(content_hash),
                object_path,
                readonly_mode=0o444,
            )
        except Exception as exc:
            self.logger.warning(
                "Failed to restore content object %s from the remote blob store: %s",
                content_hash[:12],
                exc,
            )
            return False

        return restored or await aiofiles.os.path.exists(object_path)

    async def _hydrate_missing_objects_from_blob_store(
        self,
        content_hashes: List[str],
        *,
        max_workers: int,
    ) -> None:
        """Best-effort download of missing CAS objects from the remote blob store."""
        if not self.blob_store.enabled:
            return

        unique_hashes: list[str] = []
        seen_hashes: set[str] = set()
        for content_hash in content_hashes:
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)
            object_path = self._get_object_path(content_hash)
            if await aiofiles.os.path.exists(object_path):
                continue
            unique_hashes.append(content_hash)

        if not unique_hashes:
            return

        semaphore = asyncio.Semaphore(max(1, min(max_workers, 16)))

        async def hydrate_one(content_hash: str) -> None:
            async with semaphore:
                await self._ensure_object_available_locally(content_hash)

        await asyncio.gather(*(hydrate_one(content_hash) for content_hash in unique_hashes))
    
    async def store_file(self, file_path: Path, file_type: str = "regular") -> str:
        """Asynchronously store file to content storage
        
        Args:
            file_path: File path
            file_type: File type ('regular' or 'symlink')
            
        Returns:
            str: Content hash
        """
        if not await aiofiles.os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Compute content hash
        from ape.utils.file_ops import compute_file_hash
        content_hash = await compute_file_hash(file_path, file_type=file_type)
        object_path = self._get_object_path(content_hash)
        
        # If object exists, return directly
        if await aiofiles.os.path.exists(object_path):
            await self._mirror_object_if_configured(content_hash, object_path)
            return content_hash
        
        # Store file
        await aiofiles.os.makedirs(object_path.parent, exist_ok=True)
        
        if file_type == "symlink":
            # Store symlink target
            target = await aiofiles.os.readlink(file_path)
            await atomic_write(object_path, target, encoding='utf-8')
            # Set symlink content file to readonly
            await asyncio.to_thread(os.chmod, str(object_path), 0o444)
        else:
            # Copy regular file
            temp_path = object_path.parent / f".{object_path.name}.{uuid.uuid4().hex}.tmp"
            await copy_file_with_metadata(file_path, temp_path)
            
            # Atomic replacement
            try:
                await aiofiles.os.replace(temp_path, object_path)
                # Set all files to readonly
                await asyncio.to_thread(os.chmod, str(object_path), 0o444)
            except FileExistsError:
                # In concurrent case, already created, clean temporary file
                if await aiofiles.os.path.exists(temp_path):
                    await aiofiles.os.unlink(temp_path)
        
        await self._mirror_object_if_configured(content_hash, object_path)
        return content_hash
    
    async def retrieve_file(self, content_hash: str, output_path: Path, file_type: str = "regular") -> None:
        """Asynchronously retrieve file from storage
        
        Args:
            content_hash: Content hash
            output_path: Output path
            file_type: File type
        """
        object_path = self._get_object_path(content_hash)
        
        if not await self._ensure_object_available_locally(content_hash):
            raise FileNotFoundError(f"Object not found: {content_hash}")
        
        # Delete existing file (if exists)
        try:
            await aiofiles.os.unlink(output_path)
        except FileNotFoundError:
            pass
        
        if file_type == "symlink":
            # Restore symlink
            async with aiofiles.open(object_path, 'r', encoding='utf-8') as f:
                target = (await f.read()).strip()
            await aiofiles.os.symlink(target, output_path)
        else:
            # Try hard link first, if failed, use file copy
            try:
                await asyncio.to_thread(os.link, str(object_path), str(output_path))
            except (OSError, PermissionError):
                # Hard link failed, use file copy
                self.logger.info('Hard link failed, use file copy')
                await copy_file_with_metadata(object_path, output_path)
    
    async def batch_retrieve_files(self, file_mappings: Dict[str, Dict[str, str]], 
                                  workspace_path: Path, max_workers: int = 64) -> None:
        """High-performance batch file recovery
        
        Args:
            file_mappings: File mapping {relative path: {"hash": hash, "type": type}}
            workspace_path: Workspace path
            max_workers: Maximum number of concurrent workers
        """
        start_time = datetime.now()
        self.logger.info(f"Start batch recovery {len(file_mappings)} files")
        
        # 1. Verify all objects exist
        file_items = list(file_mappings.items())
        random.shuffle(file_items)
        
        semaphore = asyncio.Semaphore(max_workers)
        
        async def check_object_exists(relative_path: str, file_info: Dict[str, str]) -> tuple:
            async with semaphore:
                object_path = self._get_object_path(file_info["hash"])
                exists = await aiofiles.os.path.exists(object_path)
                return (relative_path, file_info, object_path, exists)
        
        check_tasks = [
            check_object_exists(relative_path, file_info)
            for relative_path, file_info in file_items
        ]
        
        check_results = await asyncio.gather(*check_tasks)
        
        # Separate missing objects and restore tasks
        missing_objects = []
        restore_tasks = []
        
        for relative_path, file_info, object_path, exists in check_results:
            if not exists:
                missing_objects.append((relative_path, file_info["hash"]))
            else:
                file_path = workspace_path / relative_path
                restore_tasks.append((relative_path, file_info, file_path, object_path))

        if missing_objects and self.blob_store.enabled:
            await self._hydrate_missing_objects_from_blob_store(
                [content_hash for _, content_hash in missing_objects],
                max_workers=max_workers,
            )

            missing_objects = []
            restore_tasks = []
            for relative_path, file_info in file_items:
                object_path = self._get_object_path(file_info["hash"])
                if not await aiofiles.os.path.exists(object_path):
                    missing_objects.append((relative_path, file_info["hash"]))
                    continue
                file_path = workspace_path / relative_path
                restore_tasks.append((relative_path, file_info, file_path, object_path))
        
        if missing_objects:
            missing_files = [f"{path} (hash: {hash_val})" for path, hash_val in missing_objects[:5]]
            if len(missing_objects) > 5:
                missing_files.append(f"... and {len(missing_objects) - 5} other files")
            error_msg = f"Missing {len(missing_objects)} storage objects:\n" + "\n".join(missing_files)
            raise RuntimeError(error_msg)
        
        # 2. Concurrent create directory structure
        directories = set()
        for relative_path, _, _, _ in restore_tasks:
            file_path = workspace_path / relative_path
            directories.add(file_path.parent)
        
        async def create_directory(directory: Path) -> None:
            async with semaphore:
                await aiofiles.os.makedirs(directory, exist_ok=True)
        
        dir_tasks = [create_directory(directory) for directory in directories]
        await asyncio.gather(*dir_tasks)
        
        # 3. Concurrent restore all files
        total_files = len(restore_tasks)
        completed_count = 0
        failed_count = 0
        last_report_time = start_time
        
        async def restore_single_file(relative_path: str, file_info: Dict[str, str], 
                                     file_path: Path, object_path: Path) -> bool:
            """Restore single file"""
            async with semaphore:
                try:
                    file_type = file_info["type"]
                    
                    # Delete existing file (if exists)
                    try:
                        await aiofiles.os.unlink(file_path)
                    except FileNotFoundError:
                        pass
                    
                    if file_type == "symlink":
                        # Symlink handling
                        async with aiofiles.open(object_path, 'r', encoding='utf-8') as f:
                            target = (await f.read()).strip()
                        await aiofiles.os.symlink(target, file_path)
                    else:
                        # Hard link (if failed, use file copy)
                        try:
                            await asyncio.to_thread(os.link, str(object_path), str(file_path))
                        except (OSError, PermissionError):
                            await copy_file_with_metadata(object_path, file_path)
                    
                    return True
                except Exception as e:
                    self.logger.error(f"Restore file failed {relative_path}: {e}")
                    return False
        
        # Create all restore tasks
        file_restore_tasks = [
            restore_single_file(relative_path, file_info, file_path, object_path)
            for relative_path, file_info, file_path, object_path in restore_tasks
        ]
        
        # Use as_completed to monitor progress
        for coro in asyncio.as_completed(file_restore_tasks):
            try:
                success = await coro
                if success:
                    completed_count += 1
                else:
                    failed_count += 1
                    completed_count += 1
            except Exception as e:
                self.logger.error(f"File restore exception: {e}")
                failed_count += 1
                completed_count += 1
            
            # Print progress every 10 seconds
            current_time = datetime.now()
            if (current_time - last_report_time).total_seconds() >= 10:
                progress = completed_count / total_files
                total_elapsed = (current_time - start_time).total_seconds()
                
                # Calculate ETA
                if completed_count > 0:
                    avg_time_per_file = total_elapsed / completed_count
                    remaining_files = total_files - completed_count
                    eta_seconds = avg_time_per_file * remaining_files
                    eta_minutes = int(eta_seconds // 60)
                    eta_secs = int(eta_seconds % 60)
                    eta_str = f"{eta_minutes}m{eta_secs}s" if eta_minutes > 0 else f"{eta_secs}s"
                else:
                    eta_str = "Calculating..."
                
                files_per_sec = completed_count / total_elapsed if total_elapsed > 0 else 0
                
                self.logger.info(
                    f"Restore progress: {completed_count}/{total_files} ({progress*100:.1f}%) | "
                    f"Failed: {failed_count} | Speed: {files_per_sec:.0f} files/second | "
                    f"Elapsed time: {int(total_elapsed)}s | ETA: {eta_str}"
                )
                last_report_time = current_time
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        if failed_count > 0:
            raise RuntimeError(f"Batch restore partially failed: Success {completed_count - failed_count}/{total_files}, Failed {failed_count}, Time {elapsed_time:.2f}s")
        
        files_per_sec = total_files / elapsed_time if elapsed_time > 0 else 0
        self.logger.info(f"Batch restore completed: Successfully restored {completed_count} files, Time {elapsed_time:.2f}s, Speed: {files_per_sec:.0f} files/second")
