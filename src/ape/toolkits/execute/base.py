"""Base class for execute/verification tools providers."""

from abc import abstractmethod
from typing import Dict, Any
from ape.toolkits.base import BaseToolsProvider


class BaseExecuteToolsProvider(BaseToolsProvider):
    """Base class for code execution/verification tools providers."""

    @abstractmethod
    async def execute(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        Execute/verify code and return result.

        Args:
            code: Source code to execute/verify
            **kwargs: Additional parameters

        Returns:
            Dict with 'success' key and execution details
        """
        pass
