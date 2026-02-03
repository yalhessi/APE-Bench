"""
APE Bench Data Collection

Generalized for any formal language project (Lean, Isabelle, Coq, etc.).
Uses workspace-based architecture aligned with semantic annotation design.
"""

import asyncio
import re
import pickle
from datetime import datetime, timezone
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import pandas as pd
import git
import difflib
from tqdm import tqdm

from ape.utils.logging import create_logger
from ape.utils.file_ops import normalize_repo_url
from ape.toolkits.code.base_provider import LANGUAGE_PROVIDER_REGISTRY
from ..external_benchmarks.github_utils import get_default_target_from_repo

from .config import ApeBenchConfig

if TYPE_CHECKING:
    import logging


# Language to file extension mapping
LANGUAGE_EXTENSIONS = {
    'lean': '.lean',
    'isabelle': '.thy',
    'coq': '.v',
    'python': '.py'
}


def remove_comments_for_language(content: Optional[str], language: str) -> Optional[str]:
    """Remove comments from content based on language using LanguageProvider.

    Args:
        content: Source code content
        language: Language name (e.g., 'lean', 'isabelle', 'coq')

    Returns:
        Content with comments removed, or None if content is None
    """
    if content is None:
        return None

    file_extension = LANGUAGE_EXTENSIONS.get(language.lower())
    if not file_extension:
        return content  # Unknown language, return as-is

    provider_class = LANGUAGE_PROVIDER_REGISTRY.get(file_extension)
    if not provider_class:
        return content  # No provider registered, return as-is

    # Check if the provider has a remove_comments static method
    if not hasattr(provider_class, 'remove_comments'):
        return content  # Provider doesn't support comment removal, return as-is

    return provider_class.remove_comments(content)


def collect_commits(repo_path: Path, config: ApeBenchConfig) -> List[str]:
    """Collect commit hashes with date filtering."""
    repo = git.Repo(repo_path)
    commits = []

    earliest = datetime.strptime(config.earliest_date, "%Y-%m-%d") if config.earliest_date else None
    latest = datetime.strptime(config.latest_date, "%Y-%m-%d") if config.latest_date else None

    count = 0
    for commit in repo.iter_commits('HEAD'):
        if config.max_commits_scan is not None and count >= config.max_commits_scan:
            break

        commit_date = datetime.fromtimestamp(commit.committed_date)

        if earliest and commit_date < earliest:
            continue
        if latest and commit_date > latest:
            continue

        commits.append(commit.hexsha)
        count += 1

    return commits


def process_commit_batch(args: Tuple) -> List[Dict[str, Any]]:
    """Process a batch of commits in separate process."""
    commit_hashes, repo_path, config_dict = args
    repo = git.Repo(repo_path)
    repo_url = config_dict.get('repo_url', '')
    default_target = config_dict.get('default_target')
    language = config_dict.get('language', 'lean')
    results = []

    for commit_hash in commit_hashes:
        try:
            commit = repo.commit(commit_hash)
            if not commit.parents:
                continue

            for parent in commit.parents:
                diffs = parent.diff(commit, create_patch=True)

                for diff in diffs:
                    path_before = diff.a_path
                    path_after = diff.b_path
                    file_path = path_after or path_before

                    # Skip files with wrong extension
                    if not file_path or not file_path.endswith(config_dict['file_extension']):
                        continue

                    # Apply default_target filter if specified
                    if config_dict['filter_prefix']:
                        if not file_path.startswith(config_dict['filter_prefix']):
                            continue

                    # Skip excluded files
                    if file_path in config_dict['excluded_files']:
                        continue

                    # Determine change type
                    change_type = _determine_change_type(path_before, path_after)

                    # Skip deleted files if configured
                    if config_dict['exclude_deleted'] and change_type == 'deleted':
                        continue

                    # Get file contents
                    content_before = _get_file_content(parent, path_before)
                    content_after = _get_file_content(commit, path_after)

                    # Generate diff
                    gold_diff = _generate_diff(
                        content_before or "",
                        content_after or "",
                        Path(f"a/{path_before or 'null'}"),
                        Path(f"b/{path_after or 'null'}")
                    )

                    # Check diff size
                    diff_lines = _calculate_diff_lines(content_before, content_after)
                    if diff_lines < config_dict['min_diff'] or diff_lines > config_dict['max_diff']:
                        continue

                    # Calculate statistics
                    stats = _calc_diff_stats(gold_diff)

                    # Calculate filtered statistics
                    filtered_stats = _calc_filtered_stats_efficient(content_before, content_after, language)

                    # Build record
                    record = {
                        'file_path_before': path_before,
                        'file_path_after': path_after,
                        'content_before': content_before,
                        'content_after': content_after,
                        'gold_diff': gold_diff,
                        'commit_hash': commit.hexsha,
                        'parent_commit_hash': parent.hexsha,
                        'repo_url': repo_url,
                        'default_target': default_target,
                        'language': language,
                        'author': f"{commit.author.name} <{commit.author.email}>",
                        'message': commit.message.strip(),
                        'date': commit.committed_datetime.astimezone(timezone.utc).isoformat(),
                        'toolchain': _get_toolchain(commit, language),
                        'change_type': change_type,
                        'diff_lines': diff_lines,
                        **stats,
                        **filtered_stats
                    }

                    results.append(record)

        except Exception:
            continue

    return results


