"""
Conversation Prefix Tree utilities.

Provides a forest structure that deduplicates recorded relay sessions by
their shared prefixes while preserving the original ConversationNode payloads.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Sequence

import aiofiles
from ape.llm_clients.models import (
    ContentBlock,
    ConversationMessage,
    ConversationNode,
    ToolDefinitionsMessage,
)
from ape.utils.logging import create_logger


def _content_block_signature(block: ContentBlock) -> Dict[str, object]:
    """Return a deterministic dict representing a content block."""
    signature: Dict[str, object] = {"type": block.type}
    if block.text is not None:
        signature["text"] = block.text
    if block.is_retry_prompt is not None:
        signature["is_retry_prompt"] = block.is_retry_prompt
    if block.reasoning_content is not None:
        signature["reasoning_content"] = block.reasoning_content
    if block.name is not None:
        signature["name"] = block.name
    if block.input is not None:
        signature["input"] = block.input
    if block.result_content is not None:
        signature["result_content"] = block.result_content
    return signature


def _conversation_message_signature(
    message: ConversationMessage,
) -> Dict[str, object]:
    """Return a deterministic dict representing a conversation message."""
    signature: Dict[str, object] = {
        "role": message.role,
        "content": [_content_block_signature(block) for block in message.content],
    }
    return signature


def compute_node_signature(node: ConversationNode) -> str:
    """Generate a normalized signature string for a ConversationNode."""
    payload: Dict[str, object] = {
        "type": node.type,
        "cwd": node.cwd,
    }

    if isinstance(node.message, ConversationMessage):
        payload["message"] = _conversation_message_signature(node.message)
    elif isinstance(node.message, ToolDefinitionsMessage):
        payload["tool_definitions"] = node.message.tools

    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


class ConversationTreeNode:
    """Tree node that wraps a ConversationNode and its children."""

    __slots__ = ("node", "children", "signature")

    def __init__(self, node: ConversationNode):
        self.node = node
        self.children: Dict[str, "ConversationTreeNode"] = {}
        self.signature = compute_node_signature(node)

    def add_child(self, child: "ConversationTreeNode") -> "ConversationTreeNode":
        existing = self.children.get(child.signature)
        if existing:
            return existing
        self.children[child.signature] = child
        return child

    def to_dict(self) -> Dict[str, object]:
        return {
            "node": self.node.model_dump(mode="json"),
            "children": [child.to_dict() for child in self.children.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ConversationTreeNode":
        node = ConversationNode.model_validate(data["node"])
        tree_node = cls(node)
        for child_data in data.get("children", []):
            child = cls.from_dict(child_data)
            tree_node.children[child.signature] = child
        return tree_node


class ConversationPrefixTreeManager:
    """
    Maintain a prefix forest for recorded conversations and persist to JSONL.
    """

    def __init__(self, storage_path: Path, logger=None):
        self.storage_path = storage_path
        self.logger = logger or create_logger()
        self._lock = asyncio.Lock()
        self._loaded = False
        self._roots: Dict[str, ConversationTreeNode] = {}

    async def add_conversation(self, nodes: Sequence[ConversationNode]) -> None:
        """Insert a complete conversation path into the prefix forest."""
        if not nodes:
            return

        async with self._lock:
            await self._ensure_loaded()
            self._insert_nodes(nodes)
            await self._persist()

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._loaded = True
            return

        try:
            async with aiofiles.open(self.storage_path, "r", encoding="utf-8") as f:
                content = await f.read()
        except Exception as exc:
            self.logger.warning(
                f"Failed to read conversation prefix trees from {self.storage_path}: {exc}"
            )
            self._loaded = True
            return

        for line in content.splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                tree_node = ConversationTreeNode.from_dict(record["tree"])
                self._roots[record["signature"]] = tree_node
            except Exception as exc:
                self.logger.warning(
                    f"Failed to parse tree record from {self.storage_path}: {exc}"
                )

        self._loaded = True

    def _insert_nodes(self, nodes: Sequence[ConversationNode]) -> None:
        iterator = iter(nodes)
        first_node = next(iterator, None)
        if first_node is None:
            return

        root_signature = compute_node_signature(first_node)
        root = self._roots.get(root_signature)
        if not root:
            root = ConversationTreeNode(first_node.model_copy(deep=True))
            self._roots[root_signature] = root

        current = root
        for node in iterator:
            child_node = ConversationTreeNode(node.model_copy(deep=True))
            current = current.add_child(child_node)

    async def _persist(self) -> None:
        records = [
            json.dumps(
                {"signature": signature, "tree": root.to_dict()},
                ensure_ascii=False,
            )
            for signature, root in sorted(self._roots.items())
        ]

        temp_path = self.storage_path.with_suffix(".tmp")
        try:
            async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
                await f.write("\n".join(records))
                if records:
                    await f.write("\n")
            temp_path.replace(self.storage_path)
        except Exception as exc:
            self.logger.error(
                f"Failed to persist conversation prefix trees to {self.storage_path}: {exc}"
            )
