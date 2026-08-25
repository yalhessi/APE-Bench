"""Generic code tools Provider and language interface"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Annotated, Dict, Any, Set, Type

from fastmcp import FastMCP
from pydantic import Field

from ape.toolkits.base import BaseToolsProvider


# ========== Language Provider Registry ==========

# File extension -> Provider class mapping
LANGUAGE_PROVIDER_REGISTRY: Dict[str, Type['BaseToolsProvider']] = {}


def register_language_provider(extension: str, provider_class: Type['BaseToolsProvider']):
    """
    Register language provider

    Args:
        extension: File extension (e.g. '.lean', '.py')
        provider_class: Provider class (must implement LanguageProviderInterface)
    """
    LANGUAGE_PROVIDER_REGISTRY[extension] = provider_class


# ========== Language Provider Interface ==========

class LanguageProviderInterface(ABC):
    """
    Language Provider Interface

    All concrete language ToolsProviders must implement methods in this interface
    to be routed and called by BaseCodeToolsProvider.
    """

    @abstractmethod
    async def hover(
        self,
        file_path: Path,
        line: int,
        content_snippet: str
    ) -> Dict[str, Any]:
        """Get hover information"""
        pass

    @abstractmethod
    async def goto(
        self,
        file_path: Path,
        line: int,
        content_snippet: str
    ) -> Dict[str, Any]:
        """Jump to definition"""
        pass

    # @abstractmethod
    # async def diagnostics(self, file_path: Path) -> Dict[str, Any]:
    #     """Get file diagnostics"""
    #     pass

    # async def references(
    #     self,
    #     file_path: Path,
    #     line: int,
    #     content_snippet: str
    # ) -> Dict[str, Any]:
    #     """Find references (optional implementation)"""
    #     return {
    #         "success": False,
    #         "error": "References not supported for this language"
    #     }


# ========== Generic Code Tools Provider ==========

class BaseCodeToolsProvider(BaseToolsProvider):
    """
    Generic Code Tools Provider

    Provides language-agnostic code tools:
    - code_hover: Hover information
    - code_goto: Jump to definition
    - code_check: Diagnostic check
    - code_references: Find references

    Routes to appropriate language provider based on file extension.
    """

    SUPPORTED_TOOLS = [
        "code_hover",
        "code_goto",
        # "code_check",
        "code_references",
    ]

    def __init__(
        self,
        task=None,
        config=None,
        logger=None,
        confirmation_bridge=None,
        is_cli_mode=False,
    ):
        super().__init__(
            task=task,
            config=config,
            logger=logger,
            confirmation_bridge=confirmation_bridge,
            is_cli_mode=is_cli_mode,
        )

        # Language provider registry: extension -> provider_instance
        self._language_providers: Dict[str, LanguageProviderInterface] = {}

    def sync_tool_instances(self, tool_instances: Dict[type, 'BaseToolsProvider']) -> None:
        """Sync tool instances and initialize language providers."""
        super().sync_tool_instances(tool_instances)
        # Initialize language providers after tool_instances is synced
        self._initialize_language_providers()

    def _initialize_language_providers(self):
        """
        Initialize language providers

        Get corresponding provider instances from tool_instances based on
        global LANGUAGE_PROVIDER_REGISTRY.
        """
        for extension, provider_class in LANGUAGE_PROVIDER_REGISTRY.items():
            if provider_class in self.tool_instances:
                provider_instance = self.tool_instances[provider_class]
                self._language_providers[extension] = provider_instance
                self.logger.debug(f"Registered language provider for {extension}: {provider_class.__name__}")
            else:
                self.logger.debug(f"Language provider {provider_class.__name__} for {extension} not in tool_instances")

    def _route_to_provider(self, file_path: Path) -> LanguageProviderInterface:
        """Route to appropriate language provider based on file extension"""
        extension = file_path.suffix

        provider = self._language_providers.get(extension)
        if not provider:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                f"Supported: {list(self._language_providers.keys())}"
            )

        return provider

    def register_tools(self, mcp: FastMCP, enabled_tools: Set[str]) -> None:
        """Register generic code tools to MCP server"""
        # Initialize language providers
        self._initialize_language_providers()

        # Dynamically generate supported languages list
        supported_languages = ", ".join(sorted(
            ext.lstrip('.').capitalize()
            for ext in self._language_providers.keys()
        ))

        # Register generic tools

        if "code_hover" in enabled_tools:
            @mcp.tool(description=f"""Get hover information at code position.