def _determine_change_type(before: Optional[str], after: Optional[str]) -> str:
    """Determine change type from paths."""
    if before is None and after is not None:
        return 'created'
    elif before is not None and after is None:
        return 'deleted'
    elif before != after:
        return 'renamed'
    else:
        return 'modified'


def _get_file_content(commit: git.Commit, path: Optional[str]) -> Optional[str]:
    """Get file content at commit."""
    if not commit or not path:
        return None
    try:
        blob = commit.tree[path]
        return blob.data_stream.read().decode('utf-8', errors='replace')
    except Exception:
        return None


def _get_toolchain(commit: git.Commit, language: str) -> Optional[str]:
    """Get toolchain/version file content based on language."""
    toolchain_files = {
        'lean': ['lean-toolchain', 'leanpkg.toml'],
        'isabelle': ['ROOT', 'ROOTS'],
        'coq': ['_CoqProject', 'coqc.version']
    }

    files_to_try = toolchain_files.get(language, [])

    for filename in files_to_try:
        try:
            blob = commit.tree[filename]
            return blob.data_stream.read().decode('utf-8').strip()
        except Exception:
            continue

    return None


def _generate_diff(before: str, after: str, fromfile: Path, tofile: Path) -> str:
    """Generate unified diff."""
    before_lines = before.splitlines(keepends=False)
    after_lines = after.splitlines(keepends=False)

    diff = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=str(fromfile),
        tofile=str(tofile),
        lineterm=""
    )

    return "\n".join(diff)


def _calc_diff_stats(diff_text: str) -> Dict[str, int]:
    """Calculate diff statistics."""
    if not diff_text:
        return {
            'added_lines': 0,
            'removed_lines': 0,
            'total_changes': 0,
            'pure_changes': 0,
            'absolute_added_lines': 0
        }

    added = 0
    removed = 0

    for line in diff_text.splitlines():
        if line.startswith('+') and not line.startswith('+++'):
            added += 1
        elif line.startswith('-') and not line.startswith('---'):
            removed += 1

    return {
        'added_lines': added,
        'removed_lines': removed,
        'total_changes': added + removed,
        'pure_changes': max(added, removed),
        'absolute_added_lines': added - removed
    }


def _calculate_diff_lines(content_before: Optional[str], content_after: Optional[str]) -> int:
    """Calculate diff lines counting only added lines, ignoring whitespace-only changes."""
    if content_before is None:
        if content_after is None:
            return 0
        return len([line for line in content_after.splitlines() if line.strip()])

    if content_after is None:
        return 0

    before_lines = [line.rstrip() for line in content_before.splitlines()]
    after_lines = [line.rstrip() for line in content_after.splitlines()]

    diff = difflib.unified_diff(before_lines, after_lines, lineterm="")

    count = 0
    for line in diff:
        if line.startswith('+') and not line.startswith('+++'):
            content = line[1:]
            if content.strip():
                count += 1

    return count


