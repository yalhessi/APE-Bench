"""
Scaffold Registry Module.

Provides centralized scaffold registration management.
"""

from typing import Dict, Any, Union, Type, Optional, TYPE_CHECKING
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    from .base import BaseScaffold

_scaffolds: Dict[str, Type['BaseScaffold']] = {}
_default_logger = create_logger()


def register_scaffold(name: str, scaffold_class: Type['BaseScaffold']) -> None:
    """Register a scaffold type."""
    if name in _scaffolds:
        _default_logger.debug(f"Scaffold '{name}' already registered, skipping duplicate registration")
        return

    _scaffolds[name] = scaffold_class


def list_scaffold_types() -> list[str]:
    """Get all registered scaffold type names."""
    return list(_scaffolds.keys())


def get_scaffold_class(name: str) -> Optional[Type['BaseScaffold']]:
    """Get scaffold class by name."""
    return _scaffolds.get(name)

