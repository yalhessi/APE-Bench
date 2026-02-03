"""
Lean Retrieve Backend - Lean-specific retrieval backend
"""

import asyncio
import aiofiles
import json
from pathlib import Path
from typing import List, Dict, Optional, Set, TYPE_CHECKING
from rapidfuzz import fuzz

from ape.toolkits.retrieve.core import BaseRetrieveBackend, SearchResult
from .config import LeanRetrieveToolConfig
from .models import LeanItem
from .utils import normalize_keyword, metadata_to_item

if TYPE_CHECKING:
    import logging


class LeanRetrieveBackend(BaseRetrieveBackend):
    """Lean-specific retrieval backend with name and keyword search"""

    def __init__(
        self,
        config: LeanRetrieveToolConfig,
        commit_hash: str,
        repo_url: str,
        default_target: str,
        logger: Optional['logging.LoggerAdapter'] = None
    ):
        super().__init__(
            config=config,
            storage_key=repo_url,
            logger=logger,
            metadata_to_item_fn=metadata_to_item
        )
        self.commit_hash = commit_hash
        self.repo_url = repo_url
        self.repo_name = config.get_repo_name(repo_url)
        self.default_target = default_target

        # Lean-specific indices
        self._name_to_items: Dict[str, str] = {}
        self._keywords_to_items: Dict[str, Set[str]] = {}
        # Per-commit filename mapping (item_id -> filename for this specific commit)
        self._item_to_filename: Dict[str, str] = {}
        self._item_to_variables: Dict[str, List[str]] = {}

    def _get_storage_dir(self) -> Path:
        """Get storage directory for this repo"""
        return self.config.get_storage_dir(self.repo_url)

    def _apply_commit_fields(self, item) -> None:
        """Apply per-commit filename and variables to item (REQUIRED)

        This overrides the metadata filename with the correct file path for this specific commit.
        All items must have filename in commit_index after migration.
        """
        # filename is required - this should always exist after migration
        item.filename = self._item_to_filename[item.item_id]
        item.variables = self._item_to_variables.get(item.item_id, [])

    async def _load_index(self):
        """Load Lean-specific commit index with name and keyword indices"""
        commit_file = self.config.get_commit_index_dir(self.repo_url) / f"{self.commit_hash}.jsonl"
        if not commit_file.exists():
            return

        async with aiofiles.open(commit_file, 'r', encoding='utf-8') as f:
            async for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    rec = json.loads(line)
                    item_id = rec.get("item_id")
                    if not item_id:
                        continue

                    # REQUIRED: filename must be present in commit_index
                    filename = rec.get("filename")
                    if not filename:
                        # Skip items without filename - indicates unmigrated data
                        continue

                    self._allowed_item_ids.add(item_id)

                    # Store per-commit filename (required field)
                    self._item_to_filename[item_id] = filename
                    # Store per-commit variables (optional field)
                    variables = rec.get("variables", [])
                    if isinstance(variables, list):
                        self._item_to_variables[item_id] = [str(v) for v in variables if v is not None]
                    elif isinstance(variables, str):
                        if variables.strip():
                            try:
                                decoded = json.loads(variables)
                                if isinstance(decoded, list):
                                    self._item_to_variables[item_id] = [str(v) for v in decoded if v is not None]
                                else:
                                    self._item_to_variables[item_id] = [variables]
                            except Exception:
                                self._item_to_variables[item_id] = [variables]
                        else:
                            self._item_to_variables[item_id] = []
                    else:
                        self._item_to_variables[item_id] = []

                    # Name index
                    if name := rec.get("name"):
                        self._name_to_items[name.lower()] = item_id
                    if fullname := rec.get("fullname"):
                        self._name_to_items[fullname.lower()] = item_id

                    # Keyword index
                    if keywords_str := rec.get("keywords"):
                        keywords = [
                            normalize_keyword(kw)
                            for kw in keywords_str.split(',')
                            if kw.strip()
                        ]
                        for kw in keywords:
                            if kw:
                                self._keywords_to_items.setdefault(kw, set()).add(item_id)
                except Exception:
                    continue

    async def _compute_candidate_multiplier(self):
        """Compute candidate multiplier based on item density"""
        current_commit_items = len(self._allowed_item_ids)
        if current_commit_items == 0:
            self._candidate_multiplier = 1
            return

        indexed_ids_file = self.config.get_annotated_ids_file(self.repo_url)
        if not indexed_ids_file.exists():
            self._candidate_multiplier = 1
            return

        def count_total_items():
            with open(indexed_ids_file, 'r', encoding='utf-8') as f:
                return sum(1 for line in f if line.strip())

        total_items = await asyncio.to_thread(count_total_items)

        if total_items > 0:
            self._candidate_multiplier = max(int((total_items / current_commit_items) * 1.5), 1)
        else:
            self._candidate_multiplier = 1

    def name_search(self, target_name: str, limit: int) -> List[SearchResult]:
        """Name search using local index"""
        if not self._initialized:
            raise RuntimeError("Backend not initialized. Call initialize() first.")

        query = target_name.strip().lower()
        if not query:
            return []

        scored: Dict[str, float] = {}

        # 1. Exact match
        if query in self._name_to_items:
            scored[self._name_to_items[query]] = 1.0

        # 2. Prefix/contains match
        for name, item_id in self._name_to_items.items():
            if item_id not in scored:
                if name.startswith(query):
                    scored[item_id] = 0.8
                elif query in name:
                    scored[item_id] = 0.6

        # 3. Fuzzy match (if not enough results)
        remaining_slots = limit - len(scored)
        if remaining_slots > 0:
            candidates = []
            for name, item_id in self._name_to_items.items():
                if item_id not in scored:
                    len_diff = abs(len(query) - len(name))
                    if len_diff <= max(len(query), len(name)) // 2:
                        sim = fuzz.ratio(query, name) / 100.0
                        if sim > 0.3:
                            candidates.append((sim, item_id))
            candidates.sort(reverse=True)
            fuzzy_candidates = candidates[:remaining_slots]
            for sim, item_id in fuzzy_candidates:
                scored[item_id] = sim * 0.5

        return self._build_search_results(
            scored, limit, lambda item: f"name match: {item.fullname or item.name}"
        )

    def keywords_search(self, target_keywords: str, limit: int) -> List[SearchResult]:
        """Keyword search using local index"""
        if not self._initialized:
            raise RuntimeError("Backend not initialized. Call initialize() first.")

        input_keywords = [
            normalize_keyword(kw)
            for kw in target_keywords.split(',')
            if kw.strip()
        ]

        if not input_keywords:
            return []

        item_matches: Dict[str, Set[str]] = {}

        for kw in input_keywords:
            item_ids = self._keywords_to_items.get(kw)
            if item_ids:
                for item_id in item_ids:
                    item_matches.setdefault(item_id, set()).add(kw)

        if not item_matches:
            return []

        scored_items = [
            (item_id, len(matched_kws) / len(input_keywords), matched_kws)
            for item_id, matched_kws in item_matches.items()
        ]

        scored_items.sort(key=lambda x: (x[1], len(x[2])), reverse=True)
        candidate_count = limit * self._candidate_multiplier
        top_items = scored_items[:candidate_count]

        if not top_items:
            return []

        item_ids = [item_id for item_id, _, _ in top_items]
        id_to_item = self._fetch_items_by_ids(item_ids)

        results = []
        for item_id, score, matched_kws in top_items:
            if len(results) >= limit:
                break
            item = id_to_item.get(item_id)
            if item:
                # Apply per-commit filename before returning
                self._apply_commit_fields(item)
                matched_kws_sorted = sorted(matched_kws)
                reason = f"matched {len(matched_kws)}/{len(input_keywords)} keywords: {', '.join(matched_kws_sorted)}"
                results.append(SearchResult(
                    item=item,
                    score=score,
                    reason=reason
                ))

        return results

    def _build_search_results(
        self,
        scored: Dict[str, float],
        limit: int,
        reason_func
    ) -> List[SearchResult]:
        """Build search results from scored item IDs"""
        if not scored:
            return []

        ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)
        candidate_count = limit * self._candidate_multiplier
        candidate_ranked = ranked[:candidate_count]
        item_ids = [item_id for item_id, _ in candidate_ranked]
        id_to_item = self._fetch_items_by_ids(item_ids)

        results = []
        for item_id, score in candidate_ranked:
            if len(results) >= limit:
                break
            item = id_to_item.get(item_id)
            if item:
                # Apply per-commit filename before returning
                self._apply_commit_fields(item)
                results.append(SearchResult(
                    item=item,
                    score=score,
                    reason=reason_func(item)
                ))
        return results
