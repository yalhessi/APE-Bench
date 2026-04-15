"""Base Toolkit Module."""

from pathlib import Path
from typing import List, Optional, Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ape.tasks.base import BaseTask
    from ape.tasks.models import WorkspaceInfo
    import logging


class BaseToolsProvider:
    """Base class for all tools providers."""

    SUPPORTED_TOOLS: List[str] = []

    def __init__(
        self,
        task: Optional["BaseTask"] = None,
        config: Optional[Any] = None,
        logger: Optional['logging.LoggerAdapter'] = None,
        confirmation_bridge: Optional[Any] = None,
        is_cli_mode: bool = False,
    ):
        """Initialize tools provider.

        Args:
            task: Task instance containing all context (data, workspaces, etc.)
            config: Configuration (toolkit config or scaffold config)
            logger: Logger instance
            confirmation_bridge: Confirmation bridge for CLI mode
            is_cli_mode: Whether in CLI mode
        """
        self.task = task
        self.config = config
        self.logger = logger
        self.confirmation_bridge = confirmation_bridge
        self.is_cli_mode = is_cli_mode
        self.tool_instances: Dict[type, "BaseToolsProvider"] = {}

    def sync_tool_instances(self, tool_instances: Dict[type, "BaseToolsProvider"]) -> None:
        """Sync tool instances after all tools are initialized.

        This method is called by MCPManager after all tool providers are created,
        ensuring each provider has access to the complete set of tool instances.

        Args:
            tool_instances: Complete dictionary of tool instances (tool_class -> instance)
        """
        self.tool_instances = tool_instances

    @staticmethod
    def _normalize_trace_value(value: Any) -> Any:
        """Normalize lightweight tool-trace metadata for task-side reporting."""
        if value is None:
            return None
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            normalized = " ".join(value.split())
            if len(normalized) > 200:
                return f"{normalized[:197]}..."
            return normalized
        if isinstance(value, list):
            normalized_items = []
            for item in value[:8]:
                normalized_item = BaseToolsProvider._normalize_trace_value(item)
                if isinstance(normalized_item, (str, int, float, bool)):
                    normalized_items.append(normalized_item)
            return normalized_items
        return None

    def _record_task_tool_trace(self, tool_name: str, **metadata: Any) -> None:
        """Forward compact tool-call metadata to the active task when supported."""
        if self.task is None:
            return

        recorder = getattr(self.task, "_record_tool_usage_trace", None)
        if not callable(recorder):
            return

        normalized_metadata = {}
        for key, value in metadata.items():
            normalized_value = self._normalize_trace_value(value)
            if normalized_value is not None:
                normalized_metadata[key] = normalized_value

        recorder(tool_name=tool_name, **normalized_metadata)

    def register_tools(self, mcp: 'FastMCP', enabled_tools: set[str]) -> None:
        """Register tools to MCP server."""
        raise NotImplementedError("Subclasses must implement register_tools")

    async def cleanup(self) -> None:
        """Clean up resources held by this tool provider.

        Subclasses should override this method if they hold resources
        that need explicit cleanup (e.g., browser sessions, database connections).
        The default implementation does nothing.
        """
        pass

    @classmethod
    def get_required_resources(
        cls,
        scratch_workspace_info: Optional['WorkspaceInfo'] = None,
        target_workspace_info: Optional['WorkspaceInfo'] = None,
        reference_workspaces_info: Optional[List['WorkspaceInfo']] = None,
        config: Optional[Any] = None,
    ) -> List[tuple[Path, Optional[Path]]]:
        """Get resources required by this toolkit.

        Args:
            scratch_workspace_info: Scratch workspace info
            target_workspace_info: Target workspace info
            reference_workspaces_info: Reference workspaces info list
            config: Toolkit configuration or scaffold config

        Returns:
            List of (host_path, container_path) tuples.
            container_path=None means use default PROJECT_ROOT-based mapping.
        """
        return []

    @classmethod
    def get_environment_config(cls, config: Optional[Any] = None) -> Dict[str, str]:
        """Get environment variables required by this toolkit in container.

        Args:
            config: Toolkit configuration or scaffold config

        Returns:
            Dictionary of environment variable name -> value pairs.
            These will be injected into the container environment.
        """
        return {}
