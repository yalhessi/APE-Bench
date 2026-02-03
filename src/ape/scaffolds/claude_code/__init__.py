"""
Claude Code Scaffold - Claude Code SDK Integration

Based on Claude Code SDK scaffold implementation:
1. Follows core Scaffold protocol
2. Uses Claude Code SDK built-in tool system (Read, Write, Edit, etc.)
3. Configures tool permissions and dual workspace through ClaudeAgentOptions
4. Disables Bash commands, allows other file operation tools to execute automatically within permission scope by default
5. Provides lean_verify and lean_retrieve extension tools through MCP server
"""

from .scaffold import ClaudeCodeScaffold

__all__ = [
    'ClaudeCodeScaffold'
]

