"""
Codex Scaffold - OpenAI Codex CLI Integration

Prerequisites:
- CodexBridge must be installed at: src/ape/scaffolds/codex/codexbridge/
- Install from: https://github.com/begonia599/CodexBridge
- Clone or download the repository to the path above

Based on Codex CLI scaffold implementation:
1. Follows core Scaffold protocol
2. Uses Codex CLI with subprocess control
3. Configures MCP servers through ~/.codex/config.toml
4. Uses relay to intercept API calls and record conversations
5. Supports both batch and CLI modes
"""

from .scaffold import CodexScaffold

__all__ = [
    'CodexScaffold'
]

__version__ = '1.0.0'
