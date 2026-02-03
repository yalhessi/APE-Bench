"""
Claude Code HTTP Relay Service - Anthropic API Implementation

Inherits from BaseRelaySession and implements Anthropic-specific:
1. Anthropic API format conversion
2. Claude Code session ID extraction
3. Token counting request handling
"""

import asyncio
import json
import os
import re
import uuid
from typing import Dict, List, Any, Optional, TYPE_CHECKING, Tuple
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from ape.scaffolds.utils.base_relay import BaseRelaySession
from ape.llm_clients.models import ConversationSession, ConversationNode, ContentBlock, TokenUsage
from ape.llm_clients.config import LLMConfig, ContextLengthExceededError, MalformedResponseError
from ape.llm_clients.adapters.streaming_processor import StreamingInterruptedError
from pathlib import Path

if TYPE_CHECKING:
    import logging


class ClaudeCodeRelaySession(BaseRelaySession):
    """Claude Code relay session - Anthropic API implementation"""

    def __init__(
        self,
        port: int,
        llm_config: LLMConfig,
        fast_llm_config: Optional[LLMConfig] = None,
        conversations_dir: Optional[Path] = None,
        cwd: Optional[str] = None,
        listen_host: str = "localhost",
        logger: Optional['logging.LoggerAdapter'] = None,
        conversation_trees_path: Optional[Path] = None,
        max_turns: Optional[int] = None,
        cost_limit: Optional[float] = None
    ):
        """
        Initialize Claude Code relay session

        Args:
            port: Exclusive port
            llm_config: Main model LLM configuration
            fast_llm_config: Fast model LLM configuration for subagents, None means using llm_config
            conversations_dir: Conversation save directory (optional)
            cwd: Working directory (for recording)
            listen_host: Listening address
            logger: Logger instance
            conversation_trees_path: Prefix tree JSONL path (optional)
            max_turns: Maximum turns allowed (None means unlimited)
            cost_limit: Maximum cost allowed (None means unlimited)
        """
        super().__init__(
            port=port,
            llm_config=llm_config,
            conversations_dir=conversations_dir,
            cwd=cwd,
            listen_host=listen_host,
            logger=logger,
            conversation_trees_path=conversation_trees_path,
            max_turns=max_turns,
            cost_limit=cost_limit
        )
        # Claude Code specific: fast model for subagents
        self.fast_llm_config = fast_llm_config or llm_config
        # Claude Code specific: session ID extraction
        self.claude_code_session_id: Optional[str] = None
        # Environment variable backup for restoration
        self._env_backup: Dict[str, str] = {}

    def _setup_routes(self) -> None:
        """Setup Anthropic API routes"""
        self._app.add_api_route('/v1/messages', self._handle_messages, methods=['POST'])
        self._app.add_api_route('/v1/messages', self._handle_options, methods=['OPTIONS'])
        self._app.add_api_route('/v1/messages/count_tokens', self._handle_count_tokens, methods=['POST'])
        self._app.add_api_route('/v1/messages/count_tokens', self._handle_options, methods=['OPTIONS'])
        self._app.add_api_route('/api/event_logging/batch', self._handle_event_logging, methods=['POST'])
        self._app.add_api_route('/api/event_logging/batch', self._handle_options, methods=['OPTIONS'])

    def _get_env_vars(self) -> Dict[str, str]:
        """Get Anthropic-specific environment variables"""
        base_url = f"http://{self.listen_host}:{self.port}"
        main_model = self.llm_config.model_name
        fast_model = self.fast_llm_config.model_name
        fast_model_with_tag = f"{fast_model}@fast"

        return {
            'ANTHROPIC_BASE_URL': base_url,
            'ANTHROPIC_AUTH_TOKEN': 'relay_token',
            'ANTHROPIC_MODEL': main_model,
            'ANTHROPIC_DEFAULT_OPUS_MODEL': main_model,
            'ANTHROPIC_DEFAULT_SONNET_MODEL': main_model,
            'ANTHROPIC_DEFAULT_HAIKU_MODEL': fast_model_with_tag,
            'CLAUDE_CODE_SUBAGENT_MODEL': fast_model_with_tag,
        }

    def configure_environment(self) -> None:
        """Configure environment variables and clear proxy settings for Claude Code SDK"""
        # Backup original environment variables
        env_vars_to_backup = list(self._get_env_vars().keys()) + [
            'HTTP_PROXY', 'http_proxy', 'https_proxy', 'no_proxy'
        ]

        for var in env_vars_to_backup:
            if var in os.environ:
                self._env_backup[var] = os.environ[var]

        # Set Anthropic environment variables
        for key, value in self._get_env_vars().items():
            os.environ[key] = value

        # Clear proxy environment variables (Claude Code SDK needs direct localhost connection)
        os.environ['HTTP_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''
        os.environ['no_proxy'] = 'localhost'

        # Log configuration
        env_info = '\n'.join([f'export {k}={v}' for k, v in self._get_env_vars().items()])
        self.logger.info(
            f'\n{env_info}\n'
            f'export HTTP_PROXY=\'\'\n'
            f'export http_proxy=\'\'\n'
            f'export https_proxy=\'\'\n'
            f'export no_proxy=localhost'
        )

    def restore_environment(self) -> None:
        """Restore original environment variables"""
        all_vars = list(self._get_env_vars().keys()) + [
            'HTTP_PROXY', 'http_proxy', 'https_proxy', 'no_proxy'
        ]

        for var in all_vars:
            if var in self._env_backup:
                os.environ[var] = self._env_backup[var]
            elif var in os.environ:
                del os.environ[var]

        self._env_backup.clear()
        self.logger.info("Environment variables restored")

    async def _handle_request(self, request: Request) -> JSONResponse:
        """Main Anthropic API request handler"""
        return await self._handle_messages(request)

    async def _handle_count_tokens(self, request: Request) -> JSONResponse:
        """Handle count_tokens endpoint - return fixed token count"""
        try:
            await request.json()
            return JSONResponse({"input_tokens": 100})
        except Exception as e:
            self.logger.error(f"Error in count_tokens: {e}")
            return JSONResponse(
                {"error": {"type": "invalid_request_error", "message": str(e)}},
                status_code=400
            )

    async def _handle_event_logging(self, request: Request) -> JSONResponse:
        """Handle event_logging/batch endpoint - return empty success response"""
        try:
            # Consume the request body but don't process it
            await request.json()
            # Return empty success response
            return JSONResponse({})
        except Exception as e:
            self.logger.error(f"Error in event_logging: {e}")
            return JSONResponse({})

    async def _handle_messages(self, request: Request) -> JSONResponse:
        """Handle Anthropic messages endpoint"""
        try:
            # Check limits BEFORE processing request (unified base implementation)
            limit_response = await self._check_limits_and_shutdown_if_needed()
            if limit_response is not None:
                return limit_response

            anthropic_request = await request.json()
            client_requested_model = anthropic_request.get('model')

            if not client_requested_model:
                raise ValueError("Missing 'model' field in request")

            self.logger.info(f"Received request: {client_requested_model} (turn {self.get_current_turns() + 1}/{self.max_turns or '∞'})")

            # Extract and save Claude Code session ID
            user_id = anthropic_request.get('metadata', {}).get('user_id')
            if user_id:
                session_id = self._extract_session_id(user_id)
                if session_id and not self.claude_code_session_id:
                    self.claude_code_session_id = session_id
                    self.logger.info(f"Extracted Claude Code session ID: {session_id}")

            # Check if token counting request
            if self._is_token_count_request(anthropic_request):
                self.logger.info("Detected token counting request, returning mock response")
                return JSONResponse(
                    self._create_token_count_response(client_requested_model)
                )

            # Select backend config based on @fast tag
            backend_config = (
                self.fast_llm_config if client_requested_model.endswith('@fast')
                else self.llm_config
            )

            # Convert Anthropic tools to OpenAI format
            anthropic_tools = anthropic_request.get("tools")
            openai_tools = (
                self._convert_anthropic_tools_to_openai(anthropic_tools)
                if anthropic_tools else None
            )

            # Convert request to ConversationSession
            request_session = self._convert_anthropic_to_session(
                anthropic_request, openai_tools
            )

            # Call backend
            response_nodes, usage, raw_response = await self._call_backend(
                request_session,
                openai_tools,
                anthropic_request.get("max_tokens"),
                anthropic_request.get("temperature"),
                backend_config
            )

            # Record conversation
            if self.conversations_dir:
                await self.record_turn(
                    request_session, response_nodes, usage, client_requested_model, raw_response
                )

            # Cache signatures from response (before SDK loses them)
            self._cache_signatures_from_nodes(response_nodes)

            # Convert response to Anthropic format
            anthropic_response = self._convert_nodes_to_anthropic(
                response_nodes, usage, client_requested_model
            )

            self.logger.info(f"Response completed: {client_requested_model}")
            return JSONResponse(anthropic_response)

        except asyncio.CancelledError:
            self.logger.debug("Request cancelled during relay shutdown")
            return Response(status_code=499)
        except (ContextLengthExceededError, MalformedResponseError, StreamingInterruptedError) as e:
            # Store error and trigger shutdown
            self.last_error = e
            if self._server:
                self._server.should_exit = True
            error_type = type(e).__name__
            status_code = 400 if isinstance(e, ContextLengthExceededError) else 500
            return JSONResponse(
                {"error": {"type": error_type, "message": str(e)}},
                status_code=status_code
            )
        except Exception as e:
            import traceback
            self.logger.error(f"Request failed: {traceback.format_exc()}")
            return JSONResponse(
                {"error": {"type": "internal_error", "message": str(e)}},
                status_code=500
            )

    def _extract_session_id(self, user_id: str) -> Optional[str]:
        """Extract Claude Code session ID from user_id"""
        if not user_id:
            return None
        match = re.search(r'__session_([a-f0-9\-]+)', user_id)
        return match.group(1) if match else None

    def _is_token_count_request(self, request: Dict[str, Any]) -> bool:
        """Check if request is a token counting request"""
        messages = request.get("messages", [])
        if len(messages) != 1 or messages[0].get("role") != "user":
            return False

        content = messages[0].get("content", "")
        if isinstance(content, str):
            return content.strip() == "count"
        if isinstance(content, list) and len(content) == 1:
            block = content[0]
            return (isinstance(block, dict) and block.get("type") == "text"
                    and block.get("text", "").strip() == "count")
        return False

    def _create_token_count_response(self, model_name: str) -> Dict[str, Any]:
        """Create mock token count response"""
        return {
            "id": f"msg_{uuid.uuid4().hex[:24]}",
            "type": "message",
            "role": "assistant",
            "model": model_name,
            "content": [{
                "type": "text",
                "text": "Token counting not supported in relay mode."
            }],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 20}
        }

    def _convert_anthropic_tools_to_openai(
        self, tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert Anthropic tools to OpenAI format"""
        return [{
            "type": "function",
            "function": {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {})
            }
        } for tool in tools]

    def _convert_anthropic_to_session(
        self,
        request: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> ConversationSession:
        """Convert Anthropic request to ConversationSession"""
        session = ConversationSession(session_id=self.claude_code_session_id)
        cwd = self.cwd

        # Handle system message
        system_content = request.get("system")
        if system_content:
            if isinstance(system_content, str):
                content_blocks = [ContentBlock.text_block(system_content)]
            elif isinstance(system_content, list):
                content_blocks = [
                    ContentBlock.text_block(block.get("text", ""))
                    for block in system_content if block.get("type") == "text"
                ]
            else:
                content_blocks = []

            if content_blocks:
                session.add_system_message(content_blocks, cwd)

        # Record tool definitions
        if tools:
            session.add_tool_definitions(tools, cwd)

        # Handle messages
        for message in request.get("messages", []):
            role = message["role"]
            content = message.get("content", "")

            if role == "user":
                if isinstance(content, str):
                    session.add_user_message([ContentBlock.text_block(content)], cwd)
                elif isinstance(content, list):
                    # Separate tool_result and non-tool_result
                    tool_results = [
                        item for item in content
                        if isinstance(item, dict) and item.get("type") == "tool_result"
                    ]
                    non_tool_results = [
                        item for item in content
                        if not (isinstance(item, dict) and item.get("type") == "tool_result")
                    ]

                    # Add tool results as separate nodes
                    for item in tool_results:
                        session.add_tool_result(
                            tool_use_id=item.get("tool_use_id", ""),
                            content=item.get("content", ""),
                            cwd=cwd,
                            tool_name=item.get("name")
                        )

                    # Add non-tool content as user message
                    if non_tool_results:
                        blocks = self._convert_content_to_blocks({"content": non_tool_results})
                        session.add_user_message(blocks, cwd)

            elif role == "assistant":
                blocks = self._convert_content_to_blocks(message)
                # Restore signatures that Claude SDK lost
                self._restore_signatures_to_blocks(blocks)
                session.add_assistant_message(blocks, cwd)

        return session

    def _convert_content_to_blocks(self, message: Dict[str, Any]) -> List[ContentBlock]:
        """Convert message content to ContentBlock list"""
        content = message.get("content", "")
        blocks = []

        if isinstance(content, str):
            blocks.append(ContentBlock.text_block(content))
        elif isinstance(content, list):
            for item in content:
                if item.get("type") == "text":
                    blocks.append(ContentBlock.text_block(item.get("text", "")))
                elif item.get("type") == "tool_use":
                    blocks.append(ContentBlock.tool_use_block(
                        item.get("id", ""),
                        item.get("name", ""),
                        item.get("input", {}),
                        signature=item.get("signature")  # Extract signature from Claude SDK response
                    ))
                elif item.get("type") == "tool_result":
                    blocks.append(ContentBlock.tool_result_block(
                        item.get("tool_use_id", ""),
                        item.get("content", ""),
                        item.get("name", "")
                    ))
        else:
            blocks.append(ContentBlock.text_block(str(content)))

        return blocks

    def _convert_nodes_to_anthropic(
        self,
        nodes: List[ConversationNode],
        usage: TokenUsage,
        model_name: str
    ) -> Dict[str, Any]:
        """Convert ConversationNode list to Anthropic format"""
        response = {
            "id": f"msg_{uuid.uuid4().hex[:24]}",
            "type": "message",
            "role": "assistant",
            "model": model_name,
            "content": [],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens
            }
        }

        # Extract content from assistant nodes
        for node in nodes:
            if node.type == "assistant":
                for block in node.message.content:
                    if block.type == "text" and block.text:
                        response["content"].append({
                            "type": "text",
                            "text": block.text
                        })
                    elif block.type == "thinking" and block.reasoning_content:
                        if response["content"] and response["content"][-1]["type"] == "text":
                            response["content"][-1]["text"] += "\n\n" + block.reasoning_content
                        else:
                            response["content"].append({
                                "type": "text",
                                "text": block.reasoning_content
                            })
                    elif block.type == "tool_use":
                        tool_use_content = {
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input or {}
                        }
                        # Include signature if present (for Gemini thinking support)
                        if block.signature:
                            tool_use_content["signature"] = block.signature
                        response["content"].append(tool_use_content)
                        response["stop_reason"] = "tool_use"

        # Ensure at least some content
        if not response["content"]:
            response["content"].append({
                "type": "text",
                "text": "I apologize, but I couldn't generate a response."
            })

        return response


if __name__ == "__main__":
    import argparse
    import asyncio
    import sys
    from pathlib import Path
    from datetime import datetime
    from ape.utils.logging import create_logger
    from ape.llm_clients.config import LLMConfig
    from ape.scaffolds.utils.common import allocate_port

    async def main():
        parser = argparse.ArgumentParser(description="Claude Code relay service")
        parser.add_argument('--model', default="deepseek_v3.1", help='Model name')
        parser.add_argument('--fast_model', default="gpt_5_nano", help='Fast model name')
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
        fast_llm_config = (
            LLMConfig(
                model_name=args.fast_model,
                retry_max_attempts=args.retry_max_attempts,
                relay_mode=True
            ) if args.fast_model != args.model else None
        )

        port = allocate_port()
        session = ClaudeCodeRelaySession(
            port=port,
            llm_config=llm_config,
            fast_llm_config=fast_llm_config,
            conversations_dir=conversations_dir,
            cwd=str(Path.cwd()),
            listen_host=args.host,
            logger=logger
        )

        try:
            await session.start()
            logger.info(f"Relay started: {session.base_url}")
            logger.info(f"Main model: {llm_config.model_name}")
            logger.info(f"Fast model: {fast_llm_config.model_name if fast_llm_config else 'N/A'}")
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

    asyncio.run(main())
