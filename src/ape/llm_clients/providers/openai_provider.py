"""
OpenAI provider implementation.
"""

from typing import Dict, List, Any, Optional, Tuple
import uuid

from .base import BaseProvider
from ..config import ProviderError


class OpenAIProvider(BaseProvider):
    """OpenAI Chat Completions provider."""

    DEFAULT_BASE_URL = "https://api.openai.com/v1/chat/completions"

    def get_request_info(self, session_id: Optional[str] = None) -> Tuple[str, Dict[str, str]]:
        """Get OpenAI request URL and headers."""
        url = self.config.base_url or self.DEFAULT_BASE_URL

        if not self.config.api_key:
            raise ProviderError("OpenAI API key is required (LLMConfig.api_key).")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        if session_id:
            headers["X-Session-Id"] = session_id
        else:
            headers["X-Session-Id"] = str(uuid.uuid4())

        return url, headers

    def build_request_payload(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Build OpenAI Chat Completions payload."""
        payload: Dict[str, Any] = {
            "model": self.config.formal_model_name,
            "messages": messages,
            "max_completion_tokens": self.config.max_tokens, # max_tokens is not supported for all OpenAI models
            "temperature": self.config.temperature,
            "stream": stream,
        }

        if stream:
            # OpenAI only includes token usage in streamed chat-completions responses
            # when stream_options.include_usage is explicitly requested.
            payload["stream_options"] = {"include_usage": True}

        if tools:
            payload["tools"] = tools

        return payload
