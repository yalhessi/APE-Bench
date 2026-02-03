"""
Data collection component - multi-repo support
"""

import random
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional, TYPE_CHECKING
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

import git
from tqdm import tqdm

from .models import CommitFileMapping, DeclarationInfo, ScanResult
from .utils import parse_declarations, compute_item_id
from ape.utils.file_ops import normalize_repo_url

if TYPE_CHECKING:
    from ape.toolkits.execute.lean.config import LeanVerifyToolConfig


def _process_commits_batch(args: Tuple[List[str], str, Optional[str], str]) -> Dict[str, List[Tuple[str, str]]]:
    """Batch process commits, collect blob ID to file mapping

    Args:
        args: (commit_hashes, repo_path, default_target, file_extension)
              default_target can be None or empty string to extract all files
    """
    commit_hashes, repo_path, default_target, file_extension = args

    repo = git.Repo(repo_path)
    content_to_files = defaultdict(list)

    for commit_hash in commit_hashes:
        ls_output = repo.git.ls_tree(commit_hash, '-r')
        for line in ls_output.splitlines():
            header, path = line.split("\t", 1)
            parts = header.split()
            if len(parts) >= 3 and parts[1] == 'blob':
                sha = parts[2]
                # Filter by file extension (and optionally default_target prefix)
                if not path.endswith(file_extension):
                    continue

                # If default_target is provided, filter by prefix
                if default_target:
                    if path.startswith(f"{default_target}/"):
                        content_to_files[sha].append((commit_hash, path))
                else:
                    # No default_target filter - include all matching files
                    content_to_files[sha].append((commit_hash, path))

    return dict(content_to_files)


def _parse_contents_batch(args: Tuple[List[str], str, Set[str]]) -> Dict[str, List[Dict[str, Any]]]:
    """Batch parse file contents, extract declarations"""
    blob_ids, repo_path, existing_ids = args
    
    repo = git.Repo(repo_path)
    results = {}
    
    for blob_id in blob_ids:
        content = repo.git.cat_file('-p', blob_id)
        parsed = parse_declarations(content)
        
        declarations = []
        for decl in parsed:
            item_id = compute_item_id(decl['kind'], decl['name'], decl['signature'], decl['proof'])
            
            declaration = {
                'item_id': item_id,
                'kind': decl['kind'],
                'name': decl['name'],
                'fullname': decl.get('fullname'),
                'variables': decl.get('variables', []),
                'signature': decl['signature'],
                'span': tuple(decl['span']),
                'proof': decl['proof'],
                'existing': item_id in existing_ids
            }
            declarations.append(declaration)
        
        results[blob_id] = declarations
    
    return results


