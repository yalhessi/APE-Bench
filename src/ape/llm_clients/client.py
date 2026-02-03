"""
LLM Client Module.

Provides a unified interface for interacting with various LLM providers
through a conversation session-based architecture.
"""

import traceback
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union, TYPE_CHECKING
from tenacity import retry, stop_after_attempt, wait_exponential, wait_random, wait_combine

from ape.utils.logging import create_logger

from .config import LLMConfig, LLMProvider, ProviderError, ContextLengthExceededError, MalformedResponseError
from .models import ConversationSession, ConversationNode, TokenUsage, ContentBlock
from .adapters import ResponseProcessor, StreamingProcessor, MessageFormatter
from .providers import BaseProvider
from .logger import LLMLogger

if TYPE_CHECKING:
    import logging

class LLMClient:
    """Unified LLM client supporting multiple providers through conversation sessions."""

    def __init__(self, config: LLMConfig, logger: Optional['logging.LoggerAdapter'] = None, enable_raw_logging: bool = True):
        self.config = config
        self.logger = logger or create_logger()

        self.llm_logger = LLMLogger() if enable_raw_logging else None
        self.provider = self._create_provider()

        self.response_processor = ResponseProcessor(logger=self.logger)
        self.streaming_processor = StreamingProcessor(logger=self.logger, llm_logger=self.llm_logger)
        self.message_formatter = MessageFormatter()

    def _create_provider(self):
        """Create provider instance based on configuration."""
        return BaseProvider(self.config, self.logger, self.llm_logger)

    async def __aenter__(self):
        """Enter async context manager."""
        await self.provider.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.provider.cleanup()

    async def close(self):
        """Close the client and cleanup resources."""
        await self.provider.cleanup()
    
    async def call_api(self,
                      session: ConversationSession,
                      tools: Optional[List[Dict[str, Any]]] = None,
                      max_tokens: Optional[int] = None,
                      thinking_budget_tokens: Optional[int] = None,
                      temperature: Optional[float] = None,
                      streaming: Optional[bool] = None,
                      streaming_callback: Optional[Callable[[str, str], None]] = None,
                      meta_info: Optional[Dict[str, Any]] = None,
                      interrupt_event: Optional['asyncio.Event'] = None) -> tuple[List[ConversationNode], TokenUsage, Dict[str, Any]]:
        """Execute API call using the conversation session.

        Args:
            session: Conversation session object.
            tools: List of tool definitions.
            max_tokens: Maximum tokens (overrides config).
            thinking_budget_tokens: Thinking budget tokens (overrides config).
            temperature: Temperature parameter (overrides config).
            streaming: Whether to enable streaming response.
            streaming_callback: Callback function for streaming output.
            meta_info: Metadata dictionary.
            interrupt_event: Event for interrupting execution.

        Returns:
            Tuple of (conversation_nodes, token_usage, raw_response).
            raw_response contains the original API response for RL training.
        """
        start_time = time.time()

        api_messages = self.message_formatter.format_for_api(session)

        def log_retry_attempt(retry_state):
            exception = retry_state.outcome.exception()
            attempt_number = retry_state.attempt_number
            wait_time = retry_state.next_action.sleep if retry_state.next_action else 0
            
            error_msg = str(exception)
            error_type = type(exception).__name__
            
            self.logger.warning(
                f"API call failed, retrying - "
                f"attempt: {attempt_number}/{self.config.retry_max_attempts}, "
                f"wait: {wait_time:.2f}s, "
                f"error_type: {error_type}, "
                f"error_msg: {error_msg[:200]}"
            )

        from ape.llm_clients.adapters.streaming_processor import StreamingInterruptedError

        @retry(
            stop=stop_after_attempt(self.config.retry_max_attempts),
            wait=wait_combine(
                wait_exponential(multiplier=1, min=self.config.retry_min_wait, max=self.config.retry_max_wait),
                wait_random(0, 10)
            ),
            retry=lambda retry_state: (
                False if not retry_state.outcome.exception() else
                False if (
                    retry_state.outcome.exception() and (
                        isinstance(retry_state.outcome.exception(), ContextLengthExceededError) or
                        isinstance(retry_state.outcome.exception(), MalformedResponseError) or
                        isinstance(retry_state.outcome.exception(), StreamingInterruptedError)
                    )
                ) else True
            ),
            before_sleep=log_retry_attempt,
            reraise=True
        )
        async def _do_api_call():
            try:
                self._update_config_overrides(max_tokens, thinking_budget_tokens, temperature, meta_info)

                use_streaming = streaming if streaming is not None else self.config.streaming

                payload = self.provider.build_request_payload(
                    messages=api_messages,
                    tools=tools,
                    stream=use_streaming
                )

                self.logger.debug(
                    f"Starting API call - "
                    f"streaming: {use_streaming}, "
                    f"model: {self.config.model_name}, "
                    f"messages_count: {len(api_messages)}, "
                    f"tools_count: {len(tools) if tools else 0}, "
                    f"max_tokens: {self.config.max_tokens}, "
                    f"temperature: {self.config.temperature}"
                )

                if use_streaming:
                    nodes, usage, raw_response = await self._handle_streaming_request(
                        payload, session, streaming_callback, interrupt_event
                    )
                else:
                    raw_response = await self.provider.make_request(payload, session.session_id)

                    nodes, usage = self.response_processor.process_response(
                        raw_response=raw_response,
                        session_id=session.session_id,
                        cwd=session.nodes[0].cwd if session.nodes else "/",
                        parse_usage_fn=self.provider.parse_usage
                    )

                nodes = self.provider.postprocess_nodes(nodes)

                elapsed_time = time.time() - start_time
                self.logger.info(
                    f"{'Streaming' if use_streaming else 'Non-streaming'} API call succeeded - "
                    f"elapsed: {elapsed_time:.2f}s, "
                    f"nodes: {len(nodes)}, "
                    f"tokens: {usage.total_tokens}"
                )
                return nodes, usage, raw_response
                    
            except (MalformedResponseError, ContextLengthExceededError, StreamingInterruptedError) as e:
                elapsed_time = time.time() - start_time

                if isinstance(e, StreamingInterruptedError):
                    self.logger.info(
                        f"Streaming interrupted by user - "
                        f"elapsed: {elapsed_time:.2f}s"
                    )
                elif isinstance(e, MalformedResponseError):
                    self.logger.warning(
                        f"MalformedResponseError occurred - "
                        f"elapsed: {elapsed_time:.2f}s, "
                        f"error: {str(e)}, "
                        f"streaming: {use_streaming} "
                        f"(will retry)"
                    )
                else:
                    self.logger.error(
                        f"ContextLengthExceededError occurred - "
                        f"elapsed: {elapsed_time:.2f}s, "
                        f"error: {str(e)} "
                        f"(will not retry)"
                    )
                raise
            except Exception as e:
                elapsed_time = time.time() - start_time
                self.logger.error(
                    f"Unexpected error occurred - "
                    f"elapsed: {elapsed_time:.2f}s, "
                    f"error_type: {type(e).__name__}, "
                    f"error: {str(e)}"
                )
                raise ProviderError(f"API call failed: {traceback.format_exc()}")

        return await _do_api_call()
    
    def _update_config_overrides(self, max_tokens, thinking_budget_tokens, temperature, meta_info):
        """Update configuration overrides."""
        if max_tokens is not None:
            self.config.max_tokens = max_tokens
        if thinking_budget_tokens is not None:
            self.config.thinking_budget_tokens = thinking_budget_tokens
        if temperature is not None:
            self.config.temperature = temperature

    async def _handle_streaming_request(self, payload: Dict[str, Any],
                                       session: ConversationSession,
                                       streaming_callback: Optional[Callable[[str, str], None]] = None,
                                       interrupt_event: Optional['asyncio.Event'] = None) -> tuple[List[ConversationNode], TokenUsage, Dict[str, Any]]:
        """Handle streaming request."""
        response_stream = await self.provider.make_streaming_request(payload, session.session_id)
        try:
            nodes, usage, raw_chunks = await self.streaming_processor.process_streaming(
                response_stream=response_stream,
                session_id=session.session_id,
                cwd=session.nodes[0].cwd if session.nodes else "/",
                parse_usage_fn=self.provider.parse_usage,
                parse_error_fn=self.provider.parse_error_response,
                callback=streaming_callback,
                relay_mode=self.config.relay_mode,
                interrupt_event=interrupt_event
            )

            # Streaming: raw_chunks is already in non-streaming format (merged response)
            return nodes, usage, raw_chunks
        finally:
            try:
                await response_stream.aclose()
            except (AttributeError, TypeError):
                pass
