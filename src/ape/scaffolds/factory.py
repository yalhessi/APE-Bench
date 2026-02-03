"""
Scaffold Factory Module.

Provides factory functions for creating scaffold instances and configurations.
"""

from typing import TYPE_CHECKING
from .registry import get_scaffold_class, list_scaffold_types

if TYPE_CHECKING:
    from .base import BaseScaffold
    from .config import BaseScaffoldConfig


def create_scaffold(name: str, **kwargs) -> 'BaseScaffold':
    """Create a scaffold instance by name.

    Args:
        name: Scaffold name.
        **kwargs: Initialization parameters.

    Returns:
        Scaffold instance.

    Raises:
        ValueError: If scaffold name is unknown.
    """
    scaffold_class = get_scaffold_class(name)
    if scaffold_class is None:
        available = list_scaffold_types()
        raise ValueError(f"Unknown scaffold: {name}. Available: {available}")

    return scaffold_class(**kwargs)


def create_scaffold_config_for_type(scaffold_type: str, base_config: 'BaseScaffoldConfig', **overrides) -> 'BaseScaffoldConfig':
    """Create scaffold-specific configuration from base configuration.

    Args:
        scaffold_type: Scaffold type.
        base_config: Base configuration object.
        **overrides: Configuration parameters to override.

    Returns:
        Scaffold-specific configuration object.

    Raises:
        ValueError: If scaffold type is unknown.
    """
    scaffold_class = get_scaffold_class(scaffold_type)
    if scaffold_class is None:
        available = list_scaffold_types()
        raise ValueError(f"Unknown scaffold: {scaffold_type}. Available: {available}")

    scaffold_config_class = scaffold_class.config_class

    config_args = {
        'runs_base_dir': base_config.runs_base_dir,
        'target_workspace': base_config.target_workspace,
        'task_config': base_config.task_config,
        'execution': base_config.execution,
        'llm_config': base_config.llm_config,
        'tools_config': base_config.tools_config,
        'runtime_config': base_config.runtime_config,
    }

    config_args.update(overrides)

    return scaffold_config_class.model_validate(config_args)
