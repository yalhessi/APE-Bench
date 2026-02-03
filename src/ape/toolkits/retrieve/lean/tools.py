"""
Lean Retrieve Tool (commit scope)

Return data aligned with MajorDecl field + semantic.
"""

import asyncio
import re
import traceback
from typing import Dict, Any, Optional, Annotated, List, TYPE_CHECKING, Union
from pathlib import Path

from fastmcp import FastMCP
from pydantic import Field

from ape.utils.logging import create_logger
from ape.toolkits.file_system.utils import glob_to_regex
from .config import LeanRetrieveToolConfig
from .backend import LeanRetrieveBackend
from ape.toolkits.base import BaseToolsProvider

if TYPE_CHECKING:
    import logging
    from ape.tasks.models import WorkspaceInfo
    from ape.tasks.base import BaseTask


class LeanRetrieveToolsProvider(BaseToolsProvider):
    """
    Lean retrieve tool, providing unified search for Lean declarations with multiple search modes, supporting multi-workspace search.
    """

    SUPPORTED_TOOLS = ["lean_retrieve"]

    def __init__(
        self,
        task: Optional["BaseTask"] = None,
        config: Optional[Any] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        confirmation_bridge: Optional[Any] = None,
        is_cli_mode: bool = False,
    ):
        """Initialize search tool"""
        # Call parent constructor
        super().__init__(
            task=task,
            config=config,
            logger=logger,
            confirmation_bridge=confirmation_bridge,
            is_cli_mode=is_cli_mode,
        )

        # Override logger if not provided
        if not self.logger:
            self.logger = create_logger()

        # Extract tool configuration
        self.tool_config = config.tools_config.lean_retrieve

        # Extract paths for convenience
        self.target_workspace = self.task.target_workspace.target_path.resolve() if self.task.target_workspace else None
        self.scratch_workspace = self.task.scratch_workspace.path.resolve() if self.task.scratch_workspace else None

        # Multi-workspace support: initialize backends dictionary
        # backends structure: {'target': backend, 'reference/mathlib4': backend, ...}
        # - key: Workspace identifier in new workspace/ directory format
        # - value: LeanRetrieveBackend instance (internal use repo_name to access database)
        self.backends: Dict[str, LeanRetrieveBackend] = {}

        # Initialize target workspace backend (pass default_target)
        # Important: only create backend when target workspace has Git information
        # If user provides local path (no Git information), backends will not contain 'target'
        if self.task.target_workspace and self.task.target_workspace.commit_hash:
            target_backend = LeanRetrieveBackend(
                config=self.tool_config,
                commit_hash=self.task.target_workspace.commit_hash,
                repo_url=self.task.target_workspace.repo_url,
                default_target=self.task.target_workspace.default_target,
                logger=self.logger
            )
            self.backends['target'] = target_backend
        elif self.task.target_workspace:
            self.logger.info(
                "Target workspace has no Git information (local path mode) - "
                "LeanRetrieve tools will not be available for target workspace"
            )

        # Initialize reference workspaces backends (pass default_target)
        if self.task.reference_workspaces:
            for ws_info in self.task.reference_workspaces:
                if not ws_info or not hasattr(ws_info, 'name') or not hasattr(ws_info, 'commit_hash') or not hasattr(ws_info, 'repo_url'):
                    self.logger.warning(f"Skipping invalid WorkspaceInfo")
                    continue

                # Create backend instance (pass default_target)
                # Backend will extract repo_name from repo_url and access corresponding database
                ref_backend = LeanRetrieveBackend(
                    config=self.tool_config,
                    commit_hash=ws_info.commit_hash,
                    repo_url=ws_info.repo_url,
                    default_target=ws_info.default_target,
                    logger=self.logger
                )

                # Use new workspace directory format as backend_key
                backend_key = f"reference/{ws_info.name}"

                # Check for duplicates
                if backend_key in self.backends:
                    raise ValueError(f"Duplicate reference workspace: '{ws_info.name}'")

                self.backends[backend_key] = ref_backend

    def _matches_patterns(self, relative_path: str, patterns: Optional[List[str]]) -> bool:
        """Return True when path matches any pattern."""
        if not patterns:
            return False

        for pattern in patterns:
            if not pattern:
                continue
            try:
                if re.match(glob_to_regex(pattern), relative_path):
                    return True
            except Exception:
                continue

        return False

    def _should_filter_result(self, filename: str, workspace: str) -> bool:
        """Check if result should be filtered (based on workspace access patterns)."""
        workspace_info = None

        if workspace == 'target':
            workspace_info = self.task.target_workspace
        elif workspace.startswith('reference/'):
            parts = workspace.split('/', 1)
            if len(parts) == 2:
                ref_name = parts[1].lower()
                for ref_ws in self.task.reference_workspaces or []:
                    if ref_ws.name == ref_name:
                        workspace_info = ref_ws
                        break

        if not workspace_info:
            return False

        no_read_paths = workspace_info.no_read_path_patterns
        blocked_paths = workspace_info.blocked_path_patterns

        if not no_read_paths and not blocked_paths:
            return False

        # commit_index filename is repo-root relative
        relative_path = filename

        if self._matches_patterns(relative_path, blocked_paths):
            self.logger.debug(f"Filtering result from blocked path: {filename}")
            return True

        if self._matches_patterns(relative_path, no_read_paths):
            self.logger.debug(f"Filtering result from no-read path: {filename}")
            return True

        return False

    async def lean_retrieve_impl(
        self,
        workspace: Optional[str] = None,
        natural_language_query: Optional[str] = None,
        lean_name: Optional[str] = None,
        keywords: Optional[str] = None,
        limit: int = 10,
        include_def_proof: bool = False,
        include_theorem_proof: bool = False
    ) -> Dict[str, Any]:
        """Core implementation of unified Lean retrieval. Can be called directly or via MCP.

        Supports combining multiple search modes with automatic result deduplication.

        Args:
            workspace: Workspace to search in (e.g., "target", "reference/mathlib4"). None = search all.
            natural_language_query: Natural language description for semantic search.
            lean_name: Exact or partial Lean name for name search.
            keywords: Comma-separated keywords for keyword search.
            limit: Maximum number of results to return.
            include_def_proof: Include proof/implementation for definitions.
            include_theorem_proof: Include proof for theorems and lemmas.

        Returns:
            Dict with 'success', 'error' (optional), and 'results' fields.
        """
        # Validate that at least one search parameter is provided
        search_params = [
            ("natural_language_query", natural_language_query),
            ("lean_name", lean_name),
            ("keywords", keywords)
        ]
        provided_params = [(name, value) for name, value in search_params if value is not None and str(value).strip()]

        if len(provided_params) == 0:
            return {
                "success": False,
                "error": "At least one of 'natural_language_query', 'lean_name', or 'keywords' must be provided",
                "results": []
            }

        # Execute all provided search modes
        self.logger.info(f"lean_retrieve_impl: execution started with modes: {[name for name, _ in provided_params]}")

        all_results = []
        for param_name, param_value in provided_params:
            try:
                if param_name == "natural_language_query":
                    result = await self._semantic_search_impl(param_value, workspace, limit, include_def_proof, include_theorem_proof)
                elif param_name == "lean_name":
                    result = await self._name_search_impl(param_value, workspace, limit, include_def_proof, include_theorem_proof)
                else:  # keywords
                    result = await self._keywords_search_impl(param_value, workspace, limit, include_def_proof, include_theorem_proof)

                if result.get("success") and result.get("results"):
                    all_results.extend(result["results"])
            except Exception as e:
                self.logger.warning(f"Search mode {param_name} failed: {e}")
                continue

        # Deduplicate by signature and merge source lists
        signature_map = {}
        for item in all_results:
            signature = item.get("signature", "")
            if not signature:
                continue

            if signature in signature_map:
                # Merge source lists, avoiding duplicates
                existing_item = signature_map[signature]
                existing_sources = existing_item["source"]
                new_sources = item.get("source", [])
                for src in new_sources:
                    if src not in existing_sources:
                        existing_sources.append(src)
                existing_vars = existing_item.get("variables") or []
                new_vars = item.get("variables") or []
                if not existing_vars and new_vars:
                    existing_item["variables"] = new_vars
                elif existing_vars and new_vars and existing_vars != new_vars:
                    merged_vars = []
                    seen = set()
                    for v in list(existing_vars) + list(new_vars):
                        if v not in seen:
                            merged_vars.append(v)
                            seen.add(v)
                    existing_item["variables"] = merged_vars
            else:
                signature_map[signature] = item

        deduplicated_results = list(signature_map.values())

        # Apply limit to final results
        final_results = deduplicated_results[:limit]

        self.logger.info(f"lean_retrieve_impl: execution completed with {len(final_results)} unique results")
        return {
            "success": True,
            "results": final_results
        }

    def register_tools(self, mcp: FastMCP, enabled_tools: set[str]):
        """Register unified declaration search tool to MCP server"""
        # If no backend is available, do not register any tool
        available_workspaces = list(self.backends.keys())
        if not available_workspaces:
            self.logger.info(
                "No workspaces available for LeanRetrieve tools - skipping tool registration. "
                "This is expected when using local workspace paths without Git information."
            )
            return

        # Build workspace list for tool description (key is already in environment variable format)
        workspace_list = ', '.join(self.backends.keys())

        if "lean_retrieve" in enabled_tools:
            @mcp.tool(
                description=f"""Unified search tool for Lean declarations. At least ONE of the search parameters must be provided. Multiple search modes can be combined.

**Search modes** (provide one or more):
- natural_language_query: Search by natural language description (e.g., "commutativity of addition")
- lean_name: Search by exact or partial Lean name (e.g., "Nat.add_comm", "bezout")
- keywords: Search by comma-separated keywords (e.g., "group, homomorphism")

**Available workspaces**: {workspace_list}

**RETURNS**: `{{success: bool, error: str|null, results: [{{signature, semantic, variables, filename, line_start, line_end, proof?}}]}}`"""
            )
            async def lean_retrieve(
                workspace: Annotated[Optional[str], Field(
                    description=f"Workspace placeholder to search in. Available: {workspace_list}. If not provided or empty, searches all available workspaces."
                )] = None,
                natural_language_query: Annotated[Optional[str], Field(
                    description="Natural language description for semantic search. Examples: \"commutativity of addition\", \"prime factorization is unique\""
                )] = None,
                lean_name: Annotated[Optional[str], Field(
                    description="Exact or partial Lean name for name search. Examples: \"Nat.add_comm\", \"bezout\", \"prime_factorization\""
                )] = None,
                keywords: Annotated[Optional[str], Field(
                    description="Comma-separated keywords for keyword search. Examples: \"group, homomorphism\", \"prime, factorization\""
                )] = None,
                limit: Annotated[int, Field(
                    description="Maximum number of results to return"
                )] = 10,
                include_def_proof: Annotated[bool, Field(
                    description="Include proof/implementation for definitions"
                )] = False,
                include_theorem_proof: Annotated[bool, Field(
                    description="Include proof for theorems and lemmas"
                )] = False
            ) -> Dict[str, Any]:
                """Unified search for Lean declarations. Supports combining multiple search modes with result deduplication."""
                return await self.lean_retrieve_impl(
                    workspace=workspace,
                    natural_language_query=natural_language_query,
                    lean_name=lean_name,
                    keywords=keywords,
                    limit=limit,
                    include_def_proof=include_def_proof,
                    include_theorem_proof=include_theorem_proof
                )
    
    async def _format_search_results(self, results, include_def_proof: bool, include_theorem_proof: bool, workspace: str) -> List[Dict[str, Any]]:
        """Format search results with filename, line positions, and configurable proof inclusion (asynchronous, to avoid blocking large result sets)

        Args:
            results: Search result list
            include_def_proof: Whether to include proof for definitions/non-theorems
            include_theorem_proof: Whether to include proof for theorems/lemmas
            workspace: workspace type, for access control check
        """
        def format_results():
            formatted_results = []
            for result in results:
                if self._should_filter_result(result.item.filename, workspace):
                    continue

                item_dict = {
                    "fullname": result.item.fullname,
                    "variables": result.item.variables,
                    "signature": result.item.signature,
                    "semantic": result.item.semantic,
                    "filename": result.item.filename,
                    "line_start": result.item.span_start,
                    "line_end": result.item.span_end,
                    "source": [workspace],
                }

                # Include proof based on kind and parameters (theorem/lemma vs definition)
                is_theorem_kind = result.item.kind in ("theorem", "lemma")
                should_include_proof = (
                    (is_theorem_kind and include_theorem_proof) or
                    (not is_theorem_kind and include_def_proof)
                )

                if should_include_proof:
                    item_dict["proof"] = result.item.proof

                formatted_results.append(item_dict)
            return formatted_results

        return await asyncio.to_thread(format_results)
    
    async def _semantic_search_impl(self, query: str, workspace: Optional[str] = None, limit: int = 10, include_def_proof: bool = False, include_theorem_proof: bool = False) -> Dict[str, Any]:
        """Implementation of semantic search across one or multiple workspaces"""
        # Validate parameters
        if not query or not query.strip():
            return {
                "success": False,
                "error": "Query cannot be empty",
                "results": []
            }

        # Determine which workspaces to search
        if workspace and workspace.strip():
            workspaces_to_search = [workspace.strip()]
        else:
            workspaces_to_search = list(self.backends.keys())

        # Set search limit
        search_limit = min(limit, self.tool_config.max_limit)

        try:
            all_results = []

            # Search across all specified workspaces
            for ws in workspaces_to_search:
                # 1. Validate workspace exists
                if ws not in self.backends:
                    self.logger.warning(f'Workspace {ws} not found, skipping')
                    continue

                # 2. Get backend for the specified workspace
                backend = self.backends[ws]

                # 3. Ensure backend is initialized
                await backend.initialize()

                # Execute search (whole search function in thread pool, because it is CPU-intensive)
                results = await asyncio.to_thread(
                    backend.semantic_search,
                    query.strip(),
                    search_limit
                )

                # Format results - include core information, filename and line positions, and apply access control filtering
                formatted_results = await self._format_search_results(results, include_def_proof, include_theorem_proof, ws)
                all_results.extend(formatted_results)

            return {
                "success": True,
                "results": all_results
            }

        except Exception:
            self.logger.error(f"Semantic search error: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Search failed: {traceback.format_exc()}",
                "results": []
            }

    async def _name_search_impl(self, target_name: str, workspace: Optional[str] = None, limit: int = 10, include_def_proof: bool = False, include_theorem_proof: bool = False) -> Dict[str, Any]:
        """Implementation of name search across one or multiple workspaces"""
        # Validate parameters
        if not target_name or not target_name.strip():
            return {
                "success": False,
                "error": "Target name cannot be empty",
                "results": []
            }

        # Determine which workspaces to search
        if workspace and workspace.strip():
            workspaces_to_search = [workspace.strip()]
        else:
            workspaces_to_search = list(self.backends.keys())

        # Set search limit
        search_limit = min(limit, self.tool_config.max_limit)

        try:
            all_results = []

            # Search across all specified workspaces
            for ws in workspaces_to_search:
                # 1. Validate workspace exists
                if ws not in self.backends:
                    self.logger.warning(f'Workspace {ws} not found, skipping')
                    continue

                # 2. Get backend for the specified workspace
                backend = self.backends[ws]

                # 3. Ensure backend is initialized
                await backend.initialize()

                # Execute search (whole search function in thread pool, because it is CPU-intensive)
                results = await asyncio.to_thread(
                    backend.name_search,
                    target_name.strip(),
                    search_limit
                )

                # Format results - include core information, filename and line positions, and apply access control filtering
                formatted_results = await self._format_search_results(results, include_def_proof, include_theorem_proof, ws)
                all_results.extend(formatted_results)

            return {
                "success": True,
                "results": all_results
            }

        except Exception:
            self.logger.error(f"Name search error: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Search failed: {traceback.format_exc()}",
                "results": []
            }

    async def _keywords_search_impl(self, keywords: str, workspace: Optional[str] = None, limit: int = 10, include_def_proof: bool = False, include_theorem_proof: bool = False) -> Dict[str, Any]:
        """Implementation of keywords search across one or multiple workspaces"""
        # Validate parameters
        if not keywords or not keywords.strip():
            return {
                "success": False,
                "error": "Keywords cannot be empty",
                "results": []
            }

        # Determine which workspaces to search
        if workspace and workspace.strip():
            workspaces_to_search = [workspace.strip()]
        else:
            workspaces_to_search = list(self.backends.keys())

        # Set search limit
        search_limit = min(limit, self.tool_config.max_limit)

        try:
            all_results = []

            # Search across all specified workspaces
            for ws in workspaces_to_search:
                # 1. Validate workspace exists
                if ws not in self.backends:
                    self.logger.warning(f'Workspace {ws} not found, skipping')
                    continue

                # 2. Get backend for the specified workspace
                backend = self.backends[ws]

                # 3. Ensure backend is initialized
                await backend.initialize()

                # Execute search (whole search function in thread pool, because it is CPU-intensive)
                results = await asyncio.to_thread(
                    backend.keywords_search,
                    keywords.strip(),
                    search_limit
                )

                # Format results - include core information, filename and line positions, and apply access control filtering
                formatted_results = await self._format_search_results(results, include_def_proof, include_theorem_proof, ws)
                all_results.extend(formatted_results)

            return {
                "success": True,
                "results": all_results
            }

        except Exception:
            self.logger.error(f"Keywords search error: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Search failed: {traceback.format_exc()}",
                "results": []
            }

    @classmethod
    def get_required_resources(
        cls,
        scratch_workspace_info: Optional['WorkspaceInfo'] = None,
        target_workspace_info: Optional['WorkspaceInfo'] = None,
        reference_workspaces_info: Optional[List['WorkspaceInfo']] = None,
        config: Optional[Any] = None,
    ) -> List[tuple[Path, Optional[Path]]]:
        """Get resources required by lean_retrieve toolkit.

        Returns embedding model and database paths for all repos.
        Only includes commit index files for specific commits actually used.
        All resources are in PROJECT_ROOT, so use default mapping.
        """
        from typing import Dict, Set
        actual_config = config.tools_config.lean_retrieve
        resources = []
        reference_workspaces_info = reference_workspaces_info or []

        # Collect all required (repo_name, commit_hash) pairs
        required_commits: Dict[str, Set[str]] = {}  # repo_name -> {commit_hashes}
        repo_name_to_url: Dict[str, str] = {}  # repo_name -> repo_url

        if target_workspace_info and target_workspace_info.repo_url:
            repo_name, repo_url = actual_config.resolve_repo(target_workspace_info.repo_url)
            repo_name_to_url[repo_name] = repo_url
            if target_workspace_info.commit_hash:
                required_commits.setdefault(repo_name, set()).add(
                    target_workspace_info.commit_hash
                )

        for ref_ws in reference_workspaces_info:
            if ref_ws.repo_url and ref_ws.commit_hash:
                repo_name, repo_url = actual_config.resolve_repo(ref_ws.repo_url)
                repo_name_to_url[repo_name] = repo_url
                required_commits.setdefault(repo_name, set()).add(ref_ws.commit_hash)

        # Add resources for each repo
        for repo_name, commit_hashes in required_commits.items():
            repo_url = repo_name_to_url[repo_name]

            # Add storage dir (ChromaDB + annotated_ids.txt)
            storage_dir = actual_config.get_storage_dir(repo_url)
            if storage_dir.exists():
                resources.append((storage_dir, None))

            # Add only specific commit index files (NOT the entire directory)
            commit_index_dir = actual_config.get_commit_index_dir(repo_url)
            for commit_hash in commit_hashes:
                commit_index_file = commit_index_dir / f"{commit_hash}.jsonl"
                if commit_index_file.exists():
                    resources.append((commit_index_file, None))

        # Add embedding model (use default PROJECT_ROOT mapping)
        if actual_config.embedding_model.exists():
            resources.append((actual_config.embedding_model, None))

        return resources


# Automatically register tool
from ape.toolkits.registry import register_tool
register_tool(LeanRetrieveToolsProvider)
