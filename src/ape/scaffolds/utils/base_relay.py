"""
Base Relay Session - Abstract base class for HTTP relay services

This module provides the abstract base for all relay implementations,
handling common HTTP service setup, conversation recording, and token tracking.
"""

import json
import uuid
import aiofiles
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ape.utils.logging import create_logger
from ape.llm_clients import LLMClient, LLMConfig
from ape.llm_clients.models import ConversationSession, ConversationNode, ContentBlock, TokenUsage
from .conversation_tree import ConversationPrefixTreeManager

if TYPE_CHECKING:
    import logging


class BaseRelaySession(ABC):
    """
    Base Relay Session - Abstract HTTP relay service

    Responsibilities (Common):
    1. HTTP service lifecycle (start/stop)
    2. Environment variable configuration
    3. Conversation recording
    4. Token usage tracking

    Responsibilities (Subclass):
    1. Request handling (_handle_request)
    2. Format conversion (_convert_request_to_session, _convert_response_to_format)
    3. API-specific endpoints setup (_setup_routes)
    """

    def __init__(
        self,
        port: int,
        llm_config: LLMConfig,
        conversations_dir: Optional[Path] = None,
        cwd: Optional[str] = None,
        listen_host: str = "localhost",
        logger: Optional['logging.LoggerAdapter'] = None,
        conversation_trees_path: Optional[Path] = None,
        max_turns: Optional[int] = None,
        cost_limit: Optional[float] = None
    ):
        """
        Initialize base relay session

        Args:
            port: Exclusive port
            llm_config: Main model LLM configuration
            conversations_dir: Conversation save directory (optional)
            cwd: Working directory (for recording)
            listen_host: Listening address
            logger: Logger instance
            conversation_trees_path: Prefix tree JSONL path (optional)
            max_turns: Maximum turns allowed (None means unlimited)
            cost_limit: Maximum cost allowed (None means unlimited)
        """
        self.port = port
        self.llm_config = llm_config
        self.listen_host = listen_host
        self.logger = logger or create_logger()

        # Limit tracking
        self.max_turns = max_turns
        self.cost_limit = cost_limit
        self._turn_limit_reached = False
        self._cost_limit_reached = False
        self.last_error: Optional[Exception] = None

        # Conversation recording configuration
        self.conversations_dir = Path(conversations_dir) if conversations_dir else None
        self.cwd = cwd or str(Path.cwd())
        self._conversation_trees_path = Path(conversation_trees_path) if conversation_trees_path else None
        self._conversation_tree_manager = (
            ConversationPrefixTreeManager(self._conversation_trees_path, logger=self.logger)
            if self._conversation_trees_path
            else None
        )

        # Create conversation directory (if enabled)
        if self.conversations_dir:
            self.conversations_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Recording enabled: {self.conversations_dir}")
        else:
            self.logger.info("Recording disabled (no conversations_dir provided)")

        # Usage history: [(model_name, TokenUsage), ...]
        self._usage_history: List[Tuple[str, TokenUsage]] = []

        # State management
        self._app: Optional[FastAPI] = None
        self._server: Optional[uvicorn.Server] = None
        self._server_task: Optional[asyncio.Task] = None
        self._is_running = False

        # Environment variable backup
        self._original_env = {}

        # Session ID (for tracking)
        self.session_id: Optional[str] = None

        # Signature cache: Map (tool_name, arguments_str) -> signature
        # Only enabled when Gemini returns signatures (thinking mode)
        self._signature_cache: Dict[Tuple[str, str], str] = {}
        self._signature_cache_enabled: bool = False

    @abstractmethod
    def _setup_routes(self) -> None:
        """
        Setup API routes - must be implemented by subclass

        Example:
            self._app.add_api_route('/v1/messages', self._handle_anthropic_messages, methods=['POST'])
            self._app.add_api_route('/v1/chat/completions', self._handle_openai_chat, methods=['POST'])
        """
        pass

    @abstractmethod
    async def _handle_request(self, request: Request) -> Response:
        """
        Handle API request - must be implemented by subclass

        Args:
            request: FastAPI Request

        Returns:
            FastAPI Response
        """
        pass

    async def _check_limits_and_shutdown_if_needed(self) -> Optional[Response]:
        """
        Check turn and cost limits before processing request.
        If limit reached, shutdown uvicorn server and return error response.

        Returns:
            None if within limits, error Response if limit exceeded
        """
        # Check turn limit
        if self.max_turns is not None:
            current_turns = self.get_current_turns()
            if current_turns >= self.max_turns:
                self._turn_limit_reached = True
                error_msg = f"Turn limit reached: {current_turns}/{self.max_turns}"
                self.logger.warning(f"[BaseRelay] {error_msg} - shutting down server")

                # Store error for propagation
                from ape.scaffolds.base import MaxTurnsReachedError
                self.last_error = MaxTurnsReachedError(error_msg)

                # Trigger server shutdown
                if self._server:
                    self._server.should_exit = True

                # Return error response before shutdown completes
                return JSONResponse(
                    {
                        "error": {
                            "type": "turn_limit_exceeded",
                            "message": error_msg
                        }
                    },
                    status_code=429
                )

        # Check cost limit
        if self.cost_limit is not None:
            current_cost = self.get_token_usage().total_cost
            if current_cost >= self.cost_limit:
                self._cost_limit_reached = True
                error_msg = f"Cost limit exceeded: ${current_cost:.6f} >= ${self.cost_limit:.6f}"
                self.logger.warning(f"[BaseRelay] {error_msg} - shutting down server")

                # Store error for propagation
                from ape.llm_clients.config import CostExhaustedError
                self.last_error = CostExhaustedError(error_msg)

                # Trigger server shutdown
                if self._server:
                    self._server.should_exit = True

                # Return error response before shutdown completes
                return JSONResponse(
                    {
                        "error": {
                            "type": "cost_limit_exceeded",
                            "message": error_msg
                        }
                    },
                    status_code=429
                )

        return None

    @abstractmethod
    def _get_env_vars(self) -> Dict[str, str]:
        """
        Get environment variables to set - must be implemented by subclass

        Returns:
            Dict of environment variables to set

        Example:
            return {
                'ANTHROPIC_BASE_URL': f"http://{self.listen_host}:{self.port}",
                'ANTHROPIC_AUTH_TOKEN': 'relay_token',
            }
        """
        pass

    async def _handle_options(self, _request: Request) -> Response:
        """Handle OPTIONS preflight request"""
        return Response(
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, x-api-key, anthropic-version'
            }
        )

    async def _call_backend(
        self,
        session: ConversationSession,
        tools: Optional[List[Dict[str, Any]]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        backend_config: Optional[LLMConfig] = None
    ) -> Tuple[List[ConversationNode], TokenUsage, Dict[str, Any]]:
        """
        Call backend LLM service

        Args:
            session: ConversationSession
            tools: Tools definition
            max_tokens: Max tokens
            temperature: Temperature
            backend_config: Backend configuration (default: self.llm_config)

        Returns:
            Tuple of (response_nodes, usage, raw_response)
            raw_response contains original API response (for RL training)
        """
        if backend_config is None:
            backend_config = self.llm_config

        async with LLMClient(backend_config, logger=self.logger) as client:
            response_nodes, usage, raw_response = await client.call_api(
                session=session,
                tools=tools,
                max_tokens=max_tokens,
                temperature=temperature
            )
        return response_nodes, usage, raw_response

    async def record_turn(
        self,
        request_session: ConversationSession,
        response_nodes: List[ConversationNode],
        usage: TokenUsage,
        model_name: str,
        raw_response: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a complete conversation turn

        Args:
            request_session: Requested ConversationSession
            response_nodes: Response ConversationNode list
            usage: Token usage statistics
            model_name: Model name (may contain tag, like @fast)
            raw_response: Raw LLM API response (for RL training)
        """
        if not self.conversations_dir:
            return

        # Generate file name
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S_%f")[:-3]
        file_uid = str(uuid.uuid4())[:8]

        safe_model_name = model_name.replace('/', '_').replace(':', '_')
        filename = f"{timestamp_str}__{safe_model_name}__{file_uid}.jsonl"
        filepath = self.conversations_dir / filename

        # Merge request and response nodes
        combined_session = ConversationSession(
            session_id=request_session.session_id,
            nodes=request_session.nodes + response_nodes
        )

        # Write conversation file
        await self._write_conversation_file(filepath, combined_session)
        await self._update_prefix_trees(combined_session.nodes)

        # Write raw response file (for RL training)
        if raw_response:
            raw_filename = f"{timestamp_str}__{safe_model_name}__{file_uid}_raw.jsonl"
            raw_filepath = self.conversations_dir / raw_filename
            await self._write_raw_response_file(raw_filepath, raw_response)

        # Record usage history
        self._usage_history.append((model_name, usage))

        self.logger.debug(
            f"Recorded turn: {filename}, cost=${usage.total_cost:.6f}"
        )

    async def _write_conversation_file(
        self,
        filepath: Path,
        session: ConversationSession
    ) -> None:
        """Write to single conversation file"""
        try:
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                for node in session.nodes:
                    line = json.dumps(
                        node.model_dump(mode='json'),
                        ensure_ascii=False,
                        default=str
                    ) + '\n'
                    await f.write(line)
        except Exception as e:
            self.logger.error(f"Failed to write conversation file {filepath}: {e}")

    async def _write_raw_response_file(
        self,
        filepath: Path,
        raw_response: Dict[str, Any]
    ) -> None:
        """Write raw LLM response file (for RL training)"""
        try:
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                line = json.dumps(
                    raw_response,
                    ensure_ascii=False,
                    default=str
                ) + '\n'
                await f.write(line)
        except Exception as e:
            self.logger.error(f"Failed to write raw response file {filepath}: {e}")

    async def _update_prefix_trees(self, nodes: List[ConversationNode]) -> None:
        """Update conversation prefix forest if enabled."""
        if not self._conversation_tree_manager:
            return

        try:
            await self._conversation_tree_manager.add_conversation(nodes)
        except Exception as exc:
            self.logger.warning(f"Failed to update conversation prefix trees: {exc}")

    def configure_environment(self) -> None:
        """
        Configure environment - default implementation does nothing.
        Subclasses should override to implement their specific configuration logic.
        """
        pass

    def restore_environment(self) -> None:
        """
        Restore environment - default implementation does nothing.
        Subclasses should override to implement their specific restoration logic.
        """
        pass

    async def start(self) -> None:
        """Start relay service"""
        if self._is_running:
            return

        # Create FastAPI application
        self._app = FastAPI()

        # Add CORS middleware
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes (subclass implementation)
        self._setup_routes()

        # Configure uvicorn server with custom logging
        # Disable default uvicorn logging configuration
        config = uvicorn.Config(
            app=self._app,
            host=self.listen_host,
            port=self.port,
            log_config=None,  # Disable default log config
            access_log=False,
        )
        self._server = uvicorn.Server(config)

        # Redirect all uvicorn/starlette logs to relay logger file
        # This prevents CancelledError and other internal logs from appearing in console
        self._configure_uvicorn_logging()

        # Start server in background task
        self._server_task = asyncio.create_task(self._server.serve())

        # Wait for server to be ready
        while not self._server.started:
            await asyncio.sleep(0.01)

        self._is_running = True
        self.configure_environment()

        self.logger.info(f"Relay service started: http://{self.listen_host}:{self.port}")

    def _configure_uvicorn_logging(self) -> None:
        """
        Configure uvicorn and starlette loggers to use relay logger's handlers.

        This ensures all uvicorn logs (including CancelledError during shutdown)
        are written to the relay log file instead of console.
        """
        # Get the file handlers from relay logger
        relay_handlers = []
        if hasattr(self.logger, 'logger'):
            # LoggerAdapter wraps the actual logger
            actual_logger = self.logger.logger
            relay_handlers = [h for h in actual_logger.handlers
                            if isinstance(h, logging.FileHandler)]

        # Configure uvicorn and starlette loggers
        for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "starlette"]:
            uvicorn_logger = logging.getLogger(logger_name)

            # Remove existing handlers to prevent console output
            uvicorn_logger.handlers.clear()

            # Add relay's file handlers if available
            for handler in relay_handlers:
                uvicorn_logger.addHandler(handler)

            # If no file handlers, create a NullHandler to suppress console output
            if not relay_handlers:
                uvicorn_logger.addHandler(logging.NullHandler())

            # Set level to capture all logs
            uvicorn_logger.setLevel(logging.DEBUG)

            # Prevent propagation to root logger (which might output to console)
            uvicorn_logger.propagate = False

    async def stop(self) -> None:
        """Stop relay service gracefully"""
        if not self._is_running:
            return

        self.logger.debug("Stopping relay service...")
        self.restore_environment()

        # Shutdown uvicorn server gracefully
        if self._server:
            self._server.should_exit = True
            if self._server_task:
                try:
                    # Wait for graceful shutdown
                    await asyncio.wait_for(self._server_task, timeout=5.0)
                    self.logger.debug("Server task completed gracefully")
                except asyncio.TimeoutError:
                    # Graceful shutdown timed out, force shutdown
                    self.logger.debug("Server shutdown timeout, forcing shutdown")
                    self._server.force_exit = True
                    try:
                        await asyncio.wait_for(self._server.shutdown(), timeout=2.0)
                    except asyncio.TimeoutError:
                        self.logger.debug("Server force shutdown timed out")
                    except asyncio.CancelledError:
                        # Normal during shutdown
                        pass
                    except Exception as e:
                        self.logger.debug(f"Exception during server shutdown: {type(e).__name__}")

                    # Cancel the server task
                    self._server_task.cancel()
                    try:
                        await asyncio.wait_for(self._server_task, timeout=2.0)
                    except asyncio.CancelledError:
                        # This is expected when cancelling
                        self.logger.debug("Server task cancelled successfully")
                    except asyncio.TimeoutError:
                        self.logger.debug("Server task cancellation timed out")
                    except Exception as e:
                        self.logger.debug(f"Exception during task cancellation: {type(e).__name__}")
                except asyncio.CancelledError:
                    # Normal if stop() is called during shutdown
                    self.logger.debug("Server task already cancelled")
                except Exception as e:
                    # Unexpected error
                    self.logger.debug(f"Unexpected error during server shutdown: {type(e).__name__}: {e}")

                self._server_task = None
            self._server = None

        self._app = None
        self._is_running = False

        self.logger.info("Relay service stopped")

    @property
    def is_running(self) -> bool:
        """Check if service is running"""
        return self._is_running

    @property
    def base_url(self) -> str:
        """Get service base URL"""
        return f"http://{self.listen_host}:{self.port}"

    def get_token_usage(self) -> TokenUsage:
        """Get accumulated token usage"""
        if not self._usage_history:
            return TokenUsage()

        # Add up all fields
        total_input = sum(u.input_tokens for _, u in self._usage_history)
        total_output = sum(u.output_tokens for _, u in self._usage_history)
        total_reasoning = sum(u.reasoning_tokens or 0 for _, u in self._usage_history)
        total_cache_creation = sum(
            u.cache_creation_input_tokens or 0 for _, u in self._usage_history
        )
        total_cache_read = sum(
            u.cache_read_input_tokens or 0 for _, u in self._usage_history
        )
        total_cost = sum(u.total_cost for _, u in self._usage_history)
        cached_total_cost = sum(u.cached_total_cost for _, u in self._usage_history)

        return TokenUsage(
            input_tokens=total_input,
            output_tokens=total_output,
            total_tokens=total_input + total_output,
            reasoning_tokens=total_reasoning if total_reasoning > 0 else None,
            cache_creation_input_tokens=total_cache_creation if total_cache_creation > 0 else None,
            cache_read_input_tokens=total_cache_read if total_cache_read > 0 else None,
            total_cost=total_cost,
            cached_total_cost=cached_total_cost
        )

    def get_current_turns(self) -> int:
        """Get current conversation turn"""
        return len(self._usage_history)

    def _serialize_args(self, args: Any) -> str:
        """Serialize arguments to stable string format for signature cache key"""
        if args is None:
            return "{}"
        elif isinstance(args, str):
            return args
        else:
            return json.dumps(args, sort_keys=True, ensure_ascii=False)

    def _cache_signatures_from_nodes(self, nodes: List[ConversationNode]) -> None:
        """Extract and cache signatures from response nodes (before client SDK loses them)"""
        has_signature = False
        for node in nodes:
            if node.type == "assistant":
                for block in node.message.content:
                    if block.type == "tool_use" and block.signature:
                        has_signature = True
                        args_str = self._serialize_args(block.input)
                        cache_key = (block.name, args_str)
                        self._signature_cache[cache_key] = block.signature
                        self.logger.debug(f"Cached signature for tool={block.name}")

        # Enable cache only if we see signatures (Gemini thinking mode)
        if has_signature and not self._signature_cache_enabled:
            self._signature_cache_enabled = True
            self.logger.info("Signature cache enabled (Gemini thinking mode detected)")

    def _restore_signatures_to_blocks(self, blocks: List[ContentBlock]) -> None:
        """Restore signatures to tool_use blocks from cache (client SDK lost them)"""
        if not self._signature_cache_enabled:
            return

        for block in blocks:
            if block.type == "tool_use" and not block.signature:
                args_str = self._serialize_args(block.input)
                cache_key = (block.name, args_str)
                if cache_key in self._signature_cache:
                    block.signature = self._signature_cache[cache_key]
                    # self.logger.debug(f"Restored signature for tool={block.name}")
