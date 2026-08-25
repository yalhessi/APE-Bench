"""
OpenAI-specific message formatter.
"""

from typing import Dict, Any, List

from .message_formatter import MessageFormatter
from ..models import ConversationSession


class OpenAIMessageFormatter(MessageFormatter):
    """Formats conversation nodes for OpenAI Chat Completions."""

    def format_for_api(self, session: ConversationSession) -> List[Dict[str, Any]]:
        """Convert ConversationSession to OpenAI-compatible API messages."""
        base_messages = super().format_for_api(session)

        normalized_messages: List[Dict[str, Any]] = []
        for message in base_messages:
            normalized: Dict[str, Any] = {
                "role": message.get("role"),
                "content": message.get("content", ""),
            }

            if message.get("tool_calls"):
                normalized["tool_calls"] = message["tool_calls"]
            if message.get("tool_call_id"):
                normalized["tool_call_id"] = message["tool_call_id"]
            if message.get("name"):
                normalized["name"] = message["name"]

            normalized_messages.append(normalized)

        return normalized_messages
