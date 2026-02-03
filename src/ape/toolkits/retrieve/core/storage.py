"""
Core storage operations for ChromaDB
"""

import asyncio
import json
import aiofiles
from pathlib import Path
from typing import List, Dict, Any, Set
from tqdm import tqdm


async def init_chromadb(storage_dir: Path, collection_name: str):
    """Initialize ChromaDB (async to avoid blocking)"""
    import chromadb
    from chromadb.config import Settings

    def _init():
        client_settings = Settings(anonymized_telemetry=False)
        client = chromadb.PersistentClient(
            path=str(storage_dir / "chroma_db"),
            settings=client_settings
        )
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        return client, collection

    return await asyncio.to_thread(_init)


async def compute_embeddings(
    texts: List[str],
    embedding_model_path: Path,
    batch_size: int,
    logger
) -> List[List[float]]:
    """Compute embeddings for texts"""
    if not texts:
        return []

    logger.info(f"Computing embeddings for {len(texts)} texts...")

    try:
        from sentence_transformers import SentenceTransformer

        model = await asyncio.to_thread(
            lambda: SentenceTransformer(
                str(embedding_model_path),
                local_files_only=True
            )
        )

        embeddings_array = await asyncio.to_thread(
            lambda: model.encode(
                texts,
                show_progress_bar=True,
                convert_to_tensor=False,
                batch_size=batch_size
            )
        )
        embeddings = embeddings_array.tolist()

        logger.info(f"Successfully computed {len(embeddings)} embeddings")
        return embeddings

    except Exception as e:
        logger.error(f"Error computing embeddings: {e}")
        return []


async def add_to_chromadb_batched(
    ids: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]],
    documents: List[str],
    collection,
    batch_size: int,
    logger
):
    """Batch add to ChromaDB"""
    total_items = len(ids)

    if total_items <= batch_size:
        await asyncio.to_thread(
            collection.add,
            ids,
            embeddings,
            metadatas,
            documents,
        )
        return

    num_batches = (total_items + batch_size - 1) // batch_size
    logger.info(f"Adding to ChromaDB in {num_batches} batches of size {batch_size}")

    for i in tqdm(range(0, total_items, batch_size), desc="Adding to ChromaDB"):
        end_idx = min(i + batch_size, total_items)

        batch_ids = ids[i:end_idx]
        batch_embeddings = embeddings[i:end_idx]
        batch_metadatas = metadatas[i:end_idx]
        batch_documents = documents[i:end_idx]

        await asyncio.to_thread(
            collection.add,
            batch_ids,
            batch_embeddings,
            batch_metadatas,
            batch_documents,
        )


async def load_indexed_ids(indexed_ids_file: Path) -> Set[str]:
    """Load indexed item IDs"""
    if not indexed_ids_file.exists():
        return set()

    result = set()
    async with aiofiles.open(indexed_ids_file, 'r', encoding='utf-8') as f:
        async for line in f:
            line = line.strip()
            if line and len(line) == 64:
                result.add(line)
    return result


async def append_indexed_ids(indexed_ids_file: Path, item_ids: List[str]):
    """Append new indexed IDs to file"""
    indexed_ids_file.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(indexed_ids_file, 'a', encoding='utf-8') as f:
        for item_id in item_ids:
            await f.write(f"{item_id}\n")


async def load_commit_index_ids(commit_index_file: Path) -> Set[str]:
    """Load existing item IDs from commit index"""
    if not commit_index_file.exists():
        return set()

    ids = set()
    async with aiofiles.open(commit_index_file, "r", encoding="utf-8") as f:
        async for line in f:
            if not (line := line.strip()):
                continue
            try:
                if item_id := json.loads(line).get("item_id"):
                    ids.add(item_id)
            except Exception:
                continue
    return ids


async def append_commit_index(
    commit_index_file: Path,
    records: List[Dict[str, Any]]
):
    """Append records to commit index"""
    if not records:
        return

    commit_index_file.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(commit_index_file, "a", encoding="utf-8") as f:
        for record in records:
            await f.write(json.dumps(record, ensure_ascii=False) + "\n")
