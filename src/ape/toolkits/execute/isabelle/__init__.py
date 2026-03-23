"""Isabelle execution and verification support."""

from .config import IsabelleVerifyToolConfig
from .core import IsabelleVerificationEngine
from .tools import IsabelleVerifyToolsProvider

from ape.toolkits.registry import register_executor

register_executor('.thy', IsabelleVerifyToolsProvider)

__all__ = [
    "IsabelleVerifyToolConfig",
    "IsabelleVerificationEngine",
    "IsabelleVerifyToolsProvider",
]
