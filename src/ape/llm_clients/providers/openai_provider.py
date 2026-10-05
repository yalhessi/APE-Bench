"""
OpenAI provider implementations: Chat Completions, and Responses behind `openai_api`.
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import uuid

from .base import BaseProvider
from ..config import MODEL_MAPPINGS, LLMProvider, ProviderError, RequestRejectedError


def is_openai_model(model_name: Optional[str]) -> bool:
    """An OpenAI model, called directly or through ELM (a row marked `openai_responses`)."""

    entry = MODEL_MAPPINGS.get(model_name) or {}
    return entry.get("provider") is LLMProvider.OPENAI or bool(entry.get("openai_responses"))


def reasoning_drop_refusal(config) -> Optional[str]:
    """Why this config would drop an OpenAI model's reasoning between turns, or None.

    The GPT-5 models reason, and only the Responses API returns that reasoning, as encrypted
    items the next request can carry back. Chat Completions returns none, so every turn of a
    session would reason from nothing, and Responses with carry-over off drops the items too.
    So an OpenAI model runs on Responses with carry-over, or not at all (the user, 2026-10-05).
    Carry-over was already the standard condition: it concluded 44 of 44 sessions and cut
    repeats tenfold at a fifth of the cost (`docs/todo/reviewer-model-gap.md`, Phase 0). Chat
    Completions also refuses tools with reasoning for gpt-5.4 and gpt-5.5 (HTTP 400, 2026-09-30).

    One check with two callers: the OpenAI providers refuse a request before sending it, and
    `cli plan` refuses the run before any spend. A refusal and not a new default, so a config
    written for the old endpoint fails at once instead of quietly meaning something else.
    """

    if not is_openai_model(getattr(config, "model_name", None)):
        return None
    if getattr(config, "openai_api", "chat_completions") != "responses":
        return (f"{config.model_name} is an OpenAI model, and those run on the Responses API with "
                "their reasoning carried: Chat Completions returns no reasoning, so every turn "
                "would reason from nothing. Set llm_config.openai_api: responses and "
                "llm_config.openai_responses_reasoning_carryover: true.")
    if not config.openai_responses_reasoning_carryover:
        return (f"{config.model_name} on Responses with carry-over off drops each turn's reasoning "
                "items. Set llm_config.openai_responses_reasoning_carryover: true.")
    return None


class OpenAIProvider(BaseProvider):
    """OpenAI Chat Completions provider."""

    DEFAULT_BASE_URL = "https://api.openai.com/v1/chat/completions"

    def get_request_info(self, session_id: Optional[str] = None) -> Tuple[str, Dict[str, str]]:
        """Get OpenAI request URL and headers."""
        url = self.config.base_url or self.DEFAULT_BASE_URL

        if not self.config.api_key:
            raise ProviderError("OpenAI API key is required (LLMConfig.api_key).")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        if session_id:
            headers["X-Session-Id"] = session_id
        else:
            headers["X-Session-Id"] = str(uuid.uuid4())

        return url, headers

    def build_request_payload(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Build OpenAI Chat Completions payload."""
        refusal = reasoning_drop_refusal(self.config)
        if refusal:
            raise RequestRejectedError(refusal)
        payload: Dict[str, Any] = {
            "model": self.config.formal_model_name,
            "messages": messages,
            "max_completion_tokens": self.config.max_tokens, # max_tokens is not supported for all OpenAI models
            "temperature": self.config.temperature,
            "stream": stream,
        }

        # Absent means "the provider's default", which is what every run before this field
        # did. Sent only when stated, so adding the field changed no existing run.
        if self.config.reasoning_effort is not None:
            payload["reasoning_effort"] = self.config.reasoning_effort

        if stream:
            # OpenAI only includes token usage in streamed chat-completions responses
            # when stream_options.include_usage is explicitly requested.
            payload["stream_options"] = {"include_usage": True}

        if tools:
            payload["tools"] = tools

        return payload


