"""Runtime Registry.

Provides runtime registration and lookup functionality.
"""

from typing import Dict, Optional, Type, TYPE_CHECKING, Union, Tuple

from ape.utils.logging import create_logger

if TYPE_CHECKING:
    from ape.runtime.base import BaseRuntime, RuntimeConfig

_runtimes: Dict[str, Type['BaseRuntime']] = {}
_logger = create_logger()


def register_runtime(runtime_type: str, runtime_class: Type['BaseRuntime']) -> None:
    """Register a runtime class.

    Args:
        runtime_type: Runtime type identifier (e.g., 'sandbox', 'container')
        runtime_class: Runtime class that inherits from BaseRuntime
    """
    if runtime_type in _runtimes:
        _logger.debug(f"Runtime '{runtime_type}' already registered, skipping")
        return

    _runtimes[runtime_type] = runtime_class


def list_runtime_types() -> list[str]:
    """Get all registered runtime type names."""
    return list(_runtimes.keys())


def get_runtime_class(runtime_type: str) -> Optional[Type['BaseRuntime']]:
    """Get runtime class by runtime type.

    Args:
        runtime_type: Runtime type identifier

    Returns:
        Runtime class or None if not found
    """
    return _runtimes.get(runtime_type)


def get_all_runtime_config_classes() -> Tuple[Type['RuntimeConfig'], ...]:
    """Get all registered runtime config classes as a tuple.

    Returns:
        Tuple of all runtime config classes for use in Union types.
    """
    return tuple(
        runtime_class.config_class
        for runtime_class in _runtimes.values()
        if runtime_class.config_class is not None
    )
