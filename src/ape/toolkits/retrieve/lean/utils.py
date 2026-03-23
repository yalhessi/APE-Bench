"""
Lean-specific utility functions
"""

import asyncio
import json
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple, TYPE_CHECKING
from tqdm import tqdm

from .models import LeanItem
from .config import LeanRetrieveToolConfig
from ape.toolkits.retrieve.core.storage import (
    init_chromadb,
    compute_embeddings,
    add_to_chromadb_batched,
    load_indexed_ids,
    append_indexed_ids,
    load_commit_index_ids,
    append_commit_index
)

if TYPE_CHECKING:
    import logging
    from .tools import LeanRetrieveToolsProvider


def normalize_keyword(keyword: str) -> str:
    """Normalize keyword"""
    norm = keyword.strip().lower()
    # Remove plural form
    if len(norm) > 4 and norm.endswith('s') and not norm.endswith('es'):
        norm = norm[:-1]
    return norm


def metadata_to_item(metadata: Dict[str, Any]) -> LeanItem:
    """Convert ChromaDB metadata to LeanItem"""
    name = metadata.get("name")
    if name == "":
        name = None
    fullname = metadata.get("fullname")
    if fullname == "":
        fullname = None
    variables_raw = metadata.get("variables", [])
    variables: List[str] = []
    if isinstance(variables_raw, list):
        variables = [str(v) for v in variables_raw if v is not None]
    elif isinstance(variables_raw, str):
        if variables_raw.strip():
            try:
                decoded = json.loads(variables_raw)
                if isinstance(decoded, list):
                    variables = [str(v) for v in decoded if v is not None]
                else:
                    variables = [variables_raw]
            except Exception:
                variables = [variables_raw]

    return LeanItem(
        item_id=metadata["item_id"],
        kind=metadata["kind"],
        name=name,
        fullname=fullname,
        variables=variables,
        signature=metadata["signature"],
        proof=metadata["proof"],
        filename=metadata["filename"],
        span_start=metadata["span_start"],
        span_end=metadata["span_end"],
        semantic=metadata.get("semantic", ""),
        keywords=metadata.get("keywords", ""),
    )


def item_to_metadata(item: LeanItem) -> Dict[str, Any]:
    """Convert LeanItem to ChromaDB metadata"""
    return {
        "item_id": item.item_id,
        "kind": item.kind,
        "name": item.name or "",
        "fullname": item.fullname or "",
        "variables": json.dumps(item.variables, ensure_ascii=False) if item.variables else "",
        "signature": item.signature,
        "proof": item.proof,
        "filename": item.filename,
        "span_start": item.span_start,
        "span_end": item.span_end,
        "semantic": item.semantic,
        "keywords": item.keywords,
    }


def _collect_unique_items(commit_data_map: Dict[str, Tuple[List[LeanItem], List[Tuple[str, Optional[str], str, List[str]]]]]) -> List[LeanItem]:
    """Collect and deduplicate all items"""
    all_items = []
    seen_item_ids = set()

    for commit_hash, (annotated_items, _) in commit_data_map.items():
        for item in annotated_items:
            if item.item_id not in seen_item_ids:
                all_items.append(item)
                seen_item_ids.add(item.item_id)

    return all_items




async def _fetch_missing_metadata(
    missing_ids: Set[str],
    collection,
    logger,
    batch_size: int = 512
) -> Dict[str, LeanItem]:
    """Fetch missing metadata from ChromaDB"""
    if not missing_ids:
        logger.info("No missing metadata to fetch from ChromaDB")
        return {}

    missing_ids_list = list(missing_ids)
    total_items = len(missing_ids_list)
    logger.info(f"Fetching metadata for {total_items} missing items from ChromaDB...")

    fetched_items = {}
    total_fetched_count = 0

    if total_items <= batch_size:
        data = await asyncio.to_thread(lambda: collection.get(ids=missing_ids_list))

        if data and data.get('ids') and data.get('metadatas'):
            for item_id, metadata in zip(data['ids'], data['metadatas']):
                if not item_id or not metadata:
                    continue
                try:
                    item = metadata_to_item(metadata)
                    fetched_items[item_id] = item
                    total_fetched_count += 1
                except Exception:
                    continue
    else:
        num_batches = (total_items + batch_size - 1) // batch_size
        logger.info(f"Fetching from ChromaDB in {num_batches} batches of size {batch_size}")

        for i in range(0, total_items, batch_size):
            end_idx = min(i + batch_size, total_items)
            batch_ids = missing_ids_list[i:end_idx]

            try:
                data = await asyncio.to_thread(lambda: collection.get(ids=batch_ids))

                if data and data.get('ids') and data.get('metadatas'):
                    for item_id, metadata in zip(data['ids'], data['metadatas']):
                        if not item_id or not metadata:
                            continue
                        try:
                            item = metadata_to_item(metadata)
                            fetched_items[item_id] = item
                            total_fetched_count += 1
                        except Exception:
                            continue
            except Exception as e:
                logger.warning(f"Failed to fetch batch {i//batch_size + 1}/{num_batches}: {e}")
                continue

    logger.info(f"Successfully fetched metadata for {total_fetched_count}/{total_items} items")
    return fetched_items




