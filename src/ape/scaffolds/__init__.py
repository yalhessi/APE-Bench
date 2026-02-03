"""Scaffolds module - Provides base scaffold classes and implementations."""

# Base classes
from .base import BaseScaffold, ScaffoldTerminationResult
# Registry
from .registry import register_scaffold, list_scaffold_types, get_scaffold_class
# Concrete scaffold implementations (automatically registered on import)
from .ape_agent import ApeAgentScaffold
from .claude_code import ClaudeCodeScaffold
from .codex import CodexScaffold
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