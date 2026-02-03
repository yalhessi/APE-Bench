"""
Codex HTTP Relay Service - OpenAI API Implementation

Inherits from BaseRelaySession and implements OpenAI-specific:
1. OpenAI API format conversion
2. Chat completions endpoint handling
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, TYPE_CHECKING, AsyncIterator
from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from ape.scaffolds.utils.base_relay import BaseRelaySession
from ape.llm_clients.models import ConversationSession, ConversationNode, ContentBlock, TokenUsage

if TYPE_CHECKING:
    import logging


class CodexRelaySession(BaseRelaySession):
    """Codex relay session - OpenAI API implementation"""

    def _setup_routes(self) -> None:
        """Setup OpenAI API routes"""
        self._app.add_api_route('/chat/completions', self._handle_chat_completions, methods=['POST'])
        self._app.add_api_route('/chat/completions', self._handle_options, methods=['OPTIONS'])

    def _get_env_vars(self) -> Dict[str, str]:
        """
        Codex relay does NOT use environment variables for configuration.

        Codex reads configuration from TOML file specified by CODEX_HOME.
        The TOML file is created in __main__ when running relay directly.

        Returns empty dict - no environment variables needed.
        """
        return {}

    def configure_environment(self) -> None:
        """
        Codex does NOT need environment configuration.

        Unlike Claude Code which uses environment variables (ANTHROPIC_BASE_URL, etc.),
        Codex uses TOML configuration file. The TOML file path is set via CODEX_HOME
        in the main execution logic, not here.
        """
        pass

    def restore_environment(self) -> None:
        """No environment variables to restore for Codex"""
        pass

    async def _handle_request(self, request: Request) -> JSONResponse:
        """Main OpenAI API request handler"""
        return await self._handle_chat_completions(request)

    async def _handle_streaming_response(self, _request: Request, openai_request: Dict[str, Any], client_requested_model: str) -> StreamingResponse:
        """Handle streaming chat completions (SSE format)"""
        # Note: Turn limit and cost limit already checked in _handle_chat_completions before calling this
        # _request parameter kept for consistency with handler signature but not used

        # Use main llm_config (fast model removed)
        backend_config = self.llm_config

        # Get tools
        openai_tools = openai_request.get("tools")

        # Convert request to ConversationSession
        request_session = self._convert_openai_to_session(openai_request, openai_tools)

        # Call backend (non-streaming)
        response_nodes, usage, raw_response = await self._call_backend(
            request_session,
            openai_tools,
            openai_request.get("max_tokens"),
            openai_request.get("temperature"),
            backend_config
        )

        # Record conversation
        if self.conversations_dir:
            await self.record_turn(
                request_session, response_nodes, usage, client_requested_model, raw_response
            )

        # Cache signatures from response (before client loses them)
        self._cache_signatures_from_nodes(response_nodes)

        # Convert to OpenAI format
        openai_response = self._convert_nodes_to_openai(
            response_nodes, usage, client_requested_model
        )

        # Create async generator for streaming
        async def generate() -> AsyncIterator[str]:
            try:
                # Send the complete response as SSE chunks
                message = openai_response['choices'][0]['message']
                content = message.get('content', '')
                tool_calls = message.get('tool_calls', [])

                chunk_id = openai_response['id']
                created = openai_response['created']

                # If there's text content, stream it
                if content:
                    # Send content as a single delta
                    chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": client_requested_model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": content
                            },
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"

                # If there are tool calls, stream them
                if tool_calls:
                    for tool_call in tool_calls:
                        # Note: signature is already included in tool_call from _convert_nodes_to_openai
                        chunk = {
                            "id": chunk_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": client_requested_model,
                            "choices": [{
                                "index": 0,
                                "delta": {
                                    "tool_calls": [tool_call]
                                },
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"

                # Send final chunk with finish_reason
                finish_reason = "tool_calls" if tool_calls else "stop"
                final_chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": client_requested_model,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": finish_reason
                    }]
                }
                yield f"data: {json.dumps(final_chunk)}\n\n"

                # Send [DONE]
                yield "data: [DONE]\n\n"

                self.logger.info(f"Streaming response completed: {client_requested_model}")

            except asyncio.CancelledError:
                # Normal shutdown - streaming cancelled during relay shutdown
                self.logger.debug("Streaming cancelled during relay shutdown")
                raise
            except Exception as e:
                self.logger.error(f"Streaming error: {e}")

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )

    async def _handle_chat_completions(self, request: Request) -> JSONResponse:
        """Handle OpenAI chat completions endpoint"""
        try:
            # Check limits BEFORE processing request (unified base implementation)
            limit_response = await self._check_limits_and_shutdown_if_needed()
            if limit_response is not None:
                return limit_response

            openai_request = await request.json()
            client_requested_model = openai_request.get('model')

            if not client_requested_model:
                raise ValueError("Missing 'model' field in request")

            self.logger.info(f"Received request: {client_requested_model} (turn {self.get_current_turns() + 1}/{self.max_turns or '∞'})")

            # Check if streaming is requested
            is_streaming = openai_request.get('stream', False)
            self.logger.debug(f"Request stream={is_streaming}")

            if is_streaming:
                return await self._handle_streaming_response(request, openai_request, client_requested_model)

            # Use main llm_config (fast model removed)
            backend_config = self.llm_config

            # Get tools (already in OpenAI format)
            openai_tools = openai_request.get("tools")

            # Convert request to ConversationSession
            request_session = self._convert_openai_to_session(openai_request, openai_tools)

            # Call backend
            response_nodes, usage, raw_response = await self._call_backend(
                request_session,
                openai_tools,
                openai_request.get("max_tokens"),
                openai_request.get("temperature"),
                backend_config
            )

            # Record conversation
            if self.conversations_dir:
                await self.record_turn(
                    request_session, response_nodes, usage, client_requested_model, raw_response
                )

            # Cache signatures from response (before client loses them)
            self._cache_signatures_from_nodes(response_nodes)

            # Convert response to OpenAI format
            openai_response = self._convert_nodes_to_openai(
                response_nodes, usage, client_requested_model
            )

            self.logger.info(f"Response completed: {client_requested_model}")
            return JSONResponse(openai_response)

        except asyncio.CancelledError:
            # Normal shutdown - request cancelled during relay shutdown
            self.logger.debug("Request cancelled during relay shutdown")
            return Response(status_code=499)
        except Exception as e:
            import traceback
            self.logger.error(f"Request failed: {traceback.format_exc()}")
            return JSONResponse(
                {"error": {"type": "internal_error", "message": str(e)}},
                status_code=500
            )

    def _convert_openai_to_session(
        self,
        request: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> ConversationSession:
        """Convert OpenAI request to ConversationSession"""
        # Don't pass session_id, let it auto-generate via default_factory
        session = ConversationSession()
        cwd = self.cwd
        messages = request.get("messages", [])

        # Extract system message if present (first message with role="system")
        if messages and messages[0].get("role") == "system":
            system_message = messages[0]
            system_content = system_message.get("content", "")
            if system_content:
                session.add_system_message(
                    [ContentBlock.text_block(system_content)],
                    cwd
                )
            messages = messages[1:]

        # Record tool definitions
        if tools:
            session.add_tool_definitions(tools, cwd)

        # Handle regular messages
        for message in messages:
            role = message.get("role")
            content = message.get("content", "")

            if role == "user":
                if isinstance(content, str):
                    session.add_user_message(
                        [ContentBlock.text_block(content)],
                        cwd
                    )
                elif isinstance(content, list):
                    blocks = self._convert_openai_content_to_blocks(content)
                    session.add_user_message(blocks, cwd)

            elif role == "assistant":
                blocks = []
                # Text content
                if content:
                    blocks.append(ContentBlock.text_block(content))

                # Tool calls
                tool_calls = message.get("tool_calls", [])
                for tool_call in tool_calls:
                    if tool_call.get("type") == "function":
                        func = tool_call.get("function", {})

                        # Use safe argument parsing (extracts first valid JSON object)
                        from ape.llm_clients.adapters.response_processor import _parse_tool_arguments
                        arguments_str = func.get("arguments", "{}")
                        if isinstance(arguments_str, str):
                            parsed_input = _parse_tool_arguments(arguments_str, func.get("name", "unknown"), self.logger)
                        else:
                            parsed_input = arguments_str

                        blocks.append(ContentBlock.tool_use_block(
                            id=tool_call.get("id", ""),
                            name=func.get("name", ""),
                            input=parsed_input,
                            signature=tool_call.get("signature")  # Extract signature for Gemini thinking support
                        ))

                # Restore signatures that client lost
                self._restore_signatures_to_blocks(blocks)

                if blocks:
                    session.add_assistant_message(blocks, cwd)

            elif role == "tool":
                # Tool result
                tool_call_id = message.get("tool_call_id", "")
                tool_content = message.get("content", "")
                session.add_tool_result(
                    tool_use_id=tool_call_id,
                    content=tool_content,
                    cwd=cwd,
                    tool_name=message.get("name")
                )

        return session

    def _convert_openai_content_to_blocks(
        self, content: List[Dict[str, Any]]
    ) -> List[ContentBlock]:
        """Convert OpenAI content array to ContentBlock list"""
        blocks = []
        for item in content:
            content_type = item.get("type")
            if content_type == "text":
                blocks.append(ContentBlock.text_block(item.get("text", "")))
            # Add other content types if needed
        return blocks

    def _convert_nodes_to_openai(
        self,
        nodes: List[ConversationNode],
        usage: TokenUsage,
        model_name: str
    ) -> Dict[str, Any]:
        """Convert ConversationNode list to OpenAI format"""
        response = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": model_name,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": []
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": usage.input_tokens,
                "completion_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens
            }
        }

        message = response["choices"][0]["message"]
        text_parts = []
        tool_calls = []

        # Extract content from assistant nodes
        for node in nodes:
            if node.type == "assistant":
                for block in node.message.content:
                    if block.type == "text" and block.text:
                        text_parts.append(block.text)
                    elif block.type == "thinking" and block.reasoning_content:
                        text_parts.append(block.reasoning_content)
                    elif block.type == "tool_use":
                        tool_call = {
                            "id": block.id,
                            "type": "function",
                            "function": {
                                "name": block.name,
                                "arguments": json.dumps(block.input or {})
                            }
                        }
                        # Include signature if present (for Gemini thinking support)
                        if block.signature:
                            tool_call["signature"] = block.signature
                        tool_calls.append(tool_call)

        # Set content and tool_calls
        message["content"] = "\n".join(text_parts) if text_parts else None

        if tool_calls:
            message["tool_calls"] = tool_calls
            response["choices"][0]["finish_reason"] = "tool_calls"

        return response


if __name__ == "__main__":
    import argparse
    import asyncio
    import os
    import sys
    import tempfile
    import shutil
    from pathlib import Path
    from datetime import datetime
    from ape.utils.logging import create_logger
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.utils.common import allocate_port

    async def main():
        parser = argparse.ArgumentParser(description="Codex relay service")
        parser.add_argument('--model', default="deepseek_v3.1", help='Model name')
        parser.add_argument('--host', default='localhost', help='Listening address')
        parser.add_argument('--retry_max_attempts', type=int, default=1, help='Max retry attempts')
        parser.add_argument('--conversations_dir', default="data/relay_conversations", help='Conversation directory')

        args = parser.parse_args()

        base_dir = Path(args.conversations_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conversations_dir = base_dir / f"session_{timestamp}"
        log_dir = base_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"relay_{timestamp}.log"

        logger = create_logger(log_file=log_file, to_console=True)

        llm_config = LLMConfig(
            model_name=args.model,
            retry_max_attempts=args.retry_max_attempts,
            relay_mode=True
        )

        port = allocate_port()
        session = CodexRelaySession(
            port=port,
            llm_config=llm_config,
            conversations_dir=conversations_dir,
            cwd=str(Path.cwd()),
            listen_host=args.host,
            logger=logger
        )

        # Create temporary CODEX_HOME directory with config.toml
        temp_codex_home = None
        original_codex_home = os.environ.get('CODEX_HOME')

        try:
            # Create temporary directory for CODEX_HOME
            temp_codex_home = Path(tempfile.mkdtemp(prefix="codex_relay_"))
            logger.info(f"Created temporary CODEX_HOME: {temp_codex_home}")

            # Build TOML config
            import tomli_w

            relay_base_url = f"http://{args.host}:{port}"
            config = {
                "model_provider": "relay",
                "model": args.model,
                "model_providers": {
                    "relay": {
                        "name": "Relay",
                        "base_url": relay_base_url
                    }
                }
            }

            # Write config.toml
            config_path = temp_codex_home / "config.toml"
            with open(config_path, 'wb') as f:
                tomli_w.dump(config, f)

            logger.info(f"Created TOML config: {config_path}")
            logger.info(f"  - Model provider: relay @ {relay_base_url}")
            logger.info(f"  - Model: {args.model}")

            # Set CODEX_HOME environment variable
            os.environ['CODEX_HOME'] = str(temp_codex_home)

            # Start relay server
            await session.start()
            logger.info(f"Relay started: {session.base_url}")
            logger.info(f"Model: {llm_config.model_name}")
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"To use this relay, run codex with:\n  export CODEX_HOME={temp_codex_home}\n  codex")
            logger.info("=" * 60)
            logger.info("")
            logger.info("Press Ctrl+C to stop")

            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("\nStopping...")
        except Exception as e:
            logger.error(f"Failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
        finally:
            await session.stop()

            # Restore original CODEX_HOME
            if original_codex_home:
                os.environ['CODEX_HOME'] = original_codex_home
            elif 'CODEX_HOME' in os.environ:
                del os.environ['CODEX_HOME']

            # Clean up temporary directory
            if temp_codex_home and temp_codex_home.exists():
                shutil.rmtree(temp_codex_home)
                logger.info(f"Cleaned up temporary CODEX_HOME: {temp_codex_home}")

    asyncio.run(main())
