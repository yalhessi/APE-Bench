"""Lean execution and verification support."""

from .tools import LeanVerifyToolsProvider
from .config import LeanVerifyToolConfig
from .core.verification import VerificationEngine

# Register LeanVerifyToolsProvider as executor for .lean files
# This allows FileSystemProvider to find and use the shared instance
from ape.toolkits.registry import register_executor
register_executor('.lean', LeanVerifyToolsProvider)

__all__ = [
    "LeanVerifyToolsProvider",
    "LeanVerifyToolConfig",
    "VerificationEngine",
]