async def _update_commit_indices(
    commit_data_map: Dict[str, Tuple[List[LeanItem], List[Tuple[str, Optional[str], str, List[str]]]]],
    id_to_data: Dict[str, LeanItem],
    config: LeanRetrieveToolConfig,
    logger,
    repo_url: str
) -> int:
    """Update commit indices

    Args:
        commit_data_map: Dict mapping commit_hash to (annotated_items, commit_items)
            - commit_items: List of (item_id, name, filename, variables) tuples with per-commit paths
    """
    total_records = 0
    commit_index_dir = config.get_commit_index_dir(repo_url)

    for i, (commit_hash, (_, commit_items)) in enumerate(commit_data_map.items(), 1):
        commit_file = commit_index_dir / f"{commit_hash}.jsonl"
        commit_file.parent.mkdir(parents=True, exist_ok=True)

        # Use core storage function
        existing_ids = await load_commit_index_ids(commit_file)

        # Build new records - now includes filename from commit_items
        new_records = []
        for item_id, name, filename, variables in commit_items:
            if item_id in existing_ids:
                continue
            data = id_to_data.get(item_id)
            if not data:
                continue
            new_records.append({
                "item_id": item_id,
                "name": name or data.name,
                "fullname": data.fullname or "",
                "keywords": data.keywords,
                "filename": filename,  # Add per-commit filename to commit index
                "variables": variables or data.variables,
            })

        # Use core storage function
        if new_records:
            await append_commit_index(commit_file, new_records)
            total_records += len(new_records)

        logger.info(f"[{i}/{len(commit_data_map)}] Commit {commit_hash[:8]}: {len(new_records)} new records")

    return total_records


async def save_data_batch(
    commit_data_map: Dict[str, Tuple[List[LeanItem], List[Tuple[str, Optional[str], str, List[str]]]]],
    config: LeanRetrieveToolConfig,
    repo_url: str,
    logger: Optional['logging.LoggerAdapter'] = None
) -> Dict[str, Any]:
    """
    Batch save annotated data for multiple commits

    Args:
        commit_data_map: Dict mapping commit_hash to (annotated_items, commit_items)
            - annotated_items: List of LeanItem with full annotation data
            - commit_items: List of (item_id, name, filename, variables) tuples for commit index
                          filename is the per-commit file path (relative to default_target)
        config: LeanRetrieveToolConfig instance
        repo_url: Repository URL
        logger: Logger instance

    Returns:
        Dict with statistics about saved data
    """
    from ape.utils.logging import create_logger

    logger = logger or create_logger()

    storage_dir = config.get_storage_dir(repo_url)
    commit_index_dir = config.get_commit_index_dir(repo_url)
    storage_dir.mkdir(parents=True, exist_ok=True)
    commit_index_dir.mkdir(parents=True, exist_ok=True)

    # Initialize ChromaDB
    client, collection = await init_chromadb(storage_dir, config.collection_name)

    # Collect and filter new items
    all_items = _collect_unique_items(commit_data_map)
    annotated_ids_file = config.get_annotated_ids_file(repo_url)
    existing_ids = await load_indexed_ids(annotated_ids_file)
    to_add = [item for item in all_items if item.item_id not in existing_ids]

    # Compute embeddings and write to ChromaDB
    successful_items = []
    if to_add:
        texts = [item.semantic for item in to_add]
        embeddings = await compute_embeddings(
            texts,
            config.embedding_model,
            config.batch_size,
            logger
        )

        if embeddings:
            ids = [item.item_id for item in to_add]
            metadatas = [item_to_metadata(item) for item in to_add]
            documents = texts

            await add_to_chromadb_batched(
                ids, embeddings, metadatas, documents,
                collection, config.batch_size, logger
            )

            successful_items = to_add

            # Update annotated IDs file using core storage function
            annotated_ids_file = config.get_annotated_ids_file(repo_url)
            await append_indexed_ids(annotated_ids_file, ids)

    # Build complete id mapping
    id_to_data = {item.item_id: item for item in all_items}

    # Fill in missing metadata
    # commit_items is now List[(item_id, name, filename, variables)]
    missing_ids = {
        item_id
        for _, (_, commit_items) in commit_data_map.items()
        for item_id, _, _, _ in commit_items
        if item_id not in id_to_data
    }

    fetched_items = await _fetch_missing_metadata(missing_ids, collection, logger, config.batch_size)
    id_to_data.update(fetched_items)

    # Update commit indices
    total_records = await _update_commit_indices(commit_data_map, id_to_data, config, logger, repo_url)

    return {
        "new_items_added": len(successful_items),
        "total_items": len(all_items),
        "total_commit_records_added": total_records,
        "commits_processed": len(commit_data_map),
    }