**Supported**: {supported_languages}

**Returns**: Type information, documentation, diagnostics at position""")
            async def code_hover(
                file_path: Annotated[str, Field(description="Workspace file path (e.g., scratch/file.lean)")],
                line: Annotated[int, Field(description="Line number (1-indexed)", ge=1)],
                content: Annotated[str, Field(description="Unique content snippet on that line to identify position")]
            ) -> Dict[str, Any]:
                """Get code hover information (routed to appropriate language provider)"""
                try:
                    provider = self._route_to_provider(Path(file_path))
                    result = await provider.hover(Path(file_path), line, content)
                    self._record_task_tool_trace(
                        "code_hover",
                        file_path=file_path,
                        line=line,
                    )
                    return result
                except Exception as e:
                    self.logger.error(f"code_hover error: {e}")
                    return {"success": False, "error": str(e)}

        if "code_goto" in enabled_tools:
            @mcp.tool(description=f"""Jump to definition of a symbol.

**Supported**: {supported_languages}

**Returns**: Definition locations with file path, line, content""")
            async def code_goto(
                file_path: Annotated[str, Field(description="Workspace file path")],
                line: Annotated[int, Field(description="Line number where symbol appears (1-indexed)", ge=1)],
                content: Annotated[str, Field(description="Symbol name or unique snippet to identify")]
            ) -> Dict[str, Any]:
                """Jump to definition (routed to appropriate language provider)"""
                try:
                    provider = self._route_to_provider(Path(file_path))
                    result = await provider.goto(Path(file_path), line, content)
                    self._record_task_tool_trace(
                        "code_goto",
                        file_path=file_path,
                        line=line,
                    )
                    return result
                except Exception as e:
                    self.logger.error(f"code_goto error: {e}")
                    return {"success": False, "error": str(e)}

#         if "code_check" in enabled_tools:
#             @mcp.tool(description=f"""Check file for errors and warnings.

# **Supported**: {supported_languages}

# **Returns**: diagnostics, error_count, warning_count, has_errors""")
#             async def code_check(
#                 file_path: Annotated[str, Field(description="Workspace file path to check")]
#             ) -> Dict[str, Any]:
#                 """Check file diagnostics (routed to appropriate language provider)"""
#                 try:
#                     provider = self._route_to_provider(Path(file_path))
#                     return await provider.diagnostics(Path(file_path))
#                 except Exception as e:
#                     self.logger.error(f"code_check error: {e}")
#                     return {"success": False, "error": str(e)}

#         if "code_references" in enabled_tools:
#             @mcp.tool(description=f"""Find all references to a symbol.

# **Supported**: {supported_languages}

# **Returns**: references list and count""")
#             async def code_references(
#                 file_path: Annotated[str, Field(description="Workspace file path")],
#                 line: Annotated[int, Field(description="Line number where symbol appears (1-indexed)", ge=1)],
#                 content: Annotated[str, Field(description="Symbol name or unique snippet")]
#             ) -> Dict[str, Any]:
#                 """Find references (routed to appropriate language provider)"""
#                 try:
#                     provider = self._route_to_provider(Path(file_path))
#                     return await provider.references(Path(file_path), line, content)
#                 except Exception as e:
#                     self.logger.error(f"code_references error: {e}")
#                     return {"success": False, "error": str(e)}


# Register tool at end of file
from ape.toolkits.registry import register_tool
register_tool(BaseCodeToolsProvider)
