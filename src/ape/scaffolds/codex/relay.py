"""
Codex HTTP Relay Service - the Responses API Codex speaks, answered by APE's client.

`codex-cli` 0.144 refuses Chat Completions (`wire_api = "chat"` is "no longer supported") and
always streams, so this relay serves `/responses` and answers as a Responses event stream. Every
request is rebuilt as a `ConversationSession` and sent through APE's own client with the run's
`llm_config`, so the model, its reasoning settings, usage, limits and the recorded turns are the
same as under the other scaffolds; what Codex asks for (`model`, `reasoning`) is not used.

Two shapes have no Chat equivalent, and both were captured from the installed CLI against a local
recording server (no model, 2026-10-01):

- **MCP tools arrive as a `namespace`** (`{"type": "namespace", "name": "mcp__core", "tools":
  [...]}`). They are flattened to `mcp__core__<tool>` for the backend, and a call is answered as
  `{"name": "<tool>", "namespace": "mcp__core"}`: Codex refuses the flat name ("unsupported call").
- **Reasoning comes back as input items.** Codex returns each turn's reasoning items, encrypted
  content and all but without their `id`. They become the turn's message `signature`, the slot
  `openai_provider` reads for carry-over, with the `id` restored from what this relay sent.

A message's `phase` takes the same road in both directions: out on the message item, and back in
from the one Codex returns (it does return it; captured the same way, 2026-10-05).
"""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from ape.llm_clients.adapters.streaming_processor import StreamingInterruptedError
from ape.llm_clients.config import ContextLengthExceededError, MalformedResponseError
from ape.llm_clients.models import ContentBlock, ConversationNode, ConversationSession, TokenUsage
from ape.scaffolds.utils.base_relay import BaseRelaySession

#: Codex tool types with no function-call equivalent for the backend. None is offered to the
#: model; the scaffold disables what it can, and this drops the rest.
_UNRELAYED_TOOL_TYPES = frozenset({"custom", "web_search", "tool_search", "local_shell",
                                   "image_generation", "computer_use_preview"})


def _text(item: Dict[str, Any]) -> str:
    content = item.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part.get("text") or "" for part in content if isinstance(part, dict))
    return ""


def response_event_stream(response: Dict[str, Any]) -> str:
    """A finished Responses object as the event stream of a streamed one: created, each output
    item added and done, completed. The minimal sequence the CLI was shown to accept."""

    def event(name: str, data: Dict[str, Any]) -> str:
        return f"event: {name}\ndata: {json.dumps(data)}\n\n"

    out = [event("response.created", {"type": "response.created",
                                       "response": {**response, "status": "in_progress", "output": []}})]
    for index, item in enumerate(response.get("output") or []):
        out.append(event("response.output_item.added",
                         {"type": "response.output_item.added", "output_index": index, "item": item}))
        out.append(event("response.output_item.done",
                         {"type": "response.output_item.done", "output_index": index, "item": item}))
    out.append(event("response.completed", {"type": "response.completed", "response": response}))
    return "".join(out)


