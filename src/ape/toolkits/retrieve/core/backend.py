"""
Base retrieval backend with shared embedding model and ChromaDB management
"""

import asyncio
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Callable, TYPE_CHECKING

from .config import BaseRetrieveConfig
from .models import BaseItem, SearchResult
from .storage import init_chromadb

if TYPE_CHECKING:
    import logging


class BaseRetrieveBackend:
    """Base retrieval backend with shared resources"""

    # Global embedding model cache (shared across all backends)
    _embedding_model = None
    _embedding_model_path = None

    def __init__(
        self,
        config: BaseRetrieveConfig,
        storage_key: str,  # repo_url or dataset_name
        logger: Optional['logging.LoggerAdapter'] = None,
        metadata_to_item_fn: Optional[Callable[[Dict[str, Any]], BaseItem]] = None
    ):
        self.config = config
        self.storage_key = storage_key
        self.logger = logger
        self.metadata_to_item_fn = metadata_to_item_fn
        self._initialized = False

        # ChromaDB (per-backend instance)
        self.client = None
        self.collection = None

        # Filtering (can be updated dynamically)
        self._allowed_item_ids: Set[str] = set()
        self._candidate_multiplier: int = 1

    async def initialize(self):
        """Initialize backend"""
        if self._initialized:
            return

        try:
            # Initialize ChromaDB
            storage_dir = self._get_storage_dir()
            self.client, self.collection = await init_chromadb(
                storage_dir,
                self.config.collection_name
            )

            # Initialize shared embedding model (class-level)
            await self._init_embedding_model()

            # Load index
            await self._load_index()

            # Compute candidate multiplier
            await self._compute_candidate_multiplier()

            self._initialized = True

            self.logger.info(
                f"Backend initialized for {self.storage_key}, "
                f"candidate_multiplier={self._candidate_multiplier}"
            )

        except Exception as e:
            exc_msg = traceback.format_exc()
            self.logger.error(f"Failed to initialize backend: {exc_msg}")
            raise RuntimeError(f"Backend initialization failed: {e}")

    async def _init_embedding_model(self):
        """Initialize shared embedding model (class-level singleton)"""
        model_path_str = str(self.config.embedding_model)

        # Check if model is already loaded
        if BaseRetrieveBackend._embedding_model is not None:
            if BaseRetrieveBackend._embedding_model_path == model_path_str:
                self.logger.info(f"Reusing cached embedding model: {model_path_str}")
                return

        # Load model
        self.logger.info(f"Loading embedding model: {model_path_str}")

        from sentence_transformers import SentenceTransformer

        model = await asyncio.to_thread(
            lambda: SentenceTransformer(model_path_str, local_files_only=True)
        )

        # Cache at class level
        BaseRetrieveBackend._embedding_model = model
        BaseRetrieveBackend._embedding_model_path = model_path_str

        self.logger.info(f"Embedding model loaded and cached")

    def _get_storage_dir(self) -> Path:
        """Get storage directory - override in subclass if needed"""
        raise NotImplementedError("Subclass must implement _get_storage_dir()")

    async def _load_index(self):
        """Load index - override in subclass"""
        raise NotImplementedError("Subclass must implement _load_index()")

    async def _compute_candidate_multiplier(self):
        """Compute candidate multiplier - override in subclass if needed"""
        self._candidate_multiplier = 1

    def _fetch_items_by_ids(self, ids: List[str]) -> Dict[str, BaseItem]:
        """Fetch items from ChromaDB by IDs"""
        if not ids or not self.metadata_to_item_fn:
            return {}

        data = self.collection.get(ids=ids)

        items = {}
        if data and data.get('ids') and data.get('metadatas'):
            for item_id, metadata in zip(data['ids'], data['metadatas']):
                if item_id and metadata:
                    try:
                        items[item_id] = self.metadata_to_item_fn(metadata)
                    except Exception:
                        continue
        return items

    def semantic_search(self, query: str, limit: int) -> List[SearchResult]:
        """Semantic search using shared embedding model"""
        if not self._initialized:
            raise RuntimeError("Backend not initialized. Call initialize() first.")

        try:
            query_stripped = query.strip()

            # Use class-level cached model
            query_embedding = BaseRetrieveBackend._embedding_model.encode([query_stripped]).tolist()[0]

            candidate_count = limit * self._candidate_multiplier
            query_size = min(candidate_count, self.config.max_query_size)

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=query_size,
                include=["metadatas", "distances"],
            )

            if not results or not results.get('metadatas'):
                return []

            metadatas = results['metadatas'][0]
            dists = results['distances'][0]

            # Filter by allowed item IDs
            merged = []
            for metadata, dist in zip(metadatas, dists):
                if metadata and 'item_id' in metadata:
                    iid = metadata['item_id']
                    if iid in self._allowed_item_ids:
                        merged.append((iid, dist))

            if not merged:
                return []

            top_results = merged[:candidate_count]
            top_ids = [iid for iid, _ in top_results]
            id_to_item = self._fetch_items_by_ids(top_ids)

            results_list = []
            for iid, dist in top_results:
                if len(results_list) >= limit:
                    break
                item = id_to_item.get(iid)
                if item:
                    score = 1 - float(dist)
                    results_list.append(SearchResult(
                        item=item,
                        score=score,
                        reason=f"semantic similarity: {score:.3f}"
                    ))

            return results_list

        except Exception as e:
            exc_msg = traceback.format_exc()
            self.logger.error(f"Semantic search failed: {exc_msg}")
            raise RuntimeError(f"Semantic search failed: {e}")