def create_lean_retrieve_tools(
    workspaces: List[Dict[str, Any]],
    config: Optional[LeanRetrieveToolConfig] = None,
    logger: Optional['logging.LoggerAdapter'] = None
) -> 'LeanRetrieveToolsProvider':
    """Create LeanRetrieveToolsProvider with multiple workspaces.

    Args:
        workspaces: List of workspace configuration dictionaries.
                   First workspace becomes target, rest become references.
                   Each dict should contain:
                   - repo_url (str): Git repository URL
                   - commit_hash (str): Git commit hash
                   - default_target (str, optional): Target subdirectory filter (e.g., 'Mathlib')
                   - name (str, optional): Workspace name (auto-generated from repo_url if not provided)
                   - toolchain (str, optional): Lean toolchain version
                   - blocked_path_patterns (List[str], optional): Paths completely blocked from access
                   - read_only_path_patterns (List[str], optional): Read-only paths (write blocked)
                   - no_read_path_patterns (List[str], optional): Write-only paths (read blocked)

        config: Optional LeanRetrieveToolConfig instance.
        logger: Optional logger instance.

    Returns:
        LeanRetrieveToolsProvider instance configured with all workspaces.

    Access Control:
        - blocked_path_patterns: Files matching these patterns will be filtered from search results
        - no_read_path_patterns: Files matching these patterns will be filtered from search results
        - read_only_path_patterns: Does not affect search results (only affects write operations)

        Patterns support glob syntax (e.g., "*.lean", "Mathlib/Data/**") and are matched
        relative to workspace root, or absolute paths for exact file matching.

    Example:
        >>> workspaces = [
        ...     {
        ...         "repo_url": "https://github.com/leanprover-community/mathlib4.git",
        ...         "commit_hash": "aa1fd78da07d73daef2fee4e01722ef00e47c0f6",
        ...         "default_target": "Mathlib",
        ...         "blocked_path_patterns": ["Mathlib/Internal/**"],  # Block internal files
        ...         "no_read_path_patterns": ["Mathlib/Tactic/Private/**"],  # Hide private tactics
        ...     },
        ...     {
        ...         "repo_url": "https://github.com/leanprover-community/mathlib4.git",
        ...         "commit_hash": "2df2f0150c275ad53cb3c90f7c98ec15a56a1a67",
        ...         "default_target": "Mathlib",
        ...         "name": "mathlib4",  # Custom reference name
        ...     },
        ... ]
        >>> provider = create_lean_retrieve_tools(workspaces)
    """
    from ape.utils.logging import create_logger
    from ape.tasks.models import WorkspaceInfo, GitWorkspaceSource
    from .tools import LeanRetrieveToolsProvider

    if not workspaces:
        raise ValueError("At least one workspace must be provided")

    if config is None:
        config = LeanRetrieveToolConfig()

    if logger is None:
        logger = create_logger()

    def _create_workspace_info(ws_config: Dict[str, Any], is_target: bool) -> WorkspaceInfo:
        """Create WorkspaceInfo from configuration dictionary."""
        # Required fields
        repo_url = ws_config.get("repo_url")
        commit_hash = ws_config.get("commit_hash")

        if not repo_url or not commit_hash:
            raise ValueError(f"Workspace config must contain 'repo_url' and 'commit_hash': {ws_config}")

        # Auto-generate name if not provided
        if is_target:
            name = ws_config.get("name", "target")
        else:
            default_name = repo_url.split('/')[-1].replace('.git', '').lower()
            name = ws_config.get("name", default_name)

        # Dummy path (not actually used for retrieval)
        path = Path(f"/tmp/dummy_ws_{name}")

        # Create WorkspaceInfo with all fields
        return WorkspaceInfo(
            name=name,
            path=path,
            source=GitWorkspaceSource(
                commit_hash=commit_hash,
                repo_url=repo_url,
            ),
            default_target=ws_config.get("default_target"),
            toolchain=ws_config.get("toolchain"),
            blocked_path_patterns=ws_config.get("blocked_path_patterns", []),
            read_only_path_patterns=ws_config.get("read_only_path_patterns", []),
            no_read_path_patterns=ws_config.get("no_read_path_patterns", []),
        )

    # First workspace is target
    target_workspace = _create_workspace_info(workspaces[0], is_target=True)

    # Rest are references (empty list if no references)
    reference_workspaces = [
        _create_workspace_info(ws_config, is_target=False)
        for ws_config in workspaces[1:]
    ]

    # Create mock task
    class MockTask:
        def __init__(self, target_ws, ref_ws):
            self.target_workspace = target_ws
            self.scratch_workspace = None
            self.reference_workspaces = ref_ws if ref_ws else None

    mock_task = MockTask(target_workspace, reference_workspaces)

    # Create a BaseScaffoldConfig with the LeanRetrieveToolConfig
    from ape.scaffolds.config import BaseScaffoldConfig, BaseToolsConfig

    tools_config = BaseToolsConfig(lean_retrieve=config)
    scaffold_config = BaseScaffoldConfig(
        scaffold_type="lean_retrieve_test",
        tools_config=tools_config,
    )

    # Create provider
    provider = LeanRetrieveToolsProvider(
        task=mock_task,
        config=scaffold_config,
        logger=logger
    )

    return provider
