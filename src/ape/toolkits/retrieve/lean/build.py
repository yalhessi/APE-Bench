"""
Lean Retrieve Database Builder - Build retrieval system database

Scan Git commits and generate semantic annotations to build Lean code retrieval database.
"""

import argparse
import asyncio
import hashlib
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

import json

from ape.utils.logging import create_logger
from ape.utils import load_yaml, parse_cli_args, deep_merge
from ape.scaffolds.factory import create_scaffold_config_for_type
from ape.tasks.base import create_task_config_for_type
from ape.tasks.models import parse_workspace_info
from ape.scaffolds.config import BaseScaffoldConfig
from ape.orchestration.config import ExecutionConfig
from ape.orchestration.orchestrator import TaskOrchestrator, OrchestratorResults
from ape.utils.file_ops import normalize_repo_url

from .semantic_annotation.config import AnnotationConfig
from .semantic_annotation.models import ScanResult, AnnotationStats, DeclarationInfo
from .semantic_annotation.collector import DataCollector
from .semantic_annotation.utils import (
    compute_config_hash,
    load_existing_ids,
    generate_task_id,
    get_cache_file_path,
    load_cache,
    save_cache
)
from .semantic_annotation.task import AnnotationTask
from .models import LeanItem
from .utils import save_data_batch


def parse_repo_spec(spec: str) -> Tuple[str, str, Optional[str]]:
    """Parse repo_url@@commit_hash or repo_url@@commit_hash@@default_target"""
    parts = spec.split("@@")
    repo_url = parts[0]
    commit_hash = parts[1]
    default_target = parts[2] if len(parts) > 2 else None
    return repo_url, commit_hash, default_target


