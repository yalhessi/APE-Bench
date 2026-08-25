"""
Provider base class - adapter for new ConversationNode architecture
"""

from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
import httpx
import asyncio
import uuid
import json
import re
from ape.utils.logging import create_logger

from ..config import LLMConfig, ProviderError, ContextLengthExceededError
from ..models import TokenUsage

if TYPE_CHECKING:
    import logging
    from ..logger import LLMLogger


class BaseProvider:
    """LLM provider base class."""

    def __init__(self, config: LLMConfig, logger: Optional['logging.LoggerAdapter'] = None, llm_logger: Optional['LLMLogger'] = None):
        self.config = config
        self.logger = logger or create_logger()
        self.llm_logger = llm_logger
        self._session: Optional[httpx.AsyncClient] = None
    
    async def initialize(self):
        """Initialize HTTP session."""
        if self._session is None:
            timeout = httpx.Timeout(
                timeout=self.config.timeout,
                connect=self.config.connect_timeout,
                read=3000.0
            )
            self._session = httpx.AsyncClient(
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
    
    async def cleanup(self):
        """Clean up resources."""
        if self._session and not self._session.is_closed:
            try:
                await self._session.aclose()
            except Exception:
                pass
        self._session = None
    
    def build_request_payload(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
                            stream: bool = False) -> Dict[str, Any]:
        """Build request payload."""
        payload = {
            "model": self.config.formal_model_name,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": stream
        }
        
        if self.config.thinking_budget_tokens > 0:
            payload['thinking'] = {
                "type": "enabled",
                "budget_tokens": self.config.thinking_budget_tokens
            }
            payload["anthropic_beta"] = ["interleaved-thinking-2025-05-14"]
            payload['temperature'] = 1.0
        
        if tools:
            payload["tools"] = tools
        
        return payload
    
    def get_request_info(self, session_id: Optional[str] = None) -> Tuple[str, Dict[str, str]]:
        """Get request URL and headers."""
        url = f"{self.config.base_url}?ak={self.config.api_key}"
        if session_id is None:
            session_id = str(uuid.uuid4())
            self.logger.debug(f"Generated new session_id: {session_id}")
        else:
            self.logger.debug(f"Using provided session_id: {session_id} (for prompt cache)")
        logid = str(uuid.uuid4())
        
        headers = {
            'Content-Type': 'application/json',
            'extra': json.dumps({"session_id": session_id}),
            'X-TT-logid': logid
        }
        return url, headers
    
    async def make_request(self, payload: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send HTTP request with application-layer timeout protection."""
        if self._session is None:
            await self.initialize()
        
        if self.llm_logger:
            await self.llm_logger.log_request(payload, "request")
        
        url, headers = self.get_request_info(session_id)
        
        self.logger.debug(
            f"Sending request to {url[:100]}..., "
            f"model: {payload.get('model')}, "
            f"messages: {len(payload.get('messages', []))}, "
            f"stream: {payload.get('stream', False)}, "
            f"timeout_config: (total={self.config.timeout}s, connect={self.config.connect_timeout}s, sock_read=300s)"
        )
        
        async def _make_request_impl():
            try:
                self.logger.debug(f"Initiating HTTP POST request...")
                response = await self._session.post(url, json=payload, headers=headers)
                self.logger.debug(f"Received response status: {response.status_code}")
                response_data = None
                try:
                    self.logger.debug(f"Reading response JSON body...")
                    response_data = response.json()
                    response.raise_for_status()
                    self.logger.debug(f"Successfully parsed JSON response")
                    if self.llm_logger:
                        await self.llm_logger.log_response(response_data, "response")

                    if 'error' in response_data:
                        self.logger.warning(f"Response contains error field despite HTTP 200 status")
                        error_msg = self.parse_error_response(response_data)
                        raise ProviderError(f"API returned error: {error_msg}")

                    self.logger.debug(
                        f"Received response - "
                        f"status: {response.status_code}, "
                        f"choices: {len(response_data.get('choices', []))}"
                    )

                    return response_data
                except httpx.HTTPStatusError as e:
                    if response_data is None:
                        try:
                            response_text = response.text
                            response_data = {"error": response_text}
                        except:
                            response_data = {"error": f"HTTP {response.status_code}: Failed to read response"}

                    try:
                        error_msg = self.parse_error_response(response_data)
                    except ContextLengthExceededError:
                        raise
                    except:
                        error_msg = f"HTTP {response.status_code}: {response_data}"

                    self.logger.error(
                        f"API request failed - "
                        f"status: {response.status_code}, "
                        f"error: {error_msg}"
                    )
                    raise ProviderError(f"API request failed: {error_msg}")
            except httpx.RequestError as e:
                error_msg = str(e)
                self.logger.error(f"API connection failed: {error_msg}")
                raise ProviderError(f"API connection failed: {error_msg}")
        
        try:
            return await asyncio.wait_for(_make_request_impl(), timeout=self.config.timeout)
        except asyncio.TimeoutError:
            error_msg = f"Request timeout ({self.config.timeout} seconds) - application-layer forced interruption"
            self.logger.error(error_msg)
            raise ProviderError(error_msg)
    
    async def make_streaming_request(self, payload: Dict[str, Any], session_id: Optional[str] = None):
        """Send streaming request with application-layer timeout protection."""
        if self._session is None:
            await self.initialize()

        if self.llm_logger:
            await self.llm_logger.log_request(payload, "streaming_request")

        url, headers = self.get_request_info(session_id)

        self.logger.debug(f"Sending streaming request to {url[:100]}...")

        async def _make_streaming_request_impl():
            try:
                response = await self._session.post(url, json=payload, headers=headers)
                try:
                    error_data = None
                    if response.status_code != 200:
                        try:
                            error_data = response.json()
                        except:
                            pass

                    response.raise_for_status()
                    self.logger.debug(f"Streaming request started - status: {response.status_code}")
                    return response
                except httpx.HTTPStatusError as e:
                    try:
                        if error_data:
                            error_msg = self.parse_error_response(error_data)
                        else:
                            error_msg = f"HTTP {response.status_code}: {str(e)}"
                    except ContextLengthExceededError:
                        await response.aclose()
                        raise
                    except:
                        error_msg = f"HTTP {response.status_code}: {str(e)}"
                    finally:
                        await response.aclose()

                    self.logger.error(
                        f"Streaming request failed - "
                        f"status: {response.status_code}, "
                        f"error: {error_msg}"
                    )
                    raise ProviderError(f"Streaming request failed: {error_msg}")
            except httpx.RequestError as e:
                error_msg = str(e)
                self.logger.error(f"Streaming connection failed: {error_msg}")
                raise ProviderError(f"Streaming connection failed: {error_msg}")

        try:
            return await asyncio.wait_for(_make_streaming_request_impl(), timeout=self.config.timeout)
        except asyncio.TimeoutError:
            error_msg = f"Streaming request timeout ({self.config.timeout} seconds) - application-layer forced interruption"
            self.logger.error(error_msg)
            raise ProviderError(error_msg)
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int,
                       cache_read_input_tokens: int = 0,
                       cache_creation_input_tokens: int = 0) -> tuple[float, float]:
        """
        Calculate cost.

        Args:
            input_tokens: new input tokens
            output_tokens: output tokens
            cache_read_input_tokens: tokens read from cache
            cache_creation_input_tokens: tokens created for cache

        Returns:
            (total_cost, cached_total_cost) tuple:
            - total_cost: cost without cache discount (cache_read + input are calculated as input price)
            - cached_total_cost: cost with cache discount
        """
        if input_tokens == 0 and output_tokens == 0 and cache_read_input_tokens == 0:
            return 0.0, 0.0

        from ..config import DEFAULT_COST_MODEL, MODEL_MAPPINGS

        cost_model = getattr(self.config, "cost_model", DEFAULT_COST_MODEL)
        for config in MODEL_MAPPINGS.values():
            if config["model_name"] == self.config.formal_model_name:
                # The one thing the two models disagree about: is `cache_read_input_tokens`
                # part of `input_tokens`, or separate from it?
                #
                # `prompt_inclusive` says part of. Then the full prompt is `input_tokens`,
                # and the portion billed at the normal rate is what is left after removing
                # the cached part. `prompt_exclusive` says separate, so the full prompt is
                # the sum and `input_tokens` is already the uncached remainder.
                #
                # Getting this backwards charges the cached tokens twice — at full rate
                # inside `input_tokens` and again at the cache rate — which inflates *both*
                # returned figures, not just the nominal one.
                if cost_model == "prompt_inclusive":
                    total_input_tokens = input_tokens
                    # Defensive: a provider that ever reports more cached than prompt tokens
                    # is not describing a subset, so fall back rather than go negative.
                    uncached_input_tokens = (
                        input_tokens - cache_read_input_tokens
                        if cache_read_input_tokens <= input_tokens else input_tokens
                    )
                else:
                    total_input_tokens = cache_read_input_tokens + input_tokens
                    uncached_input_tokens = input_tokens

                # `total_cost` is the counterfactual: what the call would have cost with no
                # cache at all. `cached_total_cost` is what was actually billed.
                total_cost = (total_input_tokens / 1_000_000) * config["input_per_1M"] + \
                            (output_tokens / 1_000_000) * config["output_per_1M"]

                input_cost = (uncached_input_tokens / 1_000_000) * config["input_per_1M"]

                cache_read_cost = 0.0
                if cache_read_input_tokens > 0 and config["cached_input_per_1M_usd"]:
                    cache_read_cost = (cache_read_input_tokens / 1_000_000) * config["cached_input_per_1M_usd"]
                
                cache_creation_cost = 0.0
                if cache_creation_input_tokens > 0 and config["cache_creation_per_1M_usd"]:
                    cache_creation_cost = (cache_creation_input_tokens / 1_000_000) * config["cache_creation_per_1M_usd"]
                
                output_cost = (output_tokens / 1_000_000) * config["output_per_1M"]
                
                cached_total_cost = input_cost + cache_read_cost + cache_creation_cost + output_cost
                
                return total_cost, cached_total_cost
        
        raise ValueError(f"Model pricing configuration not found for: {self.config.formal_model_name}")
    
    def parse_usage(self, usage_data: Dict[str, Any]) -> TokenUsage:
        """
        Parse usage information from usage dictionary.
        
       Unified usage structure (all models):
        {
            "prompt_tokens": 5165,        # new input tokens (without cache)
            "completion_tokens": 82,
            "total_tokens": 15533,        # = prompt_tokens + cached_tokens + completion_tokens
            "completion_tokens_details": {
                "reasoning_tokens": 417
            },
            "prompt_tokens_details": {
                "cached_tokens": 10286    # this is cache_read_input_tokens
            }
        }
        """
        input_tokens = usage_data.get("prompt_tokens", 0)
        output_tokens = usage_data.get("completion_tokens", 0)
        total_tokens = usage_data.get("total_tokens", 0)
        
        # extract reasoning_tokens from completion_tokens_details
        completion_details = usage_data.get("completion_tokens_details", {})
        reasoning_tokens = completion_details.get("reasoning_tokens", 0) if completion_details else 0
        
        # extract cache related fields from prompt_tokens_details
        prompt_details = usage_data.get("prompt_tokens_details", {})
        
        # cache_read_input_tokens: try top level, then details.cached_tokens, then details.cache_read_input_tokens
        cache_read_input_tokens = usage_data.get("cache_read_input_tokens", 0)
        if cache_read_input_tokens == 0 and prompt_details:
            # cached_tokens is cache_read_input_tokens
            cache_read_input_tokens = prompt_details.get("cached_tokens", 0)
            if cache_read_input_tokens == 0:
                cache_read_input_tokens = prompt_details.get("cache_read_input_tokens", 0)
        
        # cache_creation_input_tokens: try top level, then details
        cache_creation_input_tokens = usage_data.get("cache_creation_input_tokens", 0)
        if cache_creation_input_tokens == 0 and prompt_details:
            cache_creation_input_tokens = prompt_details.get("cache_creation_input_tokens", 0)
        
        total_cost, cached_total_cost = self._calculate_cost(
            input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens
        )
        
        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            reasoning_tokens=reasoning_tokens if reasoning_tokens > 0 else None,
            cache_creation_input_tokens=cache_creation_input_tokens if cache_creation_input_tokens > 0 else None,
            cache_read_input_tokens=cache_read_input_tokens if cache_read_input_tokens > 0 else None,
            total_cost=total_cost,
            cached_total_cost=cached_total_cost
        )
    
    def parse_error_response(self, response_data: dict) -> str:
        """Parse error response."""
        error_message = ""
        if isinstance(response_data, dict):
            if 'error' in response_data:
                error = response_data['error']
                if isinstance(error, dict):
                    error_message = error.get('message', str(error))
                else:
                    error_message = str(error)
            elif 'message' in response_data:
                error_message = response_data['message']
            else:
                error_message = str(response_data)
        else:
            error_message = str(response_data)

        # check context length exceeded model capability errors (inline regex matching)
        # note: exclude QPM rate limit errors (e.g. "reach token limit")
        if error_message and any([
            # Input length XXX exceeds ... length XXX
            re.search(r'input\s+length.*exceed.*length', error_message, re.IGNORECASE),
            # exceeded model/context token limit (exceeded, not reach)
            re.search(r'exceed(ed|s)\s+(model|context).*token\s+limit', error_message, re.IGNORECASE),
            # context length exceeded
            re.search(r'context[_\s]length[_\s]exceed', error_message, re.IGNORECASE),
            # maximum context length
            re.search(r'maximum\s+context\s+length', error_message, re.IGNORECASE),
            # payload/request too large/long
            re.search(r'(payload|request)\s+(too\s+)?(large|long)', error_message, re.IGNORECASE),
        ]):
            raise ContextLengthExceededError(error_message)

        return error_message

    def postprocess_nodes(self, nodes: List):
        """
        Post-process ConversationNode list.

        Default implementation: return original nodes, no processing.
        Subclasses can override this method to implement specific post-processing logic (e.g. extract tool calls from text).

        Note: this method will be executed for both streaming and non-streaming.
        """
        return nodes
