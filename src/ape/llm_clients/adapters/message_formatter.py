"""
Message Formatter Module.

Converts internal ContentBlock representations to standard API message format.
"""

import json
from typing import Dict, Any, List
from ..models import ConversationSession, ConversationNode, ContentBlock


class MessageFormatter:
    """Converts conversation nodes to standard API message format."""

    def format_for_api(self, session: ConversationSession) -> List[Dict[str, Any]]:
        """Convert ConversationSession to API message format.

        Args:
            session: Conversation session object.

        Returns:
            List of API message dictionaries.

        Note: tool_definitions nodes are excluded as tools are passed separately.
        """
        return [
            self._format_conversation_node(node)
            for node in session.nodes
            if node.type != "tool_definitions"
        ]

    def _format_conversation_node(self, node: ConversationNode) -> Dict[str, Any]:
        """Format a single ConversationNode into API message format."""
        content_text = ""
        reasoning_content = ""
        tool_calls = []
        tool_results = []
        
        for block in node.message.content:
            if block.type == "text" and block.text:
                if content_text:
                    content_text += "\n\n"
                content_text += block.text
            
            elif block.type == "thinking" and block.reasoning_content:
                reasoning_content += block.reasoning_content


            elif block.type == "tool_use":
                tool_call = {
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": self._serialize_arguments(block.input)
                    }
                }
                # Include signature if present (required by Gemini when using thinking)
                if block.signature:
                    tool_call["signature"] = block.signature
                tool_calls.append(tool_call)
            
            elif block.type == "tool_result":
                tool_results.append({
                    "content": block.get_tool_result_content(),
                    "tool_call_id": block.tool_use_id,
                    "name": block.name
                })

        if tool_results:
            if len(tool_results) > 1:
                raise ValueError(f"ConversationNode contains multiple tool_result blocks ({len(tool_results)}). Each tool_result should be in a separate node.")

            tool_result = tool_results[0]
            message = {
                "role": "tool",
                "content": tool_result["content"] if isinstance(tool_result["content"], str) else json.dumps(tool_result["content"], ensure_ascii=False),
                "tool_call_id": tool_result["tool_call_id"] or ""
            }
            if tool_result["name"]:
                message["name"] = tool_result["name"]
            return message

        message = {
            "role": node.message.role,
            "content": content_text or ""
        }

        if reasoning_content:
            message["reasoning_content"] = reasoning_content

        if tool_calls:
            message["tool_calls"] = tool_calls

        if node.message.signature:
            message["signature"] = node.message.signature

        return message

    def _serialize_arguments(self, arguments: Any) -> str:
        """Serialize tool arguments to JSON string."""
        if arguments is None:
            return "{}"
        
        if isinstance(arguments, str):
            return arguments
        
        try:
            return json.dumps(arguments, ensure_ascii=False)
        except (TypeError, ValueError):
            return "{}"
    
    def extract_tool_calls_from_nodes(self, nodes: List[ConversationNode]) -> List[Dict[str, Any]]:
        """Extract all tool calls from ConversationNode list.

        Returns:
            List of tool calls with tool_use_id, name, and arguments.
        """
        tool_calls = []
        
        for node in nodes:
            if node.type == "assistant":
                for block in node.message.content:
                    if block.type == "tool_use":
                        tool_calls.append({
                            "tool_use_id": block.id,
                            "name": block.name,
                            "arguments": block.input or {}
                        })
        
        return tool_calls
    
    def check_has_tool_calls(self, nodes: List[ConversationNode]) -> bool:
        """Check if node list contains any tool calls."""
        for node in nodes:
            if node.type == "assistant":
                for block in node.message.content:
                    if block.type == "tool_use":
                        return True
        return False