class SemanticAnnotationPipeline:
    """Simplified semantic annotation pipeline"""

    def __init__(self, config: AnnotationConfig, logger=None, orchestrator_id: Optional[str] = None):
        self.config = config
        self.orchestrator_id = orchestrator_id
        self.logger = logger or create_logger()
        self._config_hash = compute_config_hash(self.config)

        # Initialize components
        self.collector = DataCollector(
            self.config.lean_verify_config,
            self.config.required_file_extension,
            self.logger
        )

        # Scaffold configuration
        task_config = create_task_config_for_type("lean_semantic_annotation")
        execution_config = ExecutionConfig(
            num_processes=config.num_processes,
            task_max_retries=config.max_retries
        )
        from ape.llm_clients.config import LLMConfig
        from ape.scaffolds.config import BaseToolsConfig
        from ape.runtime import LocalRuntimeConfig

        # Create a minimal base config with scaffold_type for the factory
        base_config = BaseScaffoldConfig(
            scaffold_type=config.scaffold_type,  # Add required scaffold_type field
            task_config=task_config,
            execution=execution_config,
            tools_config=BaseToolsConfig(),
            runtime_config=LocalRuntimeConfig()
        )
        self.scaffold_config = create_scaffold_config_for_type(
            scaffold_type=config.scaffold_type,
            base_config=base_config,
            llm_config=LLMConfig(model_name=config.model)
        )
    
    def _compute_orchestrator_id(self) -> str:
        """Compute orchestrator ID"""
        return f"semantic_annotation_{self._config_hash}"

    @staticmethod
    def _compute_existing_ids_signature(existing_ids: Set[str]) -> str:
        """Compute stable signature based on existing_ids, for cache"""
        if not existing_ids:
            return "empty"
        payload = '\n'.join(sorted(existing_ids))
        return hashlib.md5(payload.encode()).hexdigest()

    def _build_cache_tokens(
        self,
        repos_commits: Dict[str, List[str]],
        existing_ids_by_repo: Dict[str, Set[str]]
    ) -> List[str]:
        """Build cache token list (contains repo/commit and existing_ids signature)"""
        tokens: List[str] = []
        for repo_url in sorted(repos_commits.keys()):
            commits = sorted(set(repos_commits[repo_url]))
            tokens.extend(f"{repo_url}#{commit}" for commit in commits)
            sig = self._compute_existing_ids_signature(existing_ids_by_repo.get(repo_url, set()))
            tokens.append(f"{repo_url}#ids:{sig}")
        return tokens

    def _effective_repo_url(self, repo_url: Optional[str]) -> str:
        """Ensure repo_url always has a value"""
        return repo_url or self.config.lean_verify_config.default_repo_url

    def _make_repo_retrieve_config(self, repo_url: Optional[str]):
        """Copy retrieval configuration and bind to specific repo"""
        effective_url = self._effective_repo_url(repo_url)
        return self.config.lean_retrieve_config.model_copy(update={"repo_url": effective_url})

    @staticmethod
    def _count_commits(commit_index: Dict[str, Dict[str, List]]) -> int:
        """Count total commit number"""
        return sum(len(commits) for commits in commit_index.values())

    async def run(self) -> AnnotationStats:
        """Run complete semantic annotation pipeline"""
        start_time = time.time()

        repos_commits, repos_default_target, target_references = self._extract_repos_from_input()
        if not repos_commits:
            self.logger.info("No repositories found in input; nothing to process")
            return AnnotationStats(duration_sec=time.time() - start_time)
        
        existing_ids_by_repo: Dict[str, Set[str]] = {}
        total_existing = 0
        for repo_url in repos_commits.keys():
            # Directly use get_annotated_ids_file(repo_url)
            ids = load_existing_ids(
                self.config.lean_retrieve_config.get_annotated_ids_file(repo_url)
            )
            existing_ids_by_repo[repo_url] = ids
            total_existing += len(ids)
        self.logger.info(
            f"Loaded {total_existing} existing annotations across {len(existing_ids_by_repo)} repos"
        )
        
        # First phase: global scanning (with optional cache)
        if self.config.use_cache:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_tokens = self._build_cache_tokens(repos_commits, existing_ids_by_repo)
            cache_file = get_cache_file_path(self.config.cache_dir, self._config_hash, cache_tokens)
            cached_scan_result = await asyncio.to_thread(load_cache, cache_file)
            if cached_scan_result:
                self.logger.info(f"Phase 1 cache hit: {cache_file}")
                scan_result = cached_scan_result
            else:
                scan_result = await self._phase1_global_scan(
                    repos_commits,
                    existing_ids_by_repo,
                    repos_default_target,
                    cache_file
                )
        else:
            self.logger.info("Phase 1 cache disabled; scanning without cache")
            scan_result = await self._phase1_global_scan(
                repos_commits,
                existing_ids_by_repo,
                repos_default_target,
                cache_file=None
            )
        
        if self.config.index_only_mode:
            # Index only mode
            total_indexed = await self._index_only_update(scan_result.commit_index, existing_ids_by_repo)
            return AnnotationStats(
                commits_processed=self._count_commits(scan_result.commit_index),
                indexed=total_indexed,
                duration_sec=time.time() - start_time,
                mode="index_only"
            )
        else:
            # Normal annotation mode
            if not scan_result.global_declarations:
                self.logger.info("No new declarations to annotate")
                return AnnotationStats(
                    commits_processed=self._count_commits(scan_result.commit_index),
                    skipped=scan_result.existing_skipped,
                    duration_sec=time.time() - start_time
                )
            
            # Second phase: annotation tasks
            orchestrator_id = self.orchestrator_id or self._compute_orchestrator_id()
            total_annotated = await self._phase2_annotation(scan_result, target_references, orchestrator_id)
            
            return AnnotationStats(
                commits_processed=self._count_commits(scan_result.commit_index),
                annotated=total_annotated,
                skipped=scan_result.existing_skipped,
                duration_sec=time.time() - start_time
            )

    def _extract_repos_from_input(self) -> Tuple[Dict[str, List[str]], Dict[str, Optional[str]], Dict[Tuple[str, str], List[Dict[str, Any]]]]:
        """
        Extract all repos, commits, default_target, and reference workspaces from input file

        Returns:
            Tuple of:
            - Dict[repo_url, List[commit_hash]]
            - Dict[repo_url, default_target] (default_target can be None to extract all files)
            - Dict[(target_repo_url, target_commit), List[ref_workspace_dict]] - reference workspaces per target
        """
        repos_commits = defaultdict(set)
        repos_default_target: Dict[str, Optional[str]] = {}
        target_references: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

        with open(self.config.input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)

                target_workspace = record.get('target_workspace')
                if not isinstance(target_workspace, dict):
                    raise ValueError("Each record must include target_workspace")

                target_workspace_info = parse_workspace_info(target_workspace)
                commit = target_workspace_info.commit_hash
                repo_url = self._effective_repo_url(target_workspace_info.repo_url)
                if commit:
                    repos_commits[repo_url].add(commit)
                    if repo_url not in repos_default_target:
                        default_target = target_workspace_info.default_target
                        repos_default_target[repo_url] = default_target if default_target else None

                ref_workspaces = record.get('reference_workspaces', [])

                # Store reference workspaces for this target
                if commit and ref_workspaces:
                    target_key = (repo_url, commit)
                    target_references[target_key] = ref_workspaces
                if isinstance(ref_workspaces, list):
                    for ref_ws in ref_workspaces:
                        if isinstance(ref_ws, dict):
                            ref_workspace_info = parse_workspace_info(ref_ws)
                            ref_commit = ref_workspace_info.commit_hash
                            ref_url = self._effective_repo_url(ref_workspace_info.repo_url)
                            if ref_commit:
                                repos_commits[ref_url].add(ref_commit)
                                if ref_url not in repos_default_target:
                                    ref_default_target = ref_workspace_info.default_target
                                    repos_default_target[ref_url] = ref_default_target if ref_default_target else None

        return {k: list(v) for k, v in repos_commits.items()}, repos_default_target, target_references

    async def _phase1_global_scan(
        self,
        repos_commits: Dict[str, List[str]],
        existing_ids_by_repo: Dict[str, Set[str]],
        repos_default_target: Dict[str, Optional[str]],
        cache_file: Optional[Path] = None
    ) -> ScanResult:
        """First phase: global scanning (multi-repo)"""
        self.logger.info("Phase 1: Multi-repo scanning...")
        self.logger.info(f"Found {len(repos_commits)} repositories")

        all_declarations = {}
        all_commit_index: Dict[str, Dict[str, List[Tuple[str, Optional[str], str, List[str]]]]] = defaultdict(lambda: defaultdict(list))
        skipped_total = 0
        unique_blobs_total = 0

        for repo_url, commits in repos_commits.items():
            repo_name = normalize_repo_url(repo_url)
            self.logger.info(f"Scanning [{repo_name}]: {len(commits)} commits")
            existing_ids = existing_ids_by_repo.get(repo_url, set())

            # Get default_target (can be None to extract all files)
            default_target = repos_default_target[repo_url]

            # 1. Ensure repo is cloned (using LeanVerifyToolConfig standard structure)
            repo_path = await self.collector.ensure_repo_cloned(repo_url)

            # 2. Collect file mapping (pass default_target)
            file_mapping = self.collector.collect_file_mappings(
                repo_path, commits,
                self.config.batch_size, self.config.io_workers,
                default_target=default_target
            )
            
            # 3. Parse content
            content_to_declarations = await self.collector.parse_contents(
                repo_path, file_mapping.content_to_files, existing_ids,
                self.config.batch_size, self.config.num_processes
            )
            
            # 4. Build declarations (pass default_target)
            scan_result = self.collector.build_scan_result(
                content_to_declarations, file_mapping,
                self.config.index_only_mode, repo_url,
                default_target=default_target
            )
            skipped_total += scan_result.existing_skipped
            unique_blobs_total += scan_result.unique_blobs
            
            # 5. Merge results
            all_declarations.update(scan_result.global_declarations)
            for repo_key, commits_map in scan_result.commit_index.items():
                bucket = all_commit_index[repo_key]
                for commit_hash, items in commits_map.items():
                    if commit_hash not in bucket:
                        bucket[commit_hash] = []
                    bucket[commit_hash].extend(items)
        
        total = len(all_declarations)
        self.logger.info(f"Total: {total} unique declarations")
        merged_commit_index = {
            repo_url: dict(commits) for repo_url, commits in all_commit_index.items()
        }
        
        result = ScanResult(
            global_declarations=all_declarations,
            commit_index=merged_commit_index,
            total_declarations=total,
            existing_skipped=skipped_total,
            unique_blobs=unique_blobs_total
        )
        
        if cache_file:
            await asyncio.to_thread(save_cache, cache_file, result)
            self.logger.info(f"Phase 1 cache saved: {cache_file}")
        
        return result

    async def _phase2_annotation(self, scan_result: ScanResult, target_references: Dict[Tuple[str, str], List[Dict[str, Any]]], orchestrator_id: str) -> int:
        """Second phase: create and execute annotation tasks"""
        self.logger.info(f"Phase 2: Creating tasks for {len(scan_result.global_declarations)} declarations...")

        tasks = self._create_annotation_tasks(scan_result.global_declarations, target_references)
        if not tasks:
            self.logger.info("No tasks to execute")
            return 0
        
        # Run tasks
        self.logger.info(f"Running {len(tasks)} tasks with orchestrator ID: {orchestrator_id}")
        orchestrator = TaskOrchestrator(
            config=self.scaffold_config,
            orchestrator_id=orchestrator_id,
            logger=self.logger
        )
        
        results = await orchestrator.run(tasks)
        
        # Save results
        return await self._save_annotation_results(results, scan_result)

    def _create_annotation_tasks(self, global_declarations: Dict[str, DeclarationInfo], target_references: Dict[Tuple[str, str], List[Dict[str, Any]]]) -> List[AnnotationTask]:
        """Create annotation tasks with reference workspaces"""
        file_groups = defaultdict(list)

        for decl_info in global_declarations.values():
            # Keep repo separation to avoid mixing identical commit hashes across repos
            key = (decl_info.repo_url, decl_info.commit_hash, decl_info.file_path)
            file_groups[key].append(decl_info)
        
        tasks = []
        files_processed = 0
        
        for (repo_url, commit_hash, file_path), declarations in file_groups.items():
            if self.config.max_files_scan is not None and files_processed >= self.config.max_files_scan:
                self.logger.info(f"Reached max_files_scan limit of {self.config.max_files_scan}")
                break

            # Skip if no declarations (should not happen, but defensive check)
            if not declarations:
                self.logger.warning(f"Skipping empty declaration group for {file_path}")
                continue

            declarations.sort(key=lambda d: d.span[0])

            # Get default_target from first declaration (all declarations should share the same default_target)
            default_target = declarations[0].default_target

            max_decls = self.config.max_declarations_per_task
            chunks = [declarations[i:i + max_decls] for i in range(0, len(declarations), max_decls)]

            for chunk_idx, chunk_declarations in enumerate(chunks):
                task_id = generate_task_id(
                    commit_hash, file_path,
                    chunk_idx if len(chunks) > 1 else None
                )

                # Build target_workspace for annotation task
                from ape.tasks.models import WorkspaceInfo, GitWorkspaceSource

                target_workspace = WorkspaceInfo(
                    name='target',
                    source=GitWorkspaceSource(
                        commit_hash=commit_hash,
                        repo_url=repo_url,
                    ),
                    default_target=default_target
                )

                # Build reference_workspaces from target_references
                # Logic: If this (repo_url, commit_hash) is a target in the input,
                # attach its reference workspaces; otherwise it's being built standalone
                reference_workspaces = None
                target_key = (repo_url, commit_hash)
                if target_key in target_references:
                    # This is a target workspace - attach references for agent to search
                    reference_workspaces = []
                    for ref_ws_dict in target_references[target_key]:
                        ref_workspace_info = parse_workspace_info(ref_ws_dict)
                        ref_url = ref_workspace_info.repo_url
                        ref_commit = ref_workspace_info.commit_hash
                        ref_default = ref_workspace_info.default_target
                        if ref_url and ref_commit:
                            # Generate unique name for reference workspace
                            ref_name = ref_url.split('/')[-1].replace('.git', '').lower()
                            reference_workspaces.append(WorkspaceInfo(
                                name=ref_name,
                                source=GitWorkspaceSource(
                                    commit_hash=ref_commit,
                                    repo_url=ref_url,
                                ),
                                default_target=ref_default
                            ))
                    self.logger.info(
                        f"Building target workspace {normalize_repo_url(repo_url)}@{commit_hash[:8]} "
                        f"with {len(reference_workspaces)} reference(s)"
                    )
                else:
                    # This is a reference workspace being built standalone
                    self.logger.info(
                        f"Building reference workspace {normalize_repo_url(repo_url)}@{commit_hash[:8]} "
                        f"(no references attached)"
                    )

                task_data = {
                    'task_id': task_id,
                    'task_type': 'lean_semantic_annotation',
                    'filename': file_path,
                    'declarations': chunk_declarations,
                    'target_workspace': target_workspace,
                    'reference_workspaces': reference_workspaces
                }
                task = AnnotationTask.from_data(task_data, self.scaffold_config)
                tasks.append(task)

            files_processed += 1
        
        self.logger.info(f"Created {len(tasks)} annotation tasks from {files_processed} files")
        return tasks

    async def _save_annotation_results(self, results: OrchestratorResults, scan_result: ScanResult) -> int:
        """Save annotation results"""
        all_annotations = {}
        for tr in results.task_results:
            if tr.success and tr.task_type == 'lean_semantic_annotation':
                annotations = tr.annotations
                for item_id, annotation_data in annotations.items():
                    if item_id in scan_result.global_declarations:
                        all_annotations[item_id] = annotation_data
        
        if not all_annotations:
            return 0
        
        self.logger.info(f"Saving {len(all_annotations)} annotations...")
        
        commit_items: Dict[str, Dict[str, List[LeanItem]]] = defaultdict(lambda: defaultdict(list))
        
        for repo_url, commits in scan_result.commit_index.items():
            for commit_hash, items in commits.items():
                # Unpack 4-tuple: (item_id, name, filename, variables)
                for item_id, _, filename, variables in items:
                    if item_id in all_annotations:
                        decl_info = scan_result.global_declarations[item_id]
                        annotation = all_annotations[item_id]
                        line_start, line_end = decl_info.span
                        # Use filename from commit_index (per-commit path) instead of decl_info.file_path
                        commit_items[repo_url][commit_hash].append(LeanItem(
                            item_id=item_id,
                            kind=decl_info.kind,
                            name=decl_info.name,
                            fullname=decl_info.fullname,
                            variables=variables,
                            signature=decl_info.signature,
                            proof=decl_info.proof,
                            filename=filename,  # Use per-commit filename from commit_index
                            span_start=line_start,
                            span_end=line_end,
                            semantic=annotation.semantic_statement,
                            keywords=annotation.keywords,
                        ))
        
        total_new_items = 0
        for repo_url, repo_commits in commit_items.items():
            commit_data_map = {}
            for commit_hash, items in repo_commits.items():
                if items:
                    # commit_index now contains 4-tuple: (item_id, name, filename, variables)
                    commit_data_map[commit_hash] = (items, scan_result.commit_index[repo_url][commit_hash])
            if not commit_data_map:
                continue
            
            # Directly pass config and repo_url, no need to model_copy
            save_result = await save_data_batch(
                commit_data_map, 
                self.config.lean_retrieve_config, 
                repo_url=repo_url  # Pass repo_url parameter
            )
            repo_name = normalize_repo_url(self._effective_repo_url(repo_url))
            self.logger.info(f"[{repo_name}] Save complete: {save_result['new_items_added']} new items")
            total_new_items += save_result['new_items_added']
        
        if total_new_items == 0:
            self.logger.info("No new annotations were saved")
        
        return len(all_annotations)

    async def _index_only_update(
        self,
        commit_index: Dict[str, Dict[str, List]],
        existing_ids_by_repo: Dict[str, Set[str]]
    ) -> int:
        """Index only update mode"""
        self.logger.info("Index-only mode: updating commit indices")
        
        total_indexed_items = 0
        total_records_added = 0
        
        for repo_url, commits in commit_index.items():
            repo_existing = existing_ids_by_repo.get(repo_url, set())
            filtered_commit_data_map = {}
            
            for commit_hash, items in commits.items():
                # Unpack 4-tuple: (item_id, name, filename, variables) and keep all for commit_index
                annotated_items = [
                    (item_id, name, filename, variables)
                    for item_id, name, filename, variables in items
                    if item_id in repo_existing
                ]
                
                if annotated_items:
                    filtered_commit_data_map[commit_hash] = ([], annotated_items)
                    total_indexed_items += len(annotated_items)
                    self.logger.info(
                        f"[{normalize_repo_url(self._effective_repo_url(repo_url))}] "
                        f"Commit {commit_hash[:8]}: {len(annotated_items)} items to index"
                    )
            
            if not filtered_commit_data_map:
                continue
            
            # Directly pass config and repo_url
            save_result = await save_data_batch(
                filtered_commit_data_map, 
                self.config.lean_retrieve_config,
                repo_url=repo_url  # Pass repo_url parameter
            )
            total_records_added += save_result['total_commit_records_added']
        
        if total_indexed_items == 0:
            self.logger.info("No annotated items found for index update")
            return 0
        
        self.logger.info(f"Updating indices for {total_indexed_items} items total")
        return total_records_added