class OpenAIResponsesProvider(OpenAIProvider):
    """OpenAI's `/v1/responses`, translated to and from Chat Completions at this boundary.

    Why it exists: gpt-5.4 and gpt-5.5 reject tools with a reasoning effort on Chat
    Completions (HTTP 400, "use /v1/responses or set reasoning_effort to 'none'"), and every
    review task sends tools. Selected by `LLMConfig.openai_api: responses`.

    Everything else in the client is Chat-Completions-shaped -- the formatter emits
    `messages`, `ResponseProcessor` reads `choices[0].message`, `StreamingProcessor` merges
    `delta` chunks, `parse_usage` reads `prompt_tokens` -- so this class translates the
    request on the way out and the response on the way back, and nothing downstream changes.

    Measured against the live endpoint on 2026-09-30 (fixtures in tests/ape/fixtures/openai/):

    * a Chat tool flattens to `{type, name, description, parameters}`. Responses makes a tool
      **strict** by default when its schema qualifies -- it rewrote a probe tool to
      `additionalProperties: false, strict: true` -- and Chat Completions never does, so
      `strict: false` is sent unless the tool asks for it. Strict means constrained decoding,
      which would be a different condition.
    * `temperature` 1.0 is accepted with reasoning on, anything else is a 400 naming
      `temperature`. It is sent as configured, as the Chat provider sends it; a bad
      combination fails at once through `RequestRejectedError`.
    * usage uses other names -- `input_tokens`, `input_tokens_details.cached_tokens`,
      `output_tokens`, `output_tokens_details.reasoning_tokens` -- and the same accounting:
      cached is a subset of input, `total = input + output`. They map one to one.
    * `store: false` throughout, so nothing refers to server-side state.
    * a stream's final `response.completed` event carries the whole response.

    Reasoning between turns is `openai_responses_reasoning_carryover`, which an OpenAI model must
    have on (`reasoning_drop_refusal`); off survives only for a model that is not one. On, the
    encrypted items ride in the assistant message's
    `signature` (the slot `ConversationMessage` keeps for opaque provider reasoning state) and
    go back as `reasoning` input items, in their original order: the API rejects a reasoning
    item passed without the item that followed it.

    A message's `phase` (`commentary` before tool calls, `final_answer`) rides in the same slot and
    goes back on the replayed text, with carry-over on or off. gpt-5.4 and gpt-5.5 set it, and
    OpenAI's reasoning guide says to keep it in a manual replay: "Missing or dropped `phase` can
    cause preambles to be treated as final answers". No response logged here held two messages
    (6,278 calls, 2026-10-05), so a turn's joined text takes its first message's phase.

    `openai_responses_reasoning_summary` asks for a summary of each reasoning item. It comes back
    inside the item, and is also recorded as the turn's `reasoning_content`, which the processors
    keep as a thinking block and nothing sends back. Only beside text or a call: a reply that is
    reasoning alone stays the empty reply it is without the knob.

    No `reasoning.context` is sent. The default, `current_turn`, keeps carried reasoning since the
    last user message or text-only answer, and a review session has neither after its task prompt
    (0 in 33 high-effort sessions, measured 2026-09-30), so it keeps all of it. `all_turns` would
    change nothing there, and gpt-5.2 refuses it.
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1/responses"

    @property
    def _carryover(self) -> bool:
        return self.config.openai_responses_reasoning_carryover

    def build_request_payload(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """The Responses payload for these Chat Completions messages and tools."""

        refusal = reasoning_drop_refusal(self.config)
        if refusal:
            raise RequestRejectedError(refusal)
        instructions, items = responses_input(messages, carryover=self._carryover)
        payload: Dict[str, Any] = {
            "model": self.config.formal_model_name,
            "input": items,
            "max_output_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": stream,
            "store": False,
        }
        if instructions:
            payload["instructions"] = instructions
        if self.config.reasoning_effort is not None:
            payload["reasoning"] = {"effort": self.config.reasoning_effort}
        if self.config.openai_responses_reasoning_summary is not None:
            payload.setdefault("reasoning", {})["summary"] = (
                self.config.openai_responses_reasoning_summary)
        if self._carryover:
            payload["include"] = ["reasoning.encrypted_content"]
        if tools:
            payload["tools"] = [responses_tool(tool) for tool in tools]
        return payload

    async def make_request(self, payload: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        response = await super().make_request(payload, session_id)
        return responses_to_chat_completion(response, carryover=self._carryover)

    async def make_streaming_request(self, payload: Dict[str, Any], session_id: Optional[str] = None):
        response = await super().make_streaming_request(payload, session_id)
        return _CompletedResponseStream(response, carryover=self._carryover)


def responses_tool(tool: Dict[str, Any]) -> Dict[str, Any]:
    """A Chat Completions tool as a Responses function tool, non-strict unless it says so."""

    function = tool.get("function") or {}
    flat = {"type": "function", "name": function.get("name", ""),
            "parameters": function.get("parameters") or {"type": "object", "properties": {}},
            "strict": bool(function.get("strict", False))}
    if function.get("description"):
        flat["description"] = function["description"]
    return flat


def responses_input(messages: List[Dict[str, Any]], *,
                    carryover: bool) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """Chat Completions messages as Responses `(instructions, input)`.

    Leading system messages become `instructions`; a later one stays in place as a system
    item. A tool result becomes a `function_call_output`, and an assistant turn becomes its
    text, under the `phase` it was given, and its `function_call` items -- preceded, with
    carry-over on, by the reasoning items it recorded, in their original order.
    """

    instructions: List[str] = []
    items: List[Dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        if role == "system" and not items:
            if message.get("content"):
                instructions.append(message["content"])
        elif role == "tool":
            items.append({"type": "function_call_output",
                          "call_id": message.get("tool_call_id") or "",
                          "output": message.get("content") or ""})
        elif role == "assistant":
            items.extend(_assistant_items(message, carryover=carryover))
        else:
            items.append({"role": role, "content": message.get("content") or ""})
    return "\n\n".join(instructions) or None, items


def _assistant_items(message: Dict[str, Any], *, carryover: bool) -> List[Dict[str, Any]]:
    """One assistant turn as input items, in the order the model produced them."""

    text = ({"role": "assistant", "content": message["content"]}
            if message.get("content") else None)
    calls = {}
    for call in message.get("tool_calls") or []:
        function = call.get("function") or {}
        calls[call.get("id") or ""] = {
            "type": "function_call", "call_id": call.get("id") or "",
            "name": function.get("name") or "", "arguments": function.get("arguments") or "{}"}

    items: List[Dict[str, Any]] = []
    for entry in _carried_output(message.get("signature")):
        if entry.get("type") == "reasoning":
            if carryover:
                items.append(entry)
        elif entry.get("type") == "message" and text is not None:
            items.append({**text, "phase": entry["phase"]} if entry.get("phase") else text)
            text = None
        elif entry.get("type") == "function_call" and entry.get("call_id") in calls:
            items.append(calls.pop(entry["call_id"]))
    if text is not None:
        items.append(text)
    items.extend(calls.values())
    return items


def _carried_output(signature: Optional[str]) -> List[Dict[str, Any]]:
    """The output order a turn recorded, or nothing if the signature is not one."""

    if not signature:
        return []
    try:
        carried = json.loads(signature)
    except (TypeError, ValueError):
        return []
    order = carried.get("responses_output") if isinstance(carried, dict) else None
    return [entry for entry in order if isinstance(entry, dict)] if isinstance(order, list) else []


def responses_to_chat_completion(response: Dict[str, Any], *, carryover: bool) -> Dict[str, Any]:
    """A Responses response as the Chat Completions response the processors read."""

    texts: List[str] = []
    refusals: List[str] = []
    summaries: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    order: List[Dict[str, Any]] = []
    for item in response.get("output") or []:
        kind = item.get("type")
        if kind == "message":
            parts = item.get("content") or []
            texts.append("".join(p.get("text") or "" for p in parts if p.get("type") == "output_text"))
            refusals.extend(p.get("refusal") or "" for p in parts if p.get("type") == "refusal")
            order.append({"type": "message", "phase": item["phase"]} if item.get("phase")
                         else {"type": "message"})
        elif kind == "function_call":
            tool_calls.append({"id": item.get("call_id") or "", "type": "function",
                               "function": {"name": item.get("name") or "",
                                            "arguments": item.get("arguments") or "{}"}})
            order.append({"type": "function_call", "call_id": item.get("call_id") or ""})
        elif kind == "reasoning":
            summaries.extend(part.get("text") or "" for part in item.get("summary") or [])
            if carryover:
                order.append({key: item[key]
                              for key in ("type", "id", "encrypted_content", "summary") if key in item})

    message: Dict[str, Any] = {"role": "assistant",
                               "content": "\n\n".join(t for t in texts if t) or None}
    if tool_calls:
        message["tool_calls"] = tool_calls
    summary = "\n\n".join(s for s in summaries if s)
    if summary and (message["content"] or tool_calls):
        message["reasoning_content"] = summary
    if refusals:
        message["refusal"] = "\n\n".join(refusals)
    if any(entry["type"] == "reasoning" or entry.get("phase") for entry in order):
        message["signature"] = json.dumps({"responses_output": order})

    if response.get("status") == "incomplete":
        reason = (response.get("incomplete_details") or {}).get("reason")
        finish_reason = {"max_output_tokens": "length"}.get(reason, reason or "length")
    else:
        finish_reason = "tool_calls" if tool_calls else "stop"

    usage = response.get("usage") or {}
    return {
        "id": response.get("id"),
        "object": "chat.completion",
        "model": response.get("model"),
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
        "usage": {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "prompt_tokens_details": {
                "cached_tokens": (usage.get("input_tokens_details") or {}).get("cached_tokens", 0)},
            "completion_tokens_details": {
                "reasoning_tokens":
                    (usage.get("output_tokens_details") or {}).get("reasoning_tokens", 0)},
        },
    }


class _CompletedResponseStream:
    """A Responses event stream, re-emitted as the single Chat Completions chunk it amounts to.

    Streaming is kept because it keeps a long reasoning call's connection alive -- gpt-5.2's
    longest high-effort call took 230 s. The typed deltas are ignored: the final
    `response.completed` (or `response.incomplete`) event carries the whole response, so
    `StreamingProcessor` merges one chunk and no second delta merger exists. A failure event
    is re-emitted as an `error` chunk, which the processor already raises on.
    """

    def __init__(self, response, *, carryover: bool):
        self._response = response
        self._carryover = carryover

    async def aiter_lines(self):
        final = None
        async for line in self._response.aiter_lines():
            line = line.strip()
            if not line.startswith("data: "):
                continue
            try:
                event = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            kind = event.get("type")
            if kind in ("response.completed", "response.incomplete"):
                final = event.get("response") or {}
            elif kind in ("response.failed", "error"):
                error = ((event.get("response") or {}).get("error") if kind == "response.failed"
                         else event.get("error") or event)
                yield "data: " + json.dumps({"error": error or {"message": kind}})
                return
        if final is None:
            raise ProviderError("the Responses stream ended without a response.completed event")
        completion = responses_to_chat_completion(final, carryover=self._carryover)
        choice = completion["choices"][0]
        delta = dict(choice["message"])
        if delta.get("tool_calls"):
            delta["tool_calls"] = [{"index": i, **call} for i, call in enumerate(delta["tool_calls"])]
        yield "data: " + json.dumps({
            "choices": [{"index": 0, "delta": delta, "finish_reason": choice["finish_reason"]}],
            "usage": completion["usage"]})
        yield "data: [DONE]"

    async def aclose(self):
        await self._response.aclose()