def _calc_filtered_stats_efficient(before: Optional[str], after: Optional[str], language: str) -> Dict[str, int]:
    """Calculate statistics after filtering, without storing the filtered diff."""
    filtered_before = remove_comments_for_language(before, language)
    filtered_after = remove_comments_for_language(after, language)

    if filtered_before is None and filtered_after is None:
        return {
            'filtered_added_lines': 0,
            'filtered_removed_lines': 0,
            'filtered_total_changes': 0,
            'filtered_pure_changes': 0,
            'filtered_absolute_added_lines': 0,
            'filtered_diff_lines': 0
        }

    filtered_diff = _generate_diff(
        filtered_before or "",
        filtered_after or "",
        Path("a/filtered"),
        Path("b/filtered")
    )

    stats = _calc_diff_stats(filtered_diff)

    return {
        'filtered_added_lines': stats['added_lines'],
        'filtered_removed_lines': stats['removed_lines'],
        'filtered_total_changes': stats['total_changes'],
        'filtered_pure_changes': stats['pure_changes'],
        'filtered_absolute_added_lines': stats['absolute_added_lines'],
        'filtered_diff_lines': len(filtered_diff.splitlines())
    }


def _analyze_modification_quality_single(row_data: Dict[str, Any], min_edit_distance: int,
                                         max_scattered_ratio: float, scattered_threshold: int,
                                         language: str) -> bool:
    """Analyze modification quality for a single row."""
    content_before = row_data.get('content_before', '')
    content_after = row_data.get('content_after', '')

    if not content_before or not content_after:
        return True

    before_clean = remove_comments_for_language(content_before, language) or ''
    after_clean = remove_comments_for_language(content_after, language) or ''

    before_processed = ''.join(before_clean.split())
    after_processed = ''.join(after_clean.split())

    if before_processed == after_processed:
        return False

    total_changes = row_data.get('filtered_total_changes', 0)
    if total_changes < min_edit_distance:
        return False

    gold_diff = row_data.get('gold_diff', '')
    if gold_diff:
        scattered_ratio = _calculate_scattered_ratio_standalone(gold_diff, scattered_threshold)
        return scattered_ratio < max_scattered_ratio

    return True


def _calculate_scattered_ratio_standalone(diff_text: str, scattered_threshold: int) -> float:
    """Calculate ratio of scattered modifications in diff."""
    if not diff_text:
        return 0.0

    lines = diff_text.splitlines()
    change_lines = [line for line in lines
                    if line.startswith('+') and not line.startswith('+++') or
                    line.startswith('-') and not line.startswith('---')]

    if not change_lines:
        return 0.0

    scattered_changes = 0
    current_block_size = 1

    for i in range(1, len(change_lines)):
        prev_line = change_lines[i - 1]
        curr_line = change_lines[i]

        if prev_line[0] == curr_line[0]:
            current_block_size += 1
        else:
            if current_block_size <= scattered_threshold:
                scattered_changes += current_block_size
            current_block_size = 1

    if current_block_size <= scattered_threshold:
        scattered_changes += current_block_size

    total_changes = len(change_lines)
    return scattered_changes / total_changes if total_changes > 0 else 0.0


def _analyze_modification_quality_batch(batch_data: List[Tuple[int, Dict[str, Any]]],
                                        min_edit_distance: int, max_scattered_ratio: float,
                                        scattered_threshold: int, language: str) -> List[int]:
    """Process a batch of rows for modification quality analysis."""
    valid_indices = []

    for idx, row_data in batch_data:
        try:
            if _analyze_modification_quality_single(row_data, min_edit_distance,
                                                    max_scattered_ratio, scattered_threshold, language):
                valid_indices.append(idx)
        except Exception:
            continue

    return valid_indices


