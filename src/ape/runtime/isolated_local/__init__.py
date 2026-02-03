"""Isolated Local Runtime - Copy-on-execute with file permission control.

This runtime provides local execution with workspace isolation through full copying.
Target and reference workspaces are fully copied (not hardlinked) during execution,
allowing fine-grained file permission control. After execution, copies are removed
and original symlinks are restored.

Key features:
- Full workspace copy before execution (no hardlinks)
- File permission-based access control (blocked/readonly paths)
- Automatic symlink restoration after execution
"""

from .runtime import IsolatedLocalRuntime, IsolatedLocalRuntimeConfig

__all__ = ['IsolatedLocalRuntime', 'IsolatedLocalRuntimeConfig']
