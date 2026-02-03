"""Runtime Factory.

Provides factory functions for creating runtime instances and configurations.
"""

from typing import Optional, TYPE_CHECKING

from ape.runtime.base import RuntimeConfig
from ape.runtime.registry import get_runtime_class, list_runtime_types

if TYPE_CHECKING:
    import logging
    from ape.runtime.base import BaseRuntime


def create_runtime(
    config: RuntimeConfig,
    logger: Optional['logging.LoggerAdapter'] = None
) -> 'BaseRuntime':
    """Create a runtime instance from a RuntimeConfig object.

    Args:
        config: RuntimeConfig instance (e.g., SandboxRuntimeConfig, ContainerRuntimeConfig)
        logger: Optional logger instance

    Returns:
        Runtime instance

    Raises:
        ValueError: If runtime_type is not found or config is invalid
    """
    if not hasattr(config, 'runtime_type'):
        raise ValueError(f"RuntimeConfig must have a 'runtime_type' field. Got: {type(config)}")

    runtime_type = config.runtime_type
    runtime_class = get_runtime_class(runtime_type)

    if runtime_class is None:
        available = list_runtime_types()
        raise ValueError(f"Unknown runtime: {runtime_type}. Available: {available}")

    return runtime_class(config=config, logger=logger)


def create_runtime_config_for_type(
    runtime_type: str,
    **overrides
) -> RuntimeConfig:
    """Create runtime-specific configuration from runtime type.

    Args:
        runtime_type: Runtime type identifier (e.g., 'sandbox', 'container')
        **overrides: Configuration parameters to override

    Returns:
        Runtime-specific configuration object

    Raises:
        ValueError: If runtime type is unknown
    """
    runtime_class = get_runtime_class(runtime_type)
    if runtime_class is None:
        available = list_runtime_types()
        raise ValueError(f"Unknown runtime type: {runtime_type}. Available: {available}")

    runtime_config_class = runtime_class.config_class
    return runtime_config_class.model_validate(overrides)