class DataCollector:
    """Data collector for any formal language project."""

    def __init__(self, config: ApeBenchConfig, config_hash: str, logger: Optional['logging.LoggerAdapter'] = None):
        self.config = config
        self.config_hash = config_hash
        self.default_target: Optional[str] = None
        if logger is None:
            logger = create_logger()
        self.logger = logger

        # Initialize cache system
        self.cache_dir = config.dataset_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_repo_path(self) -> Path:
        """Get local repository path using workspace_config standard structure"""
        repo_name = normalize_repo_url(self.config.repo_url)
        return self.config.workspace_config.get_repo_source_path(repo_name)

    async def ensure_repo_cloned(self) -> Path:
        """Ensure repository is cloned to standard location using workspace_config structure"""
        repo_path = self.get_repo_path()

        if repo_path.exists():
            self.logger.info(f"Repository exists: {repo_path}")
            return repo_path

        self.logger.info(f"Cloning {self.config.repo_url} to {repo_path}")
        repo_path.parent.mkdir(parents=True, exist_ok=True)

        await asyncio.to_thread(git.Repo.clone_from, self.config.repo_url, str(repo_path))

        self.logger.info(f"Cloned: {repo_path}")
        return repo_path

    def _get_cache_path(self, stage: str) -> Path:
        """Get cache file path for a specific stage."""
        return self.cache_dir / f"{stage}_{self.config_hash}.pkl"

    def _save_cache(self, data: pd.DataFrame, stage: str) -> None:
        """Save data to cache for a specific stage."""
        cache_path = self._get_cache_path(stage)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            self.logger.info(f"Cached {len(data)} records to {cache_path.name}")
        except Exception as e:
            self.logger.warning(f"Failed to save cache for {stage}: {e}")

    def _load_cache(self, stage: str) -> Optional[pd.DataFrame]:
        """Load data from cache for a specific stage."""
        cache_path = self._get_cache_path(stage)
        try:
            if cache_path.exists():
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                self.logger.info(f"Loaded {len(data)} records from cache {cache_path.name}")
                return data
        except Exception as e:
            self.logger.warning(f"Failed to load cache for {stage}: {e}")
        return None

    def _check_cache_sequence(self) -> Tuple[Optional[pd.DataFrame], str]:
        """Check cache from latest stage backwards, return data and stage."""
        # If verification is enabled, include verified stage
        if self.config.enable_verification:
            stages = ["final", "verified", "filtered", "raw"]
        else:
            stages = ["final", "filtered", "raw"]

        for stage in stages:
            data = self._load_cache(stage)
            if data is not None:
                return data, stage

        return None, "none"

    async def collect_and_process_data(self) -> pd.DataFrame:
        """Collect and process commit data with caching support."""
        self.logger.info(f"Starting data collection with config hash: {self.config_hash}")

        if self.config.language == "lean" and self.default_target is None:
            repo_path = await self.ensure_repo_cloned()
            default_target = get_default_target_from_repo(repo_path)
            if not default_target:
                raise ValueError(
                    "default_target is required for Lean datasets and could not be inferred from lakefile. "
                    "Ensure the repository has a lakefile with default target."
                )
            self.default_target = default_target
            self.logger.info(f"Detected default_target: {self.default_target}")

        # Check cache sequence from latest to earliest
        cached_data, cache_stage = self._check_cache_sequence()

        if cached_data is not None:
            self.logger.info(f"Using cached data from {cache_stage} stage")

            if cache_stage == "final":
                return cached_data
            elif cache_stage == "verified":
                # Already verified, skip to final
                df = cached_data
                df = df.reset_index(drop=True)
                self._save_cache(df, "final")
                return df
            elif cache_stage == "filtered":
                df = cached_data
            elif cache_stage == "raw":
                df = cached_data
                df = await self._apply_filters(df)
                self._save_cache(df, "filtered")

                if df.empty:
                    self.logger.warning("No records passed filtering")
                    return df
        else:
            df = await self._collect_raw_data()
            if df.empty:
                return df

            self._save_cache(df, "raw")

            df = await self._apply_filters(df)
            self._save_cache(df, "filtered")

            if df.empty:
                self.logger.warning("No records passed filtering")
                return df

        # Apply latest_num_data selection BEFORE verification
        if self.config.latest_num_data is not None:
            self.logger.info(f"Selecting latest {self.config.latest_num_data} records before verification")
            df = df.sort_values('date', ascending=False).head(self.config.latest_num_data)

        # Verify commits (only on selected data)
        if self.config.enable_verification:
            df = await self._verify_commits(df)
            self._save_cache(df, "verified")

        # Final processing
        df = df.reset_index(drop=True)
        self._save_cache(df, "final")

        return df

    async def _collect_raw_data(self) -> pd.DataFrame:
        """Collect raw commit data."""
        repo_path = await self.ensure_repo_cloned()
        default_target = self.default_target if self.config.language == "lean" else None

        self.logger.info("Collecting commits...")
        commit_hashes = collect_commits(repo_path, self.config)

        if not commit_hashes:
            self.logger.warning("No commits found")
            return pd.DataFrame()

        self.logger.info(f"Processing {len(commit_hashes)} commits...")

        # Create batches efficiently
        batch_size = max(10, len(commit_hashes) // (self.config.max_cpu_limit) * 2)
        batches = [commit_hashes[i:i + batch_size] for i in range(0, len(commit_hashes), batch_size)]

        # Prepare config dict for multiprocessing
        filter_prefix = f"{default_target}/" if default_target else ""
        excluded_files = [f"{default_target}{self.config.file_extension}"] if default_target else []

        config_dict = {
            'filter_prefix': filter_prefix,
            'excluded_files': excluded_files,
            'exclude_deleted': self.config.exclude_deleted_files,
            'min_diff': self.config.min_diff_lines,
            'max_diff': self.config.max_diff_lines,
            'repo_url': self.config.repo_url,
            'default_target': default_target,
            'file_extension': self.config.file_extension,
            'language': self.config.language
        }

        # Process batches in parallel
        all_records = []

        with ProcessPoolExecutor(max_workers=self.config.max_cpu_limit) as executor:
            futures = {
                executor.submit(process_commit_batch, (batch, repo_path, config_dict)): i
                for i, batch in enumerate(batches)
            }

            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing commits"):
                try:
                    records = future.result()
                    all_records.extend(records)
                except Exception as e:
                    self.logger.error(f"Batch processing failed: {e}")

        if not all_records:
            self.logger.warning("No file modifications found")
            return pd.DataFrame()

        df = pd.DataFrame(all_records)
        self.logger.info(f"Collected {len(df)} file modifications")

        return df

    async def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all filters to the dataframe."""
        if df.empty:
            return df

        original_count = len(df)
        self.logger.info(f"Applying filters to {original_count} records...")

        # 1. Commit type filter
        if 'message' in df.columns:
            def extract_commit_type(msg: str) -> Optional[str]:
                if not msg:
                    return None
                match = re.match(r'^(\w+)[\s:(/]', msg)
                if match:
                    commit_type = match.group(1).lower()
                    return self.config.commit_typo_map.get(commit_type, commit_type)
                return None

            pre_filter_count = len(df)
            df['commit_type'] = df['message'].apply(extract_commit_type)
            df = df[df['commit_type'].isin(self.config.allowed_commit_types)]
            post_filter_count = len(df)
            self.logger.info(f"Commit type filter: {pre_filter_count} → {post_filter_count} records "
                             f"({pre_filter_count - post_filter_count} filtered out)")

        # 2. Content quality filter
        pre_filter_count = len(df)
        df = df[
            (df['filtered_pure_changes'] > 0) &
            (
                    (df['filtered_absolute_added_lines'] > 0) |
                    (
                            (df['filtered_added_lines'] > self.config.min_absolute_added_lines) &
                            (df['filtered_absolute_added_lines'] * self.config.max_more_removed_line_ratio +
                             df['filtered_added_lines'] > 0)
                    )
            )
            ]
        post_filter_count = len(df)
        self.logger.info(f"Content quality filter: {pre_filter_count} → {post_filter_count} records "
                         f"({pre_filter_count - post_filter_count} filtered out)")

        # 3. Non-repeating modifications filter
        def check_non_repeating(diff: str) -> bool:
            if not diff:
                return True

            lines = diff.splitlines()
            threshold = self.config.non_repeating_threshold

            additions = [line[1:].strip() for line in lines
                         if line.startswith('+') and not line.startswith('+++') and line[1:].strip()]
            if additions and len(set(additions)) / len(additions) < threshold:
                return False

            deletions = [line[1:].strip() for line in lines
                         if line.startswith('-') and not line.startswith('---') and line[1:].strip()]
            if deletions and len(set(deletions)) / len(deletions) < threshold:
                return False

            return True

        if 'gold_diff' in df.columns:
            pre_filter_count = len(df)
            df = df[df['gold_diff'].apply(check_non_repeating)]
            post_filter_count = len(df)
            self.logger.info(f"Non-repeating modifications filter: {pre_filter_count} → {post_filter_count} records "
                             f"({pre_filter_count - post_filter_count} filtered out)")

        # 4. Enhanced edit distance filter
        df = await self._apply_edit_distance_filter(df)

        filtered_count = len(df)
        self.logger.info(
            f"All filters complete: {original_count} → {filtered_count} records "
            f"({(original_count - filtered_count) / original_count * 100:.1f}% total filtered out)"
        )

        return df

    async def _verify_commits(self, df: pd.DataFrame) -> pd.DataFrame:
        """Verify commits can build successfully (language-specific, optional)."""
        if df.empty:
            return df

        # Only verify if enabled and language supports it
        if not self.config.enable_verification:
            self.logger.info("Verification disabled, skipping commit verification")
            return df

        if self.config.language == 'lean':
            return await self._verify_lean_commits(df)
        else:
            self.logger.info(f"Verification not implemented for {self.config.language}, skipping")
            return df

    async def _verify_lean_commits(self, df: pd.DataFrame) -> pd.DataFrame:
        """Verify Lean commits can build successfully."""
        try:
            from ape.toolkits.execute.lean.build import BatchBuilder
            from ape.toolkits.execute.lean.config import LeanVerifyToolConfig

            unique_commits = df['commit_hash'].unique().tolist()
            toolchain_series = df[df['toolchain'].notna()]['toolchain']
            toolchains = list(toolchain_series.unique())

            self.logger.info(f"Verifying {len(unique_commits)} unique Lean commits with {self.config.lean_verify_num_processes} processes...")

            # Convert commit hashes to the format expected by build_commits
            commit_entries = [{"commit_hash": commit} for commit in unique_commits]

            lean_config = LeanVerifyToolConfig(
                num_processes=self.config.lean_verify_num_processes
            )
            batch_builder = BatchBuilder(lean_config, self.logger)
            build_results = await batch_builder.build_commits(
                commit_entries,
                toolchains=toolchains
            )

            successful_commits = set()
            for result in build_results.get('task_results', []):
                if result.get('success', False):
                    successful_commits.add(result.get('commit_hash'))

            self.logger.info(
                f"Lean compilation successful: {len(successful_commits)}/{len(unique_commits)} commits"
            )

            verified_df = df[df['commit_hash'].isin(successful_commits)]

            if verified_df.empty:
                self.logger.warning("No commits passed Lean compilation verification")
            else:
                self.logger.info(f"Final dataset: {len(verified_df)} records from verified commits")

            return verified_df

        except ImportError as e:
            self.logger.warning(f"Lean verification not available: {e}")
            return df

    async def _apply_edit_distance_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply enhanced edit distance filter with scattered modification analysis."""
        if df.empty:
            return df

        original_count = len(df)
        self.logger.info(f"Starting edit distance filter on {original_count} records...")

        rows_data = []
        for idx, row in df.iterrows():
            rows_data.append((idx, row.to_dict()))

        batch_size = max(50, len(rows_data) // (self.config.max_cpu_limit) * 2)
        batches = [rows_data[i:i + batch_size] for i in range(0, len(rows_data), batch_size)]

        valid_indices = set()
        language = self.config.language

        with ProcessPoolExecutor(max_workers=self.config.max_cpu_limit) as executor:
            futures = {
                executor.submit(
                    _analyze_modification_quality_batch,
                    batch,
                    self.config.min_edit_distance,
                    self.config.edit_distance_max_scattered_ratio,
                    self.config.edit_distance_scattered_threshold,
                    language
                ): i for i, batch in enumerate(batches)
            }

            for future in tqdm(as_completed(futures), total=len(futures), desc="Edit distance analysis"):
                try:
                    batch_valid_indices = future.result()
                    valid_indices.update(batch_valid_indices)
                except Exception as e:
                    self.logger.error(f"Edit distance batch processing failed: {e}")

        filtered_df = df.loc[df.index.isin(valid_indices)]

        filtered_count = len(filtered_df)
        self.logger.info(f"Edit distance filter: {original_count} → {filtered_count} records "
                         f"({original_count - filtered_count} filtered out)")

        return filtered_df
