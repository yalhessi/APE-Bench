"""Backward-compatible shim for the new blob-store abstraction."""

from .blob_store import S3BlobStore

S3Mirror = S3BlobStore

__all__ = ["S3Mirror", "S3BlobStore"]
