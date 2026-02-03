"""
Response Processor Module.

Processes non-streaming LLM responses and converts them to ConversationNode lists.
"""

import json
from typing import Dict, Any, List, Optional, Callable, TYPE_CHECKING
from ..models import ConversationNode, ConversationMessage, ContentBlock, TokenUsage
from ..config import MalformedResponseError

if TYPE_CHECKING:
    import logging


def _parse_tool_arguments(arguments_str: str, tool_name: str = "unknown", logger: Optional['logging.LoggerAdapter'] = None) -> Dict[str, Any]:
    """Parse tool arguments string, extracting only the first valid JSON object.

    Args:
        arguments_str: Arguments string (may contain multiple concatenated JSON objects)
        tool_name: Tool name for logging
        logger: Optional logger

    Returns:
        Parsed dict or empty dict if parsing fails
    """
    try:
        # Try normal JSON parsing first
        return json.loads(arguments_str)
    except json.JSONDecodeError:
        # Try to extract the first valid JSON object
        try:
            decoder = json.JSONDecoder()
            parsed_args, end_idx = decoder.raw_decode(arguments_str)

            # Check if there's trailing content
            if end_idx < len(arguments_str.strip()):
                if logger:
                    logger.warning(
                        f"Tool '{tool_name}': Detected malformed arguments with trailing content. "
                        f"Extracted first valid JSON object. "
                        f"Original length: {len(arguments_str)}, parsed until: {end_idx}"
                    )

            return parsed_args if isinstance(parsed_args, dict) else {}
        except (json.JSONDecodeError, ValueError) as e:
            if logger:
                logger.warning(
                    f"Tool '{tool_name}': Failed to parse arguments, using empty dict. "
                    f"Error: {e}, Arguments preview: {arguments_str[:200]}"
                )
            return {}


def parse_message_to_node(
    message_data: Dict[str, Any],
    session_id: str,
    cwd: str,
    usage: TokenUsage,
    logger: Optional['logging.LoggerAdapter'] = None
) -> ConversationNode:
    """Parse message dict to ConversationNode.

    Shared by ResponseProcessor (non-streaming) and StreamingProcessor (streaming).

    Args:
        message_data: Message dict from API response (choices[0]['message'])
        session_id: Session ID
        cwd: Current working directory
        usage: Token usage
        logger: Optional logger for recording warnings

    Returns:
        ConversationNode
    """
    # Extract content blocks (order: thinking -> text -> tool_use)
    blocks = []

    reasoning_content = message_data.get("reasoning_content")
    if reasoning_content:
        blocks.append(ContentBlock.thinking_block(reasoning_content))

    content = message_data.get("content", "")
    if content:
        blocks.append(ContentBlock.text_block(content))

    tool_calls = message_data.get("tool_calls") or []
    for tool_call in tool_calls:
        if tool_call.get("type") == "function":
            function_data = tool_call.get("function", {})

            arguments = function_data.get("arguments", "{}")
            if isinstance(arguments, str):
                parsed_args = _parse_tool_arguments(arguments, function_data.get("name", "unknown"), logger)
            else:
                parsed_args = arguments

            # Extract signature from tool_call (Gemini may include it here)
            tool_signature = tool_call.get("signature")

            tool_use_block = ContentBlock.tool_use_block(
                id=tool_call.get("id", ""),
                name=function_data.get("name", ""),
                input=parsed_args,
                signature=tool_signature
            )
            blocks.append(tool_use_block)

    # Create message
    message = ConversationMessage(
        role=message_data.get("role", "assistant"),
        content=blocks,
        model=message_data.get("model"),
        usage=usage,
        signature=message_data.get("signature")
    )

    # Create node
    node = ConversationNode(
        cwd=cwd,
        sessionId=session_id,
        type="assistant",
        message=message
    )

    return node


