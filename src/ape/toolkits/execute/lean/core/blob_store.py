"""
Blob-store abstractions for immutable Lean execute artifacts.

These backends are intentionally generic: they move opaque blobs addressed by a
string key. Higher-level managers decide how CAS objects and snapshot manifests
map onto keys.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import Optional, Protocol, TYPE_CHECKING

import aiofiles.os

from ..config import LeanVerifyToolConfig
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging


class BlobStore(Protocol):
    """Generic remote store for immutable artifact blobs."""

    @property
    def enabled(self) -> bool:
        """Return True when the blob store can service remote operations."""

    @property
    def max_concurrent_transfers(self) -> int:
        """Return the recommended maximum number of concurrent remote transfers."""

    async def upload_file_if_missing(self, local_path: Path, key: str) -> bool:
        """Upload a local file to the remote store only when the blob is absent."""

    async def download_file_if_present(
        self,
        key: str,
        local_path: Path,
        *,
        readonly_mode: Optional[int] = None,
    ) -> bool:
        """Download a remote blob when present, leaving local state unchanged otherwise."""


class NoopBlobStore:
    """Disabled blob store used for local-only deployments."""

    @property
    def enabled(self) -> bool:
        return False

    @property
    def max_concurrent_transfers(self) -> int:
        return 1

    async def upload_file_if_missing(self, local_path: Path, key: str) -> bool:
        return False

    async def download_file_if_present(
        self,
        key: str,
        local_path: Path,
        *,
        readonly_mode: Optional[int] = None,
    ) -> bool:
        return False


class S3BlobStore:
    """S3-backed blob store for immutable Lean execute artifacts."""

    def __init__(
        self,
        config: Optional[LeanVerifyToolConfig] = None,
        logger: Optional["logging.LoggerAdapter"] = None,
    ):
        self.config = config or LeanVerifyToolConfig()
        self.logger = logger or create_logger()
        remote_store = self.config.remote_artifact_store
        self.bucket = str(remote_store.bucket or "").strip()
        self.prefix = str(remote_store.prefix or "").strip().strip("/")
        self.endpoint_url = str(remote_store.endpoint_url or "").strip() or None
        self.region = str(remote_store.region or "").strip() or None
        self.profile = str(remote_store.profile or "").strip() or None
        self.request_checksum_calculation = (
            str(remote_store.request_checksum_calculation or "").strip() or None
        )
        self.response_checksum_validation = (
            str(remote_store.response_checksum_validation or "").strip() or None
        )
        self.max_pool_connections = self._derive_max_pool_connections()
        self._client = None

    @property
    def enabled(self) -> bool:
        return bool(self.bucket)

    @property
    def max_concurrent_transfers(self) -> int:
        return max(1, self.max_pool_connections)

    def _derive_max_pool_connections(self) -> int:
        candidates = [10]
        for attr_name in ("max_concurrent_operations", "max_concurrent_restores"):
            raw_value = getattr(self.config, attr_name, None)
            if raw_value is None:
                continue
            try:
                candidates.append(int(raw_value))
            except (TypeError, ValueError):
                continue
        return max(candidates)

    def _build_key(self, suffix: str) -> str:
        normalized_suffix = str(suffix).lstrip("/")
        if not self.prefix:
            return normalized_suffix
        return f"{self.prefix}/{normalized_suffix}"

    def _get_client(self):
        if not self.enabled:
            raise RuntimeError("S3 blob store requested but no bucket is configured")

        if self._client is None:
            try:
                import boto3
                from botocore.config import Config as BotoConfig
            except ImportError as exc:
                raise RuntimeError(
                    "S3 support requires boto3/botocore. Reinstall APE-Bench after "
                    "updating its Python requirements."
                ) from exc

            session_kwargs = {}
            if self.profile:
                session_kwargs["profile_name"] = self.profile

            session = boto3.session.Session(**session_kwargs)
            client_kwargs = {}
            if self.endpoint_url:
                client_kwargs["endpoint_url"] = self.endpoint_url
            if self.region:
                client_kwargs["region_name"] = self.region

            config_kwargs = {}
            if self.request_checksum_calculation:
                config_kwargs["request_checksum_calculation"] = (
                    self.request_checksum_calculation
                )
            if self.response_checksum_validation:
                config_kwargs["response_checksum_validation"] = (
                    self.response_checksum_validation
                )
            config_kwargs["max_pool_connections"] = self.max_pool_connections
            if config_kwargs:
                client_kwargs["config"] = BotoConfig(**config_kwargs)

            self._client = session.client("s3", **client_kwargs)

        return self._client

    @staticmethod
    def _is_not_found_error(exc: Exception) -> bool:
        response = getattr(exc, "response", None)
        if not isinstance(response, dict):
            return False

        error = response.get("Error", {}) if isinstance(response.get("Error"), dict) else {}
        code = str(error.get("Code") or "").strip()
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        return code in {"404", "NoSuchKey", "NotFound"} or status == 404

    async def _object_exists(self, key: str) -> bool:
        if not self.enabled:
            return False

        client = self._get_client()
        remote_key = self._build_key(key)

        def _head() -> bool:
            try:
                client.head_object(Bucket=self.bucket, Key=remote_key)
                return True
            except Exception as exc:
                if self._is_not_found_error(exc):
                    return False
                raise

        return await asyncio.to_thread(_head)

    async def upload_file_if_missing(self, local_path: Path, key: str) -> bool:
        if not self.enabled:
            return False

        if await self._object_exists(key):
            return False

        client = self._get_client()
        remote_key = self._build_key(key)
        await asyncio.to_thread(
            client.upload_file,
            str(local_path),
            self.bucket,
            remote_key,
        )
        return True

    async def download_file_if_present(
        self,
        key: str,
        local_path: Path,
        *,
        readonly_mode: Optional[int] = None,
    ) -> bool:
        if not self.enabled:
            return False

        await aiofiles.os.makedirs(local_path.parent, exist_ok=True)
        temp_path = local_path.parent / f".{local_path.name}.{uuid.uuid4().hex}.blobtmp"
        client = self._get_client()
        remote_key = self._build_key(key)

        try:
            await asyncio.to_thread(
                client.download_file,
                self.bucket,
                remote_key,
                str(temp_path),
            )
        except Exception as exc:
            if await aiofiles.os.path.exists(temp_path):
                try:
                    await aiofiles.os.unlink(temp_path)
                except Exception:
                    pass

            if self._is_not_found_error(exc):
                return False
            raise

        try:
            await aiofiles.os.replace(temp_path, local_path)
        except Exception:
            if await aiofiles.os.path.exists(temp_path):
                try:
                    await aiofiles.os.unlink(temp_path)
                except Exception:
                    pass
            raise

        if readonly_mode is not None:
            try:
                await asyncio.to_thread(os.chmod, str(local_path), readonly_mode)
            except OSError:
                pass

        return True


def create_blob_store(
    config: Optional[LeanVerifyToolConfig] = None,
    logger: Optional["logging.LoggerAdapter"] = None,
) -> BlobStore:
    """Build the remote blob-store backend for the current configuration."""
    actual_config = config or LeanVerifyToolConfig()
    remote_store = actual_config.remote_artifact_store
    if remote_store.enabled:
        if remote_store.kind != "s3":
            raise ValueError(
                f"Unsupported remote artifact-store kind: {remote_store.kind!r}"
            )
        return S3BlobStore(actual_config, logger)
    return NoopBlobStore()
