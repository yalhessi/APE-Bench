"""
LLM Clients - Modern LLM calling and conversation management.

Core design principles:
1. Modern data modeling using Pydantic
2. Complete separation of LLM API layer and conversation management
3. Compliant with Claude Code standard conversation format
4. Provides unified parsing and tool calling interface
"""

from .models import ContentBlock, ConversationMessage, ToolDefinitionsMessage, ConversationNode, ConversationSession, TokenUsage
from .config import LLMConfig, LLMProvider
from .client import LLMClient
from .adapters import ResponseProcessor, StreamingProcessor, MessageFormatter
from .logger import LLMLogger

__version__ = "3.0.0"

__all__ = [
    # Core components
    'LLMClient',

    # Core data models
    'ContentBlock',
    'ConversationMessage',
    'ToolDefinitionsMessage',
    'ConversationNode',
    'ConversationSession',
    'TokenUsage',

    # Configuration
    'LLMConfig',
    'LLMProvider',

    # Processor components
    'ResponseProcessor',
    'StreamingProcessor',
    'MessageFormatter',

    # Logger component
    'LLMLogger',
]
