#!/usr/bin/env python3
"""
Storage repair tool

System design:
1. Read all file mappings for all commit hashes from snapshot file
2. Identify corrupted files and their types (source files vs compiled files)
3. Repair strategy:
   - Source files: Download correct version from GitHub
   - Compiled files: Delete and recompile
4. Update affected snapshot

Usage:
    python -m ape.toolkits.execute.lean.utils.repair_storage --verification-report verification.json
"""

import os
import sys
import json
import asyncio
import argparse
import hashlib
import tempfile
import traceback
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

import aiofiles
import aiofiles.os
import git


def verify_single_commit_worker(commit_hash: str, config_dict: Dict) -> Dict:
    """Verify single repaired commit in independent process"""
    from ape.utils.logging import create_logger
    
    process_logger = create_logger()
    start_time = datetime.now()
    
    async def async_verify():
        """Asynchronous verification function"""
        from ape.toolkits.execute.lean.config import LeanVerifyToolConfig
        from ape.toolkits.execute.lean.core.restore_manager import RestoreManager
        from ape.utils.file_ops import safe_remove_directory
        
        config = LeanVerifyToolConfig.model_validate(config_dict)
        logger = create_logger()
        
        try:
            logger.info(f"Start verifying repaired workspace: {commit_hash}")
            
            # 1. Delete existing workspace to trigger a new restore
            workspace_path = config.workspace_dir / commit_hash
            if await aiofiles.os.path.exists(workspace_path):
                logger.info(f"Delete existing workspace: {commit_hash}")
                await safe_remove_directory(workspace_path)
                logger.info(f"Deleted workspace: {commit_hash}")
            
            # 2. Call restore (automatically restores from storage and verifies)
            logger.info(f"Start restore workspace (includes automatic verification): {commit_hash}")
            restore_manager = RestoreManager(config, logger)
            workspace_path = await restore_manager.get_workspace(commit_hash)
            
            logger.info(f"Verification successful: {commit_hash}, workspace path: {workspace_path}")
            return True
            
        except Exception as e:
            logger.error(f"Verification failed {commit_hash}: {e}")
            logger.debug(f"Verification exception details {commit_hash}: {traceback.format_exc()}")
            return False
    
    try:
        success = asyncio.run(async_verify())
        
        return {
            'commit_hash': commit_hash,
            'success': success,
            'execution_time': (datetime.now() - start_time).total_seconds(),
            'error_message': None if success else "Verification failed"
        }
    except Exception as e:
        process_logger.error(f"Verification exception {commit_hash}: {traceback.format_exc()}")
        return {
            'commit_hash': commit_hash,
            'success': False,
            'execution_time': (datetime.now() - start_time).total_seconds(),
            'error_message': str(e)
        }


