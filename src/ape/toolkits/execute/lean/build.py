"""
Batch build system - simplified builder based on new architecture
"""

import os
import sys
import asyncio
import argparse
import traceback
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from datetime import datetime
import pandas as pd
import json
from ape.utils.logging import create_logger
import aiofiles
from ape.utils.file_ops import safe_remove_directory

if TYPE_CHECKING:
    import logging

from .config import LeanVerifyToolConfig
from .utils.process_ops import run_command

os.environ["LD_LIBRARY_PATH"] = ""
os.environ["LD_PRELOAD"] = ""

def parse_repo_spec(spec: str) -> Tuple[str, str]:
    """Parse repo_url@@commit_hash"""
    parts = spec.split("@@")
    repo_url = parts[0]
    commit_hash = parts[1]
    return repo_url, commit_hash


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def build_single_commit_worker(entry: Dict[str, Any], config_dict: Dict[str, Any], shared_stats: Dict[str, Any], stats_lock, log_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Execute a single build task in an independent process"""
    
    # Create process-level logger
    from ape.utils.logging import create_logger
    from datetime import datetime

    # Subprocess logger: write to file, not console (keeps output ordered)
    if log_dir:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        commit_hash = entry.get('commit_hash', 'unknown')[:8]
        log_file = log_dir / f"build_{commit_hash}_{timestamp}.log"
        process_logger = create_logger(log_file=log_file, to_console=False)
    else:
        process_logger = create_logger()
    
    config = LeanVerifyToolConfig.model_validate(config_dict)

    async def async_build():
        # Recreate manager in worker process
        from .core.build_manager import BuildManager
        
        commit_hash = entry.get("commit_hash")
        if not commit_hash:
            raise ValueError("Missing commit_hash in build entry")
        repo_name, repo_url = config.resolve_repo(entry.get("repo_url"))
        entry["repo_name"] = repo_name
        entry["repo_url"] = repo_url

        build_manager = BuildManager(
            config,
            process_logger,
            repo_url=repo_url
        )

        fetch_repo_url = entry.get("fetch_repo_url")
        fetch_ref = entry.get("fetch_ref")
        cache_repo_full_name = entry.get("cache_repo_full_name")
        if fetch_repo_url or fetch_ref:
            return await build_manager.build_workspace_from_ref(
                commit_hash,
                fetch_repo_url=fetch_repo_url,
                fetch_ref=fetch_ref,
                cache_repo_full_name=cache_repo_full_name,
            )

        return await build_manager.build_workspace(commit_hash)
    
    # Execute asynchronous build
    start_time = datetime.now()
    try:
        result = asyncio.run(async_build())
        commit_hash = entry.get("commit_hash")
        repo_name = entry.get("repo_name") or config.default_repo_name
        repo_url = entry.get("repo_url") or config.default_repo_url
        
        # Update shared statistics
        with stats_lock:
            shared_stats['completed'] = shared_stats.get('completed', 0) + 1
            if result.success:
                shared_stats['successful'] = shared_stats.get('successful', 0) + 1
            else:
                shared_stats['failed'] = shared_stats.get('failed', 0) + 1
        
        return {
            'task_id': commit_hash,
            'success': result.success,
            'execution_time': (datetime.now() - start_time).total_seconds(),
            'commit_hash': commit_hash,
            'repo_name': repo_name,
            'repo_url': repo_url,
            'build_duration': result.build_duration,
            'file_count': result.file_count,
            'error_message': result.error_message
        }
        
    except Exception as e:
        # Update failed statistics
        with stats_lock:
            shared_stats['completed'] = shared_stats.get('completed', 0) + 1
            shared_stats['failed'] = shared_stats.get('failed', 0) + 1
        
        commit_hash = entry.get("commit_hash")
        repo_name = entry.get("repo_name")
        repo_url = entry.get("repo_url")
        if not repo_name or not repo_url:
            repo_name, repo_url = config.resolve_repo(entry.get("repo_url"))
        process_logger.error(f"Build failed for {repo_name}@{commit_hash}: {traceback.format_exc()}")
        return {
            'task_id': commit_hash,
            'success': False,
            'execution_time': (datetime.now() - start_time).total_seconds(),
            'commit_hash': commit_hash,
            'repo_name': repo_name,
            'repo_url': repo_url,
            'error_message': traceback.format_exc()
        }

class BatchBuilder:
    """Simplified batch builder - based on new architecture"""
    
    def __init__(self, config: LeanVerifyToolConfig, logger: Optional['logging.LoggerAdapter'] = None):
        """Initialize batch builder"""
        self.config = config
        self.logger = logger or create_logger()
        self.logger.info("Batch builder initialized")
    
    def _get_log_dir_for_subprocess(self) -> Optional[Path]:
        """Get log_dir parameter for subprocess"""
        actual_logger = self.logger.logger
        log_file = getattr(actual_logger, "_ape_logger_log_file", None)
        if log_file:
            return Path(log_file).parent
        return None
    
    async def _install_toolchains(self, toolchain_list: List[str]) -> bool:
        """Install required Lean toolchains"""
        if not toolchain_list:
            self.logger.info("No toolchains need to be installed")
            return True
        
        # Remove duplicate toolchains
        to_install = set(t.strip() for t in toolchain_list if t.strip() and t.strip().lower() != 'none')
        
        if not to_install:
            self.logger.info("No valid toolchains need to be installed")
            return True
        
        self.logger.info(f"Installing {len(to_install)} toolchains...")
        
        success_count = 0
        semaphore = asyncio.Semaphore(self.config.max_concurrent_installs)
        
        async def install_one_toolchain(toolchain: str) -> bool:
            async with semaphore:
                max_retries = self.config.max_retries
                for attempt in range(max_retries):
                    try:
                        self.logger.info(f"Installing toolchain: {toolchain} (attempt {attempt + 1})")
                        
                        stdout, stderr, returncode = await run_command(
                            ["elan", "toolchain", "install", toolchain],
                            timeout=self.config.toolchain_install_timeout,
                            print_output=True,
                            logger=self.logger
                        )
                        
                        if returncode == 0 or 'is already installed' in stderr:
                            self.logger.info(f"Successfully installed toolchain: {toolchain}")
                            return True
                        elif returncode == -15:
                            self.logger.warning(f"Toolchain {toolchain} timeout")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(self.config.retry_base_delay * (attempt + 1))
                        else:
                            self.logger.warning(f"Failed to install toolchain {toolchain}: {stderr}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(self.config.retry_base_delay * (attempt + 1))
                            
                    except Exception as e:
                        self.logger.error(f"Exception installing toolchain {toolchain}: {e}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(self.config.retry_base_delay * (attempt + 1))
                
                return False
        
        # Concurrent installation of all toolchains
        tasks = [install_one_toolchain(toolchain) for toolchain in to_install]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate success count
        for result in results:
            if result is True:
                success_count += 1
            elif isinstance(result, Exception):
                self.logger.error(f"Toolchain installation exception: {result}")
        
        self.logger.info(f"Toolchain installation completed: {success_count}/{len(to_install)} successful")
        return success_count == len(to_install)
    
    async def _ensure_repositories_cloned(self, repo_list: List[Dict[str, str]]) -> bool:
        """Ensure all required Git repositories are cloned"""
        if not repo_list:
            self.logger.info("No repositories need to be cloned")
            return True
        
        # Remove duplicate repositories
        unique_repos = {}
        for repo_info in repo_list:
            repo_name = repo_info['repo_name']
            if repo_name not in unique_repos:
                unique_repos[repo_name] = repo_info['repo_url']
        
        if not unique_repos:
            self.logger.info("No valid repositories need to be cloned")
            return True
        
        self.logger.info(f"Checking {len(unique_repos)} repositories...")
        
        async def ensure_one_repo(repo_name: str, repo_url: str) -> bool:
            """Ensure single repository is cloned"""
            repo_path = self.config.get_repo_path(repo_name)
            
            # If repository exists, return success
            if await aiofiles.os.path.exists(repo_path):
                self.logger.info(f"Repository exists: {repo_name}")
                return True
            
            max_retries = self.config.max_retries
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"Cloning repository: {repo_name} from {repo_url} (attempt {attempt + 1})")
                    
                    import git
                    await aiofiles.os.makedirs(repo_path.parent, exist_ok=True)
                    
                    # Execute clone in thread
                    await asyncio.to_thread(
                        git.Repo.clone_from,
                        repo_url,
                        str(repo_path)
                    )
                    
                    self.logger.info(f"Successfully cloned repository: {repo_name}")
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Failed to clone repository {repo_name} (attempt {attempt + 1}): {e}")
                    
                    if await aiofiles.os.path.exists(repo_path):
                        try:
                            await safe_remove_directory(repo_path)
                        except Exception:
                            pass
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(self.config.retry_base_delay * (attempt + 1))
            
            return False
        
        # Concurrent cloning of all repositories
        tasks = [ensure_one_repo(repo_name, repo_url) for repo_name, repo_url in unique_repos.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate success count
        success_count = 0
        for result in results:
            if result is True:
                success_count += 1
            elif isinstance(result, Exception):
                self.logger.error(f"Repository cloning exception: {result}")
        
        self.logger.info(f"Repository check completed: {success_count}/{len(unique_repos)} ready")
        return success_count == len(unique_repos)
    
    def _load_entries_from_file(
        self,
        file_path: Path,
        commit_id_key: str = 'commit_hash',
        use_pr_head_refs: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Load commit information (including repository metadata) and toolchains from input file"""
        
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        if file_path.suffix.lower() == '.jsonl':
            return self._load_from_jsonl(file_path, commit_id_key, use_pr_head_refs)
        elif file_path.suffix.lower() == '.parquet':
            return self._load_from_parquet(file_path, commit_id_key, use_pr_head_refs)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def _load_from_jsonl(
        self,
        file_path: Path,
        commit_id_key: str,
        use_pr_head_refs: bool,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Load from JSONL file"""
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Invalid JSON on line {line_num}: {e}")
        
        return self._extract_entries_and_toolchains(records, commit_id_key, use_pr_head_refs)

    def _load_from_parquet(
        self,
        file_path: Path,
        commit_id_key: str,
        use_pr_head_refs: bool,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Load from Parquet file"""
        try:
            df = pd.read_parquet(file_path)
            records = df.to_dict('records')
            return self._extract_entries_and_toolchains(records, commit_id_key, use_pr_head_refs)
        except Exception as e:
            raise ValueError(f"Failed to read Parquet file: {e}")

    def _extract_entries_and_toolchains(
        self,
        records: List[Dict],
        commit_id_key: str,
        use_pr_head_refs: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Extract commit metadata and toolchains from records using Pydantic models.

        Uses BaseLeanTaskData to parse and validate records, ensuring consistency
        with the main task execution pipeline.
        """
        if use_pr_head_refs:
            return self._extract_pr_head_entries_and_toolchains(records)

        from ape.tasks.lean_tasks.base import BaseLeanTaskData
        from pydantic import ValidationError

        entries = []
        toolchains = []

        for idx, record in enumerate(records):
            try:
                # Parse record using BaseLeanTaskData Pydantic model
                # This ensures validation and consistency with main pipeline
                task_data = BaseLeanTaskData.model_validate(record)

                # Extract target workspace commit
                if task_data.target_workspace and task_data.target_workspace.commit_hash:
                    entries.append({
                        "commit_hash": task_data.target_workspace.commit_hash.strip(),
                        "repo_url": task_data.target_workspace.repo_url
                    })

                    # Extract target workspace toolchain
                    if task_data.target_workspace.toolchain:
                        toolchain = task_data.target_workspace.toolchain.strip()
                        if toolchain and toolchain.lower() != 'none':
                            toolchains.append(toolchain)

                # Extract reference workspaces
                if task_data.reference_workspaces:
                    for ref_ws in task_data.reference_workspaces:
                        if ref_ws.commit_hash:
                            entries.append({
                                "commit_hash": ref_ws.commit_hash.strip(),
                                "repo_url": ref_ws.repo_url
                            })

                            # Extract reference workspace toolchain
                            if ref_ws.toolchain:
                                ref_toolchain = ref_ws.toolchain.strip()
                                if ref_toolchain and ref_toolchain.lower() != 'none':
                                    toolchains.append(ref_toolchain)

            except ValidationError as e:
                self.logger.warning(
                    f"Failed to parse record {idx} as BaseLeanTaskData: {e}\n"
                    f"Record: {record}"
                )
                continue
            except Exception as e:
                self.logger.warning(f"Unexpected error parsing record {idx}: {e}")
                continue

        return entries, toolchains

    def _extract_pr_head_entries_and_toolchains(self, records: List[Dict]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Extract PR-head build entries from PR review task records."""
        entries: List[Dict[str, Any]] = []
        toolchains: List[str] = []

        for idx, record in enumerate(records):
            try:
                snapshot = record.get("snapshot") or {}
                if not isinstance(snapshot, dict):
                    snapshot = {}
                snapshot_head_sha = str(
                    snapshot.get("snapshot_head_sha") or record.get("snapshot_head_sha") or ""
                ).strip()
                metadata = record.get("metadata") or {}
                if not isinstance(metadata, dict):
                    metadata = {}
                pr_head = snapshot.get("pr_head") or metadata.get("pr_head") or {}
                if not isinstance(pr_head, dict):
                    pr_head = {}

                fetch_repo_url = str(pr_head.get("clone_url") or "").strip()
                fetch_ref = str(pr_head.get("ref") or "").strip()
                cache_repo_full_name = str(pr_head.get("repo_full_name") or "").strip()

                target_workspace = record.get("target_workspace") or {}
                if not isinstance(target_workspace, dict):
                    target_workspace = {}
                repo_url = str(target_workspace.get("repo_url") or self.config.default_repo_url).strip()

                if not snapshot_head_sha or not fetch_repo_url or not fetch_ref:
                    self.logger.warning(
                        "Skipping record %s for PR-head prewarm because snapshot_head_sha/clone_url/ref is missing",
                        idx,
                    )
                    continue

                entries.append(
                    {
                        "commit_hash": snapshot_head_sha,
                        "repo_url": repo_url,
                        "fetch_repo_url": fetch_repo_url,
                        "fetch_ref": fetch_ref,
                        "cache_repo_full_name": cache_repo_full_name or None,
                    }
                )

                toolchain = str(pr_head.get("toolchain") or target_workspace.get("toolchain") or "").strip()
                if toolchain and toolchain.lower() != "none":
                    toolchains.append(toolchain)

            except Exception as e:
                self.logger.warning(f"Unexpected error parsing PR-head record {idx}: {e}")
                continue

        return entries, toolchains
    
    def _print_progress(self, shared_stats: Dict[str, Any], total_tasks: int, start_time: datetime) -> None:
        """Print progress"""
        completed = shared_stats.get('completed', 0)
        successful = shared_stats.get('successful', 0)
        failed = shared_stats.get('failed', 0)

        progress_pct = completed / total_tasks * 100
        success_rate = successful / completed * 100 if completed > 0 else 0

        # Calculate ETA
        elapsed_seconds = (datetime.now() - start_time).total_seconds()
        remaining = max(total_tasks - completed, 0)
        if completed > 0 and remaining > 0:
            avg_per_task = elapsed_seconds / completed
            eta_seconds = int(remaining * avg_per_task)
            eta_hours = int(eta_seconds / 3600)
            eta_minutes = int((eta_seconds % 3600) / 60)
            eta_secs = int(eta_seconds % 60)
            eta_str = f"{eta_hours}h{eta_minutes}m{eta_secs}s"
        else:
            eta_str = "N/A"

        # Colored output
        report = (
            f"{Colors.BOLD}{Colors.CYAN}Progress:{Colors.RESET} {Colors.GREEN}{completed}{Colors.RESET}/"
            f"{Colors.BLUE}{total_tasks}{Colors.RESET} ({Colors.GREEN}{progress_pct:.1f}%{Colors.RESET}) | "
            f"{Colors.BOLD}{Colors.CYAN}Success:{Colors.RESET} {Colors.GREEN}{successful}{Colors.RESET}/"
            f"{Colors.BLUE}{completed}{Colors.RESET} ({Colors.GREEN}{success_rate:.1f}%{Colors.RESET}) | "
            f"{Colors.BOLD}{Colors.CYAN}Failed:{Colors.RESET} {Colors.RED}{failed}{Colors.RESET} | "
            f"{Colors.BOLD}{Colors.CYAN}ETA:{Colors.RESET} {Colors.YELLOW}{eta_str}{Colors.RESET}"
        )

        self.logger.info(report)
    
    async def build_from_file(
        self,
        input_files: Optional[List[str]] = None,
        commit_hash: Optional[str] = None,
        repo_url: Optional[str] = None,
        commit_id_key: str = 'commit_hash',
        use_pr_head_refs: bool = False,
    ) -> Dict[str, Any]:
        """Build all commits from input file"""
        start_time = datetime.now()

        try:
            if commit_hash:
                self.logger.info(f"Building with specified commit: {commit_hash}")
                if repo_url:
                    self.logger.info(f"Using specified repository: {repo_url}")
                entries = [{
                    "commit_hash": commit_hash.strip(),
                    "repo_name": None,
                    "repo_url": repo_url
                }]
                toolchains = []
            elif input_files:
                # Process multiple input files
                all_entries = []
                all_toolchains = []
                
                self.logger.info(f"Starting batch build from {len(input_files)} files")
                
                for input_file in input_files:
                    self.logger.info(f"Loading file: {input_file}")
                    file_entries, file_toolchains = self._load_entries_from_file(
                        Path(input_file),
                        commit_id_key,
                        use_pr_head_refs,
                    )
                    all_entries.extend(file_entries)
                    all_toolchains.extend(file_toolchains)
                    self.logger.info(
                        f"  Loaded {len(file_entries)} commits and "
                        f"{len(file_toolchains)} toolchains from {input_file}"
                    )
                
                entries = all_entries
                toolchains = all_toolchains
                
                if not entries:
                    self.logger.warning("No commits found in all input files")
                    return {
                        'total_commits': 0,
                        'successful_builds': 0,
                        'failed_builds': 0,
                        'build_duration_seconds': (datetime.now() - start_time).total_seconds(),
                        'success_rate': 0.0
                    }
                
                self.logger.info(f"Total {len(entries)} commits and {len(toolchains)} toolchains found")
            else:
                self.logger.info("Building with default commit")
                entries = [{
                    "commit_hash": self.config.default_commit_hash,
                    "repo_url": None
                }]
                toolchains = []
                self.logger.info(f"Using default commit: {self.config.default_commit_hash}")
            
            # Execute batch build
            results = await self.build_commits(entries, toolchains=toolchains)
            
            # Add duration
            results['build_duration_seconds'] = (datetime.now() - start_time).total_seconds()
            return results
            
        except Exception as e:
            self.logger.error(f"Batch build failed: {e}")
            raise
    
    async def build_commits(
        self, 
        entries: List[Dict[str, Any]],
        toolchains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Use ProcessPoolExecutor to build multiple commits concurrently"""
        if not entries:
            return {
                'total_commits': 0,
                'successful_builds': 0,
                'failed_builds': 0,
                'success_rate': 0.0,
                'task_results': []
            }
        
        normalized_entries: List[Dict[str, Any]] = []
        for entry in entries:
            commit_hash = (entry.get("commit_hash") or "").strip()
            if not commit_hash:
                continue
            repo_name, repo_url = self.config.resolve_repo(entry.get("repo_url"))
            normalized_entry = dict(entry)
            normalized_entry.update({
                "commit_hash": commit_hash,
                "repo_name": repo_name,
                "repo_url": repo_url
            })
            normalized_entries.append(normalized_entry)

        if not normalized_entries:
            return {
                'total_commits': 0,
                'successful_builds': 0,
                'failed_builds': 0,
                'success_rate': 0.0,
                'task_results': []
            }

        # Remove duplicate commits (by repo+commit)
        unique_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for entry in normalized_entries:
            key = (entry["repo_name"], entry["commit_hash"])
            if key not in unique_map:
                unique_map[key] = entry
        unique_entries = list(unique_map.values())
        
        # ==================== New: unified repository cloning ====================
        # Collect all required repositories
        repos_to_clone = []
        for entry in unique_entries:
            repos_to_clone.append({
                "repo_name": entry["repo_name"],
                "repo_url": entry["repo_url"]
            })
        
        # Clone all repositories before concurrent build
        self.logger.info(f"Checking and cloning required Git repositories...")
        try:
            repo_success = await self._ensure_repositories_cloned(repos_to_clone)
            if not repo_success:
                self.logger.warning("Some repositories failed to clone, continue build process")
        except Exception as e:
            self.logger.error(f"Repository cloning failed: {e}")
            self.logger.warning("Continue build process")
        # ==================== Repository cloning end ====================
        
        # Install toolchains
        if toolchains:
            self.logger.info(f"Installing {len(toolchains)} toolchains...")
            try:
                toolchain_success = await self._install_toolchains(toolchains)
                if not toolchain_success:
                    self.logger.warning("Some toolchains failed to install, continue build process")
            except Exception as e:
                self.logger.error(f"Toolchain installation failed: {e}")
                self.logger.warning("Continue build process")
        
        self.logger.info(f"Concurrent build {len(unique_entries)} commits, using {self.config.num_processes} processes")
        
        # Create shared statistics state
        manager = mp.Manager()
        shared_stats = manager.dict({
            'completed': 0,
            'successful': 0,
            'failed': 0
        })
        stats_lock = manager.Lock()
        
        # Configuration dictionary
        config_dict = self.config.model_dump(mode='json')
        log_dir = self._get_log_dir_for_subprocess()
        
        # Concurrent execution
        results = []
        total_tasks = len(unique_entries)
        parent_start_time = datetime.now()

        try:
            with ProcessPoolExecutor(max_workers=self.config.num_processes) as executor:
                # Submit all tasks
                future_to_commit = {}
                for entry in unique_entries:
                    future = executor.submit(
                        build_single_commit_worker,
                        entry, 
                        config_dict,
                        shared_stats, 
                        stats_lock,
                        log_dir
                    )
                    future_to_commit[future] = entry
                
                # Monitor progress and collect results
                last_print_time = 0
                for future in as_completed(future_to_commit):
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Limit print frequency
                        current_time = datetime.now().timestamp()
                        if current_time - last_print_time >= 1.0:
                            self._print_progress(shared_stats, total_tasks, parent_start_time)
                            last_print_time = current_time
                        
                    except Exception as e:
                        entry = future_to_commit[future]
                        commit = entry.get("commit_hash")
                        repo_name = entry.get("repo_name")
                        repo_url = entry.get("repo_url")
                        self.logger.error(f"Exception occurred while building {repo_name or 'unknown'}@{commit}: {e}")
                        
                        results.append({
                            'task_id': commit,
                            'success': False,
                            'commit_hash': commit,
                            'repo_name': repo_name,
                            'repo_url': repo_url,
                            'error_message': traceback.format_exc()
                        })
                
                # Final progress print
                self._print_progress(shared_stats, total_tasks, parent_start_time)
                self.logger.info("")  # New line
            
            self.logger.info("Concurrent build completed")
            
            successful_builds = shared_stats.get('successful', 0)
            failed_builds = shared_stats.get('failed', 0)
            success_rate = successful_builds / len(unique_entries) if unique_entries else 0.0
            
            self.logger.info(f"Build results: successful {successful_builds}, failed {failed_builds}, success rate {success_rate:.2%}")
            
            return {
                'total_commits': len(unique_entries),
                'successful_builds': successful_builds,
                'failed_builds': failed_builds,
                'success_rate': success_rate,
                'task_results': results
            }
            
        except Exception as e:
            self.logger.error(f"Concurrent build failed: {traceback.format_exc()}")
            return {
                'total_commits': len(unique_entries),
                'successful_builds': 0,
                'failed_builds': len(unique_entries),
                'success_rate': 0.0,
                'task_results': [],
                'error': traceback.format_exc()
            }

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Lean verification service - batch builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build with default commit
  python -m ape.toolkits.execute.lean.build

  # Build specified single repo
  python -m ape.toolkits.execute.lean.build --target_repo "git@github.com:user/repo.git@@abc123def456"

  python -m ape.toolkits.execute.lean.build --target_repo git@github.com:leanprover-community/mathlib4.git@@2df2f0150c275ad53cb3c90f7c98ec15a56a1a67

  # Build from single JSONL file
  python -m ape.toolkits.execute.lean.build --input_file commits.jsonl

  # Build from multiple files
  python -m ape.toolkits.execute.lean.build --input_file file1.jsonl file2.jsonl file3.parquet

  # Build from all files in directory using wildcard
  python -m ape.toolkits.execute.lean.build --input_file inputs/minictx_v2/*.jsonl

  # Custom settings
  python -m ape.toolkits.execute.lean.build \\
      --input_file commits.jsonl --num_processes 4

  # Prewarm PR-head workspaces from PR review task files
  python -m ape.toolkits.execute.lean.build \\
      --input_file inputs/proof_pr_review/*.jsonl --prewarm_pr_heads
        """
    )
    
    parser.add_argument(
        "--input_file",
        type=str,
        nargs='*',  # Accept 0 or more values
        help="Input file paths containing commits (JSONL or Parquet format), can specify multiple files"
    )

    parser.add_argument(
        "--target_repo",
        type=str,
        help="Target repository in format: repo_url@@commit_hash. "
             "Example: git@github.com:user/repo.git@@abc123"
    )

    parser.add_argument(
        "--commit_id_key",
        type=str,
        default="commit_hash",
        help="Key name for commit ID in input data (default: %(default)s)"
    )

    parser.add_argument(
        "--num_processes",
        type=int,
        default=None,
        help="Number of parallel processes"
    )

    parser.add_argument(
        "--build_timeout",
        type=float,
        help="Build timeout (seconds)"
    )

    parser.add_argument(
        "--prewarm_pr_heads",
        action="store_true",
        help="Extract PR-head refs from PR review task files and build those heads explicitly",
    )
    
    return parser

async def run_batch_build(args: argparse.Namespace) -> int:
    """Run batch build process"""
    logger = create_logger()

    try:
        config = LeanVerifyToolConfig()
        if args.num_processes:
            config.num_processes = args.num_processes

        logger.info("Starting batch build process")

        # Parse target_repo if provided
        commit_hash = None
        repo_url = None
        if args.target_repo:
            repo_url, commit_hash = parse_repo_spec(args.target_repo)
            logger.info(f"Target repo: {repo_url}@@{commit_hash}")

        if args.input_file:
            logger.info(f"Input file: {args.input_file}")
            logger.info(f"Commit ID key name: {args.commit_id_key}")
        elif not args.target_repo:
            logger.info("Using default commit for build")

        logger.info(f"Number of processes: {config.num_processes}")

        # Create batch builder
        builder = BatchBuilder(config, logger)

        # Execute batch build
        results = await builder.build_from_file(
            input_files=args.input_file,
            commit_hash=commit_hash,
            repo_url=repo_url,
            commit_id_key=args.commit_id_key,
            use_pr_head_refs=args.prewarm_pr_heads,
        )
        
        # Print results
        logger.info("Batch build completed!")
        logger.info(f"Total commits: {results['total_commits']}")
        logger.info(f"Successful builds: {results['successful_builds']}")
        logger.info(f"Failed builds: {results['failed_builds']}")
        logger.info(f"Success rate: {results['success_rate']:.2%}")
        
        if 'build_duration_seconds' in results:
            logger.info(f"Total duration: {results['build_duration_seconds']:.2f} seconds")
        
        # Return exit code
        if results['failed_builds'] > 0:
            logger.warning(f"{results['failed_builds']} builds failed")
            return 1
        else:
            logger.info("All builds completed successfully")
            return 0
            
    except KeyboardInterrupt:
        logger.warning("Build process interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Build process failed: {e}")
        logger.debug(f"Exception details: {traceback.format_exc()}")
        return 1

def main() -> int:
    """Main entry point for batch builder"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    logger = create_logger()
    logger.info("Lean verification service batch builder")
    
    try:
        return asyncio.run(run_batch_build(args))
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.debug(f"Exception details: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
