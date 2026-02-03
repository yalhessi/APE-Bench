"""
LLM Clients Data Models - Claude Code Standard Format.

Core design principles:
1. All content is List[ContentBlock] type
2. Tool definitions recorded through independent tool_definitions nodes, not system messages
3. tool_result uses role="user" in storage, dynamically converted to role="tool" only during API calls
4. ToolDefinitionsMessage is pure metadata, does not participate in LLM conversation
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Literal, Union
from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token usage statistics."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    cache_creation_input_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None
    total_cost: float = 0.0  # Cost without cache discount
    cached_total_cost: float = 0.0  # Actual cost after cache discount
    
    def model_post_init(self, __context) -> None:
        if self.total_tokens is None:
            self.total_tokens = self.input_tokens + self.output_tokens


class ContentBlock(BaseModel):
    """Message content block - explicit types, no Union types."""

    type: str

    # Text type fields
    text: Optional[str] = None
    is_retry_prompt: Optional[bool] = None  # Mark if this is a retry prompt (for smart stop detection)

    # Thinking type fields
    reasoning_content: Optional[str] = None

    # Tool_use type fields
    id: Optional[str] = None
    name: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    signature: Optional[str] = None  # Gemini thinking signature (for tool_use blocks)

    # Tool_result type fields
    tool_use_id: Optional[str] = None
    result_content: Optional[str] = None  # Unified tool result content (string form)

    @classmethod
    def text_block(cls, text: str, is_retry_prompt: bool = False) -> "ContentBlock":
        """Create text block."""
        return cls(type="text", text=text, is_retry_prompt=is_retry_prompt)

    @classmethod
    def thinking_block(cls, reasoning_content: str) -> "ContentBlock":
        """Create a thinking block."""
        return cls(type="thinking", reasoning_content=reasoning_content)
    
    @classmethod
    def tool_use_block(cls, id: str, name: str, input: Dict[str, Any], signature: Optional[str] = None) -> "ContentBlock":
        """Create a tool_use block."""
        return cls(type="tool_use", id=id, name=name, input=input, signature=signature)
    
    @classmethod
    def tool_result_block(cls, tool_use_id: str, content: Union[str, Dict, List], 
                         tool_name: Optional[str] = None) -> "ContentBlock":
        """Create a tool_result block - handles multiple content types and reuses name/id fields."""
        if isinstance(content, str):
            result_content = content
        else:
            result_content = json.dumps(content, ensure_ascii=False)
        
        return cls(type="tool_result", tool_use_id=tool_use_id, name=tool_name, 
                  result_content=result_content)
    
    def get_tool_result_content(self) -> Any:
        """Get the content returned by a tool_result block."""
        if self.type != "tool_result":
            return None
        return self.result_content


class ConversationMessage(BaseModel):
    """LLM-level message where content is always a list of ContentBlock instances.

    Note: there is no "tool" role in storage because tool_result entries
    are stored as role="user" and only converted to role="tool" by the message_formatter when calling APIs.
    """
    role: Literal["user", "assistant", "system"]
    content: List[ContentBlock]

    # Response metadata
    model: Optional[str] = None
    usage: Optional[TokenUsage] = None

    # Bedrock thinking fields
    signature: Optional[str] = None


class ToolDefinitionsMessage(BaseModel):
    """Tool definition message used purely to record tool metadata.

    Design notes:
    - Pure metadata node; does not participate in LLM dialog so no role field is required.
    - `tools` stores OpenAI-style tool definition lists.
    - message_formatter skips this node when sending to the API.
    """
    tools: List[Dict[str, Any]]


class ConversationNode(BaseModel):
    """Full conversation node following the Claude Code standard format.

    Note: there is no "tool" type because tool_result entries are stored as type="user"
    and only converted to role="tool" dynamically when calling APIs.
    """
    parentUuid: Optional[str] = None
    cwd: Optional[str] = None  # May be None in standalone mode
    sessionId: str
    type: Literal["user", "assistant", "system", "tool_definitions"]
    message: Union[ConversationMessage, ToolDefinitionsMessage]
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat() + "Z")


class ConversationSession(BaseModel):
    """Conversation session data model wrapping a list of ConversationNodes."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nodes: List[ConversationNode] = Field(default_factory=list)
    
    def _create_node(self, role: str, content_blocks: List[ContentBlock], cwd: Optional[str] = None,
                     model: Optional[str] = None, usage: Optional[TokenUsage] = None,
                     is_system: bool = False) -> ConversationNode:
        """Unified node creation helper."""
        # System messages have no parent; other messages link to the previous node
        parent_uuid = None if is_system else (self.nodes[-1].uuid if self.nodes else None)

        message = ConversationMessage(
            role=role,
            content=content_blocks,
            model=model,
            usage=usage
        )

        node = ConversationNode(
            parentUuid=parent_uuid,
            cwd=cwd,
            sessionId=self.session_id,
            type=role,
            message=message
        )

        return node
    
    # Core methods that only accept ContentBlock lists
    def add_user_message(self, content_blocks: List[ContentBlock], cwd: str) -> ConversationNode:
        """Add a user message (core method)."""
        node = self._create_node("user", content_blocks, cwd)
        self.nodes.append(node)
        return node

    def add_assistant_message(self, content_blocks: List[ContentBlock], cwd: str,
                             model: Optional[str] = None, usage: Optional[TokenUsage] = None) -> ConversationNode:
        """Add an assistant message (core method)."""
        node = self._create_node("assistant", content_blocks, cwd, model, usage)
        self.nodes.append(node)
        return node

    def add_system_message(self, content_blocks: List[ContentBlock], cwd: str) -> ConversationNode:
        """Add a system message (core method).

        Note: does not accept tools; use add_tool_definitions separately.
        """
        node = self._create_node("system", content_blocks, cwd, is_system=True)

        # Replace the first system message if present
        if self.nodes and self.nodes[0].type == "system":
            self.nodes[0] = node
        else:
            self.nodes.insert(0, node)

        return node

    def add_tool_definitions(self, tools: List[Dict[str, Any]], cwd: str) -> ConversationNode:
        """Add a tool-definition node (core method).

        Tool definitions are stored as independent nodes, not tied to a system message.
        If a system message exists, insert after it; otherwise insert at the start.

        Args:
            tools: List of tool definitions (OpenAI format).
            cwd: Working directory.

        Returns:
            The created ConversationNode.
        """
        # Create a dedicated ToolDefinitionsMessage
        tool_def_message = ToolDefinitionsMessage(tools=tools)

        # Create node (parentUuid None indicates metadata)
        node = ConversationNode(
            parentUuid=None,
            cwd=cwd,
            sessionId=self.session_id,
            type="tool_definitions",
            message=tool_def_message
        )

        # Insert after system message if present; otherwise at the front
        insert_index = 0
        if self.nodes and self.nodes[0].type == "system":
            insert_index = 1

        # Replace an existing tool_definitions node if it already exists
        existing_tool_def_idx = None
        for i, n in enumerate(self.nodes):
            if n.type == "tool_definitions":
                existing_tool_def_idx = i
                break

        if existing_tool_def_idx is not None:
            self.nodes[existing_tool_def_idx] = node
        else:
            self.nodes.insert(insert_index, node)

        return node
    
    def add_tool_result(self, tool_use_id: str, content: Union[str, Dict, List],
                       cwd: str, tool_name: Optional[str] = None) -> ConversationNode:
        """Add a tool-result message (core method)."""
        tool_result_block = ContentBlock.tool_result_block(tool_use_id, content, tool_name)
        return self.add_user_message([tool_result_block], cwd)  # tool_result stored as user type in Claude Code format
    
    def get_assistant_count(self) -> int:
        """Return the number of assistant messages."""
        return len([node for node in self.nodes if node.type == "assistant"])
    
    