class StorageRepairer:
    """Storage repair tool"""
    
    def __init__(self, storage_dir: Path, snapshot_dir: Path, mathlib_repo: Path, workers: int = 8):
        self.storage_dir = storage_dir
        self.snapshot_dir = snapshot_dir
        self.mathlib_repo = mathlib_repo
        self.workers = workers
        
        # Git repo
        if not self.mathlib_repo.exists():
            raise FileNotFoundError(f"Mathlib repository does not exist: {self.mathlib_repo}")
        self.git_repo = git.Repo(self.mathlib_repo)
        
        print(f"Storage directory: {self.storage_dir}")
        print(f"Snapshot directory: {self.snapshot_dir}")
        print(f"Mathlib repository: {self.mathlib_repo}")
        print(f"Concurrent number: {self.workers}")
    
    def is_source_file(self, relative_path: str) -> bool:
        """Check if it is a source file (can be obtained from Git)
        
        Rule: All files outside the .lake directory are source files
        """
        return not relative_path.startswith('.lake/')
    
    def is_build_file(self, relative_path: str) -> bool:
        """Check if it is a compiled file
        
        Rule: All files in the .lake directory are compiled files
        """
        return relative_path.startswith('.lake/')
    
    async def compute_file_hash(self, file_path: Path, file_type: str = "regular") -> str:
        """Compute file hash"""
        if file_type == "symlink":
            target = await aiofiles.os.readlink(file_path)
            hasher = hashlib.sha256()
            hasher.update(target.encode('utf-8'))
            return hasher.hexdigest()
        else:
            hasher = hashlib.sha256()
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
    
    async def load_snapshot(self, commit_hash: str) -> Optional[Dict[str, Dict[str, str]]]:
        """Load snapshot"""
        snapshot_path = self.snapshot_dir / f"{commit_hash}.snap"
        
        if not await aiofiles.os.path.exists(snapshot_path):
            return None
        
        import struct
        
        try:
            async with aiofiles.open(snapshot_path, 'rb') as f:
                data = await f.read()
            
            if len(data) < 4:
                return None
            
            file_mappings = {}
            offset = 0
            
            record_count = struct.unpack('!I', data[offset:offset+4])[0]
            offset += 4
            
            for i in range(record_count):
                if offset + 35 > len(data):
                    break
                
                path_len, hash_bin, file_type_code = struct.unpack('!H32sB', data[offset:offset+35])
                offset += 35
                
                if offset + path_len > len(data):
                    break
                
                path_data = data[offset:offset+path_len]
                offset += path_len
                
                rel_path = path_data.decode('utf-8')
                file_hash = hash_bin.hex()
                file_type = "symlink" if file_type_code == 1 else "regular"
                
                file_mappings[rel_path] = {
                    "hash": file_hash,
                    "type": file_type
                }
            
            return file_mappings
            
        except Exception as e:
            print(f"Load snapshot failed {commit_hash}: {e}")
            return None
    
    async def find_affected_commits(self, corrupted_hashes: Set[str]) -> Dict[str, List[str]]:
        """Find all commits that use corrupted files
        
        Returns:
            Dict[commit_hash -> List[relative_paths]]
        """
        print("\nScan all snapshots to find affected commits...")
        
        affected = {}
        snapshot_files = list(self.snapshot_dir.glob("*.snap"))
        
        for snapshot_file in snapshot_files:
            commit_hash = snapshot_file.stem
            file_mappings = await self.load_snapshot(commit_hash)
            
            if not file_mappings:
                continue
            
            corrupted_files = []
            for rel_path, file_info in file_mappings.items():
                if file_info["hash"] in corrupted_hashes:
                    corrupted_files.append(rel_path)
            
            if corrupted_files:
                affected[commit_hash] = corrupted_files
        
        print(f"Found {len(affected)} affected commits")
        return affected
    
    def _normalize_text_file(self, content: str) -> str:
        """Normalize text file content (simulate Git checkout behavior)
        
        Git normalizes text files when checking out/worktree, ensuring:
        1. The file ends with exactly one newline character
        2. This is different from the original output of git show
        """
        # Remove all trailing newlines
        content = content.rstrip('\n\r')
        # Add a standard Unix newline
        content = content + '\n'
        return content
    
    async def repair_source_file(self, commit_hash: str, relative_path: str, 
                                 expected_hash: str, file_type: str) -> bool:
        """Repair source file - get correct version from Git and normalize
        
        Returns:
            bool: Whether the repair is successful
        """
        from ....utils.file_ops import safe_unlink
        
        try:
            # 1. Check if the target object exists and is correct
            object_path = self._get_object_path(expected_hash)
            if await aiofiles.os.path.exists(object_path):
                # Verify the hash of the existing file
                existing_hash = await self.compute_file_hash(object_path, file_type)
                if existing_hash == expected_hash:
                    print(f"  File already exists and is correct: {relative_path}")
                    return True
                else:
                    # Existing file is corrupted, delete it (handle read-only permissions)
                    print(f"  Existing file is corrupted, delete and re-obtain: {relative_path}")
                    await safe_unlink(object_path)
            
            # 2. Handle symlink (special case)
            if file_type == "symlink":
                return await self._repair_symlink(commit_hash, relative_path, expected_hash)
            
            # 3. Get file content from Git (text mode)
            try:
                # Use git show to get file content
                file_content = self.git_repo.git.show(f"{commit_hash}:{relative_path}")
            except git.GitCommandError as e:
                print(f"  Git get failed {relative_path}: {e}")
                return False
            except UnicodeDecodeError:
                # If a decoding error occurs, it may be a binary file
                print(f"  Warning: {relative_path} may be a binary file (rare in Git repository)")
                return await self._repair_binary_file(commit_hash, relative_path, expected_hash)
            
            # 4. Normalize text content (critical step!)
            # Git worktree normalizes the newline characters at the end of the file, git show does not
            # We need to simulate the behavior of Git worktree
            file_content_normalized = self._normalize_text_file(file_content)
            
            # 5. Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(file_content_normalized)
                tmp_path = Path(tmp_file.name)
            
            try:
                # 6. Compute actual hash
                actual_hash = await self.compute_file_hash(tmp_path, file_type)
                
                # 7. Verify if the hash matches
                if actual_hash != expected_hash:
                    print(f"  Hash does not match {relative_path}:")
                    print(f"     Expected: {expected_hash}")
                    print(f"     Actual: {actual_hash}")
                    print(f"     Even after normalization, the file may have been modified")
                    return False
                
                # 8. Store to storage
                object_path = self._get_object_path(actual_hash)
                await aiofiles.os.makedirs(object_path.parent, exist_ok=True)
                
                # 9. Copy file
                async with aiofiles.open(tmp_path, 'rb') as src:
                    content = await src.read()
                async with aiofiles.open(object_path, 'wb') as dst:
                    await dst.write(content)
                
                # 10. Set readonly
                await asyncio.to_thread(os.chmod, str(object_path), 0o444)
                
                # 11. Final verification
                final_hash = await self.compute_file_hash(object_path, file_type)
                if final_hash != expected_hash:
                    print(f"  Verification failed after storage {relative_path}: hash does not match")
                    await safe_unlink(object_path)
                    return False
                
                print(f"  Repair source file: {relative_path} (hash: {expected_hash[:8]}...)")
                return True
                
            finally:
                # Clean up temporary file
                if await aiofiles.os.path.exists(tmp_path):
                    await aiofiles.os.unlink(tmp_path)
                
        except Exception as e:
            print(f"  Repair failed {relative_path}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _repair_symlink(self, commit_hash: str, relative_path: str, expected_hash: str) -> bool:
        """Repair symlink file"""
        try:
            # Get symlink target from Git
            target = self.git_repo.git.show(f"{commit_hash}:{relative_path}")
            
            # Create temporary file to store symlink target
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(target)
                tmp_path = Path(tmp_file.name)
            
            try:
                # Verify hash (the hash of symlink is the hash of the target path)
                actual_hash = await self.compute_file_hash(tmp_path, "symlink")
                
                if actual_hash != expected_hash:
                    print(f"  Symlink hash does not match {relative_path}")
                    return False
                
                # Store to storage (as a text file to store symlink target)
                object_path = self._get_object_path(actual_hash)
                await aiofiles.os.makedirs(object_path.parent, exist_ok=True)
                
                async with aiofiles.open(object_path, 'w', encoding='utf-8') as f:
                    await f.write(target)
                
                await asyncio.to_thread(os.chmod, str(object_path), 0o444)
                
                print(f"  Repair symlink: {relative_path} -> {target}")
                return True
                
            finally:
                if await aiofiles.os.path.exists(tmp_path):
                    await aiofiles.os.unlink(tmp_path)
                    
        except Exception as e:
            print(f"  Repair symlink failed {relative_path}: {e}")
            return False
    
    async def _repair_binary_file(self, commit_hash: str, relative_path: str, expected_hash: str) -> bool:
        """Repair binary file (rare case)"""
        try:
            print(f"  Use binary mode to process: {relative_path}")
            
            # Use binary mode to get file content
            file_content_bytes = self.git_repo.git.show(f"{commit_hash}:{relative_path}", binary=True)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp_file:
                tmp_file.write(file_content_bytes)
                tmp_path = Path(tmp_file.name)
            
            try:
                actual_hash = await self.compute_file_hash(tmp_path, "regular")
                
                if actual_hash != expected_hash:
                    print(f"  Binary file hash does not match {relative_path}")
                    return False
                
                object_path = self._get_object_path(actual_hash)
                await aiofiles.os.makedirs(object_path.parent, exist_ok=True)
                
                async with aiofiles.open(tmp_path, 'rb') as src:
                    content = await src.read()
                async with aiofiles.open(object_path, 'wb') as dst:
                    await dst.write(content)
                
                await asyncio.to_thread(os.chmod, str(object_path), 0o444)
                
                print(f"  Repair binary file: {relative_path}")
                return True
                
            finally:
                if await aiofiles.os.path.exists(tmp_path):
                    await aiofiles.os.unlink(tmp_path)
                    
        except Exception as e:
            print(f"  Repair binary file failed {relative_path}: {e}")
            return False
    
    def _get_object_path(self, content_hash: str) -> Path:
        """Get object path in storage"""
        level1 = content_hash[:2]
        level2 = content_hash[2:4]
        return self.storage_dir / level1 / level2 / content_hash
    
    async def verify_repaired_workspace(self, commit_hash: str) -> bool:
        """Verify a repaired workspace via restore plus built-in validation.

        Strategy:
        1. Delete the existing workspace and state.
        2. Call restore (loads from repaired storage).
        3. Restore automatically runs lake build verification (60-second timeout).
        4. Success indicates the repair worked.

        Returns:
            bool: True if verification succeeds.
        """
        from ..config import LeanVerifyToolConfig
        from ..core.restore_manager import RestoreManager
        from ....utils.file_ops import safe_remove_directory
        from ape.utils.logging import create_logger
        
        # Create logger (same as build.py)
        config = LeanVerifyToolConfig()
        logger = create_logger()
        
        try:
            logger.info(f"Start verifying repaired workspace: {commit_hash}")
            
            # 1. Delete existing workspace (trigger re-restore)
            # Note: Keep state files and snapshot, only delete workspace
            # This way restore will restore files from storage (including repaired source files)
            workspace_path = config.workspace_dir / commit_hash
            if await aiofiles.os.path.exists(workspace_path):
                logger.info(f"Delete existing workspace: {commit_hash}")
                await safe_remove_directory(workspace_path)
                logger.info(f"Deleted workspace: {commit_hash}")
            
            # 2. Call restore (will automatically restore files from storage and verify)
            logger.info(f"Start restore workspace (includes automatic verification): {commit_hash}")
            restore_manager = RestoreManager(config, logger)
            
            # Restore will:
            # - Restore files from storage (including repaired source files)
            # - Run lake build verification (60 seconds timeout)
            # - If verification fails, an exception will be thrown
            workspace_path = await restore_manager.get_workspace(commit_hash)
            
            logger.info(f"Verification successful: {commit_hash}, workspace path: {workspace_path}")
            print(f"Verification successful: {commit_hash[:8]}")
            return True
                
        except Exception as e:
            logger.error(f"Verification failed {commit_hash}: {e}")
            print(f"Verification failed {commit_hash[:8]}: {e}")
            import traceback
            logger.debug(f"Verification exception details {commit_hash}: {traceback.format_exc()}")
            return False
    
    
    async def repair_unique_source_files(self, unique_source_files: Dict[str, Dict]) -> Dict[str, bool]:
        """Repair all unique source files in parallel
        
        Args:
            unique_source_files: {hash -> {"commit": commit_hash, "path": relative_path, "type": file_type}}
        
        Returns:
            Dict[hash -> success]: Repair results
        """
        print(f"\nParallel repair {len(unique_source_files)} unique source files...")
        
        repair_results = {}
        semaphore = asyncio.Semaphore(self.workers)
        
        async def repair_one(file_hash: str, file_info: Dict) -> Tuple[str, bool]:
            async with semaphore:
                success = await self.repair_source_file(
                    file_info["commit"],
                    file_info["path"],
                    file_hash,
                    file_info["type"]
                )
                return (file_hash, success)
        
        tasks = [
            repair_one(file_hash, file_info)
            for file_hash, file_info in unique_source_files.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, tuple):
                file_hash, success = result
                repair_results[file_hash] = success
            else:
                print(f"  Repair exception: {result}")
        
        success_count = sum(1 for success in repair_results.values() if success)
        print(f"Source file repair completed: {success_count}/{len(unique_source_files)} successful")
        
        return repair_results
    
    async def repair_from_verification_report(self, report_path: Path) -> None:
        """Repair storage from verification report - optimized version"""
        print(f"\nRead verification report: {report_path}")
        
        # Read report
        async with aiofiles.open(report_path, 'r', encoding='utf-8') as f:
            report_content = await f.read()
            report = json.loads(report_content)
        
        corrupted_files = report.get("corrupted_files", [])
        
        if not corrupted_files:
            print("No corrupted files to repair")
            return
        
        print(f"Found {len(corrupted_files)} corrupted files")
        
        # Collect all corrupted hashes
        corrupted_hashes = {file_info["expected_hash"] for file_info in corrupted_files}
        
        # Find affected commits
        affected_commits = await self.find_affected_commits(corrupted_hashes)
        
        if not affected_commits:
            print("No affected commits found")
            return
        
        print(f"\n{'='*70}")
        print("Analyze corrupted file types")
        print(f"{'='*70}")
        
        # Step 1: Analyze all affected files, classify by type
        unique_source_files = {}  # {hash -> {"commit": commit, "path": path, "type": type}}
        commits_need_rebuild = set()  # Commits that need to be rebuilt
        commit_file_types = {}  # {commit -> {"source": [...], "build": [...]}}
        
        for commit_hash, corrupted_files_list in affected_commits.items():
            # Load snapshot
            file_mappings = await self.load_snapshot(commit_hash)
            if not file_mappings:
                print(f"Cannot load snapshot: {commit_hash}")
                continue
            
            source_files = []
            build_files = []
            
            for rel_path in corrupted_files_list:
                if rel_path not in file_mappings:
                    continue
                
                file_info = file_mappings[rel_path]
                file_hash = file_info["hash"]
                
                if self.is_source_file(rel_path):
                    source_files.append(rel_path)
                    # Record unique source files (deduplication)
                    if file_hash not in unique_source_files:
                        unique_source_files[file_hash] = {
                            "commit": commit_hash,
                            "path": rel_path,
                            "type": file_info["type"]
                        }
                elif self.is_build_file(rel_path):
                    build_files.append(rel_path)
                    # Compiled files are corrupted, need to rebuild
                    commits_need_rebuild.add(commit_hash)
            
            commit_file_types[commit_hash] = {
                "source": source_files,
                "build": build_files
            }
            
            print(f"  {commit_hash[:8]}: Source files {len(source_files)}, compiled files {len(build_files)}")
        
        print(f"\nStatistics:")
        print(f"  Unique source files: {len(unique_source_files)}")
        print(f"  Commits need to be rebuilt: {len(commits_need_rebuild)}")
        
        # Step 2: Parallel repair all unique source files
        repair_results = {}
        if unique_source_files:
            repair_results = await self.repair_unique_source_files(unique_source_files)
            
            # If any source file is repaired, need to rebuild!
            # Because source file changed → compiled product needs to be regenerated
            for commit_hash, file_types in commit_file_types.items():
                if file_types["source"]:
                    # Source file is corrupted, need to rebuild regardless of success or failure
                    commits_need_rebuild.add(commit_hash)
                    
                    # If source file repair fails, record log
                    file_mappings = await self.load_snapshot(commit_hash)
                    for rel_path in file_types["source"]:
                        if rel_path in file_mappings:
                            file_hash = file_mappings[rel_path]["hash"]
                            if not repair_results.get(file_hash, False):
                                print(f"  {commit_hash[:8]}: Source file {rel_path} repair failed, will try to rebuild")
        
        # Step 3: Multi-process parallel verification of repaired commits
        from ....utils.file_ops import safe_unlink
        from ..config import LeanVerifyToolConfig
        
        verify_success = 0
        verify_failed = 0
        
        if commits_need_rebuild:
            print(f"\n{'='*70}")
            print(f"Multi-process parallel verification of {len(commits_need_rebuild)} repaired commits")
            print(f"{'='*70}")
            
            # First clean up corrupted compiled files (sequential execution, fast)
            for commit_hash in sorted(commits_need_rebuild):
                file_types = commit_file_types.get(commit_hash, {})
                if file_types.get("build"):
                    file_mappings = await self.load_snapshot(commit_hash)
                    for rel_path in file_types.get("build", []):
                        if rel_path in file_mappings:
                            file_hash = file_mappings[rel_path]["hash"]
                            object_path = self._get_object_path(file_hash)
                            if await aiofiles.os.path.exists(object_path):
                                await safe_unlink(object_path)
                            print(f"  Delete corrupted compiled file: {rel_path} (commit: {commit_hash[:8]})")
            
            # Prepare config dictionary (for inter-process transfer)
            config = LeanVerifyToolConfig()
            config_dict = config.model_dump()
            
            # Multi-process parallel verification
            print(f"\nStart multi-process verification (number of processes: {self.workers})...")
            
            # Display commits to be verified
            for commit_hash in sorted(commits_need_rebuild):
                file_types = commit_file_types.get(commit_hash, {})
                print(f"  • {commit_hash[:8]}: Source files {len(file_types.get('source', []))}, compiled files {len(file_types.get('build', []))}")
            
            # Use ProcessPoolExecutor to execute multi-process verification
            with ProcessPoolExecutor(max_workers=self.workers) as executor:
                # Submit all tasks
                future_to_commit = {
                    executor.submit(verify_single_commit_worker, commit_hash, config_dict): commit_hash
                    for commit_hash in sorted(commits_need_rebuild)
                }
                
                # Wait for completion and collect results
                for future in as_completed(future_to_commit):
                    commit_hash = future_to_commit[future]
                    try:
                        result = future.result()
                        if result['success']:
                            print(f"Verification successful: {commit_hash[:8]}")
                            verify_success += 1
                        else:
                            print(f"Verification failed: {commit_hash[:8]}")
                            verify_failed += 1
                    except Exception as e:
                        print(f"Verification exception {commit_hash[:8]}: {e}")
                        verify_failed += 1
        
        # Output summary
        total_source_repaired = sum(1 for success in repair_results.values() if success)
        total_source_failed = len(repair_results) - total_source_repaired
        
        print(f"\n{'='*70}")
        print("Repair summary")
        print(f"{'='*70}")
        print(f"Affected commits:        {len(affected_commits)}")
        print(f"Unique source files repaired successfully:      {total_source_repaired}/{len(unique_source_files)}")
        print(f"Unique source files repaired failed:      {total_source_failed}/{len(unique_source_files)}")
        print(f"Commits to be verified:       {len(commits_need_rebuild)}")
        print(f"Commits verified successfully:       {verify_success}")
        print(f"Commits verified failed:       {verify_failed}")
        print(f"{'='*70}")
        
        if total_source_failed == 0 and verify_failed == 0:
            print("\nAll files repaired and verified successfully!")
        else:
            print(f"\nThere are problems: source file failed {total_source_failed}, verification failed {verify_failed}")


async def async_main(args):
    """Asynchronous main function"""
    # Load configuration
    from ..config import LeanVerifyToolConfig
    config = LeanVerifyToolConfig()
    
    storage_dir = Path(args.storage_dir) if args.storage_dir else config.storage_dir
    snapshot_dir = Path(args.snapshot_dir) if args.snapshot_dir else config.snapshot_dir
    mathlib_repo = Path(args.mathlib_repo) if args.mathlib_repo else config.mathlib_repo
    
    # Create repair tool
    repairer = StorageRepairer(
        storage_dir=storage_dir,
        snapshot_dir=snapshot_dir,
        mathlib_repo=mathlib_repo,
        workers=args.workers
    )
    
    # Execute repair
    report_path = Path(args.verification_report)
    if not report_path.exists():
        print(f"Verification report not found: {report_path}")
        sys.exit(1)
    
    await repairer.repair_from_verification_report(report_path)


def main():
    parser = argparse.ArgumentParser(
        description="Repair corrupted files in content-addressed storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Repair strategy:
  1. Source files (.lean, .toml, etc.): Download from GitHub corresponding commit
  2. Compiled files (.olean, etc.): Delete and recompile the entire workspace
  3. Automatically update affected snapshot

Examples:
# Repair using verification report
  python repair_storage.py --verification-report temp/storage_verification_20241010.json
  
# Specify custom directory
  python repair_storage.py \\
    --verification-report report.json \\
    --storage-dir /path/to/storage \\
    --snapshot-dir /path/to/snapshots \\
    --mathlib-repo /path/to/mathlib4
        """
    )
    
    parser.add_argument(
        '--verification_report',
        type=str,
        required=True,
        help='Verification report file path (generated by verify_storage.py)'
    )

    parser.add_argument(
        '--storage_dir',
        type=str,
        default=None,
        help='Storage directory path (default: read from config)'
    )

    parser.add_argument(
        '--snapshot_dir',
        type=str,
        default=None,
        help='Snapshot directory path (default: read from config)'
    )

    parser.add_argument(
        '--mathlib_repo',
        type=str,
        default=None,
        help='Mathlib repository path (default: read from config)'
    )
    
    parser.add_argument(
        '--workers',
        type=str,
        default='auto',
        help='Concurrent number of processes ("auto" uses CPU core number, default: auto)'
    )
    
    args = parser.parse_args()
    
    # Determine concurrent number of processes
    if args.workers == 'auto':
        workers = cpu_count()
    else:
        try:
            workers = int(args.workers)
            if workers <= 0:
                print(f"Error: number of processes must be greater than 0")
                sys.exit(1)
        except ValueError:
            print(f"Error: invalid number of processes: {args.workers}")
            sys.exit(1)
    
    # Update args
    args.workers = workers
    
    # Run asynchronous main function
    asyncio.run(async_main(args))


if __name__ == '__main__':
    main()
