"""Bash execution support."""

from .tools import BashExecuteToolsProvider
from .config import BashExecuteToolConfig

# Register BashExecuteToolsProvider as executor for .sh files
from ape.toolkits.registry import register_executor
register_executor('.sh', BashExecuteToolsProvider)

__all__ = [
    "BashExecuteToolsProvider",
    "BashExecuteToolConfig",
]
