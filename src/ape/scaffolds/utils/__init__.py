"""
Shared utilities for scaffold implementations

This module provides common abstractions and utilities used across different scaffolds:
- Base relay for HTTP service and conversation recording
- MCP server management
- Common utility functions
"""

# MCPServerManager has been removed, use MCPManager from ape.toolkits instead
from .common import allocate_port, open_file_in_vscode
from .base_relay import BaseRelaySession
from .base_conversation import BaseConversationManager

__all__ = [
    'allocate_port',
    'open_file_in_vscode',
    'BaseRelaySession',
    'BaseConversationManager',
]
