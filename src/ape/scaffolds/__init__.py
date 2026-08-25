"""Scaffolds module - Provides base scaffold classes and implementations."""

# Base classes
from .base import BaseScaffold, ScaffoldTerminationResult
# Registry
from .registry import register_scaffold, list_scaffold_types, get_scaffold_class
# Factory and creation utilities
from .factory import create_scaffold, create_scaffold_config_for_type

__all__ = [
    # Base classes
    'BaseScaffold',
    'ScaffoldTerminationResult',
    # Registry management
    'register_scaffold',
    'list_scaffold_types',
    'get_scaffold_class',
    # Factory and creation
    'create_scaffold',
    'create_scaffold_config_for_type',
    # Concrete implementations
    'ApeAgentScaffold',
    'ClaudeCodeScaffold',
    'CodexScaffold',
]


def __getattr__(name: str):
    """Lazily load concrete scaffold classes to avoid circular imports."""
    if name == 'ApeAgentScaffold':
        from .ape_agent import ApeAgentScaffold

        return ApeAgentScaffold

    if name == 'ClaudeCodeScaffold':
        from .claude_code import ClaudeCodeScaffold

        return ClaudeCodeScaffold

    if name == 'CodexScaffold':
        from .codex import CodexScaffold

        return CodexScaffold

    raise AttributeError(f"module 'ape.scaffolds' has no attribute {name!r}")
