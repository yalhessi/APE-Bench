"""
Streaming Processor Module.

Processes streaming LLM responses and converts SSE streams to ConversationNode lists.
"""

import asyncio
import json
import traceback
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator, TYPE_CHECKING
from pydantic import BaseModel, Field

from ..config import LLMError, MalformedResponseError, ContextLengthExceededError
from ..models import ConversationNode, ConversationMessage, ContentBlock, TokenUsage

if TYPE_CHECKING:
    import logging
    from ..logger import LLMLogger


class StreamingError(LLMError):
    """Streaming processing error."""
    pass


class StreamingInterruptedError(LLMError):
    """Streaming processing interrupted by user."""
    pass


class StreamingMessage(BaseModel):
    """Message accumulator for streaming processing."""

    role: str = "assistant"
    text_content: str = ""
    reasoning_content: str = ""

    tool_calls: Dict[int, Dict[str, Any]] = Field(default_factory=dict)

    signature: str = ""

    finish_reason: Optional[str] = None

    def has_content(self) -> bool:
        """Check if message has any content."""
        return bool(
            self.text_content or
            self.reasoning_content or
            self.tool_calls or
            self.signature
        )

    def to_content_blocks(self) -> List[ContentBlock]:
        """Convert to ContentBlock list."""
        blocks = []

        if self.reasoning_content:
            blocks.append(ContentBlock.thinking_block(self.reasoning_content))

        if self.text_content:
            blocks.append(ContentBlock.text_block(self.text_content))

        for tool_call in self.tool_calls.values():
            tool_use_block = ContentBlock.tool_use_block(
                id=tool_call["id"],
                name=tool_call["function"]["name"],
                input=json.loads(tool_call["function"]["arguments"]) if tool_call["function"]["arguments"] else {},
                signature=tool_call.get("signature")  # Extract signature for Gemini thinking support
            )
            blocks.append(tool_use_block)

        return blocks


