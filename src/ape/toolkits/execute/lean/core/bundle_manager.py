"""
Snapshot-scoped remote bundle acceleration for Lean execute artifacts.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import os
import struct
import uuid
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

import aiofiles
import aiofiles.os

from ..config import LeanVerifyToolConfig
from .blob_store import BlobStore, create_blob_store
from ape.utils.file_ops import atomic_write
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging


_BUNDLE_INDEX_MAGIC = b"APEBNDL1"
_BUNDLE_INDEX_VERSION = 1
_BUNDLE_LAYOUT_VERSION = 1
_BUNDLE_INDEX_HEADER_STRUCT = struct.Struct("!8sIII")
_BUNDLE_DESCRIPTOR_STRUCT = struct.Struct("!IIQ")
_BUNDLE_ENTRY_STRUCT = struct.Struct("!32sIQI")


@dataclass(frozen=True)
class SnapshotBundleDescriptor:
    bundle_id: int
    object_count: int
    packed_size_bytes: int


@dataclass(frozen=True)
class SnapshotBundleEntry:
    content_hash: str
    bundle_id: int
    offset: int
    length: int


@dataclass(frozen=True)
class SnapshotBundleIndex:
    bundles: Dict[int, SnapshotBundleDescriptor]
    entries: Dict[str, SnapshotBundleEntry]


@dataclass(frozen=True)
class SnapshotBundleBuildResult:
    enabled: bool
    bundle_count: int
    bundled_object_count: int
    bundled_bytes: int


@dataclass(frozen=True)
class SnapshotBundleHydrationResult:
    attempted: bool
    eligible_hash_count: int
    bundle_download_count: int
    downloaded_bytes: int
    hydrated_hash_count: int
    hydrated_bytes: int


class SnapshotBundleManager:
    """Manage snapshot-scoped remote bundle packs for cold-restore acceleration."""

    def __init__(
        self,
        config: Optional[LeanVerifyToolConfig] = None,
        logger: Optional["logging.LoggerAdapter"] = None,
        repo_name: str = "mathlib4",
        blob_store: Optional[BlobStore] = None,
    ):
        self.config = config or LeanVerifyToolConfig()
        self.logger = logger or create_logger()
        self.repo_name = repo_name
        self.snapshot_dir = self.config.get_snapshot_dir(repo_name)
        self.storage_dir = self.config.storage_dir
        self.blob_store = blob_store or create_blob_store(self.config, self.logger)
        self.bundle_config = self.config.remote_artifact_store.bundle_acceleration

    @property
    def enabled(self) -> bool:
        return bool(self.bundle_config.enabled and self.blob_store.enabled)

    @property
    def bundle_layout_id(self) -> str:
        """Stable identifier for bundle artifacts built from the current layout settings."""
        return (
            f"v{_BUNDLE_LAYOUT_VERSION}"
            f"-obj{self.bundle_config.max_object_size_bytes}"
            f"-pack{self.bundle_config.target_bundle_size_bytes}"
        )

    def _get_object_path(self, content_hash: str) -> Path:
        if len(content_hash) < 4:
            raise ValueError(f"Invalid hash length: {content_hash}")
        return self.storage_dir / content_hash[:2] / content_hash[2:4] / content_hash

    def _metadata_path(self, workspace_id: str) -> Path:
        return self.snapshot_dir / f"{workspace_id}.{self.bundle_layout_id}.bundles"

    def _bundle_blob_prefix(self, workspace_id: str) -> str:
        return (
            f"repos/{self.repo_name}/snapshots/{workspace_id}/bundles/"
            f"{self.bundle_layout_id}"
        )

    def _metadata_blob_key(self, workspace_id: str) -> str:
        return f"{self._bundle_blob_prefix(workspace_id)}/index.bundles"

    def _pack_blob_key(self, workspace_id: str, bundle_id: int) -> str:
        return f"{self._bundle_blob_prefix(workspace_id)}/bundle-{bundle_id:06d}.pack"

    @staticmethod
    def _encode_bundle_index(index: SnapshotBundleIndex) -> bytes:
        buffer = io.BytesIO()
        buffer.write(
            _BUNDLE_INDEX_HEADER_STRUCT.pack(
                _BUNDLE_INDEX_MAGIC,
                _BUNDLE_INDEX_VERSION,
                len(index.bundles),
                len(index.entries),
            )
        )

        for bundle_id in sorted(index.bundles):
            descriptor = index.bundles[bundle_id]
            buffer.write(
                _BUNDLE_DESCRIPTOR_STRUCT.pack(
                    descriptor.bundle_id,
                    descriptor.object_count,
                    descriptor.packed_size_bytes,
                )
            )

        for content_hash in sorted(index.entries):
            entry = index.entries[content_hash]
            buffer.write(
                _BUNDLE_ENTRY_STRUCT.pack(
                    bytes.fromhex(entry.content_hash),
                    entry.bundle_id,
                    entry.offset,
                    entry.length,
                )
            )

        return buffer.getvalue()

    @staticmethod
    def _decode_bundle_index(data: bytes) -> SnapshotBundleIndex:
        if len(data) < _BUNDLE_INDEX_HEADER_STRUCT.size:
            raise ValueError("Invalid bundle index header")

        offset = 0
        magic, version, bundle_count, entry_count = _BUNDLE_INDEX_HEADER_STRUCT.unpack_from(
            data, offset
        )
        offset += _BUNDLE_INDEX_HEADER_STRUCT.size

        if magic != _BUNDLE_INDEX_MAGIC:
            raise ValueError("Unsupported bundle index magic")
        if version != _BUNDLE_INDEX_VERSION:
            raise ValueError(f"Unsupported bundle index version: {version}")

        bundles: Dict[int, SnapshotBundleDescriptor] = {}
        for _ in range(bundle_count):
            if offset + _BUNDLE_DESCRIPTOR_STRUCT.size > len(data):
                raise ValueError("Incomplete bundle descriptor table")
            bundle_id, object_count, packed_size_bytes = _BUNDLE_DESCRIPTOR_STRUCT.unpack_from(
                data, offset
            )
            offset += _BUNDLE_DESCRIPTOR_STRUCT.size
            bundles[bundle_id] = SnapshotBundleDescriptor(
                bundle_id=bundle_id,
                object_count=object_count,
                packed_size_bytes=packed_size_bytes,
            )

        entries: Dict[str, SnapshotBundleEntry] = {}
        for _ in range(entry_count):
            if offset + _BUNDLE_ENTRY_STRUCT.size > len(data):
                raise ValueError("Incomplete bundle entry table")
            hash_bytes, bundle_id, entry_offset, length = _BUNDLE_ENTRY_STRUCT.unpack_from(
                data, offset
            )
            offset += _BUNDLE_ENTRY_STRUCT.size
            content_hash = hash_bytes.hex()
            if bundle_id not in bundles:
                raise ValueError(f"Bundle entry references unknown bundle: {bundle_id}")
            entries[content_hash] = SnapshotBundleEntry(
                content_hash=content_hash,
                bundle_id=bundle_id,
                offset=entry_offset,
                length=length,
            )

        if offset != len(data):
            raise ValueError("Unexpected trailing bytes in bundle index")

        return SnapshotBundleIndex(bundles=bundles, entries=entries)

    def _collect_bundle_candidates_sync(
        self,
        file_mappings: Dict[str, Dict[str, str]],
    ) -> List[tuple[str, Path, int]]:
        seen_hashes: set[str] = set()
        candidates: List[tuple[str, Path, int]] = []

        for file_info in file_mappings.values():
            if file_info.get("type") != "regular":
                continue

            content_hash = str(file_info.get("hash") or "")
            if not content_hash or content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)

            object_path = self._get_object_path(content_hash)
            if not object_path.exists():
                continue

            size_bytes = object_path.stat().st_size
            if size_bytes > self.bundle_config.max_object_size_bytes:
                continue

            candidates.append((content_hash, object_path, size_bytes))

        candidates.sort(key=lambda item: item[0])
        return candidates

    def _group_candidates(
        self,
        candidates: List[tuple[str, Path, int]],
    ) -> List[List[tuple[str, Path, int]]]:
        if not candidates:
            return []

        target_size = max(1, self.bundle_config.target_bundle_size_bytes)
        bundles: List[List[tuple[str, Path, int]]] = []
        current_bundle: List[tuple[str, Path, int]] = []
        current_size = 0

        for candidate in candidates:
            size_bytes = candidate[2]
            if current_bundle and current_size + size_bytes > target_size:
                bundles.append(current_bundle)
                current_bundle = []
                current_size = 0

            current_bundle.append(candidate)
            current_size += size_bytes

        if current_bundle:
            bundles.append(current_bundle)

        return bundles

    @staticmethod
    def _write_pack_sync(
        temp_pack_path: Path,
        bundle_candidates: List[tuple[str, Path, int]],
    ) -> tuple[int, List[tuple[str, int, int]]]:
        entries: List[tuple[str, int, int]] = []
        offset = 0

        with open(temp_pack_path, "wb") as pack_file:
            for content_hash, object_path, _ in bundle_candidates:
                payload = object_path.read_bytes()
                pack_file.write(payload)
                entries.append((content_hash, offset, len(payload)))
                offset += len(payload)

        return offset, entries

    @staticmethod
    def _extract_bundle_sync(
        pack_path: Path,
        descriptor: SnapshotBundleDescriptor,
        entries: List[SnapshotBundleEntry],
        storage_dir: Path,
        readonly_mode: Optional[int],
    ) -> tuple[int, int]:
        actual_size = pack_path.stat().st_size
        if actual_size != descriptor.packed_size_bytes:
            raise ValueError(
                f"Unexpected pack size for bundle {descriptor.bundle_id}: "
                f"{actual_size} != {descriptor.packed_size_bytes}"
            )

        hydrated_hash_count = 0
        hydrated_bytes = 0
        sorted_entries = sorted(entries, key=lambda item: item.offset)

        with open(pack_path, "rb") as pack_file:
            for entry in sorted_entries:
                if entry.offset + entry.length > actual_size:
                    raise ValueError(
                        f"Bundle entry exceeds pack bounds for {entry.content_hash[:12]}"
                    )

                object_path = storage_dir / entry.content_hash[:2] / entry.content_hash[2:4] / entry.content_hash
                if object_path.exists():
                    continue

                pack_file.seek(entry.offset)
                payload = pack_file.read(entry.length)
                if len(payload) != entry.length:
                    raise ValueError(
                        f"Failed to read packed object {entry.content_hash[:12]}"
                    )

                if hashlib.sha256(payload).hexdigest() != entry.content_hash:
                    raise ValueError(
                        f"Bundle payload hash mismatch for {entry.content_hash[:12]}"
                    )

                object_path.parent.mkdir(parents=True, exist_ok=True)
                temp_object_path = (
                    object_path.parent / f".{object_path.name}.{uuid.uuid4().hex}.bundletmp"
                )
                try:
                    with open(temp_object_path, "wb") as output_file:
                        output_file.write(payload)
                    os.replace(temp_object_path, object_path)
                    if readonly_mode is not None:
                        os.chmod(object_path, readonly_mode)
                finally:
                    if temp_object_path.exists():
                        try:
                            temp_object_path.unlink()
                        except OSError:
                            pass

                hydrated_hash_count += 1
                hydrated_bytes += entry.length

        return hydrated_hash_count, hydrated_bytes

    async def load_bundle_index(self, workspace_id: str) -> Optional[SnapshotBundleIndex]:
        metadata_path = self._metadata_path(workspace_id)

        if not await aiofiles.os.path.exists(metadata_path):
            if not self.enabled:
                return None

            restored = await self.blob_store.download_file_if_present(
                self._metadata_blob_key(workspace_id),
                metadata_path,
            )
            if not restored and not await aiofiles.os.path.exists(metadata_path):
                return None

        async with aiofiles.open(metadata_path, "rb") as metadata_file:
            data = await metadata_file.read()
        return self._decode_bundle_index(data)

    async def store_snapshot_bundles(
        self,
        workspace_id: str,
        file_mappings: Dict[str, Dict[str, str]],
    ) -> SnapshotBundleBuildResult:
        if not self.enabled:
            return SnapshotBundleBuildResult(False, 0, 0, 0)

        start_time = datetime.now()

        candidates = await asyncio.to_thread(
            self._collect_bundle_candidates_sync,
            file_mappings,
        )
        bundle_candidates = self._group_candidates(candidates)

        if not bundle_candidates:
            self.logger.info(
                "Snapshot bundle acceleration found no eligible objects for %s",
                workspace_id,
            )
            return SnapshotBundleBuildResult(True, 0, 0, 0)

        descriptors: Dict[int, SnapshotBundleDescriptor] = {}
        entries: Dict[str, SnapshotBundleEntry] = {}
        bundled_bytes = 0

        await aiofiles.os.makedirs(self.snapshot_dir, exist_ok=True)
        temp_pack_paths: List[Path] = []

        try:
            for bundle_id, candidates_for_bundle in enumerate(bundle_candidates):
                temp_pack_path = (
                    self.snapshot_dir
                    / f".{workspace_id}.bundle-{bundle_id:06d}.{uuid.uuid4().hex}.packtmp"
                )
                pack_size, pack_entries = await asyncio.to_thread(
                    self._write_pack_sync,
                    temp_pack_path,
                    candidates_for_bundle,
                )
                temp_pack_paths.append(temp_pack_path)

                descriptors[bundle_id] = SnapshotBundleDescriptor(
                    bundle_id=bundle_id,
                    object_count=len(pack_entries),
                    packed_size_bytes=pack_size,
                )
                bundled_bytes += pack_size

                for content_hash, offset, length in pack_entries:
                    entries[content_hash] = SnapshotBundleEntry(
                        content_hash=content_hash,
                        bundle_id=bundle_id,
                        offset=offset,
                        length=length,
                    )

            for bundle_id, temp_pack_path in enumerate(temp_pack_paths):
                await self.blob_store.upload_file_if_missing(
                    temp_pack_path,
                    self._pack_blob_key(workspace_id, bundle_id),
                )

            metadata_path = self._metadata_path(workspace_id)
            metadata = self._encode_bundle_index(
                SnapshotBundleIndex(bundles=descriptors, entries=entries)
            )
            await atomic_write(metadata_path, metadata, encoding=None)
            try:
                await self.blob_store.upload_file_if_missing(
                    metadata_path,
                    self._metadata_blob_key(workspace_id),
                )
            except Exception as exc:
                self.logger.warning(
                    "Failed to mirror bundle metadata for %s to the remote blob store: %s",
                    workspace_id,
                    exc,
                )

            self.logger.info(
                "Built snapshot bundle acceleration for %s [%s]: %s objects, %s packs, %s bytes, %.2fs",
                workspace_id,
                self.bundle_layout_id,
                len(entries),
                len(descriptors),
                bundled_bytes,
                (datetime.now() - start_time).total_seconds(),
            )
            return SnapshotBundleBuildResult(
                enabled=True,
                bundle_count=len(descriptors),
                bundled_object_count=len(entries),
                bundled_bytes=bundled_bytes,
            )
        finally:
            for temp_pack_path in temp_pack_paths:
                if await aiofiles.os.path.exists(temp_pack_path):
                    try:
                        await aiofiles.os.unlink(temp_pack_path)
                    except OSError:
                        pass

    async def _download_and_extract_bundle(
        self,
        workspace_id: str,
        descriptor: SnapshotBundleDescriptor,
        entries: List[SnapshotBundleEntry],
    ) -> tuple[int, int, int]:
        temp_pack_path = (
            self.snapshot_dir
            / f".{workspace_id}.bundle-{descriptor.bundle_id:06d}.{uuid.uuid4().hex}.download"
        )

        try:
            restored = await self.blob_store.download_file_if_present(
                self._pack_blob_key(workspace_id, descriptor.bundle_id),
                temp_pack_path,
            )
            if not restored:
                self.logger.warning(
                    "Bundle pack missing during restore for %s bundle %s",
                    workspace_id,
                    descriptor.bundle_id,
                )
                return 0, 0, 0

            hydrated_hash_count, hydrated_bytes = await asyncio.to_thread(
                self._extract_bundle_sync,
                temp_pack_path,
                descriptor,
                entries,
                self.storage_dir,
                0o444,
            )
            return descriptor.packed_size_bytes, hydrated_hash_count, hydrated_bytes
        finally:
            if await aiofiles.os.path.exists(temp_pack_path):
                try:
                    await aiofiles.os.unlink(temp_pack_path)
                except OSError:
                    pass

    async def hydrate_snapshot_objects(
        self,
        workspace_id: str,
        content_hashes: List[str],
    ) -> SnapshotBundleHydrationResult:
        if not self.enabled or not content_hashes:
            return SnapshotBundleHydrationResult(False, 0, 0, 0, 0, 0)

        try:
            bundle_index = await self.load_bundle_index(workspace_id)
        except Exception as exc:
            self.logger.warning(
                "Failed to load snapshot bundle metadata for %s: %s",
                workspace_id,
                exc,
            )
            return SnapshotBundleHydrationResult(False, 0, 0, 0, 0, 0)

        if bundle_index is None or not bundle_index.entries:
            return SnapshotBundleHydrationResult(False, 0, 0, 0, 0, 0)

        unique_hashes = sorted(set(content_hashes))
        eligible_entries = [
            bundle_index.entries[content_hash]
            for content_hash in unique_hashes
            if content_hash in bundle_index.entries
        ]

        if (
            len(eligible_entries)
            < self.bundle_config.min_missing_objects_for_bundle_restore
        ):
            self.logger.info(
                "Skipping bundle hydration for %s: %s eligible misses below threshold %s",
                workspace_id,
                len(eligible_entries),
                self.bundle_config.min_missing_objects_for_bundle_restore,
            )
            return SnapshotBundleHydrationResult(False, len(eligible_entries), 0, 0, 0, 0)

        bundles_to_hydrate: Dict[int, List[SnapshotBundleEntry]] = {}
        for entry in eligible_entries:
            bundles_to_hydrate.setdefault(entry.bundle_id, []).append(entry)

        self.logger.info(
            "Hydrating %s bundled CAS objects for %s [%s] from %s bundle packs",
            len(eligible_entries),
            workspace_id,
            self.bundle_layout_id,
            len(bundles_to_hydrate),
        )

        semaphore = asyncio.Semaphore(
            self.bundle_config.max_concurrent_bundle_downloads
        )

        async def hydrate_bundle(bundle_id: int) -> tuple[int, int, int]:
            descriptor = bundle_index.bundles.get(bundle_id)
            if descriptor is None:
                self.logger.warning(
                    "Snapshot bundle metadata for %s references unknown bundle %s",
                    workspace_id,
                    bundle_id,
                )
                return 0, 0, 0

            async with semaphore:
                try:
                    return await self._download_and_extract_bundle(
                        workspace_id,
                        descriptor,
                        bundles_to_hydrate[bundle_id],
                    )
                except Exception as exc:
                    self.logger.warning(
                        "Failed to hydrate bundle %s for %s: %s",
                        bundle_id,
                        workspace_id,
                        exc,
                    )
                    return 0, 0, 0

        results = await asyncio.gather(
            *(hydrate_bundle(bundle_id) for bundle_id in sorted(bundles_to_hydrate))
        )

        downloaded_bytes = sum(result[0] for result in results)
        hydrated_hash_count = sum(result[1] for result in results)
        hydrated_bytes = sum(result[2] for result in results)

        self.logger.info(
            "Bundle hydration completed for %s [%s]: %s packs, %s bytes downloaded, %s objects hydrated",
            workspace_id,
            self.bundle_layout_id,
            len(bundles_to_hydrate),
            downloaded_bytes,
            hydrated_hash_count,
        )
        return SnapshotBundleHydrationResult(
            attempted=True,
            eligible_hash_count=len(eligible_entries),
            bundle_download_count=len(bundles_to_hydrate),
            downloaded_bytes=downloaded_bytes,
            hydrated_hash_count=hydrated_hash_count,
            hydrated_bytes=hydrated_bytes,
        )
