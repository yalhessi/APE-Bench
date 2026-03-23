"""Toolkits - organized by functionality (file_system, retrieve, execute)."""

from .file_system import (
    FileSystemProvider,
    FileSystemToolsProvider,
    FileSystemToolConfig,
)

from .retrieve import (
    LeanRetrieveBackend,
    LeanRetrieveToolsProvider,
    LeanRetrieveToolConfig,
)

from .execute import (
    LeanVerifyToolsProvider,
    LeanVerifyToolConfig,
    VerificationEngine,
    IsabelleVerifyToolsProvider,
    IsabelleVerifyToolConfig,
    IsabelleVerificationEngine,
    BashExecuteToolsProvider,
    BashExecuteToolConfig,
)

# mcp_adapter has been removed, all logic moved to MCPManager
from .registry import register_tool, get_all_tool_names, get_tool_provider_class

__all__ = [
    # File System
    "FileSystemProvider",
    "FileSystemToolsProvider",
    "FileSystemToolConfig",
    # Retrieve
    "LeanRetrieveBackend",
    "LeanRetrieveToolsProvider",
    "LeanRetrieveToolConfig",
    # Execute
    "LeanVerifyToolsProvider",
    "LeanVerifyToolConfig",
    "VerificationEngine",
    "IsabelleVerifyToolsProvider",
    "IsabelleVerifyToolConfig",
    "IsabelleVerificationEngine",
    "BashExecuteToolsProvider",
    "BashExecuteToolConfig",
    # Registry
    "register_tool",
    "get_all_tool_names",
    "get_tool_provider_class",
]