class CodexRelaySession(BaseRelaySession):
    """Codex relay session - the Responses API, served from APE's client."""

    def __init__(self, *args, relayed_builtin_tools: Optional[List[str]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        # Codex's own function tools that reach the model; None passes all. Namespace (MCP)
        # tools always pass.
        self.relayed_builtin_tools = (None if relayed_builtin_tools is None
                                      else frozenset(relayed_builtin_tools))
        # flat backend name -> (namespace, tool name), from the tools Codex offers
        self._namespaced: Dict[str, Tuple[str, str]] = {}
        # encrypted reasoning content -> the item id this relay sent with it
        self._reasoning_ids: Dict[str, str] = {}

    def _setup_routes(self) -> None:
        """Codex posts to `<base_url>/responses`; both spellings of the base are served."""
        for path in ('/responses', '/v1/responses'):
            self._app.add_api_route(path, self._handle_responses, methods=['POST'])
            self._app.add_api_route(path, self._handle_options, methods=['OPTIONS'])

    def _get_env_vars(self) -> Dict[str, str]:
        """Codex reads its provider from the scaffold's config.toml, not the environment."""
        return {}

    async def _handle_request(self, request: Request) -> Response:
        return await self._handle_responses(request)

    # --- request: Responses -> ConversationSession -------------------------------------------

    def _backend_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Codex's tools as function tools, a namespace's children flattened to `<ns>__<tool>`."""

        def function(name: str, tool: Dict[str, Any]) -> Dict[str, Any]:
            return {"type": "function", "function": {
                "name": name, "description": tool.get("description") or "",
                "parameters": tool.get("parameters") or {"type": "object", "properties": {}}}}

        out = []
        for tool in tools:
            kind = tool.get("type")
            if kind == "function":
                if self.relayed_builtin_tools is None or tool["name"] in self.relayed_builtin_tools:
                    out.append(function(tool["name"], tool))
            elif kind == "namespace":
                for child in tool.get("tools") or []:
                    if child.get("type") == "function":
                        flat = f"{tool['name']}__{child['name']}"
                        self._namespaced[flat] = (tool["name"], child["name"])
                        out.append(function(flat, child))
            elif kind not in _UNRELAYED_TOOL_TYPES:
                self.logger.warning(f"Codex offered a tool of unknown type {kind!r}; not relayed")
        return out

    def _flat_name(self, call: Dict[str, Any]) -> str:
        namespace = call.get("namespace")
        return f"{namespace}__{call.get('name')}" if namespace else call.get("name") or ""

    def _assistant_turn(self, session: ConversationSession, items: List[Dict[str, Any]],
                        cwd: Optional[str]) -> None:
        """One run of model-output items as an assistant node, its reasoning as the signature."""
        blocks: List[ContentBlock] = []
        order: List[Dict[str, Any]] = []
        for item in items:
            kind = item.get("type")
            if kind == "reasoning":
                encrypted = item.get("encrypted_content")
                if not encrypted:
                    continue  # a summary alone carries nothing the backend accepts back
                entry = {"type": "reasoning", "encrypted_content": encrypted,
                         "summary": item.get("summary") or []}
                rid = item.get("id") or self._reasoning_ids.get(encrypted)
                if rid:
                    entry["id"] = rid
                order.append(entry)
            elif kind == "function_call":
                try:
                    arguments = json.loads(item.get("arguments") or "{}")
                except (TypeError, ValueError):
                    arguments = {"_raw": item.get("arguments")}
                blocks.append(ContentBlock.tool_use_block(item.get("call_id") or "",
                                                          self._flat_name(item), arguments))
                order.append({"type": "function_call", "call_id": item.get("call_id") or ""})
            else:
                text = _text(item)
                if text:
                    blocks.append(ContentBlock.text_block(text))
                    order.append({"type": "message", "phase": item["phase"]} if item.get("phase")
                                 else {"type": "message"})
        if not blocks:
            return  # reasoning with nothing after it: the API rejects such an item
        node = session.add_assistant_message(blocks, cwd)
        if any(e["type"] == "reasoning" or e.get("phase") for e in order):
            node.message.signature = json.dumps({"responses_output": order})

    def _responses_to_session(self, body: Dict[str, Any],
                              tools: List[Dict[str, Any]]) -> ConversationSession:
        session = ConversationSession()
        cwd = self.cwd
        items = list(body.get("input") or [])
        # A session holds one system message, at the front, and a second replaces the first. So
        # the instructions and the developer messages that open the input (Codex's permissions
        # text) are one system message; a developer message later on becomes a user message,
        # which keeps its place.
        system = [body["instructions"]] if body.get("instructions") else []
        while items and (items[0].get("type") or "message") == "message" and items[0].get("role") in ("system", "developer"):
            system.append(_text(items.pop(0)))
        if system:
            session.add_system_message([ContentBlock.text_block("\n\n".join(system))], cwd)
        if tools:
            session.add_tool_definitions(tools, cwd)
        pending: List[Dict[str, Any]] = []
        for item in items:
            kind = item.get("type") or "message"
            role = item.get("role")
            if kind in ("reasoning", "function_call") or (kind == "message" and role == "assistant"):
                pending.append(item)
                continue
            if pending:
                self._assistant_turn(session, pending, cwd)
                pending = []
            if kind == "function_call_output":
                output = item.get("output")
                if not isinstance(output, str):
                    output = json.dumps(output)
                session.add_tool_result(tool_use_id=item.get("call_id") or "", content=output, cwd=cwd)
            elif kind == "message":
                session.add_user_message([ContentBlock.text_block(_text(item))], cwd)
            else:
                self.logger.warning(f"Codex input item of type {kind!r} not relayed")
        if pending:
            self._assistant_turn(session, pending, cwd)
        return session

    # --- response: ConversationNode -> Responses ---------------------------------------------

    def _nodes_to_response(self, nodes: List[ConversationNode], usage: TokenUsage,
                           model: str) -> Dict[str, Any]:
        output: List[Dict[str, Any]] = []

        def message(text: str, phase: Optional[str] = None) -> Dict[str, Any]:
            item = {"type": "message", "id": f"msg_{uuid.uuid4().hex[:24]}", "role": "assistant",
                    "status": "completed",
                    "content": [{"type": "output_text", "text": text, "annotations": []}]}
            if phase:
                item["phase"] = phase
            return item

        def call(block: ContentBlock) -> Dict[str, Any]:
            namespace, name = self._namespaced.get(block.name, (None, block.name))
            item = {"type": "function_call", "id": f"fc_{uuid.uuid4().hex[:24]}",
                    "call_id": block.id, "name": name,
                    "arguments": json.dumps(block.input or {}), "status": "completed"}
            if namespace:
                item["namespace"] = namespace
            return item

        for node in nodes:
            if node.type != "assistant":
                continue
            texts = [b.text for b in node.message.content if b.type == "text" and b.text]
            calls = {b.id: b for b in node.message.content if b.type == "tool_use"}
            try:
                carried = json.loads(node.message.signature or "{}").get("responses_output") or []
            except (TypeError, ValueError, AttributeError):
                carried = []
            for entry in carried:
                if entry.get("type") == "reasoning" and entry.get("encrypted_content"):
                    rid = entry.get("id") or f"rs_{uuid.uuid4().hex[:24]}"
                    self._reasoning_ids[entry["encrypted_content"]] = rid
                    output.append({"type": "reasoning", "id": rid, "summary": entry.get("summary") or [],
                                   "encrypted_content": entry["encrypted_content"]})
                elif entry.get("type") == "message" and texts:
                    output.append(message("\n\n".join(texts), entry.get("phase")))
                    texts = []
                elif entry.get("type") == "function_call" and entry.get("call_id") in calls:
                    output.append(call(calls.pop(entry["call_id"])))
            if texts:
                output.append(message("\n\n".join(texts)))
            output.extend(call(b) for b in calls.values())

        return {"id": f"resp_{uuid.uuid4().hex[:24]}", "object": "response", "status": "completed",
                "model": model, "output": output,
                "usage": {"input_tokens": usage.input_tokens or 0,
                          "output_tokens": usage.output_tokens or 0,
                          "total_tokens": (usage.input_tokens or 0) + (usage.output_tokens or 0),
                          "input_tokens_details": {"cached_tokens": usage.cache_read_input_tokens or 0},
                          "output_tokens_details": {"reasoning_tokens": usage.reasoning_tokens or 0}}}

    # --- the route ---------------------------------------------------------------------------

    async def _handle_responses(self, request: Request) -> Response:
        try:
            limit_response = await self._check_limits_and_shutdown_if_needed()
            if limit_response is not None:
                return limit_response

            body = await request.json()
            model = body.get("model") or ""
            self.logger.info(f"Received request: {model} "
                             f"(turn {self.get_current_turns() + 1}/{self.max_turns or '∞'})")

            tools = self._backend_tools(body.get("tools") or [])
            session = self._responses_to_session(body, tools)
            response_nodes, usage, raw_response = await self._call_backend(
                session, tools or None, body.get("max_output_tokens"), None, self.llm_config)

            if self.conversations_dir:
                await self.record_turn(session, response_nodes, usage, model, raw_response)

            response = self._nodes_to_response(response_nodes, usage, model)
            self.logger.info(f"Response completed: {model}")
            return Response(content=response_event_stream(response), media_type="text/event-stream")

        except asyncio.CancelledError:
            self.logger.debug("Request cancelled during relay shutdown")
            return Response(status_code=499)
        except (ContextLengthExceededError, MalformedResponseError, StreamingInterruptedError) as e:
            self.last_error = e
            if self._server:
                self._server.should_exit = True
            status_code = 400 if isinstance(e, ContextLengthExceededError) else 500
            return JSONResponse({"error": {"type": type(e).__name__, "message": str(e)}},
                                status_code=status_code)
        except Exception as e:  # noqa: BLE001
            import traceback
            self.logger.error(f"Request failed: {traceback.format_exc()}")
            return JSONResponse({"error": {"type": "internal_error", "message": str(e)}},
                                status_code=500)
