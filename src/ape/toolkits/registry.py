"""Tool Registry."""

from typing import Dict, Optional, Type, TYPE_CHECKING
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    from ape.toolkits.base import BaseToolsProvider

# Tool registry: tool_name -> provider_class
_tools: Dict[str, Type['BaseToolsProvider']] = {}
_default_logger = create_logger()

# Executor registry (by file extension)
_executors: Dict[str, Type] = {}   # extension -> executor_class


def register_tool(provider_class: Type['BaseToolsProvider']) -> None:
    """Register tool provider by reading its SUPPORTED_TOOLS class variable.

    Args:
        provider_class: A BaseToolsProvider subclass (the class itself, not an instance)

    Example:
        class MyToolsProvider(BaseToolsProvider):
            SUPPORTED_TOOLS = ["my_tool", "another_tool"]

        register_tool(MyToolsProvider)
        # Registers "my_tool" -> MyToolsProvider
        #           "another_tool" -> MyToolsProvider
    """

    supported_tools = provider_class.SUPPORTED_TOOLS

    for tool_name in supported_tools:
        if tool_name in _tools:
            _default_logger.debug(
                f"Tool '{tool_name}' already registered to {_tools[tool_name].__name__}, "
                f"skipping registration from {provider_class.__name__}"
            )
            continue
        _tools[tool_name] = provider_class


def get_all_tool_names() -> list[str]:
    return list(_tools.keys())


def get_tool_provider_class(tool_name: str) -> type:
    return _tools.get(tool_name)


def list_registered_tools() -> Dict[str, type]:
    return _tools.copy()


# Executor registration
def register_executor(extension: str, executor_class: type) -> None:
    """Register executor for file extension (e.g., '.lean')."""
    _executors[extension] = executor_class


def get_executor_class(extension: str) -> Optional[type]:
    """Get executor class by file extension."""
    return _executors.get(extension)