class ResponseProcessor:
    """Processes non-streaming LLM API responses and converts to ConversationNode lists."""

    def __init__(self, logger: Optional['logging.LoggerAdapter'] = None):
        """Initialize response processor.

        Args:
            logger: Logger for recording processing information.
        """
        self.logger = logger
    
    def process_response(self, raw_response: Dict[str, Any],
                        session_id: str, cwd: str,
                        parse_usage_fn: Callable[[Dict[str, Any]], TokenUsage]) -> tuple[List[ConversationNode], TokenUsage]:
        """Process complete response in non-streaming mode.

        Returns:
            Tuple of (conversation_nodes, usage).
        """
        nodes = []

        usage_data = raw_response.get("usage", {})
        usage = parse_usage_fn(usage_data)

        if "choices" not in raw_response or not raw_response["choices"]:
            error_msg = f"API returned empty response (no choices), retry needed"
            if self.logger:
                self.logger.warning(
                    f"{error_msg}, "
                    f"raw_response keys: {list(raw_response.keys())}, "
                    f"usage: {usage_data}"
                )
            raise MalformedResponseError(error_msg)
        else:
            for choice in raw_response["choices"]:
                message_data = choice.get("message", {})

                finish_reason = choice.get("finish_reason")
                if finish_reason == "malformed_function_call":
                    error_msg = f"API returned malformed_function_call error, retry needed"
                    if self.logger:
                        self.logger.warning(f"{error_msg}, message_data: {message_data}")
                    raise MalformedResponseError(error_msg)

                # Use shared parsing function
                node = parse_message_to_node(
                    message_data=message_data,
                    session_id=session_id,
                    cwd=cwd,
                    usage=usage,
                    logger=self.logger
                )

                # Validate content
                if not self._has_valid_content(node.message.content):
                    error_msg = f"API returned empty content message (content, reasoning_content, tool_calls all empty), retry needed"
                    if self.logger:
                        self.logger.warning(
                            f"{error_msg}, "
                            f"finish_reason: {finish_reason}, "
                            f"role: {message_data.get('role')}, "
                            f"content: '{message_data.get('content', '')}', "
                            f"reasoning_content: '{message_data.get('reasoning_content', '')}', "
                            f"tool_calls: {len(message_data.get('tool_calls', []))} calls"
                        )
                    raise MalformedResponseError(error_msg)

                nodes.append(node)

        merged_nodes = self._apply_merging_strategy(nodes)

        return merged_nodes, usage

    def _has_valid_content(self, content_blocks: List[ContentBlock]) -> bool:
        """Check if content_blocks contain valid content.

        Valid content includes:
        - Non-empty text content
        - Non-empty thinking/reasoning content
        - Any tool_use or tool_result blocks
        """
        if not content_blocks:
            return False
        
        for block in content_blocks:
            if block.type == "text" and block.text and block.text.strip():
                return True
            elif block.type == "thinking" and block.reasoning_content and block.reasoning_content.strip():
                return True
            elif block.type in ["tool_use", "tool_result"]:
                return True
        
        return False

    def _apply_merging_strategy(self, nodes: List[ConversationNode]) -> List[ConversationNode]:
        """Apply merging strategy to combine related nodes."""
        if not nodes:
            return nodes
        
        merged_nodes = []
        for node in nodes:
            if self._is_tool_calling_node(node) and merged_nodes:
                self._merge_tool_calling_node(merged_nodes[-1], node)
            elif self._is_thinking_response_node(node) and merged_nodes:
                self._merge_thinking_response_node(merged_nodes[-1], node)
            else:
                merged_nodes.append(node)

        return self._post_process_nodes(merged_nodes)

    def _is_tool_calling_node(self, node: ConversationNode) -> bool:
        """Check if node contains tool calls."""
        return any(block.type == "tool_use" for block in node.message.content)

    def _is_thinking_response_node(self, node: ConversationNode) -> bool:
        """Check if node is a thinking response node."""
        has_thinking = any(block.type == "thinking" and block.reasoning_content for block in node.message.content)
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

    def _merge_thinking_response_node(self, target_node: ConversationNode, thinking_node: ConversationNode):
        """Merge thinking response node into target node."""
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

            if text_block and not text_block.text:
                text_block.text = reasoning_content
            elif text_block:
                text_block.text = (text_block.text or "") + "\n\n" + reasoning_content
            else:
                target_node.message.content.insert(0, ContentBlock.text_block(reasoning_content))

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