class StreamingProcessor:
    """Processes streaming LLM API responses and converts to ConversationNode lists."""

    def __init__(self, logger: Optional['logging.LoggerAdapter'] = None, llm_logger: Optional['LLMLogger'] = None):
        """Initialize streaming processor.

        Args:
            logger: Logger for recording processing information.
            llm_logger: LLM raw message logger.
        """
        self.logger = logger
        self.llm_logger = llm_logger
        self._parse_error_fn = None
    
    async def process_streaming(self, response_stream,
                               session_id: str, cwd: str,
                               parse_usage_fn: Callable[[Dict[str, Any]], TokenUsage],
                               parse_error_fn: Optional[Callable[[dict], str]] = None,
                               callback: Optional[Callable[[str, str], None]] = None,
                               relay_mode: bool = False,
                               interrupt_event: Optional['asyncio.Event'] = None) -> tuple[List[ConversationNode], TokenUsage, Dict[str, Any]]:
        """Process streaming response.

        Two-stage processing:
        1. Merge stage: merge all SSE chunks into complete response (same format as non-streaming)
        2. Parse stage: parse complete response into ConversationNodes (shared with non-streaming)

        Args:
            response_stream: Response stream.
            session_id: Session ID.
            cwd: Current working directory.
            parse_usage_fn: Usage parsing function.
            parse_error_fn: Error parsing function.
            callback: Streaming callback function.
            relay_mode: bool = False,
            interrupt_event: Event for interrupting execution.

        Returns:
            Tuple of (conversation_nodes, usage, merged_response).
            merged_response: complete response in non-streaming format (for RL training).
        """
        self._parse_error_fn = parse_error_fn

        try:
            # Stage 1: Merge chunks into complete response
            merged_response, finish_reason = await self._merge_sse_chunks(
                response_stream, callback, relay_mode, interrupt_event
            )

            if self.llm_logger:
                await self.llm_logger.log_response(merged_response, request_type="streaming_request")

            # Extract usage
            usage = parse_usage_fn(merged_response.get('usage', {}))

            # Stage 2: Parse complete response into ConversationNodes
            nodes = self._parse_response_to_nodes(
                merged_response, session_id, cwd, usage
            )

            merged_nodes = self._apply_merging_strategy(nodes)
            final_nodes = self._post_process_nodes(merged_nodes)

            if callback:
                try:
                    callback("", 'stream_end')
                except TypeError:
                    pass

            return final_nodes, usage, merged_response

        except (MalformedResponseError, ContextLengthExceededError, StreamingInterruptedError):
            raise
        except Exception:
            raise StreamingError(f"Streaming processing failed: {traceback.format_exc()}")

    async def _merge_sse_chunks(self, response_stream, callback, relay_mode, interrupt_event) -> tuple[Dict[str, Any], Optional[str]]:
        """Merge SSE chunks into complete response (same format as non-streaming).

        Returns:
            Tuple of (merged_response, finish_reason).
            merged_response contains: choices[0]['message'] with all fields (raw_output_ids, etc.)
        """
        merged = {
            'choices': [{
                'index': 0,
                'message': {
                    'role': 'assistant',
                    'content': '',
                },
                'finish_reason': None
            }],
            'usage': {}
        }

        message = merged['choices'][0]['message']
        finish_reason = None

        async for chunk in self._parse_sse_stream(response_stream):
            if interrupt_event and interrupt_event.is_set():
                if self.logger:
                    self.logger.info("Streaming interrupted by user (ESC key)")
                raise StreamingInterruptedError("Streaming interrupted by user")

            if self.llm_logger:
                await self.llm_logger.log_streaming_chunk(chunk)

            # Merge usage
            if chunk.get('usage'):
                merged['usage'].update(chunk['usage'])

            if not chunk.get('choices'):
                continue

            choice = chunk['choices'][0]

            # Merge choice-level usage
            if choice.get('usage'):
                merged['usage'].update(choice['usage'])

            delta = choice.get('delta', {})

            # Merge message fields from delta
            for key, value in delta.items():
                if key == 'content' and value:
                    message['content'] += value
                    if callback:
                        try:
                            callback(value, 'content')
                        except TypeError:
                            callback(value)
                elif key == 'reasoning_content' and value:
                    message['reasoning_content'] = message.get('reasoning_content', '') + value
                    if callback:
                        try:
                            callback(value, 'thinking')
                        except TypeError:
                            pass
                elif key == 'signature' and value:
                    message['signature'] = message.get('signature', '') + value
                    if callback:
                        try:
                            callback(value, 'signature')
                        except TypeError:
                            pass
                elif key == 'tool_calls' and value:
                    if 'tool_calls' not in message:
                        message['tool_calls'] = {}
                    for tool_call_delta in value:
                        self._merge_tool_call_delta(tool_call_delta, message['tool_calls'])

            # Merge all other fields in choice['message'] (like raw_output_ids, response_log_probs)
            if 'message' in choice:
                for key, value in choice['message'].items():
                    if key not in ['role', 'content', 'reasoning_content', 'signature', 'tool_calls']:
                        # These are cumulative fields like raw_output_ids
                        if isinstance(value, list):
                            if key not in message:
                                message[key] = []
                            message[key] = value  # Direct assignment for cumulative lists
                        else:
                            message[key] = value

            # Check finish reason
            if choice.get('finish_reason') or choice.get('stop_reason'):
                finish_reason = choice.get('finish_reason') or choice.get('stop_reason')
                merged['choices'][0]['finish_reason'] = finish_reason
                if finish_reason == "malformed_function_call" and not relay_mode:
                    error_msg = f"Streaming API returned malformed_function_call error, retry needed"
                    if self.logger:
                        self.logger.warning(f"{error_msg}")
                    raise MalformedResponseError(error_msg)

        # Convert tool_calls dict to list
        if 'tool_calls' in message and isinstance(message['tool_calls'], dict):
            message['tool_calls'] = list(message['tool_calls'].values())

        # Validate response
        if not message.get('content') and not message.get('tool_calls') and not relay_mode:
            error_msg = f"Streaming API returned empty content, retry needed"
            if self.logger:
                self.logger.warning(f"{error_msg}, finish_reason: {finish_reason}")
            raise MalformedResponseError(error_msg)

        return merged, finish_reason

    def _merge_tool_call_delta(self, tool_call_delta: Dict[str, Any], accumulated_tool_calls: Dict[int, Dict[str, Any]]) -> None:
        """Merge tool call delta into accumulated tool calls."""
        tool_index = tool_call_delta.get('index', 0)

        if tool_index not in accumulated_tool_calls:
            accumulated_tool_calls[tool_index] = {
                'id': tool_call_delta.get('id', ''),
                'type': tool_call_delta.get('type', 'function'),
                'function': {
                    'name': tool_call_delta.get('function', {}).get('name', ''),
                    'arguments': tool_call_delta.get('function', {}).get('arguments', '')
                }
            }
            # Initialize signature field for Gemini support
            if 'signature' in tool_call_delta:
                accumulated_tool_calls[tool_index]['signature'] = tool_call_delta['signature']
        else:
            current = accumulated_tool_calls[tool_index]
            if 'function' in tool_call_delta and 'arguments' in tool_call_delta['function']:
                current['function']['arguments'] += tool_call_delta['function']['arguments']
            # Accumulate signature if present (Gemini may stream it)
            if 'signature' in tool_call_delta:
                current['signature'] = current.get('signature', '') + tool_call_delta['signature']

    def _parse_response_to_nodes(self, response: Dict[str, Any], session_id: str, cwd: str,
                                 usage: TokenUsage) -> List[ConversationNode]:
        """Parse complete response into ConversationNodes.

        Uses shared parse_message_to_node function (same as non-streaming).
        """
        from .response_processor import parse_message_to_node

        message_data = response['choices'][0]['message']

        node = parse_message_to_node(
            message_data=message_data,
            session_id=session_id,
            cwd=cwd,
            usage=usage,
            logger=self.logger
        )

        return [node]

    def _apply_merging_strategy(self, nodes: List[ConversationNode]) -> List[ConversationNode]:
        """Apply merging strategy to combine tool calling and thinking response messages."""
        if not nodes:
            return nodes
        
        merged_nodes = []
        for node in nodes:
            if self._is_tool_calling_node(node) and merged_nodes:
                self._merge_tool_calling_node(merged_nodes[-1], node)
            elif self._is_thinking_response_node(node) and merged_nodes:
                self._merge_thinking_node(merged_nodes[-1], node)
            else:
                merged_nodes.append(node)

        return merged_nodes

    def _is_tool_calling_node(self, node: ConversationNode) -> bool:
        """Check if node contains tool calls."""
        return any(block.type == "tool_use" for block in node.message.content)

    def _is_thinking_response_node(self, node: ConversationNode) -> bool:
        """Check if node is a thinking response node."""
        has_thinking = any(block.type == "thinking" for block in node.message.content)
        has_other = any(
            (block.type == "tool_use") or (block.type == "text" and block.text)
            for block in node.message.content
        )
        return has_thinking and not has_other

    def _merge_tool_calling_node(self, target_node: ConversationNode, tool_node: ConversationNode):
        """Merge tool calling node into target node."""
        for block in tool_node.message.content:
            if block.type == "tool_use":
                target_node.message.content.append(block)

    def _merge_thinking_node(self, target_node: ConversationNode, thinking_node: ConversationNode):
        """Merge thinking node into target node."""
        if not isinstance(target_node.message.content, list):
            target_node.message.content = []
        if not isinstance(thinking_node.message.content, list):
            return

        reasoning_content = ""
        for block in thinking_node.message.content:
            if block.type == "thinking" and block.reasoning_content:
                reasoning_content += block.reasoning_content

        if reasoning_content:
            text_block = None
            for block in target_node.message.content:
                if block.type == "text":
                    text_block = block
                    break

            if text_block:
                text_block.text = (text_block.text or "") + "\n\n" + reasoning_content
            else:
                target_node.message.content.insert(0, ContentBlock.text_block(reasoning_content))

    async def _parse_sse_stream(self, response_stream) -> AsyncGenerator[Dict[str, Any], None]:
        """Parse SSE stream with unified error detection logic."""
        async for line in response_stream.aiter_lines():
            line = line.strip()

            if not line:
                continue

            if line.startswith('data: '):
                data_content = line[6:]

                if data_content == '[DONE]':
                    break

                try:
                    chunk_data = json.loads(data_content)

                    if 'error' in chunk_data and self._parse_error_fn:
                        if self.logger:
                            self.logger.warning(f"Streaming chunk contains error field")

                        error_msg = self._parse_error_fn(chunk_data)
                        from ..config import ProviderError
                        raise ProviderError(f"Streaming response contains error: {error_msg}")

                    yield chunk_data
                except json.JSONDecodeError:
                    continue

    def _post_process_nodes(self, nodes: List[ConversationNode]) -> List[ConversationNode]:
        """Post-process nodes to ensure correct format and clean empty fields."""
        valid_nodes = []
        
        for node in nodes:
            if isinstance(node.message.content, list):
                valid_blocks = []
                
                for block in node.message.content:
                    if block.type == "text":
                        if block.text is None:
                            block.text = ""
                        valid_blocks.append(block)
                    elif block.type == "thinking":
                        if block.reasoning_content is None:
                            block.reasoning_content = ""
                        valid_blocks.append(block)
                    elif block.type in ["tool_use", "tool_result"]:
                        valid_blocks.append(block)
                
                if not valid_blocks:
                    valid_blocks.append(ContentBlock.text_block(""))
                
                node.message.content = valid_blocks
            
            elif isinstance(node.message.content, str):
                if node.message.content is None:
                    node.message.content = ""
            
            valid_nodes.append(node)
        
        return valid_nodes