async def main(
    input_file: Path,
    config_path: Optional[Path] = None,
    orchestrator_id: str = None,
    cli_overrides: Dict[str, Any] = None,
    logger = None
) -> int:
    """Main entry function

    Configuration priority: CLI dot-notation overrides > YAML > defaults

    Args:
        input_file: Input JSONL file path
        config_path: Optional YAML configuration file path
        orchestrator_id: Orchestrator ID
        cli_overrides: CLI overrides from dot-notation arguments
        logger: Logger instance
    """
    if logger is None:
        logger = create_logger()

    # Build configuration: YAML + CLI overrides
    config_dict = load_yaml(config_path) if config_path else {}
    if cli_overrides:
        config_dict = deep_merge(config_dict, cli_overrides)

    # Required parameters
    config_dict['input_file'] = input_file

    config = AnnotationConfig.model_validate(config_dict)
    
    logger.info("Starting Lean Semantic Annotation Pipeline")
    
    pipeline = SemanticAnnotationPipeline(config, logger, orchestrator_id)
    stats = await pipeline.run()
    
    if stats.mode == "index_only":
        logger.info(f"Index update complete: {stats.indexed} items indexed, {stats.duration_sec:.1f}s total")
    else:
        logger.info(f"Annotation complete: {stats.annotated} new annotations, {stats.skipped} skipped, {stats.duration_sec:.1f}s total")
    
    return 0


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Lean Retrieve Database Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build database from input file
  python -m ape.toolkits.retrieve.lean.build --target_repo=https://github.com/leanprover-community/mathlib4.git@@2df2f0150c275ad53cb3c90f7c98ec15a56a1a67 --reference_repo=https://github.com/leanprover-community/mathlib4.git@@79e94a093aff4a60fb1b1f92d9681e407124c2ca@@Mathlib num_processes=2

  python -m ape.toolkits.retrieve.lean.build --target_repo=https://github.com/leanprover-community/mathlib4.git@@2df2f0150c275ad53cb3c90f7c98ec15a56a1a67@@Mathlib
  """
    )

    # Input parameters (input_file or target_repo)
    parser.add_argument("--input_file", type=str, help="Input JSONL file path")
    parser.add_argument(
        "--target_repo",
        type=str,
        help="Target repository in format: repo_url@@commit_hash or repo_url@@commit_hash@@default_target. "
             "Example: git@github.com:user/repo.git@@abc123@@Mathlib"
    )
    parser.add_argument(
        "--reference_repo",
        type=str,
        action='append',
        help="Reference repository in same format as --target_repo. Can be specified multiple times. "
             "Example: --reference_repo git@github.com:leanprover-community/mathlib4.git@@def456@@Mathlib"
    )

    # Configuration
    parser.add_argument("--config", type=Path, help="YAML configuration file path")
    parser.add_argument("--orchestrator_id", type=str, help="Orchestrator ID")
    parser.add_argument("--no_cache", action="store_true", help="Disable phase 1 cache load/save")

    return parser


if __name__ == "__main__":
    console_logger = create_logger()

    parser = create_argument_parser()
    args, remaining_args = parser.parse_known_args()

    # Parse dot-notation CLI overrides
    cli_overrides = parse_cli_args(remaining_args)

    # Process input source
    input_file = None
    temp_file = None

    try:
        if args.target_repo:
            # Use target_repo mode: create temporary JSONL file
            repo_url, commit_hash, default_target = parse_repo_spec(args.target_repo)

            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            temp_file = temp_dir / f"annotation_temp_{commit_hash[:8]}.jsonl"

            with open(temp_file, 'w', encoding='utf-8') as f:
                import json
                record = {
                    "target_workspace": {
                        "name": "target",
                        "commit_hash": commit_hash,
                        "repo_url": repo_url,
                        "default_target": default_target,
                    }
                }
                if default_target:
                    console_logger.info(f"Target: {repo_url}@@{commit_hash}@@{default_target}")
                else:
                    console_logger.info(f"Target: {repo_url}@@{commit_hash} (all files)")

                # Add reference workspaces if provided
                if args.reference_repo:
                    reference_workspaces = []
                    for ref_spec in args.reference_repo:
                        ref_url, ref_commit, ref_default = parse_repo_spec(ref_spec)
                        ref_ws = {
                            "name": ref_url.split("/")[-1].replace(".git", "").lower(),
                            "repo_url": ref_url,
                            "commit_hash": ref_commit,
                            "default_target": ref_default,
                        }
                        reference_workspaces.append(ref_ws)
                        console_logger.info(f"Reference: {ref_url}@@{ref_commit}@@{ref_default or 'all files'}")

                    record["reference_workspaces"] = reference_workspaces

                f.write(json.dumps(record) + "\n")

            input_file = temp_file
            console_logger.info(f"Created temporary input file: {input_file}")
        elif args.input_file:
            input_file = Path(args.input_file)
        else:
            console_logger.error(
                "Either --input_file or --target_repo must be provided"
            )
            sys.exit(1)

        if args.no_cache:
            cli_overrides = dict(cli_overrides or {})
            cli_overrides["use_cache"] = False

        exit_code = asyncio.run(main(
            input_file=input_file,
            config_path=args.config,
            orchestrator_id=args.orchestrator_id,
            cli_overrides=cli_overrides,
            logger=console_logger
        ))
    finally:
        # Ensure temporary file is cleaned up
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
                console_logger.info(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                console_logger.warning(f"Failed to clean up temporary file {temp_file}: {e}")

    sys.exit(exit_code)