class DataCollector:
    """Data collector - multi-repo support, using LeanVerifyToolConfig for path management"""

    def __init__(self, config: "LeanVerifyToolConfig", file_extension: str, logger):
        self.config = config
        self.file_extension = file_extension
        self.logger = logger

    def get_repo_path(self, repo_url: str) -> Path:
        """Get local source code path based on repo_url using config methods"""
        repo_name = normalize_repo_url(repo_url)
        return self.config.get_repo_source_path(repo_name)

    async def ensure_repo_cloned(self, repo_url: str) -> Path:
        """Ensure repository is cloned to standard location using LeanVerifyToolConfig structure"""
        repo_path = self.get_repo_path(repo_url)

        if repo_path.exists():
            self.logger.info(f"Repository exists: {repo_path}")
            return repo_path

        self.logger.info(f"Cloning {repo_url} to {repo_path}")
        repo_path.parent.mkdir(parents=True, exist_ok=True)

        import asyncio
        await asyncio.to_thread(git.Repo.clone_from, repo_url, str(repo_path))

        self.logger.info(f"Cloned: {repo_path}")
        return repo_path
    
    def collect_file_mappings(
        self,
        repo_path: Path,
        commit_hashes: List[str],
        batch_size: int,
        io_workers: int,
        default_target: Optional[str] = None
    ) -> CommitFileMapping:
        """Collect file mapping

        Args:
            repo_path: Repository path
            commit_hashes: List of commit hashes
            batch_size: Batch size for processing
            io_workers: Number of IO workers
            default_target: Default target directory filter (optional, e.g., 'Mathlib').
                          If None or empty, extracts all files matching the extension.
        """
        random.shuffle(commit_hashes)
        batches = [commit_hashes[i:i + batch_size] for i in range(0, len(commit_hashes), batch_size)]

        self.logger.info(f"Collecting files: {len(commit_hashes)} commits, {len(batches)} batches")
        if default_target:
            self.logger.info(f"Filtering by default_target: {default_target}")
        else:
            self.logger.info("No default_target filter - extracting all matching files")

        content_to_files = defaultdict(list)
        commit_file_lists = {}

        # Pass default_target directly to batch processing
        batch_args = [(batch, str(repo_path), default_target, self.file_extension) for batch in batches]
        
        with ThreadPoolExecutor(max_workers=io_workers) as executor:
            futures = {executor.submit(_process_commits_batch, args): i for i, args in enumerate(batch_args)}
            
            for future in tqdm(as_completed(futures), total=len(batches), desc="Collecting files"):
                batch_results = future.result()
                for content_id, file_list in batch_results.items():
                    content_to_files[content_id].extend(file_list)
        
        for content_id, file_list in content_to_files.items():
            for commit_hash, file_path in file_list:
                if commit_hash not in commit_file_lists:
                    commit_file_lists[commit_hash] = []
                if file_path not in commit_file_lists[commit_hash]:
                    commit_file_lists[commit_hash].append(file_path)
        
        return CommitFileMapping(
            content_to_files=dict(content_to_files),
            commit_file_lists=commit_file_lists
        )
    
    async def parse_contents(
        self,
        repo_path: Path,
        content_to_files: Dict[str, List[Tuple[str, str]]], 
        existing_ids: Set[str], 
        batch_size: int, 
        num_processes: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Parse contents"""
        blob_ids = list(content_to_files.keys())
        random.shuffle(blob_ids)
        batches = [blob_ids[i:i + batch_size] for i in range(0, len(blob_ids), batch_size)]
        
        self.logger.info(f"Parsing: {len(blob_ids)} blobs, {len(batches)} batches")
        
        content_to_declarations = {}
        batch_args = [(batch, str(repo_path), existing_ids) for batch in batches]
        
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            futures = {executor.submit(_parse_contents_batch, args): i for i, args in enumerate(batch_args)}
            
            for future in tqdm(as_completed(futures), total=len(batches), desc="Parsing"):
                batch_results = future.result()
                content_to_declarations.update(batch_results)
        
        return content_to_declarations
    
    def build_scan_result(
        self,
        content_to_declarations: Dict[str, List[Dict[str, Any]]],
        file_mapping: CommitFileMapping,
        index_only_mode: bool,
        repo_url: str,
        default_target: str
    ) -> ScanResult:
        """Build scan result

        Args:
            default_target: Default target directory (REQUIRED)
        """
        global_declarations = {}
        commit_index = defaultdict(list)
        all_unique_declarations = {}
        
        commit_file_to_content = {}
        for blob_id, file_list in file_mapping.content_to_files.items():
            for commit_hash, file_path in file_list:
                commit_file_to_content[(commit_hash, file_path)] = blob_id
        
        for commit_hash, file_paths in file_mapping.commit_file_lists.items():
            seen_item_ids = set()
            
            for file_path in file_paths:
                if (commit_hash, file_path) in commit_file_to_content:
                    content_id = commit_file_to_content[(commit_hash, file_path)]
                    if content_id in content_to_declarations:
                        declarations = content_to_declarations[content_id]
                        
                        for decl in declarations:
                            item_id = decl['item_id']
                            
                            if item_id not in all_unique_declarations:
                                all_unique_declarations[item_id] = {
                                    'existing': decl.get('existing', False),
                                    'decl_data': decl
                                }
                            
                            if item_id not in seen_item_ids:
                                # Include filename and variables in commit_index for per-commit tracking
                                commit_index[commit_hash].append(
                                    (item_id, decl['name'], file_path, decl.get('variables', []))
                                )
                                seen_item_ids.add(item_id)
                            
                            if index_only_mode or not decl.get('existing'):
                                if item_id not in global_declarations:
                                    decl_info = DeclarationInfo(
                                        item_id=item_id,
                                        kind=decl['kind'],
                                        name=decl['name'],
                                        fullname=decl.get('fullname'),
                                        variables=decl.get('variables', []),
                                        signature=decl['signature'],
                                        proof=decl['proof'],
                                        span=decl['span'],
                                        commit_hash=commit_hash,
                                        repo_url=repo_url,
                                        file_path=str(file_path),
                                        default_target=default_target
                                    )
                                    global_declarations[item_id] = decl_info
        
        total_unique = len(all_unique_declarations)
        existing_unique = sum(1 for info in all_unique_declarations.values() if info['existing'])
        new_unique = len(global_declarations)
        
        repo_name = normalize_repo_url(repo_url)
        self.logger.info(f"[{repo_name}] {total_unique} unique, {existing_unique} existing, {new_unique} new")
        
        return ScanResult(
            global_declarations=global_declarations,
            commit_index={repo_url: dict(commit_index)},
            total_declarations=total_unique,
            existing_skipped=existing_unique,
            unique_blobs=len(content_to_declarations)
        )
